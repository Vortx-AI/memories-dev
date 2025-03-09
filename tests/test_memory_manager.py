"""Tests for MemoryManager functionality."""

import pytest
import os
import duckdb
import yaml
import faiss
import redis
import boto3
import numpy as np
from unittest.mock import patch, MagicMock
from memories.core.memory_manager import MemoryManager
from memories.core.glacier.artifacts.sentinel import SentinelConnector
from memories.core.glacier.artifacts.landsat import LandsatConnector
from memories.core.glacier.artifacts.planetary import PlanetaryConnector
from memories.core.glacier.artifacts.osm import OSMConnector
from memories.core.glacier.artifacts.overture import OvertureConnector
from memories.core.cold import ColdMemory

@pytest.fixture
def mock_all():
    """Mock all external dependencies."""
    redis_mock = MagicMock()
    boto3_mock = MagicMock()
    cold_mock = MagicMock()
    cold_instance = MagicMock()
    cold_mock.return_value = cold_instance
    
    with patch('redis.from_url', return_value=redis_mock) as redis_patch, \
         patch('boto3.client', return_value=boto3_mock) as boto3_patch, \
         patch('memories.core.cold.ColdMemory', return_value=cold_instance) as cold_patch:
        
        # Ensure the mocks are used when initializing the MemoryManager
        MemoryManager._instance = None  # Reset singleton
        manager = MemoryManager()
        
        # Replace the actual instances with mocks
        manager._redis_client = redis_mock
        manager._s3_client = boto3_mock
        manager._cold_memory = cold_instance
        
        yield {
            'redis': redis_mock,
            'boto3': boto3_mock,
            'cold': cold_mock
        }

@pytest.fixture
def test_config():
    """Create test configuration."""
    base_path = os.path.join(os.getcwd(), 'data', 'memory')
    return {
        'memory': {
            'base_path': base_path,
            'red_hot': {
                'path': 'red_hot',
                'index_type': 'Flat',
                'use_gpu': False
            },
            'hot': {
                'path': 'hot',
                'redis_url': 'redis://localhost:6379',
                'redis_db': 0
            },
            'cold': {
                'path': 'cold',
                'duckdb': {
                    'memory_limit': '4.0 GiB'
                }
            },
            'glacier': {
                'path': 'glacier',
                'storage': {
                    'type': 's3',
                    'bucket': 'test-bucket',
                    'region': 'us-west-2',
                    'credentials': {
                        'aws_access_key_id': 'test_key',
                        'aws_secret_access_key': 'test_secret'
                    }
                }
            }
        },
        'data': {
            'cache': os.path.join(os.getcwd(), 'data', 'cache'),
            'storage': os.path.join(os.getcwd(), 'data', 'storage')
        }
    }

@pytest.fixture
def memory_manager(mock_all):
    """Create memory manager instance with mocked dependencies."""
    return MemoryManager()

def test_singleton_pattern():
    """Test singleton pattern."""
    manager1 = MemoryManager()
    manager2 = MemoryManager()
    assert manager1 is manager2

def test_config_loading(memory_manager, test_config):
    """Test configuration loading and override."""
    assert memory_manager.config['memory']['base_path'] == test_config['memory']['base_path']

def test_path_initialization(memory_manager, test_config):
    """Test path initialization."""
    # Check that base path exists
    base_path = test_config['memory']['base_path']
    assert os.path.exists(base_path)
    
    # Check that tier paths exist
    for tier in ['red_hot', 'hot', 'cold', 'glacier']:
        tier_path = os.path.join(base_path, test_config['memory'][tier]['path'])
        assert os.path.exists(tier_path)

def test_faiss_initialization(memory_manager):
    """Test FAISS initialization."""
    # Get FAISS index
    index = memory_manager.get_faiss_index()
    assert index is not None

def test_redis_initialization(memory_manager, mock_all):
    """Test Redis initialization for hot tier."""
    # Get hot tier backend
    redis_client = memory_manager.get_storage_backend('hot')
    assert redis_client is mock_all['redis']

def test_glacier_storage_initialization(memory_manager, mock_all):
    """Test glacier storage initialization."""
    # Get glacier tier backend
    s3_client = memory_manager.get_storage_backend('glacier')
    assert s3_client is mock_all['boto3']

def test_invalid_storage_backend(memory_manager):
    """Test invalid storage backend."""
    with pytest.raises(ValueError):
        memory_manager.get_storage_backend('invalid')

def test_invalid_faiss_index(memory_manager):
    """Test invalid FAISS index type."""
    memory_manager.config['memory']['red_hot']['index_type'] = 'Invalid'
    with pytest.raises(ValueError):
        memory_manager.get_faiss_index()

def test_duckdb_initialization(memory_manager):
    """Test DuckDB initialization."""
    # Get DuckDB connection
    con = memory_manager.get_duckdb_connection()
    assert isinstance(con, duckdb.DuckDBPyConnection)

    # Test basic query
    result = con.execute("SELECT 1").fetchone()[0]
    assert result == 1

    # Test configuration
    cold_config = memory_manager.config['memory']['cold']['duckdb']
    expected_memory_limit = cold_config['memory_limit']

    # Get actual memory limit and normalize format
    memory_limit = con.execute("SELECT current_setting('memory_limit')").fetchone()[0]
    if memory_limit.endswith('GiB') and expected_memory_limit.endswith('GB'):
        # Convert GB to GiB for comparison
        expected_value = float(expected_memory_limit[:-2])
        actual_value = float(memory_limit[:-4])
        assert abs(actual_value - expected_value) < 0.1  # Allow small difference due to conversion
    else:
        assert memory_limit == expected_memory_limit

def test_cleanup(memory_manager, tmp_path):
    """Test cleanup functionality."""
    # Create test files
    test_file = os.path.join(memory_manager.config['data']['storage'], "test.txt")
    test_file_parent = os.path.dirname(test_file)
    os.makedirs(test_file_parent, exist_ok=True)
    with open(test_file, 'w') as f:
        f.write("test")

    # Cleanup
    memory_manager.cleanup_cold_memory(remove_storage=True)

    # Check storage directory is removed
    assert not os.path.exists(test_file)
    assert not os.path.exists(test_file_parent)

@pytest.mark.asyncio
async def test_async_operations(memory_manager):
    """Test async operations with connectors."""
    # Create connectors
    sentinel = memory_manager.get_connector('sentinel', store_in_cold=True)
    assert sentinel is not None

def test_cold_memory_initialization(memory_manager, mock_all):
    """Test cold memory initialization."""
    # Get cold memory
    cold = memory_manager.get_cold_memory()
    assert cold is not None
    assert cold is mock_all['cold'].return_value

def test_cleanup_cold_memory(memory_manager, mock_all):
    """Test cold memory cleanup."""
    # Setup mock cold memory
    cold = memory_manager.get_cold_memory()
    assert cold is mock_all['cold'].return_value

    # Call cleanup
    memory_manager.cleanup_cold_memory(remove_storage=True)
    assert cold.cleanup.called 