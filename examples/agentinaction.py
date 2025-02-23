#!/usr/bin/env python3
"""
AgentInAction Example
--------------------
An intelligent agent that combines chat capabilities with location-aware
context processing and future scenario generation.
"""

import os
import sys
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import json
import numpy as np
from pathlib import Path
import torch

from memories import MemoryStore, Config, LoadModel
from memories.data_acquisition.sources.overture_api import OvertureAPI
from memories.data_acquisition.sources.sentinel_api import SentinelAPI
from memories.agents.agent import Agent
from memories.agents.agent_context import LocationExtractor
from memories.utils.text import TextProcessor
from memories.core import HotMemory, WarmMemory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class AgentContext:
    """Stores the current context of the agent's conversation"""
    location: Optional[Dict[str, Any]] = None
    temporal_range: Optional[Tuple[str, str]] = None
    last_query_type: Optional[str] = None
    conversation_history: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.conversation_history is None:
            self.conversation_history = []

class IntelligentAgent:
    """Advanced agent combining chat, location analysis, and scenario generation"""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """Initialize the intelligent agent with model and memory store."""
        self.logger = logging.getLogger(__name__)
        
        # Set up GPU if available
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        if self.device.type == "cuda":
            torch.cuda.empty_cache()
        
        # Initialize model - try local installation first, then OpenAI
        try:
            # Try loading local DeepSeek model first
            self.model = LoadModel(
                use_gpu=self.device.type == "cuda",
                model_provider="deepseek-ai",
                deployment_type="local",
                model_name="deepseek-coder-6.7b"
            )
            self.logger.info("Successfully initialized local DeepSeek model")
        except Exception as e:
            self.logger.warning(f"Failed to load local model: {str(e)}")
            
            # Fall back to OpenAI if API key is provided
            if openai_api_key:
                try:
                    self.model = LoadModel(
                        use_gpu=False,  # OpenAI API doesn't use local GPU
                        model_provider="openai",
                        deployment_type="api",
                        model_name="gpt-4",
                        api_key=openai_api_key
                    )
                    self.logger.info("Successfully initialized OpenAI model")
                except Exception as e:
                    raise RuntimeError(f"Failed to initialize OpenAI model: {str(e)}")
            else:
                raise RuntimeError(
                    "No local model found and no OpenAI API key provided. "
                    "Please either install a local model or provide an OpenAI API key."
                )
        
        # Set up directories and initialize components
        self._setup_directories()
        self.context = AgentContext()
        
        self.logger.info(f"Agent initialized with model: {self.model.model_provider}/{self.model.model_name}")
        self.logger.info(f"Using device: {self.device}")
        
        # Initialize APIs
        self.overture_api = OvertureAPI()
        self.sentinel_api = SentinelAPI()
        self.geocoder = GeoCoderAgent()
        
        # Initialize context and processors
        self.text_processor = TextProcessor()
    
    def _setup_directories(self):
        """Create necessary directories for data storage"""
        for path in ['cache', 'data', 'scenarios']:
            Path(f"./agent_{path}").mkdir(parents=True, exist_ok=True)
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process user query based on context and type
        
        Args:
            query (str): User's input query
            
        Returns:
            Dict[str, Any]: Processed response with relevant data
        """
        # Add to conversation history
        self.context.conversation_history.append({
            "role": "user",
            "content": query,
            "timestamp": datetime.now().isoformat()
        })
        
        # Determine query type and context
        query_type = self._classify_query(query)
        
        try:
            if query_type == "location_query":
                response = await self._handle_location_query(query)
            elif query_type == "future_scenario":
                response = await self._handle_future_scenario(query)
            else:
                response = await self._handle_general_query(query)
            
            # Add response to history
            self.context.conversation_history.append({
                "role": "assistant",
                "content": response["response"],
                "timestamp": datetime.now().isoformat(),
                "metadata": response.get("metadata", {})
            })
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return {
                "error": str(e),
                "response": "I encountered an error processing your request."
            }
    
    def _classify_query(self, query: str) -> str:
        """Classify the type of query"""
        query_lower = query.lower()
        
        # Location-related keywords
        location_keywords = ["where", "location", "place", "area", "region", "city"]
        future_keywords = ["future", "predict", "will", "forecast", "scenario"]
        
        if any(keyword in query_lower for keyword in location_keywords):
            return "location_query"
        elif any(keyword in query_lower for keyword in future_keywords):
            return "future_scenario"
        return "general_query"
    
    async def _handle_location_query(self, query: str) -> Dict[str, Any]:
        """Handle queries requiring location context"""
        # Extract location from query
        location_info = self.geocoder.LocationExtractor(query)
        
        if not location_info:
            return {
                "response": "I couldn't identify a specific location in your query. Could you please specify the location?",
                "metadata": {"query_type": "location_query", "status": "location_needed"}
            }
        
        # Update context
        self.context.location = location_info
        
        # Gather location data
        location_data = await self._gather_location_data(location_info)
        
        # Analyze location data
        analysis = self._analyze_location_data(location_data)
        
        # Generate response
        response = self._generate_location_response(analysis)
        
        return {
            "response": response,
            "metadata": {
                "query_type": "location_query",
                "location": location_info,
                "analysis": analysis
            }
        }
    
    async def _gather_location_data(self, location: Dict[str, Any]) -> Dict[str, Any]:
        """Gather data from various sources for a location"""
        # Create bounding box for location
        bbox = self._create_bbox(location)
        
        # Gather data concurrently
        overture_task = asyncio.create_task(self._get_overture_data(bbox))
        sentinel_task = asyncio.create_task(self._get_sentinel_data(bbox))
        
        # Wait for all data
        overture_data, sentinel_data = await asyncio.gather(
            overture_task,
            sentinel_task
        )
        
        return {
            "overture": overture_data,
            "sentinel": sentinel_data,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _get_overture_data(self, bbox: Dict[str, float]) -> Dict[str, Any]:
        """Get data from Overture Maps"""
        try:
            return await self.overture_api.get_features(
                bbox=bbox,
                themes=["buildings", "places", "transportation"]
            )
        except Exception as e:
            logger.error(f"Error fetching Overture data: {str(e)}")
            return {}
    
    async def _get_sentinel_data(self, bbox: Dict[str, float]) -> Dict[str, Any]:
        """Get satellite data from Sentinel"""
        try:
            return await self.sentinel_api.get_data(
                bbox=bbox,
                cloud_cover=20.0,
                start_date=(datetime.now() - timedelta(days=30)).isoformat(),
                end_date=datetime.now().isoformat()
            )
        except Exception as e:
            logger.error(f"Error fetching Sentinel data: {str(e)}")
            return {}
    
    def _analyze_location_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze gathered location data"""
        analysis = {
            "urban_metrics": self._analyze_urban_features(data.get("overture", {})),
            "environmental_metrics": self._analyze_environmental_data(data.get("sentinel", {})),
            "temporal_patterns": self._analyze_temporal_patterns(data),
            "summary": {}
        }
        
        # Generate summary
        analysis["summary"] = self._generate_location_summary(analysis)
        
        return analysis
    
    def _analyze_urban_features(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze urban features from Overture data"""
        buildings = data.get("buildings", [])
        places = data.get("places", [])
        
        return {
            "building_density": len(buildings) / 1000,  # per km²
            "place_types": self._categorize_places(places),
            "urbanization_level": self._calculate_urbanization_level(data)
        }
    
    def _analyze_environmental_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze environmental metrics from satellite data"""
        return {
            "vegetation_index": self._calculate_vegetation_index(data),
            "urban_change": self._calculate_urban_change(data),
            "environmental_health": self._assess_environmental_health(data)
        }
    
    async def _handle_future_scenario(self, query: str) -> Dict[str, Any]:
        """Handle queries about future scenarios"""
        # Get current location context or extract from query
        location = self.context.location
        if not location:
            location_info = self.geocoder.LocationExtractor(query)
            if location_info:
                location = location_info
            else:
                return {
                    "response": "I need a location context to generate future scenarios. Could you specify a location?",
                    "metadata": {"query_type": "future_scenario", "status": "location_needed"}
                }
        
        # Generate scenarios
        scenarios = await self._generate_future_scenarios(location, query)
        
        # Format response
        response = self._format_scenario_response(scenarios)
        
        return {
            "response": response,
            "metadata": {
                "query_type": "future_scenario",
                "location": location,
                "scenarios": scenarios
            }
        }
    
    async def _generate_future_scenarios(self, location: Dict[str, Any], query: str) -> List[Dict[str, Any]]:
        """Generate possible future scenarios for a location"""
        # Get historical data
        current_data = await self._gather_location_data(location)
        
        # Generate scenarios
        scenarios = []
        
        # Optimistic scenario
        scenarios.append({
            "type": "optimistic",
            "probability": 0.3,
            "timeline": "6 months",
            "changes": self._project_optimistic_changes(current_data),
            "impact_factors": self._identify_impact_factors(current_data, "positive")
        })
        
        # Moderate scenario
        scenarios.append({
            "type": "moderate",
            "probability": 0.5,
            "timeline": "6 months",
            "changes": self._project_moderate_changes(current_data),
            "impact_factors": self._identify_impact_factors(current_data, "neutral")
        })
        
        # Conservative scenario
        scenarios.append({
            "type": "conservative",
            "probability": 0.2,
            "timeline": "6 months",
            "changes": self._project_conservative_changes(current_data),
            "impact_factors": self._identify_impact_factors(current_data, "negative")
        })
        
        return scenarios
    
    async def _handle_general_query(self, query: str) -> Dict[str, Any]:
        """Handle general queries without location context"""
        # Process query with model
        response = self.model.generate_response(
            prompt=query,
            max_length=1000
        )
        
        return {
            "response": response,
            "metadata": {
                "query_type": "general_query",
                "context_used": "conversation_history"
            }
        }
    
    def _create_bbox(self, location: Dict[str, Any], radius_km: float = 1.0) -> Dict[str, float]:
        """Create a bounding box around a location"""
        lat, lon = location["latitude"], location["longitude"]
        # Approximate 1km at equator
        lat_offset = radius_km / 111.32
        lon_offset = radius_km / (111.32 * np.cos(np.radians(lat)))
        
        return {
            "xmin": lon - lon_offset,
            "ymin": lat - lat_offset,
            "xmax": lon + lon_offset,
            "ymax": lat + lat_offset
        }
    
    def _format_scenario_response(self, scenarios: List[Dict[str, Any]]) -> str:
        """Format scenarios into a readable response"""
        response_parts = ["Based on my analysis, here are possible future scenarios:\n"]
        
        for scenario in scenarios:
            response_parts.append(f"\n{scenario['type'].title()} Scenario (Probability: {scenario['probability']*100:.0f}%)")
            response_parts.append(f"Timeline: {scenario['timeline']}")
            response_parts.append("Expected Changes:")
            for change in scenario['changes']:
                response_parts.append(f"- {change}")
            response_parts.append("\nKey Impact Factors:")
            for factor in scenario['impact_factors']:
                response_parts.append(f"- {factor}")
            response_parts.append("")
        
        return "\n".join(response_parts)
    
    def _generate_location_response(self, analysis: Dict[str, Any]) -> str:
        """Generate a natural language response from location analysis"""
        summary = analysis["summary"]
        response_parts = [f"Here's what I found about this location:\n"]
        
        if "urban_character" in summary:
            response_parts.append(f"Urban Character: {summary['urban_character']}")
        
        if "environmental_status" in summary:
            response_parts.append(f"Environmental Status: {summary['environmental_status']}")
        
        if "key_features" in summary:
            response_parts.append("\nKey Features:")
            for feature in summary["key_features"]:
                response_parts.append(f"- {feature}")
        
        if "recommendations" in summary:
            response_parts.append("\nRecommendations:")
            for rec in summary["recommendations"]:
                response_parts.append(f"- {rec}")
        
        return "\n".join(response_parts)

async def main():
    """Run an interactive session with the agent"""
    print("\nInitializing Intelligent Agent...")
    
    # Get OpenAI API key from environment
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        return
    
    agent = IntelligentAgent(openai_api_key=openai_api_key)
    
    print("\nAgent initialized! Type 'quit' to exit.")
    print("Example commands:")
    print("- General query: 'What is sustainable urban development?'")
    print("- Location query: 'Tell me about Central Park, New York'")
    print("- Future scenario: 'What might happen to Silicon Valley in 6 months?'")
    print("="*50)
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if user_input.lower() == 'quit':
                print("\nGoodbye!")
                break
            
            response = await agent.process_query(user_input)
            print("\nAgent:", response["response"])
            
        except Exception as e:
            print(f"\nError: {str(e)}")
            print("Please try again with a different query.")

if __name__ == "__main__":
    asyncio.run(main()) 