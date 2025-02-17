"""
OpenStreetMap data source for vector data.
"""

import os
from typing import Dict, List, Optional, Tuple, Union, Any
from pathlib import Path
import aiohttp
import geopandas as gpd
from shapely.geometry import box, Polygon, mapping
import json
import logging
import osmium
from .base import DataSource

class OSMHandler(osmium.SimpleHandler):
    """Custom handler for processing OSM data."""
    
    def __init__(self, tags: List[str]):
        super().__init__()
        self.tags = tags
        self.features = {
            'buildings': [],
            'highways': [],
            'landuse': [],
            'waterways': [],
            'other': []
        }
    
    def way(self, w):
        """Process OSM way elements."""
        tags = dict(w.tags)
        coords = [(n.lon, n.lat) for n in w.nodes]
        
        if 'building' in tags:
            self.features['buildings'].append({
                'type': 'Feature',
                'geometry': {
                    'type': 'Polygon',
                    'coordinates': [coords]
                },
                'properties': tags
            })
        elif 'highway' in tags:
            self.features['highways'].append({
                'type': 'Feature',
                'geometry': {
                    'type': 'LineString',
                    'coordinates': coords
                },
                'properties': tags
            })
        elif 'landuse' in tags:
            self.features['landuse'].append({
                'type': 'Feature',
                'geometry': {
                    'type': 'Polygon',
                    'coordinates': [coords]
                },
                'properties': tags
            })
        elif 'waterway' in tags:
            self.features['waterways'].append({
                'type': 'Feature',
                'geometry': {
                    'type': 'LineString',
                    'coordinates': coords
                },
                'properties': tags
            })
        else:
            for tag in self.tags:
                if tag in tags:
                    self.features['other'].append({
                        'type': 'Feature',
                        'geometry': {
                            'type': 'Polygon' if w.is_closed() else 'LineString',
                            'coordinates': [coords] if w.is_closed() else coords
                        },
                        'properties': tags
                    })
                    break

