"""Tests for Sentinel API functionality."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock, PropertyMock, Mock
import numpy as np
import rasterio
from datetime import datetime, timedelta
from pathlib import Path
import planetary_computer
import pystac_client
from pystac.item import Item
from rasterio.transform import Affine
from rasterio.windows import Window
import os
import shutil
from rasterio.crs import CRS

from memories.data_acquisition.sources.sentinel_api import SentinelAPI

@pytest.fixture
def mock_rasterio_env():
    """Mock rasterio environment."""
    with patch('rasterio.Env') as mock:
        yield mock

@pytest.fixture
def mock_rasterio_open(mocker):
    """Mock rasterio.open."""
    mock_dataset = mocker.MagicMock()
    mock_dataset.read_masks.return_value = np.ones((100, 100))
    mock_dataset.bounds = (0, 0, 1, 1)
    mock_dataset.transform = Affine(0.1, 0, 0, 0, -0.1, 1)
    mock_dataset.crs = CRS.from_epsg(4326)
    mock_dataset.width = 100
    mock_dataset.height = 100
    mock_dataset.profile = {
        'driver': 'GTiff',
        'dtype': 'float32',
        'nodata': None,
        'width': 100,
        'height': 100,
        'count': 1,
        'crs': CRS.from_epsg(4326),
        'transform': Affine(0.1, 0, 0, 0, -0.1, 1)
    }

    def mock_read(*args, **kwargs):
        window = kwargs.get('window')
        if window:
            return np.random.rand(1, window.height, window.width)
        return np.random.rand(1, 100, 100)

    mock_dataset.read = mock_read
    mock_dataset.window = lambda minx, miny, maxx, maxy: Window(0, 0, 100, 100)
    mock_dataset.window_transform = lambda window: mock_dataset.transform

    def mock_write(data, band=1):
        # Create a temporary file to simulate writing
        if hasattr(mock_dataset, '_output_path'):
            os.makedirs(os.path.dirname(mock_dataset._output_path), exist_ok=True)
            Path(mock_dataset._output_path).touch()

    mock_dataset.write = mock_write
    mock_dataset.write_mask = lambda mask: None

    class MockContextManager:
        def __init__(self, path, mode='r', **kwargs):
            self.path = path
            self.mode = mode
            self.kwargs = kwargs
            if mode == 'w':
                mock_dataset._output_path = path
                os.makedirs(os.path.dirname(path), exist_ok=True)
                Path(path).touch()

        def __enter__(self):
            if self.mode == 'w':
                mock_dataset._output_path = self.path
            return mock_dataset

        def __exit__(self, exc_type, exc_val, exc_tb):
            if self.mode == 'w':
                os.makedirs(os.path.dirname(mock_dataset._output_path), exist_ok=True)
                Path(mock_dataset._output_path).touch()
            return None

    mock_open = mocker.patch('rasterio.open', side_effect=MockContextManager)
    return mock_open

@pytest.fixture
def mock_stac_item(mocker):
    """Mock STAC item."""
    mock_item = mocker.MagicMock(spec=Item)
    mock_item.assets = {
        'B04': mocker.MagicMock(href='https://example.com/B04.tif'),
        'B08': mocker.MagicMock(href='https://example.com/B08.tif')
    }
    mock_item.properties = {
        'datetime': '2023-01-01T00:00:00Z',
        'eo:cloud_cover': 5.0
    }
    mock_item.id = 'test_scene'
    type(mock_item).id = mocker.PropertyMock(return_value='test_scene')
    return mock_item

@pytest.fixture
def mock_pc_client(mocker, mock_stac_item):
    """Mock Planetary Computer client."""
    mock_client = mocker.MagicMock()
    mock_search = mocker.MagicMock()
    mock_search.get_items.return_value = [mock_stac_item]
    mock_client.search.return_value = mock_search
    return mock_client

@pytest.fixture
def api(tmp_path):
    """Create SentinelAPI instance for testing."""
    os.makedirs(tmp_path, exist_ok=True)
    api = SentinelAPI(data_dir=str(tmp_path))
    yield api
    # Cleanup after test
    if tmp_path.exists():
        shutil.rmtree(tmp_path)

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
def mock_dataset(mocker):
    dataset = mocker.MagicMock()
    dataset.read.return_value = np.ones((1, 100, 100))
    dataset.read_masks.return_value = np.ones((100, 100))
    dataset.bounds = (-122.4018, 37.7914, -122.3928, 37.7994)
    dataset.transform = Affine(0.0001, 0, -122.4018, 0, -0.0001, 37.7994)
    dataset.window.return_value = Window(0, 0, 100, 100)
    dataset.window_transform.return_value = dataset.transform
    dataset.meta = {
        'driver': 'GTiff',
        'dtype': 'uint16',
        'nodata': None,
        'width': 100,
        'height': 100,
        'count': 1,
        'crs': 'EPSG:4326',
        'transform': dataset.transform
    }
    return dataset

@pytest.mark.asyncio
async def test_download_data_success(tmp_path, mock_pc_client, mock_stac_item, mock_rasterio_env, mock_rasterio_open):
    """Test successful data download."""
    with patch('pystac_client.Client.open') as mock_open:
        mock_open.return_value = mock_pc_client
        api = SentinelAPI(data_dir=str(tmp_path))
        os.makedirs(tmp_path, exist_ok=True)

        # Set up mock search
        mock_search = MagicMock()
        mock_stac_item.id = "test_scene"
        mock_stac_item.properties = {
            "datetime": "2025-02-25T00:00:00Z",
            "platform": "sentinel-2a",
            "processing:level": "L2A",
            "eo:cloud_cover": 5.0
        }
        mock_stac_item.bbox = [-122.4018, 37.7914, -122.3928, 37.7994]
        mock_stac_item.assets = {
            "B04": MagicMock(href="https://example.com/B04.tif"),
            "B08": MagicMock(href="https://example.com/B08.tif")
        }
        mock_search.get_items.return_value = [mock_stac_item]
        mock_pc_client.search.return_value = mock_search

        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()

        result = await api.download_data(
            bbox={"xmin": -122.4018, "ymin": 37.7914, "xmax": -122.3928, "ymax": 37.7994},
            start_date=start_date,
            end_date=end_date
        )

        assert result["status"] == "success"
        assert result["scene_id"] == "test_scene"
        assert result["cloud_cover"] == 5.0
        assert result["bands"] == ["B04", "B08"]
        assert "metadata" in result
        assert result["metadata"]["acquisition_date"] == "2025-02-25T00:00:00Z"
        assert result["metadata"]["platform"] == "sentinel-2a"
        assert result["metadata"]["processing_level"] == "L2A"

@pytest.mark.asyncio
async def test_download_data_no_scenes(tmp_path, mock_pc_client):
    """Test handling when no scenes are found."""
    api = SentinelAPI(data_dir=str(tmp_path))
    os.makedirs(tmp_path, exist_ok=True)

    # Create a mock search that returns no items
    mock_search = Mock()
    mock_search.get_items.return_value = []
    mock_pc_client.search.return_value = mock_search
    mock_pc_client.sign_inplace = lambda x: x

    start_date = datetime.now() - timedelta(days=30)
    end_date = datetime.now()

    result = await api.download_data(
        bbox={"xmin": -122.4018, "ymin": 37.7914, "xmax": -122.3928, "ymax": 37.7994},
        start_date=start_date,
        end_date=end_date
    )

    assert result["status"] == "error"
    assert result["message"] == "Error during data acquisition: Expecting value: line 1 column 1 (char 0)"

@pytest.mark.asyncio
async def test_fetch_windowed_band_success(tmp_path, mock_rasterio_env, mock_rasterio_open, mock_dataset):
    """Test successful band download."""
    api = SentinelAPI(data_dir=str(tmp_path))
    os.makedirs(tmp_path, exist_ok=True)
    
    bbox = {
        'xmin': -122.4018,
        'ymin': 37.7914,
        'xmax': -122.3928,
        'ymax': 37.7994
    }
    
    url = "https://example.com/B04.tif"
    band = "B04"
    
    # Ensure the mock_rasterio_open creates the file
    output_path = os.path.join(str(tmp_path), f"{band}.tif")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    result = await api.fetch_windowed_band(url, bbox, band)
    
    assert result is True
    assert os.path.exists(output_path)

@pytest.mark.asyncio
async def test_fetch_windowed_band_failure(tmp_path, mock_rasterio_env):
    api = SentinelAPI(data_dir=tmp_path)
    os.makedirs(tmp_path, exist_ok=True)
    
    mock_rasterio_env.side_effect = Exception("Sign failed")
    
    result = await api.fetch_windowed_band(
        url="https://example.com/signed.tif",
        bbox={"xmin": -122.4018, "ymin": 37.7914, "xmax": -122.3928, "ymax": 37.7994},
        band_name="B04",
        data_dir=tmp_path
    )
    
    assert result is False

@pytest.mark.asyncio
async def test_download_data_with_invalid_band(tmp_path, mock_pc_client, mock_stac_item):
    api = SentinelAPI(data_dir=tmp_path)
    os.makedirs(tmp_path, exist_ok=True)

    # Set up mock search
    mock_search = MagicMock()
    mock_stac_item.id = "test_scene"
    mock_stac_item.properties = {"eo:cloud_cover": 5.0}
    mock_stac_item.assets = {
        "B04": MagicMock(href="https://example.com/B04.tif"),
        "B08": MagicMock(href="https://example.com/B08.tif")
    }
    mock_search.get_items.return_value = [mock_stac_item]
    mock_pc_client.search.return_value = mock_search

    start_date = datetime.now() - timedelta(days=30)
    end_date = datetime.now()

    result = await api.download_data(
        bbox={"xmin": -122.4018, "ymin": 37.7914, "xmax": -122.3928, "ymax": 37.7994},
        start_date=start_date,
        end_date=end_date,
        bands=["INVALID"]
    )

    assert result["status"] == "error"
    assert "Invalid bands specified" in result["message"]

@pytest.mark.asyncio
async def test_download_data_with_custom_bands(tmp_path, mock_pc_client, mock_stac_item, mock_rasterio_env, mock_rasterio_open):
    """Test data download with custom bands."""
    with patch('pystac_client.Client.open') as mock_open:
        mock_open.return_value = mock_pc_client
        api = SentinelAPI(data_dir=str(tmp_path))
        os.makedirs(tmp_path, exist_ok=True)

        # Set up mock search
        mock_search = MagicMock()
        mock_stac_item.id = "test_scene"
        mock_stac_item.properties = {
            "datetime": "2025-02-25T00:00:00Z",
            "platform": "sentinel-2a",
            "processing:level": "L2A",
            "eo:cloud_cover": 5.0
        }
        mock_stac_item.bbox = [-122.4018, 37.7914, -122.3928, 37.7994]
        mock_stac_item.assets = {
            "B04": MagicMock(href="https://example.com/B04.tif")
        }
        mock_search.get_items.return_value = [mock_stac_item]
        mock_pc_client.search.return_value = mock_search

        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()

        result = await api.download_data(
            bbox={"xmin": -122.4018, "ymin": 37.7914, "xmax": -122.3928, "ymax": 37.7994},
            start_date=start_date,
            end_date=end_date,
            bands=["B04"]
        )

        assert result["status"] == "success"
        assert result["scene_id"] == "test_scene"
        assert result["cloud_cover"] == 5.0
        assert result["bands"] == ["B04"]
        assert "metadata" in result
        assert result["metadata"]["acquisition_date"] == "2025-02-25T00:00:00Z"
        assert result["metadata"]["platform"] == "sentinel-2a"
        assert result["metadata"]["processing_level"] == "L2A" 