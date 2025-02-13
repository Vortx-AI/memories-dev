<div align="center">

# memories.dev

**Contextual Memory Infrastructure for AI Systems**

[![Documentation](https://img.shields.io/badge/docs-latest-brightgreen.svg)](https://docs.memories.dev)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

</div>

## Overview

memories.dev is a high-performance infrastructure for providing real-world context to AI models during inference. It processes, indexes, and serves location-tagged intelligence ("memories") from multiple data sources including satellite imagery, climate sensors, and urban development metrics. These memories enhance AI models' understanding and reasoning capabilities with real-world context.

## Core Features

### Memory Sources
- Global Points of Interest Database
- Global Places Database
- Cadastral Data & Digital Elevation Models
- Census & Demographics
- Satellite Data:
  - ESA Sentinel-1 & 2
  - NASA Landsat 7/8
  - Custom data source integration

### Key Capabilities
- Real-time memory retrieval during model inference
- Context-aware AI reasoning
- Multi-modal memory fusion
- Temporal pattern analysis
- Location-aware intelligence
- Privacy-preserving memory access

## System Architecture

### Core Components

```mermaid
graph TD
    %% Styles
    classDef source fill:#e1f5fe,stroke:#01579b,stroke-width:2px;
    classDef memory fill:#f3e5f5,stroke:#4a148c,stroke-width:2px;
    classDef agent fill:#fff3e0,stroke:#e65100,stroke-width:2px;
    classDef output fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px;

    %% Data Sources
    subgraph Sources
        S1[Satellite Networks]
        S2[Climate Sensors]
        S3[Urban Systems]
    end

    %% Memory System
    subgraph Memory
        M1[Ingestion]
        M2[Processing]
        M3[Storage]
        M4[Retrieval]
    end

    %% Agent System
    subgraph Agents
        A1[Reasoning]
        A2[Synthesis]
        A3[Analysis]
    end

    %% Output System
    subgraph Output
        O1[Reports]
        O2[Analytics]
        O3[API]
    end

    %% Flow
    S1 & S2 & S3 --> M1
    M1 --> M2 --> M3 --> M4
    M4 --> A1 --> A2 --> A3
    A3 --> O1 & O2 & O3

    %% Apply styles
    class S1,S2,S3 source;
    class M1,M2,M3,M4 memory;
    class A1,A2,A3 agent;
    class O1,O2,O3 output;
```

### Memory Architecture

```mermaid
graph TD
    %% Styles
    classDef store fill:#e1f5fe,stroke:#01579b,stroke-width:2px;
    classDef cache fill:#f3e5f5,stroke:#4a148c,stroke-width:2px;
    classDef index fill:#fff3e0,stroke:#e65100,stroke-width:2px;

    %% Memory Store
    subgraph Store[Memory Store]
        V[Vector Store]
        T[Time Series DB]
        S[Spatial Index]
    end

    %% Cache System
    subgraph Cache[Cache Layers]
        L1[L1 Cache - Memory]
        L2[L2 Cache - SSD]
        L3[L3 Cache - Distributed]
    end

    %% Index System
    subgraph Index[Index Types]
        I1[Spatial Index]
        I2[Temporal Index]
        I3[Semantic Index]
    end

    %% Flow
    V & T & S --> L1
    L1 --> L2 --> L3
    L3 --> I1 & I2 & I3

    %% Styles
    class V,T,S store;
    class L1,L2,L3 cache;
    class I1,I2,I3 index;
```

### Data Flow

```mermaid
graph LR
    %% Styles
    classDef input fill:#e1f5fe,stroke:#01579b,stroke-width:2px;
    classDef process fill:#f3e5f5,stroke:#4a148c,stroke-width:2px;
    classDef output fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px;

    %% Pipeline
    I[Raw Data] --> P1[Preprocessing]
    P1 --> P2[Feature Extraction]
    P2 --> P3[Memory Formation]
    P3 --> P4[Memory Storage]
    P4 --> P5[Memory Retrieval]
    P5 --> O[AI Integration]

    %% Styles
    class I input;
    class P1,P2,P3,P4,P5 process;
    class O output;
```

## Quick Start

```python
from memories-dev.vortx import memories-dev
from memories-dev.memories.earth_memory import EarthMemoryStore
from memories-dev.agents.agent import Agent


# Initialize with advanced models
vx = Vortx(
    models={
        "reasoning": deepseek-coder-small,
        "vision": deepseek-vision-small
    },
    use_gpu=True
)

# Create Earth memories
memory_store = EarthMemoryStore()
memories = memory_store.create_memories(
    location=(37.7749, -122.4194),
    time_range=("2020-01-01", "2024-01-01"),
    modalities=["satellite", "climate", "social"]
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

```bash
# Basic installation (Coming Soon)
pip install memories-dev

# With GPU support (Coming Soon)
pip install memories-dev[gpu]
```

## System Requirements

### Minimum
- Python 3.9+
- 16GB RAM
- 4+ CPU cores
- 20GB storage

### Recommended
- 32GB RAM
- 8+ CPU cores
- NVIDIA GPU (8GB+ VRAM)
- 50GB SSD storage

## Use Cases

- **Enhanced Language Models**: Provide real-world context during inference
- **Report Generation**: Create detailed reports with location-specific insights
- **Trend Analysis**: Analyze temporal patterns with historical context
- **Impact Assessment**: Evaluate environmental and urban development impacts
- **Decision Support**: Aid decision-making with contextual intelligence


## Contributing

We welcome contributions! See our [Contributing Guide](CONTRIBUTING.md) for:
- Development Setup
- Code Style Guidelines
- Testing Requirements
- PR Process

## Support

- [GitHub Issues](https://github.com/memories-dev/memories.dev/issues)
- [Discord Community](https://discord.gg/7qAFEekp)
- Email: hello@memories.dev

## License

Apache License 2.0 - See [LICENSE](LICENSE) for details.

---

<div align="center">
<p>Empowering AI with Real-World Context</p>
</div>
