# Data Acquisition Module

This module handles data acquisition, processing, and storage for the Memories system.

## What's New in Version 2.0.2 (Scheduled for February 25, 2025)

Since our initial release (v1.0.0 on February 14, 2025), we've made significant improvements to the data acquisition module:

### New Data Sources
- **Overture Maps**: Complete integration with Overture Maps for high-quality vector data
- **OpenStreetMap Enhanced**: Improved OSM integration with advanced filtering and processing
- **Earth Engine**: Integration with Google Earth Engine for advanced satellite data processing

### New Features
- **Multi-source Fusion**: Combine data from multiple sources for comprehensive analysis
- **Advanced Filtering**: Sophisticated filtering options for all data sources
- **Vector Data Processing**: Enhanced processing capabilities for vector data
- **Temporal Analysis**: Track changes over time with temporal data analysis
- **Automated Data Validation**: Validate data quality and completeness automatically

## Architecture

The data acquisition module is organized into several components:

```
data_acquisition/
├── __init__.py
├── data_manager.py           # Main interface for data acquisition
├── sources/                  # Data source implementations
│   ├── __init__.py
│   ├── sentinel_api.py       # Sentinel-2 data source
│   ├── landsat_api.py        # Landsat data source
│   ├── osm_api.py            # OpenStreetMap data source
│   ├── overture_api.py       # Overture Maps data source
│   ├── wfs_api.py            # WFS data source
│   └── planetary_compute.py  # Microsoft Planetary Computer
├── processing/               # Data processing utilities
│   ├── __init__.py
│   ├── cloud_mask.py         # Cloud masking for satellite imagery
│   ├── indices.py            # Spectral indices calculation
│   ├── fusion.py             # Multi-source data fusion
│   └── validation.py         # Data validation utilities
└── utils/                    # Utility functions
    ├── __init__.py
    ├── bbox.py               # Bounding box utilities
    ├── caching.py            # Caching utilities
    └── conversion.py         # Data format conversion utilities
```

## Usage Examples

### Data Manager

The `DataManager` class provides a unified interface for acquiring data from various sources:

```python
from memories.data_acquisition.data_manager import DataManager
import asyncio

# Initialize data manager
data_manager = DataManager(cache_dir="./data_cache")

# Define area of interest
bbox = {
    'xmin': -122.4018,
    'ymin': 37.7914,
    'xmax': -122.3928,
    'ymax': 37.7994
}

# Get satellite data
async def get_satellite_data():
    satellite_data = await data_manager.get_satellite_data(
        bbox_coords=bbox,
        start_date="2023-01-01",
        end_date="2023-01-31",
        source="sentinel-2",
        bands=["B02", "B03", "B04", "B08"],
        cloud_cover_max=20
    )
    return satellite_data

# Get vector data
async def get_vector_data():
    vector_data = await data_manager.get_vector_data(
        bbox=bbox,
        source="openstreetmap",
        layers=["buildings", "roads", "landuse", "water"]
    )
    return vector_data

# Run the async functions
satellite_data = asyncio.run(get_satellite_data())
vector_data = asyncio.run(get_vector_data())

# Process the data
from memories.data_acquisition.processing.indices import calculate_ndvi

ndvi = calculate_ndvi(satellite_data)
```

### Sentinel-2 Data

```python
from memories.data_acquisition.sources.sentinel_api import SentinelAPI
import asyncio

# Initialize the API
api = SentinelAPI(data_dir="./sentinel_data")
await api.initialize()

# Define area of interest
bbox = {
    'xmin': -122.4018,
    'ymin': 37.7914,
    'xmax': -122.3928,
    'ymax': 37.7994
}

# Download specific bands with cloud cover filter
result = await api.download_data(
    bbox=bbox,
    start_date="2023-01-01",
    end_date="2023-01-31",
    bands=["B04", "B08"],
    cloud_cover=10.0
)

if result["status"] == "success":
    print(f"Downloaded files: {result['files']}")
    print(f"Metadata: {result['metadata']}")
```

### OpenStreetMap Data

