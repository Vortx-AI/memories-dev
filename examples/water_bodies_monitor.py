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
from memories.agents.agent_base import BaseAgent
from memories.utils.text import TextProcessor
from memories.data_acquisition.sources.overture_api import OvertureAPI
from memories.data_acquisition.sources.sentinel_api import SentinelAPI
from memories.utils.processors import ImageProcessor, VectorProcessor
from memories.data_acquisition.data_manager import DataManager
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def setup_directories(config):
    """Create all necessary data directories."""
    logger.info("Setting up data directories...")
    
    # Ensure all required paths are in config
    required_paths = {
        'data_root': os.path.join(os.getenv('PROJECT_ROOT', '.'), 'data'),
        'satellite_path': os.path.join(os.getenv('PROJECT_ROOT', '.'), 'data', 'satellite'),
        'overture_path': os.path.join(os.getenv('PROJECT_ROOT', '.'), 'data', 'overture'),
        'processed_path': os.path.join(os.getenv('PROJECT_ROOT', '.'), 'data', 'processed'),
        'cache_path': os.path.join(os.getenv('PROJECT_ROOT', '.'), 'data', 'cache')
    }
    
    # Update config with required paths
    if 'data' not in config.config:
        config.config['data'] = {}
    config.config['data'].update(required_paths)
    
    # Create directories
    for path in config.config['data'].values():
        logger.info(f"Creating directory: {path}")
        Path(path).mkdir(parents=True, exist_ok=True)

