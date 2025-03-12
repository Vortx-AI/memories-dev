import pytest
import os
import sys
from typing import Dict, Any
from dotenv import load_dotenv
import tempfile
import shutil
from pathlib import Path
import yaml

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

@pytest.fixture(scope="session")
def project_root():
    """Get the project root directory."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

@pytest.fixture(scope="session")
def test_config_dir(project_root):
    """Create a temporary config directory for tests."""
    # Use the actual config file as a base
    base_config_path = os.path.join(project_root, 'config', 'db_config.yml')
    
    # Create temp directory
    temp_dir = tempfile.mkdtemp()
    temp_config_dir = os.path.join(temp_dir, 'config')
    os.makedirs(temp_config_dir)
    
    # Copy and modify the config for testing
    test_config_path = os.path.join(temp_config_dir, 'db_config.yml')
    
    # Read the base config
    with open(base_config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Modify paths to use temp directory
    config['database']['path'] = os.path.join(temp_dir, 'data', 'db')
    config['data']['storage'] = os.path.join(temp_dir, 'data', 'storage')
    config['data']['models'] = os.path.join(temp_dir, 'data', 'models')
    config['data']['cache'] = os.path.join(temp_dir, 'data', 'cache')
    config['data']['raw_path'] = os.path.join(temp_dir, 'data', 'raw')
    config['memory']['base_path'] = os.path.join(temp_dir, 'data', 'memory')
    
    # Write the test config
    with open(test_config_path, 'w') as f:
        yaml.dump(config, f)
    
    # Set environment variable for tests
    os.environ['PROJECT_ROOT'] = temp_dir
    
    yield temp_dir
    
    # Cleanup
    try:
        shutil.rmtree(temp_dir)
    except Exception as e:
        print(f"Warning: Failed to clean up temporary directory {temp_dir}: {e}")

@pytest.fixture(scope="session")
def test_config_path(test_config_dir):
    """Get the path to the test config file."""
    return os.path.join(test_config_dir, 'config', 'db_config.yml') 