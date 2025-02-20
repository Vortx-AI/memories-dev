"""
OpenStreetMap data source for vector data using Overpass API.
"""

import os
from typing import Dict, List, Optional, Tuple, Union, Any
from pathlib import Path
import aiohttp
import requests
import geopandas as gpd
from shapely.geometry import box, Polygon, mapping
import json
import logging
from .base import DataSource


class OSMDataAPI(DataSource):
    """Interface for accessing data from OpenStreetMap using Overpass API."""

    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize OpenStreetMap interface.

        Args:
            cache_dir: Optional directory for caching data
        """
        super().__init__(cache_dir)
        self.base_url = "https://overpass-api.de/api/interpreter"
        self.logger = logging.getLogger(__name__)

        # Define available feature types and their tags
        self.feature_types = {
            'buildings': ['building'],
            'highways': ['highway'],
            'landuse': ['landuse'],
            'waterways': ['waterway', 'water', 'natural=water'],
            'other': []
        }

    def _build_query(
        self,
        bbox: Union[Tuple[float, float, float, float], List[float], Polygon],
        tag: str
    ) -> str:
        """
        Build Overpass QL query.

        Args:
            bbox: Bounding box coordinates [west, south, east, north] or Polygon
            tag: OSM tag to query

        Returns:
            Overpass QL query string
        """
        if isinstance(bbox, Polygon):
            minx, miny, maxx, maxy = bbox.bounds
        else:
            minx, miny, maxx, maxy = bbox

        # Handle different tag formats
        if '=' in tag:
            key, value = tag.split('=')
            tag_filter = f'["{key}"="{value}"]'
        else:
            tag_filter = f'["{tag}"]'

        return f"""
            [out:json][timeout:25];
            (
                way{tag_filter}({miny},{minx},{maxy},{maxx});
                relation{tag_filter}({miny},{minx},{maxy},{maxx});
            );
            out body;
            >;
            out skel qt;
        """

    async def search(
        self,
        bbox: Union[Tuple[float, float, float, float], List[float], Polygon],
        tags: List[str] = ["building", "highway"],
        timeout: int = 25
    ) -> Dict[str, Any]:
        """
        Search for OSM features.

        Args:
            bbox: Bounding box coordinates [west, south, east, north] or Polygon
            tags: List of OSM tags to query
            timeout: Query timeout in seconds

        Returns:
            Dictionary containing features by type
        """
        results = {'features': []}

        for tag in tags:
            query = self._build_query(bbox, tag)
            
            try:
                async with aiohttp.ClientSession() as session:
                    response = await session.post(
                        self.base_url,
                        data={'data': query},
                        timeout=timeout
                    )
                    async with response:
                        if response.status == 200:
                            data = await response.json()
                            if 'elements' in data:
                                # First, collect all nodes
                                nodes = {}
                                for element in data['elements']:
                                    if element['type'] == 'node':
                                        nodes[element['id']] = element
                                
                                # Then process ways and relations
                                for element in data['elements']:
                                    if element['type'] in ['way', 'relation']:
                                        try:
                                            # Get coordinates for each node reference
                                            coordinates = []
                                            for node_id in element.get('nodes', []):
                                                if node_id in nodes:
                                                    node = nodes[node_id]
                                                    coordinates.append([node['lon'], node['lat']])
                                            
                                            if coordinates:
                                                # Close the polygon if needed
                                                if coordinates[0] != coordinates[-1]:
                                                    coordinates.append(coordinates[0])
                                                
                                                feature = {
                                                    'type': 'Feature',
                                                    'geometry': {
                                                        'type': 'Polygon',
                                                        'coordinates': [coordinates]
                                                    },
                                                    'properties': element.get('tags', {})
                                                }
                                                results['features'].append(feature)
                                        except Exception as e:
                                            self.logger.warning(f"Error processing element: {str(e)}")
            except Exception as e:
                self.logger.error(f"Error querying OSM data: {str(e)}")

        return results

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
        if layer not in self.feature_types:
            raise ValueError(f"Layer {layer} not available")
        
        return {
            "name": layer,
            "tags": self.feature_types[layer],
            "geometry_type": "polygon",
            "source": "OpenStreetMap",
            "license": "ODbL",
            "description": f"OpenStreetMap {layer} features"
        }
    
    def get_available_layers(self) -> List[str]:
        """Get list of available layers."""
        return list(self.feature_types.keys())
    
    def get_layer_tags(self, layer: str) -> Dict:
        """Get OSM tags for a layer."""
        if layer not in self.feature_types:
            raise ValueError(f"Layer {layer} not available")
        return self.feature_types[layer]
    
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
            if layer not in self.feature_types:
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
            (
                way[name="{place_name}"][boundary=administrative];
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
                    
                    # First collect all nodes
                    nodes = {}
                    for element in data.get("elements", []):
                        if element["type"] == "node":
                            nodes[element["id"]] = element
                    
                    # Then find administrative boundary ways
                    for element in data.get("elements", []):
                        if (element.get("type") == "way" and 
                            element.get("tags", {}).get("boundary") == "administrative"):
                            node_refs = element.get("nodes", [])
                            if node_refs:
                                coords = []
                                for node_id in node_refs:
                                    if node_id in nodes:
                                        node = nodes[node_id]
                                        coords.append([node["lon"], node["lat"]])
                                
                                if coords and coords[0] != coords[-1]:
                                    coords.append(coords[0])  # Close the polygon
                                
                                if len(coords) >= 4:  # Need at least 4 points for a valid polygon
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