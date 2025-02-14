"""
Unified API interface for coordinating multiple data sources.
"""

import os
from typing import Dict, List, Optional, Tuple, Union, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from pathlib import Path
import time
from enum import Enum
import json
import geopandas as gpd
import pandas as pd
import duckdb
import pyarrow as pa
import pyarrow.parquet as pq
from shapely.geometry import box, Polygon
import planetary_computer as pc
import pystac_client
import xarray as xr
import rasterio
import owslib.wms
import owslib.wfs
from owslib.wmts import WebMapTileService

from .cog_stac_api import COGSTACAPI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataSourceSpeed(Enum):
    VERY_FAST = 5
    FAST = 4
    MODERATE = 3
    SLOW = 2
    VERY_SLOW = 1

class DataSourceCost(Enum):
    FREE = 5
    LOW = 4
    MODERATE = 3
    HIGH = 2
    VERY_HIGH = 1

class DataSourceReliability(Enum):
    VERY_HIGH = 5
    HIGH = 4
    MODERATE = 3
    LOW = 2
    VERY_LOW = 1

class DataSourceMetrics:
    def __init__(
        self,
        speed: DataSourceSpeed,
        cost: DataSourceCost,
        reliability: DataSourceReliability,
        requires_auth: bool = False,
        supports_streaming: bool = False,
        supports_async: bool = False
    ):
        self.speed = speed
        self.cost = cost
        self.reliability = reliability
        self.requires_auth = requires_auth
        self.supports_streaming = supports_streaming
        self.supports_async = supports_async

