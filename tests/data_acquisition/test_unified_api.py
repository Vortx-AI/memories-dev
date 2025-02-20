"""
Test UnifiedAPI functionality.
"""

import pytest
import json
import geopandas as gpd
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from shapely.geometry import box, Polygon
import planetary_computer as pc
import pystac_client
import xarray as xr
import rasterio
from datetime import datetime
from memories.data_acquisition.sources.unified_api import (
    UnifiedAPI,
    DataSourceSpeed,
    DataSourceCost,
    DataSourceReliability,
    DataSourceMetrics
)

@pytest.fixture
def mock_pc_client():
    """Mock Planetary Computer client."""
    with patch('pystac_client.Client') as mock:
        mock_client = MagicMock()
        mock.return_value.open.return_value = mock_client
        yield mock_client

@pytest.fixture
def mock_wms_service():
    """Mock WMS service."""
    with patch('owslib.wms.WebMapService') as mock:
        mock_service = MagicMock()
        mock_service.contents = {
            'layer1': MagicMock(
                title='Test Layer',
                abstract='Test Description',
                boundingBox=(-180, -90, 180, 90)
            )
        }
        mock.return_value = mock_service
        yield mock_service

@pytest.fixture
def unified_api(tmp_path, mock_pc_client, mock_wms_service):
    """Create UnifiedAPI instance for testing."""
    return UnifiedAPI(
        cache_dir=str(tmp_path / "unified_cache"),
        max_workers=2,
        enable_streaming=True
    )

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

@pytest.fixture
def mock_pc_items():
    """Sample Planetary Computer items."""
    return [
        {
            'id': 'item1',
            'collection': 'sentinel-2-l2a',
            'properties': {
                'datetime': '2023-01-15T00:00:00Z',
                'eo:cloud_cover': 10.5
            },
            'assets': {
                'B02': {
                    'href': 'https://example.com/B02.tif',
                    'type': 'image/tiff; application=geotiff; profile=cloud-optimized'
                },
                'B03': {
                    'href': 'https://example.com/B03.tif',
                    'type': 'image/tiff; application=geotiff; profile=cloud-optimized'
                }
            }
        }
    ]

def test_init(unified_api):
    """Test UnifiedAPI initialization."""
    assert unified_api.cache_dir.exists()
    assert unified_api.max_workers == 2
    assert unified_api.enable_streaming is True
    assert len(unified_api.data_sources) > 0
    assert all(
        isinstance(source_info['metrics'], DataSourceMetrics)
        for source_info in unified_api.data_sources.values()
    )

def test_get_data(unified_api, bbox, date_range, mock_pc_items):
    """Test getting data from multiple sources."""
    # Mock Planetary Computer response
    mock_search = MagicMock()
    mock_search.get_all_items.return_value = mock_pc_items
    unified_api.data_sources['planetary_computer']['client'].search.return_value = mock_search
    
    # Mock WMS response
    mock_img = MagicMock()
    mock_img.read.return_value = b'test_image_data'
    unified_api.data_sources['wms_services']['client']['usgs'].getmap.return_value = mock_img
    
    results = unified_api.get_data(
        bbox=bbox,
        start_date=date_range['start_date'],
        end_date=date_range['end_date'],
        collections=['sentinel-2-l2a'],
        data_types=['raster'],
        formats=['geojson'],
        resolution=10.0,
        max_cloud_cover=20.0
    )
    
    assert isinstance(results, dict)
    assert 'geojson' in results
    assert 'planetary_computer' in results['geojson']
    assert len(results['geojson']['planetary_computer']) > 0

