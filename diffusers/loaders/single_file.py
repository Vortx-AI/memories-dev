"""
Mock single file loader module for documentation build.

This module provides mock objects for the diffusers.loaders.single_file module
to allow documentation to be built without requiring all dependencies.
"""

from unittest.mock import MagicMock

# Fix for the __type_params__ error
class SingleFileLoader(MagicMock):
    """Mock single file loader class."""
    __type_params__ = tuple()
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

# Export mock components
load_file = MagicMock()
save_file = MagicMock() 