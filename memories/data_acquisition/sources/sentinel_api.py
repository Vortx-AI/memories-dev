"""
Sentinel-2 data source using Planetary Computer.
"""

import os
import logging
import asyncio
import planetary_computer
import pystac_client
import rasterio
import numpy as np
from datetime import datetime
from pathlib import Path
from shapely.geometry import box
from rasterio.windows import Window
from typing import Dict, Any, Optional, List
import json

class SentinelAPI:
    """Interface for accessing Sentinel-2 data using Planetary Computer."""

    def __init__(self, data_dir: Optional[str] = None):
        """Initialize the Sentinel-2 interface.
        
        Args:
            data_dir: Directory to store downloaded data. Defaults to current directory.
        """
        self.data_dir = Path(data_dir or os.getcwd())
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize the STAC client
        self.client = pystac_client.Client.open(
            "https://planetarycomputer.microsoft.com/api/stac/v1",
            modifier=planetary_computer.sign_inplace
        )

    async def fetch_windowed_band(self, url: str, bbox: Dict[str, float], band_name: str, data_dir: Optional[Path] = None) -> bool:
        """Download a specific band from a Sentinel scene for a given bounding box.
        
        Args:
            url: URL of the band image
            bbox: Dictionary containing xmin, ymin, xmax, ymax
            band_name: Name of the band to download
            data_dir: Optional directory to save the data (defaults to self.data_dir)
            
        Returns:
            bool: True if successful, False otherwise
        """
        data_dir = data_dir or self.data_dir
        os.makedirs(data_dir, exist_ok=True)
        output_file = data_dir / f"{band_name}.tif"
        
        try:
            logging.info(f"Downloading band {band_name} from {url}")
            
            with rasterio.Env():
                with rasterio.open(url) as src:
                    window = src.window(bbox['xmin'], bbox['ymin'], bbox['xmax'], bbox['ymax'])
                    window_transform = src.window_transform(window)
                    
                    # Read the data for the window
                    data = src.read(1, window=window)
                    mask = src.read_masks(1, window=window)
                    
                    # Create output profile
                    profile = src.profile.copy()
                    profile.update({
                        'driver': 'GTiff',
                        'height': window.height,
                        'width': window.width,
                        'transform': window_transform
                    })
                    
                    # Write the output file
                    with rasterio.open(output_file, 'w', **profile) as dst:
                        dst.write(data, 1)
                        dst.write_mask(mask)
            
            return True
        except Exception as e:
            logging.error(f"Error downloading band {band_name}: {str(e)}")
            return False

    async def download_data(
        self,
        bbox: Dict[str, float],
        start_date: datetime,
        end_date: datetime,
        cloud_cover: float = 10.0,
        bands: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Download Sentinel-2 data for a given bounding box and time range.
        
        Args:
            bbox: Dictionary containing xmin, ymin, xmax, ymax
            start_date: Start date for the search
            end_date: End date for the search
            cloud_cover: Maximum cloud cover percentage (default: 10.0)
            bands: Optional list of bands to download (default: ["B04", "B08"])
            
        Returns:
            Dict containing status and metadata
        """
        try:
            # Create data directory if it doesn't exist
            os.makedirs(self.data_dir, exist_ok=True)
            
            # Convert bbox to WKT for search
            bbox_polygon = box(bbox['xmin'], bbox['ymin'], bbox['xmax'], bbox['ymax'])
            logging.info(f"Searching for scenes in area: {bbox_polygon}")
            
            # Set default bands if not provided
            if bands is None:
                bands = ["B04", "B08"]
            
            # Validate bands
            valid_bands = ["B01", "B02", "B03", "B04", "B05", "B06", "B07", "B08", "B8A", "B09", "B11", "B12"]
            if not all(band in valid_bands for band in bands):
                return {
                    "status": "error",
                    "message": "Invalid bands specified"
                }
            
            # Search for scenes
            search = self.client.search(
                collections=["sentinel-2-l2a"],
                intersects=bbox_polygon,
                datetime=[start_date.isoformat(), end_date.isoformat()],
                query={"eo:cloud_cover": {"lt": cloud_cover}}
            )
            
            items = list(search.get_items())
            if not items:
                return {
                    "status": "error",
                    "message": "No suitable imagery found"
                }
            
            # Get the first item (most recent)
            item = items[0]
            
            # Download each band
            downloaded_bands = []
            for band in bands:
                if band in item.assets:
                    signed_url = planetary_computer.sign(item.assets[band].href)
                    if await self.fetch_windowed_band(signed_url, bbox, band):
                        downloaded_bands.append(band)
            
            if not downloaded_bands:
                return {
                    "status": "error",
                    "message": "No suitable imagery found"
                }
            
            # Save metadata
            metadata = {
                "scene_id": item.id,
                "cloud_cover": item.properties.get("eo:cloud_cover", 0),
                "datetime": item.properties.get("datetime"),
                "bands": downloaded_bands
            }
            
            with open(self.data_dir / "metadata.json", "w") as f:
                json.dump(metadata, f)
            
            return {
                "status": "success",
                "metadata": metadata
            }
            
        except Exception as e:
            logging.error(f"Error downloading data: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }