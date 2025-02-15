"""
Utility functions for Earth observation data analysis.
"""

import numpy as np
import geopandas as gpd
from typing import Union, List, Dict, Any
from shapely.geometry import Polygon, MultiPolygon
import rasterio
from rasterio.features import shapes
from scipy import ndimage

def calculate_ndvi(nir_band: np.ndarray, red_band: np.ndarray) -> np.ndarray:
    """
    Calculate Normalized Difference Vegetation Index.
    
    Args:
        nir_band: Near-infrared band
        red_band: Red band
        
    Returns:
        NDVI array
    """
    ndvi = np.where(
        (nir_band + red_band) != 0,
        (nir_band - red_band) / (nir_band + red_band),
        0
    )
    return ndvi

def detect_changes(
    before_image: np.ndarray,
    after_image: np.ndarray,
    threshold: float = 0.2
) -> np.ndarray:
    """
    Detect changes between two images.
    
    Args:
        before_image: Image at time t1
        after_image: Image at time t2
        threshold: Change detection threshold
        
    Returns:
        Binary change mask
    """
    diff = np.abs(after_image - before_image)
    changes = diff > threshold
    
    # Remove noise
    changes = ndimage.binary_opening(changes)
    return changes

def vectorize_raster(
    raster_data: np.ndarray,
    transform: Any,
    crs: Any
) -> gpd.GeoDataFrame:
    """
    Convert raster to vector format.
    
    Args:
        raster_data: Input raster
        transform: Raster transform
        crs: Coordinate reference system
        
    Returns:
        GeoDataFrame with vectorized features
    """
    mask = raster_data > 0
    features = shapes(raster_data, mask=mask, transform=transform)
    
    geometries = []
    values = []
    
    for geom, val in features:
        geometries.append(Polygon(geom['coordinates'][0]))
        values.append(val)
    
    gdf = gpd.GeoDataFrame({
        'geometry': geometries,
        'value': values
    }, crs=crs)
    
    return gdf

def smooth_timeseries(
    data: np.ndarray,
    window_size: int = 5
) -> np.ndarray:
    """
    Apply smoothing to time series data.
    
    Args:
        data: Input time series
        window_size: Smoothing window size
        
    Returns:
        Smoothed time series
    """
    kernel = np.ones(window_size) / window_size
    smoothed = ndimage.convolve1d(data, kernel, mode='reflect')
    return smoothed

def calculate_area_statistics(
    gdf: gpd.GeoDataFrame,
    value_column: str = None
) -> Dict[str, float]:
    """
    Calculate area-based statistics for vector features.
    
    Args:
        gdf: Input GeoDataFrame
        value_column: Optional column for weighted statistics
        
    Returns:
        Dictionary of statistics
    """
    stats = {
        'total_area': gdf.geometry.area.sum(),
        'mean_area': gdf.geometry.area.mean(),
        'count': len(gdf)
    }
    
    if value_column and value_column in gdf.columns:
        stats.update({
            'weighted_mean': np.average(
                gdf.geometry.area,
                weights=gdf[value_column]
            )
        })
    
    return stats 