"""
Memory query implementation for handling different types of queries.
"""

from typing import Dict, Any, Union, Optional
import logging
import os
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import sys

from memories.models.load_model import LoadModel
from memories.utils.text.context_utils import classify_query
from memories.utils.earth.location_utils import (
    get_bounding_box_from_address,
    get_bounding_box_from_coords,
    get_address_from_coords,
    get_coords_from_address,
    expand_bbox_with_radius
)
from memories.core.memory_retrieval import MemoryRetrieval
from memories.utils.code.code_execution import CodeExecution
from memories.data_acquisition.sources.osm_api import OSMDataAPI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)
logger.info(f"Loading environment from {env_path}")

class MemoryQuery:
    """Memory query handler for processing different types of queries."""
    
    def __init__(
        self,
        model_provider: str = "openai",
        deployment_type: str = "api",
        model_name: str = "gpt-4",
        api_key: Optional[str] = None,
        functions_file: str = "function_definitions.json"
    ):
        """
        Initialize the memory query handler with LoadModel.
        
        Args:
            model_provider (str): The model provider (e.g., "openai")
            deployment_type (str): Type of deployment (e.g., "api")
            model_name (str): Name of the model to use
            api_key (Optional[str]): API key for the model provider
            functions_file (str): Path to the JSON file containing function definitions
        """
        try:
            self.model = LoadModel(
                model_provider=model_provider,
                deployment_type=deployment_type,
                model_name=model_name,
                api_key=api_key
            )
            logger.info(f"Successfully initialized LoadModel with {model_name}")
            
            # Initialize memory retrieval if needed for spatial queries
            self.memory_retrieval = None
            
            # Initialize code execution
            self.code_execution = CodeExecution()
            
            # Initialize OvertureAPI and OSM API
            from memories.data_acquisition.sources.overture_api import OvertureAPI
            self.overture_api = OvertureAPI(data_dir="data/overture")
            self.osm_api = OSMDataAPI(cache_dir="data/osm")
            
            # Load function definitions
            self.function_mapping = {
                "get_bounding_box": get_bounding_box_from_address,
                "get_bounding_box_from_coords": get_bounding_box_from_coords,
                "get_address_from_coords": get_address_from_coords,
                "get_coords_from_address": get_coords_from_address,
                "expand_bbox_with_radius": expand_bbox_with_radius,
                "search_geospatial_data_in_bbox": self.search_geospatial_data_in_bbox_wrapper,
                "download_theme_type": self.overture_api.download_theme_type,
                "get_data_by_bbox": self.get_data_by_bbox_wrapper,
                "get_data_by_bbox_and_value": self.get_data_by_bbox_and_value_wrapper,
                "get_data_by_fuzzy_search": self.get_data_by_fuzzy_search_wrapper,
                "execute_code": self.code_execution.execute_code
            }
            
            # Load functions from JSON file
            functions_path = Path(__file__).parent / functions_file
            try:
                with open(functions_path, 'r') as f:
                    function_data = json.load(f)
                self.tools = function_data.get("location_functions", [])
                logger.info(f"Successfully loaded {len(self.tools)} functions from {functions_file}")
            except Exception as e:
                logger.error(f"Error loading functions from {functions_file}: {e}")
                self.tools = []
                
        except Exception as e:
            logger.error(f"Failed to initialize LoadModel: {e}")
            raise

    def get_data_by_bbox_wrapper(self, min_lon: float, min_lat: float, max_lon: float, max_lat: float, 
                                lon_column: str = "longitude", lat_column: str = "latitude", 
                                geom_column: str = "geometry", limit: int = 1000) -> Dict[str, Any]:
        """Wrapper for get_data_by_bbox to handle initialization and return format."""
        try:
            # Initialize memory_retrieval if not already done
            if self.memory_retrieval is None:
                from memories.core.cold import ColdMemory
                cold_memory = ColdMemory(storage_path=Path('data'))
                self.memory_retrieval = MemoryRetrieval(cold_memory)

            # Call get_data_by_bbox
            results = self.memory_retrieval.get_data_by_bbox(
                min_lon=min_lon,
                min_lat=min_lat,
                max_lon=max_lon,
                max_lat=max_lat,
                lon_column=lon_column,
                lat_column=lat_column,
                geom_column=geom_column,
                limit=limit
            )

            # Convert results to dictionary format
            return {
                "status": "success" if not results.empty else "no_results",
                "data": results.to_dict('records') if not results.empty else [],
                "count": len(results) if not results.empty else 0
            }
        except Exception as e:
            logger.error(f"Error in get_data_by_bbox: {e}")
            return {
                "status": "error",
                "message": str(e),
                "data": []
            }

    def get_data_by_bbox_and_value_wrapper(
        self, 
        min_lon: float, 
        min_lat: float, 
        max_lon: float, 
        max_lat: float,
        search_value: str,
        case_sensitive: bool = False,
        lon_column: str = "longitude",
        lat_column: str = "latitude",
        geom_column: str = "geometry",
        limit: int = 1000
    ) -> Dict[str, Any]:
        """Wrapper for get_data_by_bbox_and_value to handle initialization and return format."""
        try:
            # Initialize memory_retrieval if not already done
            if self.memory_retrieval is None:
                from memories.core.cold import ColdMemory
                cold_memory = ColdMemory(storage_path=Path('data'))
                self.memory_retrieval = MemoryRetrieval(cold_memory)

            # Call get_data_by_bbox_and_value
            results = self.memory_retrieval.get_data_by_bbox_and_value(
                min_lon=min_lon,
                min_lat=min_lat,
                max_lon=max_lon,
                max_lat=max_lat,
                search_value=search_value,
                case_sensitive=case_sensitive,
                lon_column=lon_column,
                lat_column=lat_column,
                geom_column=geom_column,
                limit=limit
            )

            # Convert results to dictionary format
            return {
                "status": "success" if not results.empty else "no_results",
                "data": results.to_dict('records') if not results.empty else [],
                "count": len(results) if not results.empty else 0
            }
        except Exception as e:
            logger.error(f"Error in get_data_by_bbox_and_value: {e}")
            return {
                "status": "error",
                "message": str(e),
                "data": []
            }

    def get_data_by_fuzzy_search_wrapper(
        self,
        search_term: str,
        similarity_threshold: float = 0.3,
        case_sensitive: bool = False,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Wrapper for get_data_by_fuzzy_search to handle initialization and return format."""
        try:
            # Initialize memory_retrieval if not already done
            if self.memory_retrieval is None:
                from memories.core.cold import ColdMemory
                cold_memory = ColdMemory(storage_path=Path('data'))
                self.memory_retrieval = MemoryRetrieval(cold_memory)

            # Call get_data_by_fuzzy_search
            results = self.memory_retrieval.get_data_by_fuzzy_search(
                search_term=search_term,
                similarity_threshold=similarity_threshold,
                case_sensitive=case_sensitive,
                limit=limit
            )

            # Convert results to dictionary format
            return {
                "status": "success" if not results.empty else "no_results",
                "data": results.to_dict('records') if not results.empty else [],
                "count": len(results) if not results.empty else 0
            }
        except Exception as e:
            logger.error(f"Error in get_data_by_fuzzy_search: {e}")
            return {
                "status": "error",
                "message": str(e),
                "data": []
            }

    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a query by classifying it and generating appropriate response.
        
        Args:
            query (str): The user's query
            
        Returns:
            Dict containing classification and response
        """
        try:
            # First classify the query
            classification_result = classify_query(query, self.model)
            query_type = classification_result.get("classification", "N")
            
            logger.info(f"Query classified as: {query_type}")
            
            if query_type == "L1_2":
                system_message = {
                    "role": "system",
                    "content": """You are a helpful assistant that MUST use the available functions to completely answer location-based queries.
                    For queries about buildings, roads, or other features, you MUST:
                    1. Use get_bounding_box to get the area coordinates
                    2. IMMEDIATELY use search_geospatial_data_in_bbox with those coordinates to find the features
                    3. Summarize the results
                    
                    DO NOT stop after getting the bounding box - you must search for the features!
                    DO NOT just describe what you will do - actually do it!
                    
                    Example flow:
                    1. get_bounding_box -> gets coordinates
                    2. search_geospatial_data_in_bbox with "building" as query_word -> finds buildings
                    3. Summarize what was found."""
                }
                
                messages = [
                    system_message,
                    {"role": "user", "content": query}
                ]
                results = []
                
                while True:
                    response = self.model.chat_completion(
                        messages=messages,
                        tools=self.tools,
                        tool_choice="auto"
                    )
                    
                    if response.get("error"):
                        return {
                            "classification": "L1_2",
                            "response": f"Error in chat completion: {response['error']}",
                            "status": "error"
                        }
                    
                    assistant_message = response.get("message", {})
                    tool_calls = response.get("tool_calls", [])
                    
                    # Process tool calls
                    if tool_calls:
                        for tool_call in tool_calls:
                            function_name = tool_call.get("function", {}).get("name")
                            
                            try:
                                # Parse the arguments
                                args = json.loads(tool_call["function"]["arguments"])
                                
                                # Get the corresponding function from the mapping
                                if function_name in self.function_mapping:
                                    function_result = self.function_mapping[function_name](**args)
                                else:
                                    return {
                                        "classification": "L1_2",
                                        "response": f"Unknown function: {function_name}",
                                        "status": "error"
                                    }
                                
                                # Check if request was successful
                                if isinstance(function_result, dict) and function_result.get("status") == "error":
                                    error_msg = function_result.get("message", f"Unknown error in {function_name}")
                                    return {
                                        "classification": "L1_2",
                                        "response": f"Error in {function_name}: {error_msg}",
                                        "status": "error"
                                    }
                                
                                # Store the result
                                results.append({
                                    "function_name": function_name,
                                    "args": args,
                                    "result": function_result
                                })
                                
                                # Add the function result to messages
                                messages.append({
                                    "role": "assistant",
                                    "content": None,
                                    "function_call": {
                                        "name": function_name,
                                        "arguments": json.dumps(args)
                                    }
                                })
                                messages.append({
                                    "role": "function",
                                    "name": function_name,
                                    "content": json.dumps(function_result)
                                })
                                
                            except json.JSONDecodeError as e:
                                logger.error(f"Error parsing tool arguments: {e}")
                                return {
                                    "classification": "L1_2",
                                    "response": "Error parsing location request",
                                    "status": "error"
                                }
                            except Exception as e:
                                logger.error(f"Error processing tool call: {e}")
                                return {
                                    "classification": "L1_2",
                                    "response": f"Error processing location: {str(e)}",
                                    "status": "error"
                                }
                        
                        # Force continuation if only get_bounding_box was called
                        if len(results) == 1 and results[0]["function_name"] == "get_bounding_box":
                            messages.append({
                                "role": "system",
                                "content": "You MUST now use search_geospatial_data_in_bbox to find the features in this area. Do not stop here!"
                            })
                            continue
                    
                    # Only return if we have both get_bounding_box and search_geospatial_data_in_bbox results
                    if len(results) >= 2:
                        return {
                            "classification": "L1_2",
                            "response": assistant_message.get("content", ""),
                            "status": "success",
                            "results": results
                        }
                        
                    # If we only have get_bounding_box, force continuation
                    if len(results) == 1:
                        messages.append({
                            "role": "system",
                            "content": "Continue with search_geospatial_data_in_bbox to find the features!"
                        })
                        continue
                    
            elif query_type in ["N", "L0"]:
                # For N and L0, get direct response from model
                response = self.model.get_response(query)
                return {
                    "classification": query_type,
                    "response": response,
                    "status": "success"
                }
            else:
                return {
                    "classification": "unknown",
                    "response": "Unsupported query type",
                    "status": "error"
                }
                
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                "classification": "error",
                "response": f"Error processing query: {str(e)}",
                "status": "error"
            }

    def search_geospatial_data_in_bbox_wrapper(
        self,
        query_word: str,
        bbox: list,
        similarity_threshold: float = 0.5
    ) -> Dict[str, Any]:
        """Wrapper for search_geospatial_data_in_bbox to handle initialization and return format."""
        try:
            # Initialize memory_retrieval if not already done
            if self.memory_retrieval is None:
                from memories.core.cold import ColdMemory
                cold_memory = ColdMemory(storage_path=Path('data'))
                self.memory_retrieval = MemoryRetrieval(cold_memory)

            # Convert bbox list to tuple
            bbox_tuple = tuple(bbox)
            
            # Call search function
            results = self.memory_retrieval.search_geospatial_data_in_bbox(
                query_word=query_word,
                bbox=bbox_tuple,
                similarity_threshold=similarity_threshold
            )

            # Convert results to dictionary format
            return {
                "status": "success" if not results.empty else "no_results",
                "data": results.to_dict('records') if not results.empty else [],
                "count": len(results) if not results.empty else 0
            }
        except Exception as e:
            logger.error(f"Error in search_geospatial_data_in_bbox: {e}")
            return {
                "status": "error",
                "message": str(e),
                "data": []
            }

