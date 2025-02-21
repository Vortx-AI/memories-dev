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
from abc import ABC, abstractmethod

from .sources import (
    PlanetaryCompute,
    SentinelAPI,
    LandsatAPI,
    OvertureAPI,
    OSMDataAPI
)
from ..utils.processors import ImageProcessor, VectorProcessor, DataFusion

logger = logging.getLogger(__name__)

class DataConnector(ABC):
    @abstractmethod
    def download_data(self, location: Tuple[float, float], time_range: Tuple[str, str], **params) -> Any:
        """
        Download data from the source.
        
        Args:
            location: Tuple of (latitude, longitude)
            time_range: Tuple of (start_date, end_date)
            **params: Additional parameters specific to the connector
            
        Returns:
            Downloaded and processed data
        """
        pass

class OSMLocalSource(DataConnector):
    def download_data(self, location: Tuple[float, float], time_range: Tuple[str, str], **params) -> Any:
        bbox = self._location_to_bbox(location)
        from memories.data_acquisition.sources.osm_local import get_landuse_data
        return get_landuse_data(bbox=bbox, **params)
    
    def _location_to_bbox(self, location: Tuple[float, float]) -> Tuple[float, float, float, float]:
        lat, lon = location
        # Add 0.1 degree buffer around the point
        return (lon-0.1, lat-0.1, lon+0.1, lat+0.1)

class SentinelConnector(DataConnector):
    def download_data(self, location: Tuple[float, float], time_range: Tuple[str, str], **params) -> Any:
        # TODO: Implement Sentinel data download
        raise NotImplementedError("Sentinel connector not implemented yet")

class LandsatConnector(DataConnector):
    def download_data(self, location: Tuple[float, float], time_range: Tuple[str, str], **params) -> Any:
        # TODO: Implement Landsat data download
        raise NotImplementedError("Landsat connector not implemented yet")

