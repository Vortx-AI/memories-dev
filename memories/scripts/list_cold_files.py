#!/usr/bin/env python3
"""
Script to list all files stored in Cold storage.

This script provides a command-line interface for viewing all files that have
been stored in Cold storage using the file-based storage approach.

Usage:
    python3 list_cold_files.py

The script will display a list of all files in Cold storage, including their
paths, sizes, and metadata.
"""

import asyncio
import sys
import logging
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def format_size(size_bytes):
    """Format file size in a human-readable format."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

def format_timestamp(timestamp_str):
    """Format a timestamp string into a more readable format."""
    try:
        # Parse ISO format timestamp
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        # Format as a readable string
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return timestamp_str

async def main():
    """Main function to list files in Cold storage."""
    # Import here to avoid circular imports
    from memories.core.cold import ColdMemory
    
    # Initialize Cold memory
    cold_memory = ColdMemory()
    
    try:
        # List all files in cold storage
        files = await cold_memory.list_registered_files()
        
        if not files:
            print("No files found in Cold storage.")
            return
        
        print(f"\n{'=' * 80}")
        print(f"COLD STORAGE FILES: {len(files)} files found")
        print(f"{'=' * 80}")
        
        for i, file_info in enumerate(files):
            file_path = file_info.get('file_path')
            size = file_info.get('size', 0)
            created_at = file_info.get('timestamp')
            
            print(f"\n{i+1}. File: {os.path.basename(file_path)}")
            print(f"   Path: {file_path}")
            print(f"   Size: {format_size(size)}")
            
            # Add more details if available
            if created_at:
                print(f"   Created: {format_timestamp(created_at)}")
            
            # Print metadata excluding some verbose fields
            print("   Metadata:")
            for key, value in file_info.items():
                if key not in ['file_path', 'size', 'timestamp', 'id'] and value:
                    print(f"      {key}: {value}")
        
        print(f"\n{'=' * 80}\n")
        
    except Exception as e:
        logger.error(f"Error listing files in Cold storage: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 