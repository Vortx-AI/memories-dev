"""
Data fusion processor for combining raster and vector data.
"""

import os
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import geopandas as gpd
from shapely.geometry import box, Polygon
import rasterio
from rasterio import features
import cv2

class DataFusion:
    """Processor for combining raster and vector data."""
    
    def fuse_data(
        self,
        raster_data: Dict,
        vector_data: Dict,
        bbox: Union[Tuple[float, float, float, float], Polygon],
        resolution: float
    ) -> Dict:
        """
        Fuse raster and vector data.
        
        Args:
            raster_data: Dictionary containing raster data by source
            vector_data: Dictionary containing vector data by source
            bbox: Bounding box or Polygon
            resolution: Target resolution in meters
            
        Returns:
            Dictionary containing fused data
        """
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
        
        # Process vector data
        vector_layers = {}
        for source, layers in vector_data.items():
            for layer_name, gdf in layers.items():
                if gdf.empty:
                    continue
                
                # Rasterize vector data
                raster = self._rasterize_layer(
                    gdf,
                    (height, width),
                    transform,
                    layer_name
                )
                
                if layer_name not in vector_layers:
                    vector_layers[layer_name] = []
                vector_layers[layer_name].append(raster)
        
        # Merge vector layers
        merged_vectors = {}
        for layer_name, rasters in vector_layers.items():
            if rasters:
                merged = np.maximum.reduce(rasters)
                merged_vectors[layer_name] = merged
        
        # Process raster data
        processed_rasters = {}
        for source, data in raster_data.items():
            if not data:
                continue
            
            # Resize raster to target resolution if needed
            resized = self._resize_raster(
                data["data"],
                (height, width)
            )
            
            processed_rasters[source] = resized
        
        # Combine all data
        fused_data = {
            "raster": processed_rasters,
            "vector": merged_vectors,
            "metadata": {
                "resolution": resolution,
                "crs": "EPSG:4326",
                "transform": transform,
                "bounds": (minx, miny, maxx, maxy),
                "shape": (height, width)
            }
        }
        
        return fused_data
    
    def _rasterize_layer(
        self,
        gdf: gpd.GeoDataFrame,
        shape: Tuple[int, int],
        transform: rasterio.transform.Affine,
        layer_name: str
    ) -> np.ndarray:
        """Rasterize a vector layer with appropriate attributes."""
        
        if layer_name == "buildings":
            # Use height information if available
            if "height" in gdf.columns:
                values = gdf["height"].fillna(1).values
            else:
                values = np.ones(len(gdf))
                
        elif layer_name == "roads":
            # Use road type importance
            road_importance = {
                "motorway": 5,
                "trunk": 4,
                "primary": 3,
                "secondary": 2,
                "tertiary": 1
            }
            if "type" in gdf.columns:
                values = gdf["type"].map(
                    lambda x: road_importance.get(x, 1)
                ).fillna(1).values
            else:
                values = np.ones(len(gdf))
                
        else:
            # Default to binary mask
            values = np.ones(len(gdf))
        
        # Prepare shapes for rasterization
        shapes = ((geom, value) for geom, value in zip(gdf.geometry, values))
        
        # Rasterize
        raster = features.rasterize(
            shapes=shapes,
            out_shape=shape,
            transform=transform,
            fill=0,
            all_touched=True
        )
        
        return raster
    
    def _resize_raster(
        self,
        data: np.ndarray,
        target_shape: Tuple[int, int]
    ) -> np.ndarray:
        """Resize raster data to target shape."""
        if data.shape[1:] == target_shape:
            return data
        
        resized = np.zeros(
            (data.shape[0], *target_shape),
            dtype=data.dtype
        )
        
        for band in range(data.shape[0]):
            resized[band] = cv2.resize(
                data[band],
                (target_shape[1], target_shape[0]),
                interpolation=cv2.INTER_CUBIC
            )
        
        return resized
    
    def create_training_sample(
        self,
        fused_data: Dict,
        sample_size: Tuple[int, int] = (256, 256),
        include_layers: Optional[List[str]] = None
    ) -> Dict:
        """
        Create a training sample from fused data.
        
        Args:
            fused_data: Dictionary containing fused data
            sample_size: Size of the training sample
            include_layers: Optional list of vector layers to include
            
        Returns:
            Dictionary containing training sample
        """
        # Get available layers
        raster_data = fused_data["raster"]
        vector_data = fused_data["vector"]
        
        if include_layers is None:
            include_layers = list(vector_data.keys())
        
        # Stack raster bands
        raster_bands = []
        for source_data in raster_data.values():
            raster_bands.append(source_data)
        
        if raster_bands:
            stacked_raster = np.concatenate(raster_bands, axis=0)
        else:
            raise ValueError("No raster data available")
        
        # Stack vector layers
        vector_bands = []
        for layer in include_layers:
            if layer in vector_data:
                vector_bands.append(vector_data[layer])
        
        if vector_bands:
            stacked_vector = np.stack(vector_bands, axis=0)
        else:
            stacked_vector = np.zeros((0, *sample_size))
        
        # Resize to sample size if needed
        if stacked_raster.shape[1:] != sample_size:
            stacked_raster = self._resize_raster(
                stacked_raster,
                sample_size
            )
        
        if stacked_vector.shape[1:] != sample_size:
            stacked_vector = self._resize_raster(
                stacked_vector,
                sample_size
            )
        
        return {
            "raster_data": stacked_raster,
            "vector_data": stacked_vector,
            "metadata": {
                "raster_bands": [
                    f"{source}_{i}"
                    for source in raster_data.keys()
                    for i in range(raster_data[source].shape[0])
                ],
                "vector_layers": include_layers,
                "sample_size": sample_size
            }
        }
    
    def create_condition_mask(
        self,
        fused_data: Dict,
        condition_layers: List[str],
        sample_size: Tuple[int, int] = (256, 256)
    ) -> np.ndarray:
        """
        Create a condition mask for controlled generation.
        
        Args:
            fused_data: Dictionary containing fused data
            condition_layers: List of vector layers to use
            sample_size: Size of the condition mask
            
        Returns:
            Condition mask array
        """
        vector_data = fused_data["vector"]
        
        # Stack selected layers
        mask_layers = []
        for layer in condition_layers:
            if layer in vector_data:
                mask_layers.append(vector_data[layer])
            else:
                print(f"Warning: Layer {layer} not found")
        
        if not mask_layers:
            raise ValueError("No valid layers for condition mask")
        
        # Stack and resize
        condition_mask = np.stack(mask_layers, axis=0)
        if condition_mask.shape[1:] != sample_size:
            condition_mask = self._resize_raster(
                condition_mask,
                sample_size
            )
        
        return condition_mask 