"""Memory retrieval functionality for querying from different memory tiers."""

import logging
from typing import Dict, Any, Optional, List, Union, Tuple
import pandas as pd
import os
from pathlib import Path
import duckdb
# Move this to a lazy import to avoid circular dependency
# from memories.core.cold import Config
import json
import glob
import time
import numpy as np
# Remove direct imports to avoid circular dependencies
# from memories.core.red_hot import RedHotMemory
from sentence_transformers import SentenceTransformer
from memories.core.memory_manager import MemoryManager
from memories.core.glacier.factory import create_connector
# Remove direct imports to avoid circular dependencies
# from memories.core.hot import HotMemory
# from memories.core.warm import WarmMemory
# from memories.core.red_hot import RedHotMemory
# from memories.core.cold import ColdMemory
# from memories.core.glacier.artifacts.overture import OvertureConnector
# from memories.core.glacier.artifacts.sentinel import SentinelConnector
from datetime import datetime, timedelta

# Initialize GPU support flags
HAS_CUDF = False
HAS_CUSPATIAL = False
cudf = None
cuspatial = None

# Try importing GPU libraries
try:
    import cudf
    import cuspatial
    import cupy
    # Try to get CUDA device to confirm GPU is actually available
    cupy.cuda.Device(0).compute_capability
    HAS_CUDF = True
    HAS_CUSPATIAL = True
except (ImportError, AttributeError, Exception):
    pass

logger = logging.getLogger(__name__)

