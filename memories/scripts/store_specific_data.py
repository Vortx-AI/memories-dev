#!/usr/bin/env python
"""
Simple script to store specific data in Glacier Memory using the GCS connector.
"""

import os
import asyncio
import sys
import json
from dotenv import load_dotenv
from memories.core.glacier import GlacierMemory

# Load environment variables from .env file
load_dotenv()

async def store_data(data, key):
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
    success = await glacier.store(data, key)
    
    if success:
        print(f"Successfully stored data with key: {key}")
    else:
        print(f"Failed to store data with key: {key}")
    
    return success

async def main():
    """Main function to store data."""
    # Check if data and key are provided as command line arguments
    if len(sys.argv) < 3:
        print("Usage: python store_specific_data.py <data> <key>")
        print("Example: python store_specific_data.py 'Hello World' 'test/hello.txt'")
        return
    
    # Get data and key from command line arguments
    data = sys.argv[1]
    key = sys.argv[2]
    
    # Try to parse data as JSON if it starts with { or [
    if data.startswith('{') or data.startswith('['):
        try:
            data = json.loads(data)
            print("Data parsed as JSON")
        except json.JSONDecodeError:
            print("Data provided as string (JSON parsing failed)")
    
    # Store the data
    await store_data(data, key)

if __name__ == "__main__":
    asyncio.run(main()) 