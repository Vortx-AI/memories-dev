"""
Memory query implementation for handling different types of queries.
"""

from typing import Dict, Any, Union, Optional, List
import logging
from logging.handlers import RotatingFileHandler
import os
import json
from pathlib import Path
from datetime import datetime, date
from dotenv import load_dotenv
import sys
import pandas as pd
import numpy as np
# Add Azure imports
from azure.ai.inference import ChatCompletionsClient
from azure.core.credentials import AzureKeyCredential

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

# Configure logging with both file and console handlers
def setup_logging():
    """Set up logging configuration with both file and console output."""
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Create a logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(message)s'  # Simpler format for console
    )
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        log_dir / "memory_chat.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Set up logging
logger = setup_logging()

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)
logger.info(f"Loading environment from {env_path}")

# Initialize GPU support flags
HAS_GPU_SUPPORT = False
HAS_CUDF = False
HAS_CUSPATIAL = False

try:
    import cudf
    HAS_CUDF = True
except ImportError:
    logging.warning("cudf not available. GPU acceleration for dataframes will be disabled.")

try:
    import cuspatial
    HAS_CUSPATIAL = True
except ImportError:
    logging.warning("cuspatial not available. GPU acceleration for spatial operations will be disabled.")

if HAS_CUDF and HAS_CUSPATIAL:
    HAS_GPU_SUPPORT = True
    logging.info("GPU support enabled with cudf and cuspatial.")

