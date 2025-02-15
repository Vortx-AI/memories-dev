"""Data sources module for handling different satellite data providers"""

import logging
from typing import Dict, Any, List, Optional, Generator
from datetime import datetime, timedelta
from pathlib import Path
import json
import aiohttp
import asyncio
from pystac_client import Client
from pystac.item import Item
import planetary_computer
import rasterio
import xarray as xr

class DataSource:
    """Base class for satellite data sources"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
    
    async def search(self,
                    bbox: List[float],
                    start_date: datetime,
                    end_date: datetime,
                    **kwargs) -> List[Dict[str, Any]]:
        """Search for satellite data"""
        raise NotImplementedError
    
    async def download(self,
                      item: Dict[str, Any],
                      output_dir: Path,
                      **kwargs) -> Path:
        """Download satellite data"""
        raise NotImplementedError

class SentinelDataSource(DataSource):
    """Sentinel satellite data source"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.stac_endpoint = "https://earth-search.aws.element84.com/v0"
        self.collection = "sentinel-s2-l2a-cogs"
    
    async def search(self,
                    bbox: List[float],
                    start_date: datetime,
                    end_date: datetime,
                    max_cloud_cover: float = 20.0,
                    limit: int = 10) -> List[Dict[str, Any]]:
        """Search Sentinel data"""
        try:
            # Initialize STAC client
            client = Client.open(self.stac_endpoint)
            
            # Build search query
            search = client.search(
                collections=[self.collection],
                bbox=bbox,
                datetime=f"{start_date.isoformat()}/{end_date.isoformat()}",
                query={"eo:cloud_cover": {"lt": max_cloud_cover}},
                limit=limit
            )
            
            # Get items
            items = [item.to_dict() for item in search.get_items()]
            self.logger.info(f"Found {len(items)} Sentinel scenes")
            return items
            
        except Exception as e:
            self.logger.error(f"Error searching Sentinel data: {e}")
            raise

    async def download(self,
                      item: Dict[str, Any],
                      output_dir: Path,
                      bands: List[str] = ["B02", "B03", "B04", "B08"]) -> Path:
        """Download Sentinel data"""
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Get asset URLs for requested bands
            urls = {
                band: item["assets"][band]["href"]
                for band in bands
                if band in item["assets"]
            }
            
            # Download bands
            async with aiohttp.ClientSession() as session:
                tasks = []
                for band, url in urls.items():
                    output_path = output_dir / f"{item['id']}_{band}.tif"
                    task = asyncio.create_task(
                        self._download_band(session, url, output_path)
                    )
                    tasks.append(task)
                
                await asyncio.gather(*tasks)
            
            # Merge bands into single file
            output_path = output_dir / f"{item['id']}_merged.tif"
            self._merge_bands(
                [output_dir / f"{item['id']}_{band}.tif" for band in bands],
                output_path
            )
            
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error downloading Sentinel data: {e}")
            raise
    
    async def _download_band(self,
                           session: aiohttp.ClientSession,
                           url: str,
                           output_path: Path) -> None:
        """Download a single band"""
        async with session.get(url) as response:
            with open(output_path, "wb") as f:
                async for chunk in response.content.iter_chunked(8192):
                    f.write(chunk)
    
    def _merge_bands(self,
                    input_paths: List[Path],
                    output_path: Path) -> None:
        """Merge multiple bands into a single file"""
        # Read all bands
        arrays = []
        profile = None
        for path in input_paths:
            with rasterio.open(path) as src:
                arrays.append(src.read(1))
                if profile is None:
                    profile = src.profile
        
        # Update profile for multiple bands
        profile.update(count=len(arrays))
        
        # Write merged file
        with rasterio.open(output_path, "w", **profile) as dst:
            for i, array in enumerate(arrays, 1):
                dst.write(array, i)

class LandsatDataSource(DataSource):
    """Landsat satellite data source"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.stac_endpoint = "https://landsatlook.usgs.gov/stac-server"
        self.collection = "landsat-c2l2-sr"
    
    async def search(self,
                    bbox: List[float],
                    start_date: datetime,
                    end_date: datetime,
                    max_cloud_cover: float = 20.0,
                    limit: int = 10) -> List[Dict[str, Any]]:
        """Search Landsat data"""
        try:
            # Initialize STAC client
            client = Client.open(self.stac_endpoint)
            
            # Build search query
            search = client.search(
                collections=[self.collection],
                bbox=bbox,
                datetime=f"{start_date.isoformat()}/{end_date.isoformat()}",
                query={"eo:cloud_cover": {"lt": max_cloud_cover}},
                limit=limit
            )
            
            # Get items
            items = [item.to_dict() for item in search.get_items()]
            self.logger.info(f"Found {len(items)} Landsat scenes")
            return items
            
        except Exception as e:
            self.logger.error(f"Error searching Landsat data: {e}")
            raise

    async def download(self,
                      item: Dict[str, Any],
                      output_dir: Path,
                      bands: List[str] = ["SR_B2", "SR_B3", "SR_B4", "SR_B5"]) -> Path:
        """Download Landsat data"""
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Get asset URLs for requested bands
            urls = {
                band: item["assets"][band]["href"]
                for band in bands
                if band in item["assets"]
            }
            
            # Download bands
            async with aiohttp.ClientSession() as session:
                tasks = []
                for band, url in urls.items():
                    output_path = output_dir / f"{item['id']}_{band}.tif"
                    task = asyncio.create_task(
                        self._download_band(session, url, output_path)
                    )
                    tasks.append(task)
                
                await asyncio.gather(*tasks)
            
            # Merge bands into single file
            output_path = output_dir / f"{item['id']}_merged.tif"
            self._merge_bands(
                [output_dir / f"{item['id']}_{band}.tif" for band in bands],
                output_path
            )
            
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error downloading Landsat data: {e}")
            raise
    
    async def _download_band(self,
                           session: aiohttp.ClientSession,
                           url: str,
                           output_path: Path) -> None:
        """Download a single band"""
        async with session.get(url) as response:
            with open(output_path, "wb") as f:
                async for chunk in response.content.iter_chunked(8192):
                    f.write(chunk)
    
    def _merge_bands(self,
                    input_paths: List[Path],
                    output_path: Path) -> None:
        """Merge multiple bands into a single file"""
        # Read all bands
        arrays = []
        profile = None
        for path in input_paths:
            with rasterio.open(path) as src:
                arrays.append(src.read(1))
                if profile is None:
                    profile = src.profile
        
        # Update profile for multiple bands
        profile.update(count=len(arrays))
        
        # Write merged file
        with rasterio.open(output_path, "w", **profile) as dst:
            for i, array in enumerate(arrays, 1):
                dst.write(array, i) 