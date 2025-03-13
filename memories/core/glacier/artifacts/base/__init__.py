"""
Base classes for glacier artifacts.

This module provides base classes and interfaces for glacier storage artifacts.
"""

# Import DataSource class from the parent directory's base.py
import sys
import os
import importlib.util
from pathlib import Path

# Get the path to base.py in the parent directory
base_py_path = Path(__file__).parent.parent / "base.py"

# Check if base.py exists in the parent directory
if base_py_path.exists():
    # Load the module dynamically
    spec = importlib.util.spec_from_file_location("base_module", base_py_path)
    base_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(base_module)
    
    # Import the DataSource class from the module
    DataSource = base_module.DataSource
else:
    # Provide a mock version if base.py doesn't exist
    class DataSource:
        """Base class for data source connectors."""
        
        def __init__(self, *args, **kwargs):
            """Initialize the data source."""
            pass
        
        def get_cache_path(self, *args, **kwargs):
            """Get cache path for a file."""
            pass
            
        def clear_cache(self):
            """Clear the cache directory."""
            pass
            
        def validate_bbox(self, *args, **kwargs):
            """Validate bounding box coordinates."""
            pass

class Artifact:
    """Base class for glacier artifacts."""
    
    def __init__(self, *args, **kwargs):
        """Initialize the artifact."""
        pass
    
    def store(self, *args, **kwargs):
        """Store the artifact in glacier storage."""
        pass
    
    def retrieve(self, *args, **kwargs):
        """Retrieve the artifact from glacier storage."""
        pass 