# 🧠 memories-dev Core Module

<div align="center">

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Tests](https://github.com/Vortx-AI/memories-dev/actions/workflows/tests.yml/badge.svg)](https://github.com/Vortx-AI/memories-dev/actions/workflows/tests.yml)

**Building the World's Memory for Artificial General Intelligence**

</div>

> Collective AGI memory - v2.0.4 (Scheduled for March 3, 2025)

## 📋 Release Timeline
- **v1.0.0** - Released on February 14, 2025: Initial stable release with core functionality
- **v2.0.4** - Scheduled for March 3, 2025: Current development version with enhanced features

## 🌟 What's New in Version 2.0.4

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

## 🚀 Overview

memories-dev is a comprehensive Python library for building and managing collective AGI memory systems using satellite imagery, vector data, and large language models. It provides a robust architecture for memory formation, retrieval, and synthesis across multiple modalities, enabling AI models to maintain and utilize contextual understanding across interactions.

### 🎯 Key Goals
- Enable persistent memory for AI systems
- Provide context-aware intelligence
- Support multi-modal memory integration
- Ensure scalable and efficient memory operations
- Maintain privacy and security in memory access

## 💻 Quick Start

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
        "timestamp": "2025-02-15T10:30:00Z",
        "source": "satellite_analysis"
    }
)

# Query memories with context
relevant_memories = memory_system.query(
    query="What is the building density in this urban area?",
    location=bbox,
    time_range=("2025-01-01", "2025-02-15")
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

### Available in v2.0.4
- Comprehensive logging system with structured output
- Memory operation metrics with Prometheus integration
- Performance tracking for core operations
- Health check endpoints
- Grafana dashboards for memory metrics
- Real-time memory operation monitoring
- Advanced performance analytics
- Automated alerting system

## 📁 Project Structure

```
memories/
├── core/            # Core memory system
│   ├── memory_manager.py # Memory management
│   └── policies.py # Memory policies
│
├── data_acquisition/ # Data Collection
│   ├── sources/     # Data sources
│   │   ├── sentinel_api.py # Sentinel-2
│   │   ├── landsat_api.py # Landsat
│   │   ├── osm_api.py # OpenStreetMap
│   │   ├── overture_api.py # Overture Maps
│   │   ├── wfs_api.py # WFS
│   │   └── planetary_compute.py # Planetary Computer
│   ├── processing/ # Data processing
│   │   ├── cloud_mask.py # Cloud masking
│   │   ├── indices.py # Spectral indices
│   │   ├── fusion.py # Data fusion
│   │   └── validation.py # Data validation
│   └── data_manager.py # Data management
│
├── models/          # AI Models
│   ├── base_model.py # Base model implementation
│   ├── load_model.py # Model loader
│   ├── api_connector.py # API connectors
│   ├── streaming.py # Streaming responses
│   ├── caching.py # Response caching
│   ├── function_calling.py # Function calling
│   └── multi_model.py # Multi-model inference
│
└── deployments/     # Deployment options
    ├── standalone/ # Standalone deployment
    ├── consensus/ # Consensus deployment
    └── swarmed/ # Swarmed deployment
```

## 🧩 Core Components

### 1. 📡 Data Acquisition
Handles multi-modal data ingestion from various sources including satellite imagery, vector data, and environmental metrics.

### 2. 🧠 Memory Management
Provides tiered memory storage with hot, warm, and cold tiers for efficient data access and storage optimization.

### 3. 🤖 Model Integration
Supports multiple model providers with both local deployment and API-based access options.

### 4. 🚀 Deployment
Offers flexible deployment options including standalone, consensus-based, and swarmed architectures.

## 📚 Documentation

For more detailed information, check out our documentation:

- [Quick Start Guide](https://memories-dev.readthedocs.io/quickstart.html)
- [User Guide](https://memories-dev.readthedocs.io/user_guide/index.html)
- [API Reference](https://memories-dev.readthedocs.io/api_reference/index.html)
- [Examples](https://memories-dev.readthedocs.io/user_guide/examples.html)
- [Development Guide](https://memories-dev.readthedocs.io/development/index.html)

<p align="center">Built with 💜 by the memories-dev team</p>
