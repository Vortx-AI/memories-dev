"""
Traffic Pattern Analyzer Example
--------------------------------
This example demonstrates using the Memories-Dev framework to analyze
traffic patterns using Overture Maps data.
"""

import os
import logging
import asyncio
import uuid
from datetime import datetime, timedelta
import random
import numpy as np
from typing import Dict, List, Any, Tuple
from pathlib import Path
import logging

from memories import MemoryStore
from memories.config import Config
from memories.data_acquisition import DataManager
from memories.utils.processors import ImageProcessor, VectorProcessor
from memories.data_acquisition.sources.overture_api import OvertureAPI

class TrafficAnalyzer:
    """Analyzes traffic patterns and road conditions."""

    def __init__(self, memory_store, data_manager):
        """Initialize traffic analyzer.
        
        Args:
            memory_store: Memory store for persisting insights
            data_manager: Data manager for data acquisition
        """
        self.memory_store = memory_store
        self.data_manager = data_manager
        self.overture_api = OvertureAPI()
        self.image_processor = ImageProcessor()
        self.vector_processor = VectorProcessor()

    async def analyze_traffic(self, road_data):
        """Analyze traffic patterns for a road segment.
        
        Args:
            road_data: Road segment data including bbox
            
        Returns:
            Dictionary containing traffic analysis insights
            
        Raises:
            ValueError: If required data is missing
        """
        if not road_data:
            raise ValueError("Missing road data")
            
        if 'bbox' not in road_data:
            raise ValueError("Missing bbox data")
            
        try:
            overture_data = await self.overture_api.search(road_data['bbox'])
            insights = await self._analyze_traffic_data(road_data, overture_data)
            
            return {
                "road_id": road_data.get("id"),
                "timestamp": datetime.now().isoformat(),
                "traffic_metrics": insights["traffic_metrics"],
                "road_conditions": insights["road_conditions"],
                "recommendations": insights["recommendations"]
            }
        except Exception as e:
            logging.error(f"Error analyzing traffic: {str(e)}")
            return {
                "error": str(e),
                "road_id": road_data.get("id"),
                "timestamp": datetime.now().isoformat()
            }

    async def _analyze_traffic_data(self, road_segment, overture_data):
        """Analyze traffic data for a road segment.
        
        Args:
            road_segment: Road segment data
            overture_data: Overture Maps data
            
        Returns:
            Dictionary containing traffic insights
        """
        # Check if Overture data is empty
        if not overture_data or not overture_data.get("roads", {}).get("features"):
            return {
                "traffic_metrics": {
                    "congestion_level": 0.0,
                    "average_speed": 0.0,
                    "volume": 0,
                    "peak_hours": []
                },
                "road_conditions": {
                    "surface_quality": 0.0,
                    "maintenance_status": "unknown",
                    "risk_factors": []
                },
                "congestion_patterns": {
                    "daily_pattern": [],
                    "severity": 0.0,
                    "bottleneck_risk": 0.0
                },
                "hazards": [],
                "predictions": {
                    "short_term": {"expected_congestion": 0.0, "peak_likelihood": 0.0},
                    "long_term": {"maintenance_needed": False, "improvement_priority": 0.0},
                    "risk_assessment": {"accident_risk": 0.0, "infrastructure_risk": 0.0}
                },
                "recommendations": ["No data available for analysis"]
            }
        
        sensor_data = road_segment.get("sensor_data", {})
        road_type = road_segment.get("type", "unknown")
        
        traffic_metrics = self._calculate_traffic_metrics(sensor_data, road_type)
        road_conditions = self._analyze_road_conditions(
            self._extract_satellite_features(overture_data),
            road_segment
        )
        congestion_patterns = self._analyze_congestion_patterns(traffic_metrics, road_type)
        hazards = self._detect_road_hazards(self._extract_satellite_features(overture_data))
        predictions = self._generate_predictions(traffic_metrics, congestion_patterns, road_conditions)
        
        recommendations = [
            "Consider alternate routes during peak hours",
            "Monitor weather conditions",
            "Plan for maintenance in next 2 weeks"
        ]
        
        return {
            "traffic_metrics": traffic_metrics,
            "road_conditions": road_conditions,
            "congestion_patterns": congestion_patterns,
            "hazards": hazards,
            "predictions": predictions,
            "recommendations": recommendations
        }

    def _calculate_traffic_metrics(self, sensor_data, road_type):
        """Calculate traffic metrics for a road segment."""
        if not sensor_data:
            return {
                "congestion_level": 0.0,
                "average_speed": 0.0,
                "volume": 0,
                "peak_hours": []
            }
            
        traffic_counts = sensor_data.get("traffic_counts", [])
        speeds = sensor_data.get("average_speed", [])
        
        if not traffic_counts or not speeds:
            return {
                "congestion_level": 0.0,
                "average_speed": 0.0,
                "volume": 0,
                "peak_hours": []
            }
        
        # Filter out any None or invalid values
        traffic_counts = [count for count in traffic_counts if isinstance(count, (int, float)) and count >= 0]
        speeds = [speed for speed in speeds if isinstance(speed, (int, float)) and speed >= 0]
        
        if not traffic_counts or not speeds:
            return {
                "congestion_level": 0.0,
                "average_speed": 0.0,
                "volume": 0,
                "peak_hours": []
            }
        
        avg_volume = np.mean(traffic_counts)
        avg_speed = np.mean(speeds)
        max_volume = max(traffic_counts)
        max_speed = max(speeds)
        
        # Calculate congestion level (0-1) based on volume and speed
        volume_factor = min(1.0, avg_volume / (max_volume if max_volume > 0 else 1))
        speed_factor = 1.0 - (avg_speed / max_speed if max_speed > 0 else 0)
        congestion_level = (volume_factor + speed_factor) / 2
        
        # Identify peak hours
        peak_threshold = np.percentile(traffic_counts, 75)
        peak_indices = [i for i, count in enumerate(traffic_counts) if count >= peak_threshold]
        peak_hours = [f"{(8 + i):02d}:00" for i in peak_indices]
        
        return {
            "congestion_level": congestion_level,
            "average_speed": float(avg_speed),
            "volume": int(avg_volume),
            "peak_hours": peak_hours
        }

    def _analyze_road_conditions(self, satellite_features, road_segment):
        """Analyze road conditions."""
        if not satellite_features or not road_segment:
            return {
                "surface_quality": 0.0,
                "maintenance_status": "unknown",
                "risk_factors": []
            }
            
        surface_quality = satellite_features.get("condition_score", 0.8)
        maintenance_history = satellite_features.get("maintenance_history", [])
        
        # Calculate maintenance status
        if len(maintenance_history) >= 3:
            maintenance_status = "good"
        elif len(maintenance_history) >= 1:
            maintenance_status = "fair"
        else:
            maintenance_status = "needs_inspection"
        
        risk_factors = []
        if surface_quality < 0.7:
            risk_factors.append("surface_degradation")
        if maintenance_status == "needs_inspection":
            risk_factors.append("maintenance_required")
        if road_segment.get("type") == "motorway" and surface_quality < 0.8:
            risk_factors.append("high_speed_risk")
        
        return {
            "surface_quality": surface_quality,
            "maintenance_status": maintenance_status,
            "risk_factors": risk_factors
        }

    def _analyze_congestion_patterns(self, traffic_metrics, road_type):
        """Analyze congestion patterns."""
        if not traffic_metrics:
            return {
                "daily_pattern": [],
                "severity": 0.0,
                "bottleneck_risk": 0.0
            }
            
        congestion_level = traffic_metrics.get("congestion_level", 0)
        volume = traffic_metrics.get("volume", 0)
        peak_hours = traffic_metrics.get("peak_hours", [])
        
        # Determine daily pattern
        daily_pattern = []
        if "08:00" in peak_hours:
            daily_pattern.append("morning_peak")
        if "17:00" in peak_hours:
            daily_pattern.append("evening_peak")
        
        # Calculate severity based on road type and congestion
        base_severity = congestion_level
        if road_type == "motorway":
            severity = base_severity * 1.5  # Higher impact on motorways
        elif road_type == "arterial":
            severity = base_severity * 1.2  # Moderate impact on arterial roads
        else:
            severity = base_severity
        
        # Calculate bottleneck risk based on severity and volume
        bottleneck_risk = min(1.0, (severity * volume) / 1000)
        
        return {
            "daily_pattern": daily_pattern,
            "severity": min(1.0, severity),
            "bottleneck_risk": bottleneck_risk
        }

    def _detect_road_hazards(self, satellite_features):
        """Detect road hazards."""
        if not satellite_features:
            return []
            
        hazards = []
        
        surface_condition = satellite_features.get("surface_condition", "good")
        weather_impact = satellite_features.get("weather_impact", "low")
        visibility = satellite_features.get("visibility", "good")
        
        if surface_condition == "fair":
            hazards.append({
                "type": "surface_wear",
                "severity": 0.4
            })
        elif surface_condition == "poor":
            hazards.append({
                "type": "surface_damage",
                "severity": 0.8
            })
        
        if weather_impact == "moderate":
            hazards.append({
                "type": "weather_hazard",
                "severity": 0.5
            })
        elif weather_impact == "severe":
            hazards.append({
                "type": "severe_weather",
                "severity": 0.9
            })
        
        if visibility == "poor":
            hazards.append({
                "type": "visibility_hazard",
                "severity": 0.7
            })
        
        return hazards

    def _generate_predictions(self, traffic_metrics, congestion_patterns, road_conditions):
        """Generate traffic predictions."""
        if not traffic_metrics or not congestion_patterns or not road_conditions:
            return {
                "short_term": {"expected_congestion": 0.0, "peak_likelihood": 0.0},
                "long_term": {"maintenance_needed": False, "improvement_priority": 0.0},
                "risk_assessment": {"accident_risk": 0.0, "infrastructure_risk": 0.0}
            }
            
        return {
            "short_term": {
                "expected_congestion": congestion_patterns["severity"],
                "peak_likelihood": 0.8 if congestion_patterns["daily_pattern"] else 0.3
            },
            "long_term": {
                "maintenance_needed": road_conditions["maintenance_status"] == "needs_inspection",
                "improvement_priority": 0.7 if road_conditions["risk_factors"] else 0.2
            },
            "risk_assessment": {
                "accident_risk": min(1.0, congestion_patterns["severity"] * 0.8),
                "infrastructure_risk": 1.0 - road_conditions["surface_quality"]
            }
        }

    def _extract_satellite_features(self, overture_data):
        """Extract relevant features from satellite data."""
        if not overture_data or not overture_data.get("roads", {}).get("features"):
            return None
            
        return {
            "surface_condition": "fair",
            "weather_impact": "moderate",
            "visibility": "good",
            "condition_score": 0.85,
            "maintenance_history": ["2023-01", "2023-06", "2023-12"]
        }

