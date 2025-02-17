from typing import Dict
import numpy as np

class ImageProcessor:
    """Process satellite imagery and extract features."""
    
    def __init__(self):
        """Initialize the image processor."""
        pass
        
    def calculate_ndwi(self, data: np.ndarray) -> np.ndarray:
        """Calculate Normalized Difference Water Index.
        
        Args:
            data: Multi-band image data with shape (bands, height, width)
            
        Returns:
            NDWI array with shape (height, width)
        """
        # Using green (band 1) and near-infrared (band 2)
        return (data[1] - data[2]) / (data[1] + data[2] + 1e-10)
    
    def extract_features(self, data: np.ndarray) -> Dict[str, np.ndarray]:
        """Extract features from satellite imagery.
        
        Args:
            data: Multi-band image data with shape (bands, height, width)
            
        Returns:
            Dictionary of extracted features including NDWI, greenery index, and built-up index
        """
        # Calculate NDWI (Normalized Difference Water Index)
        ndwi = self.calculate_ndwi(data)
        
        # Calculate vegetation index (NDVI-like)
        # Using red (band 0) and near-infrared (band 1)
        greenery_index = (data[1] - data[0]) / (data[1] + data[0] + 1e-10)
        
        # Calculate built-up index
        # Using near-infrared (band 1) and shortwave infrared (band 2)
        built_up_index = (data[2] - data[1]) / (data[2] + data[1] + 1e-10)
        
        return {
            "ndwi": ndwi,
            "greenery_index": greenery_index,
            "built_up_index": built_up_index
        } 