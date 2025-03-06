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
from datetime import datetime, timedelta
import asyncio

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
    """Test satellite data acquisition."""
    mock_sentinel_data = {
        "status": "success",
        "metadata": {
            "scene_id": "test_scene",
            "cloud_cover": 5.0,
            "datetime": "2023-01-01T00:00:00Z",
            "bands": ["B04", "B08"]
        }
    }
    
    data_manager.sentinel.download_data = AsyncMock(return_value=mock_sentinel_data)
    
    bbox = [-122.5, 37.5, -122.0, 38.0]  # San Francisco area
    start_date = "2023-01-01"
    end_date = "2023-01-31"
    
    results = await data_manager.get_satellite_data(
        bbox_coords=bbox,
        start_date=start_date,
        end_date=end_date
    )
    
    assert results["status"] == "success"
    assert "metadata" in results
    assert results["metadata"]["scene_id"] == "test_scene"
    assert results["metadata"]["cloud_cover"] == 5.0
    assert results["metadata"]["bands"] == ["B04", "B08"]

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
    mock_data = np.random.rand(3, 100, 100)  # 3 bands (Red, NIR, SWIR)
    mock_metadata = {
        'scene_id': 'test_scene',
        'cloud_cover': 5.0,
        'datetime': '2023-01-01T00:00:00Z',
        'bands_downloaded': ['B04', 'B08', 'B11'],
        'failed_bands': [],
        'recovered_files': []
    }
    
    mock_response = {
        'status': 'success',
        'metadata': mock_metadata,
        'data': mock_data.tolist()  # Convert to list for JSON serialization
    }
    
    # Mock the SentinelAPI
    data_manager.sentinel.download_data = AsyncMock(return_value=mock_response)
    
    results = await data_manager.get_satellite_data(
        bbox_coords=bbox,
        start_date=date_range['start_date'],
        end_date=date_range['end_date']
    )
    
    assert results['status'] == 'success'
    assert 'metadata' in results
    assert results['metadata']['scene_id'] == 'test_scene'
    assert results['metadata']['cloud_cover'] == 5.0
    assert len(results['metadata']['bands_downloaded']) == 3

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
async def test_get_location_data(data_manager):
    """Test getting location data."""
    mock_sentinel_data = {
        "status": "success",
        "metadata": {
            "scene_id": "test_scene",
            "cloud_cover": 5.0,
            "datetime": "2023-01-01T00:00:00Z",
            "bands": ["B04", "B08"]
        }
    }
    
    mock_vector_data = {
        "overture": {"features": [{"type": "Feature", "properties": {"id": "b1"}}]},
        "osm": {"buildings": [{"type": "Feature", "properties": {"id": "b1"}}]}
    }
    
    data_manager.sentinel.download_data = AsyncMock(return_value=mock_sentinel_data)
    data_manager.get_vector_data = AsyncMock(return_value=mock_vector_data)
    
    bbox = [-122.5, 37.5, -122.0, 38.0]
    start_date = "2023-01-01"
    end_date = "2023-01-31"
    
    results = await data_manager.get_location_data(
        bbox_coords=bbox,
        start_date=start_date,
        end_date=end_date
    )
    
    assert results["status"] == "success"
    assert "satellite_data" in results
    assert "vector_data" in results
    assert results["satellite_data"]["metadata"]["scene_id"] == "test_scene"
    assert results["satellite_data"]["metadata"]["cloud_cover"] == 5.0
    assert results["satellite_data"]["metadata"]["bands"] == ["B04", "B08"]

@pytest.mark.asyncio
async def test_concurrent_downloads(data_manager):
    """Test concurrent data downloads."""
    mock_sentinel_data = {
        "status": "success",
        "metadata": {
            "scene_id": "test_scene",
            "cloud_cover": 5.0,
            "datetime": "2023-01-01T00:00:00Z",
            "bands": ["B04", "B08"]
        }
    }
    
    mock_vector_data = {
        "overture": {"features": [{"type": "Feature", "properties": {"id": "b1"}}]},
        "osm": {"buildings": [{"type": "Feature", "properties": {"id": "b1"}}]}
    }
    
    data_manager.sentinel.download_data = AsyncMock(return_value=mock_sentinel_data)
    data_manager.get_vector_data = AsyncMock(return_value=mock_vector_data)
    
    bbox = [-122.5, 37.5, -122.0, 38.0]
    start_date = datetime.now() - timedelta(days=30)
    end_date = datetime.now()
    
    tasks = [
        data_manager.get_location_data(bbox, start_date, end_date),
        data_manager.get_location_data(bbox, start_date, end_date),
        data_manager.get_location_data(bbox, start_date, end_date)
    ]
    
    results = await asyncio.gather(*tasks)
    
    for result in results:
        assert result["status"] == "success"
        assert "satellite_data" in result
        assert "vector_data" in result
        assert result["satellite_data"]["metadata"]["scene_id"] == "test_scene"

@pytest.mark.asyncio
async def test_cache_invalidation(data_manager):
    """Test that cache invalidation works correctly."""
    bbox = [-122.5, 37.5, -122.0, 38.0]
    date_range = {
        'start_date': '2024-01-01',
        'end_date': '2024-12-31'
    }
    
    # Create two different mock responses
    mock_response_1 = {
        'status': 'success',
        'metadata': {
            'scene_id': 'scene_001',
            'cloud_cover': 5.0,
            'datetime': '2024-01-15T10:30:00Z',
            'bands': ['B04', 'B08']
        }
    }
    
    mock_response_2 = {
        'status': 'success',
        'metadata': {
            'scene_id': 'scene_002',
            'cloud_cover': 10.0,
            'datetime': '2024-01-16T10:30:00Z',
            'bands': ['B04', 'B08']
        }
    }
    
    # Keep track of calls to mock_download_data
    call_count = 0
    
    # Mock the download_data method to return different responses
    async def mock_download_data(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        # First call returns mock_response_1, subsequent calls return mock_response_2
        return mock_response_1 if call_count == 1 else mock_response_2
    
    # Patch the download_data method
    data_manager.sentinel.download_data = mock_download_data
    
    # First call - should get mock_response_1 and cache it
    result1 = await data_manager.get_satellite_data(
        bbox_coords=bbox,
        start_date=date_range['start_date'],
        end_date=date_range['end_date']
    )
    
    assert result1['status'] == 'success'
    assert result1['metadata']['scene_id'] == 'scene_001'
    assert result1['metadata']['cloud_cover'] == 5.0 