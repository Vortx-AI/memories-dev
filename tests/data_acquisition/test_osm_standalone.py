"""Standalone test for OSM API functionality."""

import pytest
import asyncio
import json
import aiohttp
import logging
from typing import Dict, List, Any, Optional, Union, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OSMDataAPI:
    """Interface for accessing data from OpenStreetMap using Overpass API."""

    def __init__(self, cache_dir: Optional[str] = None):
        """Initialize OpenStreetMap interface."""
        self.base_url = "https://overpass-api.de/api/interpreter"
        self.logger = logging.getLogger(__name__)
        
        # Natural language to OSM tag mapping
        self.feature_map = {
            "park": '["leisure"="park"]',
            "road": '["highway"]',
            "building": '["building"]',
            "water": '["natural"="water"]',
            "forest": '["landuse"="forest"]',
            "restaurant": '["amenity"="restaurant"]',
            "school": '["amenity"="school"]',
            "hospital": '["amenity"="hospital"]',
            "shop": '["shop"]',
            "parking": '["amenity"="parking"]'
        }

    def _build_query(
        self,
        bbox: Union[Tuple[float, float, float, float], List[float]],
        tag: str
    ) -> str:
        """Build Overpass QL query."""
        minx, miny, maxx, maxy = bbox
        
        # Handle different tag formats
        if '=' in tag:
            key, value = tag.split('=')
            tag_filter = f'["{key}"="{value}"]'
        else:
            tag_filter = f'["{tag}"]'
        
        return f"""
            [out:json][timeout:25];
            (
                way{tag_filter}({miny},{minx},{maxy},{maxx});
                relation{tag_filter}({miny},{minx},{maxy},{maxx});
            );
            out body;
            >;
            out skel qt;
        """

    async def search(
        self,
        bbox: Union[Tuple[float, float, float, float], List[float]],
        tags: List[str] = ["building", "highway"],
        timeout: int = 25
    ) -> Dict[str, Any]:
        """Search for OSM features."""
        results = {'features': []}
        
        for tag in tags:
            query = self._build_query(bbox, tag)
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self.base_url,
                        data={'data': query},
                        timeout=timeout
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            if 'elements' in data:
                                # First, collect all nodes
                                nodes = {}
                                for element in data['elements']:
                                    if element['type'] == 'node':
                                        nodes[element['id']] = element
                                
                                # Then process ways and relations
                                for element in data['elements']:
                                    if element['type'] in ['way', 'relation']:
                                        try:
                                            # Get coordinates for each node reference
                                            coordinates = []
                                            for node_id in element.get('nodes', []):
                                                if node_id in nodes:
                                                    node = nodes[node_id]
                                                    coordinates.append([node['lon'], node['lat']])
                                            
                                            if coordinates:
                                                # Close the polygon if needed
                                                if coordinates[0] != coordinates[-1]:
                                                    coordinates.append(coordinates[0])
                                                
                                                feature = {
                                                    'type': 'Feature',
                                                    'geometry': {
                                                        'type': 'Polygon',
                                                        'coordinates': [coordinates]
                                                    },
                                                    'properties': element.get('tags', {})
                                                }
                                                results['features'].append(feature)
                                        except Exception as e:
                                            self.logger.warning(f"Error processing element: {str(e)}")
            except Exception as e:
                self.logger.error(f"Error querying OSM data: {str(e)}")
        
        return results

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
        
        # Print feature type counts for debugging
        print("\nFeature type counts:")
        for ftype, count in sorted(feature_types.items()):
            print(f"{ftype}: {count}")
        
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