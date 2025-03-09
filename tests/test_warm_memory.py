"""Tests for warm memory functionality."""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock, AsyncMock
import json
from pathlib import Path
from datetime import datetime
import duckdb
import uuid
import os

from memories.core.warm import WarmMemory
from memories.core.memory_manager import MemoryManager

# Mock the MemoryManager for testing
@pytest.fixture
def mock_memory_manager():
    """Mock memory manager with configuration."""
    with patch('memories.core.memory_manager.MemoryManager', autospec=True) as mock:
        instance = mock.return_value
        instance.config = {
            'memory': {
                'base_path': './data/memory',
                'warm': {
                    'path': 'warm',
                    'duckdb': {
                        'memory_limit': '1GB',
                        'threads': 2
                    }
                }
            }
        }
        # Create a mock DuckDB connection
        instance.con = duckdb.connect(database=':memory:')
        return instance

@pytest.fixture
def warm_memory(mock_memory_manager):
    """Create a WarmMemory instance with mocked dependencies."""
    with patch('memories.core.warm.MemoryManager', return_value=mock_memory_manager):
        memory = WarmMemory()
        yield memory
        # Clean up after tests
        memory.cleanup()

# Test data fixtures
@pytest.fixture
def sample_dict_data():
    """Sample dictionary data for testing."""
    return {
        "name": "Test Item",
        "value": 42,
        "nested": {
            "key": "value"
        }
    }

@pytest.fixture
def sample_list_data():
    """Sample list data for testing."""
    return [
        {"id": 1, "name": "Item 1"},
        {"id": 2, "name": "Item 2"},
        {"id": 3, "name": "Item 3"}
    ]

@pytest.fixture
def sample_numpy_data():
    """Sample numpy array for testing."""
    return np.array([1, 2, 3, 4, 5])

@pytest.fixture
def sample_pandas_data():
    """Sample pandas DataFrame for testing."""
    return pd.DataFrame({
        'col1': [1, 2, 3],
        'col2': ['a', 'b', 'c']
    })

@pytest.mark.asyncio
async def test_init(mock_memory_manager):
    """Test initialization of WarmMemory."""
    with patch('memories.core.warm.MemoryManager', return_value=mock_memory_manager):
        memory = WarmMemory()
        
        # Verify tables were created
        result = memory.con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        table_names = [row[0] for row in result]
        
        assert "warm_data" in table_names
        assert "warm_tags" in table_names

@pytest.mark.asyncio
async def test_store_dict_data(warm_memory, sample_dict_data):
    """Test storing dictionary data."""
    metadata = {"source": "test", "timestamp": datetime.now().isoformat()}
    tags = ["test", "dict", "sample"]
    
    result = await warm_memory.store(sample_dict_data, metadata, tags)
    assert result["success"] is True
    assert "data_id" in result
    assert "table_name" in result
    
    # Verify data was stored
    stored_data = warm_memory.default_con.execute("SELECT * FROM warm_data").fetchall()
    assert len(stored_data) == 1
    
    # Verify tags were stored
    stored_tags = warm_memory.default_con.execute("SELECT * FROM warm_tags").fetchall()
    assert len(stored_tags) == 3  # 3 tags

@pytest.mark.asyncio
async def test_store_list_data(warm_memory, sample_list_data):
    """Test storing list data."""
    result = await warm_memory.store(sample_list_data)
    assert result["success"] is True
    
    # Verify data was stored
    stored_data = warm_memory.default_con.execute("SELECT * FROM warm_data").fetchall()
    assert len(stored_data) == 1
    
    # Verify the stored data is a list
    data_json = stored_data[0][1]  # data column
    data = json.loads(data_json)
    assert isinstance(data, list)
    assert len(data) == 3

@pytest.mark.asyncio
async def test_store_numpy_data(warm_memory, sample_numpy_data):
    """Test storing numpy array."""
    result = await warm_memory.store(sample_numpy_data)
    assert result["success"] is True
    
    # Verify data was stored
    stored_data = warm_memory.default_con.execute("SELECT * FROM warm_data").fetchall()
    assert len(stored_data) == 1
    
    # Verify the stored data matches the original
    data_json = stored_data[0][1]  # data column
    data = json.loads(data_json)
    assert isinstance(data, list)
    np.testing.assert_array_equal(np.array(data), sample_numpy_data)

