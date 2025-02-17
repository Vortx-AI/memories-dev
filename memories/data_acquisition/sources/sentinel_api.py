"""
Sentinel API data source for satellite imagery using Planetary Computer.
"""

import os
from typing import Dict, List, Optional, Tuple, Union, Any
from datetime import datetime
import planetary_computer as pc
import pystac_client
import rasterio
import numpy as np
from shapely.geometry import box, Polygon, mapping
from rasterio.warp import transform_bounds
import logging
from pathlib import Path
from .base import DataSource

class SentinelAPI(DataSource):
    """Interface for Sentinel data access through Planetary Computer."""
    
    def __init__(self, token: Optional[str] = None, cache_dir: Optional[str] = None):
        """
        Initialize Sentinel interface.
        
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
    
    async def search(self,
                    bbox: List[float],
                    start_date: str,
                    end_date: str,
                    collection: str = "sentinel-2-l2a",
                    cloud_cover: float = 20.0,
                    limit: int = 10) -> Dict[str, Any]:
        """
        Search for Sentinel imagery.
        
        Args:
            bbox: Bounding box coordinates [west, south, east, north]
            start_date: Start date in ISO format
            end_date: End date in ISO format
            collection: Collection ID (e.g., "sentinel-2-l2a")
            cloud_cover: Maximum cloud cover percentage
            limit: Maximum number of results
            
        Returns:
            Dictionary of products
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
        return {"items": items}
    
    async def download(self,
                      item_id: str,
                      output_dir: Path,
                      bands: List[str] = ["B02", "B03", "B04", "B08"]) -> Path:
        """
        Download Sentinel product.
        
        Args:
            item_id: Item identifier or STAC item
            output_dir: Directory to save output
            bands: List of bands to download
            
        Returns:
            Path to downloaded file
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Check cache
        cache_path = self.get_cache_path(f"{item_id}.tif")
        if cache_path and cache_path.exists():
            self.logger.info(f"Using cached file: {cache_path}")
            return cache_path
        
        # Get item if ID was provided
        if isinstance(item_id, str):
            search = self.catalog.search(
                collections=["sentinel-2-l2a"],
                ids=[item_id]
            )
            items = list(search.get_items())
            if not items:
                raise ValueError(f"Item {item_id} not found")
            item = items[0]
        else:
            item = item_id
        
        # Download and merge bands
        band_arrays = []
        for band in bands:
            if band not in item.assets:
                raise ValueError(f"Band {band} not found in item assets")
                
            href = item.assets[band].href
            signed_href = pc.sign(href)
            
            with rasterio.open(signed_href) as src:
                band_arrays.append(src.read(1))
                profile = src.profile
        
        # Create multi-band image
        output_path = output_dir / f"{item.id}.tif"
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
    
    def get_metadata(self, item_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a product.
        
        Args:
            item_id: Item identifier
            
        Returns:
            Dictionary containing product information
        """
        search = self.catalog.search(
            collections=["sentinel-2-l2a"],
            ids=[item_id]
        )
        items = list(search.get_items())
        if not items:
            raise ValueError(f"Item {item_id} not found")
        
        item = items[0]
        return {
            "id": item.id,
            "datetime": item.datetime.strftime("%Y-%m-%d"),
            "cloud_cover": float(item.properties.get("eo:cloud_cover", 0)),
            "platform": item.properties.get("platform", ""),
            "instrument": item.properties.get("instruments", []),
            "bands": list(item.assets.keys()),
            "bbox": item.bbox,
            "collection": item.collection_id
        }
    
    def get_available_collections(self) -> List[str]:
        """Get list of available Sentinel collections."""
        collections = self.catalog.get_collections()
        return [c.id for c in collections if c.id.startswith("sentinel-")]
