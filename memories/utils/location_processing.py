"""
Location processing module for handling location filtering, geocoding, and location-based operations.
"""

from typing import Dict, Any, Optional, Union, List, Tuple, Set
import logging
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from geopy.location import Location

from memories.utils.location_utils import normalize_location, is_valid_coordinates, extract_coordinates
from memories.utils.location_tools import (
    filter_by_distance,
    filter_by_type,
    sort_locations_by_distance,
    get_bounding_box,
    cluster_locations
)
from memories.models.load_model import LoadModel
from memories.models.model_base import BaseModel

class LocationProcessing(BaseModel):
    """Module for handling location processing, filtering, and geocoding operations."""
    
    def __init__(self, model: Optional[LoadModel] = None):
        """Initialize the Location Processing module.
        
        Args:
            model (Optional[LoadModel]): Model instance for processing
        """
        super().__init__(name="location_processing", model=model)
        self.logger = logging.getLogger(__name__)
        self.geolocator = Nominatim(user="memories_module")
    
    def get_capabilities(self) -> List[str]:
        """Return a list of high-level capabilities this module provides."""
        return [
            "Filter locations by distance from a point",
            "Filter locations by type",
            "Sort locations by distance",
            "Calculate bounding box for locations",
            "Cluster nearby locations",
            "Normalize location data",
            "Validate and extract coordinates",
            "Geocode addresses to coordinates",
            "Reverse geocode coordinates to addresses"
        ]
    
    def requires_model(self) -> bool:
        """This module requires a model for processing."""
        return True
    
    def _initialize_tools(self):
        """Initialize the location processing tools."""
        # External location processing tools
        self.register_tool(
            "filter_by_distance",
            filter_by_distance,
            "Filter locations within a certain radius of a center point",
            {"locations", "center", "radius_km"}
        )
        self.register_tool(
            "filter_by_type",
            filter_by_type,
            "Filter locations by their type",
            {"locations", "location_types"}
        )
        self.register_tool(
            "sort_by_distance",
            sort_locations_by_distance,
            "Sort locations by distance from a reference point",
            {"locations", "reference_point"}
        )
        self.register_tool(
            "get_bounding_box",
            get_bounding_box,
            "Calculate the bounding box containing all locations",
            {"locations"}
        )
        self.register_tool(
            "cluster_locations",
            cluster_locations,
            "Cluster locations that are within a maximum distance of each other",
            {"locations", "max_distance_km"}
        )
        
        # Location utility tools
        self.register_tool(
            "normalize_location",
            normalize_location,
            "Normalize location information into a standard format",
            {"location", "location_type"}
        )
        self.register_tool(
            "validate_coordinates",
            is_valid_coordinates,
            "Check if a string contains valid coordinates",
            {"location"}
        )
        self.register_tool(
            "extract_coordinates",
            extract_coordinates,
            "Extract coordinates from text if present",
            {"text"}
        )
        self.register_tool(
            "geocode",
            self._geocode,
            "Convert an address to coordinates with full location details",
            {"address"}
        )
        self.register_tool(
            "reverse_geocode",
            self._reverse_geocode,
            "Convert coordinates to an address with full location details",
            {"coordinates"}
        )
    
    async def process(self, goal: str, **kwargs) -> Dict[str, Any]:
        """
        Process a location-related goal.
        
        Args:
            goal: The goal to achieve (e.g., "find locations within 5km of point")
            **kwargs: Arguments needed by the tools
            
        Returns:
            Dict containing processing results
        """
        # Create a plan based on the goal
        plan = self.plan(goal)
        
        if not plan:
            return {
                "status": "error",
                "error": f"No tools available to handle goal: {goal}",
                "data": None
            }
        
        # Execute the plan
        return self.execute_plan(**kwargs)
    
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