"""OpenStreetMap connector for glacier storage."""

import osmnx as ox
import geopandas as gpd
from typing import Dict, List, Union, Optional, Any, Tuple
from shapely.geometry import box
import requests
from urllib.parse import quote
import logging
import aiohttp
from pathlib import Path

from memories.core.glacier.api_connector import APIConnector
from memories.core.glacier.artifacts import DataSource
from memories.core.glacier.memory import GlacierMemory
import asyncio

logger = logging.getLogger(__name__)

class OSMConnector(APIConnector, DataSource):
    """OpenStreetMap connector using Overpass API."""
    
    def __init__(self, config: Dict[str, Any], cache_dir: Optional[str] = None):
        """Initialize OSM connector."""
        default_config = {
            'type': 'rest',
            'base_url': 'https://nominatim.openstreetmap.org',
            'overpass_url': 'https://overpass-api.de/api/interpreter',
            'timeout': 25,
            'feature_types': {
                'buildings': ['building'],
                'highways': ['highway'],
                'water': ['water', 'waterway', 'natural=water']
            }
        }
        default_config.update(config or {})
        
        APIConnector.__init__(self, default_config)
        DataSource.__init__(self, cache_dir)
        
        self.config = default_config
        self._session = None

    async def connect(self) -> None:
        """Establish connection to the API."""
        if not self._session:
            self._session = aiohttp.ClientSession()

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self._session:
            await self._session.close()
            self._session = None

    async def list_objects(self, prefix: str = "") -> List[str]:
        """List available objects (not applicable for OSM)."""
        return []

    async def delete(self, key: str) -> bool:
        """Delete an object (not applicable for OSM)."""
        return False

    async def store(self, key: str, data: Any) -> bool:
        """Store data (not applicable for OSM as it's read-only)."""
        return False

    async def search(self, bbox: Union[List[float], tuple[float, float, float, float]], tags: List[str] = None) -> Dict:
        """Search for OSM data."""
        # Implementation here
        pass

    async def download(self, bbox: Union[List[float], tuple[float, float, float, float]], tags: List[str] = None) -> Path:
        """Download OSM data."""
        # Implementation here
        pass

    def get_metadata(self, *args, **kwargs) -> Dict[str, Any]:
        """Get metadata about the OSM data."""
        return {
            "source": "OpenStreetMap",
            "api": self.config['base_url'],
            "feature_types": self.config.get('feature_types', {})
        }

    def _build_query(self, bbox: Union[List[float], Tuple[float, float, float, float]], tag: str) -> str:
        """Build Overpass API query.
        
        Args:
            bbox: [north, south, east, west] coordinates
            tag: OSM tag to query
            
        Returns:
            Overpass QL query string
        """
        # Ensure bbox is in correct format [south,west,north,east] for Overpass API
        south, west = min(bbox[0], bbox[1]), min(bbox[2], bbox[3])
        north, east = max(bbox[0], bbox[1]), max(bbox[2], bbox[3])
        
        # Handle different tag formats
        if '=' in tag:
            key, value = tag.split('=')
            tag_filter = f'["{key}"="{value}"]'
        else:
            tag_filter = f'["{tag}"]'
        
        # Build query with proper formatting
        query = f"""
            [out:json][timeout:{self.config['timeout']}];
            (
                way{tag_filter}({south},{west},{north},{east});
                relation{tag_filter}({south},{west},{north},{east});
            );
            out body;
            >;
            out skel qt;
        """
        return query.strip()

    async def get_address_from_coords(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Get address details from coordinates using Nominatim OpenStreetMap API.
        
        Args:
            lat: Latitude of the location (-90 to 90)
            lon: Longitude of the location (-180 to 180)
            
        Returns:
            Dictionary containing:
                - status: "success" or "error"
                - address: Full address details if found
                - display_name: Formatted display name
                - message: Error message if status is "error"
        """
        try:
            # Validate coordinates
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                return {
                    "status": "error",
                    "message": "Invalid coordinates: latitude must be between -90 and 90, longitude between -180 and 180",
                    "address": None
                }
            
            # Define headers for Nominatim API
            headers = {
                'User-Agent': 'Memories/1.0 (https://github.com/your-repo/memories)',
                'Accept-Language': 'en-US,en;q=0.5'
            }
            
            # Make request to Nominatim API using reverse geocoding
            url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&addressdetails=1"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            # Parse response
            result = response.json()
            
            if not result or "error" in result:
                return {
                    "status": "error",
                    "message": result.get("error", "No results found for the given coordinates"),
                    "address": None
                }
                
            return {
                "status": "success",
                "address": result.get("address", {}),
                "display_name": result.get("display_name"),
                "osm_type": result.get("osm_type"),
                "osm_id": result.get("osm_id"),
                "place_id": result.get("place_id"),
                "lat": float(result.get("lat", lat)),
                "lon": float(result.get("lon", lon))
            }
            
        except Exception as e:
            logger.error(f"Error getting address from coordinates: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "address": None
            }

    async def get_bounding_box_from_address(self, address: str) -> Dict[str, Any]:
        """
        Get bounding box coordinates for an address using Nominatim OpenStreetMap API.
        
        Args:
            address: Address string to geocode
            
        Returns:
            Dictionary containing:
                - boundingbox: List of [min_lat, max_lat, min_lon, max_lon]
                - status: "success" or "error"
                - message: Error message if status is "error"
                - display_name: Full display name of the location
                - lat: Latitude of the location center
                - lon: Longitude of the location center
        """
        try:
            # Format the address for URL
            encoded_address = quote(address)
            
            # Define headers - this is important for Nominatim's terms of use
            headers = {
                'User-Agent': 'Memories/1.0 (https://github.com/your-repo/memories)',
                'Accept-Language': 'en-US,en;q=0.5'
            }
            
            # Make request to Nominatim API
            url = f"https://nominatim.openstreetmap.org/search?q={encoded_address}&format=json&polygon_geojson=1"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            # Parse response
            results = response.json()
            
            if not results:
                return {
                    "status": "error",
                    "message": "No results found for the given address",
                    "boundingbox": None
                }
                
            # Get first result
            result = results[0]
            
            return {
                "status": "success",
                "boundingbox": result["boundingbox"],  # [min_lat, max_lat, min_lon, max_lon]
                "display_name": result["display_name"],
                "lat": float(result["lat"]),
                "lon": float(result["lon"])
            }
            
        except Exception as e:
            logger.error(f"Error getting bounding box for address: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "boundingbox": None
            }

    async def get_osm_data(self, location: Union[str, List[float]], themes: Union[str, List[str]] = "all") -> Dict[str, Any]:
        """
        Fetch OSM data for given location (address or bbox) and themes.
        
        Args:
            location: Address string or bounding box [south, west, north, east]
            themes: "all" or list of themes ["landuse", "buildings", "roads", etc.]
        
        Returns:
            Raw OSM data response
        """
        try:
            # Get bbox from address if string is provided
            if isinstance(location, str):
                result = await self.get_bounding_box_from_address(location)
                if result["status"] == "error":
                    logger.error(f"Error: {result['message']}")
                    return None
                # Convert Nominatim bbox [min_lat, max_lat, min_lon, max_lon] to [south, west, north, east]
                bbox = [
                    float(result["boundingbox"][0]),  # south (min_lat)
                    float(result["boundingbox"][2]),  # west (min_lon)
                    float(result["boundingbox"][1]),  # north (max_lat)
                    float(result["boundingbox"][3])   # east (max_lon)
                ]
            else:
                bbox = location

            # Validate bbox coordinates
            if len(bbox) != 4:
                logger.error("Invalid bounding box: must have 4 coordinates [south, west, north, east]")
                return None
            
            south, west, north, east = bbox
            if not (-90 <= south <= 90 and -90 <= north <= 90):
                logger.error("Invalid latitude values: must be between -90 and 90")
                return None
            if not (-180 <= west <= 180 and -180 <= east <= 180):
                logger.error("Invalid longitude values: must be between -180 and 180")
                return None
            if south > north:
                logger.error("Invalid coordinates: south latitude must be less than north latitude")
                return None

            # Convert themes to tags based on feature_types config
            if themes == "all":
                tags = []
                for theme_tags in self.config['feature_types'].values():
                    tags.extend(theme_tags)
            else:
                if isinstance(themes, str):
                    themes = [themes]
                tags = []
                for theme in themes:
                    if theme in self.config['feature_types']:
                        tags.extend(self.config['feature_types'][theme])

            # Build query parts for each tag
            tag_queries = []
            for tag in tags:
                if '=' in tag:
                    key, value = tag.split('=')
                    tag_filter = f'["{key}"="{value}"]'
                else:
                    tag_filter = f'["{tag}"]'
                tag_queries.append(f"""
                    way{tag_filter}({south},{west},{north},{east});
                    relation{tag_filter}({south},{west},{north},{east});
                """)

            # Combine all tag queries
            query = f"""
                [out:json][timeout:{self.config['timeout']}];
                (
                    {' '.join(tag_queries)}
                );
                out body;
                >;
                out skel qt;
            """
            
            logger.debug(f"Executing Overpass query: {query.strip()}")
            
            # Make request to Overpass API
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.config['overpass_url'],
                    data=query.strip(),
                    headers={'Content-Type': 'text/plain'},
                    timeout=self.config['timeout']
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        response_text = await response.text()
                        logger.error(f"Error from Overpass API: {response.status}, Response: {response_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error querying OSM data: {str(e)}")
            return None

    async def get_data(self, spatial_input: Union[str, List[float], Dict], spatial_input_type: str = "bbox", tags: List[str] = None) -> Dict[str, Any]:
        """Get OSM data for the given spatial input.
        
        Args:
            spatial_input: Either a bounding box [south, west, north, east], address string, or dict with bbox
            spatial_input_type: Type of spatial input ("bbox" or "address")
            tags: List of OSM tags to filter by
            
        Returns:
            Dictionary containing OSM data or None if error
            
        Raises:
            ValueError: If spatial_input_type is not supported
        """
        if spatial_input_type not in ["bbox", "address"]:
            raise ValueError(f"Unsupported spatial input type: {spatial_input_type}")
            
        # Convert input format if needed
        if isinstance(spatial_input, dict):
            if "bbox" in spatial_input:
                bbox = spatial_input["bbox"]
            else:
                bbox = [
                    spatial_input.get("ymin", 0),  # south
                    spatial_input.get("xmin", 0),  # west
                    spatial_input.get("ymax", 0),  # north
                    spatial_input.get("xmax", 0)   # east
                ]
        else:
            bbox = spatial_input
            
        return await self.get_osm_data(bbox, tags if tags else "all")