class UnifiedAPI:
    """Unified interface for accessing multiple data sources."""
    
    def __init__(
        self,
        cache_dir: Optional[str] = None,
        max_workers: int = 4,
        enable_streaming: bool = True
    ):
        """
        Initialize the unified API interface.
        
        Args:
            cache_dir: Directory for caching data
            max_workers: Maximum number of concurrent workers
            enable_streaming: Whether to enable data streaming
        """
        self.cache_dir = Path(cache_dir) if cache_dir else Path.home() / ".tileformer_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_workers = max_workers
        self.enable_streaming = enable_streaming
        
        # Initialize data sources with metrics
        self.data_sources = {
            "planetary_computer": {
                "client": self._init_planetary_computer(),
                "metrics": DataSourceMetrics(
                    speed=DataSourceSpeed.FAST,
                    cost=DataSourceCost.FREE,
                    reliability=DataSourceReliability.HIGH,
                    requires_auth=False,
                    supports_streaming=True,
                    supports_async=True
                )
            },
            "stac_api": {
                "client": None,  # Initialized on demand
                "metrics": DataSourceMetrics(
                    speed=DataSourceSpeed.MODERATE,
                    cost=DataSourceCost.FREE,
                    reliability=DataSourceReliability.HIGH,
                    requires_auth=False,
                    supports_streaming=True,
                    supports_async=True
                )
            },
            "wms_services": {
                "client": self._init_wms_services(),
                "metrics": DataSourceMetrics(
                    speed=DataSourceSpeed.VERY_FAST,
                    cost=DataSourceCost.FREE,
                    reliability=DataSourceReliability.MODERATE,
                    requires_auth=False,
                    supports_streaming=False,
                    supports_async=False
                )
            },
            "cog_stac": {
                "client": COGSTACAPI(
                    cache_dir=str(self.cache_dir / "cog_cache"),
                    max_workers=max_workers,
                    enable_streaming=enable_streaming
                ),
                "metrics": DataSourceMetrics(
                    speed=DataSourceSpeed.FAST,
                    cost=DataSourceCost.FREE,
                    reliability=DataSourceReliability.HIGH,
                    requires_auth=False,
                    supports_streaming=True,
                    supports_async=True
                )
            }
        }
        
        # Initialize database connection
        self.db = duckdb.connect(str(self.cache_dir / "metadata.db"))
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables."""
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS metadata (
                source TEXT,
                collection TEXT,
                bbox TEXT,
                timestamp TIMESTAMP,
                data_type TEXT,
                format TEXT,
                resolution FLOAT,
                file_path TEXT,
                metadata JSON
            )
        """)
        
        self.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_metadata_source_collection
            ON metadata(source, collection)
        """)
    
    def _init_planetary_computer(self) -> Any:
        """Initialize Planetary Computer client."""
        try:
            return pystac_client.Client.open(
                "https://planetarycomputer.microsoft.com/api/stac/v1",
                modifier=pc.sign_inplace
            )
        except Exception as e:
            logger.error(f"Failed to initialize Planetary Computer: {e}")
            return None
    
    def _init_wms_services(self) -> Dict:
        """Initialize WMS service connections."""
        wms_endpoints = {
            "usgs": "https://basemap.nationalmap.gov/arcgis/services/USGSTopo/MapServer/WMSServer",
            "nasa": "https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi",
            "esa": "https://services.sentinel-hub.com/ogc/wms/public-endpoint"
        }
        
        services = {}
        for name, url in wms_endpoints.items():
            try:
                services[name] = owslib.wms.WebMapService(url)
            except Exception as e:
                logger.error(f"Failed to initialize WMS service {name}: {e}")
        
        return services
    
    def get_data(
        self,
        bbox: Union[Tuple[float, float, float, float], Polygon],
        start_date: str,
        end_date: str,
        collections: List[str] = ["sentinel-2-l2a"],
        data_types: List[str] = ["raster", "vector"],
        formats: List[str] = ["geoparquet", "geojson"],
        resolution: float = 10.0,
        max_cloud_cover: float = 20.0,
        use_cache: bool = True
    ) -> Dict:
        """
        Get data from multiple sources with automatic fallback.
        
        Args:
            bbox: Bounding box or Polygon
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            collections: List of collections to search
            data_types: List of data types to fetch
            formats: List of output formats
            resolution: Target resolution in meters
            max_cloud_cover: Maximum cloud cover percentage
            use_cache: Whether to use cached data
            
        Returns:
            Dictionary containing retrieved data
        """
        results = {}
        errors = []
        
        # Check cache first if enabled
        if use_cache:
            cached_data = self._get_from_cache(
                bbox=bbox,
                collections=collections,
                start_date=start_date,
                end_date=end_date
            )
            if cached_data:
                return cached_data
        
        # Try sources in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_source = {
                executor.submit(
                    self._get_from_source,
                    source_name,
                    source_info,
                    bbox,
                    start_date,
                    end_date,
                    collections,
                    data_types,
                    resolution,
                    max_cloud_cover
                ): source_name
                for source_name, source_info in self.data_sources.items()
            }
            
            for future in as_completed(future_to_source):
                source_name = future_to_source[future]
                try:
                    data = future.result()
                    if data:
                        results[source_name] = data
                except Exception as e:
                    errors.append({
                        "source": source_name,
                        "error": str(e)
                    })
                    logger.error(f"Error fetching from {source_name}: {e}")
        
        if not results:
            raise RuntimeError(
                f"Failed to fetch data from all sources. Errors: {errors}"
            )
        
        # Convert to requested formats
        formatted_results = self._convert_formats(results, formats)
        
        # Cache results if enabled
        if use_cache:
            self._save_to_cache(formatted_results, bbox, collections)
        
        return formatted_results
    
    def _get_from_source(
        self,
        source_name: str,
        source_info: Dict,
        bbox: Union[Tuple[float, float, float, float], Polygon],
        start_date: str,
        end_date: str,
        collections: List[str],
        data_types: List[str],
        resolution: float,
        max_cloud_cover: float
    ) -> Optional[Dict]:
        """Get data from a specific source."""
        client = source_info["client"]
        if not client:
            return None
        
        try:
            if source_name == "planetary_computer":
                return self._get_from_planetary_computer(
                    client,
                    bbox,
                    start_date,
                    end_date,
                    collections,
                    max_cloud_cover
                )
            elif source_name == "stac_api":
                return self._get_from_stac(
                    client,
                    bbox,
                    start_date,
                    end_date,
                    collections
                )
            elif source_name == "wms_services":
                return self._get_from_wms(
                    client,
                    bbox,
                    resolution
                )
            elif source_name == "cog_stac":
                return self._get_from_cog_stac(
                    client,
                    bbox,
                    start_date,
                    end_date,
                    collections,
                    resolution
                )
        except Exception as e:
            logger.error(f"Error in {source_name}: {e}")
            return None
    
    def _get_from_planetary_computer(
        self,
        client: Any,
        bbox: Union[Tuple[float, float, float, float], Polygon],
        start_date: str,
        end_date: str,
        collections: List[str],
        max_cloud_cover: float
    ) -> Dict:
        """Get data from Planetary Computer."""
        if isinstance(bbox, tuple):
            bbox_poly = box(*bbox)
        else:
            bbox_poly = bbox
        
        search_params = {
            "collections": collections,
            "intersects": bbox_poly.__geo_interface__,
            "datetime": f"{start_date}/{end_date}",
            "query": {
                "eo:cloud_cover": {"lt": max_cloud_cover}
            }
        }
        
        try:
            items = client.search(**search_params).get_all_items()
            
            if not items:
                return {}
            
            results = {}
            for collection in collections:
                collection_items = [
                    item for item in items
                    if item.collection_id == collection
                ]
                
                if collection_items:
                    results[collection] = self._process_items(
                        collection_items,
                        bbox_poly
                    )
            
            return results
            
        except Exception as e:
            logger.error(f"Planetary Computer search failed: {e}")
            return {}
    
    def _get_from_wms(
        self,
        services: Dict,
        bbox: Union[Tuple[float, float, float, float], Polygon],
        resolution: float
    ) -> Dict:
        """Get data from WMS services."""
        if isinstance(bbox, Polygon):
            bbox = bbox.bounds
        
        results = {}
        for name, service in services.items():
            try:
                layers = list(service.contents)
                if not layers:
                    continue
                
                # Get first available layer
                layer = layers[0]
                
                # Calculate image size based on resolution
                width = int((bbox[2] - bbox[0]) / resolution)
                height = int((bbox[3] - bbox[1]) / resolution)
                
                img = service.getmap(
                    layers=[layer],
                    srs='EPSG:4326',
                    bbox=bbox,
                    size=(width, height),
                    format='image/tiff',
                    transparent=True
                )
                
                results[name] = {
                    "data": img.read(),
                    "metadata": {
                        "service": name,
                        "layer": layer,
                        "resolution": resolution,
                        "bbox": bbox
                    }
                }
                
            except Exception as e:
                logger.error(f"WMS {name} request failed: {e}")
        
        return results
    
    def _get_from_cog_stac(
        self,
        client: COGSTACAPI,
        bbox: Union[Tuple[float, float, float, float], Polygon],
        start_date: str,
        end_date: str,
        collections: List[str],
        resolution: float
    ) -> Dict:
        """Get data from COG/STAC source."""
        try:
            # Search for collections
            available_collections = client.search_collections(
                bbox=bbox,
                start_date=start_date,
                end_date=end_date
            )
            
            results = {}
            for collection in available_collections:
                if collection["id"] in collections:
                    # Get assets with COG URLs
                    assets = self._get_collection_assets(
                        client,
                        collection,
                        bbox,
                        start_date,
                        end_date
                    )
                    
                    if assets:
                        collection_data = {}
                        for asset_name, asset_url in assets.items():
                            try:
                                data = client.get_cog_data(
                                    url=asset_url,
                                    bbox=bbox,
                                    resolution=resolution
                                )
                                collection_data[asset_name] = data
                            except Exception as e:
                                logger.error(
                                    f"Error getting COG data for {asset_name}: {e}"
                                )
                        
                        if collection_data:
                            results[collection["id"]] = collection_data
            
            return results
            
        except Exception as e:
            logger.error(f"Error in COG/STAC source: {e}")
            return {}
    
    def _get_collection_assets(
        self,
        client: COGSTACAPI,
        collection: Dict,
        bbox: Union[Tuple[float, float, float, float], Polygon],
        start_date: str,
        end_date: str
    ) -> Dict[str, str]:
        """Get COG assets from a collection."""
        try:
            # Search for items in collection
            items = client.search_collections(
                bbox=bbox,
                start_date=start_date,
                end_date=end_date,
                query={"collections": [collection["id"]]}
            )
            
            if not items:
                return {}
            
            # Get first item's assets
            item = items[0]
            assets = {}
            
            # Filter for COG assets
            for asset_name, asset in item.get("assets", {}).items():
                if (
                    asset.get("type") == "image/tiff; application=geotiff; profile=cloud-optimized"
                    or asset.get("roles", []).count("cloud-optimized")
                ):
                    assets[asset_name] = asset["href"]
            
            return assets
            
        except Exception as e:
            logger.error(f"Error getting collection assets: {e}")
            return {}
    
    def _convert_formats(self, data: Dict, formats: List[str]) -> Dict:
        """Convert data to requested formats."""
        converted = {}
        
        for format in formats:
            if format == "geoparquet":
                converted[format] = self._convert_to_geoparquet(data)
            elif format == "geojson":
                converted[format] = self._convert_to_geojson(data)
        
        return converted
    
    def _convert_to_geoparquet(self, data: Dict) -> Dict:
        """Convert data to GeoParquet format."""
        results = {}
        
        for source, source_data in data.items():
            if isinstance(source_data, gpd.GeoDataFrame):
                # Save to GeoParquet
                output_path = self.cache_dir / f"{source}.parquet"
                source_data.to_parquet(output_path)
                results[source] = str(output_path)
            elif isinstance(source_data, Dict):
                # Recursively convert nested dictionaries
                results[source] = self._convert_to_geoparquet(source_data)
        
        return results
    
    def _convert_to_geojson(self, data: Dict) -> Dict:
        """Convert data to GeoJSON format."""
        results = {}
        
        for source, source_data in data.items():
            if isinstance(source_data, gpd.GeoDataFrame):
                # Save to GeoJSON
                output_path = self.cache_dir / f"{source}.geojson"
                source_data.to_file(output_path, driver="GeoJSON")
                results[source] = str(output_path)
            elif isinstance(source_data, Dict):
                # Recursively convert nested dictionaries
                results[source] = self._convert_to_geojson(source_data)
        
        return results
    
    def get_source_metrics(self, source_name: str) -> Optional[DataSourceMetrics]:
        """Get metrics for a data source."""
        if source_name in self.data_sources:
            return self.data_sources[source_name]["metrics"]
        return None
    
    def get_available_sources(self) -> List[Dict]:
        """Get list of available data sources with their metrics."""
        return [
            {
                "name": name,
                "metrics": {
                    "speed": info["metrics"].speed.name,
                    "cost": info["metrics"].cost.name,
                    "reliability": info["metrics"].reliability.name,
                    "requires_auth": info["metrics"].requires_auth,
                    "supports_streaming": info["metrics"].supports_streaming,
                    "supports_async": info["metrics"].supports_async
                },
                "status": "active" if info["client"] else "inactive"
            }
            for name, info in self.data_sources.items()
        ]
    
    def __del__(self):
        """Cleanup on deletion."""
        try:
            self.db.close()
        except:
            pass 