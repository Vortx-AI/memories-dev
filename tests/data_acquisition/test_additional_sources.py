"""
Test additional source implementations functionality.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
import numpy as np
import aiohttp
import json
from datetime import datetime
from shapely.geometry import box, Polygon
import asyncio
from memories.data_acquisition.sources import (
    WFSAPI,
    SentinelAPI,
    LandsatAPI,
    OvertureAPI,
    OSMDataAPI,
    PlanetaryCompute
)

@pytest.fixture
def bbox():
    """Sample bounding box for testing."""
    return [-122.5, 37.5, -122.0, 38.0]  # San Francisco area

@pytest.fixture
def date_range():
    """Sample date range for testing."""
    return {
        'start_date': datetime(2023, 1, 1),
        'end_date': datetime(2023, 1, 31)
    }

@pytest.fixture
def wfs_api(tmp_path):
    """Create a WFS API instance."""
    return WFSAPI(cache_dir=str(tmp_path))

@pytest.fixture
def sentinel_api(tmp_path):
    """Create a Sentinel API instance."""
    return SentinelAPI(data_dir=str(tmp_path))

@pytest.fixture
def landsat_api(tmp_path):
    """Create a Landsat API instance."""
    return LandsatAPI(cache_dir=str(tmp_path))

@pytest.fixture
def overture_api(tmp_path):
    """Create an Overture API instance."""
    return OvertureAPI(data_dir=str(tmp_path))

@pytest.fixture
def osm_api(tmp_path):
    """Create an OSM API instance."""
    return OSMDataAPI(cache_dir=str(tmp_path))

@pytest.fixture
def planetary_compute(tmp_path):
    """Create a Planetary Compute instance."""
    return PlanetaryCompute(cache_dir=str(tmp_path))





@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling across different sources."""
    api = WFSAPI(cache_dir='test')
    
    # Test invalid bbox
    with pytest.raises(ValueError):
        await api.search(
            bbox=[0],  # Invalid bbox
            layer='test'
        )
    
    # Test invalid layer
    with pytest.raises(ValueError):
        await api.search(
            bbox=[-122.5, 37.5, -122.0, 38.0],
            layer=''  # Empty layer name
        )


@pytest.mark.asyncio
async def test_concurrent_operations(wfs_api, bbox):
    """Test concurrent operations."""
    # Create multiple concurrent requests
    requests = []
    for i in range(3):
        modified_bbox = [x + i * 0.1 for x in bbox]
        requests.append(
            wfs_api.search(
                bbox=modified_bbox,
                layer='test'
            )
        )
    
    # Execute requests concurrently
    results = await asyncio.gather(*requests)
    
    assert len(results) == 3
    assert all(isinstance(r, dict) for r in results)

def test_cleanup(wfs_api, tmp_path):
    """Test cleanup of temporary files."""
    # Create test files
    test_files = [
        tmp_path / "test1.geojson",
        tmp_path / "test2.geojson",
        tmp_path / "test3.geojson"
    ]
    
    for file in test_files:
        file.touch()
    
    # Run cleanup
    wfs_api._cleanup_files(test_files)
    
    # Verify files are removed
    for file in test_files:
        assert not file.exists() 