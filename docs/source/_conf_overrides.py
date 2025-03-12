"""
Configuration overrides for Sphinx to handle import issues.
This file is imported by conf.py to provide mock modules.
"""

import sys
import os
from unittest.mock import MagicMock

# Define a mock class with __type_params__ to avoid errors
class MockClass(MagicMock):
    __type_params__ = tuple()
    
    @classmethod
    def from_pretrained(cls, *args, **kwargs):
        return cls()

# Create data directories
data_dirs = [
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data'),
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data/models'),
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data/cache'),
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config'),
]
for d in data_dirs:
    os.makedirs(d, exist_ok=True)

# Create mock modules that are problematic
MOCK_MODULES = [
    'diffusers',
    'diffusers.pipelines',
    'diffusers.pipelines.stable_diffusion',
    'diffusers.pipelines.stable_diffusion.pipeline_stable_diffusion',
    'diffusers.loaders',
    'diffusers.loaders.single_file',
    'memories.utils.earth',
    'memories.utils.earth.advanced_analysis',
    'memories.utils.types',
    'mercantile',
    'pyproj',
    'shapely',
    'shapely.geometry',
]

for mod_name in MOCK_MODULES:
    if mod_name in ('diffusers.pipelines.stable_diffusion.pipeline_stable_diffusion', 'diffusers.loaders.single_file'):
        sys.modules[mod_name] = MockClass()
    else:
        sys.modules[mod_name] = MagicMock()

# Set special attributes on mock modules
sys.modules['diffusers'].__version__ = '0.25.0'
if 'Bounds' not in dir(sys.modules['memories.utils.types']):
    sys.modules['memories.utils.types'].Bounds = type('Bounds', (), {}) 