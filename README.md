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
    
    # Get transportation network
    transportation = await overture_source.get_transportation(
        bbox=bbox,
        types=["road", "railway", "path"]
    )
    
    # Get administrative boundaries
    boundaries = await overture_source.get_boundaries(
        bbox=bbox,
        admin_levels=[1, 2, 3]
    )
    
    return {
        "places": places,
        "buildings": buildings,
        "transportation": transportation,
        "boundaries": boundaries
    }

# Run the async function
overture_data = asyncio.run(get_overture_data())

# Process the data
for place in overture_data["places"][:5]:
    print(f"Place: {place.name}, Category: {place.category}")
```

### Integrated Data Manager

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

# Get comprehensive location data
async def get_location_data():
    location_data = await data_manager.get_location_data(
        bbox_coords=bbox,
        start_date="2023-01-01",
        end_date="2023-01-31",
        layers=["buildings", "roads", "landuse", "water", "pois"]
    )
    return location_data

# Run the async function
location_data = asyncio.run(get_location_data())

# Access the integrated data
satellite_imagery = location_data["satellite"]
vector_features = location_data["vector"]
environmental = location_data["environmental"]

print(f"Satellite scenes: {len(satellite_imagery['scenes'])}")
print(f"Vector features: {sum(len(layer) for layer in vector_features.values())}")
```

## 🧠 Model System

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
    api_key="your-api-key"  # Or set OPENAI_API_KEY environment variable
)

# Generate text with parameters
response = model.get_response(
    "Explain the impact of climate change on urban areas",
    temperature=0.7,
    max_tokens=500
)
print(response["text"])
```

### Multi-Provider Example

```python
from memories.models.load_model import LoadModel

# Initialize models from different providers
models = {
    "openai": LoadModel(
        model_provider="openai",
        deployment_type="api",
        model_name="gpt-4"
    ),
    "anthropic": LoadModel(
        model_provider="anthropic",
        deployment_type="api",
        model_name="claude-3-opus"
    ),
    "deepseek": LoadModel(
        model_provider="deepseek-ai",
        deployment_type="local",
        model_name="deepseek-coder-small",
        use_gpu=True
    )
}

# Generate responses from each model
prompt = "Explain how satellite imagery can be used for urban planning"
responses = {}

for provider, model in models.items():
    responses[provider] = model.get_response(prompt)
    print(f"\n--- {provider.upper()} RESPONSE ---")
    print(responses[provider]["text"])

# Clean up resources
for model in models.values():
    model.cleanup()
```

## 🚀 Deployment

memories-dev supports various deployment configurations:

### Standalone Deployment

```python
from memories.deployments.standalone import StandaloneDeployment

# Configure GCP standalone deployment
deployment = StandaloneDeployment(
    provider="gcp",
    config={
        "instance": {
            "machine_type": "n2-standard-4",
            "zone": "us-west1-a"
        },
        "hardware": {
            "cpu": {"vcpus": 4},
            "memory": {"ram": 16},
            "storage": {
                "boot_disk": {"size": 100, "type": "pd-ssd"}
            }
        },
        "network": {
            "vpc_name": "memories-vpc",
            "public_ip": True
        }
    }
)

# Deploy the application
deployment.deploy()
```

### Consensus-based Deployment

```python
from memories.deployments.consensus import ConsensusDeployment

# Configure AWS consensus deployment
deployment = ConsensusDeployment(
    provider="aws",
    config={
        "consensus": {
            "algorithm": "raft",
            "min_nodes": 3,
            "max_nodes": 5,
            "quorum_size": 2
        },
        "node_specs": [
            {
                "id": "node1",
                "instance_type": "t3.medium",
                "region": "us-west-2",
                "zone": "us-west-2a"
            },
            {
                "id": "node2",
                "instance_type": "t3.medium",
                "region": "us-west-2",
                "zone": "us-west-2b"
            },
            {
                "id": "node3",
                "instance_type": "t3.medium",
                "region": "us-west-2",
                "zone": "us-west-2c"
            }
        ],
        "network": {
            "vpc_id": "vpc-12345",
            "subnet_ids": ["subnet-a1b2c3", "subnet-d4e5f6", "subnet-g7h8i9"]
        }
    }
)

