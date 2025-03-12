"""
Configuration overrides for Sphinx to handle import issues.
This file is imported by conf.py to provide mock modules.
"""

import sys
import os
from unittest.mock import MagicMock

# Create data directories
data_dirs = [
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data'),
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data/models'),
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data/cache'),
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config'),
]
for d in data_dirs:
    os.makedirs(d, exist_ok=True)

# Create a custom dictionary-based mock class
class DictBasedMock(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__ = self
        self.__type_params__ = tuple()
    
    def __getattr__(self, name):
        if name in self:
            return self[name]
        return MagicMock()

# Create mock modules that are problematic
MOCK_MODULES = [
    'diffusers',
    'diffusers.pipelines',
    'diffusers.pipelines.stable_diffusion',
    'diffusers.pipelines.stable_diffusion.pipeline_stable_diffusion',
    'diffusers.loaders',
    'memories.utils.earth',
    'memories.utils.earth.advanced_analysis',
    'memories.utils.types',
    'mercantile',
    'pyproj',
    'shapely',
    'shapely.geometry',
    'torch',
    'transformers',
    'sentence_transformers',
]

# Mock all modules
for mod_name in MOCK_MODULES:
    sys.modules[mod_name] = MagicMock()

# Special handling for the problematic module
sys.modules['diffusers.loaders.single_file'] = DictBasedMock()

# Set special attributes on mock modules
if 'diffusers' in sys.modules:
    sys.modules['diffusers'].__version__ = '0.25.0'

# Ensure Bounds type exists
if 'memories.utils.types' in sys.modules:
    sys.modules['memories.utils.types'].Bounds = type('Bounds', (), {}) 