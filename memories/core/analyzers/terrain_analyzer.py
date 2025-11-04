"""Terrain analysis for Earth memory."""

import logging
from typing import Dict, Any, Optional, List
import numpy as np

logger = logging.getLogger(__name__)


class TerrainAnalyzer:
    """Analyzes terrain characteristics using elevation data."""

    def __init__(self, data_source: Optional[str] = "srtm"):
        """Initialize terrain analyzer.

        Args:
            data_source: Elevation data source (srtm, aster, etc.)
        """
        self.data_source = data_source
        self.logger = logging.getLogger(__name__)

    async def analyze(
        self,
        location: Dict[str, float],
        resolution: str = "medium",
        radius: float = 1000
    ) -> Dict[str, Any]:
        """Analyze terrain at location.

        Args:
            location: Dict with 'lat' and 'lon' keys
            resolution: Resolution level (low, medium, high)
            radius: Analysis radius in meters

        Returns:
            Dict with terrain analysis results
        """
        lat = location.get("lat")
        lon = location.get("lon")

        if lat is None or lon is None:
            raise ValueError("Location must contain 'lat' and 'lon' keys")

        self.logger.info(f"Analyzing terrain at ({lat}, {lon}) with radius {radius}m")

        try:
            # Get elevation data
            elevation_data = await self._get_elevation_data(lat, lon, radius, resolution)

            # Calculate terrain metrics
            metrics = self._calculate_terrain_metrics(elevation_data)

            # Classify terrain type
            terrain_type = self._classify_terrain(metrics)

            # Assess development suitability
            suitability = self._assess_suitability(metrics)

            return {
                "location": location,
                "elevation": metrics["mean_elevation"],
                "elevation_range": {
                    "min": metrics["min_elevation"],
                    "max": metrics["max_elevation"]
                },
                "slope": {
                    "mean": metrics["mean_slope"],
                    "max": metrics["max_slope"],
                    "category": metrics["slope_category"]
                },
                "aspect": {
                    "dominant": metrics["dominant_aspect"],
                    "distribution": metrics["aspect_distribution"]
                },
                "roughness": metrics["roughness"],
                "terrain_type": terrain_type,
                "suitability": suitability,
                "analysis_metadata": {
                    "resolution": resolution,
                    "radius_meters": radius,
                    "data_source": self.data_source
                }
            }

        except Exception as e:
            self.logger.error(f"Terrain analysis error: {str(e)}", exc_info=True)
            raise

    async def _get_elevation_data(
        self,
        lat: float,
        lon: float,
        radius: float,
        resolution: str
    ) -> np.ndarray:
        """Get elevation data for area.

        Args:
            lat: Latitude
            lon: Longitude
            radius: Radius in meters
            resolution: Resolution level

        Returns:
            Elevation data array
        """
        # Simulate elevation data retrieval
        # In production, this would fetch from SRTM, ASTER, or similar
        resolution_samples = {
            "low": 50,
            "medium": 100,
            "high": 200
        }

        samples = resolution_samples.get(resolution, 100)

        # Generate synthetic elevation data for demonstration
        # In production, replace with actual data source API calls
        x = np.linspace(-radius, radius, samples)
        y = np.linspace(-radius, radius, samples)
        X, Y = np.meshgrid(x, y)

        # Simulate terrain with some variation
        base_elevation = 100 + lat * 10  # Varies with latitude
        elevation = base_elevation + 20 * np.sin(X/200) + 30 * np.cos(Y/150)
        elevation += np.random.normal(0, 5, elevation.shape)  # Add noise

        return elevation

    def _calculate_terrain_metrics(self, elevation_data: np.ndarray) -> Dict[str, Any]:
        """Calculate terrain metrics from elevation data.

        Args:
            elevation_data: Elevation data array

        Returns:
            Dict with terrain metrics
        """
        # Basic statistics
        metrics = {
            "mean_elevation": float(np.mean(elevation_data)),
            "min_elevation": float(np.min(elevation_data)),
            "max_elevation": float(np.max(elevation_data)),
            "std_elevation": float(np.std(elevation_data))
        }

        # Calculate slopes
        dy, dx = np.gradient(elevation_data)
        slopes = np.sqrt(dx**2 + dy**2)

        metrics["mean_slope"] = float(np.mean(slopes))
        metrics["max_slope"] = float(np.max(slopes))
        metrics["std_slope"] = float(np.std(slopes))

        # Classify slope
        if metrics["mean_slope"] < 5:
            metrics["slope_category"] = "flat"
        elif metrics["mean_slope"] < 15:
            metrics["slope_category"] = "gentle"
        elif metrics["mean_slope"] < 30:
            metrics["slope_category"] = "moderate"
        else:
            metrics["slope_category"] = "steep"

        # Calculate aspects
        aspects = np.arctan2(dy, dx) * 180 / np.pi
        metrics["aspect_distribution"] = {
            "north": float(np.sum((aspects >= -22.5) & (aspects < 22.5)) / aspects.size),
            "east": float(np.sum((aspects >= 22.5) & (aspects < 67.5)) / aspects.size),
            "south": float(np.sum((aspects >= 67.5) & (aspects < 112.5)) / aspects.size),
            "west": float(np.sum((aspects >= 112.5) & (aspects < 157.5)) / aspects.size)
        }

        # Dominant aspect
        metrics["dominant_aspect"] = max(
            metrics["aspect_distribution"],
            key=metrics["aspect_distribution"].get
        )

        # Calculate roughness (standard deviation of elevation)
        metrics["roughness"] = float(np.std(elevation_data))

        return metrics

    def _classify_terrain(self, metrics: Dict[str, Any]) -> str:
        """Classify terrain type based on metrics.

        Args:
            metrics: Terrain metrics

        Returns:
            Terrain type classification
        """
        slope = metrics["mean_slope"]
        roughness = metrics["roughness"]

        if slope < 5 and roughness < 10:
            return "plains"
        elif slope < 15 and roughness < 20:
            return "rolling_hills"
        elif slope < 30:
            return "hilly"
        elif slope < 45:
            return "mountainous"
        else:
            return "alpine"

    def _assess_suitability(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Assess terrain suitability for various uses.

        Args:
            metrics: Terrain metrics

        Returns:
            Suitability assessments
        """
        slope = metrics["mean_slope"]
        roughness = metrics["roughness"]

        suitability = {}

        # Building development
        if slope < 5 and roughness < 10:
            suitability["building_development"] = "excellent"
        elif slope < 15 and roughness < 20:
            suitability["building_development"] = "good"
        elif slope < 30:
            suitability["building_development"] = "moderate"
        else:
            suitability["building_development"] = "poor"

        # Agriculture
        if slope < 8 and roughness < 15:
            suitability["agriculture"] = "excellent"
        elif slope < 20:
            suitability["agriculture"] = "good"
        else:
            suitability["agriculture"] = "poor"

        # Recreation
        if slope > 15 and slope < 40:
            suitability["outdoor_recreation"] = "excellent"
        elif slope < 15:
            suitability["outdoor_recreation"] = "good"
        else:
            suitability["outdoor_recreation"] = "moderate"

        # Infrastructure
        if slope < 10 and roughness < 15:
            suitability["infrastructure"] = "excellent"
        elif slope < 20:
            suitability["infrastructure"] = "good"
        else:
            suitability["infrastructure"] = "challenging"

        return suitability

    def analyze_viewshed(
        self,
        location: Dict[str, float],
        observer_height: float = 1.7
    ) -> Dict[str, Any]:
        """Analyze viewshed from location.

        Args:
            location: Observer location
            observer_height: Observer height in meters

        Returns:
            Viewshed analysis
        """
        # Placeholder for viewshed analysis
        return {
            "visible_area_km2": 15.5,
            "max_visible_distance_km": 8.2,
            "visibility_score": 0.75,
            "obstructions": ["hills", "buildings"]
        }
