#!/usr/bin/env python3
"""
Location Ambience Analyzer Example
--------------------------------
This example demonstrates how to use the Memories-Dev framework to analyze
the ambience and characteristics of different locations using multi-modal data.
"""

import os
import logging
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from textblob import TextBlob
from dotenv import load_dotenv
from memories import MemoryStore, Config
from memories.core import HotMemory, WarmMemory, ColdMemory
from memories.agents import BaseAgent
from memories.utils.text import TextProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class AmbienceAnalyzerAgent(BaseAgent):
    """Agent specialized in location ambience analysis."""
    
    def __init__(self, memory_store: MemoryStore):
        super().__init__(name="ambience_analyzer_agent")
        self.memory_store = memory_store
        self.text_processor = TextProcessor()
        
    def analyze_location(self, location_data):
        """Analyze location data and generate ambience insights."""
        # Process various aspects of the location
        social_analysis = self._analyze_social_data(location_data["social_data"])
        environmental_analysis = self._analyze_environmental_data(location_data["environmental_data"])
        temporal_analysis = self._analyze_temporal_patterns(location_data["temporal_data"])
        
        # Combine analyses
        insights = {
            "social_analysis": social_analysis,
            "environmental_analysis": environmental_analysis,
            "temporal_analysis": temporal_analysis,
            "ambience_profile": self._generate_ambience_profile(
                social_analysis, environmental_analysis, temporal_analysis
            ),
            "recommendations": self._generate_recommendations(
                social_analysis, environmental_analysis, temporal_analysis
            )
        }
        
        # Store insights in memory
        self._store_insights(insights, location_data)
        
        return insights
    
    def _analyze_social_data(self, social_data):
        """Analyze social aspects of the location."""
        # Process social media mentions, check-ins, and reviews
        sentiments = []
        crowd_patterns = []
        
        for post in social_data["posts"]:
            blob = TextBlob(post["text"])
            sentiments.append(blob.sentiment.polarity)
            
            if "crowd_size" in post:
                crowd_patterns.append(post["crowd_size"])
        
        return {
            "sentiment_score": np.mean(sentiments),
            "crowd_density": np.mean(crowd_patterns) if crowd_patterns else 0,
            "popular_activities": self._identify_popular_activities(social_data),
            "demographic_profile": self._analyze_demographics(social_data)
        }
    
    def _analyze_environmental_data(self, env_data):
        """Analyze environmental aspects of the location."""
        return {
            "noise_level": self._calculate_noise_level(env_data),
            "lighting": self._analyze_lighting(env_data),
            "weather_impact": self._analyze_weather_impact(env_data),
            "spatial_metrics": self._analyze_spatial_characteristics(env_data)
        }
    
    def _analyze_temporal_patterns(self, temporal_data):
        """Analyze temporal patterns of the location."""
        return {
            "peak_hours": self._identify_peak_hours(temporal_data),
            "seasonal_variations": self._analyze_seasonal_variations(temporal_data),
            "event_impact": self._analyze_event_impact(temporal_data)
        }
    
    def _generate_ambience_profile(self, social, environmental, temporal):
        """Generate comprehensive ambience profile."""
        # Calculate various ambience scores
        energy_score = self._calculate_energy_score(social, environmental)
        comfort_score = self._calculate_comfort_score(environmental)
        accessibility_score = self._calculate_accessibility_score(social, temporal)
        
        return {
            "energy_level": energy_score,
            "comfort_rating": comfort_score,
            "accessibility": accessibility_score,
            "best_suited_for": self._determine_best_uses(energy_score, comfort_score),
            "ambience_tags": self._generate_ambience_tags(social, environmental)
        }
    
    def _generate_recommendations(self, social, environmental, temporal):
        """Generate location-specific recommendations."""
        recommendations = []
        
        # Crowd management recommendations
        if social["crowd_density"] > 0.8:
            recommendations.append("Consider implementing crowd management systems")
        
        # Environmental recommendations
        if environmental["noise_level"] > 0.7:
            recommendations.append("Implement noise reduction measures")
        
        # Temporal recommendations
        if len(temporal["peak_hours"]) > 3:
            recommendations.append("Consider extended operating hours")
        
        return recommendations
    
    def _store_insights(self, insights, location_data):
        """Store insights in appropriate memory layers."""
        # Store in hot memory if location has exceptional characteristics
        if (insights["ambience_profile"]["energy_level"] > 0.8 or 
            insights["ambience_profile"]["comfort_rating"] > 0.8):
            self.memory_store.hot_memory.store({
                "timestamp": datetime.now().isoformat(),
                "type": "exceptional_location",
                "location_id": location_data["id"],
                "insights": insights
            })
        else:
            self.memory_store.warm_memory.store({
                "timestamp": datetime.now().isoformat(),
                "type": "location_analysis",
                "location_id": location_data["id"],
                "insights": insights
            })
    
    def _identify_popular_activities(self, data):
        """Identify popular activities at the location."""
        activities = ["dining", "shopping", "socializing", "working", "exercising"]
        return [
            {"activity": activity, "popularity": np.random.uniform(0.3, 1.0)}
            for activity in np.random.choice(activities, size=3, replace=False)
        ]
    
    def _analyze_demographics(self, data):
        """Analyze demographic patterns."""
        return {
            "age_groups": ["18-25", "26-35", "36-45"],
            "primary_audience": np.random.choice(["young_professionals", "families", "tourists"]),
            "diversity_index": np.random.uniform(0.5, 1.0)
        }
    
    def _calculate_noise_level(self, data):
        """Calculate average noise level."""
        return np.random.uniform(0, 1)
    
    def _analyze_lighting(self, data):
        """Analyze lighting conditions."""
        return {
            "natural_light": np.random.uniform(0, 1),
            "artificial_light": np.random.uniform(0, 1),
            "overall_quality": np.random.uniform(0, 1)
        }
    
    def _analyze_weather_impact(self, data):
        """Analyze weather impact on location."""
        return {
            "weather_dependency": np.random.uniform(0, 1),
            "indoor_outdoor_ratio": np.random.uniform(0, 1)
        }
    
    def _analyze_spatial_characteristics(self, data):
        """Analyze spatial characteristics."""
        return {
            "openness": np.random.uniform(0, 1),
            "layout_efficiency": np.random.uniform(0, 1),
            "capacity_utilization": np.random.uniform(0, 1)
        }
    
    def _identify_peak_hours(self, data):
        """Identify location peak hours."""
        return [
            {"time": "12:00-14:00", "intensity": np.random.uniform(0.7, 1.0)},
            {"time": "17:00-19:00", "intensity": np.random.uniform(0.6, 0.9)}
        ]
    
    def _analyze_seasonal_variations(self, data):
        """Analyze seasonal variations."""
        seasons = ["spring", "summer", "fall", "winter"]
        return {season: np.random.uniform(0.3, 1.0) for season in seasons}
    
    def _analyze_event_impact(self, data):
        """Analyze impact of events on location."""
        return {
            "event_frequency": np.random.uniform(0, 1),
            "average_impact": np.random.uniform(0, 1)
        }
    
    def _calculate_energy_score(self, social, environmental):
        """Calculate location energy score."""
        return np.random.uniform(0, 1)
    
    def _calculate_comfort_score(self, environmental):
        """Calculate location comfort score."""
        return np.random.uniform(0, 1)
    
    def _calculate_accessibility_score(self, social, temporal):
        """Calculate location accessibility score."""
        return np.random.uniform(0, 1)
    
    def _determine_best_uses(self, energy_score, comfort_score):
        """Determine best uses for the location."""
        uses = []
        if energy_score > 0.7:
            uses.extend(["social_gatherings", "events"])
        if comfort_score > 0.7:
            uses.extend(["relaxation", "work_space"])
        return uses if uses else ["general_purpose"]
    
    def _generate_ambience_tags(self, social, environmental):
        """Generate descriptive ambience tags."""
        possible_tags = [
            "cozy", "energetic", "peaceful", "modern", "traditional",
            "spacious", "intimate", "bright", "calm", "vibrant"
        ]
        return np.random.choice(possible_tags, size=4, replace=False).tolist()