class MemoryQuery:
    """Memory query handler for processing different types of queries."""
    
    def __init__(
        self,
        model_provider: str = "openai",
        deployment_type: str = "api",
        model_name: str = "gpt-4",
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        functions_file: str = "function_definitions.json",
        use_gpu: bool = True
    ):
        """
        Initialize the memory query handler with LoadModel.
        
        Args:
            model_provider (str): The model provider (e.g., "openai", "azure-ai")
            deployment_type (str): Type of deployment (e.g., "api")
            model_name (str): Name of the model to use
            api_key (Optional[str]): API key for the model provider
            endpoint (Optional[str]): Endpoint URL for Azure AI
            functions_file (str): Path to the JSON file containing function definitions
            use_gpu (bool): Whether to use GPU acceleration if available
        """
        logger.info("Initializing MemoryQuery...")
        try:
            self.model = LoadModel(
                model_provider=model_provider,
                deployment_type=deployment_type,
                model_name=model_name,
                api_key=api_key,
                endpoint=endpoint
            )
            logger.info(f"Successfully initialized LoadModel with {model_name}")
            
            # Initialize memory manager
            from memories.core.memory_manager import MemoryManager
            self.memory_manager = MemoryManager()
            logger.info("Memory manager initialized")
            
            # Initialize memory retrieval
            self.memory_retrieval = MemoryRetrieval()
            self.memory_retrieval.cold = self.memory_manager.cold_memory
            
            # Set GPU support flags
            self.memory_retrieval.HAS_GPU_SUPPORT = HAS_GPU_SUPPORT
            self.memory_retrieval.HAS_CUDF = HAS_CUDF
            self.memory_retrieval.HAS_CUSPATIAL = HAS_CUSPATIAL
            
            # Initialize code execution
            self.code_execution = CodeExecution()
            
            # Initialize OvertureAPI and OSM API
            from memories.data_acquisition.sources.overture_api import OvertureAPI
            self.overture_api = OvertureAPI(data_dir="data/overture")
            self.osm_api = OSMDataAPI(cache_dir="data/osm")
            
            # Check GPU availability
            self.use_gpu = use_gpu and HAS_GPU_SUPPORT
            if use_gpu and not HAS_GPU_SUPPORT:
                logger.warning("GPU acceleration requested but not available. Using CPU instead.")
            elif self.use_gpu:
                logger.info("GPU acceleration enabled for spatial operations.")
            
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
                "execute_code": self.code_execution.execute_code,
                "analyze_geospatial_data": self.analyze_geospatial_data_wrapper
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
            logger.error(f"Failed to initialize MemoryQuery: {e}", exc_info=True)
            raise

    def get_data_by_bbox_wrapper(self, min_lon: float, min_lat: float, max_lon: float, max_lat: float, 
                                lon_column: str = "longitude", lat_column: str = "latitude", 
                                geom_column: str = "geometry", limit: int = 1000) -> Dict[str, Any]:
        """Wrapper for get_data_by_bbox to handle initialization and return format."""
        try:
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
        """Process a query by letting the model decide the approach and function sequence."""
        logger.info(f"Processing query: {query}")
        try:
            system_message = {
                "role": "system",
                "content": """You are an intelligent assistant that helps with location-based queries.
                Based on the query, decide what information you need and which functions to call.
                
                You have access to these functions:
                - get_bounding_box: Convert a text address into a geographic bounding box
                - expand_bbox_with_radius: Expand a bounding box by radius or create box around point
                - get_bounding_box_from_coords: Convert coordinates into a geographic bounding box
                - get_address_from_coords: Get address details from coordinates using reverse geocoding
                - get_coords_from_address: Get coordinates from an address using forward geocoding
                - search_geospatial_data_in_bbox: Search for geospatial features within a bounding box
                - download_theme_type: Download data for a specific theme and type within a bounding box
                - execute_code: Execute custom Python code with pandas and numpy
                
                You can:
                1. Use any combination of functions in any order
                2. Make multiple calls if needed
                3. Decide based on the available data
                4. Skip unnecessary steps
                
                Always explain your reasoning before making function calls."""
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
                        "response": f"Error in chat completion: {response['error']}",
                        "status": "error"
                    }
                
                # Handle Azure AI's specific response format
                assistant_message = response.get("message", {})
                if isinstance(assistant_message, str):  # Azure returns content directly as string
                    assistant_message = {"role": "assistant", "content": assistant_message}
                
                tool_calls = response.get("tool_calls", [])
                
                if not tool_calls and assistant_message.get("content"):
                    return {
                        "response": assistant_message.get("content"),
                        "status": "success",
                        "results": results
                    }
                
                if tool_calls:
                    for tool_call in tool_calls:
                        # Handle Azure's tool call format
                        if isinstance(tool_call, dict):
                            function_name = tool_call.get("function", {}).get("name")
                            function_args = tool_call.get("function", {}).get("arguments")
                        else:  # Azure might return tool_call object directly
                            function_name = tool_call.function.name
                            function_args = tool_call.function.arguments
                        
                        logger.info(f"Executing function: {function_name}")
                        try:
                            args = json.loads(function_args)
                            
                            if function_name in self.function_mapping:
                                function_result = self.function_mapping[function_name](**args)
                                serialized_result = self.serialize_result(function_result)
                            else:
                                return {
                                    "response": f"Unknown function: {function_name}",
                                    "status": "error"
                                }
                            
                            if isinstance(serialized_result, dict) and serialized_result.get("status") == "error":
                                error_msg = serialized_result.get("message", f"Unknown error in {function_name}")
                                return {
                                    "response": f"Error in {function_name}: {error_msg}",
                                    "status": "error"
                                }
                            
                            results.append({
                                "function_name": function_name,
                                "args": args,
                                "result": serialized_result
                            })
                            
                            # Format messages for Azure AI
                            messages.append({
                                "role": "assistant",
                                "content": None,
                                "tool_calls": [{
                                    "id": tool_call.id if hasattr(tool_call, 'id') else None,
                                    "type": "function",
                                    "function": {
                                        "name": function_name,
                                        "arguments": json.dumps(args)
                                    }
                                }]
                            })
                            messages.append({
                                "role": "tool",  # Azure uses 'tool' instead of 'function'
                                "content": json.dumps(serialized_result),
                                "tool_call_id": tool_call.id if hasattr(tool_call, 'id') else None
                            })
                            
                            logger.info(f"Successfully executed {function_name}")
                        except json.JSONDecodeError as e:
                            logger.error(f"Error parsing arguments: {e}")
                            return {
                                "response": "Error parsing request",
                                "status": "error"
                            }
                        except Exception as e:
                            logger.error(f"Error processing tool call: {e}", exc_info=True)
                            return {
                                "response": f"Error: {str(e)}",
                                "status": "error"
                            }
                    
                    messages.append({
                        "role": "system",
                        "content": "Based on these results, decide if you need more information or can provide a final answer."
                    })
                    continue
                
        except Exception as e:
            logger.error(f"Error processing query: {e}", exc_info=True)
            return {
                "response": f"Error processing query: {str(e)}",
                "status": "error"
            }

    def search_geospatial_data_in_bbox_wrapper(
        self,
        query_word: str,
        bbox: tuple,
        similarity_threshold: float = 0.7,
        max_workers: int = 4,
        batch_size: int = 1000000
    ) -> Dict[str, Any]:
        """Wrapper for search_geospatial_data_in_bbox to handle initialization and return format."""
        try:
            # Call search_geospatial_data_in_bbox
            results = self.memory_retrieval.search_geospatial_data_in_bbox(
                query_word=query_word,
                bbox=bbox,
                
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

    def analyze_geospatial_data_wrapper(
        self,
        query_word: str,
        bbox: list,
        analysis_action: str = "summary",
        similarity_threshold: float = 0.7,
        max_tokens: int = 15000
    ) -> Dict[str, Any]:
        """Wrapper for analyze_geospatial_data to handle initialization and return format."""
        try:
            # Convert bbox list to tuple
            bbox_tuple = tuple(bbox)
            
            # Call analyze_geospatial_data
            results = self.memory_retrieval.analyze_geospatial_data(
                query_word=query_word,
                bbox=bbox_tuple,
                analysis_action=analysis_action,
                similarity_threshold=similarity_threshold,
                max_tokens=max_tokens
            )

            return results
            
        except Exception as e:
            logger.error(f"Error in analyze_geospatial_data: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

    def _format_azure_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Format messages for Azure AI API."""
        formatted_messages = []
        for msg in messages:
            formatted_msg = {
                "role": msg["role"],
                "content": msg["content"]
            }
            
            # Handle tool calls
            if "tool_calls" in msg:
                formatted_msg["tool_calls"] = msg["tool_calls"]
            
            # Handle tool responses
            if msg["role"] == "tool":
                formatted_msg["tool_call_id"] = msg.get("tool_call_id")
            
            formatted_messages.append(formatted_msg)
        
        return formatted_messages

def main():
    """Example usage of MemoryQuery"""
    try:
        # Initialize MemoryQuery with Azure AI credentials
        api_key = os.getenv("AZURE_INFERENCE_CREDENTIAL")
        endpoint = os.getenv("AZURE_INFERENCE_ENDPOINT")
        
        if not api_key:
            logger.error("AZURE_INFERENCE_CREDENTIAL environment variable not set")
            return
        if not endpoint:
            logger.error("AZURE_INFERENCE_ENDPOINT environment variable not set")
            return

        logger.info("=" * 80)
        logger.info("Starting Memory Chat")
        logger.info("=" * 80)
        
        memory_query = MemoryQuery(
            model_provider="azure-ai",  # Change to azure-ai
            deployment_type="api",
            model_name="gpt-4",  # This will be ignored as the model is determined by the endpoint
            api_key=api_key,
            endpoint=endpoint  # Add endpoint parameter
        )
        
        # Check if query was provided
        if len(sys.argv) < 2:
            logger.error("No query provided. Usage: python3 memory_chat.py 'your query here'")
            return
            
        # Join all arguments after the script name to form the complete query
        query = ' '.join(sys.argv[1:])
        logger.info("-" * 80)
        logger.info(f"Processing query: {query}")
        logger.info("-" * 80)
        
        result = memory_query.process_query(query)
        
        # Log and print the results
        logger.info("\nQuery Result:")
        logger.info("=" * 80)
        logger.info(f"Status: {result.get('status', 'unknown')}")
        
        # Log function calls
        if 'results' in result and result['results']:
            logger.info("\nFunction Call Sequence:")
            logger.info("-" * 80)
            for i, r in enumerate(result['results'], 1):
                logger.info(f"\n{i}. Function: {r.get('function_name')}")
                logger.info(f"   Arguments: {json.dumps(r.get('args'), indent=2)}")
                
                # Format the result based on its type
                result_data = r.get('result', {})
                if isinstance(result_data, dict):
                    if 'data' in result_data and isinstance(result_data['data'], list):
                        logger.info(f"   Results: Found {len(result_data['data'])} items")
                        if result_data['data']:
                            logger.info("   Sample data:")
                            logger.info(json.dumps(result_data['data'][0], indent=2))
                    else:
                        logger.info(f"   Result: {json.dumps(result_data, indent=2)}")
                else:
                    logger.info(f"   Result: {result_data}")
                logger.info("   " + "-" * 70)
        
        # Log final response
        logger.info("\nFinal Response:")
        logger.info("-" * 80)
        if isinstance(result.get('response'), dict):
            logger.info(json.dumps(result['response'], indent=2))
        else:
            logger.info(result.get('response', 'No response generated'))
        
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main() 