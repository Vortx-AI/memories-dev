"""
Advanced raster tile processor with real-time processing capabilities.
"""

import os
import io
from typing import Dict, List, Optional, Tuple, Union, Any
from datetime import datetime
import json
from pathlib import Path
import mercantile
import numpy as np
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.enums import Compression
from rasterio.io import MemoryFile
from rasterio.mask import mask
from rasterio.merge import merge
from rasterio.windows import Window
from PIL import Image
import xarray as xr
import dask.array as da
from shapely.geometry import box, mapping
import pyproj
from pyproj import Transformer
import duckdb
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
from rasterio.transform import from_bounds
import logging

# Initialize GPU support flags
HAS_CUDF = False
cudf = None

try:
    import cudf
    HAS_CUDF = True
except ImportError:
    pass

logger = logging.getLogger(__name__)

class RasterTileProcessor:
    """Advanced raster tile processor with real-time capabilities"""
    
    def __init__(self):
        """Initialize the raster tile processor."""
        self._styles = self._load_styles()
        self._transformations = self._load_transformations()
        self._filters = self._load_filters()
        self.db = self._init_database()
        
    async def process_tile(
        self,
        bounds: mercantile.bounds,
        format: str = 'png',
        style: Optional[str] = None,
        time: Optional[str] = None,
        filter: Optional[str] = None,
        transform: Optional[str] = None,
        use_gpu: bool = False
    ) -> bytes:
        """Process raster tile with advanced features"""
        try:
            # Get data for bounds
            data = await self._get_data(bounds, time)
            
            # Process on GPU if requested and available
            if use_gpu and HAS_CUDF and cudf:
                try:
                    data = self._process_on_gpu(data)
                except Exception as e:
                    logger.warning(f"GPU processing failed: {e}")
                    data = self._process_on_cpu(data)
            else:
                data = self._process_on_cpu(data)
            
            # Apply filters if specified
            if filter:
                data = self._apply_filter(data, filter)
            
            # Apply transformations if specified
            if transform:
                data = self._apply_transformation(data, transform)
            
            # Apply styling if specified
            if style:
                data = self._apply_style(data, style)
            
            # Convert to specified format
            return self._to_format(data, format)
            
        except Exception as e:
            raise Exception(f"Error processing raster tile: {str(e)}")
    
    async def _get_data(
        self,
        bounds: mercantile.bounds,
        time: Optional[str]
    ) -> xr.DataArray:
        """Get raster data for bounds"""
        # Build query
        query = f"""
        SELECT path, band_metadata
        FROM raster_data
        WHERE ST_Intersects(bounds, ST_GeomFromText('{box(*bounds).__geo_interface__}'))
        """
        
        if time:
            query += f" AND time_column <= '{time}'"
            
        # Execute query
        with self.db.cursor() as cursor:
            cursor.execute(query)
            results = cursor.fetchall()
            
        # Load and merge raster data
        datasets = []
        for path, metadata in results:
            with rasterio.open(path) as src:
                # Read data for bounds
                window = src.window(*bounds)
                data = src.read(window=window)
                
                # Create DataArray
                ds = xr.DataArray(
                    data,
                    dims=('band', 'y', 'x'),
                    coords={
                        'band': range(data.shape[0]),
                        'y': np.linspace(bounds.north, bounds.south, data.shape[1]),
                        'x': np.linspace(bounds.west, bounds.east, data.shape[2])
                    },
                    attrs=metadata
                )
                datasets.append(ds)
                
        # Merge datasets
        if len(datasets) > 1:
            return xr.concat(datasets, dim='time')
        elif len(datasets) == 1:
            return datasets[0]
        else:
            raise Exception("No data found for bounds")
    
    def _process_on_gpu(self, data: xr.DataArray) -> xr.DataArray:
        """Process data using GPU acceleration."""
        if not (HAS_CUDF and cudf):
            raise RuntimeError("GPU processing requested but GPU support not available")
        
        try:
            # Convert to GPU DataFrame
            gpu_data = cudf.from_pandas(data.to_dataframe())
            # Add GPU processing logic here
            return xr.DataArray.from_dataframe(gpu_data.to_pandas())
        except Exception as e:
            logger.error(f"GPU processing error: {e}")
            raise

    def _process_on_cpu(self, data: xr.DataArray) -> xr.DataArray:
        """Process data using CPU."""
        return data
    
    def _apply_filter(self, data: xr.DataArray, filter: str) -> xr.DataArray:
        """Apply filter to the data."""
        if filter == 'median':
            return data.rolling(y=3, x=3, min_periods=1).median()
        elif filter == 'mean':
            return data.rolling(y=3, x=3, min_periods=1).mean()
        elif filter == 'gaussian':
            import scipy.ndimage as ndimage
            return xr.apply_ufunc(
                ndimage.gaussian_filter,
                data,
                kwargs={'sigma': 1}
            )
        return data
    
    def _apply_transformation(self, data: xr.DataArray, transform: str) -> xr.DataArray:
        """Apply transformation to the data."""
        if transform == 'flip_vertical':
            return data.flip('y')
        elif transform == 'flip_horizontal':
            return data.flip('x')
        elif transform == 'rotate_90':
            return data.transpose('y', 'x')
        return data
    
    def _apply_style(self, data: xr.DataArray, style: str) -> xr.DataArray:
        """Apply style to the data."""
        style_config = self._styles.get(style, {})
        if not style_config:
            return data
        
        # Apply style transformations
        if 'colormap' in style_config:
            data = self._apply_colormap(data, style_config['colormap'])
        if 'hillshade' in style_config:
            data = self._calculate_hillshade(data)
        return data
    
    def _to_format(self, data: xr.DataArray, format: str) -> bytes:
        """Convert data to the specified format."""
        import io
        from PIL import Image
        
        # Convert to numpy array
        array = data.values
        
        # Scale to 0-255 range if needed
        if array.dtype != np.uint8:
            array = ((array - array.min()) * (255.0 / (array.max() - array.min()))).astype(np.uint8)
        
        # Create image
        img = Image.fromarray(array)
        
        # Save to bytes
        output = io.BytesIO()
        img.save(output, format=format.upper())
        return output.getvalue()
    
    def _calculate_hillshade(
        self,
        data: xr.DataArray,
        azimuth: float = 315.0,
        altitude: float = 45.0
    ) -> xr.DataArray:
        """Calculate hillshade"""
        x, y = np.gradient(data.values)
        slope = np.pi/2. - np.arctan(np.sqrt(x*x + y*y))
        aspect = np.arctan2(-x, y)
        azimuthrad = azimuth*np.pi/180.
        altituderad = altitude*np.pi/180.
        
        shaded = np.sin(altituderad)*np.sin(slope) + \
                np.cos(altituderad)*np.cos(slope)*np.cos(azimuthrad-aspect)
                
        return xr.DataArray(
            shaded,
            dims=data.dims,
            coords=data.coords
        )
    
    def _apply_colormap(
        self,
        data: xr.DataArray,
        colormap: Dict[str, List[int]]
    ) -> xr.DataArray:
        """Apply colormap to data"""
        # Create lookup table
        lut = np.zeros((256, 3), dtype=np.uint8)
        for value, color in colormap.items():
            lut[int(value)] = color
            
        # Apply lookup table
        return xr.DataArray(
            lut[data.values.astype(np.uint8)],
            dims=('y', 'x', 'band'),
            coords={
                'y': data.y,
                'x': data.x,
                'band': ['R', 'G', 'B']
            }
        )
    
    def available_styles(self) -> Dict[str, Any]:
        """Get available styles"""
        return self._styles
    
    def available_transformations(self) -> List[str]:
        """Get available transformations"""
        return list(self._transformations.keys())
    
    def available_filters(self) -> List[str]:
        """Get available filters"""
        return list(self._filters.keys())
    
    def _load_styles(self) -> Dict[str, Any]:
        """Load style configurations"""
        return {
            'default': {
                'colormap': {
                    'water': [0, 0, 255],
                    'land': [0, 255, 0]
                }
            }
        }
    
    def _load_transformations(self) -> Dict[str, Any]:
        """Load transformation configurations"""
        return {
            'flip_vertical': 'Flip vertically',
            'flip_horizontal': 'Flip horizontally',
            'rotate_90': 'Rotate 90 degrees'
        }
    
    def _load_filters(self) -> Dict[str, Any]:
        """Load filter configurations"""
        return {
            'median': 'Median filter',
            'mean': 'Mean filter',
            'gaussian': 'Gaussian filter'
        }
    
    def _init_database(self) -> duckdb.DuckDBPyConnection:
        """Initialize DuckDB database"""
        db = duckdb.connect(':memory:')
        
        # Install and load spatial extension
        db.execute("INSTALL spatial;")
        db.execute("LOAD spatial;")
        
        db.execute("""
            CREATE TABLE raster_data (
                id INTEGER,
                path VARCHAR,
                bounds GEOMETRY,
                time_column TIMESTAMP,
                band_metadata JSON
            )
        """)
        return db 