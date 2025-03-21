# 🌍 memories-dev

<div align="center">

**Test-Time Memory Framework: Eliminate Hallucinations in Foundation Models**

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Python Versions](https://img.shields.io/pypi/pyversions/memories-dev.svg)](https://pypi.org/project/memories-dev/)
[![PyPI Download](https://img.shields.io/pypi/dm/memories-dev.svg)](https://pypi.org/project/memories-dev/)
[![Version](https://img.shields.io/badge/version-2.0.7-blue.svg)](https://github.com/Vortx-AI/memories-dev/releases/tag/v2.0.7)
[![Discord](https://img.shields.io/discord/1339432819784683522?color=7289da&label=Discord&logo=discord&logoColor=white)](https://discord.gg/tGCVySkX4d)

<a href="https://www.producthunt.com/posts/memories-dev?embed=true&utm_source=badge-featured&utm_medium=badge&utm_souce=badge-memories&#0045;dev" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/featured.svg?post_id=879661&theme=light&t=1739530783374" alt="memories&#0046;dev - Collective&#0032;AGI&#0032;Memory | Product Hunt" style="width: 250px; height: 54px;" width="250" height="54" /></a>

</div>

<div align="center">
  <h3>Real-time Contextual Memory Integration for Mission-Critical AI Applications</h3>
  <p><i>Deployment-ready • Space-hardened • 99.9% Reliability</i></p>
</div>

<hr>

<div align="center">
  <img src="https://github.com/Vortx-AI/memories-dev/raw/main/docs/source/_static/architecture_overview.gif" alt="memories-dev Architecture" width="700px">
</div>

## 📊 Overview

**memories-dev** provides a robust framework for eliminating hallucinations in foundation models through real-time contextual memory integration. Built for developers requiring absolute reliability, our system ensures AI outputs are verified against factual context before delivery to your applications.

Key benefits include:
- **Factual Grounding**: Verify AI responses against contextual truth data in real-time
- **Minimal Latency**: Framework adds less than 100ms overhead to inference
- **Deployment Flexibility**: Horizontal scaling for high-throughput applications
- **Comprehensive Verification**: Multi-stage validation ensures response accuracy

These capabilities are achieved through our memory verification framework that integrates seamlessly with any AI model, providing reliable operation even in challenging environments.

## 📝 Table of Contents

- [Memory Verification Framework](#-memory-verification-framework)
- [Installation](#-installation)
- [Common Issues and Solutions](#-common-issues-and-solutions)
- [Development Setup](#-development-setup)
- [Core Architecture](#-core-architecture)
- [Advanced Applications](#-advanced-applications)
- [Deployment Patterns](#-deployment-patterns)
- [Developer-Centric Reliability](#-developer-centric-reliability)
- [Technical Principles](#-technical-principles)
- [Usage Examples](#-usage-examples)
- [Contributing](#-contributing)
- [License](#-license)

## 🔬 Memory Verification Framework

Our three-stage verification framework ensures reliable AI outputs:

### Stage 1: Input Validation (EARTH)
Prevents corrupted or invalid data from entering the memory system using advanced validation rules and structured verification protocols.

### Stage 2: Truth Verification (S-2)
Cross-validates information using multiple sources to establish reliable ground truth. Implements consistency checks and verification algorithms for data quality.

### Stage 3: Response Validation (S-3)
Real-time verification of outputs against verified truth database. Applies confidence scoring to ensure response accuracy and validity.

Each stage works together to create a reliable memory system:

```mermaid
%%{init: { 'theme': 'default', 'themeVariables': { 'primaryColor': '#4C78B5', 'primaryTextColor': '#fff', 'primaryBorderColor': '#3A5D8C', 'lineColor': '#3A5D8C', 'secondaryColor': '#41B883', 'tertiaryColor': '#F7A922' } }}%%
graph TD
    classDef inputStage fill:#3b82f6,stroke:#2563eb,stroke-width:2px,color:white,font-weight:bold,rounded:true
    classDef truthStage fill:#ef4444,stroke:#dc2626,stroke-width:2px,color:white,font-weight:bold,rounded:true
    classDef responseStage fill:#10b981,stroke:#059669,stroke-width:2px,color:white,font-weight:bold,rounded:true
    classDef dataFlow fill:#8b5cf6,stroke:#7c3aed,stroke-width:2px,color:white,font-weight:bold,rounded:true
    
    A[Input Data] -->|"Feed"| B[Stage 1: Input Validation]
    B -->|"Process"| C[Validated Input]
    C -->|"Verify"| D[Stage 2: Truth Verification]
    D -->|"Confirm"| E[Verified Truth]
    E -->|"Validate"| F[Stage 3: Response Validation]
    F -->|"Deliver"| G[Verified Response]
    
    B:::inputStage
    D:::truthStage
    F:::responseStage
    A:::dataFlow
    C:::dataFlow
    E:::dataFlow
    G:::dataFlow

    linkStyle default stroke-width:2px,fill:none,stroke:#3A5D8C,curve:basis
```

## 📦 Installation

Choose the installation option that best fits your needs:

### 1. CPU-only Installation (Default)
```bash
pip install memories-dev
```

### 2. GPU Support Installation
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

### 3. Development Installation
For contributing to the project:
```bash
pip install memories-dev[dev]
```

### 4. Documentation Tools
For building documentation:
```bash
pip install memories-dev[docs]
```

### 5. Alternative Installation via Conda
```bash
conda install -c memories-dev
```

## 🔧 Common Issues and Solutions

### Shapely Version Conflicts
- For Python <3.13: Uses Shapely 1.7.0-1.8.5
- For Python ≥3.13: Uses Shapely 2.0+

### GPU Dependencies
- CUDA toolkit must be installed separately
- PyTorch Geometric packages are installed from wheels matching your CUDA version

### Package Conflicts
If you encounter dependency conflicts:
```bash
pip install --upgrade pip
pip install memories-dev --no-deps
pip install -r requirements.txt
```

### Missing Dependencies
For some specialized features, you may need to install:
```bash
# For spatial data processing
pip install geopandas rtree pyproj

# For advanced visualization
pip install matplotlib seaborn plotly
```

### Memory Configuration Issues
If encountering memory-related errors:
```python
from memories import Config

# Adjust memory tiers based on your hardware
config = Config(
    hot_memory_size=4,  # GB
    warm_memory_size=16,  # GB
    cold_memory_size=64,  # GB
    vector_store="faiss"  # Alternatives: milvus, qdrant, pgvector
)
```

## 🛠️ Development Setup

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

5. Run tests:
```bash
pytest tests/
```

6. Build documentation:
```bash
cd docs
make html
```

## 🏗️ Core Architecture

The Test-Time Memory Framework integrates with your AI systems through a simple, effective process:

1. AI model generates initial response
2. Memory framework retrieves contextual data
3. Response is verified against contextual information
4. Verified response delivered to application

```mermaid
%%{init: { 'theme': 'default', 'themeVariables': { 'primaryColor': '#1F3A60', 'primaryTextColor': '#fff', 'primaryBorderColor': '#0F2A4C', 'lineColor': '#0F2A4C', 'secondaryColor': '#41B883', 'tertiaryColor': '#F7A922' } }}%%
sequenceDiagram
    participant App as Application
    participant AI as AI Model
    participant MF as Memory Framework
    participant CD as Contextual Data
    
    rect rgba(64, 78, 103, 0.1)
    note right of App: Request Phase
    App->>+AI: Request response
    AI->>AI: Generate initial response
    end
    
    rect rgba(43, 155, 128, 0.1)
    note right of AI: Verification Phase
    AI->>+MF: Send for verification
    MF->>+CD: Retrieve contextual data
    CD-->>-MF: Return relevant context
    MF->>MF: Verify response against context
    MF-->>-AI: Return verified response
    end
    
    rect rgba(170, 110, 40, 0.1)
    note right of AI: Delivery Phase
    AI-->>-App: Deliver validated response
    end
    
    note over App,CD: Complete Verification Cycle
```

### Memory System Architecture

Our multi-tiered memory system ensures optimal performance and reliability:

```mermaid
%%{init: { 'theme': 'default', 'themeVariables': { 'primaryColor': '#2c3e50', 'primaryTextColor': '#ecf0f1', 'primaryBorderColor': '#34495e', 'lineColor': '#3498db', 'secondaryColor': '#2980b9', 'tertiaryColor': '#1abc9c' } }}%%
graph TB
    classDef primary fill:#2c3e50,stroke:#34495e,stroke-width:2px,color:white,font-weight:bold,rounded:true
    classDef secondary fill:#3498db,stroke:#2980b9,stroke-width:2px,color:white,rounded:true
    classDef tertiary fill:#1abc9c,stroke:#16a085,stroke-width:2px,color:white,rounded:true
    
    A[Client Application]:::primary -->|"Requests"| B[Memory Manager]:::primary
    B -->|"Collects"| C[Data Acquisition]:::secondary
    B -->|"Stores"| D[Memory Store]:::secondary
    B -->|"Analyzes"| E[Earth Analyzers]:::secondary
    B -->|"Integrates"| F[AI Integration]:::secondary
    
    C -->|"Satellite"| C1[Satellite Data]:::tertiary
    C -->|"Vector"| C2[Vector Data]:::tertiary
    C -->|"IoT"| C3[Sensor Data]:::tertiary
    C -->|"External"| C4[Environmental APIs]:::tertiary
    
    D -->|"Fast Access"| D1[Hot Memory]:::tertiary
    D -->|"Regular Access"| D2[Warm Memory]:::tertiary
    D -->|"Infrequent Access"| D3[Cold Memory]:::tertiary
    D -->|"Archival"| D4[Glacier Storage]:::tertiary
    
    E -->|"Elevation"| E1[Terrain Analysis]:::tertiary
    E -->|"Weather"| E2[Climate Analysis]:::tertiary
    E -->|"Impact"| E3[Environmental Impact]:::tertiary
    E -->|"Development"| E4[Urban Development]:::tertiary
    
    F -->|"LLM"| F1[Model Connectors]:::tertiary
    F -->|"Context"| F2[Context Formation]:::tertiary
    F -->|"Prompts"| F3[Prompt Engineering]:::tertiary
    F -->|"Validation"| F4[Response Validation]:::tertiary
    
    linkStyle default stroke-width:2px,fill:none,stroke:#3498db,curve:basis
```

### Data Processing Workflow

Our comprehensive data flow architecture transforms raw observation data into actionable intelligence:

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': { 'primaryColor': '#0f172a', 'primaryTextColor': '#f8fafc', 'primaryBorderColor': '#334155', 'lineColor': '#3b82f6', 'secondaryColor': '#10b981', 'tertiaryColor': '#8b5cf6'}}}%%
graph LR
    classDef ingestion fill:#1d4ed8,stroke:#1e40af,stroke-width:2px,color:white,font-weight:bold,rounded:true
    classDef processing fill:#b91c1c,stroke:#991b1b,stroke-width:2px,color:white,font-weight:bold,rounded:true
    classDef storage fill:#047857,stroke:#065f46,stroke-width:2px,color:white,font-weight:bold,rounded:true
    classDef analytics fill:#7c3aed,stroke:#6d28d9,stroke-width:2px,color:white,font-weight:bold,rounded:true
    classDef delivery fill:#9a3412,stroke:#9a3412,stroke-width:2px,color:white,font-weight:bold,rounded:true
    
    %% Data Ingestion Nodes
    A1[Satellite Imagery] -.->|"Raw Data"| A
    A2[Vector Databases] -.->|"Spatial"| A
    A3[Sensor Networks] -.->|"IoT"| A
    A4[Environmental APIs] -.->|"External"| A
    A[Data Ingestion Engine] ==>|"Input"| B
    
    %% Data Processing Nodes
    B ==>|"Process"| B1[Data Cleaning]
    B ==>|"Extract"| B2[Feature Extraction]
    B ==>|"Time Align"| B3[Temporal Alignment]
    B ==>|"Geo Register"| B4[Spatial Registration]
    B[Multi-Modal Processing] ==>|"Transform"| C
    
    %% Storage Nodes
    C ==>|"Immediate"| C1[Hot Memory Cache]
    C ==>|"Regular"| C2[Warm Vector Store]
    C ==>|"Archive"| C3[Cold Object Storage]
    C ==>|"Deep Archive"| C4[Glacier Archive]
    C[Adaptive Memory System] ==>|"Store"| D
    
    %% Analytics Nodes
    D ==>|"Spatial"| D1[Geospatial Analytics]
    D ==>|"Temporal"| D2[Time Series Analytics]
    D ==>|"Evolution"| D3[Change Detection]
    D ==>|"Patterns"| D4[Correlation Engine]
    D[Earth Intelligence Suite] ==>|"Analyze"| E
    
    %% Delivery Nodes
    E ==>|"Models"| E1[AI Model Integration]
    E ==>|"Services"| E2[Application APIs]
    E ==>|"Visual"| E3[Visualization Tools]
    E ==>|"Export"| E4[Export Services]
    E[Insight Delivery] ==>|"Decide"| F
    
    F[Decision Intelligence]
    
    %% Classifications
    A1:::ingestion
    A2:::ingestion
    A3:::ingestion
    A4:::ingestion
    A:::ingestion
    
    B1:::processing
    B2:::processing
    B3:::processing
    B4:::processing
    B:::processing
    
    C1:::storage
    C2:::storage
    C3:::storage
    C4:::storage
    C:::storage
    
    D1:::analytics
    D2:::analytics
    D3:::analytics
    D4:::analytics
    D:::analytics
    
    E1:::delivery
    E2:::delivery
    E3:::delivery
    E4:::delivery
    E:::delivery
    
    F:::delivery
    
    linkStyle 0,1,2,3 stroke:#1d4ed8,stroke-width:1.5px,stroke-dasharray:3,curve:basis;
    linkStyle 4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24 stroke-width:3px,fill:none,curve:basis;
```

## 🚀 Advanced Applications

Our satellite-verified memory system powers a wide range of cutting-edge AI applications where factual grounding and reliability are mission-critical:

### Space-Based Applications

#### Upstream Ground Systems
Enhance pre-launch verification with AI that can validate mission parameters against physical constraints, preventing costly errors before they reach orbit.

#### In-Orbit Decision Making
Enable autonomous spacecraft to make reliable decisions during communication blackouts by maintaining factual context about their environment and mission parameters.

#### Downstream Data Processing
Process satellite telemetry and science data with context-aware AI that can detect anomalies, classify observations, and prioritize findings without hallucinations.

### Robotics & Physical AI

#### Autonomous Systems
Ground exploration robots maintain accurate terrain understanding and mission objectives even with delayed or limited communication with control systems.

#### Industrial Automation
Enable robotic construction and manufacturing with AI that maintains accurate spatial awareness and operation plans verified against physical constraints.

### Earth Applications

#### Healthcare
In medical diagnostics and treatment planning, our memory framework ensures AI systems provide accurate recommendations by verifying outputs against real-time patient data and established medical protocols.

#### Transportation & Logistics
For autonomous vehicles, air traffic control, and logistics management, our framework helps reduce decision errors by incorporating real-time environmental data into AI decision processes.

#### Financial Services
For algorithmic trading, fraud detection, and risk assessment, our technology helps prevent costly errors by verifying AI decisions against current market conditions and regulatory requirements.

## 🚢 Deployment Patterns

memories.dev supports three powerful deployment patterns to meet diverse operational needs:

### 1. Standalone Deployment

Optimized for single-tenant applications requiring maximum performance:

```mermaid
%%{init: { 'theme': 'default', 'themeVariables': { 'primaryColor': '#0F4C81', 'primaryTextColor': '#fff', 'primaryBorderColor': '#0D3E69', 'lineColor': '#0D3E69', 'secondaryColor': '#41B883', 'tertiaryColor': '#F7A922' } }}%%
graph TD
    subgraph Architecture["Standalone Architecture"]
        direction TB
        
        Client[Client Applications] -->|"Requests"| API[API Gateway]
        API -->|"Process"| Server[Memories Server]
        Server -->|"Inference"| Models[Model System]
        Server -->|"Data"| DataAcq[Data Acquisition]
        Models -->|"Local"| LocalModels[Local Models]
        Models -->|"External"| APIModels[API-based Models]
        DataAcq -->|"Vector"| VectorData[Vector Data Sources]
        DataAcq -->|"Earth"| SatelliteData[Satellite Data]
        Server -->|"Persist"| Storage[Persistent Storage]
    end
    
    classDef client fill:#4C78B5,stroke:#3A5D8C,color:white,font-weight:bold,rounded:true
    classDef server fill:#41B883,stroke:#2D8A64,color:white,font-weight:bold,rounded:true
    classDef model fill:#F7A922,stroke:#BF821A,color:white,rounded:true
    classDef data fill:#F06292,stroke:#C2185B,color:white,rounded:true
    classDef storage fill:#7E57C2,stroke:#5E35B1,color:white,rounded:true
    
    class Client client
    class API,Server server
    class Models,LocalModels,APIModels model
    class DataAcq,VectorData,SatelliteData data
    class Storage storage
    
    linkStyle default stroke-width:2px,fill:none,curve:basis
```

Best suited for:
- High-performance computing workloads
- Machine learning model inference
- Real-time data processing
- Direct hardware access

### 2. Consensus Deployment

Perfect for distributed systems requiring strong consistency:

```mermaid
%%{init: { 'theme': 'default', 'themeVariables': { 'primaryColor': '#0F4C81', 'primaryTextColor': '#fff', 'primaryBorderColor': '#0D3E69', 'lineColor': '#0D3E69', 'secondaryColor': '#41B883', 'tertiaryColor': '#F7A922' } }}%%
graph TD
    subgraph ConsensusArch["Consensus Architecture"]
        direction TB
        
        Client[Client Applications] -->|"Load Balanced"| LB[Load Balancer]
        LB -->|"Route"| Node1[Node 1]
        LB -->|"Route"| Node2[Node 2]
        LB -->|"Route"| Node3[Node 3]
        
        subgraph "Consensus Group"
            direction LR
            Node1 <-->|"Sync"| Node2
            Node2 <-->|"Sync"| Node3
            Node3 <-->|"Sync"| Node1
        end
        
        Node1 -->|"Inference"| Models1[Model System]
        Node2 -->|"Inference"| Models2[Model System]
        Node3 -->|"Inference"| Models3[Model System]
        
        Node1 -->|"Data"| DataAcq1[Data Acquisition]
        Node2 -->|"Data"| DataAcq2[Data Acquisition]
        Node3 -->|"Data"| DataAcq3[Data Acquisition]
        
        subgraph "Shared Storage"
            Storage[Distributed Storage]
        end
        
        Node1 -->|"Write"| Storage
        Node2 -->|"Write"| Storage
        Node3 -->|"Write"| Storage
    end
    
    classDef client fill:#4C78B5,stroke:#3A5D8C,color:white,font-weight:bold,rounded:true
    classDef loadbal fill:#F7A922,stroke:#BF821A,color:white,font-weight:bold,rounded:true
    classDef node fill:#41B883,stroke:#2D8A64,color:white,font-weight:bold,rounded:true
    classDef model fill:#7E57C2,stroke:#5E35B1,color:white,rounded:true
    classDef data fill:#F06292,stroke:#C2185B,color:white,rounded:true
    classDef storage fill:#FF8A65,stroke:#E64A19,color:white,font-weight:bold,rounded:true
    
    class Client client
    class LB loadbal
    class Node1,Node2,Node3 node
    class Models1,Models2,Models3 model
    class DataAcq1,DataAcq2,DataAcq3 data
    class Storage storage
    
    linkStyle default stroke-width:2px,fill:none,curve:basis
    linkStyle 3,4,5 stroke:#41B883,stroke-width:3px,stroke-dasharray:5 5
```

Best suited for:
- Distributed databases
- Blockchain networks
- Distributed caching systems
- Mission-critical applications

### 3. Swarmed Deployment

Ideal for globally distributed applications:

```mermaid
%%{init: { 'theme': 'default', 'themeVariables': { 'primaryColor': '#0F4C81', 'primaryTextColor': '#fff', 'primaryBorderColor': '#0D3E69', 'lineColor': '#0D3E69', 'secondaryColor': '#41B883', 'tertiaryColor': '#F7A922' } }}%%
graph TD
    subgraph SwarmArch["Swarmed Architecture"]
        direction TB
        
        Client[Client Applications] -->|"Load Balanced"| LB[Load Balancer]
        LB -->|"Route"| API1[API Gateway 1]
        LB -->|"Route"| API2[API Gateway 2]
        LB -->|"Route"| API3[API Gateway 3]
        
        subgraph "Manager Nodes"
            direction LR
            Manager1[Manager 1]
            Manager2[Manager 2]
            Manager3[Manager 3]
            
            Manager1 <-->|"Orchestrate"| Manager2
            Manager2 <-->|"Orchestrate"| Manager3
            Manager3 <-->|"Orchestrate"| Manager1
        end
        
        API1 -->|"Direct"| Manager1
        API2 -->|"Direct"| Manager2
        API3 -->|"Direct"| Manager3
        
        subgraph "Worker Nodes"
            direction TB
            Worker1[Worker 1]
            Worker2[Worker 2]
            Worker3[Worker 3]
            Worker4[Worker 4]
            Worker5[Worker 5]
        end
        
        Manager1 -->|"Dispatch"| Worker1
        Manager1 -->|"Dispatch"| Worker2
        Manager2 -->|"Dispatch"| Worker3
        Manager2 -->|"Dispatch"| Worker4
        Manager3 -->|"Dispatch"| Worker5
        
        subgraph "Shared Services"
            direction LR
            Registry[Container Registry]
            Config[Configuration Store]
            Secrets[Secrets Management]
            Monitoring[Monitoring & Logging]
        end
        
        Manager1 -->|"Utilize"| Registry
        Manager1 -->|"Configure"| Config
        Manager1 -->|"Secure"| Secrets
        Manager1 -->|"Monitor"| Monitoring
    end
    
    classDef client fill:#4C78B5,stroke:#3A5D8C,color:white,font-weight:bold,rounded:true
    classDef loadbal fill:#F7A922,stroke:#BF821A,color:white,font-weight:bold,rounded:true
    classDef gateway fill:#9CCC65,stroke:#7CB342,color:white,font-weight:bold,rounded:true
    classDef manager fill:#42A5F5,stroke:#1E88E5,color:white,font-weight:bold,rounded:true
    classDef worker fill:#7E57C2,stroke:#5E35B1,color:white,rounded:true
    classDef service fill:#F06292,stroke:#EC407A,color:white,font-weight:bold,rounded:true
    
    class Client client
    class LB loadbal
    class API1,API2,API3 gateway
    class Manager1,Manager2,Manager3 manager
    class Worker1,Worker2,Worker3,Worker4,Worker5 worker
    class Registry,Config,Secrets,Monitoring service
    
    linkStyle default stroke-width:2px,fill:none,curve:basis
    linkStyle 7,8,9 stroke:#42A5F5,stroke-width:3px,stroke-dasharray:5 5
```

Best suited for:
- Edge computing applications
- Content delivery networks
- IoT device networks
- Global data distribution

### Cloud Provider Support

Each deployment pattern is supported across major cloud providers with:

| Cloud Provider | Features | Deployment Models | Hardware Support |
|----------------|----------|-------------------|-----------------|
| AWS | Auto-scaling, S3 integration, Lambda functions | All | NVIDIA GPUs, Graviton (ARM) |
| GCP | Kubernetes, TPU support, Cloud Storage | All | NVIDIA GPUs, TPUs |
| Azure | AKS, Container Apps, Blob Storage | All | NVIDIA GPUs, AMD MI |
| On-premises | Custom hardware support, airgapped operation | All | NVIDIA GPUs, AMD MI, Intel GPUs |

## 👩‍💻 Developer-Centric Reliability

Our memory framework provides a simple API that lets your AI systems cross-check responses against environmental facts and context, reducing hallucinations while maintaining the flexibility developers need.

### For ML Engineers
- Simple API integration with any LLM
- Minimal latency overhead (< 100ms typical)
- Production-ready with comprehensive logging

### For System Architects
- Horizontal scaling for high-throughput needs
- Distributed verification architecture
- On-premise or cloud deployment options

### For Safety Teams
- Comprehensive audit trails
- Real-time monitoring dashboards
- Configurable verification thresholds

## 🔧 Technical Principles

| Principle | Feature | Description |
|-----------|---------|-------------|
| **Context** | Environmental Awareness | Integration of real-time situational data into inference processes |
| **Verification** | Multi-source Validation | Cross-checking outputs against multiple reliable data sources |
| **Latency** | Minimal Processing Overhead | Optimized for fast response times in time-sensitive applications |
| **Reliability** | Fault-Tolerant Design | Resilient architecture for operation in challenging environments |

## 💻 Usage Examples

### Multi-Model Integration

```python
from memories.models.load_model import LoadModel
from memories.models.multi_model import MultiModelInference

# Initialize multiple models for ensemble analysis
models = {
    "openai": LoadModel(model_provider="openai", model_name="gpt-4"),
    "anthropic": LoadModel(model_provider="anthropic", model_name="claude-3-opus"),
    "deepseek": LoadModel(model_provider="deepseek-ai", model_name="deepseek-coder")
}

# Create multi-model inference engine
multi_model = MultiModelInference(models=models)

# Analyze property with Earth memory integration
responses = multi_model.get_responses_with_earth_memory(
    query="Analyze environmental risks for this property",
    location={"lat": 37.7749, "lon": -122.4194},
    earth_memory_analyzers=["terrain", "climate", "water"]
)

# Compare model assessments
for provider, response in responses.items():
    print(f"\n--- {provider.upper()} ASSESSMENT ---")
    print(response["analysis"])
```

### Earth Analyzers

```python
from memories.core.analyzers import TerrainAnalyzer, ClimateAnalyzer, WaterResourceAnalyzer

# Initialize analyzers
terrain = TerrainAnalyzer()
climate = ClimateAnalyzer()
water = WaterResourceAnalyzer()

# Analyze location
terrain_analysis = await terrain.analyze(
    location={"lat": 37.7749, "lon": -122.4194},
    resolution="high"
)

climate_analysis = await climate.analyze(
    location={"lat": 37.7749, "lon": -122.4194},
    time_range={"start": "2020-01-01", "end": "2023-01-01"}
)

water_analysis = await water.analyze(
    location={"lat": 37.7749, "lon": -122.4194},
    include_forecast=True
)
```

### Real Estate Analysis

```python
from memories import MemoryStore, Config
from examples.real_estate_agent import RealEstateAgent

# Initialize memory store
config = Config(
    storage_path="./real_estate_data",
    hot_memory_size=50,
    warm_memory_size=200,
    cold_memory_size=1000
)
memory_store = MemoryStore(config)

# Initialize agent with earth memory
agent = RealEstateAgent(
    memory_store,
    enable_earth_memory=True,
    analyzers=["terrain", "climate", "water", "environmental"]
)

# Add property and analyze
property_id = await agent.add_property(property_data)
analysis = await agent.analyze_property_environment(property_id)

print(f"Property added: {property_id}")
print(f"Environmental analysis: {analysis}")
```

### Environmental Monitoring

```python
from memories.analyzers import ChangeDetector
from datetime import datetime, timedelta

# Initialize change detector
detector = ChangeDetector(
    baseline_date=datetime(2020, 1, 1),
    comparison_dates=[
        datetime(2021, 1, 1),
        datetime(2022, 1, 1),
        datetime(2023, 1, 1),
        datetime(2024, 1, 1)
    ]
)

# Detect environmental changes
changes = await detector.analyze_changes(
    location={"lat": 37.7749, "lon": -122.4194, "radius": 5000},
    indicators=["vegetation", "water_bodies", "urban_development"],
    visualization=True
)

# Present findings
detector.visualize_changes(changes)
detector.generate_report(changes, format="pdf")
```

## 🤝 Contributing

We welcome contributions to the memories-dev project! Please see our [CONTRIBUTING.md](CONTRIBUTING.md) file for guidelines on how to contribute.

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

<p align="center">Built with 💜 by the memories-dev team</p>
