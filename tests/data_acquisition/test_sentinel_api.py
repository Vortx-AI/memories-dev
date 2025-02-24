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
async def test_download_data_success(sentinel_api, bbox):
    """Test successful data download."""
    result = await sentinel_api.download_data(bbox, cloud_cover=10.0)
    
    assert result['success'] is True
    assert 'data' in result
    assert isinstance(result['data'], np.ndarray)
    assert len(result['bands']) > 0
    assert 'properties' in result
    assert result['properties']['cloud_cover'] == 10.0
    assert result['properties']['bbox'] == bbox

@pytest.mark.asyncio
async def test_download_data_invalid_bbox(sentinel_api):
    """Test download with invalid bbox."""
    with pytest.raises(ValueError, match="Invalid bbox format"):
        await sentinel_api.download_data({'invalid': 'bbox'})

@pytest.mark.asyncio
async def test_download_data_high_cloud_cover(sentinel_api, bbox):
    """Test download with high cloud cover."""
    result = await sentinel_api.download_data(bbox, cloud_cover=100.0)
    assert result['success'] is True
    assert 'data' in result
    assert result['properties']['cloud_cover'] == 100.0

@pytest.mark.asyncio
async def test_download_data_missing_bands(sentinel_api, bbox):
    """Test download with missing bands."""
    result = await sentinel_api.download_data(
        bbox,
        bands={"B99": "NonexistentBand"}
    )
    assert result['success'] is False
    assert 'error' in result

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
async def test_cleanup(sentinel_api, tmp_path):
    """Test cleanup functionality."""
    test_file = tmp_path / "test.tif"
    test_file.touch()
    
    sentinel_api._cleanup_temp_files([test_file])
    assert not test_file.exists() 