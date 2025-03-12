"""
Pre-import configuration for Sphinx documentation.

This script is imported at the very beginning of conf.py before any other imports.
It sets up mocks and environment variables to ensure the documentation build succeeds.
"""

import os
import sys
import types

# Set environment variables
os.environ['DISABLE_DIFFUSERS'] = '1'

# Add parent directory to path so we can import our mock_diffusers
sys.path.insert(0, os.path.abspath('../..'))

# Create a simple mock for diffusers in case mock_diffusers.py fails
class MockModule:
    """Simple mock module that raises ImportError for any attribute access."""
    
    def __init__(self, name):
        self.__name__ = name
        self.__all__ = []
        self.__path__ = []
        self.__file__ = __file__
        
    def __getattr__(self, name):
        """Raise ImportError for any attribute access."""
        raise ImportError(
            f"The {self.__name__}.{name} module is not available. "
            "This is a mock module created for documentation builds."
        )

# Create mock diffusers module
sys.modules['diffusers'] = MockModule('diffusers')

# Create common submodules
for submodule in [
    'diffusers.loaders',
    'diffusers.models',
    'diffusers.pipelines',
    'diffusers.schedulers',
    'diffusers.utils',
]:
    sys.modules[submodule] = MockModule(submodule)

# Try to import the more sophisticated mock_diffusers
try:
    import mock_diffusers
    mock_diffusers.setup_mock_diffusers()
    print('Successfully loaded mock_diffusers module')
except Exception as e:
    print(f'Error loading mock_diffusers module: {e}')
    print('Using simple mock module instead')

# Add diffusers to autodoc_mock_imports
autodoc_mock_imports = [
    "diffusers",
    "diffusers.loaders",
    "diffusers.loaders.single_file",
    "diffusers.pipelines",
    "diffusers.models",
    "diffusers.schedulers",
    "diffusers.utils",
]

# Print confirmation
print("Pre-import configuration completed successfully") 