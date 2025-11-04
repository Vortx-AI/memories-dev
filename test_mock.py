#!/usr/bin/env python
"""Test script for mock setup."""
import os
import sys
from unittest.mock import MagicMock

# Create a custom mock class with type_params
class TypedMock(MagicMock):
    @property
    def __type_params__(self):
        return tuple()

# Test mock modules
MOCK_MODULES = [
    'diffusers', 'diffusers.pipelines', 'diffusers.pipelines.stable_diffusion',
    'diffusers.loaders', 'diffusers.loaders.single_file', 'torch', 'transformers'
]

for mod_name in MOCK_MODULES:
    if 'single_file' in mod_name:
        sys.modules[mod_name] = TypedMock()
    else:
        sys.modules[mod_name] = MagicMock()
    
print("Mock setup complete")

# Test importing a mocked module
try:
    import diffusers
    print(f"Successfully imported diffusers, version: {getattr(diffusers, '__version__', 'unknown')}")
except Exception as e:
    print(f"Error importing diffusers: {e}")

# Test the type_params attribute
try:
    import diffusers.loaders.single_file
    type_params = diffusers.loaders.single_file.__type_params__
    print(f"Successfully accessed __type_params__: {type_params}")
    print(f"Type of __type_params__: {type(type_params)}")
except Exception as e:
    print(f"Error accessing __type_params__: {e}") 