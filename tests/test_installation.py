"""
Test script to verify memories-dev package installation.
"""

import pytest
import importlib.util
from memories import MemoryManager
from memories.core import MemoryManager as CoreMemoryManager
import os
from unittest.mock import patch
from memories.core.config import Config

def test_package_installed():
    """Test that the package is installed and can be imported as 'memories'."""
    assert importlib.util.find_spec("memories") is not None

def test_core_imports():
    """Test importing core components."""
    from memories.core.memory_manager import MemoryManager
    assert MemoryManager is not None

def test_version():
    """Test that version is properly set."""
    from memories import __version__
    assert isinstance(__version__, str)
    assert len(__version__.split(".")) == 3  # Should be in format x.y.z

def test_cli():
    """Test CLI imports."""
    from memories.cli import cli
    assert cli is not None

def test_config_loading(test_config_path):
    """Test that the configuration can be loaded."""
    with patch.dict(os.environ, {'PROJECT_ROOT': os.path.dirname(os.path.dirname(test_config_path))}):
        config = Config(config_path=test_config_path)
        assert config is not None
        assert config.config is not None
        assert 'database' in config.config
        assert 'data' in config.config
        assert 'memory' in config.config

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 