# memories-dev

<div align="center">

**Building the World's Memory for Artificial General Intelligence**

[![Documentation](https://img.shields.io/badge/docs-latest-brightgreen.svg)](https://memories-dev.readthedocs.io/index.html)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Version](https://img.shields.io/badge/version-2.0.2-blue.svg)](https://github.com/Vortx-AI/memories-dev/releases/tag/v2.0.2)
[![Discord](https://img.shields.io/discord/1339432819784683522?color=7289da&label=Discord&logo=discord&logoColor=white)](https://discord.gg/tGCVySkX4d)

<a href="https://www.producthunt.com/posts/memories-dev?embed=true&utm_source=badge-featured&utm_medium=badge&utm_souce=badge-memories&#0045;dev" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/featured.svg?post_id=879661&theme=light&t=1739530783374" alt="memories&#0046;dev - Collective&#0032;AGI&#0032;Memory | Product Hunt" style="width: 250px; height: 54px;" width="250" height="54" /></a>

</div>

## 📖 Overview

memories-dev is a comprehensive Python library for creating and managing memories using satellite imagery, vector data, and large language models. It provides a unified interface for data acquisition, processing, and model integration, enabling developers to build sophisticated applications with rich contextual understanding of the physical world.

### 🚀 Key Features

- **Data Acquisition**: 
  - Satellite imagery (Sentinel-2, Landsat, Earth Engine)
  - Vector data (OpenStreetMap, Overture Maps, WFS Services)
  - Environmental metrics (climate data, terrain analysis)
  - Temporal-spatial data integration
  - Real-time data streams

- **Model Integration**: 
  - Local model deployment
  - API-based model access
  - Multiple provider support (DeepSeek, OpenAI, Anthropic, Mistral, Meta)
  - GPU acceleration and optimization
  - Multi-modal processing (text, imagery, vector data)

- **Deployment Options**: 
  - Local deployment (CPU/GPU)
  - Cloud deployment (AWS, GCP, Azure)
  - Distributed systems (consensus-based, swarmed)
  - Container orchestration (Docker, Kubernetes)
  - Edge deployment for low-latency applications

- **Advanced Features**: 
  - Concurrent data processing
  - GPU memory management
  - Caching and optimization
  - Error handling and validation
  - Automated data fusion and harmonization

## System Architecture

The system is built on three core components:

1. **Data Acquisition**: Collects and processes data from various sources
2. **Model System**: Manages model loading, inference, and API connections
3. **Deployment**: Handles deployment configurations and resource management

<div align="center">
  <img src="https://raw.githubusercontent.com/Vortx-AI/memories-dev/main/docs/source/_static/architecture.png" alt="memories-dev Architecture" width="700px">
</div>

## Release Timeline

- **v1.0.0** - Released on February 14, 2025: Initial stable release with core functionality
- **v2.0.2** - Scheduled for February 25, 2025: Current development version with enhanced features

## Quick Start

### Installation

```bash
# Basic installation
pip install memories-dev

# With GPU support
pip install memories-dev[gpu]

# For development
pip install memories-dev[dev]

# For documentation
pip install memories-dev[docs]
```

### Basic Usage

```python
from memories.models.load_model import LoadModel
from memories.data_acquisition.data_manager import DataManager
import asyncio

# Initialize model
model = LoadModel(
    use_gpu=True,
    model_provider="deepseek-ai",
    deployment_type="local",
    model_name="deepseek-coder-small"
)

# Initialize data manager
data_manager = DataManager(cache_dir="./data_cache")

# Define area of interest (San Francisco)
bbox = {
    'xmin': -122.4018,
    'ymin': 37.7914,
    'xmax': -122.3928,
    'ymax': 37.7994
}

# Get satellite data
async def get_data():
    satellite_data = await data_manager.get_satellite_data(
        bbox_coords=bbox,
        start_date="2023-01-01",
        end_date="2023-02-01"
    )
    return satellite_data

# Run the async function
satellite_data = asyncio.run(get_data())

# Generate text with the model
response = model.get_response(
    f"Describe the satellite data for this region: {satellite_data}"
)
print(response["text"])

# Clean up resources
model.cleanup()
```

## 📊 Data Acquisition

The data acquisition module provides robust capabilities for fetching and processing data from various sources:

### Sentinel API

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
from memories.data_acquisition.sources.osm import OSMDataSource
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
from memories.data_acquisition.sources.overture import OvertureDataSource
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

## 🤖 Model Integration

The model system provides a unified interface for both local and API-based models:

### Local Models

```python
from memories.models.load_model import LoadModel

# Initialize local model
model = LoadModel(
    use_gpu=True,
    model_provider="deepseek-ai",
    deployment_type="local",
    model_name="deepseek-coder-small"
)

# Generate text
response = model.get_response("Write a function to calculate factorial")
print(response["text"])

# Clean up resources
model.cleanup()
```

### API-based Models

```python
from memories.models.load_model import LoadModel

# Initialize API-based model
model = LoadModel(
    model_provider="openai",
    deployment_type="api",
    model_name="gpt-4",
    api_key="your-api-key"
)

# Generate text
response = model.get_response(
    "Analyze this satellite image for urban development",
    temperature=0.7,
    max_tokens=500
)
print(response["text"])
```

## 🚀 Deployment Options

The deployment module supports various deployment configurations:

### Standalone Deployment

```python
from memories.deployments.standalone import StandaloneDeployment

# Configure standalone deployment
deployment = StandaloneDeployment(
    provider="gcp",
    config={
        "machine_type": "n2-standard-4",
        "region": "us-west1",
        "zone": "us-west1-a"
    }
)

# Deploy the system
deployment.deploy()
```

### Consensus-based Deployment

```python
from memories.deployments.consensus import ConsensusDeployment

# Configure consensus-based deployment
deployment = ConsensusDeployment(
    provider="aws",
    config={
        "min_nodes": 3,
        "max_nodes": 5,
        "quorum_size": 2,
        "region": "us-west-2"
    }
)

# Deploy the system
deployment.deploy()
```

### Swarmed Deployment

```python
from memories.deployments.swarmed import SwarmedDeployment

# Configure swarmed deployment
deployment = SwarmedDeployment(
    provider="azure",
    config={
        "min_nodes": 3,
        "max_nodes": 10,
        "manager_nodes": 3,
        "worker_nodes": 5,
        "location": "westus2"
    }
)

# Deploy the system
deployment.deploy()
```

## 📚 Documentation

For more detailed information, check out our documentation:

- [Quick Start Guide](https://memories-dev.readthedocs.io/quickstart.html)
- [User Guide](https://memories-dev.readthedocs.io/user_guide/index.html)
- [API Reference](https://memories-dev.readthedocs.io/api_reference/index.html)
- [Examples](https://memories-dev.readthedocs.io/user_guide/examples.html)
- [Development Guide](https://memories-dev.readthedocs.io/development/index.html)

## 🔜 Coming in Version 2.1.0 (March 2025)

- **Maxar Integration**: Access to Maxar's high-resolution satellite imagery
- **Sentinel-3 Support**: Integration with Sentinel-3 OLCI and SLSTR instruments
- **Multi-source Fusion**: Advanced algorithms for combining data from multiple sources
- **Function Calling**: Support for OpenAI and Anthropic function calling APIs
- **Multi-model Inference**: Compare results from multiple models in parallel
- **Memory Snapshots**: Point-in-time memory snapshots for backup and recovery

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](https://memories-dev.readthedocs.io/development/contributing.html) for more information.

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

<p align="center">Built with 💜 by the memories-dev team</p>

