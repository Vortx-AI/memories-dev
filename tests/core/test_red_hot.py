"""
Tests for the RedHotMemory class in the core.red_hot module.
"""

import os
import pytest
import numpy as np
import tempfile
import shutil
from pathlib import Path
import asyncio

from memories.core.red_hot import RedHotMemory


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
def red_hot_memory(temp_storage_path):
    """Create a RedHotMemory instance for testing."""
    memory = RedHotMemory(dimension=128, storage_path=temp_storage_path)
    yield memory
    # Clean up
    memory.cleanup()


class TestRedHotMemory:
    """Tests for the RedHotMemory class."""

    def test_initialization(self, temp_storage_path):
        """Test that RedHotMemory initializes correctly."""
        memory = RedHotMemory(dimension=128, storage_path=temp_storage_path)
        
        # Check that the storage directory was created
        assert Path(temp_storage_path).exists()
        
        # Check that the dimension was set correctly
        assert memory.dimension == 128
        
        # Check that the metadata is initialized
        assert memory.metadata == {}

    @pytest.mark.asyncio
    async def test_store_and_retrieve(self, red_hot_memory):
        """Test storing and retrieving vectors."""
        # Create a test vector
        test_vector = np.random.rand(128).astype(np.float32)
        test_metadata = {"source": "test", "importance": "high"}
        test_tags = ["test", "important"]
        
        # Store the vector
        result = await red_hot_memory.store(
            data=test_vector,
            metadata=test_metadata,
            tags=test_tags
        )
        assert result is True
        
        # Retrieve the vector
        retrieved = await red_hot_memory.retrieve(query_vector=test_vector, k=1)
        
        # Check that we got a result
        assert retrieved is not None
        assert len(retrieved) == 1
        
        # Check that the metadata and tags were stored correctly
        assert retrieved[0]["metadata"] == test_metadata
        assert retrieved[0]["tags"] == test_tags
        
        # Check that the distance is close to 0 (exact match)
        assert retrieved[0]["distance"] < 1e-5

    @pytest.mark.asyncio
    async def test_retrieve_with_tags(self, red_hot_memory):
        """Test retrieving vectors filtered by tags."""
        # Create and store two test vectors with different tags
        vector1 = np.random.rand(128).astype(np.float32)
        vector2 = np.random.rand(128).astype(np.float32)
        
        await red_hot_memory.store(
            data=vector1,
            metadata={"id": "vector1"},
            tags=["tag1", "common"]
        )
        
        await red_hot_memory.store(
            data=vector2,
            metadata={"id": "vector2"},
            tags=["tag2", "common"]
        )
        
        # Retrieve with tag1 filter
        retrieved = await red_hot_memory.retrieve(
            query_vector=vector1,
            k=2,
            tags=["tag1"]
        )
        
        # Should only get vector1
        assert len(retrieved) == 1
        assert retrieved[0]["metadata"]["id"] == "vector1"
        
        # Retrieve with common tag filter
        retrieved = await red_hot_memory.retrieve(
            query_vector=vector1,
            k=2,
            tags=["common"]
        )
        
        # Should get both vectors
        assert len(retrieved) == 2

    @pytest.mark.asyncio
    async def test_clear(self, red_hot_memory):
        """Test clearing the memory."""
        # Store a vector
        test_vector = np.random.rand(128).astype(np.float32)
        await red_hot_memory.store(data=test_vector)
        
        # Clear the memory
        red_hot_memory.clear()
        
        # Check that the metadata is empty
        assert red_hot_memory.metadata == {}
        
        # Try to retrieve the vector (should return None)
        retrieved = await red_hot_memory.retrieve(query_vector=test_vector, k=1)
        assert not retrieved

    @pytest.mark.asyncio
    async def test_get_schema(self, red_hot_memory):
        """Test getting schema information for a vector."""
        # Store a vector
        test_vector = np.random.rand(128).astype(np.float32)
        test_metadata = {"source": "test"}
        test_tags = ["test"]
        
        await red_hot_memory.store(
            data=test_vector,
            metadata=test_metadata,
            tags=test_tags
        )
        
        # Get schema for the vector
        schema = await red_hot_memory.get_schema(vector_id=0)
        
        # Check schema properties
        assert schema is not None
        assert schema["dimension"] == 128
        assert schema["type"] == "vector"
        assert schema["source"] == "faiss"
        assert schema["metadata"] == test_metadata
        assert schema["tags"] == test_tags

    def test_list_input(self, red_hot_memory):
        """Test that the store method accepts list inputs."""
        # Create a test vector as a list
        test_vector = list(np.random.rand(128).astype(np.float32))
        
        # Store the vector with metadata to ensure it's returned in results
        # (RedHotMemory.retrieve() only returns results with metadata)
        result = asyncio.run(red_hot_memory.store(
            data=test_vector,
            metadata={"source": "test"},
            tags=["test"]
        ))
        assert result is True
        
        # Retrieve the vector
        retrieved = asyncio.run(red_hot_memory.retrieve(query_vector=test_vector, k=1))
        
        # Check that we got a result
        assert retrieved is not None
        assert len(retrieved) == 1
        
        # Check that the distance is close to 0 (exact match)
        assert retrieved[0]["distance"] < 1e-5 