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
import pandas as pd
import shutil
import pyarrow as pa
import pyarrow.parquet as pq
import faiss
import torch

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
    
    def __init__(self, cache_dir: Optional[str] = None, load_embeddings: bool = True):
        # Set up storage paths and tiers
        self.project_root = Path(__file__).parents[2]
        
        # If cache_dir is provided, use it as the base for all storage paths
        base_path = Path(cache_dir) if cache_dir else self.project_root / 'data'
        self.cache_dir = base_path  # Store cache_dir as an attribute
        
        self.storage_paths = {
            'hot': base_path / 'cache',     # In-memory/temporary
            'warm': base_path / 'active',   # Frequent access
            'cold': base_path / 'archive',  # Infrequent access
            'glacier': base_path / 'backup' # Long-term storage
        }
        
        # Create storage directories
        for path in self.storage_paths.values():
            path.mkdir(parents=True, exist_ok=True)
            
        # Memory cache for hot storage
        self.hot_cache = {}
        
        # Initialize data sources
        self.overture = OvertureAPI(data_dir=str(self.storage_paths['warm']))
        self.planetary = PlanetaryCompute(cache_dir=str(self.storage_paths['warm']))
        self.sentinel = SentinelAPI(data_dir=str(self.storage_paths['warm']))
        self.landsat = LandsatAPI(cache_dir=str(self.storage_paths['warm']))
        self.osm = OSMDataAPI(cache_dir=str(self.storage_paths['warm']))
        
        # Initialize processors
        self.image_processor = ImageProcessor()
        self.vector_processor = VectorProcessor()
        self.data_fusion = DataFusion()
        
        logger.info(f"Initialized data manager with cache at {self.storage_paths['warm']}")
        
        # Set up logging
        self.setup_logging()
        
        # Initialize data catalog
        self.catalog_path = self.storage_paths['warm'] / 'data_catalog.json'
        self.catalog = self.load_catalog()
        
        # Initialize embeddings and FAISS index only if requested
        self.embeddings = None
        self.faiss_index = None
        self.vector_metadata = []
        self.embedding_dim = 300  # Standard embedding dimension
        
        if load_embeddings:
            try:
                self.embeddings = self.load_embeddings()
                self.faiss_index = faiss.IndexFlatL2(self.embedding_dim)
            except Exception as e:
                logger.warning(f"Failed to load embeddings: {str(e)}")
                self.embeddings = None
                self.faiss_index = None
    
    def setup_logging(self):
        """Set up logging configuration"""
        log_path = self.storage_paths['warm'] / 'logs'
        log_path.mkdir(exist_ok=True)
        
        logging.basicConfig(
            filename=log_path / 'data_manager.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def load_catalog(self) -> dict:
        """Load existing catalog or create new one"""
        if self.catalog_path.exists():
            with open(self.catalog_path, 'r') as f:
                return json.load(f)
        return {}

    def save_catalog(self):
        """Save catalog to disk"""
        with open(self.catalog_path, 'w') as f:
            json.dump(self.catalog, f, indent=2)

    def analyze_dataset(self, data: pd.DataFrame, metadata: dict) -> dict:
        """
        Analyze dataset and extract schema information
        
        Args:
            data: The dataset to analyze
            metadata: Basic metadata about the dataset
        """
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata,
            "schema": {
                "columns": {},
                "row_count": len(data),
                "memory_usage": data.memory_usage(deep=True).sum(),
            }
        }

        for column in data.columns:
            col_info = {
                "dtype": str(data[column].dtype),
                "null_count": data[column].isnull().sum()
            }
            
            # Get unique values for string columns
            if data[column].dtype == 'object' or data[column].dtype == 'string':
                unique_values = data[column].unique()
                if len(unique_values) < 100:  # Only store if manageable
                    col_info["unique_values"] = unique_values.tolist()
                col_info["unique_count"] = len(unique_values)

            analysis["schema"]["columns"][column] = col_info

        return analysis

    def register_dataset(self, 
                        data: pd.DataFrame, 
                        artifact_type: str,
                        source: str,
                        location: tuple,
                        time_range: tuple,
                        storage_tier: str):
        """
        Register dataset in catalog with analysis
        """
        metadata = {
            "artifact_type": artifact_type,
            "source": source,
            "location": {
                "latitude": location[0],
                "longitude": location[1]
            },
            "time_range": {
                "start": time_range[0],
                "end": time_range[1]
            },
            "storage_tier": storage_tier
        }

        # Generate unique dataset ID
        dataset_id = f"{artifact_type}_{source}_{location[0]}_{location[1]}_{time_range[0]}_{time_range[1]}"
        
        # Analyze dataset
        analysis = self.analyze_dataset(data, metadata)
        
        # Add to catalog
        self.catalog[dataset_id] = analysis
        
        # Save catalog
        self.save_catalog()
        
        # Log the addition
        self.logger.info(f"Registered dataset: {dataset_id}")
        self.logger.info(f"Schema: {json.dumps(analysis['schema'], indent=2)}")

        # Add schema and unique values to FAISS index
        self.index_dataset_schema(data, artifact_type, source)
        
        # Save FAISS index
        self.save_faiss_index()

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
        cache_path = self.storage_paths['warm'] / f"{cache_key}.json"
        return cache_path.exists()
    
    def get_from_cache(self, cache_key: str) -> Optional[Dict]:
        """Get data from cache."""
        cache_path = self.storage_paths['warm'] / f"{cache_key}.json"
        if cache_path.exists():
            with open(cache_path, 'r') as f:
                return json.load(f)
        return None
    
    def save_to_cache(self, cache_key: str, data: Dict) -> None:
        """Save data to cache."""
        cache_path = self.storage_paths['warm'] / f"{cache_key}.json"
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

    def check_existing_data(self, 
                           artifact_type: str,
                           source: str, 
                           location: tuple,
                           time_range: tuple) -> Optional[Dict]:
        """
        Check if data already exists for given parameters
        
        Args:
            artifact_type: Type of data (satellite, landuse, etc.)
            source: Data source (osm, sentinel-2, etc.)
            location: (latitude, longitude)
            time_range: (start_date, end_date)
            
        Returns:
            Dict with dataset info if exists, None otherwise
        """
        # Define tolerance for coordinate matching (e.g., 0.01 degrees)
        COORD_TOLERANCE = 0.01
        
        for dataset_id, info in self.catalog.items():
            metadata = info["metadata"]
            
            # Check if this is the same type and source
            if (metadata["artifact_type"] != artifact_type or 
                metadata["source"] != source):
                continue
            
            # Check if location matches within tolerance
            stored_lat = metadata["location"]["latitude"]
            stored_lon = metadata["location"]["longitude"]
            if (abs(stored_lat - location[0]) > COORD_TOLERANCE or 
                abs(stored_lon - location[1]) > COORD_TOLERANCE):
                continue
            
            # Check if time range overlaps
            stored_start = metadata["time_range"]["start"]
            stored_end = metadata["time_range"]["end"]
            if (time_range[0] <= stored_end and 
                time_range[1] >= stored_start):
                self.logger.info(f"Found existing data for {artifact_type}/{source} at location {location}")
                return {
                    "dataset_id": dataset_id,
                    "info": info,
                    "storage_tier": metadata["storage_tier"]
                }
        
        self.logger.info(f"No existing data found for {artifact_type}/{source} at location {location}")
        return None

    def determine_storage_tier(self, data_size: int, last_access: datetime) -> str:
        """
        Determine appropriate storage tier based on data size and access patterns
        """
        now = datetime.now()
        days_since_access = (now - last_access).days
        
        # Size thresholds in bytes
        HOT_THRESHOLD = 100 * 1024 * 1024  # 100MB
        WARM_THRESHOLD = 1 * 1024 * 1024 * 1024  # 1GB
        
        if data_size < HOT_THRESHOLD and days_since_access < 1:
            return 'hot'
        elif data_size < WARM_THRESHOLD and days_since_access < 7:
            return 'warm'
        elif days_since_access < 30:
            return 'cold'
        else:
            return 'glacier'

    def store_data(self, 
                   data: Union[pd.DataFrame, gpd.GeoDataFrame], 
                   dataset_id: str,
                   storage_tier: str) -> None:
        """
        Store data in the specified storage tier
        """
        if storage_tier == 'hot':
            self.hot_cache[dataset_id] = data
            
        else:
            # Determine file path
            file_path = self.storage_paths[storage_tier] / f"{dataset_id}.parquet"
            
            # Apply compression based on tier
            compression = {
                'warm': 'snappy',    # Fast compression/decompression
                'cold': 'zstd',      # Better compression
                'glacier': 'brotli'  # Best compression
            }.get(storage_tier, 'snappy')
            
            # Save with appropriate compression
            if isinstance(data, gpd.GeoDataFrame):
                data.to_parquet(file_path, compression=compression)
            else:
                table = pa.Table.from_pandas(data)
                pq.write_table(table, file_path, compression=compression)

    def load_data(self, dataset_id: str, current_tier: str) -> Tuple[Any, str]:
        """
        Load data from storage, potentially moving between tiers
        """
        # Check hot cache first
        if dataset_id in self.hot_cache:
            return self.hot_cache[dataset_id], 'hot'
            
        # Look in other tiers
        for tier in ['warm', 'cold', 'glacier']:
            file_path = self.storage_paths[tier] / f"{dataset_id}.parquet"
            if file_path.exists():
                # Load data
                try:
                    data = gpd.read_parquet(file_path)
                except:
                    data = pd.read_parquet(file_path)
                
                # Determine if tier change needed
                new_tier = self.determine_storage_tier(
                    data_size=file_path.stat().st_size,
                    last_access=datetime.fromtimestamp(file_path.stat().st_mtime)
                )
                
                # Move to new tier if needed
                if new_tier != tier:
                    self.store_data(data, dataset_id, new_tier)
                    if tier != 'hot':  # Don't delete if moving to hot cache
                        file_path.unlink()  # Remove from old tier
                    
                    # Update catalog
                    self.catalog[dataset_id]['metadata']['storage_tier'] = new_tier
                    self.save_catalog()
                
                return data, new_tier
                
        return None, None

    def get_data(self, 
                 artifact_type: str, 
                 source: str, 
                 location: tuple,
                 time_range: tuple,
                 **params) -> Any:
        """Get data with storage tier management"""
        
        # Check if data already exists
        existing_data = self.check_existing_data(
            artifact_type=artifact_type,
            source=source,
            location=location,
            time_range=time_range
        )
        
        if existing_data:
            dataset_id = existing_data['dataset_id']
            current_tier = existing_data['storage_tier']
            
            # Try to load from storage
            data, new_tier = self.load_data(dataset_id, current_tier)
            if data is not None:
                self.logger.info(f"Loaded data from {current_tier} storage, moved to {new_tier}")
                return data
        
        # Download new data if not found or couldn't load
        connector = self.data_connectors[artifact_type][source]
        try:
            data = connector.download_data(
                location=location,
                time_range=time_range,
                **params
            )
            
            if isinstance(data, (pd.DataFrame, gpd.GeoDataFrame)):
                # Generate dataset_id
                dataset_id = f"{artifact_type}_{source}_{location[0]}_{location[1]}_{time_range[0]}_{time_range[1]}"
                
                # Determine initial storage tier
                initial_tier = self.determine_storage_tier(
                    data_size=data.memory_usage(deep=True).sum(),
                    last_access=datetime.now()
                )
                
                # Store data
                self.store_data(data, dataset_id, initial_tier)
                
                # Register in catalog
                self.register_dataset(
                    data=data,
                    artifact_type=artifact_type,
                    source=source,
                    location=location,
                    time_range=time_range,
                    storage_tier=initial_tier
                )
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error downloading data from {source}: {str(e)}")
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

    def query_catalog(self, **filters) -> list:
        """
        Query the data catalog with filters
        """
        results = []
        for dataset_id, info in self.catalog.items():
            match = all(
                info["metadata"].get(k) == v 
                for k, v in filters.items()
            )
            if match:
                results.append({
                    "dataset_id": dataset_id,
                    "info": info
                })
        return results

    def load_embeddings(self) -> Optional[Dict[str, np.ndarray]]:
        """Load pre-trained word embeddings from numpy file if available"""
        embeddings_path = self.project_root / 'models' / 'word_embeddings.npy'
        vocab_path = self.project_root / 'models' / 'vocab.json'
        
        if not embeddings_path.exists() or not vocab_path.exists():
            logger.warning("Word embeddings or vocabulary file not found")
            return None
            
        try:
            # Load embeddings matrix
            embeddings_matrix = np.load(str(embeddings_path))
            
            # Load vocabulary
            with open(vocab_path, 'r') as f:
                vocab = json.load(f)
                
            # Create word-to-vector dictionary
            embeddings_dict = {word: embeddings_matrix[idx] for word, idx in vocab.items()}
            
            logger.info(f"Loaded {len(embeddings_dict)} word embeddings")
            return embeddings_dict
            
        except Exception as e:
            logger.error(f"Error loading embeddings: {str(e)}")
            return None

    def get_embedding(self, text: str) -> np.ndarray:
        """Get embedding for text by averaging word vectors.
        
        If any word in the text is unknown (not in vocabulary), returns a zero vector.
        Otherwise returns the average of the word vectors for all words.
        
        Args:
            text: Input text to get embedding for
            
        Returns:
            300-dimensional numpy array - either zero vector if any word unknown,
            or average of word vectors if all words known
        """
        if self.embeddings is None:
            return None
            
        words = text.lower().split()
        
        # Return zeros if any word is unknown
        if any(word not in self.embeddings for word in words):
            return np.zeros(self.embedding_dim)
        
        # All words are known, so get their vectors and average
        vectors = [self.embeddings[word] for word in words]
        return np.mean(vectors, axis=0)

    def add_to_faiss_index(self, 
                          text: str, 
                          is_column: bool, 
                          associated_column: str = None) -> None:
        """Add text embedding to FAISS index with metadata if available"""
        if self.faiss_index is None or self.embeddings is None:
            return
            
        vector = self.get_embedding(text)
        if vector is None:
            return
            
        vector = vector.reshape(1, -1).astype(np.float32)
        self.faiss_index.add(vector)
        self.vector_metadata.append({
            'text': text,
            'is_column': is_column,
            'associated_column': associated_column,
            'index': self.faiss_index.ntotal - 1
        })

    def index_dataset_schema(self, 
                           data: pd.DataFrame, 
                           artifact_type: str,
                           source: str) -> None:
        """Index column names and unique values in FAISS if available"""
        if self.faiss_index is None or self.embeddings is None:
            return
            
        # Index column names
        for column in data.columns:
            self.add_to_faiss_index(
                text=column,
                is_column=True
            )
            
            # Index unique values for string columns
            if data[column].dtype == 'object' or data[column].dtype == 'string':
                unique_values = set(data[column].dropna().unique())
                for value in unique_values:
                    if isinstance(value, str):
                        self.add_to_faiss_index(
                            text=value,
                            is_column=False,
                            associated_column=column
                        )

        if self.faiss_index is not None:
            self.logger.info(f"Indexed schema for {artifact_type}/{source}: "
                            f"{len(data.columns)} columns, "
                            f"{len(self.vector_metadata)} total vectors")

    def search_similar(self, query: str, k: int = 5) -> List[Dict]:
        """Search for similar terms in the index"""
        query_vector = self.get_embedding(query)
        query_vector = query_vector.reshape(1, -1).astype(np.float32)
        
        distances, indices = self.faiss_index.search(query_vector, k)
        
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx >= 0:  # Valid index
                metadata = self.vector_metadata[idx]
                results.append({
                    'text': metadata['text'],
                    'is_column': metadata['is_column'],
                    'associated_column': metadata['associated_column'],
                    'distance': float(dist)
                })
        
        return results

    def save_faiss_index(self):
        """Save FAISS index and metadata"""
        index_path = self.storage_paths['warm'] / 'faiss_index.bin'
        metadata_path = self.storage_paths['warm'] / 'faiss_metadata.json'
        
        faiss.write_index(self.faiss_index, str(index_path))
        with open(metadata_path, 'w') as f:
            json.dump(self.vector_metadata, f)

    def load_faiss_index(self):
        """Load FAISS index and metadata"""
        index_path = self.storage_paths['warm'] / 'faiss_index.bin'
        metadata_path = self.storage_paths['warm'] / 'faiss_metadata.json'
        
        if index_path.exists() and metadata_path.exists():
            self.faiss_index = faiss.read_index(str(index_path))
            with open(metadata_path, 'r') as f:
                self.vector_metadata = json.load(f)

def main():
    """Example usage of DataManager"""
    data_manager = DataManager()
    
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