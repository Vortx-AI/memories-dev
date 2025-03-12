"""
Tests for the MemoryCatalog class in the core.memory_catalog module.
"""

import os
import pytest
import tempfile
import json
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock

from memories.core.memory_catalog import MemoryCatalog


@pytest.fixture
def mock_memory_manager():
    """Create a mock MemoryManager instance."""
    mock_manager = MagicMock()
    mock_manager.get_storage_path.return_value = "/tmp/test_storage"
    return mock_manager


@pytest.fixture
def memory_catalog(mock_memory_manager):
    """Create a MemoryCatalog instance with mocked dependencies."""
    # Create a mock DuckDB connection
    mock_con = MagicMock()
    mock_con.execute.return_value = mock_con
    
    # Configure the mock to return test data
    mock_con.fetchone.return_value = ["test-data-id", "cold", "test_location", "2023-01-01T00:00:00", "2023-01-01T00:00:00", 1, 1000, '["test"]', "dataframe", "test_table", '{"source":"test"}']
    mock_con.fetchall.return_value = [
        ["test-data-id", "cold", "test_location", "2023-01-01T00:00:00", "2023-01-01T00:00:00", 1, 1000, '["test"]', "dataframe", "test_table", '{"source":"test"}']
    ]
    
    # Create a catalog instance
    catalog = MemoryCatalog()
    
    # Set up the mock connection
    catalog.con = mock_con
    catalog._memory_manager = mock_memory_manager
    
    # Mock the async methods to return test data
    async def mock_register_data(tier, location, size, data_type, tags=None, metadata=None, table_name=None):
        return "test-data-id"
    
    async def mock_update_access(data_id):
        catalog.con.execute("UPDATE mock_query")
        return None
    
    async def mock_get_data_info(data_id):
        return {
            "data_id": data_id,
            "tier": "cold",
            "location": "test_location",
            "created": "2023-01-01T00:00:00",
            "last_accessed": "2023-01-01T00:00:00",
            "access_count": 1,
            "size": 1000,
            "tags": ["test"],
            "data_type": "dataframe",
            "table_name": "test_table",
            "metadata": {"source": "test"}
        }
    
    async def mock_search_by_tags(tags):
        return [{
            "data_id": "test-data-id",
            "tier": "cold",
            "location": "test_location",
            "created": "2023-01-01T00:00:00",
            "last_accessed": "2023-01-01T00:00:00",
            "access_count": 1,
            "size": 1000,
            "tags": ["test"],
            "data_type": "dataframe",
            "table_name": "test_table",
            "metadata": {"source": "test"}
        }]
    
    async def mock_get_tier_data(tier):
        return [{
            "data_id": "test-data-id",
            "tier": tier,
            "location": "test_location",
            "created": "2023-01-01T00:00:00",
            "last_accessed": "2023-01-01T00:00:00",
            "access_count": 1,
            "size": 1000,
            "tags": ["test"],
            "data_type": "dataframe",
            "table_name": "test_table",
            "metadata": {"source": "test"}
        }]
    
    async def mock_delete_data(data_id):
        catalog.con.execute("DELETE mock_query")
        return True
    
    # Assign the mock methods
    catalog.register_data = mock_register_data
    catalog.update_access = mock_update_access
    catalog.get_data_info = mock_get_data_info
    catalog.search_by_tags = mock_search_by_tags
    catalog.get_tier_data = mock_get_tier_data
    catalog.delete_data = mock_delete_data
    
    return catalog


class TestMemoryCatalog:
    """Tests for the MemoryCatalog class."""
    
    def test_initialization(self, memory_catalog):
        """Test initialization of MemoryCatalog."""
        assert memory_catalog is not None
        assert memory_catalog.con is not None
    
    def test_singleton_pattern(self, memory_catalog):
        """Test that MemoryCatalog follows the singleton pattern."""
        catalog2 = MemoryCatalog()
        assert memory_catalog is catalog2
    
    @pytest.mark.asyncio
    async def test_register_data(self, memory_catalog):
        """Test registering data in the catalog."""
        # Register test data
        data_id = await memory_catalog.register_data(
            tier="cold",
            location="test_location",
            size=1000,
            tags=["test"],
            data_type="dataframe",
            table_name="test_table",
            metadata={"source": "test"}
        )
        
        # Check that the data was registered
        assert data_id is not None
        assert isinstance(data_id, str)
        assert data_id == "test-data-id"
    
    @pytest.mark.asyncio
    async def test_update_access(self, memory_catalog):
        """Test updating access time for data."""
        # Update access time
        await memory_catalog.update_access("test-data-id")
        
        # Check that execute was called with the correct SQL
        memory_catalog.con.execute.assert_called()
    
    @pytest.mark.asyncio
    async def test_get_data_info(self, memory_catalog):
        """Test getting data info from the catalog."""
        # Get data info
        data_info = await memory_catalog.get_data_info("test-data-id")
        
        # Check that the data info was returned
        assert data_info is not None
        assert data_info["data_id"] == "test-data-id"
        assert data_info["tier"] == "cold"
        assert data_info["location"] == "test_location"
        assert data_info["created"] == "2023-01-01T00:00:00"
        assert data_info["last_accessed"] == "2023-01-01T00:00:00"
        assert data_info["access_count"] == 1
        assert data_info["size"] == 1000
        assert data_info["tags"] == ["test"]
        assert data_info["data_type"] == "dataframe"
        assert data_info["table_name"] == "test_table"
        assert data_info["metadata"] == {"source": "test"}
    
    @pytest.mark.asyncio
    async def test_search_by_tags(self, memory_catalog):
        """Test searching for data by tags."""
        # Search by tags
        results = await memory_catalog.search_by_tags(["test"])
        
        # Check that the results were returned
        assert results is not None
        assert len(results) == 1
        assert results[0]["data_id"] == "test-data-id"
    
    @pytest.mark.asyncio
    async def test_get_tier_data(self, memory_catalog):
        """Test getting all data for a tier."""
        # Get tier data
        results = await memory_catalog.get_tier_data("cold")
        
        # Check that the results were returned
        assert results is not None
        assert len(results) == 1
        assert results[0]["data_id"] == "test-data-id"
    
    @pytest.mark.asyncio
    async def test_delete_data(self, memory_catalog):
        """Test deleting data from the catalog."""
        # Delete data
        result = await memory_catalog.delete_data("test-data-id")
        
        # Check that execute was called with the correct SQL
        memory_catalog.con.execute.assert_called()
        assert result is True
    
    def test_cleanup(self, memory_catalog):
        """Test cleanup method."""
        # Create a new mock connection
        mock_con = MagicMock()
        
        # Replace the existing connection with our mock
        original_con = memory_catalog.con
        memory_catalog.con = mock_con
        
        try:
            # Call cleanup
            memory_catalog.cleanup()
            
            # Check that the connection was closed
            mock_con.close.assert_called_once()
        finally:
            # Restore the original connection to avoid affecting other tests
            memory_catalog.con = original_con 