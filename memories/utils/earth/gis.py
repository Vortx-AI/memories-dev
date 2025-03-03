"""
GIS module for handling geographic information system operations.
"""

import os
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
import logging
from memories.models.load_model import LoadModel
from memories.models.model_base import BaseModel

# Load environment variables
load_dotenv()

class GIS(BaseModel):
    """Module specialized in GIS operations."""
    
    def __init__(self, memory_store: Any = None, model: Optional[LoadModel] = None):
        """Initialize the GIS module with API capabilities and FAISS storage.
        
        Args:
            memory_store: Optional memory store for persistence
            model: Optional model for ML operations
        """
        super().__init__(memory_store=memory_store, name="gis", model=model)
        
        
        # Initialize FAISS storage
        project_root = os.getenv("PROJECT_ROOT")
        if project_root is None:
            raise ValueError("PROJECT_ROOT environment variable is not set")
        #self.storage = FAISSStorage(directory=os.path.join(project_root, "faiss_data"))
    
    def get_api_for_field(self, field: str) -> str:
        """
        Determine which API to use for a specific field using FAISS similarity search
        
        Args:
            field: The field name to match against stored values
            
        Returns:
            api_id: The determined API ID ("1", "2", or "3")
        """
        try:
            results = self.storage.query_similar_with_metadata(
                query=field,
                limit=1
            )
            
            if results and len(results) > 0:
                node, score = results[0]
                api_id = node.metadata.get("api_id")
                
                # Handle case where api_id is a list
                if isinstance(api_id, list):
                    # Use the first API in the list
                    chosen_api = api_id[0]
                    self.logger.info(f"Matched field '{field}' to multiple APIs {api_id}, using API {chosen_api} (score: {score:.2f})")
                    return chosen_api
                else:
                    self.logger.info(f"Matched field '{field}' to API {api_id} (score: {score:.2f})")
                    return api_id
            
            self.logger.warning(f"No API match found for field '{field}', defaulting to API 3")
            return "3"
            
        except Exception as e:
            self.logger.error(f"Error determining API: {e}")
            return "3"
    
    def query_field(self, lat: float, lon: float, field: str) -> Any:
        """
        Query a specific field using the appropriate API
        
        Args:
            lat: Latitude
            lon: Longitude
            field: Field name to query
            
        Returns:
            Value for the requested field
        """
        api_id = self.get_api_for_field(field)
        
        try:
            if api_id == "1":
                response = self.tools.reverse_geocode(lat, lon)
                self.logger.info(f"API 1 Response for field '{field}': {response.data}")
                if response.status == "success":
                    # First check in address dictionary
                    address_data = response.data.get('address', {})
                    if field in address_data:
                        value = address_data[field]
                    # Then check in main response
                    elif field in response.data:
                        value = response.data[field]
                    # Special handling for display_name
                    elif field == 'address':
                        value = response.data.get('display_name')
                    else:
                        value = None
                    self.logger.info(f"Extracted value for '{field}': {value}")
                    return value
                
            elif api_id == "2":
                response = self.tools.forward_geocode(f"{lat},{lon}")
                self.logger.info(f"API 2 Response for field '{field}': {response.data}")
                if response.status == "success" and response.data:
                    first_result = response.data[0]
                    # Check in address if it exists
                    address_data = first_result.get('address', {})
                    if field in address_data:
                        value = address_data[field]
                    # Then check in main response
                    elif field in first_result:
                        value = first_result[field]
                    else:
                        value = None
                    self.logger.info(f"Extracted value for '{field}': {value}")
                    return value
                
            else:  # api_id == "3" or default
                response = self.tools.query_overpass(lat, lon, {"term": field}, 500)
                self.logger.info(f"API 3 Response for field '{field}': {response.data}")
                if response.status == "success":
                    features = response.data.get('features', [])
                    if features:
                        # First check in tags
                        tags = features[0].get('tags', {})
                        if field in tags:
                            value = tags[field]
                        # Then check in properties
                        elif field in features[0].get('properties', {}):
                            value = features[0]['properties'][field]
                        else:
                            value = None
                        self.logger.info(f"Extracted value for '{field}': {value}")
                        return value
            
            self.logger.warning(f"No value found for field '{field}' using API {api_id}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error querying field {field} with API {api_id}: {e}")
            return None

    def get_location_data(self, lat: float, lon: float, required_fields: List[str]) -> Dict[str, Any]:
        """
        Get data for multiple fields at a location
        
        Args:
            lat: Latitude
            lon: Longitude
            required_fields: List of field names to query
            
        Returns:
            Dictionary mapping field names to their values
        """
        self.logger.info(f"Querying location ({lat}, {lon}) for fields: {required_fields}")
        result = {}
        
        for field in required_fields:
            self.logger.info(f"\nProcessing field: {field}")
            value = self.query_field(lat, lon, field)
            result[field] = value if value is not None else ""
            self.logger.info(f"Final result for '{field}': {result[field]}")
            
        self.logger.info(f"Complete results: {result}")
        return result

    def determine_api(self, context: str) -> str:
        """
        Determine which API to use based on context using FAISS similarity search
        
        Args:
            context: The context string to match against stored values
            
        Returns:
            api_id: The determined API ID ("1", "2", or "3")
        """
        try:
            # Query similar values with metadata
            results = self.storage.query_similar_with_metadata(
                query=context,
                limit=1  # Get the closest match
            )
            
            if results and len(results) > 0:
                node, score = results[0]
                api_id = node.metadata.get("api_id")
                self.logger.info(f"Matched context '{context}' to API {api_id} (score: {score:.2f})")
                return api_id
            
            # Default to API 3 (Overpass) if no match found
            self.logger.warning(f"No API match found for context '{context}', defaulting to API 3")
            return "3"
            
        except Exception as e:
            self.logger.error(f"Error determining API: {e}")
            return "3"  # Default to API 3 on error
    
    async def process(self, *args, **kwargs) -> Dict[str, Any]:
        """Process data using this module.
        
        This method implements the required abstract method from BaseModel.
        It serves as a wrapper around query method.
        
        Args:
            lat: Latitude
            lon: Longitude
            context: Dictionary containing search context
            
        Returns:
            Dict[str, Any]: Processing results
        """
        lat = kwargs.get('lat')
        lon = kwargs.get('lon')
        context = kwargs.get('context', {})
        
        if lat is None or lon is None:
            return {
                "status": "error",
                "error": "Latitude and longitude are required",
                "data": None
            }
            
        try:
            result = await self.query(lat, lon, context)
            return {
                "status": "success" if result.get('status') != 'error' else "error",
                "data": result if result.get('status') != 'error' else None,
                "error": result.get('error')
            }
        except Exception as e:
            self.logger.error(f"Error in process: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "data": None
            }

    async def query(self, lat: float, lon: float, context: Dict[str, str]) -> Dict[str, Any]:
        """
        Query location based on context using the appropriate API
        
        Args:
            lat: Latitude
            lon: Longitude
            context: Dictionary containing search context
            
        Returns:
            Response data from the appropriate API
        """
        try:
            # Determine which API to use based on context
            api_id = self.determine_api(str(context))
            
            # Query the appropriate API
            if api_id == "1":
                response = self.tools.reverse_geocode(lat, lon)
            elif api_id == "2":
                response = self.tools.forward_geocode(f"{lat},{lon}")
            else:  # api_id == "3" or default
                response = self.tools.query_overpass(lat, lon, context, 500)
            
            # Format the response
            if response.status == "success":
                return {
                    "status": "success",
                    "data": response.data,
                    "api_used": api_id,
                    "error": None
                }
            else:
                return {
                    "status": "error",
                    "error": response.error,
                    "api_used": api_id,
                    "data": None
                }
                
        except Exception as e:
            self.logger.error(f"Error in query: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "api_used": None,
                "data": None
            }

    def format_response(self, response_data: Dict[str, Any]) -> str:
        """
        Format the response data into a readable string
        
        Args:
            response_data: Dictionary containing response data
            
        Returns:
            Formatted string representation of the data
        """
        try:
            if response_data.get("status") == "error":
                return f"Error: {response_data.get('error', 'Unknown error')}"
            
            data = response_data.get("data", {})
            api_used = response_data.get("api_used", "unknown")
            
            if not data:
                return "No data found"
            
            # Format based on API type
            if api_used == "1":
                return f"Location: {data.get('display_name', 'Unknown')}"
            elif api_used == "2":
                if isinstance(data, list) and data:
                    return f"Location: {data[0].get('display_name', 'Unknown')}"
                return "No location data found"
            else:  # api_used == "3" or default
                features = data.get("features", [])
                if not features:
                    return "No features found"
                    
                result = []
                for feature in features[:5]:  # Limit to first 5 features
                    name = feature.get("properties", {}).get("name", "Unnamed")
                    tags = feature.get("tags", {})
                    result.append(f"- {name}: {tags}")
                
                return "\n".join(result)
                
        except Exception as e:
            self.logger.error(f"Error formatting response: {str(e)}")
            return f"Error formatting response: {str(e)}"

    def requires_model(self) -> bool:
        """This module does not require a model."""
        return False 