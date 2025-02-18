#!/usr/bin/env python3
"""
Global Water Bodies Monitor Example
---------------------------------
This example demonstrates how to use the Memories-Dev framework to monitor
and analyze changes in global water bodies using satellite data.
"""

import os
import logging
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from shapely.geometry import box
from memories import MemoryStore, Config
from memories.core import HotMemory, WarmMemory, ColdMemory
from memories.agents import BaseAgent
from memories.utils.text import TextProcessor
from memories.data_acquisition.data_manager import DataManager
from memories.utils.processors import ImageProcessor, VectorProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class WaterBodyAgent(BaseAgent):
    """Agent specialized in water body analysis."""
    
    def __init__(self, memory_store: MemoryStore):
        super().__init__(memory_store)
        self.text_processor = TextProcessor()
        self.data_manager = DataManager(
            cache_dir=str(Path.home() / ".memories" / "cache")
        )
        self.image_processor = ImageProcessor()
        self.vector_processor = VectorProcessor()
    
    async def process(self, bbox, start_date, end_date):
        """Process water body data.
        
        This is the main processing method required by BaseAgent.
        """
        return await self.analyze_water_body(bbox, start_date, end_date)
    
    async def analyze_water_body(self, bbox, start_date, end_date):
        """Analyze water body data and store insights."""
        # Get satellite and vector data
        data = await self.data_manager.prepare_training_data(
            bbox=bbox,
            start_date=start_date,
            end_date=end_date,
            satellite_collections=["sentinel-2-l2a"],
            vector_layers=["water"],
            cloud_cover=20.0
        )
        
        # Process the data
        insights = await self._process_water_data(data)
        
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
    
    async def _process_water_data(self, data):
        """Process satellite and vector data for water body analysis."""
        satellite_data = data["satellite_data"]
        vector_data = data["vector_data"]
        
        # Extract water bodies from OSM data
        water_features = vector_data["osm"].get("waterways", [])
        water_area = sum(feature["properties"].get("area", 0) for feature in water_features)
        
        # Analyze satellite imagery
        if "pc" in satellite_data and "sentinel-2-l2a" in satellite_data["pc"]:
            sentinel_data = satellite_data["pc"]["sentinel-2-l2a"][0]
            ndwi = self.image_processor.calculate_ndwi(
                sentinel_data["data"],
                green_band=1,  # Index for green band
                nir_band=3    # Index for NIR band
            )
            water_quality = self._analyze_quality(ndwi)
        else:
            ndwi = None
            water_quality = self._analyze_quality(None)
        
        return {
            "location": f"Bbox: {data['bbox']}",
            "surface_area": water_area,
            "ndwi_mean": float(np.mean(ndwi)) if ndwi is not None else None,
            "quality_metrics": water_quality,
            "timestamp": datetime.now().isoformat()
        }
    
    def _is_significant_change(self, insights):
        """Determine if the change is significant."""
        if "ndwi_mean" in insights and insights["ndwi_mean"] is not None:
            return abs(insights["ndwi_mean"]) > 0.3  # Significant water presence
        return False
    
    def _analyze_quality(self, ndwi_data):
        """Analyze water quality metrics using NDWI data."""
        if ndwi_data is not None:
            return {
                "clarity": float(np.percentile(ndwi_data, 75)),
                "water_presence": float(np.mean(ndwi_data > 0)),
                "variability": float(np.std(ndwi_data))
            }
        return {
            "clarity": None,
            "water_presence": None,
            "variability": None
        }

async def main():
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
    
    # Define monitoring locations (bounding boxes)
    locations = [
        {
            "name": "Lake Victoria",
            "bbox": [32.0, -1.0, 34.0, 0.0]  # Simplified bbox for example
        },
        {
            "name": "Lake Superior",
            "bbox": [-87.0, 46.5, -84.0, 48.5]
        }
    ]
    
    # Set time range for analysis
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    # Monitor water bodies
    for location in locations:
        logger.info(f"Analyzing water body: {location['name']}")
        
        try:
            # Analyze and store results
            insights = await agent.analyze_water_body(
                bbox=location["bbox"],
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d")
            )
            
            # Log results
            logger.info(f"Analysis results for {location['name']}:")
            logger.info(f"Surface Area: {insights['surface_area']:.2f} sq km")
            if insights['ndwi_mean'] is not None:
                logger.info(f"NDWI Mean: {insights['ndwi_mean']:.2f}")
            logger.info("Quality Metrics:")
            for metric, value in insights['quality_metrics'].items():
                if value is not None:
                    logger.info(f"  - {metric}: {value:.2f}")
            logger.info("-" * 50)
            
        except Exception as e:
            logger.error(f"Error analyzing {location['name']}: {str(e)}")
    
    # Demonstrate memory retrieval
    hot_memories = memory_store.hot_memory.retrieve_all()
    logger.info(f"\nSignificant changes detected: {len(hot_memories)}")
    
    # Clean up (optional)
    memory_store.clear()

if __name__ == "__main__":
    asyncio.run(main()) 