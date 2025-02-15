from typing import Dict, Any, Optional
import logging
from memories.utils.query.location_extractor import LocationExtractor

class AgentContext:
    def __init__(self, query: str, load_model: Any):
        """
        Initialize the Context Agent with query and model.
        
        Args:
            query (str): The user's query
            load_model (Any): The initialized model instance
        """
        self.query = query
        self.load_model = load_model
        self.logger = logging.getLogger(__name__)
        
        # Initialize location extractor
        self.location_extractor = LocationExtractor(load_model)

    def process_query(self) -> Dict[str, Any]:
        """
        Process the query to extract context information.
        
        Returns:
            Dict containing extracted information about data type and location
        """
        try:
            self.logger.info(f"Processing query for context: {self.query}")
            
            # Extract information using location extractor
            extracted_info = self.location_extractor.extract_query_info(self.query)
            
            # Normalize location if present
            if extracted_info.get('location_info'):
                location = extracted_info['location_info'].get('location')
                location_type = extracted_info['location_info'].get('location_type')
                
                if location and location_type:
                    normalized_location = self.location_extractor.normalize_location(
                        location,
                        location_type
                    )
                    extracted_info['location_info']['normalized'] = normalized_location
            
            response = {
                "query": self.query,
                "data_type": extracted_info.get('data_type'),
                "location_info": extracted_info.get('location_info'),
                "status": "success"
            }
            
            self.logger.info(f"Successfully extracted context information")
            return response
            
        except Exception as e:
            self.logger.error(f"Error processing query context: {str(e)}")
            return {
                "query": self.query,
                "status": "error",
                "error": str(e)
            }

def main():
    """Test the Context Agent"""
    from memories.models.load_model import LoadModel
    
    # Initialize the model
    load_model = LoadModel(
        use_gpu=True,
        model_provider="deepseek-ai",
        deployment_type="deployment",
        model_name="deepseek-coder-1.3b-base"
    )
    
    # Test queries
    test_queries = [
        "Find restaurants near Central Park",
        "What's the weather at 40.7128, -74.0060",
        "Show me hotels in Manhattan",
        "What's the population density of New York City"
    ]
    
    # Process each query
    for query in test_queries:
        print("\n" + "="*50)
        print(f"Query: {query}")
        
        agent = AgentContext(query, load_model)
        result = agent.process_query()
        
        print("\nExtracted Context:")
        print(f"Status: {result.get('status')}")
        
        if result.get('status') == "success":
            print(f"Data Type: {result.get('data_type')}")
            if result.get('location_info'):
                loc_info = result['location_info']
                print("\nLocation Information:")
                print(f"Location: {loc_info.get('location')}")
                print(f"Type: {loc_info.get('location_type')}")
                if 'normalized' in loc_info:
                    print("\nNormalized Location:")
                    print(loc_info['normalized'])
        else:
            print(f"Error: {result.get('error')}")

if __name__ == "__main__":
    main()
