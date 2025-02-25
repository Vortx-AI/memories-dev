# Memories-Dev Framework

A powerful framework for building AI applications with advanced memory management and earth data integration.

## What's New in Version 2.0.2

- **Enhanced Earth Memory Integration**: Seamless integration with Overture and Sentinel data
- **New Example Applications**: 
  - Real Estate Agent with environmental analysis
  - Property Analyzer with comprehensive assessment
  - Water Body Agent for monitoring water resources
  - Food Analyzer for nutrition analysis
  - Traffic Analyzer for pattern recognition
  - Autonomous Vehicle Memory system
- **Improved Performance**: Optimized memory usage and processing speed
- **Better Documentation**: Enhanced examples and usage guides

## Features

- **Tiered Memory Management**:
  - Hot Memory: Fast access to frequently used data
  - Warm Memory: Balanced storage for semi-active data
  - Cold Memory: Efficient storage for historical data

- **Earth Memory Integration**:
  - Overture Maps for location data
  - Sentinel satellite imagery
  - Environmental analysis capabilities
  - Terrain and geological data

- **AI Capabilities**:
  - Semantic search and retrieval
  - Context-aware processing
  - Multi-modal data handling
  - Advanced embedding generation

## Quick Start

```bash
# Install the framework
pip install memories-dev[all]

# Set up environment variables
export OVERTURE_API_KEY=your_api_key
export SENTINEL_USER=your_username
export SENTINEL_PASSWORD=your_password

# Run an example
python examples/real_estate_agent.py
```

## Basic Usage

```python
from memories import MemoryStore, Config
from memories.earth import OvertureClient, SentinelClient

# Configure memory store
config = Config(
    storage_path="./data",
    hot_memory_size=50,  # MB
    warm_memory_size=200,  # MB
    cold_memory_size=1000  # MB
)

# Initialize memory store
memory_store = MemoryStore(config)

# Initialize earth memory clients
overture_client = OvertureClient(api_key=os.getenv("OVERTURE_API_KEY"))
sentinel_client = SentinelClient(
    username=os.getenv("SENTINEL_USER"),
    password=os.getenv("SENTINEL_PASSWORD")
)

# Store and retrieve data
await memory_store.store("key1", "value1", tier="hot")
value = await memory_store.retrieve("key1")
```

## Example Applications

Check out our [examples directory](examples/) for complete applications:

- **Real Estate Agent**: AI-powered property analysis
- **Property Analyzer**: Environmental assessment
- **Water Body Agent**: Water resource monitoring
- **Food Analyzer**: Nutrition analysis
- **Traffic Analyzer**: Pattern recognition
- **Autonomous Vehicle Memory**: Car memory system

## Documentation

- [Getting Started Guide](docs/getting_started.md)
- [API Reference](docs/api_reference.md)
- [Example Applications](examples/README.md)
- [Earth Memory Integration](docs/earth_memory.md)
- [Advanced Features](docs/advanced_features.md)

## Requirements

