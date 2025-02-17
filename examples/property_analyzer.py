#!/usr/bin/env python3
"""
Real Estate Property Analyzer Example
-----------------------------------
This example demonstrates how to use the Memories-Dev framework to analyze
real estate properties and market trends using historical data.
"""

import os
import logging
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
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

class PropertyAgent(BaseAgent):
    """Agent specialized in real estate analysis."""
    
    def __init__(self, memory_store: MemoryStore):
        super().__init__(name="property_agent")
        self.memory_store = memory_store
        self.text_processor = TextProcessor()
        
    def analyze_property(self, property_data):
        """Analyze property data and generate insights."""
        # Process property data
        analysis = self._analyze_property_details(property_data)
        market_context = self._analyze_market_context(property_data["location"])
        
        # Combine analyses
        insights = {
            "property_analysis": analysis,
            "market_context": market_context,
            "recommendations": self._generate_recommendations(analysis, market_context)
        }
        
        # Store insights in memory
        self._store_insights(insights, property_data)
        
        return insights
    
    def _analyze_property_details(self, property_data):
        """Analyze specific property details."""
        return {
            "price_per_sqft": property_data["price"] / property_data["square_feet"],
            "condition_score": self._calculate_condition_score(property_data),
            "location_score": self._calculate_location_score(property_data),
            "investment_potential": self._calculate_investment_potential(property_data)
        }
    
    def _analyze_market_context(self, location):
        """Analyze market conditions for the area."""
        return {
            "market_trend": self._get_market_trend(location),
            "comparable_properties": self._find_comparable_properties(location),
            "market_volatility": self._calculate_market_volatility(location)
        }
    
    def _generate_recommendations(self, analysis, market_context):
        """Generate property-specific recommendations."""
        recommendations = []
        
        # Price-based recommendations
        if analysis["price_per_sqft"] > market_context["comparable_properties"]["avg_price_per_sqft"]:
            recommendations.append("Property is priced above market average - consider negotiation")
        
        # Investment recommendations
        if analysis["investment_potential"] > 0.7:
            recommendations.append("High investment potential - consider long-term hold")
        
        # Market-based recommendations
        if market_context["market_trend"]["direction"] == "up":
            recommendations.append("Market is trending upward - good time to buy")
        
        return recommendations
    
    def _store_insights(self, insights, property_data):
        """Store insights in appropriate memory layers."""
        # Store in hot memory if high investment potential
        if insights["property_analysis"]["investment_potential"] > 0.8:
            self.memory_store.hot_memory.store({
                "timestamp": datetime.now().isoformat(),
                "type": "high_potential_property",
                "property_id": property_data["id"],
                "insights": insights
            })
        else:
            self.memory_store.warm_memory.store({
                "timestamp": datetime.now().isoformat(),
                "type": "property_analysis",
                "property_id": property_data["id"],
                "insights": insights
            })
    
    def _calculate_condition_score(self, data):
        """Calculate property condition score."""
        # Simulate condition scoring
        return np.random.uniform(0.5, 1.0)
    
    def _calculate_location_score(self, data):
        """Calculate location desirability score."""
        # Simulate location scoring
        return np.random.uniform(0.3, 1.0)
    
    def _calculate_investment_potential(self, data):
        """Calculate investment potential score."""
        # Simulate investment potential calculation
        return np.random.uniform(0.2, 1.0)
    
    def _get_market_trend(self, location):
        """Get market trend data for location."""
        # Simulate market trend analysis
        return {
            "direction": np.random.choice(["up", "down", "stable"]),
            "strength": np.random.uniform(0, 1),
            "confidence": np.random.uniform(0.5, 1.0)
        }
    
    def _find_comparable_properties(self, location):
        """Find and analyze comparable properties."""
        return {
            "count": np.random.randint(3, 15),
            "avg_price_per_sqft": np.random.uniform(200, 500),
            "price_range": {
                "min": np.random.uniform(150, 300),
                "max": np.random.uniform(400, 800)
            }
        }
    
    def _calculate_market_volatility(self, location):
        """Calculate market volatility index."""
        return np.random.uniform(0, 1)

def simulate_property_data():
    """Generate simulated property data for demonstration."""
    return {
        "id": f"PROP-{np.random.randint(1000, 9999)}",
        "price": np.random.uniform(200000, 1500000),
        "square_feet": np.random.uniform(1000, 4000),
        "bedrooms": np.random.randint(2, 6),
        "bathrooms": np.random.randint(1, 4),
        "year_built": np.random.randint(1950, 2023),
        "location": {
            "city": np.random.choice(["San Francisco", "New York", "Austin", "Seattle"]),
            "neighborhood": f"District-{np.random.randint(1, 10)}"
        }
    }

def main():
    """Main execution function."""
    # Initialize memory system
    config = Config(
        storage_path="./property_data",
        hot_memory_size=50,
        warm_memory_size=500,
        cold_memory_size=5000
    )
    
    memory_store = MemoryStore(config)
    
    # Initialize agent
    agent = PropertyAgent(memory_store)
    
    # Analyze multiple properties
    for _ in range(5):
        # Generate sample property data
        property_data = simulate_property_data()
        
        logger.info(f"\nAnalyzing property: {property_data['id']}")
        logger.info(f"Location: {property_data['location']['city']}, "
                   f"{property_data['location']['neighborhood']}")
        
        # Perform analysis
        insights = agent.analyze_property(property_data)
        
        # Log results
        logger.info("\nAnalysis Results:")
        logger.info(f"Price per sq ft: ${insights['property_analysis']['price_per_sqft']:.2f}")
        logger.info(f"Investment Potential: {insights['property_analysis']['investment_potential']:.2f}")
        logger.info("\nMarket Context:")
        logger.info(f"Market Trend: {insights['market_context']['market_trend']['direction']}")
        logger.info("\nRecommendations:")
        for rec in insights['recommendations']:
            logger.info(f"- {rec}")
        logger.info("-" * 50)
    
    # Retrieve high-potential properties
    hot_memories = memory_store.hot_memory.retrieve_all()
    logger.info(f"\nHigh potential properties found: {len(hot_memories)}")
    
    # Clean up
    memory_store.clear()

if __name__ == "__main__":
    main() 