"""
Planetary Computer data source for satellite imagery.
"""

import os
from typing import Dict, List, Optional, Tuple, Union, Any
from datetime import datetime
import planetary_computer as pc
import pystac_client
import rasterio
import numpy as np
from shapely.geometry import box, Polygon, mapping
import xarray as xr
from rasterio.warp import transform_bounds
import logging
from pathlib import Path
from pystac.item import Item
from .base import DataSource

class PlanetaryCompute(DataSource):
    """Interface for accessing data from Microsoft Planetary Computer."""
    
    def __init__(self, token: Optional[str] = None, cache_dir: Optional[str] = None):
        """
        Initialize Planetary Computer client.
        
        Args:
            token: Planetary Computer API token
            cache_dir: Optional directory for caching data
        """
        super().__init__(cache_dir)
        self.token = token or os.getenv("PLANETARY_COMPUTER_API_KEY")
        if self.token:
            pc.settings.set_subscription_key(self.token)
        
        self.logger = logging.getLogger(__name__)
        self.catalog = pystac_client.Client.open(
            "https://planetarycomputer.microsoft.com/api/stac/v1",
            modifier=pc.sign_inplace
        )
    
    def validate_bbox(self, bbox: List[float]) -> bool:
        """
        Validate bounding box format.
        
        Args:
            bbox: List of coordinates [west, south, east, north]
            
        Returns:
            bool: True if valid, raises ValueError if invalid
        """
        if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
            raise ValueError("bbox must be a list/tuple of 4 coordinates")
        
        west, south, east, north = bbox
        if not all(isinstance(x, (int, float)) for x in [west, south, east, north]):
            raise ValueError("bbox coordinates must be numbers")
            
        if not (-180 <= west <= 180 and -180 <= east <= 180):
            raise ValueError("longitude must be between -180 and 180")
            
        if not (-90 <= south <= 90 and -90 <= north <= 90):
            raise ValueError("latitude must be between -90 and 90")
            
        return True
    
    async def search(self,
                    bbox: List[float],
                    start_date: str,
                    end_date: str,
                    collection: str = "sentinel-2-l2a",
                    cloud_cover: float = 20.0,
                    limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for satellite imagery.
        
        Args:
            bbox: Bounding box coordinates [west, south, east, north]
            start_date: Start date in ISO format
            end_date: End date in ISO format
            collection: Collection ID (e.g., "sentinel-2-l2a")
            cloud_cover: Maximum cloud cover percentage
            limit: Maximum number of results
            
        Returns:
            List of STAC items
        """
        self.validate_bbox(bbox)
        
        search = self.catalog.search(
            collections=[collection],
            bbox=bbox,
            datetime=f"{start_date}/{end_date}",
            query={"eo:cloud_cover": {"lt": cloud_cover}},
            limit=limit
        )
        
        items = list(search.get_items())
        self.logger.info(f"Found {len(items)} items matching criteria")
        return items
    
    async def download(self,
                      item: Dict[str, Any],
                      output_dir: Path,
                      bands: List[str] = ["B02", "B03", "B04"]) -> Path:
        """
        Download and process satellite imagery.
        
        Args:
            item: STAC item
            output_dir: Directory to save output
            bands: List of band names to download
            
        Returns:
            Path to downloaded file
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create output filename
        item_id = item.get('id', 'unnamed')
        output_path = output_dir / f"{item_id}.tif"
        
        # Check cache
        cache_path = self.get_cache_path(f"{item_id}.tif")
        if cache_path and cache_path.exists():
            self.logger.info(f"Using cached file: {cache_path}")
            return cache_path
        
        # Download and merge bands
        band_arrays = []
        for band in bands:
            if band not in item['assets']:
                raise ValueError(f"Band {band} not found in item assets")
                
            href = item['assets'][band].href
            signed_href = pc.sign(href)
            
            with rasterio.open(signed_href) as src:
                band_arrays.append(src.read(1))
                profile = src.profile
        
        # Create multi-band image
        profile.update(count=len(bands))
        with rasterio.open(output_path, 'w', **profile) as dst:
            for i, array in enumerate(band_arrays, 1):
                dst.write(array, i)
        
        # Cache the result if caching is enabled
        if cache_path:
            output_path.rename(cache_path)
            output_path = cache_path
        
        self.logger.info(f"Saved image to {output_path}")
        return output_path
    
    async def search_and_download(
        self,
        bbox: Union[Tuple[float, float, float, float], Polygon],
        start_date: str,
        end_date: str,
        collections: List[str] = ["sentinel-2-l2a"],
        cloud_cover: float = 20.0
    ) -> Dict:
        """Search and download data from Planetary Computer.
        
        Args:
            bbox: Bounding box coordinates [west, south, east, north] or Polygon
            start_date: Start date in ISO format
            end_date: End date in ISO format
            collections: List of collections to search
            cloud_cover: Maximum cloud cover percentage
            
        Returns:
            Dictionary of downloaded data by collection
        """
        # Convert bbox to shapely box if it's a list/tuple
        if isinstance(bbox, (list, tuple)):
            bbox = box(*bbox)
        
        results = {}
        for collection in collections:
            search = self.catalog.search(
                collections=[collection],
                intersects=mapping(bbox),
                datetime=f"{start_date}/{end_date}",
                query={"eo:cloud_cover": {"lt": cloud_cover}}
            )
            items = list(search.get_items())
            
            if not items:
                continue
            
            results[collection] = await self._process_collection(
                items,
                bbox,
                collection
            )
        
        return results
    
    async def _process_collection(
        self,
        items: List[Item],
        bbox: Union[Polygon, box],
        collection: str
    ) -> Dict:
        """Process items from a specific collection."""
        
        if collection == "sentinel-2-l2a":
            return await self._process_sentinel2(items, bbox)
        elif collection == "landsat-8-c2-l2":
            return await self._process_landsat8(items, bbox)
        else:
            return {}
    
    async def _process_sentinel2(self, items: List[Item], bbox: Union[Polygon, box]) -> Dict:
        """Process Sentinel-2 data."""
        # Sort by cloud cover and get best scene
        items.sort(key=lambda x: float(x.properties["eo:cloud_cover"]))
        best_item = items[0]
        
        # Get required bands
        bands = ["B02", "B03", "B04", "B08"]  # Blue, Green, Red, NIR
        hrefs = [
            best_item.assets[band].href
            for band in bands
        ]
        
        # Open and read data
        data_arrays = []
        for href in hrefs:
            signed_href = pc.sign(href)
            with rasterio.open(signed_href) as src:
                # Reproject bbox if needed
                bounds = transform_bounds(
                    "EPSG:4326",
                    src.crs,
                    *bbox.bounds
                )
                
                # Read data
                window = src.window(*bounds)
                data = src.read(1, window=window)
                data_arrays.append(data)
        
        # Stack bands
        stacked_data = np.stack(data_arrays)
        
        return {
            "data": stacked_data,
            "metadata": {
                "datetime": best_item.datetime.strftime("%Y-%m-%d"),
                "cloud_cover": float(best_item.properties["eo:cloud_cover"]),
                "bands": bands,
                "resolution": 10.0,
                "crs": "EPSG:32632",  # UTM zone for the data
                "bounds": bbox.bounds
            }
        }
    
    async def _process_landsat8(self, items: List[Item], bbox: Union[Polygon, box]) -> Dict:
        """Process Landsat-8 data."""
        # Sort by cloud cover and get best scene
        items.sort(key=lambda x: float(x.properties["eo:cloud_cover"]))
        best_item = items[0]
        
        # Get required bands
        bands = ["B2", "B3", "B4", "B5"]  # Blue, Green, Red, NIR
        hrefs = [
            best_item.assets[band].href
            for band in bands
        ]
        
        # Open and read data
        data_arrays = []
        for href in hrefs:
            signed_href = pc.sign(href)
            with rasterio.open(signed_href) as src:
                # Reproject bbox if needed
                bounds = transform_bounds(
                    "EPSG:4326",
                    src.crs,
                    *bbox.bounds
                )
                
                # Read data
                window = src.window(*bounds)
                data = src.read(1, window=window)
                data_arrays.append(data)
        
        # Stack bands
        stacked_data = np.stack(data_arrays)
        
        return {
            "data": stacked_data,
            "metadata": {
                "datetime": best_item.datetime.strftime("%Y-%m-%d"),
                "cloud_cover": float(best_item.properties["eo:cloud_cover"]),
                "bands": bands,
                "resolution": 30.0,
                "crs": "EPSG:32632",  # UTM zone for the data
                "bounds": bbox.bounds
            }
        }
    
    def get_metadata(self, collection_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a collection.
        
        Args:
            collection_id: Collection identifier
            
        Returns:
            Dictionary containing collection metadata
        """
        collection = self.catalog.get_collection(collection_id)
        return {
            "id": collection.id,
            "title": collection.title,
            "description": collection.description,
            "license": collection.license,
            "providers": [p.name for p in collection.providers],
            "spatial_extent": collection.extent.spatial.bboxes,
            "temporal_extent": collection.extent.temporal.intervals
        }
    
    def get_available_collections(self) -> List[str]:
        """Get list of available collections."""
        collections = self.catalog.get_collections()
        return [c.id for c in collections] 