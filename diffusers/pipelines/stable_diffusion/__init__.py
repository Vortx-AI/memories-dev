"""
Mock stable diffusion pipeline module for documentation build.

This module provides mock objects for the diffusers.pipelines.stable_diffusion module
to allow documentation to be built without requiring all dependencies.
"""

# Import statements needed for proper module resolution
import sys
from unittest.mock import MagicMock

# Create mock modules to prevent import errors
sys.modules['diffusers.pipelines.stable_diffusion.pipeline_stable_diffusion'] = MagicMock()

# Export mock components
from .pipeline_stable_diffusion import StableDiffusionPipeline 