def simulate_road_segment() -> Dict[str, Any]:
    """Generate simulated road segment data for testing."""
    road_types = ["motorway", "arterial", "local"]
    traffic_counts = [random.randint(100, 500) for _ in range(24)]
    speeds = [random.randint(20, 70) for _ in range(24)]
    
    # Ensure congested pattern has higher counts and lower speeds
    if random.random() < 0.3:  # 30% chance of congested pattern
        traffic_counts = [count * 2 for count in traffic_counts]
        speeds = [speed * 0.5 for speed in speeds]
    
    return {
        "id": str(uuid.uuid4()),
        "name": f"Road_{random.randint(1000, 9999)}",
        "type": random.choice(road_types),
        "coordinates": {
            "start": {
                "lat": round(random.uniform(37.7, 37.8), 4),
                "lon": round(random.uniform(-122.5, -122.4), 4)
            },
            "end": {
                "lat": round(random.uniform(37.7, 37.8), 4),
                "lon": round(random.uniform(-122.5, -122.4), 4)
            }
        },
        "bbox": [-122.5, 37.5, -122.0, 38.0],
        "sensor_data": {
            "traffic_counts": traffic_counts,
            "average_speed": speeds,
            "timestamps": [
                (datetime.now() - timedelta(hours=i)).isoformat()
                for i in range(24, 0, -1)
            ]
        }
    }

