"""
Mock diffusers module for documentation builds.

This module creates a mock structure that mimics the diffusers package
but raises ImportError when any actual functionality is imported.
This prevents documentation builds from failing due to missing dependencies.
"""

import os
import sys
import types

class MockDiffusers:
    """Mock class for diffusers package."""
    
    def __init__(self):
        self.__all__ = []
        self.__path__ = []
        self.__file__ = __file__
        self.__name__ = "diffusers"
        
    def __getattr__(self, name):
        """Raise ImportError for any attribute access."""
        raise ImportError(
            f"The diffusers.{name} module is not available. "
            "This is a mock module created for documentation builds."
        )

def setup_mock_diffusers():
    """Set up mock diffusers module in sys.modules."""
    # Create the mock module
    mock_diffusers = MockDiffusers()
    
    # Add it to sys.modules
    sys.modules['diffusers'] = mock_diffusers
    
    # Create common submodules
    for submodule in [
        'diffusers.loaders',
        'diffusers.models',
        'diffusers.pipelines',
        'diffusers.schedulers',
        'diffusers.utils',
    ]:
        sys.modules[submodule] = types.ModuleType(submodule)
        setattr(sys.modules[submodule], '__file__', __file__)
        setattr(sys.modules[submodule], '__path__', [])
        setattr(sys.modules[submodule], '__package__', submodule)
        
        # Make any attribute access raise ImportError
        def get_attr_raiser(submodule_name):
            def __getattr__(name):
                raise ImportError(
                    f"The {submodule_name}.{name} module is not available. "
                    "This is a mock module created for documentation builds."
                )
            return __getattr__
            
        setattr(sys.modules[submodule], '__getattr__', get_attr_raiser(submodule))
    
    print("Mock diffusers module has been set up successfully.")
    return mock_diffusers

if __name__ == "__main__":
    # If run directly, set up the mock module
    setup_mock_diffusers() 