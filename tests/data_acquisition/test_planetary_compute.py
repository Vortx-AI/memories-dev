"""
Test Planetary Computer functionality.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from shapely.geometry import box, Polygon, mapping
import planetary_computer as pc
import pystac_client
import rasterio
import numpy as np
from datetime import datetime
from memories.data_acquisition.sources.planetary_compute import PlanetaryCompute

@pytest.fixture
def mock_pc_client():
    """Mock Planetary Computer client."""
    with patch('pystac_client.Client') as mock:
        mock_client = MagicMock()
        mock.return_value.open.return_value = mock_client
        yield mock_client

@pytest.fixture
def pc_api(tmp_path, mock_pc_client):
    """Create a Planetary Computer API instance for testing."""
    api = PlanetaryCompute(cache_dir=str(tmp_path / "pc_cache"))
    # Mock the catalog
    api.catalog = MagicMock()
    return api

@pytest.fixture
def bbox():
    """Sample bounding box for testing."""
    return [-122.5, 37.5, -122.0, 38.0]  # San Francisco area

@pytest.fixture
def mock_stac_item():
    """Sample STAC item for testing."""
    return {
        'id': 'S2A_MSIL2A_20230115_R044_T10SEG_20230115T185427',
        'collection': 'sentinel-2-l2a',
        'properties': {
            'datetime': '2023-01-15T00:00:00Z',
            'eo:cloud_cover': 10.5,
            'sentinel:utm_zone': 10,
            'sentinel:latitude_band': 'S',
            'sentinel:grid_square': 'EG',
            'platform': 'sentinel-2a',
            'instruments': ['msi']
        },
        'assets': {
            'B02': {
                'href': 'https://example.com/B02.tif',
                'type': 'image/tiff; application=geotiff'
            },
            'B03': {
                'href': 'https://example.com/B03.tif',
                'type': 'image/tiff; application=geotiff'
            },
            'B04': {
                'href': 'https://example.com/B04.tif',
                'type': 'image/tiff; application=geotiff'
            },
            'B08': {
                'href': 'https://example.com/B08.tif',
                'type': 'image/tiff; application=geotiff'
            }
        }
    }

def test_init_with_token():
    """Test initialization with token."""
    token = "test_token"
    with patch('planetary_computer.settings.set_subscription_key') as mock_set_key:
        api = PlanetaryCompute(token=token)
        mock_set_key.assert_called_once_with(token)

def test_validate_bbox(pc_api):
    """Test bounding box validation."""
    # Valid bbox
    valid_bbox = [-122.5, 37.5, -122.0, 38.0]
    assert pc_api.validate_bbox(valid_bbox) is True
    
    # Invalid format
    with pytest.raises(ValueError, match="bbox must be a list/tuple of 4 coordinates"):
        pc_api.validate_bbox([0, 0])
    
    # Invalid types
    with pytest.raises(ValueError, match="bbox coordinates must be numbers"):
        pc_api.validate_bbox([-122.5, "37.5", -122.0, 38.0])
    
    # Invalid longitude
    with pytest.raises(ValueError, match="longitude must be between -180 and 180"):
        pc_api.validate_bbox([-190, 37.5, -122.0, 38.0])
    
    # Invalid latitude
    with pytest.raises(ValueError, match="latitude must be between -90 and 90"):
        pc_api.validate_bbox([-122.5, 95, -122.0, 38.0])

@pytest.mark.asyncio
async def test_search(pc_api, bbox, mock_stac_item):
    """Test searching for satellite imagery."""
    # Mock search response
    mock_search = MagicMock()
    mock_search.get_items.return_value = [mock_stac_item]
    pc_api.catalog.search.return_value = mock_search
    
    results = await pc_api.search(
        bbox=bbox,
        start_date='2023-01-01',
        end_date='2023-01-31',
        collection='sentinel-2-l2a',
        cloud_cover=20.0
    )
    
    assert len(results) == 1
    assert results[0]['id'] == mock_stac_item['id']
    assert results[0]['collection'] == mock_stac_item['collection']
    
    # Verify search parameters
    pc_api.catalog.search.assert_called_with(
        collections=['sentinel-2-l2a'],
        bbox=bbox,
        datetime='2023-01-01/2023-01-31',
        query={"eo:cloud_cover": {"lt": 20.0}},
        limit=10
    )

@pytest.mark.asyncio
async def test_download(pc_api, tmp_path, mock_stac_item):
    """Test downloading satellite imagery."""
    # Create mock dataset with proper context manager behavior
    class MockDataset:
        def __init__(self, mode='r'):
            self.count = 3
            self.profile = {
                'driver': 'GTiff',
                'dtype': 'uint16',
                'nodata': None,
                'width': 100,
                'height': 100,
                'count': 3,
                'crs': 'EPSG:32610',
                'transform': [10.0, 0.0, 0.0, 0.0, -10.0, 0.0]
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
    output_file = tmp_path / f"{mock_stac_item['id']}.tif"
    output_file.touch()
    
    def mock_rasterio_open(path, mode='r', **kwargs):
        return MockDataset(mode=mode)
    
    with patch('rasterio.open', side_effect=mock_rasterio_open), \
         patch('planetary_computer.sign', return_value='https://example.com/signed.tif'):
        output_path = await pc_api.download(
            item=mock_stac_item,
            output_dir=tmp_path,
            bands=['B02', 'B03', 'B04']
        )
        
        assert output_path is not None
        assert output_path.exists()
        assert output_path.suffix == '.tif'
        
        # Verify the output file
        with rasterio.open(output_path) as src:
            assert src.count == 3  # Number of bands
            assert src.profile['driver'] == 'GTiff'

@pytest.mark.asyncio
async def test_search_and_download(pc_api, bbox, mock_stac_item, tmp_path):
    """Test combined search and download functionality."""
    # Mock search response
    mock_search = MagicMock()
    mock_search.get_items.return_value = [mock_stac_item]
    pc_api.catalog.search.return_value = mock_search
    
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
        'transform': [10.0, 0.0, 0.0, 0.0, -10.0, 0.0]
    }
    mock_dataset.__enter__.return_value = mock_dataset
    
    with patch('rasterio.open', return_value=mock_dataset), \
         patch('planetary_computer.sign', return_value='https://example.com/signed.tif'):
        results = await pc_api.search_and_download(
            bbox=box(*bbox),
            start_date='2023-01-01',
            end_date='2023-01-31',
            collections=['sentinel-2-l2a'],
            cloud_cover=20.0
        )
        
        assert isinstance(results, dict)
        assert 'sentinel-2-l2a' in results

def test_get_metadata(pc_api, mock_stac_item):
    """Test getting collection metadata."""
    # Mock search response
    mock_search = MagicMock()
    mock_search.get_items.return_value = [mock_stac_item]
    pc_api.catalog.search.return_value = mock_search
    
    metadata = pc_api.get_metadata('sentinel-2-l2a')
    
    assert isinstance(metadata, dict)
    assert 'description' in metadata
    assert 'license' in metadata
    assert 'providers' in metadata

def test_get_available_collections(pc_api):
    """Test getting available collections."""
    # Mock collections response
    mock_collections = [
        MagicMock(id='sentinel-2-l2a'),
        MagicMock(id='landsat-8-c2-l2'),
        MagicMock(id='naip')
    ]
    pc_api.catalog.get_collections.return_value = mock_collections
    
    collections = pc_api.get_available_collections()
    
    assert isinstance(collections, list)
    assert 'sentinel-2-l2a' in collections
    assert 'landsat-8-c2-l2' in collections
    assert 'naip' in collections

def test_error_handling(pc_api, bbox):
    """Test error handling."""
    # Test invalid collection
    with pytest.raises(ValueError, match="Collection .* not found"):
        pc_api.get_metadata("nonexistent_collection")
    
    # Test search with no results
    mock_search = MagicMock()
    mock_search.get_items.return_value = []
    pc_api.catalog.search.return_value = mock_search
    
    with pytest.raises(ValueError, match="No items found matching criteria"):
        pc_api.get_metadata("sentinel-2-l2a") 