# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.8] - 2025-02-16

### Changed
- Updated Python version requirement to exclude 3.13 temporarily
- Added build requirements for better compatibility
- Updated blis dependency to version 0.7.11 for compatibility
- Updated thinc and spacy dependencies

### Fixed
- Compilation issues with Python 3.13's C API
- Build system configuration for better cross-version support
- Package dependency resolution issues with blis

## [1.0.7] - 2025-02-16

### Changed
- Updated dependency versions for better Python 3.13 compatibility
- Pinned blis version to 0.7.12 to resolve build issues with Python 3.13
- Fixed deprecated Py_UNICODE warnings and missing function declarations
- Added explicit Python version requirement (<3.13) due to C API changes
- Added Cython>=3.0.8 as build requirement for better compatibility

### Fixed
- Build issues with Python 3.13's C API changes
- Missing function declarations in blis compilation

## [1.0.6] - 2025-02-16

### Fixed
- Added redis dependency to buildtestrequirements.txt
- Fixed Python 3.13 compatibility issues with thinc and spacy
- Pinned thinc and spacy versions for better stability

## [1.0.5] - 2025-02-16

### Added
- Comprehensive .gitignore file
- Installation verification tests
- CLI functionality with basic commands
- Detailed installation guide (INSTALL.md)

### Changed
- Updated package configuration to ensure proper naming (memories-dev on PyPI, memories for imports)
- Improved project structure with proper __init__.py files
- Enhanced documentation with clearer installation instructions

## [1.0.4] - 2025-02-15

### Changed
- Renamed `memories.memories` module to `memories.core` for better code organization
- Updated all import references to use the new module structure
- Fixed import paths in agent and memory modules

### Fixed
- Import path issues in various modules
- Module structure to be more intuitive

## [1.0.3] - 2025-02-14

### Added
- Initial public release
- Core memory functionality
- Earth observation capabilities
- Agent system for memory processing
- GPU acceleration support
- Documentation and examples 
