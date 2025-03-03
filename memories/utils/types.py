"""
Common type definitions used across the memories package.
"""

from typing import TypedDict, Union, List, Dict, Any, Tuple
from dataclasses import dataclass
import numpy as np

@dataclass
class Bounds:
    """Geographic bounds."""
    north: float
    south: float
    east: float
    west: float
    
    @property
    def as_tuple(self) -> Tuple[float, float, float, float]:
        """Return bounds as (north, south, east, west) tuple."""
        return (self.north, self.south, self.east, self.west)
    
    @property
    def as_dict(self) -> Dict[str, float]:
        """Return bounds as dictionary."""
        return {
            'north': self.north,
            'south': self.south,
            'east': self.east,
            'west': self.west
        }

# Image types
ImageType = Union[np.ndarray, List[np.ndarray]]
RasterType = np.ndarray
VectorType = Dict[str, Any]  # GeoJSON-like structure 