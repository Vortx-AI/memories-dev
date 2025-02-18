"""
Sentinel-2 data source using Planetary Computer.
"""

import os
import logging
import asyncio
import planetary_computer as pc
import pystac_client
import rasterio
from rasterio.windows import from_bounds
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from shapely.geometry import box
import pyproj
from shapely.ops import transform
from typing import Dict, List, Any, Optional, Union

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Set to DEBUG level to see more information

class SentinelAPI:
    """Interface for accessing Sentinel-2 data using Planetary Computer."""
    
    def __init__(self, data_dir: str = None):
        """Initialize the Sentinel-2 interface.
        
        Args:
            data_dir: Optional directory for storing downloaded data
        """
        self.data_dir = Path(data_dir) if data_dir else Path("examples/data/satellite")
        
    async def fetch_windowed_band(
        self,
        url: str,
        bbox: Dict[str, float],
        band_name: str,
        data_dir: Optional[Path] = None
    ) -> bool:
        """Fetch only the required window of the image for the given band.
        
        Args:
            url: URL of the band asset
            bbox: Bounding box dictionary with xmin, ymin, xmax, ymax
            band_name: Name of the band
            data_dir: Optional directory for output (uses instance data_dir if None)
            
        Returns:
            bool: True if download successful
        """
        data_dir = data_dir or self.data_dir
        output_file = data_dir / f"{band_name}.tif"
        
        # Remove existing file if it exists
        if output_file.exists():
            logger.info(f"Removing existing file: {output_file}")
            output_file.unlink()
        
        logger.info(f"Downloading {band_name}...")
        
        try:
            # Sign URL properly
            signed_asset = pc.sign(url)
            if isinstance(signed_asset, dict) and 'href' in signed_asset:
                signed_url = signed_asset['href']
            else:
                signed_url = signed_asset
                
            if not isinstance(signed_url, str) or not signed_url.startswith('https://'):
                raise ValueError(f"Invalid signed URL for {band_name}")
                
            logger.info(f"Signed URL for {band_name}: {signed_url[:100]}...")
            vsicurl_path = f"/vsicurl/{signed_url}"
            
            # Set up GDAL environment with error handling
            gdal_config = {
                'GDAL_HTTP_MULTIPLEX': 'YES',
                'GDAL_HTTP_VERSION': '2',
                'GDAL_DISABLE_READDIR_ON_OPEN': 'EMPTY_DIR',
                'CPL_VSIL_CURL_ALLOWED_EXTENSIONS': 'tif,tiff',
                'GDAL_MAX_DATASET_POOL_SIZE': '256',
                'CPL_VSIL_CURL_USE_HEAD': 'NO',
                'GDAL_HTTP_RETRY_COUNT': '3',
                'GDAL_HTTP_TIMEOUT': '30',
                'VSI_CACHE': 'TRUE',
                'VSI_CACHE_SIZE': '50000000',
                'GDAL_DISABLE_READDIR_ON_OPEN': 'YES',
                'CPL_DEBUG': 'YES'
            }
            
            with rasterio.Env(**gdal_config):
                try:
                    logger.info(f"Opening raster for {band_name}...")
                    with rasterio.open(vsicurl_path) as src:
                        logger.info(f"Raster opened successfully for {band_name}")
                        logger.info(f"Raster bounds: {src.bounds}")
                        logger.info(f"Raster size: {src.width}x{src.height}")
                        logger.info(f"Raster CRS: {src.crs}")
                        
                        # Convert input bbox to the raster's CRS if needed
                        if src.crs.to_epsg() != 4326:  # If not WGS84
                            transformer = pyproj.Transformer.from_crs(
                                "epsg:4326",
                                src.crs,
                                always_xy=True
                            )
                            bbox_transformed = transform(
                                transformer.transform,
                                box(bbox['xmin'], bbox['ymin'], bbox['xmax'], bbox['ymax'])
                            )
                            window_bounds = bbox_transformed.bounds
                        else:
                            window_bounds = (
                                bbox['xmin'], bbox['ymin'],
                                bbox['xmax'], bbox['ymax']
                            )
                        
                        # Get the window for our bbox
                        window = from_bounds(*window_bounds, transform=src.transform)
                        
                        # Ensure window is within image bounds
                        window = window.crop(height=src.height, width=src.width)
                        logger.info(f"Window for {band_name}: {window}")
                        
                        if window.width <= 0 or window.height <= 0:
                            raise ValueError(f"Invalid window dimensions for {band_name}")
                        
                        # Calculate output dimensions to target ~5MB file size
                        target_pixels = int(5 * 1024 * 1024 / 2)  # Target 5MB at 2 bytes per pixel
                        current_pixels = window.width * window.height
                        scale_factor = min((target_pixels / current_pixels) ** 0.5, 1.0)
                        
                        out_shape = (
                            max(int(window.height * scale_factor), 100),
                            max(int(window.width * scale_factor), 100)
                        )
                        logger.info(f"Output shape for {band_name}: {out_shape}")
                        
                        # Read the windowed data
                        logger.info(f"Reading {band_name} data...")
                        data = src.read(
                            1,
                            window=window,
                            out_shape=out_shape,
                            resampling=rasterio.enums.Resampling.bilinear
                        )
                        
                        if data is None or data.size == 0:
                            raise ValueError(f"No data read for {band_name}")
                            
                        logger.info(f"Data shape for {band_name}: {data.shape}")
                        logger.info(f"Data statistics - min: {data.min()}, max: {data.max()}, mean: {data.mean()}")
                        
                        # Create output profile
                        profile = src.profile.copy()
                        profile.update({
                            'height': data.shape[0],
                            'width': data.shape[1],
                            'transform': rasterio.windows.transform(window, src.transform),
                            'compress': 'deflate',
                            'predictor': 2,
                            'zlevel': 9,
                            'tiled': True,
                            'blockxsize': 256,
                            'blockysize': 256,
                            'sparse_ok': True,
                            'interleave': 'band'
                        })
                        
                        # Save the windowed data
                        logger.info(f"Saving {band_name} data...")
                        with rasterio.open(output_file, 'w', **profile) as dst:
                            dst.write(data, 1)
                        
                        file_size_mb = os.path.getsize(output_file) / (1024 * 1024)
                        logger.info(f"Band {band_name} size: {file_size_mb:.1f} MB")
                        
                        return True
                        
                except rasterio.errors.RasterioIOError as e:
                    logger.error(f"IO Error reading {band_name}: {e}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error downloading {band_name}: {str(e)}")
            if os.path.exists(output_file):
                os.remove(output_file)
            return False
            
    async def download_data(
        self,
        bbox: Dict[str, float],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        cloud_cover: float = 10.0,
        bands: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Download satellite imagery for a given bounding box.
        
        Args:
            bbox: Bounding box dictionary with xmin, ymin, xmax, ymax
            start_date: Optional start date (defaults to 30 days ago)
            end_date: Optional end date (defaults to now)
            cloud_cover: Maximum cloud cover percentage
            bands: Optional dictionary of band IDs to names
            
        Returns:
            Dictionary with download results and metadata
        """
        # Create data directory
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Convert bbox to geometry
        bbox_list = [bbox['xmin'], bbox['ymin'], bbox['xmax'], bbox['ymax']]
        aoi = box(*bbox_list)
        
        # Convert to UTM
        utm_zone = int((bbox['xmin'] + 180) / 6) + 1
        epsg_code = f"epsg:326{utm_zone}"
        project = pyproj.Transformer.from_crs("epsg:4326", epsg_code, always_xy=True).transform
        utm_aoi = transform(project, aoi)
        
        logger.info(f"Area of Interest (UTM Zone {utm_zone}):")
        logger.info(f"Bounds: {utm_aoi.bounds}")
        
        # Set up date range
        end_date = end_date or datetime.now()
        start_date = start_date or (end_date - timedelta(days=30))
        time_range = f"{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
        
        try:
            # Initialize Planetary Computer client
            logger.info("Connecting to Planetary Computer...")
            catalog = pystac_client.Client.open(
                "https://planetarycomputer.microsoft.com/api/stac/v1",
                modifier=pc.sign_inplace
            )
            
            # Search for scenes
            logger.info("Searching for scenes...")
            search = catalog.search(
                collections=["sentinel-2-l2a"],
                intersects=aoi,
                datetime=time_range,
                query={"eo:cloud_cover": {"lt": cloud_cover}},
                sortby=["-datetime"],
                max_items=1
            )
            
            items = list(search.get_items())
            
            if not items:
                logger.warning("No suitable imagery found")
                return {
                    "status": "no_data",
                    "message": "No suitable imagery found for the given parameters",
                    "parameters": {
                        "bbox": bbox,
                        "time_range": time_range,
                        "cloud_cover": cloud_cover
                    }
                }
            
            item = items[0]
            logger.info(f"\nFound scene from {item.properties['datetime']}")
            logger.info(f"Cloud cover: {item.properties['eo:cloud_cover']}%")
            logger.info(f"Scene ID: {item.id}")
            
            # Download relevant bands
            bands = bands or {
                "B04": "Red",
                "B08": "NIR",
                "B11": "SWIR"
            }
            
            tasks = []
            for band_id, band_name in bands.items():
                if band_id not in item.assets:
                    logger.warning(f"Warning: Band {band_id} not found in scene")
                    continue
                    
                asset = item.assets[band_id]
                logger.info(f"\nProcessing {band_name} band ({band_id})...")
                logger.info(f"Asset href: {asset.href[:100]}...")
                
                task = self.fetch_windowed_band(asset.href, bbox, band_id, self.data_dir)
                tasks.append(task)
            
            if not tasks:
                logger.warning("No valid bands to download")
                return {"error": "No valid bands to download"}
            
            # Wait for all downloads to complete
            try:
                results = await asyncio.gather(*tasks)
                
                # Save metadata if all downloads succeeded
                if all(results):
                    metadata = {
                        "datetime": item.properties["datetime"],
                        "cloud_cover": item.properties["eo:cloud_cover"],
                        "satellite": item.properties["platform"],
                        "scene_id": item.id,
                        "bbox": bbox_list,
                        "utm_zone": utm_zone,
                        "bands_downloaded": list(bands.keys())
                    }
                    
                    metadata_file = self.data_dir / "metadata.txt"
                    with open(metadata_file, 'w') as f:
                        for key, value in metadata.items():
                            f.write(f"{key}: {value}\n")
                    
                    logger.info(f"\nSatellite data downloaded to: {self.data_dir}")
                    logger.info(f"Metadata saved to: {metadata_file}")
                    
                    return {
                        "success": True,
                        "metadata": metadata,
                        "data_dir": str(self.data_dir)
                    }
                else:
                    return {
                        "error": "Some band downloads failed",
                        "failed_bands": [
                            band_id for band_id, result in zip(bands.keys(), results)
                            if not result
                        ]
                    }
            except asyncio.CancelledError:
                logger.info("\nDownload cancelled by user. Cleaning up...")
                # Clean up any partially downloaded files
                for band_id in bands.keys():
                    file_path = self.data_dir / f"{band_id}.tif"
                    if file_path.exists():
                        try:
                            file_path.unlink()
                            logger.info(f"Removed partial download: {file_path}")
                        except:
                            pass
                raise
                
        except Exception as e:
            logger.error(f"Error during satellite data download: {str(e)}")
            return {"error": str(e)}
