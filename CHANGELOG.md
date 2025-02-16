# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

### Fixed
- Various bug fixes
- Performance optimizations

## [1.0.3] - 2025-02-14

### Added
- Initial stable release
- Core memory functionality
- Basic text processing
- Geographic data handling 