class WaterBodyAgent(BaseAgent):
    """Agent specialized in water body analysis."""
    
    def __init__(self, memory_store: MemoryStore, config: Config):
        """Initialize the Water Body Agent.
        
        Args:
            memory_store: Memory store instance
            config: Configuration instance
        """
        super().__init__(name="water_body_agent", memory_store=memory_store)
        self.text_processor = TextProcessor()
        self.image_processor = ImageProcessor()
        self.vector_processor = VectorProcessor()
        self.config = config
        
        # Initialize data manager
        self.data_manager = DataManager(cache_dir=config.config['data']['processed_path'])
        
        # Initialize APIs with config paths
        self.overture_api = OvertureAPI(data_dir=config.config['data']['overture_path'])
        self.sentinel_api = SentinelAPI(data_dir=config.config['data']['satellite_path'])
        
        # Initialize tools
        self._initialize_tools()
    
    def get_capabilities(self) -> List[str]:
        """Return a list of high-level capabilities this agent provides."""
        return [
            "Analyze water bodies using satellite data",
            "Process water quality metrics",
            "Monitor water body changes",
            "Calculate surface area and perimeter",
            "Extract water features from vector data"
        ]
    
    def _initialize_tools(self):
        """Initialize the tools this agent can use."""
        self.register_tool(
            "analyze_water_body",
            self.analyze_water_body,
            "Analyze a water body using satellite and vector data",
            {"bbox"}
        )
        self.register_tool(
            "analyze_quality",
            self.analyze_quality,
            "Analyze water quality using satellite data",
            {"satellite_data"}
        )
        self.register_tool(
            "_process_water_data",
            self._process_water_data,
            "Process water body data to extract key metrics",
            {"data"}
        )
    
    async def process(self, goal: str, **kwargs) -> Dict[str, Any]:
        """Process a goal using this agent."""
        try:
            # Create a plan
            plan = self.plan(goal)
            
            # Execute the plan with the provided arguments
            if goal == "analyze water bodies in area":
                return await self.analyze_water_body(**kwargs)
            
            return {
                "status": "error",
                "error": "Unsupported goal",
                "data": None
            }
            
        except Exception as e:
            self.logger.error(f"Error in process: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "data": None
            }
    
    async def analyze_water_body(self, bbox, start_date=None, end_date=None):
        """Analyze a water body using satellite and vector data."""
        logger.info(f"analyze_water_body - Input bbox: {bbox}, type: {type(bbox)}")
        
        # Prepare data
        data = await self.data_manager.prepare_training_data(
            bbox=bbox,
            start_date=start_date,
            end_date=end_date
        )
        
        # Process data
        insights = await self._process_water_data(data)
        
        # Extract quality metrics
        quality_metrics = insights.get("quality_metrics", {})
        if not quality_metrics:
            quality_metrics = {
                "clarity": 0.0,
                "water_presence": 0.0,
                "variability": 0.0
            }
        
        return {
            "surface_area": insights.get("surface_area", 0.0),
            "perimeter": insights.get("perimeter", 0.0),
            "water_features": insights.get("water_features", 0),
            "ndwi_mean": insights.get("ndwi_mean", 0.0),
            "quality_metrics": quality_metrics
        }
    
    async def _process_water_data(self, data):
        """Process water body data to extract key metrics."""
        logger.info("\n=== Processing Water Body Data ===")
        
        if not data or "vector_data" not in data:
            logger.warning("No vector data available")
            return {
                "location": f"Bbox: {data.get('bbox', 'unknown')}",
                "surface_area": 0.0,
                "perimeter": 0.0,
                "water_features": 0,
                "quality_metrics": {},
                "ndwi_mean": 0.0  # Default float value
            }
            
        water_features = []
        total_area = 0.0
        total_perimeter = 0.0
        
        # Process Overture water features from base theme
        if "overture" in data["vector_data"] and "base" in data["vector_data"]["overture"]:
            base_features = data["vector_data"]["overture"]["base"]
            # Filter for water features
            water_features.extend([
                feature for feature in base_features 
                if feature.get("feature_type", "").lower() in ["water", "lake", "river", "reservoir"]
            ])
        
        # Process OSM water features
        if "osm" in data["vector_data"] and "waterways" in data["vector_data"]["osm"]:
            water_features.extend(data["vector_data"]["osm"]["waterways"])
            
        # Calculate total area and perimeter
        for feature in water_features:
            # Handle area from properties
            if "properties" in feature and "area" in feature["properties"]:
                total_area += feature["properties"]["area"]
            
            # Calculate area and perimeter from geometry if available
            if "geometry" in feature:
                if feature["geometry"]["type"] == "Polygon":
                    coords = feature["geometry"]["coordinates"][0]  # Outer ring
                    # Calculate perimeter
                    for i in range(len(coords)-1):
                        x1, y1 = coords[i]
                        x2, y2 = coords[i+1]
                        total_perimeter += ((x2-x1)**2 + (y2-y1)**2)**0.5
                    
                    # Calculate area if not in properties
                    if "area" not in feature.get("properties", {}):
                        # Simple area calculation for small areas (not geodesic)
                        area = 0
                        for i in range(len(coords)-1):
                            x1, y1 = coords[i]
                            x2, y2 = coords[i+1]
                            area += x1*y2 - x2*y1
                        total_area += abs(area) / 2
        
        logger.info(f"Found {len(water_features)} water features")
        logger.info(f"Total water area: {total_area:.2f} sq km")
        logger.info(f"Total perimeter: {total_perimeter:.2f} km")
        
        # Process satellite data if available
        quality_metrics = {}
        ndwi_mean = 0.0  # Default float value
        if "satellite_data" in data and "pc" in data["satellite_data"]:
            try:
                quality_metrics = await self.analyze_quality(data["satellite_data"])
                if "ndwi_mean" in quality_metrics:
                    ndwi_mean = quality_metrics.pop("ndwi_mean") or 0.0
            except Exception as e:
                logger.warning(f"Error analyzing water quality: {str(e)}")
                logger.warning("No satellite data available")
        else:
            logger.warning("No satellite data available")
            
        return {
            "location": f"Bbox: {data.get('bbox', 'unknown')}",
            "surface_area": total_area,
            "perimeter": total_perimeter,
            "water_features": len(water_features),
            "quality_metrics": quality_metrics,
            "ndwi_mean": ndwi_mean
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

    async def analyze_quality(self, satellite_data):
        """Analyze water quality using satellite data."""
        if not satellite_data or "pc" not in satellite_data:
            return {
                "turbidity": 0.0,
                "chlorophyll": 0.0,
                "temperature": 0.0,
                "ndwi_mean": 0.0,
                "clarity": 0.0,
                "water_presence": 0.0,
                "variability": 0.0
            }
            
        try:
            # Extract Sentinel-2 data
            if "sentinel-2-l2a" in satellite_data["pc"]:
                scenes = satellite_data["pc"]["sentinel-2-l2a"]
                if scenes and len(scenes) > 0:
                    scene = scenes[0]  # Use most recent scene
                    bands = scene.get("data", None)
                    
                    if bands is not None and len(bands) >= 4:
                        # Calculate NDWI using green (band 3) and NIR (band 8)
                        green = bands[2]  # Band 3 (green)
                        nir = bands[7]    # Band 8 (NIR)
                        
                        # Ensure bands are not empty
                        if green is not None and nir is not None:
                            ndwi = (green - nir) / (green + nir + 1e-6)  # Add small epsilon to avoid division by zero
                            ndwi_mean = float(np.nanmean(ndwi))
                            
                            # Calculate other metrics
                            turbidity = float(np.nanmean(bands[1]))  # Use blue band for turbidity
                            chlorophyll = float(np.nanmean(bands[3]))  # Use red band for chlorophyll
                            temperature = 0.0  # Sentinel-2 doesn't have thermal bands
                            
                            # Calculate additional quality metrics
                            clarity = float(np.nanmean(bands[1] / (bands[2] + 1e-6)))  # Blue/Green ratio
                            water_presence = float(np.nanmean(ndwi > 0))  # Fraction of pixels with water
                            variability = float(np.nanstd(ndwi))  # Standard deviation of NDWI
                            
                            return {
                                "turbidity": turbidity,
                                "chlorophyll": chlorophyll,
                                "temperature": temperature,
                                "ndwi_mean": ndwi_mean,
                                "clarity": clarity,
                                "water_presence": water_presence,
                                "variability": variability
                            }
        except Exception as e:
            logger.warning(f"Error calculating water quality metrics: {str(e)}")
            
        return {
            "turbidity": 0.0,
            "chlorophyll": 0.0,
            "temperature": 0.0,
            "ndwi_mean": 0.0,
            "clarity": 0.0,
            "water_presence": 0.0,
            "variability": 0.0
        }

async def main():
    """Run the water bodies monitor example."""
    # Load configuration
    config = Config()
    
    # Setup directories
    setup_directories(config)
    
    # Initialize memory store with proper configuration
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
    
    # Update config with memory settings
    config.config['redis'] = {
        'url': redis_url,
        'db': 0
    }
    config.config['memory'] = {
        'hot_size': 1000,
        'warm_size': 1000,
        'cold_size': 1000
    }
    
    # Initialize memory store with config
    memory_store = MemoryStore(config)
    
    # Initialize water body agent
    agent = WaterBodyAgent(memory_store, config)
    
    # Define area of interest (Bangalore lakes)
    bbox = box(77.4, 12.8, 77.8, 13.2)
    bbox_dict = {
        'xmin': bbox.bounds[0],
        'ymin': bbox.bounds[1],
        'xmax': bbox.bounds[2],
        'ymax': bbox.bounds[3]
    }
    
    # Define time range (last 30 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    try:
        # Download Overture data first
        print("\nDownloading Overture data for the specified area...")
        download_results = agent.overture_api.download_data(bbox_dict)
        
        if download_results.get('base', False):
            print("✅ Successfully downloaded base theme data (includes water features)")
        else:
            print("❌ Failed to download base theme data")
            
        # Process water bodies
        print("\nAnalyzing water bodies...")
        insights = await agent.process(
            goal="analyze water bodies in area",
            bbox=bbox,
            start_date=start_date,
            end_date=end_date
        )
        
        # Print results
        print("\nWater Bodies Analysis Results:")
        print("="*50)
        print(f"Surface Area: {insights.get('surface_area', 0):.2f} sq km")
        print(f"Perimeter: {insights.get('perimeter', 0):.2f} km")
        print(f"Water Features: {insights.get('water_features', 0)}")
        print(f"NDWI Mean: {insights.get('ndwi_mean', 0):.3f}")
        
        quality = insights.get('quality_metrics', {})
        print("\nWater Quality Metrics:")
        print("-"*30)
        for metric, value in quality.items():
            print(f"{metric.title()}: {value:.3f}")
            
    finally:
        # Clean up memory store (non-async)
        if hasattr(memory_store, 'cleanup'):
            memory_store.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 