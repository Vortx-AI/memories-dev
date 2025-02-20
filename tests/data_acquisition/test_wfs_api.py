"""
Test WFS (Web Feature Service) API functionality.
"""

import pytest
import json
import geopandas as gpd
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from shapely.geometry import box, Polygon
from memories.data_acquisition.sources.wfs_api import WFSAPI

@pytest.fixture
def mock_wfs():
    """Mock WebFeatureService for testing."""
    with patch('owslib.wfs.WebFeatureService') as mock:
        mock.return_value = MagicMock()
        yield mock

@pytest.fixture
def wfs_source(tmp_path, mock_wfs):
    """Create a WFS API source for testing."""
    return WFSAPI(
        cache_dir=str(tmp_path / "wfs_cache"),
        usgs_url="https://services.nationalmap.gov/arcgis/services/WFS/MapServer/WFSServer",
        geoserver_url="http://geoserver.org/geoserver/wfs",
        mapserver_url="http://mapserver.org/cgi-bin/wfs"
    )

@pytest.fixture
def bbox():
    """Sample bounding box for testing."""
    return [-122.5, 37.5, -122.0, 38.0]  # San Francisco area

@pytest.fixture
def mock_features():
    """Sample GeoJSON features for testing."""
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
                },
                "properties": {"name": "test_feature", "type": "building"}
            },
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [0.5, 0.5]
                },
                "properties": {"name": "test_point", "type": "poi"}
            }
        ]
    }

def test_init(wfs_source):
    """Test WFS API initialization."""
    assert wfs_source.cache_dir.exists()
    assert wfs_source.timeout == 30
    assert isinstance(wfs_source.endpoints, dict)
    assert all(key in wfs_source.endpoints for key in ["usgs", "geoserver", "mapserver"])
    for endpoint in wfs_source.endpoints.values():
        assert "url" in endpoint
        assert "version" in endpoint

def test_init_with_partial_urls(tmp_path, mock_wfs):
    """Test WFS API initialization with only some URLs provided."""
    # Test with only USGS URL
    wfs_source = WFSAPI(
        cache_dir=str(tmp_path / "wfs_cache"),
        usgs_url="https://services.nationalmap.gov/arcgis/services/WFS/MapServer/WFSServer"
    )
    assert len(wfs_source.endpoints) == 1
    assert "usgs" in wfs_source.endpoints
    assert "geoserver" not in wfs_source.endpoints
    assert "mapserver" not in wfs_source.endpoints
    
    # Test with only GeoServer URL
    wfs_source = WFSAPI(
        cache_dir=str(tmp_path / "wfs_cache"),
        geoserver_url="http://geoserver.org/geoserver/wfs"
    )
    assert len(wfs_source.endpoints) == 1
    assert "geoserver" in wfs_source.endpoints
    assert "usgs" not in wfs_source.endpoints
    assert "mapserver" not in wfs_source.endpoints

def test_init_with_no_urls(tmp_path, mock_wfs):
    """Test WFS API initialization with no URLs provided."""
    wfs_source = WFSAPI(cache_dir=str(tmp_path / "wfs_cache"))
    assert len(wfs_source.endpoints) == 0
    assert len(wfs_source.services) == 0

def test_init_with_custom_version(tmp_path, mock_wfs):
    """Test WFS API initialization with custom WFS version."""
    wfs_source = WFSAPI(
        cache_dir=str(tmp_path / "wfs_cache"),
        usgs_url="https://services.nationalmap.gov/arcgis/services/WFS/MapServer/WFSServer",
        wfs_version="1.0.0"
    )
    assert wfs_source.endpoints["usgs"]["version"] == "1.0.0"

def test_init_services(wfs_source, mock_wfs):
    """Test WFS service initialization."""
    # Verify the mock was called for each endpoint
    assert mock_wfs.call_count == len(wfs_source.endpoints)
    assert len(wfs_source.services) == len(wfs_source.endpoints)
    
    # Verify each service was initialized with correct parameters
    for name, config in wfs_source.endpoints.items():
        mock_wfs.assert_any_call(
            url=config["url"],
            version=config["version"],
            timeout=wfs_source.timeout
        )
        assert name in wfs_source.services

def test_get_features(wfs_source, bbox, mock_features):
    """Test getting features from WFS service."""
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(mock_features)
    
    mock_service = MagicMock()
    mock_service.contents = {
        "buildings": MagicMock(boundingBoxWGS84=(-180, -90, 180, 90)),
        "poi": MagicMock(boundingBoxWGS84=(-180, -90, 180, 90))
    }
    mock_service.getfeature.return_value = mock_response
    
    with patch.dict(wfs_source.services, {"usgs": mock_service}):
        results = wfs_source.get_features(
            bbox=bbox,
            layers=["buildings", "poi"],
            service_name="usgs"
        )
        
        assert len(results) == 2
        assert "buildings" in results
        assert "poi" in results
        assert isinstance(results["buildings"], gpd.GeoDataFrame)
        assert isinstance(results["poi"], gpd.GeoDataFrame)
        assert not results["buildings"].empty
        assert not results["poi"].empty

def test_get_features_with_max_features(wfs_source, bbox, mock_features):
    """Test feature limit enforcement."""
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(mock_features)
    
    mock_service = MagicMock()
    mock_service.contents = {"buildings": MagicMock(boundingBoxWGS84=(-180, -90, 180, 90))}
    mock_service.getfeature.return_value = mock_response
    
    with patch.dict(wfs_source.services, {"usgs": mock_service}):
        results = wfs_source.get_features(
            bbox=bbox,
            layers=["buildings"],
            service_name="usgs",
            max_features=1
        )
        
        mock_service.getfeature.assert_called_with(
            typename="buildings",
            bbox=bbox,
            maxfeatures=1,
            outputFormat="GeoJSON"
        )
        assert "buildings" in results
        assert isinstance(results["buildings"], gpd.GeoDataFrame)