@pytest.mark.asyncio
async def test_store_pandas_data(warm_memory, sample_pandas_data):
    """Test storing pandas DataFrame."""
    result = await warm_memory.store(sample_pandas_data)
    assert result["success"] is True
    
    # Verify data was stored
    stored_data = warm_memory.default_con.execute("SELECT * FROM warm_data").fetchall()
    assert len(stored_data) == 1

@pytest.mark.asyncio
async def test_retrieve_by_tag(warm_memory, sample_dict_data):
    """Test retrieving data by tag."""
    # Store data with tags
    tags = ["retrieve_test", "important"]
    result = await warm_memory.store(sample_dict_data, tags=tags)
    assert result["success"] is True
    
    # Retrieve by tag
    result = await warm_memory.retrieve(tags=["retrieve_test"])
    
    assert result is not None
    assert isinstance(result, dict)  # Single result
    assert "data" in result
    assert result["data"]["name"] == "Test Item"
    assert "tags" in result
    assert "retrieve_test" in result["tags"]

@pytest.mark.asyncio
async def test_retrieve_multiple_results(warm_memory):
    """Test retrieving multiple results."""
    # Store multiple items with the same tag
    tag = "multiple_test"
    result1 = await warm_memory.store({"id": 1, "value": "first"}, tags=[tag])
    result2 = await warm_memory.store({"id": 2, "value": "second"}, tags=[tag])
    result3 = await warm_memory.store({"id": 3, "value": "third"}, tags=[tag])
    
    assert result1["success"] is True
    assert result2["success"] is True
    assert result3["success"] is True
    
    # Retrieve all items with the tag
    results = await warm_memory.retrieve(tags=[tag])
    
    assert results is not None
    assert isinstance(results, list)
    assert len(results) == 3
    
    # Check that results are ordered by stored_at (most recent first)
    assert results[0]["data"]["id"] == 3
    assert results[1]["data"]["id"] == 2
    assert results[2]["data"]["id"] == 1

@pytest.mark.asyncio
async def test_retrieve_by_query(warm_memory):
    """Test retrieving data by query."""
    # Store data with specific values
    result = await warm_memory.store(
        {"category": "electronics", "price": 100},
        metadata={"in_stock": True}
    )
    assert result["success"] is True
    
    # Retrieve by data query
    result = await warm_memory.retrieve(query={"data": {"category": "electronics"}})
    assert result is not None
    assert result["data"]["price"] == 100
    
    # Retrieve by metadata query
    result = await warm_memory.retrieve(query={"metadata": {"in_stock": True}})
    assert result is not None
    assert result["data"]["category"] == "electronics"

@pytest.mark.asyncio
async def test_retrieve_no_results(warm_memory):
    """Test retrieving with no matching results."""
    # Retrieve with non-existent tag
    result = await warm_memory.retrieve(tags=["nonexistent"])
    assert result is None
    
    # Retrieve with non-matching query
    result = await warm_memory.retrieve(query={"data": {"category": "nonexistent"}})
    assert result is None

@pytest.mark.asyncio
async def test_clear(warm_memory, sample_dict_data):
    """Test clearing all data."""
    # Store some data
    result = await warm_memory.store(sample_dict_data, tags=["test"])
    assert result["success"] is True
    
    # Verify data exists
    data_count = warm_memory.default_con.execute("SELECT COUNT(*) FROM warm_data").fetchone()[0]
    tags_count = warm_memory.default_con.execute("SELECT COUNT(*) FROM warm_tags").fetchone()[0]
    assert data_count > 0
    assert tags_count > 0
    
    # Clear data
    warm_memory.clear()
    
    # Verify data was cleared
    data_count = warm_memory.default_con.execute("SELECT COUNT(*) FROM warm_data").fetchone()[0]
    tags_count = warm_memory.default_con.execute("SELECT COUNT(*) FROM warm_tags").fetchone()[0]
    assert data_count == 0
    assert tags_count == 0

@pytest.mark.asyncio
async def test_get_schema_dict(warm_memory, sample_dict_data):
    """Test getting schema for dictionary data."""
    # Store data and get ID
    result = await warm_memory.store(sample_dict_data)
    assert result["success"] is True
    data_id = result["data_id"]
    
    # Get schema
    schema = await warm_memory.get_schema(data_id)
    
    assert schema is not None
    assert schema["type"] == "dict"
    assert "fields" in schema
    assert "name" in schema["fields"]
    assert "value" in schema["fields"]
    assert "nested" in schema["fields"]
    assert schema["types"]["name"] == "str"
    assert schema["types"]["value"] == "int"

