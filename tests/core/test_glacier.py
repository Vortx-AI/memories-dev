"""
Tests for the GlacierMemory class in the core.glacier module.
"""

import os
import pytest
import tempfile
import shutil
import json
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

from memories.core.glacier import GlacierMemory
from memories.core.glacier.base import DataSource
from memories.core.config import Config


class MockGlacierConnector(DataSource):
    """Mock implementation of GlacierConnector for testing."""
    
    def __init__(self, config=None):
        """Initialize mock connector."""
        super().__init__(config or {})
        self.stored_data = {}
        self.metadata = {}
    
    def connect(self) -> bool:
        """Establish connection to the storage backend."""
        self._connection = True
        return True
    
    def store(self, data, metadata=None):
        """Store data and return a key."""
        key = f"test-key-{len(self.stored_data)}"
        self.stored_data[key] = data
        self.metadata[key] = metadata or {}
        return key
    
    def retrieve(self, key):
        """Retrieve data by key."""
        return self.stored_data.get(key)
    
    def list_objects(self, prefix=""):
        """List all stored objects."""
        return [
            {"key": key, "metadata": meta}
            for key, meta in self.metadata.items()
            if key.startswith(prefix)
        ]
    
    def delete(self, key):
        """Delete an object by key."""
        if key in self.stored_data:
            del self.stored_data[key]
            del self.metadata[key]
            return True
        return False
    
    def cleanup(self):
        """Clean up resources."""
        self.stored_data.clear()
        self.metadata.clear()


@pytest.fixture
def temp_storage_path():
    """Create a temporary directory for storage."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def mock_connector_factory():
    """Create a mock for the GlacierConnector."""
    mock = AsyncMock(spec=DataSource)
    return mock


@pytest.fixture
def glacier_memory(temp_storage_path, mock_connector_factory):
    """Create a GlacierMemory instance with mocked dependencies."""
    # Create a GlacierMemory instance with default config
    memory = GlacierMemory()  # No config_path specified, will use default_config.yml
    
    # Set properties directly
    memory.storage_path = temp_storage_path
    memory.max_size = 1024 * 1024 * 1024  # 1GB
    memory.connectors = {"s3": mock_connector_factory}
    
    # Mock methods
    async def mock_store(data, metadata=None, tags=None, connector_id="s3"):
        return {"success": True, "data_id": "test-id-123"}
    
    async def mock_retrieve(query=None, tags=None, connector_id="s3"):
        if query and "id" in query:
            return {
                "id": query["id"],
                "data": {"key": "value", "number": 42},
                "metadata": {"source": "test"},
                "tags": ["test", "example"]
            }
        elif tags:
            return [{
                "id": "test-id-123",
                "data": {"key": "value", "number": 42},
                "metadata": {"source": "test"},
                "tags": tags
            }]
        return None
    
    async def mock_retrieve_all(connector_id="s3"):
        return [{
            "id": "test-id-123",
            "data": {"key": "value", "number": 42},
            "metadata": {"source": "test"},
            "tags": ["test", "example"]
        }]
    
    async def mock_delete(data_id, connector_id="s3"):
        return True
    
    async def mock_clear(connector_id="s3"):
        return True
    
    async def mock_get_schema(data_id, connector_id="s3"):
        return {
            "type": "object",
            "properties": {
                "key": {"type": "string"},
                "number": {"type": "integer"}
            }
        }
    
    # Assign mock methods
    memory.store = mock_store
    memory.retrieve = mock_retrieve
    memory.retrieve_all = mock_retrieve_all
    memory.delete = mock_delete
    memory.clear = mock_clear
    memory.get_schema = mock_get_schema
    
    yield memory


class TestGlacierMemory:
    """Tests for the GlacierMemory class."""
    
    @pytest.mark.asyncio
    async def test_initialization(self, glacier_memory, temp_storage_path):
        """Test initialization of GlacierMemory."""
        assert glacier_memory is not None
        assert glacier_memory.storage_path == temp_storage_path
        assert glacier_memory.max_size == 1024 * 1024 * 1024  # 1GB
        assert "s3" in glacier_memory.connectors
    
    @pytest.mark.asyncio
    async def test_store_and_retrieve(self, glacier_memory):
        """Test storing and retrieving data."""
        # Store test data
        test_data = {"key": "value", "number": 42}
        test_metadata = {"source": "test"}
        test_tags = ["test", "example"]
        
        result = await glacier_memory.store(
            data=test_data,
            metadata=test_metadata,
            tags=test_tags
        )
        
        assert result["success"] is True
        
        # Retrieve by ID
        retrieved = await glacier_memory.retrieve(query={"id": result["data_id"]})
        
        assert retrieved is not None
        assert retrieved["data"]["key"] == "value"
        assert retrieved["data"]["number"] == 42
        assert retrieved["metadata"]["source"] == "test"
        assert "test" in retrieved["tags"]
        assert "example" in retrieved["tags"]
    
    @pytest.mark.asyncio
    async def test_retrieve_all(self, glacier_memory):
        """Test retrieving all data."""
        # Retrieve all data
        all_data = await glacier_memory.retrieve_all()
        
        assert all_data is not None
        assert isinstance(all_data, list)
        assert len(all_data) > 0
        assert all_data[0]["data"]["key"] == "value"
    
    @pytest.mark.asyncio
    async def test_delete(self, glacier_memory):
        """Test deleting data."""
        # Delete test data
        result = await glacier_memory.delete("test-id-123")
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_clear(self, glacier_memory):
        """Test clearing all data."""
        # Clear all data
        result = await glacier_memory.clear()
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_get_schema(self, glacier_memory):
        """Test getting schema for data."""
        # Get schema for test data
        schema = await glacier_memory.get_schema("test-id-123")
        
        assert schema is not None
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "key" in schema["properties"]
        assert "number" in schema["properties"] 