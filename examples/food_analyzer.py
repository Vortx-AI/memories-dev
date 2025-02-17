#!/usr/bin/env python3
"""
Food and Restaurant Analysis Example
----------------------------------
This example demonstrates how to use the Memories-Dev framework to analyze
restaurant reviews, food trends, and generate insights about dining establishments.
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

class FoodAnalyzerAgent(BaseAgent):
    """Agent specialized in food and restaurant analysis."""
    
    def __init__(self, memory_store: MemoryStore):
        super().__init__(name="food_analyzer_agent")
        self.memory_store = memory_store
        self.text_processor = TextProcessor()
        
    def analyze_restaurant(self, restaurant_data):
        """Analyze restaurant data and generate insights."""
        # Process reviews and data
        review_analysis = self._analyze_reviews(restaurant_data["reviews"])
        trend_analysis = self._analyze_trends(restaurant_data)
        cuisine_analysis = self._analyze_cuisine(restaurant_data)
        
        # Combine analyses
        insights = {
            "review_analysis": review_analysis,
            "trend_analysis": trend_analysis,
            "cuisine_analysis": cuisine_analysis,
            "recommendations": self._generate_recommendations(
                review_analysis, trend_analysis, cuisine_analysis
            )
        }
        
        # Store insights in memory
        self._store_insights(insights, restaurant_data)
        
        return insights
    
    def _analyze_reviews(self, reviews):
        """Analyze customer reviews."""
        sentiments = []
        topics = {"food": [], "service": [], "ambiance": [], "price": []}
        
        for review in reviews:
            # Analyze sentiment
            blob = TextBlob(review["text"])
            sentiment = blob.sentiment.polarity
            sentiments.append(sentiment)
            
            # Categorize review aspects
            lower_text = review["text"].lower()
            if any(word in lower_text for word in ["food", "dish", "taste", "flavor"]):
                topics["food"].append(sentiment)
            if any(word in lower_text for word in ["service", "staff", "waiter"]):
                topics["service"].append(sentiment)
            if any(word in lower_text for word in ["ambiance", "atmosphere", "decor"]):
                topics["ambiance"].append(sentiment)
            if any(word in lower_text for word in ["price", "value", "expensive"]):
                topics["price"].append(sentiment)
        
        return {
            "overall_sentiment": np.mean(sentiments),
            "sentiment_std": np.std(sentiments),
            "topic_sentiments": {
                topic: np.mean(scores) if scores else 0
                for topic, scores in topics.items()
            }
        }
    
    def _analyze_trends(self, data):
        """Analyze restaurant trends."""
        return {
            "popularity_trend": self._calculate_popularity_trend(data),
            "peak_hours": self._identify_peak_hours(data),
            "seasonal_patterns": self._analyze_seasonal_patterns(data)
        }
    
    def _analyze_cuisine(self, data):
        """Analyze cuisine-specific metrics."""
        return {
            "cuisine_type": data["cuisine_type"],
            "signature_dishes": self._identify_signature_dishes(data),
            "price_category": self._analyze_price_category(data),
            "dietary_options": self._analyze_dietary_options(data)
        }
    
    def _generate_recommendations(self, review_analysis, trend_analysis, cuisine_analysis):
        """Generate restaurant-specific recommendations."""
        recommendations = []
        
        # Review-based recommendations
        if review_analysis["topic_sentiments"]["service"] < 0:
            recommendations.append("Consider staff training to improve service quality")
        
        # Trend-based recommendations
        if trend_analysis["popularity_trend"]["direction"] == "down":
            recommendations.append("Review marketing strategy to boost popularity")
        
        # Cuisine-based recommendations
        if len(cuisine_analysis["dietary_options"]) < 3:
            recommendations.append("Consider adding more dietary options to menu")
        
        return recommendations
    
    def _store_insights(self, insights, restaurant_data):
        """Store insights in appropriate memory layers."""
        # Store in hot memory if review sentiment is very positive or negative
        if abs(insights["review_analysis"]["overall_sentiment"]) > 0.7:
            self.memory_store.hot_memory.store({
                "timestamp": datetime.now().isoformat(),
                "type": "significant_sentiment",
                "restaurant_id": restaurant_data["id"],
                "insights": insights
            })
        else:
            self.memory_store.warm_memory.store({
                "timestamp": datetime.now().isoformat(),
                "type": "restaurant_analysis",
                "restaurant_id": restaurant_data["id"],
                "insights": insights
            })
    
    def _calculate_popularity_trend(self, data):
        """Calculate restaurant popularity trend."""
        return {
            "direction": np.random.choice(["up", "down", "stable"]),
            "strength": np.random.uniform(0, 1),
            "factors": ["social_media", "local_events", "seasonal"]
        }
    
    def _identify_peak_hours(self, data):
        """Identify restaurant peak hours."""
        return {
            "weekday": {
                "lunch": "12:00-14:00",
                "dinner": "18:00-20:00"
            },
            "weekend": {
                "brunch": "10:00-13:00",
                "dinner": "19:00-21:00"
            }
        }
    
    def _analyze_seasonal_patterns(self, data):
        """Analyze seasonal patterns in restaurant performance."""
        return {
            "high_season": ["summer", "winter_holidays"],
            "low_season": ["early_spring", "late_fall"],
            "special_events": ["valentine's_day", "new_year's_eve"]
        }
    
    def _identify_signature_dishes(self, data):
        """Identify restaurant's signature dishes."""
        return [
            {"name": "Dish 1", "popularity": np.random.uniform(0.7, 1.0)},
            {"name": "Dish 2", "popularity": np.random.uniform(0.6, 0.9)},
            {"name": "Dish 3", "popularity": np.random.uniform(0.5, 0.8)}
        ]
    
    def _analyze_price_category(self, data):
        """Analyze restaurant's price category."""
        return {
            "category": np.random.choice(["$", "$$", "$$$", "$$$$"]),
            "average_meal_cost": np.random.uniform(15, 100),
            "value_rating": np.random.uniform(0.5, 1.0)
        }
    
    def _analyze_dietary_options(self, data):
        """Analyze available dietary options."""
        options = ["vegetarian", "vegan", "gluten-free", "dairy-free"]
        return np.random.choice(options, size=np.random.randint(1, len(options)+1), replace=False).tolist()

