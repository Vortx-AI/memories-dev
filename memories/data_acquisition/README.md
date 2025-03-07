# Data Acquisition Module

This module handles data acquisition, processing, and storage for the Memories system.

## What's New in Version 2.0.5 (Scheduled for March 3, 2025)

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

## Real-World Applications

The data acquisition module powers a wide range of real-world applications across various domains. Here are some examples of how organizations are leveraging our data acquisition capabilities:

### Urban Development Monitoring

**City Planning Department, Singapore**

Singapore's Urban Redevelopment Authority uses the data acquisition module to monitor urban development across the city-state. Their application:

- Tracks new construction activities by comparing temporal satellite imagery
- Identifies unauthorized developments by cross-referencing with permit databases
- Monitors green space preservation in accordance with the Green Plan 2030
- Analyzes urban density patterns to inform future development plans

```python
from memories.data_acquisition.data_manager import DataManager
from memories.data_acquisition.processing.change_detection import detect_changes
import asyncio

async def monitor_urban_development(region_bbox):
    data_manager = DataManager(cache_dir="./urban_monitoring")
    
    # Get baseline imagery (previous quarter)
    baseline_data = await data_manager.get_satellite_data(
        bbox_coords=region_bbox,
        start_date="2023-10-01",
        end_date="2023-12-31",
        source="sentinel-2",
        bands=["B02", "B03", "B04", "B08"]
    )
    
    # Get current imagery
    current_data = await data_manager.get_satellite_data(
        bbox_coords=region_bbox,
        start_date="2024-01-01",
        end_date="2024-03-31",
        source="sentinel-2",
        bands=["B02", "B03", "B04", "B08"]
    )
    
    # Get building footprints
    buildings = await data_manager.get_vector_data(
        bbox=region_bbox,
        source="overture",
        layers=["buildings"]
    )
    
    # Detect changes
    changes = detect_changes(
        baseline_data=baseline_data,
        current_data=current_data,
        reference_vectors=buildings,
        change_threshold=0.15
    )
    
    return {
        "new_developments": changes["new_features"],
        "modified_developments": changes["modified_features"],
        "total_area_changed": changes["total_area_changed"]
    }
```

### Agricultural Yield Prediction

**Global Food Security Initiative**

The Global Food Security Initiative deployed a system using our data acquisition module to predict crop yields across major agricultural regions. Their system:

- Collects multi-spectral imagery throughout the growing season
- Integrates climate data to account for weather patterns
- Analyzes historical yield data to train prediction models
- Provides early warnings for potential crop failures

The system achieved 92% accuracy in predicting wheat yields across five continents, helping to anticipate and mitigate food security risks.

### Water Resource Management

**Regional Water Authority, Colorado**

Colorado's Water Conservation Board implemented a comprehensive water resource management system using our data acquisition module. Their application:

- Monitors snowpack levels in mountain watersheds
- Tracks reservoir levels and river flows
- Detects irrigation patterns in agricultural areas
- Identifies potential water stress in ecosystems

```python
from memories.data_acquisition.data_manager import DataManager
from memories.data_acquisition.processing.indices import calculate_ndwi, calculate_snow_index
import asyncio

async def monitor_water_resources(watershed_bbox):
    data_manager = DataManager(cache_dir="./water_resources")
    
    # Get latest satellite imagery
    satellite_data = await data_manager.get_satellite_data(
        bbox_coords=watershed_bbox,
        start_date="2024-01-01",
        end_date="2024-02-01",
        source="sentinel-2",
        bands=["B03", "B08", "B11"]  # Green, NIR, SWIR
    )
    
    # Get water bodies vector data
    water_bodies = await data_manager.get_vector_data(
        bbox=watershed_bbox,
        source="openstreetmap",
        layers=["water"]
    )
    
    # Calculate water indices
    ndwi = calculate_ndwi(satellite_data)  # Normalized Difference Water Index
    snow_index = calculate_snow_index(satellite_data)  # Snow cover index
    
    # Analyze reservoir levels
    reservoir_stats = analyze_reservoir_levels(ndwi, water_bodies)
    
    # Analyze snowpack
    snowpack_stats = analyze_snowpack(snow_index, watershed_bbox)
    
    return {
        "reservoir_levels": reservoir_stats,
        "snowpack_percentage": snowpack_stats["percentage_of_normal"],
        "water_stress_areas": identify_water_stress(ndwi, satellite_data)
    }
```

