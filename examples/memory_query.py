"""Memory query implementation for handling different types of queries.
Supports REST API interface with HTTP/HTTPS support.
"""

import os
import sys
import logging
import uvicorn
import ssl
import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import argparse
from dotenv import load_dotenv

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)
logger.info(f"Loading environment from {env_path}")

# Set default API key
DEFAULT_API_KEY = os.getenv('MEMORY_API_KEY', 'default-memory-key-12345')
os.environ['MEMORY_API_KEY'] = DEFAULT_API_KEY

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

class MemoryQueryProcessor:
    """Memory Query Processor for handling different types of queries."""
    
    def __init__(self):
        """Initialize the Memory Query Processor."""
        self.model = LoadModel()
        self.memory_retrieval = MemoryRetrieval()
        self.code_execution = CodeExecution()
        
    async def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a memory query and return appropriate response.
        
        Args:
            query: The query text to process
            
        Returns:
            Dict containing the processed response
        """
        try:
            # First classify the query
            classification = classify_query(query, self.model)
            logger.info(f"Query classification: {classification}")
            
            if classification["classification"] == "L1_2":
                # Handle location-based query
                location_info = classification.get("location_details", {})
                if location_info:
                    # Get coordinates for the location
                    coords = await get_coords_from_address(location_info["text"])
                    if coords:
                        # Get bounding box for the location
                        bbox = get_bounding_box_from_coords(*coords)
                        # Retrieve memories for the location
                        memories = await self.memory_retrieval.get_memories_for_location(bbox)
                        return {
                            "type": "location_based",
                            "query": query,
                            "location": location_info,
                            "coordinates": coords,
                            "memories": memories,
                            "timestamp": datetime.now().isoformat()
                        }
                
            # For non-location queries or if location processing fails
            # Get direct response from the model
            response = self.model.get_response(query)
            
            return {
                "type": "direct_response",
                "query": query,
                "response": response.get("text"),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                "error": str(e),
                "query": query,
                "timestamp": datetime.now().isoformat()
            }

def run_server(
    host: str = "0.0.0.0",
    port: int = 8000,
    reload: bool = False,
    workers: int = 1,
    log_level: str = "info"
) -> None:
    """
    Run the API server.
    
    Args:
        host: Host to bind to
        port: Port to bind to
        reload: Enable auto-reload for development
        workers: Number of worker processes
        log_level: Logging level
    """
    logger.info(f"Starting {PROJECT_TITLE} {VERSION}")
    logger.info(f"API Documentation: http://{host}:{port}/docs")
    logger.info(f"Using API key: {DEFAULT_API_KEY}")
    
    # Initialize the memory query processor
    processor = MemoryQueryProcessor()
    
    # Update the API route to use the processor
    from memories.interface.api.routers.memory import router, MemoryRequest, MemoryResponse
    
    @router.post("/process", response_model=MemoryResponse)
    async def process_memory(request: MemoryRequest):
        """Process a memory request"""
        try:
            # Process the query
            result = await processor.process_query(request.text)
            
            return MemoryResponse(
                status="success",
                message="Request processed successfully",
                data=result,
                timestamp=datetime.now()
            )
        except Exception as e:
            logger.error(f"Error processing memory request: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    config = uvicorn.Config(
        app="memories.interface.api.main:app",
        host=host,
        port=port,
        reload=reload,
        workers=workers,
        log_level=log_level
    )
    
    server = uvicorn.Server(config)
    server.run()

def main():
    """Main entry point for the memory query server."""
    parser = argparse.ArgumentParser(description=PROJECT_DESCRIPTION)
    parser.add_argument("--host", type=str, default="0.0.0.0",
                      help="Host to bind to (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000,
                      help="Port to bind to (default: 8000)")
    parser.add_argument("--reload", action="store_true",
                      help="Enable auto-reload for development")
    parser.add_argument("--workers", type=int, default=1,
                      help="Number of worker processes (default: 1)")
    parser.add_argument("--log-level", type=str, default="info",
                      choices=["debug", "info", "warning", "error", "critical"],
                      help="Logging level (default: info)")
    
    args = parser.parse_args()
    
    try:
        run_server(
            host=args.host,
            port=args.port,
            reload=args.reload,
            workers=args.workers,
            log_level=args.log_level
        )
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise

if __name__ == "__main__":
    main() 