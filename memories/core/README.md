# Memory Management System

This directory contains the implementation of a 4-tier memory management system designed for efficient data storage and retrieval across different performance requirements.

## What's New in Version 2.0.2

### New Features
- **Memory Optimization**: Advanced memory usage optimization with automatic tier balancing
- **Distributed Memory**: Support for distributed memory across multiple nodes
- **Memory Snapshots**: Point-in-time memory snapshots for backup and recovery
- **Memory Analytics**: Built-in analytics for memory usage patterns and optimization

### Improvements
- **Enhanced GPU Support**: Improved CUDA integration with support for newer GPU architectures
- **Memory Compression**: Intelligent compression algorithms for all memory tiers
- **Query Performance**: Optimized query execution across memory tiers
- **Memory Migration**: Smarter policies for moving data between tiers
- **Persistence Options**: Additional persistence configurations for all memory tiers

## Memory Tiers

### 1. Hot Memory (GPU Memory)
- **Purpose**: Ultra-fast, GPU-accelerated memory for immediate inference and processing
- **Characteristics**:
  - Fastest possible access times
  - GPU-accelerated operations
  - Limited by GPU memory capacity
  - Optimized for parallel processing
  - Ideal for real-time inference and vector operations
  - CUDA-accelerated similarity search
  - Multi-GPU support (New in 2.0.2)
  - Tensor optimization (New in 2.0.2)

### 2. Warm Memory (CPU/In-Memory)
- **Purpose**: Fast CPU-based memory and in-memory storage for frequent access
- **Characteristics**:
  - Very fast key-value access
  - Data persistence with AOF/RDB
  - Supports complex data structures
  - Ideal for frequently accessed data
  - Scalable with Redis Cluster
  - CPU-based processing when needed
  - Memory compression (New in 2.0.2)
  - Distributed caching (New in 2.0.2)

### 3. Cold Memory (On-Device Storage)
- **Purpose**: Efficient on-device storage for less frequently accessed data
- **Characteristics**:
  - SQL-like query capabilities
  - Efficient columnar storage
  - ACID compliance
  - Ideal for analytical queries
  - Local storage with fast access
  - Optimized for structured data
  - Incremental backups (New in 2.0.2)
  - Query optimization (New in 2.0.2)

### 4. Glacier Memory (Off-Device Storage)
- **Purpose**: Long-term storage of historical data
- **Characteristics**:
  - Highly compressed storage
  - Columnar format for efficient queries
  - Ideal for archival and analytics
  - Can be stored on external/network storage
  - Cost-effective for large datasets
  - Optimized for long-term retention
  - Cloud storage integration (New in 2.0.2)
  - Tiered archival policies (New in 2.0.2)

## Memory Flow

Data typically flows through the system in the following pattern:

1. New data enters through Hot Memory for immediate GPU processing
2. Frequently accessed data moves to Warm Memory for CPU/in-memory operations
3. Less frequently accessed data is moved to Cold Memory
4. Historical data is archived in Glacier Memory

### Advanced Flow Control (New in 2.0.2)

Version 2.0.2 introduces advanced flow control mechanisms:

- **Predictive Caching**: Pre-loads data into higher tiers based on usage patterns
- **Access-Based Migration**: Automatically moves data between tiers based on access frequency
- **Batch Processing**: Optimizes data movement in batches to reduce overhead
- **Priority Queues**: Assigns priorities to data for optimized tier placement

## Usage

The memory system is managed by the `MemoryManager` class, which provides a unified interface for:

- Storing data across all tiers
- Retrieving data from specific tiers
- Managing data lifecycle
- Cleaning up resources

### Basic Usage

```python
from memories.core.memory_manager import MemoryManager

# Initialize memory manager with tier sizes
manager = MemoryManager(
    hot_memory_size=2,    # GB for GPU memory
    warm_memory_size=8,   # GB for in-memory storage
    cold_memory_size=50,  # GB for on-device storage
    glacier_memory_size=500  # GB for off-device storage
)

# Store data with automatic tier placement
manager.store(
    key="location_123",
    data={
        "satellite_image": image_data,
        "vector_data": vector_features,
        "metadata": metadata_dict
    }
)

# Retrieve data (automatically fetches from appropriate tier)
result = manager.retrieve(key="location_123")

# Explicitly retrieve from specific tier
hot_result = manager.retrieve_from_tier(key="location_123", tier="hot")

# Clean up when done
manager.cleanup()
```

### Advanced Usage (New in 2.0.2)

