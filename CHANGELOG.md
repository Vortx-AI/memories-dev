# Changelog

All notable changes to memories.dev will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.7] - 2025-03-15

### Added

- **Core**
  - Added direct file storage capability for Glacier to Cold transfers
  - Implemented `store_file` method in `ColdMemory` class for binary data storage
  - Added `glacier_to_cold_file` method to preserve binary file formats
  - Enhanced metadata handling for file-based storage
  - Improved error handling for binary data transfers

- **Scripts & Utilities**

  - Improved file path handling and validation
  - Enhanced file metadata recording and retrieval

### Enhanced

- **Core**
  - Improved binary data handling in Cold storage
  - Added support for preserving file formats without encoding
  - Enhanced file registration in memory catalog
  - Added better file path management and timestamp-based naming
  - Improved error reporting for storage operations
  - Enhanced retrieval of binary data from Glacier storage
  - Improved file format detection and handling
  - Better error handling for large file transfers
  - Added support for custom filenames during transfers

### Fixed

- Fixed data transfer issue when moving binary data from Glacier to Cold storage
- Resolved issue with non-existent `store_raw` method in `ColdMemory` class
- Improved handling of different data types during tier transfers
- Enhanced base64 encoding for binary data that needs database storage
- Fixed parameter handling in `ColdMemory.store` method calls

## [2.0.6] - 2025-03-13

### Added

- **Core**
  - Enhanced schema transfer from cold to red hot memory
  - Added schema embeddings for semantic column search
  - Improved metadata extraction and storage for parquet files
  - Optimized parquet file handling to reduce disk space usage
  - Improved batch processing for large datasets
  - Enhanced memory cleanup routines
  - Better error handling and logging across core functions

- **Models**
  - Added robust error handling for models
  - Enhanced API integration for models
  - Improved API key management from environment variables
  - Added comprehensive logging for API interactions
  - Enhanced chat completion functionality

- **Utils**
  - Added dependency version checks and compatibility validation
  - Improved temporary directory handling and cleanup
  - Enhanced DuckDB lock management and release mechanisms

- **Deployment**
  - Added test environment configuration handling
  - Enhanced geospatial data testing
  - Added comprehensive API connector tests

- **Configuration**
  - Added fallback configuration handling for test environments
  - Improved config file path handling
  - Added environment-aware configuration loading
  - Enhanced error messages for missing configurations
  - Added test-specific configuration defaults

### Fixed

- **Core**
  - Fixed TypeError in batch parquet import tests related to 'enable_red_hot' parameter
  - Resolved multiple TypeErrors in memory retrieval tests related to 'vector_encoder' parameter
  - Fixed geospatial data querying test failures

- **Models**
  - Fixed API connector test reliability issues

- **Utils**
  - Enhanced test suite with better mocking and fixtures
  - Added conditional test skipping for optional dependencies

- **Deployment**
  - Fixed config file not found error in test environments
  - Added proper test configuration initialization

- **Configuration**
  - Updated test suite to match new API parameters
  - Resolved documentation test dependencies

### Enhanced

- **Documentation**
  - Improved version consistency checks
  - Enhanced API reference completeness
  - Added better example code validation
  - Updated changelog formatting and structure
  - Improved license information consistency
  - Added test environment setup documentation

## [2.0.5] - 2025-03-05

### Added

- **Schema Management**
  - Enhanced schema transfer from cold to red hot memory
  - Added schema embeddings for semantic column search
  - Improved metadata extraction and storage for parquet files

- **System Improvements**
  - Added dependency version checks and compatibility validation
  - Improved temporary directory handling and cleanup
  - Enhanced DuckDB lock management and release mechanisms
  - Better error handling and logging across core functions
  - Added fallback configuration handling for test environments

- **Memory Optimization**
  - Optimized parquet file handling to reduce disk space usage
  - Improved batch processing for large datasets
  - Enhanced memory cleanup routines

- **Testing Improvements**
  - Enhanced test suite with better mocking and fixtures
  - Added conditional test skipping for optional dependencies
  - Improved documentation testing with mock imports
  - Added comprehensive API connector tests
  - Enhanced geospatial data testing
  - Added test environment configuration handling

- **API Connectors**
  - Added robust error handling for  API
  - Enhanced API integration
  - Improved API key management from environment variables
  - Added comprehensive logging for API interactions
  - Enhanced chat completion functionality

### Fixed

