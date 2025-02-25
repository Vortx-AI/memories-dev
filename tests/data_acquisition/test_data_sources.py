"""Tests for data source implementations."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import numpy as np
import rasterio
from datetime import datetime
from pathlib import Path
import asyncio

from memories.data_acquisition.sources import SentinelAPI

@pytest.fixture
def mock_rasterio_env():
    """Mock rasterio environment."""
    with patch('rasterio.Env') as mock:
        yield mock

@pytest.fixture
def mock_rasterio_open():
    """Mock rasterio.open context manager."""
    mock_dataset = MagicMock()
    mock_dataset.bounds = (-122.4, 37.7, -122.3, 37.8)
    mock_dataset.width = 1000
    mock_dataset.height = 1000
    mock_dataset.crs.to_epsg.return_value = 4326
    mock_dataset.transform = (0.0001, 0, -122.4, 0, -0.0001, 37.8)
    mock_dataset.profile = {
        'count': 1,
        'dtype': 'uint16',
        'height': 1000,
        'width': 1000,
        'transform': mock_dataset.transform,
        'crs': mock_dataset.crs
    }
    mock_dataset.read.return_value = np.random.randint(0, 10000, (100, 100), dtype=np.uint16)

    with patch('rasterio.open') as mock_open:
        mock_open.return_value.__enter__.return_value = mock_dataset
        yield mock_open

@pytest.fixture
def sentinel_api(tmp_path):
    """Create a Sentinel API instance."""
    return SentinelAPI(data_dir=str(tmp_path))

@pytest.fixture
def bbox():
    """Sample bounding box for testing."""
    return {
        'xmin': -122.4018,
        'ymin': 37.7914,
        'xmax': -122.3928,
        'ymax': 37.7994
    }

@pytest.mark.asyncio
async def test_sentinel_download(sentinel_api, bbox, mock_rasterio_open, mock_rasterio_env):
    """Test Sentinel data download."""
    with patch('planetary_computer.sign', return_value="https://example.com/signed.tif"), \
         patch('pystac_client.Client.open') as mock_client:
        
        # Mock STAC search results
        mock_item = MagicMock()
        mock_item.id = "test_scene"
        mock_item.properties = {
            "datetime": "2023-01-01T00:00:00Z",
            "eo:cloud_cover": 5.0,
            "platform": "sentinel-2a"
        }
        mock_item.assets = {
            "B04": MagicMock(href="https://example.com/B04.tif"),
            "B08": MagicMock(href="https://example.com/B08.tif")
        }
        
        mock_search = MagicMock()
        mock_search.get_items.return_value = [mock_item]
        mock_client.return_value.search.return_value = mock_search
        
        result = await sentinel_api.download_data(
            bbox=bbox,
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 1, 31)
        )
        
        assert result["success"] is True
        assert "metadata" in result
        assert result["metadata"]["scene_id"] == "test_scene"

@pytest.mark.asyncio
async def test_concurrent_downloads(sentinel_api, bbox, mock_rasterio_open, mock_rasterio_env):
    """Test concurrent downloads."""
    with patch('planetary_computer.sign', return_value="https://example.com/signed.tif"), \
         patch('pystac_client.Client.open') as mock_client:
        
        # Mock STAC search results
        mock_item = MagicMock()
        mock_item.id = "test_scene"
        mock_item.properties = {
            "datetime": "2023-01-01T00:00:00Z",
            "eo:cloud_cover": 5.0,
            "platform": "sentinel-2a"
        }
        mock_item.assets = {
            "B04": MagicMock(href="https://example.com/B04.tif"),
            "B08": MagicMock(href="https://example.com/B08.tif")
        }
        
        mock_search = MagicMock()
        mock_search.get_items.return_value = [mock_item]
        mock_client.return_value.search.return_value = mock_search
        
        tasks = []
        for i in range(3):
            tasks.append(
                sentinel_api.download_data(
                    bbox=bbox,
                    start_date=datetime(2023, 1, 1),
                    end_date=datetime(2023, 1, 31)
                )
            )
        
        results = await asyncio.gather(*tasks)
        assert len(results) == 3
        assert all(r["success"] for r in results) 