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
version = '2.0.1'
# The full version, including alpha/beta/rc tags
release = '2.0.1'

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
    'myst_parser'
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
]

html_js_files = [
    'https://buttons.github.io/buttons.js',
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
    'titles_only': False,
    'analytics_id': 'UA-XXXXXXXX-1',  # Replace with your Google Analytics ID
}

# HTML context
html_context = {
    'display_github': True,
    'github_user': 'Vortx-AI',
    'github_repo': 'memories-dev',
    'github_version': 'main',
    'conf_py_path': '/docs/source/',
}

# Custom sidebar templates
html_sidebars = {
    '**': [
        'globaltoc.html',
        'relations.html',
        'sourcelink.html',
        'searchbox.html',
    ]
}

# Intersphinx configuration
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
    'pandas': ('https://pandas.pydata.org/docs/', None),
    'torch': ('https://pytorch.org/docs/stable/', None),
}

# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = True
napoleon_use_ivar = False
napoleon_attr_annotations = True

# Autodoc settings
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__',
    'show-inheritance': True
}

autodoc_class_signature = 'separated'
autodoc_member_order = 'bysource'
autodoc_warningiserror = False

# NotFound page settings
notfound_context = {
    'title': 'Page Not Found',
    'body': '''
        <h1>Page Not Found</h1>
        <p>Sorry, we couldn't find that page. Try using the navigation or search box.</p>
    '''
}
notfound_no_urls_prefix = True
notfound_template = '404.html'

# Enable todo items
todo_include_todos = True
todo_emit_warnings = True
todo_link_only = False

# HoverXRef settings
hoverxref_auto_ref = True
hoverxref_domains = ['py']
hoverxref_roles = [
    'ref',
    'doc',
]
hoverxref_role_types = {
    'ref': 'tooltip',
    'doc': 'tooltip',
    'class': 'tooltip',
    'func': 'tooltip',
    'meth': 'tooltip',
}

# Copy button settings
copybutton_prompt_text = r">>> |\.\.\. |\$ |In \[\d*\]: | {2,5}\.\.\.: | {5,8}: "
copybutton_prompt_is_regexp = True
copybutton_only_copy_prompt_lines = True
copybutton_remove_prompts = True

# Mermaid settings
mermaid_params = {
    'theme': 'default',
}

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
    "fsspec",
    "cryptography",
    "pyjwt",
    "fastapi",
    "netCDF4",
    "earthengine",
    "sentinelhub",
    "sentence_transformers"
] 