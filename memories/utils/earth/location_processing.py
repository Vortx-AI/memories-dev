"""
Location processing utilities for handling geographic data.
"""

from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
import os
import logging
from time import sleep
from memories.utils.validation import Validator, validate_input, ValidationError

logger = logging.getLogger(__name__)

def filter_by_distance(
    locations: List[Dict[str, Any]], 
    center: List[float], 
    radius_km: float
) -> List[Dict[str, Any]]:
    """Filter locations within a certain radius of a center point.
    
    Args:
        locations: List of locations to filter
        center: Center point coordinates [lat, lon]
        radius_km: Radius in kilometers
        
    Returns:
        List of locations within the specified radius
    """
    filtered = []
    for loc in locations:
        if 'coordinates' not in loc:
            continue
        coords = loc['coordinates']
        distance = geodesic(center, coords).kilometers
        if distance <= radius_km:
            loc['distance'] = distance
            filtered.append(loc)
    return filtered

def filter_by_type(
    locations: List[Dict[str, Any]], 
    location_type: str
) -> List[Dict[str, Any]]:
    """Filter locations by their type.
    
    Args:
        locations: List of locations to filter
        location_type: Type of location to filter for
        
    Returns:
        List of locations matching the specified type
    """
    return [loc for loc in locations if loc.get('type') == location_type]

def sort_by_distance(
    locations: List[Dict[str, Any]], 
    center: List[float]
) -> List[Dict[str, Any]]:
    """Sort locations by distance from a center point.
    
    Args:
        locations: List of locations to sort
        center: Center point coordinates [lat, lon]
        
    Returns:
        List of locations sorted by distance
    """
    for loc in locations:
        if 'distance' not in loc and 'coordinates' in loc:
            loc['distance'] = geodesic(center, loc['coordinates']).kilometers
    return sorted(locations, key=lambda x: x.get('distance', float('inf')))

@validate_input(
    address=lambda x: Validator.validate_string(x, min_length=1, max_length=500),
    timeout=lambda x: Validator.validate_number(x, min_value=1, max_value=300, integer_only=True)
)
def geocode(
    address: str,
    user_agent: Optional[str] = None,
    timeout: int = 10
) -> Dict[str, Any]:
    """Convert address to coordinates.
    
    Args:
        address: Address string to geocode
        user_agent: User agent string for the geocoding service
        timeout: Timeout in seconds for the geocoding request
        
    Returns:
        Dictionary with location information
    """
    try:
        # Get user agent from environment or use default
        if not user_agent:
            user_agent = os.getenv('NOMINATIM_USER_AGENT', 'memories-dev-app')
        
        # Initialize geocoder
        geolocator = Nominatim(user_agent=user_agent)
        
        # Geocode the address
        location = geolocator.geocode(address, timeout=timeout)
        
        if location:
            return {
                'address': location.address,
                'coordinates': [location.latitude, location.longitude],
                'latitude': location.latitude,
                'longitude': location.longitude,
                'raw': location.raw
            }
        else:
            logger.warning(f"Could not geocode address: {address}")
            return {
                'address': address,
                'coordinates': None,
                'error': 'Location not found'
            }
    
    except Exception as e:
        logger.error(f"Geocoding error for address '{address}': {e}")
        return {
            'address': address,
            'coordinates': None,
            'error': str(e)
        }

def batch_geocode(
    addresses: List[str],
    user_agent: Optional[str] = None,
    timeout: int = 10,
    delay: float = 1.0
) -> List[Dict[str, Any]]:
    """Geocode multiple addresses with rate limiting.
    
    Args:
        addresses: List of address strings to geocode
        user_agent: User agent string for the geocoding service
        timeout: Timeout in seconds for each geocoding request
        delay: Delay in seconds between requests (for rate limiting)
        
    Returns:
        List of dictionaries with location information
    """
    results = []
    for i, address in enumerate(addresses):
        # Add delay between requests (except for the first one)
        if i > 0:
            sleep(delay)
        
        result = geocode(address, user_agent, timeout)
        results.append(result)
        
        # Log progress for large batches
        if len(addresses) > 10 and (i + 1) % 10 == 0:
            logger.info(f"Geocoded {i + 1}/{len(addresses)} addresses")
    
    return results

def reverse_geocode(
    coordinates: List[float],
    user_agent: Optional[str] = None,
    timeout: int = 10
) -> Dict[str, Any]:
    """Convert coordinates to address.
    
    Args:
        coordinates: [lat, lon] coordinates
        user_agent: User agent string for the geocoding service
        timeout: Timeout in seconds for the geocoding request
        
    Returns:
        Dictionary with location information
    """
    try:
        # Validate coordinates
        if len(coordinates) != 2:
            raise ValueError("Coordinates must be a list of [lat, lon]")
        
        lat, lon = coordinates
        if not (-90 <= lat <= 90):
            raise ValueError(f"Invalid latitude: {lat}")
        if not (-180 <= lon <= 180):
            raise ValueError(f"Invalid longitude: {lon}")
        
        # Get user agent from environment or use default
        if not user_agent:
            user_agent = os.getenv('NOMINATIM_USER_AGENT', 'memories-dev-app')
        
        # Initialize geocoder
        geolocator = Nominatim(user_agent=user_agent)
        
        # Reverse geocode the coordinates
        location = geolocator.reverse(f"{lat}, {lon}", timeout=timeout)
        
        if location:
            return {
                'address': location.address,
                'coordinates': coordinates,
                'latitude': lat,
                'longitude': lon,
                'raw': location.raw
            }
        else:
            logger.warning(f"Could not reverse geocode coordinates: {coordinates}")
            return {
                'coordinates': coordinates,
                'address': None,
                'error': 'Address not found'
            }
    
    except Exception as e:
        logger.error(f"Reverse geocoding error for coordinates {coordinates}: {e}")
        return {
            'coordinates': coordinates,
            'address': None,
            'error': str(e)
        } 