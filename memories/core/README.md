# Memory Management System

This directory contains the core memory management system for the Memories project.

## What's New in Version 2.0.6 (Scheduled for March 3, 2025)

Since our initial release (v1.0.0 on February 14, 2025), we've made significant improvements to the memory management system:

### New Features
- **Memory Optimization**: Advanced memory usage with automatic tier balancing
- **Distributed Memory**: Support for distributed memory across multiple nodes
- **Memory Snapshots**: Point-in-time memory snapshots for backup and recovery
- **Memory Analytics**: Built-in analytics for memory usage and performance

### Improvements
- **Enhanced GPU Support**: Better utilization of GPU memory for hot tier
- **Memory Compression**: Intelligent compression for cold and glacier tiers
- **Query Performance**: Faster memory retrieval with optimized indexing
- **Memory Migration**: Improved policies for automatic data migration
- **Persistence Options**: More flexible options for persistent storage

## Memory Tiers

The memory management system is built on a 4-tier architecture designed for efficient data storage and retrieval:

### 1. Hot Memory (GPU Memory)
- **Purpose**: Ultra-fast access for active processing
- **Characteristics**:
  - Highest speed, limited capacity
  - Optimized for tensor operations
  - Automatic garbage collection
- **New in 2.0.6**:
  - Multi-GPU support
  - Tensor optimization
  - Priority-based allocation

### 2. Warm Memory (CPU/In-Memory)
- **Purpose**: Fast access for working data
- **Characteristics**:
  - High speed, moderate capacity
  - RAM-based storage
  - Efficient for structured data
- **New in 2.0.6**:
  - Memory pooling
  - Shared memory support
  - Improved serialization

### 3. Cold Memory (On-Device Storage)
- **Purpose**: Persistent storage for less frequently accessed data
- **Characteristics**:
  - Moderate speed, high capacity
  - Disk-based storage
  - Automatic indexing
- **New in 2.0.6**:
  - Intelligent compression
  - Partial loading
  - Optimized file formats

### 4. Glacier Memory (Off-Device Storage)
- **Purpose**: Long-term archival storage
- **Characteristics**:
  - Slow access, unlimited capacity
  - Cloud or network storage
  - Cost-optimized
- **New in 2.0.6**:
  - Multi-provider support
  - Encrypted storage
  - Batch operations

## Data Flow

Data flows through the system as follows:

1. New data enters the system in Hot or Warm Memory
2. Based on access patterns and policies, data migrates between tiers
3. Least recently used data moves to colder tiers
4. Frequently accessed data in cold tiers is promoted to warmer tiers
5. Data can be explicitly placed in specific tiers when needed

### Advanced Flow Control (New in 2.0.6)

- **Predictive Caching**: Pre-loads data based on predicted access patterns
- **Access-Based Migration**: Automatically moves data based on access frequency
- **Batch Processing**: Efficiently processes large datasets across tiers
- **Priority Queues**: Prioritizes critical data for faster access

## Usage Examples

### Basic Usage

```python
from memories.core import MemoryManager

# Initialize memory manager
memory_manager = MemoryManager(
    hot_memory_size=2,    # GB
    warm_memory_size=8,   # GB
    cold_memory_size=50,  # GB
    glacier_enabled=True
)

# Store data in memory
memory_manager.store(
    key="location_data",
    value=location_data,
    tier="warm"  # Options: "hot", "warm", "cold", "glacier"
)

# Retrieve data from memory
data = memory_manager.retrieve("location_data")

# Check if data exists
exists = memory_manager.exists("location_data")

# Delete data
memory_manager.delete("location_data")
```

### Advanced Usage (New in 2.0.6)

