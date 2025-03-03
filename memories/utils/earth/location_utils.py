"""
Utility functions for location processing and extraction.
"""

import re
from typing import Dict, Any, Tuple, Optional, List
import logging
from urllib.parse import quote
import requests
from geopy.geocoders import Nominatim

logger = logging.getLogger(__name__)

__all__ = [
    'is_valid_coordinates',
    'extract_coordinates',
    'normalize_location',
    'get_address_from_coords',
    'get_coords_from_address',
    'get_bounding_box_from_address',
    'get_bounding_box_from_coords'
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
    """Get address details from coordinates using a geocoding service."""
    # Implementation depends on your geocoding service
    # This is a placeholder that should be implemented based on your needs
    pass

def get_coords_from_address(address: str) -> Dict[str, Any]:
    """Get coordinates from address using a geocoding service."""
    # Implementation depends on your geocoding service
    # This is a placeholder that should be implemented based on your needs
    pass

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
