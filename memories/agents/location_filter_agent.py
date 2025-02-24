import logging
import os
from typing import Dict, Any, List
from memories.agents import BaseAgent

class LocationFilterAgent(BaseAgent):
    """Agent specialized in filtering location-based data."""
    
    def __init__(self, memory_store: Any = None):
        """Initialize the Location Filter Agent."""
        super().__init__(memory_store=memory_store, name="location_filter_agent")

    async def process(self, *args, **kwargs) -> Dict[str, Any]:
        """Process data using this agent.
        
        This method implements the required abstract method from BaseAgent.
        It serves as a wrapper around filter_by_location.
        
        Args:
            location_type: String specifying the type of location
            
        Returns:
            Dict[str, Any]: Processing results
        """
        location_type = kwargs.get('location_type', args[0] if args else None)
        
        if not location_type:
            return {
                "status": "error",
                "error": "No location type provided",
                "data": None
            }
            
        try:
            fields = self.filter_by_location(location_type)
            return {
                "status": "success",
                "data": {
                    "fields": fields,
                    "location_type": location_type
                },
                "error": None
            }
        except Exception as e:
            self.logger.error(f"Error in process: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "data": None
            }

    def filter_by_location(self, location_type: str) -> List[str]:
        """
        Filter available fields based on the location type.
        
        Args:
            location_type (str): The type of location extracted (e.g., 'point', 'city').
        
        Returns:
            List[str]: List of relevant field names.
        """
        try:
            # Example filtering logic based on location_type
            if location_type.lower() == "point":
                return ["id", "landuse", "geometry"]
            elif location_type.lower() == "city":
                return ["id", "population", "name"]
            elif location_type.lower() == "state":
                return ["id", "name", "area"]
            elif location_type.lower() == "country":
                return ["id", "name", "gdp"]
            elif location_type.lower() == "address":
                return ["id", "street", "city", "zipcode"]
            elif location_type.lower() == "polygon":
                return ["id", "name", "coordinates"]
            else:
                self.logger.warning(f"No filtering rule defined for location type: {location_type}")
                return []
        except Exception as e:
            self.logger.error(f"Error in filter_by_location: {str(e)}")
            return []

    def get_filtered_values(self, location_info: Dict[str, Any], 
                          value_keys: List[str] = None) -> List[Any]:
        """
        Get specific values from filtered metadata.
        
        Args:
            location_info (Dict[str, Any]): Dictionary containing location and location_type
            value_keys (List[str], optional): List of keys to extract from metadata. 
                                            If None, returns entire metadata entries.
            
        Returns:
            List[Any]: List of extracted values or complete metadata entries
        """
        try:
            filtered_metadata = self.filter_by_location(location_info)
            
            if not value_keys:
                return filtered_metadata
            
            # Extract specified values from filtered metadata
            extracted_values = []
            for metadata in filtered_metadata:
                values = {}
                for key in value_keys:
                    if key in metadata:
                        values[key] = metadata[key]
                if values:
                    extracted_values.append(values)
                    
            return extracted_values
            
        except Exception as e:
            self.logger.error(f"Error getting filtered values: {str(e)}")
            return []

    def requires_model(self) -> bool:
        """This agent does not require a model."""
        return False 