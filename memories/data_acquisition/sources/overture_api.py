"""
Overture Maps API data source for vector data.
"""

import os
from typing import Dict, List, Optional, Tuple, Union, Any
from pathlib import Path
import aiohttp
import geopandas as gpd
from shapely.geometry import box, Polygon, mapping
import json
import logging
from .base import DataSource

class OvertureAPI(DataSource):
    """Interface for accessing data from Overture Maps."""
    
    def __init__(self, api_key: Optional[str] = None, cache_dir: Optional[str] = None):
        """
        Initialize Overture Maps interface.
        
        Args:
            api_key: Optional API key for authentication
            cache_dir: Optional directory for caching data
        """
        super().__init__(cache_dir)
        self.api_key = api_key or os.getenv("OVERTURE_API_KEY")
        self.base_url = "https://api.overturemaps.org/v1"
        self.logger = logging.getLogger(__name__)
        
        # Define available layers and their properties
        self.layers = {
            "buildings": {
                "endpoint": "/buildings",
                "properties": ["height", "levels", "class", "type"]
            },
            "roads": {
                "endpoint": "/transportation",
                "properties": ["class", "type", "surface"]
            },
            "places": {
                "endpoint": "/places",
                "properties": ["class", "type", "name"]
            },
            "admins": {
                "endpoint": "/admins",
                "properties": ["class", "type", "name"]
            }
        }
    
    def _bbox_to_geojson(self, bbox: Union[Tuple[float, float, float, float], List[float], Polygon]) -> Dict[str, Any]:
        """
        Convert bounding box to GeoJSON format.
        
        Args:
            bbox: List of coordinates [west, south, east, north] or Polygon
            
        Returns:
            Dict containing GeoJSON polygon
        """
        if isinstance(bbox, Polygon):
            return mapping(bbox)
        elif isinstance(bbox, (tuple, list)) and len(bbox) == 4:
            west, south, east, north = bbox
            polygon = box(west, south, east, north)
            return mapping(polygon)
        else:
            raise ValueError("Invalid bbox format. Must be [west, south, east, north] or Polygon")
    
    async def search(self,
                    bbox: Union[Tuple[float, float, float, float], List[float], Polygon],
                    layer: str = "buildings",
                    limit: int = 1000) -> Dict[str, Any]:
        """
        Search for vector features.
        
        Args:
            bbox: Bounding box coordinates [west, south, east, north] or Polygon
            layer: Data layer to query (buildings, roads, places, etc.)
            limit: Maximum number of features to return
            
        Returns:
            GeoJSON FeatureCollection
        """
        valid_layers = ["buildings", "roads", "places", "admins"]
        if layer not in valid_layers:
            raise ValueError(f"Invalid layer. Must be one of: {valid_layers}")
        
        headers = {
            "Content-Type": "application/json"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        # Convert bbox to Overture Maps API format
        if isinstance(bbox, Polygon):
            minx, miny, maxx, maxy = bbox.bounds
        else:
            minx, miny, maxx, maxy = bbox
        
        params = {
            "bbox": f"{minx},{miny},{maxx},{maxy}",
            "limit": limit
        }
        
        async with aiohttp.ClientSession() as session:
            response = await session.get(
                f"{self.base_url}/{layer}",
                headers=headers,
                params=params
            )
            await response.raise_for_status()
            data = await response.json()
            if 'features' in data:
                self.logger.info(f"Found {len(data['features'])} features in {layer} layer")
            return data
    
    async def download(self,
                      bbox: Union[Tuple[float, float, float, float], List[float], Polygon],
                      layer: str,
                      output_dir: Path,
                      format: str = "geojson") -> Path:
        """
        Download and save vector data.
        
        Args:
            bbox: Bounding box coordinates or Polygon
            layer: Layer to download
            output_dir: Directory to save output
            format: Output format (geojson or gpkg)
            
        Returns:
            Path to downloaded file
        """
        if format not in ["geojson", "gpkg"]:
            raise ValueError("Format must be 'geojson' or 'gpkg'")
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Get features
        data = await self.search(bbox, layer)
        
        # Create output filename
        output_path = output_dir / f"overture_{layer}.{format}"
        
        # Check cache
        cache_path = self.get_cache_path(f"overture_{layer}.{format}")
        if cache_path and cache_path.exists():
            self.logger.info(f"Using cached file: {cache_path}")
            return cache_path
        
        if format == "geojson":
            with open(output_path, 'w') as f:
                json.dump(data, f)
        else:  # gpkg
            gdf = gpd.GeoDataFrame.from_features(data['features'])
            gdf.to_file(output_path, driver="GPKG")
        
        # Cache the result if caching is enabled
        if cache_path:
            output_path.rename(cache_path)
            output_path = cache_path
        
        self.logger.info(f"Saved {layer} data to {output_path}")
        return output_path
    
    def get_metadata(self, layer: str) -> Dict[str, Any]:
        """
        Get metadata about a data layer.
        
        Args:
            layer: Data layer name
            
        Returns:
            Dictionary containing layer metadata
        """
        if layer not in self.layers:
            raise ValueError(f"Layer {layer} not available")
        
        return {
            "name": layer,
            "endpoint": self.layers[layer]["endpoint"],
            "properties": self.layers[layer]["properties"],
            "source": "Overture Maps",
            "license": "ODbL",
            "description": f"Overture Maps {layer} features"
        }
    
    def get_available_layers(self) -> List[str]:
        """Get list of available layers."""
        return list(self.layers.keys())
    
    def get_layer_properties(self, layer: str) -> List[str]:
        """Get available properties for a layer."""
        if layer not in self.layers:
            raise ValueError(f"Layer {layer} not available")
        return self.layers[layer]["properties"]
    
    def get_features(
        self,
        bbox: Union[Tuple[float, float, float, float], Polygon],
        layers: List[str] = ["buildings", "roads"]
    ) -> Dict:
        """
        Get vector features from Overture Maps.
        
        Args:
            bbox: Bounding box or Polygon
            layers: List of layers to fetch
            
        Returns:
            Dictionary containing vector data by layer
        """
        # Convert bbox to coordinates
        if isinstance(bbox, tuple):
            minx, miny, maxx, maxy = bbox
        else:
            minx, miny, maxx, maxy = bbox.bounds
        
        results = {}
        
        for layer in layers:
            if layer not in self.layers:
                print(f"Warning: Layer {layer} not available")
                continue
            
            layer_info = self.layers[layer]
            
            # Build query
            params = {
                "bbox": f"{minx},{miny},{maxx},{maxy}",
                "properties": ",".join(layer_info["properties"]),
                "format": "geojson"
            }
            
            if self.api_key:
                params["key"] = self.api_key
            
            # Make request
            try:
                response = requests.get(
                    f"{self.base_url}{layer_info['endpoint']}",
                    params=params
                )
                response.raise_for_status()
                
                # Convert to GeoDataFrame
                gdf = gpd.GeoDataFrame.from_features(
                    response.json()["features"]
                )
                
                if not gdf.empty:
                    results[layer] = gdf
                
            except Exception as e:
                print(f"Error fetching {layer} data: {e}")
        
        return results
    
    def get_layer_schema(self, layer: str) -> Dict:
        """Get schema information for a layer."""
        if layer not in self.layers:
            raise ValueError(f"Layer {layer} not available")
        
        try:
            response = requests.get(
                f"{self.base_url}{self.layers[layer]['endpoint']}/schema",
                params={"key": self.api_key} if self.api_key else None
            )
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            print(f"Error fetching schema for {layer}: {e}")
            return {}
    
    def validate_bbox(self, bbox: Union[Tuple[float, float, float, float], Polygon]) -> bool:
        """Validate if bbox is within allowed limits."""
        if isinstance(bbox, tuple):
            minx, miny, maxx, maxy = bbox
        else:
            minx, miny, maxx, maxy = bbox.bounds
        
        # Check coordinate ranges
        if not (-180 <= minx <= 180 and -180 <= maxx <= 180):
            return False
        if not (-90 <= miny <= 90 and -90 <= maxy <= 90):
            return False
        
        # Check area size (prevent too large requests)
        if (maxx - minx) * (maxy - miny) > 1.0:  # ~12,000 km² at equator
            return False
        
        return True
    
    def download_to_file(
        self,
        bbox: Union[Tuple[float, float, float, float], Polygon],
        layers: List[str],
        output_dir: str
    ) -> Dict[str, Path]:
        """
        Download vector data to GeoJSON files.
        
        Args:
            bbox: Bounding box or Polygon
            layers: List of layers to fetch
            output_dir: Directory to save files
            
        Returns:
            Dictionary mapping layer names to file paths
        """
        results = self.get_features(bbox, layers)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        file_paths = {}
        for layer, gdf in results.items():
            if not gdf.empty:
                file_path = output_dir / f"{layer}.geojson"
                gdf.to_file(file_path, driver="GeoJSON")
                file_paths[layer] = file_path
        
        return file_paths 