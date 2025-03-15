Changelog
=========

All notable changes to this project will be documented in this file.

[1.1.8] - 2025-02-16
--------------------

Changed
~~~~~~~
- Bumped version to 1.1.8 for maintenance release

[1.1.7] - 2025-02-16
--------------------

Added
~~~~~
- Added matplotlib as a required core dependency for visualization support
- Ensured matplotlib is installed by default with the base package

Fixed
~~~~~
- Fixed ModuleNotFoundError for matplotlib in core memory module
- Improved dependency management for visualization components
- Made matplotlib a compulsory dependency to prevent import errors

[1.1.6] - 2025-02-16
--------------------

Added
~~~~~
- Added missing dependencies: netCDF4, python-multipart, pyjwt, folium, rtree
- Added new CUDA setup script for better GPU support
- Added comprehensive installation verification

Changed
~~~~~~~
- Updated geopy version to 2.4.1
- Improved dependency management across Python versions
- Enhanced GPU installation process
- Updated documentation with clearer installation instructions

Fixed
~~~~~
- Fixed version inconsistencies across configuration files
- Improved error handling in GPU setup
- Resolved package conflicts in Python 3.13

For a complete list of changes, please visit our `GitHub releases page <https://github.com/Vortx-AI/memories-dev/releases>`_.

Version 2.0.6 (March 13, 2025)
---------------------------------

Added
~~~~~
- Added default configuration file for GlacierMemory

Fixed
~~~~~
- Updated GlacierMemory to accept config_path parameter for better compatibility with tests

Version 2.0.5 (March 7, 2025)
----------------------------

Added
~~~~~

**Schema Management**

* Enhanced schema transfer from cold to red hot memory
* Added schema embeddings for semantic column search
* Improved metadata extraction and storage for parquet files

**System Improvements**

* Added dependency version checks and compatibility validation
* Improved temporary directory handling and cleanup
* Enhanced DuckDB lock management and release mechanisms
* Better error handling and logging across core functions
* Added fallback configuration handling for test environments

**Memory Optimization**

* Optimized parquet file handling to reduce disk space usage
* Improved batch processing for large datasets
* Enhanced memory cleanup routines

**Testing Improvements**

* Enhanced test suite with better mocking and fixtures
* Added conditional test skipping for optional dependencies
* Improved documentation testing with mock imports
* Added comprehensive API connector tests
* Enhanced geospatial data testing
* Added test environment configuration handling

**API Connectors**

* Added robust error handling for OpenAI API
* Enhanced Deepseek API integration
* Improved API key management from environment variables
* Added comprehensive logging for API interactions
* Enhanced chat completion functionality

**New Examples**

* Added Real Estate Agent example for property analysis with earth memory integration
* Added Property Analyzer for comprehensive property and environmental analysis
* Added Multimodal AI Assistant for processing text, images, and geospatial data
* Added Code Intelligence Agent for code analysis and understanding
* Added LLM Training Optimizer for improving model training
* Added Ambience Analyzer for environmental context understanding

Fixed
~~~~~

**Test Suite Fixes**

* Fixed TypeError in batch parquet import tests related to 'enable_red_hot' parameter
* Resolved multiple TypeErrors in memory retrieval tests related to 'vector_encoder' parameter
* Fixed geospatial data querying test failures
* Updated test suite to match new API parameters

**Memory System Fixes**

* Fixed memory leaks in long-running processes
* Resolved race conditions in concurrent memory access
* Fixed issues with memory persistence across sessions
* Improved error handling for failed memory operations

**API Integration Fixes**

* Fixed authentication issues with external APIs
* Resolved timeout handling in API requests
* Improved error reporting for failed API calls

**Documentation Fixes**

* Updated code examples to match current API
* Fixed broken links and references
* Improved clarity of installation instructions
* Enhanced API documentation with more examples

[2.0.5] - 2025-03-07
--------------------

Added
~~~~~
- Added new features and improvements as described in the changelog

Changed
~~~~~~~
- Updated geopy version to 2.4.1
- Improved dependency management across Python versions
- Enhanced GPU installation process
- Updated documentation with clearer installation instructions

Fixed
~~~~~
- Fixed version inconsistencies across configuration files
- Improved error handling in GPU setup
- Resolved package conflicts in Python 3.13

For a complete list of changes, please visit our `GitHub releases page <https://github.com/Vortx-AI/memories-dev/releases>`_.

Version 2.0.7 (March 14, 2025)
-----------------------------

Added
~~~~~

**Memory Tiering**

* Added direct file storage capability for Glacier to Cold transfers
* Implemented ``store_file`` method in ``ColdMemory`` class for binary data storage
* Added ``glacier_to_cold_file`` method to preserve binary file formats
* Enhanced metadata handling for file-based storage
* Improved error handling for binary data transfers

**Scripts & Utilities**

* Added ``tier_file_data.py`` script for transferring files from Glacier to Cold
* Added ``list_cold_files.py`` for listing files stored in Cold storage
* Added ``extract_cold_file.py`` for retrieving files from Cold storage
* Improved file path handling and validation
* Enhanced file metadata recording and retrieval

Enhanced
~~~~~~~~

**Cold Storage**

* Improved binary data handling in Cold storage
* Added support for preserving file formats without encoding
* Enhanced file registration in memory catalog
* Added better file path management and timestamp-based naming
* Improved error reporting for storage operations

**Glacier Integration**

* Enhanced retrieval of binary data from Glacier storage
* Improved file format detection and handling
* Better error handling for large file transfers
* Added support for custom filenames during transfers

Fixed
~~~~~

* Fixed data transfer issue when moving binary data from Glacier to Cold storage
* Resolved issue with non-existent ``store_raw`` method in ``ColdMemory`` class
* Improved handling of different data types during tier transfers
* Enhanced base64 encoding for binary data that needs database storage
* Fixed parameter handling in ``ColdMemory.store`` method calls

[1.1.8] - 2025-02-16
--------------------

Changed
~~~~~~~
- Bumped version to 1.1.8 for maintenance release

[1.1.7] - 2025-02-16
--------------------

Added
~~~~~
- Added matplotlib as a required core dependency for visualization support
- Ensured matplotlib is installed by default with the base package

Fixed
~~~~~
- Fixed ModuleNotFoundError for matplotlib in core memory module
- Improved dependency management for visualization components
- Made matplotlib a compulsory dependency to prevent import errors

[1.1.6] - 2025-02-16
--------------------

Added
~~~~~
- Added missing dependencies: netCDF4, python-multipart, pyjwt, folium, rtree
- Added new CUDA setup script for better GPU support
- Added comprehensive installation verification

Changed
~~~~~~~
- Updated geopy version to 2.4.1
- Improved dependency management across Python versions
- Enhanced GPU installation process
- Updated documentation with clearer installation instructions

Fixed
~~~~~
- Fixed version inconsistencies across configuration files
- Improved error handling in GPU setup
- Resolved package conflicts in Python 3.13

For a complete list of changes, please visit our `GitHub releases page <https://github.com/Vortx-AI/memories-dev/releases>`_. 