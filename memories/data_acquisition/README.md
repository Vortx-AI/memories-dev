# Data Acquisition Module

This module handles all data acquisition, processing, and storage operations for the Memories system. It provides a robust framework for collecting, processing, and managing various types of satellite and vector data sources.

## Structure

```
data_acquisition/
├── sources/            # Source-specific implementations
│   ├── __init__.py    # Source exports
│   ├── base.py        # Base classes
│   ├── sentinel_api.py # Sentinel-2 data source
│   ├── landsat_api.py # Landsat data source
│   ├── wfs_api.py     # WFS data source
│   ├── osm_api.py     # OpenStreetMap API
│   ├── overture_api.py # Overture Maps API
│   └── planetary_compute.py # Microsoft Planetary Computer
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

### Data Sources (`sources/`)
The module provides several data source implementations:

#### Satellite Data Sources
- `SentinelAPI`: Sentinel-2 L2A data
  - 10m resolution bands (B02, B03, B04, B08)
  - 20m resolution bands (B05-B07, B8A, B11, B12)
  - Cloud cover filtering
  - Quality indicators
  
- `LandsatAPI`: Landsat Collection 2 Level 2
  - Surface reflectance bands (SR_B2-SR_B7)
  - Quality assessment
  - 30m resolution
  
- `PlanetaryCompute`: Microsoft Planetary Computer
  - Multiple collections support
  - STAC API integration
  - Cloud-optimized access

#### Vector Data Sources
- `OvertureAPI`: Overture Maps Foundation
  - Building footprints
  - Transportation networks
  - Land use data
  - Global coverage

- `OSMAPI`: OpenStreetMap
  - Buildings, roads, POIs
  - Land use and natural features
  - Real-time updates
  
- `WFSAPI`: Web Feature Service
  - Standard OGC WFS support
  - Vector data queries
  - Custom layer support

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

### 3. Training Data Preparation

```python
# Prepare combined satellite and vector data for ML
training_data = await manager.prepare_training_data(
    bbox=bbox,
    start_date="2023-01-01",
    end_date="2023-12-31",
    satellite_collections=["sentinel-2-l2a"],
    vector_layers=["buildings", "roads"],
    cloud_cover=20.0,
    resolution=10.0
)
```

## Data Formats

### Satellite Data
- Sentinel-2:
  - 10m resolution bands: B02 (Blue), B03 (Green), B04 (Red), B08 (NIR)
  - 20m resolution bands: B05, B06, B07, B8A, B11, B12
  - Cloud masks and quality indicators
  
- Landsat:
  - Surface Reflectance bands: SR_B2 through SR_B7
  - Quality Assessment bands
  - 30m resolution

### Vector Data
- GeoJSON format
- Supported features:
  - Buildings (footprints, height, type)
  - Roads (geometry, classification)
  - Land use (polygons, categories)

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
```

## Error Handling

The module implements comprehensive error handling:

```python
try:
    data = await manager.get_satellite_data(bbox=bbox)
except ValueError as e:
    # Handle invalid input parameters
    print(f"Invalid input: {e}")
except Exception as e:
    # Handle other errors
    print(f"Error fetching data: {e}")
```

## Best Practices

1. **Resource Management**
   - Use appropriate timeouts for API calls
   - Implement rate limiting for external services
   - Clean up temporary files after processing

2. **Data Quality**
   - Filter clouds and shadows in satellite data
   - Validate vector geometries
   - Check for data completeness

3. **Performance**
   - Use caching for frequently accessed data
   - Implement parallel downloads where possible
   - Optimize raster operations

4. **Error Handling**
   - Implement proper exception handling
   - Log errors with sufficient context
   - Provide meaningful error messages

## Testing

Tests are located in `tests/data_acquisition/` and cover:

### Test Files
- `test_data_manager.py`: Tests for the data manager functionality
- `test_data_sources.py`: Tests for the data sources module
- `test_sources.py`: Tests for individual source implementations

### Test Coverage
- Unit tests for each component
- Integration tests for data flow
- Mock tests for external APIs
- Cache management tests
- Error handling scenarios
- Performance benchmarks
- Concurrent operations
- Resource cleanup

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