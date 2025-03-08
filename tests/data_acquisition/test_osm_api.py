import pytest
import asyncio
import json
from memories.data_acquisition.sources.osm_api import OSMDataAPI

@pytest.fixture
def osm_api():
    """Create an instance of OSMDataAPI for testing."""
    return OSMDataAPI()

@pytest.fixture
def sf_bbox():
    """San Francisco area bounding box for testing."""
    return [-122.4194, 37.7749, -122.4089, 37.7858]  # Small area in SF

@pytest.fixture
def search_tags():
    """Common OSM tags to search for."""
    return ["building", "highway", "amenity=restaurant"]

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

@pytest.mark.asyncio
async def test_bbox_search(osm_api, sf_bbox, search_tags):
    """Test searching for features within a bounding box."""
    try:
        # Search for features in the bounding box
        results = await osm_api.search(bbox=sf_bbox, tags=search_tags)
        
        # Verify results structure
        assert isinstance(results, dict)
        assert 'features' in results
        assert isinstance(results['features'], list)
        
        # Check if we got any features
        features = results['features']
        assert len(features) > 0, "No features found in the test area"
        
        # Verify feature structure
        sample_feature = features[0]
        assert 'type' in sample_feature
        assert 'geometry' in sample_feature
        assert 'properties' in sample_feature
        
        # Save results for manual inspection if needed
        output_file = "test_osm_results.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Count feature types
        feature_types = {}
        for feature in features:
            props = feature.get('properties', {})
            for key, value in props.items():
                type_key = f"{key}={value}" if value else key
                if type_key not in feature_types:
                    feature_types[type_key] = 0
                feature_types[type_key] += 1
        
        # Verify we got some of the feature types we asked for
        found_types = set()
        for tag in search_tags:
            for type_key in feature_types.keys():
                if tag in type_key:
                    found_types.add(tag)
                    break
        
        assert len(found_types) > 0, f"None of the requested feature types {search_tags} were found"
        
    except Exception as e:
        pytest.fail(f"Error during bbox search: {str(e)}")

if __name__ == "__main__":
    pytest.main(["-v", __file__]) 