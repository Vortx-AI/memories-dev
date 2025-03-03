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
from datetime import datetime, timedelta
import aiohttp
import logging

from .sources import (
    PlanetaryCompute,
    SentinelAPI,
    LandsatAPI,
    OvertureAPI,
    OSMDataAPI
)
from memories.utils.processors import ImageProcessor, VectorProcessor, DataFusion

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
    
    def _validate_bbox(self, bbox_coords):
        """Validate and convert bbox coordinates to the correct format."""
        try:
            if isinstance(bbox_coords, (list, tuple)) and len(bbox_coords) == 4:
                return {
                    'xmin': float(bbox_coords[0]),
                    'ymin': float(bbox_coords[1]),
                    'xmax': float(bbox_coords[2]),
                    'ymax': float(bbox_coords[3])
                }
            elif isinstance(bbox_coords, dict) and all(k in bbox_coords for k in ['xmin', 'ymin', 'xmax', 'ymax']):
                return {k: float(v) for k, v in bbox_coords.items()}
            else:
                logger.error(f"Invalid bbox format: {bbox_coords}")
                return None
        except (ValueError, TypeError) as e:
            logger.error(f"Error validating bbox: {str(e)}")
            return None

    async def get_satellite_data(self, bbox_coords: Union[List[float], Dict[str, float]], start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """Get satellite data for a given bounding box.

        Args:
            bbox_coords (Union[List[float], Dict[str, float]]): Bounding box coordinates [xmin, ymin, xmax, ymax] or
                dict with keys 'xmin', 'ymin', 'xmax', 'ymax'
            start_date (Optional[str]): Start date for data collection (YYYY-MM-DD)
            end_date (Optional[str]): End date for data collection (YYYY-MM-DD)

        Returns:
            Dict[str, Any]: Dictionary containing satellite data and metadata
        """
        try:
            # Convert bbox_coords to dictionary format if it's a list
            if isinstance(bbox_coords, (list, tuple)) and len(bbox_coords) == 4:
                bbox_dict = {
                    "xmin": float(bbox_coords[0]),
                    "ymin": float(bbox_coords[1]),
                    "xmax": float(bbox_coords[2]),
                    "ymax": float(bbox_coords[3])
                }
            elif isinstance(bbox_coords, dict) and all(k in bbox_coords for k in ['xmin', 'ymin', 'xmax', 'ymax']):
                bbox_dict = {k: float(v) for k, v in bbox_coords.items()}
            else:
                return {"status": "error", "message": "Invalid bounding box format"}

            # Convert string dates to datetime if provided
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, "%Y-%m-%d")
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, "%Y-%m-%d")

            result = await self.sentinel.download_data(
                bbox=bbox_dict,
                start_date=start_date,
                end_date=end_date
            )

            if result["status"] == "error":
                return result

            return {
                "status": "success",
                "metadata": result["metadata"],
                "data": result.get("data", None)
            }

        except Exception as e:
            logging.error(f"Error in get_satellite_data: {str(e)}")
            return {"status": "error", "message": str(e)}
    
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
        bbox_coords: Union[List[float], Dict[str, float]],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        layers: List[str] = ["buildings", "roads", "landuse"]
    ) -> Dict[str, Any]:
        """Get both satellite and vector data for a location.

        Args:
            bbox_coords (Union[List[float], Dict[str, float]]): Bounding box coordinates [xmin, ymin, xmax, ymax] or
                dict with keys 'xmin', 'ymin', 'xmax', 'ymax'
            start_date (Optional[str]): Start date for data collection (YYYY-MM-DD)
            end_date (Optional[str]): End date for data collection (YYYY-MM-DD)
            layers (List[str]): Vector data layers to fetch

        Returns:
            Dict[str, Any]: Dictionary containing both satellite and vector data
        """
        try:
            logger.info(f"get_location_data - Input bbox: {bbox_coords}, type: {type(bbox_coords)}")
            
            # Get satellite data
            satellite_data = await self.get_satellite_data(
                bbox_coords=bbox_coords,
                start_date=start_date,
                end_date=end_date
            )
            
            if satellite_data["status"] == "error":
                return satellite_data
            
            # Get vector data
            vector_data = await self.get_vector_data(
                bbox=bbox_coords,
                layers=layers
            )
            
            return {
                "status": "success",
                "satellite_data": satellite_data,
                "vector_data": vector_data
            }
            
        except Exception as e:
            logger.error(f"Error in get_location_data: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            } 