async def main():
    """Run the traffic pattern analyzer example."""
    # Initialize memory store
    config = Config(
        storage_path="./traffic_data",
        hot_memory_size=50,
        warm_memory_size=200,
        cold_memory_size=1000
    )
    memory_store = MemoryStore(config)
    
    # Create traffic analyzer
    data_manager = DataManager(cache_dir="traffic_cache")
    analyzer = TrafficAnalyzer(memory_store, data_manager)
    
    # Analyze multiple road segments
    for _ in range(3):
        road_data = simulate_road_segment()
        insights = await analyzer.analyze_traffic(road_data)
        
        print(f"\nAnalysis for {road_data['name']} ({road_data['type']}):")
        print(f"Start: {road_data['coordinates']['start']['lat']}, {road_data['coordinates']['start']['lon']}")
        print(f"End: {road_data['coordinates']['end']['lat']}, {road_data['coordinates']['end']['lon']}")
        
        if "error" not in insights:
            print("\nTraffic Metrics:")
            metrics = insights["traffic_metrics"]
            print(f"- Congestion Level: {metrics['congestion_level']:.2f}")
            print(f"- Average Speed: {metrics['average_speed']:.1f} mph")
            print(f"- Volume: {metrics['volume']} vehicles/hour")
            print(f"- Peak Hours: {', '.join(metrics['peak_hours'])}")
            
            print("\nRoad Conditions:")
            conditions = insights["road_conditions"]
            print(f"- Surface Quality: {conditions['surface_quality']:.2f}")
            print(f"- Maintenance Status: {conditions['maintenance_status']}")
            print(f"- Risk Factors: {', '.join(conditions['risk_factors'])}")
            
            print("\nRecommendations:")
            for rec in insights["recommendations"]:
                print(f"- {rec}")
        else:
            print(f"Error: {insights['error']}")

if __name__ == "__main__":
    asyncio.run(main()) 