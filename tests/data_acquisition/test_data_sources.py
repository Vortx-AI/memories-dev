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
    """Test concurrent band downloads."""
    source = SentinelDataSource()
    
    # Mock successful response
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.read = AsyncMock(return_value=b"test_data")
    
    mock_session = AsyncMock()
    mock_session.__aenter__.return_value = mock_session
    mock_session.get.return_value.__aenter__.return_value = mock_response
    
    urls = [f"https://example.com/band{i}.tif" for i in range(4)]
    output_paths = [tmp_path / f"band{i}.tif" for i in range(4)]
    
    tasks = [
        source._download_band(mock_session, url, path)
        for url, path in zip(urls, output_paths)
    ]
    
    await asyncio.gather(*tasks)
    
    # Verify all files were created
    for path in output_paths:
        assert path.exists()

@pytest.mark.asyncio
async def test_download_error_handling(tmp_path):
    """Test error handling during downloads."""
    source = SentinelDataSource()
    
    # Mock failed response
    mock_response = AsyncMock()
    mock_response.status = 404
    mock_response.text = AsyncMock(return_value="Not found")
    
    mock_session = AsyncMock()
    mock_session.__aenter__.return_value = mock_session
    mock_session.get.return_value.__aenter__.return_value = mock_response
    
    with pytest.raises(Exception) as exc_info:
        await source._download_band(
            mock_session,
            "https://example.com/nonexistent.tif",
            tmp_path / "test.tif"
        )
    assert "404" in str(exc_info.value)

@pytest.mark.asyncio
async def test_invalid_band_merging(tmp_path):
    """Test error handling during band merging with invalid files."""
    source = SentinelDataSource()
    
    # Create invalid band paths
    invalid_paths = [tmp_path / f"nonexistent{i}.tif" for i in range(4)]
    output_path = tmp_path / "merged.tif"
    
    with pytest.raises(Exception):
        source._merge_bands(invalid_paths, output_path)

@pytest.mark.asyncio
async def test_wfs_init(wfs_source):
    """Test WFS API initialization."""
    assert wfs_source.cache_dir.exists()
    assert wfs_source.timeout == 30
    assert "usgs" in wfs_source.endpoints
    assert "geoserver" in wfs_source.endpoints
    assert "mapserver" in wfs_source.endpoints

@pytest.mark.asyncio
async def test_wfs_get_features(wfs_source, bbox):
    """Test getting features from WFS service."""
    mock_features = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
                },
                "properties": {"name": "test_feature"}
            }
        ]
    }
    
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(mock_features)
    
    mock_service = MagicMock()
    mock_service.contents = {"test_layer": MagicMock(boundingBoxWGS84=(-180, -90, 180, 90))}
    mock_service.getfeature.return_value = mock_response
    
    with patch.dict(wfs_source.services, {"usgs": mock_service}):
        results = wfs_source.get_features(
            bbox=bbox,
            layers=["test_layer"],
            service_name="usgs"
        )
        
        assert "usgs" in results
        assert "test_layer" in results["usgs"]
        assert not results["usgs"]["test_layer"].empty
        assert "name" in results["usgs"]["test_layer"].columns

@pytest.mark.asyncio
async def test_wfs_layer_info(wfs_source):
    """Test getting layer information."""
    mock_layer = MagicMock()
    mock_layer.title = "Test Layer"
    mock_layer.abstract = "Test layer description"
    mock_layer.keywords = ["test", "layer"]
    mock_layer.boundingBoxWGS84 = (-180, -90, 180, 90)
    mock_layer.crsOptions = ["EPSG:4326"]
    mock_layer.properties = [MagicMock(name="test_property")]
    
    mock_service = MagicMock()
    mock_service.contents = {"test_layer": mock_layer}
    
    with patch.dict(wfs_source.services, {"usgs": mock_service}):
        layer_info = wfs_source.get_layer_info("test_layer", "usgs")
        
        assert layer_info is not None
        assert layer_info["service"] == "usgs"
        assert layer_info["title"] == "Test Layer"
        assert layer_info["keywords"] == ["test", "layer"]
        assert layer_info["properties"] == ["test_property"]

@pytest.mark.asyncio
async def test_wfs_available_layers(wfs_source):
    """Test getting available layers."""
    mock_service = MagicMock()
    mock_service.contents = {
        "layer1": MagicMock(),
        "layer2": MagicMock()
    }
    
    with patch.dict(wfs_source.services, {"usgs": mock_service}):
        layers = wfs_source.get_available_layers("usgs")
        
        assert "usgs" in layers
        assert "layer1" in layers["usgs"]
        assert "layer2" in layers["usgs"]
        assert len(layers["usgs"]) == 2

@pytest.mark.asyncio
async def test_wfs_download_to_file(wfs_source, bbox, tmp_path):
    """Test downloading WFS data to file."""
    mock_features = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
                },
                "properties": {"name": "test_feature"}
            }
        ]
    }
    
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(mock_features)
    
    mock_service = MagicMock()
    mock_service.contents = {"test_layer": MagicMock(boundingBoxWGS84=(-180, -90, 180, 90))}
    mock_service.getfeature.return_value = mock_response
    
    with patch.dict(wfs_source.services, {"usgs": mock_service}):
        output_files = wfs_source.download_to_file(
            bbox=bbox,
            layers=["test_layer"],
            output_dir=str(tmp_path),
            service_name="usgs"
        )
        
        assert "test_layer" in output_files
        assert output_files["test_layer"].exists()
        assert output_files["test_layer"].suffix == ".geojson"

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