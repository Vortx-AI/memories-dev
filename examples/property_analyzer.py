#!/usr/bin/env python3
"""
Real Estate Property Analyzer Example
----------------------------------
This example demonstrates using the Memories-Dev framework to analyze
real estate properties using Overture Maps and Planetary Computer data.
"""

import os
import logging
import asyncio
from datetime import datetime, timedelta
import numpy as np
from dotenv import load_dotenv
from pathlib import Path
from memories import MemoryStore, Config
from memories.agents import BaseAgent
from memories.utils.text import TextProcessor
from memories.data_acquisition.sources.overture_api import OvertureAPI
from memories.data_acquisition.sources.planetary_compute import PlanetaryCompute
from memories.data_acquisition import DataManager
from memories.utils.processors import ImageProcessor, VectorProcessor
import uuid
import random
from typing import Dict, List, Any
from shapely.geometry import box

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class PropertyAnalyzer:
    """Analyzes property data and generates insights."""

    def __init__(self, data_manager, memory_store):
        """Initialize property analyzer.
        
        Args:
            data_manager: Data manager instance for accessing data sources
            memory_store: Memory store for persisting insights
        """
        self.data_manager = data_manager
        self.memory_store = memory_store
        self.overture_api = OvertureAPI()
        self.pc_api = PlanetaryCompute()
        self.image_processor = ImageProcessor()

    async def analyze_property(self, property_data):
        try:
            if property_data is None:
                raise ValueError("Invalid property data format")
            
            if not isinstance(property_data, dict):
                raise ValueError("Invalid property data format")
            
            if "location" not in property_data:
                raise ValueError("Missing location or bbox data")
                
            location = property_data["location"]
            if "bbox" not in location:
                raise ValueError("Missing bbox data")
            
            bbox = location["bbox"]
            if not isinstance(bbox, list) or len(bbox) != 4:
                raise ValueError("Invalid bbox format. Must be [west, south, east, north] or Polygon")
            
            try:
                # Get Overture data for property context
                overture_data = await self.overture_api.search(bbox)
                
                # Get satellite data from Planetary Computer
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)  # Last 30 days
                satellite_data = await self.pc_api.search_and_download(
                    bbox=bbox,
                    start_date=start_date.strftime("%Y-%m-%d"),
                    end_date=end_date.strftime("%Y-%m-%d"),
                    collections=["sentinel-2-l2a"],
                    cloud_cover=20.0
                )
                
                insights = await self._analyze_property_data(property_data, overture_data, satellite_data)
                return {
                    "property_id": property_data.get("id", "unknown"),
                    "timestamp": datetime.now().isoformat(),
                    **insights
                }
            except Exception as e:
                # Handle API errors gracefully
                if "Cannot connect to host" in str(e):
                    # Mock data for testing when API is unavailable
                    insights = await self._analyze_property_data(
                        property_data,
                        {"buildings": [], "roads": [], "amenities": []},
                        None
                    )
                    return {
                        "property_id": property_data.get("id", "unknown"),
                        "timestamp": datetime.now().isoformat(),
                        **insights
                    }
                raise
        except Exception as e:
            logger.error(f"Error analyzing property: {str(e)}")
            return {
                "error": str(e),
                "property_id": property_data.get("id", "unknown"),
                "timestamp": None
            }

    async def _analyze_property_data(self, property_data, overture_data, satellite_data):
        condition_score = self._calculate_condition_score(property_data)
        location_score = self._calculate_location_score(property_data, overture_data.get("buildings", []))
        market_score = self._calculate_market_score(property_data)
        environmental_score = self._calculate_environmental_score(satellite_data)
        investment_potential = self._calculate_investment_potential(
            condition_score, 
            location_score, 
            market_score,
            environmental_score
        )
        
        recommendations = self._generate_recommendations(
            condition_score,
            location_score,
            market_score,
            environmental_score,
            investment_potential
        )
        
        return {
            "scores": {
                "condition": condition_score,
                "location": location_score,
                "market": market_score,
                "environmental": environmental_score,
                "investment_potential": investment_potential
            },
            "recommendations": recommendations,
            "satellite_metadata": satellite_data.get("sentinel-2-l2a", {}).get("metadata", {}) if satellite_data else {}
        }

    def _calculate_condition_score(self, property_data):
        """Calculate property condition score."""
        # Mock implementation for testing
        return 0.8

    def _calculate_location_score(self, property_data, nearby_buildings):
        """Calculate location score based on property location and nearby buildings."""
        # Mock implementation for testing
        return 0.7

    def _calculate_market_score(self, property_data):
        """Calculate market score based on property data."""
        # Mock implementation for testing
        return 0.75

    def _calculate_environmental_score(self, satellite_data):
        """Calculate environmental score using satellite data."""
        if not satellite_data or "sentinel-2-l2a" not in satellite_data:
            return 0.5  # Default score when no satellite data available
            
        try:
            ndvi_data = satellite_data["sentinel-2-l2a"]["data"]
            if len(ndvi_data) >= 4:  # Ensure we have enough bands
                red_band = ndvi_data[2]  # B04
                nir_band = ndvi_data[3]  # B08
                ndvi = (nir_band - red_band) / (nir_band + red_band)
                return float(np.mean(ndvi))
        except Exception:
            pass
            
        return 0.5

    def _calculate_investment_potential(self, condition_score, location_score, market_score, environmental_score):
        """Calculate overall investment potential."""
        weights = {
            "condition": 0.25,
            "location": 0.3,
            "market": 0.25,
            "environmental": 0.2
        }
        
        potential = (
            condition_score * weights["condition"] +
            location_score * weights["location"] +
            market_score * weights["market"] +
            environmental_score * weights["environmental"]
        )
        
        return min(1.0, max(0.0, potential))

    def _generate_recommendations(self, condition_score, location_score, market_score, environmental_score, investment_potential):
        """Generate property recommendations."""
        recommendations = []
        
        if condition_score < 0.6:
            recommendations.append("Consider property improvements to increase value")
        if location_score < 0.5:
            recommendations.append("Location may limit future appreciation")
        if market_score < 0.6:
            recommendations.append("Market conditions suggest caution")
        if environmental_score < 0.4:
            recommendations.append("Environmental factors may affect long-term value")
        if investment_potential < 0.5:
            recommendations.append("High risk investment - thorough due diligence recommended")
        elif investment_potential > 0.8:
            recommendations.append("Strong investment potential - consider acting quickly")
            
        return recommendations

