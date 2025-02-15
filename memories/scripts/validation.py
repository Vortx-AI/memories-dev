"""
Validation utilities for Earth observation data analysis.
"""

from typing import Dict, Any, Union, List
import numpy as np
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon
import rasterio
from datetime import datetime

class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass

def validate_raster_data(
    data: np.ndarray,
    expected_bands: int = None,
    allow_nan: bool = False
) -> bool:
    """
    Validate raster data array.
    
    Args:
        data: Input raster array
        expected_bands: Expected number of bands
        allow_nan: Whether to allow NaN values
        
    Returns:
        True if valid, raises ValidationError otherwise
    """
    if not isinstance(data, np.ndarray):
        raise ValidationError("Input must be a numpy array")
        
    if expected_bands and data.shape[0] != expected_bands:
        raise ValidationError(
            f"Expected {expected_bands} bands, got {data.shape[0]}"
        )
        
    if not allow_nan and np.isnan(data).any():
        raise ValidationError("NaN values found in data")
        
    return True

def validate_vector_data(
    data: gpd.GeoDataFrame,
    required_columns: List[str] = None,
    geometry_types: List[str] = None
) -> bool:
    """
    Validate vector data.
    
    Args:
        data: Input GeoDataFrame
        required_columns: List of required columns
        geometry_types: List of allowed geometry types
        
    Returns:
        True if valid, raises ValidationError otherwise
    """
    if not isinstance(data, gpd.GeoDataFrame):
        raise ValidationError("Input must be a GeoDataFrame")
        
    if required_columns:
        missing = [col for col in required_columns if col not in data.columns]
        if missing:
            raise ValidationError(f"Missing required columns: {missing}")
            
    if geometry_types:
        invalid = data[~data.geometry.type.isin(geometry_types)]
        if len(invalid) > 0:
            raise ValidationError(
                f"Invalid geometry types found: {invalid.geometry.type.unique()}"
            )
            
    return True

def validate_date_range(
    start_date: Union[str, datetime],
    end_date: Union[str, datetime]
) -> bool:
    """
    Validate date range.
    
    Args:
        start_date: Start date
        end_date: End date
        
    Returns:
        True if valid, raises ValidationError otherwise
    """
    if isinstance(start_date, str):
        try:
            start_date = datetime.fromisoformat(start_date)
        except ValueError:
            raise ValidationError("Invalid start_date format")
            
    if isinstance(end_date, str):
        try:
            end_date = datetime.fromisoformat(end_date)
        except ValueError:
            raise ValidationError("Invalid end_date format")
            
    if start_date > end_date:
        raise ValidationError("start_date must be before end_date")
        
    return True

def validate_analysis_config(config: Dict[str, Any]) -> bool:
    """
    Validate analysis configuration.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        True if valid, raises ValidationError otherwise
    """
    required_keys = ['tile_size', 'overlap', 'batch_size']
    missing = [key for key in required_keys if key not in config]
    
    if missing:
        raise ValidationError(f"Missing required config keys: {missing}")
        
    if config['tile_size'] <= 0:
        raise ValidationError("tile_size must be positive")
        
    if config['overlap'] < 0:
        raise ValidationError("overlap must be non-negative")
        
    if config['batch_size'] <= 0:
        raise ValidationError("batch_size must be positive")
        
    return True

def validate_bounds(
    bounds: Union[List[float], Dict[str, float]]
) -> List[float]:
    """
    Validate and normalize spatial bounds.
    
    Args:
        bounds: Spatial bounds as list [minx, miny, maxx, maxy]
               or dict with keys 'minx', 'miny', 'maxx', 'maxy'
               
    Returns:
        Normalized bounds as list [minx, miny, maxx, maxy]
    """
    if isinstance(bounds, dict):
        required = ['minx', 'miny', 'maxx', 'maxy']
        if not all(key in bounds for key in required):
            raise ValidationError(
                f"Missing required bounds keys: {required}"
            )
        bounds = [bounds['minx'], bounds['miny'],
                 bounds['maxx'], bounds['maxy']]
                 
    if len(bounds) != 4:
        raise ValidationError(
            f"Bounds must have 4 values, got {len(bounds)}"
        )
        
    if bounds[0] >= bounds[2] or bounds[1] >= bounds[3]:
        raise ValidationError(
            "Invalid bounds: minx/miny must be less than maxx/maxy"
        )
        
    return bounds 