import os
import osmnx as ox
import geopandas as gpd
from shapely.geometry import box, Polygon
import numpy as np
import pandas as pd
from pathlib import Path
import json
import pyarrow.parquet as pq
from typing import Dict, List, Any, Union, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

# Try to import cudf for GPU acceleration
try:
    import cudf
    HAS_CUDF = True
except ImportError:
    logger.warning("cudf not available. GPU acceleration will be disabled.")
    HAS_CUDF = False

# Define ALL possible landuse tags
ALL_TAGS = {
    'landuse': [
        'residential', 'commercial', 'industrial', 'retail', 'agricultural',
        'forest', 'grass', 'farmland', 'farm', 'meadow', 'vineyard', 'orchard',
        'cemetery', 'garages', 'military', 'railway', 'education', 'institutional',
        'religious', 'civic', 'hospital', 'parking', 'quarry', 'landfill',
        'brownfield', 'greenfield', 'construction', 'allotments', 'recreation_ground',
        'conservation', 'reservoir', 'basin', 'village_green', 'plant_nursery',
        'greenhouse_horticulture', 'farmyard', 'port', 'logistics', 'salt_pond',
        'aquaculture', 'flowerbed'
    ],
    'leisure': [
        'park', 'garden', 'playground', 'sports_centre', 'stadium', 'pitch',
        'swimming_pool', 'recreation_ground', 'golf_course', 'track',
        'nature_reserve', 'dog_park', 'fitness_station'
    ],
    'amenity': [
        'school', 'university', 'college', 'hospital', 'clinic', 'marketplace',
        'place_of_worship', 'community_centre', 'library', 'theatre',
        'public_building', 'townhall', 'police', 'fire_station', 'prison'
    ],
    'natural': [
        'wood', 'grassland', 'heath', 'scrub', 'wetland', 'marsh', 'bog',
        'swamp', 'water', 'beach', 'sand', 'bare_rock'
    ],
    'area': 'yes'
}

def get_landuse_data(
    bbox: Optional[Union[Tuple[float, float, float, float], List[float], Polygon]] = None,
    tags: Optional[Dict[str, List[str]]] = None,
    save_path: str = "landuse.geoparquet"
) -> Optional[gpd.GeoDataFrame]:
    """
    Fetch landuse data from OSM for a specific bbox and/or tags.
    
    Args:
        bbox: Optional bounding box as (west, south, east, north) or Polygon
        tags: Optional dictionary of OSM tags to fetch. If None, fetches all tags
        save_path: Path to save the GeoParquet file
        
    Returns:
        GeoDataFrame containing the landuse data
    """
    print("Downloading landuse data...")
    
    # Use all tags if none specified
    if tags is None:
        tags = ALL_TAGS.copy()
    
    try:
        # Handle bbox input
        if bbox is not None:
            if isinstance(bbox, (tuple, list)):
                # Convert bbox to polygon
                west, south, east, north = bbox
                bbox_polygon = box(west, south, east, north)
            elif isinstance(bbox, Polygon):
                bbox_polygon = bbox
            else:
                raise ValueError("bbox must be tuple/list of coordinates or Polygon")
            
            # Fetch data using OSMnx with bbox
            gdf = ox.features_from_polygon(bbox_polygon, tags=tags)
        else:
            # Fetch data for India if no bbox specified
            gdf = ox.features_from_place("India", tags=tags)
        
        # Filter for polygon geometries only
        gdf = gdf[gdf.geometry.type.isin(['Polygon', 'MultiPolygon'])]
        
        # Create a comprehensive landuse classification
        def determine_landuse(row):
            # Check each tag type in priority order
            if 'landuse' in row and pd.notnull(row['landuse']):
                return str(row['landuse'])
            elif 'leisure' in row and pd.notnull(row['leisure']):
                return f"leisure_{row['leisure']}"
            elif 'amenity' in row and pd.notnull(row['amenity']):
                return f"amenity_{row['amenity']}"
            elif 'natural' in row and pd.notnull(row['natural']):
                return f"natural_{row['natural']}"
            return 'unclassified'

        # Add unified landuse classification
        gdf['landuse_type'] = gdf.apply(determine_landuse, axis=1)

        # Print summary statistics
        print("\nLanduse Statistics:")
        print("===================")
        print(f"Total features: {len(gdf)}")
        print("\nTop 20 landuse types by count:")
        print(gdf['landuse_type'].value_counts().head(20))
        print(f"\nTotal unique landuse types: {len(gdf['landuse_type'].unique())}")

        # Calculate total area covered
        gdf_projected = gdf.to_crs(epsg=3857)  # Project to Mercator for area calculation
        total_area_sqkm = gdf_projected.geometry.area.sum() / 1_000_000  # Convert to sq km
        print(f"\nTotal area covered: {total_area_sqkm:.2f} sq km")

        # If file exists, append new data
        if os.path.exists(save_path):
            print("\nAppending to existing GeoParquet file...")
            existing_gdf = gpd.read_parquet(save_path)
            gdf = gpd.pd.concat([existing_gdf, gdf]).drop_duplicates()

        # Save to GeoParquet
        gdf.to_parquet(save_path, index=False)
        print(f"\nOSM land-use data saved to {save_path}")
        
        return gdf

    except Exception as e:
        print(f"Error fetching landuse data: {str(e)}")
        return None

