"""
Test Sentinel API functionality.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from shapely.geometry import box, Polygon
from shapely.ops import transform
import planetary_computer as pc
import pystac_client
import rasterio
import numpy as np
from datetime import datetime
import pyproj
import asyncio
from memories.data_acquisition.sources.sentinel_api import SentinelAPI

@pytest.fixture
def mock_pc_client():
    """Mock Planetary Computer client."""
    with patch('pystac_client.Client') as mock:
        mock_client = MagicMock()
        mock.open.return_value = mock_client
        yield mock_client

@pytest.fixture
def mock_client():
    return MagicMock()

@pytest.fixture
def sentinel_api(mock_client):
    """Create a SentinelAPI instance for testing."""
    with patch('pystac_client.Client.open', return_value=mock_client):
        api = SentinelAPI(data_dir='test_output')
        yield api

@pytest.fixture
def bbox():
    """Sample bounding box for testing."""
    return {
        'xmin': -122.5,
        'ymin': 37.5,
        'xmax': -122.0,
        'ymax': 38.0
    }  # San Francisco area

class MockAsset:
    def __init__(self, href):
        self.href = href

class MockItem:
    def __init__(self, id, collection, properties, assets):
        self.id = id
        self.collection = collection
        self.properties = properties
        self.assets = {k: MockAsset(v) for k, v in assets.items()}

    def to_dict(self):
        return {
            'id': self.id,
            'collection': self.collection,
            'properties': self.properties,
            'assets': {k: {'href': v.href} for k, v in self.assets.items()}
        }

@pytest.fixture
def mock_sentinel_item():
    return MockItem(
        id='S2A_MSIL2A_20230115_R044_T10SEG_20230115T185412',
        collection='sentinel-2-l2a',
        properties={
            'datetime': '2023-01-15T00:00:00Z',
            'eo:cloud_cover': 10.5,
            'platform': 'SENTINEL-2A'
        },
        assets={
            'B04': 'https://example.com/B04.tif',
            'B03': 'https://example.com/B03.tif',
            'B02': 'https://example.com/B02.tif',
        }
    )

@pytest.mark.asyncio
async def test_fetch_windowed_band(sentinel_api, bbox, tmp_path):
    """Test fetching a windowed band."""
    # Create mock dataset with proper context manager behavior
    class MockDataset:
        def __init__(self, mode='r'):
            self.mode = mode
            self.bounds = (-122.5, 37.5, -122.0, 38.0)
            self.width = 100
            self.height = 100
            self.crs = rasterio.crs.CRS.from_epsg(4326)
            self.transform = rasterio.transform.from_bounds(*self.bounds, self.width, self.height)
            self.profile = {
                'driver': 'GTiff',
                'dtype': 'uint16',
                'nodata': None,
                'width': self.width,
                'height': self.height,
                'count': 1,
                'crs': self.crs,
                'transform': self.transform
            }

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            if self.mode == 'w':
                # Create an empty file to simulate writing
                Path(self.filepath).touch()
            return False

        def read(self, band_idx, window=None, out_shape=None, resampling=None):
            if self.mode != 'r':
                raise RuntimeError("Cannot read from output dataset")
            return np.zeros(out_shape or (self.height, self.width))
            
        def write(self, data, band_idx):
            """Mock write method."""
            if self.mode != 'w':
                raise RuntimeError("Cannot write to input dataset")

    def mock_rasterio_open(filepath, mode='r', **kwargs):
        """Mock rasterio.open that handles both read and write modes."""
        mock_ds = MockDataset(mode=mode)
        mock_ds.filepath = filepath
        return mock_ds

    # Create output directory
    output_dir = tmp_path / "B04.tif"
    output_dir.parent.mkdir(parents=True, exist_ok=True)

    with patch('rasterio.open', side_effect=mock_rasterio_open), \
         patch('planetary_computer.sign', return_value='https://example.com/signed.tif'):
        result = await sentinel_api.fetch_windowed_band(
            url='https://example.com/B04.tif',
            bbox=bbox,
            band_name='B04',
            data_dir=tmp_path
        )

        assert result is True
        assert (tmp_path / 'B04.tif').exists()

@pytest.mark.asyncio
async def test_download_data(sentinel_api, mock_client, mock_sentinel_item, tmp_path):
    mock_search = MagicMock()
    mock_search.get_items.return_value = [mock_sentinel_item]
    mock_client.search.return_value = mock_search

    # Create output directory
    output_dir = tmp_path / "test_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a new SentinelAPI instance with the test output directory
    sentinel_api = SentinelAPI(data_dir=str(output_dir))

    # Mock rasterio.open to return a dataset that works
    mock_dataset = MagicMock()
    mock_dataset.bounds = (-122.5, 37.5, -122.0, 38.0)
    mock_dataset.width = 100
    mock_dataset.height = 100
    mock_dataset.crs = rasterio.crs.CRS.from_epsg(4326)
    mock_dataset.transform = rasterio.Affine(0.01, 0, -122.5, 0, -0.01, 38.0)
    mock_dataset.read.return_value = np.zeros((1, 100, 100))  # Add channel dimension
    mock_dataset.profile = {
        'height': 100,
        'width': 100,
        'transform': rasterio.Affine(0.01, 0, -122.5, 0, -0.01, 38.0),
        'crs': rasterio.crs.CRS.from_epsg(4326),
        'driver': 'GTiff',
        'dtype': 'float32',
        'count': 1
    }

    # Create context manager mocks for both read and write operations
    mock_read_context = MagicMock()
    mock_read_context.__enter__.return_value = mock_dataset
    mock_read_context.__exit__.return_value = None

    mock_write_context = MagicMock()
    mock_write_context.__enter__.return_value = mock_dataset
    mock_write_context.__exit__.return_value = None

    # Mock both input and output file operations
    with patch('rasterio.open', side_effect=[mock_read_context, mock_write_context]), \
         patch('planetary_computer.sign', return_value={'href': 'https://example.com/B04.tif'}), \
         patch('pathlib.Path.exists', return_value=False), \
         patch('pathlib.Path.unlink'), \
         patch('os.path.getsize', return_value=1024):
        results = await sentinel_api.download_data(
            bbox={
                'xmin': -122.5,
                'ymin': 37.5,
                'xmax': -122.0,
                'ymax': 38.0
            },
            bands={'B04': 'Red'}
        )

    assert 'success' in results
    assert results['success'] is True
    assert results['metadata']['scene_id'] == mock_sentinel_item.id
    assert results['metadata']['bands_downloaded'] == ['B04']

@pytest.mark.asyncio
async def test_download_data_no_results(sentinel_api, bbox):
    """Test download data with no results."""
    # Mock empty search response
    mock_client = MagicMock()
    mock_search = MagicMock()
    mock_search.get_items.return_value = []
    mock_client.search.return_value = mock_search

    with patch('pystac_client.Client.open', return_value=mock_client):
        results = await sentinel_api.download_data(
            bbox=bbox,
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 1, 31)
        )

        assert 'status' in results
        assert results['status'] == 'no_data'
        assert 'message' in results
        assert 'No suitable imagery found' in results['message']

@pytest.mark.asyncio
async def test_download_data_with_errors(sentinel_api, mock_client, mock_sentinel_item):
    mock_search = MagicMock()
    mock_search.get_items.return_value = [mock_sentinel_item]
    mock_client.search.return_value = mock_search

    # Simulate an error during download
    with patch('rasterio.open', side_effect=Exception('Download failed')):
        results = await sentinel_api.download_data(
            bbox={
                'xmin': -122.5,
                'ymin': 37.5,
                'xmax': -122.0,
                'ymax': 38.0
            },
            bands={'B04': 'Red'}
        )

    assert 'failed_bands' in results
    assert 'B04' in results['failed_bands']

@pytest.mark.asyncio
async def test_download_data_with_invalid_bands(sentinel_api, mock_client, mock_sentinel_item):
    """Test download data with invalid bands."""
    mock_search = MagicMock()
    mock_search.get_items.return_value = [mock_sentinel_item]
    mock_client.search.return_value = mock_search

    results = await sentinel_api.download_data(
        bbox={
            'xmin': -122.5,
            'ymin': 37.5,
            'xmax': -122.0,
            'ymax': 38.0
        },
        bands={'invalid_band': 'Invalid'}
    )

    assert 'error' in results
    assert 'No valid bands to download' in str(results['error'])

@pytest.mark.asyncio
async def test_download_data_with_cancellation(sentinel_api, mock_client, mock_sentinel_item):
    mock_search = MagicMock()
    mock_search.get_items.return_value = [mock_sentinel_item]
    mock_client.search.return_value = mock_search

    # Mock fetch_windowed_band to be slow enough for cancellation
    original_fetch = sentinel_api.fetch_windowed_band

    async def slow_fetch(*args, **kwargs):
        await asyncio.sleep(0.5)  # Long enough for cancellation
        return await original_fetch(*args, **kwargs)

    sentinel_api.fetch_windowed_band = slow_fetch

    try:
        # Create a task and cancel it
        task = asyncio.create_task(
            sentinel_api.download_data(
                bbox={
                    'xmin': -122.5,
                    'ymin': 37.5,
                    'xmax': -122.0,
                    'ymax': 38.0
                },
                bands={'B04': 'Red'}
            )
        )
        await asyncio.sleep(0.1)  # Give the task time to start
        task.cancel()
        
        with pytest.raises(asyncio.CancelledError):
            await task
    finally:
        # Restore original method
        sentinel_api.fetch_windowed_band = original_fetch

def test_utm_conversion(sentinel_api, bbox):
    """Test UTM zone conversion."""
    # Convert bbox to geometry
    bbox_list = [bbox['xmin'], bbox['ymin'], bbox['xmax'], bbox['ymax']]
    aoi = box(*bbox_list)

    # Calculate UTM zone
    utm_zone = int((bbox['xmin'] + 180) / 6) + 1
    epsg_code = f"epsg:326{utm_zone}"

    # Convert to UTM
    project = pyproj.Transformer.from_crs("epsg:4326", epsg_code, always_xy=True).transform
    utm_aoi = Polygon(transform(project, aoi))

    assert utm_aoi.is_valid
    assert utm_aoi.area > 0

@pytest.mark.asyncio
async def test_concurrent_band_downloads(sentinel_api, mock_client, mock_sentinel_item, tmp_path):
    """Test downloading multiple bands concurrently."""
    mock_search = MagicMock()
    mock_search.get_items.return_value = [mock_sentinel_item]
    mock_client.search.return_value = mock_search

    # Create output directory
    output_dir = tmp_path / "test_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    sentinel_api = SentinelAPI(data_dir=str(output_dir))

    # Mock dataset for multiple bands
    mock_dataset = MagicMock()
    mock_dataset.bounds = (-122.5, 37.5, -122.0, 38.0)
    mock_dataset.width = 100
    mock_dataset.height = 100
    mock_dataset.crs = rasterio.crs.CRS.from_epsg(4326)
    mock_dataset.transform = rasterio.Affine(0.01, 0, -122.5, 0, -0.01, 38.0)
    mock_dataset.read.return_value = np.zeros((1, 100, 100))
    mock_dataset.profile = {
        'height': 100,
        'width': 100,
        'transform': rasterio.Affine(0.01, 0, -122.5, 0, -0.01, 38.0),
        'crs': rasterio.crs.CRS.from_epsg(4326),
        'driver': 'GTiff',
        'dtype': 'float32',
        'count': 1
    }

    mock_context = MagicMock()
    mock_context.__enter__.return_value = mock_dataset
    mock_context.__exit__.return_value = None

    with patch('rasterio.open', return_value=mock_context), \
         patch('planetary_computer.sign', return_value={'href': 'https://example.com/test.tif'}), \
         patch('pathlib.Path.exists', return_value=False), \
         patch('pathlib.Path.unlink'), \
         patch('os.path.getsize', return_value=1024):
        results = await sentinel_api.download_data(
            bbox={
                'xmin': -122.5,
                'ymin': 37.5,
                'xmax': -122.0,
                'ymax': 38.0
            },
            bands={'B02': 'Blue', 'B03': 'Green', 'B04': 'Red'}
        )

    assert results['success'] is True
    assert len(results['metadata']['bands_downloaded']) == 3
    assert all(band in results['metadata']['bands_downloaded'] for band in ['B02', 'B03', 'B04'])

@pytest.mark.asyncio
async def test_download_with_cloud_cover_filter(sentinel_api, mock_client, mock_sentinel_item):
    """Test downloading data with cloud cover filter."""
    output_dir = Path("test_output")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Set up mock response
    mock_search = AsyncMock()
    mock_search.get_items.return_value = [mock_sentinel_item]
    mock_client.search.return_value = mock_search
    
    # Test with cloud cover filter
    results = await sentinel_api.download_data(
        bbox={'xmin': -122.5, 'ymin': 37.5, 'xmax': -122.0, 'ymax': 38.0},
        cloud_cover=5.0
    )
    
    assert results['success'] is True
    assert mock_client.search.call_args[1]['query']['eo:cloud_cover']['lt'] == 5.0

@pytest.mark.asyncio
async def test_download_with_date_range(sentinel_api, mock_client, mock_sentinel_item, tmp_path):
    """Test downloading with date range filtering."""
    # Create items with different dates
    old_item = MockItem(
        id='S2A_MSIL2A_20220115',
        collection='sentinel-2-l2a',
        properties={
            'datetime': '2022-01-15T00:00:00Z',
            'eo:cloud_cover': 10.5,
            'platform': 'SENTINEL-2A'
        },
        assets={
            'B04': 'https://example.com/old_B04.tif'
        }
    )

    mock_search = MagicMock()
    mock_search.get_items.return_value = [old_item, mock_sentinel_item]
    mock_client.search.return_value = mock_search

    # Create output directory
    output_dir = tmp_path / "test_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    sentinel_api = SentinelAPI(data_dir=str(output_dir))

    mock_dataset = MagicMock()
    mock_dataset.profile = {
        'height': 100,
        'width': 100,
        'transform': rasterio.Affine(0.01, 0, -122.5, 0, -0.01, 38.0),
        'crs': rasterio.crs.CRS.from_epsg(4326),
        'driver': 'GTiff',
        'dtype': 'float32',
        'count': 1
    }
    mock_dataset.read.return_value = np.zeros((1, 100, 100))

    mock_context = MagicMock()
    mock_context.__enter__.return_value = mock_dataset
    mock_context.__exit__.return_value = None

    with patch('rasterio.open', return_value=mock_context), \
         patch('planetary_computer.sign', return_value={'href': 'https://example.com/test.tif'}), \
         patch('pathlib.Path.exists', return_value=False), \
         patch('pathlib.Path.unlink'), \
         patch('os.path.getsize', return_value=1024):
        results = await sentinel_api.download_data(
            bbox={
                'xmin': -122.5,
                'ymin': 37.5,
                'xmax': -122.0,
                'ymax': 38.0
            },
            bands={'B04': 'Red'},
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 12, 31)
        )

    assert results['success'] is True
    assert results['metadata']['scene_id'] == mock_sentinel_item.id
    assert '2023' in results['metadata']['timestamp']

@pytest.mark.asyncio
async def test_download_with_retry(sentinel_api, mock_client, mock_sentinel_item, tmp_path):
    """Test downloading with retry on temporary failure."""
    mock_search = MagicMock()
    mock_search.get_items.return_value = [mock_sentinel_item]
    mock_client.search.return_value = mock_search

    # Create output directory
    output_dir = tmp_path / "test_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    sentinel_api = SentinelAPI(data_dir=str(output_dir))

    # Mock dataset that fails first time, succeeds second time
    mock_dataset = MagicMock()
    mock_dataset.profile = {
        'height': 100,
        'width': 100,
        'transform': rasterio.Affine(0.01, 0, -122.5, 0, -0.01, 38.0),
        'crs': rasterio.crs.CRS.from_epsg(4326),
        'driver': 'GTiff',
        'dtype': 'float32',
        'count': 1
    }
    mock_dataset.read.return_value = np.zeros((1, 100, 100))

    mock_context = MagicMock()
    mock_context.__enter__.return_value = mock_dataset
    mock_context.__exit__.return_value = None

    # Counter for number of attempts
    attempt_count = 0
    def mock_rasterio_open(*args, **kwargs):
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count == 1:
            raise rasterio.errors.RasterioIOError("Temporary failure")
        return mock_context

    with patch('rasterio.open', side_effect=mock_rasterio_open), \
         patch('planetary_computer.sign', return_value={'href': 'https://example.com/test.tif'}), \
         patch('pathlib.Path.exists', return_value=False), \
         patch('pathlib.Path.unlink'), \
         patch('os.path.getsize', return_value=1024):
        results = await sentinel_api.download_data(
            bbox={
                'xmin': -122.5,
                'ymin': 37.5,
                'xmax': -122.0,
                'ymax': 38.0
            },
            bands={'B04': 'Red'}
        )

    assert results['success'] is True
    assert attempt_count > 1  # Verify that retry occurred

@pytest.mark.asyncio
async def test_download_with_invalid_bbox(sentinel_api, mock_client, mock_sentinel_item):
    """Test downloading with invalid bounding box."""
    mock_search = MagicMock()
    mock_search.get_items.return_value = [mock_sentinel_item]
    mock_client.search.return_value = mock_search

    # Test with invalid bbox format
    results = await sentinel_api.download_data(
        bbox={
            'xmin': -122.5,
            'ymin': 37.5,
            'xmax': -123.0,  # xmax < xmin
            'ymax': 38.0
        },
        bands={'B04': 'Red'}
    )

    assert 'error' in results
    assert 'Invalid bounding box' in str(results['error'])

    # Test with out of bounds bbox
    results = await sentinel_api.download_data(
        bbox={
            'xmin': -190.0,  # Out of valid longitude range
            'ymin': 37.5,
            'xmax': -180.0,
            'ymax': 38.0
        },
        bands={'B04': 'Red'}
    )

    assert 'error' in results
    assert 'Invalid coordinates' in str(results['error'])

@pytest.mark.asyncio
async def test_download_with_memory_management(sentinel_api, mock_client, mock_sentinel_item, tmp_path):
    """Test downloading with memory management for large datasets."""
    mock_search = MagicMock()
    mock_search.get_items.return_value = [mock_sentinel_item]
    mock_client.search.return_value = mock_search

    # Create output directory
    output_dir = tmp_path / "test_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    sentinel_api = SentinelAPI(data_dir=str(output_dir))

    # Mock a large dataset
    mock_dataset = MagicMock()
    mock_dataset.profile = {
        'height': 10000,  # Large dimensions
        'width': 10000,
        'transform': rasterio.Affine(0.01, 0, -122.5, 0, -0.01, 38.0),
        'crs': rasterio.crs.CRS.from_epsg(4326),
        'driver': 'GTiff',
        'dtype': 'float32',
        'count': 1
    }
    mock_dataset.read.return_value = np.zeros((1, 1000, 1000))  # Smaller chunk

    mock_context = MagicMock()
    mock_context.__enter__.return_value = mock_dataset
    mock_context.__exit__.return_value = None

    with patch('rasterio.open', return_value=mock_context), \
         patch('planetary_computer.sign', return_value={'href': 'https://example.com/test.tif'}), \
         patch('pathlib.Path.exists', return_value=False), \
         patch('pathlib.Path.unlink'), \
         patch('os.path.getsize', return_value=1024):
        results = await sentinel_api.download_data(
            bbox={
                'xmin': -122.5,
                'ymin': 37.5,
                'xmax': -122.0,
                'ymax': 38.0
            },
            bands={'B04': 'Red'},
            chunk_size=1000  # Use smaller chunks for memory management
        )

    assert results['success'] is True
    assert results['metadata']['scene_id'] == mock_sentinel_item.id
    assert 'chunk_size' in results['metadata']
    assert results['metadata']['chunk_size'] == 1000

@pytest.mark.asyncio
async def test_cleanup_on_error(sentinel_api, mock_client, mock_sentinel_item, tmp_path):
    """Test cleanup of temporary files on error."""
    mock_search = MagicMock()
    mock_search.get_items.return_value = [mock_sentinel_item]
    mock_client.search.return_value = mock_search

    # Create output directory
    output_dir = tmp_path / "test_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    sentinel_api = SentinelAPI(data_dir=str(output_dir))

    # Create a test file that should be cleaned up
    test_file = output_dir / "B04.tif"
    test_file.touch()

    # Mock dataset that raises an error
    mock_dataset = MagicMock()
    mock_dataset.profile = {
        'height': 100,
        'width': 100,
        'transform': rasterio.Affine(0.01, 0, -122.5, 0, -0.01, 38.0),
        'crs': rasterio.crs.CRS.from_epsg(4326),
        'driver': 'GTiff',
        'dtype': 'float32',
        'count': 1
    }
    mock_dataset.read.side_effect = rasterio.errors.RasterioIOError("Test error")

    mock_context = MagicMock()
    mock_context.__enter__.return_value = mock_dataset
    mock_context.__exit__.return_value = None

    with patch('rasterio.open', return_value=mock_context), \
         patch('planetary_computer.sign', return_value={'href': 'https://example.com/test.tif'}):
        results = await sentinel_api.download_data(
            bbox={
                'xmin': -122.5,
                'ymin': 37.5,
                'xmax': -122.0,
                'ymax': 38.0
            },
            bands={'B04': 'Red'}
        )

    assert 'error' in results
    assert not test_file.exists()  # File should be cleaned up

@pytest.mark.asyncio
async def test_partial_download_recovery(sentinel_api, mock_client, mock_sentinel_item, tmp_path):
    """Test recovery from partial downloads."""
    mock_search = MagicMock()
    mock_search.get_items.return_value = [mock_sentinel_item]
    mock_client.search.return_value = mock_search

    # Create output directory
    output_dir = tmp_path / "test_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    sentinel_api = SentinelAPI(data_dir=str(output_dir))

    # Create a partial download file
    partial_file = output_dir / "B04.tif"
    partial_file.write_bytes(b"partial data")

    mock_dataset = MagicMock()
    mock_dataset.profile = {
        'height': 100,
        'width': 100,
        'transform': rasterio.Affine(0.01, 0, -122.5, 0, -0.01, 38.0),
        'crs': rasterio.crs.CRS.from_epsg(4326),
        'driver': 'GTiff',
        'dtype': 'float32',
        'count': 1
    }
    mock_dataset.read.return_value = np.zeros((1, 100, 100))

    mock_context = MagicMock()
    mock_context.__enter__.return_value = mock_dataset
    mock_context.__exit__.return_value = None

    with patch('rasterio.open', return_value=mock_context), \
         patch('planetary_computer.sign', return_value={'href': 'https://example.com/test.tif'}), \
         patch('os.path.getsize', return_value=1024):
        results = await sentinel_api.download_data(
            bbox={
                'xmin': -122.5,
                'ymin': 37.5,
                'xmax': -122.0,
                'ymax': 38.0
            },
            bands={'B04': 'Red'}
        )

    assert results['success'] is True
    assert results['metadata']['recovered_files'] == ['B04.tif']

@pytest.mark.asyncio
async def test_concurrent_download_limit(sentinel_api, mock_client, mock_sentinel_item, tmp_path):
    """Test concurrent download limit handling."""
    mock_search = MagicMock()
    mock_search.get_items.return_value = [mock_sentinel_item]
    mock_client.search.return_value = mock_search

    # Create output directory
    output_dir = tmp_path / "test_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    sentinel_api = SentinelAPI(data_dir=str(output_dir), max_concurrent_downloads=2)

    mock_dataset = MagicMock()
    mock_dataset.profile = {
        'height': 100,
        'width': 100,
        'transform': rasterio.Affine(0.01, 0, -122.5, 0, -0.01, 38.0),
        'crs': rasterio.crs.CRS.from_epsg(4326),
        'driver': 'GTiff',
        'dtype': 'float32',
        'count': 1
    }
    mock_dataset.read.return_value = np.zeros((1, 100, 100))

    mock_context = MagicMock()
    mock_context.__enter__.return_value = mock_dataset
    mock_context.__exit__.return_value = None

    # Track concurrent downloads
    active_downloads = 0
    max_concurrent = 0

    async def mock_download(*args, **kwargs):
        nonlocal active_downloads, max_concurrent
        active_downloads += 1
        max_concurrent = max(max_concurrent, active_downloads)
        await asyncio.sleep(0.1)  # Simulate download time
        active_downloads -= 1
        return True

    with patch('rasterio.open', return_value=mock_context), \
         patch('planetary_computer.sign', return_value={'href': 'https://example.com/test.tif'}), \
         patch.object(sentinel_api, 'fetch_windowed_band', side_effect=mock_download):
        results = await sentinel_api.download_data(
            bbox={
                'xmin': -122.5,
                'ymin': 37.5,
                'xmax': -122.0,
                'ymax': 38.0
            },
            bands={'B02': 'Blue', 'B03': 'Green', 'B04': 'Red', 'B08': 'NIR'}
        )

    assert results['success'] is True
    assert max_concurrent <= 2  # Should not exceed concurrent download limit 

@pytest.mark.asyncio
async def test_planetary_compute_search(sentinel_api, mock_client, mock_sentinel_item, bbox):
    """Test Planetary Computer search functionality."""
    mock_search = MagicMock()
    mock_search.get_items.return_value = [mock_sentinel_item]
    mock_client.search.return_value = mock_search

    results = await sentinel_api.search_planetary_compute(
        bbox={
            'xmin': bbox['xmin'],
            'ymin': bbox['ymin'],
            'xmax': bbox['xmax'],
            'ymax': bbox['ymax']
        },
        start_date=datetime(2023, 1, 1),
        end_date=datetime(2023, 12, 31),
        max_cloud_cover=20.0,
        collection='sentinel-2-l2a'
    )

    assert len(results) == 1
    assert results[0].id == mock_sentinel_item.id
    assert results[0].collection == mock_sentinel_item.collection
    
    # Verify search parameters
    mock_client.search.assert_called_with(
        collections=['sentinel-2-l2a'],
        bbox=[bbox['xmin'], bbox['ymin'], bbox['xmax'], bbox['ymax']],
        datetime='2023-01-01/2023-12-31',
        query={"eo:cloud_cover": {"lt": 20.0}}
    )

@pytest.mark.asyncio
async def test_planetary_compute_download(sentinel_api, mock_client, mock_sentinel_item, tmp_path):
    """Test Planetary Computer data download."""
    mock_search = MagicMock()
    mock_search.get_items.return_value = [mock_sentinel_item]
    mock_client.search.return_value = mock_search

    # Create output directory
    output_dir = tmp_path / "test_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    sentinel_api = SentinelAPI(data_dir=str(output_dir))

    # Mock dataset
    mock_dataset = MagicMock()
    mock_dataset.profile = {
        'height': 100,
        'width': 100,
        'transform': rasterio.Affine(0.01, 0, -122.5, 0, -0.01, 38.0),
        'crs': rasterio.crs.CRS.from_epsg(4326),
        'driver': 'GTiff',
        'dtype': 'float32',
        'count': 1
    }
    mock_dataset.read.return_value = np.zeros((1, 100, 100))

    mock_context = MagicMock()
    mock_context.__enter__.return_value = mock_dataset
    mock_context.__exit__.return_value = None

    with patch('rasterio.open', return_value=mock_context), \
         patch('planetary_computer.sign', return_value={'href': 'https://example.com/test.tif'}), \
         patch('pathlib.Path.exists', return_value=False), \
         patch('pathlib.Path.unlink'), \
         patch('os.path.getsize', return_value=1024):
        results = await sentinel_api.download_from_planetary_compute(
            item=mock_sentinel_item,
            bands=['B04'],
            output_dir=output_dir
        )

    assert results['success'] is True
    assert len(results['downloaded_files']) == 1
    assert 'B04.tif' in str(results['downloaded_files'][0])

@pytest.mark.asyncio
async def test_planetary_compute_signed_url(sentinel_api, mock_client, mock_sentinel_item):
    """Test Planetary Computer signed URL generation."""
    with patch('planetary_computer.sign') as mock_sign:
        mock_sign.return_value = {'href': 'https://example.com/signed.tif'}
        
        url = sentinel_api.get_signed_url(mock_sentinel_item.assets['B04'].href)
        
        assert url == 'https://example.com/signed.tif'
        mock_sign.assert_called_once_with(mock_sentinel_item.assets['B04'].href)

@pytest.mark.asyncio
async def test_planetary_compute_collection_validation(sentinel_api, mock_client):
    """Test Planetary Computer collection validation."""
    # Test with valid collection
    assert sentinel_api.validate_collection('sentinel-2-l2a') is True
    
    # Test with invalid collection
    assert sentinel_api.validate_collection('invalid-collection') is False 