```python
from memories.core.memory_manager import MemoryManager
from memories.core.policies import MigrationPolicy, CompressionPolicy

# Define custom policies
migration_policy = MigrationPolicy(
    hot_to_warm_threshold=24,  # hours
    warm_to_cold_threshold=72,  # hours
    cold_to_glacier_threshold=30  # days
)

compression_policy = CompressionPolicy(
    warm_compression_ratio=0.7,
    cold_compression_ratio=0.5,
    glacier_compression_ratio=0.3,
    compression_algorithm="lz4"
)

# Initialize with custom policies
manager = MemoryManager(
    hot_memory_size=2,
    warm_memory_size=8,
    cold_memory_size=50,
    glacier_memory_size=500,
    migration_policy=migration_policy,
    compression_policy=compression_policy,
    enable_distributed=True,
    nodes=["node1:6379", "node2:6379"]
)

# Store with explicit tier placement
manager.store_in_tier(
    key="location_123",
    data=location_data,
    tier="warm",
    metadata={
        "priority": "high",
        "retention_days": 90,
        "access_pattern": "frequent"
    }
)

# Create memory snapshot
snapshot_id = manager.create_snapshot(
    tiers=["hot", "warm"],
    description="Pre-deployment state"
)

# Restore from snapshot
manager.restore_snapshot(snapshot_id)

# Get memory analytics
analytics = manager.get_analytics(
    time_range="last_7_days",
    metrics=["usage", "hit_rate", "migration_count"]
)

# Optimize memory usage
manager.optimize(target_tier="warm")
```

## Implementation Details

Each memory tier is implemented as a separate class with consistent interfaces:

- `HotMemory`: GPU-accelerated storage using CUDA
- `WarmMemory`: In-memory storage using Redis + CPU operations
- `ColdMemory`: On-device storage using DuckDB
- `GlacierMemory`: Off-device storage using Parquet

Each class implements the following methods:
- `store(data)`: Store new data
- `retrieve(query)`: Retrieve data matching query
- `retrieve_all()`: Retrieve all stored data
- `clear()`: Clear all data
- `cleanup()`: Clean up resources

### New Methods in 2.0.2

- `compress(data)`: Apply tier-specific compression
- `decompress(data)`: Decompress tier-specific data
- `create_snapshot()`: Create point-in-time snapshot
- `restore_snapshot(snapshot_id)`: Restore from snapshot
- `get_metrics()`: Retrieve performance metrics
- `optimize()`: Optimize storage and access patterns

## Configuration

### Memory Tier Configuration

```python
# Configure individual tiers
config = {
    "hot": {
        "device": "cuda:0",  # Use specific GPU
        "precision": "float16",  # Use half precision
        "max_batch_size": 64,
        "enable_tensor_cores": True  # New in 2.0.2
    },
    "warm": {
        "host": "localhost",
        "port": 6379,
        "db": 0,
        "password": "password",
        "cluster_mode": True,  # New in 2.0.2
        "nodes": ["node1:6379", "node2:6379"]  # New in 2.0.2
    },
    "cold": {
        "path": "./cold_storage.db",
        "journal_mode": "WAL",
        "synchronous": "NORMAL",
        "temp_directory": "/tmp",
        "enable_indexing": True  # New in 2.0.2
    },
    "glacier": {
        "path": "./glacier_storage/",
        "format": "parquet",
        "compression": "snappy",
        "partition_cols": ["year", "month"],
        "cloud_provider": "aws",  # New in 2.0.2
        "bucket": "memories-archive"  # New in 2.0.2
    }
}

# Initialize with configuration
manager = MemoryManager(config=config)
```

## Performance Considerations

- **Hot Memory**: Optimized for tensor operations and similarity search
- **Warm Memory**: Balances speed and capacity for frequent access
- **Cold Memory**: Provides query capabilities with reasonable performance
- **Glacier Memory**: Optimized for storage efficiency over access speed

### Performance Tuning (New in 2.0.2)

```python
# Performance tuning example
manager.tune_performance(
    hot_memory_batch_size=32,
    warm_memory_max_connections=100,
    cold_memory_cache_size=1024,  # MB
    glacier_memory_chunk_size=128  # MB
)

# Monitor performance
metrics = manager.get_performance_metrics()
print(f"Hot memory access time: {metrics['hot_access_time_ms']}ms")
print(f"Warm memory hit rate: {metrics['warm_hit_rate']}%")
print(f"Cold memory query time: {metrics['cold_query_time_ms']}ms")
```

## Error Handling

The memory system includes comprehensive error handling:

```python
try:
    result = manager.retrieve(key="location_123")
except MemoryTierError as e:
    print(f"Tier-specific error: {e}")
    # Fall back to next tier
    result = manager.retrieve_from_tier(key="location_123", tier="warm")
except MemoryKeyError as e:
    print(f"Key not found: {e}")
    # Handle missing data
except MemoryCapacityError as e:
    print(f"Memory capacity exceeded: {e}")
    # Trigger cleanup or expansion
```

## Best Practices

1. **Tier Sizing**
   - Size hot memory based on GPU capacity
   - Size warm memory for frequently accessed data
   - Size cold memory for analytical workloads
   - Size glacier memory for long-term retention

2. **Data Placement**
   - Place inference data in hot memory
   - Place frequently accessed metadata in warm memory
   - Place historical data in cold memory
   - Place archival data in glacier memory

3. **Performance Optimization**
   - Use batching for hot memory operations
   - Use pipelining for warm memory operations
   - Use indexing for cold memory queries
   - Use partitioning for glacier memory storage

4. **Resource Management**
   - Monitor memory usage across tiers
   - Implement automatic cleanup policies
   - Use snapshots for critical states
   - Implement proper error handling

<p align="center">Built with 💜 by the memories-dev team</p>

