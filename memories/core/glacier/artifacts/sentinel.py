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
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from shapely.geometry import box
from rasterio.windows import Window
from typing import Dict, Any, Optional, List, Union
import json
from memories.core.cold import ColdMemory

class SentinelConnector:
    """Interface for accessing Sentinel-2 data using Planetary Computer."""

    def __init__(self, data_dir: Union[str, Path] = None, keep_files: bool = False, store_in_cold: bool = True):
        """Initialize the Sentinel-2 interface.
        
        Args:
            data_dir (Union[str, Path], optional): Directory to store downloaded data. If None, uses cold storage
            keep_files (bool): Whether to keep downloaded files (default: False)
            store_in_cold (bool): Whether to store files in cold memory (default: True)
        """
        self.keep_files = keep_files
        self.store_in_cold = store_in_cold
        self.logger = logging.getLogger(__name__)
        self.client = None
        self._downloaded_files = []
        
        # Initialize cold memory first if enabled
        self.cold_memory = ColdMemory() if store_in_cold else None
        # Add cold attribute for backward compatibility
        self.cold = self.cold_memory
        
        if self.cold_memory:
            logging.info(f"Cold storage location: {self.cold_memory.raw_data_path}")
        
        # Use default cold storage path if no data_dir provided
        if data_dir is None and self.cold_memory:
            data_dir = self.cold_memory.raw_data_path / "sentinel"
            logging.info(f"Using cold storage path for data: {data_dir}")
        else:
            data_dir = Path(data_dir) if data_dir else Path("data/sentinel")
            logging.info(f"Using custom data directory: {data_dir}")
            
        self.data_dir = Path(data_dir)
        os.makedirs(self.data_dir, exist_ok=True)

    async def store_in_cold_memory(self, band_name: str, output_file: Path, metadata: Dict[str, Any]) -> bool:
        """Store downloaded band in cold memory.
        
        Args:
            band_name: Name of the band
            output_file: Path to the downloaded file
            metadata: Associated metadata
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.cold_memory:
            return False
            
        try:
            # Create storage path in cold memory
            cold_path = f"sentinel/bands/{band_name}/{output_file.name}"
            
            # Generate a unique ID for this band data
            data_id = f"sentinel_{band_name}_{metadata.get('datetime', 'unknown')}".replace(":", "_")
            
            # Prepare data dictionary
            data = {
                "file_path": str(output_file),
                "target_path": cold_path,
                "band": band_name
            }
            
            # Prepare metadata
            band_metadata = {
                "id": data_id,  # Add required id field
                "type": "sentinel_band",
                "band": band_name,
                "acquisition_date": metadata.get("datetime"),
                "platform": metadata.get("platform"),
                "processing_level": metadata.get("processing:level"),
                "bbox": metadata.get("bbox"),
                "cloud_cover": metadata.get("eo:cloud_cover")
            }
            
            # Store in cold memory - removed await since store() is not async
            success = self.cold_memory.store(data, band_metadata)
            
            if success:
                logging.info(f"Successfully stored {band_name} in cold memory at {cold_path}")
                return True
            else:
                logging.error(f"Failed to store {band_name} in cold memory")
                return False
                
        except Exception as e:
            logging.error(f"Error storing {band_name} in cold memory: {str(e)}")
            return False

    async def fetch_windowed_band(self, url: str, bbox: Dict[str, float], band_name: str, metadata: Dict[str, Any] = None) -> bool:
        """Download a specific band from a Sentinel scene for a given bounding box.
        
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
            
            logging.info(f"Downloading band {band_name} from {url}")
            
            with rasterio.Env():
                with rasterio.open(url) as src:
                    # Get bounds and CRS of the source image
                    src_bounds = src.bounds
                    src_crs = src.crs
                    logging.info(f"Source image CRS: {src_crs}")
                    logging.info(f"Source image bounds: {src_bounds}")
                    logging.info(f"Input WGS84 bbox: {bbox}")

                    # Create a polygon from the input bbox (in WGS84)
                    from shapely.geometry import box as shbox
                    from rasterio.warp import transform_bounds
                    
                    # Transform bbox from WGS84 to image CRS
                    transformed_bounds = transform_bounds(
                        'EPSG:4326',  # WGS84
                        src_crs,
                        bbox['xmin'], bbox['ymin'],
                        bbox['xmax'], bbox['ymax']
                    )
                    logging.info(f"Transformed bounds in image CRS: {transformed_bounds}")

                    # Check if transformed bbox intersects with source bounds
                    if not (src_bounds.left <= transformed_bounds[2] and
                           transformed_bounds[0] <= src_bounds.right and
                           src_bounds.bottom <= transformed_bounds[3] and
                           transformed_bounds[1] <= src_bounds.top):
                        logging.error(f"Transformed bbox does not intersect with source bounds")
                        return False

                    # Get the window in pixel coordinates
                    window = rasterio.windows.from_bounds(
                        *transformed_bounds,
                        transform=src.transform
                    )
                    
                    # Round window to integer pixels
                    window = window.round_lengths()
                    
                    logging.info(f"Calculated window pixels: rows={window.height}, cols={window.width}")
                    
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
                    
                    logging.info(f"Saving band {band_name} to {output_file}")
                    logging.info(f"Output dimensions: {profile['height']}x{profile['width']}")
                    
                    # Write the output file
                    with rasterio.open(output_file, 'w', **profile) as dst:
                        dst.write(data, 1)
                        dst.write_mask(mask)
                    
                    # Verify the output file
                    if output_file.exists() and output_file.stat().st_size > 0:
                        logging.info(f"Successfully saved band {band_name}")
                        
                        # Store in cold memory if enabled
                        if self.store_in_cold and metadata:
                            await self.store_in_cold_memory(band_name, output_file, metadata)
                        
                        return True
                    else:
                        logging.error(f"Failed to save band {band_name}")
                        return False
            
        except Exception as e:
            logging.error(f"Error downloading band {band_name}: {str(e)}")
            return False

    def cleanup(self):
        """Clean up downloaded files if keep_files is False."""
        if not self.keep_files and not self.store_in_cold:
            try:
                if self.data_dir.exists():
                    logging.info(f"Cleaning up directory: {self.data_dir}")
                    shutil.rmtree(self.data_dir)
                    logging.info("Cleanup completed")
            except Exception as e:
                logging.error(f"Error during cleanup: {str(e)}")

    def __del__(self):
        """Cleanup on object destruction."""
        self.cleanup()

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
        """
        if self.client is None:
            if not await self.initialize():
                return {
                    "status": "error",
                    "message": "Failed to initialize Sentinel API"
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
        
        # Validate coordinates are within valid ranges
        if not (-180 <= bbox['xmin'] <= 180 and -180 <= bbox['xmax'] <= 180):
            return {
                "status": "error",
                "message": "Invalid bbox: longitude values must be between -180 and 180"
            }
            
        if not (-90 <= bbox['ymin'] <= 90 and -90 <= bbox['ymax'] <= 90):
            return {
                "status": "error",
                "message": "Invalid bbox: latitude values must be between -90 and 90"
            }
        
        # Validate dates
        if end_date < start_date:
            return {
                "status": "error",
                "message": "Invalid date range: end_date must be after start_date"
            }

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
            # Create a polygon from the bounding box coordinates
            bbox_polygon = box(bbox["xmin"], bbox["ymin"], bbox["xmax"], bbox["ymax"])
            bbox_wkt = bbox_polygon.wkt

            # Print search parameters
            logging.info("Search Parameters:")
            logging.info(f"- Collection: sentinel-2-l2a")
            logging.info(f"- Bounding Box (WKT): {bbox_wkt}")
            logging.info(f"- Time Range: {start_date.isoformat()} to {end_date.isoformat()}")
            logging.info(f"- Cloud Cover Threshold: {cloud_cover}%")

            # Search for scenes
            search = self.client.search(
                collections=["sentinel-2-l2a"],
                intersects=bbox_polygon,
                datetime=[start_date.isoformat(), end_date.isoformat()],
                query={"eo:cloud_cover": {"lt": cloud_cover}}
            )

            # Print the actual search URL
            if hasattr(search, '_get_request_url'):
                search_url = search._get_request_url()
                logging.info(f"Search URL: {search_url}")

            # Get items and print count
            items = list(search.get_items())
            logging.info(f"Found {len(items)} scenes matching criteria")

            if not items:
                return {
                    "status": "error",
                    "message": "No suitable imagery found"
                }

            # Get the first item (scene)
            item = items[0]
            scene_id = item.id
            cloud_cover = item.properties.get("eo:cloud_cover", 0)

            # Print available assets/bands
            logging.info(f"Available bands in scene {scene_id}:")
            for asset_key, asset in item.assets.items():
                logging.info(f"- {asset_key}: {asset.href}")

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
                    logging.info(f"Downloading band {band} from URL: {url}")
                    success = await self.fetch_windowed_band(url, bbox, band, item.properties)
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
            logging.error(f"Error during data acquisition: {str(e)}")
            return {
                "status": "error",
                "message": f"Error during data acquisition: {str(e)}"
            }
