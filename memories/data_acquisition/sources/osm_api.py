"""
OpenStreetMap data source for vector data.
"""

import os
from typing import Dict, List, Optional, Tuple, Union
from pathlib import Path
import osmnx as ox
import geopandas as gpd
from shapely.geometry import box, Polygon
import json

class OSMDataAPI:
    """Interface for accessing data from OpenStreetMap."""
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize OSM data client.
        
        Args:
            cache_dir: Directory for caching downloaded data
        """
        self.cache_dir = Path(cache_dir) if cache_dir else Path.home() / ".osm_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure OSMnx
        ox.config(
            cache_folder=str(self.cache_dir),
            use_cache=True,
            log_console=False
        )
        
        # Define available layers and their OSM tags
        self.layers = {
            "buildings": {
                "tags": {"building": True},
                "geometry_type": "polygon"
            },
            "roads": {
                "tags": {"highway": True},
                "geometry_type": "line"
            },
            "landuse": {
                "tags": {"landuse": True},
                "geometry_type": "polygon"
            },
            "water": {
                "tags": {"water": True, "waterway": True},
                "geometry_type": "polygon"
            },
            "natural": {
                "tags": {"natural": True},
                "geometry_type": "polygon"
            }
        }
    
    def get_features(
        self,
        bbox: Union[Tuple[float, float, float, float], Polygon],
        layers: List[str] = ["buildings", "roads"]
    ) -> Dict:
        """
        Get vector features from OpenStreetMap.
        
        Args:
            bbox: Bounding box or Polygon
            layers: List of layers to fetch
            
        Returns:
            Dictionary containing vector data by layer
        """
        # Convert bbox to coordinates
        if isinstance(bbox, tuple):
            north, south = bbox[3], bbox[1]
            east, west = bbox[2], bbox[0]
        else:
            north, south = bbox.bounds[3], bbox.bounds[1]
            east, west = bbox.bounds[2], bbox.bounds[0]
        
        results = {}
        
        for layer in layers:
            if layer not in self.layers:
                print(f"Warning: Layer {layer} not available")
                continue
            
            layer_info = self.layers[layer]
            
            try:
                # Download data using OSMnx
                if layer_info["geometry_type"] == "polygon":
                    gdf = ox.geometries_from_bbox(
                        north, south, east, west,
                        tags=layer_info["tags"]
                    )
                elif layer_info["geometry_type"] == "line":
                    if layer == "roads":
                        gdf = ox.graph_from_bbox(
                            north, south, east, west,
                            network_type="all"
                        )
                        gdf = ox.graph_to_gdfs(gdf, nodes=False)
                    else:
                        gdf = ox.geometries_from_bbox(
                            north, south, east, west,
                            tags=layer_info["tags"]
                        )
                
                # Clean and process the data
                if not gdf.empty:
                    # Reproject to WGS84
                    if gdf.crs != "EPSG:4326":
                        gdf = gdf.to_crs("EPSG:4326")
                    
                    # Clean columns
                    gdf = self._clean_attributes(gdf, layer)
                    
                    results[layer] = gdf
                
            except Exception as e:
                print(f"Error fetching {layer} data: {e}")
        
        return results
    
    def _clean_attributes(self, gdf: gpd.GeoDataFrame, layer: str) -> gpd.GeoDataFrame:
        """Clean and standardize attributes for a layer."""
        if layer == "buildings":
            keep_cols = [
                "geometry", "building", "height", "levels",
                "building:levels", "name", "amenity"
            ]
        elif layer == "roads":
            keep_cols = [
                "geometry", "highway", "name", "surface",
                "lanes", "oneway", "maxspeed"
            ]
        elif layer == "landuse":
            keep_cols = [
                "geometry", "landuse", "name", "amenity"
            ]
        else:
            # Keep all columns for other layers
            return gdf
        
        # Keep only specified columns if they exist
        cols = [col for col in keep_cols if col in gdf.columns]
        return gdf[cols]
    
    def get_place_boundary(self, place_name: str) -> Optional[Polygon]:
        """Get the boundary polygon for a place."""
        try:
            gdf = ox.geocode_to_gdf(place_name)
            if not gdf.empty:
                return gdf.iloc[0].geometry
        except Exception as e:
            print(f"Error getting boundary for {place_name}: {e}")
        return None
    
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
    
    def get_available_layers(self) -> List[str]:
        """Get list of available layers."""
        return list(self.layers.keys())
    
    def get_layer_tags(self, layer: str) -> Dict:
        """Get OSM tags for a layer."""
        if layer not in self.layers:
            raise ValueError(f"Layer {layer} not available")
        return self.layers[layer]["tags"] 