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
from typing import Dict, Any, Optional, List, Union
import json

class SentinelAPI:
    """Interface for accessing Sentinel-2 data using Planetary Computer."""

    def __init__(self, data_dir: Union[str, Path]):
        """Initialize the Sentinel-2 interface.
        
        Args:
            data_dir (Union[str, Path]): Directory to store downloaded data
        """
        self.data_dir = Path(data_dir)
        os.makedirs(self.data_dir, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self.client = None

    async def initialize(self) -> bool:
        """Initialize the Sentinel API.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Initialize the STAC client
            self.client = pystac_client.Client.open(
                "https://planetarycomputer.microsoft.com/api/stac/v1",
                modifier=planetary_computer.sign_inplace
            )
            return True
        except Exception as e:
            self.logger.error(f"Error initializing Sentinel API: {str(e)}")
            return False

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
        bands: Optional[List[str]] = None,
        cloud_cover: float = 20.0
    ) -> Dict[str, Any]:
        """Download Sentinel-2 data for a given bounding box and time range.

        Args:
            bbox: Bounding box as a dictionary with xmin, ymin, xmax, ymax
            start_date: Start date for the search
            end_date: End date for the search
            bands: List of bands to download (default: ["B04", "B08"])
            cloud_cover: Maximum cloud cover percentage (default: 20.0)

        Returns:
            Dict containing status, message (if error), and data (if success)

        Raises:
            ValueError: If bbox is invalid or if end_date is before start_date
        """
        # Initialize if not already initialized
        if self.client is None:
            if not await self.initialize():
                return {
                    "status": "error",
                    "message": "Failed to initialize Sentinel API"
                }

        # Validate bbox
        if not all(k in bbox for k in ['xmin', 'ymin', 'xmax', 'ymax']):
            raise ValueError("Invalid bbox: must contain xmin, ymin, xmax, ymax")
        
        if bbox['xmin'] >= bbox['xmax'] or bbox['ymin'] >= bbox['ymax']:
            raise ValueError("Invalid bbox: min coordinates must be less than max coordinates")
        
        # Validate dates
        if end_date < start_date:
            raise ValueError("Invalid date range: end_date must be after start_date")

        if bands is None:
            bands = ["B04", "B08"]

        # Validate bands
        valid_bands = ["B01", "B02", "B03", "B04", "B05", "B06", "B07", "B08", "B8A", "B09", "B11", "B12"]
        invalid_bands = [band for band in bands if band not in valid_bands]
        if invalid_bands:
            return {
                "status": "error",
                "message": f"Invalid bands specified: {', '.join(invalid_bands)}. Valid bands are: {', '.join(valid_bands)}"
            }

        try:
            # Convert bbox to WKT format for searching
            bbox_coords = [bbox["xmin"], bbox["ymin"], bbox["xmax"], bbox["ymax"]]
            bbox_geom = box(bbox_coords[0], bbox_coords[1], bbox_coords[2], bbox_coords[3])
            bbox_wkt = bbox_geom.wkt

            # Search for scenes
            search = self.client.search(
                collections=["sentinel-2-l2a"],
                intersects=bbox_wkt,
                datetime=[start_date.isoformat(), end_date.isoformat()],
                query={"eo:cloud_cover": {"lt": cloud_cover}}
            )
            items = list(search.get_items())

            if not items:
                return {
                    "status": "error",
                    "message": "No suitable imagery found"
                }

            # Get the first item (scene)
            item = items[0]
            scene_id = item.id
            cloud_cover = item.properties.get("eo:cloud_cover", 0)

            # Download each requested band
            downloaded_bands = []
            for band in bands:
                if band not in item.assets:
                    return {
                        "status": "error",
                        "message": f"Band {band} not available in scene {scene_id}"
                    }

                try:
                    url = item.assets[band].href
                    logging.info(f"Downloading band {band} from {url}")
                    success = await self.fetch_windowed_band(url, bbox, band)
                    if not success:
                        return {
                            "status": "error",
                            "message": f"Failed to download band {band}"
                        }
                    downloaded_bands.append(band)
                except Exception as e:
                    return {
                        "status": "error",
                        "message": f"Failed to download band {band}: {str(e)}"
                    }

            return {
                "status": "success",
                "scene_id": scene_id,
                "cloud_cover": cloud_cover,
                "bands": downloaded_bands,
                "metadata": {
                    "acquisition_date": item.properties.get("datetime"),
                    "platform": item.properties.get("platform"),
                    "processing_level": item.properties.get("processing:level"),
                    "bbox": item.bbox
                }
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Error during data acquisition: {str(e)}"
            }