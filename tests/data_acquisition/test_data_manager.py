"""
Test data manager functionality.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
from memories.data_acquisition.data_manager import DataManager
from shapely.geometry import box
from shapely.geometry import Polygon
import numpy as np

@pytest.fixture
def data_manager(tmp_path):
    """Create a data manager instance for testing."""
    return DataManager(cache_dir=str(tmp_path / "cache"))

@pytest.fixture
def bbox():
    """Sample bounding box for testing."""
    return [-122.5, 37.5, -122.0, 38.0]  # San Francisco area

@pytest.fixture
def date_range():
    """Sample date range for testing."""
    return {
        'start_date': '2023-01-01',
        'end_date': '2023-01-31'
    }

def test_initialization(tmp_path):
    """Test data manager initialization."""
    cache_dir = tmp_path / "cache"
    
    dm = DataManager(
        cache_dir=str(cache_dir)
    )
    
    assert dm.cache_dir == cache_dir
    assert dm.cache_dir.exists()
    assert dm.planetary is not None
    assert dm.sentinel is not None
    assert dm.landsat is not None
    assert dm.overture is not None
    assert dm.osm is not None

@pytest.mark.asyncio
async def test_get_satellite_data(data_manager):
    """Test getting satellite data."""
    mock_pc_items = [{"id": "test_item"}]
    
    # Mock the search and download methods
    data_manager.planetary.search_and_download = AsyncMock(return_value={'sentinel-2-l2a': mock_pc_items})
    data_manager.sentinel.search = AsyncMock(return_value={"items": []})
    data_manager.landsat.search = AsyncMock(return_value={"items": []})
    
    bbox = [0, 0, 1, 1]
    start_date = "2023-01-01"
    end_date = "2023-01-02"
    
    results = await data_manager.get_satellite_data(
        bbox=bbox,
        start_date=start_date,
        end_date=end_date
    )
    
    assert "pc" in results
    assert results["pc"]["sentinel-2-l2a"] == mock_pc_items

@pytest.mark.asyncio
async def test_get_vector_data(data_manager, bbox):
    """Test vector data acquisition."""
    # Mock Overture and OSM responses
    mock_overture_data = {
        'features': [
            {'type': 'Feature', 'properties': {'id': 'b1'}},
            {'type': 'Feature', 'properties': {'id': 'b2'}}
        ]
    }
    mock_osm_data = {
        'buildings': [
            {'type': 'Feature', 'properties': {'id': 'b1'}},
            {'type': 'Feature', 'properties': {'id': 'b2'}}
        ]
    }
    
    data_manager.overture.search = AsyncMock(return_value=mock_overture_data)
    data_manager.osm.search = AsyncMock(return_value=mock_osm_data)
    
    results = await data_manager.get_vector_data(
        bbox=bbox,
        layers=['buildings']
    )
    
    assert 'overture' in results
    assert 'osm' in results
    assert len(results['overture']['features']) == 2
    assert len(results['osm']['buildings']) == 2

@pytest.mark.asyncio
async def test_prepare_training_data(data_manager, bbox, date_range):
    """Test training data preparation."""
    # Mock satellite data
    mock_pc_items = [{'id': 'pc1', 'properties': {'cloud_cover': 10.0}}]
    mock_satellite_data = {
        'pc': {'sentinel-2-l2a': mock_pc_items},
        'sentinel': {'items': mock_pc_items}
    }
    
    # Mock vector data
    mock_vector_data = {
        'overture': {'features': [{'type': 'Feature', 'properties': {'id': 'b1'}}]},
        'osm': {'buildings': [{'type': 'Feature', 'properties': {'id': 'b1'}}]}
    }
    
    data_manager.get_satellite_data = AsyncMock(return_value=mock_satellite_data)
    data_manager.get_vector_data = AsyncMock(return_value=mock_vector_data)
    
    results = await data_manager.prepare_training_data(
        bbox=bbox,
        start_date=date_range['start_date'],
        end_date=date_range['end_date'],
        satellite_collections=['sentinel-2-l2a'],
        vector_layers=['buildings']
    )
    
    assert 'satellite_data' in results
    assert 'vector_data' in results
    assert 'pc' in results['satellite_data']
    assert 'overture' in results['vector_data']

def test_cache_operations(data_manager, tmp_path):
    """Test cache operations."""
    # Create a temporary cache directory
    data_manager.cache_dir = tmp_path / "test_cache"
    data_manager.cache_dir.mkdir(parents=True, exist_ok=True)
    
    cache_key = "test_data"
    test_data = {'value': 42}
    
    # Test cache miss
    assert not data_manager.cache_exists(cache_key)
    assert data_manager.get_from_cache(cache_key) is None
    
    # Test cache write and read
    data_manager.save_to_cache(cache_key, test_data)
    assert data_manager.cache_exists(cache_key)
    cached_data = data_manager.get_from_cache(cache_key)
    assert cached_data == test_data

def test_bbox_handling(data_manager):
    """Test bounding box handling."""
    # Test tuple bbox
    tuple_bbox = (-122.5, 37.5, -122.0, 38.0)
    bbox_from_tuple = data_manager._get_bbox_polygon(tuple_bbox)
    assert isinstance(bbox_from_tuple, (list, tuple))
    assert len(bbox_from_tuple) == 4
    
    # Test polygon bbox
    polygon_bbox = box(-122.5, 37.5, -122.0, 38.0)
    bbox_from_polygon = data_manager._get_bbox_polygon(polygon_bbox)
    assert isinstance(bbox_from_polygon, Polygon)
    
    # Test invalid bbox
    with pytest.raises(ValueError):
        data_manager._get_bbox_polygon([0, 0])  # Invalid format

def test_error_handling(data_manager, bbox):
    """Test error handling."""
    # Test invalid bbox
    with pytest.raises(ValueError):
        data_manager._get_bbox_polygon([0, 0])  # Invalid format
    
    # Test invalid layer
    with pytest.raises(ValueError):
        data_manager._get_bbox_polygon("invalid_bbox")

@pytest.mark.asyncio
async def test_resolution_handling(data_manager, bbox, date_range):
    """Test resolution handling."""
    # Mock satellite data with resolution
    mock_pc_items = [{'id': 'pc1', 'properties': {'cloud_cover': 10.0}}]
    mock_satellite_data = {
        'pc': {'sentinel-2-l2a': mock_pc_items},
        'sentinel': {'items': mock_pc_items, 'resolution': 10.0}
    }
    
    data_manager.get_satellite_data = AsyncMock(return_value=mock_satellite_data)
    
    results = await data_manager.get_satellite_data(
        bbox=bbox,
        start_date=date_range['start_date'],
        end_date=date_range['end_date'],
        collections=['sentinel-2-l2a'],
        resolution=10.0
    )
    
    assert 'pc' in results
    assert 'sentinel' in results
    assert results['sentinel']['resolution'] == 10.0

@pytest.mark.asyncio
async def test_download_satellite_data(data_manager, bbox, date_range):
    """Test downloading satellite data."""
    # Mock satellite data
    mock_data = np.random.rand(4, 100, 100)  # 4 bands, 100x100 pixels
    mock_metadata = {
        "cloud_cover": 9.24,
        "datetime": "2025-02-20T12:48:05.424634"
    }
    
    mock_response = {
        "success": True,
        "data": mock_data,
        "metadata": mock_metadata
    }
    
    # Mock the SentinelAPI
    data_manager.sentinel.download_data = AsyncMock(return_value=mock_response)
    
    results = await data_manager.get_satellite_data(
        bbox=bbox,
        start_date=date_range['start_date'],
        end_date=date_range['end_date']
    )
    
    assert "sentinel" in results
    assert "data" in results["sentinel"]
    assert "metadata" in results["sentinel"]
    assert results["sentinel"]["data"].shape == (4, 100, 100)
    assert results["sentinel"]["metadata"]["cloud_cover"] == 9.24

@pytest.mark.asyncio
async def test_download_vector_data(data_manager, bbox):
    """Test downloading vector data."""
    with patch('memories.data_acquisition.data_manager.OSMDataAPI') as mock_osm:
        mock_osm.return_value.search.return_value = [
            {'type': 'Feature', 'geometry': {'type': 'Polygon'}}
        ]
        mock_osm.return_value.download.return_value = Path("test.geojson")
        
        results = await data_manager.download_vector_data(
            layer="buildings",
            bbox=bbox
        )
        
        assert len(results) == 1
        assert all('type' in item for item in results)
        assert all('geometry' in item for item in results)

@pytest.mark.asyncio
async def test_get_location_data(data_manager, bbox, date_range):
    """Test retrieving location data."""
    # Mock Overture response
    mock_overture_data = {
        'type': 'FeatureCollection',
        'features': [
            {
                'type': 'Feature',
                'properties': {'name': 'Test Location'},
                'geometry': {'type': 'Point', 'coordinates': [-122.4, 37.8]}
            }
        ]
    }
    
    # Mock OSM response
    mock_osm_data = {
        'type': 'FeatureCollection',
        'features': [
            {
                'type': 'Feature',
                'properties': {'name': 'Test Building'},
                'geometry': {'type': 'Polygon', 'coordinates': [[[-122.4, 37.8], [-122.3, 37.8], [-122.3, 37.9], [-122.4, 37.9], [-122.4, 37.8]]]}
            }
        ]
    }
    
    # Mock the APIs
    data_manager.overture.search = AsyncMock(return_value=mock_overture_data)
    data_manager.osm.search = AsyncMock(return_value=mock_osm_data)
    
    results = await data_manager.get_location_data(
        bbox=bbox,
        start_date=date_range['start_date'],
        end_date=date_range['end_date']
    )
    
    assert 'overture' in results
    assert 'osm' in results
    assert len(results['overture']['features']) == 1
    assert len(results['osm']['features']) == 1
    assert results['overture']['features'][0]['properties']['name'] == 'Test Location'
    assert results['osm']['features'][0]['properties']['name'] == 'Test Building'

@pytest.mark.asyncio
async def test_concurrent_downloads(data_manager, bbox, date_range):
    """Test concurrent download operations."""
    with patch('memories.data_acquisition.data_manager.SentinelAPI') as mock_sentinel, \
         patch('memories.data_acquisition.data_manager.OSMDataAPI') as mock_osm:
        
        # Mock satellite data
        mock_sentinel.return_value.search.return_value = [
            {'id': 'test1', 'url': 'http://example.com/1'}
        ]
        mock_sentinel.return_value.download.return_value = Path("test.tif")
        
        # Mock vector data
        mock_osm.return_value.search.return_value = [
            {'type': 'Feature', 'geometry': {'type': 'Polygon'}}
        ]
        mock_osm.return_value.download.return_value = Path("test.geojson")
        
        # Test preparing training data which involves concurrent downloads
        result = await data_manager.prepare_training_data(
            bbox=bbox,
            start_date=date_range['start_date'],
            end_date=date_range['end_date'],
            satellite_collections=['sentinel-2-l2a'],
            vector_layers=['buildings']
        )
        
        assert 'satellite_data' in result
        assert 'vector_data' in result
        assert len(result['satellite_data']) > 0
        assert len(result['vector_data']) > 0

@pytest.mark.asyncio
async def test_cache_invalidation(data_manager, bbox, date_range):
    """Test cache invalidation and refresh."""
    # First, add some data to cache
    cache_key = "test_key"
    test_data = {"test": "data"}
    data_manager.save_to_cache(cache_key, test_data)
    
    # Verify data is in cache
    assert data_manager.cache_exists(cache_key)
    assert data_manager.get_from_cache(cache_key) == test_data
    
    # Mock new data fetch
    with patch('memories.data_acquisition.data_manager.SentinelAPI') as mock_sentinel:
        mock_sentinel.return_value.search.return_value = [
            {'id': 'new_test', 'url': 'http://example.com/new'}
        ]
        
        # Force refresh by passing refresh=True
        result = await data_manager.get_satellite_data(
            bbox=bbox,
            start_date=date_range['start_date'],
            end_date=date_range['end_date'],
            refresh=True
        )
        
        assert result != test_data
        assert len(result) > 0
        
        # Verify cache was updated
        assert data_manager.get_from_cache(cache_key) != test_data 