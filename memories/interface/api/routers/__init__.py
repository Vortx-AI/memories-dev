"""
Mock API routers module for documentation build.

This module provides mock objects for the memories.interface.api.routers module
to allow documentation to be built without requiring all dependencies.
"""

# Import statements needed for proper module resolution
import sys
from unittest.mock import MagicMock

# Create mock modules to prevent import errors
for mod_name in [
    'memories.interface.api.routers.memory',
    'memories.interface.api.routers.text',
    'memories.interface.api.routers.image',
    'memories.interface.api.routers.video',
]:
    sys.modules[mod_name] = MagicMock()

# Export mock router components
memory_router = MagicMock()
text_router = MagicMock()
image_router = MagicMock()
video_router = MagicMock() 