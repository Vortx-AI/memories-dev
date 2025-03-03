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
from datetime import datetime

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

def analyze_vegetation(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze vegetation patterns and health.
    
    Args:
        data: Dictionary containing NIR and red bands
        
    Returns:
        Dictionary containing vegetation analysis results
    """
    if 'nir_band' not in data or 'red_band' not in data:
        raise ValueError("NIR and red bands are required for vegetation analysis")
        
    ndvi = calculate_ndvi(data['nir_band'], data['red_band'])
    
    return {
        'ndvi_mean': float(np.mean(ndvi)),
        'ndvi_std': float(np.std(ndvi)),
        'vegetation_coverage': float(np.sum(ndvi > 0.3) / ndvi.size),
        'health_index': float(np.percentile(ndvi[ndvi > 0], 75))
    }

def analyze_urban_patterns(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze urban development patterns.
    
    Args:
        data: Dictionary containing urban feature data
        
    Returns:
        Dictionary containing urban pattern analysis
    """
    if 'features' not in data:
        raise ValueError("Urban features data is required")
        
    gdf = gpd.GeoDataFrame(data['features'])
    
    return {
        'building_density': len(gdf) / gdf.total_bounds.area,
        'mean_building_size': float(gdf.geometry.area.mean()),
        'urban_coverage': float(gdf.geometry.area.sum() / gdf.total_bounds.area),
        'pattern_type': _classify_urban_pattern(gdf)
    }

def analyze_change(
    before_data: Dict[str, Any],
    after_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Analyze changes between two time periods.
    
    Args:
        before_data: Data from earlier time period
        after_data: Data from later time period
        
    Returns:
        Dictionary containing change analysis results
    """
    changes = detect_changes(
        before_data.get('image', np.array([])),
        after_data.get('image', np.array([]))
    )
    
    return {
        'change_area': float(np.sum(changes)),
        'change_percentage': float(np.mean(changes)) * 100,
        'change_clusters': int(ndimage.label(changes)[1]),
        'major_changes': _identify_major_changes(changes)
    }

def generate_report(analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate a comprehensive analysis report.
    
    Args:
        analyses: List of analysis results
        
    Returns:
        Dictionary containing complete analysis report
    """
    return {
        'timestamp': datetime.now().isoformat(),
        'summary': _generate_summary(analyses),
        'details': analyses,
        'recommendations': _generate_recommendations(analyses)
    }

def _classify_urban_pattern(gdf: gpd.GeoDataFrame) -> str:
    """Classify urban development pattern."""
    # Implementation would analyze spatial relationships
    # and classify as grid, organic, radial, etc.
    return "grid"  # Placeholder

def _identify_major_changes(changes: np.ndarray) -> List[Dict[str, Any]]:
    """Identify and characterize major changes."""
    # Implementation would analyze change clusters
    # and characterize their nature
    return []  # Placeholder

def _generate_summary(analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate a summary of analyses."""
    return {
        'total_analyses': len(analyses),
        'analysis_types': list(set(a.get('type', '') for a in analyses))
    }

def _generate_recommendations(analyses: List[Dict[str, Any]]) -> List[str]:
    """Generate recommendations based on analyses."""
    return []  # Placeholder

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