```python
from memories.data_acquisition.sources.osm_api import OSMDataSource
import asyncio

# Initialize OSM data source
osm_source = OSMDataSource(cache_dir="./osm_cache")

# Define area of interest
bbox = {
    'xmin': -122.4018,
    'ymin': 37.7914,
    'xmax': -122.3928,
    'ymax': 37.7994
}

# Get specific OSM features
async def get_osm_data():
    # Get buildings
    buildings = await osm_source.get_buildings(bbox)
    
    # Get road network
    roads = await osm_source.get_roads(bbox)
    
    # Get points of interest
    pois = await osm_source.get_pois(bbox, categories=["amenity", "shop"])
    
    # Get land use polygons
    landuse = await osm_source.get_landuse(bbox)
    
    return {
        "buildings": buildings,
        "roads": roads,
        "pois": pois,
        "landuse": landuse
    }

# Run the async function
osm_data = asyncio.run(get_osm_data())

# Access the data
print(f"Found {len(osm_data['buildings'])} buildings")
print(f"Found {len(osm_data['roads'])} road segments")
```

### Overture Maps Data

```python
from memories.data_acquisition.sources.overture_api import OvertureDataSource
import asyncio

# Initialize Overture data source with API key
overture_source = OvertureDataSource(
    api_key="your-overture-api-key",
    cache_dir="./overture_cache"
)

# Define area of interest
bbox = {
    'xmin': -122.4018,
    'ymin': 37.7914,
    'xmax': -122.3928,
    'ymax': 37.7994
}

# Get Overture data
async def get_overture_data():
    # Get places
    places = await overture_source.get_places(
        bbox=bbox,
        categories=["restaurant", "cafe", "hotel"]
    )
    
    # Get buildings with detailed attributes
    buildings = await overture_source.get_buildings(
        bbox=bbox,
        include_height=True,
        include_building_type=True
    )
    
    return {
        "places": places,
        "buildings": buildings
    }

# Run the async function
overture_data = asyncio.run(get_overture_data())
```

### Multi-source Data Fusion

```python
from memories.data_acquisition.data_manager import DataManager
from memories.data_acquisition.processing.fusion import fuse_data
import asyncio

# Initialize data manager
data_manager = DataManager(cache_dir="./data_cache")

# Define area of interest
bbox = {
    'xmin': -122.4018,
    'ymin': 37.7914,
    'xmax': -122.3928,
    'ymax': 37.7994
}

# Get data from multiple sources
async def get_fused_data():
    # Get satellite data
    satellite_data = await data_manager.get_satellite_data(
        bbox_coords=bbox,
        start_date="2023-01-01",
        end_date="2023-01-31"
    )
    
    # Get OSM data
    osm_data = await data_manager.get_vector_data(
        bbox=bbox,
        source="openstreetmap",
        layers=["buildings", "roads"]
    )
    
    # Get Overture data
    overture_data = await data_manager.get_vector_data(
        bbox=bbox,
        source="overture",
        layers=["places", "buildings"]
    )
    
    # Fuse the data
    fused_data = fuse_data(
        sources=[
            {"type": "satellite", "data": satellite_data},
            {"type": "vector", "data": osm_data},
            {"type": "vector", "data": overture_data}
        ],
        fusion_strategy="overlay"
    )
    
    return fused_data

# Run the async function
fused_data = asyncio.run(get_fused_data())
```

## Coming in Version 2.1.0 (March 2025)

- **Maxar Integration**: Access to Maxar's high-resolution satellite imagery
- **Sentinel-3 Support**: Integration with Sentinel-3 OLCI and SLSTR instruments
- **Multi-source Fusion**: Advanced algorithms for combining data from multiple sources
- **Temporal Analysis**: Enhanced capabilities for tracking changes over time
- **Custom Data Sources**: Framework for adding custom data sources

## Contributing

We welcome contributions to the data acquisition module! Please see our [Contributing Guide](https://memories-dev.readthedocs.io/development/contributing.html) for more information.

<p align="center">Built with 💜 by the memories-dev team</p> 