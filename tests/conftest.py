import pytest
import os
import sys

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

# Configure pytest
def pytest_configure(config):
    """Configure pytest"""
    # Register markers
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    ) 