"""
Test data source implementations.
"""

import pytest
import pandas as pd
import json
import aiohttp
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime
from pathlib import Path
import contextlib
import numpy as np
import rasterio
from memories.data_acquisition.sources import (
    PlanetaryCompute,
    SentinelAPI,
    LandsatAPI,
    OvertureAPI,
    OSMDataAPI,
    WFSAPI
)
from memories.data_acquisition.data_sources import (
    DataSource,
    SentinelDataSource,
    LandsatDataSource
)
import geopandas as gpd
from shapely.geometry import Polygon, box

async def download_file(session: aiohttp.ClientSession, url: str, output_path: Path) -> bool:
    """Download a file from a URL and save it to the specified path.
    
    Args:
        session: aiohttp client session
        url: URL to download from
        output_path: Path to save the file to
        
    Returns:
        bool: True if download was successful, False otherwise
    """
    try:
        async with session.get(url) as response:
            if response.status == 200:
                content = await response.read()
                output_path.write_bytes(content)
                return True
            return False
    except Exception:
        return False

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

@pytest.fixture
def wfs_source(tmp_path):
    """Create a WFS API source for testing."""
    return WFSAPI(cache_dir=str(tmp_path / "wfs_cache"))

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

@pytest.mark.asyncio
async def test_base_datasource_methods():
    """Test that base DataSource class methods raise NotImplementedError."""
    source = DataSource()
    
    with pytest.raises(NotImplementedError):
        await source.search(
            bbox=[-122.5, 37.5, -122.0, 38.0],
            start_date=datetime.now(),
            end_date=datetime.now()
        )
    
    with pytest.raises(NotImplementedError):
        await source.download(
            item={},
            output_dir=Path("test")
        )

@pytest.mark.asyncio
async def test_sentinel_band_merging(tmp_path):
    """Test band merging functionality for Sentinel data."""
    source = SentinelDataSource()
    
    # Create mock band files
    test_array = np.zeros((10, 10), dtype=np.float32)
    band_paths = []
    
    for band in ["B02", "B03", "B04", "B08"]:
        band_path = tmp_path / f"{band}.tif"
        with rasterio.open(
            band_path,
            'w',
            driver='GTiff',
            height=10,
            width=10,
            count=1,
            dtype=np.float32
        ) as dst:
            dst.write(test_array, 1)
        band_paths.append(band_path)
    
    output_path = tmp_path / "merged.tif"
    source._merge_bands(band_paths, output_path)
    
    with rasterio.open(output_path) as src:
        assert src.count == 4  # Should have 4 bands
        assert src.shape == (10, 10)

@pytest.mark.asyncio
async def test_concurrent_downloads(tmp_path):
    """Test concurrent downloads."""
    # Create a mock aiohttp session
    mock_session = AsyncMock()
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.read = AsyncMock(return_value=b"test data")
    mock_session.get = AsyncMock(return_value=mock_response)
    
    # Create test URLs
    urls = [
        "http://example.com/file1",
        "http://example.com/file2",
        "http://example.com/file3"
    ]
    
    # Create output paths
    output_paths = [
        tmp_path / "file1.tif",
        tmp_path / "file2.tif",
        tmp_path / "file3.tif"
    ]
    
    # Run concurrent downloads
    async with aiohttp.ClientSession() as session:
        tasks = [
            download_file(session, url, output_path)
            for url, output_path in zip(urls, output_paths)
        ]
        results = await asyncio.gather(*tasks)
    
    # Check results
    assert all(results)
    assert all(path.exists() for path in output_paths)

@pytest.mark.asyncio
async def test_download_error_handling(tmp_path):
    """Test error handling during downloads."""
    # Create a mock aiohttp session
    mock_session = AsyncMock()
    mock_response = AsyncMock()
    mock_response.status = 404
    mock_response.text = AsyncMock(return_value="Not Found")
    mock_session.get = AsyncMock(return_value=mock_response)
    
    # Test URL and output path
    url = "http://example.com/nonexistent"
    output_path = tmp_path / "nonexistent.tif"
    
    # Attempt download
    async with aiohttp.ClientSession() as session:
        result = await download_file(session, url, output_path)
    
    # Check results
    assert not result
    assert not output_path.exists()
    assert mock_session.get.called_with(url)

@pytest.mark.asyncio
async def test_invalid_band_merging(tmp_path):
    """Test error handling during band merging with invalid files."""
    source = SentinelDataSource()
    
    # Create invalid band paths
    invalid_paths = [tmp_path / f"nonexistent{i}.tif" for i in range(4)]
    output_path = tmp_path / "merged.tif"
    
    with pytest.raises(Exception):
        source._merge_bands(invalid_paths, output_path)

def test_wfs_init():
    """Test WFS API initialization."""
    api = WFSAPI()
    
    # Check default endpoints
    assert isinstance(api.endpoints, dict)
    assert "usgs" in api.endpoints
    assert "geoserver" in api.endpoints
    assert "mapserver" in api.endpoints
    
    # Check endpoint structure
    for name, endpoint in api.endpoints.items():
        assert "url" in endpoint
        assert "version" in endpoint
        assert endpoint["version"] == "2.0.0"
    
    # Check specific endpoints
    assert api.endpoints["usgs"]["url"] == "https://services.nationalmap.gov/arcgis/services/WFS/MapServer/WFSServer"
    assert api.endpoints["geoserver"]["url"] == "http://geoserver.org/geoserver/wfs"
    assert api.endpoints["mapserver"]["url"] == "http://mapserver.org/cgi-bin/wfs"

