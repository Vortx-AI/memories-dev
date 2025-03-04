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

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)
logger.info(f"Loading environment from {env_path}")

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