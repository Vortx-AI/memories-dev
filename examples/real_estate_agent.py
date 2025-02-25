#!/usr/bin/env python3
"""
Real Estate Agent with AI-Powered Property Analysis
----------------------------------
This example demonstrates how to use the Memories-Dev framework to create
an AI agent that analyzes real estate properties, stores property information,
and provides intelligent recommendations based on user preferences.
"""

import os
import logging
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple, Union
from pathlib import Path
from dotenv import load_dotenv
import requests
import json
import rasterio
from shapely.geometry import Point, Polygon
import geopandas as gpd
from sentinelsat import SentinelAPI

from memories import MemoryStore, Config
from memories.models import BaseModel
from memories.utils.text import TextProcessor
from memories.utils.processors.vector_processor import VectorProcessor
from memories.utils.query_understanding import QueryUnderstanding
from memories.utils.response_generation import ResponseGenerator
from memories.utils.earth_memory import (
    OvertureClient, 
    SentinelClient,
    TerrainAnalyzer,
    ClimateDataFetcher,
    EnvironmentalImpactAnalyzer
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Earth Memory clients
overture_client = OvertureClient(api_key=os.getenv("OVERTURE_API_KEY"))
sentinel_client = SentinelClient(
    user=os.getenv("SENTINEL_USER"),
    password=os.getenv("SENTINEL_PASSWORD")
)
terrain_analyzer = TerrainAnalyzer()
climate_fetcher = ClimateDataFetcher()
impact_analyzer = EnvironmentalImpactAnalyzer()

class RealEstateAgent(BaseModel):
    """AI agent specialized in real estate property analysis and recommendations with earth memory integration."""
    
    def __init__(
        self, 
        memory_store: MemoryStore, 
        embedding_model: str = "all-MiniLM-L6-v2",
        embedding_dimension: int = 384,
        similarity_threshold: float = 0.75,
        enable_earth_memory: bool = True
    ):
        """
        Initialize the Real Estate Agent.
        
        Args:
            memory_store: Memory store for maintaining property data
            embedding_model: Name of the embedding model to use
            embedding_dimension: Dimension of the embedding vectors
            similarity_threshold: Threshold for similarity matching
            enable_earth_memory: Whether to enable earth memory features
        """
        super().__init__()
        self.memory_store = memory_store
        self.embedding_model = embedding_model
        self.embedding_dimension = embedding_dimension
        self.similarity_threshold = similarity_threshold
        self.enable_earth_memory = enable_earth_memory
        
        # Initialize utility components
        self.text_processor = TextProcessor()
        self.vector_processor = VectorProcessor(model_name=embedding_model)
        self.query_understanding = QueryUnderstanding()
        self.response_generator = ResponseGenerator()
        
        # Create collection for property embeddings if it doesn't exist
        if "property_embeddings" not in self.memory_store.list_collections():
            self.memory_store.create_collection(
                "property_embeddings", 
                vector_dimension=embedding_dimension
            )
        
        # Create collection for earth memory data if enabled
        if enable_earth_memory and "earth_memory_data" not in self.memory_store.list_collections():
            self.memory_store.create_collection(
                "earth_memory_data",
                vector_dimension=embedding_dimension
            )
    
    async def add_property(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a new property to the database with embeddings and earth memory data.
        
        Args:
            property_data: Dictionary containing property information
                (location, price, features, description, etc.)
            
        Returns:
            Dictionary with property ID and status
        """
        # Create property description for embedding
        property_description = self._create_property_description(property_data)
        
        # Generate embedding for the property description
        embedding = self._generate_embedding(property_description)
        
        # Create metadata
        metadata = {
            "property_id": property_data.get("property_id", str(hash(property_description))[:10]),
            "location": property_data.get("location", ""),
            "coordinates": property_data.get("coordinates", {"lat": 0, "lon": 0}),
            "price": property_data.get("price", 0),
            "bedrooms": property_data.get("bedrooms", 0),
            "bathrooms": property_data.get("bathrooms", 0),
            "square_feet": property_data.get("square_feet", 0),
            "property_type": property_data.get("property_type", ""),
            "year_built": property_data.get("year_built", 0),
            "added_date": datetime.now().isoformat(),
        }
        
        # Fetch and add earth memory data if enabled
        if self.enable_earth_memory:
            earth_memory_data = await self._fetch_earth_memory_data(
                metadata["coordinates"]["lat"],
                metadata["coordinates"]["lon"]
            )
            metadata["earth_memory_data"] = earth_memory_data
        
        # Store the embedding
        embedding_record = {
            "vector": embedding,
            "text": property_description,
            "metadata": metadata
        }
        
        self._store_embedding(embedding_record)
        
        return {
            "property_id": metadata["property_id"],
            "status": "added",
            "embedding_generated": True,
            "earth_memory_data_added": self.enable_earth_memory
        }
    
    async def _fetch_earth_memory_data(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Fetch comprehensive earth memory data for a location.
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Dictionary containing earth memory data
        """
        # Create location point
        location = Point(lon, lat)
        
        # Fetch terrain data
        terrain_data = await terrain_analyzer.analyze_location(location)
        
        # Fetch climate data
        climate_data = await climate_fetcher.get_climate_data(lat, lon)
        
        # Fetch environmental impact data
        impact_data = await impact_analyzer.analyze_location_impact(location)
        
        # Fetch Sentinel satellite imagery
        sentinel_data = await self._fetch_sentinel_data(lat, lon)
        
        # Fetch Overture map data
        overture_data = await self._fetch_overture_data(lat, lon)
        
        return {
            "terrain": terrain_data,
            "climate": climate_data,
            "environmental_impact": impact_data,
            "satellite_imagery": sentinel_data,
            "map_data": overture_data,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _fetch_sentinel_data(self, lat: float, lon: float) -> Dict[str, Any]:
        """Fetch Sentinel satellite imagery data."""
        try:
            # Define area of interest
            bbox = [lon-0.1, lat-0.1, lon+0.1, lat+0.1]
            
            # Query Sentinel data
            products = await sentinel_client.query(
                bbox=bbox,
                date=('NOW-30DAYS', 'NOW'),
                platformname='Sentinel-2',
                cloudcoverpercentage=(0, 20)
            )
            
            if not products:
                return {"error": "No recent Sentinel data available"}
            
            # Get the most recent product
            product = products[0]
            
            # Download and process imagery
            imagery_data = await sentinel_client.get_product_data(product)
            
            return {
                "product_id": product.id,
                "acquisition_date": product.beginposition.isoformat(),
                "cloud_cover": product.cloudcoverpercentage,
                "data": imagery_data
            }
            
        except Exception as e:
            logger.error(f"Error fetching Sentinel data: {str(e)}")
            return {"error": str(e)}
    
    async def _fetch_overture_data(self, lat: float, lon: float) -> Dict[str, Any]:
        """Fetch Overture map data."""
        try:
            # Query Overture for location context
            location_data = await overture_client.get_location_context(lat, lon)
            
            # Get nearby amenities
            amenities = await overture_client.get_nearby_amenities(
                lat, lon, radius_meters=1000
            )
            
            # Get transportation data
            transportation = await overture_client.get_transportation_data(
                lat, lon, radius_meters=1000
            )
            
            return {
                "location_context": location_data,
                "nearby_amenities": amenities,
                "transportation": transportation,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error fetching Overture data: {str(e)}")
            return {"error": str(e)}
    
    async def analyze_property_environment(self, property_id: str) -> Dict[str, Any]:
        """
        Perform detailed environmental analysis of a property.
        
        Args:
            property_id: ID of the property to analyze
            
        Returns:
            Dictionary with environmental analysis
        """
        # Retrieve property data
        property_data = self._get_property_by_id(property_id)
        
        if not property_data or not self.enable_earth_memory:
            return {"error": "Property not found or earth memory not enabled"}
        
        metadata = property_data["metadata"]
        earth_data = metadata.get("earth_memory_data", {})
        
        # Analyze terrain risks
        terrain_risks = self._analyze_terrain_risks(earth_data.get("terrain", {}))
        
        # Analyze climate impacts
        climate_impacts = self._analyze_climate_impacts(earth_data.get("climate", {}))
        
        # Analyze environmental sustainability
        sustainability = self._analyze_sustainability(
            earth_data.get("environmental_impact", {})
        )
        
        # Generate recommendations
        recommendations = self._generate_environmental_recommendations(
            terrain_risks,
            climate_impacts,
            sustainability
        )
        
        return {
            "property_id": property_id,
            "terrain_risks": terrain_risks,
            "climate_impacts": climate_impacts,
            "sustainability": sustainability,
            "recommendations": recommendations,
            "analysis_date": datetime.now().isoformat()
        }
    
    def _analyze_terrain_risks(self, terrain_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze terrain-related risks."""
        risks = []
        risk_level = "low"
        
        # Check elevation and slope
        elevation = terrain_data.get("elevation", 0)
        slope = terrain_data.get("slope", 0)
        
        if slope > 30:
            risks.append("Steep slope may pose landslide risk")
            risk_level = "high"
        elif slope > 15:
            risks.append("Moderate slope may require additional foundation work")
            risk_level = "medium"
            
        # Check flood risk
        flood_risk = terrain_data.get("flood_risk", "low")
        if flood_risk in ["medium", "high"]:
            risks.append(f"{flood_risk.capitalize()} flood risk identified")
            risk_level = flood_risk
            
        return {
            "risk_level": risk_level,
            "identified_risks": risks,
            "elevation": elevation,
            "slope": slope,
            "flood_risk": flood_risk
        }
    
    def _analyze_climate_impacts(self, climate_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze climate-related impacts."""
        impacts = []
        impact_level = "low"
        
        # Analyze temperature trends
        temp_trend = climate_data.get("temperature_trend", 0)
        if abs(temp_trend) > 2:
            impacts.append(f"Significant temperature change trend: {temp_trend}°C/decade")
            impact_level = "high"
            
        # Analyze precipitation changes
        precip_change = climate_data.get("precipitation_change", 0)
        if abs(precip_change) > 20:
            impacts.append(f"Notable precipitation change: {precip_change}%")
            impact_level = "medium"
            
        # Analyze extreme weather frequency
        extreme_weather = climate_data.get("extreme_weather_frequency", "low")
        if extreme_weather != "low":
            impacts.append(f"{extreme_weather.capitalize()} frequency of extreme weather events")
            impact_level = extreme_weather
            
        return {
            "impact_level": impact_level,
            "identified_impacts": impacts,
            "temperature_trend": temp_trend,
            "precipitation_change": precip_change,
            "extreme_weather_frequency": extreme_weather
        }
    
    def _analyze_sustainability(self, impact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze environmental sustainability."""
        factors = []
        sustainability_score = 0
        
        # Analyze air quality
        air_quality = impact_data.get("air_quality", 0)
        if air_quality > 0:
            sustainability_score += air_quality
            factors.append(f"Air quality index: {air_quality}")
            
        # Analyze green space proximity
        green_space = impact_data.get("green_space_proximity", 0)
        if green_space > 0:
            sustainability_score += green_space
            factors.append(f"Green space proximity score: {green_space}")
            
        # Analyze solar potential
        solar_potential = impact_data.get("solar_potential", 0)
        if solar_potential > 0:
            sustainability_score += solar_potential
            factors.append(f"Solar energy potential: {solar_potential}")
            
        # Calculate overall score
        max_possible_score = 300  # Assuming each factor is 0-100
        sustainability_score = (sustainability_score / max_possible_score) * 100
        
        return {
            "sustainability_score": sustainability_score,
            "factors": factors,
            "air_quality": air_quality,
            "green_space_proximity": green_space,
            "solar_potential": solar_potential
        }
    
    def _generate_environmental_recommendations(
        self,
        terrain_risks: Dict[str, Any],
        climate_impacts: Dict[str, Any],
        sustainability: Dict[str, Any]
    ) -> List[str]:
        """Generate environmental recommendations."""
        recommendations = []
        
        # Terrain-based recommendations
        if terrain_risks["risk_level"] != "low":
            for risk in terrain_risks["identified_risks"]:
                if "flood" in risk.lower():
                    recommendations.append(
                        "Consider flood mitigation measures such as elevated foundations "
                        "and proper drainage systems"
                    )
                elif "slope" in risk.lower():
                    recommendations.append(
                        "Consult with a geotechnical engineer about slope stability "
                        "and appropriate foundation design"
                    )
                    
        # Climate-based recommendations
        if climate_impacts["impact_level"] != "low":
            for impact in climate_impacts["identified_impacts"]:
                if "temperature" in impact.lower():
                    recommendations.append(
                        "Consider enhanced insulation and energy-efficient HVAC systems "
                        "to address temperature trends"
                    )
                elif "precipitation" in impact.lower():
                    recommendations.append(
                        "Implement robust water management systems and consider "
                        "drought-resistant landscaping"
                    )
                    
        # Sustainability recommendations
        if sustainability["sustainability_score"] < 60:
            recommendations.append(
                "Consider improvements to increase property sustainability: "
                "solar panels, energy-efficient appliances, and green building materials"
            )
            
        if not recommendations:
            recommendations.append(
                "Property shows good environmental characteristics. "
                "Continue maintaining current sustainability features."
            )
            
        return recommendations

def simulate_property_database() -> List[Dict[str, Any]]:
    """Generate a simulated database of properties."""
    properties = [
        {
            "property_id": "PROP001",
            "location": "San Francisco, CA",
            "coordinates": {"lat": 37.7749, "lon": -122.4194},
            "price": 1250000,
            "bedrooms": 2,
            "bathrooms": 2,
            "square_feet": 1200,
            "property_type": "Condo",
            "year_built": 2015,
            "features": ["Hardwood floors", "Stainless steel appliances", "In-unit laundry"],
            "description": "Modern condo in the heart of San Francisco with beautiful city views."
        },
        {
            "property_id": "PROP002",
            "location": "San Francisco, CA",
            "coordinates": {"lat": 37.7833, "lon": -122.4167},
            "price": 2500000,
            "bedrooms": 4,
            "bathrooms": 3,
            "square_feet": 2800,
            "property_type": "Single Family Home",
            "year_built": 1998,
            "features": ["Backyard", "Garage", "Fireplace", "Updated kitchen"],
            "description": "Spacious family home in a quiet neighborhood with excellent schools nearby."
        },
        {
            "property_id": "PROP003",
            "location": "Oakland, CA",
            "coordinates": {"lat": 37.8044, "lon": -122.2711},
            "price": 850000,
            "bedrooms": 3,
            "bathrooms": 2,
            "square_feet": 1800,
            "property_type": "Single Family Home",
            "year_built": 1965,
            "features": ["Renovated bathroom", "Large kitchen", "Deck"],
            "description": "Charming mid-century home with character and modern updates."
        },
        {
            "property_id": "PROP004",
            "location": "Berkeley, CA",
            "coordinates": {"lat": 37.8716, "lon": -122.2727},
            "price": 1100000,
            "bedrooms": 3,
            "bathrooms": 2,
            "square_feet": 1600,
            "property_type": "Craftsman",
            "year_built": 1925,
            "features": ["Original woodwork", "Built-ins", "Garden"],
            "description": "Classic Berkeley Craftsman with period details and a beautiful garden."
        },
        {
            "property_id": "PROP005",
            "location": "Palo Alto, CA",
            "coordinates": {"lat": 37.4419, "lon": -122.1430},
            "price": 3200000,
            "bedrooms": 4,
            "bathrooms": 3.5,
            "square_feet": 2400,
            "property_type": "Contemporary",
            "year_built": 2020,
            "features": ["Smart home", "Solar panels", "Home office", "Pool"],
            "description": "Luxury contemporary home with high-end finishes and energy-efficient features."
        }
    ]
    
    return properties

async def main():
    """Main execution function."""
    # Initialize memory system
    config = Config(
        storage_path="./real_estate_agent_data",
        hot_memory_size=50,
        warm_memory_size=200,
        cold_memory_size=1000
    )
    
    memory_store = MemoryStore(config)
    
    # Initialize real estate agent
    real_estate_agent = RealEstateAgent(memory_store, enable_earth_memory=True)
    
    # Generate property database
    property_database = simulate_property_database()
    
    # Add properties to the agent's memory
    logger.info("Adding properties to the database with earth memory data...")
    for property_data in property_database:
        result = await real_estate_agent.add_property(property_data)
        logger.info(f"Added property {result['property_id']} with earth memory: {result['earth_memory_data_added']}")
    
    # Search for properties
    search_query = "Modern home in San Francisco with at least 2 bedrooms"
    logger.info(f"\nSearching for: '{search_query}'")
    
    search_results = await real_estate_agent.search_properties(search_query, top_k=3)
    
    logger.info("\nTop matching properties:")
    for i, result in enumerate(search_results):
        logger.info(f"{i+1}. Match score: {result['similarity']:.4f}")
        logger.info(f"   {result['bedrooms']}bd/{result['bathrooms']}ba {result['property_type']} in {result['location']}")
        logger.info(f"   Price: ${result['price']:,}")
        logger.info(f"   {result['square_feet']} sq ft, built in {result['year_built']}")
    
    # Analyze environmental aspects of a specific property
    property_to_analyze = "PROP005"  # Palo Alto contemporary
    logger.info(f"\nAnalyzing environmental aspects of property {property_to_analyze}...")
    
    env_analysis = await real_estate_agent.analyze_property_environment(property_to_analyze)
    
    if "error" not in env_analysis:
        logger.info("\nEnvironmental Analysis:")
        logger.info(f"Terrain Risk Level: {env_analysis['terrain_risks']['risk_level']}")
        if env_analysis['terrain_risks']['identified_risks']:
            logger.info("Identified Terrain Risks:")
            for risk in env_analysis['terrain_risks']['identified_risks']:
                logger.info(f"- {risk}")
        
        logger.info(f"\nClimate Impact Level: {env_analysis['climate_impacts']['impact_level']}")
        if env_analysis['climate_impacts']['identified_impacts']:
            logger.info("Identified Climate Impacts:")
            for impact in env_analysis['climate_impacts']['identified_impacts']:
                logger.info(f"- {impact}")
        
        logger.info(f"\nSustainability Score: {env_analysis['sustainability']['sustainability_score']:.1f}/100")
        if env_analysis['sustainability']['factors']:
            logger.info("Sustainability Factors:")
            for factor in env_analysis['sustainability']['factors']:
                logger.info(f"- {factor}")
        
        logger.info("\nEnvironmental Recommendations:")
        for rec in env_analysis['recommendations']:
            logger.info(f"- {rec}")
    else:
        logger.error(f"Error analyzing property: {env_analysis['error']}")
    
    # Recommend properties based on user preferences with environmental considerations
    user_preferences = {
        "location": "San Francisco",
        "min_bedrooms": 2,
        "min_bathrooms": 2,
        "max_price": 2000000,
        "features": ["Hardwood floors"],
        "environmental_preferences": {
            "min_sustainability_score": 70,
            "max_climate_risk": "medium",
            "prefer_solar_ready": True
        }
    }
    
    logger.info("\nRecommending properties based on user preferences...")
    recommendations = await real_estate_agent.recommend_properties(user_preferences)
    
    logger.info("\nTop recommendations:")
    for i, rec in enumerate(recommendations):
        logger.info(f"{i+1}. Match score: {rec['weighted_score']:.4f}")
        logger.info(f"   {rec['bedrooms']}bd/{rec['bathrooms']}ba {rec['property_type']} in {rec['location']}")
        logger.info(f"   Price: ${rec['price']:,}")
        if "earth_memory_data" in rec:
            env_data = rec["earth_memory_data"]
            logger.info(f"   Sustainability Score: {env_data.get('sustainability_score', 'N/A')}")
            logger.info(f"   Climate Risk: {env_data.get('climate_risk', 'N/A')}")
            logger.info(f"   Solar Potential: {env_data.get('solar_potential', 'N/A')}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
