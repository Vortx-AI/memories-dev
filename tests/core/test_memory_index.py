"""
Tests for the MemoryIndex class in the core.memory_index module.
"""

import os
import pytest
import numpy as np
import pandas as pd
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

from memories.core.memory_index import MemoryIndex


@pytest.fixture
def mock_memory_catalog():
    """Create a mock MemoryCatalog."""
    mock_catalog = AsyncMock()
    
    # Configure the mock to return test data
    mock_catalog.get_tier_data.return_value = [
        {
            "data_id": "test-data-id",
            "tier": "cold",
            "location": "test_location",
            "created_at": "2023-01-01T00:00:00",
            "last_accessed": "2023-01-01T00:00:00",
            "access_count": 1,
            "size": 1000,
            "tags": '["test"]',
            "data_type": "dataframe",
            "table_name": "test_table",
            "additional_meta": '{"source":"test"}'
        }
    ]
    
    return mock_catalog


@pytest.fixture
def mock_sentence_transformer():
    """Create a mock SentenceTransformer."""
    mock_transformer = MagicMock()
    
    # Configure the mock to return test vectors
    mock_transformer.encode.return_value = np.array([[0.1, 0.2, 0.3, 0.4] * 96])  # 384-dimensional vector
    
    return mock_transformer


@pytest.fixture
def mock_memory_manager():
    """Create a mock MemoryManager instance."""
    mock = MagicMock()
    mock.get_storage_path.return_value = "/tmp/test_storage"
    return mock


@pytest.fixture
def memory_index(mock_memory_catalog, mock_sentence_transformer, mock_memory_manager):
    """Create a MemoryIndex instance with mocked dependencies."""
    # Patch the dependencies
    with patch('memories.core.memory_index.memory_catalog', mock_memory_catalog), \
         patch('memories.core.memory_index.SentenceTransformer', return_value=mock_sentence_transformer), \
         patch('memories.core.memory_index.faiss.IndexFlatL2') as mock_index_flat:
        
        # Create mock FAISS index
        mock_index = MagicMock()
        mock_index_flat.return_value = mock_index
        
        # Configure the mock to return test search results
        mock_index.search.return_value = (
            np.array([[0.5]]),  # Distances
            np.array([[0]])     # Indices
        )
        
        # Create the MemoryIndex instance
        index = MemoryIndex()
        
        # Set up the mock memory manager
        index._memory_manager = mock_memory_manager
        
        # Set up the mock model and index
        index.model = mock_sentence_transformer
        index._indexes = {
            "cold": {
                "index": mock_index,
                "data_ids": ["test-data-id"]
            }
        }
        
        # Set up mock memory tiers
        index._hot_memory = MagicMock()
        index._warm_memory = MagicMock()
        index._cold_memory = MagicMock()
        index._red_hot_memory = MagicMock()
        index._glacier_memory = MagicMock()
        
        # Configure the mock to return test data
        index._cold_memory.get_schema.return_value = {
            "columns": ["id", "name", "value"],
            "dtypes": {"id": "int", "name": "string", "value": "float"},
            "type": "dataframe"
        }
        
        yield index
        
        # Clean up
        try:
            index.cleanup()
        except Exception as e:
            print(f"Warning: Failed to clean up MemoryIndex: {e}")


class TestMemoryIndex:
    """Tests for the MemoryIndex class."""
    
    def test_initialization(self, memory_index):
        """Test initialization of MemoryIndex."""
        assert memory_index is not None
        assert memory_index.model is not None
        assert memory_index._indexes is not None
    
    def test_singleton_pattern(self, memory_index):
        """Test that MemoryIndex follows the singleton pattern."""
        index2 = MemoryIndex()
        assert memory_index is index2
    
    def test_vectorize_schema(self, memory_index):
        """Test vectorizing a schema."""
        # Create a test schema
        schema = {
            "columns": ["id", "name", "value"],
            "dtypes": {"id": "int", "name": "string", "value": "float"},
            "type": "dataframe"
        }
        
        # Vectorize the schema
        vector = memory_index._vectorize_schema(schema)
        
        # Check that the vector was created
        assert vector is not None
        assert isinstance(vector, np.ndarray)
        assert vector.shape == (384,)
    
    @pytest.mark.asyncio
    async def test_update_index(self, memory_index):
        """Test updating an index for a specific tier."""
        # Update the index
        await memory_index.update_index("cold")
        
        # Check that the index was updated
        assert "cold" in memory_index._indexes
        assert memory_index._indexes["cold"]["index"] is not None
        assert memory_index._indexes["cold"]["data_ids"] is not None
    
    @pytest.mark.asyncio
    async def test_update_all_indexes(self, memory_index):
        """Test updating all indexes."""
        # Update all indexes
        await memory_index.update_all_indexes()
        
        # Check that the indexes were updated
        assert "cold" in memory_index._indexes
    
    @pytest.mark.asyncio
    async def test_search(self, memory_index):
        """Test searching across memory tiers."""
        # Search for a query
        results = await memory_index.search("test query", tiers=["cold"], k=1)
        
        # Check that the results were returned
        assert results is not None
        assert len(results) == 1
        assert results[0]["data_id"] == "test-data-id"
        assert results[0]["tier"] == "cold"
        assert results[0]["distance"] == 0.5
        assert "schema" in results[0]
        
        # Check that the model was called to encode the query
        memory_index.model.encode.assert_called_once_with("test query")
    
    @pytest.mark.asyncio
    async def test_cleanup(self, memory_index):
        """Test cleanup method."""
        # Call cleanup
        await memory_index.cleanup()
        
        # Check that each memory tier was cleaned up
        memory_index._hot_memory.cleanup.assert_called_once()
        memory_index._warm_memory.cleanup.assert_called_once()
        memory_index._cold_memory.cleanup.assert_called_once()
        memory_index._red_hot_memory.cleanup.assert_called_once()
        memory_index._glacier_memory.cleanup.assert_called_once() 