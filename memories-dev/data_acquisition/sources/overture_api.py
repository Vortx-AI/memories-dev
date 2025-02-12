"""
Overture Maps API data source for vector data.
"""

import os
from typing import Dict, List, Optional, Tuple, Union
from pathlib import Path
import requests
import geopandas as gpd
from shapely.geometry import box, Polygon, mapping
import json

class OvertureAPI:
    """Interface for accessing data from Overture Maps."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://overture-maps.org/api/v1"
    ):
        """
        Initialize Overture Maps client.
        
        Args:
            api_key: Overture Maps API key
            base_url: API endpoint URL
        """
        self.api_key = api_key or os.getenv("OVERTURE_API_KEY")
        self.base_url = base_url
        
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
            "landuse": {
                "endpoint": "/places",
                "properties": ["class", "type"]
            },
            "places": {
                "endpoint": "/places",
                "properties": ["class", "type", "name"]
            }
        }
    
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
    
    def get_available_layers(self) -> List[str]:
        """Get list of available layers."""
        return list(self.layers.keys())
    
    def get_layer_properties(self, layer: str) -> List[str]:
        """Get available properties for a layer."""
        if layer not in self.layers:
            raise ValueError(f"Layer {layer} not available")
        return self.layers[layer]["properties"]
    
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