def simulate_location_data():
    """Generate simulated location data for demonstration."""
    return {
        "id": f"LOC-{np.random.randint(1000, 9999)}",
        "name": f"Location {np.random.randint(1, 100)}",
        "type": np.random.choice([
            "cafe", "park", "office_space", "shopping_center", "cultural_venue"
        ]),
        "social_data": {
            "posts": [
                {
                    "text": "Great atmosphere and perfect for working!",
                    "crowd_size": np.random.uniform(0, 1),
                    "timestamp": datetime.now() - timedelta(hours=np.random.randint(1, 48))
                }
                for _ in range(5)
            ]
        },
        "environmental_data": {
            "temperature": np.random.uniform(18, 25),
            "humidity": np.random.uniform(30, 70),
            "noise_samples": [np.random.uniform(30, 70) for _ in range(5)]
        },
        "temporal_data": {
            "visit_patterns": [
                {
                    "hour": hour,
                    "visitor_count": np.random.randint(10, 100)
                }
                for hour in range(9, 22)
            ]
        }
    }

def main():
    """Main execution function."""
    # Initialize memory system
    config = Config(
        storage_path="./location_data",
        hot_memory_size=50,
        warm_memory_size=500,
        cold_memory_size=5000
    )
    
    memory_store = MemoryStore(config)
    
    # Initialize agent
    agent = AmbienceAnalyzerAgent(memory_store)
    
    # Analyze multiple locations
    for _ in range(3):
        # Generate sample location data
        location_data = simulate_location_data()
        
        logger.info(f"\nAnalyzing location: {location_data['name']}")
        logger.info(f"Type: {location_data['type']}")
        
        # Perform analysis
        insights = agent.analyze_location(location_data)
        
        # Log results
        logger.info("\nAmbience Profile:")
        logger.info(f"Energy Level: {insights['ambience_profile']['energy_level']:.2f}")
        logger.info(f"Comfort Rating: {insights['ambience_profile']['comfort_rating']:.2f}")
        logger.info(f"Best Suited For: {', '.join(insights['ambience_profile']['best_suited_for'])}")
        
        logger.info("\nAmbience Tags:")
        logger.info(f"Tags: {', '.join(insights['ambience_profile']['ambience_tags'])}")
        
        logger.info("\nRecommendations:")
        for rec in insights['recommendations']:
            logger.info(f"- {rec}")
        logger.info("-" * 50)
    
    # Retrieve exceptional locations
    hot_memories = memory_store.hot_memory.retrieve_all()
    logger.info(f"\nExceptional locations found: {len(hot_memories)}")
    
    # Clean up
    memory_store.clear()

if __name__ == "__main__":
    main() 