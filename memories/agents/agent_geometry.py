from typing import Dict, Any
import logging
from memories.utils.earth.geometry_retriever import GeometryExtractor

class AgentGeometry:
    def __init__(self):
        """Initialize AgentGeometry with GeometryExtractor"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        self.geometry_retriever = GeometryExtractor()

    def process_location(self, location_info: Dict[str, Any], radius_meters: float = 1000) -> Dict[str, Any]:
        """
        Process location information and retrieve geometries
        
        Args:
            location_info (Dict): Must contain:
                - location (str): Coordinate string
                - location_type (str): Type of location (e.g., 'point')
                - coordinates (Tuple): (lat, lon) tuple
            radius_meters (float): Search radius in meters
            
        Returns:
            Dict[str, Any]: Retrieved geometries and properties
        """
        try:
            self.logger.info(f"Processing location: {location_info['location']}")
            
            # Validate location info
            if not isinstance(location_info, dict):
                raise ValueError("Location info must be a dictionary")
            
            required_keys = ['location', 'location_type', 'coordinates']
            if not all(key in location_info for key in required_keys):
                missing_keys = [key for key in required_keys if key not in location_info]
                raise ValueError(f"Missing required keys in location_info: {missing_keys}")
            
            # Retrieve geometries
            geometries = self.geometry_retriever.retrieve_geometry(
                location_info=location_info,
                radius_meters=radius_meters
            )
            
            # Log results
            if 'features' in geometries:
                self.logger.info(
                    f"Found {len(geometries['features'])} features within "
                    f"{radius_meters}m of {location_info['location']}"
                )
            
            return geometries
            
        except Exception as e:
            self.logger.error(f"Error in AgentGeometry: {str(e)}")
            return {
                "error": str(e),
                "location_info": location_info
            }

    def __str__(self) -> str:
        """String representation of AgentGeometry"""
        return "AgentGeometry(GeometryExtractor)"


def main():
    """Example usage of AgentGeometry"""
    # Initialize agent
    agent = AgentGeometry()
    
    # Example location info
    location_info = {
        'location': '-12.911935, 77.611699',
        'location_type': 'point',
        'coordinates': (-12.911935, 77.611699)
    }
    
    # Process location
    result = agent.process_location(location_info)
    
    # Print results
    print("\nGeometry Results:")
    print("="*50)
    if 'error' in result:
        print(f"Error: {result['error']}")
    else:
        print(f"Query Point: {result['query']['location']}")
        print(f"Features found: {len(result['features'])}")
        print("\nFirst few features:")
        for feature in result['features'][:3]:
            print(f"\nType: {feature['properties']['geom_type']}")
            print(f"Name: {feature['properties'].get('name', 'Unnamed')}")
            print(f"Distance: {feature['properties']['distance_meters']:.1f}m")

if __name__ == "__main__":
    main()
