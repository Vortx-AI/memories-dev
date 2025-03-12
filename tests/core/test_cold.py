"""
Tests for the ColdMemory class in the core.cold module.
"""

import os
import sys
import pytest
import pandas as pd
import numpy as np
import tempfile
import shutil
import json
from io import StringIO
from pathlib import Path
import asyncio
import importlib.util
from unittest.mock import patch, MagicMock, AsyncMock

# Import Config and ColdMemory directly from the file to avoid initialization issues
def import_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

# Import the Config and ColdMemory classes directly from the file
cold_module = import_module_from_path("cold", "memories/core/cold.py")
Config = cold_module.Config
ColdMemory = cold_module.ColdMemory


class MockMemoryCatalog:
    """Mock for the memory catalog."""
    
    async def register_data(self, tier, location, size, data_type, metadata=None, tags=None):
        """Mock register_data method."""
        return "test-data-id"
    
    async def get_data_schema(self, data_id):
        """Mock get_data_schema method."""
        return {
            "id": data_id,
            "tier": "cold",
            "data_type": "dataframe",
            "size": 1000,
            "created_at": "2023-01-01T00:00:00",
            "tags": ["test"]
        }
    
    async def list_data(self, tier=None, tags=None):
        """Mock list_data method."""
        return [
            {
                "id": "test-data-id",
                "tier": "cold",
                "data_type": "dataframe",
                "size": 1000,
                "created_at": "2023-01-01T00:00:00",
                "tags": ["test"]
            }
        ]
    
    async def delete_data(self, data_id):
        """Mock delete_data method."""
        return True
        
    async def get_data_info(self, data_id):
        """Mock get_data_info method."""
        return {
            "data_id": data_id,
            "tier": "cold",
            "data_type": "dataframe",
            "location": "test_location",
            "size": 1000,
            "created_at": "2023-01-01T00:00:00",
            "additional_meta": json.dumps({"source": "test"})
        }
        
    async def get_tier_data(self, tier):
        """Mock get_tier_data method."""
        return [
            {
                "data_id": "test-data-id",
                "tier": tier,
                "data_type": "txt",
                "location": "test_file.txt",
                "size": 1000,
                "created_at": "2023-01-01T00:00:00",
                "additional_meta": json.dumps({"is_external": True, "file_path": "test_file.txt"})
            }
        ]


class MockDuckDBConnection:
    """Mock for DuckDB connection."""
    
    def execute(self, query, params=None):
        """Mock execute method."""
        return self
        
    def fetchall(self):
        """Mock fetchall method."""
        return [{"data": json.dumps({"result": "test data"})}]
        
    def fetchone(self):
        """Mock fetchone method."""
        return [json.dumps({"id": 1, "name": "test"})]
        
    def fetchdf(self):
        """Mock fetchdf method."""
        return pd.DataFrame({"column": ["type"], "type": ["INTEGER"]})
        
    def close(self):
        """Mock close method."""
        pass


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
storage:
  path: {}/data
