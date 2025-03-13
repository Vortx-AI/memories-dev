"""Landsat data source for glacier storage."""

import os
import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import planetary_computer as pc
import pystac_client
import logging
import json
from pathlib import Path
# Update import to correct path
from memories.core.glacier.artifacts import DataSource
from memories.core.cold import ColdMemory
import uuid

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True  # Force reconfiguration of the root logger
)
logger = logging.getLogger(__name__)

# Add a stream handler if none exists
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

logger.info("Starting Landsat module initialization")

class LandsatConnector(DataSource):
    """Interface for Landsat data access through Planetary Computer."""
    
    def __init__(self):
        """Initialize Landsat interface."""
        super().__init__()
        self.token = os.getenv("PLANETARY_COMPUTER_API_KEY")
        if self.token:
            pc.settings.set_subscription_key(self.token)
        
        self.catalog = pystac_client.Client.open(
            "https://planetarycomputer.microsoft.com/api/stac/v1",
            modifier=pc.sign_inplace
        )
        
        # Set up cold storage paths with absolute path
        root_dir = Path(__file__).parent.parent.parent.parent.parent  # Go up to project root
        self.storage_dir = root_dir / "data" / "cold_storage" / "landsat"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized Landsat cold storage at: {self.storage_dir.absolute()}")
        
        # Initialize cold memory
        self.cold_memory = ColdMemory()

    def _get_storage_path(self, scene_id: str) -> Path:
        """Get the storage path for a scene."""
        storage_path = self.storage_dir / f"{scene_id}.json"
        logger.info(f"Storing data at: {storage_path.absolute()}")
        return storage_path

    def _save_to_cold_storage(self, scene_id: str, data: Dict[str, Any]) -> bool:
        """Save data to cold storage."""
        try:
            # Create storage path in cold storage
            storage_path = self._get_storage_path(scene_id)
            storage_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save data to file
            with open(storage_path, 'w') as f:
                json.dump(data, f, indent=2)
                
            # Create a unique identifier for this data
            timestamp = data.get("datetime", datetime.now().isoformat())
            # Add microseconds to timestamp to ensure uniqueness
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp)
            
            # Add random suffix to ensure uniqueness
            unique_suffix = str(uuid.uuid4())[:8]  # Use first 8 chars of UUID
            unique_timestamp = timestamp.strftime('%Y-%m-%dT%H_%M_%S_%f')
            data_id = f"landsat_{scene_id}_{unique_timestamp}_{unique_suffix}"
            
            # Prepare metadata
            metadata = {
                "id": data_id,  # Required field for cold memory
                "type": "landsat",
                "collection": "landsat-c2-l2",
                "datetime": timestamp.isoformat(),
                "bbox": data.get("bbox"),
                "properties": data.get("properties", {}),
                "cloud_cover": data.get("properties", {}).get("eo:cloud_cover"),
                "platform": data.get("properties", {}).get("platform"),
                "instrument": data.get("properties", {}).get("instruments"),
                "processing_level": data.get("properties", {}).get("processing:level")
            }
            
            # Prepare data dictionary for cold memory
            data_dict = {
                "file_path": str(storage_path),
                "scene_id": scene_id,
                "metadata": metadata,
                "data": data  # Include the full data
            }
            
            # Store in cold memory
            success = self.cold_memory.store(data_dict, metadata)
            
            if success:
                logger.info(f"Successfully stored {scene_id} in cold storage")
                return True
            else:
                logger.error(f"Failed to store {scene_id} in cold storage")
                return False
                
        except Exception as e:
            logger.error(f"Error saving to cold storage: {str(e)}")
            return False

    def _load_from_cold_storage(self, scene_id: str) -> Optional[Dict[str, Any]]:
        """Load data from cold storage."""
        try:
            storage_path = self._get_storage_path(scene_id)
            if storage_path.exists():
                with open(storage_path, 'r') as f:
                    data = json.load(f)
                logger.info(f"Loaded data from cold storage: {storage_path}")
                return data
            logger.info(f"No data found in cold storage for scene {scene_id}")
            return None
        except Exception as e:
            logger.error(f"Error loading from cold storage: {e}")
            return None

    async def search_scenes(
        self,
        bbox: List[float],
        start_date: datetime,
        end_date: datetime,
        max_cloud_cover: float = 20.0,
        limit: int = 5
    ) -> List[Any]:
        """Search for Landsat scenes."""
        logger.info("=" * 80)
        logger.info("Starting Landsat scene search")
        logger.info(f"Search parameters:")
        logger.info(f"- Time range: {start_date} to {end_date}")
        logger.info(f"- Bbox: {bbox}")
        logger.info(f"- Cloud cover limit: {max_cloud_cover}%")
        logger.info(f"- Result limit: {limit}")
        logger.info("=" * 80)
        
        search = self.catalog.search(
            collections=["landsat-c2-l2"],  # Updated collection name
            bbox=bbox,
            datetime=f"{start_date.isoformat()}/{end_date.isoformat()}",
            query={"eo:cloud_cover": {"lt": max_cloud_cover}},
            limit=limit
        )
        
        # Use items() instead of get_items()
        scenes = list(search.items())
        logger.info(f"\nFound {len(scenes)} scenes matching criteria")
        
        # Save search results to cold storage
        for scene in scenes:
            logger.info(f"\nProcessing scene: {scene.id}")
            logger.info(f"- Cloud cover: {scene.properties.get('eo:cloud_cover', 'N/A')}%")
            logger.info(f"- Date: {scene.datetime.isoformat() if scene.datetime else 'N/A'}")
            logger.info(f"- Platform: {scene.properties.get('platform', 'N/A')}")
            
            success = self._save_to_cold_storage(scene.id, {
                "id": scene.id,
                "properties": scene.properties,
                "bbox": scene.bbox,
                "datetime": scene.datetime.isoformat() if scene.datetime else None
            })
            
            if success:
                logger.info(f"Successfully saved scene {scene.id} to cold storage")
            else:
                logger.warning(f"Failed to save scene {scene.id} to cold storage")
        
        logger.info("=" * 80)
        return scenes

    def get_metadata(self, *args, **kwargs) -> Dict[str, Any]:
        """Get metadata about a data source or specific item."""
        # Create a new event loop for this synchronous method
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # Call the async method and run it in the event loop
            return loop.run_until_complete(self._get_metadata_async(*args, **kwargs))
        finally:
            loop.close()

    async def _get_metadata_async(self, scene_id: str) -> Optional[Dict[str, Any]]:
        """Async implementation of get_metadata."""
        # Try to load from cold storage first
        cached_data = self._load_from_cold_storage(scene_id)
        if cached_data:
            metadata = cached_data.get("properties", {})
            metadata["id"] = scene_id  # Add scene ID to metadata
            return metadata

        # If not in cold storage, fetch from API
        try:
            item = self.catalog.get_collection("landsat-c2-l2").get_item(scene_id)
            metadata = item.properties
            metadata["id"] = scene_id  # Add scene ID to metadata
            
            # Save to cold storage
            self._save_to_cold_storage(scene_id, {
                "id": item.id,
                "properties": metadata,
                "bbox": item.bbox,
                "datetime": item.datetime.isoformat() if item.datetime else None
            })
            return metadata
        except Exception as e:
            logger.error(f"Error getting metadata for scene {scene_id}: {e}")
            return None

    async def get_data(self, spatial_input: Dict[str, Any], other_inputs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get Landsat data for the specified area and parameters.
        
        Args:
            spatial_input: Dictionary containing spatial search parameters
            other_inputs: Additional search parameters
            
        Returns:
            Dictionary containing the retrieved data and metadata
        """
        try:
            # Extract parameters
            bbox_dict = spatial_input.get('bbox')
            if not bbox_dict:
                raise ValueError("Bounding box is required")
            
            # Convert bbox dictionary to list of floats
            bbox = [
                float(bbox_dict['xmin']),
                float(bbox_dict['ymin']),
                float(bbox_dict['xmax']),
                float(bbox_dict['ymax'])
            ]

            # Get default or specified dates
            end_date = other_inputs.get('end_date', datetime.now()) if other_inputs else datetime.now()
            start_date = other_inputs.get('start_date', end_date - timedelta(days=90))
            max_cloud_cover = other_inputs.get('max_cloud_cover', 20.0) if other_inputs else 20.0
            limit = other_inputs.get('limit', 5) if other_inputs else 5
            
            logger.info(f"Search parameters:")
            logger.info(f"- Start date: {start_date}")
            logger.info(f"- End date: {end_date}")
            logger.info(f"- Bbox: {bbox}")
            
            # Search for scenes
            scenes = await self.search_scenes(
                bbox=bbox,
                start_date=start_date,
                end_date=end_date,
                max_cloud_cover=max_cloud_cover,
                limit=limit
            )
            
            if not scenes:
                return {
                    "status": "error",
                    "message": "No scenes found matching criteria"
                }
            
            # Get metadata for first scene
            first_scene = scenes[0]
            metadata = await self._get_metadata_async(first_scene.id)
            
            if not metadata:
                return {
                    "status": "error",
                    "message": "Failed to retrieve metadata"
                }
            
            # Prepare metadata with properties
            scene_metadata = {
                "id": first_scene.id,
                "properties": first_scene.properties,
                "bbox": first_scene.bbox,
                "datetime": first_scene.datetime.isoformat() if first_scene.datetime else None,
                "created": datetime.now().isoformat(),
                "description": "Landsat Collection 2 Level-2"
            }
            
            # Save to cold storage
            self._save_to_cold_storage(first_scene.id, scene_metadata)
            
            return {
                "status": "success",
                "data": {
                    "scenes": [
                        {
                            "id": scene.id,
                            "properties": scene.properties,
                            "bbox": scene.bbox
                        } for scene in scenes
                    ],
                    "metadata": scene_metadata,
                    "total_scenes": len(scenes)
                }
            }
            
        except Exception as e:
            logger.error(f"Error retrieving Landsat data: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

    async def search(self, *args, **kwargs) -> Union[List[Dict], Dict]:
        """Search for data matching specified criteria."""
        return await self.search_scenes(*args, **kwargs)

    async def download(self, *args, **kwargs) -> Path:
        """Download data to local storage."""
        result = await self.get_data(*args, **kwargs)
        if result["status"] == "success":
            # Save the data to a file and return the path
            output_path = self.storage_dir / f"{result['data']['metadata']['id']}.json"
            with open(output_path, 'w') as f:
                json.dump(result['data'], f, indent=2)
            return output_path
        raise Exception(result.get("message", "Download failed"))

async def main():
    """Test the Landsat API functionality."""
    logger.info("\n" + "="*80)
    logger.info("STARTING LANDSAT API TEST")
    logger.info("="*80 + "\n")
    
    # Initialize API
    api = LandsatConnector()
    logger.info("LandsatConnector initialized")
    
    # Test bounding box (San Francisco area)
    bbox = {
        "xmin": -122.5155,  # Western longitude
        "ymin": 37.7079,    # Southern latitude
        "xmax": -122.3555,  # Eastern longitude
        "ymax": 37.8119     # Northern latitude
    }
    
    # Time range (last 90 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    
    logger.info("Test Configuration:")
    logger.info(f"- Search area: San Francisco")
    logger.info(f"- Bounding box: {bbox}")
    logger.info(f"- Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    try:
        # Test data retrieval
        logger.info("\nStarting data retrieval...")
        result = await api.get_data(
            spatial_input={"bbox": bbox},
            other_inputs={
                "start_date": start_date,
                "end_date": end_date,
                "max_cloud_cover": 20.0,
                "limit": 5
            }
        )
        
        if result["status"] == "success":
            logger.info("\nData retrieval successful!")
            data = result["data"]
            logger.info(f"Total scenes found: {data['total_scenes']}")
            
            # Print metadata for first scene
            if data["scenes"]:
                first_scene = data["scenes"][0]
                logger.info("\nFirst Scene Details:")
                logger.info(f"Scene ID: {first_scene['id']}")
                logger.info(f"Bounding Box: {first_scene['bbox']}")
                
                # Print some key properties
                props = first_scene.get("properties", {})
                logger.info("\nScene Properties:")
                logger.info(f"Cloud Cover: {props.get('eo:cloud_cover', 'N/A')}%")
                logger.info(f"Platform: {props.get('platform', 'N/A')}")
                logger.info(f"Instrument: {props.get('instruments', 'N/A')}")
                logger.info(f"Processing Level: {props.get('processing:level', 'N/A')}")
                
                # Test cold storage retrieval
                logger.info("\nTesting cold storage retrieval...")
                cached_data = await api._get_metadata_async(first_scene['id'])
                if cached_data:
                    logger.info("Successfully retrieved data from cold storage")
                    logger.info(f"Cached Scene ID: {cached_data.get('id')}")
                else:
                    logger.warning("No data found in cold storage")
            
        else:
            logger.error(f"Data retrieval failed: {result.get('message', 'Unknown error')}")
            
    except Exception as e:
        logger.error(f"Error in main: {str(e)}", exc_info=True)
    finally:
        logger.info("\n" + "="*80)
        logger.info("Test completed")
        logger.info("="*80)

if __name__ == "__main__":
    logger.info("Script started - calling main()")
    asyncio.run(main()) 