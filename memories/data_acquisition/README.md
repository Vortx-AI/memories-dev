# Data Acquisition Module

This module handles all data acquisition, processing, and storage operations for the Memories system. It provides a robust framework for collecting, processing, and managing various types of satellite and vector data sources.

## What's New in Version 2.0.2

### New Data Sources
- **Overture Maps**: Complete integration with Overture Maps Foundation data
- **OpenStreetMap Enhanced**: Improved OSM data extraction with advanced filtering
- **Maxar Open Data**: Access to Maxar's open satellite imagery
- **Sentinel-3**: Added support for Sentinel-3 OLCI and SLSTR instruments

### Improvements
- **Multi-source Fusion**: Combine data from multiple sources with automatic alignment
- **Advanced Filtering**: Enhanced cloud masking and quality filtering
- **Vector Data Processing**: Improved building footprint extraction and road network analysis
- **Temporal Analysis**: Support for time-series analysis of satellite imagery
- **Data Validation**: Automated quality checks and validation pipelines

## Structure

```
data_acquisition/
├── sources/            # Source-specific implementations
│   ├── __init__.py    # Source exports
│   ├── base.py        # Base classes
│   ├── sentinel_api.py # Sentinel-2 data source
│   ├── sentinel3_api.py # Sentinel-3 data source (New in 2.0.2)
│   ├── landsat_api.py # Landsat data source
│   ├── maxar_api.py   # Maxar data source (New in 2.0.2)
│   ├── wfs_api.py     # WFS data source
│   ├── osm_api.py     # OpenStreetMap API
│   ├── overture_api.py # Overture Maps API
│   └── planetary_compute.py # Microsoft Planetary Computer
├── processing/         # Data processing utilities (New in 2.0.2)
│   ├── __init__.py    # Processing exports
│   ├── cloud_mask.py  # Cloud masking algorithms
│   ├── indices.py     # Spectral indices calculation
│   ├── fusion.py      # Multi-source data fusion
│   └── validation.py  # Data validation tools
├── __init__.py        # Module initialization
├── data_manager.py    # Core data management functionality
└── README.md          # Module documentation
```

## Core Components

### Data Manager (`data_manager.py`)
The Data Manager serves as the central coordinator for all data operations, providing:
- Data source registration and management
- Satellite and vector data acquisition
- Caching and data persistence
- Training data preparation
- Coordinate system and bbox handling

Key features:
- Asynchronous data fetching
- Automatic caching with refresh capability
- Support for multiple data formats
- Error handling and logging
- Flexible bbox input (tuples, lists, or Polygon objects)
- Multi-source data fusion (New in 2.0.2)
- Temporal analysis support (New in 2.0.2)

### Data Sources (`sources/`)
The module provides several data source implementations:

#### Satellite Data Sources
- `SentinelAPI`: Sentinel-2 L2A data
  - 10m resolution bands (B02, B03, B04, B08)
  - 20m resolution bands (B05-B07, B8A, B11, B12)
  - Cloud cover filtering
  - Quality indicators
  - Atmospheric correction (New in 2.0.2)
  
- `Sentinel3API`: Sentinel-3 data (New in 2.0.2)
  - OLCI instrument (21 bands, 300m resolution)
  - SLSTR instrument (9 bands, 500m/1km resolution)
  - Sea and land surface temperature
  - Ocean color products
  
- `LandsatAPI`: Landsat Collection 2 Level 2
  - Surface reflectance bands (SR_B2-SR_B7)
  - Quality assessment
  - 30m resolution
  - Landsat 8 and 9 support (New in 2.0.2)
  
- `MaxarAPI`: Maxar Open Data (New in 2.0.2)
  - High-resolution imagery (30-50cm)
  - Disaster response data
  - Open data program access
  
- `PlanetaryCompute`: Microsoft Planetary Computer
  - Multiple collections support
  - STAC API integration
  - Cloud-optimized access
  - Enhanced query capabilities (New in 2.0.2)

#### Vector Data Sources
- `OvertureAPI`: Overture Maps Foundation
  - Building footprints
  - Transportation networks
  - Land use data
  - Global coverage
  - Places and POIs (New in 2.0.2)
  - Administrative boundaries (New in 2.0.2)

