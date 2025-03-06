import pytest
import os
import sys
from typing import Dict, Any
from dotenv import load_dotenv

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

# Load environment variables from .env file
load_dotenv()

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

@pytest.fixture(scope="session")
def gcp_credentials() -> Dict[str, str]:
    """Fixture for GCP credentials"""
    return {
        "project_id": os.getenv("GCP_PROJECT_ID"),
        "credentials_path": os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    }

@pytest.fixture(scope="session")
def aws_credentials() -> Dict[str, str]:
    """Fixture for AWS credentials"""
    return {
        "aws_access_key_id": os.getenv("AWS_ACCESS_KEY_ID"),
        "aws_secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
        "region": os.getenv("AWS_DEFAULT_REGION", "us-west-2")
    }

@pytest.fixture(scope="session")
def azure_credentials() -> Dict[str, str]:
    """Fixture for Azure credentials"""
    return {
        "subscription_id": os.getenv("AZURE_SUBSCRIPTION_ID"),
        "tenant_id": os.getenv("AZURE_TENANT_ID"),
        "client_id": os.getenv("AZURE_CLIENT_ID"),
        "client_secret": os.getenv("AZURE_CLIENT_SECRET")
    }

@pytest.fixture(scope="session")
def test_output_dir() -> str:
    """Fixture for test output directory"""
    output_dir = os.path.join(os.path.dirname(__file__), "test-results")
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

@pytest.fixture(scope="session")
def deployments_dir() -> str:
    """Fixture for deployments directory"""
    return os.path.join(os.path.dirname(__file__), "..", "deployments")

@pytest.fixture(scope="function")
def temp_test_dir(tmp_path) -> str:
    """Fixture for temporary test directory"""
    return str(tmp_path)

@pytest.fixture(scope="session")
def test_data_dir() -> str:
    """Fixture for test data directory"""
    return os.path.join(os.path.dirname(__file__), "test_data") 