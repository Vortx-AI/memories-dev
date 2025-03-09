"""Tests for memory catalog functionality."""

import pytest
import duckdb
import json
from datetime import datetime
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np

from memories.core.memory_catalog import MemoryCatalog, memory_catalog

@pytest.fixture
def catalog():
    """Create a fresh memory catalog instance for each test."""
    # Reset the singleton instance
    MemoryCatalog._instance = None
    catalog = MemoryCatalog()
    yield catalog
    # Cleanup after test
    catalog.cleanup()

@pytest.mark.asyncio
async def test_register_data(catalog):
    """Test registering data in the catalog."""
    # Test data
    tier = "cold"
    location = "cold/20240309_123456"
    size = 1024
    data_type = "dataframe"
    tags = ["test", "data"]
    metadata = {"source": "test"}
    
    # Register data
    data_id = await catalog.register_data(
        tier=tier,
        location=location,
        size=size,
        data_type=data_type,
        tags=tags,
        metadata=metadata
    )
    
    # Verify data was registered
    result = catalog.con.execute("""
        SELECT * FROM memory_catalog
        WHERE data_id = ?
    """, [data_id]).fetchone()
    
    assert result is not None
    assert result[1] == tier  # primary_tier
    assert result[2] == location  # location
    assert result[6] == size  # size
    assert result[8] == data_type  # data_type
    assert result[7] == "test,data"  # tags
    assert json.loads(result[9]) == metadata  # additional_meta

@pytest.mark.asyncio
async def test_update_access(catalog):
    """Test updating access time and count."""
    # First register some data
    data_id = await catalog.register_data(
        tier="hot",
        location="hot/test",
        size=100,
        data_type="dict"
    )
    
    # Get initial access count
    initial = await catalog.get_data_info(data_id)
    initial_count = initial['access_count']
    initial_access = initial['last_accessed']
    
    # Update access
    await catalog.update_access(data_id)
    
    # Get updated info
    updated = await catalog.get_data_info(data_id)
    
    assert updated['access_count'] == initial_count + 1
    assert updated['last_accessed'] > initial_access

@pytest.mark.asyncio
async def test_get_data_info(catalog):
    """Test retrieving data information."""
    # Register test data
    data_id = await catalog.register_data(
        tier="warm",
        location="warm/test",
        size=512,
        data_type="array",
        tags=["test"],
        metadata={"description": "test data"}
    )
    
    # Get data info
    info = await catalog.get_data_info(data_id)
    
    assert info is not None
    assert info['data_id'] == data_id
    assert info['primary_tier'] == "warm"
    assert info['location'] == "warm/test"
    assert info['size'] == 512
    assert info['data_type'] == "array"
    assert info['tags'] == "test"
    assert json.loads(info['additional_meta']) == {"description": "test data"}

@pytest.mark.asyncio
async def test_search_by_tags(catalog):
    """Test searching data by tags."""
    # Register multiple data items with different tags
    await catalog.register_data(
        tier="cold",
        location="cold/1",
        size=100,
        data_type="dict",
        tags=["tag1", "tag2"]
    )
    
    await catalog.register_data(
        tier="cold",
        location="cold/2",
        size=200,
        data_type="dict",
        tags=["tag2", "tag3"]
    )
    
    await catalog.register_data(
        tier="cold",
        location="cold/3",
        size=300,
        data_type="dict",
        tags=["tag3", "tag4"]
    )
    
    # Search by tag2
    results = await catalog.search_by_tags(["tag2"])
    assert len(results) == 2
    
    # Search by tag3
    results = await catalog.search_by_tags(["tag3"])
    assert len(results) == 2
    
    # Search by non-existent tag
    results = await catalog.search_by_tags(["nonexistent"])
    assert len(results) == 0

@pytest.mark.asyncio
async def test_register_data_with_different_types(catalog):
    """Test registering different types of data."""
    # Test with DataFrame
    df = pd.DataFrame({"test": [1, 2, 3]})
    data_id = await catalog.register_data(
        tier="cold",
        location="cold/df",
        size=df.memory_usage(deep=True).sum(),
        data_type="dataframe"
    )
    assert data_id is not None
    
    # Test with numpy array
    arr = np.array([1, 2, 3])
    data_id = await catalog.register_data(
        tier="red_hot",
        location="red_hot/array",
        size=arr.nbytes,
        data_type="array"
    )
    assert data_id is not None
    
    # Test with dictionary
    data = {"key": "value"}
    data_id = await catalog.register_data(
        tier="hot",
        location="hot/dict",
        size=1024,
        data_type="dict"
    )
    assert data_id is not None

@pytest.mark.asyncio
async def test_register_data_invalid_input(catalog):
    """Test registering data with invalid input."""
    # Test with missing required fields
    with pytest.raises(Exception):
        await catalog.register_data(
            tier="cold",
            location=None,  # Missing required field
            size=100,
            data_type="dict"
        )
    
    # Test with invalid tier
    with pytest.raises(Exception):
        await catalog.register_data(
            tier="invalid_tier",
            location="test",
            size=100,
            data_type="dict"
        )

@pytest.mark.asyncio
async def test_singleton_pattern():
    """Test that MemoryCatalog follows singleton pattern."""
    # Reset singleton instance
    MemoryCatalog._instance = None
    
    # Create two instances
    catalog1 = MemoryCatalog()
    catalog2 = MemoryCatalog()
    
    # Verify they are the same instance
    assert catalog1 is catalog2
    
    # Register data using first instance
    data_id = await catalog1.register_data(
        tier="cold",
        location="test",
        size=100,
        data_type="dict"
    )
    
    # Verify data can be retrieved using second instance
    info = await catalog2.get_data_info(data_id)
    assert info is not None
    assert info['data_id'] == data_id

@pytest.mark.asyncio
async def test_cleanup(catalog):
    """Test cleanup functionality."""
    # Register some data
    await catalog.register_data(
        tier="cold",
        location="test",
        size=100,
        data_type="dict"
    )
    
    # Verify connection is active
    assert catalog.con is not None
    
    # Cleanup
    catalog.cleanup()
    
    # Verify connection is closed
    with pytest.raises(Exception):
        catalog.con.execute("SELECT 1")

@pytest.mark.asyncio
async def test_get_tier_data(catalog):
    """Test retrieving all data for a specific tier."""
    # Register multiple data items in different tiers
    await catalog.register_data(
        tier="cold",
        location="cold/1",
        size=100,
        data_type="dict",
        tags=["tag1"],
        metadata={"order": 1}
    )
    
    await catalog.register_data(
        tier="cold",
        location="cold/2",
        size=200,
        data_type="dict",
        tags=["tag2"],
        metadata={"order": 2}
    )
    
    await catalog.register_data(
        tier="hot",
        location="hot/1",
        size=300,
        data_type="dict",
        tags=["tag3"],
        metadata={"order": 3}
    )
    
    # Get all data from cold tier
    cold_data = await catalog.get_tier_data("cold")
    assert len(cold_data) == 2
    for item in cold_data:
        assert item['primary_tier'] == "cold"
        assert item['data_type'] == "dict"
        assert isinstance(json.loads(item['additional_meta']), dict)
    
    # Get all data from hot tier
    hot_data = await catalog.get_tier_data("hot")
    assert len(hot_data) == 1
    assert hot_data[0]['primary_tier'] == "hot"
    assert hot_data[0]['size'] == 300
    
    # Test with empty tier
    warm_data = await catalog.get_tier_data("warm")
    assert len(warm_data) == 0
    
    # Test with invalid tier
    with pytest.raises(ValueError):
        await catalog.get_tier_data("invalid_tier") 