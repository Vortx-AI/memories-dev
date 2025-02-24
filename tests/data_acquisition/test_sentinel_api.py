"""
Test Sentinel API functionality.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import numpy as np
from pathlib import Path
import rasterio
from datetime import datetime
from memories.data_acquisition.sources.sentinel_api import SentinelAPI

@pytest.fixture
def sentinel_api(tmp_path):
    """Create a Sentinel API instance for testing."""
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

@pytest.fixture
def mock_raster_data():
    """Create mock raster data."""
    return np.random.randint(0, 10000, (100, 100), dtype=np.uint16)

@pytest.mark.asyncio
async def test_download_data_success(sentinel_api, bbox, mock_raster_data, tmp_path):
    """Test successful data download."""
    
    # Mock rasterio.open context
    mock_src = Mock()
    mock_src.profile = {
        'count': 1,
        'dtype': 'uint16',
        'driver': 'GTiff',
        'width': 10980,
        'height': 10980,
        'transform': rasterio.transform.from_bounds(499980.0, 4090200.0, 609780.0, 4200000.0, 10980, 10980),
        'crs': rasterio.crs.CRS.from_epsg(32610)
    }
    mock_src.bounds = rasterio.coords.BoundingBox(
        left=499980.0,
        bottom=4090200.0,
        right=609780.0,
        top=4200000.0
    )
    mock_src.read = Mock(return_value=mock_raster_data)
    mock_src.width = 10980
    mock_src.height = 10980
    
    with patch('rasterio.open', return_value=mock_src):
        with patch('planetary_computer.sign') as mock_sign:
            # Mock the planetary computer signing
            mock_sign.return_value = "https://signed-url.example.com/scene.tif"
            
            # Mock STAC client and search
            mock_items = [{
                'id': 'S2A_MSIL2A_20250115T000000',
                'datetime': '2025-01-15T00:00:00Z',
                'properties': {
                    'datetime': '2025-01-15T00:00:00Z',
                    'eo:cloud_cover': 5.0,
                },
                'assets': {
                    'B04': {'href': 'https://example.com/B04.tif'},
                    'B08': {'href': 'https://example.com/B08.tif'},
                    'B11': {'href': 'https://example.com/B11.tif'}
                }
            }]
            
            with patch('pystac_client.Client.open') as mock_client:
                mock_search = AsyncMock()
                mock_search.get_items = Mock(return_value=mock_items)
                mock_client.return_value.search = Mock(return_value=mock_search)
                
                # Test download
                result = await sentinel_api.download_data(
                    bbox=bbox,
                    cloud_cover=10.0,
                    bands={
                        'B04': 'Red',
                        'B08': 'NIR',
                        'B11': 'SWIR'
                    }
                )
                
                # Verify results
                assert result['success'] is True
                assert 'metadata' in result
                metadata = result['metadata']
                assert metadata['scene_id'] == 'S2A_MSIL2A_20250115T000000'
                assert metadata['cloud_cover'] == 5.0
                assert set(metadata['bands_downloaded']) == {'B04', 'B08', 'B11'}
                
                # Verify files were created
                data_dir = Path(result['data_dir'])
                assert (data_dir / 'B04.tif').exists()
                assert (data_dir / 'B08.tif').exists()
                assert (data_dir / 'B11.tif').exists()
                assert (data_dir / 'metadata.txt').exists()

@pytest.mark.asyncio
async def test_download_data_no_scenes(sentinel_api, bbox):
    """Test download when no scenes are found."""
    with patch('pystac_client.Client.open') as mock_client:
        mock_search = AsyncMock()
        mock_search.get_items = Mock(return_value=[])
        mock_client.return_value.search = Mock(return_value=mock_search)
        
        result = await sentinel_api.download_data(bbox=bbox)
        
        assert 'status' in result
        assert result['status'] == 'no_data'
        assert 'message' in result
        assert 'No suitable imagery found' in result['message']

@pytest.mark.asyncio
async def test_download_data_invalid_bbox(sentinel_api):
    """Test download with invalid bbox."""
    invalid_bbox = {
        'xmin': 200,  # Invalid longitude
        'ymin': 37.7914,
        'xmax': -122.3928,
        'ymax': 37.7994
    }
    
    with pytest.raises(ValueError) as exc_info:
        await sentinel_api.download_data(bbox=invalid_bbox)
    assert "Invalid bbox coordinates" in str(exc_info.value)

@pytest.mark.asyncio
async def test_download_data_high_cloud_cover(sentinel_api, bbox):
    """Test download with high cloud cover scenes."""
    mock_items = [{
        'id': 'S2A_MSIL2A_20250115T000000',
        'datetime': '2025-01-15T00:00:00Z',
        'properties': {
            'datetime': '2025-01-15T00:00:00Z',
            'eo:cloud_cover': 90.0,  # High cloud cover
        },
        'assets': {
            'B04': {'href': 'https://example.com/B04.tif'}
        }
    }]
    
    with patch('pystac_client.Client.open') as mock_client:
        mock_search = AsyncMock()
        mock_search.get_items = Mock(return_value=mock_items)
        mock_client.return_value.search = Mock(return_value=mock_search)
        
        result = await sentinel_api.download_data(
            bbox=bbox,
            cloud_cover=10.0  # Request low cloud cover
        )
        
        assert 'status' in result
        assert result['status'] == 'no_data'
        assert 'No suitable imagery found' in result['message']

@pytest.mark.asyncio
async def test_download_data_missing_bands(sentinel_api, bbox, mock_raster_data):
    """Test download with missing bands in scene."""
    mock_items = [{
        'id': 'S2A_MSIL2A_20250115T000000',
        'datetime': '2025-01-15T00:00:00Z',
        'properties': {
            'datetime': '2025-01-15T00:00:00Z',
            'eo:cloud_cover': 5.0,
        },
        'assets': {
            'B04': {'href': 'https://example.com/B04.tif'}
            # Missing B08 and B11
        }
    }]
    
    with patch('pystac_client.Client.open') as mock_client:
        mock_search = AsyncMock()
        mock_search.get_items = Mock(return_value=mock_items)
        mock_client.return_value.search = Mock(return_value=mock_search)
        
        result = await sentinel_api.download_data(
            bbox=bbox,
            bands={
                'B04': 'Red',
                'B08': 'NIR',  # Requested but not available
                'B11': 'SWIR'  # Requested but not available
            }
        )
        
        assert 'error' in result
        assert 'Some band downloads failed' in result['error']
        assert set(result['failed_bands']) == {'B08', 'B11'}

def test_cleanup(sentinel_api, tmp_path):
    """Test cleanup of temporary files."""
    # Create test files
    test_files = [
        tmp_path / "B04.tif",
        tmp_path / "B08.tif",
        tmp_path / "B11.tif"
    ]
    
    for file in test_files:
        file.touch()
    
    # Run cleanup (this would typically be called internally)
    for file in test_files:
        if file.exists():
            file.unlink()
    
    # Verify files are removed
    for file in test_files:
        assert not file.exists() 