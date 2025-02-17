"""
Test property analyzer example functionality.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
import numpy as np
from pathlib import Path
from examples.property_analyzer import PropertyAgent, simulate_property_data
from memories.config import Config
from memories import MemoryStore

@pytest.fixture
def memory_store():
    """Create a memory store for testing."""
    config = Config(
        storage_path="./test_property_data",
        hot_memory_size=10,
        warm_memory_size=100,
        cold_memory_size=1000
    )
    return MemoryStore(config)

@pytest.fixture
def property_agent(memory_store):
    """Create a property agent instance for testing."""
    return PropertyAgent(memory_store)

@pytest.fixture
def mock_data():
    """Create mock data for testing."""
    return {
        "satellite_imagery": np.random.rand(3, 10, 10),
        "local_context": {
            "amenities": [
                {"type": "restaurant", "distance": 0.5, "rating": 4.5},
                {"type": "park", "distance": 1.0, "rating": 4.0}
            ],
            "transportation": ["bus", "subway"],
            "schools": ["elementary", "high"]
        }
    }

@pytest.fixture
def property_data():
    """Create mock property data for testing."""
    return {
        "id": "123",
        "price": 500000,
        "size_sqft": 2000,
        "year_built": 1990,
        "condition": "good",
        "price_history": [450000, 475000, 500000],
        "bbox": [-122.5, 37.5, -122.0, 38.0]  # San Francisco area bounding box
    }

@pytest.mark.asyncio
async def test_analyze_property(property_agent, property_data, mock_data):
    """Test property analysis functionality."""
    # Mock the data manager's prepare_training_data method
    property_agent.data_manager.prepare_training_data = AsyncMock(return_value={
        "satellite_data": {
            "pc": {
                "sentinel-2-l2a": [{
                    "data": np.random.random((4, 100, 100)),
                    "metadata": {
                        "datetime": datetime.now().isoformat(),
                        "cloud_cover": 5.0
                    }
                }]
            }
        },
        "vector_data": {
            "osm": {
                "buildings": [{
                    "type": "Feature",
                    "properties": {
                        "area": 1000.0,
                        "type": "building"
                    },
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]]
                    }
                }]
            }
        }
    })
    
    insights = await property_agent.analyze_property(property_data)
    
    assert "timestamp" in insights
    assert "property_analysis" in insights
    assert "recommendations" in insights
    
    analysis = insights["property_analysis"]
    assert 0 <= analysis["condition_score"] <= 1
    assert 0 <= analysis["location_score"] <= 1
    assert 0 <= analysis["market_score"] <= 1
    assert 0 <= analysis["investment_potential"] <= 1

@pytest.mark.asyncio
async def test_analyze_property_data(property_agent, property_data, mock_data):
    """Test property data analysis."""
    insights = await property_agent._analyze_property_data(property_data, mock_data)
    
    assert "timestamp" in insights
    assert "property_analysis" in insights
    assert "recommendations" in insights
    
    analysis = insights["property_analysis"]
    assert "satellite_features" in analysis
    assert all(k in analysis["satellite_features"] for k in ["ndwi", "greenery_index", "built_up_index"])

@pytest.mark.asyncio
async def test_store_insights(property_agent, property_data, mock_data):
    """Test insights storage functionality."""
    insights = await property_agent._analyze_property_data(property_data, mock_data)
    property_agent._store_insights(insights, property_data)
    
    # Check memory tiers
    hot_memories = property_agent.memory_store.hot_memory.retrieve_all()
    warm_memories = property_agent.memory_store.warm_memory.retrieve_all()
    cold_memories = property_agent.memory_store.cold_memory.retrieve_all()
    
    # At least one memory tier should have the insights
    assert len(hot_memories) > 0 or len(warm_memories) > 0 or len(cold_memories) > 0

def test_generate_recommendations(property_agent):
    """Test recommendation generation."""
    recommendations = property_agent._generate_recommendations(
        condition_score=0.8,
        location_score=0.7,
        market_score=0.9,
        investment_potential=0.85
    )
    
    assert isinstance(recommendations, list)
    assert len(recommendations) > 0
    assert all(isinstance(r, str) for r in recommendations)

def test_simulated_data():
    """Test simulated property data generation."""
    data = simulate_property_data()
    
    assert isinstance(data, dict)
    assert "id" in data
    assert "price" in data
    assert "size_sqft" in data
    assert "year_built" in data
    assert "condition" in data
    assert "price_history" in data 