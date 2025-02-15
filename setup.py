from setuptools import setup, find_packages

setup(
    name="memories",
    version="0.1.0",
    packages=find_packages(),
    
    author="Memories-dev",
    author_email="hello@memories-dev.com",
    description="An awesome package for daily synthesis of Earth Memories, helping agents answer about location-first queries. ",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Vortx-AI/memories_dev",
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
        "pyproj>=3.6.1"
    ],
    
    extras_require={
        "gpu": ["faiss-gpu>=1.7.4"],
        "dev": ["pytest>=6.0"],
        "docs": ["sphinx>=4.0.0"]
    },
    
    python_requires=">=3.8",
    
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: GIS"
    ],
    
    entry_points={
        "console_scripts": [
            "vortx=vortx.cli:main"
        ]
    },
    
    package_data={
        "memories": [
            "config/*.yaml",
            "data/*.json"
        ]
    },
    
    include_package_data=True
) 