# Deploy the consensus-based system
deployment.deploy()
```

### Swarmed Deployment

```python
from memories.deployments.swarmed import SwarmedDeployment

# Configure Azure swarmed deployment
deployment = SwarmedDeployment(
    provider="azure",
    config={
        "swarm": {
            "min_nodes": 3,
            "max_nodes": 10,
            "manager_nodes": 3,
            "worker_nodes": 5
        },
        "node_specs": {
            "manager_specs": {
                "instance_type": "Standard_D2s_v3",
                "storage_size": 100
            },
            "worker_specs": {
                "instance_type": "Standard_B2s",
                "storage_size": 50
            }
        },
        "network": {
            "vnet_name": "swarmed-vnet",
            "subnet_name": "swarmed-subnet",
            "nsg_name": "swarmed-nsg",
            "resource_group": "swarmed-rg",
            "location": "westus2"
        },
        "scaling": {
            "min_worker_nodes": 3,
            "max_worker_nodes": 10,
            "target_cpu_utilization": 70
        }
    }
)

# Deploy the swarmed system
deployment.deploy()
```

## 🌍 Real-World Use Cases

### Urban Planning and Development

```python
from memories.data_acquisition.data_manager import DataManager
from memories.models.load_model import LoadModel
import asyncio
import matplotlib.pyplot as plt
import folium

# Initialize components
data_manager = DataManager(cache_dir="./urban_planning_cache")
model = LoadModel(
    model_provider="openai",
    deployment_type="api",
    model_name="gpt-4"
)

# Define area of interest (Downtown Seattle)
bbox = {
    'xmin': -122.3400,
    'ymin': 47.5950,
    'xmax': -122.3200,
    'ymax': 47.6150
}

# Get comprehensive data
async def analyze_urban_area():
    # Get satellite imagery
    satellite_data = await data_manager.get_satellite_data(
        bbox_coords=bbox,
        start_date="2023-01-01",
        end_date="2023-01-31"
    )
    
    # Get vector data
    vector_data = await data_manager.get_vector_data(
        bbox=bbox,
        layers=["buildings", "roads", "landuse", "amenities"]
    )
    
    # Calculate urban metrics
    building_density = len(vector_data["buildings"]) / (
        (bbox['xmax'] - bbox['xmin']) * (bbox['ymax'] - bbox['ymin'])
    )
    
    road_length = sum(road.length for road in vector_data["roads"])
    green_space_area = sum(
        area.area for area in vector_data["landuse"] 
        if area.properties.get("landuse") in ["park", "forest", "grass"]
    )
    
    # Generate analysis with LLM
    urban_prompt = f"""
    Analyze this urban area with the following metrics:
    - Building density: {building_density:.2f} buildings per sq km
    - Road network length: {road_length:.2f} km
    - Green space area: {green_space_area:.2f} sq km
    
    Provide urban planning recommendations for improving:
    1. Walkability
    2. Green space access
    3. Public transportation
    4. Housing density
    """
    
    analysis = model.get_response(urban_prompt)
    
    return {
        "satellite": satellite_data,
        "vector": vector_data,
        "metrics": {
            "building_density": building_density,
            "road_length": road_length,
            "green_space_area": green_space_area
        },
        "analysis": analysis["text"]
    }

# Run the analysis
urban_analysis = asyncio.run(analyze_urban_area())

# Create visualization
m = folium.Map(
    location=[(bbox['ymin'] + bbox['ymax'])/2, (bbox['xmin'] + bbox['xmax'])/2],
    zoom_start=15
)

# Add buildings
for building in urban_analysis["vector"]["buildings"][:1000]:  # Limit for performance
    folium.Polygon(
        locations=[[p[1], p[0]] for p in building.exterior.coords],
        color='blue',
        fill=True,
        fill_color='blue',
        fill_opacity=0.4
    ).add_to(m)

