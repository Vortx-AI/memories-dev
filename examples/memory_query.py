"""
Memory query implementation for handling different types of queries.
"""

from typing import Dict, Any, Union, Optional
import logging
import os
import json
import asyncio
from pathlib import Path
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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

class MemoryQueryServer:
    """WebRTC server wrapper for MemoryQuery."""
    
    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8765,
        model_provider: str = "openai",
        deployment_type: str = "api",
        model_name: str = "gpt-4",
        api_key: Optional[str] = None,
        functions_file: str = "function_definitions.json"
    ):
        """Initialize the WebRTC server with MemoryQuery backend."""
        self.memory_query = MemoryQuery(
            model_provider=model_provider,
            deployment_type=deployment_type,
            model_name=model_name,
            api_key=api_key,
            functions_file=functions_file
        )
        self.server = WebRTCInterface(host=host, port=port)
        
    def setup(self):
        """Register MemoryQuery functions with the WebRTC server."""
        self.server.register_function(self.process_query)
        self.server.register_function(self.get_data_by_bbox)
        self.server.register_function(self.get_data_by_bbox_and_value)
        self.server.register_function(self.get_data_by_fuzzy_search)
        
    async def process_query(self, query: str) -> Dict[str, Any]:
        """WebRTC wrapper for process_query."""
        return self.memory_query.process_query(query)
        
    async def get_data_by_bbox(self, *args, **kwargs) -> Dict[str, Any]:
        """WebRTC wrapper for get_data_by_bbox."""
        return self.memory_query.get_data_by_bbox_wrapper(*args, **kwargs)
        
    async def get_data_by_bbox_and_value(self, *args, **kwargs) -> Dict[str, Any]:
        """WebRTC wrapper for get_data_by_bbox_and_value."""
        return self.memory_query.get_data_by_bbox_and_value_wrapper(*args, **kwargs)
        
    async def get_data_by_fuzzy_search(self, *args, **kwargs) -> Dict[str, Any]:
        """WebRTC wrapper for get_data_by_fuzzy_search."""
        return self.memory_query.get_data_by_fuzzy_search_wrapper(*args, **kwargs)
        
    def start(self):
        """Start the WebRTC server."""
        self.setup()
        self.server.start()
        
    def stop(self):
        """Stop the WebRTC server."""
        self.server.stop()

class MemoryQueryClient:
    """WebRTC client for MemoryQuery."""
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        """Initialize the WebRTC client."""
        self.client = WebRTCClient(host=host, port=port)
        
    async def connect(self):
        """Connect to the MemoryQuery server."""
        await self.client.connect()
        
    async def close(self):
        """Close the connection."""
        await self.client.close()
        
    async def process_query(self, query: str) -> Dict[str, Any]:
        """Process a query through WebRTC."""
        return await self.client.call_function("process_query", query)
        
    async def get_data_by_bbox(self, *args, **kwargs) -> Dict[str, Any]:
        """Get data by bounding box through WebRTC."""
        return await self.client.call_function("get_data_by_bbox", *args, **kwargs)
        
    async def get_data_by_bbox_and_value(self, *args, **kwargs) -> Dict[str, Any]:
        """Get data by bounding box and value through WebRTC."""
        return await self.client.call_function("get_data_by_bbox_and_value", *args, **kwargs)
        
    async def get_data_by_fuzzy_search(self, *args, **kwargs) -> Dict[str, Any]:
        """Get data by fuzzy search through WebRTC."""
        return await self.client.call_function("get_data_by_fuzzy_search", *args, **kwargs)

async def run_server(
    host: str = "0.0.0.0",
    port: int = 8765,
    model_provider: str = "openai",
    deployment_type: str = "api",
    model_name: str = "gpt-4",
    api_key: Optional[str] = None,
    functions_file: str = "function_definitions.json"
):
    """Run the MemoryQuery WebRTC server."""
    server = MemoryQueryServer(
        host=host,
        port=port,
        model_provider=model_provider,
        deployment_type=deployment_type,
        model_name=model_name,
        api_key=api_key,
        functions_file=functions_file
    )
    server.start()
    
    try:
        logger.info(f"MemoryQuery WebRTC server running on {host}:{port}")
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
    finally:
        server.stop()

async def run_client_example():
    """Interactive client for querying the MemoryQuery server."""
    client = MemoryQueryClient()
    
    try:
        print("Connecting to MemoryQuery server...")
        await client.connect()
        print("Connected successfully!")
        print("\nMemory Query System")
        print("==================")
        print("Type your queries and press Enter. Type 'exit' to quit.\n")
        
        while True:
            try:
                # Get query from user
                query = input("\nEnter your query: ").strip()
                
                # Check for exit command
                if query.lower() in ['exit', 'quit']:
                    print("\nExiting Memory Query System...")
                    break
                
                if not query:
                    continue
                
                print("\nProcessing query...")
                print("------------------")
                
                # Process the query
                result = await client.process_query(query)
                
                # Display the results in a formatted way
                print("\nResults:")
                print("--------")
                
                # Show classification
                if "classification" in result:
                    print(f"Query Type: {result['classification']}")
                
                # Show status
                if "status" in result:
                    status = result["status"]
                    status_color = "\033[92m" if status == "success" else "\033[91m"  # Green for success, red for others
                    print(f"Status: {status_color}{status}\033[0m")
                
                # Show response
                if "response" in result:
                    print("\nResponse:")
                    print("---------")
                    print(result["response"])
                
                # Show any additional results
                if "results" in result and result["results"]:
                    print("\nDetailed Results:")
                    print("----------------")
                    for item in result["results"]:
                        print(f"\nFunction: {item['function_name']}")
                        if "args" in item:
                            print("Arguments:", json.dumps(item['args'], indent=2))
                        if "result" in item:
                            print("Result:", json.dumps(item['result'], indent=2))
                
                # Show any notes
                if "note" in result:
                    print("\nNote:", result["note"])
                
                print("\n" + "="*50)  # Separator line
                
            except KeyboardInterrupt:
                print("\nInterrupted by user. Type 'exit' to quit.")
            except Exception as e:
                print(f"\n\033[91mError: {str(e)}\033[0m")  # Show errors in red
                logger.error(f"Error processing query: {e}")
    
    except Exception as e:
        print(f"\n\033[91mConnection Error: {str(e)}\033[0m")
        logger.error(f"Connection error: {e}")
    finally:
        print("\nClosing connection...")
        await client.close()
        print("Connection closed.")

def main():
    """Main entry point."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Server: python memory_query.py server [--host HOST] [--port PORT]")
        print("  Client: python memory_query.py client")
        sys.exit(1)
        
    if sys.argv[1] == "server":
        # Parse server arguments
        host = "0.0.0.0"
        port = 8765
        i = 2
        while i < len(sys.argv):
            if sys.argv[i] == "--host":
                host = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == "--port":
                port = int(sys.argv[i + 1])
                i += 2
            else:
                i += 1
                
        try:
            asyncio.run(run_server(host=host, port=port))
        except KeyboardInterrupt:
            logger.info("Server stopped by user")
    elif sys.argv[1] == "client":
        try:
            asyncio.run(run_client_example())
        except KeyboardInterrupt:
            logger.info("Client stopped by user")
    else:
        print("Invalid argument. Use 'server' or 'client'")
        sys.exit(1)

if __name__ == "__main__":
    main() 