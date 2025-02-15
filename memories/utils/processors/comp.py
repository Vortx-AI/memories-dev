"""
Image computation utilities with GPU acceleration when available.
"""

import numpy as np

try:
    import cupy as cp
    HAS_CUDA = True
except ImportError:
    HAS_CUDA = False

def calculate_ndvi(image: np.ndarray) -> np.ndarray:
    """
    Calculate Normalized Difference Vegetation Index (NDVI).
    Falls back to CPU if GPU is not available.
    
    Args:
        image (np.ndarray): Input image array with shape (H, W, C)
                           where C >= 2 (red and NIR bands)
    
    Returns:
        np.ndarray: NDVI values scaled to 0-255 range
    """
    if len(image.shape) != 3 or image.shape[2] < 2:
        raise ValueError("Image must have at least 2 channels (red and NIR)")
    
    # Extract red and NIR bands
    red = image[..., 0].astype(np.float32)
    nir = image[..., 1].astype(np.float32)
    
    # Use GPU if available
    if HAS_CUDA:
        red_gpu = cp.asarray(red)
        nir_gpu = cp.asarray(nir)
        
        # Calculate NDVI
        numerator = nir_gpu - red_gpu
        denominator = nir_gpu + red_gpu
        ndvi = numerator / (denominator + 1e-8)  # Add small epsilon to avoid division by zero
        
        # Scale to 0-255 range
        ndvi = ((ndvi + 1) * 127.5).astype(cp.uint8)
        
        # Transfer back to CPU
        return cp.asnumpy(ndvi)
    else:
        # Calculate NDVI on CPU
        numerator = nir - red
        denominator = nir + red
        ndvi = numerator / (denominator + 1e-8)
        
        # Scale to 0-255 range
        return ((ndvi + 1) * 127.5).astype(np.uint8)

def transformer_process(image: np.ndarray) -> np.ndarray:
    """
    Process image using transformer-based approach.
    Falls back to CPU if GPU is not available.
    
    Args:
        image (np.ndarray): Input image array
    
    Returns:
        np.ndarray: Processed image array
    """
    if HAS_CUDA:
        # Convert to GPU array if not already
        if not isinstance(image, cp.ndarray):
            image = cp.asarray(image)
            
        # Apply transformations
        processed = cp.mean(image, axis=2) if len(image.shape) == 3 else image
        processed = cp.clip(processed, 0, 255)
        
        # Transfer back to CPU
        return cp.asnumpy(processed)
    else:
        # Process on CPU
        processed = np.mean(image, axis=2) if len(image.shape) == 3 else image
        return np.clip(processed, 0, 255)
