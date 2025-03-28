#!/usr/bin/env python3
"""
Landsat Data Download Example
----------------------------
This script demonstrates how to download Landsat satellite imagery
using the Memories framework.
"""

import asyncio
from datetime import datetime, timedelta
import logging
from pathlib import Path
import os
from dotenv import load_dotenv

from memories.core.memory_manager import MemoryManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

async def download_landsat_data(
    bbox: dict,
    start_date: datetime,
    end_date: datetime,
    bands: list = ["red", "nir08"],
    cloud_cover: float = 30.0,
    collection: str = "landsat-c2-l2",
    data_dir: str = None
) -> dict:
    """
    Download Landsat satellite data for a specified area and time range.
    
    Args:
        bbox: Dictionary with bounding box coordinates (xmin, ymin, xmax, ymax)
        start_date: Start date for data retrieval
        end_date: End date for data retrieval
        bands: List of band names to download (default: ["red", "nir08"])
        cloud_cover: Maximum cloud cover percentage (default: 30.0)
        collection: Landsat collection ID (default: "landsat-c2-l2")
        data_dir: Directory to store downloaded data (default: None)
        
    Returns:
        Dictionary containing download results and metadata
    """
    try:
        # Initialize memory manager
        memory_manager = MemoryManager()
        
        # Create an explicit data directory if not provided
        if data_dir is None:
            data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "landsat")
            os.makedirs(data_dir, exist_ok=True)
            logger.info(f"Using data directory: {data_dir}")
        
        # Get Landsat connector with explicit data directory and disable cold storage to avoid path issues
        landsat = memory_manager.get_connector(
            'landsat', 
            data_dir=data_dir,
            keep_files=True, 
            store_in_cold=False
        )
        
        try:
            # Initialize the connector
            success = await landsat.initialize()
            if not success:
                return {"status": "error", "message": "Failed to initialize Landsat connector"}
            
            # Download the data
            result = await landsat.download_data(
                bbox=bbox,
                start_date=start_date,
                end_date=end_date,
                bands=bands,
                cloud_cover=cloud_cover,
                collection=collection
            )
            
            if result["status"] == "success":
                logger.info(f"Successfully downloaded Landsat data:")
                logger.info(f"Scene ID: {result['scene_id']}")
                logger.info(f"Cloud Cover: {result['cloud_cover']}%")
                logger.info(f"Downloaded Bands: {result['bands']}")
                logger.info(f"Datetime: {result['metadata']['datetime']}")
                logger.info(f"Platform: {result['metadata']['platform']}")
            else:
                logger.error(f"Failed to download data: {result['message']}")
            
            return result
            
        finally:
            # Cleanup resources
            try:
                await memory_manager.reset()
            except Exception as e:
                logger.error(f"Error during cleanup: {str(e)}")
    except Exception as e:
        logger.error(f"Error in download_landsat_data: {str(e)}")
        return {"status": "error", "message": str(e)}

async def main():
    """Main execution function."""
    
    # Example bounding box for San Francisco
    sf_bbox = {
        "xmin": -122.5155,
        "ymin": 37.7079,
        "xmax": -122.3555,
        "ymax": 37.8119
    }
    
    # Time range for the last 365 days
    end_date = datetime.now() - timedelta(days=30)  # Use data from 30 days ago
    start_date = end_date - timedelta(days=365)  # Look back 1 year
    
    print(f"Downloading Landsat data for San Francisco")
    print(f"Time range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"Bounding box: {sf_bbox}")
    print(f"Cloud cover threshold: 90.0%")
    
    # Create a data directory that will definitely work
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "landsat")
    os.makedirs(data_dir, exist_ok=True)
    print(f"Using data directory: {data_dir}")
    
    # Download data for natural color bands
    try:
        result = await download_landsat_data(
            bbox=sf_bbox,
            start_date=start_date,
            end_date=end_date,
            bands=["red", "green", "blue"],  # Natural color
            cloud_cover=90.0,
            collection="landsat-c2-l2",
            data_dir=data_dir
        )
        
        # Print results
        if result["status"] == "success":
            print("\nData download completed successfully!")
            print(f"Data stored in: {os.path.abspath(data_dir)}")
            print(f"\nScene ID: {result['scene_id']}")
            print(f"Cloud Cover: {result['cloud_cover']}%")
            print(f"Downloaded Bands: {result['bands']}")
            print(f"Datetime: {result['metadata']['datetime']}")
            print(f"Platform: {result['metadata']['platform']}")
        else:
            print("\nData download failed.")
            print(f"Error: {result.get('message', 'Unknown error')}")
            print("\nSearch parameters used:")
            print(f"Time range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
            print(f"Bounding box: {sf_bbox}")
            print(f"Cloud cover threshold: 90.0%")
    except Exception as e:
        print(f"\nFailed to download Landsat data: {str(e)}")
    
    print("\n--- Common band combinations ---")
    print("Natural Color: [\"red\", \"green\", \"blue\"]")
    print("False Color (vegetation): [\"nir08\", \"red\", \"green\"]")
    print("Agriculture: [\"swir16\", \"nir08\", \"red\"]")
    print("Atmospheric Penetration: [\"swir22\", \"swir16\", \"nir08\"]")
    print("Healthy Vegetation: [\"nir08\", \"swir16\", \"red\"]")

if __name__ == "__main__":
    asyncio.run(main()) 