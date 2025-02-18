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
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Tuple
import yaml

import numpy as np
import rasterio
import duckdb

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    print(f"Added {project_root} to Python path")
    sys.path.append(project_root)

from memories import Config
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
    
    def __init__(self, config: Any):
        """Initialize the analyzer with configuration.
        
        Args:
            config: Either a Config object or a dictionary containing configuration
        """
        # Handle both Config objects and dictionaries
        if isinstance(config, dict):
            self.config = config
            data_paths = config.get('data_paths', {})
            self.overture_dir = Path(data_paths.get('overture_data', 'examples/data/overture'))
            self.satellite_dir = Path(data_paths.get('satellite_data', 'examples/data/satellite'))
        else:
            self.config = config.config
            self.overture_dir = Path(self.config['data']['overture_path'])
            self.satellite_dir = Path(self.config['data']['satellite_path'])
        
        # Create directories if they don't exist
        self.overture_dir.mkdir(parents=True, exist_ok=True)
        self.satellite_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize DuckDB connection
        self.con = duckdb.connect(database=":memory:")
        self.con.execute("INSTALL spatial;")
        self.con.execute("LOAD spatial;")
    
    def download_overture_data(self, bbox: Dict[str, float]) -> Dict[str, bool]:
        """Download Overture data for a given bounding box.
        
        Args:
            bbox: Bounding box dictionary with xmin, ymin, xmax, ymax
            
        Returns:
            Dictionary of theme names and their download status
        """
        # Themes to download with their specific columns
        themes = {
            'buildings': """
                id,
                type as building_type,
                height,
                bbox.xmin,
                bbox.ymin,
                bbox.xmax,
                bbox.ymax,
                geometry
            """,
            'places': """
                id,
                type as place_type,
                confidence,
                bbox.xmin,
                bbox.ymin,
                bbox.xmax,
                bbox.ymax,
                geometry
            """,
            'transportation': """
                id,
                type as road_type,
                bbox.xmin,
                bbox.ymin,
                bbox.xmax,
                bbox.ymax,
                geometry
            """
        }
        
        results = {}
        for theme, columns in themes.items():
            theme_dir = self.overture_dir / theme
            theme_dir.mkdir(parents=True, exist_ok=True)
            output_file = theme_dir / f"{theme}.geojsonseq"
            
            try:
                # Create optimized query with index hint and feature limit
                query = f"""
                COPY (
                    SELECT
                        {columns}
                    FROM read_json_auto(
                        'examples/data/overture/{theme}/{theme}.geojsonseq',
                        format='newline_delimited'
                    )
                    WHERE bbox.xmin >= {bbox['xmin']}
                    AND bbox.xmin <= {bbox['xmax']}
                    AND bbox.ymin >= {bbox['ymin']}
                    AND bbox.ymin <= {bbox['ymax']}
                    LIMIT 100  -- Limit to 100 features per category
                ) TO '{output_file}' WITH (FORMAT GDAL, DRIVER 'GeoJSONSeq');
                """
                
                # Execute query with optimized memory settings
                self.con.execute("SET memory_limit='1GB';")  # Reduced memory limit
                self.con.execute("SET threads=4;")  # Limit thread usage
                self.con.execute(query)
                logger.info(f"Successfully downloaded {theme} data to {output_file}")
                results[theme] = True
                
            except Exception as e:
                logger.error(f"Error downloading {theme} data: {e}")
                results[theme] = False
        
        return results
    
    async def analyze_location(
        self,
        bbox: List[float],
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """Analyze location using previously downloaded data."""
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
            
            # Download Overture data
            download_results = self.download_overture_data(bbox_dict)
            
            # Load Overture data from downloaded files
            overture_data = {}
            for theme in ['buildings', 'places', 'transportation']:
                theme_file = self.overture_dir / theme / f"{theme}.geojsonseq"
                if theme_file.exists():
                    try:
                        query = f"""
                        SELECT *
                        FROM read_json_auto('{theme_file}', format='newline_delimited')
                        LIMIT 1000;
                        """
                        df = self.con.execute(query).fetchdf()
                        overture_data[theme] = df.to_dict('records')
                        logger.info(f"Found {len(overture_data[theme])} {theme} features")
                    except Exception as e:
                        logger.warning(f"Error loading {theme} data: {str(e)}")
                        overture_data[theme] = []
                else:
                    overture_data[theme] = []
            
            # Generate simulated data if no real data available
            if not overture_data or not any(overture_data.values()):
                logger.warning("No Overture data found, using simulated data")
                overture_data = self._generate_simulated_urban_features()
            
            # Analyze urban features
            urban_features = self._analyze_urban_features(overture_data)
            
            # Calculate environmental scores
            env_scores = {
                "green_space": 0.83,  # Simulated scores
                "air_quality": 1.00,
                "water_bodies": 0.57,
                "urban_density": 0.66,
                "heat_island": 0.29
            }
            
            # Calculate urban metrics
            urban_metrics = {
                "building_density": 0.0,  # Simulated scores
                "road_density": 0.0,
                "amenity_density": 0.0,
                "mixed_use_ratio": 0.0,
                "walkability": 0.0
            }
            
            # Calculate noise levels
            noise_levels = {
                "average": 0.0,  # Simulated scores
                "peak": 0.0,
                "variability": 0.0
            }
            
            # Calculate accessibility scores
            accessibility = {
                "transit_access": 0.0,  # Simulated scores
                "walkability": 0.0,
                "amenity_access": 0.0,
                "connectivity": 0.0
            }
            
            # Calculate overall ambience score (weighted average of all scores)
            weights = {
                'environmental': 0.4,
                'urban': 0.3,
                'noise': 0.2,
                'accessibility': 0.1
            }
            
            # Calculate component averages
            env_avg = sum(env_scores.values()) / len(env_scores) if env_scores else 0.0
            urban_avg = sum(urban_metrics.values()) / len(urban_metrics) if urban_metrics else 0.0
            noise_avg = 1 - (sum(noise_levels.values()) / len(noise_levels)) if noise_levels else 0.0
            access_avg = sum(accessibility.values()) / len(accessibility) if accessibility else 0.0
            
            # Calculate weighted score
            ambience_score = (
                weights['environmental'] * env_avg * 10 +
                weights['urban'] * urban_avg * 10 +
                weights['noise'] * noise_avg * 10 +
                weights['accessibility'] * access_avg * 10
            )
            
            # Generate recommendations based on scores
            recommendations = [
                "Promote mixed-use development to increase activity and vibrancy",
                "Increase building density while maintaining open spaces",
                "Enhance public transit access and frequency",
                "Improve pedestrian infrastructure and walkability",
                "Add more green spaces and urban vegetation"
            ]
            
            return {
                "location_id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat(),
                "bbox": bbox,
                "analysis_period": {
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat()
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
                "bbox": bbox,
                "error": str(e),
                "ambience_score": 0.0,
                "environmental_scores": {},
                "urban_metrics": {},
                "noise_levels": {},
                "accessibility_scores": {},
                "recommendations": ["Unable to generate recommendations due to error"]
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
                    # Set target shape from first band
                    if "target_shape" not in satellite_data:
                        satellite_data["target_shape"] = (100, 100)  # Fixed size for consistency
                    satellite_data["red"] = self._resize_array(
                        satellite_data["red"], 
                        satellite_data["target_shape"]
                    )
                    logger.info(f"Loaded red band with shape {satellite_data['red'].shape}")
            else:
                # Simulate data if file doesn't exist
                logger.warning("Red band file not found, using simulated data")
                satellite_data["target_shape"] = (100, 100)
                satellite_data["red"] = np.random.normal(1500, 500, satellite_data["target_shape"])
                
            # Load NIR band (B08)
            nir_path = self.satellite_dir / "B08.tif"
            if nir_path.exists():
                with rasterio.open(nir_path) as src:
                    satellite_data["nir"] = src.read(1)
                    satellite_data["nir"] = self._resize_array(
                        satellite_data["nir"], 
                        satellite_data["target_shape"]
                    )
                    logger.info(f"Loaded NIR band with shape {satellite_data['nir'].shape}")
            else:
                # Simulate data if file doesn't exist
                logger.warning("NIR band file not found, using simulated data")
                satellite_data["nir"] = np.random.normal(2000, 600, satellite_data["target_shape"])
                
            # Load SWIR band (B11)
            swir_path = self.satellite_dir / "B11.tif"
            if swir_path.exists():
                with rasterio.open(swir_path) as src:
                    satellite_data["swir"] = src.read(1)
                    satellite_data["swir"] = self._resize_array(
                        satellite_data["swir"], 
                        satellite_data["target_shape"]
                    )
                    logger.info(f"Loaded SWIR band with shape {satellite_data['swir'].shape}")
            else:
                # Simulate data if file doesn't exist
                logger.warning("SWIR band file not found, using simulated data")
                satellite_data["swir"] = np.random.normal(1800, 400, satellite_data["target_shape"])
            
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
    
    def _resize_array(self, array: np.ndarray, target_shape: Tuple[int, int]) -> np.ndarray:
        """Resize array to target shape using simple interpolation."""
        if array.shape == target_shape:
            return array
            
        # Use simple numpy interpolation
        h, w = array.shape
        th, tw = target_shape
        
        # Create coordinate grids
        x = np.linspace(0, w-1, tw)
        y = np.linspace(0, h-1, th)
        
        # Create interpolation function
        from scipy.interpolate import RectBivariateSpline
        interp = RectBivariateSpline(np.arange(h), np.arange(w), array)
        
        # Interpolate
        return interp(y, x)
    
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
        if not overture_data or not isinstance(overture_data, dict):
            # Generate simulated data for testing
            logger.warning("No valid Overture data found, using simulated urban features")
            return self._generate_simulated_urban_features()
            
        buildings = overture_data.get("buildings", [])
        transportation = overture_data.get("transportation", [])
        places = overture_data.get("places", [])
        
        if not isinstance(buildings, list):
            buildings = []
        if not isinstance(transportation, list):
            transportation = []
        if not isinstance(places, list):
            places = []
        
        # Calculate building metrics
        building_heights = [b.get("height", 0) for b in buildings if isinstance(b, dict)]
        building_areas = [self._calculate_area(b.get("geometry", {})) for b in buildings if isinstance(b, dict)]
        
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
    
    def _count_types(self, features: List[Dict[str, Any]], type_field: str) -> Dict[str, int]:
        """Helper method to count feature types."""
        type_counts = {}
        for feature in features:
            feature_type = feature.get(type_field, "unknown")
            type_counts[feature_type] = type_counts.get(feature_type, 0) + 1
        return type_counts

async def main():
    """Main execution function."""
    # Load configuration
    config_path = os.path.join(os.path.dirname(__file__), "config", "db_config.yml")
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # Create data directories
    data_dir = config.get('data_paths', {}).get('overture_data', 'examples/data/overture')
    os.makedirs(data_dir, exist_ok=True)

    # Initialize location analyzer with config
    analyzer = LocationDataAnalyzer(config)

    # Define location to analyze (San Francisco Financial District)
    location = {
        'name': 'San Francisco Financial District',
        'bbox': [-122.4053, 37.7881, -122.3981, 37.7937]  # [min_lon, min_lat, max_lon, max_lat]
    }

    # Set time range for analysis (last 30 days)
    end_time = datetime.now()
    start_time = end_time - timedelta(days=30)

    try:
        # Analyze location
        results = await analyzer.analyze_location(
            location['bbox'],
            start_time=start_time,
            end_time=end_time
        )

        # Print analysis results
        print(f"\nLocation Analysis Report for {location['name']}")
        print("-" * 50)
        print(f"Ambience Score: {results['ambience_score']:.2f}/10")
        
        print("\nEnvironmental Scores:")
        for metric, score in results['environmental_scores'].items():
            print(f"- {metric}: {score:.2f}")
        
        print("\nUrban Metrics:")
        for metric, score in results['urban_metrics'].items():
            print(f"- {metric}: {score:.2f}")
        
        print("\nNoise Levels:")
        for metric, level in results['noise_levels'].items():
            print(f"- {metric}: {level:.2f}")
        
        print("\nAccessibility Scores:")
        for metric, score in results['accessibility_scores'].items():
            print(f"- {metric}: {score:.2f}")
        
        print("\nRecommendations:")
        for rec in results['recommendations']:
            print(f"- {rec}")

    except Exception as e:
        print(f"Error during analysis: {str(e)}")
        raise

if __name__ == "__main__":
    # Add parent directories to Python path
    sys.path.extend([
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ])
    asyncio.run(main()) 