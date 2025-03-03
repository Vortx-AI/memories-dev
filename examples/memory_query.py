"""
Memory query implementation for handling different types of queries.
"""

from typing import Dict, Any, Union, Optional
import logging
import os
import json
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
            self.code_executor = CodeExecution()
            
            # Load function definitions
            self.function_mapping = {
                "get_bounding_box": get_bounding_box_from_address,
                "get_bounding_box_from_coords": get_bounding_box_from_coords,
                "get_address_from_coords": get_address_from_coords,
                "get_coords_from_address": get_coords_from_address,
                "get_data_by_bbox": self.get_data_by_bbox_wrapper,
                "execute_code": self.code_executor.execute_code
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
                from memories.core.cold_memory import ColdMemory
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

def main():
    """Main function to demonstrate memory query usage."""
    try:
        # Get API key from environment variable or user input
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            api_key = input("Please enter your OpenAI API key: ")
        
        # Initialize memory query with specific model parameters
        memory_query = MemoryQuery(
            model_provider="openai",
            deployment_type="api",
            model_name="gpt-4",
            api_key=api_key
        )
        
        print("\nMemory Query System initialized successfully!")
        print("Type 'exit' to quit the program")
       
        
        while True:
            # Get query from user
            query = input("\nEnter your query: ").strip()
            
            # Check if user wants to exit
            if query.lower() == 'exit':
                print("Exiting Memory Query System...")
                break
            
            # Process the query
            if query:
                result = memory_query.process_query(query)
                print(f"\nClassification: {result['classification']}")
                print(f"Response: {result['response']}")
                print(f"Status: {result['status']}")
                if "note" in result:
                    print(f"Note: {result['note']}")
            else:
                print("Please enter a valid query.")

    except Exception as e:
        logger.error(f"Error in main: {e}")

if __name__ == "__main__":
    main() 