def test_get_data_with_cache(unified_api, bbox, date_range, tmp_path):
    """Test data retrieval with caching."""
    # Create mock cached data
    cache_data = {
        'test_collection': {
            'features': [
                {
                    'type': 'Feature',
                    'geometry': {
                        'type': 'Polygon',
                        'coordinates': [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
                    },
                    'properties': {'name': 'test'}
                }
            ]
        }
    }
    
    cache_file = unified_api.cache_dir / "cache.geojson"
    with open(cache_file, 'w') as f:
        json.dump(cache_data, f)
    
    results = unified_api.get_data(
        bbox=bbox,
        start_date=date_range['start_date'],
        end_date=date_range['end_date'],
        collections=['test_collection'],
        use_cache=True
    )
    
    assert isinstance(results, dict)
    assert len(results) > 0

def test_source_metrics(unified_api):
    """Test data source metrics."""
    # Test getting metrics for each source
    for source_name in unified_api.data_sources:
        metrics = unified_api.get_source_metrics(source_name)
        assert isinstance(metrics, DataSourceMetrics)
        assert isinstance(metrics.speed, DataSourceSpeed)
        assert isinstance(metrics.cost, DataSourceCost)
        assert isinstance(metrics.reliability, DataSourceReliability)
        assert isinstance(metrics.requires_auth, bool)
        assert isinstance(metrics.supports_streaming, bool)
        assert isinstance(metrics.supports_async, bool)

def test_get_available_sources(unified_api):
    """Test getting available data sources."""
    sources = unified_api.get_available_sources()
    assert isinstance(sources, list)
    assert len(sources) > 0
    for source in sources:
        assert 'name' in source
        assert 'metrics' in source
        assert 'status' in source
        assert isinstance(source['metrics'], dict)
        assert all(
            metric in source['metrics']
            for metric in ['speed', 'cost', 'reliability']
        )

def test_format_conversion(unified_api, mock_pc_items):
    """Test data format conversion."""
    # Create test GeoDataFrame
    gdf = gpd.GeoDataFrame(
        {
            'geometry': [Polygon([[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]])],
            'name': ['test']
        }
    )
    
    test_data = {
        'source1': gdf
    }
    
    # Test GeoJSON conversion
    geojson_results = unified_api._convert_to_geojson(test_data)
    assert isinstance(geojson_results, dict)
    assert 'source1' in geojson_results
    assert Path(geojson_results['source1']).suffix == '.geojson'
    
    # Test GeoParquet conversion
    parquet_results = unified_api._convert_to_geoparquet(test_data)
    assert isinstance(parquet_results, dict)
    assert 'source1' in parquet_results
    assert Path(parquet_results['source1']).suffix == '.parquet'

def test_error_handling(unified_api, bbox, date_range):
    """Test error handling for failed data sources."""
    # Make all sources fail
    for source_info in unified_api.data_sources.values():
        if source_info['client']:
            source_info['client'].search = MagicMock(side_effect=Exception("Test error"))
    
    with pytest.raises(RuntimeError) as exc_info:
        unified_api.get_data(
            bbox=bbox,
            start_date=date_range['start_date'],
            end_date=date_range['end_date'],
            collections=['sentinel-2-l2a']
        )
    
    assert "Failed to fetch data from all sources" in str(exc_info.value)

def test_concurrent_fetching(unified_api, bbox, date_range, mock_pc_items):
    """Test concurrent data fetching."""
    # Mock slow responses
    def slow_response(*args, **kwargs):
        import time
        time.sleep(0.1)
        mock_search = MagicMock()
        mock_search.get_all_items.return_value = mock_pc_items
        return mock_search
    
    unified_api.data_sources['planetary_computer']['client'].search = MagicMock(side_effect=slow_response)
    unified_api.data_sources['wms_services']['client']['usgs'].getmap = MagicMock(side_effect=slow_response)
    
    # Time the concurrent execution
    import time
    start_time = time.time()
    
    results = unified_api.get_data(
        bbox=bbox,
        start_date=date_range['start_date'],
        end_date=date_range['end_date'],
        collections=['sentinel-2-l2a']
    )
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    # Verify results
    assert isinstance(results, dict)
    # Execution time should be less than sequential execution
    assert execution_time < 0.3  # Allow some overhead

def test_invalid_inputs(unified_api):
    """Test handling of invalid inputs."""
    # Test invalid bbox
    with pytest.raises(ValueError):
        unified_api.get_data(
            bbox=[0, 0],  # Invalid format
            start_date='2023-01-01',
            end_date='2023-01-31'
        )
    
    # Test invalid date range
    with pytest.raises(ValueError):
        unified_api.get_data(
            bbox=[-122.5, 37.5, -122.0, 38.0],
            start_date='invalid_date',
            end_date='2023-01-31'
        )
    
    # Test invalid collection
    results = unified_api.get_data(
        bbox=[-122.5, 37.5, -122.0, 38.0],
        start_date='2023-01-01',
        end_date='2023-01-31',
        collections=['nonexistent_collection']
    )
    assert len(results) == 0

def test_database_operations(unified_api, bbox, mock_pc_items):
    """Test metadata database operations."""
    # Insert test metadata
    test_metadata = {
        'source': 'test_source',
        'collection': 'test_collection',
        'bbox': json.dumps(bbox),
        'timestamp': datetime.now(),
        'data_type': 'raster',
        'format': 'GeoTIFF',
        'resolution': 10.0,
        'file_path': '/test/path.tif',
        'metadata': json.dumps({'key': 'value'})
    }
    
    unified_api.db.execute("""
        INSERT INTO metadata (
            source, collection, bbox, timestamp, data_type,
            format, resolution, file_path, metadata
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, list(test_metadata.values()))
    
    # Query metadata
    result = unified_api.db.execute("""
        SELECT * FROM metadata
        WHERE source = 'test_source'
    """).fetchone()
    
    assert result is not None
    assert result[0] == 'test_source'
    assert result[1] == 'test_collection'

def test_cleanup(unified_api):
    """Test cleanup on deletion."""
    # Add some test data to clean up
    test_file = unified_api.cache_dir / "test.txt"
    test_file.write_text("test")
    
    # Delete the instance
    del unified_api
    
    # Verify cleanup
    assert not test_file.exists()  # Cache should be cleaned up 