class MemoryRetrieval:
    """Memory retrieval class for querying from different memory tiers."""
    
    def __init__(self):
        """Initialize memory retrieval system."""
        self.logger = logging.getLogger(__name__)
        self.memory_manager = MemoryManager()
        
        # Lazy imports to avoid circular dependencies
        from memories.core.cold import Config
        self.config = Config()
        
        # Initialize memory tiers as None - will be created on demand
        self._hot_memory = None
        self._warm_memory = None
        self._cold_memory = None
        self._red_hot_memory = None
        self._glacier_memory = {}  # Initialize as empty dictionary
        
        # Initialize connectors as None - will be created on demand
        self._overture_connector = None
        self._sentinel_connector = None

    def _init_hot(self) -> None:
        """Initialize hot memory on demand."""
        if not self._hot_memory:
            from memories.core.hot import HotMemory
            self._hot_memory = HotMemory()

    def _init_warm(self) -> None:
        """Initialize warm memory on demand."""
        if not self._warm_memory:
            from memories.core.warm import WarmMemory
            self._warm_memory = WarmMemory()

    def _init_cold(self) -> None:
        """Initialize cold memory on demand."""
        if not self._cold_memory:
            from memories.core.cold import ColdMemory
            self._cold_memory = ColdMemory()

    def _init_red_hot(self) -> None:
        """Initialize red hot memory on demand."""
        if not self._red_hot_memory:
            from memories.core.red_hot import RedHotMemory
            self._red_hot_memory = RedHotMemory()
            
    def _init_overture_connector(self) -> None:
        """Initialize Overture connector on demand."""
        if not self._overture_connector:
            from memories.core.glacier.artifacts.overture import OvertureConnector
            self._overture_connector = OvertureConnector()
            
    def _init_sentinel_connector(self) -> None:
        """Initialize Sentinel connector on demand."""
        if not self._sentinel_connector:
            from memories.core.glacier.artifacts.sentinel import SentinelConnector
            self._sentinel_connector = SentinelConnector()

    def _get_glacier_connector(self, source: str):
        """Get or create glacier connector for specific source."""
        if source not in self._glacier_memory:
            self._glacier_memory[source] = create_connector(source)
        return self._glacier_memory[source]

    async def retrieve(
        self,
        from_tier: str,
        source: str,
        spatial_input_type: str,
        spatial_input: Union[List[float], str, Dict[str, float]],
        tags: Any = None,
        temporal_input: Dict[str, datetime] = None  # Added temporal input for Sentinel
    ) -> Any:
        """
        Retrieve data from specified memory tier.
        
        Args:
            from_tier: Memory tier to retrieve from ("glacier", "cold", "warm", "hot", "sensory")
            source: Data source type ("osm", "sentinel", "overture", etc.)
            spatial_input_type: Type of spatial input ("bbox", "address", etc.)
            spatial_input: Spatial input data
            tags: Optional tags for filtering
            temporal_input: Optional temporal input for filtering

        Returns:
            Retrieved data

        Raises:
            ValueError: If the tier is invalid or if the spatial input type is unsupported
        """
        valid_tiers = ["glacier", "cold", "warm", "hot", "sensory"]
        if from_tier not in valid_tiers:
            raise ValueError(f"Invalid tier: {from_tier}. Must be one of {valid_tiers}")

        try:
            if from_tier == "glacier":
                result = await self._retrieve_from_glacier(source, spatial_input_type, spatial_input, tags, temporal_input)
                if result is None:
                    logger.error(f"Failed to retrieve data from {from_tier} tier")
                return result
            elif from_tier == "cold":
                return await self._retrieve_from_cold(spatial_input_type, spatial_input, tags)
            elif from_tier == "warm":
                return await self._retrieve_from_warm(spatial_input_type, spatial_input, tags)
            elif from_tier == "hot":
                return await self._retrieve_from_hot(spatial_input_type, spatial_input, tags)
            elif from_tier == "sensory":
                return await self._retrieve_from_red_hot(spatial_input_type, spatial_input, tags)
        except ValueError as e:
            # Re-raise ValueError exceptions (like unsupported spatial input type)
            raise
        except Exception as e:
            logger.error(f"Error retrieving from {from_tier} tier: {e}")
            return None

    async def _retrieve_from_glacier(
        self,
        source: str,
        spatial_input_type: str,
        spatial_input: Union[List[float], str, Dict[str, float]],
        tags: Any = None,
        temporal_input: Dict[str, datetime] = None
    ) -> Any:
        """
        Retrieve data from glacier storage.

        Args:
            source: Data source type ("osm", "sentinel", "overture", etc.)
            spatial_input_type: Type of spatial input ("bbox", "address", etc.)
            spatial_input: Spatial input data
            tags: Optional tags for filtering
            temporal_input: Optional temporal input for filtering

        Returns:
            Retrieved data

        Raises:
            ValueError: If the source is invalid or if the spatial input type is unsupported
        """
        try:
            connector = self._get_glacier_connector(source)
            if not connector:
                raise ValueError(f"Failed to initialize connector for source: {source}")

            if source == "osm":
                if spatial_input_type not in ["bbox", "address"]:
                    logger.error(f"Unsupported spatial input type for OSM: {spatial_input_type}")
                    raise ValueError(f"Unsupported spatial input type for OSM: {spatial_input_type}")

                # Convert spatial input to bbox format if needed
                if isinstance(spatial_input, (list, tuple)):
                    bbox = {
                        "xmin": spatial_input[0],  # West
                        "ymin": spatial_input[1],  # South
                        "xmax": spatial_input[2],  # East
                        "ymax": spatial_input[3]   # North
                    }
                else:
                    bbox = spatial_input

                # Get data
                result = await connector.get_data(
                    spatial_input=bbox,
                    spatial_input_type=spatial_input_type,
                    tags=tags
                )

                return result

            elif source == "planetary":
                if spatial_input_type != "bbox":
                    logger.error(f"Unsupported spatial input type for Planetary: {spatial_input_type}")
                    raise ValueError(f"Unsupported spatial input type for Planetary: {spatial_input_type}")

                # Convert spatial input to bbox format if needed
                if isinstance(spatial_input, (list, tuple)):
                    bbox = [
                        spatial_input[0],  # West
                        spatial_input[1],  # South
                        spatial_input[2],  # East
                        spatial_input[3]   # North
                    ]
                else:
                    bbox = [
                        spatial_input["xmin"],  # West
                        spatial_input["ymin"],  # South
                        spatial_input["xmax"],  # East
                        spatial_input["ymax"]   # North
                    ]

                # Set default temporal range if not provided
                if not temporal_input:
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=90)
                else:
                    start_date = temporal_input.get('start_date', datetime.now() - timedelta(days=90))
                    end_date = temporal_input.get('end_date', datetime.now())

                # Set default collection if not specified in tags
                if tags is None:
                    tags = ["sentinel-2-l2a"]
                collection = tags[0] if tags else "sentinel-2-l2a"

                # Search for items
                items = await connector.search(
                    bbox=bbox,
                    start_date=start_date.isoformat(),
                    end_date=end_date.isoformat(),
                    collection=collection,
                    cloud_cover=20.0
                )

                if not items:
                    return {
                        "status": "error",
                        "message": "No items found"
                    }

                # Process first item
                item = items[0]
                bands = ["B02", "B03", "B04", "B08"]  # Default bands for Sentinel-2

                # Convert pystac Item to dictionary
                item_dict = {
                    "id": item.id,
                    "datetime": item.datetime.isoformat(),
                    "bbox": item.bbox,
                    "properties": item.properties
                }

                # Create result structure
                result = {
                    collection: {
                        "status": "success",
                        "data": {
                            "shape": None,
                            "bands": bands
                        },
                        "metadata": item_dict
                    }
                }

                return result

            elif source == "sentinel":
                if spatial_input_type != "bbox":
                    logger.error(f"Unsupported spatial input type for Sentinel: {spatial_input_type}")
                    raise ValueError(f"Unsupported spatial input type for Sentinel: {spatial_input_type}")

                # Convert spatial input to bbox format if needed
                if isinstance(spatial_input, (list, tuple)):
                    bbox = {
                        "xmin": spatial_input[0],  # West
                        "ymin": spatial_input[1],  # South
                        "xmax": spatial_input[2],  # East
                        "ymax": spatial_input[3]   # North
                    }
                else:
                    bbox = spatial_input

                # Set default temporal range if not provided
                if not temporal_input:
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=90)
                else:
                    start_date = temporal_input.get('start_date', datetime.now() - timedelta(days=90))
                    end_date = temporal_input.get('end_date', datetime.now())

                # Set default bands if not specified in tags
                bands = tags if tags else ["B04", "B08"]

                # Initialize Sentinel API if needed
                if not await connector.initialize():
                    return {
                        "status": "error",
                        "message": "Failed to initialize Sentinel API"
                    }

                # Download data
                result = await connector.download_data(
                    bbox=bbox,
                    start_date=start_date,
                    end_date=end_date,
                    bands=bands,
                    cloud_cover=30.0
                )

                return result

            elif source == "landsat":
                if spatial_input_type != "bbox":
                    logger.error(f"Unsupported spatial input type for Landsat: {spatial_input_type}")
                    raise ValueError(f"Unsupported spatial input type for Landsat: {spatial_input_type}")

                # Convert spatial input to bbox format if needed
                if isinstance(spatial_input, (list, tuple)):
                    bbox = {
                        "xmin": spatial_input[0],  # West
                        "ymin": spatial_input[1],  # South
                        "xmax": spatial_input[2],  # East
                        "ymax": spatial_input[3]   # North
                    }
                else:
                    bbox = spatial_input

                # Set default temporal range if not provided
                if not temporal_input:
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=90)
                else:
                    start_date = temporal_input.get('start_date', datetime.now() - timedelta(days=90))
                    end_date = temporal_input.get('end_date', datetime.now())

                # Ensure tags is not None before using it
                if tags is None:
                    tags = []

                # Get data
                result = await connector.get_data(
                    spatial_input={"bbox": bbox},
                    other_inputs={
                        "start_date": start_date,
                        "end_date": end_date,
                        "max_cloud_cover": 20.0,
                        "limit": 5
                    }
                )

                return result

            elif source == "overture":
                if spatial_input_type == "bbox":
                    # Convert spatial input to bbox format if needed
                    if isinstance(spatial_input, (list, tuple)):
                        bbox = {
                            "xmin": spatial_input[0],
                            "ymin": spatial_input[1],
                            "xmax": spatial_input[2],
                            "ymax": spatial_input[3]
                        }
                    else:
                        bbox = spatial_input

                    # If tags are specified, download specific themes
                    if tags:
                        if isinstance(tags, str):
                            tags = [tags]
                        results = {}
                        for tag in tags:
                            if tag not in connector.THEMES:
                                logger.warning(f"Invalid theme: {tag}")
                                continue
                            for type_name in connector.THEMES[tag]:
                                success = connector.download_theme_type(tag, type_name, bbox)
                                if success:
                                    features = await connector.search_features_by_type(tag, bbox)
                                    if not features.get("error"):
                                        results[tag] = features.get("features", [])
                                else:
                                    logger.warning(f"Failed to download theme {tag}")
                                    results[tag] = []
                        return results
                    else:
                        # Download all themes
                        download_results = connector.download_data(bbox)
                        if any(download_results.values()):
                            features = await connector.search(bbox)
                            return features
                        else:
                            logger.warning("Failed to download any themes")
                            return {theme: [] for theme in connector.THEMES}

                else:
                    logger.error(f"Unsupported spatial input type for Overture: {spatial_input_type}")
                    raise ValueError(f"Unsupported spatial input type for Overture: {spatial_input_type}")

            else:
                logger.error(f"Unsupported source: {source}")
                raise ValueError(f"Unsupported source: {source}")

        except Exception as e:
            logger.error(f"Error retrieving from glacier tier: {e}")
            return None

    async def _retrieve_from_cold(self, spatial_input_type, spatial_input, tags):
        """Handle retrieval from cold storage."""
        try:
            self._init_cold()
            
            if not self._cold_memory:
                logger.error("Cold memory not initialized")
                return None
            
            # Ensure tags is not None before using it
            if tags is None:
                tags = []
                
            # Handle Landsat data format
            if tags and "landsat" in tags:
                storage_path = Path(self._cold_memory.raw_data_path) / "cold_storage/landsat"
                if not storage_path.exists():
                    logger.warning("No Landsat data found in cold storage")
                    return None
                    
                # Convert spatial input to bbox format if needed
                if spatial_input_type == "bbox":
                    if isinstance(spatial_input, (list, tuple)):
                        bbox = {
                            "xmin": spatial_input[0],
                            "ymin": spatial_input[1],
                            "xmax": spatial_input[2],
                            "ymax": spatial_input[3]
                        }
                    else:
                        bbox = spatial_input
                        
                    # Find scenes that intersect with the bbox
                    scenes = []
                    for file_path in storage_path.glob("*.json"):
                        try:
                            with open(file_path, 'r') as f:
                                scene_data = json.load(f)
                                
                            # Check if scene intersects with bbox
                            scene_bbox = scene_data.get("bbox")
                            if scene_bbox:
                                if (bbox["xmin"] <= scene_bbox[2] and bbox["xmax"] >= scene_bbox[0] and
                                    bbox["ymin"] <= scene_bbox[3] and bbox["ymax"] >= scene_bbox[1]):
                                    scenes.append(scene_data)
                        except Exception as e:
                            logger.error(f"Error reading scene file {file_path}: {e}")
                            
                    return {
                        "data": {
                            "scenes": scenes,
                            "total_scenes": len(scenes),
                            "metadata": {
                                "bbox": bbox,
                                "storage_path": str(storage_path)
                            }
                        }
                    }
                    
            # Handle Sentinel-2 data format
            elif tags and "sentinel-2-l2a" in tags:
                storage_path = Path(self._cold_memory.raw_data_path) / "planetary/sentinel-2-l2a"
                if not storage_path.exists():
                    logger.warning("No Sentinel-2 data found in cold storage")
                    return None
                    
                # Find all stored scenes
                scenes = []
                for file_path in storage_path.glob("*_metadata.json"):
                    try:
                        with open(file_path, 'r') as f:
                            metadata = json.load(f)
                            
                        # Get corresponding data file
                        data_file = file_path.parent / file_path.name.replace("_metadata.json", "_data.npy")
                        if data_file.exists():
                            scenes.append({
                                "metadata": metadata,
                                "data_file": str(data_file)
                            })
                    except Exception as e:
                        logger.error(f"Error reading scene file {file_path}: {e}")
                        
                return {
                    "sentinel-2-l2a": {
                        "data": scenes,
                        "metadata": {
                            "storage_path": str(storage_path),
                            "total_scenes": len(scenes)
                        }
                    }
                }
                
            # Handle other data formats
            else:
                # Default to using the cold memory's retrieve method
                return self._cold_memory.retrieve({
                    "spatial_input_type": spatial_input_type,
                    "spatial_input": spatial_input,
                    "tags": tags
                })

        except Exception as e:
            logger.error(f"Error in _retrieve_from_cold: {e}")
            return None

    async def _retrieve_from_hot(self, spatial_input_type, spatial_input, tags):
        """Handle retrieval from hot storage."""
        # Implementation for hot tier retrieval
        pass

    async def _retrieve_from_warm(self, spatial_input_type, spatial_input, tags):
        """Handle retrieval from warm storage."""
        # Implementation for warm tier retrieval
        pass

    async def _retrieve_from_red_hot(self, spatial_input_type, spatial_input, tags):
        """Handle retrieval from red hot storage."""
        # Implementation for red hot tier retrieval
        pass