class OSMDataAPI(DataSource):
    """Interface for accessing data from OpenStreetMap."""
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize OSM data client.
        
        Args:
            cache_dir: Directory for caching downloaded data
        """
        super().__init__(cache_dir)
        self.base_url = "https://overpass-api.de/api/interpreter"
        self.logger = logging.getLogger(__name__)
        
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
    
    def _build_query(self, bbox: Union[Tuple[float, float, float, float], List[float], Polygon], tag: str) -> str:
        """
        Build Overpass QL query.
        
        Args:
            bbox: Bounding box coordinates [west, south, east, north] or Polygon
            tag: OSM tag to query
            
        Returns:
            str: Overpass QL query
        """
        if isinstance(bbox, Polygon):
            west, south, east, north = bbox.bounds
        elif isinstance(bbox, (tuple, list)) and len(bbox) == 4:
            west, south, east, north = bbox
        else:
            raise ValueError("Invalid bbox format. Must be [west, south, east, north] or Polygon")
        
        # Handle special cases for common tags
        if tag == "building":
            tag_filter = '[building]'
        elif tag == "highway":
            tag_filter = '[highway]'
        elif tag == "landuse":
            tag_filter = '[landuse]'
        else:
            tag_filter = f'["{tag}"]'
        
        return f"""
            [out:json][timeout:25];
            (
                way{tag_filter}({south},{west},{north},{east});
                >;
            );
            out body;
        """
    
    async def search(self,
                    bbox: Union[Tuple[float, float, float, float], List[float], Polygon],
                    tags: List[str] = ["building", "highway"],
                    timeout: int = 25) -> Dict[str, Any]:
        """
        Search for OSM features.
        
        Args:
            bbox: Bounding box coordinates [west, south, east, north] or Polygon
            tags: OSM tags to search for
            timeout: Query timeout in seconds
            
        Returns:
            Dictionary containing features by category
        """
        if not tags:
            return {}
            
        query = self._build_query(bbox, tags[0])  # Use first tag for now
        
        async with aiohttp.ClientSession() as session:
            response = await session.post(
                self.base_url,
                data={"data": query},
                timeout=timeout
            )
            await response.raise_for_status()
            content = await response.read()
            
            # Process OSM data
            handler = OSMHandler(tags)
            handler.apply_buffer(content)  # Remove "osm" parameter as it's not needed
            
            # Initialize empty result with all possible categories
            result = {
                'buildings': [],
                'highways': [],
                'landuse': [],
                'waterways': [],
                'other': []
            }
            
            # Update with actual features
            for category, features in handler.features.items():
                if features:  # Only include non-empty feature lists
                    result[category] = features
            
            feature_counts = {k: len(v) for k, v in result.items() if v}
            self.logger.info(f"Found features: {', '.join(f'{k}: {count}' for k, count in feature_counts.items())}")
            return result
    
    async def download(self,
                      bbox: Union[Tuple[float, float, float, float], List[float], Polygon],
                      tags: List[str],
                      output_dir: Path,
                      format: str = "geojson") -> Dict[str, Path]:
        """
        Download and save OSM data.
        
        Args:
            bbox: Bounding box coordinates or Polygon
            tags: OSM tags to download
            output_dir: Directory to save output
            format: Output format (geojson or gpkg)
            
        Returns:
            Dictionary mapping feature types to file paths
        """
        if format not in ["geojson", "gpkg"]:
            raise ValueError("Format must be 'geojson' or 'gpkg'")
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Get features
        features = await self.search(bbox, tags)
        
        # Save each feature type to a separate file
        output_files = {}
        for feature_type, feature_list in features.items():
            if not feature_list:
                continue
                
            # Check cache
            cache_path = self.get_cache_path(f"osm_{feature_type}.{format}")
            if cache_path and cache_path.exists():
                self.logger.info(f"Using cached file: {cache_path}")
                output_files[feature_type] = cache_path
                continue
                
            output_path = output_dir / f"osm_{feature_type}.{format}"
            
            if format == "geojson":
                feature_collection = {
                    "type": "FeatureCollection",
                    "features": feature_list
                }
                with open(output_path, 'w') as f:
                    json.dump(feature_collection, f)
            else:  # gpkg
                gdf = gpd.GeoDataFrame.from_features(feature_list)
                gdf.to_file(output_path, driver="GPKG")
            
            # Cache the result if caching is enabled
            if cache_path:
                output_path.rename(cache_path)
                output_path = cache_path
            
            output_files[feature_type] = output_path
            self.logger.info(f"Saved {feature_type} data to {output_path}")
        
        return output_files
    
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
            "tags": self.layers[layer]["tags"],
            "geometry_type": self.layers[layer]["geometry_type"],
            "source": "OpenStreetMap",
            "license": "ODbL",
            "description": f"OpenStreetMap {layer} features"
        }
    
    def get_available_layers(self) -> List[str]:
        """Get list of available layers."""
        return list(self.layers.keys())
    
    def get_layer_tags(self, layer: str) -> Dict:
        """Get OSM tags for a layer."""
        if layer not in self.layers:
            raise ValueError(f"Layer {layer} not available")
        return self.layers[layer]["tags"]
    
    async def get_features(
        self,
        bbox: Union[Tuple[float, float, float, float], List[float], Polygon],
        layers: List[str] = ["buildings", "roads"]
    ) -> Dict[str, Any]:
        """
        Get vector features from OpenStreetMap.
        
        Args:
            bbox: Bounding box or Polygon
            layers: List of layers to fetch
            
        Returns:
            Dictionary containing vector data by layer
        """
        results = {}
        
        for layer in layers:
            if layer not in self.layers:
                print(f"Warning: Layer {layer} not available")
                continue
            
            # Build query
            query = self._build_query(bbox, layer)
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self.base_url,
                        data={"data": query},
                        timeout=25
                    ) as response:
                        response.raise_for_status()
                        data = await response.json()
                        
                        # Convert to GeoDataFrame
                        features = []
                        for element in data.get("elements", []):
                            if element.get("type") == "way":
                                tags = element.get("tags", {})
                                nodes = element.get("nodes", [])
                                if nodes:
                                    # Get node coordinates
                                    coords = []
                                    for node_id in nodes:
                                        node = next((n for n in data["elements"] if n["type"] == "node" and n["id"] == node_id), None)
                                        if node:
                                            coords.append([node["lon"], node["lat"]])
                                    
                                    if coords:
                                        geometry_type = "Polygon" if nodes[0] == nodes[-1] else "LineString"
                                        features.append({
                                            "type": "Feature",
                                            "geometry": {
                                                "type": geometry_type,
                                                "coordinates": [coords] if geometry_type == "Polygon" else coords
                                            },
                                            "properties": tags
                                        })
                        
                        if features:
                            gdf = gpd.GeoDataFrame.from_features(features)
                            if not gdf.empty:
                                results[layer] = gdf
                
            except Exception as e:
                print(f"Error fetching {layer} data: {e}")
        
        return results
    
    async def get_place_boundary(self, place_name: str) -> Optional[Polygon]:
        """Get the boundary polygon for a place."""
        query = f"""
            [out:json][timeout:25];
            area[name="{place_name}"]->.searchArea;
            (
                way(area.searchArea)[boundary=administrative];
                relation(area.searchArea)[boundary=administrative];
            );
            out body;
            >;
            out skel qt;
        """
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.base_url,
                    data={"data": query},
                    timeout=25
                ) as response:
                    response.raise_for_status()
                    data = await response.json()
                    
                    # Process boundary data
                    features = []
                    for element in data.get("elements", []):
                        if element.get("type") == "way":
                            nodes = element.get("nodes", [])
                            if nodes:
                                coords = []
                                for node_id in nodes:
                                    node = next((n for n in data["elements"] if n["type"] == "node" and n["id"] == node_id), None)
                                    if node:
                                        coords.append([node["lon"], node["lat"]])
                                
                                if coords and coords[0] == coords[-1]:
                                    return Polygon(coords)
            
        except Exception as e:
            print(f"Error getting boundary for {place_name}: {e}")
        
        return None
    
    async def download_to_file(
        self,
        bbox: Union[Tuple[float, float, float, float], List[float], Polygon],
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
        results = await self.get_features(bbox, layers)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        file_paths = {}
        for layer, gdf in results.items():
            if not gdf.empty:
                file_path = output_dir / f"{layer}.geojson"
                gdf.to_file(file_path, driver="GeoJSON")
                file_paths[layer] = file_path
        
        return file_paths 