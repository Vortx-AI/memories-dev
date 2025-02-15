"""
Common type definitions for the memories package.
"""

from typing import Union, Tuple, TypeVar, Any
import mercantile

# Type alias for bounds that can be either a tuple of coordinates or a mercantile.LngLatBbox
Bounds = Union[Tuple[float, float, float, float], mercantile.LngLatBbox]

# Type alias for image data (numpy array)
ImageType = Any  # numpy.ndarray but avoid import

# Type alias for raster data
RasterType = Any  # Dict with data, transform, and crs but avoid complex imports

# Generic type variable for vector data
VectorType = TypeVar('VectorType')  # Typically geopandas.GeoDataFrame but avoid import

__all__ = [
    'Bounds',
    'ImageType',
    'RasterType',
    'VectorType'
] 