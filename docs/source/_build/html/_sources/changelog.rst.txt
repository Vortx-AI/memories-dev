Changelog
=========

All notable changes to this project will be documented in this file.

[1.1.8] - 2025-02-16
------------------

Changed
~~~~~~~
- Bumped version to 1.1.8 for maintenance release

[1.1.7] - 2025-02-16
------------------

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
------------------

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