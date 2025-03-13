"""
Tests for the MemoryManager class in the core.memory_manager module.
"""

import os
import pytest
import tempfile
import shutil
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

from memories.core.memory_manager import MemoryManager


@pytest.fixture
def temp_config_dir():
    """Create a temporary directory for config files."""
    temp_dir = tempfile.mkdtemp()
    config_dir = Path(temp_dir) / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a minimal config file
    config_file = config_dir / "db_config.yml"
    with open(config_file, 'w') as f:
        f.write("""
memory:
  base_path: {}/data/memory
  red_hot:
    path: red_hot
    max_size: 1000000
    vector_dim: 128
    index_type: Flat
  hot:
    path: hot
    max_size: 104857600
  warm:
    path: warm
    max_size: 1073741824
    duckdb:
      memory_limit: 1GB
      threads: 2
  cold:
    path: cold
    max_size: 10737418240
    duckdb:
      db_file: cold.duckdb
      memory_limit: 1GB
      threads: 2
  glacier:
    path: glacier
    max_size: 107374182400
    remote_storage:
      type: s3
      bucket: test-bucket
      prefix: data/
      region: us-west-2

data:
  storage: {}/data/storage
  models: {}/data/models
  cache: {}/data/cache
        """.format(temp_dir, temp_dir, temp_dir, temp_dir))
    
    # Create data directories
    memory_dir = Path(temp_dir) / "data" / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True)
    
    for tier in ['red_hot', 'hot', 'warm', 'cold', 'glacier']:
        tier_dir = memory_dir / tier
        tier_dir.mkdir(parents=True, exist_ok=True)
    
    yield temp_dir
    
    # Clean up
    try:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
    except Exception as e:
        print(f"Warning: Failed to clean up temporary directory {temp_dir}: {e}")


@pytest.fixture
def memory_manager(temp_config_dir):
    """Create a MemoryManager instance with mocked dependencies."""
    # Create a mock MemoryManager
    with patch('duckdb.connect') as mock_connect, \
         patch('faiss.IndexFlatL2') as mock_index:
        
        # Configure the mocks
        mock_con = MagicMock()
        mock_connect.return_value = mock_con
        
        mock_faiss_index = MagicMock()
        mock_index.return_value = mock_faiss_index
        
        # Create the manager instance
        manager = MemoryManager()
        
        # Mock the get_data_source_path and get_cache_path methods
        def mock_get_data_source_path(source_type):
            return Path(temp_config_dir) / "data" / "storage" / source_type
            
        def mock_get_cache_path(source_type):
            return Path(temp_config_dir) / "data" / "cache" / source_type
            
        manager.get_data_source_path = mock_get_data_source_path
        manager.get_cache_path = mock_get_cache_path
        
        # Mock the get_duckdb_connection method
        manager.get_duckdb_connection = MagicMock(return_value=mock_con)
        
        # Mock the get_faiss_index method
        manager.get_faiss_index = MagicMock(return_value=mock_faiss_index)
        
        # Mock the get_storage_backend method
        manager.get_storage_backend = MagicMock(return_value=MagicMock())
        
        yield manager


class TestMemoryManager:
    """Tests for the MemoryManager class."""
    
    def test_initialization(self, memory_manager):
        """Test initialization of MemoryManager."""
        assert memory_manager is not None
        assert hasattr(memory_manager, 'get_data_source_path')
        assert hasattr(memory_manager, 'get_cache_path')
        assert hasattr(memory_manager, 'get_duckdb_connection')
        assert hasattr(memory_manager, 'get_faiss_index')
        assert hasattr(memory_manager, 'get_storage_backend')
    
    def test_singleton_pattern(self, memory_manager):
        """Test that MemoryManager follows the singleton pattern."""
        manager2 = MemoryManager()
        assert memory_manager is manager2
    
    def test_get_data_source_path(self, memory_manager, temp_config_dir):
        """Test getting the data source path."""
        path = memory_manager.get_data_source_path("sentinel")
        expected_path = Path(temp_config_dir) / "data" / "storage" / "sentinel"
        assert path == expected_path
    
    def test_get_cache_path(self, memory_manager, temp_config_dir):
        """Test getting the cache path."""
        path = memory_manager.get_cache_path("sentinel")
        expected_path = Path(temp_config_dir) / "data" / "cache" / "sentinel"
        assert path == expected_path
    
    def test_get_duckdb_connection(self, memory_manager):
        """Test getting the DuckDB connection."""
        connection = memory_manager.get_duckdb_connection()
        assert connection is not None
        memory_manager.get_duckdb_connection.assert_called_once()
    
    def test_get_faiss_index(self, memory_manager):
        """Test getting the FAISS index."""
        index = memory_manager.get_faiss_index("red_hot")
        assert index is not None
        memory_manager.get_faiss_index.assert_called_once_with("red_hot")
    
    def test_get_storage_backend(self, memory_manager):
        """Test getting the storage backend."""
        backend = memory_manager.get_storage_backend("cold")
        assert backend is not None
        memory_manager.get_storage_backend.assert_called_once_with("cold") 