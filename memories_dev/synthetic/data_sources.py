from typing import List, Dict, Any, Optional
import numpy as np
import requests
import rasterio
import netCDF4
import ee  # Google Earth Engine
import sentinelhub  # Sentinel Hub
from datetime import datetime, timedelta
from pathlib import Path
from .synthesis import DataSource
import os
import json

class WeatherDataSource(DataSource):
    """Handler for weather and climate data."""

    def __init__(
        self,
        name: str = "weather",
        resolution: float = 1000.0,  # 1km resolution
        api_key: Optional[str] = None,
        variables: List[str] = ["temperature", "precipitation", "humidity"]
    ):
        super().__init__(name, resolution)
        self.api_key = api_key
        self.variables = variables

    def load_data(
        self,
        coordinates: tuple,
        timestamp: datetime,
        window_size: tuple = (1, 1)
    ) -> np.ndarray:
        """Load weather data for location and time."""
        lat, lon = coordinates

        # Example using OpenWeatherMap API
        if self.api_key:
            url = f"https://api.openweathermap.org/data/2.5/weather"
            params = {
                "lat": lat,
                "lon": lon,
                "appid": self.api_key,
                "units": "metric"
            }
            response = requests.get(url, params=params)
            data = response.json()

            # Extract relevant variables
            weather_data = []
            if "temperature" in self.variables:
                weather_data.append(data["main"]["temp"])
            if "precipitation" in self.variables:
                weather_data.append(data.get("rain", {}).get("1h", 0))
            if "humidity" in self.variables:
                weather_data.append(data["main"]["humidity"])

            return np.array(weather_data).reshape(-1, 1, 1)
        else:
            # Placeholder data if no API key
            return np.random.rand(len(self.variables), 1, 1)

    def preprocess(self, data: np.ndarray) -> np.ndarray:
        """Normalize weather data."""
        return (data - np.mean(data)) / (np.std(data) + 1e-8)

class ElevationDataSource(DataSource):
    """Handler for elevation and terrain data."""

    def __init__(
        self,
        name: str = "elevation",
        resolution: float = 30.0,  # 30m resolution (SRTM)
        data_path: Path = None
    ):
        super().__init__(name, resolution)
        self.data_path = data_path

    def load_data(
        self,
        coordinates: tuple,
        timestamp: datetime,
        window_size: tuple = (256, 256)
    ) -> np.ndarray:
        """Load elevation data for location."""
        if self.data_path:
            with rasterio.open(self.data_path) as src:
                py, px = src.index(*coordinates)

                half_h, half_w = window_size[0]//2, window_size[1]//2
                window = rasterio.windows.Window(
                    px - half_w, py - half_h,
                    window_size[0], window_size[1]
                )

                data = src.read(1, window=window)
                return data[np.newaxis, :, :]  # Add channel dimension
        else:
            # Placeholder data if no path
            return np.random.rand(1, *window_size)

    def preprocess(self, data: np.ndarray) -> np.ndarray:
        """Normalize elevation data."""
        return (data - data.min()) / (data.max() - data.min() + 1e-8)

class LandUseDataSource(DataSource):
    """Handler for land use and land cover data."""

    def __init__(
        self,
        name: str = "landuse",
        resolution: float = 100.0,  # 100m resolution
        data_path: Path = None,
        num_classes: int = 10
    ):
        super().__init__(name, resolution)
        self.data_path = data_path
        self.num_classes = num_classes

    def load_data(
        self,
        coordinates: tuple,
        timestamp: datetime,
        window_size: tuple = (256, 256)
    ) -> np.ndarray:
        """Load land use data for location."""
        if self.data_path:
            with rasterio.open(self.data_path) as src:
                py, px = src.index(*coordinates)

                half_h, half_w = window_size[0]//2, window_size[1]//2
                window = rasterio.windows.Window(
                    px - half_w, py - half_h,
                    window_size[0], window_size[1]
                )

                data = src.read(1, window=window)
                # One-hot encode land use classes
                one_hot = np.eye(self.num_classes)[data]
                return one_hot.transpose(2, 0, 1)  # [C, H, W]
        else:
            # Placeholder data if no path
            return np.random.rand(self.num_classes, *window_size)

    def preprocess(self, data: np.ndarray) -> np.ndarray:
        """No preprocessing needed for one-hot encoded data."""
        return data

