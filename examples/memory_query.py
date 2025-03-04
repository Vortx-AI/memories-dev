"""
Memory query implementation for handling different types of queries.
"""

from typing import Dict, Any, Union, Optional
import logging
import os
import json
from pathlib import Path
from datetime import datetime, date
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from enum import Enum
import numpy as np
import pandas as pd

from memories.models.load_model import LoadModel
from memories.utils.text.context_utils import classify_query
from memories.utils.earth.location_utils import (
    get_bounding_box_from_address,
    get_bounding_box_from_coords,
    get_address_from_coords,
    get_coords_from_address,
    
)
from memories.core.memory_retrieval import MemoryRetrieval
from memories.utils.code.code_execution import CodeExecution

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)
logger.info(f"Loading environment from {env_path}")

# Set default API key
DEFAULT_API_KEY = os.getenv('MEMORY_API_KEY', 'a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6')
os.environ['MEMORY_API_KEY'] = DEFAULT_API_KEY

# Create FastAPI app with metadata
app = FastAPI(
    title="Memory Query API",
    description="API for processing memory queries with advanced functionality",
    version="1.0.0"
)

# Define MessageType enum for API
class MessageType(str, Enum):
    TEXT = "text"
    QUERY = "query"
    COMMAND = "command"

# Define request/response models for API
class MemoryRequest(BaseModel):
    text: str = Field(..., description="Text content to process")
    message_type: MessageType = Field(default=MessageType.QUERY, description="Type of message")
    api_key: Optional[str] = Field(default=None, description="Optional API key for authentication")

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
                "search_geospatial_data_in_bbox": self.search_geospatial_data_in_bbox_wrapper,
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

    def serialize_result(self, obj):
        """Helper function to make results JSON serializable."""
        if isinstance(obj, bytearray):
            return obj.hex()  # Convert bytearray to hex string
        elif isinstance(obj, bytes):
            return obj.hex()
        elif isinstance(obj, pd.DataFrame):
            return obj.to_dict('records')
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif isinstance(obj, (int, float, str, bool, type(None))):
            return obj
        elif isinstance(obj, (list, tuple)):
            return [self.serialize_result(item) for item in obj]
        elif isinstance(obj, dict):
            return {k: self.serialize_result(v) for k, v in obj.items()}
        else:
            return str(obj)  # Convert any other type to string

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
                            "classification": query_type,
                            "response": f"Error in chat completion: {response['error']}",
                            "status": "error"
                        }
                    
                    assistant_message = response.get("message", {})
                    tool_calls = response.get("tool_calls", [])
                    
                    if not tool_calls and assistant_message.get("content"):
                        return {
                            "classification": query_type,
                            "response": assistant_message.get("content"),
                            "status": "success",
                            "results": results
                        }
                    
                    if tool_calls:
                        for tool_call in tool_calls:
                            function_name = tool_call.get("function", {}).get("name")
                            
                            try:
                                args = json.loads(tool_call["function"]["arguments"])
                                
                                if function_name in self.function_mapping:
                                    function_result = self.function_mapping[function_name](**args)
                                    # Serialize the result before storing
                                    serialized_result = self.serialize_result(function_result)
                                else:
                                    return {
                                        "classification": query_type,
                                        "response": f"Unknown function: {function_name}",
                                        "status": "error"
                                    }
                                
                                results.append({
                                    "function_name": function_name,
                                    "args": args,
                                    "result": serialized_result
                                })
                                
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
                                    "content": json.dumps(serialized_result)
                                })
                                
                            except Exception as e:
                                logger.error(f"Error processing tool call: {e}")
                                return {
                                    "classification": query_type,
                                    "response": f"Error: {str(e)}",
                                    "status": "error"
                                }
                        
                        messages.append({
                            "role": "system",
                            "content": "Based on these results, decide if you need more information or can provide a final answer."
                        })
                        continue
                        
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

# Initialize global memory query instance
memory_query = None

@app.on_event("startup")
async def startup_event():
    """Initialize the memory query system on startup."""
    global memory_query
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        memory_query = MemoryQuery(
            model_provider="openai",
            deployment_type="api",
            model_name="gpt-4",
            api_key=api_key
        )
        logger.info("Memory Query System initialized successfully!")
    except Exception as e:
        logger.error(f"Failed to initialize Memory Query System: {e}")
        raise

@app.post("/api/v1/memory/process", response_model=MemoryResponse)
async def process_memory(request: MemoryRequest):
    """Process a memory request."""
    try:
        if not memory_query:
            raise HTTPException(status_code=500, detail="Memory Query System not initialized")

        # Validate API key if provided
        if request.api_key and request.api_key != DEFAULT_API_KEY:
            raise HTTPException(status_code=401, detail="Invalid API key")

        # Process the query
        result = memory_query.process_query(request.text)
        
        return MemoryResponse(
            status="success" if result["status"] == "success" else "error",
            message="Request processed successfully" if result["status"] == "success" else result.get("response", "Error processing request"),
            data=result,
            timestamp=datetime.now()
        )
    except Exception as e:
        logger.error(f"Error processing memory request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """Root endpoint - provides API information"""
    return {
        "title": "Memory Query API",
        "version": "1.0.0",
        "description": "API for processing memory queries with advanced functionality",
        "endpoints": [
            {
                "path": "/api/v1/memory/process",
                "method": "POST",
                "description": "Process memory queries"
            }
        ]
    }

def run_server(
    host: str = "0.0.0.0",
    port: int = 8000,
    reload: bool = False,
    workers: int = 1,
    log_level: str = "info"
) -> None:
    """Run the API server."""
    logger.info(f"Starting Memory Query API server")
    logger.info(f"API Documentation: http://{host}:{port}/docs")
    logger.info(f"Using API key: {DEFAULT_API_KEY}")
    
    config = uvicorn.Config(
        app="memory_query:app",
        host=host,
        port=port,
        reload=reload,
        workers=workers,
        log_level=log_level
    )
    
    server = uvicorn.Server(config)
    server.run()

if __name__ == "__main__":
    run_server() 