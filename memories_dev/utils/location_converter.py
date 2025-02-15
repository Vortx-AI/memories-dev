import re
from typing import List, Dict, Union, Tuple, Any
from shapely.geometry import Point, Polygon, MultiPolygon
import geopandas as gpd
from geopy.geocoders import Nominatim
import numpy as np

class LocationConverter:
    def __init__(self):
        """Initialize the location converter with geocoder."""
        self.geocoder = Nominatim(user_agent="memories_dev")
    
    def parse_coordinates(self, coord_str: str) -> List[Tuple[float, float]]:
        """
        Parse coordinate string into list of coordinate tuples.
        Handles formats like: "(37.7749, -122.4194),(37.7750, -122.4195)"
        """
        # Remove spaces and split by coordinate pairs
        coords = []
        # Match coordinates pattern (including with or without parentheses)
        pattern = r'\(?\s*(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\s*\)?'
        matches = re.finditer(pattern, coord_str)
        
        for match in matches:
            lat, lon = float(match.group(1)), float(match.group(2))
            coords.append((lat, lon))
        
        return coords

    def is_coordinates(self, location: str) -> bool:
        """Check if string represents coordinate pairs."""
        pattern = r'^[\s\(\)0-9\.-,]+$'
        return bool(re.match(pattern, location))
    
    def is_polygon(self, coords: List[Tuple[float, float]]) -> bool:
        """Check if coordinates form a polygon (3+ points with first = last)."""
        return len(coords) >= 3
    
    def is_multipolygon(self, location: Union[str, List[List[Tuple[float, float]]]]) -> bool:
        """Check if location represents multiple polygons."""
        if isinstance(location, str):
            # Split into separate polygon coordinates and check each
            polygon_strings = re.split(r'\)\s*,\s*\(', location)
            return len(polygon_strings) > 1
        return len(location) > 1
    
    def convert_location(self, location: Union[str, Dict, gpd.GeoDataFrame]) -> Dict[str, Any]:
        """
        Convert various location formats into standardized dictionary with
        centroid, polygon, and address information.
        
        Args:
            location: Can be:
                     - Coordinate string "(lat,lon)"
                     - Multiple coordinates "(lat,lon),(lat,lon)"
                     - Polygon coordinates
                     - Address string
                     - GeoJSON dict
                     - GeoDataFrame
        
        Returns:
            Dict with:
                - type: "point", "polygon", "multipolygon", or "address"
                - centroid: (lat, lon)
                - polygon: List of coordinate tuples (if applicable)
                - address: String address (if applicable)
        """
        result = {
            "type": None,
            "centroid": None,
            "polygon": None,
            "address": None
        }
        
        try:
            if isinstance(location, str):
                if self.is_coordinates(location):
                    coords = self.parse_coordinates(location)
                    
                    if len(coords) == 1:
                        # Single point
                        result["type"] = "point"
                        result["centroid"] = coords[0]
                        # Get address for the point
                        location_obj = self.geocoder.reverse(f"{coords[0][0]}, {coords[0][1]}")
                        result["address"] = location_obj.address if location_obj else None
                        
                    elif self.is_multipolygon(location):
                        # Multiple polygons
                        result["type"] = "multipolygon"
                        result["polygon"] = coords
                        # Calculate centroid of all points
                        centroid = np.mean(coords, axis=0)
                        result["centroid"] = tuple(centroid)
                        
                    elif self.is_polygon(coords):
                        # Single polygon
                        result["type"] = "polygon"
                        result["polygon"] = coords
                        # Calculate centroid
                        poly = Polygon(coords)
                        result["centroid"] = (poly.centroid.y, poly.centroid.x)
                        
                else:
                    # Treat as address
                    result["type"] = "address"
                    result["address"] = location
                    # Get coordinates for the address
                    location_obj = self.geocoder.geocode(location)
                    if location_obj:
                        result["centroid"] = (location_obj.latitude, location_obj.longitude)
                        
            elif isinstance(location, dict):
                # Handle GeoJSON
                if location.get("type") == "Point":
                    result["type"] = "point"
                    coords = location["coordinates"]
                    result["centroid"] = (coords[1], coords[0])  # Convert from lon,lat to lat,lon
                    
                elif location.get("type") in ["Polygon", "MultiPolygon"]:
                    result["type"] = location["type"].lower()
                    coords = location["coordinates"][0]  # Get outer ring
                    result["polygon"] = [(c[1], c[0]) for c in coords]  # Convert from lon,lat to lat,lon
                    # Calculate centroid
                    poly = Polygon(result["polygon"])
                    result["centroid"] = (poly.centroid.y, poly.centroid.x)
                    
            elif isinstance(location, gpd.GeoDataFrame):
                # Handle GeoDataFrame
                geometry = location.geometry.iloc[0]
                if isinstance(geometry, Point):
                    result["type"] = "point"
                    result["centroid"] = (geometry.y, geometry.x)
                elif isinstance(geometry, Polygon):
                    result["type"] = "polygon"
                    result["polygon"] = [(y, x) for x, y in geometry.exterior.coords]
                    result["centroid"] = (geometry.centroid.y, geometry.centroid.x)
                elif isinstance(geometry, MultiPolygon):
                    result["type"] = "multipolygon"
                    result["polygon"] = [[(y, x) for x, y in poly.exterior.coords] 
                                       for poly in geometry.geoms]
                    result["centroid"] = (geometry.centroid.y, geometry.centroid.x)
            
        except Exception as e:
            print(f"Error converting location: {str(e)}")
            raise
            
        return result

if __name__ == "__main__":
    # Example usage
    converter = LocationConverter()
    
    # Test different formats
    locations = [
        "(37.7749, -122.4194)",  # Single point
        "(37.7749, -122.4194),(37.7750, -122.4195),(37.7751, -122.4196)", # Polygon
        "123 Main St, San Francisco, CA",  # Address
        {"type": "Point", "coordinates": [-122.4194, 37.7749]},  # GeoJSON
    ]
    
    for loc in locations:
        result = converter.convert_location(loc)
        print(f"\nInput: {loc}")
        print(f"Result: {result}")
