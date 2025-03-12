#!/usr/bin/env python
"""
Setup script for mock packages required for ReadTheDocs documentation build.
This script installs mock versions of dependencies that aren't available or cause problems.
"""

import os
import sys
import site
import importlib.util
from pathlib import Path
from unittest.mock import MagicMock


def create_module_file(path, content):
    """Create a module file with the given content."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(content)
    print(f"Created mock module: {path}")


def ensure_directories():
    """Ensure necessary directories exist."""
    dirs = [
        'data',
        'data/models',
        'data/cache',
        'data/datasets',
        'config'
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        print(f"Ensured directory exists: {d}")


def create_mock_config():
    """Create mock configuration files."""
    if not os.path.exists('config/db_config.yml'):
        with open('config/db_config.yml', 'w') as f:
            f.write('''# Mock database configuration for ReadTheDocs build
databases:
  memory_store:
    host: localhost
    port: 5432
    user: mock_user
    password: mock_password
    database: memory_store
  vector_db:
    host: localhost
    port: 6333
    collection: memories
''')
        print("Created mock db_config.yml")


def ensure_doc_directories():
    """Ensure documentation directories exist."""
    dirs = [
        'docs/source/getting_started',
        'docs/source/_templates',
        'docs/source/algorithms',
        'docs/source/api_reference'
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        print(f"Ensured doc directory exists: {d}")


def setup_mock_modules():
    """Set up mock modules for problematic imports."""
    # Define mock class with type_params
    class MockClass(MagicMock):
        __type_params__ = tuple()
        
        @classmethod
        def from_pretrained(cls, *args, **kwargs):
            return cls()
    
    # Create list of modules to mock
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
        'torch',
        'transformers',
        'sentence_transformers'
    ]
    
    # Mock all modules
    for mod_name in MOCK_MODULES:
        if mod_name in ('diffusers.pipelines.stable_diffusion.pipeline_stable_diffusion', 'diffusers.loaders.single_file'):
            sys.modules[mod_name] = MockClass()
        else:
            sys.modules[mod_name] = MagicMock()
    
    # Set special attributes on mock modules
    if 'diffusers' in sys.modules:
        sys.modules['diffusers'].__version__ = '0.25.0'
    
    if 'memories.utils.types' in sys.modules and 'Bounds' not in dir(sys.modules['memories.utils.types']):
        sys.modules['memories.utils.types'].Bounds = type('Bounds', (), {})
    
    print("Set up mock modules for documentation build")


def main():
    """Main entry point."""
    print("Setting up mock packages for ReadTheDocs build...")
    
    # Set up directories
    ensure_directories()
    ensure_doc_directories()
    
    # Create mock configuration
    create_mock_config()
    
    # Set up mock modules
    setup_mock_modules()
    
    print("Mock packages setup complete!")


if __name__ == "__main__":
    main() 