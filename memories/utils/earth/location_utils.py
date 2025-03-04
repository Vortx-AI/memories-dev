"""
Utility functions for location processing and extraction.
"""

import re
from typing import Dict, Any, Tuple, Optional, List, Union
import logging
from urllib.parse import quote
import requests
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import math

logger = logging.getLogger(__name__)

__all__ = [
    'is_valid_coordinates',
    'extract_coordinates',
    'normalize_location',
    'get_address_from_coords',
    'get_coords_from_address',
    'get_bounding_box_from_address',
    'get_bounding_box_from_coords',
    'expand_bbox_with_radius'
]

def is_valid_coordinates(location: str) -> bool:
    """Check if a string contains valid coordinates."""
    try:
        # Match coordinate patterns like (12.34, 56.78) or 12.34, 56.78
        pattern = r'\(?\s*(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\s*\)?'
        match = re.match(pattern, location)
        
        if match:
            lat, lon = map(float, match.groups())
            # Basic validation of coordinate ranges
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                return True
        return False
    except Exception as e:
        logger.error(f"Error validating coordinates: {str(e)}")
        return False

def extract_coordinates(text: str) -> Optional[Tuple[float, float]]:
    """Extract coordinates from text if present."""
    coordinates_pattern = r'\(?\s*(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\s*\)?'
    coord_match = re.search(coordinates_pattern, text)
    if coord_match:
        lat, lon = map(float, coord_match.groups())
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            return (lat, lon)
    return None

def normalize_location(location: str, location_type: str) -> Dict[str, Any]:
    """
    Normalize location information into a standard format.
    
    Args:
        location (str): Location string (address or coordinates)
        location_type (str): Type of location (point, city, etc.)
    
    Returns:
        Dict with normalized location information
    """
    try:
        if location_type == "point":
            coords = extract_coordinates(location)
            if coords:
                return {
                    "type": "point",
                    "coordinates": coords,
                    "original": location
                }
        
        # For other location types, return structured format
        return {
            "type": location_type,
            "name": location.strip(),
            "original": location
        }
        
    except Exception as e:
        logger.error(f"Error normalizing location: {str(e)}")
        return {
            "type": "unknown",
            "error": str(e),
            "original": location
        }

def get_address_from_coords(lat: float, lon: float) -> Dict[str, Any]:
    """
    Get address details from coordinates using Nominatim OpenStreetMap API.
    
    Args:
        lat: Latitude of the location (-90 to 90)
        lon: Longitude of the location (-180 to 180)
        
    Returns:
        Dictionary containing:
            - status: "success" or "error"
            - address: Full address details if found
            - display_name: Formatted display name
            - message: Error message if status is "error"
    """
    try:
        # Validate coordinates
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            return {
                "status": "error",
                "message": "Invalid coordinates: latitude must be between -90 and 90, longitude between -180 and 180",
                "address": None
            }
        
        # Define headers for Nominatim API
        headers = {
            'User-Agent': 'Memories/1.0 (https://github.com/your-repo/memories)',
            'Accept-Language': 'en-US,en;q=0.5'
        }
        
        # Make request to Nominatim API using reverse geocoding
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&addressdetails=1"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Parse response
        result = response.json()
        
        if not result or "error" in result:
            return {
                "status": "error",
                "message": result.get("error", "No results found for the given coordinates"),
                "address": None
            }
            
        return {
            "status": "success",
            "address": result.get("address", {}),
            "display_name": result.get("display_name"),
            "osm_type": result.get("osm_type"),
            "osm_id": result.get("osm_id"),
            "place_id": result.get("place_id"),
            "lat": float(result.get("lat", lat)),
            "lon": float(result.get("lon", lon))
        }
        
    except Exception as e:
        logger.error(f"Error getting address from coordinates: {str(e)}")
        return {
            "status": "error",
            "message": str(e),
            "address": None
        }