class ClimateDataSource(DataSource):
    """Handler for climate data from NetCDF files."""

    def __init__(
        self,
        name: str = "climate",
        resolution: float = 25000.0,  # 25km resolution
        data_path: Path = None,
        variables: List[str] = ["temperature", "precipitation"]
    ):
        super().__init__(name, resolution)
        self.data_path = data_path
        self.variables = variables

    def load_data(
        self,
        coordinates: tuple,
        timestamp: datetime,
        window_size: tuple = (1, 1)
    ) -> np.ndarray:
        """Load climate data for location and time."""
        if self.data_path:
            with netCDF4.Dataset(self.data_path) as nc:
                lat, lon = coordinates

                # Find nearest grid points
                lat_idx = np.abs(nc.variables['latitude'][:] - lat).argmin()
                lon_idx = np.abs(nc.variables['longitude'][:] - lon).argmin()

                # Find nearest time point
                time_var = nc.variables['time']
                time_idx = np.abs(time_var[:] - timestamp).argmin()

                # Extract data for all variables
                data = []
                for var in self.variables:
                    var_data = nc.variables[var][time_idx, lat_idx, lon_idx]
                    data.append(var_data)

                return np.array(data).reshape(-1, 1, 1)
        else:
            # Placeholder data if no path
            return np.random.rand(len(self.variables), 1, 1)

    def preprocess(self, data: np.ndarray) -> np.ndarray:
        """Normalize climate data."""
        return (data - np.mean(data)) / (np.std(data) + 1e-8)

class NightLightDataSource(DataSource):
    """Handler for night light data (VIIRS/DMSP)."""

    def __init__(
        self,
        name: str = "nightlight",
        resolution: float = 500.0,  # 500m resolution
        data_path: Optional[Path] = None,
        use_gee: bool = True
    ):
        super().__init__(name, resolution)
        self.data_path = data_path
        self.use_gee = use_gee
        if use_gee:
            # Load service account credentials
            service_account_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            if not service_account_path or not os.path.exists(service_account_path):
                raise RuntimeError(f"Service account file not found: {service_account_path}")

            # Extract project ID from JSON
            with open(service_account_path, "r") as f:
                service_account_data = json.load(f)
                project_id = service_account_data.get("project_id", None)

            if not project_id:
                raise RuntimeError("No project ID found in the service account JSON.")

            # Authenticate with Google Earth Engine
            try:
                credentials = ee.ServiceAccountCredentials(None, service_account_path)
                ee.Initialize(credentials, project=project_id)
                print(f"✅ Google Earth Engine initialized with project: {project_id}")
            except Exception as e:
                raise RuntimeError(f"Google Earth Engine Initialization failed: {e}")


    def load_data(
        self,
        coordinates: tuple,
        timestamp: datetime,
        window_size: tuple = (256, 256)
    ) -> np.ndarray:
        """Load night light data for location."""
        if self.use_gee:
            # Use Google Earth Engine for VIIRS data
            point = ee.Geometry.Point([coordinates[1], coordinates[0]])
            dataset = ee.ImageCollection('NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG')
            image = dataset.filterDate(
                timestamp.strftime('%Y-%m-%d'),
                (timestamp + timedelta(days=31)).strftime('%Y-%m-%d')
            ).first()

            data = image.sample(point, window_size[0]).getInfo()
            return np.array(data['features'][0]['properties']['avg_rad']).reshape(1, 1, 1)
        else:
            return super().load_data(coordinates, timestamp, window_size)

