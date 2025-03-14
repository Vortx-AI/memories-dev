#!/usr/bin/env python3
"""
Script to move data directly as files from Glacier to Cold storage.

This script provides a command-line interface for transferring data from
Glacier storage to Cold storage as files, preserving the binary format
without encoding in a database.

Usage:
    python3 tier_file_data.py [glacier_key] [optional_destination_filename]

Example:
    python3 tier_file_data.py dubai_landuse.pkl
    python3 tier_file_data.py dubai_landuse.pkl custom_name.pkl

The script will retrieve data from Glacier storage using the provided key
and store it as a file in the Cold storage location.
"""

import asyncio
import sys
import logging
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

async def main():
    """Main function to transfer data from Glacier to Cold storage as a file."""
    # Check arguments
    if len(sys.argv) < 2:
        print("Usage: python3 tier_file_data.py [glacier_key] [optional_destination_filename]")
        sys.exit(1)
    
    # Get glacier key from command line arguments
    glacier_key = sys.argv[1]
    
    # Get optional destination filename from command line arguments
    destination_filename = None
    if len(sys.argv) >= 3:
        destination_filename = sys.argv[2]
    
    # Import here to avoid circular imports
    from memories.core.memory_tiering import MemoryTiering
    
    # Initialize memory tiering
    memory_tiering = MemoryTiering()
    await memory_tiering.initialize_tiers()
    
    # Transfer data from Glacier to Cold storage as a file
    logger.info(f"Transferring data from Glacier to Cold storage: {glacier_key}")
    success, file_path = await memory_tiering.glacier_to_cold_file(
        key=glacier_key,
        destination_filename=destination_filename
    )
    
    if success:
        logger.info(f"Successfully transferred data to Cold storage")
        logger.info(f"File stored at: {file_path}")
        
        # Get file info
        file_size = Path(file_path).stat().st_size
        logger.info(f"File size: {file_size} bytes ({file_size / 1024 / 1024:.2f} MB)")
    else:
        logger.error(f"Failed to transfer data to Cold storage")
        sys.exit(1)
    
    # List all files in cold storage (if available)
    try:
        files = await memory_tiering.cold.list_registered_files()
        logger.info(f"Files in Cold storage: {len(files)}")
        for i, file_info in enumerate(files):
            logger.info(f"File {i+1}: {file_info.get('file_path')} - {file_info.get('size', 0)} bytes")
    except Exception as e:
        logger.warning(f"Could not list files in Cold storage: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 