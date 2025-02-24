"""
Test source implementations functionality.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
import numpy as np
import aiohttp
import json
from datetime import datetime
from shapely.geometry import box
import asyncio
from memories.data_acquisition.sources import (
    WFSAPI,
    SentinelAPI,
    LandsatAPI,
    OvertureAPI,
    OSMDataAPI,
    PlanetaryCompute
)

@pytest.fixture
def bbox():
    """Sample bounding box for testing."""
    return [-122.5, 37.5, -122.0, 38.0]  # San Francisco area

@pytest.fixture
def date_range():
    """Sample date range for testing."""
    return {
        'start_date': datetime(2023, 1, 1),
        'end_date': datetime(2023, 1, 31)
    }

@pytest.fixture
def wfs_api(tmp_path):
    """Create a WFS API instance."""
    return WFSAPI(cache_dir=str(tmp_path))

@pytest.fixture
def sentinel_api(tmp_path):
    """Create a Sentinel API instance."""
    return SentinelAPI(data_dir=str(tmp_path))

@pytest.fixture
def landsat_api(tmp_path):
    """Create a Landsat API instance."""
    return LandsatAPI(cache_dir=str(tmp_path))

@pytest.fixture
def overture_api(tmp_path):
    """Create an Overture API instance."""
    return OvertureAPI(data_dir=str(tmp_path))

@pytest.fixture
def osm_api(tmp_path):
    """Create an OSM API instance."""
    return OSMDataAPI(cache_dir=str(tmp_path))

@pytest.fixture
def planetary_compute(tmp_path):
    """Create a Planetary Compute instance."""
    return PlanetaryCompute(cache_dir=str(tmp_path))

@pytest.mark.asyncio
async def test_wfs_search(wfs_api, bbox):
    """Test WFS search functionality."""
    mock_response = {
        'type': 'FeatureCollection',
        'features': [
            {
                'type': 'Feature',
                'properties': {
                    'id': 'feature1',
                    'type': 'water_body'
                },
                'geometry': {
                    'type': 'Polygon',
                    'coordinates': [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]]
                }
            }
        ]
    }
    
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_get.return_value.__aenter__.return_value.json = AsyncMock(
            return_value=mock_response
        )
        
        results = await wfs_api.search(
            bbox=bbox,
            layer='water_bodies'
        )
        
        assert len(results['features']) == 1
        assert results['features'][0]['properties']['type'] == 'water_body'

@pytest.mark.asyncio
async def test_sentinel_api_search(sentinel_api, bbox, date_range):
    """Test Sentinel API search functionality."""
    mock_response = {
        'features': [
            {
                'id': 'S2A_MSIL2A_20230115T000000',
                'properties': {
                    'datetime': '2023-01-15T00:00:00Z',
                    'eo:cloud_cover': 5.0,
                    'sentinel:data_coverage': 100.0
                },
                'assets': {
                    'B02': {'href': 'https://example.com/B02.tif'},
                    'B03': {'href': 'https://example.com/B03.tif'},
                    'B04': {'href': 'https://example.com/B04.tif'}
                }
            }
        ]
    }
    
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_get.return_value.__aenter__.return_value.json = AsyncMock(
            return_value=mock_response
        )
        
        results = await sentinel_api.search(
            bbox=bbox,
            start_date=date_range['start_date'],
            end_date=date_range['end_date']
        )
        
        assert len(results['features']) == 1
        assert results['features'][0]['id'] == 'S2A_MSIL2A_20230115T000000'

@pytest.mark.asyncio
async def test_landsat_api_search(landsat_api, bbox, date_range):
    """Test Landsat API search functionality."""
    mock_response = {
        'features': [
            {
                'id': 'LC08_L2SP_123456_20230115_02_T1',
                'properties': {
                    'datetime': '2023-01-15T00:00:00Z',
                    'eo:cloud_cover': 10.0,
                    'landsat:cloud_cover_land': 8.0
                },
                'assets': {
                    'SR_B2': {'href': 'https://example.com/SR_B2.tif'},
                    'SR_B3': {'href': 'https://example.com/SR_B3.tif'},
                    'SR_B4': {'href': 'https://example.com/SR_B4.tif'}
                }
            }
        ]
    }
    
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_get.return_value.__aenter__.return_value.json = AsyncMock(
            return_value=mock_response
        )
        
        results = await landsat_api.search(
            bbox=bbox,
            start_date=date_range['start_date'],
            end_date=date_range['end_date']
        )
        
        assert len(results['features']) == 1
        assert results['features'][0]['id'] == 'LC08_L2SP_123456_20230115_02_T1'

@pytest.mark.asyncio
async def test_overture_api_search(overture_api, bbox):
    """Test Overture API search functionality."""
    mock_response = {
        'type': 'FeatureCollection',
        'features': [
            {
                'type': 'Feature',
                'properties': {
                    'id': 'building1',
                    'type': 'building',
                    'height': 20.0
                },
                'geometry': {
                    'type': 'Polygon',
                    'coordinates': [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]]
                }
            }
        ]
    }
    
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_get.return_value.__aenter__.return_value.json = AsyncMock(
            return_value=mock_response
        )
        
        results = await overture_api.search(bbox)
        
        assert len(results['features']) == 1
        assert results['features'][0]['properties']['type'] == 'building'

@pytest.mark.asyncio
async def test_osm_api_search(osm_api, bbox):
    """Test OSM API search functionality."""
    mock_response = {
        'elements': [
            {
                'type': 'way',
                'id': 123456,
                'tags': {
                    'building': 'yes',
                    'height': '20'
                },
                'nodes': [1, 2, 3, 4, 1]
            }
        ]
    }
    
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_get.return_value.__aenter__.return_value.json = AsyncMock(
            return_value=mock_response
        )
        
        results = await osm_api.search(
            bbox=bbox,
            tags=['building']
        )
        
        assert 'buildings' in results
        assert len(results['buildings']) > 0

@pytest.mark.asyncio
async def test_planetary_compute_search(planetary_compute, bbox, date_range):
    """Test Planetary Compute search functionality."""
    mock_items = [
        {
            'id': 'sentinel_scene_1',
            'properties': {
                'datetime': '2023-01-15T00:00:00Z',
                'eo:cloud_cover': 5.0
            },
            'assets': {
                'B02': {'href': 'https://example.com/B02.tif'},
                'B03': {'href': 'https://example.com/B03.tif'},
                'B04': {'href': 'https://example.com/B04.tif'}
            }
        }
    ]
    
    with patch('pystac_client.Client.open') as mock_client:
        mock_search = AsyncMock()
        mock_search.get_items = Mock(return_value=mock_items)
        mock_client.return_value.search = Mock(return_value=mock_search)
        
        results = await planetary_compute.search(
            collection='sentinel-2-l2a',
            bbox=bbox,
            start_date=date_range['start_date'],
            end_date=date_range['end_date']
        )
        
        assert len(results) == 1
        assert results[0]['id'] == 'sentinel_scene_1'

@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling across different sources."""
    api = WFSAPI(cache_dir='test')
    
    # Test invalid bbox
    with pytest.raises(ValueError):
        await api.search(
            bbox=[0],  # Invalid bbox
            layer='test'
        )
    
    # Test invalid layer
    with pytest.raises(ValueError):
        await api.search(
            bbox=[-122.5, 37.5, -122.0, 38.0],
            layer=''  # Empty layer name
        )