class PowerInfrastructureDataSource(DataSource):
    """Handler for power infrastructure data (OpenInfraMap/OSM)."""

    def __init__(
        self,
        name: str = "power",
        resolution: float = 100.0,
        api_key: Optional[str] = None
    ):
        super().__init__(name, resolution)
        self.api_key = api_key

    def load_data(
        self,
        coordinates: tuple,
        timestamp: datetime,
        window_size: tuple = (1, 1)
    ) -> np.ndarray:
        """Load power infrastructure data."""
        lat, lon = coordinates

        # Query OpenStreetMap for power infrastructure
        overpass_url = "http://overpass-api.de/api/interpreter"
        query = f"""
        [out:json];
        (
          way["power"~"line|station|substation|plant"](around:5000,{lat},{lon});
          node["power"~"tower|pole|station|substation|plant"](around:5000,{lat},{lon});
        );
        out body;
        """

        response = requests.post(overpass_url, data={"data": query})
        data = response.json()

        # Process infrastructure data
        features = np.zeros(5)  # [lines, stations, substations, plants, towers]
        for element in data["elements"]:
            if element.get("tags", {}).get("power") == "line":
                features[0] += 1
            elif element.get("tags", {}).get("power") == "station":
                features[1] += 1
            elif element.get("tags", {}).get("power") == "substation":
                features[2] += 1
            elif element.get("tags", {}).get("power") == "plant":
                features[3] += 1
            elif element.get("tags", {}).get("power") in ["tower", "pole"]:
                features[4] += 1

        return features.reshape(-1, 1, 1)

class DataCenterDataSource(DataSource):
    """Handler for data center locations and characteristics."""

    def __init__(
        self,
        name: str = "datacenter",
        resolution: float = 1000.0,
        api_key: Optional[str] = None
    ):
        super().__init__(name, resolution)
        self.api_key = api_key

    def load_data(
        self,
        coordinates: tuple,
        timestamp: datetime,
        window_size: tuple = (1, 1)
    ) -> np.ndarray:
        """Load data center information."""
        lat, lon = coordinates

        # Query OpenStreetMap for data centers
        overpass_url = "http://overpass-api.de/api/interpreter"
        query = f"""
        [out:json];
        (
          way["building"="data_center"](around:10000,{lat},{lon});
          node["building"="data_center"](around:10000,{lat},{lon});
        );
        out body;
        """

        response = requests.post(overpass_url, data={"data": query})
        data = response.json()

        # Process data center information
        features = np.zeros(3)  # [count, total_area, avg_distance]
        distances = []

        for element in data["elements"]:
            features[0] += 1
            if "bounds" in element:
                area = (
                    (element["bounds"]["maxlat"] - element["bounds"]["minlat"]) *
                    (element["bounds"]["maxlon"] - element["bounds"]["minlon"])
                ) * 111 * 111  # Rough km² conversion
                features[1] += area

            center_lat = element.get("lat", element["bounds"]["minlat"])
            center_lon = element.get("lon", element["bounds"]["minlon"])
            distance = np.sqrt(
                (center_lat - lat)**2 +
                (center_lon - lon)**2
            ) * 111  # km
            distances.append(distance)

        if distances:
            features[2] = np.mean(distances)

        return features.reshape(-1, 1, 1)

