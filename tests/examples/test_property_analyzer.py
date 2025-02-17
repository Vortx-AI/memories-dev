"""Tests for the property analyzer example."""

import pytest
from datetime import datetime, timedelta
import numpy as np
from typing import Dict, Any
from unittest.mock import MagicMock, patch
from unittest.mock import AsyncMock

from memories import MemoryStore
from memories.config import Config
from memories.data_acquisition import DataManager
from examples.property_analyzer import PropertyAnalyzer, simulate_property_data

@pytest.fixture
def memory_store():
    """Create a memory store for testing."""
    config = Config(
        storage_path="test_property_data",
        hot_memory_size=10,
        warm_memory_size=20,
        cold_memory_size=50
    )
    return MemoryStore(config)

@pytest.fixture
def data_manager():
    """Create a data manager for testing."""
    return DataManager(cache_dir="test_property_data")

@pytest.fixture
def property_analyzer(data_manager, memory_store):
    """Create a property analyzer for testing."""
    return PropertyAnalyzer(data_manager, memory_store)

@pytest.fixture
def mock_property_data():
    """Create mock property data for testing."""
    return {
        "id": "test123",
        "location": {
            "lat": 37.7749,
            "lon": -122.4194,
            "bbox": [-122.5, 37.7, -122.3, 37.8]
        },
        "condition": "good",
        "age": 15,
        "maintenance_history": [
            {"date": "2022-01-01", "type": "renovation"},
            {"date": "2022-06-01", "type": "repair"}
        ],
        "nearby_amenities": ["school", "park", "restaurant"],
        "nearby_schools": ["Elementary School", "High School"],
        "public_transport": ["bus_stop", "subway_station"],
        "area": 2000,
        "price_history": [
            {"date": "2020-01-01", "price": 500000},
            {"date": "2021-01-01", "price": 550000},
            {"date": "2022-01-01", "price": 600000}
        ]
    }

@pytest.fixture
def mock_satellite_data():
    # Create mock satellite data with NDVI bands
    red_band = np.random.random((100, 100))  # B04
    nir_band = np.random.random((100, 100))  # B08
    
    # Ensure some areas have vegetation (NDVI > 0.3)
    ndvi = (nir_band - red_band) / (nir_band + red_band)
    nir_band[ndvi < 0.3] *= 2  # Increase NIR values to create vegetation
    
    return {
        "sentinel-2-l2a": {
            "data": [
                np.random.random((100, 100)),  # B02
                np.random.random((100, 100)),  # B03
                red_band,  # B04
                nir_band   # B08
            ],
            "metadata": {
                "datetime": datetime.now().isoformat(),
                "cloud_cover": 10.0,
                "bands": ["B02", "B03", "B04", "B08"],
                "resolution": 10.0
            }
        }
    }

@pytest.fixture
def mock_overture_data():
    return {
        "buildings": [{"id": f"b{i}"} for i in range(50)],
        "roads": [{"id": f"r{i}"} for i in range(30)],
        "amenities": [{"id": f"a{i}"} for i in range(10)]
    }

@pytest.fixture
def test_property():
    """Create test property data."""
    return {
        "id": "test123",
        "location": {
            "bbox": [-122.5, 37.5, -122.0, 38.0]
        },
        "condition": "good",
        "age": 15,
        "price_history": [
            {"date": "2023-01", "price": 100000},
            {"date": "2023-02", "price": 102000},
            {"date": "2023-03", "price": 103000}
        ]
    }

@pytest.mark.asyncio
async def test_analyze_property(property_analyzer, mock_property_data):
    """Test property analysis."""
    insights = await property_analyzer.analyze_property(mock_property_data)
    
    assert insights["property_id"] == "test123"
    assert "timestamp" in insights
    assert "scores" in insights
    assert "recommendations" in insights
    
    scores = insights["scores"]
    assert 0 <= scores["condition"] <= 1
    assert 0 <= scores["location"] <= 1
    assert 0 <= scores["market"] <= 1
    assert 0 <= scores["investment_potential"] <= 1