class OvertureConnector(DataConnector):
    def download_data(self, location: Tuple[float, float], time_range: Tuple[str, str], **params) -> Any:
        # TODO: Implement Overture data download
        raise NotImplementedError("Overture connector not implemented yet")

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
        logger.info(f"Input bbox: {bbox}, type: {type(bbox)}")
        
        if isinstance(bbox, Polygon):
            logger.info("Input is a Polygon")
            return bbox
        elif isinstance(bbox, (tuple, list)):
            logger.info(f"Input is a {type(bbox).__name__} with length {len(bbox)}")
            if len(bbox) == 4:
                # Convert to list and ensure all values are float
                result = [float(x) for x in bbox]
                logger.info(f"Converted to float list: {result}")
                return result
            else:
                logger.error(f"Invalid bbox length: {len(bbox)}")
                raise ValueError("Invalid bbox format. Must be [west, south, east, north] or Polygon")
        else:
            logger.error(f"Invalid bbox type: {type(bbox)}")
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
        bbox: Union[List[float], Tuple[float, float, float, float], Polygon],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        refresh: bool = False
    ) -> Dict[str, Any]:
        """Get satellite data from Sentinel API.
        
        Args:
            bbox: Bounding box coordinates
            start_date: Optional start date
            end_date: Optional end date
            refresh: Whether to force refresh cached data
            
        Returns:
            Dictionary containing satellite data
        """
        logger.info(f"get_satellite_data - Input bbox: {bbox}, type: {type(bbox)}")
        
        # Convert bbox to appropriate format
        bbox_coords = self._get_bbox_polygon(bbox)
        logger.info(f"get_satellite_data - Converted bbox_coords: {bbox_coords}, type: {type(bbox_coords)}")
        
        # Convert bbox list to dictionary format for Sentinel API
        if isinstance(bbox_coords, list):
            bbox_dict = {
                'xmin': bbox_coords[0],
                'ymin': bbox_coords[1],
                'xmax': bbox_coords[2],
                'ymax': bbox_coords[3]
            }
        elif isinstance(bbox_coords, Polygon):
            bounds = bbox_coords.bounds
            bbox_dict = {
                'xmin': bounds[0],
                'ymin': bounds[1],
                'xmax': bounds[2],
                'ymax': bounds[3]
            }
        else:
            raise ValueError("Invalid bbox format")
        
        # Generate cache key
        cache_key = f"satellite_{bbox_coords}_{start_date}_{end_date}"
        
        # Check cache unless refresh is requested
        if not refresh and self.cache_exists(cache_key):
            cached_data = self.get_from_cache(cache_key)
            if cached_data:
                return cached_data
        
        # Get data from Sentinel API
        satellite_data = await self.sentinel.download_data(
            bbox=bbox_dict,
            cloud_cover=10.0,
            bands={
                "B04": "Red",
                "B08": "NIR",
                "B11": "SWIR"
            }
        )
        
        # Convert numpy arrays to lists for JSON serialization
        if satellite_data.get('success') and 'data' in satellite_data:
            if isinstance(satellite_data['data'], np.ndarray):
                satellite_data['data'] = satellite_data['data'].tolist()
        
        # Save to cache if not refreshing
        if not refresh:
            self.save_to_cache(cache_key, satellite_data)
        else:
            # For refresh, use a new cache key with timestamp
            refresh_cache_key = f"{cache_key}_{datetime.now().isoformat()}"
            self.save_to_cache(refresh_cache_key, satellite_data)
        
        return satellite_data
    
    async def get_vector_data(
        self,
        bbox: Union[Tuple[float, float, float, float], List[float], Polygon],
        layers: List[str] = ["buildings", "roads", "landuse"]
    ) -> Dict[str, Any]:
        """Get vector data from Overture Maps and OSM."""
        try:
            logger.info(f"get_vector_data - Input bbox: {bbox}, type: {type(bbox)}")
            bbox_coords = self._get_bbox_polygon(bbox)
            logger.info(f"get_vector_data - Converted bbox_coords: {bbox_coords}, type: {type(bbox_coords)}")
            
            # Convert bbox to list format for APIs
            if isinstance(bbox_coords, Polygon):
                bounds = bbox_coords.bounds
                bbox_list = [bounds[0], bounds[1], bounds[2], bounds[3]]
            else:
                bbox_list = bbox_coords
            
            logger.info(f"get_vector_data - Final bbox_list: {bbox_list}, type: {type(bbox_list)}")
            
            # Get Overture data
            overture_results = await self.overture.search(bbox_list)
            
            # Get OSM data
            osm_results = await self.osm.search(
                bbox=bbox_list,
                tags=layers
            )
            
            return {
                "overture": overture_results,
                "osm": osm_results
            }
        except Exception as e:
            logger.error(f"Error in get_vector_data: {str(e)}")
            logger.error(f"Input bbox: {bbox}, type: {type(bbox)}")
            raise
    
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
        try:
            logger.info(f"prepare_training_data - Input bbox: {bbox}, type: {type(bbox)}")
            
            # Convert bbox to appropriate format
            bbox_coords = self._get_bbox_polygon(bbox)
            logger.info(f"prepare_training_data - Converted bbox_list: {bbox_coords}, type: {type(bbox_coords)}")
            
            # Convert bbox list to dictionary format for satellite data
            if isinstance(bbox_coords, list):
                bbox_dict = {
                    'xmin': bbox_coords[0],
                    'ymin': bbox_coords[1],
                    'xmax': bbox_coords[2],
                    'ymax': bbox_coords[3]
                }
            elif isinstance(bbox_coords, Polygon):
                bounds = bbox_coords.bounds
                bbox_dict = {
                    'xmin': bounds[0],
                    'ymin': bounds[1],
                    'xmax': bounds[2],
                    'ymax': bounds[3]
                }
            else:
                raise ValueError("Invalid bbox format")
            
            # Get satellite data
            satellite_data = await self.get_satellite_data(
                bbox=bbox_coords,
                start_date=start_date,
                end_date=end_date,
                refresh=False
            )
            
            # Get vector data
            vector_data = await self.get_vector_data(
                bbox=bbox_coords,
                layers=vector_layers
            )
            
            return {
                "satellite_data": satellite_data,
                "vector_data": vector_data,
                "bbox": bbox_dict
            }
        except Exception as e:
            logger.error(f"Error in prepare_training_data: {str(e)}")
            logger.error(f"Input bbox: {bbox}, type: {type(bbox)}")
            raise
    
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
        # Convert bbox to appropriate format
        bbox_coords = self._get_bbox_polygon(bbox)
        
        # Convert bbox list to dictionary format for Sentinel API
        if isinstance(bbox_coords, list):
            bbox_dict = {
                'xmin': bbox_coords[0],
                'ymin': bbox_coords[1],
                'xmax': bbox_coords[2],
                'ymax': bbox_coords[3]
            }
        elif isinstance(bbox_coords, Polygon):
            bounds = bbox_coords.bounds
            bbox_dict = {
                'xmin': bounds[0],
                'ymin': bounds[1],
                'xmax': bounds[2],
                'ymax': bounds[3]
            }
        else:
            raise ValueError("Invalid bbox format")
        
        # Get Overture data
        overture_data = await self.overture.search(bbox_coords)
        
        # Get OSM data
        osm_data = await self.osm.search(bbox_coords)
        
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
        
        # Convert numpy arrays to lists for JSON serialization
        if satellite_data.get('success') and 'data' in satellite_data:
            satellite_data['data'] = satellite_data['data'].tolist()
        
        return {
            "overture": overture_data,
            "osm": osm_data,
            "satellite": satellite_data
        }

    def get_data(self, 
                 artifact_type: str, 
                 source: str, 
                 location: Tuple[float, float],
                 time_range: Tuple[str, str],
                 **params) -> Any:
        """
        Get data for a specific artifact type and source
        
        Args:
            artifact_type: Type of data (satellite, landuse, etc.)
            source: Specific data source (sentinel-2, osm, etc.)
            location: Tuple of (latitude, longitude)
            time_range: Tuple of (start_date, end_date)
            **params: Additional parameters for the connector
            
        Returns:
            Downloaded and processed data
        """
        if artifact_type not in self.data_connectors:
            raise ValueError(f"Unknown artifact type: {artifact_type}")
            
        if source not in self.data_connectors[artifact_type]:
            raise ValueError(f"Unknown source {source} for artifact type {artifact_type}")
            
        connector = self.data_connectors[artifact_type][source]
        
        try:
            return connector.download_data(
                location=location,
                time_range=time_range,
                **params
            )
        except Exception as e:
            raise Exception(f"Error downloading data from {source}: {str(e)}")

    def create_memories(self, 
                       model: Any,
                       location: Tuple[float, float],
                       time_range: Tuple[str, str],
                       artifacts: Dict[str, List[str]]) -> Dict[str, Dict[str, Any]]:
        """
        Create memories based on specified artifacts
        
        Args:
            model: The model instance
            location: Tuple of (latitude, longitude)
            time_range: Tuple of (start_date, end_date)
            artifacts: Dictionary mapping artifact types to list of sources
            
        Returns:
            Dictionary of memories organized by artifact type and source
        """
        memories = {}
        
        for artifact_type, sources in artifacts.items():
            memories[artifact_type] = {}
            for source in sources:
                try:
                    data = self.get_data(
                        artifact_type=artifact_type,
                        source=source,
                        location=location,
                        time_range=time_range
                    )
                    memories[artifact_type][source] = data
                except Exception as e:
                    print(f"Warning: Failed to get data for {artifact_type}/{source}: {str(e)}")
                    memories[artifact_type][source] = None
        
        return memories

def main():
    """Example usage of DataManager"""
    data_manager = DataManager(cache_dir="data/cache")
    
    # Example usage
    try:
        memories = data_manager.create_memories(
            model=None,  # Replace with actual model
            location=(37.7749, -122.4194),  # San Francisco
            time_range=("2024-01-01", "2024-02-01"),
            artifacts={
                "satellite": ["sentinel-2"],
                "landuse": ["osm"]
            }
        )
        print("Successfully created memories:", memories.keys())
    except Exception as e:
        print(f"Error creating memories: {str(e)}")

if __name__ == "__main__":
    main() 