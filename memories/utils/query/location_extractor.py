from typing import Dict, Any, Optional

class LocationExtractor:
    def __init__(self, load_model: Any):
        """
        Initialize the Location Extractor.
        
        Args:
            load_model (Any): The initialized model instance
        """
        self.load_model = load_model

    def extract_query_info(self, query: str) -> Dict[str, Any]:
        """
        Extract data type and location information from a query.
        
        Args:
            query (str): The user's query
            
        Returns:
            Dict containing data type and location information
        """
        try:
            # Extract data type being requested
            data_type_prompt = f"""From the following query, what type of data or information is being requested?
            Examples:
            "Find restaurants near Central Park" -> restaurants
            "What is the weather in London?" -> weather
            "Show me hotels within 5km of the Eiffel Tower" -> hotels
            "What is the population density in Manhattan?" -> population density
            
            Query: {query}
            
            Return only the type of data/information being requested, as a single word or short phrase."""
            
            data_type = self.load_model.get_response(data_type_prompt).strip()
            
            # Extract location and its type
            location_prompt = f"""From the following query, extract:
            1. The location mentioned
            2. The type of location (coordinates, address, landmark, city, state, country, etc.)
            
            Examples:
            "Find cafes near 40.7128, -74.0060" -> Location: 40.7128, -74.0060 | Type: coordinates
            "Show restaurants in Manhattan" -> Location: Manhattan | Type: city district
            "What's the weather at the Eiffel Tower?" -> Location: Eiffel Tower | Type: landmark
            
            Query: {query}
            
            Return in format: Location: <location> | Type: <type>"""
            
            location_info = self.load_model.get_response(location_prompt).strip()
            
            # Parse location response
            try:
                location_parts = location_info.split("|")
                location = location_parts[0].replace("Location:", "").strip()
                location_type = location_parts[1].replace("Type:", "").strip()
            except:
                location = location_info
                location_type = "unknown"
            
            return {
                "data_type": data_type,
                "location_info": {
                    "location": location,
                    "location_type": location_type
                }
            }
            
        except Exception as e:
            return {
                "error": f"Error extracting information: {str(e)}",
                "data_type": None,
                "location_info": None
            }

    def is_valid_coordinates(self, location: str) -> bool:
        """
        Check if the location string contains valid coordinates.
        
        Args:
            location (str): The location string to check
            
        Returns:
            bool: True if valid coordinates, False otherwise
        """
        try:
            # Remove any whitespace and split by comma
            parts = location.replace(" ", "").split(",")
            if len(parts) != 2:
                return False
                
            # Try to convert to float
            lat, lon = float(parts[0]), float(parts[1])
            
            # Check if within valid range
            return -90 <= lat <= 90 and -180 <= lon <= 180
        except:
            return False

    def normalize_location(self, location: str, location_type: str) -> Dict[str, Any]:
        """
        Normalize the location information based on its type.
        
        Args:
            location (str): The location string
            location_type (str): The type of location
            
        Returns:
            Dict containing normalized location information
        """
        try:
            normalized = {
                "original": location,
                "type": location_type.lower(),
                "coordinates": None
            }
            
            # If it's already coordinates, validate and format
            if location_type.lower() == "coordinates":
                if self.is_valid_coordinates(location):
                    lat, lon = map(float, location.replace(" ", "").split(","))
                    normalized["coordinates"] = {"lat": lat, "lon": lon}
            
            return normalized
            
        except Exception as e:
            return {
                "error": f"Error normalizing location: {str(e)}",
                "original": location,
                "type": location_type,
                "coordinates": None
            }

def main():
    """Test the LocationExtractor"""
    from memories.models.load_model import LoadModel
    
    # Initialize the model
    load_model = LoadModel(
        use_gpu=True,
        model_provider="deepseek-ai",
        deployment_type="deployment",
        model_name="deepseek-coder-1.3b-base"
    )
    
    # Initialize the extractor
    extractor = LocationExtractor(load_model)
    
    # Test queries
    test_queries = [
        "Find restaurants near Central Park",
        "What's the weather at 40.7128, -74.0060",
        "Show me hotels in Manhattan",
        "What's the population density of New York City"
    ]
    
    # Test extraction
    for query in test_queries:
        print("\n" + "="*50)
        print(f"Query: {query}")
        result = extractor.extract_query_info(query)
        print("\nExtracted Information:")
        print(f"Data Type: {result.get('data_type')}")
        if result.get('location_info'):
            loc_info = result['location_info']
            print(f"Location: {loc_info.get('location')}")
            print(f"Location Type: {loc_info.get('location_type')}")
            
            # Test normalization
            normalized = extractor.normalize_location(
                loc_info.get('location'),
                loc_info.get('location_type')
            )
            print("\nNormalized Location:")
            print(normalized)

if __name__ == "__main__":
    main()