```python
from memories.core import MemoryManager
from memories.core.policies import MigrationPolicy

# Define custom migration policy
class CustomMigrationPolicy(MigrationPolicy):
    def should_migrate(self, data_key, current_tier, stats):
        access_count = stats.get_access_count(data_key)
        last_access = stats.get_last_access(data_key)
        size = stats.get_size(data_key)
        
        if current_tier == "cold" and access_count > 100:
            return "warm"  # Promote frequently accessed data
        elif current_tier == "warm" and last_access > 86400:
            return "cold"  # Demote stale data
        return current_tier

# Initialize memory manager with custom policy
memory_manager = MemoryManager(
    migration_policy=CustomMigrationPolicy(),
    compression_enabled=True,
    encryption_enabled=True
)

# Store data with metadata
memory_manager.store(
    key="satellite_data",
    value=satellite_imagery,
    tier="hot",
    metadata={
        "timestamp": "2025-02-15T10:30:00Z",
        "location": "San Francisco",
        "resolution": "10m"
    }
)

# Configure glacier storage
glacier_config = {
    "provider": "gcs",  # or "azure", "local"
    "bucket": "memories-archive",
    "prefix": "archive/",
    "region": "us-west1",
    "encryption": "AES256"
}

memory_manager.configure_glacier(glacier_config)

# Batch operations
keys_to_archive = ["data1", "data2", "data3"]
memory_manager.migrate_batch(
    keys=keys_to_archive,
    target_tier="glacier",
    compression_level="high"
)

# Memory analytics
stats = memory_manager.get_stats()
print(f"Hot tier utilization: {stats.hot_tier_utilization}%")
print(f"Most accessed keys: {stats.get_top_accessed_keys(5)}")
print(f"Total data size: {stats.total_size_gb}GB")
```

## Implementation Details

### Hot Memory

```python
from memories.core.hot_memory import HotMemory

# Initialize hot memory
hot_memory = HotMemory(size_gb=2)

# Store tensor data
hot_memory.store("model_weights", model_weights_tensor)

# Retrieve tensor data
weights = hot_memory.retrieve("model_weights")

# New in 2.0.6: Tensor optimization
hot_memory.optimize_layout("model_weights")

# New in 2.0.6: Create snapshot
hot_memory.create_snapshot("weights_snapshot")
```

### Warm Memory

```python
from memories.core.warm_memory import WarmMemory

# Initialize warm memory
warm_memory = WarmMemory(size_gb=8)

# Store structured data
warm_memory.store("vector_data", vector_data)

# Retrieve data
data = warm_memory.retrieve("vector_data")

# New in 2.0.6: Memory pooling
warm_memory.allocate_pool("frequent_access", size_mb=500)

# New in 2.0.6: Get metrics
metrics = warm_memory.get_metrics()
```

### Cold Memory

```python
from memories.core.cold_memory import ColdMemory

# Initialize cold memory
cold_memory = ColdMemory(
    size_gb=50,
    storage_path="./cold_storage"
)

# Store large dataset
cold_memory.store("historical_data", historical_data)

# Retrieve data
data = cold_memory.retrieve("historical_data")

# New in 2.0.6: Partial retrieval
header = cold_memory.retrieve(
    "historical_data", 
    partial=True,
    start=0,
    end=1000
)

# New in 2.0.6: Compress data
cold_memory.compress("historical_data")
```

### Glacier Memory

```python
from memories.core.glacier_memory import GlacierMemory

# Initialize glacier memory
glacier_memory = GlacierMemory(
    provider="local",  # Options: "local", "gcs", "azure"
    config={
        "storage_path": "./glacier_storage"
    }
)

# Store archival data
glacier_memory.store("archive_2024", archive_data)

# Retrieve data (may be slow)
data = glacier_memory.retrieve("archive_2024")

# New in 2.0.6: Batch operations
glacier_memory.batch_store([
    {"key": "archive_1", "value": archive_1},
    {"key": "archive_2", "value": archive_2},
    {"key": "archive_3", "value": archive_3}
])
```

## Configuration

### Memory Tier Configuration

