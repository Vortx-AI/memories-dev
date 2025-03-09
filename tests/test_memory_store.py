"""Tests for memory store functionality."""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import json
from pathlib import Path
from datetime import datetime
import redis
import duckdb
import faiss

from memories.core.memory_store import MemoryStore
from memories.core.memory_manager import MemoryManager

@pytest.fixture
def mock_memory_manager():
    """Mock memory manager with all storage backends."""
    with patch('memories.core.memory_manager.MemoryManager') as mock:
        # Mock DuckDB connection
        mock_duckdb = MagicMock()
        mock.get_duckdb_connection.return_value = mock_duckdb
        
        # Mock Redis client
        mock_redis = MagicMock()
        mock.get_storage_backend.return_value = mock_redis
        
        # Mock FAISS index
        mock_faiss = faiss.IndexFlatL2(384)  # Create real FAISS index for testing
        mock.get_faiss_index.return_value = mock_faiss
        
        # Mock config
        mock.config = {
            'memory': {
                'warm': {'path': 'data/memory/warm'},
                'red_hot': {'path': 'data/memory/red_hot'}
            }
        }
        
        return mock

@pytest.fixture
def memory_store(mock_memory_manager):
    """Create memory store instance with mocked dependencies."""
    store = MemoryStore()
    store.memory_manager = mock_memory_manager
    return store

@pytest.mark.asyncio
async def test_store_invalid_tier(memory_store):
    """Test storing data to invalid tier."""
    with pytest.raises(ValueError):
        await memory_store.store("invalid_tier", {})

@pytest.mark.asyncio
async def test_store_in_cold(memory_store):
    """Test storing data in cold storage."""
    # Test with DataFrame
    df = pd.DataFrame({
        'col1': [1, 2, 3],
        'col2': ['a', 'b', 'c']
    })
    
    result = await memory_store.store(
        "cold",
        df,
        metadata={"source": "test"},
        tags=["test_tag"]
    )
    
    assert result is True
    mock_con = memory_store.memory_manager.get_duckdb_connection()
    assert mock_con.execute.call_count == 2  # CREATE TABLE and INSERT

    # Test with dictionary
    data_dict = {
        'col1': [1, 2, 3],
        'col2': ['a', 'b', 'c']
    }
    
    result = await memory_store.store(
        "cold",
        data_dict,
        metadata={"source": "test"},
        tags=["test_tag"]
    )
    
    assert result is True

@pytest.mark.asyncio
async def test_store_in_hot(memory_store):
    """Test storing data in hot storage."""
    data = {"key": "value"}
    metadata = {"source": "test"}
    tags = ["test_tag"]
    
    result = await memory_store.store(
        "hot",
        data,
        metadata=metadata,
        tags=tags
    )
    
    assert result is True
    mock_redis = memory_store.memory_manager.get_storage_backend()
    assert mock_redis.set.called
    assert mock_redis.sadd.called

@pytest.mark.asyncio
async def test_store_in_warm(memory_store, tmp_path):
    """Test storing data in warm storage."""
    # Mock the warm storage path to use tmp_path
    memory_store.memory_manager.config['memory']['warm']['path'] = str(tmp_path)
    
    data = {"key": "value"}
    metadata = {"source": "test"}
    tags = ["test_tag"]
    
    result = await memory_store.store(
        "warm",
        data,
        metadata=metadata,
        tags=tags
    )
    
    assert result is True
    # Check if file was created
    files = list(tmp_path.glob("*.json"))
    assert len(files) == 1
    
    # Verify file contents
    with open(files[0], 'r') as f:
        stored_data = json.load(f)
        assert stored_data["data"] == data
        assert stored_data["metadata"] == metadata
        assert stored_data["tags"] == tags

@pytest.mark.asyncio
async def test_store_in_red_hot(memory_store, tmp_path):
    """Test storing vector data in red hot storage."""
    # Mock the red hot storage path to use tmp_path
    memory_store.memory_manager.config['memory']['red_hot']['path'] = str(tmp_path)
    
    # Test with numpy array
    vector = np.random.rand(384).astype(np.float32)  # 384-dimensional vector
    metadata = {"source": "test"}
    tags = ["test_tag"]
    
    result = await memory_store.store(
        "red_hot",
        vector,
        metadata=metadata,
        tags=tags
    )
    
    assert result is True
    
    # Test with list
    vector_list = [float(x) for x in np.random.rand(384)]
    result = await memory_store.store(
        "red_hot",
        vector_list,
        metadata=metadata,
        tags=tags
    )
    
    assert result is True
    
    # Verify metadata file was created
    metadata_file = tmp_path / "metadata.json"
    assert metadata_file.exists()
    
    with open(metadata_file, 'r') as f:
        stored_metadata = json.load(f)
        assert len(stored_metadata) == 2  # Two vectors stored
        assert stored_metadata["0"]["metadata"] == metadata
        assert stored_metadata["0"]["tags"] == tags

@pytest.mark.asyncio
async def test_store_in_glacier(memory_store):
    """Test storing data in glacier storage (placeholder)."""
    result = await memory_store.store(
        "glacier",
        {"data": "test"},
        metadata={"source": "test"},
        tags=["test_tag"]
    )
    
    assert result is False  # Glacier storage is not implemented

@pytest.mark.asyncio
async def test_store_invalid_data_types(memory_store):
    """Test storing invalid data types."""
    # Test invalid data type for cold storage
    result = await memory_store.store(
        "cold",
        "invalid_data",  # String is not valid for cold storage
        metadata={"source": "test"},
        tags=["test_tag"]
    )
    assert result is False
    
    # Test invalid data type for red hot storage
    result = await memory_store.store(
        "red_hot",
        "invalid_data",  # String is not valid for red hot storage
        metadata={"source": "test"},
        tags=["test_tag"]
    )
    assert result is False

@pytest.mark.asyncio
async def test_store_with_missing_dependencies(memory_store):
    """Test storing when dependencies are not initialized."""
    # Test cold storage with no DuckDB connection
    memory_store.memory_manager.get_duckdb_connection.return_value = None
    result = await memory_store.store(
        "cold",
        pd.DataFrame({"test": [1, 2, 3]}),
        metadata={"source": "test"},
        tags=["test_tag"]
    )
    assert result is False
    
    # Test hot storage with no Redis client
    memory_store.memory_manager.get_storage_backend.return_value = None
    result = await memory_store.store(
        "hot",
        {"test": "data"},
        metadata={"source": "test"},
        tags=["test_tag"]
    )
    assert result is False
    
    # Test red hot storage with no FAISS index
    memory_store.memory_manager.get_faiss_index.return_value = None
    result = await memory_store.store(
        "red_hot",
        np.random.rand(384).astype(np.float32),
        metadata={"source": "test"},
        tags=["test_tag"]
    )
    assert result is False 