def get_specific_tags(tag_categories: List[str]) -> Dict[str, List[str]]:
    """
    Get specific tag categories from ALL_TAGS.
    
    Args:
        tag_categories: List of tag categories to include (e.g. ['landuse', 'leisure'])
        
    Returns:
        Dictionary containing only the specified tag categories
    """
    return {
        category: ALL_TAGS[category]
        for category in tag_categories
        if category in ALL_TAGS
    }

def index_osm_parquet(base_path: str = "./osm_data") -> Dict[str, List[str]]:
    """
    Analyze OSM local parquet files and record any processing errors.
    
    Args:
        base_path (str): Base directory containing OSM parquet files
        
    Returns:
        Dict containing lists of processed and error files
    """
    # Convert base_path to Path object
    base_path = Path(base_path)
    
    # Set up data directory path relative to project root
    data_dir = Path(__file__).parents[3] / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    results = {
        "processed_files": [],
        "error_files": []
    }
    
    # Walk through all files in the directory
    for root, _, files in os.walk(base_path):
        for file_name in files:
            if file_name.endswith('.parquet'):
                file_path = Path(root) / file_name
                
                try:
                    # Try reading the parquet file
                    table = pq.read_table(str(file_path))
                    results["processed_files"].append({
                        "file_name": file_name,
                        "file_path": str(file_path)
                    })
                except Exception as e:
                    results["error_files"].append({
                        "file_name": file_name,
                        "file_path": str(file_path),
                        "error": str(e)
                    })
                    print(f"Error processing {file_name}: {str(e)}")
    
    # Save results to JSON file in project's data directory
    output_path = data_dir / "osm_parquet_index.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nAnalysis saved to: {output_path}")
    
    # Print summary
    print("\nSummary:")
    print(f"Total processed files: {len(results['processed_files'])}")
    print(f"Total error files: {len(results['error_files'])}")
    
    return results

if __name__ == "__main__":
    gdf = get_landuse_data()
    
    if gdf is not None:
        # Additional validation
        print("\nValidation Results:")
        print("===================")
        print(f"Number of valid geometries: {sum(gdf.geometry.is_valid)}")
        print(f"Number of invalid geometries: {sum(~gdf.geometry.is_valid)}")
        
        # Print some example coordinates to verify location
        print("\nSample Coordinates (first 5 features):")
        for idx, row in gdf.head().iterrows():
            centroid = row.geometry.centroid
            print(f"Landuse: {row['landuse_type']}, Location: ({centroid.y:.6f}, {centroid.x:.6f})")

        # GPU Processing with cuDF if available
        if HAS_CUDF:
            print("Loading data into GPU for processing...")
            gdf_cudf = cudf.from_pandas(gdf)

            # Example GPU query: Filter only parks
            gdf_parks = gdf_cudf[gdf_cudf["landuse_type"] == "leisure_park"]

            # Convert back to Pandas if needed
            gdf_parks_pd = gdf_parks.to_pandas()
            print("Filtered parks dataset:")
            print(gdf_parks_pd.head())

# Run the analysis
error_details = index_osm_parquet()

