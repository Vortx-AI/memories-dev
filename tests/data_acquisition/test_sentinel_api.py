"""Tests for Sentinel API functionality."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock, PropertyMock
import numpy as np
import rasterio
from datetime import datetime
from pathlib import Path
import planetary_computer
import pystac_client
from pystac.item import Item
from rasterio.transform import Affine
from rasterio.windows import Window

from memories.data_acquisition.sources.sentinel_api import SentinelAPI

@pytest.fixture
def mock_rasterio_env():
    """Mock rasterio environment."""
    with patch('rasterio.Env') as mock:
        yield mock

@pytest.fixture
def mock_rasterio_open():
    """Mock rasterio.open context manager."""
    mock_dataset = MagicMock()
    
    # Set up bounds and dimensions
    mock_dataset.bounds = (-122.4, 37.7, -122.3, 37.8)
    mock_dataset.width = 1000
    mock_dataset.height = 1000
    
    # Set up CRS
    mock_crs = MagicMock()
    mock_crs.to_epsg.return_value = 4326
    type(mock_dataset).crs = PropertyMock(return_value=mock_crs)
    
    # Create a proper Affine transform object
    transform = Affine(0.0001, 0, -122.4, 0, -0.0001, 37.8)
    type(mock_dataset).transform = PropertyMock(return_value=transform)
    
    # Set up profile with transform
    mock_dataset.profile = {
        'count': 1,
        'dtype': 'uint16',
        'height': 1000,
        'width': 1000,
        'transform': transform,
        'crs': mock_crs
    }
    
    # Mock read method to return random data
    mock_dataset.read.return_value = np.random.randint(0, 10000, (1, 100, 100), dtype=np.uint16)
    
    # Mock window reading
    def mock_read_with_window(band_index, window=None, out_shape=None, **kwargs):
        if window is None:
            window = Window(0, 0, mock_dataset.width, mock_dataset.height)
        if out_shape is None:
            out_shape = (window.height, window.width)
        return np.random.randint(0, 10000, (1, *out_shape), dtype=np.uint16)
        
    mock_dataset.read = mock_read_with_window

    with patch('rasterio.open') as mock_open:
        mock_open.return_value.__enter__.return_value = mock_dataset
        yield mock_open

@pytest.fixture
def mock_stac_item():
    """Create a mock STAC item."""
    item = MagicMock(spec=Item)
    item.id = "test_scene"
    item.properties = {
        "datetime": "2023-01-01T00:00:00Z",
        "eo:cloud_cover": 5.0,
        "platform": "sentinel-2a"
    }
    item.assets = {
        "B04": MagicMock(href="https://example.com/B04.tif"),
        "B08": MagicMock(href="https://example.com/B08.tif")
    }
    return item

@pytest.fixture
def mock_pc_client(mock_stac_item):
    """Mock Planetary Computer client."""
    mock_search = MagicMock()
    mock_search.get_items.return_value = [mock_stac_item]
    
    mock_client = MagicMock()
    mock_client.search.return_value = mock_search
    
    with patch('pystac_client.Client.open', return_value=mock_client):
        yield mock_client

@pytest.fixture
def api(tmp_path):
    """Create SentinelAPI instance for testing."""
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
async def test_download_data_success(api, bbox, mock_pc_client, mock_rasterio_open, mock_rasterio_env):
    """Test successful data download."""
    with patch('planetary_computer.sign', return_value="https://example.com/signed.tif"):
        result = await api.download_data(
            bbox=bbox,
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 1, 31),
            cloud_cover=10.0,
            bands={
                "B04": "Red",
                "B08": "NIR",
                "B11": "SWIR"
            }
        )
        
        assert isinstance(result, dict)
        assert "metadata" in result
        assert result["metadata"]["scene_id"] == "test_scene"
        assert result["metadata"]["cloud_cover"] == 5.0
        assert set(result["metadata"]["bands_downloaded"]) == {"B04", "B08", "B11"}

@pytest.mark.asyncio
async def test_download_data_no_scenes(api, bbox, mock_pc_client):
    """Test download with no available scenes."""
    mock_pc_client.search.return_value.get_items.return_value = []
    
    result = await api.download_data(
        bbox=bbox,
        start_date=datetime(2023, 1, 1),
        end_date=datetime(2023, 1, 31),
        cloud_cover=10.0,
        bands={
            "B04": "Red",
            "B08": "NIR",
            "B11": "SWIR"
        }
    )
    
    assert result["status"] == "no_data"
    assert "No suitable imagery found" in result["message"]

@pytest.mark.asyncio
async def test_fetch_windowed_band_success(api, bbox, mock_rasterio_open, mock_rasterio_env):
    """Test successful band download."""
    with patch('planetary_computer.sign', return_value="https://example.com/signed.tif"):
        result = await api.fetch_windowed_band(
            url="https://example.com/B04.tif",
            bbox=bbox,
            band_name="B04"
        )
        assert result is True

@pytest.mark.asyncio
async def test_fetch_windowed_band_failure(api, bbox):
    """Test band download failure."""
    with patch('planetary_computer.sign', side_effect=Exception("Sign failed")):
        result = await api.fetch_windowed_band(
            url="https://example.com/B04.tif",
            bbox=bbox,
            band_name="B04"
        )
        assert result is False

@pytest.mark.asyncio
async def test_download_data_with_invalid_band(api, bbox, mock_pc_client, mock_rasterio_open):
    """Test download with invalid band."""
    result = await api.download_data(
        bbox=bbox,
        start_date=datetime(2023, 1, 1),
        end_date=datetime(2023, 1, 31),
        cloud_cover=10.0,
        bands={"invalid_band": "Invalid"}
    )
    
    assert "error" in result
    assert "No valid bands to download" in result["error"]

@pytest.mark.asyncio
async def test_download_data_with_custom_bands(api, bbox, mock_pc_client, mock_rasterio_open, mock_rasterio_env):
    """Test download with custom band selection."""
    with patch('planetary_computer.sign', return_value="https://example.com/signed.tif"):
        result = await api.download_data(
            bbox=bbox,
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 1, 31),
            cloud_cover=10.0,
            bands={
                "B04": "Red",
                "B08": "NIR"
            }
        )
        
        assert isinstance(result, dict)
        assert "metadata" in result
        assert set(result["metadata"]["bands_downloaded"]) == {"B04", "B08"}
        assert "B11" not in result["metadata"]["bands_downloaded"]
        assert result["metadata"]["scene_id"] == "test_scene"
        assert result["metadata"]["cloud_cover"] == 5.0 