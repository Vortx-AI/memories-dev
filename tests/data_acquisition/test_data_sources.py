"""
Test data source implementations.
"""

import pytest
import pandas as pd
import json
import aiohttp
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime
from pathlib import Path
import contextlib
from memories.data_acquisition.sources import (
    PlanetaryCompute,
    SentinelAPI,
    LandsatAPI,
    OvertureAPI,
    OSMDataAPI
)

@pytest.fixture
def pc_source():
    """Create a Planetary Computer data source for testing."""
    return PlanetaryCompute()

@pytest.fixture
def sentinel_source():
    """Create a Sentinel API data source for testing."""
    return SentinelAPI()

@pytest.fixture
def landsat_source():
    """Create a Landsat API data source for testing."""
    return LandsatAPI()

@pytest.fixture
def overture_source():
    """Create an Overture API data source for testing."""
    return OvertureAPI()

@pytest.fixture
def osm_source():
    """Create an OSM data source for testing."""
    return OSMDataAPI()

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

@pytest.mark.asyncio
async def test_pc_search(pc_source, bbox, date_range):
    """Test Planetary Computer search functionality."""
    with patch('pystac_client.Client') as mock_client:
        # Mock STAC API response
        mock_items = [
            {'id': 'item1', 'properties': {'cloud_cover': 10.0}},
            {'id': 'item2', 'properties': {'cloud_cover': 15.0}}
        ]
        mock_client.return_value.search.return_value.get_items.return_value = mock_items
        pc_source.catalog = mock_client.return_value
        
        results = await pc_source.search(
            bbox=bbox,
            start_date=date_range['start_date'],
            end_date=date_range['end_date'],
            collection='sentinel-2-l2a'
        )
        
        assert len(results) == 2
        assert all('id' in item for item in results)

@pytest.mark.asyncio
async def test_sentinel_search():
    """Test Sentinel data search."""
    bbox = [0, 0, 1, 1]
    start_date = "2023-01-01"
    end_date = "2023-01-02"
    
    sentinel_source = SentinelAPI(data_dir="test_cache")
    
    # Mock the download method
    sentinel_source.download_data = AsyncMock(return_value={"items": []})
    
    results = await sentinel_source.download_data(
        bbox=bbox,
        start_date=start_date,
        end_date=end_date
    )
    
    assert isinstance(results, dict)
    assert "items" in results

@pytest.mark.asyncio
async def test_landsat_search(landsat_source, bbox, date_range):
    """Test Landsat API search functionality."""
    with patch('pystac_client.Client') as mock_client:
        # Mock STAC API response
        mock_items = [
            {'id': 'item1', 'properties': {'cloud_cover': 10.0}},
            {'id': 'item2', 'properties': {'cloud_cover': 15.0}}
        ]
        mock_client.return_value.search.return_value.get_items.return_value = mock_items
        landsat_source.catalog = mock_client.return_value
        
        results = await landsat_source.search(
            bbox=bbox,
            start_date=date_range['start_date'],
            end_date=date_range['end_date']
        )
        
        assert len(results) == 2
        assert all('id' in item for item in results)

class AsyncContextManagerMock:
    """Helper class to mock async context managers."""
    def __init__(self, response):
        self.response = response
    
    async def __aenter__(self):
        return self.response
    
    async def __aexit__(self, exc_type, exc, tb):
        pass

@pytest.mark.asyncio
async def test_overture_search():
    """Test Overture data search."""
    bbox = [0, 0, 1, 1]
    
    overture_source = OvertureAPI(data_dir="test_cache")
    
    results = await overture_source.search(
        bbox=bbox
    )
    
    assert isinstance(results, dict)

@pytest.mark.asyncio
async def test_osm_search(osm_source, bbox):
    """Test OSM data search functionality."""
    mock_response = {
        'elements': [
            {
                'type': 'node',
                'id': 1,
                'lat': 37.7,
                'lon': -122.4
            },
            {
                'type': 'node',
                'id': 2,
                'lat': 37.7,
                'lon': -122.3
            },
            {
                'type': 'node',
                'id': 3,
                'lat': 37.8,
                'lon': -122.3
            },
            {
                'type': 'node',
                'id': 4,
                'lat': 37.7,
                'lon': -122.4
            },
            {
                'type': 'way',
                'id': 100,
                'nodes': [1, 2, 3, 4, 1],
                'tags': {'building': 'yes'}
            }
        ]
    }
    
    mock_response_obj = AsyncMock()
    mock_response_obj.status = 200
    mock_response_obj.json = AsyncMock(return_value=mock_response)
    mock_response_obj.__aenter__ = AsyncMock(return_value=mock_response_obj)
    mock_response_obj.__aexit__ = AsyncMock(return_value=None)
    
    mock_session = AsyncMock()
    mock_session.post = AsyncMock(return_value=mock_response_obj)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        results = await osm_source.search(
            bbox=bbox,
            tags=['building']
        )
        
        assert 'features' in results
        assert len(results['features']) > 0
        assert results['features'][0]['type'] == 'Feature'
        assert results['features'][0]['properties']['building'] == 'yes'

@pytest.mark.asyncio
async def test_pc_download(pc_source, tmp_path):
    """Test Planetary Computer data download."""
    test_item = {
        'assets': {
            'B02': MagicMock(href='https://example.com/B02.tif'),
            'B03': MagicMock(href='https://example.com/B03.tif'),
            'B04': MagicMock(href='https://example.com/B04.tif')
        }
    }
    
    # Create a test file
    output_file = tmp_path / "test_output.tif"
    output_file.touch()
    
    with patch('planetary_computer.sign') as mock_sign, \
         patch('rasterio.open') as mock_rasterio:
        mock_sign.return_value = 'https://example.com/signed.tif'
        mock_rasterio.return_value.__enter__.return_value.profile = {'count': 1}
        mock_rasterio.return_value.__enter__.return_value.read.return_value = None
        
        output_path = await pc_source.download(
            item=test_item,
            output_dir=tmp_path,
            bands=['B02', 'B03', 'B04']
        )
        
        assert isinstance(output_path, Path)
        assert output_path.suffix == '.tif'

def test_error_handling():
    """Test error handling in data sources."""
    # Test invalid bbox
    pc_source = PlanetaryCompute()
    with pytest.raises(ValueError):
        pc_source.validate_bbox([0, 0])  # Invalid bbox format

@pytest.mark.asyncio
async def test_cloud_cover_filtering(pc_source, bbox, date_range):
    """Test cloud cover filtering."""
    with patch('pystac_client.Client') as mock_client:
        mock_items = [
            {'id': 'item1', 'properties': {'cloud_cover': 5.0}},
            {'id': 'item2', 'properties': {'cloud_cover': 25.0}}  # Above threshold
        ]
        mock_client.return_value.search.return_value.get_items.return_value = [mock_items[0]]  # Only return item below threshold
        pc_source.catalog = mock_client.return_value
        
        results = await pc_source.search(
            bbox=bbox,
            start_date=date_range['start_date'],
            end_date=date_range['end_date'],
            collection='sentinel-2-l2a',
            cloud_cover=20.0
        )
        
        assert len(results) == 1
        assert results[0]['id'] == 'item1' 