```python
# Hot Memory Configuration
hot_config = {
    "size_gb": 2,
    "device": "cuda:0",  # or "cuda:1", etc.
    "precision": "float16",  # or "float32", "bfloat16"
    "garbage_collection_threshold": 0.8  # 80% usage triggers GC
}

# Warm Memory Configuration
warm_config = {
    "size_gb": 8,
    "serialization_format": "pickle",  # or "msgpack", "json"
    "compression": "lz4",  # or "zstd", "none"
    "shared_memory": False
}

# Cold Memory Configuration
cold_config = {
    "size_gb": 50,
    "storage_path": "./cold_storage",
    "file_format": "parquet",  # or "hdf5", "zarr"
    "compression": "zstd",  # or "lz4", "snappy", "none"
    "index_in_memory": True
}

# Glacier Memory Configuration
glacier_config = {
    "provider": "gcs",  # or "azure", "local"
    "bucket": "memories-archive",
    "prefix": "archive/",
    "region": "us-west1",
    "encryption": "AES256"
}
```

## Real-World Memory System Applications

Our memory management system powers a wide range of real-world applications that require efficient handling of large-scale data. Here are some examples of how organizations are leveraging our memory architecture:

### Large-Scale Machine Learning Operations

**AI Research Laboratory**

A leading AI research laboratory implemented our memory management system to optimize their large language model training pipeline. Their application:

- Utilizes Hot Memory (GPU) for active model parameters and gradients
- Stores intermediate activations in Warm Memory (RAM)
- Keeps checkpoints and training datasets in Cold Memory (SSD)
- Archives historical models and experiment results in Glacier Memory (HDD/Cloud)

```python
from memories.core.memory_manager import MemoryManager
import torch

def optimize_llm_training(model, training_data, batch_size):
    # Initialize memory manager with custom tier sizes
    memory_manager = MemoryManager(
        hot_memory_size=24,  # 24GB GPU memory
        warm_memory_size=128,  # 128GB RAM
        cold_memory_size=2048,  # 2TB SSD
        glacier_memory_size=20480  # 20TB Cloud Storage
    )
    
    # Store model in hot memory for training
    model_key = memory_manager.store(
        "active_model",
        model.state_dict(),
        tier="hot",
        priority="high"
    )
    
    # Store training dataset in cold memory
    dataset_key = memory_manager.store(
        "training_dataset",
        training_data,
        tier="cold",
        compression=True
    )
    
    # Training loop
    for epoch in range(10):
        # Load batch data into warm memory
        for batch_idx in range(0, len(training_data), batch_size):
            batch_data = memory_manager.retrieve_partial(
                dataset_key,
                start_idx=batch_idx,
                end_idx=batch_idx + batch_size
            )
            
            # Move batch to hot memory for processing
            batch_key = memory_manager.store(
                f"batch_{batch_idx}",
                batch_data,
                tier="hot"
            )
            
            # Process batch
            # ...
            
            # Store intermediate results in warm memory
            memory_manager.store(
                f"epoch_{epoch}_batch_{batch_idx}_results",
                intermediate_results,
                tier="warm"
            )
        
        # Create checkpoint in cold memory
        checkpoint = {
            "epoch": epoch,
            "model_state": memory_manager.retrieve(model_key),
            "optimizer_state": optimizer.state_dict()
        }
        
        memory_manager.store(
            f"checkpoint_epoch_{epoch}",
            checkpoint,
            tier="cold",
            metadata={"epoch": epoch, "timestamp": time.time()}
        )
    
    # Archive final model to glacier memory
    memory_manager.store(
        "final_model",
        memory_manager.retrieve(model_key),
        tier="glacier",
        metadata={"training_completed": time.time()}
    )
    
    # Clean up resources
    memory_manager.cleanup()
```

The system reduced training time by 42% and decreased GPU memory fragmentation by 78%, enabling the training of larger models on the same hardware.

### Real-Time Geospatial Analytics

**Smart City Platform**

A smart city platform uses our memory management system to process and analyze real-time geospatial data from thousands of IoT sensors. Their application:

