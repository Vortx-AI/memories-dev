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

## 🚀 Key Features

- **Tiered Memory Management**:
  - Hot Memory: Fast access to frequently used data
  - Warm Memory: Balanced storage for semi-active data
  - Cold Memory: Efficient storage for historical data

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

## 🏗️ Quick Start

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

## 💻 Basic Usage

```python
from memories import MemoryStore, Config
from memories.earth import OvertureClient, SentinelClient
import os

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

## 🧩 System Architecture

The system is built on three core components:

1. **Data Acquisition**: Collects and processes data from various sources
2. **Model System**: Manages model loading, inference, and API connections
3. **Deployment**: Handles deployment configurations and resource management

<div align="center">
  <img src="https://raw.githubusercontent.com/Vortx-AI/memories-dev/main/docs/source/_static/architecture.png" alt="memories-dev Architecture" width="700px">
</div>

## 📊 Example Applications

Check out our [examples directory](examples/) for complete applications:

- **Real Estate Agent**: AI-powered property analysis
- **Property Analyzer**: Environmental assessment
- **Water Body Agent**: Water resource monitoring
- **Food Analyzer**: Nutrition analysis
- **Traffic Analyzer**: Pattern recognition
- **Autonomous Vehicle Memory**: Car memory system

## 📚 Documentation

- [Getting Started Guide](docs/getting_started.md)
- [API Reference](docs/api_reference.md)
- [Example Applications](examples/README.md)
- [Earth Memory Integration](docs/earth_memory.md)
- [Advanced Features](docs/advanced_features.md)

## ⚙️ System Requirements

- Python 3.9+
- 500MB minimum RAM (2GB recommended)
- Internet connection for earth memory features
- API keys for external services

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## 📜 License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- [Issue Tracker](https://github.com/Vortx-AI/memories-dev/issues)
- [Documentation](docs/)
- [Community Forum](https://forum.memories-dev.com)
- [Discord Community](https://discord.gg/tGCVySkX4d)

## 📅 Release Timeline

- **v1.0.0** - Released on February 14, 2025: Initial stable release with core functionality
- **v2.0.2** - Scheduled for February 25, 2025: Current development version with enhanced features

<p align="center">Built with 💜 by the memories-dev team</p>

