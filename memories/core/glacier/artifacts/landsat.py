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
        if data_dir is None and self.cold_memory:
            raw_data_path = self.cold_memory.config['storage'].get('raw_data_path')
            if raw_data_path:
                data_dir = Path(raw_data_path) / "landsat"
            else:
                data_dir = Path("data/landsat")
            logger.info(f"Using cold storage path for data: {data_dir}")
        else:
            data_dir = Path(data_dir) if data_dir else Path("data/landsat")
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

    async def fetch_windowed_band(self, url: str, bbox: Dict[str, float], band_name: str, metadata: Dict[str, Any] = None) -> bool:
        """Download a specific band from a Landsat scene for a given bounding box.
        
        Args:
            url: URL of the band image
            bbox: Dictionary containing xmin, ymin, xmax, ymax in WGS84 coordinates
            band_name: Name of the band to download
            metadata: Optional metadata about the scene
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create output directory structure
            band_dir = self.data_dir / band_name
            band_dir.mkdir(parents=True, exist_ok=True)
            output_file = band_dir / f"{band_name}.tif"
            
            logger.info(f"Downloading band {band_name} from {url}")
            
            with rasterio.open(url) as src:
                # Create a window for the bounding box
                bbox_polygon = box(bbox["xmin"], bbox["ymin"], bbox["xmax"], bbox["ymax"])
                
                try:
                    # Try to use windowed reading if the bounding box is within the image
                    window = from_bounds(
                        bbox["xmin"],
                        bbox["ymin"],
                        bbox["xmax"],
                        bbox["ymax"],
                        src.transform
                    )
                    
                    logger.info(f"Calculated window pixels: rows={window.height}, cols={window.width}")
                    
                    # Ensure window has valid dimensions
                    if window.height < 1 or window.width < 1:
                        raise ValueError(f"Invalid window dimensions: height={window.height}, width={window.width}")
                    
                    # Get the transform for the window
                    window_transform = src.window_transform(window)
                    
                    # Read the data for the window
                    data = src.read(1, window=window)
                    
                    # Get the mask (nodata values)
                    mask = src.read_masks(1, window=window)
                    
                    # Create output profile
                    profile = src.profile.copy()
                    profile.update({
                        'driver': 'GTiff',
                        'height': int(window.height),
                        'width': int(window.width),
                        'transform': window_transform,
                        'compress': 'LZW',
                        'tiled': True,
                        'blockxsize': 256,
                        'blockysize': 256
                    })
                
                except Exception as window_error:
                    # If windowed reading fails, fall back to reading the entire image
                    logger.warning(f"Windowed reading failed: {str(window_error)}. Falling back to reading entire image.")
                    data = src.read()
                    profile = src.profile.copy()
                
                logger.info(f"Saving band {band_name} to {output_file}")
                if 'height' in profile and 'width' in profile:
                    logger.info(f"Output dimensions: {profile['height']}x{profile['width']}")
                
                # Write the output file
                with rasterio.open(output_file, 'w', **profile) as dst:
                    if len(data.shape) == 3:
                        # Multi-band data
                        dst.write(data)
                    else:
                        # Single band data
                        dst.write(data, 1)
                        if 'mask' in locals():
                            dst.write_mask(mask)
                
                # Verify the output file
                if output_file.exists() and output_file.stat().st_size > 0:
                    logger.info(f"Successfully saved band {band_name}")
                    
                    # Store in cold memory if enabled
                    if self.store_in_cold and metadata and hasattr(self, 'store_in_cold_memory'):
                        await self.store_in_cold_memory(band_name, output_file, metadata)
                    
                    return True
                else:
                    logger.error(f"Failed to save band {band_name}")
                    return False
        
        except Exception as e:
            logger.error(f"Error downloading band {band_name}: {str(e)}")
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
        """Download Landsat data for a given bounding box and time range.

        Args:
            bbox: Bounding box as a dictionary with xmin, ymin, xmax, ymax
            start_date: Start date for the search
            end_date: End date for the search
            collection: Collection ID (e.g., "landsat-c2-l2", "landsat-9-c2-l2")
            bands: List of bands to download (default: ["red", "nir08"])
            cloud_cover: Maximum cloud cover percentage (default: 30.0)

        Returns:
            Dict containing status, message (if error), and data (if success)
        """
        if self.client is None:
            if not await self.initialize():
                return {
                    "status": "error",
                    "message": "Failed to initialize Landsat API"
                }

        # Validate bbox
        if not all(k in bbox for k in ['xmin', 'ymin', 'xmax', 'ymax']):
            return {
                "status": "error",
                "message": "Invalid bbox: must contain xmin, ymin, xmax, ymax"
            }
        
        if bbox['xmin'] >= bbox['xmax'] or bbox['ymin'] >= bbox['ymax']:
            return {
                "status": "error",
                "message": "Invalid bbox: min coordinates must be less than max coordinates"
            }

        # Set default bands if none provided
        if bands is None:
            bands = ["red", "nir08"]  # Default to Red and NIR bands

        try:
            # Create a polygon from the bounding box coordinates
            bbox_polygon = box(bbox["xmin"], bbox["ymin"], bbox["xmax"], bbox["ymax"])
            bbox_wkt = bbox_polygon.wkt

            # Print search parameters
            logger.info("Search Parameters:")
            logger.info(f"- Collection: {collection}")
            logger.info(f"- Bounding Box (WKT): {bbox_wkt}")
            logger.info(f"- Time Range: {start_date.isoformat()} to {end_date.isoformat()}")
            logger.info(f"- Cloud Cover Threshold: {cloud_cover}%")
            logger.info(f"- Requested Bands: {bands}")

            # Search for scenes
            search = self.client.search(
                collections=[collection],
                intersects=bbox_polygon,
                datetime=[start_date.isoformat(), end_date.isoformat()],
                query={"eo:cloud_cover": {"lt": cloud_cover}}
            )

            # Get items and print count
            items = list(search.get_items())
            logger.info(f"Found {len(items)} scenes matching criteria")

            if not items:
                return {
                    "status": "error",
                    "message": "No scenes found matching criteria"
                }

            # Get the first item
            item = items[0]
            logger.info(f"Processing scene: {item.id}")

            # List available assets in the item for debugging
            logger.info("Available assets in scene:")
            for asset_key in item.assets.keys():
                logger.info(f"- {asset_key}")

            # Download each band
            downloaded_bands = []
            for band in bands:
                if band not in item.assets:
                    return {
                        "status": "error",
                        "message": f"Band {band} not available in scene {item.id}"
                    }

                # Get the signed URL for the band
                href = item.assets[band].href
                signed_href = planetary_computer.sign(href)

                # Download the band
                success = await self.fetch_windowed_band(
                    signed_href,
                    bbox,
                    band,
                    item.properties
                )

                if success:
                    downloaded_bands.append(band)
                else:
                    return {
                        "status": "error",
                        "message": f"Failed to download band {band}"
                    }

            # Return success response
            return {
                "status": "success",
                "scene_id": item.id,
                "cloud_cover": item.properties.get("eo:cloud_cover", 0),
                "bands": downloaded_bands,
                "metadata": {
                    "datetime": item.datetime.isoformat(),
                    "platform": item.properties.get("platform"),
                    "instrument": item.properties.get("instruments", []),
                    "processing:level": item.properties.get("processing:level"),
                    "collection": item.collection_id
                }
            }

        except Exception as e:
            logger.error(f"Error downloading Landsat data: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }

    async def store_in_cold_memory(self, band_name: str, file_path: Path, metadata: Dict[str, Any]) -> bool:
        """Store downloaded file in cold memory."""
        if not self.cold_memory:
            return False
        
        try:
            # Prepare metadata
            meta = {
                "band": band_name,
                "timestamp": datetime.now().isoformat(),
                "source": "landsat",
                **metadata
            }
            
            # Store in cold memory
            await self.cold_memory.store_file(
                file_path=file_path,
                metadata=meta,
                content_type="image/tiff"
            )
            
            logger.info(f"Stored {band_name} in cold memory")
            return True
        
        except Exception as e:
            logger.error(f"Error storing {band_name} in cold memory: {str(e)}")
            return False

    def cleanup(self):
        """Clean up downloaded files if keep_files is False."""
        if not self.keep_files and not self.store_in_cold:
            try:
                if self.data_dir.exists():
                    logger.info(f"Cleaning up directory: {self.data_dir}")
                    shutil.rmtree(self.data_dir)
                    logger.info("Cleanup completed")
            except Exception as e:
                logger.error(f"Error during cleanup: {str(e)}")

    def __del__(self):
        """Cleanup on object destruction."""
        self.cleanup() 