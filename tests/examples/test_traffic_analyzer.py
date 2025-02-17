"""
Test traffic analyzer example functionality with Overture Maps data.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import numpy as np
from pathlib import Path
from examples.traffic_analyzer import TrafficAnalyzer
from memories.config import Config
from memories import MemoryStore
from memories.data_acquisition import DataManager

@pytest.fixture
def memory_store():
    """Create a memory store for testing."""
    config = Config(
        storage_path="test_traffic_data",
        hot_memory_size=50,
        warm_memory_size=200,
        cold_memory_size=1000
    )
    return MemoryStore(config)

@pytest.fixture
def data_manager():
    """Create a data manager for testing."""
    return DataManager(cache_dir="test_cache")

@pytest.fixture
def traffic_analyzer(memory_store, data_manager):
    """Create a traffic analyzer for testing."""
    return TrafficAnalyzer(memory_store, data_manager)

@pytest.fixture
def mock_overture_data():
    """Create mock Overture Maps data for testing."""
    return {
        "roads": {
            "features": [
                {
                    "type": "Feature",
                    "properties": {
                        "class": "motorway",
                        "lanes": 4,
                        "surface": "paved",
                        "speed_limit": 65,
                        "toll": False
                    }
                },
                {
                    "type": "Feature",
                    "properties": {
                        "class": "primary",
                        "lanes": 3,
                        "surface": "paved",
                        "speed_limit": 45,
                        "toll": False
                    }
                },
                {
                    "type": "Feature",
                    "properties": {
                        "class": "residential",
                        "lanes": 2,
                        "surface": "paved",
                        "speed_limit": 25,
                        "toll": False
                    }
                }
            ]
        },
        "buildings": {
            "features": [
                {
                    "type": "Feature",
                    "properties": {
                        "type": "commercial",
                        "height": 20
                    }
                }
            ]
        },
        "places": {
            "features": [
                {
                    "type": "Feature",
                    "properties": {
                        "class": "parking",
                        "name": "Test Parking"
                    }
                }
            ]
        },
        "bbox": [-122.5, 37.5, -122.0, 38.0]
    }

@pytest.fixture
def road_segment():
    """Create test road segment data."""
    return {
        "id": "road-123",
        "name": "Test Highway",
        "type": "motorway",
        "bbox": [-122.5, 37.5, -122.0, 38.0],
        "lanes": 4,
        "speed_limit": 65,
        "surface": "paved",
        "sensor_data": {
            "traffic_counts": [100, 150, 200, 250, 300],
            "average_speed": [60, 55, 45, 40, 35],
            "timestamps": [
                (datetime.now() - timedelta(hours=i)).isoformat()
                for i in range(5, 0, -1)
            ]
        }
    }

@pytest.mark.asyncio
async def test_analyze_traffic(traffic_analyzer, road_segment, mock_overture_data):
    """Test traffic analysis functionality using Overture data."""
    # Mock the Overture API search method
    traffic_analyzer.overture_api.search = AsyncMock(return_value=mock_overture_data)
    
    # Test analysis
    insights = await traffic_analyzer.analyze_traffic(road_segment)
    
    # Verify results structure
    assert "road_id" in insights
    assert "timestamp" in insights
    assert "traffic_metrics" in insights
    assert "recommendations" in insights
    
    # Verify traffic metrics
    metrics = insights["traffic_metrics"]
    assert "congestion_level" in metrics
    assert "average_speed" in metrics
    assert "volume" in metrics
    assert "peak_hours" in metrics
    
    # Verify score ranges
    assert 0 <= metrics["congestion_level"] <= 1
    assert metrics["average_speed"] >= 0
    assert metrics["volume"] >= 0
    
    # Verify recommendations
    assert isinstance(insights["recommendations"], list)
    assert len(insights["recommendations"]) > 0
    assert all(isinstance(rec, str) for rec in insights["recommendations"])

@pytest.mark.asyncio
async def test_analyze_traffic_data(traffic_analyzer, road_segment, mock_overture_data):
    """Test traffic data analysis using Overture data."""
    insights = await traffic_analyzer._analyze_traffic_data(road_segment, mock_overture_data)
    
    # Verify traffic metrics structure
    metrics = insights["traffic_metrics"]
    assert "congestion_level" in metrics
    assert "average_speed" in metrics
    assert "volume" in metrics
    assert "peak_hours" in metrics
    
    # Verify road conditions
    assert "road_conditions" in insights
    assert "surface_quality" in insights["road_conditions"]
    assert "maintenance_status" in insights["road_conditions"]

def test_calculate_traffic_metrics(traffic_analyzer):
    """Test traffic metrics calculation."""
    sensor_data = {
        "traffic_counts": [100, 150, 200, 250, 300],
        "average_speed": [60, 55, 45, 40, 35],
        "timestamps": [
            (datetime.now() - timedelta(hours=i)).isoformat()
            for i in range(5, 0, -1)
        ]
    }
    
    metrics = traffic_analyzer._calculate_traffic_metrics(sensor_data, "motorway")
    
    # Verify metrics structure
    assert "congestion_level" in metrics
    assert "average_speed" in metrics
    assert "volume" in metrics
    assert "peak_hours" in metrics
    
    # Verify metric ranges
    assert 0 <= metrics["congestion_level"] <= 1
    assert metrics["average_speed"] > 0
    assert metrics["volume"] > 0
    assert isinstance(metrics["peak_hours"], list)

def test_analyze_road_conditions(traffic_analyzer):
    """Test road conditions analysis."""
    satellite_features = {
        "surface_type": "paved",
        "maintenance_history": ["2023-01", "2023-06", "2023-12"],
        "condition_score": 0.85
    }
    
    road_segment = {
        "type": "motorway",
        "surface": "paved",
        "lanes": 4
    }
    
    conditions = traffic_analyzer._analyze_road_conditions(satellite_features, road_segment)
    
    # Verify conditions structure
    assert "surface_quality" in conditions
    assert "maintenance_status" in conditions
    assert "risk_factors" in conditions
    
    # Verify condition scores
    assert 0 <= conditions["surface_quality"] <= 1
    assert isinstance(conditions["maintenance_status"], str)
    assert isinstance(conditions["risk_factors"], list)

def test_analyze_congestion_patterns(traffic_analyzer):
    """Test congestion pattern analysis."""
    traffic_metrics = {
        "congestion_level": 0.75,
        "average_speed": 35,
        "volume": 250,
        "peak_hours": ["08:00", "17:00"]
    }
    
    patterns = traffic_analyzer._analyze_congestion_patterns(traffic_metrics, "motorway")
    
    # Verify patterns structure
    assert "daily_pattern" in patterns
    assert "severity" in patterns
    assert "bottleneck_risk" in patterns
    
    # Verify pattern analysis
    assert isinstance(patterns["daily_pattern"], list)
    assert 0 <= patterns["severity"] <= 1
    assert 0 <= patterns["bottleneck_risk"] <= 1

def test_detect_road_hazards(traffic_analyzer):
    """Test road hazard detection."""
    satellite_features = {
        "surface_condition": "fair",
        "weather_impact": "moderate",
        "visibility": "good"
    }
    
    hazards = traffic_analyzer._detect_road_hazards(satellite_features)
    
    # Verify hazard detection
    assert isinstance(hazards, list)
    assert all(isinstance(h, dict) for h in hazards)
    assert all("type" in h and "severity" in h for h in hazards)
    assert all(0 <= h["severity"] <= 1 for h in hazards)

def test_generate_predictions(traffic_analyzer):
    """Test traffic prediction generation."""
    traffic_metrics = {
        "congestion_level": 0.75,
        "average_speed": 35,
        "volume": 250,
        "peak_hours": ["08:00", "17:00"]
    }
    
    congestion_patterns = {
        "daily_pattern": ["morning_peak", "evening_peak"],
        "severity": 0.8,
        "bottleneck_risk": 0.6
    }
    
    road_conditions = {
        "surface_quality": 0.85,
        "maintenance_status": "good",
        "risk_factors": ["weather", "volume"]
    }
    
    predictions = traffic_analyzer._generate_predictions(
        traffic_metrics,
        congestion_patterns,
        road_conditions
    )
    
    # Verify predictions structure
    assert "short_term" in predictions
    assert "long_term" in predictions
    assert "risk_assessment" in predictions
    
    # Verify prediction content
    assert isinstance(predictions["short_term"], dict)
    assert isinstance(predictions["long_term"], dict)
    assert isinstance(predictions["risk_assessment"], dict)
    assert all(0 <= score <= 1 for score in predictions["risk_assessment"].values())

@pytest.mark.asyncio
async def test_traffic_analysis_with_invalid_data(traffic_analyzer):
    """Test traffic analysis with invalid or missing data."""
    invalid_road = {
        "id": "invalid-123",
        "name": "Invalid Road"
        # Missing required fields
    }
    
    with pytest.raises(ValueError):
        await traffic_analyzer.analyze_traffic(invalid_road)

@pytest.mark.asyncio
async def test_traffic_analysis_with_empty_data(traffic_analyzer, road_segment):
    """Test traffic analysis with empty Overture data."""
    empty_data = {
        "roads": {"features": []},
        "buildings": {"features": []},
        "places": {"features": []},
        "bbox": road_segment["bbox"]
    }
    
    traffic_analyzer.overture_api.search = AsyncMock(return_value=empty_data)
    
    insights = await traffic_analyzer.analyze_traffic(road_segment)
    
    # Verify that the analysis handles empty data gracefully
    assert insights["traffic_metrics"]["congestion_level"] == 0
    assert len(insights["recommendations"]) > 0

def test_memory_storage_integration(traffic_analyzer, road_segment, mock_overture_data):
    """Test integration with memory store."""
    # Store test data
    traffic_analyzer.memory_store.store({
        "road_id": road_segment["id"],
        "timestamp": datetime.now().isoformat(),
        "data": mock_overture_data
    })
    
    # Verify data retrieval
    stored_data = traffic_analyzer.memory_store.retrieve({
        "road_id": road_segment["id"]
    })
    
    assert stored_data is not None
    assert "road_id" in stored_data
    assert "data" in stored_data

def test_traffic_pattern_analysis(traffic_analyzer):
    """Test traffic pattern analysis functionality."""
    # Test with various traffic patterns
    normal_pattern = {
        "traffic_counts": [100, 200, 300, 200, 100],
        "average_speed": [60, 45, 30, 45, 60],
        "timestamps": [
            (datetime.now() - timedelta(hours=i)).isoformat()
            for i in range(5, 0, -1)
        ]
    }
    
    congested_pattern = {
        "traffic_counts": [200, 400, 600, 400, 200],
        "average_speed": [40, 25, 15, 25, 40],
        "timestamps": [
            (datetime.now() - timedelta(hours=i)).isoformat()
            for i in range(5, 0, -1)
        ]
    }
    
    off_peak_pattern = {
        "traffic_counts": [50, 75, 100, 75, 50],
        "average_speed": [65, 60, 55, 60, 65],
        "timestamps": [
            (datetime.now() - timedelta(hours=i)).isoformat()
            for i in range(5, 0, -1)
        ]
    }
    
    # Calculate metrics for each pattern
    normal_metrics = traffic_analyzer._calculate_traffic_metrics(normal_pattern, "motorway")
    congested_metrics = traffic_analyzer._calculate_traffic_metrics(congested_pattern, "motorway")
    off_peak_metrics = traffic_analyzer._calculate_traffic_metrics(off_peak_pattern, "motorway")
    
    # Verify pattern relationships
    assert congested_metrics["congestion_level"] > normal_metrics["congestion_level"]
    assert normal_metrics["congestion_level"] > off_peak_metrics["congestion_level"]
    assert off_peak_metrics["average_speed"] > normal_metrics["average_speed"]
    assert normal_metrics["average_speed"] > congested_metrics["average_speed"] 