def simulate_property_data() -> Dict[str, Any]:
    """Generate random property data for testing."""
    return {
        "id": str(uuid.uuid4()),
        "price": random.randint(200000, 2000000),
        "size_sqft": random.randint(1000, 10000),
        "year_built": random.randint(1950, 2023),
        "condition": random.choice(["excellent", "good", "fair", "poor"]),
        "price_history": [
            random.randint(200000, 2000000) 
            for _ in range(random.randint(3, 10))
        ],
        "bbox": [-122.5, 37.5, -122.0, 38.0],  # San Francisco area
        "location": {
            "bbox": [-122.5, 37.5, -122.0, 38.0]
        }
    }

async def main():
    """Run the property analyzer example."""
    # Initialize memory store
    config = Config(
        storage_path="./examples/data/property_data",
        hot_memory_size=50,
        warm_memory_size=200,
        cold_memory_size=1000
    )
    memory_store = MemoryStore(config)
    
    # Create property analyzer
    data_manager = DataManager()
    analyzer = PropertyAnalyzer(data_manager, memory_store)
    
    # Analyze a simulated property
    property_data = simulate_property_data()
    insights = await analyzer.analyze_property(property_data)
    
    # Print results
    print("\nProperty Analysis Results:")
    print("-" * 50)
    print(f"Property ID: {insights['property_id']}")
    print(f"Analysis Timestamp: {insights['timestamp']}")
    print("\nScores:")
    for key, value in insights['scores'].items():
        print(f"- {key.replace('_', ' ').title()}: {value:.2f}")
    print("\nRecommendations:")
    for rec in insights['recommendations']:
        print(f"- {rec}")

if __name__ == "__main__":
    asyncio.run(main()) 