import pytest
import asyncio
from memories.data_acquisition.sources.osm_api import OSMDataAPI

@pytest.fixture
def osm_api():
    """Create an instance of OSMDataAPI for testing."""
    return OSMDataAPI()

@pytest.fixture
def sf_bbox():
    """San Francisco area bounding box for testing."""
    return (37.7749, -122.4194, 37.7793, -122.4094)  # Small area in SF

def test_get_overture_data_sync(osm_api, sf_bbox):
    """Test synchronous get_overture_data function."""
    # Test park data
    park_data = osm_api.get_overture_data("park", sf_bbox)
    assert isinstance(park_data, dict)
    assert "elements" in park_data
    
    # Test invalid feature
    with pytest.raises(ValueError) as exc_info:
        osm_api.get_overture_data("invalid_feature", sf_bbox)
    assert "not supported" in str(exc_info.value)
    
    # Test supported features
    for feature in ["road", "building", "water"]:
        data = osm_api.get_overture_data(feature, sf_bbox)
        assert isinstance(data, dict)
        assert "elements" in data

@pytest.mark.asyncio
async def test_get_overture_data_async(osm_api, sf_bbox):
    """Test asynchronous get_overture_data_async function."""
    # Test park data
    park_data = await osm_api.get_overture_data_async("park", sf_bbox)
    assert isinstance(park_data, dict)
    assert "elements" in park_data
    
    # Test invalid feature
    with pytest.raises(ValueError) as exc_info:
        await osm_api.get_overture_data_async("invalid_feature", sf_bbox)
    assert "not supported" in str(exc_info.value)
    
    # Test supported features
    for feature in ["road", "building", "water"]:
        data = await osm_api.get_overture_data_async(feature, sf_bbox)
        assert isinstance(data, dict)
        assert "elements" in data

def test_feature_map_completeness(osm_api):
    """Test that all advertised features are properly mapped."""
    expected_features = [
        "park", "road", "building", "water", "forest",
        "restaurant", "school", "hospital", "shop", "parking"
    ]
    
    for feature in expected_features:
        assert feature in osm_api.feature_map
        assert isinstance(osm_api.feature_map[feature], str)
        assert osm_api.feature_map[feature].startswith('[')
        assert osm_api.feature_map[feature].endswith(']')

if __name__ == "__main__":
    pytest.main(["-v", __file__]) 