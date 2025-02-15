from setuptools import setup, find_packages

setup(
    name="memories-dev",
    version="1.0.8",
    packages=find_packages(include=['memories', 'memories.*']),
    
    author="Memories-dev",
    author_email="hello@memories-dev.com",
    description="An awesome package for daily synthesis of Earth Memories, helping agents answer about location-first queries. ",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Vortx-AI/memories-dev",
    license="Apache License 2.0",
    
    install_requires=[
        "torch>=2.0.0",
        "transformers>=4.30.0",
        "accelerate>=1.3.0",
        "pillow>=10.0.0",
        "numpy>=1.24.0",
        "pandas>=2.0.0",
        "duckdb>=0.9.0",
        "matplotlib>=3.7.0",
        "ipywidgets>=8.0.0",
        "pyarrow>=14.0.1",
        "tqdm>=4.65.0",
        "requests>=2.31.0",
        "pyyaml>=6.0.1",
        "scikit-learn>=1.3.0",
        "rasterio>=1.3.8",
        "geopandas>=0.14.0",
        "shapely>=2.0.0",
        "opencv-python>=4.8.0",
        "albumentations>=1.3.1",
        "python-dotenv>=1.0.0",
        "langchain>=0.1.0",
        "langchain-community>=0.0.1",
        "geopy>=2.3.0",
        "faiss-cpu>=1.7.4",
        "sentence-transformers>=2.2.0",
        "mercantile>=1.2.1",
        "mapbox-vector-tile>=2.0.1",
        "pyproj>=3.6.1",
        "pystac>=1.8.0",
        "xarray>=2023.0.0",
        "dask>=2024.1.0",
        "dask[array]>=2024.1.0",
        "spacy==3.7.4",
        "thinc==8.2.2",
        "blis==0.7.11",
        "redis>=5.0.0",
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
        "pre-commit>=3.6.0",
        "sphinx>=7.2.0",
        "sphinx-rtd-theme>=2.0.0",
        "sphinx-autodoc-typehints>=2.0.0",
        "nbsphinx>=0.9.0",
        "pandoc>=2.3"
    ],
    
    extras_require={
        "gpu": [
            "faiss-gpu>=1.7.4",
            "cupy-cuda12x>=12.0.0",
            "cudf>=24.2.0",
            "cuspatial>=24.2.0"
        ],
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
            "pandoc>=2.3"
        ]
    },
    
    python_requires=">=3.9,<3.13",
    
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: GIS",
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Developers",
        "Natural Language :: English"
    ],
    
    entry_points={
        "console_scripts": [
            "memories=memories.cli:main"
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
        "Homepage": "https://github.com/Vortx-AI/memories-dev",
        "Documentation": "https://docs.memories-dev.dev",
        "Repository": "https://github.com/Vortx-AI/memories-dev.git",
        "Issues": "https://github.com/Vortx-AI/memories-dev/issues",
        "Changelog": "https://github.com/Vortx-AI/memories-dev/blob/main/CHANGELOG.md"
    }
) 
