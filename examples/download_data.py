#!/usr/bin/env python3
"""
Example script demonstrating data download using Overture and Sentinel APIs.
"""

import os
import sys
import asyncio
from pathlib import Path
from memories.data_acquisition.sources.overture_api import OvertureAPI
from memories.data_acquisition.sources.sentinel_api import SentinelAPI
from memories import Config

# San Francisco Financial District (1km x 1km)
SF_BBOX = {
    'xmin': -122.4018,  # Approximately Market & Montgomery
    'ymin': 37.7914,
    'xmax': -122.3928,  # About 1km east
    'ymax': 37.7994     # About 1km north
}

def setup_directories(config):
    """Create all necessary data directories."""
    for path in config.config['data'].values():
        Path(path).mkdir(parents=True, exist_ok=True)

async def main():
    """Download Overture Maps and satellite data for San Francisco."""
    print("=== Downloading Data for San Francisco Financial District ===")
    
    # Initialize config and create directories
    config = Config()
    setup_directories(config)
    
    # Initialize APIs with config paths
    overture_api = OvertureAPI(data_dir=config.config['data']['overture_path'])
    sentinel_api = SentinelAPI(data_dir=config.config['data']['satellite_path'])
    
    # Download Overture data
    print("\n=== Downloading Overture Maps Data ===")
    overture_results = overture_api.download_data(SF_BBOX)
    
    if all(overture_results.values()):
        print("\nSuccessfully downloaded all Overture themes:")
        for theme, success in overture_results.items():
            print(f"- {theme}: {'✓' if success else '✗'}")
    else:
        print("\nSome Overture downloads failed:")
        for theme, success in overture_results.items():
            print(f"- {theme}: {'✓' if success else '✗'}")
    
    # Download satellite data
    print("\n=== Downloading Satellite Imagery ===")
    satellite_results = await sentinel_api.download_data(
        bbox=SF_BBOX,
        cloud_cover=10.0,
        bands={
            "B04": "Red",
            "B08": "NIR",
            "B11": "SWIR"
        }
    )
    
    if satellite_results.get("success"):
        print("\nSuccessfully downloaded satellite data:")
        metadata = satellite_results["metadata"]
        print(f"- Scene ID: {metadata['scene_id']}")
        print(f"- Date: {metadata['datetime']}")
        print(f"- Cloud cover: {metadata['cloud_cover']}%")
        print(f"- Bands: {', '.join(metadata['bands_downloaded'])}")
    else:
        print("\nSatellite data download failed:")
        print(f"- Error: {satellite_results.get('error')}")
        if 'failed_bands' in satellite_results:
            print(f"- Failed bands: {', '.join(satellite_results['failed_bands'])}")
    
    print("\n🎉 Download complete!")

if __name__ == "__main__":
    asyncio.run(main()) 