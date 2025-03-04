#!/usr/bin/env python3
import os
import sys
import uvicorn
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def main():
    """Start the Memory Query API server."""
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    print(f"Starting Memory Query API server on {host}:{port}")
    print(f"API documentation will be available at http://{host}:{port}/docs")
    
    uvicorn.run(
        "memories.interface.api.main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main() 