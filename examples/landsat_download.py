#!/usr/bin/env python3
"""
Example script for downloading Landsat data using the MemoryManager.
"""

import os
import logging
from datetime import datetime, timedelta
from pathlib import Path
from memories.core.memory_manager import MemoryManager
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

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

# Create a data directory using absolute path
try:
    # Try using __file__ if available (script mode)
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "landsat")
except NameError:
    # Fallback for interactive mode or notebook
    data_dir = os.path.join(os.getcwd(), "data", "landsat")

os.makedirs(data_dir, exist_ok=True)
print(f"Using data directory: {data_dir}")

# Initialize memory manager
memory_manager = MemoryManager()

# Get Landsat connector with explicit data directory and disable cold storage
landsat = memory_manager.get_connector(
    'landsat', 
    data_dir=data_dir,
    keep_files=True, 
    store_in_cold=False
)

# Initialize the connector and download the data
try:
    # We need to use asyncio to run the async functions
    import asyncio
    
    # Define a function to run our async operations
    async def run_download():
        # Initialize the connector
        success = await landsat.initialize()
        if not success:
            print("Failed to initialize Landsat connector")
            return
        
        # Download the data
        result = await landsat.download_data(
            bbox=sf_bbox,
            start_date=start_date,
            end_date=end_date,
            bands=["red", "green", "blue"],  # Natural color
            cloud_cover=90.0,
            collection="landsat-c2-l2"
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
        
        # Cleanup
        await memory_manager.reset()
    
    # Run the async function
    asyncio.run(run_download())
    
except Exception as e:
    print(f"Error downloading Landsat data: {e}")

print("\n--- Common band combinations ---")
print("Natural Color: [\"red\", \"green\", \"blue\"]")
print("False Color (vegetation): [\"nir08\", \"red\", \"green\"]")
print("Agriculture: [\"swir16\", \"nir08\", \"red\"]")
print("Atmospheric Penetration: [\"swir22\", \"swir16\", \"nir08\"]")
print("Healthy Vegetation: [\"nir08\", \"swir16\", \"red\"]") 