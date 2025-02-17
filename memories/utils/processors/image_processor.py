"""
Image processor for satellite imagery.
"""

import os
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from shapely.geometry import box, Polygon
import cv2

class ImageProcessor:
    """Processor for satellite imagery."""
    
    def calculate_ndwi(self, data: np.ndarray, green_band: int = 1, nir_band: int = 2) -> np.ndarray:
        """Calculate Normalized Difference Water Index (NDWI).
        
        Args:
            data: Multi-band image data with shape (bands, height, width)
            green_band: Index of the green band (default: 1)
            nir_band: Index of the near-infrared band (default: 2)
            
        Returns:
            NDWI array with shape (height, width)
        """
        green = data[green_band]
        nir = data[nir_band]
        
        # Avoid division by zero
        denominator = green + nir
        denominator[denominator == 0] = 1e-10
        
        ndwi = (green - nir) / denominator
        return ndwi
    
    def extract_features(self, data: np.ndarray) -> Dict[str, np.ndarray]:
        """Extract features from satellite imagery.
        
        Args:
            data: Multi-band image data with shape (bands, height, width)
            
        Returns:
            Dictionary of extracted features
        """
        # Calculate various indices
        ndwi = self.calculate_ndwi(data)
        
        # Calculate other features
        greenery_index = (data[1] - data[0]) / (data[1] + data[0] + 1e-10)  # Normalized difference vegetation index
        built_up_index = (data[2] - data[1]) / (data[2] + data[1] + 1e-10)  # Built-up index
        
        return {
            "ndwi": ndwi,
            "greenery_index": greenery_index,
            "built_up_index": built_up_index
        }
    
    def process_satellite_data(
        self,
        data: Dict,
        target_resolution: float,
        bbox: Union[Tuple[float, float, float, float], Polygon]
    ) -> Dict:
        """
        Process satellite imagery from various sources.
        
        Args:
            data: Dictionary containing satellite data by source
            target_resolution: Target resolution in meters
            bbox: Bounding box or Polygon
            
        Returns:
            Dictionary containing processed imagery
        """
        processed_data = {}
        
        for source, source_data in data.items():
            if not source_data:
                continue
                
            try:
                # Get source resolution
                source_res = source_data["metadata"]["resolution"]
                
                # Resample if needed
                if source_res != target_resolution:
                    resampled_data = self._resample_image(
                        source_data["data"],
                        source_res,
                        target_resolution
                    )
                else:
                    resampled_data = source_data["data"]
                
                # Normalize data
                normalized_data = self._normalize_data(resampled_data)
                
                # Store processed data
                processed_data[source] = {
                    "data": normalized_data,
                    "metadata": {
                        **source_data["metadata"],
                        "resolution": target_resolution,
                        "processing": {
                            "resampled": source_res != target_resolution,
                            "normalized": True
                        }
                    }
                }
                
            except Exception as e:
                print(f"Error processing {source} data: {e}")
        
        return processed_data
    
    def _resample_image(
        self,
        data: np.ndarray,
        source_res: float,
        target_res: float
    ) -> np.ndarray:
        """Resample image to target resolution."""
        scale_factor = source_res / target_res
        
        if scale_factor == 1:
            return data
        
        # Calculate new dimensions
        new_height = int(data.shape[1] * scale_factor)
        new_width = int(data.shape[2] * scale_factor)
        
        resampled_data = np.zeros((data.shape[0], new_height, new_width), dtype=data.dtype)
        
        for band in range(data.shape[0]):
            resampled_data[band] = cv2.resize(
                data[band],
                (new_width, new_height),
                interpolation=cv2.INTER_CUBIC
            )
        
        return resampled_data
    
    def _normalize_data(self, data: np.ndarray) -> np.ndarray:
        """Normalize data to 0-1 range."""
        # Handle different data types
        if data.dtype == np.uint8:
            return data.astype(np.float32) / 255.0
        elif data.dtype == np.uint16:
            return data.astype(np.float32) / 65535.0
        else:
            # For float data, clip to valid range
            data_min = np.percentile(data, 1)
            data_max = np.percentile(data, 99)
            clipped = np.clip(data, data_min, data_max)
            return (clipped - data_min) / (data_max - data_min)
    
    def merge_sources(
        self,
        processed_data: Dict,
        weights: Optional[Dict[str, float]] = None
    ) -> np.ndarray:
        """
        Merge data from multiple sources.
        
        Args:
            processed_data: Dictionary of processed data by source
            weights: Optional weights for each source
            
        Returns:
            Merged array
        """
        if not processed_data:
            return None
        
        # Get shapes of all arrays
        shapes = {
            source: data["data"].shape
            for source, data in processed_data.items()
        }
        
        # Find common shape (minimum dimensions)
        common_shape = (
            min(s[0] for s in shapes.values()),  # bands
            min(s[1] for s in shapes.values()),  # height
            min(s[2] for s in shapes.values())   # width
        )
        
        # Resize all arrays to common shape
        resized_data = {}
        for source, data in processed_data.items():
            if shapes[source] == common_shape:
                resized_data[source] = data["data"]
            else:
                resized = np.zeros(common_shape, dtype=np.float32)
                for band in range(common_shape[0]):
                    resized[band] = cv2.resize(
                        data["data"][band],
                        (common_shape[2], common_shape[1]),
                        interpolation=cv2.INTER_CUBIC
                    )
                resized_data[source] = resized
        
        # Apply weights if provided
        if weights is None:
            weights = {source: 1.0 for source in processed_data.keys()}
        
        # Normalize weights
        total_weight = sum(weights.values())
        weights = {k: w/total_weight for k, w in weights.items()}
        
        # Merge arrays
        merged = np.zeros(common_shape, dtype=np.float32)
        for source, data in resized_data.items():
            merged += data * weights[source]
        
        return merged
    
    def enhance_image(
        self,
        data: np.ndarray,
        enhancement: str = "standard"
    ) -> np.ndarray:
        """
        Apply image enhancement.
        
        Args:
            data: Input image array
            enhancement: Enhancement type ("standard", "contrast", "sharpen")
            
        Returns:
            Enhanced array
        """
        if enhancement == "standard":
            # Standard enhancement (histogram equalization)
            enhanced = np.zeros_like(data)
            for band in range(data.shape[0]):
                enhanced[band] = cv2.equalizeHist(
                    (data[band] * 255).astype(np.uint8)
                ).astype(np.float32) / 255.0
                
        elif enhancement == "contrast":
            # Contrast enhancement
            enhanced = np.zeros_like(data)
            for band in range(data.shape[0]):
                band_data = data[band]
                p2, p98 = np.percentile(band_data, (2, 98))
                enhanced[band] = np.clip(
                    (band_data - p2) / (p98 - p2),
                    0, 1
                )
                
        elif enhancement == "sharpen":
            # Sharpening
            kernel = np.array([
                [-1,-1,-1],
                [-1, 9,-1],
                [-1,-1,-1]
            ])
            enhanced = np.zeros_like(data)
            for band in range(data.shape[0]):
                enhanced[band] = cv2.filter2D(
                    data[band],
                    -1,
                    kernel
                )
            enhanced = np.clip(enhanced, 0, 1)
            
        else:
            raise ValueError(f"Unknown enhancement type: {enhancement}")
        
        return enhanced
    
    def create_composite(
        self,
        data: np.ndarray,
        bands: List[int] = [2, 1, 0]  # RGB by default
    ) -> np.ndarray:
        """
        Create a composite image from selected bands.
        
        Args:
            data: Input image array
            bands: List of band indices to use
            
        Returns:
            Composite array (HxWx3)
        """
        if len(bands) != 3:
            raise ValueError("Must specify exactly 3 bands")
            
        composite = np.stack([
            data[band_idx] for band_idx in bands
        ], axis=-1)
        
        return np.clip(composite, 0, 1) 