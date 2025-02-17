# Data Acquisition Module

This module handles all data acquisition, processing, and storage operations for the Memories system. It provides a robust framework for collecting, processing, and managing various types of data sources.

## Structure

```
data_acquisition/
├── sources/            # Source-specific implementations
├── __init__.py        # Module initialization
├── data_manager.py    # Core data management functionality
├── data_sources.py    # Data source abstractions and implementations
├── duckdb_utils.py    # DuckDB database utilities
├── index_parquet.py   # Parquet file indexing utilities
└── knowledge-base.json # Knowledge base configuration
```

## Core Components

### Data Manager (`data_manager.py`)
The Data Manager serves as the central coordinator for all data operations, providing:
- Data source registration and management
- Data ingestion pipeline coordination
- Storage management and optimization
- Query interface for stored data

### Data Sources (`data_sources.py`)
Implements various data source connectors and abstractions:
- REST API data sources
- File-based data sources
- Streaming data sources
- Custom data source implementations

### DuckDB Utilities (`duckdb_utils.py`)
Provides database operations for efficient data storage and querying:
- Table creation and management
- Query optimization
- Data indexing
- Cache management

### Parquet Indexing (`index_parquet.py`)
Handles Parquet file operations:
- File creation and compression
- Column-based storage optimization
- Index management
- Query acceleration

## Usage Examples

### 1. Basic Data Acquisition

```python
from memories.data_acquisition.data_manager import DataManager
from memories.data_acquisition.data_sources import RESTDataSource

# Initialize data manager
data_manager = DataManager()

# Configure a REST data source
rest_source = RESTDataSource(
    base_url="https://api.example.com",
    endpoints={
        "data": "/v1/data"
    }
)

# Register the data source
data_manager.register_source("example_source", rest_source)

# Acquire data
data = data_manager.acquire("example_source")
```

### 2. Working with Knowledge Base

```python
from memories.data_acquisition.data_manager import DataManager

# Initialize with custom knowledge base
data_manager = DataManager(knowledge_base_path="custom_knowledge_base.json")

# Access knowledge base configurations
config = data_manager.get_knowledge_base_config()
```

### 3. Data Storage and Retrieval

```python
from memories.data_acquisition.duckdb_utils import DuckDBManager

# Initialize DuckDB manager
db_manager = DuckDBManager("memory_duckdb.db")

# Store data
db_manager.store_data("table_name", data_frame)

# Query data
result = db_manager.query("SELECT * FROM table_name WHERE condition = 'value'")
```

## Data Source Implementations

The module supports various data source types:

1. **REST APIs**
   - Standard HTTP methods (GET, POST, PUT, DELETE)
   - Authentication handling
   - Rate limiting
   - Response parsing

2. **File Systems**
   - Local file system
   - Remote file systems (S3, GCS)
   - File format handling (CSV, JSON, Parquet)

3. **Streaming Sources**
   - Real-time data processing
   - Event-driven acquisition
   - Buffer management

## Performance Considerations

- Uses DuckDB for efficient query processing
- Implements caching mechanisms
- Supports parallel data acquisition
- Optimizes storage through Parquet compression

## Error Handling

The module implements comprehensive error handling:

```python
try:
    data_manager.acquire("source_name")
except DataSourceNotFoundError:
    # Handle missing source
except DataAcquisitionError:
    # Handle acquisition failure
except StorageError:
    # Handle storage issues
```

## Configuration

Knowledge base configuration (`knowledge-base.json`) defines:
- Data source endpoints
- Authentication requirements
- Rate limiting rules
- Storage preferences

## Best Practices

1. Always use the DataManager interface for consistency
2. Implement proper error handling
3. Configure appropriate timeouts
4. Use caching when possible
5. Monitor resource usage

## Testing

Tests are located in `tests/data_acquisition/` and cover:
- Unit tests for each component
- Integration tests for data flow
- Performance benchmarks
- Error handling scenarios 