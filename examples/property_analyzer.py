#!/usr/bin/env python3
"""
Property Analyzer with AI-Powered Environmental Analysis
----------------------------------
This example demonstrates how to use the Memories-Dev framework to create
an AI agent that performs detailed analysis of properties using earth memory data,
focusing on environmental impact, sustainability, and future risks.
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
from shapely.geometry import Point, Polygon, box
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
    EnvironmentalImpactAnalyzer,
    LandUseClassifier,
    WaterResourceAnalyzer,
    GeologicalDataFetcher
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
land_use_classifier = LandUseClassifier()
water_analyzer = WaterResourceAnalyzer()
geological_fetcher = GeologicalDataFetcher()

class PropertyAnalyzer(BaseModel):
    """AI agent specialized in comprehensive property analysis using earth memory data."""
    
    def __init__(
        self, 
        memory_store: MemoryStore,
        embedding_model: str = "all-MiniLM-L6-v2",
        embedding_dimension: int = 384,
        analysis_radius_meters: int = 2000
    ):
        """
        Initialize the Property Analyzer.
        
        Args:
            memory_store: Memory store for maintaining analysis data
            embedding_model: Name of the embedding model to use
            embedding_dimension: Dimension of the embedding vectors
            analysis_radius_meters: Radius around property for analysis
        """
        super().__init__()
        self.memory_store = memory_store
        self.embedding_model = embedding_model
        self.embedding_dimension = embedding_dimension
        self.analysis_radius_meters = analysis_radius_meters
        
        # Initialize utility components
        self.text_processor = TextProcessor()
        self.vector_processor = VectorProcessor(model_name=embedding_model)
        self.query_understanding = QueryUnderstanding()
        self.response_generator = ResponseGenerator()
        
        # Create collections if they don't exist
        self._initialize_collections()
    
    def _initialize_collections(self):
        """Initialize memory collections."""
        collections = [
            ("property_analyses", self.embedding_dimension),
            ("environmental_data", self.embedding_dimension),
            ("geological_data", self.embedding_dimension),
            ("water_resources", self.embedding_dimension),
            ("land_use_changes", self.embedding_dimension),
            ("historical_imagery", self.embedding_dimension)
        ]
        
        for name, dim in collections:
            if name not in self.memory_store.list_collections():
                self.memory_store.create_collection(name, vector_dimension=dim)
    
    async def analyze_property(
        self,
        lat: float,
        lon: float,
        property_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform comprehensive property analysis.
        
        Args:
            lat: Property latitude
            lon: Property longitude
            property_data: Optional additional property data
            
        Returns:
            Dictionary containing comprehensive analysis results
        """
        location = Point(lon, lat)
        analysis_area = self._create_analysis_area(lat, lon)
        
        # Fetch and analyze various data sources
        terrain_analysis = await self._analyze_terrain(location, analysis_area)
        water_analysis = await self._analyze_water_resources(location, analysis_area)
        geological_analysis = await self._analyze_geological_features(location, analysis_area)
        environmental_analysis = await self._analyze_environmental_factors(location, analysis_area)
        land_use_analysis = await self._analyze_land_use(location, analysis_area)
        historical_analysis = await self._analyze_historical_changes(location, analysis_area)
        
        # Combine analyses and generate recommendations
        combined_analysis = self._combine_analyses(
            terrain_analysis,
            water_analysis,
            geological_analysis,
            environmental_analysis,
            land_use_analysis,
            historical_analysis
        )
        
        # Store analysis results
        self._store_analysis_results(combined_analysis, lat, lon)
        
        return combined_analysis
    
    def _create_analysis_area(self, lat: float, lon: float) -> Polygon:
        """Create a polygon representing the analysis area."""
        # Convert radius from meters to degrees (approximate)
        radius_deg = self.analysis_radius_meters / 111000  # 1 degree ≈ 111km
        
        return box(
            lon - radius_deg,
            lat - radius_deg,
            lon + radius_deg,
            lat + radius_deg
        )
    
    async def _analyze_terrain(self, location: Point, area: Polygon) -> Dict[str, Any]:
        """Analyze terrain features and risks."""
        # Get terrain data
        terrain_data = await terrain_analyzer.analyze_location(location)
        
        # Analyze slope stability
        slope_analysis = await terrain_analyzer.analyze_slope_stability(area)
        
        # Analyze drainage patterns
        drainage = await terrain_analyzer.analyze_drainage_patterns(area)
        
        # Analyze soil conditions
        soil_data = await geological_fetcher.get_soil_data(location)
        
        return {
            "elevation": terrain_data["elevation"],
            "slope": terrain_data["slope"],
            "aspect": terrain_data["aspect"],
            "slope_stability": slope_analysis,
            "drainage_patterns": drainage,
            "soil_conditions": soil_data,
            "terrain_risks": self._assess_terrain_risks(
                terrain_data,
                slope_analysis,
                drainage,
                soil_data
            )
        }
    
    async def _analyze_water_resources(self, location: Point, area: Polygon) -> Dict[str, Any]:
        """Analyze water resources and risks."""
        # Analyze surface water
        surface_water = await water_analyzer.analyze_surface_water(area)
        
        # Analyze groundwater
        groundwater = await water_analyzer.analyze_groundwater(location)
        
        # Analyze flood risk
        flood_risk = await water_analyzer.analyze_flood_risk(area)
        
        # Analyze water quality
        water_quality = await water_analyzer.analyze_water_quality(location)
        
        return {
            "surface_water": surface_water,
            "groundwater": groundwater,
            "flood_risk": flood_risk,
            "water_quality": water_quality,
            "water_risks": self._assess_water_risks(
                surface_water,
                groundwater,
                flood_risk,
                water_quality
            )
        }
    
    async def _analyze_geological_features(self, location: Point, area: Polygon) -> Dict[str, Any]:
        """Analyze geological features and risks."""
        # Get geological data
        geology = await geological_fetcher.get_geological_data(location)
        
        # Analyze seismic risk
        seismic = await geological_fetcher.analyze_seismic_risk(area)
        
        # Analyze subsidence risk
        subsidence = await geological_fetcher.analyze_subsidence_risk(area)
        
        # Analyze mineral resources
        minerals = await geological_fetcher.analyze_mineral_resources(area)
        
        return {
            "geological_formation": geology["formation"],
            "rock_types": geology["rock_types"],
            "seismic_risk": seismic,
            "subsidence_risk": subsidence,
            "mineral_resources": minerals,
            "geological_risks": self._assess_geological_risks(
                geology,
                seismic,
                subsidence
            )
        }
    
    async def _analyze_environmental_factors(self, location: Point, area: Polygon) -> Dict[str, Any]:
        """Analyze environmental factors and impacts."""
        # Analyze climate data
        climate = await climate_fetcher.get_climate_data(location.y, location.x)
        
        # Analyze air quality
        air_quality = await impact_analyzer.analyze_air_quality(location)
        
        # Analyze noise pollution
        noise = await impact_analyzer.analyze_noise_pollution(area)
        
        # Analyze biodiversity
        biodiversity = await impact_analyzer.analyze_biodiversity(area)
        
        return {
            "climate_data": climate,
            "air_quality": air_quality,
            "noise_pollution": noise,
            "biodiversity": biodiversity,
            "environmental_risks": self._assess_environmental_risks(
                climate,
                air_quality,
                noise,
                biodiversity
            )
        }
    
    async def _analyze_land_use(self, location: Point, area: Polygon) -> Dict[str, Any]:
        """Analyze land use patterns and changes."""
        # Get current land use
        current_use = await land_use_classifier.classify_land_use(location)
        
        # Analyze land use changes
        changes = await land_use_classifier.analyze_historical_changes(area)
        
        # Analyze urban development
        urban_dev = await land_use_classifier.analyze_urban_development(area)
        
        # Predict future changes
        future_changes = await land_use_classifier.predict_future_changes(area)
        
        return {
            "current_land_use": current_use,
            "historical_changes": changes,
            "urban_development": urban_dev,
            "predicted_changes": future_changes,
            "land_use_risks": self._assess_land_use_risks(
                current_use,
                changes,
                urban_dev,
                future_changes
            )
        }
    
    async def _analyze_historical_changes(self, location: Point, area: Polygon) -> Dict[str, Any]:
        """Analyze historical changes in the area."""
        # Get historical satellite imagery
        imagery = await sentinel_client.get_historical_imagery(area)
        
        # Analyze landscape changes
        landscape_changes = await land_use_classifier.analyze_landscape_changes(imagery)
        
        # Analyze development patterns
        development = await land_use_classifier.analyze_development_patterns(imagery)
        
        return {
            "historical_imagery": imagery,
            "landscape_changes": landscape_changes,
            "development_patterns": development,
            "historical_risks": self._assess_historical_risks(
                landscape_changes,
                development
            )
        }
    
    def _assess_terrain_risks(
        self,
        terrain_data: Dict[str, Any],
        slope_analysis: Dict[str, Any],
        drainage: Dict[str, Any],
        soil_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Assess terrain-related risks."""
        risks = []
        
        # Assess slope risks
        if slope_analysis["stability_rating"] < 0.6:
            risks.append({
                "type": "slope_stability",
                "level": "high",
                "description": "Potential slope stability issues identified",
                "mitigation": "Detailed geotechnical investigation recommended"
            })
        
        # Assess drainage risks
        if drainage["quality_rating"] < 0.5:
            risks.append({
                "type": "drainage",
                "level": "medium",
                "description": "Poor drainage patterns detected",
                "mitigation": "Drainage system improvements recommended"
            })
        
        # Assess soil risks
        if soil_data["bearing_capacity"] < 1500:  # kPa
            risks.append({
                "type": "soil_stability",
                "level": "high",
                "description": "Low soil bearing capacity",
                "mitigation": "Special foundation design required"
            })
        
        return risks
    
    def _assess_water_risks(
        self,
        surface_water: Dict[str, Any],
        groundwater: Dict[str, Any],
        flood_risk: Dict[str, Any],
        water_quality: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Assess water-related risks."""
        risks = []
        
        # Assess flood risks
        if flood_risk["probability"] > 0.3:
            risks.append({
                "type": "flood",
                "level": "high" if flood_risk["probability"] > 0.6 else "medium",
                "description": f"Flood probability: {flood_risk['probability']:.1%}",
                "mitigation": "Flood protection measures recommended"
            })
        
        # Assess groundwater risks
        if groundwater["depth"] < 3:  # meters
            risks.append({
                "type": "groundwater",
                "level": "medium",
                "description": "High groundwater table",
                "mitigation": "Waterproofing measures recommended"
            })
        
        # Assess water quality risks
        if water_quality["rating"] < 0.7:
            risks.append({
                "type": "water_quality",
                "level": "medium",
                "description": "Water quality concerns identified",
                "mitigation": "Water quality treatment may be necessary"
            })
        
        return risks
    
    def _assess_geological_risks(
        self,
        geology: Dict[str, Any],
        seismic: Dict[str, Any],
        subsidence: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Assess geological risks."""
        risks = []
        
        # Assess seismic risks
        if seismic["risk_level"] > 0.5:
            risks.append({
                "type": "seismic",
                "level": "high" if seismic["risk_level"] > 0.7 else "medium",
                "description": "Significant seismic risk",
                "mitigation": "Seismic-resistant design required"
            })
        
        # Assess subsidence risks
        if subsidence["risk_level"] > 0.3:
            risks.append({
                "type": "subsidence",
                "level": "high" if subsidence["risk_level"] > 0.6 else "medium",
                "description": "Ground subsidence risk identified",
                "mitigation": "Foundation design must account for potential settlement"
            })
        
        return risks
    
    def _assess_environmental_risks(
        self,
        climate: Dict[str, Any],
        air_quality: Dict[str, Any],
        noise: Dict[str, Any],
        biodiversity: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Assess environmental risks."""
        risks = []
        
        # Assess climate risks
        if climate["extreme_weather_probability"] > 0.3:
            risks.append({
                "type": "climate",
                "level": "high" if climate["extreme_weather_probability"] > 0.6 else "medium",
                "description": "Increased extreme weather risk",
                "mitigation": "Climate-resilient design recommended"
            })
        
        # Assess air quality risks
        if air_quality["index"] > 100:  # AQI
            risks.append({
                "type": "air_quality",
                "level": "high" if air_quality["index"] > 150 else "medium",
                "description": "Poor air quality detected",
                "mitigation": "Air filtration systems recommended"
            })
        
        # Assess noise risks
        if noise["level"] > 65:  # dB
            risks.append({
                "type": "noise",
                "level": "medium",
                "description": "High noise levels",
                "mitigation": "Sound insulation recommended"
            })
        
        return risks
    
    def _assess_land_use_risks(
        self,
        current_use: Dict[str, Any],
        changes: Dict[str, Any],
        urban_dev: Dict[str, Any],
        future_changes: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Assess land use related risks."""
        risks = []
        
        # Assess development pressure
        if urban_dev["pressure_level"] > 0.7:
            risks.append({
                "type": "urban_development",
                "level": "medium",
                "description": "High urban development pressure",
                "mitigation": "Monitor local development plans"
            })
        
        # Assess land use conflicts
        if current_use["conflict_probability"] > 0.5:
            risks.append({
                "type": "land_use_conflict",
                "level": "medium",
                "description": "Potential land use conflicts",
                "mitigation": "Review zoning regulations"
            })
        
        # Assess future changes
        if future_changes["significant_change_probability"] > 0.6:
            risks.append({
                "type": "future_changes",
                "level": "medium",
                "description": "Significant land use changes predicted",
                "mitigation": "Consider future area development in planning"
            })
        
        return risks
    
    def _assess_historical_risks(
        self,
        landscape_changes: Dict[str, Any],
        development: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Assess risks based on historical changes."""
        risks = []
        
        # Assess rapid development risks
        if development["rate_of_change"] > 0.5:
            risks.append({
                "type": "rapid_development",
                "level": "medium",
                "description": "Rapid area development observed",
                "mitigation": "Monitor infrastructure capacity"
            })
        
        # Assess landscape degradation
        if landscape_changes["degradation_level"] > 0.4:
            risks.append({
                "type": "landscape_degradation",
                "level": "medium",
                "description": "Landscape degradation trends observed",
                "mitigation": "Environmental protection measures recommended"
            })
        
        return risks
    
    def _combine_analyses(
        self,
        terrain_analysis: Dict[str, Any],
        water_analysis: Dict[str, Any],
        geological_analysis: Dict[str, Any],
        environmental_analysis: Dict[str, Any],
        land_use_analysis: Dict[str, Any],
        historical_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Combine all analyses into a comprehensive report."""
        # Combine all risks
        all_risks = (
            terrain_analysis.get("terrain_risks", []) +
            water_analysis.get("water_risks", []) +
            geological_analysis.get("geological_risks", []) +
            environmental_analysis.get("environmental_risks", []) +
            land_use_analysis.get("land_use_risks", []) +
            historical_analysis.get("historical_risks", [])
        )
        
        # Calculate overall risk level
        risk_levels = [risk["level"] for risk in all_risks]
        overall_risk = "high" if "high" in risk_levels else "medium" if "medium" in risk_levels else "low"
        
        # Generate recommendations
        recommendations = self._generate_recommendations(all_risks)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_risk_level": overall_risk,
            "analyses": {
                "terrain": terrain_analysis,
                "water": water_analysis,
                "geological": geological_analysis,
                "environmental": environmental_analysis,
                "land_use": land_use_analysis,
                "historical": historical_analysis
            },
            "identified_risks": all_risks,
            "recommendations": recommendations
        }
    
    def _generate_recommendations(self, risks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate prioritized recommendations based on identified risks."""
        recommendations = []
        
        # Group risks by level
        high_risks = [r for r in risks if r["level"] == "high"]
        medium_risks = [r for r in risks if r["level"] == "medium"]
        
        # Generate immediate action recommendations for high risks
        for risk in high_risks:
            recommendations.append({
                "priority": "high",
                "type": risk["type"],
                "action": risk["mitigation"],
                "timeframe": "immediate"
            })
        
        # Generate medium-term recommendations for medium risks
        for risk in medium_risks:
            recommendations.append({
                "priority": "medium",
                "type": risk["type"],
                "action": risk["mitigation"],
                "timeframe": "medium-term"
            })
        
        # Add general recommendations if no significant risks
        if not high_risks and not medium_risks:
            recommendations.append({
                "priority": "low",
                "type": "general",
                "action": "Maintain regular monitoring and standard maintenance",
                "timeframe": "ongoing"
            })
        
        return recommendations
    
    def _store_analysis_results(self, analysis: Dict[str, Any], lat: float, lon: float) -> None:
        """Store analysis results in memory."""
        # Create embedding for the analysis
        analysis_text = json.dumps(analysis)
        embedding = self.vector_processor.embed_text(analysis_text)
        
        # Store in property analyses collection
        self.memory_store.add_item(
            "property_analyses",
            vector=embedding,
            text=analysis_text,
            metadata={
                "latitude": lat,
                "longitude": lon,
                "timestamp": analysis["timestamp"],
                "overall_risk_level": analysis["overall_risk_level"]
            }
        )

def simulate_properties() -> List[Dict[str, Any]]:
    """Generate simulated properties for analysis."""
    return [
        {
            "name": "Hillside Property",
            "coordinates": {"lat": 37.7749, "lon": -122.4194},
            "description": "Property on a steep hillside with potential slope stability concerns."
        },
        {
            "name": "Waterfront Property",
            "coordinates": {"lat": 37.8044, "lon": -122.2711},
            "description": "Property near the waterfront with potential flood risks."
        },
        {
            "name": "Urban Development",
            "coordinates": {"lat": 37.7833, "lon": -122.4167},
            "description": "Property in a rapidly developing urban area."
        }
    ]

async def main():
    """Main execution function."""
    # Initialize memory system
    config = Config(
        storage_path="./property_analyzer_data",
        hot_memory_size=50,
        warm_memory_size=200,
        cold_memory_size=1000
    )
    
    memory_store = MemoryStore(config)
    
    # Initialize property analyzer
    analyzer = PropertyAnalyzer(memory_store)
    
    # Get simulated properties
    properties = simulate_properties()
    
    # Analyze each property
    for property_data in properties:
        logger.info(f"\nAnalyzing property: {property_data['name']}")
        logger.info(f"Description: {property_data['description']}")
        
        analysis = await analyzer.analyze_property(
            property_data["coordinates"]["lat"],
            property_data["coordinates"]["lon"],
            property_data
        )
        
        logger.info(f"\nAnalysis Results:")
        logger.info(f"Overall Risk Level: {analysis['overall_risk_level']}")
        
        logger.info("\nIdentified Risks:")
        for risk in analysis["identified_risks"]:
            logger.info(f"- {risk['type']} (Level: {risk['level']})")
            logger.info(f"  Description: {risk['description']}")
            logger.info(f"  Mitigation: {risk['mitigation']}")
        
        logger.info("\nRecommendations:")
        for rec in analysis["recommendations"]:
            logger.info(f"- Priority: {rec['priority']}")
            logger.info(f"  Action: {rec['action']}")
            logger.info(f"  Timeframe: {rec['timeframe']}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 