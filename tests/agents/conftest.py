"""
Pytest configuration and shared fixtures for agent tests.
"""

import pytest
from unittest.mock import Mock
from typing import Dict, Any, List

from memories.models.load_model import LoadModel

# Common test data
@pytest.fixture
def sample_locations() -> List[Dict[str, Any]]:
    """Sample location data for testing."""
    return [
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
    """Create a mock model with common methods."""
    model = Mock(spec=LoadModel)
    
    # Add common model responses
    model.get_response.return_value = "Test response"
    
    return model

@pytest.fixture
def mock_geocoder():
    """Create a mock geocoder with common responses."""
    geocoder = Mock()
    
    # Mock location object
    location = Mock()
    location.latitude = 40.7128
    location.longitude = -74.0060
    location.address = "New York, NY"
    location.raw = {
        "osm_type": "node",
        "place_id": "123",
        "address": {"city": "New York"}
    }
    
    geocoder.geocode.return_value = location
    geocoder.reverse.return_value = location
    
    return geocoder

# Test utilities
def assert_tool_result(result: Dict[str, Any], expected_status: str = "success"):
    """Helper to assert common tool result structure."""
    assert isinstance(result, dict)
    assert "status" in result
    assert result["status"] == expected_status
    
    if expected_status == "success":
        assert "data" in result
        assert result["error"] is None
    else:
        assert "error" in result

def assert_agent_state(agent, expected_status: str):
    """Helper to assert agent state."""
    assert agent.state.status == expected_status
    if expected_status == "idle":
        assert agent.state.current_goal is None
        assert agent.state.current_plan is None
    elif expected_status == "completed":
        assert agent.state.last_result is not None
        assert agent.state.error is None 