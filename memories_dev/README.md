# 🧠 memories.dev


> Collective AGI memory - v1.0.0

## 🌟 Overview

memories.dev is a groundbreaking framework for building and managing collective AGI memory systems. It provides a robust architecture for memory formation, retrieval, and synthesis across multiple modalities, enabling AI models to maintain and utilize contextual understanding across interactions.

### 🎯 Key Goals
- Enable persistent memory for AI systems
- Provide context-aware intelligence
- Support multi-modal memory integration
- Ensure scalable and efficient memory operations
- Maintain privacy and security in memory access

## 🚀 Quick Start

```python
from memories_dev import MemorySystem
from memories_dev.agents import Agent
from memories_dev.models import ModelRegistry

# Initialize the memory system
memory_system = MemorySystem(
    store_type="vector",  # Options: "vector", "graph", "hybrid"
    vector_store="milvus",  # Coming in v1.1: Support for multiple vector stores
    embedding_model="text-embedding-3-small"
)

# Create an agent with memory access
agent = Agent(
    memory_system=memory_system,
    model_name="gpt-4",  # Default model for reasoning
    capabilities=["analysis", "synthesis"]
)

# Store a memory
memory_id = memory_system.store(
    content="The city's air quality improved by 15% after implementing new policies.",
    metadata={
        "location": {"lat": 37.7749, "lon": -122.4194},
        "timestamp": "2024-03-15T10:30:00Z",
        "source": "environmental_sensor"
    }
)

# Query memories with context
relevant_memories = memory_system.query(
    query="What were the environmental changes in San Francisco?",
    location_radius_km=10,
    time_range=("2024-01-01", "2024-03-15")
)

# Agent reasoning with memory context
analysis = agent.analyze(
    query="Evaluate the impact of environmental policies",
    context_memories=relevant_memories
)
```

## 🏗️ Installation

### Current Release (v1.0.0)
```bash
# Basic installation
pip install git+https://github.com/Vortx-AI/memories-dev.git

# Development installation
git clone https://github.com/Vortx-AI/memories-dev.git
cd memories-dev
pip install -e ".[dev]"
```

### Coming in v1.1.0
```bash
# Installation with all features
pip install memories-dev[all]

# GPU-optimized installation
pip install memories-dev[gpu]
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

### Available Now (v1.0.0)
- Basic logging system with structured output
- Memory operation metrics
- Performance tracking for core operations
- Health check endpoints

### Coming in v1.1.0
- 📈 Grafana dashboards for memory metrics
- 🔍 Prometheus integration
- 🔄 Real-time memory operation monitoring
- 📊 Advanced performance analytics
- 🚨 Automated alerting system

## 🧪 Development Features

### Available Now
- Memory store implementations
- Basic agent system
- Core memory operations
- Unit test framework
- Development environment setup

### Coming Soon (v1.1.0)
- Enhanced memory compression
- Advanced caching system
- Distributed memory operations
- Memory garbage collection
- Advanced security features

## 🏗️ Architecture

Our system is built with modularity and scalability in mind, organized into key components that work together seamlessly:

```
src/
├── 🤖 agents/               # Intelligent Agent System
├── 📡 data_acquisition/    # Multi-source Data Collection
├── 🧠 memories/           # Core Memory System
├── 🔮 models/             # AI & ML Models
├── 🔄 synthesis/          # Memory Synthesis
└── 🛠️ utils/              # Utilities & Tools
```

### Core Components

#### 🤖 Agents
The brain of our system, handling intelligent operations:
```
agents/
├── core/              # Foundation of agent operations
│   ├── base.py       # Base agent architecture
│   └── registry.py   # Agent management system
├── memory/           # Memory interaction layer
│   ├── context.py    # Context handling
│   └── retrieval.py  # Memory access patterns
└── specialized/      # Purpose-built agents
    ├── analysis.py   # Analytical capabilities
    └── synthesis.py  # Memory synthesis
```

#### 📡 Data Acquisition
Multi-modal data ingestion system:
```
data_acquisition/
├── satellite/        # Earth observation data
├── sensors/         # IoT & sensor networks
└── streams/         # Real-time data handling
```

#### 🧠 Memories
The heart of our memory system:
```
memories/
├── store/           # Memory storage systems
│   ├── vector.py    # Vector embeddings store
│   └── index.py     # Advanced indexing
├── formation/       # Memory creation engine
└── query/           # Memory retrieval system
```

#### 🔮 Models
AI/ML powerhouse:
```
models/
├── embedding/       # Multi-modal embeddings
├── reasoning/       # Logic & inference
└── fusion/         # Cross-modal integration
```

#### 🔄 Synthesis
Memory enhancement and generation:
```
synthesis/
├── fusion/         # Advanced data fusion
└── generation/     # Synthetic memory creation
```

## 🎯 Features (v1.0.0)

### Core Capabilities
- 🔄 Real-time memory formation and updates
- 🔍 Advanced spatial and temporal querying
- 🤝 Multi-agent collaboration
- 🎯 Context-aware memory retrieval
- 🔗 Cross-modal memory linking

### Technical Features
- ⚡ High-performance vector storage
- 🔐 Secure memory management
- 📊 Advanced data fusion algorithms
- 🎨 Multi-modal data support
- 🔄 Real-time stream processing

## 🚀 Roadmap

### Coming in v1.1.0
- Enhanced memory compression
- Improved cross-modal reasoning
- Advanced context understanding

### Future Horizons
- Distributed memory networks
- Quantum-inspired memory storage
- Advanced consciousness simulation

## 🛠️ Development

### Prerequisites
- Python 3.8+
- CUDA-compatible GPU (recommended)
- Vector store backend (Redis/Milvus/Pinecone)
- Docker & Docker Compose
- Make (optional, for using Makefile commands)

### Environment Setup

1. **Clone and Setup**
```bash
# Clone the repository
git clone https://github.com/yourusername/memories.dev.git
cd memories.dev

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies
```

2. **Environment Variables**
```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configurations
nano .env
```

3. **Development Database**
```bash
# Start development services
docker-compose up -d
```

### Development Workflow

#### 1. Code Style
We use `black` for code formatting and `flake8` for linting:
```bash
# Format code
make format

