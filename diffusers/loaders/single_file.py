"""
Mock single file loader module for documentation.

This module provides mock objects for the diffusers.loaders.single_file module
to allow documentation to be built without requiring all dependencies.
"""

from unittest.mock import MagicMock

class SingleFileLoader:
    """Mock single file loader class."""
    __type_params__ = tuple()
    
    def __init__(self, *args, **kwargs):
        """Initialize the mock loader."""
        pass
    
    def load(self, *args, **kwargs):
        """Mock load method."""
        return {}
    
    def save(self, *args, **kwargs):
        """Mock save method."""
        pass

# Export mock functions
def load_file(*args, **kwargs):
    """Mock load_file function."""
    return {}

def save_file(*args, **kwargs):
    """Mock save_file function."""
    pass 