# Add roads
for road in urban_analysis["vector"]["roads"][:500]:  # Limit for performance
    folium.PolyLine(
        locations=[[p[1], p[0]] for p in road.coords],
        color='black',
        weight=2
    ).add_to(m)

# Add green spaces
for area in urban_analysis["vector"]["landuse"]:
    if area.properties.get("landuse") in ["park", "forest", "grass"]:
        folium.Polygon(
            locations=[[p[1], p[0]] for p in area.exterior.coords],
            color='green',
            fill=True,
            fill_color='green',
            fill_opacity=0.4
        ).add_to(m)

# Save the map
m.save('urban_analysis.html')

# Print the analysis
print(urban_analysis["analysis"])

# Clean up
model.cleanup()
```

### Environmental Monitoring

```python
from memories.data_acquisition.data_manager import DataManager
from memories.models.load_model import LoadModel
import asyncio
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Initialize components
data_manager = DataManager(cache_dir="./environmental_cache")
model = LoadModel(
    model_provider="anthropic",
    deployment_type="api",
    model_name="claude-3-opus"
)

# Define area of interest (Amazon Rainforest region)
bbox = {
    'xmin': -60.0,
    'ymin': -10.0,
    'xmax': -55.0,
    'ymax': -5.0
}

# Define time series (5 years of data)
end_date = datetime.now()
start_date = end_date - timedelta(days=5*365)
time_points = 10  # Sample 10 points over 5 years

# Get time series data
async def monitor_deforestation():
    forest_coverage = []
    dates = []
    
    # Generate dates
    for i in range(time_points):
        date = start_date + (end_date - start_date) * (i / (time_points - 1))
        dates.append(date)
        
        # Get satellite data for this date
        satellite_data = await data_manager.get_satellite_data(
            bbox_coords=bbox,
            start_date=(date - timedelta(days=15)).strftime("%Y-%m-%d"),
            end_date=(date + timedelta(days=15)).strftime("%Y-%m-%d")
        )
        
        # Calculate forest coverage (simplified)
        ndvi_values = satellite_data["ndvi_mean"] if "ndvi_mean" in satellite_data else 0.65 - (i * 0.03)
        forest_coverage.append(ndvi_values)
    
    # Generate analysis with LLM
    env_prompt = f"""
    Analyze this time series of forest coverage in the Amazon rainforest:
    
    Dates: {[d.strftime("%Y-%m-%d") for d in dates]}
    NDVI values: {forest_coverage}
    
    Provide an environmental assessment including:
    1. Rate of deforestation
    2. Potential ecological impacts
    3. Recommendations for conservation efforts
    4. Prediction of future trends if current patterns continue
    """
    
    analysis = model.get_response(env_prompt)
    
    return {
        "dates": dates,
        "forest_coverage": forest_coverage,
        "analysis": analysis["text"]
    }

# Run the analysis
deforestation_analysis = asyncio.run(monitor_deforestation())

# Create visualization
plt.figure(figsize=(12, 6))
plt.plot(deforestation_analysis["dates"], deforestation_analysis["forest_coverage"], 'g-', marker='o')
plt.title('Forest Coverage Over Time (NDVI)')
plt.xlabel('Date')
plt.ylabel('NDVI (Normalized Difference Vegetation Index)')
plt.grid(True)
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('deforestation_trend.png')

# Print the analysis
print(deforestation_analysis["analysis"])

# Clean up
model.cleanup()
```

### Disaster Response Planning

```python
from memories.data_acquisition.data_manager import DataManager
from memories.models.load_model import LoadModel
import asyncio
import folium
from folium.plugins import HeatMap
import numpy as np

# Initialize components
data_manager = DataManager(cache_dir="./disaster_response_cache")
model = LoadModel(
    model_provider="openai",
    deployment_type="api",
    model_name="gpt-4"
)

