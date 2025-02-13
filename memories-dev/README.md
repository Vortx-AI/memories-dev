# Source Code Documentation

## 📁 Directory Structure

```
src/
├── agents/                 # 🤖 Agent System
│   ├── core/              # Core agent functionality
│   │   ├── base.py        # Base agent classes
│   │   └── registry.py    # Agent registry
│   ├── memory/            # Memory integration
│   │   ├── context.py     # Context management
│   │   └── retrieval.py   # Memory retrieval
│   └── specialized/       # Specialized agents
│       ├── analysis.py    # Analysis agents
│       └── synthesis.py   # Synthesis agents
│
├── data_acquisition/      # 📡 Data Collection
│   ├── satellite/         # Satellite data handlers
│   │   ├── sentinel/     # Sentinel-1/2
│   │   └── landsat/      # Landsat 7/8
│   ├── sensors/          # Sensor networks
│   │   ├── climate/      # Climate sensors
│   │   └── urban/        # Urban sensors
│   └── streams/          # Real-time streams
│       ├── ingest.py     # Stream ingestion
│       └── process.py    # Stream processing
│
├── memories/             # 🧠 Memory System
│   ├── store/           # Storage backend
│   │   ├── vector.py    # Vector store
│   │   └── index.py     # Indexing system
│   ├── formation/       # Memory creation
│   │   ├── create.py    # Memory formation
│   │   └── update.py    # Memory updates
│   └── query/           # Query system
│       ├── spatial.py   # Spatial queries
│       └── temporal.py  # Temporal queries
│
├── models/              # 🔮 AI Models
│   ├── embedding/      # Embedding models
│   │   ├── text.py    # Text embeddings
│   │   └── vision.py  # Vision embeddings
│   ├── reasoning/     # Reasoning models
│   │   ├── llm.py    # Language models
│   │   └── chain.py  # Reasoning chains
│   └── fusion/       # Multi-modal fusion
│       └── combine.py # Modality fusion
│
├── synthesis/         # 🔄 Memory Synthesis
│   ├── fusion/       # Data fusion
│   │   ├── spatial.py  # Spatial fusion
│   │   └── temporal.py # Temporal fusion
│   └── generation/   # Synthetic data
│       ├── augment.py  # Data augmentation
│       └── create.py   # Synthetic creation
│
└── utils/            # 🛠️ Utilities
    ├── config/       # Configuration
    ├── logging/      # Logging system
    └── validation/   # Data validation
```

## 🔄 Workflows

### Memory Formation Pipeline

```mermaid
graph LR
    %% Node Styles
    classDef input fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    classDef process fill:#f3e5f5,stroke:#6a1b9a,stroke-width:2px
    classDef storage fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    
    %% Input Nodes
    I1(("📡 Raw Data")):::input
    I2(("🛰️ Satellite")):::input
    I3(("🌡️ Sensors")):::input
    
    %% Processing Nodes
    P1["🔄 Preprocessing"]:::process
    P2["⚡ Feature Extraction"]:::process
    P3["🧠 Memory Formation"]:::process
    
    %% Storage Nodes
    S1[("💾 Vector Store")]:::storage
    S2[("📊 Time Series DB")]:::storage
    S3[("🗺️ Spatial Index")]:::storage
    
    %% Flow
    I1 & I2 & I3 --> P1
    P1 --> P2
    P2 --> P3
    P3 --> S1 & S2 & S3
```

### Query Pipeline

```mermaid
graph TD
    %% Node Styles
    classDef query fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef memory fill:#f3e5f5,stroke:#6a1b9a,stroke-width:2px
    classDef output fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px

    %% Query Flow
    Q1["🔍 Query Request"]:::query
    Q2["📍 Location Filter"]:::query
    Q3["⏱️ Time Filter"]:::query
    
    %% Memory Operations
    M1["🧠 Memory Lookup"]:::memory
    M2["🔄 Context Assembly"]:::memory
    M3["⚡ Real-time Update"]:::memory
    
    %% Output Generation
    O1["📊 Results"]:::output
    O2["📝 Analysis"]:::output
    O3["🔄 Synthesis"]:::output

    %% Connections
    Q1 --> Q2 & Q3
    Q2 & Q3 --> M1
    M1 --> M2 --> M3
    M3 --> O1 & O2 & O3
```

### Agent System

```mermaid
graph TD
    %% Node Styles
    classDef agent fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef memory fill:#f3e5f5,stroke:#6a1b9a,stroke-width:2px
    classDef task fill:#e3f2fd,stroke:#1565c0,stroke-width:2px

    %% Agent Components
    subgraph "🤖 Agent System"
        A1["🧠 Reasoning Engine"]:::agent
        A2["🔄 Memory Integration"]:::agent
        A3["📊 Analysis Engine"]:::agent
    end

    %% Memory Access
    subgraph "💾 Memory Access"
        M1["📥 Retrieval"]:::memory
        M2["🔄 Update"]:::memory
        M3["🔍 Query"]:::memory
    end

    %% Task Processing
    subgraph "📋 Tasks"
        T1["📊 Analysis"]:::task
        T2["🔄 Synthesis"]:::task
        T3["📝 Reporting"]:::task
    end

    %% Connections
    A1 --> M1 & M2 & M3
    M1 & M2 & M3 --> A2
    A2 --> A3
    A3 --> T1 & T2 & T3
```

## 🔑 Key Components

### 🤖 Agent System
- **Base Agent**: Core agent functionality and interfaces
- **Memory Integration**: Memory access and context management
- **Specialized Agents**: Task-specific agent implementations

### 📡 Data Acquisition
- **Satellite Data**: Handlers for various satellite data sources
- **Sensor Networks**: Climate and urban sensor data collection
- **Stream Processing**: Real-time data stream handling

### 🧠 Memory System
- **Storage**: Vector store and indexing systems
- **Formation**: Memory creation and update mechanisms
- **Query**: Spatial and temporal query capabilities

### 🔮 Models
- **Embeddings**: Text and vision embedding models
- **Reasoning**: LLM integration and reasoning chains
- **Fusion**: Multi-modal data fusion capabilities

### 🔄 Synthesis
- **Data Fusion**: Spatial and temporal data fusion
- **Generation**: Synthetic data creation and augmentation

### 🛠️ Utilities
- **Configuration**: System configuration management
- **Logging**: Comprehensive logging system
- **Validation**: Data validation utilities

## 📚 Module Dependencies

```mermaid
graph TD
    %% Node Styles
    classDef core fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    classDef dep fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef util fill:#f3e5f5,stroke:#6a1b9a,stroke-width:2px

    %% Core Modules
    C1["🧠 Memory Core"]:::core
    C2["🤖 Agent Core"]:::core
    C3["📡 Data Core"]:::core

    %% Dependencies
    D1["📊 NumPy/Pandas"]:::dep
    D2["🔥 PyTorch"]:::dep
    D3["🗄️ Vector Store"]:::dep
    D4["🌐 Network Utils"]:::dep

    %% Utilities
    U1["⚙️ Config"]:::util
    U2["📝 Logging"]:::util
    U3["✅ Validation"]:::util

    %% Connections
    D1 & D2 --> C1
    D3 --> C1 & C2
    D4 --> C3
    U1 --> C1 & C2 & C3
    U2 --> C1 & C2 & C3
    U3 --> C1 & C2 & C3
```

## 🚀 Getting Started

For development setup and usage examples, please refer to the main [README.md](../README.md) in the project root.
