#!/usr/bin/env python
"""
Script to store a file in Glacier Memory using the GCS connector.
"""

import os
import asyncio
import sys
import json
from pathlib import Path
from dotenv import load_dotenv
from memories.core.glacier import GlacierMemory

# Load environment variables from .env file
load_dotenv()

async def store_file(file_path, key=None, metadata=None):
    """Store a file in Glacier Memory using GCS connector."""
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
    
    # Convert file path to Path object
    file_path = Path(file_path)
    
    # Generate key if not provided
    if key is None:
        key = f"files/{file_path.name}"
    
    # Generate metadata if not provided
    if metadata is None:
        metadata = {
            "original_filename": file_path.name,
            "original_path": str(file_path.absolute()),
            "file_size": file_path.stat().st_size,
            "file_extension": file_path.suffix
        }
    
    # Read the file
    try:
        with open(file_path, 'rb') as f:
            file_content = f.read()
            
        # For text files, try to decode
        if file_path.suffix.lower() in ['.txt', '.json', '.py', '.md', '.csv', '.yml', '.yaml', '.html', '.css', '.js']:
            try:
                file_content = file_content.decode('utf-8')
                
                # If it's a JSON file, parse it
                if file_path.suffix.lower() == '.json':
                    try:
                        file_content = json.loads(file_content)
                        metadata['content_type'] = 'application/json'
                    except json.JSONDecodeError:
                        metadata['content_type'] = 'text/plain'
                else:
                    metadata['content_type'] = 'text/plain'
            except UnicodeDecodeError:
                # If decoding fails, keep as binary
                metadata['content_type'] = 'application/octet-stream'
        else:
            # Binary file
            metadata['content_type'] = 'application/octet-stream'
        
        # Store the file
        success = await glacier.store(file_content, key, metadata)
        
        if success:
            print(f"Successfully stored file '{file_path}' with key: {key}")
        else:
            print(f"Failed to store file '{file_path}' with key: {key}")
        
        return success
        
    except Exception as e:
        print(f"Error storing file: {str(e)}")
        return False

async def main():
    """Main function to store a file."""
    # Check if file path is provided as command line argument
    if len(sys.argv) < 2:
        print("Usage: python store_file_in_glacier.py <file_path> [key]")
        print("Example: python store_file_in_glacier.py data.json data/my_data.json")
        return
    
    # Get file path from command line arguments
    file_path = sys.argv[1]
    
    # Get optional key from command line arguments
    key = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Store the file
    await store_file(file_path, key)

if __name__ == "__main__":
    asyncio.run(main()) 