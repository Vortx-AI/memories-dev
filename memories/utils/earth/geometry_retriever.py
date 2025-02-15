from typing import Dict, Any, Tuple, List
import duckdb
import logging
from pathlib import Path

class GeometryExtractor:
    def __init__(self):
        """Initialize GeometryExtractor with DuckDB connection"""
        self.logger = logging.getLogger(__name__)
        self.conn = duckdb.connect()
        self.conn.execute("INSTALL spatial;")
        self.conn.execute("LOAD spatial;")

    def extract_by_point(self, location: Dict[str, Any], radius_meters: float = 1000) -> Dict[str, Any]:
        """
        Extract geometries near a point location
        
        Args:
            location (Dict): Location info with coordinates
            radius_meters (float): Search radius in meters
            
        Returns:
            Dict[str, Any]: Geometries found near the point
        """
        try:
            lat, lon = location['coordinates']
            
            # Create point geometry
            point = f"ST_Point({lon}, {lat})"
            
            # Create search area (buffer around point)
            search_area = f"ST_Buffer(ST_Transform({point}, 3857), {radius_meters})"
            
            # Query for nearby features from OSM data
            query = f"""
                SELECT 
                    'multipolygons' as layer,
                    name,
                    landuse,
                    leisure,
                    amenity,
                    ST_AsText(geom) as geometry,
                    ST_Distance(ST_Transform(geom, 3857), ST_Transform({point}, 3857)) as distance
                FROM 'osm_data/india_multipolygons.parquet'
                WHERE ST_Intersects(
                    ST_Transform(geom, 3857),
                    {search_area}
                )
                UNION ALL
                SELECT 
                    'points' as layer,
                    name,
                    NULL as landuse,
                    NULL as leisure,
                    amenity,
                    ST_AsText(geom) as geometry,
                    ST_Distance(ST_Transform(geom, 3857), ST_Transform({point}, 3857)) as distance
                FROM 'osm_data/india_points.parquet'
                WHERE ST_Intersects(
                    ST_Transform(geom, 3857),
                    {search_area}
                )
                ORDER BY distance
                LIMIT 100;
            """
            
            results = self.conn.execute(query).fetchdf()
            
            response = {
                "query_point": {
                    "type": "Point",
                    "coordinates": [lon, lat]
                },
                "radius_meters": radius_meters,
                "features": []
            }
            
            # Format results
            for _, row in results.iterrows():
                feature = {
                    "layer": row['layer'],
                    "geometry": row['geometry'],
                    "properties": {
                        "name": row['name'],
                        "distance_meters": float(row['distance'])
                    }
                }
                
                # Add non-null properties
                for prop in ['landuse', 'leisure', 'amenity']:
                    if row[prop] is not None:
                        feature['properties'][prop] = row[prop]
                
                response['features'].append(feature)
            
            self.logger.info(f"Found {len(response['features'])} features near {lat}, {lon}")
            return response
            
        except Exception as e:
            self.logger.error(f"Error extracting geometries: {str(e)}")
            return {
                "error": str(e),
                "location": location
            }

    def process(self, location: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process location info and extract relevant geometries
        
        Args:
            location (Dict): Location information from LocationExtractor
            
        Returns:
            Dict[str, Any]: Extracted geometries and properties
        """
        try:
            if location.get('location_type') == 'point':
                return self.extract_by_point(location)
            else:
                self.logger.error(f"Unsupported location type: {location.get('location_type')}")
                return {
                    "error": f"Unsupported location type: {location.get('location_type')}",
                    "location": location
                }
                
        except Exception as e:
            self.logger.error(f"Error in geometry extraction: {str(e)}")
            return {
                "error": str(e),
                "location": location
            }

if __name__ == "__main__":
    # Test code for a specific point: -12.911935, 77.611699
    logging.basicConfig(level=logging.INFO)
    
    extractor = GeometryExtractor()
    # Create a location dictionary with the test coordinates
    test_location = {
        "location_type": "point",
        "coordinates": [-12.911935, 77.611699]
    }
    
    # Call the extract_by_point method and print the result
    result = extractor.extract_by_point(test_location, radius_meters=1000)
    print("Result for test point (-12.911935, 77.611699):")
    print(result)