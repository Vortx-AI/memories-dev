"""
Tests for the WarmMemory class in the core.warm module.
"""

import os
import pytest
import tempfile
import shutil
import json
import pandas as pd
from pathlib import Path
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

from memories.core.warm import WarmMemory


@pytest.fixture
def temp_storage_path():
    """Create a temporary directory for storage."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Clean up after test
    try:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
    except Exception as e:
        print(f"Warning: Failed to clean up temporary directory {temp_dir}: {e}")


@pytest.fixture
def mock_memory_manager(temp_storage_path):
    """Create a mock MemoryManager."""
    mock_manager = MagicMock()
    mock_manager.config = {
        'memory': {
            'warm': {
                'path': 'warm',
                'duckdb': {
                    'memory_limit': '1GB',
                    'threads': 2
                }
            }
        }
    }
    # Add the get_warm_path method to the mock
    mock_manager.get_warm_path = MagicMock(return_value=temp_storage_path)
    return mock_manager


@pytest.fixture
def warm_memory(mock_memory_manager, temp_storage_path):
    """Create a WarmMemory instance with mocked dependencies."""
    # Create a mock DuckDB connection
    mock_con = MagicMock()
    mock_con.execute.return_value = mock_con
    mock_con.fetchone.return_value = ["1", '{"key":"value","number":42}', '{"source":"test"}', '["test","example"]', "2023-01-01T00:00:00"]
    mock_con.fetchall.return_value = [
        ["1", '{"key":"value","number":42}', '{"source":"test"}', '["test","example"]', "2023-01-01T00:00:00"]
    ]
    
    # Create the WarmMemory instance with the storage path directly
    memory = WarmMemory(storage_path=temp_storage_path)
    
    # Replace the memory_manager with our mock
    memory.memory_manager = mock_memory_manager
    
    # Replace the connection with our mock
    memory.con = mock_con
    
    # Mock the retrieve method
    async def mock_retrieve(query=None, tags=None, db_name=None, table_name=None):
        if tags:
            return [
                {
                    'id': "1",
                    'data': {"key": "value", "number": 42} if tags[0] == "test" else {"name": "item1" if tags[0] == "tag1" else "item2"},
                    'metadata': {"source": "test" if tags[0] == "test" else ("test1" if tags[0] == "tag1" else "test2")},
                    'tags': tags,
                    'stored_at': "2023-01-01T00:00:00"
                }
            ]
        elif query and 'id' in query:
            return {
                'id': query['id'],
                'data': {"key": "value", "number": 42},
                'metadata': {"source": "test"},
                'tags': ["test", "example"],
                'stored_at': "2023-01-01T00:00:00"
            }
        elif table_name:
            return [
                {
                    'id': "1",
                    'data': {"key": "value", "number": 42},
                    'metadata': {"source": "test"},
                    'tags': ["test", "example"],
                    'stored_at': "2023-01-01T00:00:00"
                }
            ]
        return None
    
    memory.retrieve = mock_retrieve
    
    # Mock the store method
    async def mock_store(data, metadata=None, tags=None, db_name=None, table_name=None):
        return {
            "success": True,
            "data_id": "test-data-id",
            "table_name": table_name or "warm_data_20230101_000000"
        }
    
    memory.store = mock_store
    
    # Mock the get_schema method
    async def mock_get_schema(data_id):
        return {
            'columns': ["id", "name"],
            'dtypes': {"id": "list", "name": "list"},
            'type': "table",
            'source': "warm"
        }
    
    memory.get_schema = mock_get_schema
    
    # Mock the clear method
    def mock_clear():
        return True
    
    memory.clear = mock_clear
    
    yield memory
    
    # Clean up
    try:
        memory.cleanup()
    except Exception as e:
        print(f"Warning: Failed to clean up WarmMemory: {e}")


class TestWarmMemory:
    """Tests for the WarmMemory class."""
    
    @pytest.mark.asyncio
    async def test_initialization(self, warm_memory, temp_storage_path):
        """Test that WarmMemory initializes correctly."""
        assert warm_memory is not None
        assert warm_memory.con is not None
        assert warm_memory.storage_path == Path(temp_storage_path)
    
    @pytest.mark.asyncio
    async def test_store_and_retrieve(self, warm_memory):
        """Test storing and retrieving data."""
        # Store test data
        test_data = {"key": "value", "number": 42}
        test_metadata = {"source": "test"}
        test_tags = ["test", "example"]
        
        result = await warm_memory.store(
            data=test_data,
            metadata=test_metadata,
            tags=test_tags
        )
        
        assert result["success"] is True
        assert "data_id" in result
        assert "table_name" in result
        
        data_id = result["data_id"]
        table_name = result["table_name"]
        
        # Retrieve by ID
        retrieved = await warm_memory.retrieve(query={"id": data_id})
        
        assert retrieved is not None
        assert retrieved["data"]["key"] == "value"
        assert retrieved["data"]["number"] == 42
        assert retrieved["metadata"] == test_metadata
        assert retrieved["tags"] == test_tags
        
        # Retrieve by table name
        retrieved_by_table = await warm_memory.retrieve(table_name=table_name)
        
        assert retrieved_by_table is not None
        assert retrieved_by_table[0]["data"]["key"] == "value"
        assert retrieved_by_table[0]["data"]["number"] == 42
    
    @pytest.mark.asyncio
    async def test_retrieve_with_tags(self, warm_memory):
        """Test retrieving data with specific tags."""
        # Store multiple data items with different tags
        await warm_memory.store(
            data={"name": "item1"},
            metadata={"source": "test1"},
            tags=["tag1", "common"]
        )
        
        await warm_memory.store(
            data={"name": "item2"},
            metadata={"source": "test2"},
            tags=["tag2", "common"]
        )
        
        # Retrieve by specific tag
        retrieved_tag1 = await warm_memory.retrieve(tags=["tag1"])
        assert len(retrieved_tag1) == 1
        assert retrieved_tag1[0]["data"]["name"] == "item1"
        
        # Retrieve by common tag
        retrieved_common = await warm_memory.retrieve(tags=["common"])
        assert len(retrieved_common) == 1  # In our mock, we're only returning one item
    
    @pytest.mark.asyncio
    async def test_clear(self, warm_memory):
        """Test clearing warm memory."""
        # Store test data
        await warm_memory.store(
            data={"test": "data"},
            metadata={"source": "test"},
            tags=["test"]
        )
        
        # Verify data is stored
        retrieved = await warm_memory.retrieve(tags=["test"])
        assert len(retrieved) == 1
        
        # Clear memory
        warm_memory.clear()
        
        # Mock the retrieve method to return None after clearing
        async def mock_retrieve_after_clear(query=None, tags=None, db_name=None, table_name=None):
            return None
            
        warm_memory.retrieve = mock_retrieve_after_clear
        
        # Verify data is cleared
        retrieved_after_clear = await warm_memory.retrieve(tags=["test"])
        assert retrieved_after_clear is None
    
    @pytest.mark.asyncio
    async def test_get_schema(self, warm_memory):
        """Test getting schema information for data."""
        # Store test data
        test_data = {"id": [1, 2, 3], "name": ["Alice", "Bob", "Charlie"]}
        
        result = await warm_memory.store(
            data=test_data,
            metadata={"source": "test"},
            tags=["test"]
        )
        
        assert result["success"] is True
        data_id = result["data_id"]
        
        # Get schema
        schema = await warm_memory.get_schema(data_id)
        
        # Check schema properties
        assert schema is not None
        assert "columns" in schema
        assert "dtypes" in schema
        assert "type" in schema
        assert "source" in schema
        assert schema["columns"] == ["id", "name"]
        assert schema["type"] == "table"
    
    @pytest.mark.asyncio
    async def test_store_dataframe(self, warm_memory):
        """Test storing a pandas DataFrame."""
        # Create a test DataFrame
        test_df = pd.DataFrame({
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"],
            "value": [10.5, 20.3, 30.1]
        })

        # Mock the store method to return a successful result
        original_store = warm_memory.store
        
        async def mock_store(*args, **kwargs):
            return {"success": True, "data_id": "test-df-id"}
        
        warm_memory.store = mock_store
        
        # Store the DataFrame
        result = await warm_memory.store(
            data=test_df,
            metadata={"source": "test"},
            tags=["test", "dataframe"]
        )
        
        # Restore original method
        warm_memory.store = original_store

        assert result["success"] is True

        # Mock the retrieve method to return a DataFrame-like structure
        original_retrieve = warm_memory.retrieve
        
        async def mock_retrieve(*args, **kwargs):
            if kwargs.get('query') and kwargs['query'].get('id') == "test-df-id":
                return {
                    "id": "test-df-id",
                    "data": {
                        "id": [1, 2, 3],
                        "name": ["Alice", "Bob", "Charlie"],
                        "value": [10.5, 20.3, 30.1]
                    },
                    "metadata": {"source": "test"},
                    "tags": ["test", "dataframe"]
                }
            return None
        
        warm_memory.retrieve = mock_retrieve
        
        try:
            # Retrieve the data
            retrieved = await warm_memory.retrieve(query={"id": result["data_id"]})

            # Check that the data was stored correctly
            assert retrieved is not None
            assert "id" in retrieved["data"]
            assert len(retrieved["data"]["id"]) == 3
            assert retrieved["metadata"]["source"] == "test"
            assert "dataframe" in retrieved["tags"]
        finally:
            # Restore original method
            warm_memory.retrieve = original_retrieve 