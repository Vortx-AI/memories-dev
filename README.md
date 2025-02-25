# memories-dev

<div align="center">

**Building the World's Memory for Artificial General Intelligence**

[![Documentation](https://img.shields.io/badge/docs-latest-brightgreen.svg)](https://memories-dev.readthedocs.io/index.html)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Version](https://img.shields.io/badge/version-2.1.0-blue.svg)](https://github.com/Vortx-AI/memories-dev/releases/tag/v2.1.0)
[![Discord](https://img.shields.io/discord/1339432819784683522?color=7289da&label=Discord&logo=discord&logoColor=white)](https://discord.gg/tGCVySkX4d)

<a href="https://www.producthunt.com/posts/memories-dev?embed=true&utm_source=badge-featured&utm_medium=badge&utm_souce=badge-memories&#0045;dev" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/featured.svg?post_id=879661&theme=light&t=1739530783374" alt="memories&#0046;dev - Collective&#0032;AGI&#0032;Memory | Product Hunt" style="width: 250px; height: 54px;" width="250" height="54" /></a>

</div>

## �� Overview

memories-dev is a comprehensive Python library for creating and managing memories using satellite imagery, vector data, and large language models. It provides a unified interface for data acquisition, processing, and model integration, enabling developers to build sophisticated applications with rich contextual understanding of the physical world.

### 🚀 Key Features

- **Data Acquisition**: 
  - Satellite imagery (Sentinel-2, Landsat)
  - Vector data (OpenStreetMap, Overture Maps)
  - Environmental metrics
  - Temporal-spatial data integration

- **Model Integration**: 
  - Local model deployment
  - API-based model access
  - Multiple provider support (DeepSeek, OpenAI, Anthropic)
  - GPU acceleration

- **Deployment Options**: 
  - Local deployment
  - Cloud deployment (AWS, GCP, Azure)
  - Distributed systems
  - Container orchestration

- **Advanced Features**: 
  - Concurrent data processing
  - GPU memory management
  - Caching and optimization
  - Error handling and validation

## System Architecture

The system is built on three core components:

1. **Data Acquisition**: Collects and processes data from various sources
2. **Model System**: Manages model loading, inference, and API connections
3. **Deployment**: Handles deployment configurations and resource management

## Quick Start

### Installation

```bash
# Basic installation
pip install memories-dev

# With GPU support
pip install memories-dev[gpu]
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

### Vector Data

```python
from memories.data_acquisition.data_manager import DataManager
import asyncio

# Initialize data manager
data_manager = DataManager(cache_dir="./data_cache")

# Get vector data
vector_data = await data_manager.get_vector_data(
    bbox={
        'xmin': -122.4018, 'ymin': 37.7914,
        'xmax': -122.3928, 'ymax': 37.7994
    },
    layers=["buildings", "roads", "landuse"]
)

# Access individual sources
buildings = vector_data["buildings"]
roads = vector_data["roads"]
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

# Generate text
response = model.get_response("Explain the impact of climate change on urban areas")
print(response["text"])
```

## 🚀 Deployment

memories-dev supports various deployment configurations:

### Cloud Deployment

```python
from memories.deployment.cloud import CloudDeployment

# Configure GCP deployment
deployment = CloudDeployment(
    provider="gcp",
    config={
        "machine_type": "n1-standard-8",
        "accelerator": "nvidia-tesla-t4",
        "accelerator_count": 1,
        "region": "us-central1",
        "zone": "us-central1-a"
    }
)

# Deploy the application
deployment.deploy()
```

### Distributed Deployment

```python
from memories.deployment.distributed import DistributedDeployment

# Configure AWS distributed deployment
deployment = DistributedDeployment(
    provider="aws",
    config={
        "instance_type": "p3.2xlarge",
        "node_count": 3,
        "quorum_size": 2,
        "region": "us-east-1",
        "availability_zones": ["us-east-1a", "us-east-1b", "us-east-1c"]
    }
)

# Deploy the distributed system
deployment.deploy()
```

## 🛠️ Installation

### System Requirements

- **Python**: 3.9 - 3.13
- **OS**: Linux, macOS, Windows
- **Memory**: 8GB RAM (minimum), 16GB+ (recommended)
- **Storage**: 10GB+ available space
- **GPU**: Optional, but recommended for optimal performance

### Installation Options

#### 1. CPU-only Installation (Default)
```bash
pip install memories-dev
```

#### 2. GPU Support Installation
```bash
pip install memories-dev[gpu]
```

#### 3. Development Installation
```bash
pip install memories-dev[dev]
```

#### 4. Documentation Tools
```bash
pip install memories-dev[docs]
```

## 📚 Documentation

For comprehensive documentation, visit [memories-dev.readthedocs.io](https://memories-dev.readthedocs.io/).

### Key Documentation Sections

- [Quick Start Guide](https://memories-dev.readthedocs.io/quickstart.html)
- [User Guide](https://memories-dev.readthedocs.io/user_guide/index.html)
- [API Reference](https://memories-dev.readthedocs.io/api_reference/index.html)
- [Development Guide](https://memories-dev.readthedocs.io/development/index.html)

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for more details.

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Community

- Join our [Discord community](https://discord.com/invite/7qAFEekp) for discussions
- Follow our [Blog](https://memories.dev/blog) for updates and tutorials
- Check out our [Examples Gallery](https://memories.dev/examples)

## Citation

If you use memories-dev in your research, please cite:

```bibtex
@software{memories_dev_2024,
  title={memories-dev: Collective Memory Infrastructure for AGI},
  author={Vortx AI Team},
  year={2024},
  url={https://github.com/Vortx-AI/memories-dev}
}
```

## Advanced Usage

### Memory Formation with Custom Sources

```python
from memories.core.memory import MemoryStore
from memories.data_acquisition.sources import CustomSource

# Initialize with custom data source
memory_store = MemoryStore()
custom_source = CustomSource(
    data_type="environmental",
    update_frequency="1h"
)

# Create specialized memories
memories = memory_store.create_memories(
    sources=[custom_source],
    location_bounds={
        "min_lat": 37.7,
        "max_lat": 37.8,
        "min_lon": -122.5,
        "max_lon": -122.4
    },
    temporal_range={
        "start": "2024-01-01",
        "end": "2024-02-01"
    }
)
```

### Advanced Query Patterns

```python
# Complex spatial-temporal query
results = memory_store.query(
    location=(37.7749, -122.4194),
    radius=5000,  # meters
    time_range=("2024-01-01", "2024-02-01"),
    data_types=["satellite", "environmental"],
    aggregation="hourly"
)

# Memory synthesis
synthesis = memory_store.synthesize(
    memories=results,
    context="urban development impact",
    temporal_resolution="daily"
)
```

## 🚀 Deployment Patterns

memories-dev supports three powerful deployment patterns to meet diverse operational needs:

### 1. Standalone Deployment
Optimized for single-tenant applications requiring maximum performance:
- High-performance computing workloads
- Machine learning model inference
- Real-time data processing
- Direct hardware access

### 2. Consensus Deployment
Perfect for distributed systems requiring strong consistency:
- Distributed databases
- Blockchain networks
- Distributed caching systems
- Mission-critical applications

### 3. Swarmed Deployment
Ideal for globally distributed applications:
- Edge computing applications
- Content delivery networks
- IoT device networks
- Global data distribution

Each deployment pattern is supported across major cloud providers (AWS, Azure, GCP) with:
- Optimized hardware configurations
- Comprehensive security features
- Advanced monitoring and logging
- Automated scaling capabilities

For detailed deployment instructions and architecture diagrams, see the [Deployment Documentation](deployments/README.md).

---

<div align="center">

**Empowering AGI with Real-World Context**

<p align="center">Built with 💜 by the memories-dev team</p>

<p align="center">
<a href="https://discord.com/invite/7qAFEekp">Discord</a> •
<a href="https://memories.dev/blog">Blog</a> •
<a href="https://memories.dev/examples">Examples</a>
</p>

</div>

