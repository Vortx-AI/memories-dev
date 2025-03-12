"""
Mock utils module for documentation build.

This module provides mock utilities for the memories.utils module
to allow documentation to be built without requiring all dependencies.
"""

import os
import sys
from unittest.mock import MagicMock

# Create mock data paths
DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
MODEL_PATH = os.path.join(DATA_PATH, 'models')
CACHE_PATH = os.path.join(DATA_PATH, 'cache')
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config')

# Ensure directories exist in the mock environment
os.makedirs(DATA_PATH, exist_ok=True)
os.makedirs(MODEL_PATH, exist_ok=True)
os.makedirs(CACHE_PATH, exist_ok=True)
os.makedirs(CONFIG_PATH, exist_ok=True)

# Create mock submodules only when BUILD_DOCUMENTATION is true (for documentation builds)
if os.getenv("BUILD_DOCUMENTATION", "false").lower() == "true":
    sys.modules['memories.utils.types'] = MagicMock()
    sys.modules['memories.utils.earth'] = MagicMock()
    sys.modules['memories.utils.earth.advanced_analysis'] = MagicMock()

from .text import *

from .types import *
