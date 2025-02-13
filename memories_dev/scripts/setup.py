from setuptools import setup, find_packages

# Read requirements from file
with open('requirements.txt') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

# Define optional dependencies
extras_require = {
    'gpu': [
        'cupy-cuda11x>=12.0.0',
        'onnxruntime-gpu>=1.15.0',
        'tensorrt>=8.6.0',
        'triton>=2.0.0'
    ],
    'ml': [
        'torchvision>=0.15.0',
        'transformers>=4.30.0',
        'timm>=0.9.0',
        'segmentation-models-pytorch>=0.3.0',
        'accelerate>=0.24.0',
        'safetensors>=0.4.0'
    ],
    'synthetic': [
        'noise>=1.2.2',
        'opensimplex>=0.4',
        'perlin-noise>=1.12',
        'trimesh>=4.0.0',
        'pyrender>=0.1.45',
        'open3d>=0.17.0',
        'py6s>=1.9.0',
        'libradtran>=2.0.4'
    ],
    'viz': [
        'matplotlib>=3.7.0',
        'seaborn>=0.12.0',
        'plotly>=5.13.0',
        'folium>=0.14.0',
        'ipyleaflet>=0.17.0',
        'pyvista>=0.42.0',
        'meshio>=5.3.0'
    ],
    'monitoring': [
        'prometheus-client>=0.16.0',
        'grafana-api>=2.0.0',
        'wandb>=0.15.0',
        'mlflow>=2.7.0'
    ],
    'dev': [
        'pytest>=7.3.0',
        'pytest-cov>=4.0.0',
        'black>=23.3.0',
        'isort>=5.12.0',
        'flake8>=6.0.0',
        'mypy>=1.2.0',
        'pre-commit>=3.2.0'
    ],
    'docs': [
        'mkdocs>=1.4.0',
        'mkdocs-material>=9.1.0',
        'mkdocstrings>=0.20.0',
        'mkdocs-jupyter>=0.24.0'
    ]
}

# Add 'all' that includes all optional dependencies
extras_require['all'] = [pkg for group in extras_require.values() for pkg in group]

setup(
    name='memories_dev',
    version='0.1.0',
    author='Kumari Jaya',
    author_email='hello@memories-dev.com',
    description='High-performance geospatial processing engine with ML capabilities',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/vortx-ai/vortx',
    project_urls={
        'Documentation': 'https://vortx.ai/docs',
        'Bug Reports': 'https://github.com/vortx-ai/vortx/issues',
        'Source Code': 'https://github.com/vortx-ai/vortx',
    },
    packages=find_packages(exclude=['tests', 'tests.*', 'examples', 'docs']),
    install_requires=requirements,
    extras_require=extras_require,
    python_requires='>=3.9',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Scientific/Engineering :: GIS',
        'Topic :: Scientific/Engineering :: Image Processing',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
    ],
    entry_points={
        'console_scripts': [
            'vo=vortx.cli:main',
        ],
    },
    include_package_data=True,
    zip_safe=False,
) 