# Create singleton instance
memory_retrieval = MemoryRetrieval().retrieve

async def test_memory_retrieval():
    """Test the memory retrieval functionality with Overture data."""
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Test with San Francisco area
    sf_bbox = [-122.5155, 37.7079, -122.3555, 37.8119]  # [West, South, East, North]
    
    logger.info("\nTesting memory retrieval with Overture data...")
    logger.info(f"Bounding box: {sf_bbox}")
    
    # Initialize memory retrieval
    retrieval = MemoryRetrieval()
    
    # Test retrieving specific themes
    themes = ["buildings", "places", "transportation"]
    logger.info(f"\nRetrieving themes: {themes}")
    
    results = await retrieval.retrieve(
        from_tier="glacier",
        source="overture",
        spatial_input_type="bbox",
        spatial_input=sf_bbox,
        tags=themes
    )
    
    if results:
        for theme, features in results.items():
            logger.info(f"\nFound {len(features)} {theme}:")
            for feature in features[:3]:  # Show first 3 features
                logger.info(f"- {feature.get('id')}: {feature.get('primary_name', 'Unnamed')}")
                if feature.get('geometry'):
                    logger.info(f"  Geometry type: {type(feature['geometry'])}")
    else:
        logger.info("No data retrieved")

def main():
    """Run the test."""
    import asyncio
    asyncio.run(test_memory_retrieval())

if __name__ == "__main__":
    main()