- `OSMAPI`: OpenStreetMap
  - Buildings, roads, POIs
  - Land use and natural features
  - Real-time updates
  - Advanced filtering (New in 2.0.2)
  - Historical data access (New in 2.0.2)
  
- `WFSAPI`: Web Feature Service
  - Standard OGC WFS support
  - Vector data queries
  - Custom layer support
  - WFS 2.0 features (New in 2.0.2)

### Data Processing (`processing/`) (New in 2.0.2)
The new processing module provides utilities for:
- Cloud masking with multiple algorithms
- Spectral indices calculation (NDVI, NDWI, etc.)
- Multi-source data fusion
- Data validation and quality assessment

## Usage Examples

### 1. Basic Data Manager Usage

```python
from memories.data_acquisition.data_manager import DataManager

# Initialize data manager with cache directory
manager = DataManager(cache_dir="./data_cache")

# Define area of interest
bbox = [-122.4, 37.7, -122.3, 37.8]  # [west, south, east, north]

# Get satellite data
satellite_data = await manager.get_satellite_data(
    bbox=bbox,
    start_date="2023-01-01",
    end_date="2023-12-31",
    refresh=False  # Use cache if available
)
```

### 2. Vector Data Acquisition

```python
# Get vector data for multiple layers
vector_data = await manager.get_vector_data(
    bbox=bbox,
    layers=["buildings", "roads", "landuse"]
)

# Access individual sources
overture_data = vector_data["overture"]
osm_data = vector_data["osm"]
```

### 3. Multi-source Data Fusion (New in 2.0.2)

```python
from memories.data_acquisition.processing.fusion import fuse_sources

# Get data from multiple sources
sentinel_data = await manager.get_satellite_data(
    bbox=bbox,
    start_date="2023-01-01",
    end_date="2023-01-31",
    collection="sentinel-2-l2a"
)

landsat_data = await manager.get_satellite_data(
    bbox=bbox,
    start_date="2023-01-01",
    end_date="2023-01-31",
    collection="landsat-c2-l2"
)

# Fuse the data sources
fused_data = fuse_sources(
    sources=[sentinel_data, landsat_data],
    method="weighted_average",
    weights=[0.6, 0.4],
    resolution=10.0
)

# Use the fused data
analysis_result = await manager.analyze_data(fused_data)
```

### 4. Temporal Analysis (New in 2.0.2)

```python
from memories.data_acquisition.processing.indices import calculate_ndvi
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Define time period
end_date = datetime.now()
start_date = end_date - timedelta(days=365)

# Get time series data
time_series = await manager.get_time_series(
    bbox=bbox,
    start_date=start_date.strftime("%Y-%m-%d"),
    end_date=end_date.strftime("%Y-%m-%d"),
    collection="sentinel-2-l2a",
    frequency="monthly"
)

# Calculate NDVI for each time point
ndvi_series = []
dates = []

for date, data in time_series.items():
    ndvi = calculate_ndvi(data)
    ndvi_mean = ndvi.mean()
    ndvi_series.append(ndvi_mean)
    dates.append(date)

# Plot the results
plt.figure(figsize=(12, 6))
plt.plot(dates, ndvi_series, 'g-', marker='o')
plt.title('NDVI Change Over Time')
plt.xlabel('Date')
plt.ylabel('Mean NDVI')
plt.grid(True)
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('ndvi_trend.png')
```

### 5. Overture Maps Integration (New in 2.0.2)

```python
# Get building data from Overture Maps
overture_buildings = await manager.get_vector_data(
    bbox=bbox,
    source="overture",
    layers=["buildings"],
    attributes=["height", "building_type", "last_updated"]
)

# Get places data from Overture Maps
overture_places = await manager.get_vector_data(
    bbox=bbox,
    source="overture",
    layers=["places"],
    categories=["food_and_drink", "education", "healthcare"]
)

# Combine with OSM data for comparison
osm_buildings = await manager.get_vector_data(
    bbox=bbox,
    source="osm",
    layers=["buildings"]
)

# Compare building coverage
building_comparison = await manager.compare_sources(
    sources=[overture_buildings, osm_buildings],
    metrics=["count", "area_coverage", "attribute_completeness"]
)

print(f"Overture buildings: {building_comparison['overture']['count']}")
print(f"OSM buildings: {building_comparison['osm']['count']}")
print(f"Coverage difference: {building_comparison['difference_percent']}%")
```

