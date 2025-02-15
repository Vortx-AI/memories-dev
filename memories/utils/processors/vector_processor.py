"""
Vector processor for handling vector data.
"""

import os
from typing import Dict, List, Optional, Tuple, Union
import geopandas as gpd
from shapely.geometry import box, Polygon
import numpy as np
import pandas as pd

class VectorProcessor:
    """Processor for vector data."""
    
    def process_vector_data(
        self,
        data: Dict,
        bbox: Union[Tuple[float, float, float, float], Polygon]
    ) -> Dict:
        """
        Process vector data from various sources.
        
        Args:
            data: Dictionary containing vector data by source
            bbox: Bounding box or Polygon
            
        Returns:
            Dictionary containing processed vector data
        """
        processed_data = {}
        
        for source, source_data in data.items():
            if not source_data:
                continue
                
            try:
                # Process each layer
                processed_layers = {}
                for layer, gdf in source_data.items():
                    if gdf.empty:
                        continue
                    
                    # Ensure data is in WGS84
                    if gdf.crs != "EPSG:4326":
                        gdf = gdf.to_crs("EPSG:4326")
                    
                    # Clip to bbox if needed
                    if isinstance(bbox, tuple):
                        bbox_poly = box(*bbox)
                    else:
                        bbox_poly = bbox
                    
                    gdf = gdf[gdf.intersects(bbox_poly)]
                    if not gdf.empty:
                        gdf = gdf.clip(bbox_poly)
                    
                    # Clean and standardize attributes
                    gdf = self._standardize_attributes(gdf, layer)
                    
                    # Add to processed layers
                    processed_layers[layer] = gdf
                
                if processed_layers:
                    processed_data[source] = processed_layers
                
            except Exception as e:
                print(f"Error processing {source} data: {e}")
        
        return processed_data
    
    def _standardize_attributes(
        self,
        gdf: gpd.GeoDataFrame,
        layer: str
    ) -> gpd.GeoDataFrame:
        """Standardize attributes for a layer."""
        # Define standard attribute mappings
        mappings = {
            "buildings": {
                "height": ["height", "building:height", "building:levels"],
                "type": ["building", "building:type", "building:use"],
                "name": ["name", "addr:housename"],
                "levels": ["building:levels", "levels"]
            },
            "roads": {
                "type": ["highway", "road_type"],
                "name": ["name", "ref"],
                "surface": ["surface", "road_surface"],
                "width": ["width", "road_width"]
            },
            "landuse": {
                "type": ["landuse", "land_use"],
                "name": ["name"],
                "area": ["area"]
            }
        }
        
        if layer not in mappings:
            return gdf
        
        # Create standardized columns
        for std_col, source_cols in mappings[layer].items():
            # Find first available source column
            for src_col in source_cols:
                if src_col in gdf.columns:
                    gdf[std_col] = gdf[src_col]
                    break
        
        return gdf
    
    def merge_sources(
        self,
        processed_data: Dict,
        priority: Optional[List[str]] = None
    ) -> Dict[str, gpd.GeoDataFrame]:
        """
        Merge vector data from multiple sources.
        
        Args:
            processed_data: Dictionary of processed data by source
            priority: Optional list of sources in priority order
            
        Returns:
            Dictionary of merged GeoDataFrames by layer
        """
        if not processed_data:
            return {}
        
        # Get all available layers
        all_layers = set()
        for source_data in processed_data.values():
            all_layers.update(source_data.keys())
        
        # If no priority specified, use alphabetical order
        if priority is None:
            priority = sorted(processed_data.keys())
        
        merged_data = {}
        
        for layer in all_layers:
            layer_gdfs = []
            
            # Get data from each source in priority order
            for source in priority:
                if source in processed_data and layer in processed_data[source]:
                    layer_gdfs.append(processed_data[source][layer])
            
            if layer_gdfs:
                # Concatenate GeoDataFrames
                merged = gpd.GeoDataFrame(
                    pd.concat(layer_gdfs, ignore_index=True),
                    crs=layer_gdfs[0].crs
                )
                
                # Remove duplicates based on geometry
                merged = merged.drop_duplicates(subset="geometry")
                
                merged_data[layer] = merged
        
        return merged_data
    
    def rasterize_layer(
        self,
        gdf: gpd.GeoDataFrame,
        resolution: float,
        bbox: Union[Tuple[float, float, float, float], Polygon],
        attribute: Optional[str] = None
    ) -> np.ndarray:
        """
        Rasterize vector data.
        
        Args:
            gdf: GeoDataFrame to rasterize
            resolution: Output resolution in meters
            bbox: Bounding box or Polygon
            attribute: Optional attribute to use for pixel values
            
        Returns:
            Rasterized array
        """
        import rasterio
        from rasterio import features
        
        # Convert bbox to bounds
        if isinstance(bbox, tuple):
            minx, miny, maxx, maxy = bbox
        else:
            minx, miny, maxx, maxy = bbox.bounds
        
        # Calculate dimensions
        width = int((maxx - minx) / resolution)
        height = int((maxy - miny) / resolution)
        
        # Create transform
        transform = rasterio.transform.from_bounds(
            minx, miny, maxx, maxy,
            width, height
        )
        
        # Prepare shapes for rasterization
        if attribute:
            shapes = ((geom, value) for geom, value in zip(gdf.geometry, gdf[attribute]))
        else:
            shapes = ((geom, 1) for geom in gdf.geometry)
        
        # Rasterize
        raster = features.rasterize(
            shapes=shapes,
            out_shape=(height, width),
            transform=transform,
            fill=0,
            all_touched=True
        )
        
        return raster
    
    def calculate_density(
        self,
        gdf: gpd.GeoDataFrame,
        resolution: float,
        bbox: Union[Tuple[float, float, float, float], Polygon],
        kernel_size: int = 5
    ) -> np.ndarray:
        """
        Calculate feature density.
        
        Args:
            gdf: GeoDataFrame to analyze
            resolution: Output resolution in meters
            bbox: Bounding box or Polygon
            kernel_size: Size of the smoothing kernel
            
        Returns:
            Density array
        """
        import cv2
        
        # Rasterize first
        raster = self.rasterize_layer(gdf, resolution, bbox)
        
        # Apply Gaussian smoothing
        kernel = np.ones((kernel_size, kernel_size)) / (kernel_size * kernel_size)
        density = cv2.filter2D(raster.astype(np.float32), -1, kernel)
        
        return density 