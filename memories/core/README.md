# Memory Management System

This directory contains the implementation of a 4-tier memory management system designed for efficient data storage and retrieval across different performance requirements.

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

### 2. Warm Memory (CPU/In-Memory)
- **Purpose**: Fast CPU-based memory and in-memory storage for frequent access
- **Characteristics**:
  - Very fast key-value access
  - Data persistence with AOF/RDB
  - Supports complex data structures
  - Ideal for frequently accessed data
  - Scalable with Redis Cluster
  - CPU-based processing when needed

### 3. Cold Memory (On-Device Storage)
- **Purpose**: Efficient on-device storage for less frequently accessed data
- **Characteristics**:
  - SQL-like query capabilities
  - Efficient columnar storage
  - ACID compliance
  - Ideal for analytical queries
  - Local storage with fast access
  - Optimized for structured data

### 4. Glacier Memory (Off-Device Storage)
- **Purpose**: Long-term storage of historical data
- **Characteristics**:
  - Highly compressed storage
  - Columnar format for efficient queries
  - Ideal for archival and analytics
  - Can be stored on external/network storage
  - Cost-effective for large datasets
  - Optimized for long-term retention

## Memory Flow

Data typically flows through the system in the following pattern:

1. New data enters through Hot Memory for immediate GPU processing
2. Frequently accessed data moves to Warm Memory for CPU/in-memory operations
3. Less frequently accessed data is moved to Cold Memory
4. Historical data is archived in Glacier Memory

## Usage

The memory system is managed by the `MemoryManager` class, which provides a unified interface for:

- Storing data across all tiers
- Retrieving data from specific tiers
- Managing data lifecycle
- Cleaning up resources


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

