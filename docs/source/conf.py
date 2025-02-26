# Configuration file for the Sphinx documentation builder.
import os
import sys
import platform
from packaging import version as packaging_version
import sphinx

sys.path.insert(0, os.path.abspath('../..'))

# Project information
project = 'memories-dev'
copyright = '2025, Memories-dev'
author = 'Memories-dev'
# The short X.Y version
version = '2.0.2'
# The full version, including alpha/beta/rc tags
release = '2.0.2'

# Add any Sphinx extension module names here
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.githubpages',
    'sphinx_rtd_theme',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.mathjax',
    'sphinx.ext.ifconfig',
    'sphinx.ext.autosummary',
    'nbsphinx',
    'sphinx_copybutton',
    'myst_parser',
    'sphinxcontrib.mermaid'
]

# Add enhanced extensions for better documentation
extensions += [
    'sphinx_design',           # Enhanced UI components
    'sphinx_tabs.tabs',        # Tabbed content
    'sphinx_togglebutton',     # Toggle buttons
    'sphinx_favicon',          # Multiple favicons
    'sphinx.ext.duration',     # Build duration tracking
    'sphinx_sitemap',          # Sitemap generation
    'sphinx_last_updated_by_git', # Last updated date from git
]

# Handle type hints based on Python version
python_version = packaging_version.parse(platform.python_version())
sphinx_version = packaging_version.parse(sphinx.__version__)

# Configure type hints based on Python version
if python_version >= packaging_version.parse('3.13'):
    autodoc_typehints = 'none'  # Disable automatic type hints processing
    autodoc_typehints_format = 'fully-qualified'
    napoleon_use_param = True
    napoleon_use_rtype = True
    napoleon_preprocess_types = True
    napoleon_type_aliases = None
elif python_version >= packaging_version.parse('3.12'):
    extensions.append('sphinx_autodoc_typehints')
    autodoc_typehints = 'description'
    autodoc_typehints_format = 'short'
    autodoc_type_aliases = {}
else:
    autodoc_typehints = 'none'

# Add any paths that contain templates here
templates_path = ['_templates']

# These paths are either relative to html_static_path or fully qualified paths (eg. https://...)
html_css_files = [
    'custom.css',
    'code-highlight.css',
    'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap',
]

html_js_files = [
    'https://buttons.github.io/buttons.js',
    'custom.js',
]

# The suffix of source filenames
source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

# The master toctree document
master_doc = 'index'
root_doc = 'index'

# List of patterns to exclude
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', '**.ipynb_checkpoints']

# The theme to use for HTML and HTML Help pages
html_theme = 'sphinx_rtd_theme'

# Add any paths that contain custom static files
html_static_path = ['_static']

# Theme options
html_theme_options = {
    'logo_only': False,
    'display_version': True,
    'prev_next_buttons_location': 'both',
    'style_external_links': True,
    'style_nav_header_background': '#2c3e50',
    'collapse_navigation': False,
    'sticky_navigation': True,
    'navigation_depth': 4,
    'includehidden': True,
    'titles_only': False
}

# Enhanced theme options
html_theme_options.update({
    'style_nav_header_background': '#0f172a',  # Darker blue
    'body_max_width': '1200px',
    'navigation_with_keys': True,
    'logo_only': True,
    'display_version': True,
})

# Base URL for the docs
html_baseurl = 'https://memories-dev.readthedocs.io/'

# HTML context
html_context = {
    'display_github': True,
    'github_user': 'Vortx-AI',
    'github_repo': 'memories-dev',
    'github_version': 'main',
    'conf_py_path': '/docs/source/',
}

# Mermaid configuration
mermaid_params = [
    '--theme', 'dark',
    '--securityLevel', 'loose',
    '--startOnLoad', 'true',
]

# MyST settings
myst_enable_extensions = [
    'amsmath',
    'colon_fence',
    'deflist',
    'dollarmath',
    'html_admonition',
    'html_image',
    'replacements',
    'smartquotes',
    'substitution',
    'tasklist',
]

# Add any extra paths that contain custom files
html_extra_path = ['robots.txt']

# Output file base name for HTML help builder
htmlhelp_basename = 'memories-dev-doc'

# Sitemap configuration
sitemap_url_scheme = "{link}"
sitemap_filename = "sitemap.xml"

# Last updated configuration
html_last_updated_fmt = "%b %d, %Y"

# Search configuration
search_language = "en"

# Mock imports for documentation build
autodoc_mock_imports = [
    "cudf",
    "cuspatial",
    "faiss",
    "torch",
    "transformers",
    "numpy",
    "pandas",
    "matplotlib",
    "PIL",
    "requests",
    "yaml",
    "dotenv",
    "tqdm",
    "pyarrow",
    "nltk",
    "langchain",
    "pydantic",
    "shapely",
    "geopandas",
    "rasterio",
    "pyproj",
    "pystac",
    "mercantile",
    "folium",
    "rtree",
    "geopy",
    "osmnx",
    "py6s",
    "redis",
    "xarray",
    "dask",
    "aiohttp",
    "memories",  # Mock the memories package itself
] 