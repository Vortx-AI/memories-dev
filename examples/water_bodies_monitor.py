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
        
        # Initialize APIs with config paths
        self.overture_api = OvertureAPI(data_dir=config.config['data']['overture_path'])
        self.sentinel_api = SentinelAPI(data_dir=config.config['data']['satellite_path'])
    
    async def process(self, bbox, start_date, end_date):
        """Process water body data.
        
        This is the main processing method required by BaseAgent.
        """
        return await self.analyze_water_body(bbox, start_date, end_date)
    
    async def analyze_water_body(self, bbox, start_date, end_date):
        """Analyze water body data and store insights."""
        logger.info(f"analyze_water_body - Input bbox: {bbox}, type: {type(bbox)}")
        
        # Use bbox directly if it's already a dictionary, otherwise convert it
        bbox_dict = bbox if isinstance(bbox, dict) else {
            'xmin': bbox[0],
            'ymin': bbox[1],
            'xmax': bbox[2],
            'ymax': bbox[3]
        }
        
        try:
            # Download Overture data
            logger.info("\n=== Downloading Overture Maps Data ===")
            overture_results = self.overture_api.download_data(bbox_dict)
            
            if all(overture_results.values()):
                logger.info("\nSuccessfully downloaded all Overture themes:")
                for theme, success in overture_results.items():
                    logger.info(f"- {theme}: {'✓' if success else '✗'}")
            else:
                logger.info("\nSome Overture downloads failed:")
                for theme, success in overture_results.items():
                    logger.info(f"- {theme}: {'✓' if success else '✗'}")
            
            # Download satellite data
            logger.info("\n=== Downloading Satellite Imagery ===")
            logger.info(f"Searching for imagery between {start_date} and {end_date}")
            logger.info(f"Using bbox: {bbox_dict}")
            logger.info(f"Cloud cover threshold: 50.0%")
            
            satellite_results = await self.sentinel_api.download_data(
                bbox=bbox_dict,
                start_date=datetime.strptime(start_date, "%Y-%m-%d"),
                end_date=datetime.strptime(end_date, "%Y-%m-%d"),
                cloud_cover=50.0,  # Increase cloud cover threshold to find more imagery
                bands={
                    "B04": "Red",
                    "B08": "NIR",
                    "B11": "SWIR"
                }
            )
            
            if satellite_results.get("success"):
                logger.info("\nSuccessfully downloaded satellite data:")
                metadata = satellite_results["metadata"]
                logger.info(f"- Scene ID: {metadata['scene_id']}")
                logger.info(f"- Date: {metadata['datetime']}")
                logger.info(f"- Cloud cover: {metadata['cloud_cover']}%")
                logger.info(f"- Bands: {', '.join(metadata['bands_downloaded'])}")
            else:
                logger.info("\nSatellite data download failed:")
                logger.info(f"- Error: {satellite_results.get('error')}")
                if 'failed_bands' in satellite_results:
                    logger.info(f"- Failed bands: {', '.join(satellite_results['failed_bands'])}")
                if 'parameters' in satellite_results:
                    logger.info("Search parameters:")
                    for key, value in satellite_results['parameters'].items():
                        logger.info(f"- {key}: {value}")
            
            # Process the data
            insights = await self._process_water_data({
                "satellite_data": satellite_results,
                "vector_data": overture_results,
                "bbox": bbox_dict
            })
            
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
            
        except asyncio.CancelledError:
            logger.info("\nAnalysis cancelled by user")
            raise
        except Exception as e:
            logger.error(f"Error in analyze_water_body: {str(e)}")
            return {
                "error": str(e),
                "location": f"Bbox: {bbox_dict}",
                "surface_area": 0,
                "ndwi_mean": None,
                "quality_metrics": self._analyze_quality(None),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _process_water_data(self, data):
        """Process satellite and vector data for water body analysis."""
        logger.info("\n=== Processing Water Body Data ===")
        
        satellite_data = data["satellite_data"]
        vector_data = data["vector_data"]
        
        # Extract water bodies from vector data
        water_features = []
        for theme, features in vector_data.items():
            if features and theme in ['waterways', 'water']:
                water_features.extend(features)
        
        logger.info(f"Found {len(water_features)} water features")
        water_area = sum(feature.get("area", 0) for feature in water_features)
        logger.info(f"Total water area: {water_area:.2f} sq km")
        
        # Analyze satellite imagery
        if satellite_data.get("success"):
            logger.info("\nProcessing satellite imagery...")
            metadata = satellite_data["metadata"]
            data_dir = Path(satellite_data["data_dir"])
            
            # Load the bands
            try:
                import rasterio
                
                # Try loading .tif files
                red_band = None
                nir_band = None
                
                red_file = data_dir / "B04.tif"
                nir_file = data_dir / "B08.tif"
                
                logger.info(f"Looking for band files:")
                logger.info(f"Red band file: {red_file} (exists: {red_file.exists()})")
                logger.info(f"NIR band file: {nir_file} (exists: {nir_file.exists()})")
                
                if red_file.exists() and nir_file.exists():
                    logger.info("Loading bands from .tif files...")
                    with rasterio.open(red_file) as src:
                        red_band = src.read(1)
                    with rasterio.open(nir_file) as src:
                        nir_band = src.read(1)
                else:
                    # Try loading .npy files as fallback
                    logger.info("Loading bands from .npy files...")
                    red_npy = data_dir / "B04.npy"
                    nir_npy = data_dir / "B08.npy"
                    logger.info(f"Red band NPY file: {red_npy} (exists: {red_npy.exists()})")
                    logger.info(f"NIR band NPY file: {nir_npy} (exists: {nir_npy.exists()})")
                    
                    red_band = np.load(red_npy) if red_npy.exists() else None
                    nir_band = np.load(nir_npy) if nir_npy.exists() else None
                
                if red_band is not None and nir_band is not None:
                    logger.info("Calculating NDWI...")
                    logger.info(f"Red band shape: {red_band.shape}")
                    logger.info(f"NIR band shape: {nir_band.shape}")
                    
                    ndwi = self.image_processor.calculate_ndwi(
                        np.stack([red_band, nir_band]),
                        green_band=0,  # Index for red band (using as proxy for green)
                        nir_band=1     # Index for NIR band
                    )
                    logger.info(f"NDWI shape: {ndwi.shape}")
                    logger.info(f"NDWI statistics - min: {ndwi.min():.2f}, max: {ndwi.max():.2f}, mean: {ndwi.mean():.2f}")
                    
                    water_quality = self._analyze_quality(ndwi)
                    logger.info("\nWater quality metrics:")
                    for metric, value in water_quality.items():
                        if value is not None:
                            logger.info(f"- {metric}: {value:.2f}")
                else:
                    logger.warning("Required bands not found")
                    ndwi = None
                    water_quality = self._analyze_quality(None)
            except Exception as e:
                logger.error(f"Error processing satellite data: {str(e)}")
                ndwi = None
                water_quality = self._analyze_quality(None)
        else:
            logger.warning("No satellite data available")
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