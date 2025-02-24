"""
Spatial Analysis module for processing geometric and spatial data.
"""

from typing import Dict, Any, Optional, List
import logging
from memories.utils.earth.geometry_retriever import GeometryExtractor
from memories.models.model_base import BaseModel

class SpatialAnalysis(BaseModel):
    """Module specialized in geometry and spatial data processing."""
    
    def __init__(self, model: Optional[Any] = None):
        """Initialize SpatialAnalysis with GeometryExtractor
        
        Args:
            model: Optional LLM model for advanced spatial analysis
        """
        super().__init__(name="spatial_analysis", model=model)
        self.geometry_retriever = GeometryExtractor()

    def get_capabilities(self) -> List[str]:
        """Return the capabilities of this module."""
        return [
            "Extract and analyze geometric features from locations",
            "Calculate distances and spatial relationships",
            "Process geographic coordinates and boundaries",
            "Analyze spatial patterns and distributions"
        ]

    def _initialize_tools(self) -> None:
        """Initialize spatial analysis tools."""
        self.register_tool(
            "process_location",
            self.process_location,
            "Process location information to extract geometric features"
        )
        self.register_tool(
            "analyze_spatial_relationships",
            self.analyze_spatial_relationships,
            "Analyze spatial relationships between geometric features"
        )

    async def process(self, goal: Dict[str, Any]) -> Dict[str, Any]:
        """Process spatial analysis goals.
        
        Args:
            goal: Dictionary containing:
                - location_info: Dict with location data
                - radius_meters: Optional search radius
                - analysis_type: Type of spatial analysis to perform
                
        Returns:
            Dict[str, Any]: Processing results
        """
        location_info = goal.get('location_info')
        radius_meters = goal.get('radius_meters', 1000)
        analysis_type = goal.get('analysis_type', 'basic')
        
        if not location_info:
            return {
                "status": "error",
                "error": "No location information provided",
                "data": None
            }
            
        try:
            # Get geometric features
            geometries = await self.process_location(location_info, radius_meters)
            
            # Perform additional analysis if requested
            if analysis_type != 'basic' and 'error' not in geometries:
                analysis = await self.analyze_spatial_relationships(geometries)
                geometries['analysis'] = analysis
            
            return {
                "status": "success" if "error" not in geometries else "error",
                "data": geometries if "error" not in geometries else None,
                "error": geometries.get("error")
            }
            
        except Exception as e:
            self.logger.error(f"Error in SpatialAnalysis: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "data": None
            }

    async def process_location(self, location_info: Dict[str, Any], radius_meters: float = 1000) -> Dict[str, Any]:
        """Process location information and retrieve geometries.
        
        Args:
            location_info: Dict containing:
                - location (str): Coordinate string
                - location_type (str): Type of location (e.g., 'point')
                - coordinates (Tuple): (lat, lon) tuple
            radius_meters: Search radius in meters
            
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
            self.logger.error(f"Error in process_location: {str(e)}")
            return {
                "error": str(e),
                "location_info": location_info
            }

    async def analyze_spatial_relationships(self, geometries: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze spatial relationships between geometric features.
        
        Args:
            geometries: Dictionary containing geometric features
            
        Returns:
            Dict[str, Any]: Analysis results
        """
        try:
            if 'features' not in geometries:
                raise ValueError("No features found in geometries")
                
            features = geometries['features']
            analysis = {
                'feature_count': len(features),
                'feature_types': {},
                'distance_stats': {
                    'min': float('inf'),
                    'max': 0,
                    'avg': 0
                }
            }
            
            # Analyze feature types and distances
            total_distance = 0
            for feature in features:
                # Count feature types
                geom_type = feature['properties'].get('geom_type', 'unknown')
                analysis['feature_types'][geom_type] = analysis['feature_types'].get(geom_type, 0) + 1
                
                # Track distance statistics
                distance = feature['properties'].get('distance_meters', 0)
                analysis['distance_stats']['min'] = min(analysis['distance_stats']['min'], distance)
                analysis['distance_stats']['max'] = max(analysis['distance_stats']['max'], distance)
                total_distance += distance
            
            # Calculate average distance
            if features:
                analysis['distance_stats']['avg'] = total_distance / len(features)
                
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error in analyze_spatial_relationships: {str(e)}")
            return {
                "error": str(e)
            }

    def requires_model(self) -> bool:
        """This module can operate with or without a model."""
        return False

    def __str__(self) -> str:
        """String representation of SpatialAnalysis"""
        return "SpatialAnalysis(GeometryExtractor)"


def main():
    """Example usage of SpatialAnalysis"""
    # Initialize module
    spatial = SpatialAnalysis()
    
    # Example location info
    location_info = {
        'location': '-12.911935, 77.611699',
        'location_type': 'point',
        'coordinates': (-12.911935, 77.611699)
    }
    
    # Process location
    result = spatial.process_location(location_info)
    
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