def simulate_restaurant_data():
    """Generate simulated restaurant data for demonstration."""
    return {
        "id": f"REST-{np.random.randint(1000, 9999)}",
        "name": f"Restaurant {np.random.randint(1, 100)}",
        "cuisine_type": np.random.choice([
            "Italian", "Japanese", "Mexican", "Indian", "American"
        ]),
        "reviews": [
            {
                "text": "Great food and atmosphere! The service was excellent.",
                "rating": np.random.randint(4, 6),
                "date": datetime.now() - timedelta(days=np.random.randint(1, 365))
            }
            for _ in range(5)  # Simulate 5 reviews
        ]
    }

def main():
    """Main execution function."""
    # Initialize memory system
    config = Config(
        storage_path="./restaurant_data",
        hot_memory_size=50,
        warm_memory_size=500,
        cold_memory_size=5000
    )
    
    memory_store = MemoryStore(config)
    
    # Initialize agent
    agent = FoodAnalyzerAgent(memory_store)
    
    # Analyze multiple restaurants
    for _ in range(3):
        # Generate sample restaurant data
        restaurant_data = simulate_restaurant_data()
        
        logger.info(f"\nAnalyzing restaurant: {restaurant_data['name']}")
        logger.info(f"Cuisine Type: {restaurant_data['cuisine_type']}")
        
        # Perform analysis
        insights = agent.analyze_restaurant(restaurant_data)
        
        # Log results
        logger.info("\nAnalysis Results:")
        logger.info(f"Overall Sentiment: {insights['review_analysis']['overall_sentiment']:.2f}")
        logger.info("\nTopic Sentiments:")
        for topic, score in insights['review_analysis']['topic_sentiments'].items():
            logger.info(f"- {topic}: {score:.2f}")
        
        logger.info("\nPopularity Trend:")
        logger.info(f"Direction: {insights['trend_analysis']['popularity_trend']['direction']}")
        
        logger.info("\nRecommendations:")
        for rec in insights['recommendations']:
            logger.info(f"- {rec}")
        logger.info("-" * 50)
    
    # Retrieve significant sentiment restaurants
    hot_memories = memory_store.hot_memory.retrieve_all()
    logger.info(f"\nRestaurants with significant sentiment: {len(hot_memories)}")
    
    # Clean up
    memory_store.clear()

if __name__ == "__main__":
    main() 