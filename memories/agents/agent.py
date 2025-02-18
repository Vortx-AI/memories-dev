from typing import Dict, Any
from dotenv import load_dotenv
import logging
import os
from memories.agents.agent_query_classification import AgentQueryClassification
from memories.agents.agent_context import AgentContext
from memories.agents.agent_L1 import Agent_L1
from memories.agents.agent_analyst import AgentAnalyst
from memories.core.memory import MemoryStore
from memories.utils.duckdb_queries import DuckDBQueryGenerator
import pandas as pd
from memories.agents.agent_code_executor import AgentCodeExecutor
from memories.utils.earth.run_kb_functions import execute_kb_function, validate_function_inputs
from memories.agents.response_agent import AgentResponse
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
import time
import re

# Load environment variables
load_dotenv()

class Agent:
    def __init__(self, query: str, load_model: Any, memory_store: MemoryStore, instance_id: str = None):
        """
        Initialize the Agent system.
        
        Args:
            query (str): The user's query.
            load_model (Any): The initialized model instance.
            memory_store (MemoryStore): The memory store instance.
            instance_id (str, optional): The instance ID for FAISS search.
        """
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        self.query = query
        self.load_model = load_model
        self.memory_store = memory_store
        self.instance_id = instance_id
        
        # Retrieve PROJECT_ROOT from environment variables
        project_root = os.getenv("PROJECT_ROOT")
        if project_root is None:
            raise ValueError("PROJECT_ROOT environment variable is not set")

        self.response_agent = AgentResponse(query, load_model)

        # Initialize Nominatim geocoder with a custom User-Agent
        self.geocoder = Nominatim(user_agent="memories_agent")

    def get_location_bbox(self, location: str, max_retries: int = 3) -> Dict[str, float]:
        """
        Get bounding box for a location using Nominatim.
        
        Args:
            location (str): Location string or coordinates to geocode
            max_retries (int): Maximum number of retry attempts
            
        Returns:
            Dict containing bounding box coordinates or None if not found
        """
        # Check if location is in coordinates format (lat,lon)
        coord_pattern = re.compile(r'^[-+]?([1-8]?\d(\.\d+)?|90(\.0+)?),\s*[-+]?(180(\.0+)?|((1[0-7]\d)|([1-9]?\d))(\.\d+)?)$')
        
        for attempt in range(max_retries):
            try:
                if coord_pattern.match(location.strip()):
                    # Parse coordinates
                    lat, lon = map(float, location.split(','))
                    # Create a small bounding box around the coordinates (approximately 1km)
                    delta = 0.009  # roughly 1km at the equator
                    bbox = {
                        'south': lat - delta,
                        'north': lat + delta,
                        'west': lon - delta,
                        'east': lon + delta
                    }
                else:
                    # Get location details from Nominatim
                    location_data = self.geocoder.geocode(location, exactly_one=True, timeout=10)
                    
                    if location_data and hasattr(location_data, 'raw'):
                        bbox_raw = location_data.raw.get('boundingbox')
                        if bbox_raw:
                            bbox = {
                                'south': float(bbox_raw[0]),
                                'north': float(bbox_raw[1]),
                                'west': float(bbox_raw[2]),
                                'east': float(bbox_raw[3])
                            }
                        else:
                            # If no bounding box, create one around the point
                            delta = 0.009
                            bbox = {
                                'south': location_data.latitude - delta,
                                'north': location_data.latitude + delta,
                                'west': location_data.longitude - delta,
                                'east': location_data.longitude + delta
                            }
                
                if bbox:
                    # Create WKT polygon from bbox
                    wkt_polygon = (
                        f"POLYGON(("
                        f"{bbox['west']} {bbox['south']},"
                        f"{bbox['east']} {bbox['south']},"
                        f"{bbox['east']} {bbox['north']},"
                        f"{bbox['west']} {bbox['north']},"
                        f"{bbox['west']} {bbox['south']}"
                        f"))"
                    )
                    return {'bbox': bbox, 'wkt_polygon': wkt_polygon}
                
                self.logger.warning(f"No bounding box found for location: {location}")
                return None
                
            except (GeocoderTimedOut, GeocoderUnavailable) as e:
                if attempt == max_retries - 1:
                    self.logger.error(f"Failed to geocode after {max_retries} attempts: {str(e)}")
                    return None
                time.sleep(1)  # Wait before retrying
                
            except Exception as e:
                self.logger.error(f"Error geocoding location: {str(e)}")
                return None

    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a query using multiple agents.
        """
        try:
            print("\n" + "="*80)
            print("QUERY PROCESSING PIPELINE")
            print("="*80)
            print(f"Input Query: {query}")
            print("="*80)

            #######################################################
            # Step 1: Query Classification Agent
            print("\n[Invoking Query Classification Agent]")
            print("-"*50)
            classification_agent = AgentQueryClassification(query, self.load_model)
            classification_result = classification_agent.process_query()
            
            print("Classification Agent Response:")
            print(f"• Classification: {classification_result.get('classification', '')}")
            print(f"• Explanation: {classification_result.get('explanation', '')}")
            if 'processing_hint' in classification_result:
                print(f"• Processing Hint: {classification_result.get('processing_hint', '')}")
            
            result = classification_result
            
            # Step 2: Context Agent (for both L1 and L1_2)
            if result.get('classification') in ['L1', 'L1_2','L2']:
                print("\n[Invoking Context Agent]")
                print("-"*50)
                context_agent = AgentContext(query, self.load_model)
                context_result = context_agent.process_query()
                
                # Extract location information
                location_info = context_result.get('location_info', {})
                location = 'unknown'
                coordinates = None
                
                if isinstance(location_info, dict):
                    normalized = location_info.get('normalized', {})
                    coordinates = normalized.get('coordinates', {})
                    location = normalized.get('location', 'unknown')
                    
                    # Try to get bounding box
                    location_query = None
                    if isinstance(coordinates, dict) and 'lat' in coordinates and 'lon' in coordinates:
                        location_query = f"{coordinates['lat']},{coordinates['lon']}"
                    elif location != 'unknown':
                        location_query = location
                    
                    if location_query:
                        print(f"\n[Getting Bounding Box for Location: {location_query}]")
                        print("-"*50)
                        bbox_result = self.get_location_bbox(location_query)
                        
                        if bbox_result:
                            bbox = bbox_result['bbox']
                            print("Bounding Box Found:")
                            print(f"• North: {bbox['north']}")
                            print(f"• South: {bbox['south']}")
                            print(f"• East: {bbox['east']}")
                            print(f"• West: {bbox['west']}")
                            
                            # Update result with bbox and WKT
                            result.update({
                                'bbox': bbox,
                                'wkt_polygon': bbox_result['wkt_polygon']
                            })
                        else:
                            print("No bounding box found for the location")
                
                # Update other location information
                result.update({
                    'data_type': context_result.get('data_type', ''),
                    'latitude': coordinates.get('lat', 0.0) if isinstance(coordinates, dict) else 0.0,
                    'longitude': coordinates.get('lon', 0.0) if isinstance(coordinates, dict) else 0.0,
                    'location_type': location_info.get('type', 'unknown') if isinstance(location_info, dict) else 'unknown',
                    'location': location
                })
            #######################################################
            
            # Get the AOI from the WKT polygon or use a default if not available
            aoi = bbox_result['wkt_polygon']
            print(bbox_result['bbox'])
            ############
            # Step 3: L1 Agent (if classification is L1)
            if result.get('classification') == 'L1':
                print("\n[Invoking L1 Agent - Similar Column Search]")
                print("-" * 50)
                
                if self.instance_id and result.get('data_type'):
                    # Use only the data type for column search
                    search_term = result['data_type']
                    l1_agent = Agent_L1(self.instance_id, search_term)
                    l1_result = l1_agent.process()
                    
                    print("L1 Agent Response:")
                    if l1_result["status"] == "success":
                        # Filter columns with distance < 0.5
                        similar_columns = [col for col in l1_result["similar_columns"] if col['distance'] < 0.5]
                        result['similar_columns'] = similar_columns
                        
                        if similar_columns:
                            print(f"\n• Searching columns for data type: {search_term}")
                            print("\n• Similar columns found:")
                            for col in similar_columns:
                                print(f"\n  Column: {col['column_name']}")
                                print(f"  File: {col['file_name']}")
                                print(f"  File Path: {col['file_path']}")
                                print(f"  Geometry: {col['geometry']}")
                                print(f"  Geometry Type: {col['geometry_type']}")
                                print(f"  Distance: {col['distance']:.4f}")
                            
                            # Continue with the best matching column
                            best_column = similar_columns[0]
                            # ... rest of the processing ...
                        else:
                            print("\nNo columns found with similarity distance < 0.5")
                            print("Falling back to model response...")
                            
                            # Get direct response from model as done in N and L0 cases
                            model_response = self.load_model.get_response(query)
                            return {
                                "query": query,
                                "classification": "L1",
                                "status": "fallback_to_model",
                                "explanation": "No sufficiently similar columns found (distance threshold: 0.5). Using model response instead.",
                                "response": model_response
                            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in process_query: {str(e)}")
            return {
                "query": query,
                "classification": "ERROR",
                "explanation": f"Error: {str(e)}",
                "response": f"An error occurred while processing your query: {str(e)}"
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
    from memories.core.memory import MemoryStore
    from memories.agents.agent_config import get_model_config
    
    # Get input from user
    query = "find water tanks near 12.9093124,77.6078977"
    #input("Enter your query: ")
    instance_id = "123937239372432"
    #input("Enter FAISS instance ID (or press Enter to skip): ")
    
    # Initialize model with get_model_config
    load_model, _ = get_model_config(
        use_gpu=True,
        model_provider="deepseek-ai",
        deployment_type="deployment",
        model_name="deepseek-coder-1.3b-base"
    )
    
    print(f"[Agent] Model initialized")
    
    # Initialize memory store
    memory_store = MemoryStore()
    
    # Initialize and run agent
    agent = Agent(
        query=query, 
        load_model=load_model,
        memory_store=memory_store,
        instance_id=instance_id if instance_id else None
    )
    
    agent.run()

if __name__ == "__main__":
    main()

def validate_function_inputs(function_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate the inputs for a given function.
    
    Args:
        function_name: Name of the function to validate
        parameters: Dictionary of parameters to validate
    
    Returns:
        Dictionary containing validation results
    """
    required_params = {
        'exact_match_query': {'parquet_file', 'column_name', 'value', 'geometry', 'geometry_type'},
        'like_query': {'parquet_file', 'column_name', 'pattern', 'geometry', 'geometry_type'},
        'within_area_query': {'parquet_file', 'column_name', 'value', 'geometry', 'geometry_type'},
        'nearest_query': {'parquet_file', 'column_name', 'value', 'geometry', 'geometry_type', 'limit'},
        'count_within_area_query': {'parquet_file', 'column_name', 'value', 'geometry', 'geometry_type'},
        'aggregate_query': {'parquet_file', 'group_column', 'filter_column', 'value', 'geometry', 'geometry_type'},
        'combined_filters_query': {'parquet_file', 'column_name', 'value', 'pattern_column', 'pattern', 'geometry', 'geometry_type'},
        'range_query': {'parquet_file', 'range_column', 'min_value', 'max_value', 'filter_column', 'value', 'geometry', 'geometry_type'}
    }

    if function_name not in required_params:
        return {
            "is_valid": False,
            "error": f"Unknown function: {function_name}",
            "missing_params": [],
            "extra_params": []
        }

    provided_params = set(parameters.keys())
    required = required_params[function_name]
    
    missing = required - provided_params
    extra = provided_params - required
    
    return {
        "is_valid": len(missing) == 0,
        "missing_params": list(missing),
        "extra_params": list(extra)
    }

