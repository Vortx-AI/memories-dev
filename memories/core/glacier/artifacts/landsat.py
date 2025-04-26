"""
Landsat data source using Planetary Computer.
"""

import os
import logging
import asyncio
import planetary_computer
import pystac_client
import rasterio
import numpy as np
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from shapely.geometry import box
from rasterio.windows import Window, from_bounds
from typing import Dict, Any, Optional, List, Union
import json
from memories.core.cold import ColdMemory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LandsatConnector:
    """Interface for accessing Landsat data using Planetary Computer."""
    
    def __init__(self, data_dir: Union[str, Path] = None, keep_files: bool = False, store_in_cold: bool = True):
        """Initialize the Landsat interface.
        
        Args:
            data_dir: Directory to store downloaded data. If None, uses cold storage
            keep_files: Whether to keep downloaded files (default: False)
            store_in_cold: Whether to store files in cold memory (default: True)
        """
        self.keep_files = keep_files
        self.store_in_cold = store_in_cold
        self.logger = logging.getLogger(__name__)
        self.client = None
        self._downloaded_files = []
        
        # Initialize cold memory if enabled
        self.cold_memory = ColdMemory() if store_in_cold else None
        self.cold = self.cold_memory  # For backward compatibility
        
        if self.cold_memory:
            logger.info(f"Cold storage location: {self.cold_memory.config['storage']['raw_data_path']}")
        
        # Set up data directory
        if data_dir is None:
            # Default path if no data_dir provided
            data_dir = os.path.join(os.getcwd(), "data", "landsat")
            logger.info(f"Using default data directory: {data_dir}")
        else:
            logger.info(f"Using custom data directory: {data_dir}")
            
        self.data_dir = Path(data_dir)
        os.makedirs(self.data_dir, exist_ok=True)

    async def initialize(self) -> bool:
        """Initialize the Landsat API.

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
            logger.error(f"Error initializing Landsat API: {str(e)}")
            return False

    async def fetch_windowed_band(
        self,
        url: str,
        bbox: Dict[str, float],
        band_name: str,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """Download a specific band from a Landsat scene for a given bounding box."""
        try:
            # Create output directory structure
            band_dir = self.data_dir / band_name
            band_dir.mkdir(parents=True, exist_ok=True)
            output_file = band_dir / f"{band_name}.tif"

            logger.info(f"Downloading band {band_name} from {url}")

            # Open source
            with rasterio.open(url) as src:
                # Try windowed read
                try:
                    window = from_bounds(
                        bbox["xmin"], bbox["ymin"],
                        bbox["xmax"], bbox["ymax"],
                        src.transform
                    )
                    logger.info(f"Calculated window pixels: rows={window.height}, cols={window.width}")
                    if window.height < 1 or window.width < 1:
                        raise ValueError(f"Invalid window dimensions: {window}")
                    data = src.read(1, window=window)
                    mask = src.read_masks(1, window=window)

                    profile = src.profile.copy()
                    profile.update({
                        "driver": "GTiff",
                        "height": int(window.height),
                        "width": int(window.width),
                        "transform": src.window_transform(window),
                        "compress": "LZW",
                        "tiled": True,
                        "blockxsize": 256,
                        "blockysize": 256,
                    })

                except Exception as window_error:
                    logger.warning(
                        f"Windowed reading failed ({window_error}); falling back to full read."
                    )
                    data = src.read(1)
                    mask = src.read_masks(1)
                    profile = src.profile.copy()

            # Write out
            logger.info(f"Saving band {band_name} to {output_file}")
            with rasterio.open(output_file, "w", **profile) as dst:
                dst.write(data, 1)
                dst.write_mask(mask)

            # Verify and (optionally) store in cold memory
            if output_file.exists() and output_file.stat().st_size > 0:
                logger.info(f"Successfully saved band {band_name} ({profile['height']}×{profile['width']})")
                if getattr(self, "store_in_cold", False) and metadata and hasattr(self, "store_in_cold_memory"):
                    await self.store_in_cold_memory(band_name, output_file, metadata)
                return True
            else:
                logger.error(f"Failed to save band file at {output_file}")
                return False

        except Exception as e:
            logger.error(f"Error in fetch_windowed_band for {band_name}: {e}")
            return False


    async def download_data(
        self,
        bbox: Dict[str, float],
        start_date: datetime,
        end_date: datetime,
        collection: str = "landsat-c2-l2",
        bands: Optional[List[str]] = None,
        cloud_cover: float = 30.0
    ) -> Dict[str, Any]:
        """Download Landsat data for a given bounding box and time range."""
        # Ensure client is initialized
        if self.client is None:
            if not await self.initialize():
                return {"status": "error", "message": "Failed to initialize Landsat API"}

        # Validate bbox
        if not all(k in bbox for k in ("xmin", "ymin", "xmax", "ymax")):
            return {"status": "error", "message": "Invalid bbox: must contain xmin, ymin, xmax, ymax"}
        if bbox["xmin"] >= bbox["xmax"] or bbox["ymin"] >= bbox["ymax"]:
            return {"status": "error", "message": "Invalid bbox: min coords must be less than max coords"}

        # Default bands
        if bands is None:
            bands = ["red", "nir08"]

        try:
            # Build search geometry
            bbox_polygon = box(bbox["xmin"], bbox["ymin"], bbox["xmax"], bbox["ymax"])
            logger.info(f"Searching {collection} between {start_date} and {end_date}, cloud<{cloud_cover}%")

            search = self.client.search(
                collections=[collection],
                intersects=bbox_polygon,
                datetime=[start_date.isoformat(), end_date.isoformat()],
                query={"eo:cloud_cover": {"lt": cloud_cover}}
            )
            items = list(search.get_items())
            logger.info(f"Found {len(items)} scenes")

            if not items:
                return {"status": "error", "message": "No scenes found matching criteria"}

            item = items[0]
            logger.info(f"Processing scene: {item.id}")

            # Download each requested band
            downloaded = []
            for band in bands:
                if band not in item.assets:
                    return {
                        "status": "error",
                        "message": f"Band '{band}' not available in scene {item.id}"
                    }

                href = item.assets[band].href
                signed_href = planetary_computer.sign(href)

                success = await self.fetch_windowed_band(signed_href, bbox, band, item.properties)
                if not success:
                    return {
                        "status": "error",
                        "message": f"Failed to download band '{band}'"
                    }
                downloaded.append(band)

            # If we get here, all bands succeeded
            return {
                "status": "success",
                "scene_id": item.id,
                "cloud_cover": item.properties.get("eo:cloud_cover", 0),
                "bands": downloaded,
                "metadata": {
                    "datetime": item.datetime.isoformat(),
                    "platform": item.properties.get("platform"),
                    "instrument": item.properties.get("instruments", []),
                    "processing:level": item.properties.get("processing:level"),
                    "collection": item.collection_id
                }
            }

        except Exception as e:
            logger.error(f"Error downloading Landsat data: {e}")
            return {"status": "error", "message": str(e)}


    async def store_in_cold_memory(
        self,
        band_name: str,
        file_path: Path,
        metadata: Dict[str, Any]
    ) -> bool:
        """Store downloaded file in cold memory."""
        if not getattr(self, "cold_memory", None):
            return False

        try:
            meta = {
                "band": band_name,
                "timestamp": datetime.now().isoformat(),
                "source": "landsat",
                **metadata
            }
            await self.cold_memory.store_file(
                file_path=file_path,
                metadata=meta,
                content_type="image/tiff"
            )
            logger.info(f"Stored '{band_name}' in cold memory")
            return True

        except Exception as e:
            logger.error(f"Error storing '{band_name}' in cold memory: {e}")
            return False