## Data Formats

### Satellite Data
- Sentinel-2:
  - 10m resolution bands: B02 (Blue), B03 (Green), B04 (Red), B08 (NIR)
  - 20m resolution bands: B05, B06, B07, B8A, B11, B12
  - Cloud masks and quality indicators
  
- Sentinel-3 (New in 2.0.2):
  - OLCI: 21 bands (400-1020nm), 300m resolution
  - SLSTR: 9 bands (550-12000nm), 500m/1km resolution
  
- Landsat:
  - Surface Reflectance bands: SR_B2 through SR_B7
  - Quality Assessment bands
  - 30m resolution

- Maxar (New in 2.0.2):
  - RGB and pan-sharpened imagery
  - 30-50cm resolution
  - Disaster response collections

### Vector Data
- GeoJSON format
- Supported features:
  - Buildings (footprints, height, type)
  - Roads (geometry, classification)
  - Land use (polygons, categories)
  - Places and POIs (New in 2.0.2)
  - Administrative boundaries (New in 2.0.2)

## Caching

The module implements a robust caching system:

```python
# Check cache status
exists = manager.cache_exists("cache_key")

# Get cached data
data = manager.get_from_cache("cache_key")

# Force refresh cached data
new_data = await manager.get_satellite_data(
    bbox=bbox,
    refresh=True
)

# Set cache expiration (New in 2.0.2)
manager.set_cache_policy(
    max_age_days=30,
    max_size_gb=10,
    cleanup_strategy="lru"
)
```

## Error Handling

The module implements comprehensive error handling:

```python
try:
    data = await manager.get_satellite_data(bbox=bbox)
except ValueError as e:
    # Handle invalid input parameters
    print(f"Invalid input: {e}")
except ConnectionError as e:
    # Handle API connection issues (New in 2.0.2)
    print(f"Connection error: {e}")
    # Try fallback source
    data = await manager.get_satellite_data(bbox=bbox, source="fallback")
except Exception as e:
    # Handle other errors
    print(f"Error fetching data: {e}")
```

## Best Practices

1. **Resource Management**
   - Use appropriate timeouts for API calls
   - Implement rate limiting for external services
   - Clean up temporary files after processing
   - Use connection pooling for multiple requests (New in 2.0.2)

2. **Data Quality**
   - Filter clouds and shadows in satellite data
   - Validate vector geometries
   - Check for data completeness
   - Apply automated quality assessment (New in 2.0.2)

3. **Performance**
   - Use caching for frequently accessed data
   - Implement parallel downloads where possible
   - Optimize raster operations
   - Use cloud-optimized formats (COG, ZARR) (New in 2.0.2)

4. **Error Handling**
   - Implement proper exception handling
   - Log errors with sufficient context
   - Provide meaningful error messages
   - Use fallback sources when primary fails (New in 2.0.2)

## Testing

Tests are located in `tests/data_acquisition/` and cover:

### Test Files
- `test_data_manager.py`: Tests for the data manager functionality
- `test_data_sources.py`: Tests for the data sources module
- `test_sources.py`: Tests for individual source implementations
- `test_processing.py`: Tests for processing utilities (New in 2.0.2)
- `test_fusion.py`: Tests for multi-source fusion (New in 2.0.2)

### Test Coverage
- Unit tests for each component
- Integration tests for data flow
- Mock tests for external APIs
- Cache management tests
- Error handling scenarios
- Performance benchmarks
- Concurrent operations
- Resource cleanup
- Validation tests (New in 2.0.2)

### Running Tests
```bash
# Run all data acquisition tests
python -m pytest tests/data_acquisition/

# Run specific test file
python -m pytest tests/data_acquisition/test_data_manager.py

# Run with coverage report
python -m pytest tests/data_acquisition/ --cov=memories.data_acquisition
```

### Test Requirements
Required packages for running tests are listed in `requirements-test.txt`:
- pytest
- pytest-asyncio
- pytest-cov
- aiohttp
- numpy
- rasterio
- shapely
- pystac-client
- matplotlib (New in 2.0.2)
- geopandas (New in 2.0.2)

<p align="center">Built with 💜 by the memories-dev team</p> 