"""
Tests for the LocationProcessingAgent.
"""

import pytest
from unittest.mock import Mock, patch
from typing import List, Dict, Any

from memories.agents import LocationProcessingAgent
from memories.models.load_model import LoadModel

# Test data
SAMPLE_LOCATIONS = [
    {
        "coordinates": (40.7128, -74.0060),
        "name": "New York",
        "type": "city"
    },
    {
        "coordinates": (34.0522, -118.2437),
        "name": "Los Angeles",
        "type": "city"
    },
    {
        "coordinates": (41.8781, -87.6298),
        "name": "Coffee Shop",
        "type": "cafe"
    }
]

@pytest.fixture
def mock_model():
    """Create a mock model."""
    return Mock(spec=LoadModel)

@pytest.fixture
def agent(mock_model):
    """Create a LocationProcessingAgent instance."""
    return LocationProcessingAgent(model=mock_model)

def test_agent_initialization(agent):
    """Test agent initialization."""
    assert agent.name == "location_processing_agent"
    assert agent.model is not None
    assert agent.tools != {}
    assert agent.state is not None

def test_agent_capabilities(agent):
    """Test agent capabilities."""
    capabilities = agent.get_capabilities()
    assert isinstance(capabilities, list)
    assert len(capabilities) > 0
    assert "Filter locations by distance" in capabilities[0]

def test_tool_registration(agent):
    """Test that all required tools are registered."""
    tools = agent.list_tools()
    tool_names = {tool["name"] for tool in tools}
    
    required_tools = {
        "filter_by_distance",
        "filter_by_type",
        "sort_by_distance",
        "get_bounding_box",
        "cluster_locations",
        "normalize_location",
        "validate_coordinates",
        "extract_coordinates",
        "geocode",
        "reverse_geocode"
    }
    
    assert required_tools.issubset(tool_names)

@pytest.mark.asyncio
async def test_distance_filtering(agent):
    """Test location filtering by distance."""
    result = await agent.process(
        goal="filter locations within 1000km of point",
        locations=SAMPLE_LOCATIONS,
        center=(41.0, -74.0),
        radius_km=1000
    )
    
    assert result["status"] == "success"
    assert isinstance(result["data"], list)
    filtered = result["data"][0]  # First tool result
    assert len(filtered) > 0
    assert all("distance_km" in loc for loc in filtered)

@pytest.mark.asyncio
async def test_type_filtering(agent):
    """Test location filtering by type."""
    result = await agent.process(
        goal="filter locations by type cafe",
        locations=SAMPLE_LOCATIONS,
        location_types=["cafe"]
    )
    
    assert result["status"] == "success"
    filtered = result["data"][0]
    assert len(filtered) == 1
    assert filtered[0]["type"] == "cafe"

@pytest.mark.asyncio
async def test_distance_sorting(agent):
    """Test location sorting by distance."""
    result = await agent.process(
        goal="sort locations by distance",
        locations=SAMPLE_LOCATIONS,
        reference_point=(41.0, -74.0)
    )
    
    assert result["status"] == "success"
    sorted_locs = result["data"][0]
    assert len(sorted_locs) == len(SAMPLE_LOCATIONS)
    assert all("distance_km" in loc for loc in sorted_locs)
    # Verify sorting
    distances = [loc["distance_km"] for loc in sorted_locs]
    assert distances == sorted(distances)

@pytest.mark.asyncio
async def test_bounding_box(agent):
    """Test bounding box calculation."""
    result = await agent.process(
        goal="calculate bounding box",
        locations=SAMPLE_LOCATIONS
    )
    
    assert result["status"] == "success"
    bbox = result["data"][0]
    assert "min_lat" in bbox
    assert "max_lat" in bbox
    assert "min_lon" in bbox
    assert "max_lon" in bbox

@pytest.mark.asyncio
async def test_location_clustering(agent):
    """Test location clustering."""
    result = await agent.process(
        goal="cluster locations",
        locations=SAMPLE_LOCATIONS,
        max_distance_km=1000
    )
    
    assert result["status"] == "success"
    clusters = result["data"][0]
    assert isinstance(clusters, list)
    # Should have at least one cluster
    assert len(clusters) > 0
    # Each cluster should be a list of locations
    assert all(isinstance(cluster, list) for cluster in clusters)

@pytest.mark.asyncio
async def test_geocoding():
    """Test geocoding functionality."""
    with patch("geopy.geocoders.Nominatim") as mock_nominatim:
        # Setup mock
        mock_location = Mock()
        mock_location.latitude = 40.7128
        mock_location.longitude = -74.0060
        mock_location.address = "New York, NY"
        mock_location.raw = {
            "osm_type": "node",
            "place_id": "123",
            "address": {"city": "New York"}
        }
        
        mock_nominatim.return_value.geocode.return_value = mock_location
        
        # Create agent with mock
        agent = LocationProcessingAgent()
        
        result = await agent.process(
            goal="geocode address",
            address="New York"
        )
        
        assert result["status"] == "success"
        geocoded = result["data"][0]
        assert geocoded["coordinates"] == (40.7128, -74.0060)
        assert geocoded["address"] == "New York, NY"
        assert "details" in geocoded

@pytest.mark.asyncio
async def test_error_handling(agent):
    """Test error handling."""
    # Test with invalid goal
    result = await agent.process(
        goal="invalid goal",
        locations=SAMPLE_LOCATIONS
    )
    assert result["status"] == "error"
    assert "error" in result
    
    # Test with missing required arguments
    result = await agent.process(
        goal="filter locations by distance",
        locations=SAMPLE_LOCATIONS
        # Missing center and radius_km
    )
    assert result["status"] == "error"
    assert "error" in result

def test_state_management(agent):
    """Test agent state management."""
    # Initial state
    assert agent.state.status == "idle"
    assert agent.state.current_goal is None
    
    # After planning
    plan = agent.plan("filter locations by distance")
    assert agent.state.status == "planning"
    assert agent.state.current_goal == "filter locations by distance"
    assert isinstance(agent.state.current_plan, list)
    
    # Reset state
    agent.reset_state()
    assert agent.state.status == "idle"
    assert agent.state.current_goal is None
    assert agent.state.memory == {} 