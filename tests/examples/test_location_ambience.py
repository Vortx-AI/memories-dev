"""
Test location ambience analyzer example functionality.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
import numpy as np
from examples.location_ambience import LocationAnalyzer, simulate_location_data
from memories.config import Config
from memories import MemoryStore

@pytest.fixture
def memory_store():
    """Create a memory store for testing."""
    config = Config(
        storage_path="./test_location_data",
        hot_memory_size=10,
        warm_memory_size=100,
        cold_memory_size=1000
    )
    return MemoryStore(config)

@pytest.fixture
def location_analyzer(memory_store):
    """Create a location analyzer for testing."""
    return LocationAnalyzer(memory_store)

@pytest.fixture
def mock_data():
    """Create mock satellite and environmental data."""
    return {
        "satellite_data": {
            "pc": {
                "sentinel-2-l2a": [{
                    "data": np.random.random((4, 100, 100)),  # Mock satellite bands
                    "metadata": {
                        "datetime": datetime.now().isoformat(),
                        "cloud_cover": 5.0
                    }
                }]
            }
        },
        "air_quality": {
            "aqi": 75.0,
            "pollutants": {
                "pm25": 15.0,
                "pm10": 30.0,
                "no2": 40.0
            }
        },
        "vector_data": {
            "osm": {
                "amenities": [
                    {
                        "type": "Feature",
                        "properties": {
                            "type": "parks",
                            "name": "Central Park",
                            "rating": 4.5
                        }
                    },
                    {
                        "type": "Feature",
                        "properties": {
                            "type": "restaurants",
                            "name": "Fine Dining",
                            "rating": 4.8
                        }
                    },
                    {
                        "type": "Feature",
                        "properties": {
                            "type": "cafes",
                            "name": "Coffee House",
                            "rating": 4.2
                        }
                    }
                ]
            }
        }
    }

@pytest.mark.asyncio
async def test_analyze_location(location_analyzer, mock_data):
    """Test location analysis functionality."""
    # Mock the data manager's prepare_training_data method
    location_analyzer.data_manager.prepare_training_data = AsyncMock(return_value=mock_data)
    
    # Create test location data
    location_data = {
        "id": "TEST_LOC_1",
        "name": "Test Location",
        "coordinates": [40.7128, -74.0060],
        "bbox": [40.7, -74.1, 40.8, -73.9]
    }
    
    # Test analysis
    insights = await location_analyzer.analyze_location(location_data)
    
    # Verify results structure
    assert "location_id" in insights
    assert "timestamp" in insights
    assert "location_analysis" in insights
    assert "recommendations" in insights
    
    # Check location analysis structure
    location_analysis = insights["location_analysis"]
    assert "environmental_scores" in location_analysis
    assert "urban_features" in location_analysis
    assert "noise_levels" in location_analysis
    assert "ambience_score" in location_analysis
    
    # Check environmental scores
    env_scores = location_analysis["environmental_scores"]
    assert "greenery" in env_scores
    assert "water_bodies" in env_scores
    assert "air_quality" in env_scores
    assert "urban_density" in env_scores
    
    # Verify score ranges
    assert 0 <= env_scores["greenery"] <= 1
    assert 0 <= env_scores["water_bodies"] <= 1
    assert 0 <= env_scores["air_quality"] <= 1
    assert 0 <= env_scores["urban_density"] <= 1
    
    # Check urban features
    urban_features = location_analysis["urban_features"]
    assert "parks" in urban_features
    assert "cafes" in urban_features
    assert "restaurants" in urban_features
    assert "cultural_venues" in urban_features
    
    # Check noise levels
    noise_levels = location_analysis["noise_levels"]
    assert "average_db" in noise_levels
    assert "peak_hours" in noise_levels
    assert "quiet_hours" in noise_levels
    assert 40 <= noise_levels["average_db"] <= 70

@pytest.mark.asyncio
async def test_analyze_location_data(location_analyzer, mock_data):
    """Test location data analysis."""
    location_data = simulate_location_data()
    
    # Test analysis
    insights = await location_analyzer._analyze_location_data(location_data, mock_data)
    
    # Verify structure and content
    assert isinstance(insights, dict)
    assert insights["location_id"] == location_data["id"]
    assert isinstance(insights["timestamp"], str)
    assert len(insights["recommendations"]) > 0

@pytest.fixture
def mock_memory_store():
    """Create a memory store with mock data for testing."""
    config = Config(
        storage_path="./test_location_data",
        hot_memory_size=10,
        warm_memory_size=100,
        cold_memory_size=1000
    )
    store = MemoryStore(config)
    return store

@pytest.fixture
def test_location():
    """Create test location data."""
    return {
        "id": "TEST_1",
        "name": "Test Location 1",
        "coordinates": {
            "lat": 37.7749,
            "lon": -122.4194
        },
        "bbox": [-122.5, 37.5, -122.0, 38.0]
    }

def test_store_insights(location_analyzer, test_location):
    """Test insights storage functionality."""
    # Clear Redis before running the test
    location_analyzer.memory_store.hot_memory.clear()
    
    # Create test insights
    insights = {
        "location_id": test_location["id"],
        "timestamp": datetime.now().isoformat(),
        "location_analysis": {
            "environmental_scores": {
                "greenery": 0.85,
                "water_bodies": 0.6,
                "air_quality": 0.75,
                "urban_density": 0.5
            },
            "urban_features": {
                "parks": [],
                "cafes": [],
                "restaurants": [],
                "cultural_venues": []
            },
            "noise_levels": {
                "average_db": 55.0,
                "peak_hours": ["17:00-21:00"],
                "quiet_hours": ["23:00-05:00"]
            },
            "ambience_score": 0.85
        },
        "recommendations": [
            "Excellent green spaces - ideal for outdoor activities and recreation.",
            "Premium location with excellent balance of nature and urban amenities."
        ]
    }
    
    # Store insights
    location_analyzer._store_insights(insights, test_location)
    
    # Verify storage in hot memory (due to high ambience score)
    hot_memories = location_analyzer.memory_store.hot_memory.retrieve_all()
    assert len(hot_memories) > 0
    assert any(mem["location_id"] == test_location["id"] for mem in hot_memories)
    
    # Verify insights structure
    stored_insight = next(mem for mem in hot_memories if mem["location_id"] == test_location["id"])
    assert "location_analysis" in stored_insight
    assert "environmental_scores" in stored_insight["location_analysis"]
    assert "ambience_score" in stored_insight["location_analysis"]
    assert "recommendations" in stored_insight

def test_calculate_environmental_scores(location_analyzer):
    """Test environmental score calculations."""
    satellite_features = {
        "greenery_index": np.array([0.7, 0.8, 0.9]),
        "water_index": np.array([0.2, 0.3, 0.4]),
        "built_up_index": np.array([0.5, 0.6, 0.7])
    }
    
    air_quality = {
        "aqi": 75.0
    }
    
    scores = location_analyzer._calculate_environmental_scores(satellite_features, air_quality)
    
    assert "greenery" in scores
    assert "water_bodies" in scores
    assert "air_quality" in scores
    assert "urban_density" in scores
    
    assert 0 <= scores["greenery"] <= 1
    assert 0 <= scores["water_bodies"] <= 1
    assert 0 <= scores["air_quality"] <= 1
    assert 0 <= scores["urban_density"] <= 1

def test_analyze_urban_features(location_analyzer, mock_data):
    """Test urban features analysis."""
    features = location_analyzer._analyze_urban_features(mock_data)
    
    # Verify feature categories
    assert "parks" in features
    assert "cafes" in features
    assert "restaurants" in features
    assert "cultural_venues" in features
    
    # Check venue data structure
    for category, venues in features.items():
        for venue in venues:
            assert "name" in venue
            assert "distance" in venue
            assert "rating" in venue
            assert 0 < venue["distance"] < 5
            assert 0 <= venue["rating"] <= 5

def test_estimate_noise_levels(location_analyzer):
    """Test noise level estimation."""
    urban_features = {
        "parks": [{"name": "Park 1"}, {"name": "Park 2"}],
        "restaurants": [{"name": "Restaurant 1"}],
        "cafes": [{"name": "Cafe 1"}, {"name": "Cafe 2"}]
    }
    
    noise_levels = location_analyzer._estimate_noise_levels(urban_features)
    
    assert "average_db" in noise_levels
    assert "peak_hours" in noise_levels
    assert "quiet_hours" in noise_levels
    
    assert 40 <= noise_levels["average_db"] <= 70
    assert isinstance(noise_levels["peak_hours"], list)
    assert isinstance(noise_levels["quiet_hours"], list)

def test_calculate_ambience_score(location_analyzer):
    """Test ambience score calculation."""
    env_scores = {
        "greenery": 0.8,
        "air_quality": 0.7,
        "urban_density": 0.6
    }
    
    urban_features = {
        "parks": [{"name": "Park 1"}],
        "restaurants": [{"name": "Restaurant 1"}, {"name": "Restaurant 2"}],
        "cafes": [{"name": "Cafe 1"}]
    }
    
    noise_levels = {
        "average_db": 55.0
    }
    
    score = location_analyzer._calculate_ambience_score(
        env_scores,
        urban_features,
        noise_levels
    )
    
    assert isinstance(score, float)
    assert 0 <= score <= 1

def test_generate_recommendations(location_analyzer):
    """Test recommendation generation."""
    env_scores = {
        "greenery": 0.8,
        "air_quality": 0.4,
        "urban_density": 0.7
    }
    
    urban_features = {
        "parks": [{"name": "Park 1"}, {"name": "Park 2"}],
        "restaurants": [{"name": "Restaurant 1"}],
        "cafes": []
    }
    
    noise_levels = {
        "average_db": 68.0
    }
    
    recommendations = location_analyzer._generate_recommendations(
        env_scores,
        urban_features,
        noise_levels,
        0.7
    )
    
    assert isinstance(recommendations, list)
    assert len(recommendations) > 0
    assert any("green spaces" in rec.lower() for rec in recommendations)
    assert any("air quality" in rec.lower() for rec in recommendations)
    assert any("noise levels" in rec.lower() for rec in recommendations)

def test_simulated_data():
    """Test location data simulation."""
    data = simulate_location_data()
    
    # Verify required fields
    assert "id" in data
    assert "name" in data
    assert "coordinates" in data
    assert "bbox" in data
    
    # Check coordinates
    coords = data["coordinates"]
    assert "lat" in coords
    assert "lon" in coords
    assert 37.7 <= coords["lat"] <= 37.8
    assert -122.5 <= coords["lon"] <= -122.4
    
    # Verify bbox format
    assert len(data["bbox"]) == 4
    assert all(isinstance(x, float) for x in data["bbox"]) 