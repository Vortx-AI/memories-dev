#!/usr/bin/env python3
"""
Location Data Analysis Example
----------------------------
This example demonstrates analyzing previously downloaded location data
without downloading it again.
"""

import os
import sys
import logging
import asyncio
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple

import numpy as np
import rasterio

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    print(f"Added {project_root} to Python path")
    sys.path.append(project_root)

from memories.config import Config
from memories.data_acquisition.sources.overture_api import OvertureAPI
from memories.utils.processors import ImageProcessor, VectorProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# San Francisco Financial District (1km x 1km)
SF_BBOX = {
    'xmin': -122.4018,  # Approximately Market & Montgomery
    'ymin': 37.7914,
    'xmax': -122.3928,  # About 1km east
    'ymax': 37.7994     # About 1km north
}

class LocationDataAnalyzer:
    """Analyzes location data using previously downloaded data."""
    
    def __init__(self, config: Config):
        """Initialize the analyzer with configuration."""
        self.config = config
        self.overture_api = OvertureAPI(data_dir=os.path.join(config.storage_path, "overture"))
        self.satellite_dir = Path(os.path.join(config.storage_path, "satellite"))
        
    async def analyze_location(
        self,
        location: Dict[str, Any],
        bbox: List[float],
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """Analyze location using previously downloaded data.
        
        Args:
            location: Location information dictionary
            bbox: Bounding box [xmin, ymin, xmax, ymax]
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            Dictionary containing analysis results
        """
        try:
            # Load satellite data
            satellite_data = self._load_satellite_data()
            logger.info("Loaded satellite data")
            
            # Load Overture data from cache
            bbox_dict = {
                'xmin': bbox[0],
                'ymin': bbox[1],
                'xmax': bbox[2],
                'ymax': bbox[3]
            }
            overture_data = await self.overture_api.search(bbox_dict)
            logger.info("Loaded Overture data from cache")
            
            # Analyze urban features
            urban_features = self._analyze_urban_features(overture_data)
            
            # Calculate environmental scores
            env_scores = self._calculate_environmental_scores(urban_features, satellite_data)
            
            # Calculate urban metrics
            urban_metrics = self._calculate_urban_metrics(urban_features, satellite_data)
            
            # Calculate noise levels
            noise_levels = self._estimate_noise_levels(urban_features, urban_metrics)
            
            # Calculate accessibility scores
            accessibility = self._calculate_accessibility(urban_features)
            
            # Calculate overall ambience score
            ambience_score = self._calculate_ambience_score(
                env_scores=env_scores,
                urban_metrics=urban_metrics,
                noise_levels=noise_levels,
                accessibility=accessibility
            )
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                env_scores=env_scores,
                urban_metrics=urban_metrics,
                noise_levels=noise_levels,
                accessibility=accessibility,
                ambience_score=ambience_score
            )
            
            return {
                "location_id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat(),
                "location_name": location.get("name", "Unknown Location"),
                "bbox": bbox,
                "analysis_period": {
                    "start_date": start_date,
                    "end_date": end_date
                },
                "ambience_score": ambience_score,
                "environmental_scores": env_scores,
                "urban_metrics": urban_metrics,
                "noise_levels": noise_levels,
                "accessibility_scores": accessibility,
                "recommendations": recommendations
            }
            
        except Exception as e:
            logger.error(f"Error analyzing location: {str(e)}")
            return {
                "location_id": str(uuid.uuid4()),
                "timestamp": None,
                "location_name": location.get("name", "Unknown Location"),
                "error": str(e)
            }
    
    def _load_satellite_data(self) -> Dict[str, np.ndarray]:
        """Load satellite data from downloaded files."""
        satellite_data = {}
        try:
            # Load Red band (B04)
            red_path = self.satellite_dir / "B04.tif"
            if red_path.exists():
                with rasterio.open(red_path) as src:
                    satellite_data["red"] = src.read(1)
                    logger.info(f"Loaded red band with shape {satellite_data['red'].shape}")
            else:
                # Simulate data if file doesn't exist
                logger.warning("Red band file not found, using simulated data")
                satellite_data["red"] = np.random.normal(1500, 500, (100, 100))
                
            # Load NIR band (B08)
            nir_path = self.satellite_dir / "B08.tif"
            if nir_path.exists():
                with rasterio.open(nir_path) as src:
                    satellite_data["nir"] = src.read(1)
                    logger.info(f"Loaded NIR band with shape {satellite_data['nir'].shape}")
            else:
                # Simulate data if file doesn't exist
                logger.warning("NIR band file not found, using simulated data")
                satellite_data["nir"] = np.random.normal(2000, 600, (100, 100))
                
            # Load SWIR band (B11)
            swir_path = self.satellite_dir / "B11.tif"
            if swir_path.exists():
                with rasterio.open(swir_path) as src:
                    satellite_data["swir"] = src.read(1)
                    logger.info(f"Loaded SWIR band with shape {satellite_data['swir'].shape}")
            else:
                # Simulate data if file doesn't exist
                logger.warning("SWIR band file not found, using simulated data")
                satellite_data["swir"] = np.random.normal(1800, 400, (100, 100))
            
            # Calculate indices with error handling
            if all(k in satellite_data for k in ["red", "nir", "swir"]):
                # Ensure no division by zero
                epsilon = 1e-10
                
                # NDVI (Normalized Difference Vegetation Index)
                sum_rn = satellite_data["nir"] + satellite_data["red"] + epsilon
                ndvi = (satellite_data["nir"] - satellite_data["red"]) / sum_rn
                satellite_data["ndvi"] = np.clip(ndvi, -1, 1)  # Normalize to valid range
                
                # NDWI (Normalized Difference Water Index)
                sum_ns = satellite_data["nir"] + satellite_data["swir"] + epsilon
                ndwi = (satellite_data["nir"] - satellite_data["swir"]) / sum_ns
                satellite_data["ndwi"] = np.clip(ndwi, -1, 1)
                
                # NDBI (Normalized Difference Built-up Index)
                sum_sn = satellite_data["swir"] + satellite_data["nir"] + epsilon
                ndbi = (satellite_data["swir"] - satellite_data["nir"]) / sum_sn
                satellite_data["ndbi"] = np.clip(ndbi, -1, 1)
                
                logger.info("Successfully calculated spectral indices")
                logger.info(f"NDVI range: [{np.min(ndvi):.2f}, {np.max(ndvi):.2f}]")
                logger.info(f"NDWI range: [{np.min(ndwi):.2f}, {np.max(ndwi):.2f}]")
                logger.info(f"NDBI range: [{np.min(ndbi):.2f}, {np.max(ndbi):.2f}]")
            
            return satellite_data
            
        except Exception as e:
            logger.warning(f"Error loading satellite data: {str(e)}")
            return self._generate_simulated_satellite_data()
    
    def _generate_simulated_satellite_data(self) -> Dict[str, np.ndarray]:
        """Generate simulated satellite data for testing."""
        logger.info("Generating simulated satellite data")
        size = (100, 100)
        
        # Generate realistic spectral indices
        ndvi = np.random.normal(0.3, 0.2, size)  # Typical urban NDVI
        ndwi = np.random.normal(-0.2, 0.15, size)  # Typical urban NDWI
        ndbi = np.random.normal(0.1, 0.15, size)  # Typical urban NDBI
        
        # Clip to valid ranges
        ndvi = np.clip(ndvi, -1, 1)
        ndwi = np.clip(ndwi, -1, 1)
        ndbi = np.clip(ndbi, -1, 1)
        
        return {
            "ndvi": ndvi,
            "ndwi": ndwi,
            "ndbi": ndbi
        }
    
    def _analyze_urban_features(self, overture_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze urban features from Overture data."""
        if not overture_data:
            # Generate simulated data for testing
            logger.warning("No Overture data found, using simulated urban features")
            return self._generate_simulated_urban_features()
            
        buildings = overture_data.get("buildings", [])
        transportation = overture_data.get("transportation", [])
        places = overture_data.get("places", [])
        
        # Calculate building metrics
        building_heights = [b.get("height", 0) for b in buildings]
        building_areas = [self._calculate_area(b.get("geometry", {})) for b in buildings]
        
        return {
            "building_characteristics": {
                "count": len(buildings),
                "density": len(buildings) / 100,  # per hectare
                "types": self._count_types(buildings, "building_type"),
                "avg_height": np.mean(building_heights) if building_heights else 0,
                "total_area": sum(building_areas),
                "floor_area_ratio": sum(building_areas) / 10000  # Total floor area / total land area
            },
            "road_characteristics": {
                "count": len(transportation),
                "density": len(transportation) / 100,
                "types": self._count_types(transportation, "road_type"),
                "connectivity": self._calculate_road_connectivity(transportation)
            },
            "amenity_characteristics": {
                "count": len(places),
                "density": len(places) / 100,
                "types": self._count_types(places, "place_type"),
                "diversity": self._calculate_amenity_diversity(places)
            }
        }
    
    def _generate_simulated_urban_features(self) -> Dict[str, Any]:
        """Generate simulated urban features for testing."""
        # Typical values for San Francisco Financial District
        return {
            "building_characteristics": {
                "count": 50,
                "density": 50.0,  # buildings per hectare
                "types": {
                    "commercial": 25,
                    "office": 15,
                    "residential": 8,
                    "mixed": 2
                },
                "avg_height": 45.0,  # meters
                "total_area": 75000.0,  # square meters
                "floor_area_ratio": 7.5  # typical for dense urban areas
            },
            "road_characteristics": {
                "count": 20,
                "density": 20.0,
                "types": {
                    "primary": 3,
                    "secondary": 7,
                    "tertiary": 10
                },
                "connectivity": 0.75
            },
            "amenity_characteristics": {
                "count": 30,
                "density": 30.0,
                "types": {
                    "restaurant": 12,
                    "cafe": 8,
                    "bank": 5,
                    "retail": 5
                },
                "diversity": 0.8
            }
        }
    
    def _calculate_area(self, geometry: Dict[str, Any]) -> float:
        """Calculate area of a geometry in square meters."""
        # Simplified area calculation - in real implementation, use proper geospatial libraries
        if geometry.get("type") == "Polygon" and "coordinates" in geometry:
            coords = geometry["coordinates"][0]  # Outer ring
            return abs(sum(x0*y1 - x1*y0 for ((x0, y0), (x1, y1)) in zip(coords, coords[1:] + [coords[0]]))) / 2
        return 0
    
    def _calculate_road_connectivity(self, transportation: List[Dict[str, Any]]) -> float:
        """Calculate road network connectivity score."""
        if not transportation:
            return 0.0
        
        # Count intersections and dead ends
        intersections = set()
        dead_ends = set()
        
        for road in transportation:
            if "geometry" in road and "coordinates" in road["geometry"]:
                coords = road["geometry"]["coordinates"]
                start, end = tuple(coords[0]), tuple(coords[-1])
                
                # Add to intersections if shared with another road
                if start in dead_ends:
                    intersections.add(start)
                    dead_ends.remove(start)
                else:
                    dead_ends.add(start)
                    
                if end in dead_ends:
                    intersections.add(end)
                    dead_ends.remove(end)
                else:
                    dead_ends.add(end)
        
        # Calculate connectivity ratio (intersections / total nodes)
        total_nodes = len(intersections) + len(dead_ends)
        return len(intersections) / total_nodes if total_nodes > 0 else 0
    
    def _calculate_amenity_diversity(self, places: List[Dict[str, Any]]) -> float:
        """Calculate Shannon diversity index for amenities."""
        if not places:
            return 0.0
            
        type_counts = {}
        total = len(places)
        
        for place in places:
            place_type = place.get("place_type", "unknown")
            type_counts[place_type] = type_counts.get(place_type, 0) + 1
        
        # Calculate Shannon diversity index
        diversity = 0
        for count in type_counts.values():
            p = count / total
            diversity -= p * np.log(p)
            
        return diversity
    
    def _calculate_environmental_scores(
        self,
        urban_features: Dict[str, Any],
        satellite_data: Dict[str, np.ndarray]
    ) -> Dict[str, float]:
        """Calculate environmental scores using urban features and satellite data."""
        base_scores = {
            "green_space": 0.0,
            "air_quality": 0.0,
            "water_bodies": 0.0,
            "urban_density": 0.0,
            "heat_island": 0.0
        }
        
        # Calculate scores from satellite indices
        if satellite_data:
            # Green space from NDVI
            if "ndvi" in satellite_data:
                ndvi = satellite_data["ndvi"]
                base_scores["green_space"] = float(np.clip(np.mean(ndvi[ndvi > 0]) + 0.5, 0, 1))
            
            # Water bodies from NDWI
            if "ndwi" in satellite_data:
                ndwi = satellite_data["ndwi"]
                base_scores["water_bodies"] = float(np.clip(np.mean(ndwi[ndwi > 0]) + 0.5, 0, 1))
            
            # Urban density from NDBI
            if "ndbi" in satellite_data:
                ndbi = satellite_data["ndbi"]
                base_scores["urban_density"] = float(np.clip(np.mean(ndbi[ndbi > 0]) + 0.5, 0, 1))
                
            # Heat island effect (combination of NDBI and vegetation cover)
            if "ndbi" in satellite_data and "ndvi" in satellite_data:
                heat_island = np.mean(satellite_data["ndbi"]) - np.mean(satellite_data["ndvi"])
                base_scores["heat_island"] = float(np.clip(heat_island + 0.5, 0, 1))
        
        # Adjust air quality based on urban features
        building_density = urban_features["building_characteristics"]["density"] / 100.0
        road_density = urban_features["road_characteristics"]["density"] / 100.0
        green_space = base_scores["green_space"]
        
        base_scores["air_quality"] = float(np.clip(
            1.0 - (
                0.4 * building_density +
                0.4 * road_density -
                0.2 * green_space
            ),
            0, 1
        ))
        
        return base_scores
    
    def _calculate_urban_metrics(
        self,
        urban_features: Dict[str, Any],
        satellite_data: Dict[str, np.ndarray]
    ) -> Dict[str, float]:
        """Calculate urban metrics from features and satellite data."""
        metrics = {
            "building_density": 0.0,
            "road_density": 0.0,
            "amenity_density": 0.0,
            "mixed_use_ratio": 0.0,
            "walkability": 0.0
        }
        
        # Building density (buildings per hectare)
        building_density = urban_features["building_characteristics"]["density"]
        metrics["building_density"] = min(building_density / 100.0, 1.0)
        
        # Road density (km per square km)
        road_density = urban_features["road_characteristics"]["density"]
        metrics["road_density"] = min(road_density / 50.0, 1.0)
        
        # Amenity density (amenities per hectare)
        amenity_density = urban_features["amenity_characteristics"]["density"]
        metrics["amenity_density"] = min(amenity_density / 30.0, 1.0)
        
        # Mixed use ratio (diversity of building types)
        building_types = urban_features["building_characteristics"]["types"]
        if building_types:
            type_counts = np.array(list(building_types.values()))
            total = np.sum(type_counts)
            if total > 0:
                proportions = type_counts / total
                metrics["mixed_use_ratio"] = float(-np.sum(proportions * np.log(proportions + 1e-10)))
        
        # Walkability score (combination of density metrics and connectivity)
        metrics["walkability"] = float(np.mean([
            metrics["amenity_density"],
            metrics["road_density"],
            urban_features["road_characteristics"].get("connectivity", 0.0),
            metrics["mixed_use_ratio"]
        ]))
        
        return metrics
    
    def _estimate_noise_levels(
        self,
        urban_features: Dict[str, Any],
        urban_metrics: Dict[str, float]
    ) -> Dict[str, float]:
        """Estimate noise levels based on urban features and metrics."""
        noise_levels = {
            "average": 0.0,
            "peak": 0.0,
            "variability": 0.0
        }
        
        # Base noise level from urban density
        base_noise = urban_metrics["building_density"] * 0.3 + urban_metrics["road_density"] * 0.7
        
        # Adjust for road types
        road_types = urban_features["road_characteristics"]["types"]
        if road_types:
            primary_roads = road_types.get("primary", 0)
            secondary_roads = road_types.get("secondary", 0)
            tertiary_roads = road_types.get("tertiary", 0)
            
            total_roads = primary_roads + secondary_roads + tertiary_roads
            if total_roads > 0:
                road_noise = (
                    primary_roads * 0.5 +
                    secondary_roads * 0.3 +
                    tertiary_roads * 0.2
                ) / total_roads
                base_noise = (base_noise + road_noise) / 2
        
        # Adjust for amenity density
        amenity_noise = urban_metrics["amenity_density"] * 0.4
        
        # Calculate final noise levels
        noise_levels["average"] = float(np.clip(base_noise, 0, 1))
        noise_levels["peak"] = float(np.clip(base_noise * 1.5 + amenity_noise, 0, 1))
        noise_levels["variability"] = float(np.clip(
            abs(noise_levels["peak"] - noise_levels["average"]) * 2,
            0, 1
        ))
        
        return noise_levels
    
    def _calculate_accessibility(self, urban_features: Dict[str, Any]) -> Dict[str, float]:
        """Calculate accessibility scores based on urban features."""
        scores = {
            "transit_access": 0.0,
            "walkability": 0.0,
            "amenity_access": 0.0,
            "connectivity": 0.0
        }
        
        # Transit access based on road network
        road_types = urban_features["road_characteristics"]["types"]
        if road_types:
            primary_roads = road_types.get("primary", 0)
            total_roads = sum(road_types.values())
            if total_roads > 0:
                scores["transit_access"] = float(np.clip(primary_roads / total_roads + 0.3, 0, 1))
        
        # Walkability based on road and amenity density
        road_density = urban_features["road_characteristics"]["density"] / 100.0
        amenity_density = urban_features["amenity_characteristics"]["density"] / 30.0
        scores["walkability"] = float(np.clip((road_density + amenity_density) / 2, 0, 1))
        
        # Amenity access based on amenity diversity and density
        amenity_types = urban_features["amenity_characteristics"]["types"]
        if amenity_types:
            type_counts = np.array(list(amenity_types.values()))
            total = np.sum(type_counts)
            if total > 0:
                diversity = -np.sum((type_counts / total) * np.log(type_counts / total + 1e-10))
                scores["amenity_access"] = float(np.clip(diversity * amenity_density, 0, 1))
        
        # Connectivity based on road network characteristics
        scores["connectivity"] = float(urban_features["road_characteristics"].get("connectivity", 0.0))
        
        return scores
    
    def _calculate_ambience_score(
        self,
        env_scores: Dict[str, float],
        urban_metrics: Dict[str, float],
        noise_levels: Dict[str, float],
        accessibility: Dict[str, float]
    ) -> float:
        """Calculate overall ambience score."""
        # Weights for different components
        weights = {
            "environmental": 0.35,
            "urban": 0.25,
            "noise": 0.20,
            "accessibility": 0.20
        }
        
        # Environmental component
        env_component = np.mean([
            env_scores["green_space"],
            env_scores["air_quality"],
            env_scores["water_bodies"],
            1 - env_scores["heat_island"]  # Inverse heat island effect
        ])
        
        # Urban component
        urban_component = np.mean([
            urban_metrics["mixed_use_ratio"],
            urban_metrics["walkability"],
            min(urban_metrics["building_density"], 0.8)  # Cap building density
        ])
        
        # Noise component (inverse, less noise is better)
        noise_component = 1 - np.mean([
            noise_levels["average"],
            noise_levels["peak"] * 0.7,  # Peak noise weighted less
            noise_levels["variability"] * 0.3  # Variability weighted least
        ])
        
        # Accessibility component
        access_component = np.mean([
            accessibility["transit_access"],
            accessibility["walkability"],
            accessibility["amenity_access"],
            accessibility["connectivity"]
        ])
        
        # Calculate weighted average
        ambience_score = (
            weights["environmental"] * env_component +
            weights["urban"] * urban_component +
            weights["noise"] * noise_component +
            weights["accessibility"] * access_component
        )
        
        return float(np.clip(ambience_score * 10, 0, 10))  # Scale to 0-10
    
    def _generate_recommendations(
        self,
        env_scores: Dict[str, float],
        urban_metrics: Dict[str, float],
        noise_levels: Dict[str, float],
        accessibility: Dict[str, float],
        ambience_score: float
    ) -> List[str]:
        """Generate recommendations based on analysis results."""
        recommendations = []
        
        # Environmental recommendations
        if env_scores["green_space"] < 0.4:
            recommendations.append(
                "Increase green space through urban parks, street trees, and green roofs"
            )
        if env_scores["heat_island"] > 0.6:
            recommendations.append(
                "Address urban heat island effect through increased vegetation and reflective surfaces"
            )
        if env_scores["air_quality"] < 0.5:
            recommendations.append(
                "Improve air quality through traffic reduction and green barriers"
            )
        
        # Urban form recommendations
        if urban_metrics["mixed_use_ratio"] < 0.5:
            recommendations.append(
                "Promote mixed-use development to increase diversity of building types"
            )
        if urban_metrics["building_density"] < 0.3:
            recommendations.append(
                "Consider increasing building density while maintaining open spaces"
            )
        elif urban_metrics["building_density"] > 0.8:
            recommendations.append(
                "Ensure adequate open spaces and setbacks between buildings"
            )
        
        # Amenity recommendations
        if urban_metrics["amenity_density"] < 0.4:
            recommendations.append(
                "Increase diversity of amenities to improve neighborhood services"
            )
        
        # Accessibility recommendations
        if accessibility["transit_access"] < 0.5:
            recommendations.append(
                "Improve public transit access through additional routes or stops"
            )
        if accessibility["walkability"] < 0.6:
            recommendations.append(
                "Enhance pedestrian infrastructure and street connectivity"
            )
        if accessibility["connectivity"] < 0.5:
            recommendations.append(
                "Improve street network connectivity to reduce travel distances"
            )
        
        # Noise recommendations
        if noise_levels["average"] > 0.7:
            recommendations.append(
                "Implement noise reduction measures such as barriers or traffic calming"
            )
        if noise_levels["peak"] > 0.8:
            recommendations.append(
                "Address sources of peak noise through zoning or operational restrictions"
            )
        
        return recommendations
    
    def _count_types(self, features: List[Dict[str, Any]], type_field: str) -> Dict[str, int]:
        """Helper method to count feature types."""
        type_counts = {}
        for feature in features:
            feature_type = feature.get(type_field, "unknown")
            type_counts[feature_type] = type_counts.get(feature_type, 0) + 1
        return type_counts

def simulate_location_data() -> Dict[str, Any]:
    """Generate simulated location data for the San Francisco Financial District."""
    return {
        "name": "SF Financial District",
        "bbox": [-122.4018, 37.7914, -122.3928, 37.7994],  # SF Financial District bounding box
        "description": "San Francisco's Financial District, known for its skyscrapers and business activity",
        "metadata": {
            "city": "San Francisco",
            "state": "California",
            "country": "United States",
            "timezone": "America/Los_Angeles"
        }
    }

async def main():
    """Run the location analysis example."""
    # Initialize configuration
    config = Config(
        storage_path=os.path.join(project_root, "examples/data"),
        hot_memory_size=1000,  # 1GB
        warm_memory_size=5000,  # 5GB
        cold_memory_size=10000  # 10GB
    )
    
    # Create analyzer instance
    analyzer = LocationDataAnalyzer(config)
    
    # Analyze the Financial District location
    location_data = simulate_location_data()
    insights = await analyzer.analyze_location(
        location_data,
        location_data['bbox'],
        "2024-01-01",
        "2024-12-31"
    )
    
    # Print results
    print("\nLocation Analysis Results:")
    print("-" * 50)
    print(f"Location: {insights.get('location_name')}")
    print(f"Location ID: {insights.get('location_id')}")
    print(f"Analysis Timestamp: {insights.get('timestamp')}")
    print()
    
    if "error" in insights:
        print(f"Error: {insights['error']}")
    else:
        print(f"Ambience Score: {insights['ambience_score']:.2f}/10")
        print("\nEnvironmental Scores:")
        for key, value in insights['environmental_scores'].items():
            print(f"  {key.replace('_', ' ').title()}: {value:.2f}")
        
        print("\nUrban Metrics:")
        for key, value in insights['urban_metrics'].items():
            print(f"  {key.replace('_', ' ').title()}: {value:.2f}")
        
        print("\nNoise Levels:")
        for key, value in insights['noise_levels'].items():
            print(f"  {key.replace('_', ' ').title()}: {value:.2f}")
        
        print("\nAccessibility Scores:")
        for key, value in insights['accessibility_scores'].items():
            print(f"  {key.replace('_', ' ').title()}: {value:.2f}")
        
        print("\nRecommendations:")
        for i, rec in enumerate(insights['recommendations'], 1):
            print(f"{i}. {rec}")

if __name__ == "__main__":
    asyncio.run(main()) 