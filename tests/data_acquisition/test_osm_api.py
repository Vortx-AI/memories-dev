import pytest
from unittest.mock import patch, AsyncMock
from pathlib import Path
import json
from shapely.geometry import Polygon, box
from memories.data_acquisition.sources.osm_api import OSMDataAPI

@pytest.fixture
def osm_api():
    """Create an OSM API instance for testing."""
    return OSMDataAPI()

@pytest.fixture
def bbox():
    """Create a test bounding box."""
    return [-122.4, 37.7, -122.3, 37.8]  # San Francisco area

@pytest.fixture
def polygon_bbox():
    """Create a test polygon bounding box."""
    return box(-122.4, 37.7, -122.3, 37.8)

@pytest.fixture
def mock_osm_response():
    """Create a mock OSM API response."""
    return {
        'elements': [
            {
                'type': 'node',
                'id': 1,
                'lat': 37.7,
                'lon': -122.4,
                'tags': {'amenity': 'cafe'}
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
                'lat': 37.8,
                'lon': -122.4
            },
            {
                'type': 'way',
                'id': 100,
                'nodes': [1, 2, 3, 4, 1],
                'tags': {'building': 'yes', 'height': '20'}
            },
            {
                'type': 'way',
                'id': 101,
                'nodes': [2, 3],
                'tags': {'highway': 'residential'}
            }
        ]
    }

@pytest.fixture
def mock_boundary_response():
    """Create a mock OSM API response for boundary data."""
    return {
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
                'lat': 37.8,
                'lon': -122.4
            },
            {
                'type': 'way',
                'id': 100,
                'nodes': [1, 2, 3, 4, 1],
                'tags': {
                    'boundary': 'administrative',
                    'name': 'San Francisco',
                    'admin_level': '4',
                    'type': 'boundary'
                }
            }
        ]
    }

@pytest.mark.asyncio
async def test_search_with_bbox(osm_api, bbox, mock_osm_response):
    """Test OSM search with bounding box coordinates."""
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value=mock_osm_response)
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock()

    mock_session = AsyncMock()
    mock_session.post = AsyncMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock()

    with patch('aiohttp.ClientSession', return_value=mock_session):
        results = await osm_api.search(bbox=bbox, tags=['building'])
        
        assert 'features' in results
        assert len(results['features']) > 0
        
        # Verify building feature
        building = next(f for f in results['features'] if f['properties'].get('building') == 'yes')
        assert building['type'] == 'Feature'
        assert building['geometry']['type'] == 'Polygon'
        assert len(building['geometry']['coordinates'][0]) > 3  # Polygon should have at least 4 points
        assert building['properties']['height'] == '20'

@pytest.mark.asyncio
async def test_search_with_polygon(osm_api, polygon_bbox, mock_osm_response):
    """Test OSM search with polygon bounding box."""
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value=mock_osm_response)
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock()

    mock_session = AsyncMock()
    mock_session.post = AsyncMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock()

    with patch('aiohttp.ClientSession', return_value=mock_session):
        results = await osm_api.search(bbox=polygon_bbox, tags=['building', 'highway'])
        
        assert 'features' in results
        assert len(results['features']) > 0
        
        # Verify we got both building and highway features
        features_by_type = {
            k: [f for f in results['features'] if k in f['properties']]
            for k in ['building', 'highway']
        }
        assert len(features_by_type['building']) > 0
        assert len(features_by_type['highway']) > 0

@pytest.mark.asyncio
async def test_download(osm_api, bbox, mock_osm_response, tmp_path):
    """Test downloading OSM data to files."""
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value=mock_osm_response)
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock()

    mock_session = AsyncMock()
    mock_session.post = AsyncMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock()

    with patch('aiohttp.ClientSession', return_value=mock_session):
        output_files = await osm_api.download(
            bbox=bbox,
            tags=['building', 'highway'],
            output_dir=tmp_path,
            format='geojson'
        )
        
        assert len(output_files) > 0
        for file_path in output_files.values():
            assert Path(file_path).exists()
            with open(file_path) as f:
                data = json.load(f)
                assert 'features' in data
                assert len(data['features']) > 0

@pytest.mark.asyncio
async def test_get_place_boundary(osm_api, mock_boundary_response):
    """Test getting place boundary."""
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value=mock_boundary_response)
    mock_response.raise_for_status = AsyncMock()
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock()

    mock_session = AsyncMock()
    mock_session.post = AsyncMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock()

    with patch('aiohttp.ClientSession', return_value=mock_session):
        boundary = await osm_api.get_place_boundary("San Francisco")
        
        # Verify that the mock was called correctly
        mock_session.post.assert_called_once()
        post_call_args = mock_session.post.call_args
        assert post_call_args is not None
        assert "data" in post_call_args[1]
        query = post_call_args[1]["data"]
        assert 'way[name="San Francisco"][boundary=administrative]' in query
        
        assert isinstance(boundary, Polygon)
        assert boundary.is_valid
        # The polygon should have the same coordinates as our mock data
        coords = list(boundary.exterior.coords)
        assert len(coords) == 5  # 4 points plus closing point
        assert coords[0] == coords[-1]  # First and last points should be the same
        
        # Verify the coordinates match our mock data
        expected_coords = [
            [-122.4, 37.7],  # Node 1
            [-122.3, 37.7],  # Node 2
            [-122.3, 37.8],  # Node 3
            [-122.4, 37.8],  # Node 4
            [-122.4, 37.7]   # Back to Node 1 to close the polygon
        ]
        assert coords == expected_coords

def test_get_metadata(osm_api):
    """Test getting layer metadata."""
    metadata = osm_api.get_metadata('buildings')
    assert metadata['name'] == 'buildings'
    assert 'building' in metadata['tags']
    assert metadata['geometry_type'] == 'polygon'
    assert metadata['source'] == 'OpenStreetMap'

def test_get_available_layers(osm_api):
    """Test getting available layers."""
    layers = osm_api.get_available_layers()
    assert 'buildings' in layers
    assert 'highways' in layers
    assert 'landuse' in layers
    assert 'waterways' in layers

def test_get_layer_tags(osm_api):
    """Test getting layer tags."""
    tags = osm_api.get_layer_tags('buildings')
    assert 'building' in tags

def test_invalid_layer(osm_api):
    """Test handling of invalid layer names."""
    with pytest.raises(ValueError):
        osm_api.get_metadata('invalid_layer')
    
    with pytest.raises(ValueError):
        osm_api.get_layer_tags('invalid_layer') 