def test_get_layer_info(wfs_source):
    """Test getting layer information."""
    mock_layer = MagicMock()
    mock_layer.title = "Buildings"
    mock_layer.abstract = "Building footprints"
    mock_layer.keywords = ["buildings", "footprints"]
    mock_layer.boundingBoxWGS84 = (-180, -90, 180, 90)
    mock_layer.crsOptions = ["EPSG:4326"]
    mock_layer.properties = [
        MagicMock(name="height"),
        MagicMock(name="type")
    ]
    
    mock_service = MagicMock()
    mock_service.contents = {"buildings": mock_layer}
    
    with patch.dict(wfs_source.services, {"usgs": mock_service}):
        layer_info = wfs_source.get_layer_info("buildings", "usgs")
        
        assert layer_info is not None
        assert layer_info["title"] == "Buildings"
        assert layer_info["abstract"] == "Building footprints"
        assert layer_info["keywords"] == ["buildings", "footprints"]
        assert layer_info["properties"] == ["height", "type"]

def test_get_available_layers(wfs_source):
    """Test getting available layers."""
    mock_service = MagicMock()
    mock_service.contents = {
        "buildings": MagicMock(),
        "roads": MagicMock(),
        "poi": MagicMock()
    }
    
    with patch.dict(wfs_source.services, {"usgs": mock_service}):
        layers = wfs_source.get_available_layers("usgs")
        assert isinstance(layers, list)
        assert set(layers) == {"buildings", "roads", "poi"}

def test_download_to_file(wfs_source, bbox, mock_features, tmp_path):
    """Test downloading WFS data to file."""
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(mock_features)
    
    mock_service = MagicMock()
    mock_service.contents = {"buildings": MagicMock(boundingBoxWGS84=(-180, -90, 180, 90))}
    mock_service.getfeature.return_value = mock_response
    
    with patch.dict(wfs_source.services, {"usgs": mock_service}):
        output_files = wfs_source.download_to_file(
            bbox=bbox,
            layers=["buildings"],
            output_dir=str(tmp_path),
            service_name="usgs"
        )
        
        assert "buildings" in output_files
        assert output_files["buildings"].exists()
        assert output_files["buildings"].suffix == ".geojson"
        
        # Verify file contents
        with open(output_files["buildings"]) as f:
            saved_data = json.load(f)
            assert saved_data["type"] == "FeatureCollection"
            assert len(saved_data["features"]) == len(mock_features["features"])

def test_invalid_bbox(wfs_source):
    """Test handling of invalid bounding box."""
    mock_service = MagicMock()
    mock_service.contents = {"buildings": MagicMock(boundingBoxWGS84=(0, 0, 1, 1))}
    
    with patch.dict(wfs_source.services, {"usgs": mock_service}):
        # Test bbox outside layer bounds
        results = wfs_source.get_features(
            bbox=(-2, -2, -1, -1),
            layers=["buildings"],
            service_name="usgs"
        )
        assert len(results) == 0
        
        # Test invalid bbox format
        with pytest.raises(ValueError):
            wfs_source.get_features(
                bbox=[0, 0],  # Invalid format
                layers=["buildings"],
                service_name="usgs"
            )

def test_service_errors(wfs_source, bbox):
    """Test handling of various service errors."""
    # Test nonexistent service
    results = wfs_source.get_features(
        bbox=bbox,
        layers=["buildings"],
        service_name="nonexistent"
    )
    assert len(results) == 0
    
    # Test getfeature error
    mock_service = MagicMock()
    mock_service.contents = {"buildings": MagicMock(boundingBoxWGS84=(-180, -90, 180, 90))}
    mock_service.getfeature.side_effect = Exception("Service error")
    
    with patch.dict(wfs_source.services, {"usgs": mock_service}):
        results = wfs_source.get_features(
            bbox=bbox,
            layers=["buildings"],
            service_name="usgs"
        )
        assert len(results) == 0

def test_output_formats(wfs_source, bbox, mock_features):
    """Test different output formats."""
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(mock_features)
    
    mock_service = MagicMock()
    mock_service.contents = {"buildings": MagicMock(boundingBoxWGS84=(-180, -90, 180, 90))}
    mock_service.getfeature.return_value = mock_response
    
    with patch.dict(wfs_source.services, {"usgs": mock_service}):
        # Test GeoJSON format
        results = wfs_source.get_features(
            bbox=bbox,
            layers=["buildings"],
            service_name="usgs",
            output_format="GeoJSON"
        )
        assert "buildings" in results
        assert isinstance(results["buildings"], gpd.GeoDataFrame)
        
        # Test unsupported format
        results = wfs_source.get_features(
            bbox=bbox,
            layers=["buildings"],
            service_name="usgs",
            output_format="UNSUPPORTED"
        )
        assert len(results) == 0

def test_cache_operations(wfs_source, mock_features, tmp_path):
    """Test caching functionality."""
    cache_file = tmp_path / "wfs_cache" / "test_layer.geojson"
    
    # Write to cache
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_file, 'w') as f:
        json.dump(mock_features, f)
    
    # Verify cache is used
    assert cache_file.exists()
    with open(cache_file) as f:
        cached_data = json.load(f)
        assert cached_data == mock_features 