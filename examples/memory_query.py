"""Memory query implementation for handling different types of queries.
Supports both WebRTC and REST API interfaces with HTTP/HTTPS support.
"""

import os
import sys
import logging
import asyncio
import uvicorn
import ssl
import json
from pathlib import Path
from typing import Dict, Any, Optional, Union
from datetime import datetime
import argparse
from dotenv import load_dotenv

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from memories.models.load_model import LoadModel
from memories.utils.text.context_utils import classify_query
from memories.utils.earth.location_utils import (
    get_bounding_box_from_address,
    get_bounding_box_from_coords,
    get_address_from_coords,
    get_coords_from_address
)
from memories.core.memory_retrieval import MemoryRetrieval
from memories.utils.code.code_execution import CodeExecution
from memories.interface.webrtc import WebRTCInterface, WebRTCClient
from memories.interface.api.main import app
from memories.interface.api.core.config import (
    API_V1_PREFIX,
    PROJECT_TITLE,
    PROJECT_DESCRIPTION,
    VERSION
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)
logger.info(f"Loading environment from {env_path}")

# Define MessageType enum
class MessageType(str, Enum):
    TEXT = "text"
    QUERY = "query"
    COMMAND = "command"

# Request/Response Models
class MemoryRequest(BaseModel):
    text: str
    message_type: MessageType
    api_key: str
    model_params: Optional[Dict[str, Any]] = None

class MemoryResponse(BaseModel):
    status: str
    message: str
    data: Dict[str, Any]
    timestamp: datetime

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
            # If api_key is not provided, try to get it from environment
            if api_key is None:
                api_key = os.getenv('OPENAI_API_KEY')
                if not api_key:
                    raise ValueError("OPENAI_API_KEY not found in environment variables")
                logger.info("Using OpenAI API key from environment")

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
            
            # Load function definitions
            self.function_mapping = {
                "get_bounding_box": get_bounding_box_from_address,
                "get_bounding_box_from_coords": get_bounding_box_from_coords,
                "get_address_from_coords": get_address_from_coords,
                "get_coords_from_address": get_coords_from_address,
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
            
            # Handle based on classification
            if query_type in ["N", "L0"]:
                # For N and L0, get direct response from model
                response = self.model.get_response(query)
                return {
                    "classification": query_type,
                    "response": response,
                    "status": "success"
                }
            elif query_type == "L1_2":
                # For L1_2, use chat completion with loaded functions
                messages = [{"role": "user", "content": query}]
                
                try:
                    # Use chat_completion from LoadModel with loaded tools
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
                    
                    # Handle tool calls if present
                    if tool_calls:
                        results = []
                        # Process each tool call
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
                        
                        # Get final response after processing all function calls
                        final_response = self.model.chat_completion(
                            messages=messages
                        )
                        
                        if final_response.get("error"):
                            return {
                                "classification": "L1_2",
                                "response": f"Error in final response: {final_response['error']}",
                                "status": "error"
                            }
                        
                        return {
                            "classification": "L1_2",
                            "response": final_response.get("message", {}).get("content", "No response generated"),
                            "status": "success",
                            "results": results
                        }
                    
                    # If no tool calls, return the direct response
                    return {
                        "classification": "L1_2",
                        "response": assistant_message.get("content", "No response generated"),
                        "status": "success"
                    }
                    
                except Exception as e:
                    logger.error(f"Error in chat completion: {e}")
                    return {
                        "classification": "L1_2",
                        "response": f"Error processing location query: {str(e)}",
                        "status": "error"
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

# Initialize memory query system
memory_system = MemoryQuery()

def run_server(
    http_port: int = 80,
    https_port: int = 443,
    cert_path: Optional[str] = None,
    key_path: Optional[str] = None,
    no_ssl: bool = False,
    reload: bool = False
) -> None:
    """
    Run the server with both HTTP and HTTPS support.
    
    Args:
        http_port: Port for HTTP server
        https_port: Port for HTTPS server
        cert_path: Path to SSL certificate
        key_path: Path to SSL private key
        no_ssl: Whether to disable HTTPS
        reload: Whether to enable auto-reload for development
    """
    # Check if root privileges are needed
    if (http_port < 1024 or https_port < 1024) and os.geteuid() != 0:
        raise PermissionError(
            "Root privileges required to bind to ports below 1024. "
            "Either run with sudo or use ports >= 1024."
        )

    # Configure HTTPS if enabled
    ssl_context = None
    if not no_ssl:
        if not cert_path or not key_path:
            raise ValueError("SSL certificate and key paths are required for HTTPS")
        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_context.load_cert_chain(cert_path, key_path)

    # Start HTTP server
    logger.info(f"Starting {PROJECT_TITLE} {VERSION}")
    logger.info(f"API Documentation: http://localhost:{http_port}/docs")
    
    config = uvicorn.Config(
        app="memories.interface.api.main:app",
        host="0.0.0.0",
        port=http_port,
        reload=reload,
        log_level="info"
    )
    http_server = uvicorn.Server(config)

    # Start HTTPS server if enabled
    if not no_ssl:
        https_config = uvicorn.Config(
            app="memories.interface.api.main:app",
            host="0.0.0.0",
            port=https_port,
            ssl_certfile=cert_path,
            ssl_keyfile=key_path,
            reload=reload,
            log_level="info"
        )
        https_server = uvicorn.Server(https_config)
        logger.info(f"HTTPS enabled on port {https_port}")

    try:
        # Run HTTP server
        http_server.run()
        
        # Run HTTPS server if enabled
        if not no_ssl:
            https_server.run()
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise

def main():
    """Main entry point for the memory query server."""
    parser = argparse.ArgumentParser(description=PROJECT_DESCRIPTION)
    parser.add_argument("--http-port", type=int, default=80,
                      help="Port for HTTP server (default: 80)")
    parser.add_argument("--https-port", type=int, default=443,
                      help="Port for HTTPS server (default: 443)")
    parser.add_argument("--cert", type=str,
                      help="Path to SSL certificate for HTTPS")
    parser.add_argument("--key", type=str,
                      help="Path to SSL private key for HTTPS")
    parser.add_argument("--no-ssl", action="store_true",
                      help="Disable HTTPS server")
    parser.add_argument("--reload", action="store_true",
                      help="Enable auto-reload for development")
    
    args = parser.parse_args()
    
    try:
        run_server(
            http_port=args.http_port,
            https_port=args.https_port,
            cert_path=args.cert,
            key_path=args.key,
            no_ssl=args.no_ssl,
            reload=args.reload
        )
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise

if __name__ == "__main__":
    main() 