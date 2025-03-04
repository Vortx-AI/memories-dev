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