- **Test Suite Fixes**
  - Fixed TypeError in batch parquet import tests related to 'enable_red_hot' parameter
  - Resolved multiple TypeErrors in memory retrieval tests related to 'vector_encoder' parameter
  - Fixed geospatial data querying test failures
  - Updated test suite to match new API parameters
  - Resolved documentation test dependencies
  - Fixed API connector test reliability issues
  - Fixed config file not found error in test environments
  - Added proper test configuration initialization

### Enhanced

- **Documentation**
  - Improved version consistency checks
  - Enhanced API reference completeness
  - Added better example code validation
  - Updated changelog formatting and structure
  - Improved license information consistency
  - Added test environment setup documentation

- **Configuration Management**
  - Improved config file path handling
  - Added environment-aware configuration loading
  - Enhanced error messages for missing configurations
  - Added test-specific configuration defaults

## [2.0.4] - 2025-03-03

### Added

- **Schema Management**
  - Enhanced schema transfer from cold to red hot memory
  - Added schema embeddings for semantic column search
  - Improved metadata extraction and storage for parquet files

- **System Improvements**
  - Added dependency version checks and compatibility validation
  - Improved temporary directory handling and cleanup
  - Enhanced DuckDB lock management and release mechanisms
  - Better error handling and logging across core functions

- **Memory Optimization**
  - Optimized parquet file handling to reduce disk space usage
  - Improved batch processing for large datasets
  - Enhanced memory cleanup routines

## [2.0.3] - 2025-02-28

### Added
- **Memory Management**
  - Advanced memory cleanup and optimization routines
  - Improved garbage collection for large datasets
  - Enhanced memory allocation strategies
  - Dynamic memory scaling capabilities

- **Performance**
  - Optimized query execution paths
  - Enhanced caching mechanisms
  - Improved parallel processing efficiency
  - Better resource utilization across nodes

- **Analytics**
  - Advanced memory usage analytics
  - Real-time performance monitoring
  - Detailed system health metrics
  - Resource utilization tracking

### Enhanced
- **Core Systems**
  - Improved error recovery mechanisms
  - Enhanced system stability
  - Better failover handling
  - Optimized background tasks

- **Documentation**
  - Updated deployment guides
  - Enhanced troubleshooting documentation
  - Added performance tuning guides
  - Improved API documentation

### Fixed
- Memory leaks in long-running processes
- Race conditions in parallel processing
- Cache invalidation edge cases
- Resource cleanup in error scenarios

### Security
- Enhanced access control mechanisms
- Improved data encryption
- Updated security protocols
- Better audit logging


## [2.0.2] - 2025-02-24

Enhanced Earth Memory Integration: Seamless fusion of 15+ specialized analyzers for comprehensive environmental understanding
Temporal Analysis Engine: Advanced historical change detection and future prediction capabilities
Asynchronous Processing Pipeline: Parallel execution of multiple Earth Memory analyzers for 10x faster analysis
Vector-Based Memory Storage: Efficient embedding and retrieval of complex multi-modal data
Comprehensive Scoring System: Sophisticated algorithms for property evaluation across multiple dimensions
Multi-model Inference: Compare results from multiple LLM providers
Streaming Responses: Real-time streaming for all supported model providers
Memory Optimization: Advanced memory usage with automatic tier balancing
Distributed Memory: Support for distributed memory across multiple nodes

### Added
  - New deployment patterns documentation with comprehensive 
  - **Diagrams**
  - Standalone deployment configuration for high-performance computing
  - Consensus deployment support for distributed systems
  - Swarmed deployment pattern for edge computing and global 
  - **Distribution**
  - Cross-cloud provider support (AWS, Azure, GCP)
  - Advanced hardware configuration templates
  - Security and monitoring documentation
  - **Utils**
  - Added new geometry processing utilities
  - Enhanced text processing with better error handling
  - Added location normalization utilities
  - Improved coordinate validation and processing
  - **Models**
  - Added new model loading system
  - Enhanced model cleanup procedures
  - Improved GPU memory management
  - Implemented new async process method in BaseModel
  - Added proper error handling and state management
  - Enhanced tool registration and validation system
  - Implemented memory cleanup handlers

### Enhanced
  - Improved documentation structure
  - Added mermaid diagrams for architecture visualization
  - Enhanced deployment selection guide
  - Updated folder structure for better organization
  - **Data Acquisition**
  - Enhanced OvertureAPI with direct S3 access
  - Added DuckDB integration for efficient data filtering
  - Added support for multiple Overture themes
  - Enhanced error handling in data downloads
  - **Utils**
  - Optimized data filtering and processing
  - Enhanced memory efficiency
  - Improved error handling and logging
  - Better handling of large datasets

