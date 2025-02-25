"""Tests for data source APIs."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
import asyncio

from memories.data_acquisition.sources.sentinel_api import SentinelAPI

@pytest.fixture
def bbox():
    """Sample bounding box for testing."""
    return {
        'xmin': -122.4018,
        'ymin': 37.7914,
        'xmax': -122.3928,
        'ymax': 37.7994
    }

@pytest.fixture
def date_range():
    """Sample date range for testing."""
    return {
        'start_date': datetime.now() - timedelta(days=30),
        'end_date': datetime.now()
    }

@pytest.mark.asyncio
async def test_sentinel_download(tmp_path, bbox, date_range):
    """Test Sentinel data download."""
    api = SentinelAPI(data_dir=str(tmp_path))
    
    # Create a mock geometry object
    mock_geom = MagicMock()
    mock_geom.wkt = "POLYGON ((-122.4018 37.7914, -122.4018 37.7994, -122.3928 37.7994, -122.3928 37.7914, -122.4018 37.7914))"
    
    # Create a mock client
    mock_client_instance = MagicMock()
    mock_search = MagicMock()
    mock_item = MagicMock()
    mock_item.id = "test_scene"
    mock_item.properties = {
        "datetime": "2023-01-01T00:00:00Z",
        "eo:cloud_cover": 5.0,
        "platform": "sentinel-2a",
        "processing:level": "L2A"
    }
    mock_item.assets = {
        "B04": MagicMock(href="https://example.com/B04.tif"),
        "B08": MagicMock(href="https://example.com/B08.tif")
    }
    mock_item.bbox = [-122.4018, 37.7914, -122.3928, 37.7994]
    
    # Set up the mock chain
    mock_search.get_items.return_value = [mock_item]
    mock_client_instance.search.return_value = mock_search
    mock_client = MagicMock(return_value=mock_client_instance)
    
    # Mock the sign_inplace function
    mock_sign_inplace = MagicMock()
    mock_sign_inplace.return_value = mock_client_instance
    
    with patch('planetary_computer.sign', return_value="https://example.com/signed.tif"), \
         patch('planetary_computer.sign_inplace', mock_sign_inplace), \
         patch('pystac_client.Client.open', mock_client), \
         patch.object(api, 'fetch_windowed_band', return_value=True), \
         patch('shapely.geometry.box', return_value=mock_geom):
        
        # Initialize the API
        await api.initialize()
        
        result = await api.download_data(
            bbox=bbox,
            start_date=date_range['start_date'],
            end_date=date_range['end_date'],
            cloud_cover=10.0
        )
        
        print("Result:", result)  # Debug print
        
        assert result["status"] == "success"
        assert result["scene_id"] == "test_scene"
        assert result["cloud_cover"] == 5.0
        assert "metadata" in result
        assert result["metadata"]["acquisition_date"] == "2023-01-01T00:00:00Z"
        assert result["metadata"]["platform"] == "sentinel-2a"
        assert result["metadata"]["processing_level"] == "L2A"
        assert result["metadata"]["bbox"] == [-122.4018, 37.7914, -122.3928, 37.7994]
        assert result["bands"] == ["B04", "B08"]

@pytest.mark.asyncio
async def test_error_handling(tmp_path):
    """Test error handling in data sources."""
    api = SentinelAPI(data_dir=str(tmp_path))
    
    # Test with invalid bbox
    invalid_bbox = {
        'xmin': 0,
        'ymin': 0,
        'xmax': 0,
        'ymax': 0
    }
    
    with pytest.raises(ValueError) as exc_info:
        await api.download_data(
            bbox=invalid_bbox,
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now(),
            cloud_cover=10.0
        )
    
    assert "Invalid bbox: min coordinates must be less than max coordinates" in str(exc_info.value)

@pytest.mark.asyncio
async def test_concurrent_operations(tmp_path):
    """Test concurrent operations."""
    api = SentinelAPI(data_dir=str(tmp_path))
    
    # Create multiple bounding boxes
    bboxes = [
        {
            'xmin': -122.0,
            'ymin': 37.5,
            'xmax': -121.5,
            'ymax': 38.0
        },
        {
            'xmin': -121.9,
            'ymin': 37.6,
            'xmax': -121.4,
            'ymax': 38.1
        },
        {
            'xmin': -121.8,
            'ymin': 37.7,
            'xmax': -121.3,
            'ymax': 38.2
        }
    ]
    
    # Test concurrent downloads
    tasks = [
        api.download_data(
            bbox=bbox,
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now(),
            cloud_cover=10.0,
            bands=["B04", "B08"]
        )
        for bbox in bboxes
    ]
    
    results = await asyncio.gather(*tasks)
    
    # Verify results
    for result in results:
        assert isinstance(result, dict)
        assert "status" in result 