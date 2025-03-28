#!/usr/bin/env python3
"""
Sentinel Data Retriever
----------------------
A simple script to download Sentinel satellite imagery for a specified area.
"""

import asyncio
from datetime import datetime, timedelta
from memories.core.memory_manager import MemoryManager
import logging
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

async def download_sentinel_data(
    bbox: dict,
    start_date: datetime,
    end_date: datetime,
    bands: list = ["B04", "B08"],
    cloud_cover: float = 30.0
) -> dict:
    """
    Download Sentinel satellite data for a specified area and time range.
    
    Args:
        bbox: Dictionary with bounding box coordinates (xmin, ymin, xmax, ymax)
        start_date: Start date for data retrieval
        end_date: End date for data retrieval
        bands: List of band names to download (default: ["B04", "B08"])
        cloud_cover: Maximum cloud cover percentage (default: 30.0)
        
    Returns:
        Dictionary containing download results and metadata
    """
    # Initialize memory manager
    memory_manager = MemoryManager()
    
    # Get Sentinel connector
    sentinel = memory_manager.get_connector('sentinel', keep_files=True, store_in_cold=True)
    
    try:
        # Initialize the connector
        success = await sentinel.initialize()
        if not success:
            return {"status": "error", "message": "Failed to initialize Sentinel connector"}
        
        # Download the data
        result = await sentinel.download_data(
            bbox=bbox,
            start_date=start_date,
            end_date=end_date,
            bands=bands,
            cloud_cover=cloud_cover
        )
        
        if result["status"] == "success":
            logger.info(f"Successfully downloaded Sentinel data:")
            logger.info(f"Scene ID: {result['scene_id']}")
            logger.info(f"Cloud Cover: {result['cloud_cover']}%")
            logger.info(f"Downloaded Bands: {result['bands']}")
            logger.info(f"Acquisition Date: {result['metadata']['acquisition_date']}")
            logger.info(f"Platform: {result['metadata']['platform']}")
        else:
            logger.error(f"Failed to download data: {result['message']}")
        
        return result
        
    finally:
        # Cleanup
        if hasattr(sentinel, 'client'):
            sentinel.client = None

async def main():
    """Main execution function."""
    # Example bounding box for San Francisco
    sf_bbox = {
        "xmin": -122.5155,
        "ymin": 37.7079,
        "xmax": -122.3555,
        "ymax": 37.8119
    }
    
    # Time range for the last 90 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    
    # Download data
    result = await download_sentinel_data(
        bbox=sf_bbox,
        start_date=start_date,
        end_date=end_date,
        bands=["B04", "B08"],  # Red and NIR bands
        cloud_cover=30.0
    )
    
    # Print final status
    if result["status"] == "success":
        print("\nData download completed successfully!")
        print(f"Data stored in: {os.path.abspath(os.path.join('data', 'sentinel'))}")
    else:
        print("\nData download failed.")
        print(f"Error: {result.get('message', 'Unknown error')}")

if __name__ == "__main__":
    asyncio.run(main()) 