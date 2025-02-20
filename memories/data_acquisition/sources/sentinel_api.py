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
    
    def __init__(self, data_dir: str = None, max_concurrent_downloads: int = 4):
        """Initialize the Sentinel-2 interface.
        
        Args:
            data_dir: Optional directory for storing downloaded data
            max_concurrent_downloads: Maximum number of concurrent downloads
        """
        self.data_dir = Path(data_dir) if data_dir else Path("examples/data/satellite")
        self.max_concurrent_downloads = max_concurrent_downloads
        self.semaphore = asyncio.Semaphore(max_concurrent_downloads)
        
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
        bands: Optional[Dict[str, str]] = None,
        chunk_size: int = 8192,
        max_concurrent_downloads: int = 4
    ) -> Dict[str, Any]:
        """Download satellite imagery for a given bounding box.
        
        Args:
            bbox: Bounding box dictionary with xmin, ymin, xmax, ymax
            start_date: Optional start date (defaults to 30 days ago)
            end_date: Optional end date (defaults to now)
            cloud_cover: Maximum cloud cover percentage
            bands: Optional dictionary of band IDs to names
            chunk_size: Size of chunks for streaming downloads
            max_concurrent_downloads: Maximum number of concurrent downloads
            
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
            
            # Get items
            items = list(search.get_items())
            if not items:
                logger.warning("No scenes found matching criteria")
                return {
                    "success": False,
                    "error": "No scenes found",
                    "status": "no_data"
                }
                
            item = items[0]
            logger.info(f"\nFound scene from {item.properties['datetime']}")
            logger.info(f"Cloud cover: {item.properties['eo:cloud_cover']}%")
            logger.info(f"Scene ID: {item.id}")
            
            # Default bands if not specified
            if not bands:
                bands = {
                    "B02": "blue",
                    "B03": "green",
                    "B04": "red",
                    "B08": "nir"
                }
            
            # Track recovered files
            recovered_files = []
            failed_bands = []
            successful_bands = []
            
            # Download each band
            download_tasks = []
            for band_id, band_name in bands.items():
                if band_id in item.assets:
                    url = item.assets[band_id].href
                    output_file = self.data_dir / f"{band_name}.tif"
                    
                    # Check for partial downloads
                    if output_file.exists() and output_file.stat().st_size > 0:
                        recovered_files.append(output_file.name)
                        successful_bands.append(band_id)
                        continue
                        
                    task = self.fetch_windowed_band(url, bbox, band_name)
                    download_tasks.append((band_id, task))
                else:
                    logger.warning(f"Band {band_id} not found in assets")
                    failed_bands.append(band_id)
            
            # Wait for all downloads to complete
            for band_id, task in download_tasks:
                try:
                    result = await task
                    if result:
                        successful_bands.append(band_id)
                    else:
                        failed_bands.append(band_id)
                except Exception as e:
                    logger.error(f"Error downloading {band_id}: {str(e)}")
                    failed_bands.append(band_id)
            
            # Check results
            success = len(successful_bands) > 0
            
            if success:
                # Load and merge bands
                band_data = {}
                for band_name in bands.values():
                    band_file = self.data_dir / f"{band_name}.tif"
                    if band_file.exists():
                        with rasterio.open(band_file) as src:
                            band_data[band_name] = src.read(1)
                            
                # Stack bands into a single array
                if band_data:
                    data = np.stack(list(band_data.values()))
                    
                    # Normalize to 0-1 range
                    data = (data - data.min()) / (data.max() - data.min())
                    
                    return {
                        "success": True,
                        "data": data,
                        "metadata": {
                            "scene_id": item.id,
                            "cloud_cover": item.properties.get("eo:cloud_cover"),
                            "datetime": item.properties.get("datetime"),
                            "bands_downloaded": successful_bands,
                            "failed_bands": failed_bands,
                            "recovered_files": recovered_files,
                            "chunk_size": chunk_size
                        }
                    }
            
            return {
                "success": False,
                "error": "Failed to download or process bands",
                "failed_bands": failed_bands,
                "recovered_files": recovered_files
            }
                
        except Exception as e:
            logger.error(f"Error during satellite data download: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "status": "error"
            }

    def validate_collection(self, collection: str) -> bool:
        """Validate if a collection is supported.
        
        Args:
            collection: Collection name to validate
            
        Returns:
            bool: True if collection is supported
        """
        return collection in ["sentinel-2-l2a"]
        
    def get_signed_url(self, url: str) -> str:
        """Get signed URL for Planetary Computer asset.
        
        Args:
            url: Asset URL to sign
            
        Returns:
            str: Signed URL
        """
        signed = pc.sign(url)
        if isinstance(signed, dict) and 'href' in signed:
            return signed['href']
        return signed
        
    async def search_planetary_compute(
        self,
        bbox: Dict[str, float],
        start_date: datetime,
        end_date: datetime,
        cloud_cover: float = 10.0
    ) -> Dict[str, Any]:
        """Search Planetary Computer for scenes.
        
        Args:
            bbox: Bounding box dictionary with xmin, ymin, xmax, ymax
            start_date: Start date
            end_date: End date
            cloud_cover: Maximum cloud cover percentage
            
        Returns:
            Dict containing search results
        """
        # Convert bbox to geometry
        bbox_list = [bbox['xmin'], bbox['ymin'], bbox['xmax'], bbox['ymax']]
        aoi = box(*bbox_list)
        
        # Set up date range
        time_range = f"{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
        
        try:
            # Initialize Planetary Computer client
            catalog = pystac_client.Client.open(
                "https://planetarycomputer.microsoft.com/api/stac/v1",
                modifier=pc.sign_inplace
            )
            
            # Search for scenes
            search = catalog.search(
                collections=["sentinel-2-l2a"],
                intersects=aoi,
                datetime=time_range,
                query={"eo:cloud_cover": {"lt": cloud_cover}},
                sortby=["-datetime"],
                max_items=1
            )
            
            items = list(search.get_items())
            return {
                "success": True,
                "items": items,
                "metadata": {
                    "total_items": len(items),
                    "cloud_cover_threshold": cloud_cover,
                    "time_range": time_range
                }
            }
            
        except Exception as e:
            logger.error(f"Error searching Planetary Computer: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
            
    async def download_from_planetary_compute(
        self,
        item: Dict[str, Any],
        bands: List[str],
        output_dir: Path
    ) -> Dict[str, Any]:
        """Download data from Planetary Computer.
        
        Args:
            item: STAC item to download
            bands: List of bands to download
            output_dir: Output directory
            
        Returns:
            Dict containing download results
        """
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            downloaded_bands = []
            failed_bands = []
            
            for band in bands:
                if band in item['assets']:
                    url = item['assets'][band]['href']
                    output_file = output_dir / f"{band}.tif"
                    
                    try:
                        signed_url = self.get_signed_url(url)
                        async with self.semaphore:
                            success = await self.fetch_windowed_band(
                                signed_url,
                                {'xmin': -180, 'ymin': -90, 'xmax': 180, 'ymax': 90},  # Full extent
                                band,
                                output_dir
                            )
                            
                        if success:
                            downloaded_bands.append(band)
                        else:
                            failed_bands.append(band)
                            
                    except Exception as e:
                        logger.error(f"Error downloading band {band}: {str(e)}")
                        failed_bands.append(band)
                        
            return {
                "success": len(downloaded_bands) > 0,
                "downloaded_bands": downloaded_bands,
                "failed_bands": failed_bands
            }
            
        except Exception as e:
            logger.error(f"Error downloading from Planetary Computer: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