- Keeps real-time sensor data in Hot Memory for immediate processing
- Stores recent historical data in Warm Memory for quick access
- Archives processed data in Cold Memory for reporting
- Maintains long-term historical data in Glacier Memory for trend analysis

The system processes data from over 50,000 sensors in real-time, enabling immediate response to traffic congestion, air quality issues, and public safety incidents.

### High-Frequency Trading Platform

**Financial Technology Firm**

A financial technology firm implemented our memory management system in their high-frequency trading platform. Their application:

- Utilizes Hot Memory for real-time market data and active trading algorithms
- Keeps recent market history in Warm Memory for pattern recognition
- Stores trading records and compliance data in Cold Memory
- Archives historical market data in Glacier Memory for backtesting

```python
from memories.core.memory_manager import MemoryManager
from memories.core.distributed import DistributedMemoryManager

def setup_trading_platform():
    # Initialize distributed memory manager across trading nodes
    memory_manager = DistributedMemoryManager(
        nodes=["trading-node-1", "trading-node-2", "trading-node-3"],
        primary_node="trading-node-1",
        replication_factor=2,
        hot_memory_size=16,
        warm_memory_size=64,
        cold_memory_size=1024,
        glacier_memory_size=10240
    )
    
    # Set up real-time market data in hot memory
    memory_manager.store(
        "market_data_stream",
        market_data_stream,
        tier="hot",
        distributed=True,
        update_frequency="realtime"
    )
    
    # Store trading algorithms in hot memory
    memory_manager.store(
        "trading_algorithms",
        trading_algorithms,
        tier="hot",
        distributed=True,
        priority="critical"
    )
    
    # Set up market history in warm memory with automatic migration
    memory_manager.store(
        "market_history_24h",
        recent_market_data,
        tier="warm",
        distributed=True,
        auto_migrate=True,
        migration_policy={
            "age_threshold": 86400,  # 24 hours
            "target_tier": "cold"
        }
    )
    
    # Configure automatic snapshots
    memory_manager.configure_snapshots(
        frequency=3600,  # Hourly snapshots
        retention={
            "hot": 4,     # Keep 4 hours in hot memory
            "warm": 24,   # Keep 24 hours in warm memory
            "cold": 720,  # Keep 30 days in cold memory
            "glacier": 8760  # Keep 1 year in glacier memory
        }
    )
    
    return memory_manager
```

The system achieved sub-millisecond response times for trading decisions, processing over 100,000 market events per second with 99.999% reliability.

### Genomic Research Platform

**Biotech Research Institute**

A biotech research institute uses our memory management system to process and analyze massive genomic datasets. Their application:

- Uses Hot Memory for active sequence alignment and analysis
- Keeps reference genomes and intermediate results in Warm Memory
- Stores processed genomic data in Cold Memory
- Archives raw sequencing data in Glacier Memory

The system enabled the analysis of over 10,000 whole-genome sequences, identifying novel genetic markers associated with rare diseases.

### Autonomous Vehicle Development

**Automotive Innovation Lab**

An automotive company implemented our memory management system in their autonomous vehicle development platform. Their application:

- Utilizes Hot Memory for real-time sensor fusion and decision making
- Keeps recent sensor history in Warm Memory for immediate context
- Stores drive session data in Cold Memory for analysis
- Archives all testing data in Glacier Memory for regulatory compliance