def get_coords_from_address(address: str) -> Dict[str, Any]:
    """
    Get coordinates from address using Nominatim OpenStreetMap API.
    
    Args:
        address: Address string to geocode
        
    Returns:
        Dictionary containing:
            - status: "success" or "error"
            - lat: Latitude if found
            - lon: Longitude if found
            - display_name: Formatted display name
            - message: Error message if status is "error"
    """
    try:
        # Format the address for URL
        encoded_address = quote(address)
        
        # Define headers for Nominatim API
        headers = {
            'User-Agent': 'Memories/1.0 (https://github.com/your-repo/memories)',
            'Accept-Language': 'en-US,en;q=0.5'
        }
        
        # Make request to Nominatim API
        url = f"https://nominatim.openstreetmap.org/search?q={encoded_address}&format=json&limit=1"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Parse response
        results = response.json()
        
        if not results:
            return {
                "status": "error",
                "message": "No results found for the given address",
                "lat": None,
                "lon": None
            }
            
        # Get first result
        result = results[0]
        
        return {
            "status": "success",
            "lat": float(result["lat"]),
            "lon": float(result["lon"]),
            "display_name": result["display_name"],
            "osm_type": result.get("osm_type"),
            "osm_id": result.get("osm_id"),
            "place_id": result.get("place_id"),
            "importance": result.get("importance"),
            "address_type": result.get("type"),
            "address_class": result.get("class")
        }
        
    except Exception as e:
        logger.error(f"Error getting coordinates from address: {str(e)}")
        return {
            "status": "error",
            "message": str(e),
            "lat": None,
            "lon": None
        }

def get_bounding_box_from_address(address: str) -> Dict[str, Any]:
    """
    Get bounding box coordinates for an address using Nominatim OpenStreetMap API.
    
    Args:
        address: Address string to geocode
        
    Returns:
        Dictionary containing:
            - boundingbox: List of [min_lat, max_lat, min_lon, max_lon]
            - status: "success" or "error"
            - message: Error message if status is "error"
            - display_name: Full display name of the location
            - lat: Latitude of the location center
            - lon: Longitude of the location center
    """
    try:
        # Format the address for URL
        encoded_address = quote(address)
        
        # Define headers - this is important for Nominatim's terms of use
        headers = {
            'User-Agent': 'Memories/1.0 (https://github.com/your-repo/memories)',
            'Accept-Language': 'en-US,en;q=0.5'
        }
        
        # Make request to Nominatim API
        url = f"https://nominatim.openstreetmap.org/search?q={encoded_address}&format=json&polygon_geojson=1"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Parse response
        results = response.json()
        
        if not results:
            return {
                "status": "error",
                "message": "No results found for the given address",
                "boundingbox": None
            }
            
        # Get first result
        result = results[0]
        
        return {
            "status": "success",
            "boundingbox": result["boundingbox"],  # [min_lat, max_lat, min_lon, max_lon]
            "display_name": result["display_name"],
            "lat": float(result["lat"]),
            "lon": float(result["lon"])
        }
        
    except Exception as e:
        logger.error(f"Error getting bounding box for address: {str(e)}")
        return {
            "status": "error",
            "message": str(e),
            "boundingbox": None
        }

def get_bounding_box_from_coords(lat: float, lon: float) -> Dict[str, Any]:
    """
    Get bounding box coordinates for a location using its latitude and longitude via Nominatim OpenStreetMap API.
    
    Args:
        lat: Latitude of the location
        lon: Longitude of the location
        
    Returns:
        Dictionary containing:
            - boundingbox: List of [min_lat, max_lat, min_lon, max_lon]
            - status: "success" or "error"
            - message: Error message if status is "error"
            - display_name: Full display name of the location
            - lat: Latitude of the location center
            - lon: Longitude of the location center
    """
    try:
        # Validate coordinates
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            return {
                "status": "error",
                "message": "Invalid coordinates: latitude must be between -90 and 90, longitude between -180 and 180",
                "boundingbox": None
            }
        
        # Define headers for Nominatim API
        headers = {
            'User-Agent': 'Memories/1.0 (https://github.com/your-repo/memories)',
            'Accept-Language': 'en-US,en;q=0.5'
        }
        
        # Make request to Nominatim API using reverse geocoding
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&zoom=10"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Parse response
        result = response.json()
        
        if not result or "error" in result:
            return {
                "status": "error",
                "message": result.get("error", "No results found for the given coordinates"),
                "boundingbox": None
            }
            
        return {
            "status": "success",
            "boundingbox": result["boundingbox"],  # [min_lat, max_lat, min_lon, max_lon]
            "display_name": result["display_name"],
            "lat": float(result["lat"]),
            "lon": float(result["lon"])
        }
        
    except Exception as e:
        logger.error(f"Error getting bounding box for coordinates: {str(e)}")
        return {
            "status": "error",
            "message": str(e),
            "boundingbox": None
        }

