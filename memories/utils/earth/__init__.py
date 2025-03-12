"""
Earth module for handling geographic and spatial data.
"""

from memories.utils.earth.location_processing import (
    filter_by_distance,
    filter_by_type,
    sort_by_distance,
    geocode,
    reverse_geocode
)
from memories.utils.earth.processors import ImageProcessor, VectorProcessor
from memories.utils.earth.analysis_utils import (
    calculate_ndvi,
    analyze_vegetation,
    analyze_urban_patterns,
    analyze_change,
    generate_report,
    detect_changes,
    vectorize_raster,
    smooth_timeseries,
    calculate_area_statistics
)
from memories.utils.earth.location_utils import (
    normalize_location,
    is_valid_coordinates
)
from memories.utils.earth.advanced_analysis import AdvancedAnalysis

__all__ = [
    'filter_by_distance',
    'filter_by_type',
    'sort_by_distance',
    'geocode',
    'reverse_geocode',
    'ImageProcessor',
    'VectorProcessor',
    'calculate_ndvi',
    'analyze_vegetation',
    'analyze_urban_patterns',
    'analyze_change',
    'generate_report',
    'detect_changes',
    'vectorize_raster',
    'smooth_timeseries',
    'calculate_area_statistics',
    'normalize_location',
    'is_valid_coordinates',
    'AdvancedAnalysis'
]