@pytest.mark.asyncio
async def test_caching(wfs_api, bbox, tmp_path):
    """Test caching functionality."""
    # Create mock response
    mock_response = {
        'type': 'FeatureCollection',
        'features': [
            {
                'type': 'Feature',
                'properties': {'id': 'test1'}
            }
        ]
    }
    
    # Write mock response to cache
    cache_file = tmp_path / "cache" / "wfs_cache.json"
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_file, 'w') as f:
        json.dump(mock_response, f)
    
    # Test that cache is used
    with patch('aiohttp.ClientSession.get') as mock_get:
        results = await wfs_api.search(
            bbox=bbox,
            layer='test',
            use_cache=True
        )
        
        assert not mock_get.called
        assert results == mock_response

@pytest.mark.asyncio
async def test_concurrent_operations(wfs_api, bbox):
    """Test concurrent operations."""
    # Create multiple concurrent requests
    requests = []
    for i in range(3):
        modified_bbox = [x + i * 0.1 for x in bbox]
        requests.append(
            wfs_api.search(
                bbox=modified_bbox,
                layer='test'
            )
        )
    
    # Execute requests concurrently
    results = await asyncio.gather(*requests)
    
    assert len(results) == 3
    assert all(isinstance(r, dict) for r in results)

def test_cleanup(wfs_api, tmp_path):
    """Test cleanup of temporary files."""
    # Create test files
    test_files = [
        tmp_path / "test1.geojson",
        tmp_path / "test2.geojson",
        tmp_path / "test3.geojson"
    ]
    
    for file in test_files:
        file.touch()
    
    # Run cleanup
    wfs_api._cleanup_files(test_files)
    
    # Verify files are removed
    for file in test_files:
        assert not file.exists() 