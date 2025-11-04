"""Climate analysis for Earth memory."""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import numpy as np

logger = logging.getLogger(__name__)


class ClimateAnalyzer:
    """Analyzes climate patterns and weather data."""

    def __init__(self, data_source: Optional[str] = "era5"):
        """Initialize climate analyzer.

        Args:
            data_source: Climate data source (era5, worldclim, etc.)
        """
        self.data_source = data_source
        self.logger = logging.getLogger(__name__)

    async def analyze(
        self,
        location: Dict[str, float],
        time_range: Optional[Dict[str, str]] = None,
        include_forecast: bool = False
    ) -> Dict[str, Any]:
        """Analyze climate at location.

        Args:
            location: Dict with 'lat' and 'lon' keys
            time_range: Optional time range with 'start' and 'end' keys
            include_forecast: Include future forecast

        Returns:
            Dict with climate analysis results
        """
        lat = location.get("lat")
        lon = location.get("lon")

        if lat is None or lon is None:
            raise ValueError("Location must contain 'lat' and 'lon' keys")

        self.logger.info(f"Analyzing climate at ({lat}, {lon})")

        try:
            # Get historical climate data
            historical_data = await self._get_historical_data(
                lat, lon, time_range
            )

            # Calculate climate metrics
            metrics = self._calculate_climate_metrics(historical_data)

            # Classify climate zone
            climate_zone = self._classify_climate_zone(metrics)

            # Identify patterns and trends
            patterns = self._identify_patterns(historical_data)

            # Assess risks
            risks = self._assess_climate_risks(metrics, patterns)

            result = {
                "location": location,
                "climate_zone": climate_zone,
                "temperature": {
                    "annual_mean": metrics["mean_temp"],
                    "annual_range": metrics["temp_range"],
                    "warmest_month": metrics["warmest_month"],
                    "coldest_month": metrics["coldest_month"],
                    "trend": patterns.get("temperature_trend")
                },
                "precipitation": {
                    "annual_total": metrics["annual_precipitation"],
                    "wettest_month": metrics["wettest_month"],
                    "driest_month": metrics["driest_month"],
                    "trend": patterns.get("precipitation_trend")
                },
                "humidity": {
                    "mean": metrics["mean_humidity"],
                    "seasonal_variation": metrics["humidity_variation"]
                },
                "wind": {
                    "mean_speed": metrics["mean_wind_speed"],
                    "dominant_direction": metrics["dominant_wind_direction"]
                },
                "extremes": {
                    "heat_wave_days": metrics["heat_wave_days"],
                    "frost_days": metrics["frost_days"],
                    "heavy_rain_events": metrics["heavy_rain_events"]
                },
                "patterns": patterns,
                "risks": risks,
                "analysis_metadata": {
                    "time_range": time_range,
                    "data_source": self.data_source
                }
            }

            # Add forecast if requested
            if include_forecast:
                forecast = await self._generate_forecast(lat, lon)
                result["forecast"] = forecast

            return result

        except Exception as e:
            self.logger.error(f"Climate analysis error: {str(e)}", exc_info=True)
            raise

    async def _get_historical_data(
        self,
        lat: float,
        lon: float,
        time_range: Optional[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Get historical climate data.

        Args:
            lat: Latitude
            lon: Longitude
            time_range: Time range dict

        Returns:
            Historical climate data
        """
        # Simulate historical data retrieval
        # In production, fetch from ERA5, WorldClim, etc.

        # Generate synthetic data for demonstration
        months = 12
        base_temp = 15 + lat * 0.5  # Temperature varies with latitude

        temperature = base_temp + 10 * np.sin(np.arange(months) * 2 * np.pi / 12)
        precipitation = 50 + 30 * np.cos(np.arange(months) * 2 * np.pi / 12) + 20
        humidity = 60 + 15 * np.sin(np.arange(months) * 2 * np.pi / 12)

        return {
            "temperature": temperature,
            "precipitation": precipitation,
            "humidity": humidity,
            "months": months
        }

    def _calculate_climate_metrics(
        self,
        historical_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate climate metrics from historical data.

        Args:
            historical_data: Historical climate data

        Returns:
            Climate metrics
        """
        temperature = historical_data["temperature"]
        precipitation = historical_data["precipitation"]
        humidity = historical_data["humidity"]

        metrics = {
            "mean_temp": float(np.mean(temperature)),
            "temp_range": float(np.max(temperature) - np.min(temperature)),
            "warmest_month": int(np.argmax(temperature) + 1),
            "coldest_month": int(np.argmin(temperature) + 1),
            "annual_precipitation": float(np.sum(precipitation)),
            "wettest_month": int(np.argmax(precipitation) + 1),
            "driest_month": int(np.argmin(precipitation) + 1),
            "mean_humidity": float(np.mean(humidity)),
            "humidity_variation": float(np.std(humidity)),
            "mean_wind_speed": 4.5,  # Placeholder
            "dominant_wind_direction": "west",  # Placeholder
            "heat_wave_days": 15,  # Placeholder
            "frost_days": 20,  # Placeholder
            "heavy_rain_events": 8  # Placeholder
        }

        return metrics

    def _classify_climate_zone(self, metrics: Dict[str, Any]) -> str:
        """Classify climate zone based on Köppen-Geiger system.

        Args:
            metrics: Climate metrics

        Returns:
            Climate zone classification
        """
        mean_temp = metrics["mean_temp"]
        annual_precip = metrics["annual_precipitation"]

        # Simplified Köppen-Geiger classification
        if mean_temp >= 18:
            if annual_precip >= 1500:
                return "Tropical Rainforest (Af)"
            elif annual_precip >= 500:
                return "Tropical Monsoon (Am)"
            else:
                return "Tropical Savanna (Aw)"
        elif mean_temp >= 10:
            if annual_precip >= 1000:
                return "Temperate Oceanic (Cfb)"
            elif annual_precip >= 500:
                return "Humid Subtropical (Cfa)"
            else:
                return "Mediterranean (Csa)"
        elif mean_temp >= 0:
            if annual_precip >= 500:
                return "Humid Continental (Dfa)"
            else:
                return "Subarctic (Dfc)"
        else:
            return "Polar Tundra (ET)"

    def _identify_patterns(
        self,
        historical_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Identify climate patterns and trends.

        Args:
            historical_data: Historical climate data

        Returns:
            Patterns and trends
        """
        temperature = historical_data["temperature"]
        precipitation = historical_data["precipitation"]

        # Calculate trends (simplified linear regression)
        months = np.arange(len(temperature))

        # Temperature trend
        temp_slope = np.polyfit(months, temperature, 1)[0]
        if temp_slope > 0.1:
            temp_trend = "warming"
        elif temp_slope < -0.1:
            temp_trend = "cooling"
        else:
            temp_trend = "stable"

        # Precipitation trend
        precip_slope = np.polyfit(months, precipitation, 1)[0]
        if precip_slope > 1:
            precip_trend = "increasing"
        elif precip_slope < -1:
            precip_trend = "decreasing"
        else:
            precip_trend = "stable"

        return {
            "temperature_trend": temp_trend,
            "temperature_change_per_decade": float(temp_slope * 120),
            "precipitation_trend": precip_trend,
            "precipitation_change_per_decade": float(precip_slope * 120),
            "seasonality": {
                "strong": True,
                "dominant_season": "summer"
            },
            "variability": {
                "temperature": "moderate",
                "precipitation": "high"
            }
        }

    def _assess_climate_risks(
        self,
        metrics: Dict[str, Any],
        patterns: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess climate-related risks.

        Args:
            metrics: Climate metrics
            patterns: Climate patterns

        Returns:
            Risk assessments
        """
        risks = {}

        # Heat stress risk
        if metrics["mean_temp"] > 30 or metrics["heat_wave_days"] > 30:
            risks["heat_stress"] = "high"
        elif metrics["mean_temp"] > 25:
            risks["heat_stress"] = "moderate"
        else:
            risks["heat_stress"] = "low"

        # Flooding risk
        if metrics["heavy_rain_events"] > 15 or metrics["annual_precipitation"] > 2000:
            risks["flooding"] = "high"
        elif metrics["heavy_rain_events"] > 8:
            risks["flooding"] = "moderate"
        else:
            risks["flooding"] = "low"

        # Drought risk
        if metrics["annual_precipitation"] < 400:
            risks["drought"] = "high"
        elif metrics["annual_precipitation"] < 600:
            risks["drought"] = "moderate"
        else:
            risks["drought"] = "low"

        # Cold stress risk
        if metrics["frost_days"] > 100:
            risks["cold_stress"] = "high"
        elif metrics["frost_days"] > 50:
            risks["cold_stress"] = "moderate"
        else:
            risks["cold_stress"] = "low"

        # Overall climate vulnerability
        high_risks = sum(1 for risk in risks.values() if risk == "high")
        if high_risks >= 2:
            risks["overall_vulnerability"] = "high"
        elif high_risks == 1:
            risks["overall_vulnerability"] = "moderate"
        else:
            risks["overall_vulnerability"] = "low"

        return risks

    async def _generate_forecast(
        self,
        lat: float,
        lon: float,
        days_ahead: int = 7
    ) -> Dict[str, Any]:
        """Generate climate forecast.

        Args:
            lat: Latitude
            lon: Longitude
            days_ahead: Days to forecast

        Returns:
            Forecast data
        """
        # Placeholder forecast
        forecast = {
            "forecast_days": days_ahead,
            "daily_forecast": []
        }

        base_temp = 20
        for day in range(days_ahead):
            forecast["daily_forecast"].append({
                "day": day + 1,
                "temperature_max": base_temp + np.random.normal(0, 3),
                "temperature_min": base_temp - 5 + np.random.normal(0, 2),
                "precipitation_mm": max(0, np.random.normal(2, 5)),
                "conditions": np.random.choice(["sunny", "partly_cloudy", "cloudy", "rainy"])
            })

        return forecast
