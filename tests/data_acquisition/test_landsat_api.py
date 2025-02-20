"""
Test Landsat API functionality.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from shapely.geometry import box, Polygon
import planetary_computer as pc
import pystac_client
import rasterio
import numpy as np
from datetime import datetime
from memories.data_acquisition.sources.landsat_api import LandsatAPI

@pytest.fixture
def mock_pc_client():
    """Mock Planetary Computer client."""
    with patch('pystac_client.Client') as mock:
        mock_client = MagicMock()
        mock.return_value.open.return_value = mock_client
        yield mock_client

@pytest.fixture
def landsat_api(tmp_path, mock_pc_client):
    """Create a Landsat API instance for testing."""
    api = LandsatAPI(cache_dir=str(tmp_path / "landsat_cache"))
    # Mock the catalog
    api.catalog = MagicMock()
    return api

@pytest.fixture
def bbox():
    """Sample bounding box for testing."""
    return [-122.5, 37.5, -122.0, 38.0]  # San Francisco area

@pytest.fixture
def mock_landsat_item():
    """Sample Landsat item for testing."""
    return {
        'id': 'LC08_L2SP_044034_20230115_02_T1',
        'collection': 'landsat-8-c2-l2',
        'properties': {
            'datetime': '2023-01-15T00:00:00Z',
            'eo:cloud_cover': 10.5,
            'landsat:path': '044',
            'landsat:row': '034',
            'platform': 'LANDSAT_8',
            'instruments': ['OLI', 'TIRS']
        },
        'assets': {
            'SR_B2': {
                'href': 'https://example.com/SR_B2.tif',
                'type': 'image/tiff; application=geotiff'
            },
            'SR_B3': {
                'href': 'https://example.com/SR_B3.tif',
                'type': 'image/tiff; application=geotiff'
            },
            'SR_B4': {
                'href': 'https://example.com/SR_B4.tif',
                'type': 'image/tiff; application=geotiff'
            },
            'SR_B5': {
                'href': 'https://example.com/SR_B5.tif',
                'type': 'image/tiff; application=geotiff'
            }
        }
    }

@pytest.mark.asyncio
async def test_search(landsat_api, bbox, mock_landsat_item):
    """Test searching for Landsat scenes."""
    # Mock search response
    mock_search = MagicMock()
    mock_search.get_items.return_value = [mock_landsat_item]
    landsat_api.catalog.search.return_value = mock_search
    
    results = await landsat_api.search(
        bbox=bbox,
        start_date='2023-01-01',
        end_date='2023-01-31',
        cloud_cover=20.0
    )
    
    assert len(results) == 1
    assert results[0]['id'] == mock_landsat_item['id']
    assert results[0]['collection'] == mock_landsat_item['collection']
    
    # Verify search parameters
    landsat_api.catalog.search.assert_called_with(
        collections=["landsat-8-c2-l2"],
        bbox=bbox,
        datetime='2023-01-01/2023-01-31',
        query={"eo:cloud_cover": {"lt": 20.0}},
        limit=10
    )

@pytest.mark.asyncio
async def test_download(landsat_api, tmp_path, mock_landsat_item):
    """Test downloading Landsat data."""
    # Mock search response
    mock_search = MagicMock()
    mock_search.get_items.return_value = [mock_landsat_item]
    landsat_api.catalog.search.return_value = mock_search
    
    # Create mock dataset with proper context manager behavior
    class MockDataset:
        def __init__(self, mode='r'):
            self.count = 4
            self.profile = {
                'driver': 'GTiff',
                'dtype': 'uint16',
                'nodata': None,
                'width': 100,
                'height': 100,
                'count': 4,
                'crs': 'EPSG:32610',
                'transform': [30.0, 0.0, 0.0, 0.0, -30.0, 0.0]
            }
            self.mode = mode
            self.data = {}
        
        def __enter__(self):
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass
        
        def read(self, band=1):
            if self.mode != 'r':
                raise RuntimeError("Cannot read from output dataset")
            return np.zeros((100, 100))
        
        def write(self, data, band):
            if self.mode != 'w':
                raise RuntimeError("Cannot write to input dataset")
            self.data[band] = data
    
    # Create a real file for testing
    output_file = tmp_path / f"{mock_landsat_item['id']}.tif"
    output_file.touch()
    
    def mock_rasterio_open(path, mode='r', **kwargs):
        return MockDataset(mode=mode)
    
    with patch('rasterio.open', side_effect=mock_rasterio_open), \
         patch('planetary_computer.sign', return_value='https://example.com/signed.tif'):
        output_path = await landsat_api.download(
            item_id=mock_landsat_item['id'],
            output_dir=tmp_path,
            bands=['SR_B2', 'SR_B3', 'SR_B4', 'SR_B5']
        )
        
        assert output_path is not None
        assert output_path.exists()
        assert output_path.suffix == '.tif'
        
        # Verify the output file
        with rasterio.open(output_path) as src:
            assert src.count == 4  # Number of bands
            assert src.profile['driver'] == 'GTiff'

@pytest.mark.asyncio
async def test_download_with_cache(landsat_api, tmp_path, mock_landsat_item):
    """Test downloading with cache."""
    # Create cached file
    cache_path = landsat_api.get_cache_path(f"{mock_landsat_item['id']}.tif")
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_path, 'wb') as f:
        f.write(b'test_data')
    
    output_path = await landsat_api.download(
        item_id=mock_landsat_item['id'],
        output_dir=tmp_path
    )
    
    assert output_path == cache_path
    assert output_path.exists()

def test_get_metadata(landsat_api, mock_landsat_item):
    """Test getting scene metadata."""
    # Mock search response
    mock_search = MagicMock()
    mock_search.get_items.return_value = [mock_landsat_item]
    landsat_api.catalog.search.return_value = mock_search
    
    metadata = landsat_api.get_metadata(mock_landsat_item['id'])
    
    assert metadata['id'] == mock_landsat_item['id']
    assert metadata['datetime'] == '2023-01-15'
    assert metadata['cloud_cover'] == 10.5
    assert metadata['platform'] == 'LANDSAT_8'
    assert metadata['instruments'] == ['OLI', 'TIRS']
    assert metadata['path'] == '044'
    assert metadata['row'] == '034'
    assert set(metadata['bands']) == {'SR_B2', 'SR_B3', 'SR_B4', 'SR_B5'}

def test_get_available_collections(landsat_api):
    """Test getting available Landsat collections."""
    # Mock collections response
    mock_collections = [
        MagicMock(id='landsat-8-c2-l2'),
        MagicMock(id='landsat-9-c2-l2'),
        MagicMock(id='sentinel-2-l2a')  # Should be filtered out
    ]
    landsat_api.catalog.get_collections.return_value = mock_collections
    
    collections = landsat_api.get_available_collections()
    
    assert len(collections) == 2
    assert 'landsat-8-c2-l2' in collections
    assert 'landsat-9-c2-l2' in collections
    assert 'sentinel-2-l2a' not in collections

@pytest.mark.asyncio
async def test_search_and_download(landsat_api, bbox, mock_landsat_item, tmp_path):
    """Test combined search and download functionality."""
    # Mock search response
    mock_search = MagicMock()
    mock_search.get_items.return_value = [mock_landsat_item]
    landsat_api.catalog.search.return_value = mock_search
    
    # Mock rasterio operations
    mock_dataset = MagicMock()
    test_data = np.zeros((4, 100, 100))  # Create actual numpy array
    mock_dataset.read.return_value = test_data
    mock_dataset.profile = {
        'driver': 'GTiff',
        'dtype': 'uint16',
        'nodata': None,
        'width': 100,
        'height': 100,
        'count': 4,
        'crs': 'EPSG:32610',
        'transform': [30.0, 0.0, 0.0, 0.0, -30.0, 0.0]
    }
    mock_dataset.__enter__.return_value = mock_dataset
    
    mock_rasterio = MagicMock()
    mock_rasterio.return_value = mock_dataset
    
    # Create a real file for testing
    output_file = tmp_path / f"{mock_landsat_item['id']}.tif"
    output_file.touch()
    
    with patch('rasterio.open', mock_rasterio), \
         patch('planetary_computer.sign', return_value='https://example.com/signed.tif'):
        results = await landsat_api.search_and_download(
            bbox=box(*bbox),  # Convert list to Polygon
            start_date='2023-01-01',
            end_date='2023-01-31',
            cloud_cover=20.0,
            output_dir=tmp_path
        )
        
        assert isinstance(results, dict)
        assert 'data' in results
        assert 'metadata' in results
        assert results['metadata']['scene_id'] == mock_landsat_item['id']
        assert results['metadata']['cloud_cover'] == 10.5
        assert isinstance(results['data'], np.ndarray)
        assert results['data'].shape[0] == 4  # Number of bands

def test_error_handling(landsat_api, bbox):
    """Test error handling."""
    # Test invalid bbox
    with pytest.raises(ValueError):
        landsat_api.validate_bbox([0, 0])  # Invalid format
    
    # Test search with no results
    mock_search = MagicMock()
    mock_search.get_items.return_value = []
    landsat_api.catalog.search.return_value = mock_search
    
    with pytest.raises(ValueError, match="Item .* not found"):
        landsat_api.get_metadata("nonexistent_id")

@pytest.mark.asyncio
async def test_download_error_handling(landsat_api, tmp_path, mock_landsat_item):
    """Test download error handling."""
    # Mock search response for valid item
    mock_search = MagicMock()
    mock_search.get_items.return_value = [mock_landsat_item]
    landsat_api.catalog.search.return_value = mock_search
    
    # Test missing band
    with pytest.raises(ValueError, match="Band .* not found in item assets"):
        await landsat_api.download(
            item_id=mock_landsat_item['id'],
            output_dir=tmp_path,
            bands=['nonexistent_band']
        )
    
    # Test rasterio error
    class MockDatasetError:
        def __enter__(self):
            raise Exception("Rasterio error")
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass
    
    with patch('rasterio.open', return_value=MockDatasetError()), \
         patch('planetary_computer.sign', return_value='https://example.com/signed.tif'):
        with pytest.raises(Exception, match="Error processing band data: Rasterio error"):
            await landsat_api.download(
                item_id=mock_landsat_item['id'],
                output_dir=tmp_path,
                bands=['SR_B2']  # Use valid band to get past initial validation
            )

def test_cleanup(landsat_api, tmp_path):
    """Test cleanup of temporary files."""
    # Create test files
    test_file = tmp_path / "test.tif"
    test_file.write_text("test")
    
    # Test file cleanup
    landsat_api.cleanup_temp_files(test_file)
    assert not test_file.exists()  # File should be deleted
    
    # Test directory cleanup
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    (test_dir / "test.tif").write_text("test")
    
    landsat_api.cleanup_temp_files(test_dir)
    assert not test_dir.exists()  # Directory should be deleted 