@pytest.mark.asyncio
async def test_calculate_condition_score(property_analyzer):
    """Test condition score calculation."""
    test_data = {
        "condition": "excellent",
        "age": 5,
        "maintenance_history": [{"type": "renovation"}]
    }
    score = property_analyzer._calculate_condition_score(test_data)
    assert 0 <= score <= 1

@pytest.mark.asyncio
async def test_calculate_location_score(property_analyzer):
    """Test location score calculation."""
    property_data = {
        "nearby_amenities": ["school", "park"],
        "nearby_schools": ["Elementary"],
        "public_transport": ["bus_stop"],
        "area": 1000
    }
    buildings_data = [{"type": "residential"}, {"type": "commercial"}]
    score = property_analyzer._calculate_location_score(property_data, buildings_data)
    assert 0 <= score <= 1

@pytest.mark.asyncio
async def test_calculate_market_score(property_analyzer):
    """Test market score calculation."""
    test_data = {
        "price_history": [
            {"date": "2020-01", "price": 500000},
            {"date": "2021-01", "price": 550000},
            {"date": "2022-01", "price": 600000}
        ]
    }
    score = property_analyzer._calculate_market_score(test_data)
    assert 0 <= score <= 1

@pytest.mark.asyncio
async def test_calculate_investment_potential(property_analyzer):
    """Test investment potential calculation."""
    potential = property_analyzer._calculate_investment_potential(0.8, 0.7, 0.9, 0.6)
    
    assert isinstance(potential, float)
    assert 0 <= potential <= 1
    
    # Test with different scores
    high_potential = property_analyzer._calculate_investment_potential(0.9, 0.9, 0.9, 0.9)
    low_potential = property_analyzer._calculate_investment_potential(0.3, 0.3, 0.3, 0.3)
    assert high_potential > low_potential

@pytest.mark.asyncio
async def test_generate_recommendations(property_analyzer):
    """Test recommendations generation."""
    recommendations = property_analyzer._generate_recommendations(0.8, 0.7, 0.9, 0.6, 0.85)
    
    assert isinstance(recommendations, list)
    assert all(isinstance(r, str) for r in recommendations)

@pytest.mark.asyncio
async def test_property_analysis_with_invalid_data(property_analyzer):
    """Test property analysis with invalid data."""
    invalid_data = {"id": "test123"}  # Missing required fields
    insights = await property_analyzer.analyze_property(invalid_data)
    assert "error" in insights

@pytest.mark.asyncio
async def test_property_analysis_with_empty_data(property_analyzer):
    """Test property analysis with empty data."""
    insights = await property_analyzer.analyze_property({})
    assert "error" in insights

@pytest.mark.asyncio
async def test_memory_storage_integration(property_analyzer, test_property, mock_overture_data, mock_satellite_data):
    """Test memory storage integration."""
    # Mock API calls
    property_analyzer.overture_api.search = AsyncMock(return_value=mock_overture_data)
    property_analyzer.pc_api.search_and_download = AsyncMock(return_value=mock_satellite_data)
    
    # Analyze property
    insights = await property_analyzer.analyze_property(test_property)
    
    # Store data
    stored_key = f"property_analysis_{test_property['id']}"
    memory_data = {
        "key": stored_key,
        "type": "property_analysis",
        "data": insights,
        "timestamp": datetime.now().isoformat(),
        "metadata": {
            "source": "property_analyzer"
        }
    }
    property_analyzer.memory_store.store(memory_data, memory_type="warm")
    
    # Verify storage
    stored_data = property_analyzer.memory_store.retrieve({"key": stored_key}, memory_type="warm")
    
    assert stored_data is not None
    assert "data" in stored_data
    assert "scores" in stored_data["data"]

