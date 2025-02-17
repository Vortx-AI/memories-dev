"""
Utility processors for image and vector data.
"""

import numpy as np
from typing import Optional, List, Dict, Any

class ImageProcessor:
    """Processor for satellite imagery and other image data."""
    
    def calculate_ndwi(self, data: np.ndarray, green_band: int = 1, nir_band: int = 3) -> np.ndarray:
        """Calculate Normalized Difference Water Index (NDWI).
        
        Args:
            data: Multi-band image data with shape (bands, height, width)
            green_band: Index of the green band
            nir_band: Index of the near-infrared band
            
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

class VectorProcessor:
    """Processor for vector data (GeoJSON, shapefiles, etc.)."""
    
    def calculate_area(self, features: List[Dict[str, Any]]) -> float:
        """Calculate total area of vector features.
        
        Args:
            features: List of GeoJSON features
            
        Returns:
            Total area in square meters
        """
        total_area = 0.0
        for feature in features:
            if "properties" in feature and "area" in feature["properties"]:
                total_area += feature["properties"]["area"]
        return total_area
    
    def filter_by_type(self, features: List[Dict[str, Any]], feature_type: str) -> List[Dict[str, Any]]:
        """Filter features by type.
        
        Args:
            features: List of GeoJSON features
            feature_type: Type to filter by (e.g., "water", "building")
            
        Returns:
            Filtered list of features
        """
        return [
            feature for feature in features
            if feature.get("properties", {}).get("type") == feature_type
        ] 