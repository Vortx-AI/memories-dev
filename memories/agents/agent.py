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
            location (str): Location string to geocode
            max_retries (int): Maximum number of retry attempts
            
        Returns:
            Dict containing bounding box coordinates or None if not found
        """
        for attempt in range(max_retries):
            try:
                # Get location details from Nominatim
                location_data = self.geocoder.geocode(location, exactly_one=True, timeout=10)
                
                if location_data and hasattr(location_data, 'raw'):
                    bbox = location_data.raw.get('boundingbox')
                    if bbox:
                        return {
                            'south': float(bbox[0]),
                            'north': float(bbox[1]),
                            'west': float(bbox[2]),
                            'east': float(bbox[3])
                        }
                    
                logger.warning(f"No bounding box found for location: {location}")
                return None
                
            except (GeocoderTimedOut, GeocoderUnavailable) as e:
                if attempt == max_retries - 1:
                    logger.error(f"Failed to geocode after {max_retries} attempts: {str(e)}")
                    return None
                time.sleep(1)  # Wait before retrying
                
            except Exception as e:
                logger.error(f"Error geocoding location: {str(e)}")
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
            
            # Get location from context if available
            if result.get('classification') in ['L1', 'L1_2', 'L2']:
                print("\n[Invoking Context Agent]")
                print("-"*50)
                context_agent = AgentContext(query, self.load_model)
                context_result = context_agent.process_query()
                
                # Extract location information
                location_info = context_result.get('location_info', {})
                if isinstance(location_info, dict):
                    normalized = location_info.get('normalized', {})
                    location = normalized.get('location', '')
                    
                    if location:
                        print(f"\n[Getting Bounding Box for Location: {location}]")
                        print("-"*50)
                        bbox = self.get_location_bbox(location)
                        
                        if bbox:
                            print("Bounding Box Found:")
                            print(f"• North: {bbox['north']}")
                            print(f"• South: {bbox['south']}")
                            print(f"• East: {bbox['east']}")
                            print(f"• West: {bbox['west']}")
                            
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
                            
                            # Update result with bbox and WKT
                            result.update({
                                'bbox': bbox,
                                'wkt_polygon': wkt_polygon
                            })
                        else:
                            print("No bounding box found for the location")
            
            #######################################################
            
            aoi =  "POLYGON((77.59765625 12.900390625,77.609375 12.900390625,77.609375 12.912109375,77.59765625 12.912109375,77.59765625 12.900390625))"

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
                        similar_columns = l1_result["similar_columns"]
                        result['similar_columns'] = similar_columns
                        
                        print(f"\n• Searching columns for data type: {search_term}")
                        print("\n• Similar columns found:")
                        for col in similar_columns:
                            print(f"\n  Column: {col['column_name']}")
                            print(f"  File: {col['file_name']}")
                            print(f"  File Path: {col['file_path']}")
                            print(f"  Geometry: {col['geometry']}")
                            print(f"  Geometry Type: {col['geometry_type']}")
                            
                            print(f"  Distance: {col['distance']:.4f}")
                        
                        # Use the extracted latitude and longitude from the Context Agent.
                        lat_val = result.get('latitude', 0.0)
                        lon_val = result.get('longitude', 0.0)
    
                        # Use the previously retrieved data_type.
                        data_type = result.get('data_type', '')
    
                        # Get the Parquet file information from the best matching column.
                        best_column = similar_columns[0]
                        raw_file_path = best_column.get('file_path', '')
    
                        # Construct the full Parquet file path if the provided file_path is not absolute.
                        if not os.path.isabs(raw_file_path):
                            project_root = os.getenv("PROJECT_ROOT", "")
                            parquet_file_path = os.path.join(project_root, "data", "parquet", raw_file_path)
                        else:
                            parquet_file_path = raw_file_path
    
                        print("\n[Invoking Agent Analyst]")
                        print("-" * 50)
                        analyst = AgentAnalyst(self.load_model)
                        relevant_column = best_column.get('column_name', '')
                        analyst_result = analyst.analyze_query(
                            query=query,
                            geometry=aoi,
                            geometry_type='POLYGON',  # Since aoi is a polygon
                            data_type=data_type,
                            parquet_file=parquet_file_path,
                            relevant_column=relevant_column,
                            geometry_column='geometry',
                            extra_params={}
                        )

                        print(analyst_result)
                        
                        # Execute recommended functions
                        if analyst_result.get('status') == 'success':
                            print("\n[Executing Recommended Functions]")
                            print("-" * 50)
                            
                            combined_results = []
                            for recommendation in analyst_result.get('recommendations', []):
                                function_name = recommendation.get('function_name')
                                parameters = recommendation.get('parameters', {})
                                
                                print(f"\nExecuting {function_name}:")
                                print(f"Parameters: {parameters}")
                                
                                try:
                                    # Validate inputs first
                                    validation = validate_function_inputs(function_name, parameters)
                                    if validation["is_valid"]:
                                        # Execute the function
                                        results = execute_kb_function(function_name, parameters)
                                        if isinstance(results, pd.DataFrame):
                                            # Keep only relevant columns
                                            relevant_columns = [
                                                parameters.get('column_name', ''),  # The queried data type
                                                'name',  # Name if available
                                                'address',  # Address if available
                                                'xmin', 'xmax', 'ymin', 'ymax',  # Bounding box coordinates
                                                'wkt_geometry',  # WKT geometry
                                                'distance_km'  # Distance if available
                                            ]
                                            
                                            # Filter columns that exist in the DataFrame
                                            existing_columns = [col for col in relevant_columns if col in results.columns]
                                            filtered_results = results[existing_columns].copy()
                                            
                                            # Convert to JSON-compatible format
                                            json_results = filtered_results.to_dict(orient='records')
                                            
                                            # Add metadata about the query
                                            formatted_results = {
                                                'source_function': function_name,
                                                'data_type': parameters.get('column_name', ''),
                                                'results': json_results
                                            }
                                            
                                            combined_results.append(formatted_results)
                                            print(f"Found {len(json_results)} results")
                                        else:
                                            print(f"Unexpected result type: {type(results)}")
                                    else:
                                        print(f"Invalid inputs for {function_name}:")
                                        print(f"Missing parameters: {validation['missing_params']}")
                                        print(f"Extra parameters: {validation['extra_params']}")
                                except Exception as e:
                                    print(f"Error executing {function_name}: {str(e)}")
                            
                            # Generate natural language response if we have results
                            if combined_results:
                                print("\n[Generating Response]")
                                print("-" * 50)
                                response_result = self.response_agent.process_results(query, combined_results)
                                if response_result['status'] == 'success':
                                    result['response'] = response_result['response']
                                    result['formatted_results'] = combined_results
                                    print("\nResponse:")
                                    print(response_result['response'])
                                else:
                                    print(f"Error generating response: {response_result.get('error')}")
                                    result['response'] = "Error generating natural language response."
                            else:
                                result['response'] = "No results found matching your query."
                                print("\nNo results found from any function")
            
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