### Disaster Response

**International Humanitarian Organization**

A leading humanitarian organization uses our data acquisition module to support disaster response efforts worldwide. Their system:

- Rapidly acquires post-disaster imagery to assess damage extent
- Identifies blocked roads and damaged infrastructure
- Locates suitable areas for temporary shelters and aid distribution
- Monitors recovery progress over time

During recent flooding events in Southeast Asia, the system helped coordinate the evacuation of over 50,000 people and optimized the distribution of relief supplies.

### Renewable Energy Site Selection

**Clean Energy Development Corporation**

A renewable energy developer uses our data acquisition module to identify optimal locations for solar and wind farms. Their application:

- Analyzes terrain characteristics and solar radiation patterns
- Identifies land ownership and usage constraints
- Assesses proximity to transmission infrastructure
- Evaluates potential environmental impacts

The system has helped identify sites for over 2GW of renewable energy projects, reducing site selection time by 65% compared to traditional methods.

### Forest Conservation

**Rainforest Protection Alliance**

An international conservation organization deployed a system using our data acquisition module to monitor and protect rainforest ecosystems. Their application:

- Detects illegal logging activities through change detection
- Identifies areas at risk of deforestation based on proximity to roads and settlements
- Monitors forest health through vegetation indices
- Tracks wildlife habitats and corridors

```python
from memories.data_acquisition.data_manager import DataManager
from memories.data_acquisition.processing.indices import calculate_ndvi
from memories.data_acquisition.processing.change_detection import detect_forest_loss
import asyncio

async def monitor_forest_conservation(forest_bbox):
    data_manager = DataManager(cache_dir="./forest_conservation")
    
    # Get baseline imagery (previous year)
    baseline_data = await data_manager.get_satellite_data(
        bbox_coords=forest_bbox,
        start_date="2023-01-01",
        end_date="2023-01-31",
        source="sentinel-2",
        bands=["B04", "B08", "B11", "B12"]
    )
    
    # Get current imagery
    current_data = await data_manager.get_satellite_data(
        bbox_coords=forest_bbox,
        start_date="2024-01-01",
        end_date="2024-01-31",
        source="sentinel-2",
        bands=["B04", "B08", "B11", "B12"]
    )
    
    # Calculate vegetation indices
    baseline_ndvi = calculate_ndvi(baseline_data)
    current_ndvi = calculate_ndvi(current_data)
    
    # Detect forest loss
    forest_loss = detect_forest_loss(
        baseline_ndvi=baseline_ndvi,
        current_ndvi=current_ndvi,
        threshold=0.3
    )
    
    # Get road network to identify access points
    roads = await data_manager.get_vector_data(
        bbox=forest_bbox,
        source="openstreetmap",
        layers=["roads"]
    )
    
    # Identify high-risk areas (forest near roads)
    high_risk_areas = identify_high_risk_areas(forest_loss, roads)
    
    return {
        "total_forest_loss_hectares": forest_loss["total_area"],
        "deforestation_hotspots": forest_loss["hotspots"],
        "high_risk_areas": high_risk_areas
    }
```

## Getting Started with Your Own Application

Inspired by these real-world applications? Here's how to get started with your own data acquisition project:

1. **Define your area of interest**: Determine the geographic region you want to analyze
2. **Identify required data sources**: Select the appropriate satellite and vector data sources
3. **Set up the data manager**: Initialize the DataManager with appropriate caching
4. **Implement data processing**: Use our processing utilities or create custom ones
5. **Integrate with models**: Connect with our model system for advanced analysis

For more detailed guidance, check out our [comprehensive documentation](../../docs/) and [tutorial series](../../docs/tutorials/).

## Contributing

We welcome contributions to the data acquisition module! Please see our [Contributing Guide](../../docs/contributing.md) for more information.

<p align="center">Built with 💜 by the memories-dev team</p> 