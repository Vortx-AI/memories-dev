#!/usr/bin/env python
"""Simple mock setup for ReadTheDocs."""
import os
import sys
from unittest.mock import MagicMock

# Create directories
os.makedirs('data/models', exist_ok=True)
os.makedirs('data/cache', exist_ok=True)
os.makedirs('config', exist_ok=True)

# Create mock config
if not os.path.exists('config/db_config.yml'):
    with open('config/db_config.yml', 'w') as f:
        f.write('# Mock config\ndatabases:\n  memory_store:\n    host: localhost\n')

# Create a special mock for diffusers.loaders.single_file
class SingleFileMock(MagicMock):
    pass

# Add __type_params__ as a class attribute (not an instance attribute)
SingleFileMock.__type_params__ = tuple()

# Mock modules
MOCK_MODULES = [
    'diffusers',
    'diffusers.pipelines',
    'diffusers.pipelines.stable_diffusion',
    'diffusers.loaders',
    'torch',
    'transformers',
    'sentence_transformers',
    'memories.utils.earth',
    'memories.utils.types',
    'mercantile',
    'pyproj',
    'shapely',
    'shapely.geometry'
]

# Create all mock modules
for mod_name in MOCK_MODULES:
    sys.modules[mod_name] = MagicMock()

# Special handling for the problematic module
sys.modules['diffusers.loaders.single_file'] = SingleFileMock()

# Set version for diffusers
sys.modules['diffusers'].__version__ = '0.25.0'

print("Mock setup complete")

# Test the setup
try:
    import diffusers.loaders.single_file
    print(f"diffusers.loaders.single_file.__type_params__: {diffusers.loaders.single_file.__type_params__}")
except Exception as e:
    print(f"Error: {e}") 