#!/usr/bin/env python
"""
Script to store data in Glacier Memory using the GCS connector.
"""

import os
import asyncio
import json
from pathlib import Path
from dotenv import load_dotenv
from memories.core.glacier import GlacierMemory

# Load environment variables from .env file
load_dotenv()

async def store_data_in_glacier(data, key, metadata=None):
    """Store data in Glacier Memory using GCS connector."""
    # Create configuration using environment variables
    config = {
        'storage': {
            'type': 'gcs',
            'config': {
                'bucket_name': os.getenv('GCP_BUCKET_NAME', 'glacier_tier'),
                'project_id': os.getenv('GCP_PROJECT_ID'),
                'credentials_path': os.getenv('GCP_CREDENTIALS_PATH')
            }
        }
    }
    
    # Initialize Glacier Memory with the configuration
    glacier = GlacierMemory(config)
    
    # Store the data
    success = await glacier.store(data, key, metadata)
    
    if success:
        print(f"Successfully stored data with key: {key}")
    else:
        print(f"Failed to store data with key: {key}")
    
    return success

async def main():
    """Main function to demonstrate storing data."""
    # Example data to store
    sample_data = {
        "name": "Sample Document",
        "content": "This is a test document stored in Glacier Memory",
        "tags": ["test", "sample", "glacier"]
    }
    
    # Example metadata
    metadata = {
        "created_by": "store_glacier_data.py",
        "content_type": "application/json",
        "description": "Sample test document"
    }
    
    # Store the data with a unique key
    key = f"sample/document_{int(asyncio.get_event_loop().time())}.json"
    
    await store_data_in_glacier(sample_data, key, metadata)
    
    # You can also store a file
    # Get the path to this script
    script_path = Path(__file__)
    
    # Store this script as an example file
    with open(script_path, 'r') as f:
        file_content = f.read()
    
    file_key = f"sample/files/script_{script_path.name}"
    file_metadata = {
        "file_type": "python",
        "original_path": str(script_path)
    }
    
    await store_data_in_glacier(file_content, file_key, file_metadata)

if __name__ == "__main__":
    asyncio.run(main()) 