# Run linting
make lint
```

#### 2. Testing
```bash
# Run all tests
make test

# Run specific test file
pytest tests/test_memories/test_store.py

# Run with coverage
make coverage
```

#### 3. Pre-commit Hooks
```bash
# Install pre-commit hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

### 🐳 Docker Development

```bash
# Build development image
docker build -t memories-dev -f docker/Dockerfile.dev .

# Run development container
docker run -it --gpus all -v $(pwd):/app memories-dev
```

### 📊 Monitoring & Debugging

1. **Logging**
```python
# In your code
from memories.utils.logging import get_logger

logger = get_logger(__name__)
logger.info("Memory operation completed")
```

2. **Performance Monitoring**
- Access metrics dashboard: `http://localhost:8080/metrics`
- Prometheus integration available
- Grafana dashboards in `./monitoring`

### 🔄 Common Workflows

#### Adding a New Feature
1. Create feature branch: `git checkout -b feature/your-feature`
2. Implement changes
3. Add tests in `tests/`
4. Update documentation
5. Run test suite: `make test`
6. Create pull request

#### Updating Dependencies
1. Update `requirements.in` or `requirements-dev.in`
2. Compile requirements: `make requirements`
3. Test changes: `make test`
4. Commit changes

## 🚀 CI/CD Pipeline

```mermaid
graph LR
    A[Push] --> B[Lint]
    B --> C[Test]
    C --> D[Build]
    D --> E[Deploy]
```

### Automated Checks
- Code formatting (black)
- Type checking (mypy)
- Unit tests (pytest)
- Integration tests
- Security scanning
- Performance benchmarks

### Deployment Environments
- **Dev**: Automatic deployment on main branch
- **Staging**: Manual trigger from release branches
- **Production**: Tagged releases only

## 📚 Documentation

### Building Docs Locally
```bash
# Install documentation dependencies
pip install -r docs/requirements.txt

# Build documentation
cd docs
make html

# Serve documentation
python -m http.server -d _build/html
```

### API Documentation
- [API Reference](docs/api.md)
- [Architecture Guide](docs/architecture.md)
- [Development Guide](docs/development.md)
- [Deployment Guide](docs/deployment.md)
- [Contributing Guide](CONTRIBUTING.md)

### Example Notebooks
Find example notebooks in `notebooks/`:
- 🔰 Quick Start
- 🧠 Memory Operations
- 🤖 Agent Integration
- 📊 Data Visualization

## 🎓 Developer Resources

### Tutorials & Guides
- [Getting Started Guide](docs/getting_started.md)
- [Memory System Architecture](docs/architecture.md)
- [Agent Development Guide](docs/agents.md)
- [Custom Memory Store Integration](docs/custom_stores.md)

### Example Use Cases
1. **Persistent Context in Conversations**
   ```python
   # Example of maintaining context across conversations
   conversation = memory_system.create_conversation()
   conversation.add_memory("User preference: Dark mode")
   conversation.add_memory("Language: Python")
   
   # Later in the conversation
   context = conversation.get_relevant_context("IDE settings")
   ```

2. **Spatial Memory Analysis**
   ```python
   # Analyzing patterns in spatial memories
   spatial_analysis = memory_system.analyze_spatial(
       location=(37.7749, -122.4194),
       radius_km=5,
       time_range=("2024-01-01", "2024-03-15"),
       analysis_type="pattern_recognition"
   )
   ```

### Best Practices
- Always use context managers for memory operations
- Implement proper error handling
- Use batch operations for multiple memories
- Regularly clean up unused memories
- Monitor memory usage and performance

## 🤝 Community & Support

- [Discord Community](https://discord.gg/memoriesdev)
- [GitHub Discussions](https://github.com/Vortx-AI/memories-dev/discussions)
- [Documentation](https://memoriesdev.readthedocs.io/)
- [Blog](https://memoriesdev.medium.com)

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Getting Started
1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

### Code Review Process
1. Automated checks must pass
2. Requires one approved review
3. Must maintain test coverage
4. Documentation updates required

## 📜 Version History

### v1.0.0 (Current)
- Initial stable release
- Core memory system implementation
- Basic agent framework
- Multi-modal data support

### v0.9.0 (Beta)
- Feature-complete beta release
- Performance optimizations
- API stabilization



<p align="center">Built with 💜 by the memories.dev team</p>

<p align="center">
<a href="https://discord.com/invite/7qAFEekp">Discord</a> •
</p>
