# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-02-18

### Major Changes
- Bumped version to 2.0.0 to reflect significant maturity and stability of the project
- All existing functionality from 1.1.9 maintained

## [1.1.9] - 2025-02-17

### Added
- New example applications: Location Ambience Analyzer and Traffic Analyzer
- Enhanced documentation with detailed examples and usage patterns
- Added new utility processors for image and vector data

### Fixed
- Improved Redis data handling in hot memory implementation
- Fixed data structure validation in memory storage
- Enhanced error handling and logging in data retrieval operations

### Changed
- Updated test suite with comprehensive coverage for new features
- Improved memory cleanup in test environments
- Enhanced data validation in memory storage operations

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
- Updated text processing to use LangChain and DeepSeek consistently
- Improved dependency management and version compatibility
- Enhanced error handling and logging

### Fixed
- Resolved remaining dependency conflicts
- Optimized memory usage in text processing
- Improved overall system stability

## [1.1.3] - 2025-02-16

### Added
- Added version-specific dependency management for Python 3.9-3.13
- Added `diffusers>=0.25.0` to core dependencies
- Enhanced version compatibility across different Python versions
- Added LangChain and DeepSeek for advanced text processing

### Changed
- Reorganized dependencies into core and version-specific groups
- Updated dependency version constraints for better compatibility
- Improved Python version-specific package management
- Pinned numpy to 1.26.x for Python 3.12 to ensure binary compatibility
- Removed spacy/thinc dependencies for better compatibility
- Updated text processing to use LangChain and DeepSeek

### Fixed
- Fixed dependency conflicts between different Python versions
- Optimized package requirements for each Python version
- Improved installation process across different Python environments
- Fixed numpy binary incompatibility issues in Python 3.12
- Maintained consistent text processing across all versions

## [1.1.2] - 2025-02-16

### Added
- Updated Python version support to include Python 3.13

### Changed
- Improved error handling in text processing
- Enhanced memory management for large datasets
- Updated documentation for new features

## [1.1.1] - 2025-02-16

### Changed
- Upgraded numpy to >=2.2.3 for better Python 3.13 compatibility
- Replaced spacy, thinc, and blis dependencies with nltk>=3.8.1 for better Python 3.13 compatibility

### Fixed
- Resolved installation issues on Python 3.13
- Fixed package version conflicts and compilation issues

## [1.1.0] - 2025-02-16

### Added
- New memory indexing system
- Enhanced text processing capabilities
- Improved geographic data handling

### Changed
- Updated Python version requirement to exclude 3.13 temporarily
- Fixed blis version to 0.7.11
- Updated thinc dependency to 8.1.10 for better compatibility
- Pinned numpy to 1.24.3 for binary compatibility
- Updated spacy to >=3.7.0,<3.8.0

### Fixed
- Memory leaks in long-running processes
- Build system configuration for better cross-version support
- Various performance issues
- Fixed incorrect blis version reference causing installation failures

## [1.0.9] - 2025-02-16

### Added
- Support for custom memory backends
- Enhanced error reporting

### Fixed
- Various compatibility issues with newer Python versions
- Performance improvements for large datasets

## [1.0.8] - 2025-02-16

### Changed
- Updated dependency versions for better Python 3.13 compatibility
- Pinned blis version to 0.7.12 to resolve build issues with Python 3.13

### Fixed
- Added explicit Python version requirement (<3.13) due to C API changes
- Added Cython>=3.0.8 as build requirement for better compatibility
- Various bug fixes and performance improvements

### Security
- Updated dependencies to address security vulnerabilities

## [1.0.6] - 2025-02-16

### Added
- New memory optimization features

### Fixed
- Pinned thinc and spacy versions for better stability

## [1.0.5] - 2025-02-16

### Added
- Enhanced memory management system
- Improved error handling
- Better documentation

### Fixed
- Various bug fixes
- Performance improvements
- Documentation updates

## [1.0.4] - 2025-02-15

### Added
- Memory persistence improvements
- Better error messages
- Enhanced documentation
S
### Fixed
- Various bug fixes
- Performance optimizations

## [1.0.3] - 2025-02-14

### Added
- Initial stable release
- Core memory functionality
- Basic text processing
- Geographic data handling 
