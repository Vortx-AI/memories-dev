"""
Example demonstrating the use of the memory system for location ambience analysis.

This example shows how to:
1. Analyze location characteristics using satellite imagery and environmental data
2. Process and store location ambience data in tiered memory
3. Generate location profiles and recommendations
4. Track location changes over time
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

from memories import MemoryStore
from memories.config import Config
from memories.data_acquisition import DataManager
from memories.utils.processors import ImageProcessor, VectorProcessor

class LocationAnalyzer:
    """Analyze location characteristics and ambience using satellite imagery and local context."""
    
    def __init__(self, memory_store: MemoryStore):
        """Initialize the location analyzer.
        
        Args:
            memory_store: Memory store for caching and storing insights
        """
        self.memory_store = memory_store
        self.data_manager = DataManager(cache_dir=str(Path.home() / ".memories" / "cache"))
        self.image_processor = ImageProcessor()
        self.vector_processor = VectorProcessor()
    
    async def analyze_location(
        self,
        location: Dict[str, Any],
        time_window: int = 7
    ) -> Dict[str, Any]:
        """
        Analyze location ambience using satellite and environmental data.
        
        Args:
            location: Dictionary containing location information
                Required fields: id, name, coordinates, bbox
            time_window: Number of days to analyze (default: 7)
        
        Returns:
            Dictionary containing location analysis insights
        """
        # Get historical data for the time window
        end_date = datetime.now()
        start_date = end_date - timedelta(days=time_window)
        
        data = await self.data_manager.prepare_training_data(
            bbox=location["bbox"],
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            satellite_collections=["sentinel-2-l2a"],
            vector_layers=["buildings", "roads", "landuse"]
        )
        
        # Analyze location data
        insights = await self._analyze_location_data(location, data)
        
        # Store insights based on significance
        self._store_insights(insights, location)
        
        return insights
    
    async def _analyze_location_data(
        self,
        location: Dict[str, Any],
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process and analyze location data to generate insights."""
        # Process satellite imagery
        satellite_features = self.image_processor.extract_features(
            data["satellite_data"]["pc"]["sentinel-2-l2a"][0]["data"]
        )
        
        # Calculate environmental scores
        env_scores = self._calculate_environmental_scores(
            satellite_features,
            data.get("air_quality", {})
        )
        
        # Analyze urban features
        urban_features = self._analyze_urban_features(data)
        
        # Calculate noise levels (simulated)
        noise_levels = self._estimate_noise_levels(urban_features)
        
        # Calculate overall ambience score
        ambience_score = self._calculate_ambience_score(
            env_scores,
            urban_features,
            noise_levels
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            env_scores,
            urban_features,
            noise_levels,
            ambience_score
        )
        
        return {
            "location_id": location["id"],
            "timestamp": datetime.now().isoformat(),
            "location_analysis": {
                "environmental_scores": env_scores,
                "urban_features": urban_features,
                "noise_levels": noise_levels,
                "ambience_score": ambience_score
            },
            "recommendations": recommendations
        }
    
    def _store_insights(
        self, 
        insights: Dict[str, Any], 
        location_data: Dict[str, Any]
    ) -> None:
        """Store location insights in appropriate memory tier based on ambience score."""
        ambience_score = insights["location_analysis"]["ambience_score"]
        
        # Ensure location_id is present in insights
        if "location_id" not in insights:
            insights["location_id"] = location_data["id"]
        
        # Add timestamp if not present
        if "timestamp" not in insights:
            insights["timestamp"] = datetime.now().isoformat()
        
        if ambience_score >= 0.8:
            # High-ambience locations go to hot memory for quick access
            self.memory_store.hot_memory.store(insights)
        elif ambience_score >= 0.6:
            # Medium-ambience locations go to warm memory
            self.memory_store.warm_memory.store(insights)
        else:
            # Low-ambience locations go to cold memory
            self.memory_store.cold_memory.store(insights)
    
    def _calculate_environmental_scores(
        self,
        satellite_features: Dict[str, np.ndarray],
        air_quality: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate environmental quality scores."""
        # Ensure all scores are normalized between 0 and 1
        greenery = float(np.clip(np.mean(satellite_features["greenery_index"]), 0, 1))
        water_bodies = float(np.clip(np.mean(satellite_features.get("water_index", 0)), 0, 1))
        air_quality_score = self._normalize_air_quality(
            air_quality.get("aqi", random.uniform(50, 150))
        )
        urban_density = float(np.clip(np.mean(satellite_features.get("built_up_index", 0)), 0, 1))
        
        return {
            "greenery": greenery,
            "water_bodies": water_bodies,
            "air_quality": air_quality_score,
            "urban_density": urban_density
        }
    
    def _analyze_urban_features(
        self,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze urban features from vector data."""
        features = {
            "parks": [],
            "cafes": [],
            "restaurants": [],
            "cultural_venues": []
        }
        
        if "vector_data" in data and "osm" in data["vector_data"]:
            for feature in data["vector_data"]["osm"].get("amenities", []):
                if "properties" in feature:
                    feature_type = feature["properties"].get("type", "")
                    if feature_type in features:
                        features[feature_type].append({
                            "name": feature["properties"].get("name", "Unknown"),
                            "distance": round(random.uniform(0.1, 2.0), 2),
                            "rating": round(random.uniform(3.0, 5.0), 1)
                        })
        
        return features
    
    def _estimate_noise_levels(
        self,
        urban_features: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Estimate noise levels based on urban features."""
        # Calculate base noise level from number of venues
        venue_count = sum(len(venues) for venues in urban_features.values())
        base_noise = min(70, 40 + (venue_count * 2))
        
        # Add time-based variation
        hour = datetime.now().hour
        time_factor = 1.0
        if 22 <= hour or hour <= 5:
            time_factor = 0.5
        elif 17 <= hour <= 21:
            time_factor = 1.2
        
        return {
            "average_db": round(base_noise * time_factor, 1),
            "peak_hours": ["17:00-21:00"],
            "quiet_hours": ["23:00-05:00"]
        }
    
    def _calculate_ambience_score(
        self,
        env_scores: Dict[str, float],
        urban_features: Dict[str, List[Dict[str, Any]]],
        noise_levels: Dict[str, Any]
    ) -> float:
        """Calculate overall ambience score."""
        # Environmental factors (40%)
        env_score = (
            0.4 * env_scores["greenery"] +
            0.3 * env_scores["air_quality"] +
            0.3 * (1 - env_scores["urban_density"])
        )
        
        # Urban amenities (40%)
        amenities_score = min(1.0, sum(len(venues) for venues in urban_features.values()) / 20)
        
        # Noise factor (20%)
        noise_score = max(0, 1 - (noise_levels["average_db"] - 40) / 40)
        
        # Combine scores
        total_score = (
            0.4 * env_score +
            0.4 * amenities_score +
            0.2 * noise_score
        )
        
        return round(total_score, 2)
    
    def _normalize_air_quality(self, aqi: float) -> float:
        """Normalize AQI to a 0-1 scale."""
        # AQI scale: 0-50 (Good), 51-100 (Moderate), 101-150 (Unhealthy for Sensitive Groups)
        return max(0, min(1, (150 - aqi) / 150))
    
    def _generate_recommendations(
        self,
        env_scores: Dict[str, float],
        urban_features: Dict[str, List[Dict[str, Any]]],
        noise_levels: Dict[str, Any],
        ambience_score: float
    ) -> List[str]:
        """Generate location-specific recommendations."""
        recommendations = []
        
        # Environmental recommendations
        if env_scores["greenery"] >= 0.7:
            recommendations.append(
                "Excellent green spaces - ideal for outdoor activities and recreation."
            )
        if env_scores["air_quality"] <= 0.5:
            recommendations.append(
                "Consider air quality monitoring and indoor air purification."
            )
        
        # Urban features recommendations
        venue_count = sum(len(venues) for venues in urban_features.values())
        if venue_count >= 10:
            recommendations.append(
                "Rich in cultural venues and dining options - vibrant urban lifestyle."
            )
        elif venue_count <= 3:
            recommendations.append(
                "Limited urban amenities - may require travel for entertainment."
            )
        
        # Noise level recommendations
        if noise_levels["average_db"] >= 65:
            recommendations.append(
                "High ambient noise levels - consider soundproofing measures."
            )
        elif noise_levels["average_db"] <= 45:
            recommendations.append(
                "Exceptionally quiet environment - perfect for relaxation."
            )
        
        # Overall ambience recommendations
        if ambience_score >= 0.8:
            recommendations.append(
                "Premium location with excellent balance of nature and urban amenities."
            )
        elif ambience_score <= 0.4:
            recommendations.append(
                "Consider lifestyle preferences - location may have limitations."
            )
        
        return recommendations

def simulate_location_data() -> Dict[str, Any]:
    """Generate simulated location data for testing."""
    return {
        "id": str(uuid.uuid4()),
        "name": f"Location_{random.randint(1000, 9999)}",
        "coordinates": {
            "lat": round(random.uniform(37.7, 37.8), 4),
            "lon": round(random.uniform(-122.5, -122.4), 4)
        },
        "bbox": [-122.5, 37.5, -122.0, 38.0]
    }

async def main():
    """Run the location ambience analyzer example."""
    # Initialize memory store
    config = Config(
        storage_path="./location_data",
        hot_memory_size=50,
        warm_memory_size=200,
        cold_memory_size=1000
    )
    memory_store = MemoryStore(config)
    
    # Create location analyzer
    analyzer = LocationAnalyzer(memory_store)
    
    # Analyze multiple locations
    for _ in range(3):
        location_data = simulate_location_data()
        insights = await analyzer.analyze_location(location_data)
        
        print(f"\nAnalysis for {location_data['name']}:")
        print(f"Coordinates: {location_data['coordinates']['lat']}, {location_data['coordinates']['lon']}")
        
        print("\nEnvironmental Scores:")
        for metric, score in insights["location_analysis"]["environmental_scores"].items():
            print(f"- {metric.replace('_', ' ').title()}: {score:.2f}")
        
        print("\nUrban Features:")
        for feature_type, venues in insights["location_analysis"]["urban_features"].items():
            if venues:
                print(f"- {feature_type.replace('_', ' ').title()}: {len(venues)} venues")
                for venue in venues[:2]:  # Show top 2 venues
                    print(f"  * {venue['name']} ({venue['distance']}km, {venue['rating']}★)")
        
        print("\nNoise Levels:")
        print(f"- Average: {insights['location_analysis']['noise_levels']['average_db']} dB")
        print(f"- Peak Hours: {', '.join(insights['location_analysis']['noise_levels']['peak_hours'])}")
        print(f"- Quiet Hours: {', '.join(insights['location_analysis']['noise_levels']['quiet_hours'])}")
        
        print(f"\nOverall Ambience Score: {insights['location_analysis']['ambience_score']:.2f}")
        
        print("\nRecommendations:")
        for rec in insights["recommendations"]:
            print(f"- {rec}")

if __name__ == "__main__":
    asyncio.run(main()) 