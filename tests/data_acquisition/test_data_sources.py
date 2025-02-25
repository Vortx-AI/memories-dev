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
    
    with patch('planetary_computer.sign', return_value="https://example.com/signed.tif"), \
         patch('pystac_client.Client.open') as mock_client:
        
        # Mock STAC item
        mock_item = MagicMock()
        mock_item.id = "test_scene"
        mock_item.properties = {
            "datetime": "2023-01-01T00:00:00Z",
            "eo:cloud_cover": 5.0,
            "platform": "sentinel-2a"
        }
        mock_item.assets = {
            "B04": MagicMock(href="https://example.com/B04.tif"),
            "B08": MagicMock(href="https://example.com/B08.tif"),
            "B11": MagicMock(href="https://example.com/B11.tif")
        }
        
        # Mock search results
        mock_search = MagicMock()
        mock_search.get_items.return_value = [mock_item]
        mock_client.return_value.search.return_value = mock_search
        
        result = await api.download_data(
            bbox=bbox,
            start_date=date_range['start_date'],
            end_date=date_range['end_date'],
            cloud_cover=10.0
        )
        
        assert "metadata" in result
        assert result["metadata"]["scene_id"] == "test_scene"
        assert result["metadata"]["cloud_cover"] == 5.0

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
    
    result = await api.download_data(
        bbox=invalid_bbox,
        start_date=datetime.now() - timedelta(days=30),
        end_date=datetime.now(),
        cloud_cover=10.0
    )
    
    assert result["status"] == "no_data"
    assert "No suitable imagery found" in result["message"]

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
            bands={"B04": "Red", "B08": "NIR"}
        )
        for bbox in bboxes
    ]
    
    results = await asyncio.gather(*tasks)
    
    # Verify results
    for result in results:
        assert isinstance(result, dict)
        assert "status" in result 