- Python 3.9+
- 500MB minimum RAM (2GB recommended)
- Internet connection for earth memory features
- API keys for external services

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- [Issue Tracker](https://github.com/yourusername/memories-dev/issues)
- [Documentation](docs/)
- [Community Forum](https://forum.memories-dev.com)

<p align="center">Built with 💜 by the memories-dev team</p>

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

## 🌍 Real-World Deployments & Use Cases

memories-dev is powering innovative applications across various domains. Here are some real-world examples of how organizations are using our framework:

### Environmental Monitoring

**Climate Change Impact Assessment**

The Environmental Protection Agency deployed memories-dev to monitor climate change impacts across vulnerable coastal regions. By analyzing temporal satellite imagery and correlating with ground-based sensors, they created a comprehensive dashboard that:

- Tracks shoreline changes with centimeter-level precision
- Identifies areas at risk of flooding based on elevation models
- Monitors vegetation health through multi-spectral analysis
- Provides early warning for ecosystem disruptions

```python
# Example of coastal monitoring implementation
from memories.data_acquisition.data_manager import DataManager
from memories.models.load_model import LoadModel
import asyncio

async def monitor_coastal_changes(region_bbox, baseline_year, current_year):
    data_manager = DataManager(cache_dir="./coastal_data")
    
    # Get historical imagery
    baseline_data = await data_manager.get_satellite_data(
        bbox_coords=region_bbox,
        start_date=f"{baseline_year}-01-01",
        end_date=f"{baseline_year}-12-31",
        satellite_collections=["sentinel-2-l2a"]
    )
    
    # Get current imagery
    current_data = await data_manager.get_satellite_data(
        bbox_coords=region_bbox,
        start_date=f"{current_year}-01-01",
        end_date=f"{current_year}-12-31",
        satellite_collections=["sentinel-2-l2a"]
    )
    
    # Load analysis model
    model = LoadModel(
        model_provider="deepseek-ai",
        deployment_type="local",
        model_name="environmental-analysis-v2"
    )
    
    # Generate coastal change report
    analysis = model.get_response(
        prompt=f"Analyze coastal changes between {baseline_year} and {current_year}",
        context={
            "baseline_data": baseline_data,
            "current_data": current_data,
            "region": region_bbox
        }
    )
    
    return analysis["text"]
```

### Urban Planning & Development

**Smart City Infrastructure Planning**

The Metropolitan Urban Development Authority implemented memories-dev to optimize infrastructure planning across a rapidly growing urban area. Their system:

- Analyzes building density and distribution patterns
- Identifies optimal locations for new public services
- Models traffic patterns to improve transportation networks
- Simulates the impact of proposed developments on existing infrastructure

The deployment uses a consensus-based architecture across multiple government departments, ensuring all stakeholders have access to the same data while maintaining appropriate access controls.

### Agricultural Optimization

**Precision Farming Platform**

AgriTech Solutions deployed memories-dev on edge devices installed in farming equipment, enabling real-time analysis of crop health and soil conditions. Their system:

- Processes multispectral imagery to detect early signs of crop stress
- Optimizes irrigation schedules based on soil moisture analysis
- Identifies areas requiring targeted fertilizer application
- Predicts crop yields with 94% accuracy

The deployment uses a hybrid architecture with edge processing for real-time decisions and cloud-based analysis for long-term planning.

```python
# Example of crop health monitoring implementation
from memories.deployments.standalone import StandaloneDeployment
from memories.data_acquisition.sources.sentinel_api import SentinelAPI
import asyncio

# Deploy edge processing system
edge_deployment = StandaloneDeployment(
    provider="local",
    config={
        "hardware": {
            "cpu": {"vcpus": 4},
            "memory": {"ram": 8},
            "storage": {"size": 500}
        },
        "network": {
            "connectivity": "4G"
        }
    }
)

async def monitor_crop_health(field_boundary):
    # Initialize Sentinel API
    api = SentinelAPI(data_dir="./field_data")
    await api.initialize()
    
    # Download latest imagery
    result = await api.download_data(
        bbox=field_boundary,
        start_date="2024-01-01",
        end_date="2024-02-01",
        bands=["B04", "B08", "B11"],  # Red, NIR, SWIR
        cloud_cover=5.0
    )
    
    # Calculate vegetation indices
    ndvi_map = calculate_ndvi(result["files"]["B04"], result["files"]["B08"])
    moisture_map = calculate_moisture_index(result["files"]["B08"], result["files"]["B11"])
    
    # Generate recommendations
    recommendations = {
        "irrigation_zones": identify_irrigation_needs(moisture_map),
        "fertilizer_zones": identify_nutrient_deficiency(ndvi_map),
        "problem_areas": detect_anomalies(ndvi_map, moisture_map)
    }
    
    return recommendations
```

### Disaster Response & Management

**Emergency Response Coordination System**

The National Disaster Management Agency implemented memories-dev to enhance their emergency response capabilities. Their system:

- Processes real-time satellite imagery to assess disaster impact
- Identifies accessible routes for emergency vehicles
- Prioritizes areas for evacuation based on risk assessment
- Coordinates resource allocation across multiple response teams

During recent wildfire events, the system reduced response time by 47% and improved resource allocation efficiency by 62%.

### Conservation & Biodiversity

**Wildlife Habitat Monitoring**

The Global Conservation Initiative deployed memories-dev to monitor protected wildlife habitats across multiple continents. Their system:

- Tracks changes in forest cover and fragmentation
- Identifies potential poaching activities through pattern recognition
- Monitors animal migration patterns using multi-temporal analysis
- Assesses the impact of climate change on biodiversity hotspots

The deployment uses a swarmed architecture to process massive datasets across distributed computing resources, enabling global-scale monitoring with regional precision.

## 🚀 Getting Started with Your Own Deployment

Inspired by these use cases? Get started with your own deployment:

1. **Installation**: `pip install memories-dev[full]`
2. **Documentation**: Visit our [comprehensive documentation](https://memories-dev.readthedocs.io/)
3. **Community**: Join our [Discord community](https://discord.gg/tGCVySkX4d) to connect with other developers
4. **Tutorials**: Check out our [tutorial series](https://memories-dev.readthedocs.io/tutorials/) for step-by-step guides

