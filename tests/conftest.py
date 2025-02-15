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
    config.addinivalue_line(
        "markers",
        "gpu: mark test as requiring GPU support"
    )
    config.addinivalue_line(
        "markers",
        "earth: mark test as using earth-related functionality"
    )
    config.addinivalue_line(
        "markers",
        "async_test: mark test as using async/await"
    )

def has_gpu_support():
    try:
        import cudf
        return True
    except ImportError:
        return False

def pytest_collection_modifyitems(config, items):
    skip_gpu = pytest.mark.skip(reason="GPU support not available")
    
    for item in items:
        if "gpu" in item.keywords and not has_gpu_support():
            item.add_marker(skip_gpu) 