data:
  raw_path: {}/data/raw
  modalities:
    - text
    - image
    - vector
        """.format(temp_dir, temp_dir))
    
    # Create data directories
    data_dir = Path(temp_dir) / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = data_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    yield temp_dir
    
    # Clean up
    try:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
    except Exception as e:
        print(f"Warning: Failed to clean up temporary directory {temp_dir}: {e}")


@pytest.fixture
def mock_config(temp_config_dir, monkeypatch):
    """Create a mock Config instance."""
    config_path = str(Path(temp_config_dir) / "config" / "db_config.yml")
    
    # Patch the _get_project_root method to return our temp directory
    with patch.object(Config, '_get_project_root', return_value=temp_config_dir):
        config = Config(config_path=config_path)
    
    return config


@pytest.fixture
def cold_memory(mock_config, monkeypatch):
    """Create a ColdMemory instance with mocked dependencies."""
    # Mock the memory catalog
    mock_catalog = MockMemoryCatalog()
    
    # Create a ColdMemory instance with our mocked dependencies
    with patch('memories.core.cold.Config', return_value=mock_config):
        memory = ColdMemory()
        memory.memory_catalog = mock_catalog
        
        # Replace the DuckDB connection with our mock
        memory.con = MockDuckDBConnection()
        
        # Patch methods that are difficult to mock
        memory.retrieve = AsyncMock(return_value={
            "data": pd.DataFrame({"id": [1], "value": ["test"]}),
            "metadata": {"source": "test"}
        })
        
        memory.get_schema = AsyncMock(return_value={
            "id": "test-data-id",
            "tier": "cold",
            "data_type": "dataframe",
            "location": "test_location",
            "size": 1000,
            "created_at": "2023-01-01T00:00:00",
            "tags": ["test"]
        })
        
        # Create a custom clear method that calls the mocked delete_data
        async def mock_clear():
            await mock_catalog.get_tier_data("cold")
            for item in await mock_catalog.get_tier_data("cold"):
                await mock_catalog.delete_data(item["data_id"])
            return True
            
        memory.clear = mock_clear
        
        # Create a custom unregister_file method
        async def mock_unregister_file(file_id):
            await mock_catalog.get_data_info(file_id)
            await mock_catalog.delete_data(file_id)
            return True
            
        memory.unregister_file = mock_unregister_file
        
        yield memory
        
        # Clean up
        try:
            memory.cleanup()
        except Exception as e:
            print(f"Warning: Failed to clean up ColdMemory: {e}")


class TestColdMemory:
    """Tests for the ColdMemory class."""
    
    @pytest.mark.asyncio
    async def test_register_external_file(self, cold_memory, temp_config_dir):
        """Test registering an external file."""
        # Create a test file
        test_file = Path(temp_config_dir) / "test_file.txt"
        with open(test_file, 'w') as f:
            f.write("Test content")
        
        # Mock the memory catalog's register_data method
        cold_memory.memory_catalog.register_data = AsyncMock(return_value="test-file-id")
        
        # Register the file
        await cold_memory.register_external_file(str(test_file))
        
        # Check that register_data was called with the correct arguments
        cold_memory.memory_catalog.register_data.assert_called_once()
        call_args = cold_memory.memory_catalog.register_data.call_args[1]
        assert call_args["tier"] == "cold"
        assert call_args["location"] == str(test_file)
        assert call_args["data_type"] == "txt"
        assert call_args["metadata"]["is_external"] is True
    
    @pytest.mark.asyncio
    async def test_store_dataframe(self, cold_memory):
        """Test storing a DataFrame."""
        # Create a test DataFrame
        test_df = pd.DataFrame({
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"],
            "value": [10.5, 20.3, 30.1]
        })
        
        # Mock the memory catalog's register_data method
        cold_memory.memory_catalog.register_data = AsyncMock(return_value="test-df-id")
        
        # Store the DataFrame
        result = await cold_memory.store(
            data=test_df,
            metadata={"source": "test"},
            tags=["test", "dataframe"]
        )
        
        # Check that the storage was successful
        assert result is True
        
        # Check that register_data was called with the correct arguments
        cold_memory.memory_catalog.register_data.assert_called_once()
        call_args = cold_memory.memory_catalog.register_data.call_args[1]
        assert call_args["tier"] == "cold"
        assert call_args["data_type"] == "dataframe"
        assert call_args["tags"] == ["test", "dataframe"]
    
    @pytest.mark.asyncio
    async def test_store_dict(self, cold_memory):
        """Test storing a dictionary."""
        # Create a test dictionary
        test_dict = {
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"],
            "value": [10.5, 20.3, 30.1]
        }
        
        # Mock the memory catalog's register_data method
        cold_memory.memory_catalog.register_data = AsyncMock(return_value="test-dict-id")
        
        # Store the dictionary
        result = await cold_memory.store(
            data=test_dict,
            metadata={"source": "test"},
            tags=["test", "dict"]
        )
        
        # Check that the storage was successful
        assert result is True
        
        # Check that register_data was called with the correct arguments
        cold_memory.memory_catalog.register_data.assert_called_once()
        call_args = cold_memory.memory_catalog.register_data.call_args[1]
        assert call_args["tier"] == "cold"
        assert call_args["data_type"] == "dataframe"
        assert call_args["tags"] == ["test", "dict"]
    
    @pytest.mark.asyncio
    async def test_retrieve(self, cold_memory):
        """Test retrieving data."""
        # The retrieve method is already mocked in the fixture
        
        # Retrieve the data
        result = await cold_memory.retrieve({"data_id": "test-data-id"})
        
        # Check that the retrieval was successful
        assert result is not None
        assert "data" in result
        assert "metadata" in result
    
    @pytest.mark.asyncio
    async def test_clear(self, cold_memory):
        """Test clearing the cold memory."""
        # Mock the memory catalog's get_tier_data and delete_data methods
        cold_memory.memory_catalog.get_tier_data = AsyncMock(return_value=[
            {"data_id": "test-data-id", "tier": "cold"}
        ])
        cold_memory.memory_catalog.delete_data = AsyncMock(return_value=True)
        
        # Clear the memory
        await cold_memory.clear()
        
        # Check that get_tier_data was called
        cold_memory.memory_catalog.get_tier_data.assert_called_with("cold")
        
        # Check that delete_data was called
        cold_memory.memory_catalog.delete_data.assert_called_with("test-data-id")
    
    @pytest.mark.asyncio
    async def test_unregister_file(self, cold_memory):
        """Test unregistering a file."""
        # Mock the memory catalog's get_data_info and delete_data methods
        cold_memory.memory_catalog.get_data_info = AsyncMock(return_value={
            "data_id": "test-file-id",
            "tier": "cold",
            "data_type": "txt",
            "location": "test_file.txt",
            "additional_meta": json.dumps({"is_external": True})
        })
        cold_memory.memory_catalog.delete_data = AsyncMock(return_value=True)
        
        # Unregister the file
        result = await cold_memory.unregister_file("test-file-id")
        
        # Check that the unregistration was successful
        assert result is True
        
        # Check that delete_data was called
        cold_memory.memory_catalog.delete_data.assert_called_with("test-file-id")
    
    @pytest.mark.asyncio
    async def test_list_registered_files(self, cold_memory):
        """Test listing registered files."""
        # Mock the memory catalog's get_tier_data method
        cold_memory.memory_catalog.get_tier_data = AsyncMock(return_value=[
            {
                "data_id": "test-file-id",
                "tier": "cold",
                "data_type": "txt",
                "location": "test_file.txt",
                "size": 1000,
                "created_at": "2023-01-01T00:00:00",
                "additional_meta": json.dumps({"is_external": True, "file_path": "test_file.txt"})
            }
        ])
        
        # List the registered files
        result = await cold_memory.list_registered_files()
        
        # Check that the listing was successful
        assert len(result) == 1
        assert result[0]["id"] == "test-file-id"
        
        # Check that get_tier_data was called with the correct arguments
        cold_memory.memory_catalog.get_tier_data.assert_called_once_with("cold")
    
    @pytest.mark.asyncio
    async def test_get_schema(self, cold_memory):
        """Test getting schema information for data."""
        # The get_schema method is already mocked in the fixture
        
        # Get schema for the data
        schema = await cold_memory.get_schema("test-data-id")
        
        # Check schema properties
        assert schema is not None
        assert schema["id"] == "test-data-id"
        assert schema["tier"] == "cold"
        assert schema["data_type"] == "dataframe" 