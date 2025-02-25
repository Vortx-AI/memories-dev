"""
Web Feature Service (WFS) data source for vector data.
"""

import os
from typing import Dict, List, Optional, Tuple, Union
from pathlib import Path
import logging
from shapely.geometry import box, Polygon
import geopandas as gpd
from owslib.wfs import WebFeatureService
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WFSAPI:
    """Interface for accessing data from WFS services."""
    
    def __init__(
        self,
        cache_dir: Optional[str] = None,
        timeout: int = 30
    ):
        """
        Initialize WFS client.
        
        Args:
            cache_dir: Directory for caching data
            timeout: Timeout for WFS requests in seconds
        """
        self.cache_dir = Path(cache_dir) if cache_dir else Path.home() / ".wfs_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
        
        # Define available WFS endpoints
        self.endpoints = {
            "usgs": {
                "url": "https://ows.nationalmap.gov/services/wfs",
                "version": "2.0.0"
            },
            "geoserver_demo": {
                "url": "https://ahocevar.com/geoserver/wfs",  # Demo GeoServer
                "version": "2.0.0"
            },
            "nasa_gibs": {
                "url": "https://gibs.earthdata.nasa.gov/wfs/epsg4326",
                "version": "2.0.0"
            },
            "fao": {
                "url": "https://data.apps.fao.org/map/gsrv/wfs",
                "version": "2.0.0"
            }
        }
        
        # Initialize WFS clients
        self.services = self._init_services()
    
    def _init_services(self) -> Dict:
        """Initialize WFS service connections."""
        services = {}
        for name, config in self.endpoints.items():
            try:
                services[name] = WebFeatureService(
                    url=config["url"],
                    version=config["version"],
                    timeout=self.timeout
                )
                logger.info(f"Successfully initialized WFS service: {name}")
            except Exception as e:
                logger.error(f"Failed to initialize WFS service {name}: {e}")
        return services
    
    def get_features(
        self,
        bbox: Union[Tuple[float, float, float, float], Polygon],
        layers: List[str],
        service_name: Optional[str] = None,
        max_features: int = 1000,
        output_format: str = "GeoJSON"
    ) -> Dict:
        """
        Get vector features from WFS services.
        
        Args:
            bbox: Bounding box or Polygon
            layers: List of layers to fetch
            service_name: Optional specific service to use
            max_features: Maximum number of features to return
            output_format: Output format (GeoJSON, GML, etc.)
            
        Returns:
            Dictionary containing vector data by layer
        """
        # Convert bbox to coordinates
        if isinstance(bbox, Polygon):
            bbox = bbox.bounds
        
        results = {}
        services_to_try = (
            {service_name: self.services[service_name]}
            if service_name and service_name in self.services
            else self.services
        )
        
        for name, service in services_to_try.items():
            try:
                # Get available layers
                available_layers = list(service.contents)
                logger.info(f"Available layers in {name}: {available_layers}")
                
                # Filter requested layers
                layers_to_fetch = [
                    layer for layer in layers
                    if layer in available_layers
                ]
                
                if not layers_to_fetch:
                    logger.warning(f"No requested layers available in {name}")
                    continue
                
                service_results = {}
                for layer in layers_to_fetch:
                    try:
                        # Get layer info
                        layer_info = service.contents[layer]
                        
                        # Check if bbox is within layer bounds
                        if not self._is_bbox_valid(bbox, layer_info.boundingBoxWGS84):
                            logger.warning(
                                f"Bbox {bbox} outside layer bounds for {layer}"
                            )
                            continue
                        
                        # Request features
                        response = service.getfeature(
                            typename=layer,
                            bbox=bbox,
                            maxfeatures=max_features,
                            outputFormat=output_format
                        )
                        
                        # Parse response
                        if output_format == "GeoJSON":
                            features = json.loads(response.read())
                            gdf = gpd.GeoDataFrame.from_features(features)
                        else:
                            # Handle other formats if needed
                            logger.warning(
                                f"Output format {output_format} not fully supported"
                            )
                            continue
                        
                        if not gdf.empty:
                            service_results[layer] = gdf
                            
                    except Exception as e:
                        logger.error(f"Error fetching layer {layer} from {name}: {e}")
                
                if service_results:
                    results[name] = service_results
                
            except Exception as e:
                logger.error(f"Error accessing WFS service {name}: {e}")
        
        return results
    
    def _is_bbox_valid(
        self,
        request_bbox: Tuple[float, float, float, float],
        layer_bbox: Tuple[float, float, float, float]
    ) -> bool:
        """Check if requested bbox is within layer bounds."""
        # Extract coordinates
        req_minx, req_miny, req_maxx, req_maxy = request_bbox
        lay_minx, lay_miny, lay_maxx, lay_maxy = layer_bbox
        
        # Check if request bbox is completely outside layer bbox
        if (req_maxx < lay_minx or req_minx > lay_maxx or
            req_maxy < lay_miny or req_miny > lay_maxy):
            return False
        
        return True
    
    def get_layer_info(
        self,
        layer: str,
        service_name: Optional[str] = None
    ) -> Optional[Dict]:
        """Get detailed information about a layer."""
        services_to_check = (
            {service_name: self.services[service_name]}
            if service_name and service_name in self.services
            else self.services
        )
        
        for name, service in services_to_check.items():
            try:
                if layer in service.contents:
                    layer_info = service.contents[layer]
                    return {
                        "service": name,
                        "title": layer_info.title,
                        "abstract": layer_info.abstract,
                        "keywords": layer_info.keywords,
                        "bbox": layer_info.boundingBoxWGS84,
                        "crs": layer_info.crsOptions,
                        "properties": [
                            op.name for op in layer_info.properties
                        ] if hasattr(layer_info, "properties") else []
                    }
            except Exception as e:
                logger.error(f"Error getting layer info from {name}: {e}")
        
        return None
    
    def get_available_layers(
        self,
        service_name: Optional[str] = None
    ) -> Dict[str, List[str]]:
        """Get available layers from WFS services."""
        results = {}
        
        services_to_check = (
            {service_name: self.services[service_name]}
            if service_name and service_name in self.services
            else self.services
        )
        
        for name, service in services_to_check.items():
            try:
                results[name] = list(service.contents.keys())
            except Exception as e:
                logger.error(f"Error getting layers from {name}: {e}")
        
        return results
    
    def download_to_file(
        self,
        bbox: Union[Tuple[float, float, float, float], Polygon],
        layers: List[str],
        output_dir: str,
        service_name: Optional[str] = None,
        format: str = "GeoJSON"
    ) -> Dict[str, Path]:
        """
        Download vector data to files.
        
        Args:
            bbox: Bounding box or Polygon
            layers: List of layers to fetch
            output_dir: Directory to save files
            service_name: Optional specific service to use
            format: Output format
            
        Returns:
            Dictionary mapping layer names to file paths
        """
        results = self.get_features(
            bbox=bbox,
            layers=layers,
            service_name=service_name,
            output_format=format
        )
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        file_paths = {}
        for service_name, service_data in results.items():
            for layer_name, gdf in service_data.items():
                if not gdf.empty:
                    file_path = output_dir / f"{service_name}_{layer_name}.geojson"
                    gdf.to_file(file_path, driver="GeoJSON")
                    file_paths[f"{service_name}_{layer_name}"] = file_path
        
        return file_paths 