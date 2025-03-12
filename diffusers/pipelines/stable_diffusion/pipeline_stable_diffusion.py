"""
Mock stable diffusion pipeline implementation for documentation build.

This module provides mock objects for the diffusers.pipelines.stable_diffusion.pipeline_stable_diffusion module
to allow documentation to be built without requiring all dependencies.
"""

from unittest.mock import MagicMock

class StableDiffusionPipeline(MagicMock):
    """Mock stable diffusion pipeline class."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    @classmethod
    def from_pretrained(cls, *args, **kwargs):
        """Mock from_pretrained method."""
        return cls()
    
    def __call__(self, *args, **kwargs):
        """Mock pipeline call."""
        return {"images": [MagicMock()], "nsfw_content_detected": [False]}
    
    def to(self, *args, **kwargs):
        """Mock to method."""
        return self 