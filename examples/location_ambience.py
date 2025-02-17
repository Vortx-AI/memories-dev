#!/usr/bin/env python3
"""
Location Ambience Analyzer Example
--------------------------------
This example demonstrates using the Memories-Dev framework to analyze
location characteristics using Overture Maps and Planetary Computer data.
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
from dotenv import load_dotenv
from memories import MemoryStore, Config
from memories.agents import BaseAgent
from memories.utils.text import TextProcessor
from memories.data_acquisition.sources.overture_api import OvertureAPI
from memories.data_acquisition.sources.planetary_compute import PlanetaryCompute
from memories.utils.processors import ImageProcessor, VectorProcessor
from memories.data_acquisition import DataManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class LocationAnalyzer:
    """Analyzer for location ambience and environmental characteristics."""
    
    def __init__(self, data_manager, memory_store):
        """Initialize the location analyzer.
        
        Args:
            data_manager: Data manager for data acquisition
            memory_store: Memory store for persisting insights
        """
        self.data_manager = data_manager
        self.memory_store = memory_store
        self.overture_api = OvertureAPI()
        self.pc_api = PlanetaryCompute()
        self.text_processor = TextProcessor()
        self.image_processor = ImageProcessor()

    async def analyze_location(self, location_data):
        """Analyze location ambience and environmental factors."""
        try:
            if location_data is None:
                return {
                    "error": "Missing bbox data",
                    "location_id": "unknown",
                    "timestamp": None
                }
            
            if not isinstance(location_data, dict) or 'bbox' not in location_data:
                raise ValueError("Missing bbox data")
            
            # Get Overture data for urban features
            overture_data = await self.overture_api.search(location_data['bbox'])
            
            # Get satellite data from Planetary Computer
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)  # Last 30 days
            satellite_data = await self.pc_api.search_and_download(
                bbox=location_data['bbox'],
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
                collections=["sentinel-2-l2a"],
                cloud_cover=20.0
            )
            
            insights = await self._analyze_location_data(location_data, overture_data, satellite_data)
            return {
                "location_id": location_data.get("id", "unknown"),
                "timestamp": datetime.now().isoformat(),
                "ambience_analysis": insights
            }
        except Exception as e:
            logger.error(f"Error analyzing location: {str(e)}")
            return {
                "error": str(e), 
                "location_id": location_data.get("id", "unknown"), 
                "timestamp": None
            }

    async def _analyze_location_data(self, location, overture_data, satellite_data):
        """Analyze location data with both Overture and satellite data."""
        urban_features = await self._analyze_urban_features(overture_data)
        env_scores = await self._calculate_environmental_scores(urban_features, satellite_data)
        noise_levels = await self._estimate_noise_levels(urban_features)
        
        ambience_score = await self._calculate_ambience_score(env_scores, urban_features, noise_levels)
        recommendations = await self._generate_recommendations(
            env_scores=env_scores, 
            urban_features=urban_features, 
            noise_levels=noise_levels,
            ambience_score=ambience_score
        )
        
        return {
            "scores": ambience_score,
            "urban_features": urban_features,
            "environmental_scores": env_scores,
            "noise_levels": noise_levels,
            "recommendations": recommendations,
            "satellite_metadata": satellite_data.get("sentinel-2-l2a", {}).get("metadata", {}) if satellite_data else {}
        }

    async def _analyze_urban_features(self, overture_data):
        """Analyze urban features from Overture data."""
        if not overture_data:
            return {
                "building_characteristics": {},
                "road_characteristics": {},
                "amenity_characteristics": {}
            }
            
        buildings = overture_data.get("buildings", [])
        roads = overture_data.get("roads", [])
        amenities = overture_data.get("amenities", [])
        
        return {
            "building_characteristics": {
                "count": len(buildings),
                "density": len(buildings) / 100,  # per hectare
                "types": self._count_types(buildings)
            },
            "road_characteristics": {
                "count": len(roads),
                "density": len(roads) / 100,
                "types": self._count_types(roads)
            },
            "amenity_characteristics": {
                "count": len(amenities),
                "density": len(amenities) / 100,
                "types": self._count_types(amenities)
            }
        }

    async def _calculate_environmental_scores(self, urban_features, satellite_data=None):
        """Calculate environmental scores using urban features and satellite data."""
        base_scores = {
            "green_space": 0.0,
            "air_quality": 0.0,
            "water_bodies": 0.0,
            "urban_density": 0.0
        }
        
        if satellite_data and "sentinel-2-l2a" in satellite_data:
            ndvi_data = satellite_data["sentinel-2-l2a"]["data"]
            if len(ndvi_data) >= 4:  # Ensure we have enough bands
                red_band = ndvi_data[2]  # B04
                nir_band = ndvi_data[3]  # B08
                ndvi = (nir_band - red_band) / (nir_band + red_band)
                base_scores["green_space"] = float(np.mean(ndvi))
                base_scores["air_quality"] = 1.0 - min(urban_features["building_characteristics"]["density"] / 10.0, 1.0)
        
        # Calculate urban density score
        total_density = (
            urban_features["building_characteristics"]["density"] +
            urban_features["road_characteristics"]["density"] +
            urban_features["amenity_characteristics"]["density"]
        )
        base_scores["urban_density"] = min(total_density / 30.0, 1.0)
        
        return base_scores

    async def _estimate_noise_levels(self, urban_features):
        """Estimate noise levels based on urban features."""
        if not urban_features:
            return {"average": 0.0, "peak": 0.0, "variability": 0.0}
            
        building_density = urban_features["building_characteristics"]["density"]
        road_density = urban_features["road_characteristics"]["density"]
        amenity_density = urban_features["amenity_characteristics"]["density"]
        
        # Calculate noise metrics
        average_noise = (building_density * 0.3 + road_density * 0.5 + amenity_density * 0.2)
        peak_noise = max(building_density, road_density, amenity_density)
        variability = np.std([building_density, road_density, amenity_density])
        
        return {
            "average": float(average_noise),
            "peak": float(peak_noise),
            "variability": float(variability)
        }

    async def _calculate_ambience_score(self, env_scores, urban_features, noise_levels):
        """Calculate overall ambience score."""
        # Weight the components
        env_weight = 0.4
        urban_weight = 0.3
        noise_weight = 0.3
        
        # Calculate component scores
        env_score = np.mean([
            env_scores["green_space"],
            env_scores["air_quality"],
            1.0 - env_scores["urban_density"]
        ])
        
        urban_score = min(
            (urban_features["amenity_characteristics"]["density"] * 0.6 +
             urban_features["building_characteristics"]["density"] * 0.4) / 10.0,
            1.0
        )
        
        noise_score = 1.0 - (
            noise_levels["average"] * 0.5 +
            noise_levels["peak"] * 0.3 +
            noise_levels["variability"] * 0.2
        )
        
        # Combine scores
        return float(
            env_score * env_weight +
            urban_score * urban_weight +
            noise_score * noise_weight
        )

    async def _generate_recommendations(self, env_scores, urban_features, noise_levels, ambience_score):
        """Generate recommendations based on analysis."""
        recommendations = []
        
        # Environmental recommendations
        if env_scores["green_space"] < 0.3:
            recommendations.append("Consider increasing green spaces and vegetation")
        if env_scores["air_quality"] < 0.5:
            recommendations.append("Implement measures to improve air quality")
        if env_scores["urban_density"] > 0.8:
            recommendations.append("Area may benefit from urban density optimization")
            
        # Urban feature recommendations
        if urban_features["amenity_characteristics"]["density"] < 0.2:
            recommendations.append("Consider adding more community amenities")
        if urban_features["building_characteristics"]["density"] > 0.8:
            recommendations.append("Area may be over-developed, consider adding open spaces")
            
        # Noise-related recommendations
        if noise_levels["average"] > 0.7:
            recommendations.append("Implement noise reduction measures")
        if noise_levels["peak"] > 0.9:
            recommendations.append("Address sources of peak noise levels")
            
        return recommendations

    def _count_types(self, features):
        """Helper method to count feature types."""
        type_counts = {}
        for feature in features:
            feature_type = feature.get("type", "unknown")
            type_counts[feature_type] = type_counts.get(feature_type, 0) + 1
        return type_counts

def simulate_location_data() -> Dict[str, Any]:
    """Generate random location data for testing."""
    return {
        "id": str(uuid.uuid4()),
        "name": "Test Location",
        "bbox": [-122.5, 37.5, -122.0, 38.0],  # San Francisco area
        "type": "residential"
    }

async def main():
    """Run the location ambience analyzer example."""
    # Initialize memory store
    config = Config(
        storage_path="./examples/data/location_data",
        hot_memory_size=50,
        warm_memory_size=200,
        cold_memory_size=1000
    )
    memory_store = MemoryStore(config)
    
    # Create location analyzer
    data_manager = DataManager()
    analyzer = LocationAnalyzer(data_manager, memory_store)
    
    # Analyze a simulated location
    location_data = simulate_location_data()
    insights = await analyzer.analyze_location(location_data)
    
    # Print results
    print("\nLocation Analysis Results:")
    print("-" * 50)
    print(f"Location ID: {insights['location_id']}")
    print(f"Analysis Timestamp: {insights['timestamp']}")
    
    print("\nAmbience Analysis:")
    analysis = insights["ambience_analysis"]
    
    print("\nEnvironmental Scores:")
    for key, value in analysis["environmental_scores"].items():
        print(f"- {key.replace('_', ' ').title()}: {value:.2f}")
    
    print("\nNoise Levels:")
    for key, value in analysis["noise_levels"].items():
        if key != "sources":
            print(f"- {key.title()}: {value:.2f}")
    
    print(f"\nOverall Ambience Score: {analysis['scores']:.2f}")
    
    print("\nRecommendations:")
    for rec in analysis["recommendations"]:
        print(f"- {rec}")

if __name__ == "__main__":
    asyncio.run(main()) 