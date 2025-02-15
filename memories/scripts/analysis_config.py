"""
Configuration settings for analysis operations.
"""

from typing import Dict, Any

# Vegetation analysis settings
VEGETATION_CONFIG = {
    'ndvi_threshold': 0.3,
    'min_coverage': 0.1,
    'max_cloud_cover': 0.2,
    'temporal_window': 30,  # days
    'smoothing_window': 5
}

# Urban analysis settings
URBAN_CONFIG = {
    'building_density_threshold': 0.4,
    'road_density_threshold': 0.2,
    'min_building_size': 50,  # square meters
    'buffer_distance': 100,  # meters
    'cluster_distance': 50  # meters
}

# Change detection settings
CHANGE_CONFIG = {
    'change_threshold': 0.2,
    'min_area': 1000,  # square meters
    'temporal_window': 365,  # days
    'confidence_threshold': 0.8,
    'noise_removal_kernel': 3
}

# Processing settings
PROCESSING_CONFIG = {
    'tile_size': 256,
    'overlap': 32,
    'batch_size': 8,
    'num_workers': 4,
    'use_gpu': True
}

# Output settings
OUTPUT_CONFIG = {
    'formats': ['geojson', 'shapefile', 'csv'],
    'compression': True,
    'include_metadata': True,
    'save_intermediates': False
}

def get_config(analysis_type: str) -> Dict[str, Any]:
    """
    Get configuration for specific analysis type.
    
    Args:
        analysis_type: Type of analysis
        
    Returns:
        Configuration dictionary
    """
    configs = {
        'vegetation': VEGETATION_CONFIG,
        'urban': URBAN_CONFIG,
        'change': CHANGE_CONFIG,
        'processing': PROCESSING_CONFIG,
        'output': OUTPUT_CONFIG
    }
    
    return configs.get(analysis_type, {}) 