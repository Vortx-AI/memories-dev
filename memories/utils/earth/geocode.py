import pandas as pd
import numpy as np
import faiss
from pathlib import Path
import difflib
from shapely.wkt import loads as load_wkt
from typing import List, Dict, Any, Optional

# Import the embedding function from our data connectors module.
from memories.data_acquisition.data_connectors import get_word_embedding

def create_point_geometry(lat: float, lon: float) -> str:
    """
    Create a WKT point geometry string with SRID 4326 (WGS84).
    
    Args:
        lat (float): Latitude
        lon (float): Longitude
        
    Returns:
        str: WKT point geometry string
    """
    return f"ST_SetSRID(ST_Point({lon}, {lat}), 4326)"

def transform_geometry(geom_expr: str, source_srid: int = 4326, target_srid: int = 3857) -> str:
    """
    Transform geometry from one coordinate system to another.
    
    Args:
        geom_expr (str): Geometry expression or column name
        source_srid (int): Source coordinate system SRID (default: 4326 WGS84)
        target_srid (int): Target coordinate system SRID (default: 3857 Web Mercator)
        
    Returns:
        str: SQL expression for transformed geometry
    """
    if source_srid == target_srid:
        return geom_expr
    return f"ST_Transform(ST_SetSRID({geom_expr}, {source_srid}), {target_srid})"

def compute_spatial_distance(geom1: str, geom2: str, source_srid: int = 4326, target_srid: int = 3857) -> str:
    """
    Compute distance between two geometries, transforming to a projected coordinate system if needed.
    
    Args:
        geom1 (str): First geometry expression
        geom2 (str): Second geometry expression
        source_srid (int): Source coordinate system SRID (default: 4326 WGS84)
        target_srid (int): Target coordinate system SRID (default: 3857 Web Mercator)
        
    Returns:
        str: SQL expression for distance calculation
    """
    if source_srid != target_srid:
        geom1 = transform_geometry(geom1, source_srid, target_srid)
        geom2 = transform_geometry(geom2, source_srid, target_srid)
    return f"ST_Distance({geom1}, {geom2})"

def create_spatial_query(
    parquet_file: str,
    column_name: str,
    value: str,
    geometry_column: str,
    target_lat: float,
    target_lon: float,
    radius: float,
    source_srid: int = 4326,
    target_srid: int = 3857
) -> str:
    """
    Create a spatial query with proper coordinate system transformations.
    
    Args:
        parquet_file (str): Path to the parquet file
        column_name (str): Name of the column to filter
        value (str): Value to match in the column
        geometry_column (str): Name of the geometry column
        target_lat (float): Target latitude
        target_lon (float): Target longitude
        radius (float): Search radius in meters
        source_srid (int): Source coordinate system SRID (default: 4326 WGS84)
        target_srid (int): Target coordinate system SRID (default: 3857 Web Mercator)
        
    Returns:
        str: Complete SQL query string
    """
    # Create point geometry for target location
    target_point = create_point_geometry(target_lat, target_lon)
    
    # Build the distance calculation expression
    distance_expr = compute_spatial_distance(geometry_column, target_point, source_srid, target_srid)
    
    # Construct the complete query
    query = f"""
    SELECT *
    FROM parquet_scan('{parquet_file}')
    WHERE {column_name} = '{value}' 
    AND {distance_expr} <= {radius};
    """
    
    return query

def compute_similarity(a: str, b: str) -> float:
    """
    Compute a similarity score between two strings using difflib.
    """
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()

