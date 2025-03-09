"""Tests for memory store functionality."""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock, AsyncMock
import json
from pathlib import Path
from datetime import datetime
import redis
import duckdb
import faiss

from memories.core.memory_store import MemoryStore
from memories.core.memory_manager import MemoryManager
from memories.core.hot import HotMemory
from memories.core.warm import WarmMemory
from memories.core.cold import ColdMemory
from memories.core.red_hot import RedHotMemory

@pytest.fixture
def mock_memory_manager():
    """Mock memory manager with all storage backends."""
    with patch('memories.core.memory_manager.MemoryManager') as mock:
        # Mock config
        mock.config = {
            'memory': {
                'warm': {'path': 'data/memory/warm'},
                'red_hot': {'path': 'data/memory/red_hot'}
            }
        }
        return mock

@pytest.fixture
def mock_hot_memory():
    """Mock hot memory."""
    with patch('memories.core.hot.HotMemory') as mock:
        instance = mock.return_value
        instance.store = AsyncMock(return_value=True)
        return instance

@pytest.fixture
def mock_warm_memory():
    """Mock warm memory."""
    with patch('memories.core.warm.WarmMemory') as mock:
        instance = mock.return_value
        instance.store = AsyncMock(return_value=True)
        return instance

@pytest.fixture
def mock_cold_memory():
    """Mock cold memory."""
    with patch('memories.core.cold.ColdMemory') as mock:
        instance = mock.return_value
        instance.store = AsyncMock(return_value=True)
        return instance

@pytest.fixture
def mock_red_hot_memory():
    """Mock red hot memory."""
    with patch('memories.core.red_hot.RedHotMemory') as mock:
        instance = mock.return_value
        instance.store = AsyncMock(return_value=True)
        return instance

@pytest.fixture
def memory_store(mock_memory_manager, mock_hot_memory, mock_warm_memory, mock_cold_memory, mock_red_hot_memory):
    """Create memory store instance with mocked dependencies."""
    store = MemoryStore()
    store.memory_manager = mock_memory_manager
    store._hot_memory = mock_hot_memory
    store._warm_memory = mock_warm_memory
    store._cold_memory = mock_cold_memory
    store._red_hot_memory = mock_red_hot_memory
    return store

@pytest.mark.asyncio
async def test_store_invalid_tier(memory_store):
    """Test storing data to invalid tier."""
    with pytest.raises(ValueError):
        await memory_store.store("invalid_tier", {})

@pytest.mark.asyncio
async def test_store_in_cold(memory_store, mock_cold_memory):
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
    mock_cold_memory.store.assert_called_once()

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
    assert mock_cold_memory.store.call_count == 2

@pytest.mark.asyncio
async def test_store_in_hot(memory_store, mock_hot_memory):
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
    mock_hot_memory.store.assert_called_once_with(data, metadata=metadata, tags=tags)

@pytest.mark.asyncio
async def test_store_in_warm(memory_store, mock_warm_memory, tmp_path):
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
    mock_warm_memory.store.assert_called_once_with(data, metadata=metadata, tags=tags)

@pytest.mark.asyncio
async def test_store_in_red_hot(memory_store, mock_red_hot_memory, tmp_path):
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
    mock_red_hot_memory.store.assert_called_once()
    
    # Test with list
    vector_list = [float(x) for x in np.random.rand(384)]
    result = await memory_store.store(
        "red_hot",
        vector_list,
        metadata=metadata,
        tags=tags
    )
    
    assert result is True
    assert mock_red_hot_memory.store.call_count == 2

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
async def test_store_invalid_data_types(memory_store, mock_cold_memory, mock_red_hot_memory):
    """Test storing invalid data types."""
    # Mock error responses
    mock_cold_memory.store.return_value = False
    mock_red_hot_memory.store.return_value = False
    
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
async def test_store_with_missing_dependencies(memory_store, mock_cold_memory, mock_hot_memory, mock_red_hot_memory):
    """Test storing when dependencies are not initialized."""
    # Mock error responses
    mock_cold_memory.store.return_value = False
    mock_hot_memory.store.return_value = False
    mock_red_hot_memory.store.return_value = False
    
    # Test cold storage
    result = await memory_store.store(
        "cold",
        pd.DataFrame({"test": [1, 2, 3]}),
        metadata={"source": "test"},
        tags=["test_tag"]
    )
    assert result is False
    
    # Test hot storage
    result = await memory_store.store(
        "hot",
        {"test": "data"},
        metadata={"source": "test"},
        tags=["test_tag"]
    )
    assert result is False
    
    # Test red hot storage
    result = await memory_store.store(
        "red_hot",
        np.random.rand(384).astype(np.float32),
        metadata={"source": "test"},
        tags=["test_tag"]
    )
    assert result is False 