@pytest.mark.asyncio
async def test_price_history_analysis(property_analyzer):
    """Test price history analysis."""
    steady_history = {
        "price_history": [
            {"date": "2023-01", "price": 100000},
            {"date": "2023-02", "price": 102000},
            {"date": "2023-03", "price": 103000}
        ]
    }
    
    volatile_history = {
        "price_history": [
            {"date": "2023-01", "price": 100000},
            {"date": "2023-02", "price": 120000},
            {"date": "2023-03", "price": 90000}
        ]
    }
    
    steady_score = property_analyzer._calculate_market_score(steady_history)
    volatile_score = property_analyzer._calculate_market_score(volatile_history)
    
    assert steady_score >= volatile_score

@pytest.mark.asyncio
async def test_simulated_data():
    """Test simulated data generation."""
    data = simulate_property_data()
    assert isinstance(data, dict)
    assert "id" in data
    assert "location" in data
    assert "condition" in data

@pytest.mark.asyncio
async def test_analyze_property_with_satellite(property_analyzer, mock_satellite_data, mock_overture_data):
    """Test property analysis with satellite data."""
    with patch('memories.data_acquisition.sources.overture_api.OvertureAPI.search') as mock_overture_search, \
         patch('memories.data_acquisition.sources.planetary_compute.PlanetaryCompute.search_and_download') as mock_pc_search:
        
        mock_overture_search.return_value = mock_overture_data
        mock_pc_search.return_value = mock_satellite_data
        
        property_data = simulate_property_data()
        insights = await property_analyzer.analyze_property(property_data)
        
        assert "scores" in insights
        scores = insights["scores"]
        
        # Check environmental score
        assert "environmental" in scores
        assert 0 <= scores["environmental"] <= 1
        
        # Check investment potential includes environmental factor
        assert "investment_potential" in scores
        assert 0 <= scores["investment_potential"] <= 1
        
        # Check satellite metadata
        assert "satellite_metadata" in insights
        metadata = insights["satellite_metadata"]
        assert "datetime" in metadata
        assert "cloud_cover" in metadata
        assert "bands" in metadata
        assert "resolution" in metadata

@pytest.mark.asyncio
async def test_environmental_score_calculation(property_analyzer, mock_satellite_data):
    """Test environmental score calculation using satellite data."""
    score = property_analyzer._calculate_environmental_score(mock_satellite_data)
    
    assert isinstance(score, float)
    assert 0 <= score <= 1

@pytest.mark.asyncio
async def test_environmental_score_no_satellite_data(property_analyzer):
    """Test environmental score calculation with no satellite data."""
    score = property_analyzer._calculate_environmental_score({})
    
    assert isinstance(score, float)
    assert score == 0.5  # Default score when no data available

@pytest.mark.asyncio
async def test_investment_potential_with_environmental(property_analyzer):
    """Test investment potential calculation including environmental score."""
    potential = property_analyzer._calculate_investment_potential(
        condition_score=0.8,
        location_score=0.7,
        market_score=0.6,
        environmental_score=0.9
    )
    
    assert isinstance(potential, float)
    assert 0 <= potential <= 1
    
    # Test that environmental score affects the result
    lower_potential = property_analyzer._calculate_investment_potential(
        condition_score=0.8,
        location_score=0.7,
        market_score=0.6,
        environmental_score=0.1
    )
    
    assert potential > lower_potential

@pytest.mark.asyncio
async def test_recommendations_with_environmental(property_analyzer):
    """Test recommendation generation including environmental factors."""
    recommendations = property_analyzer._generate_recommendations(
        condition_score=0.8,
        location_score=0.7,
        market_score=0.6,
        environmental_score=0.3,  # Poor environmental score
        investment_potential=0.6
    )
    
    assert isinstance(recommendations, list)
    assert any("environmental" in rec.lower() or "green space" in rec.lower() 
              for rec in recommendations) 