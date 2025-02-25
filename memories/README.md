# 🧠 memories-dev

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Tests](https://github.com/Vortx-AI/memories-dev/actions/workflows/tests.yml/badge.svg)](https://github.com/Vortx-AI/memories-dev/actions/workflows/tests.yml)

> Collective AGI memory - v2.0.2 (June 15, 2024)

## What's New in Version 2.0.2

### New Features
- **Enhanced Data Sources**: Complete integration with Overture Maps and OpenStreetMap
- **Multi-model Inference**: Compare results from multiple LLM providers
- **Streaming Responses**: Real-time streaming for all supported model providers
- **Memory Optimization**: Advanced memory usage with automatic tier balancing
- **Distributed Memory**: Support for distributed memory across multiple nodes

### Improvements
- **Data Acquisition**: Multi-source fusion and temporal analysis capabilities
- **Model Integration**: Function calling support and improved caching
- **Memory Management**: Intelligent compression and migration policies
- **Deployment Options**: Enhanced standalone, consensus, and swarmed deployments
- **Documentation**: Comprehensive examples and real-world use cases

## 🌟 Overview

memories-dev is a comprehensive Python library for building and managing collective AGI memory systems using satellite imagery, vector data, and large language models. It provides a robust architecture for memory formation, retrieval, and synthesis across multiple modalities, enabling AI models to maintain and utilize contextual understanding across interactions.

### 🎯 Key Goals
- Enable persistent memory for AI systems
- Provide context-aware intelligence
- Support multi-modal memory integration
- Ensure scalable and efficient memory operations
- Maintain privacy and security in memory access

## 🚀 Quick Start

```python
from memories import MemorySystem
from memories.models import LoadModel
from memories.data_acquisition import DataManager

# Initialize components
memory_system = MemorySystem(
    store_type="vector",  # Options: "vector", "graph", "hybrid"
    vector_store="milvus",
    embedding_model="text-embedding-3-small"
)

data_manager = DataManager(cache_dir="./data_cache")
model = LoadModel(
    model_provider="openai",
    deployment_type="api",
    model_name="gpt-4"
)

# Define area of interest
bbox = {
    'xmin': -122.4018,
    'ymin': 37.7914,
    'xmax': -122.3928,
    'ymax': 37.7994
}

# Get satellite and vector data
satellite_data = await data_manager.get_satellite_data(
    bbox_coords=bbox,
    start_date="2023-01-01",
    end_date="2023-01-31"
)

vector_data = await data_manager.get_vector_data(
    bbox=bbox,
    layers=["buildings", "roads", "landuse"]
)

# Store a memory with multi-modal data
memory_id = memory_system.store(
    content={
        "satellite_imagery": satellite_data,
        "vector_features": vector_data,
        "text_description": "Urban area with mixed residential and commercial buildings"
    },
    metadata={
        "location": bbox,
        "timestamp": "2024-06-15T10:30:00Z",
        "source": "satellite_analysis"
    }
)

# Query memories with context
relevant_memories = memory_system.query(
    query="What is the building density in this urban area?",
    location=bbox,
    time_range=("2024-01-01", "2024-06-15")
)

# Generate insights with LLM
prompt = f"Analyze this location with the following data: {satellite_data}, {vector_data}, {relevant_memories}"
insights = model.get_response(prompt)
print(insights["text"])

# Clean up
model.cleanup()
```

## 🏗️ Installation

### Standard Installation
```bash
# Basic installation
pip install memories-dev

# With GPU support
pip install memories-dev[gpu]

# Full installation with all features
pip install memories-dev[all]
```

### Development Installation
```bash
# Clone repository
git clone https://github.com/Vortx-AI/memories-dev.git
cd memories-dev

# Install development dependencies
pip install -e ".[dev]"

# Install documentation tools
pip install -e ".[docs]"
```

## 🔧 System Requirements

### Minimum (Development)
- Python 3.9+
- 16GB RAM
- 4+ CPU cores
- 20GB storage
- Docker & Docker Compose (for local development)

### Production (Recommended)
- 32GB+ RAM
- 8+ CPU cores
- NVIDIA GPU with 8GB+ VRAM
- 100GB+ SSD storage
- Kubernetes cluster for distributed deployment

## 📊 Monitoring & Observability

### Available in v2.0.2
- Comprehensive logging system with structured output
- Memory operation metrics with Prometheus integration
- Performance tracking for core operations
- Health check endpoints
- Grafana dashboards for memory metrics
- Real-time memory operation monitoring
- Advanced performance analytics
- Automated alerting system

## 🧪 Development Features

### Core Features
- Multi-tier memory store implementations
- Advanced data acquisition from multiple sources
- Integration with multiple LLM providers
- Distributed memory operations
- Memory compression and optimization
- Advanced security features

## 📁 Project Structure

```
memories-dev/
├── examples/              # Example implementations
│   ├── property_analyzer.py  # Real estate analysis
│   ├── water_bodies_monitor.py # Water monitoring
│   ├── location_ambience.py # Location analysis
│   ├── traffic_analyzer.py # Traffic patterns
│   ├── urban_planning.py # Urban development
│   ├── environmental_monitoring.py # Environmental tracking
│   ├── disaster_response.py # Disaster planning
│   └── model_comparison.py # Multi-model comparison
│
├── memories/             # Main package
│   ├── core/            # Core memory system
│   │   ├── memory_manager.py # Memory management
│   │   └── policies.py # Memory policies
│   │
│   ├── data_acquisition/ # Data Collection
│   │   ├── sources/     # Data sources
│   │   │   ├── sentinel_api.py # Sentinel-2
│   │   │   ├── sentinel3_api.py # Sentinel-3
│   │   │   ├── landsat_api.py # Landsat
│   │   │   ├── maxar_api.py # Maxar
│   │   │   ├── osm_api.py # OpenStreetMap
│   │   │   ├── overture_api.py # Overture Maps
│   │   │   ├── wfs_api.py # WFS
│   │   │   └── planetary_compute.py # Planetary Computer
│   │   ├── processing/ # Data processing
│   │   │   ├── cloud_mask.py # Cloud masking
│   │   │   ├── indices.py # Spectral indices
│   │   │   ├── fusion.py # Data fusion
│   │   │   └── validation.py # Data validation
│   │   └── data_manager.py # Data management
│   │
│   ├── models/          # AI Models
│   │   ├── base_model.py # Base model implementation
│   │   ├── load_model.py # Model loader
│   │   ├── api_connector.py # API connectors
│   │   ├── streaming.py # Streaming responses
│   │   ├── caching.py # Response caching
│   │   ├── function_calling.py # Function calling
│   │   └── multi_model.py # Multi-model inference
│   │
│   └── deployments/     # Deployment options
│       ├── standalone/ # Standalone deployment
│       ├── consensus/ # Consensus deployment
│       └── swarmed/ # Swarmed deployment
│
├── tests/              # Test Suite
│   ├── unit/          # Unit tests
│   └── integration/   # Integration tests
│
└── docs/              # Documentation
    ├── api/           # API documentation
    └── guides/        # User guides
```

## 🧩 Core Components Explained

### 1. 📡 Data Acquisition
Handles multi-modal data ingestion from various sources:

```python
from memories.data_acquisition.data_manager import DataManager
from memories.data_acquisition.processing.indices import calculate_ndvi

# Initialize data manager
manager = DataManager(cache_dir="./data_cache")

# Define area of interest
bbox = [-122.4, 37.7, -122.3, 37.8]  # [west, south, east, north]

# Get satellite data
sentinel_data = await manager.get_satellite_data(
    bbox=bbox,
    start_date="2024-01-01",
    end_date="2024-01-31",
    collection="sentinel-2-l2a"
)

# Get vector data
vector_data = await manager.get_vector_data(
    bbox=bbox,
    layers=["buildings", "roads", "landuse"],
    source="overture"  # Options: "overture", "osm", "wfs"
)

# Calculate vegetation index
ndvi = calculate_ndvi(sentinel_data)

# Combine data
combined_data = {
    "satellite": sentinel_data,
    "vector": vector_data,
    "indices": {"ndvi": ndvi}
}
```

### 2. 🧠 Memory Management
Multi-tier memory system for efficient data storage and retrieval:

```python
from memories.core.memory_manager import MemoryManager
from memories.core.policies import MigrationPolicy

# Define migration policy
migration_policy = MigrationPolicy(
    hot_to_warm_threshold=24,  # hours
    warm_to_cold_threshold=72,  # hours
    cold_to_glacier_threshold=30  # days
)

# Initialize memory manager
manager = MemoryManager(
    hot_memory_size=2,    # GB for GPU memory
    warm_memory_size=8,   # GB for in-memory storage
    cold_memory_size=50,  # GB for on-device storage
    glacier_memory_size=500,  # GB for off-device storage
    migration_policy=migration_policy
)

# Store data with automatic tier placement
manager.store(
    key="location_123",
    data=combined_data
)

# Retrieve data (automatically fetches from appropriate tier)
result = manager.retrieve(key="location_123")

# Create memory snapshot
snapshot_id = manager.create_snapshot(
    tiers=["hot", "warm"],
    description="Pre-deployment state"
)
```

### 3. 🤖 Model Integration
Integration with multiple LLM providers:

```python
from memories.models.load_model import LoadModel
from memories.models.multi_model import MultiModelInference

# Initialize models
openai_model = LoadModel(
    model_provider="openai",
    deployment_type="api",
    model_name="gpt-4"
)

anthropic_model = LoadModel(
    model_provider="anthropic",
    deployment_type="api",
    model_name="claude-3-opus"
)

# Create multi-model inference
multi_model = MultiModelInference(
    models=[openai_model, anthropic_model],
    aggregation_method="consensus"
)

# Get streaming response
for chunk in openai_model.get_streaming_response("Analyze this urban area"):
    print(chunk, end="", flush=True)

# Get responses from all models
results = multi_model.get_responses("Analyze this satellite image for urban development")

# Get aggregated response
consensus = multi_model.get_aggregated_response()
```

### 4. 🚀 Deployment
Flexible deployment options:

```python
from memories.deployments.standalone import StandaloneDeployment
from memories.deployments.consensus import ConsensusDeployment
from memories.deployments.swarmed import SwarmedDeployment

# Standalone deployment (single node)
standalone = StandaloneDeployment(
    provider="gcp",
    config={
        "hardware": {
            "cpu": {"vcpus": 8},
            "memory": {"ram": 32},
            "gpu": {"type": "nvidia-tesla-t4", "count": 1},
            "storage": {"size": 100}
        }
    }
)

# Consensus deployment (multiple coordinated nodes)
consensus = ConsensusDeployment(
    provider="aws",
    node_count=3,
    config={
        "hardware": {
            "cpu": {"vcpus": 16},
            "memory": {"ram": 64},
            "gpu": {"type": "nvidia-a10g", "count": 1},
            "storage": {"size": 200}
        },
        "consensus": {
            "algorithm": "raft",
            "timeout": 5000
        }
    }
)

# Swarmed deployment (distributed processing)
swarmed = SwarmedDeployment(
    provider="azure",
    node_count=5,
    config={
        "hardware": {
            "cpu": {"vcpus": 8},
            "memory": {"ram": 32},
            "storage": {"size": 100}
        },
        "swarm": {
            "orchestrator": "kubernetes",
            "scaling": {"min_nodes": 3, "max_nodes": 10}
        }
    }
)

# Deploy the application
deployment_id = standalone.deploy()
```

## 🌍 Real-World Use Cases

### Urban Planning
Analyze urban development patterns and optimize city planning:

```python
from memories.examples.urban_planning import UrbanPlanner

planner = UrbanPlanner(
    city="San Francisco",
    bbox=[-122.5, 37.7, -122.3, 37.8]
)

# Analyze building density
density_map = planner.analyze_building_density()

# Identify green spaces
green_spaces = planner.identify_green_spaces()

# Generate development recommendations
recommendations = planner.generate_recommendations(
    focus_areas=["housing", "transportation", "sustainability"]
)
```

### Environmental Monitoring
Track environmental changes and predict future trends:

```python
from memories.examples.environmental_monitoring import EnvironmentalMonitor

monitor = EnvironmentalMonitor(
    region="Amazon Rainforest",
    start_date="2020-01-01",
    end_date="2024-06-01"
)

# Track deforestation
deforestation = monitor.track_deforestation()

# Analyze climate impact
climate_impact = monitor.analyze_climate_impact()

# Predict future changes
predictions = monitor.predict_changes(years_ahead=5)
```

### Disaster Response Planning
Create disaster response plans based on historical and current data:

```python
from memories.examples.disaster_response import DisasterPlanner

planner = DisasterPlanner(
    region="Florida Coast",
    disaster_type="hurricane"
)

# Generate flood risk maps
flood_risk = planner.generate_flood_risk_map()

# Create evacuation routes
evacuation_routes = planner.create_evacuation_routes()

# Identify critical infrastructure
critical_infrastructure = planner.identify_critical_infrastructure()
```

## 📚 Documentation

Comprehensive documentation is available at [https://docs.memories-dev.ai](https://docs.memories-dev.ai):

- **Getting Started Guide**: Basic setup and first steps
- **API Reference**: Detailed API documentation
- **Tutorials**: Step-by-step guides for common tasks
- **Examples**: Real-world use cases and implementations
- **Deployment Guide**: Instructions for different deployment options
- **Contributing Guide**: How to contribute to the project

## 🤝 Contributing

We welcome contributions from the community! Please see our [Contributing Guide](CONTRIBUTING.md) for details on how to get started.

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

<p align="center">Built with 💜 by the memories-dev team</p>
