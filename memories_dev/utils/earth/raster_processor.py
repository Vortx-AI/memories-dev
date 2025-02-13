"""
Advanced raster tile processor with real-time processing capabilities.
"""

import os
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

class RasterTileProcessor:
    """Advanced raster tile processor with real-time capabilities"""
    
    def __init__(self):
        self.styles = self._load_styles()
        self.transformations = self._load_transformations()
        self.filters = self._load_filters()
        self.db = self._init_database()
        
    async def process_tile(
        self,
        bounds: mercantile.Bounds,
        format: str = 'png',
        style: Optional[str] = None,
        time: Optional[str] = None,
        filter: Optional[str] = None,
        transform: Optional[str] = None
    ) -> bytes:
        """Process raster tile with advanced features"""
        try:
            # Get data for bounds
            data = await self._get_data(bounds, time)
            
            # Apply filters if specified
            if filter:
                data = self._apply_filter(data, filter)
            
            # Apply transformations if specified
            if transform:
                data = self._apply_transformation(data, transform)
            
            # Apply styling if specified
            if style:
                data = self._apply_style(data, style)
            
            # Convert to requested format
            return self._to_format(data, format)
            
        except Exception as e:
            raise Exception(f"Error processing raster tile: {str(e)}")
    
    async def _get_data(
        self,
        bounds: mercantile.Bounds,
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
    
    def _apply_filter(
        self,
        data: xr.DataArray,
        filter: str
    ) -> xr.DataArray:
        """Apply raster filters"""
        if filter == 'cloud_mask':
            # Apply cloud masking
            return data.where(data > 0)
        elif filter == 'nodata_mask':
            # Mask nodata values
            return data.where(data != data.attrs.get('nodata', None))
        elif filter.startswith('threshold:'):
            # Apply threshold
            threshold = float(filter.split(':')[1])
            return data.where(data > threshold)
        return data
    
    def _apply_transformation(
        self,
        data: xr.DataArray,
        transform: str
    ) -> xr.DataArray:
        """Apply raster transformations"""
        if transform == 'normalize':
            # Normalize to 0-1 range
            return (data - data.min()) / (data.max() - data.min())
        elif transform == 'hillshade':
            # Calculate hillshade
            return self._calculate_hillshade(data)
        elif transform.startswith('resample:'):
            # Resample to new resolution
            method = transform.split(':')[1]
            return data.coarsen(
                x=2, y=2,
                boundary='trim'
            ).mean() if method == 'mean' else data
        return data
    
    def _apply_style(
        self,
        data: xr.DataArray,
        style: str
    ) -> xr.DataArray:
        """Apply styling rules"""
        style_config = self.styles.get(style, {})
        if not style_config:
            return data
            
        # Apply colormap
        if 'colormap' in style_config:
            return self._apply_colormap(data, style_config['colormap'])
            
        # Apply band combination
        if 'bands' in style_config:
            return self._apply_band_combination(data, style_config['bands'])
            
        return data
    
    def _to_format(
        self,
        data: xr.DataArray,
        format: str
    ) -> bytes:
        """Convert to requested format"""
        # Convert to numpy array
        arr = data.values
        
        # Scale to 0-255 range
        arr = ((arr - arr.min()) * (255 / (arr.max() - arr.min()))).astype(np.uint8)
        
        # Create PIL image
        img = Image.fromarray(arr)
        
        # Save to bytes
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format=format.upper())
        img_byte_arr.seek(0)
        
        return img_byte_arr.getvalue()
    
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
    
    def _apply_band_combination(
        self,
        data: xr.DataArray,
        bands: List[int]
    ) -> xr.DataArray:
        """Apply band combination"""
        return data.isel(band=bands)
    
    def available_styles(self) -> Dict[str, Any]:
        """Get available styles"""
        return self.styles
    
    def available_transformations(self) -> List[str]:
        """Get available transformations"""
        return list(self.transformations.keys())
    
    def available_filters(self) -> List[str]:
        """Get available filters"""
        return list(self.filters.keys())
    
    def _load_styles(self) -> Dict[str, Any]:
        """Load style configurations"""
        style_path = Path(__file__).parent / 'styles'
        styles = {}
        for style_file in style_path.glob('*.json'):
            with open(style_file) as f:
                styles[style_file.stem] = json.load(f)
        return styles
    
    def _load_transformations(self) -> Dict[str, Any]:
        """Load transformation configurations"""
        return {
            'normalize': 'Normalize values to 0-1 range',
            'hillshade': 'Calculate hillshade',
            'resample:mean': 'Resample using mean',
            'resample:nearest': 'Resample using nearest neighbor'
        }
    
    def _load_filters(self) -> Dict[str, Any]:
        """Load filter configurations"""
        return {
            'cloud_mask': 'Mask clouds',
            'nodata_mask': 'Mask nodata values',
            'threshold': 'Apply threshold'
        }
    
    def _init_database(self) -> duckdb.DuckDBPyConnection:
        """Initialize DuckDB database"""
        db = duckdb.connect(':memory:')
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