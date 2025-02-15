from typing import Dict, Union, Optional, Any
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from geopy.location import Location
import logging

class GeoCoderAgent:
    """Agent for handling geocoding and reverse geocoding operations."""
    
    def __init__(self):
        """Initialize the geocoder agent with Nominatim."""
        self.geolocator = Nominatim(user_agent="my_agent")
        self.logger = logging.getLogger(__name__)

    def process_location(self, location: Union[str, tuple], location_type: str = "address") -> Dict[str, Any]:
        """
        Process location data based on type (coordinates or address).
        
        Args:
            location: Either a string address or tuple of (latitude, longitude)
            location_type: Either "address" or "coordinates"
            
        Returns:
            Dictionary containing location details including coordinates, address, and raw data
        """
        try:
            if location_type == "coordinates":
                if isinstance(location, str):
                    # Convert string representation of coordinates to tuple
                    lat, lon = map(float, location.strip('()').split(','))
                    location = (lat, lon)
                return self._reverse_geocode(location)
            else:
                return self._geocode(location)
        except Exception as e:
            self.logger.error(f"Error processing location: {str(e)}")
            return {
                "coordinates": None,
                "address": None,
                "raw": None,
                "error": str(e)
            }

    def _extract_location_data(self, location: Location) -> Dict[str, Any]:
        """Extract all relevant data from a Location object."""
        if not location:
            return None
        
        return {
            "latitude": location.latitude,
            "longitude": location.longitude,
            "address": location.address,
            "altitude": getattr(location, 'altitude', None),
            "raw": location.raw,
            # Additional OSM specific fields
            "osm_type": location.raw.get('osm_type'),
            "osm_id": location.raw.get('osm_id'),
            "place_id": location.raw.get('place_id'),
            "type": location.raw.get('type'),
            "class": location.raw.get('class'),
            "importance": location.raw.get('importance'),
            "display_name": location.raw.get('display_name'),
            # Extract address components if available
            "address_components": location.raw.get('address', {})
        }

    def _geocode(self, address: str) -> Dict[str, Any]:
        """Convert address to coordinates with full location details."""
        try:
            location = self.geolocator.geocode(address, exactly_one=True)
            if location:
                location_data = self._extract_location_data(location)
                return {
                    "coordinates": (location.latitude, location.longitude),
                    "address": location.address,
                    "details": location_data,
                    "error": None
                }
            return {
                "coordinates": None,
                "address": None,
                "details": None,
                "error": "Location not found"
            }
        except GeocoderTimedOut:
            return self._handle_timeout("geocoding")

    def _reverse_geocode(self, coordinates: tuple) -> Dict[str, Any]:
        """Convert coordinates to address with full location details."""
        try:
            location = self.geolocator.reverse(coordinates)
            if location:
                location_data = self._extract_location_data(location)
                return {
                    "coordinates": coordinates,
                    "address": location.address,
                    "details": location_data,
                    "error": None
                }
            return {
                "coordinates": coordinates,
                "address": None,
                "details": None,
                "error": "Address not found"
            }
        except GeocoderTimedOut:
            return self._handle_timeout("reverse geocoding")

    def _handle_timeout(self, operation: str) -> Dict[str, Any]:
        """Handle timeout errors."""
        error_msg = f"Timeout during {operation} operation"
        self.logger.error(error_msg)
        return {
            "coordinates": None,
            "address": None,
            "details": None,
            "error": error_msg
        } 