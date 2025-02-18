"""
Data manager for coordinating data acquisition and processing.
"""

import os
from typing import Dict, List, Optional, Tuple, Union, Any
from pathlib import Path
import rasterio
import geopandas as gpd
from shapely.geometry import box, Polygon
import planetary_computer as pc
import pystac_client
import numpy as np
import json
from datetime import datetime
import aiohttp
import logging

from .sources import (
    PlanetaryCompute,
    SentinelAPI,
    LandsatAPI,
    OvertureAPI,
    OSMDataAPI
)
from ..utils.processors import ImageProcessor, VectorProcessor, DataFusion

logger = logging.getLogger(__name__)

class DataManager:
    """Manages data acquisition and processing from various sources."""
    
    def __init__(self, cache_dir: str):
        """
        Initialize data manager.
        
        Args:
            cache_dir: Directory for caching downloaded data
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize data sources
        self.overture = OvertureAPI(data_dir=str(self.cache_dir))
        self.planetary = PlanetaryCompute(cache_dir=str(self.cache_dir))
        self.sentinel = SentinelAPI(data_dir=str(self.cache_dir))
        self.landsat = LandsatAPI(cache_dir=str(self.cache_dir))
        self.osm = OSMDataAPI(cache_dir=str(self.cache_dir))
        
        # Initialize processors
        self.image_processor = ImageProcessor()
        self.vector_processor = VectorProcessor()
        self.data_fusion = DataFusion()
        
        logger.info(f"Initialized data manager with cache at {self.cache_dir}")
    
    def _get_bbox_polygon(self, bbox: Union[Tuple[float, float, float, float], List[float], Polygon]) -> Union[List[float], Polygon]:
        """Convert bbox to appropriate format."""
        if isinstance(bbox, Polygon):
            return bbox
        elif isinstance(bbox, (tuple, list)) and len(bbox) == 4:
            return bbox  # Return as list for APIs that expect [west, south, east, north]
        else:
            raise ValueError("Invalid bbox format. Must be [west, south, east, north] or Polygon")
    
    def cache_exists(self, cache_key: str) -> bool:
        """Check if data exists in cache."""
        cache_path = self.cache_dir / f"{cache_key}.json"
        return cache_path.exists()
    
    def get_from_cache(self, cache_key: str) -> Optional[Dict]:
        """Get data from cache."""
        cache_path = self.cache_dir / f"{cache_key}.json"
        if cache_path.exists():
            with open(cache_path, 'r') as f:
                return json.load(f)
        return None
    
    def save_to_cache(self, cache_key: str, data: Dict) -> None:
        """Save data to cache."""
        cache_path = self.cache_dir / f"{cache_key}.json"
        with open(cache_path, 'w') as f:
            json.dump(data, f)
    
    async def get_satellite_data(
        self,
        bbox: Union[Tuple[float, float, float, float], List[float], Polygon],
        start_date: str,
        end_date: str,
        collections: List[str] = ["sentinel-2-l2a"],
        cloud_cover: float = 20.0,
        resolution: Optional[float] = None
    ) -> Dict[str, Any]:
        """Get satellite imagery data."""
        bbox_coords = self._get_bbox_polygon(bbox)
        
        # Convert shapely box to coordinates for APIs that need them
        if isinstance(bbox_coords, Polygon):
            bounds = bbox_coords.bounds
            bbox_coords = [bounds[0], bounds[1], bounds[2], bounds[3]]
        
        results = {}
        
        # Get Planetary Computer data
        pc_results = await self.planetary.search_and_download(
            bbox=bbox_coords,
            start_date=start_date,
            end_date=end_date,
            collections=collections,
            cloud_cover=cloud_cover
        )
        if pc_results:
            results["pc"] = pc_results
        
        # Get Sentinel data
        sentinel_results = await self.sentinel.search(
            bbox=bbox_coords,
            start_date=start_date,
            end_date=end_date,
            cloud_cover=cloud_cover
        )
        if sentinel_results:
            results["sentinel"] = sentinel_results
        
        # Get Landsat data
        landsat_results = await self.landsat.search(
            bbox=bbox_coords,
            start_date=start_date,
            end_date=end_date,
            cloud_cover=cloud_cover
        )
        if landsat_results:
            results["landsat"] = landsat_results
        
        # Apply resolution if specified
        if resolution is not None:
            for source, data in results.items():
                if isinstance(data, dict) and "items" in data:
                    data["resolution"] = resolution
        
        return results
    
    async def get_vector_data(
        self,
        bbox: Union[Tuple[float, float, float, float], List[float], Polygon],
        layers: List[str] = ["buildings", "roads", "landuse"]
    ) -> Dict[str, Any]:
        """Get vector data from Overture Maps and OSM."""
        bbox_coords = self._get_bbox_polygon(bbox)
        
        # Get Overture data
        overture_results = await self.overture.search(
            bbox=bbox_coords,
            layer=layers[0] if layers else "buildings"
        )
        
        # Get OSM data
        osm_results = await self.osm.search(
            bbox=bbox_coords,
            tags=layers
        )
        
        return {
            "overture": overture_results,
            "osm": osm_results
        }
    
    async def prepare_training_data(
        self,
        bbox: Union[Tuple[float, float, float, float], List[float], Polygon],
        start_date: str,
        end_date: str,
        satellite_collections: List[str] = ["sentinel-2-l2a"],
        vector_layers: List[str] = ["buildings", "roads", "landuse"],
        cloud_cover: float = 20.0,
        resolution: Optional[float] = None
    ) -> Dict[str, Any]:
        """Prepare training data by combining satellite and vector data."""
        bbox_coords = self._get_bbox_polygon(bbox)
        
        # Get satellite data
        satellite_data = await self.get_satellite_data(
            bbox=bbox_coords,
            start_date=start_date,
            end_date=end_date,
            collections=satellite_collections,
            cloud_cover=cloud_cover,
            resolution=resolution
        )
        
        # Get vector data
        vector_data = await self.get_vector_data(
            bbox=bbox_coords,
            layers=vector_layers
        )
        
        return {
            "satellite_data": satellite_data,
            "vector_data": vector_data
        }
    
    async def download_satellite_data(
        self,
        collection: str,
        bbox: List[float],
        start_date: str,
        end_date: str,
        cloud_cover: float = 20.0
    ) -> List[Dict[str, Any]]:
        """Download satellite data from Planetary Computer.
        
        Args:
            collection: Satellite collection name
            bbox: Bounding box coordinates
            start_date: Start date
            end_date: End date
            cloud_cover: Maximum cloud cover percentage
            
        Returns:
            List of satellite data items
        """
        # In a real implementation, this would use the Planetary Computer API
        # For now, we return simulated data
        return [{
            "data": np.random.random((4, 100, 100)),
            "metadata": {
                "datetime": datetime.now().isoformat(),
                "cloud_cover": np.random.uniform(0, cloud_cover)
            }
        }]
    
    async def download_vector_data(
        self,
        layer: str,
        bbox: List[float]
    ) -> List[Dict[str, Any]]:
        """Download vector data from OpenStreetMap.
        
        Args:
            layer: Vector layer name
            bbox: Bounding box coordinates
            
        Returns:
            List of vector features
        """
        # In a real implementation, this would use the OSM API
        # For now, we return simulated data
        return [{
            "type": "Feature",
            "properties": {
                "area": np.random.uniform(100, 1000),
                "type": layer
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[bbox[0], bbox[1]], [bbox[0], bbox[3]],
                               [bbox[2], bbox[3]], [bbox[2], bbox[1]],
                               [bbox[0], bbox[1]]]]
            }
        }]

    async def get_location_data(
        self,
        bbox: List[float],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get location data from all sources.
        
        Args:
            bbox: Bounding box [min_lon, min_lat, max_lon, max_lat]
            start_date: Optional start date (YYYY-MM-DD)
            end_date: Optional end date (YYYY-MM-DD)
            
        Returns:
            Dictionary containing data from all sources
        """
        # Convert bbox list to dictionary for Sentinel API
        bbox_dict = {
            'xmin': bbox[0],
            'ymin': bbox[1],
            'xmax': bbox[2],
            'ymax': bbox[3]
        }
        
        # Get Overture data
        overture_data = await self.overture.search(bbox)
        
        # Get satellite data
        satellite_data = await self.sentinel.download_data(
            bbox=bbox_dict,
            cloud_cover=10.0,
            bands={
                "B04": "Red",
                "B08": "NIR",
                "B11": "SWIR"
            }
        )
        
        return {
            "overture": overture_data,
            "satellite": satellite_data
        } 