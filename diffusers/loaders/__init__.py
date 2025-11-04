"""
Mock loaders module for documentation build.

This module provides mock objects for the diffusers.loaders module
to allow documentation to be built without requiring all dependencies.
"""

# Import statements needed for proper module resolution
import sys
from unittest.mock import MagicMock

# Create mock modules to prevent import errors
sys.modules['diffusers.loaders.single_file'] = MagicMock()

# Export mock components
from .single_file import SingleFileLoader

__all__ = ['SingleFileLoader'] 