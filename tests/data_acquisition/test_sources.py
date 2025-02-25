"""
Test source implementations functionality.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
import numpy as np
import aiohttp
import json
from datetime import datetime
from shapely.geometry import box
import asyncio
from memories.data_acquisition.sources import (
    SentinelAPI,
    OvertureAPI,
    OSMDataAPI,
    PlanetaryCompute
)

@pytest.fixture
def bbox():
    """Sample bounding box for testing."""
    return {
        'xmin': -122.5,
        'ymin': 37.5,
        'xmax': -122.0,
        'ymax': 38.0
    }

@pytest.fixture
def date_range():
    """Sample date range for testing."""
    return {
        'start_date': datetime(2023, 1, 1),
        'end_date': datetime(2023, 1, 31)
    }

@pytest.fixture
def sentinel_api(tmp_path):
    """Create a Sentinel API instance."""
    return SentinelAPI(data_dir=str(tmp_path))

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
    api = SentinelAPI(data_dir='test')
    
    # Test invalid bbox
    with pytest.raises(ValueError):
        await api.download_data(
            bbox={'xmin': 0, 'ymin': 0, 'xmax': 0, 'ymax': 0},  # Invalid bbox
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 1, 31)
        )
    
    # Test invalid date range
    with pytest.raises(ValueError):
        await api.download_data(
            bbox={'xmin': -122.5, 'ymin': 37.5, 'xmax': -122.0, 'ymax': 38.0},
            start_date=datetime(2023, 1, 31),
            end_date=datetime(2023, 1, 1)  # End date before start date
        )

@pytest.mark.asyncio
async def test_concurrent_operations(sentinel_api, bbox):
    """Test concurrent operations."""
    # Create multiple concurrent requests
    requests = []
    for i in range(3):
        modified_bbox = {
            'xmin': bbox['xmin'] + i * 0.1,
            'ymin': bbox['ymin'] + i * 0.1,
            'xmax': bbox['xmax'] + i * 0.1,
            'ymax': bbox['ymax'] + i * 0.1
        }
        requests.append(
            sentinel_api.download_data(
                bbox=modified_bbox,
                start_date=datetime(2023, 1, 1),
                end_date=datetime(2023, 1, 31)
            )
        )
    
    # Execute requests concurrently
    results = await asyncio.gather(*requests)
    
    assert len(results) == 3
    assert all(isinstance(r, dict) for r in results) 