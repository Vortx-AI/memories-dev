"""
Example demonstrating the use of the memory system for traffic pattern analysis.

This example shows how to:
1. Analyze traffic patterns using satellite imagery and sensor data
2. Store traffic insights in tiered memory based on congestion levels
3. Generate traffic predictions and recommendations
4. Track historical traffic patterns
"""

import asyncio
import uuid
from datetime import datetime, timedelta
import random
import numpy as np
from typing import Dict, List, Any, Tuple
from pathlib import Path

from memories import MemoryStore
from memories.config import Config
from memories.data_acquisition import DataManager
from memories.utils.processors import ImageProcessor, VectorProcessor

class TrafficAnalyzer:
    """Analyze traffic patterns and congestion using satellite imagery and sensor data."""
    
    def __init__(self, memory_store: MemoryStore):
        """Initialize the traffic analyzer.
        
        Args:
            memory_store: Memory store for caching and storing insights
        """
        self.memory_store = memory_store
        self.data_manager = DataManager(cache_dir=str(Path.home() / ".memories" / "cache"))
        self.image_processor = ImageProcessor()
        self.vector_processor = VectorProcessor()
    
    async def analyze_traffic(
        self,
        road_segment: Dict[str, Any],
        time_window: int = 24
    ) -> Dict[str, Any]:
        """
        Analyze traffic patterns for a road segment.
        
        Args:
            road_segment: Dictionary containing road information
                Required fields: id, name, coordinates, bbox, road_type
            time_window: Hours of historical data to analyze (default: 24)
        
        Returns:
            Dictionary containing traffic analysis insights
        """
        # Get historical data for the time window
        end_date = datetime.now()
        start_date = end_date - timedelta(hours=time_window)
        
        data = await self.data_manager.prepare_training_data(
            bbox=road_segment["bbox"],
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            satellite_collections=["sentinel-2-l2a"],
            vector_layers=["roads", "traffic-sensors"]
        )
        
        # Analyze traffic data
        insights = await self._analyze_traffic_data(road_segment, data)
        
        # Store insights based on congestion level
        self._store_insights(insights, road_segment)
        
        return insights
    
    async def _analyze_traffic_data(
        self,
        road_segment: Dict[str, Any],
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process and analyze traffic data to generate insights."""
        # Process satellite imagery for road conditions
        satellite_features = self.image_processor.extract_features(
            data["satellite_data"]["pc"]["sentinel-2-l2a"][0]["data"]
        )
        
        # Calculate traffic metrics
        traffic_metrics = self._calculate_traffic_metrics(
            data.get("traffic_sensors", {}),
            road_segment["road_type"]
        )
        
        # Analyze road conditions
        road_conditions = self._analyze_road_conditions(
            satellite_features,
            road_segment
        )
        
        # Calculate congestion patterns
        congestion_patterns = self._analyze_congestion_patterns(
            traffic_metrics,
            road_segment["road_type"]
        )
        
        # Generate predictions
        predictions = self._generate_predictions(
            traffic_metrics,
            congestion_patterns,
            road_conditions
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            traffic_metrics,
            congestion_patterns,
            road_conditions,
            predictions
        )
        
        return {
            "road_id": road_segment["id"],
            "timestamp": datetime.now().isoformat(),
            "traffic_metrics": traffic_metrics,
            "road_conditions": road_conditions,
            "congestion_patterns": congestion_patterns,
            "predictions": predictions,
            "recommendations": recommendations
        }
    
    def _store_insights(
        self, 
        insights: Dict[str, Any], 
        road_data: Dict[str, Any]
    ) -> None:
        """Store traffic insights in appropriate memory tier based on congestion level."""
        congestion_level = insights["traffic_metrics"]["congestion_level"]
        
        # Add road segment ID to insights
        insights["road_id"] = road_data["id"]
        
        if congestion_level >= 0.8:
            # High-congestion segments go to hot memory for quick access
            self.memory_store.hot_memory.store(insights)
        elif congestion_level >= 0.6:
            # Medium-congestion segments go to warm memory
            self.memory_store.warm_memory.store(insights)
        else:
            # Low-congestion segments go to cold memory
            self.memory_store.cold_memory.store(insights)
    
    def _calculate_traffic_metrics(
        self,
        sensor_data: Dict[str, Any],
        road_type: str
    ) -> Dict[str, Any]:
        """Calculate traffic metrics from sensor data."""
        # Define speed thresholds by road type (mph)
        speed_thresholds = {
            "highway": {"min": 45, "max": 65},
            "arterial": {"min": 25, "max": 45},
            "local": {"min": 15, "max": 25}
        }
        
        # Get thresholds for road type
        thresholds = speed_thresholds.get(road_type, speed_thresholds["local"])
        
        # Simulate sensor readings if no real data
        if not sensor_data:
            avg_speed = random.uniform(thresholds["min"], thresholds["max"])
            volume = random.randint(50, 200)
        else:
            avg_speed = sensor_data.get("average_speed", random.uniform(thresholds["min"], thresholds["max"]))
            volume = sensor_data.get("volume", random.randint(50, 200))
        
        # Calculate congestion level (0-1)
        speed_ratio = (avg_speed - thresholds["min"]) / (thresholds["max"] - thresholds["min"])
        congestion_level = 1 - min(1, max(0, speed_ratio))
        
        # Calculate density (vehicles per mile)
        density = volume / max(1, avg_speed)
        
        return {
            "average_speed": round(avg_speed, 1),
            "volume": volume,
            "density": round(density, 1),
            "congestion_level": round(congestion_level, 2),
            "thresholds": thresholds
        }
    
    def _analyze_road_conditions(
        self,
        satellite_features: Dict[str, np.ndarray],
        road_segment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze road conditions from satellite imagery."""
        # Extract road surface features
        surface_quality = float(np.mean(satellite_features.get("surface_index", np.random.random())))
        
        # Calculate weather impact (simulated)
        weather_impact = random.uniform(0, 0.3)
        
        # Calculate maintenance score
        maintenance_score = max(0, min(1, surface_quality - weather_impact))
        
        return {
            "surface_quality": round(surface_quality, 2),
            "weather_impact": round(weather_impact, 2),
            "maintenance_score": round(maintenance_score, 2),
            "hazards": self._detect_road_hazards(satellite_features)
        }
    
    def _analyze_congestion_patterns(
        self,
        traffic_metrics: Dict[str, Any],
        road_type: str
    ) -> Dict[str, Any]:
        """Analyze traffic congestion patterns."""
        # Define typical peak hours
        morning_peak = ["07:00-09:00"]
        evening_peak = ["16:00-18:00"]
        
        # Calculate congestion severity
        severity = "high" if traffic_metrics["congestion_level"] >= 0.8 else \
                  "moderate" if traffic_metrics["congestion_level"] >= 0.5 else "low"
        
        # Estimate duration based on road type and current metrics
        if road_type == "highway":
            duration = random.randint(60, 180)  # minutes
        else:
            duration = random.randint(30, 90)  # minutes
        
        return {
            "peak_hours": morning_peak + evening_peak,
            "severity": severity,
            "expected_duration": duration,
            "recurring": random.choice([True, False])
        }
    
    def _detect_road_hazards(
        self,
        satellite_features: Dict[str, np.ndarray]
    ) -> List[Dict[str, Any]]:
        """Detect potential road hazards from satellite imagery."""
        hazards = []
        
        # Simulate hazard detection
        if random.random() < 0.3:  # 30% chance of detecting hazards
            hazard_types = [
                "pothole",
                "construction",
                "debris",
                "water accumulation"
            ]
            
            num_hazards = random.randint(1, 3)
            for _ in range(num_hazards):
                hazards.append({
                    "type": random.choice(hazard_types),
                    "severity": random.uniform(0.3, 0.9),
                    "location": f"mile_marker_{random.randint(1, 10)}"
                })
        
        return hazards
    
    def _generate_predictions(
        self,
        traffic_metrics: Dict[str, Any],
        congestion_patterns: Dict[str, Any],
        road_conditions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate traffic predictions."""
        # Calculate base clearance time
        base_time = congestion_patterns["expected_duration"]
        
        # Adjust for road conditions
        condition_factor = 1 + (1 - road_conditions["maintenance_score"])
        
        # Adjust for hazards
        hazard_factor = 1 + (len(road_conditions["hazards"]) * 0.2)
        
        # Calculate final clearance time
        clearance_time = int(base_time * condition_factor * hazard_factor)
        
        # Predict peak congestion times
        current_hour = datetime.now().hour
        next_peak = None
        for peak in congestion_patterns["peak_hours"]:
            start_hour = int(peak.split("-")[0].split(":")[0])
            if start_hour > current_hour:
                next_peak = peak
                break
        if not next_peak and congestion_patterns["peak_hours"]:
            next_peak = congestion_patterns["peak_hours"][0]
        
        return {
            "clearance_time": clearance_time,
            "next_peak": next_peak,
            "confidence": round(random.uniform(0.7, 0.9), 2)
        }
    
    def _generate_recommendations(
        self,
        traffic_metrics: Dict[str, Any],
        congestion_patterns: Dict[str, Any],
        road_conditions: Dict[str, Any],
        predictions: Dict[str, Any]
    ) -> List[str]:
        """Generate traffic-specific recommendations."""
        recommendations = []
        
        # Congestion-based recommendations
        if traffic_metrics["congestion_level"] >= 0.8:
            recommendations.append(
                "Severe congestion - consider alternative routes."
            )
            if predictions["clearance_time"] > 60:
                recommendations.append(
                    f"Expected to clear in {predictions['clearance_time']} minutes."
                )
        
        # Road condition recommendations
        if road_conditions["maintenance_score"] <= 0.6:
            recommendations.append(
                "Poor road conditions - exercise caution."
            )
        
        # Hazard-specific recommendations
        for hazard in road_conditions["hazards"]:
            if hazard["severity"] >= 0.7:
                recommendations.append(
                    f"Warning: {hazard['type']} reported at {hazard['location']}."
                )
        
        # Peak hour recommendations
        if predictions["next_peak"]:
            recommendations.append(
                f"Next congestion peak expected during {predictions['next_peak']}."
            )
        
        # Pattern-based recommendations
        if congestion_patterns["recurring"]:
            recommendations.append(
                "Regular congestion pattern - plan trips outside peak hours."
            )
        
        return recommendations

def simulate_road_segment() -> Dict[str, Any]:
    """Generate simulated road segment data for testing."""
    road_types = ["highway", "arterial", "local"]
    return {
        "id": str(uuid.uuid4()),
        "name": f"Road_{random.randint(1000, 9999)}",
        "road_type": random.choice(road_types),
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
        "bbox": [-122.5, 37.5, -122.0, 38.0]
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
    analyzer = TrafficAnalyzer(memory_store)
    
    # Analyze multiple road segments
    for _ in range(3):
        road_data = simulate_road_segment()
        insights = await analyzer.analyze_traffic(road_data)
        
        print(f"\nAnalysis for {road_data['name']} ({road_data['road_type']}):")
        print(f"Start: {road_data['coordinates']['start']['lat']}, {road_data['coordinates']['start']['lon']}")
        print(f"End: {road_data['coordinates']['end']['lat']}, {road_data['coordinates']['end']['lon']}")
        
        print("\nTraffic Metrics:")
        metrics = insights["traffic_metrics"]
        print(f"- Average Speed: {metrics['average_speed']} mph")
        print(f"- Volume: {metrics['volume']} vehicles/hour")
        print(f"- Density: {metrics['density']} vehicles/mile")
        print(f"- Congestion Level: {metrics['congestion_level']:.2f}")
        
        print("\nRoad Conditions:")
        conditions = insights["road_conditions"]
        print(f"- Surface Quality: {conditions['surface_quality']:.2f}")
        print(f"- Weather Impact: {conditions['weather_impact']:.2f}")
        print(f"- Maintenance Score: {conditions['maintenance_score']:.2f}")
        
        if conditions["hazards"]:
            print("\nHazards Detected:")
            for hazard in conditions["hazards"]:
                print(f"- {hazard['type'].title()} at {hazard['location']} (Severity: {hazard['severity']:.2f})")
        
        print("\nCongestion Patterns:")
        patterns = insights["congestion_patterns"]
        print(f"- Severity: {patterns['severity'].title()}")
        print(f"- Expected Duration: {patterns['expected_duration']} minutes")
        print(f"- Peak Hours: {', '.join(patterns['peak_hours'])}")
        print(f"- Recurring: {'Yes' if patterns['recurring'] else 'No'}")
        
        print("\nPredictions:")
        predictions = insights["predictions"]
        print(f"- Clearance Time: {predictions['clearance_time']} minutes")
        if predictions["next_peak"]:
            print(f"- Next Peak: {predictions['next_peak']}")
        print(f"- Confidence: {predictions['confidence']:.2f}")
        
        print("\nRecommendations:")
        for rec in insights["recommendations"]:
            print(f"- {rec}")

if __name__ == "__main__":
    asyncio.run(main()) 