"""
Mock diffusers package for documentation build.

This module provides mock objects for the diffusers package
to allow documentation to be built without requiring all dependencies.
"""

__version__ = "0.25.0"  # Mock version

# Set up mock modules for docs
import sys
from unittest.mock import MagicMock

# Create mock classes and modules
class MockPipeline:
    """Mock pipeline class"""
    
    def __init__(self, *args, **kwargs):
        """Initialize mock pipeline"""
        pass
    
    def __call__(self, *args, **kwargs):
        """Mock pipeline call"""
        return MagicMock()
    
    @classmethod
    def from_pretrained(cls, *args, **kwargs):
        """Mock from_pretrained method"""
        return cls()

# Export mock components
pipeline = MockPipeline
StableDiffusionPipeline = MockPipeline 