@pytest.mark.asyncio
async def test_get_schema_list(warm_memory, sample_list_data):
    """Test getting schema for list data."""
    # Store data and get ID
    result = await warm_memory.store(sample_list_data)
    assert result["success"] is True
    data_id = result["data_id"]
    
    # Get schema
    schema = await warm_memory.get_schema(data_id)
    
    assert schema is not None
    assert schema["type"] == "list_of_dicts"
    assert "fields" in schema
    assert "id" in schema["fields"]
    assert "name" in schema["fields"]

@pytest.mark.asyncio
async def test_get_schema_nonexistent(warm_memory):
    """Test getting schema for non-existent data."""
    schema = await warm_memory.get_schema("nonexistent_id")
    assert schema is None

@pytest.mark.asyncio
async def test_cleanup(mock_memory_manager):
    """Test cleanup method."""
    with patch('memories.core.warm.MemoryManager', return_value=mock_memory_manager):
        # Create a WarmMemory with its own connection
        with patch.object(mock_memory_manager, 'con', None):
            memory = WarmMemory()
            assert memory.con is not None
            
            # Cleanup should close the connection
            memory.cleanup()
            
            # This would raise an error if the connection was closed
            with pytest.raises(Exception):
                memory.con.execute("SELECT 1")

@pytest.mark.asyncio
async def test_shared_connection(mock_memory_manager):
    """Test using shared connection from memory manager."""
    with patch('memories.core.warm.MemoryManager', return_value=mock_memory_manager):
        memory = WarmMemory()
        
        # Should be using the connection from memory_manager
        assert memory.con is mock_memory_manager.con
        
        # Store some data
        await memory.store({"test": "data"})
        
        # Cleanup should not close the shared connection
        memory.cleanup()
        
        # Connection should still be usable
        result = mock_memory_manager.con.execute("SELECT 1").fetchone()
        assert result[0] == 1

@pytest.mark.asyncio
async def test_multiple_databases(warm_memory):
    """Test storing and retrieving data from multiple databases."""
    # Store data in default database
    result1 = await warm_memory.store(
        {"name": "Default Item", "value": 42},
        tags=["default"]
    )
    assert result1["success"] is True
    
    # Store data in custom database 1
    result2 = await warm_memory.store(
        {"name": "Database 1 Item", "value": 100},
        tags=["db1"],
        db_name="custom_db1"
    )
    assert result2["success"] is True
    
    # Store data in custom database 2
    result3 = await warm_memory.store(
        {"name": "Database 2 Item", "value": 200},
        tags=["db2"],
        db_name="custom_db2"
    )
    assert result3["success"] is True
    
    # Retrieve from default database
    result = await warm_memory.retrieve(tags=["default"])
    assert result is not None
    assert result["data"]["name"] == "Default Item"
    
    # Retrieve from custom database 1
    result = await warm_memory.retrieve(tags=["db1"], db_name="custom_db1")
    assert result is not None
    assert result["data"]["name"] == "Database 1 Item"
    
    # Retrieve from custom database 2
    result = await warm_memory.retrieve(tags=["db2"], db_name="custom_db2")
    assert result is not None
    assert result["data"]["name"] == "Database 2 Item"
    
    # List all databases
    db_names = await warm_memory.list_databases()
    assert "custom_db1" in db_names
    assert "custom_db2" in db_names
    
    # Clear specific database
    warm_memory.clear(db_name="custom_db1")
    
    # Verify database 1 is cleared
    result = await warm_memory.retrieve(tags=["db1"], db_name="custom_db1")
    assert result is None
    
    # Verify database 2 is still intact
    result = await warm_memory.retrieve(tags=["db2"], db_name="custom_db2")
    assert result is not None
    assert result["data"]["name"] == "Database 2 Item"

@pytest.mark.asyncio
async def test_get_schema_from_specific_database(warm_memory):
    """Test getting schema from a specific database."""
    # Store data in custom database
    result = await warm_memory.store(
        {"category": "test", "attributes": ["a", "b", "c"]},
        db_name="schema_db"
    )
    assert result["success"] is True
    data_id = result["data_id"]
    
    # Get schema from the specific database
    schema = await warm_memory.get_schema(data_id, db_name="schema_db")
    
    assert schema is not None
    assert schema["type"] == "dict"
    assert "category" in schema["fields"]
    assert "attributes" in schema["fields"]
    assert schema["types"]["category"] == "str"
    assert schema["types"]["attributes"] == "list" 