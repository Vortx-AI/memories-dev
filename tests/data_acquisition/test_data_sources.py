"""
Test data sources functionality.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
import numpy as np
import aiohttp
import rasterio
from datetime import datetime
import asyncio
from memories.data_acquisition.data_sources import (
    DataSource,
    SentinelDataSource,
    LandsatDataSource
)

@pytest.fixture
def sentinel_source():
    """Create a Sentinel data source instance for testing."""
    return SentinelDataSource()

@pytest.fixture
def landsat_source():
    """Create a Landsat data source instance for testing."""
    return LandsatDataSource()

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

def test_data_source_interface():
    """Test the base DataSource class interface."""
    source = DataSource()
    
    with pytest.raises(NotImplementedError):
        asyncio.run(source.search([], None, None))
    
    with pytest.raises(NotImplementedError):
        asyncio.run(source.download({}, Path()))


@pytest.mark.asyncio
async def test_sentinel_download(sentinel_source, tmp_path):
    """Test Sentinel data download functionality."""
    # Mock item data
    item = {
        'id': 'test_scene',
        'assets': {
            'B02': {'href': 'https://example.com/B02.tif'},
            'B03': {'href': 'https://example.com/B03.tif'},
            'B04': {'href': 'https://example.com/B04.tif'}
        }
    }
    
    # Mock HTTP response
    mock_content = np.random.bytes(1000)
    
    async def mock_get(*args, **kwargs):
        mock_response = AsyncMock()
        mock_response.content.iter_chunked = AsyncMock(
            return_value=[mock_content]
        )
        return mock_response
    
    with patch('aiohttp.ClientSession.get', new=mock_get):
        with patch('rasterio.open') as mock_rasterio:
            # Mock rasterio read/write operations
            mock_src = Mock()
            mock_src.profile = {'count': 1, 'dtype': 'uint8'}
            mock_src.read = Mock(return_value=np.random.rand(1, 100, 100))
            mock_rasterio.return_value.__enter__.return_value = mock_src
            
            output_path = await sentinel_source.download(
                item=item,
                output_dir=tmp_path,
                bands=['B02', 'B03', 'B04']
            )
            
            assert output_path.exists()
            assert output_path.name == f"{item['id']}_merged.tif"

@pytest.mark.asyncio
async def test_landsat_search(landsat_source, bbox, date_range):
    """Test Landsat data search functionality."""
    # Mock STAC client response
    mock_items = [
        {
            'id': 'landsat_scene_1',
            'properties': {
                'datetime': '2023-01-15T00:00:00Z',
                'eo:cloud_cover': 10.0
            },
            'assets': {
                'SR_B2': {'href': 'https://example.com/SR_B2.tif'},
                'SR_B3': {'href': 'https://example.com/SR_B3.tif'},
                'SR_B4': {'href': 'https://example.com/SR_B4.tif'},
                'SR_B5': {'href': 'https://example.com/SR_B5.tif'}
            }
        }
    ]
    
    with patch('pystac_client.Client.open') as mock_client:
        mock_search = AsyncMock()
        mock_search.get_items = Mock(return_value=mock_items)
        mock_client.return_value.search = Mock(return_value=mock_search)
        
        results = await landsat_source.search(
            bbox=bbox,
            start_date=date_range['start_date'],
            end_date=date_range['end_date'],
            max_cloud_cover=20.0
        )
        
        assert len(results) == 1
        assert results[0]['id'] == 'landsat_scene_1'
        assert results[0]['properties']['eo:cloud_cover'] == 10.0
        assert len(results[0]['assets']) == 4

@pytest.mark.asyncio
async def test_landsat_download(landsat_source, tmp_path):
    """Test Landsat data download functionality."""
    # Mock item data
    item = {
        'id': 'test_scene',
        'assets': {
            'SR_B2': {'href': 'https://example.com/SR_B2.tif'},
            'SR_B3': {'href': 'https://example.com/SR_B3.tif'},
            'SR_B4': {'href': 'https://example.com/SR_B4.tif'}
        }
    }
    
    # Mock HTTP response
    mock_content = np.random.bytes(1000)
    
    async def mock_get(*args, **kwargs):
        mock_response = AsyncMock()
        mock_response.content.iter_chunked = AsyncMock(
            return_value=[mock_content]
        )
        return mock_response
    
    with patch('aiohttp.ClientSession.get', new=mock_get):
        with patch('rasterio.open') as mock_rasterio:
            # Mock rasterio read/write operations
            mock_src = Mock()
            mock_src.profile = {'count': 1, 'dtype': 'uint8'}
            mock_src.read = Mock(return_value=np.random.rand(1, 100, 100))
            mock_rasterio.return_value.__enter__.return_value = mock_src
            
            output_path = await landsat_source.download(
                item=item,
                output_dir=tmp_path,
                bands=['SR_B2', 'SR_B3', 'SR_B4']
            )
            
            assert output_path.exists()
            assert output_path.name == f"{item['id']}_merged.tif"

@pytest.mark.asyncio
async def test_error_handling_search():
    """Test error handling in search operations."""
    source = SentinelDataSource()
    
    # Test invalid bbox
    with pytest.raises(ValueError):
        await source.search(
            bbox=[0],  # Invalid bbox
            start_date=datetime.now(),
            end_date=datetime.now()
        )
    
    # Test invalid date range
    with pytest.raises(ValueError):
        await source.search(
            bbox=[-122.5, 37.5, -122.0, 38.0],
            start_date=datetime(2023, 1, 31),  # End before start
            end_date=datetime(2023, 1, 1)
        )

@pytest.mark.asyncio
async def test_error_handling_download(sentinel_source, tmp_path):
    """Test error handling in download operations."""
    # Test invalid item format
    with pytest.raises(ValueError):
        await sentinel_source.download(
            item={},  # Invalid item
            output_dir=tmp_path
        )
    
    # Test missing assets
    with pytest.raises(ValueError):
        await sentinel_source.download(
            item={'id': 'test', 'assets': {}},  # No assets
            output_dir=tmp_path
        )
    
    # Test invalid bands
    with pytest.raises(ValueError):
        await sentinel_source.download(
            item={
                'id': 'test',
                'assets': {'B02': {'href': 'url'}}
            },
            output_dir=tmp_path,
            bands=['invalid_band']
        )

@pytest.mark.asyncio
async def test_concurrent_downloads(sentinel_source, tmp_path):
    """Test concurrent download operations."""
    # Mock item data with multiple bands
    item = {
        'id': 'test_scene',
        'assets': {
            'B02': {'href': 'https://example.com/B02.tif'},
            'B03': {'href': 'https://example.com/B03.tif'},
            'B04': {'href': 'https://example.com/B04.tif'},
            'B08': {'href': 'https://example.com/B08.tif'}
        }
    }
    
    # Mock HTTP response
    mock_content = np.random.bytes(1000)
    
    async def mock_get(*args, **kwargs):
        mock_response = AsyncMock()
        mock_response.content.iter_chunked = AsyncMock(
            return_value=[mock_content]
        )
        return mock_response
    
    with patch('aiohttp.ClientSession.get', new=mock_get):
        with patch('rasterio.open') as mock_rasterio:
            # Mock rasterio read/write operations
            mock_src = Mock()
            mock_src.profile = {'count': 1, 'dtype': 'uint8'}
            mock_src.read = Mock(return_value=np.random.rand(1, 100, 100))
            mock_rasterio.return_value.__enter__.return_value = mock_src
            
            output_path = await sentinel_source.download(
                item=item,
                output_dir=tmp_path,
                bands=['B02', 'B03', 'B04', 'B08']
            )
            
            assert output_path.exists()
            assert output_path.name == f"{item['id']}_merged.tif"

def test_cleanup(sentinel_source, tmp_path):
    """Test cleanup of temporary files after download."""
    # Create some temporary files
    temp_files = [
        tmp_path / "temp1.tif",
        tmp_path / "temp2.tif",
        tmp_path / "temp3.tif"
    ]
    
    for file in temp_files:
        file.touch()
    
    # Mock cleanup method
    with patch.object(sentinel_source, '_cleanup_temp_files') as mock_cleanup:
        mock_cleanup(temp_files)
        
        # Verify cleanup was called with correct files
        mock_cleanup.assert_called_once_with(temp_files)
        
        # Verify files were removed
        for file in temp_files:
            assert not file.exists() 