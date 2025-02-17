#!/usr/bin/env python3
"""
Global Water Bodies Monitor Example
---------------------------------
This example demonstrates how to use the Memories-Dev framework to monitor
and analyze changes in global water bodies using satellite data.
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

class WaterBodyAgent(BaseAgent):
    """Agent specialized in water body analysis."""
    
    def __init__(self, memory_store: MemoryStore):
        super().__init__(name="water_body_agent")
        self.memory_store = memory_store
        self.text_processor = TextProcessor()
    
    def analyze_water_body(self, data):
        """Analyze water body data and store insights."""
        # Process the data
        insights = self._process_water_data(data)
        
        # Store in different memory layers based on importance
        if self._is_significant_change(insights):
            self.memory_store.hot_memory.store({
                "timestamp": datetime.now().isoformat(),
                "type": "significant_change",
                "data": insights
            })
        else:
            self.memory_store.warm_memory.store({
                "timestamp": datetime.now().isoformat(),
                "type": "regular_update",
                "data": insights
            })
        
        return insights
    
    def _process_water_data(self, data):
        """Process raw water body data."""
        # Simulate processing of satellite data
        return {
            "location": data["location"],
            "surface_area": data["area"],
            "change_rate": self._calculate_change_rate(data),
            "quality_metrics": self._analyze_quality(data)
        }
    
    def _is_significant_change(self, insights):
        """Determine if the change is significant."""
        return abs(insights["change_rate"]) > 0.1  # 10% change threshold
    
    def _calculate_change_rate(self, data):
        """Calculate rate of change in water body."""
        # Simulate calculation
        return np.random.normal(0, 0.05)  # Random change for demo
    
    def _analyze_quality(self, data):
        """Analyze water quality metrics."""
        return {
            "clarity": np.random.uniform(0.5, 1.0),
            "pollution_index": np.random.uniform(0, 0.3),
            "vegetation_density": np.random.uniform(0.2, 0.8)
        }

def simulate_satellite_data(location):
    """Simulate satellite data for demonstration."""
    return {
        "location": location,
        "area": np.random.uniform(100, 1000),
        "timestamp": datetime.now(),
        "raw_measurements": {
            "spectral_data": np.random.random(10),
            "temperature": np.random.uniform(15, 25),
            "cloud_cover": np.random.uniform(0, 0.3)
        }
    }

def main():
    """Main execution function."""
    # Initialize memory system
    config = Config(
        storage_path="./water_bodies_data",
        hot_memory_size=100,
        warm_memory_size=1000,
        cold_memory_size=10000
    )
    
    memory_store = MemoryStore(config)
    
    # Initialize agent
    agent = WaterBodyAgent(memory_store)
    
    # Simulate monitoring multiple locations
    locations = [
        "Lake Victoria, Africa",
        "Lake Superior, North America",
        "Caspian Sea, Asia",
        "Lake Baikal, Russia"
    ]
    
    # Monitor water bodies
    for location in locations:
        logger.info(f"Analyzing water body: {location}")
        
        # Simulate satellite data collection
        data = simulate_satellite_data(location)
        
        # Analyze and store results
        insights = agent.analyze_water_body(data)
        
        # Log results
        logger.info(f"Analysis results for {location}:")
        logger.info(f"Surface Area: {insights['surface_area']:.2f} sq km")
        logger.info(f"Change Rate: {insights['change_rate']*100:.2f}%")
        logger.info("Quality Metrics:")
        for metric, value in insights['quality_metrics'].items():
            logger.info(f"  - {metric}: {value:.2f}")
        logger.info("-" * 50)
    
    # Demonstrate memory retrieval
    hot_memories = memory_store.hot_memory.retrieve_all()
    logger.info(f"\nSignificant changes detected: {len(hot_memories)}")
    
    # Clean up (optional)
    memory_store.clear()

if __name__ == "__main__":
    main() 