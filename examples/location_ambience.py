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
from memories.data_acquisition.sources.sentinel_api import SentinelAPI
from memories.utils.processors import ImageProcessor, VectorProcessor
from memories.data_acquisition import DataManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# San Francisco Financial District (1km x 1km)
SF_BBOX = {
    'xmin': -122.4018,  # Approximately Market & Montgomery
    'ymin': 37.7914,
    'xmax': -122.3928,  # About 1km east
    'ymax': 37.7994     # About 1km north
}

def setup_directories(config):
    """Create all necessary data directories."""
    for path in config.config['data'].values():
        Path(path).mkdir(parents=True, exist_ok=True)

async def download_location_data(config: Config, bbox: Dict[str, float]) -> Dict[str, Any]:
    """Download Overture Maps and satellite data for the location.
    
    Args:
        config: Configuration object
        bbox: Bounding box dictionary
        
    Returns:
        Dictionary containing download results
    """
    # Initialize APIs with config paths
    overture_api = OvertureAPI(data_dir=config.config['data']['overture_path'])
    sentinel_api = SentinelAPI(data_dir=config.config['data']['satellite_path'])
    
    # Download Overture data
    logger.info("\n=== Downloading Overture Maps Data ===")
    overture_results = overture_api.download_data(bbox)
    
    if all(overture_results.values()):
        logger.info("\nSuccessfully downloaded all Overture themes:")
        for theme, success in overture_results.items():
            logger.info(f"- {theme}: {'✓' if success else '✗'}")
    else:
        logger.warning("\nSome Overture downloads failed:")
        for theme, success in overture_results.items():
            logger.info(f"- {theme}: {'✓' if success else '✗'}")
    
    # Download satellite data
    logger.info("\n=== Downloading Satellite Imagery ===")
    satellite_results = await sentinel_api.download_data(
        bbox=bbox,
        cloud_cover=10.0,
        bands={
            "B04": "Red",
            "B08": "NIR",
            "B11": "SWIR"
        }
    )
    
    if satellite_results.get("success"):
        logger.info("\nSuccessfully downloaded satellite data:")
        metadata = satellite_results["metadata"]
        logger.info(f"- Scene ID: {metadata['scene_id']}")
        logger.info(f"- Date: {metadata['datetime']}")
        logger.info(f"- Cloud cover: {metadata['cloud_cover']}%")
        logger.info(f"- Bands: {', '.join(metadata['bands_downloaded'])}")
    else:
        logger.warning("\nSatellite data download failed:")
        logger.error(f"- Error: {satellite_results.get('error')}")
        if 'failed_bands' in satellite_results:
            logger.warning(f"- Failed bands: {', '.join(satellite_results['failed_bands'])}")
    
    return {
        "overture": overture_results,
        "satellite": satellite_results
    }

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
            
            insights = await self._analyze_location_data(location_data, overture_data)
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

    async def _analyze_location_data(self, location, overture_data):
        """Analyze location data with both Overture and satellite data."""
        urban_features = await self._analyze_urban_features(overture_data)
        env_scores = await self._calculate_environmental_scores(urban_features)
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
            "recommendations": recommendations
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
        transportation = overture_data.get("transportation", [])
        places = overture_data.get("places", [])
        
        return {
            "building_characteristics": {
                "count": len(buildings),
                "density": len(buildings) / 100,  # per hectare
                "types": self._count_types(buildings, "building_type")
            },
            "road_characteristics": {
                "count": len(transportation),
                "density": len(transportation) / 100,
                "types": self._count_types(transportation, "road_type")
            },
            "amenity_characteristics": {
                "count": len(places),
                "density": len(places) / 100,
                "types": self._count_types(places, "place_type")
            }
        }

    async def _calculate_environmental_scores(self, urban_features):
        """Calculate environmental scores using urban features."""
        # Default scores
        scores = {
            "green_space": 5.93,  # Example value based on typical urban area
            "air_quality": 1.0,   # Example value based on typical urban area
            "water_bodies": 0.0,  # Default if no water bodies detected
            "urban_density": 0.0  # Default if no urban density data
        }
        
        # Calculate urban density from building characteristics if available
        if "building_characteristics" in urban_features and urban_features["building_characteristics"]:
            density = urban_features["building_characteristics"].get("density", 0)
            scores["urban_density"] = min(density / 100.0, 1.0)
            scores["air_quality"] = 1.0 - min(density / 100.0, 1.0)
        
        return scores

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

    def _count_types(self, features, type_field):
        """Helper method to count feature types."""
        type_counts = {}
        for feature in features:
            feature_type = feature.get(type_field, "unknown")
            type_counts[feature_type] = type_counts.get(feature_type, 0) + 1
        return type_counts

def simulate_location_data() -> Dict[str, Any]:
    """Generate location data for San Francisco Financial District."""
    return {
        "id": str(uuid.uuid4()),
        "name": "SF Financial District",
        "bbox": [SF_BBOX['xmin'], SF_BBOX['ymin'], SF_BBOX['xmax'], SF_BBOX['ymax']],
        "type": "commercial"
    }

async def main():
    """Run the location ambience analyzer example."""
    # Initialize config and create directories
    config = Config()
    setup_directories(config)
    
    # Download required data
    logger.info("=== Downloading Required Data ===")
    download_results = await download_location_data(config, SF_BBOX)
    
    # Initialize memory store with paths in examples directory
    memory_store = MemoryStore(config)
    
    # Create location analyzer
    data_manager = DataManager(cache_dir=config.config['data']['raw_path'])
    analyzer = LocationAnalyzer(data_manager, memory_store)
    
    # Analyze the Financial District location
    location_data = simulate_location_data()
    insights = await analyzer.analyze_location(location_data)
    
    # Print results
    print("\nLocation Analysis Results:")
    print("-" * 50)
    print(f"Location: {location_data['name']}")
    print(f"Location ID: {insights.get('location_id')}")
    print(f"Analysis Timestamp: {insights.get('timestamp')}")
    print()
    
    if "error" in insights:
        print(f"Error: {insights['error']}")
    else:
        print("Ambience Analysis:")
        analysis = insights["ambience_analysis"]
        print(f"Overall Ambience Score: {analysis.get('scores', 'N/A')}")
        print("\nEnvironmental Scores:")
        for key, value in analysis.get('environmental_scores', {}).items():
            print(f"- {key}: {value:.2f}")
        print("\nNoise Levels:")
        for key, value in analysis.get('noise_levels', {}).items():
            print(f"- {key}: {value:.2f}")
        print("\nUrban Features:")
        urban = analysis.get('urban_features', {})
        for category, stats in urban.items():
            print(f"\n{category.replace('_', ' ').title()}:")
            print(f"- Count: {stats.get('count', 0)}")
            print(f"- Density: {stats.get('density', 0):.2f} per hectare")
            if 'types' in stats:
                print("- Types:")
                for type_name, count in stats['types'].items():
                    print(f"  * {type_name}: {count}")
        print("\nRecommendations:")
        for rec in analysis.get('recommendations', []):
            print(f"- {rec}")

if __name__ == "__main__":
    asyncio.run(main()) 