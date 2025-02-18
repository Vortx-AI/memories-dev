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
from memories.data_acquisition.sources.overture_api import OvertureAPI
from memories.data_acquisition.sources.sentinel_api import SentinelAPI
from memories.utils.processors import ImageProcessor, VectorProcessor
from memories.data_acquisition.data_manager import DataManager

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def setup_directories(config):
    """Create all necessary data directories."""
    logger.info("Setting up data directories...")
    for path in config.config['data'].values():
        logger.info(f"Creating directory: {path}")
        Path(path).mkdir(parents=True, exist_ok=True)
    
    # Create additional directories for satellite and vector data
    satellite_dir = Path(config.config['data']['satellite_path'])
    overture_dir = Path(config.config['data']['overture_path'])
    
    logger.info(f"Creating satellite directory: {satellite_dir}")
    satellite_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Creating Overture directory: {overture_dir}")
    overture_dir.mkdir(parents=True, exist_ok=True)

class WaterBodyAgent(BaseAgent):
    """Agent specialized in water body analysis."""
    
    def __init__(self, memory_store: MemoryStore, config: Config):
        super().__init__(memory_store)
        self.text_processor = TextProcessor()
        self.image_processor = ImageProcessor()
        self.vector_processor = VectorProcessor()
        self.config = config
        
        # Initialize data manager
        self.data_manager = DataManager(cache_dir=config.config['data']['processed_path'])
        
        # Initialize APIs with config paths
        self.overture_api = OvertureAPI(data_dir=config.config['data']['overture_path'])
        self.sentinel_api = SentinelAPI(data_dir=config.config['data']['satellite_path'])
    
    async def process(self, bbox, start_date, end_date):
        """Process water body data.
        
        This is the main processing method required by BaseAgent.
        """
        return await self.analyze_water_body(bbox, start_date, end_date)
    
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
        
        # Process OSM water features
        if "osm" in data["vector_data"] and "waterways" in data["vector_data"]["osm"]:
            water_features = data["vector_data"]["osm"]["waterways"]
            
            # Calculate total area and perimeter
            for feature in water_features:
                if "properties" in feature and "area" in feature["properties"]:
                    total_area += feature["properties"]["area"]
                    
                if "geometry" in feature and feature["geometry"]["type"] == "Polygon":
                    coords = feature["geometry"]["coordinates"][0]  # Outer ring
                    # Calculate perimeter as sum of distances between consecutive points
                    for i in range(len(coords)-1):
                        x1, y1 = coords[i]
                        x2, y2 = coords[i+1]
                        total_perimeter += ((x2-x1)**2 + (y2-y1)**2)**0.5
        
        logger.info(f"Found {len(water_features)} water features")
        logger.info(f"Total water area: {total_area:.2f} sq km")
        
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
    """Main execution function."""
    try:
        # Initialize memory system
        config = Config(config_path="examples/config/db_config.yml")  # Updated config path
        setup_directories(config)
        
        memory_store = MemoryStore(config)
        
        # Initialize agent
        agent = WaterBodyAgent(memory_store, config)
        
        # Define monitoring locations (bounding boxes)
        locations = [
            {
                "name": "Lake Victoria",
                "bbox": {
                    "xmin": 32.0,
                    "ymin": -1.0,
                    "xmax": 34.0,
                    "ymax": 0.0
                }
            },
            {
                "name": "Lake Superior",
                "bbox": {
                    "xmin": -87.0,
                    "ymin": 46.5,
                    "xmax": -84.0,
                    "ymax": 48.5
                }
            }
        ]
        
        # Set time range for analysis
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)  # Increase to 90 days to find more imagery
        
        # Monitor water bodies
        for location in locations:
            logger.info(f"Analyzing water body: {location['name']}")
            logger.info(f"Location bbox: {location['bbox']}, type: {type(location['bbox'])}")
            
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
                continue  # Continue with next location even if one fails
        
        # Demonstrate memory retrieval
        hot_memories = memory_store.hot_memory.retrieve_all()
        logger.info(f"\nSignificant changes detected: {len(hot_memories)}")
        
        # Clean up (optional)
        memory_store.clear()
        
    except KeyboardInterrupt:
        logger.info("\nScript interrupted by user. Cleaning up...")
        try:
            memory_store.clear()
        except:
            pass
    except Exception as e:
        logger.error(f"Unexpected error in main: {str(e)}")
    finally:
        logger.info("Script completed.")

if __name__ == "__main__":
    asyncio.run(main()) 