# Define area of interest (New Orleans)
bbox = {
    'xmin': -90.1,
    'ymin': 29.9,
    'xmax': -89.9,
    'ymax': 30.1
}

# Analyze flood risk and plan response
async def analyze_flood_risk():
    # Get elevation data
    elevation_data = await data_manager.get_elevation_data(bbox)
    
    # Get building and infrastructure data
    vector_data = await data_manager.get_vector_data(
        bbox=bbox,
        layers=["buildings", "roads", "critical_infrastructure", "evacuation_routes"]
    )
    
    # Simulate flood levels (simplified)
    flood_levels = np.random.normal(1.5, 0.5, size=(100, 100))
    
    # Identify at-risk areas
    at_risk_buildings = []
    for building in vector_data["buildings"]:
        building_elevation = elevation_data.sample(building.centroid)
        if building_elevation < 2.0:  # Below 2m elevation
            at_risk_buildings.append(building)
    
    # Generate evacuation plan with LLM
    disaster_prompt = f"""
    Create a flood disaster response plan for New Orleans with the following data:
    
    - Total buildings: {len(vector_data["buildings"])}
    - At-risk buildings: {len(at_risk_buildings)} (below 2m elevation)
    - Critical infrastructure: {len(vector_data["critical_infrastructure"])}
    - Evacuation routes: {len(vector_data["evacuation_routes"])}
    
    Include in your plan:
    1. Evacuation zones and priorities
    2. Emergency shelter locations
    3. Resource allocation strategy
    4. Communication plan for residents
    5. Timeline for evacuation phases
    """
    
    response_plan = model.get_response(disaster_prompt)
    
    return {
        "elevation_data": elevation_data,
        "vector_data": vector_data,
        "at_risk_buildings": at_risk_buildings,
        "flood_levels": flood_levels,
        "response_plan": response_plan["text"]
    }

# Run the analysis
flood_analysis = asyncio.run(analyze_flood_risk())

# Create visualization
m = folium.Map(
    location=[(bbox['ymin'] + bbox['ymax'])/2, (bbox['xmin'] + bbox['xmax'])/2],
    zoom_start=13
)

# Add flood risk heatmap
heat_data = []
for i in range(100):
    for j in range(100):
        lat = bbox['ymin'] + (bbox['ymax'] - bbox['ymin']) * (i / 100)
        lon = bbox['xmin'] + (bbox['xmax'] - bbox['xmin']) * (j / 100)
        intensity = flood_analysis["flood_levels"][i, j]
        heat_data.append([lat, lon, intensity])

HeatMap(heat_data).add_to(m)

# Add at-risk buildings
for building in flood_analysis["at_risk_buildings"][:500]:  # Limit for performance
    folium.Polygon(
        locations=[[p[1], p[0]] for p in building.exterior.coords],
        color='red',
        fill=True,
        fill_color='red',
        fill_opacity=0.6,
        tooltip="At-risk building"
    ).add_to(m)

# Add evacuation routes
for route in flood_analysis["vector_data"]["evacuation_routes"]:
    folium.PolyLine(
        locations=[[p[1], p[0]] for p in route.coords],
        color='green',
        weight=4,
        tooltip="Evacuation route"
    ).add_to(m)

# Save the map
m.save('flood_risk_map.html')

# Print the response plan
print(flood_analysis["response_plan"])

# Clean up
model.cleanup()
```

## 📚 Documentation

For more detailed documentation, visit [memories-dev.readthedocs.io](https://memories-dev.readthedocs.io/index.html).

- [Installation Guide](https://memories-dev.readthedocs.io/user_guide/installation.html)
- [API Reference](https://memories-dev.readthedocs.io/api_reference/index.html)
- [User Guide](https://memories-dev.readthedocs.io/user_guide/index.html)
- [Examples](https://memories-dev.readthedocs.io/user_guide/examples.html)
- [Contributing](https://memories-dev.readthedocs.io/development/contributing.html)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

<p align="center">Built with 💜 by the memories-dev team</p>

