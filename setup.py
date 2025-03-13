#!/usr/bin/env python
"""Setup script for memories-dev."""
import os
import sys
from setuptools import setup, find_packages

# Check if we should disable diffusers
DISABLE_DIFFUSERS = os.environ.get('DISABLE_DIFFUSERS', '0') == '1'

# Base requirements
install_requires = [
    'numpy>=1.20.0',
    'pandas>=1.3.0',
    'pyyaml>=6.0',
    'requests>=2.25.0',
    'tqdm>=4.62.0',
    'pillow>=9.0.0',
    'python-dotenv>=0.19.0',
]

# Only add diffusers if not disabled
if not DISABLE_DIFFUSERS:
    install_requires.append('diffusers>=0.25.0')

# Extra requirements
extras_require = {
    'dev': [
        'pytest>=7.0.0',
        'pytest-cov>=3.0.0',
        'black>=22.3.0',
        'isort>=5.10.0',
        'flake8>=4.0.0',
        'mypy>=0.950',
    ],
    'docs': [
        'sphinx>=7.1.2',
        'sphinx-rtd-theme>=1.3.0',
        'sphinx-copybutton>=0.5.0',
        'sphinx-design>=0.5.0',
        'sphinx-autodoc-typehints>=1.25.0',
        'sphinx-tabs==3.4.1',
        'sphinx-favicon>=1.0.1',
        'sphinx-sitemap>=2.5.1',
        'sphinx-last-updated-by-git>=0.3.5',
        'sphinxcontrib-mermaid==0.9.2',
        'sphinx-math-dollar>=1.2.1',
        'myst-parser>=2.0.0',
        'nbsphinx>=0.9.3',
    ],
    's3': [
        'boto3>=1.28.0',
    ],
    'gcs': [
        'google-cloud-storage>=2.9.0',
    ],
    'azure': [
        'azure-storage-blob>=12.16.0',
    ]
}

setup(
    name='memories-dev',
    version='2.0.6',
    description='Earth-grounded AI memory systems',
    author='Memories-dev',
    author_email='info@memories-dev.org',
    url='https://github.com/Vortx-AI/memories-dev',
    packages=find_packages(exclude=['tests', 'tests.*']),
    install_requires=install_requires,
    extras_require=extras_require,
    python_requires='>=3.9',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
    ],
) 
