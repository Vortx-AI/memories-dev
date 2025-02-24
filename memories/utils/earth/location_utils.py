"""
Utility functions for location processing and extraction.
"""

import re
from typing import Dict, Any, Tuple, Optional
import logging
from urllib.parse import quote
import requests

logger = logging.getLogger(__name__)

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
