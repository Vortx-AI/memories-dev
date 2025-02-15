"""
Test script to verify memories-dev package installation.
"""

import pytest
import importlib.util

def test_package_installed():
    """Test that the package is installed and can be imported as 'memories'."""
    assert importlib.util.find_spec("memories") is not None

def test_core_imports():
    """Test that core components can be imported."""
    from memories import MemoryStore, Config
    from memories.core import HotMemory, WarmMemory, ColdMemory, GlacierMemory
    
    assert all(x is not None for x in [
        MemoryStore, Config, HotMemory, WarmMemory, ColdMemory, GlacierMemory
    ])

def test_version():
    """Test that version is properly set."""
    from memories import __version__
    assert isinstance(__version__, str)
    assert len(__version__.split(".")) == 3  # Should be in format x.y.z

def test_cli():
    """Test that CLI is properly installed."""
    import memories.cli
    assert hasattr(memories.cli, "main")
    
if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 