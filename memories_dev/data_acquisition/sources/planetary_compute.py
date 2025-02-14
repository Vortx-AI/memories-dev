"""
Planetary Computer data source for satellite imagery.
"""

import os
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime
import planetary_computer as pc
import pystac_client
import rasterio
import numpy as np
from shapely.geometry import box, Polygon, mapping
import xarray as xr
from rasterio.warp import transform_bounds

class PlanetaryCompute:
    """Interface for accessing data from Microsoft Planetary Computer."""
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize Planetary Computer client.
        
        Args:
            token: Planetary Computer API token
        """
        self.token = token or os.getenv("PLANETARY_COMPUTER_API_KEY")
        if self.token:
            pc.settings.set_subscription_key(self.token)
        
        self.catalog = pystac_client.Client.open(
            "https://planetarycomputer.microsoft.com/api/stac/v1",
            modifier=pc.sign_inplace
        )
    
    def search_and_download(
        self,
        bbox: Union[Tuple[float, float, float, float], Polygon],
        start_date: str,
        end_date: str,
        collections: List[str] = ["sentinel-2-l2a"],
        cloud_cover: float = 20.0
    ) -> Dict:
        """
        Search and download satellite imagery.
        
        Args:
            bbox: Bounding box or Polygon
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            collections: List of collections to search
            cloud_cover: Maximum cloud cover percentage
            
        Returns:
            Dictionary containing downloaded data and metadata
        """
        # Convert bbox to polygon if needed
        if isinstance(bbox, tuple):
            bbox = box(*bbox)
        
        # Prepare search parameters
        search_params = {
            "collections": collections,
            "intersects": mapping(bbox),
            "datetime": f"{start_date}/{end_date}",
            "query": {
                "eo:cloud_cover": {"lt": cloud_cover}
            }
        }
        
        # Search for items
        search = self.catalog.search(**search_params)
        items = list(search.get_items())
        
        if not items:
            return {}
        
        results = {}
        for collection in collections:
            collection_items = [item for item in items if item.collection_id == collection]
            if collection_items:
                results[collection] = self._process_collection(
                    collection_items,
                    bbox,
                    collection
                )
        
        return results
    
    def _process_collection(
        self,
        items: List,
        bbox: Union[Polygon, box],
        collection: str
    ) -> Dict:
        """Process items from a specific collection."""
        
        if collection == "sentinel-2-l2a":
            return self._process_sentinel2(items, bbox)
        elif collection == "landsat-8-c2-l2":
            return self._process_landsat8(items, bbox)
        else:
            return {}
    
    def _process_sentinel2(self, items: List, bbox: Union[Polygon, box]) -> Dict:
        """Process Sentinel-2 data."""
        # Sort by cloud cover and get best scene
        items.sort(key=lambda x: float(x.properties["eo:cloud_cover"]))
        best_item = items[0]
        
        # Get required bands
        bands = ["B02", "B03", "B04", "B08"]  # Blue, Green, Red, NIR
        hrefs = [
            best_item.assets[band]["href"]
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
    
    def _process_landsat8(self, items: List, bbox: Union[Polygon, box]) -> Dict:
        """Process Landsat-8 data."""
        # Sort by cloud cover and get best scene
        items.sort(key=lambda x: float(x.properties["eo:cloud_cover"]))
        best_item = items[0]
        
        # Get required bands
        bands = ["B2", "B3", "B4", "B5"]  # Blue, Green, Red, NIR
        hrefs = [
            best_item.assets[band]["href"]
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
    
    def get_available_collections(self) -> List[str]:
        """Get list of available collections."""
        collections = self.catalog.get_collections()
        return [c.id for c in collections]
    
    def get_collection_info(self, collection_id: str) -> Dict:
        """Get detailed information about a collection."""
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