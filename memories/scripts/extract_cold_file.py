#!/usr/bin/env python3
"""
Script to extract a file from Cold storage to a specified location.

This script provides a command-line interface for retrieving a file that has
been stored in Cold storage using the file-based storage approach and extracting
it to a specified location.

Usage:
    python3 extract_cold_file.py [file_id_or_path] [destination_path]

Example:
    python3 extract_cold_file.py data/cold/files/20230415_123456_my_data.pkl /tmp/extracted_data.pkl
    python3 extract_cold_file.py some-uuid-from-list-command /tmp/extracted_data.pkl

The script will copy the file from Cold storage to the specified destination.
"""

import asyncio
import sys
import logging
import os
import shutil
from pathlib import Path
from typing import Optional, Union
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

async def find_file_in_cold_storage(cold_memory, file_id_or_path: str) -> Union[str, None]:
    """Find a file in Cold storage by ID or path."""
    # If the input is a direct file path and exists, return it
    if os.path.exists(file_id_or_path):
        return file_id_or_path
    
    # Otherwise, try to find it in the registered files
    try:
        files = await cold_memory.list_registered_files()
        for file_info in files:
            # Check if the ID matches
            if file_info.get('id') == file_id_or_path:
                return file_info.get('file_path')
            
            # Check if the filename part matches
            file_path = file_info.get('file_path', '')
            if os.path.basename(file_path) == os.path.basename(file_id_or_path):
                return file_path
            
            # Check if the path contains the input as a substring
            if file_id_or_path in file_path:
                return file_path
        
        # If we get here, no match was found
        return None
    except Exception as e:
        logger.error(f"Error finding file in Cold storage: {e}")
        return None

async def main():
    """Main function to extract a file from Cold storage."""
    # Check arguments
    if len(sys.argv) < 3:
        print("Usage: python3 extract_cold_file.py [file_id_or_path] [destination_path]")
        sys.exit(1)
    
    # Get arguments
    file_id_or_path = sys.argv[1]
    destination_path = sys.argv[2]
    
    # Import here to avoid circular imports
    from memories.core.cold import ColdMemory
    
    # Initialize Cold memory
    cold_memory = ColdMemory()
    
    # Find the file in Cold storage
    source_path = await find_file_in_cold_storage(cold_memory, file_id_or_path)
    
    if not source_path:
        logger.error(f"File not found in Cold storage: {file_id_or_path}")
        sys.exit(1)
    
    # Ensure the destination directory exists
    os.makedirs(os.path.dirname(os.path.abspath(destination_path)), exist_ok=True)
    
    try:
        # Copy the file to the destination
        shutil.copy2(source_path, destination_path)
        logger.info(f"File extracted successfully:")
        logger.info(f"  Source: {source_path}")
        logger.info(f"  Destination: {destination_path}")
        
        # Get file info
        file_size = Path(destination_path).stat().st_size
        logger.info(f"  File size: {file_size} bytes ({file_size / 1024 / 1024:.2f} MB)")
        
    except Exception as e:
        logger.error(f"Error extracting file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 