### Fixed
  - Configuration file structure and organization
  - Documentation clarity and completeness
  - Cross-provider compatibility issues
  - **Cache System**: 
    - Improved cache invalidation mechanism in DataManager
    - Fixed JSON serialization of numpy arrays in satellite data
    - Enhanced cache key generation for refresh operations
    - Added proper handling of mock responses in tests
  - **Models**:
    - Resolved async execution issues
    - Fixed tool registration validation

  - **Data Acquisition**:
    - Fixed Overture API connection issues
    - Resolved DuckDB extension loading problems
    - Fixed data filtering edge cases
    - Improved error handling in downloads

### Testing
- **Test Improvements**:
  - Enhanced test_cache_invalidation with deterministic responses
  - Added call counting for better test control
  - Improved assertions for cache refresh verification
  - Added comprehensive test coverage for cache operations
  - Added data acquisition tests
  - Improved utility function testing



## [2.0.0] - 2025-02-19 🎉 Production Release

### Major Changes 🌟
- **Production-Grade Release**: 
  - Elevated to version 2.0.0 marking enterprise readiness
  - Comprehensive stability improvements
  - Production-grade performance optimizations
  - Full backward compatibility guarantees

- **Architecture Enhancements**: 
  - Advanced memory processing algorithms
  - Improved scalability for large deployments
  - Enhanced multi-node support
  - Optimized resource utilization

- **API Maturity**: 
  - Stabilized public APIs
  - Comprehensive versioning support
  - Enhanced error handling
  - Improved response formats

### Performance Improvements ⚡
- **Memory Processing**: 
  - 50% faster memory formation
  - Reduced memory footprint
  - Optimized cache utilization
  - Enhanced parallel processing

- **Query Performance**: 
  - Advanced query optimization
  - Improved response times
  - Better resource management
  - Enhanced data retrieval

### Developer Experience 👩‍💻
- **Documentation**: 
  - Comprehensive API reference
  - Interactive code examples
  - Advanced usage patterns
  - Best practices guide

- **Testing & Quality**: 
  - Expanded test coverage
  - Real-world scenario testing
  - Performance benchmarks
  - Automated quality checks

## [1.1.9] - 2025-02-17 🚀 Feature Release

### New Features ✨
- **Location Analysis**: 
  - Advanced ambience analysis
  - Real-time traffic patterns
  - Environmental monitoring
  - Urban development tracking

- **Data Processing**: 
  - Enhanced image processing
  - Advanced vector handling
  - Improved data validation
  - Real-time updates

### Reliability Improvements 🛡️
- **Performance**: 
  - Optimized Redis integration
  - Improved memory management
  - Enhanced data cleanup
  - Better resource utilization

- **Error Handling**: 
  - Advanced error recovery
  - Network resilience
  - Improved logging
  - Better diagnostics

## [1.1.8] - 2025-02-16

### Changed
- Bumped version to 1.1.8 for maintenance release

## [1.1.7] - 2025-02-16

### Added
- Added matplotlib as a required core dependency for visualization support
- Ensured matplotlib is installed by default with the base package

### Fixed
- Fixed ModuleNotFoundError for matplotlib in core memory module
- Improved dependency management for visualization components
- Made matplotlib a compulsory dependency to prevent import errors

## [1.1.6] - 2025-02-16

### Added
- Added missing dependencies: netCDF4, python-multipart, pyjwt, folium, rtree
- Added new CUDA setup script for better GPU support
- Added comprehensive installation verification

### Changed
- Updated geopy version to 2.4.1
- Improved dependency management across Python versions
- Enhanced GPU installation process
- Updated documentation with clearer installation instructions

### Fixed
- Fixed version inconsistencies across configuration files
- Improved error handling in GPU setup
- Resolved package conflicts in Python 3.13

## [1.1.5] - 2025-02-16

### Changed
- Cleaned up dependency management
- Removed redundant and built-in Python modules from dependencies
- Standardized version constraints across Python versions
- Added missing dependencies for core functionality

### Fixed
- Removed duplicate package entries
- Fixed incorrect package specifications
- Ensured consistent dependency versions across Python versions
- Improved package compatibility across Python 3.9-3.13

## [1.1.4] - 2025-02-16

### Changed
- Updated text processing to use LangChain and model consistently
- Improved dependency management and version compatibility
- Enhanced error handling and logging

### Fixed
- Resolved remaining dependency conflicts
- Optimized memory usage in text processing
- Improved overall system stability

## [1.1.3] - 2025-02-16

### Added
- Added version-specific dependency management for Python 3.9-3.13
- Added `