def main():
    """Example usage of MemoryQuery"""
    try:
        # Initialize MemoryQuery with OpenAI API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("OPENAI_API_KEY environment variable not set")
            return

        logger.info("Initializing MemoryQuery...")
        memory_query = MemoryQuery(
            model_provider="openai",
            deployment_type="api",
            model_name="gpt-4",
            api_key=api_key
        )
        logger.info("MemoryQuery initialized successfully")
        
        # Check if query was provided
        if len(sys.argv) < 2:
            logger.error("No query provided. Usage: python3 memory_chat.py 'your query here'")
            return
            
        # Join all arguments after the script name to form the complete query
        query = ' '.join(sys.argv[1:])
        logger.info("-" * 50)
        logger.info(f"Processing query: {query}")
        logger.info("-" * 50)
        
        result = memory_query.process_query(query)
        
        # Print the result in a formatted way
        print("\nQuery Result:")
        print("=" * 80)
        print(f"Classification: {result.get('classification', 'unknown')}")
        print(f"Status: {result.get('status', 'unknown')}")
        
        # If there are function calls, show them first
        if 'results' in result and result['results']:
            print("\nFunction Call Sequence:")
            print("-" * 80)
            for i, r in enumerate(result['results'], 1):
                print(f"\n{i}. Function: {r.get('function_name')}")
                print(f"   Arguments: {json.dumps(r.get('args'), indent=2)}")
                
                # Format the result based on its type
                result_data = r.get('result', {})
                if isinstance(result_data, dict):
                    if 'data' in result_data and isinstance(result_data['data'], list):
                        print(f"   Results: Found {len(result_data['data'])} items")
                        if result_data['data']:
                            print("   Sample data:")
                            print(json.dumps(result_data['data'][0], indent=2))
                    else:
                        print(f"   Result: {json.dumps(result_data, indent=2)}")
                else:
                    print(f"   Result: {result_data}")
                print("   " + "-" * 70)
        
        # Show the final response
        print("\nFinal Response:")
        print("-" * 80)
        if isinstance(result.get('response'), dict):
            print(json.dumps(result['response'], indent=2))
        else:
            print(result.get('response', 'No response generated'))
        
        print("=" * 80)
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main() 