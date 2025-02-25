# Memory Management System

This directory contains the core memory management system for the Memories project.

## What's New in Version 2.0.2 (Scheduled for February 25, 2025)

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
- **New in 2.0.2**:
  - Multi-GPU support
  - Tensor optimization
  - Priority-based allocation

### 2. Warm Memory (CPU/In-Memory)
- **Purpose**: Fast access for working data
- **Characteristics**:
  - High speed, moderate capacity
  - RAM-based storage
  - Efficient for structured data
- **New in 2.0.2**:
  - Memory pooling
  - Shared memory support
  - Improved serialization

### 3. Cold Memory (On-Device Storage)
- **Purpose**: Persistent storage for less frequently accessed data
- **Characteristics**:
  - Moderate speed, high capacity
  - Disk-based storage
  - Automatic indexing
- **New in 2.0.2**:
  - Intelligent compression
  - Partial loading
  - Optimized file formats

### 4. Glacier Memory (Off-Device Storage)
- **Purpose**: Long-term archival storage
- **Characteristics**:
  - Slow access, unlimited capacity
  - Cloud or network storage
  - Cost-optimized
- **New in 2.0.2**:
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

### Advanced Flow Control (New in 2.0.2)

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

### Advanced Usage (New in 2.0.2)

```python
from memories.core import MemoryManager
from memories.core.policies import MigrationPolicy

# Define custom migration policy
migration_policy = MigrationPolicy(
    hot_to_warm_threshold=24,  # hours
    warm_to_cold_threshold=72,  # hours
    cold_to_glacier_threshold=30  # days
)

# Initialize memory manager with custom policy
memory_manager = MemoryManager(
    hot_memory_size=4,
    warm_memory_size=16,
    cold_memory_size=100,
    glacier_enabled=True,
    migration_policy=migration_policy
)

# Store data with metadata
memory_manager.store(
    key="satellite_imagery",
    value=imagery_data,
    metadata={
        "location": "San Francisco",
        "date": "2025-02-15",
        "source": "sentinel-2"
    }
)

# Query data by metadata
results = memory_manager.query(
    metadata_filter={
        "location": "San Francisco",
        "date": {"$gte": "2025-01-01"}
    }
)

# Create memory snapshot
snapshot_id = memory_manager.create_snapshot(
    description="Pre-processing state"
)

# Restore from snapshot
memory_manager.restore_snapshot(snapshot_id)

# Get memory metrics
metrics = memory_manager.get_metrics()
print(f"Hot memory usage: {metrics['hot']['usage_percent']}%")
print(f"Warm memory usage: {metrics['warm']['usage_percent']}%")
print(f"Cold memory usage: {metrics['cold']['usage_percent']}%")

# Compress cold memory
memory_manager.compress(tier="cold", compression_level=5)
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

# New in 2.0.2: Tensor optimization
hot_memory.optimize_layout("model_weights")

# New in 2.0.2: Create snapshot
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

# New in 2.0.2: Memory pooling
warm_memory.allocate_pool("frequent_access", size_mb=500)

# New in 2.0.2: Get metrics
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

# New in 2.0.2: Partial retrieval
header = cold_memory.retrieve(
    "historical_data", 
    partial=True,
    start=0,
    end=1000
)

# New in 2.0.2: Compress data
cold_memory.compress("historical_data")
```

### Glacier Memory

```python
from memories.core.glacier_memory import GlacierMemory

# Initialize glacier memory
glacier_memory = GlacierMemory(
    provider="local",  # Options: "local", "s3", "gcs", "azure"
    config={
        "storage_path": "./glacier_storage"
    }
)

# Store archival data
glacier_memory.store("archive_2024", archive_data)

# Retrieve data (may be slow)
data = glacier_memory.retrieve("archive_2024")

# New in 2.0.2: Batch operations
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
    "provider": "s3",  # or "gcs", "azure", "local"
    "bucket": "memories-archive",
    "prefix": "archive/",
    "region": "us-west-2",
    "encryption": "AES256"
}
```

## Coming in Version 2.1.0 (March 2025)

- **Memory Snapshots**: Enhanced point-in-time memory snapshots for backup and recovery
- **Multi-node Synchronization**: Improved synchronization for distributed memory
- **Memory Visualization**: Tools for visualizing memory usage and data flow
- **Custom Compression**: Support for custom compression algorithms
- **Memory Policies**: More flexible policies for memory management

## Contributing

We welcome contributions to the memory management system! Please see our [Contributing Guide](https://memories-dev.readthedocs.io/development/contributing.html) for more information.

<p align="center">Built with 💜 by the memories-dev team</p>