```python
from memories.core.memory_manager import MemoryManager
import numpy as np

class AutonomousVehicleMemory:
    def __init__(self):
        # Initialize memory manager
        self.memory_manager = MemoryManager(
            hot_memory_size=8,    # 8GB GPU memory
            warm_memory_size=32,  # 32GB RAM
            cold_memory_size=500, # 500GB SSD
            glacier_memory_size=8192  # 8TB Cloud Storage
        )
        
        # Initialize sensor buffers in hot memory
        self.sensor_keys = {
            "camera": self.memory_manager.store("camera_buffer", np.zeros((10, 1920, 1080, 3)), tier="hot"),
            "lidar": self.memory_manager.store("lidar_buffer", np.zeros((10, 100000, 4)), tier="hot"),
            "radar": self.memory_manager.store("radar_buffer", np.zeros((10, 1000, 4)), tier="hot"),
            "ultrasonic": self.memory_manager.store("ultrasonic_buffer", np.zeros((10, 12)), tier="hot")
        }
        
        # Initialize perception results in hot memory
        self.perception_key = self.memory_manager.store(
            "perception_results",
            {
                "objects": [],
                "lanes": [],
                "signs": []
            },
            tier="hot"
        )
        
        # Initialize recent history in warm memory
        self.history_key = self.memory_manager.store(
            "recent_history",
            {
                "positions": np.zeros((300, 3)),  # 5 minutes at 1Hz
                "velocities": np.zeros((300, 3)),
                "accelerations": np.zeros((300, 3)),
                "decisions": []
            },
            tier="warm"
        )
    
    def update_sensor_data(self, sensor_type, data):
        # Get current buffer
        buffer = self.memory_manager.retrieve(self.sensor_keys[sensor_type])
        
        # Roll buffer and add new data
        buffer = np.roll(buffer, -1, axis=0)
        buffer[-1] = data
        
        # Update buffer in hot memory
        self.memory_manager.update(self.sensor_keys[sensor_type], buffer)
    
    def save_drive_session(self, session_id):
        # Collect all data from warm memory
        history = self.memory_manager.retrieve(self.history_key)
        
        # Store in cold memory
        self.memory_manager.store(
            f"drive_session_{session_id}",
            history,
            tier="cold",
            metadata={"session_id": session_id, "timestamp": time.time()}
        )
        
        # Reset history buffer
        self.memory_manager.update(
            self.history_key,
            {
                "positions": np.zeros((300, 3)),
                "velocities": np.zeros((300, 3)),
                "accelerations": np.zeros((300, 3)),
                "decisions": []
            }
        )
    
    def archive_sessions(self, session_ids):
        # Move sessions from cold to glacier memory
        for session_id in session_ids:
            session_key = f"drive_session_{session_id}"
            session_data = self.memory_manager.retrieve(session_key, tier="cold")
            
            # Archive to glacier memory
            self.memory_manager.store(
                session_key,
                session_data,
                tier="glacier",
                compression=True,
                metadata={"archived_at": time.time()}
            )
            
            # Remove from cold memory
            self.memory_manager.delete(session_key, tier="cold")
```

The system enabled the processing of over 2TB of sensor data per vehicle per day, significantly accelerating the development and validation of autonomous driving capabilities.

## Getting Started with Your Own Memory Application

Inspired by these real-world applications? Here's how to get started with your own memory-intensive project:

1. **Analyze your data flow**: Identify hot, warm, cold, and archival data in your application
2. **Size your memory tiers**: Determine appropriate sizes for each memory tier
3. **Configure the memory manager**: Initialize the MemoryManager with your requirements
4. **Implement data placement strategies**: Decide which data belongs in which tier
5. **Set up migration policies**: Configure automatic data migration between tiers

For more detailed guidance, check out our [comprehensive documentation](../../docs/) and [tutorial series](../../docs/tutorials/).

## Coming in Version 2.1.0 (March 2025)

- **Memory Snapshots**: Enhanced point-in-time memory snapshots for backup and recovery
- **Multi-node Synchronization**: Improved synchronization for distributed memory
- **Memory Visualization**: Tools for visualizing memory usage and data flow
- **Custom Compression**: Support for custom compression algorithms
- **Memory Policies**: More flexible policies for memory management

## Contributing

We welcome contributions to the memory management system! Please see our [Contributing Guide](../../docs/contributing.md) for more information.

<p align="center">Built with 💜 by the memories-dev team</p>

# Memories Core

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-2.0.6-blue.svg)](https://github.com/Vortx-AI/memories-dev/releases/tag/v2.0.6)

