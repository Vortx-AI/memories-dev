"""
Data manager for coordinating data acquisition and processing.
"""

import os
from typing import Dict, List, Optional, Tuple, Union
from pathlib import Path
import rasterio
import geopandas as gpd
from shapely.geometry import box, Polygon
import planetary_computer as pc
import pystac_client
import numpy as np

from .sources import (
    PlanetaryCompute,
    SentinelAPI,
    LandsatAPI,
    OvertureAPI,
    OSMDataAPI
)
from .processors import ImageProcessor, VectorProcessor, DataFusion

class DataManager:
    """Manages data acquisition and processing from various sources."""
    
    def __init__(
        self,
        cache_dir: Optional[str] = None,
        pc_token: Optional[str] = None,
        sentinel_credentials: Optional[Dict] = None
    ):
        """
        Initialize the data manager.
        
        Args:
            cache_dir: Directory for caching downloaded data
            pc_token: Planetary Computer API token
            sentinel_credentials: Credentials for Sentinel Hub
        """
        self.cache_dir = Path(cache_dir) if cache_dir else Path.home() / ".dguformer_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize data sources
        self.pc = PlanetaryCompute(token=pc_token)
        self.sentinel = SentinelAPI(**sentinel_credentials) if sentinel_credentials else None
        self.landsat = LandsatAPI()
        self.overture = OvertureAPI()
        self.osm = OSMDataAPI()
        
        # Initialize processors
        self.image_processor = ImageProcessor()
        self.vector_processor = VectorProcessor()
        self.data_fusion = DataFusion()
    
    def get_satellite_data(
        self,
        bbox: Union[Tuple[float, float, float, float], Polygon],
        start_date: str,
        end_date: str,
        collections: List[str] = ["sentinel-2-l2a", "landsat-8-c2-l2"],
        cloud_cover: float = 20.0,
        resolution: float = 10.0
    ) -> Dict:
        """
        Get satellite imagery for a given bounding box.
        
        Args:
            bbox: Bounding box (minx, miny, maxx, maxy) or Polygon
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            collections: List of collections to search
            cloud_cover: Maximum cloud cover percentage
            resolution: Target resolution in meters
            
        Returns:
            Dictionary containing processed imagery and metadata
        """
        results = {}
        
        # Try Planetary Computer first
        pc_results = self.pc.search_and_download(
            bbox=bbox,
            start_date=start_date,
            end_date=end_date,
            collections=collections,
            cloud_cover=cloud_cover
        )
        
        if pc_results:
            results["planetary_computer"] = pc_results
        else:
            # Try alternative sources
            if "sentinel-2" in collections:
                sentinel_results = self.sentinel.search_and_download(
                    bbox=bbox,
                    start_date=start_date,
                    end_date=end_date,
                    cloud_cover=cloud_cover
                )
                if sentinel_results:
                    results["sentinel"] = sentinel_results
            
            if "landsat-8" in collections:
                landsat_results = self.landsat.search_and_download(
                    bbox=bbox,
                    start_date=start_date,
                    end_date=end_date,
                    cloud_cover=cloud_cover
                )
                if landsat_results:
                    results["landsat"] = landsat_results
        
        # Process and align all results
        processed_data = self.image_processor.process_satellite_data(
            results,
            target_resolution=resolution,
            bbox=bbox
        )
        
        return processed_data
    
    def get_vector_data(
        self,
        bbox: Union[Tuple[float, float, float, float], Polygon],
        layers: List[str] = ["buildings", "roads", "landuse"]
    ) -> Dict:
        """
        Get vector data from Overture Maps and OSM.
        
        Args:
            bbox: Bounding box or Polygon
            layers: List of layers to fetch
            
        Returns:
            Dictionary containing vector data by layer
        """
        results = {}
        
        # Try Overture Maps first
        overture_results = self.overture.get_features(bbox=bbox, layers=layers)
        if overture_results:
            results["overture"] = overture_results
        
        # Fallback to OSM
        osm_results = self.osm.get_features(bbox=bbox, layers=layers)
        if osm_results:
            results["osm"] = osm_results
        
        # Process and standardize vector data
        processed_data = self.vector_processor.process_vector_data(
            results,
            bbox=bbox
        )
        
        return processed_data
    
    def prepare_training_data(
        self,
        bbox: Union[Tuple[float, float, float, float], Polygon],
        start_date: str,
        end_date: str,
        satellite_collections: List[str] = ["sentinel-2-l2a"],
        vector_layers: List[str] = ["buildings", "roads"],
        resolution: float = 10.0
    ) -> Dict:
        """
        Prepare aligned satellite and vector data for model training.
        
        Args:
            bbox: Area of interest
            start_date: Start date
            end_date: End date
            satellite_collections: Satellite data collections to use
            vector_layers: Vector layers to include
            resolution: Target resolution in meters
            
        Returns:
            Dictionary containing aligned raster and vector data
        """
        # Get satellite imagery
        satellite_data = self.get_satellite_data(
            bbox=bbox,
            start_date=start_date,
            end_date=end_date,
            collections=satellite_collections,
            resolution=resolution
        )
        
        # Get vector data
        vector_data = self.get_vector_data(
            bbox=bbox,
            layers=vector_layers
        )
        
        # Fuse raster and vector data
        training_data = self.data_fusion.fuse_data(
            raster_data=satellite_data,
            vector_data=vector_data,
            bbox=bbox,
            resolution=resolution
        )
        
        return training_data
    
    def cache_exists(self, cache_key: str) -> bool:
        """Check if data exists in cache."""
        cache_path = self.cache_dir / cache_key
        return cache_path.exists()
    
    def get_from_cache(self, cache_key: str) -> Optional[Dict]:
        """Retrieve data from cache if it exists."""
        cache_path = self.cache_dir / cache_key
        if cache_path.exists():
            try:
                return np.load(cache_path, allow_pickle=True).item()
            except Exception:
                return None
        return None
    
    def save_to_cache(self, cache_key: str, data: Dict) -> None:
        """Save data to cache."""
        cache_path = self.cache_dir / cache_key
        np.save(cache_path, data) 