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
class StableDiffusionPipeline:
    """Mock StableDiffusionPipeline class."""
    
    @classmethod
    def from_pretrained(cls, *args, **kwargs):
        """Mock from_pretrained method."""
        return cls()
    
    def __call__(self, *args, **kwargs):
        """Mock pipeline call."""
        return {"images": [], "nsfw_content_detected": [False]}
    
    def to(self, *args, **kwargs):
        """Mock to method."""
        return self

# Export mock components
pipeline = StableDiffusionPipeline 