from setuptools import setup, find_packages
import sys

# Determine Python version and set appropriate dependencies
python_version = sys.version_info

def get_version_specific_deps():
    """Get version-specific dependencies based on Python version."""
    version = sys.version_info[:2]
    
    # Base dependencies common to all Python versions
    base_deps = [
        "numpy>=1.24.4,<2.0.0" if version < (3, 12) else "numpy>=1.26.0,<2.0.0",
        "pandas>=2.0.0" if version < (3, 12) else "pandas>=2.2.0",
        "matplotlib>=3.7.0" if version < (3, 12) else "matplotlib>=3.8.0",
        "ipywidgets>=8.0.0",
        "scikit-learn>=1.3.0",
        "rasterio>=1.3.8",
        "geopandas>=0.14.0",
        "albumentations>=1.3.1",
        "sentence-transformers>=2.2.0",
        "xarray>=2023.0.0",
        "dask>=2024.1.0",
        "accelerate>=1.3.0",
        "scipy>=1.11.0" if version < (3, 12) else "scipy>=1.12.0",
        "noise>=1.2.2",
        "faiss-cpu>=1.7.4"
    ]
    
    # Add version-specific constraints
    if version == (3, 9):
        base_deps.extend([
            "pandas<2.1.0",
            "matplotlib<3.8.0",
            "scikit-learn<1.4.0",
            "albumentations<1.4.0",
            "accelerate<1.4.0"
        ])
    
    # Add Python 3.13+ specific dependencies
    if version >= (3, 13):
        base_deps.append("shapely>=2.0.0")  # Modern Shapely for 3.13+
    
    return base_deps

def get_core_deps():
    """Get core dependencies with version-specific adjustments."""
    version = sys.version_info[:2]
    
    deps = [
        "transformers>=4.30.0",
        "pillow>=10.0.0",
        "requests>=2.31.0",
        "pyyaml>=6.0.1",
        "python-dotenv>=1.0.0",
        "tqdm>=4.65.0",
        "pyarrow>=14.0.1",
        "mercantile>=1.2.1",
        "pyproj>=3.6.1",
        "pystac>=1.8.0",
        "redis>=5.0.0",
        "nltk>=3.8.1",
        "diffusers>=0.25.0",
        "langchain>=0.1.0",
        "langchain-community>=0.0.1",
        "duckdb>=0.9.0",
        "geopy>=2.4.1",
        "folium>=0.15.1",
        "rtree>=1.1.0",
        "aiohttp>=3.9.0",
        "fsspec>=2024.2.0",
        "cryptography>=42.0.0",
        "pyjwt>=2.8.0",
        "pystac-client>=0.8.3",
        "planetary-computer>=1.0.0",
        "fastapi>=0.109.0",
        "netCDF4>=1.6.5",
        "earthengine-api>=0.1.390",
        "typing-extensions>=4.9.0",
        "pydantic>=2.6.0",
        "uvicorn>=0.27.0",
        "python-multipart>=0.0.9",
        "osmnx>=1.9.0",
        "py6s>=1.9.0",
        "opencv-python>=4.8.0",
        "matplotlib>=3.7.0"  # Required for visualization
    ]
    
    # Add version-specific core dependencies
    if version >= (3, 13):
        deps.extend([
            "mapbox-vector-tile>=2.0.1",  # Modern version compatible with Shapely 2.0+
            "shapely>=2.0.0,<3.0.0"  # Modern version for Python 3.13+
        ])
    else:
        deps.extend([
            "mapbox-vector-tile>=1.2.0,<2.0.0",  # Older version compatible with Shapely 1.x
            "shapely>=1.7.0,<2.0.0"  # Legacy version for older Python
        ])
    
    return deps

def get_gpu_packages():
    """Get GPU packages based on Python version and availability."""
    version = sys.version_info[:2]
    packages = ["cupy-cuda12x>=12.0.0"]  # Base GPU package
    
    # Only include faiss-gpu for compatible Python versions
    if version < (3, 12):  # faiss-gpu not yet available for 3.12+
        packages.append("faiss-gpu>=1.7.2")
    
    return packages

def get_torch_packages():
    """Get PyTorch related packages."""
    return [
        "torch>=2.2.0",
        "torchvision>=0.17.0",
        "torchaudio>=2.2.0"
    ]

def get_torch_geometric_packages():
    """Get PyTorch Geometric packages - these need to be installed separately after PyTorch."""
    return [
        "torch-scatter>=2.1.2",
        "torch-sparse>=0.6.18",
        "torch-cluster>=1.6.3",
        "torch-geometric>=2.4.0"
    ]

# Get all dependencies
install_requires = get_core_deps() + get_version_specific_deps()

setup(
    name="memories-dev",
    version="1.1.8",
    packages=find_packages(include=['memories', 'memories.*']),
    
    author="Memories-dev",
    author_email="hello@memories.dev",
    description="A Python package for managing and processing earth observation data",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://memories.dev",
    license="Apache License 2.0",
    
    install_requires=install_requires,
    
    extras_require={
        "gpu": get_gpu_packages(),
        "torch": get_torch_packages(),
        "torch-geometric": get_torch_geometric_packages(),  # Separate extra for PyG packages
        "dev": [
            "pytest>=8.3.4",
            "pytest-asyncio>=0.23.5",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.12.0",
            "pytest-xdist>=3.5.0",
            "pytest-benchmark>=4.0.0",
            "pytest-timeout>=2.2.0",
            "black>=24.1.0",
            "flake8>=7.0.0",
            "mypy>=1.8.0",
            "isort>=5.13.0",
            "pre-commit>=3.6.0"
        ],
        "docs": [
            "sphinx>=7.2.0",
            "sphinx-rtd-theme>=2.0.0",
            "sphinx-autodoc-typehints>=2.0.0",
            "nbsphinx>=0.9.0",
            "pandoc>=2.3",
            "sphinx-copybutton>=0.5.2",
            "myst-parser>=0.18.1"
        ]
    },
    
    python_requires=">=3.9,<3.14.0",
    
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: GIS",
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Developers",
        "Natural Language :: English"
    ],
    
    entry_points={
        "console_scripts": [
            "memories=memories.cli:main",
            "memories-gpu-setup=install_gpu:install_gpu_dependencies",
            "memories-cuda-setup=cuda_setup:install_cuda_packages"
        ]
    },
    
    package_data={
        "memories": [
            "config/*.yaml",
            "data/*.json",
            "models/config/*.json",
            "utils/styles/*.json"
        ]
    },
    
    include_package_data=True,
    zip_safe=False,
    
    project_urls={
        "Homepage": "https://memories.dev",
        "Documentation": "https://docs.memories.dev",
        "Repository": "https://github.com/Vortx-AI/memories-dev.git",
        "Issues": "https://github.com/Vortx-AI/memories-dev/issues",
        "Changelog": "https://github.com/Vortx-AI/memories-dev/blob/main/CHANGELOG.md"
    }
) 