def expand_bbox_with_radius(
    input_type: str,
    radius_km: float,
    coordinates: Optional[Dict[str, float]] = None,
    bbox: Optional[Dict[str, float]] = None,
    return_format: str = "bbox"
) -> Dict[str, Any]:
    """
    Expands a bounding box by a specified radius, or creates a bounding box around a point with given radius.
    The radius is applied in all directions.
    
    Args:
        input_type: Either "coordinates" or "bbox"
        radius_km: Radius in kilometers to expand the bounding box or create box around point
        coordinates: Dictionary with lat/lon (required if input_type is "coordinates")
        bbox: Dictionary with xmin/ymin/xmax/ymax (required if input_type is "bbox")
        return_format: Format of the returned bounding box ("bbox" or "geojson")
        
    Returns:
        Dictionary containing:
            - status: "success" or "error"
            - message: Error message if status is "error"
            - bbox: Expanded bounding box coordinates
            - geojson: GeoJSON representation if return_format is "geojson"
    """
    try:
        # Validate input parameters
        if input_type not in ["coordinates", "bbox"]:
            return {
                "status": "error",
                "message": "Invalid input_type. Must be either 'coordinates' or 'bbox'",
                "bbox": None
            }
            
        if radius_km <= 0:
            return {
                "status": "error",
                "message": "Radius must be greater than 0",
                "bbox": None
            }
            
        # Handle coordinates input
        if input_type == "coordinates":
            if not coordinates or 'lat' not in coordinates or 'lon' not in coordinates:
                return {
                    "status": "error",
                    "message": "Coordinates must contain 'lat' and 'lon'",
                    "bbox": None
                }
                
            lat, lon = coordinates['lat'], coordinates['lon']
            
            # Validate coordinate ranges
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                return {
                    "status": "error",
                    "message": "Invalid coordinates: latitude must be between -90 and 90, longitude between -180 and 180",
                    "bbox": None
                }
                
            # Calculate bounding box from point and radius
            # Convert radius from km to degrees (approximate)
            radius_lat = radius_km / 111.32  # 1 degree latitude = 111.32 km
            radius_lon = radius_km / (111.32 * math.cos(math.radians(lat)))  # Adjust for latitude
            
            expanded_bbox = {
                "xmin": max(-180, lon - radius_lon),
                "ymin": max(-90, lat - radius_lat),
                "xmax": min(180, lon + radius_lon),
                "ymax": min(90, lat + radius_lat)
            }
            
        # Handle bbox input
        else:
            if not bbox or not all(k in bbox for k in ['xmin', 'ymin', 'xmax', 'ymax']):
                return {
                    "status": "error",
                    "message": "Bbox must contain 'xmin', 'ymin', 'xmax', 'ymax'",
                    "bbox": None
                }
                
            # Validate bbox coordinates
            if not all(-180 <= bbox[k] <= 180 for k in ['xmin', 'xmax']) or \
               not all(-90 <= bbox[k] <= 90 for k in ['ymin', 'ymax']):
                return {
                    "status": "error",
                    "message": "Invalid bbox coordinates",
                    "bbox": None
                }
                
            # Calculate center point
            center_lat = (bbox['ymin'] + bbox['ymax']) / 2
            
            # Convert radius from km to degrees (approximate)
            radius_lat = radius_km / 111.32  # 1 degree latitude = 111.32 km
            radius_lon = radius_km / (111.32 * math.cos(math.radians(center_lat)))  # Adjust for latitude
            
            expanded_bbox = {
                "xmin": max(-180, bbox['xmin'] - radius_lon),
                "ymin": max(-90, bbox['ymin'] - radius_lat),
                "xmax": min(180, bbox['xmax'] + radius_lon),
                "ymax": min(90, bbox['ymax'] + radius_lat)
            }
            
        # Prepare response based on return format
        response = {
            "status": "success",
            "bbox": expanded_bbox
        }
        
        # Add GeoJSON format if requested
        if return_format == "geojson":
            response["geojson"] = {
                "type": "Polygon",
                "coordinates": [[
                    [expanded_bbox['xmin'], expanded_bbox['ymin']],
                    [expanded_bbox['xmin'], expanded_bbox['ymax']],
                    [expanded_bbox['xmax'], expanded_bbox['ymax']],
                    [expanded_bbox['xmax'], expanded_bbox['ymin']],
                    [expanded_bbox['xmin'], expanded_bbox['ymin']]
                ]]
            }
            
        return response
        
    except Exception as e:
        logger.error(f"Error expanding bounding box: {str(e)}")
        return {
            "status": "error",
            "message": str(e),
            "bbox": None
        }
