from typing import Dict, Any
from dotenv import load_dotenv
import logging
import os
from memories.agents.agent_query_classification import AgentQueryClassification
from memories.agents.agent_context import AgentContext
from memories.core.memory import MemoryStore

# Load environment variables
load_dotenv()

class Agent:
    def __init__(self, query: str, load_model: Any, memory_store: Any = None):
        """
        Initialize the Agent system.
        
        Args:
            query (str): The user's query.
            load_model (Any): The initialized model instance.
            memory_store (Any): The initialized memory store with FAISS index.
        """
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        self.query = query
        self.load_model = load_model
        self.memory_store = memory_store
        
        # Retrieve PROJECT_ROOT from environment variables
        project_root = os.getenv("PROJECT_ROOT")
        if project_root is None:
            raise ValueError("PROJECT_ROOT environment variable is not set")

    def search_similar_locations(self, data_type: str, location_info: Dict[str, Any], top_k: int = 5) -> list:
        """
        Search for similar locations in the FAISS index.
        
        Args:
            data_type (str): Type of data being searched (e.g., 'cafes', 'restaurants')
            location_info (Dict): Location information including coordinates
            top_k (int): Number of results to return
            
        Returns:
            list: List of similar locations with scores
        """
        try:
            if not self.memory_store:
                return []
                
            # Get normalized coordinates if available
            coordinates = None
            if location_info and 'normalized' in location_info:
                norm = location_info['normalized']
                if norm.get('coordinates'):
                    coordinates = norm['coordinates']
            
            # Perform similarity search
            search_results = self.memory_store.search_memories(
                query=data_type,
                coordinates=coordinates,
                top_k=top_k
            )
            
            return search_results
            
        except Exception as e:
            self.logger.error(f"Error in similarity search: {str(e)}")
            return []

    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a query using the query classification agent.
        
        Args:
            query (str): The user's query.
        
        Returns:
            Dict[str, Any]: The response containing the classification and result.
        """
        try:
            print("="*50)
            print(f"Starting query processing: {query}")
            print("="*50)
            
            # Initialize and use the query classification agent
            classification_agent = AgentQueryClassification(query, self.load_model)
            result = classification_agent.process_query()
            
            # Only process with context agent if classification is L1_2
            if result.get('classification') == 'L1_2':
                # Create context agent with the query
                context_agent = AgentContext(query, self.load_model)
                # Get context information
                context_result = context_agent.process_query()
                
                # Merge the context information with the classification result
                result.update({
                    'data_type': context_result.get('data_type'),
                    'location_details': context_result.get('location_info')
                })
                
                # Perform similarity search if we have a memory store
                if self.memory_store and result.get('data_type') and result.get('location_details'):
                    similar_locations = self.search_similar_locations(
                        data_type=result['data_type'],
                        location_info=result['location_details']
                    )
                    result['similar_locations'] = similar_locations
                    
            # For N and L0, just return the classification result directly
            elif result.get('classification') in ['N', 'L0']:
                # The response should already be in the result
                pass
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in process_query: {str(e)}")
            return {
                "query": query,
                "classification": "ERROR",
                "explanation": f"Error: {str(e)}"
            }

    def run(self, query: str = None) -> Dict[str, Any]:
        """
        Run the agent system.
        
        Args:
            query (str, optional): Query string. If None, will use the query from initialization.
        
        Returns:
            Dict[str, Any]: Dictionary containing the response.
        """
        try:
            if query is None:
                query = self.query
            
            return self.process_query(query)
        except Exception as e:
            self.logger.error(f"Error in run: {str(e)}")
            return {
                "query": query, 
                "classification": "ERROR",
                "explanation": f"Error: {str(e)}"
            }

def main():
    """
    Main function to run the agent directly.
    Example usage: python3 agent.py
    """
    from memories.models.load_model import LoadModel
    
    # Load environment variables
    load_dotenv()
    
    # Initialize the model
    load_model = LoadModel(
        use_gpu=True,
        model_provider="deepseek-ai",
        deployment_type="deployment",
        model_name="deepseek-coder-1.3b-base"
    )
    
    # Initialize memory store with OSM data connectors
    memory_store = MemoryStore()
    
    # Get the project root path
    project_root = os.getenv("PROJECT_ROOT")
    osm_data_path = os.path.join(project_root, "location_data", "osm_data")
    
    # Define artifacts (changed from set to list)
    artifacts = {
        "osm_data": ["points", "lines", "multipolygons"]
    }
    
    # Create the OSM data directory if it doesn't exist
    os.makedirs(osm_data_path, exist_ok=True)
    
    # Print the paths that will be used
    print(f"[Agent] Looking for OSM data in: {osm_data_path}")
    
    memories = memory_store.create_memories(
        model=load_model,
        location=location,
        time_range=time_range,
        artifacts=artifacts,  # Now using dict with lists instead of sets
        data_connectors=[
            {
                "name": "india_points",
                "type": "parquet",
                "file_path": os.path.join(osm_data_path, "india_points.parquet")
            },
            {
                "name": "india_lines",
                "type": "parquet",
                "file_path": os.path.join(osm_data_path, "india_lines.parquet")
            },
            {
                "name": "india_multipolygons",
                "type": "parquet",
                "file_path": os.path.join(osm_data_path, "india_multipolygons.parquet")
            }
        ]
    )

    
    
    # Test different types of queries
    test_queries = [
        "How do I write a Python function?",
        "What is the capital of France?",
        "Find restaurants near Central Park",
        "What cafes are within 2km of my current location?"
    ]
    
    # Initialize and run the agent for each query
    for query in test_queries:
        print("\n" + "="*50)
        print(f"Testing query: {query}")
        
        agent = Agent(query=query, load_model=load_model, memory_store=memory_store)
        result = agent.process_query(query)
        
        print("\nResults:")
        print(f"Classification: {result.get('classification', '')}")
        
        # For N and L0 classifications, show the direct model response
        if result.get('classification') in ['N', 'L0'] and 'response' in result:
            print(f"Answer: {result['response']}")
            print(f"Explanation: {result.get('explanation', '')}")
        # For L1_2 classification, show detailed information
        elif result.get('classification') == 'L1_2':
            print("\nDetailed Information:")
            print(f"Data Type: {result.get('data_type', '')}")
            if 'location_details' in result:
                loc_info = result['location_details']
                print("\nLocation Information:")
                print(f"Location: {loc_info.get('location', '')}")
                print(f"Location Type: {loc_info.get('location_type', '')}")
                if 'normalized' in loc_info:
                    norm = loc_info['normalized']
                    print("\nNormalized Location:")
                    print(f"Type: {norm.get('type', '')}")
                    if norm.get('coordinates'):
                        coords = norm['coordinates']
                        print(f"Coordinates: {coords.get('lat')}, {coords.get('lon')}")
            
            # Show similar locations if available
            if 'similar_locations' in result and result['similar_locations']:
                print("\nSimilar Locations:")
                for idx, location in enumerate(result['similar_locations'], 1):
                    print(f"\n{idx}. Score: {location.get('score', 'N/A')}")
                    print(f"   Name: {location.get('name', 'N/A')}")
                    print(f"   Type: {location.get('type', 'N/A')}")
                    if 'coordinates' in location:
                        print(f"   Coordinates: {location['coordinates']}")
            
            print(f"\nExplanation: {result.get('explanation', '')}")
        # For errors or unexpected cases
        else:
            print(f"Explanation: {result.get('explanation', '')}")

if __name__ == "__main__":
    main()

