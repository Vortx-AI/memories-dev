"""
Test traffic pattern analyzer example functionality.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
import numpy as np
from examples.traffic_analyzer import TrafficAnalyzer, simulate_road_segment
from memories.config import Config
from memories import MemoryStore

@pytest.fixture
def memory_store():
    """Create a memory store for testing."""
    config = Config(
        storage_path="./test_traffic_data",
        hot_memory_size=10,
        warm_memory_size=100,
        cold_memory_size=1000
    )
    return MemoryStore(config)

@pytest.fixture
def traffic_analyzer(memory_store):
    """Create a traffic analyzer for testing."""
    return TrafficAnalyzer(memory_store)

@pytest.fixture
def mock_data():
    """Create mock satellite and sensor data."""
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
        "traffic_sensors": {
            "average_speed": 45.0,
            "volume": 150,
            "occupancy": 0.3,
            "timestamp": datetime.now().isoformat()
        },
        "vector_data": {
            "osm": {
                "roads": [{
                    "type": "Feature",
                    "properties": {
                        "type": "highway",
                        "lanes": 4,
                        "speed_limit": 65
                    }
                }]
            }
        }
    }

@pytest.mark.asyncio
async def test_analyze_traffic(traffic_analyzer, mock_data):
    """Test traffic analysis functionality."""
    # Mock the data manager's prepare_training_data method
    traffic_analyzer.data_manager.prepare_training_data = AsyncMock(return_value=mock_data)
    
    # Create test road segment data
    road_data = simulate_road_segment()
    
    # Test analysis
    insights = await traffic_analyzer.analyze_traffic(road_data)
    
    # Verify results structure
    assert "road_id" in insights
    assert "timestamp" in insights
    assert "traffic_metrics" in insights
    assert "road_conditions" in insights
    assert "congestion_patterns" in insights
    assert "predictions" in insights
    assert "recommendations" in insights
    
    # Check traffic metrics
    metrics = insights["traffic_metrics"]
    assert "average_speed" in metrics
    assert "volume" in metrics
    assert "density" in metrics
    assert "congestion_level" in metrics
    assert "thresholds" in metrics
    
    # Verify metric ranges
    assert 15 <= metrics["average_speed"] <= 65
    assert 50 <= metrics["volume"] <= 200
    assert metrics["density"] > 0
    assert 0 <= metrics["congestion_level"] <= 1
    
    # Check road conditions
    conditions = insights["road_conditions"]
    assert "surface_quality" in conditions
    assert "weather_impact" in conditions
    assert "maintenance_score" in conditions
    assert "hazards" in conditions
    
    # Verify condition ranges
    assert 0 <= conditions["surface_quality"] <= 1
    assert 0 <= conditions["weather_impact"] <= 0.3
    assert 0 <= conditions["maintenance_score"] <= 1

@pytest.mark.asyncio
async def test_analyze_traffic_data(traffic_analyzer, mock_data):
    """Test traffic data analysis."""
    road_data = simulate_road_segment()
    
    # Test analysis
    insights = await traffic_analyzer._analyze_traffic_data(road_data, mock_data)
    
    # Verify structure and content
    assert isinstance(insights, dict)
    assert insights["road_id"] == road_data["id"]
    assert isinstance(insights["timestamp"], str)
    assert len(insights["recommendations"]) > 0

def test_store_insights(traffic_analyzer):
    """Test insights storage logic."""
    # Clear memory store before test
    traffic_analyzer.memory_store.hot_memory.clear()
    traffic_analyzer.memory_store.cold_memory.clear()
    
    # Create test insights with high congestion
    high_congestion_insights = {
        "traffic_metrics": {
            "congestion_level": 0.9
        },
        "timestamp": datetime.now().isoformat()
    }
    
    # Create test insights with low congestion
    low_congestion_insights = {
        "traffic_metrics": {
            "congestion_level": 0.4
        },
        "timestamp": datetime.now().isoformat()
    }
    
    # Test storage of high congestion road
    traffic_analyzer._store_insights(high_congestion_insights, {"id": "TEST_1"})
    hot_memories = traffic_analyzer.memory_store.hot_memory.retrieve_all()
    assert len(hot_memories) >= 1
    
    # Test storage of low congestion road
    traffic_analyzer._store_insights(low_congestion_insights, {"id": "TEST_2"})
    cold_memories = traffic_analyzer.memory_store.cold_memory.retrieve_all()
    assert len(cold_memories) >= 1

def test_calculate_traffic_metrics(traffic_analyzer):
    """Test traffic metrics calculations."""
    # Test highway metrics
    highway_metrics = traffic_analyzer._calculate_traffic_metrics(
        {"average_speed": 60, "volume": 180},
        "highway"
    )
    assert 45 <= highway_metrics["average_speed"] <= 65
    assert highway_metrics["volume"] > 0
    assert highway_metrics["density"] > 0
    
    # Test local road metrics
    local_metrics = traffic_analyzer._calculate_traffic_metrics(
        {"average_speed": 20, "volume": 80},
        "local"
    )
    assert 15 <= local_metrics["average_speed"] <= 25
    assert local_metrics["volume"] > 0
    assert local_metrics["density"] > 0

def test_analyze_road_conditions(traffic_analyzer):
    """Test road conditions analysis."""
    satellite_features = {
        "surface_index": np.array([0.7, 0.8, 0.9])
    }
    
    road_data = simulate_road_segment()
    conditions = traffic_analyzer._analyze_road_conditions(satellite_features, road_data)
    
    assert "surface_quality" in conditions
    assert "weather_impact" in conditions
    assert "maintenance_score" in conditions
    assert "hazards" in conditions
    
    assert 0 <= conditions["surface_quality"] <= 1
    assert 0 <= conditions["weather_impact"] <= 0.3
    assert 0 <= conditions["maintenance_score"] <= 1
    assert isinstance(conditions["hazards"], list)

def test_analyze_congestion_patterns(traffic_analyzer):
    """Test congestion pattern analysis."""
    traffic_metrics = {
        "congestion_level": 0.8,
        "average_speed": 35
    }
    
    patterns = traffic_analyzer._analyze_congestion_patterns(traffic_metrics, "highway")
    
    assert "peak_hours" in patterns
    assert "severity" in patterns
    assert "expected_duration" in patterns
    assert "recurring" in patterns
    
    assert patterns["severity"] in ["high", "moderate", "low"]
    assert isinstance(patterns["peak_hours"], list)
    assert 30 <= patterns["expected_duration"] <= 180
    assert isinstance(patterns["recurring"], bool)

def test_detect_road_hazards(traffic_analyzer):
    """Test road hazard detection."""
    satellite_features = {
        "surface_index": np.random.random((100, 100))
    }
    
    hazards = traffic_analyzer._detect_road_hazards(satellite_features)
    
    assert isinstance(hazards, list)
    for hazard in hazards:
        assert "type" in hazard
        assert "severity" in hazard
        assert "location" in hazard
        assert 0.3 <= hazard["severity"] <= 0.9
        assert hazard["type"] in ["pothole", "construction", "debris", "water accumulation"]

def test_generate_predictions(traffic_analyzer):
    """Test traffic prediction generation."""
    traffic_metrics = {
        "congestion_level": 0.7,
        "average_speed": 40
    }
    
    congestion_patterns = {
        "peak_hours": ["07:00-09:00", "16:00-18:00"],
        "expected_duration": 90,
        "severity": "moderate"
    }
    
    road_conditions = {
        "maintenance_score": 0.8,
        "hazards": []
    }
    
    predictions = traffic_analyzer._generate_predictions(
        traffic_metrics,
        congestion_patterns,
        road_conditions
    )
    
    assert "clearance_time" in predictions
    assert "next_peak" in predictions
    assert "confidence" in predictions
    
    assert predictions["clearance_time"] > 0
    assert 0.7 <= predictions["confidence"] <= 0.9

def test_generate_recommendations(traffic_analyzer):
    """Test recommendation generation."""
    traffic_metrics = {
        "congestion_level": 0.9,
        "average_speed": 25
    }
    
    congestion_patterns = {
        "peak_hours": ["07:00-09:00"],
        "severity": "high",
        "recurring": True
    }
    
    road_conditions = {
        "maintenance_score": 0.5,
        "hazards": [{
            "type": "pothole",
            "severity": 0.8,
            "location": "mile_marker_5"
        }]
    }
    
    predictions = {
        "clearance_time": 120,
        "next_peak": "16:00-18:00"
    }
    
    recommendations = traffic_analyzer._generate_recommendations(
        traffic_metrics,
        congestion_patterns,
        road_conditions,
        predictions
    )
    
    assert isinstance(recommendations, list)
    assert len(recommendations) > 0
    assert any("congestion" in rec.lower() for rec in recommendations)
    assert any("road conditions" in rec.lower() for rec in recommendations)
    assert any("pothole" in rec.lower() for rec in recommendations)

def test_simulated_data():
    """Test road segment data simulation."""
    data = simulate_road_segment()
    
    # Verify required fields
    assert "id" in data
    assert "name" in data
    assert "road_type" in data
    assert "coordinates" in data
    assert "bbox" in data
    
    # Check road type
    assert data["road_type"] in ["highway", "arterial", "local"]
    
    # Check coordinates
    coords = data["coordinates"]
    assert "start" in coords
    assert "end" in coords
    assert "lat" in coords["start"]
    assert "lon" in coords["start"]
    assert 37.7 <= coords["start"]["lat"] <= 37.8
    assert -122.5 <= coords["start"]["lon"] <= -122.4
    
    # Verify bbox format
    assert len(data["bbox"]) == 4
    assert all(isinstance(x, float) for x in data["bbox"]) 