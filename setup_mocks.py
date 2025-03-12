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


def create_module_file(path, content):
    """Create a module file with the given content."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(content)
    print(f"Created mock module: {path}")


def setup_diffusers_mock():
    """Set up mock diffusers package."""
    # Determine the site-packages directory
    site_packages = site.getsitepackages()[0]
    diffusers_dir = os.path.join(site_packages, 'diffusers')
    
    # Check if the real package exists
    if importlib.util.find_spec('diffusers') is not None:
        print("Real diffusers package exists, not creating mock.")
        return
    
    # Create the diffusers package directory structure
    os.makedirs(os.path.join(diffusers_dir, 'pipelines', 'stable_diffusion'), exist_ok=True)
    os.makedirs(os.path.join(diffusers_dir, 'loaders'), exist_ok=True)
    
    # Create __init__.py files
    create_module_file(os.path.join(diffusers_dir, '__init__.py'), '''"""
Mock diffusers package for documentation build.
"""
__version__ = "0.25.0"  # Mock version

from unittest.mock import MagicMock
import sys

class MockPipeline(MagicMock):
    """Mock pipeline class with proper type parameters."""
    __type_params__ = tuple()
    
    @classmethod
    def from_pretrained(cls, *args, **kwargs):
        """Mock from_pretrained method."""
        return cls()
    
    def __call__(self, *args, **kwargs):
        """Mock pipeline call."""
        return {"images": [MagicMock()], "nsfw_content_detected": [False]}

# Set up mock modules
sys.modules['diffusers.pipelines.stable_diffusion.pipeline_stable_diffusion'] = MockPipeline()
sys.modules['diffusers.loaders.single_file'] = MockPipeline()

# Export mock components
pipeline = MockPipeline
StableDiffusionPipeline = MockPipeline
''')

    create_module_file(os.path.join(diffusers_dir, 'pipelines', '__init__.py'), '"""Mock pipelines package."""')
    
    create_module_file(os.path.join(diffusers_dir, 'pipelines', 'stable_diffusion', '__init__.py'), '''"""
Mock stable_diffusion package.
"""
from unittest.mock import MagicMock

class StableDiffusionPipeline(MagicMock):
    """Mock StableDiffusionPipeline class."""
    __type_params__ = tuple()
''')
    
    create_module_file(os.path.join(diffusers_dir, 'loaders', '__init__.py'), '''"""
Mock loaders package.
"""
from unittest.mock import MagicMock

class SingleFileLoader(MagicMock):
    """Mock SingleFileLoader class."""
    __type_params__ = tuple()
''')

    create_module_file(os.path.join(diffusers_dir, 'loaders', 'single_file.py'), '''"""
Mock single_file module.
"""
from unittest.mock import MagicMock

# Fix for the __type_params__ error
class SingleFileLoader(MagicMock):
    """Mock SingleFileLoader class."""
    __type_params__ = tuple()

# Export mock components
load_file = MagicMock()
save_file = MagicMock()
''')


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


def main():
    """Main entry point."""
    print("Setting up mock packages for ReadTheDocs build...")
    
    # Set up directories
    ensure_directories()
    ensure_doc_directories()
    
    # Create mock configuration
    create_mock_config()
    
    # Set up mock packages
    setup_diffusers_mock()
    
    print("Mock packages setup complete!")


if __name__ == "__main__":
    main() 