class SatelliteTrafficDataSource(DataSource):
    """Handler for satellite traffic and coverage data."""

    def __init__(
        self,
        name: str = "satellite_traffic",
        resolution: float = 10000.0,
        api_key: Optional[str] = None
    ):
        super().__init__(name, resolution)
        self.api_key = api_key

    def load_data(
        self,
        coordinates: tuple,
        timestamp: datetime,
        window_size: tuple = (1, 1)
    ) -> np.ndarray:
        """Load satellite traffic data."""
        lat, lon = coordinates

        # Use Space-Track API if available
        if self.api_key:
            # Implementation for Space-Track API
            pass

        # Fallback to CelesTrak public TLE data
        url = "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=json"
        response = requests.get(url)
        satellites = response.json()

        # Process satellite data
        features = np.zeros(4)  # [total_sats, starlink, oneweb, other]

        for sat in satellites:
            features[0] += 1
            if "STARLINK" in sat["OBJECT_NAME"]:
                features[1] += 1
            elif "ONEWEB" in sat["OBJECT_NAME"]:
                features[2] += 1
            else:
                features[3] += 1

        return features.reshape(-1, 1, 1)

class SolarRadiationDataSource(DataSource):
    """Handler for solar radiation data."""

    def __init__(
        self,
        name: str = "solar",
        resolution: float = 1000.0,
        use_pvgis: bool = True
    ):
        super().__init__(name, resolution)
        self.use_pvgis = use_pvgis

    def load_data(
        self,
        coordinates: tuple,
        timestamp: datetime,
        window_size: tuple = (1, 1)
    ) -> np.ndarray:
        """Load solar radiation data."""
        lat, lon = coordinates

        if self.use_pvgis:
            # Use PVGIS API
            url = "https://re.jrc.ec.europa.eu/api/seriescalc"
            params = {
                "lat": lat,
                "lon": lon,
                "startyear": timestamp.year,
                "endyear": timestamp.year,
                "outputformat": "json"
            }

            response = requests.get(url, params=params)
            data = response.json()

            # Extract relevant features
            features = np.zeros(3)  # [ghi, dni, dhi]
            monthly_data = data["outputs"]["monthly"]

            for month in monthly_data:
                if month["month"] == timestamp.month:
                    features[0] = month["H(h)_m"]  # Global horizontal irradiance
                    features[1] = month["Hb(n)_m"]  # Direct normal irradiance
                    features[2] = month["Hd(h)_m"]  # Diffuse horizontal irradiance
                    break

            return features.reshape(-1, 1, 1)
        else:
            return np.random.rand(3, 1, 1)  # Placeholder data

class AirQualityDataSource(DataSource):
    """Handler for air quality data."""

    def __init__(
        self,
        name: str = "air_quality",
        resolution: float = 1000.0,
        api_key: Optional[str] = None
    ):
        super().__init__(name, resolution)
        self.api_key = api_key

    def load_data(
        self,
        coordinates: tuple,
        timestamp: datetime,
        window_size: tuple = (1, 1)
    ) -> np.ndarray:
        """Load air quality data."""
        lat, lon = coordinates

        # Use OpenAQ API
        url = f"https://api.openaq.org/v2/measurements"
        params = {
            "coordinates": f"{lat},{lon}",
            "radius": 10000,
            "date_from": timestamp.strftime("%Y-%m-%d"),
            "date_to": timestamp.strftime("%Y-%m-%d"),
            "limit": 1000
        }

        response = requests.get(url, params=params)
        data = response.json()

        # Process air quality data
        features = np.zeros(6)  # [pm25, pm10, no2, o3, so2, co]
        counts = np.zeros(6)

        for result in data["results"]:
            if result["parameter"] == "pm25":
                features[0] += result["value"]
                counts[0] += 1
            elif result["parameter"] == "pm10":
                features[1] += result["value"]
                counts[1] += 1
            elif result["parameter"] == "no2":
                features[2] += result["value"]
                counts[2] += 1
            elif result["parameter"] == "o3":
                features[3] += result["value"]
                counts[3] += 1
            elif result["parameter"] == "so2":
                features[4] += result["value"]
                counts[4] += 1
            elif result["parameter"] == "co":
                features[5] += result["value"]
                counts[5] += 1

        # Calculate averages
        for i in range(6):
            if counts[i] > 0:
                features[i] /= counts[i]

        return features.reshape(-1, 1, 1)
