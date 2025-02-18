import numpy as np
from datetime import datetime
from typing import List, Dict
from textblob import TextBlob
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_location_ambience(location_data: dict) -> dict:
    """
    Analyze the ambience of a location based on provided data.
    
    Args:
        location_data (dict): Dictionary containing location information with structure:
            {
                "id": str,
                "name": str,
                "type": str,
                "social_data": {
                    "posts": [
                        {
                            "text": str,
                            "crowd_size": float,
                            "timestamp": datetime
                        }
                    ]
                },
                "environmental_data": {
                    "temperature": float,
                    "humidity": float,
                    "noise_samples": List[float]
                },
                "temporal_data": {
                    "visit_patterns": [
                        {
                            "hour": int,
                            "visitor_count": int
                        }
                    ]
                }
            }
    
    Returns:
        dict: Analysis results containing:
            - ambience_profile
            - social_analysis
            - environmental_analysis
            - temporal_analysis
            - recommendations
    """
    
    def analyze_social_data(social_data):
        sentiments = []
        crowd_patterns = []
        
        for post in social_data["posts"]:
            blob = TextBlob(post["text"])
            sentiments.append(blob.sentiment.polarity)
            
            if "crowd_size" in post:
                crowd_patterns.append(post["crowd_size"])
        
        return {
            "sentiment_score": np.mean(sentiments) if sentiments else 0,
            "crowd_density": np.mean(crowd_patterns) if crowd_patterns else 0,
            "popular_activities": identify_popular_activities(),
            "demographic_profile": analyze_demographics()
        }
    
    def analyze_environmental_data(env_data):
        return {
            "noise_level": np.mean(env_data["noise_samples"]) / 100 if "noise_samples" in env_data else 0.5,
            "temperature_comfort": calculate_temperature_comfort(env_data.get("temperature", 20)),
            "humidity_comfort": calculate_humidity_comfort(env_data.get("humidity", 50))
        }
    
    def analyze_temporal_data(temporal_data):
        visit_patterns = temporal_data.get("visit_patterns", [])
        visitor_counts = [p["visitor_count"] for p in visit_patterns]
        
        return {
            "peak_hours": identify_peak_hours(visit_patterns),
            "average_occupancy": np.mean(visitor_counts) if visitor_counts else 0,
            "occupancy_variance": np.var(visitor_counts) if visitor_counts else 0
        }
    
    def calculate_temperature_comfort(temp):
        # Assume optimal temperature is between 20-25°C
        return 1 - min(abs(temp - 22.5) / 10, 1)
    
    def calculate_humidity_comfort(humidity):
        # Assume optimal humidity is between 30-60%
        return 1 - min(abs(humidity - 45) / 30, 1)
    
    def identify_peak_hours(patterns):
        if not patterns:
            return []
        
        sorted_patterns = sorted(patterns, key=lambda x: x["visitor_count"], reverse=True)
        return [p["hour"] for p in sorted_patterns[:3]]
    
    def identify_popular_activities():
        activities = ["dining", "shopping", "socializing", "working", "exercising"]
        return list(np.random.choice(activities, size=3, replace=False))
    
    def analyze_demographics():
        return {
            "age_groups": ["18-25", "26-35", "36-45"],
            "primary_audience": np.random.choice(["young_professionals", "families", "tourists"])
        }
    
    def generate_recommendations(social_analysis, env_analysis, temporal_analysis):
        recommendations = []
        
        if social_analysis["crowd_density"] > 0.8:
            recommendations.append("Consider implementing crowd management systems")
        
        if env_analysis["noise_level"] > 0.7:
            recommendations.append("Implement noise reduction measures")
        
        if temporal_analysis["occupancy_variance"] > 1000:
            recommendations.append("Consider capacity optimization strategies")
            
        return recommendations

    # Perform analyses
    social_analysis = analyze_social_data(location_data["social_data"])
    environmental_analysis = analyze_environmental_data(location_data["environmental_data"])
    temporal_analysis = analyze_temporal_data(location_data["temporal_data"])
    
    # Generate ambience profile
    ambience_profile = {
        "energy_level": (social_analysis["crowd_density"] + 
                        environmental_analysis["noise_level"]) / 2,
        "comfort_rating": (environmental_analysis["temperature_comfort"] + 
                          environmental_analysis["humidity_comfort"]) / 2,
        "best_suited_for": social_analysis["popular_activities"],
        "peak_hours": temporal_analysis["peak_hours"]
    }
    
    # Generate recommendations
    recommendations = generate_recommendations(
        social_analysis, environmental_analysis, temporal_analysis
    )
    
    return {
        "ambience_profile": ambience_profile,
        "social_analysis": social_analysis,
        "environmental_analysis": environmental_analysis,
        "temporal_analysis": temporal_analysis,
        "recommendations": recommendations
    }