def test_wfs_get_features():
    """Test getting features from WFS."""
    api = WFSAPI()
    
    # Mock response data
    mock_features = {
        'test_layer': gpd.GeoDataFrame(
            {
                'geometry': [Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)])],
                'name': ['test_feature']
            }
        )
    }
    
    # Mock the get_features method
    with patch.object(api, 'get_features', return_value=mock_features):
        # Test with tuple bbox
        results = api.get_features(
            bbox=(0, 0, 1, 1),
            layers=['test_layer'],
            service_name='usgs'
        )
        
        assert 'test_layer' in results
        assert isinstance(results['test_layer'], gpd.GeoDataFrame)
        assert len(results['test_layer']) == 1
        assert results['test_layer'].iloc[0]['name'] == 'test_feature'
        
        # Test with Polygon bbox
        bbox_polygon = box(0, 0, 1, 1)
        results = api.get_features(
            bbox=bbox_polygon,
            layers=['test_layer'],
            service_name='usgs'
        )
        
        assert 'test_layer' in results
        assert isinstance(results['test_layer'], gpd.GeoDataFrame)
        assert len(results['test_layer']) == 1

def test_wfs_layer_info():
    """Test getting layer info from WFS."""
    api = WFSAPI()
    
    # Mock layer info
    mock_layer_info = {
        'title': 'Test Layer',
        'abstract': 'Test layer description',
        'keywords': ['test', 'layer'],
        'bbox': (-180, -90, 180, 90),
        'crs': ['EPSG:4326'],
        'properties': ['height', 'type']
    }
    
    # Mock the get_layer_info method
    with patch.object(api, 'get_layer_info', return_value=mock_layer_info):
        # Test getting layer info
        info = api.get_layer_info('test_layer', 'usgs')
        
        assert info is not None
        assert info['title'] == 'Test Layer'
        assert info['abstract'] == 'Test layer description'
        assert info['keywords'] == ['test', 'layer']
        assert info['bbox'] == (-180, -90, 180, 90)
        assert info['crs'] == ['EPSG:4326']
        assert info['properties'] == ['height', 'type']

def test_wfs_available_layers():
    """Test getting available layers from WFS."""
    api = WFSAPI()
    
    # Mock available layers
    mock_layers = ['layer1', 'layer2']
    
    # Mock the get_available_layers method
    with patch.object(api, 'get_available_layers', return_value=mock_layers):
        # Test getting available layers
        layers = api.get_available_layers('usgs')
        
        assert isinstance(layers, list)
        assert len(layers) == 2
        assert 'layer1' in layers
        assert 'layer2' in layers

def test_wfs_download_to_file(tmp_path):
    """Test downloading WFS data to file."""
    api = WFSAPI()
    
    # Mock GeoDataFrame
    mock_gdf = gpd.GeoDataFrame(
        {
            'geometry': [Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)])],
            'name': ['test_feature']
        }
    )
    
    # Mock features response
    mock_features = {'test_layer': mock_gdf}
    
    # Mock the get_features method
    with patch.object(api, 'get_features', return_value=mock_features):
        # Test downloading to file
        results = api.download_to_file(
            bbox=(0, 0, 1, 1),
            layers=['test_layer'],
            output_dir=str(tmp_path),
            service_name='usgs'
        )
        
        assert 'test_layer' in results
        assert results['test_layer'].exists()
        assert results['test_layer'].suffix == '.geojson'
        
        # Verify file contents
        gdf = gpd.read_file(results['test_layer'])
        assert len(gdf) == 1
        assert gdf.iloc[0]['name'] == 'test_feature'

@pytest.mark.asyncio
async def test_wfs_invalid_bbox(wfs_source):
    """Test handling of invalid bounding box."""
    mock_service = MagicMock()
    mock_service.contents = {"test_layer": MagicMock(boundingBoxWGS84=(0, 0, 1, 1))}
    
    with patch.dict(wfs_source.services, {"usgs": mock_service}):
        results = wfs_source.get_features(
            bbox=(-2, -2, -1, -1),  # Outside layer bounds
            layers=["test_layer"],
            service_name="usgs"
        )
        
        assert "usgs" not in results or "test_layer" not in results.get("usgs", {})

@pytest.mark.asyncio
async def test_wfs_service_error(wfs_source, bbox):
    """Test handling of service errors."""
    mock_service = MagicMock()
    mock_service.contents = {"test_layer": MagicMock()}
    mock_service.getfeature.side_effect = Exception("Service error")
    
    with patch.dict(wfs_source.services, {"usgs": mock_service}):
        results = wfs_source.get_features(
            bbox=bbox,
            layers=["test_layer"],
            service_name="usgs"
        )
        
        assert "usgs" not in results or "test_layer" not in results.get("usgs", {}) 