def geocode_address(faiss_storage: Dict[str, Any], address: str, word_vectors: Optional[Any] = None) -> List[Dict[str, Any]]:
    """
    Given a FAISS storage (which includes an index and metadata about parquet file columns) 
    and an address, retrieve the best 5 matches. For each match the metadata includes:
        - Parquet file location
        - The address column name (e.g. "name" or "address")
        - The matching address value found
        - Its geometry (from the geometry column in that file)
        - The geometry type (point, line, polygon)
        - The centroid of the geometry as latitude and longitude

    Args:
        faiss_storage (Dict[str, Any]): A dictionary containing a FAISS index and metadata.
        address (str): The address to query for.
        word_vectors (Optional[Any]): Word embedding model. If not provided, the function
                                      will try to retrieve it from faiss_storage["word_vectors"].
    
    Returns:
        List[Dict[str, Any]]: A list of at most 5 match dictionaries.
    """
    # Get the word vectors from parameter or from faiss_storage.
    if word_vectors is None:
        word_vectors = faiss_storage.get("word_vectors")
    if word_vectors is None:
        raise ValueError("Word vectors must be provided either as a parameter or stored under 'word_vectors' in faiss_storage")

    # Ensure we know the dimension from the FAISS index.
    dimension = faiss_storage['index'].d

    # Compute the embedding for the input address.
    query_vec = get_word_embedding(address, word_vectors, dimension)
    query_vec = np.expand_dims(query_vec, axis=0)

    # Query the FAISS index for the top 5 nearest neighbors.
    k = 5
    distances, indices = faiss_storage['index'].search(query_vec, k)

    matches = []
    # Iterate over candidate indices returned by FAISS.
    for idx in indices[0]:
        # Sanity check on index.
        if idx < 0 or idx >= len(faiss_storage['metadata']):
            continue
        candidate_meta = faiss_storage['metadata'][idx]
        col_name = candidate_meta.get('column_name', '').lower()
        # Filter to only consider columns likely to hold address values.
        if not any(x in col_name for x in ['name', 'address']):
            continue

        file_path = candidate_meta.get('file_path')
        if not file_path or not Path(file_path).exists():
            continue

        try:
            df = pd.read_parquet(file_path)
        except Exception as e:
            print(f"Failed to read parquet file {file_path}: {e}")
            continue

        if candidate_meta['column_name'] not in df.columns:
            continue

        # Drop missing values in the candidate address column.
        candidate_series = df[candidate_meta['column_name']].dropna().astype(str)
        if candidate_series.empty:
            continue

        # Compute string similarity for each address value in the column.
        similarities = candidate_series.apply(lambda x: compute_similarity(address, x))
        best_idx = similarities.idxmax()
        best_similarity = similarities.loc[best_idx]
        best_address_value = str(df.loc[best_idx, candidate_meta['column_name']])
        
        # Identify the geometry column.
        geom_col = None
        if 'geom' in df.columns:
            geom_col = 'geom'
        elif 'geometry' in df.columns:
            geom_col = 'geometry'
        
        if geom_col is None:
            # Skip if no geometry information is available.
            continue
        
        geometry_value = df.loc[best_idx, geom_col]

        # Determine the geometry type from the geometry value.
        geometry_type = "unknown"
        if isinstance(geometry_value, str):
            geom_upper = geometry_value.strip().upper()
            if geom_upper.startswith("POINT"):
                geometry_type = "point"
            elif geom_upper.startswith("LINESTRING"):
                geometry_type = "line"
            elif geom_upper.startswith("POLYGON"):
                geometry_type = "polygon"
        # Otherwise, leave as "unknown" unless additional heuristics apply.

        # Compute the centroid of the geometry using Shapely.
        centroid_lat = None
        centroid_lon = None
        try:
            if isinstance(geometry_value, str):
                geom_obj = load_wkt(geometry_value)
            else:
                # Assume geometry_value is already a shapely geometry.
                geom_obj = geometry_value
            centroid = geom_obj.centroid
            centroid_lon = centroid.x
            centroid_lat = centroid.y
        except Exception as e:
            print(f"Could not compute centroid for geometry in file {file_path}: {e}")

        match_info = {
            "file_path": file_path,
            "address_column": candidate_meta['column_name'],
            "matched_address": best_address_value,
            "similarity": best_similarity,
            "geometry": geometry_value,
            "geometry_type": geometry_type,
            "centroid": {"lat": centroid_lat, "lon": centroid_lon}
        }
        matches.append(match_info)

        # Example of using the spatial query in the geocode function:
        try:
            # Create spatial query if coordinates are available
            if centroid_lat is not None and centroid_lon is not None:
                spatial_query = create_spatial_query(
                    parquet_file=file_path,
                    column_name=candidate_meta['column_name'],
                    value=best_address_value,
                    geometry_column=geom_col,
                    target_lat=centroid_lat,
                    target_lon=centroid_lon,
                    radius=1000  # Example radius in meters
                )
                # Use the spatial query as needed...
        except Exception as e:
            print(f"Error creating spatial query: {e}")
            continue

    # Sort all matches by descending similarity and return the top 5.
    matches_sorted = sorted(matches, key=lambda x: x["similarity"], reverse=True)
    top_matches = matches_sorted[:5]
    return top_matches

if __name__ == "__main__":
    # Example usage (the FAISS storage must be initialized/populated beforehand):
    # from memories.data_acquisition.data_connectors import ... (initialize faiss_storage)
    #
    # For this example, we assume 'faiss_storage' is a dictionary that was populated
    # via the multiple_parquet_connector process and that it contains:
    #    - A FAISS index under 'index'
    #    - A list of metadata dictionaries under 'metadata'
    #    - Optionally, a word vectors model under 'word_vectors'
    #
    # address_query = "123 Main Street"
    # results = geocode_address(faiss_storage, address_query)
    # print("Geocoding results:", results)
    pass
