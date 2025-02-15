import os
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
import logging
from .agentic_tool import AgenticTools, APIResponse, APIType
from .memories_index import FAISSStorage

# Load environment variables
load_dotenv()

class GISAgent:
    def __init__(self, model: str = None):
        """Initialize the GIS Agent with API capabilities and FAISS storage.
        
        Args:
            model (str, optional): The model to use for GIS operations. Defaults to None.
        """
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        self.model = model
        self.tools = AgenticTools()
        
        # Initialize FAISS storage
        project_root = os.getenv("PROJECT_ROOT")
        if project_root is None:
            raise ValueError("PROJECT_ROOT environment variable is not set")
        self.storage = FAISSStorage(directory=os.path.join(project_root, "faiss_data"))
    
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
    
    def query(self, lat: float, lon: float, context: Dict[str, str]) -> Dict[str, Any]:
        """
        Query location based on context using the appropriate API
        
        Args:
            lat: Latitude
            lon: Longitude
            context: Dictionary containing search context
            
        Returns:
            Response data from the appropriate API
        """
        # Get the context value
        context_value = context.get('term', '')
        
        # Determine which API to use
        api_id = self.determine_api(context_value)
        
        # Call the appropriate API based on api_id
        if api_id == "1":
            # Reverse geocoding
            response = self.tools.reverse_geocode(lat, lon)
            return {
                'status': response.status,
                'api_id': APIType.NOMINATIM_REVERSE.value,
                'data': response.data,
                'error': response.error
            }
            
        elif api_id == "2":
            # Forward geocoding
            response = self.tools.forward_geocode(context_value)
            return {
                'status': response.status,
                'api_id': APIType.NOMINATIM_SEARCH.value,
                'data': response.data,
                'error': response.error
            }
            
        else:  # api_id == "3" or default
            # Overpass query
            response = self.tools.query_overpass(lat, lon, context, 500)
            if response.status == "error":
                return {
                    'status': 'error',
                    'error': response.error,
                    'api_id': APIType.OVERPASS.value,
                    'query': {
                        'lat': lat,
                        'lon': lon,
                        'term': context_value
                    }
                }
            return response.data
    
    def format_response(self, response_data: Dict[str, Any]) -> str:
        """Format the API response into a readable string"""
        if response_data.get('status') == 'error':
            return f"Error: {response_data.get('error')}"
        
        api_id = response_data.get('api_id')
        
        if api_id == APIType.NOMINATIM_REVERSE.value:
            # Format reverse geocoding response
            address = response_data.get('data', {}).get('address', {})
            return f"Location: {', '.join(str(v) for v in address.values() if v)}"
            
        elif api_id == APIType.NOMINATIM_SEARCH.value:
            # Format forward geocoding response
            places = response_data.get('data', [])
            if not places:
                return "No locations found"
            return "\n".join([f"- {place.get('display_name', '')}" for place in places[:3]])
            
        else:  # APIType.OVERPASS.value
            # Format Overpass response
            features = response_data.get('features', [])
            if not features:
                return "No features found in the specified area"
            
            response_parts = [f"Found {len(features)} features nearby:"]
            for feature in features:
                feature_type = feature.get('type', '')
                tags = feature.get('tags', {})
                location = feature.get('location', {})
                
                feature_desc = f"\n- {feature_type.capitalize()}"
                if tags:
                    for key, value in tags.items():
                        feature_desc += f"\n  * {key}: {value}"
                if location:
                    feature_desc += f"\n  * location: {location.get('lat')}, {location.get('lon')}"
                
                response_parts.append(feature_desc)
            
            return "\n".join(response_parts)
