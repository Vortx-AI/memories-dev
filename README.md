<div align="center">

# memories.dev


**Collective Memory for AGI**

[![Documentation](https://img.shields.io/badge/docs-latest-brightgreen.svg)](https://docs.memories.dev)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Version](https://img.shields.io/badge/version-1.1.8-blue.svg)](https://github.com/Vortx-AI/memories-dev/releases/tag/v1.1.8)

<a href="https://www.producthunt.com/posts/memories-dev?embed=true&utm_source=badge-featured&utm_medium=badge&utm_souce=badge-memories&#0045;dev" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/featured.svg?post_id=879661&theme=light&t=1739530783374" alt="memories&#0046;dev - Collective&#0032;AGI&#0032;Memory | Product Hunt" style="width: 250px; height: 54px;" width="250" height="54" /></a>

</div>

## Overview

memories.dev is a memory infrastructure for providing real-world context to AI models during inference. It processes, indexes, and serves location-tagged intelligence ("memories") from multiple data sources including satellite imagery, climate sensors, and urban development metrics. These memories enhance AI models' understanding and reasoning capabilities with real-world context.



## System Architecture

## Quick Start

```python
from memories.models.load_model import LoadModel
from memories.core.memory import MemoryStore
from memories.agents.agent import Agent


# Initialize with advanced models
load_model = LoadModel(
    use_gpu= True 
    model_provider= "deepseek-ai" #"deepseek" or "openai"
    deployment_type= "local" #"local" or "api"
    model_name= "deepseek-r1-zero" #"deepseek-r1-zero" or "gpt-4o" or "deepseek-coder-3.1b-base" or "gpt-4o-mini"
    #api_key= #"your-api-key" optional for api deployment
)

# Create Earth memories
memory_store = MemoryStore()

memories = memory_store.create_memories(
    model = load_model,
    location=(37.7749, -122.4194),  # San Francisco coordinates
    time_range=("2024-01-01", "2024-02-01"),
    artifacts={
        "satellite": ["sentinel-2", "landsat8"],
        "landuse": ["osm","overture"]
    }
)


# Generate synthetic data
synthetic_data = vx.generate_synthetic(
    base_location=(37.7749, -122.4194),
    scenario="urban_development",
    time_steps=10,
    climate_factors=True
)

# AGI reasoning with memories
insights = Agent(
    query="Analyze urban development patterns and environmental impact",
    context_memories=memories,
    synthetic_scenarios=synthetic_data
)
```

## Installation

### Basic Installation

```bash
pip install memories-dev
```

### Python Version Compatibility

The package supports Python versions 3.9 through 3.13. Dependencies are automatically adjusted based on your Python version to ensure compatibility.

### Installation Options

#### 1. CPU-only Installation (Default)
```bash
pip install memories-dev
```

#### 2. GPU Support Installation
For CUDA 11.8:
```bash
pip install memories-dev[gpu]
```

For different CUDA versions, install PyTorch manually first:
```bash
# For CUDA 12.1
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Then install the package
pip install memories-dev[gpu]
```

#### 3. Development Installation
For contributing to the project:
```bash
pip install memories-dev[dev]
```

#### 4. Documentation Tools
For building documentation:
```bash
pip install memories-dev[docs]
```

### Version-specific Dependencies

The package automatically handles version-specific dependencies based on your Python version:

- Python 3.9: Compatible with older versions of key packages
- Python 3.10-3.11: Standard modern package versions
- Python 3.12-3.13: Latest package versions with improved performance

### Common Issues and Solutions

1. **Shapely Version Conflicts**
   - For Python <3.13: Uses Shapely 1.7.0-1.8.5
   - For Python ≥3.13: Uses Shapely 2.0+

2. **GPU Dependencies**
   - CUDA toolkit must be installed separately
   - PyTorch Geometric packages are installed from wheels matching your CUDA version

3. **Package Conflicts**
   If you encounter dependency conflicts:
   ```bash
   pip install --upgrade pip
   pip install memories-dev --no-deps
   pip install -r requirements.txt
   ```

### Development Setup

1. Clone the repository:
```bash
git clone https://github.com/Vortx-AI/memories-dev.git
cd memories-dev
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows
```

3. Install development dependencies:
```bash
pip install -e .[dev]
```

4. Install pre-commit hooks:
```bash
pre-commit install
```

## Usage

See our [documentation](https://docs.memories.dev) for detailed usage instructions and examples.

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## Support

- Documentation: https://docs.memories.dev
- Issues: https://github.com/Vortx-AI/memories-dev/issues
- Discussions: https://github.com/Vortx-AI/memories-dev/discussions

---

<div align="center">
<p>Empowering AI with Real-World Context</p>
</div>

