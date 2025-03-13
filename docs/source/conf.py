# Import pre-import configuration before anything else
try:
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from conf_pre_import import *
    print("Successfully imported pre-import configuration")
except Exception as e:
    print(f"Warning: Could not import pre-import configuration: {e}")

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
import platform
from packaging import version as packaging_version
import sphinx
import sphinx_rtd_theme

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath('../..'))

# Import configuration overrides for handling problematic dependencies
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from _conf_overrides import *
    print("Successfully imported configuration overrides")
except Exception as e:
    print(f"Warning: Could not import configuration overrides: {e}")

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'memories-dev'
copyright = '2025, Memories-dev'
author = 'Memories-dev'
# The short X.Y version
version = '2.0.6'
# The full version, including alpha/beta/rc tags
release = '2.0.6'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

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
    autodoc_typehints = 'description'
    autodoc_typehints_format = 'short'
    autodoc_type_aliases = {}
else:
    autodoc_typehints = 'none'

# Define mandatory extensions that should always be included
mandatory_extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
    'sphinx.ext.autosectionlabel',
    'sphinx_rtd_theme',
]

# Define optional extensions that could potentially fail
optional_extensions = [
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.mathjax',
    'sphinx.ext.ifconfig',
    'sphinx.ext.githubpages',
    'sphinx_copybutton',
    'sphinx_tabs.tabs',
    'sphinxcontrib.mermaid',
    'sphinx_math_dollar',
    'sphinx.ext.autosummary',
    'nbsphinx',
    'myst_parser',
]

# Initialize extensions list with mandatory extensions
extensions = mandatory_extensions.copy()

# Try to add optional extensions
for ext in optional_extensions:
    try:
        __import__(ext.split('.')[0])
        extensions.append(ext)
        print(f"Added extension: {ext}")
    except (ImportError, ModuleNotFoundError) as e:
        print(f"Warning: Could not import extension {ext}: {e}")

# Make section labels unique by prefixing them with document name
autosectionlabel_prefix_document = True
autosectionlabel_maxdepth = 2

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', '**.ipynb_checkpoints']

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_logo = '_static/logo-simple.svg'
html_favicon = '_static/favicon.ico'

# -- Extension configuration -------------------------------------------------

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

# Intersphinx settings
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
    'pandas': ('https://pandas.pydata.org/docs/', None),
    'torch': ('https://pytorch.org/docs/stable/', None),
}

# AutoDoc settings
autodoc_member_order = 'bysource'
autodoc_typehints = autodoc_typehints
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__',
    'show-inheritance': True
}

# Math settings
math_number_all = False
math_eqref_format = "Eq.{number}"
math_numfig = True

# Mermaid settings
mermaid_params = {
    'theme': 'default',
}

# Copy button settings
copybutton_prompt_text = r">>> |\.\.\. |\$ |In \[\d*\]: | {2,5}\.\.\.: | {5,8}: "
copybutton_prompt_is_regexp = True
copybutton_only_copy_prompt_lines = True
copybutton_remove_prompts = True

# -- Additional configuration ------------------------------------------------

# MathJax 3 configuration
mathjax_path = 'https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js'
mathjax3_config = {
    'tex': {
        'inlineMath': [['$', '$'], ['\\(', '\\)']],
        'displayMath': [['$$', '$$'], ['\\[', '\\]']],
        'processEscapes': True,
        'processEnvironments': True,
    },
    'options': {
        'ignoreHtmlClass': 'tex2jax_ignore',
        'processHtmlClass': 'tex2jax_process',
    },
    'chtml': {
        'scale': 1.1
    }
}

# Enable mermaid diagrams
mermaid_version = "10.6.1"
mermaid_init_js = """
    mermaid.initialize({
        startOnLoad: true,
        theme: 'neutral',
        securityLevel: 'loose',
        flowchart: {
            useMaxWidth: true,
            htmlLabels: true,
            curve: 'basis'
        },
        sequence: {
            diagramMarginX: 50,
            diagramMarginY: 10,
            actorMargin: 50,
            width: 150,
            height: 65
        },
        gantt: {
            titleTopMargin: 25,
            barHeight: 20,
            barGap: 4,
            topPadding: 50,
            leftPadding: 75
        }
    });
"""

def setup(app):
    # Add critical fixes CSS
    app.add_css_file('css/fixes.css')
    
    # Add book-style CSS
    app.add_css_file('css/book_style.css')
    
    # Add ReadTheDocs-specific fixes
    app.add_css_file('css/readthedocs-fixes.css')
    
    # Add SVG-specific fixes
    app.add_css_file('css/svg-fixes.css')
    
    # Add web fonts
    app.add_css_file('https://fonts.googleapis.com/css2?family=Georgia:ital,wght@0,400;0,700;1,400;1,700&display=swap')
    app.add_css_file('https://fonts.googleapis.com/css2?family=Source+Code+Pro:wght@400;600&display=swap')
    
    # Add polyfills for older browsers
    app.add_js_file('js/polyfills.js', priority=50)
    
    # Add Mermaid library
    app.add_js_file('https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.min.js', priority=200)
    
    # Add custom Mermaid initialization
    app.add_js_file('js/mermaid.js', priority=201)
    
    # Add mobile navigation script
    app.add_js_file('js/mobile-nav.js', priority=100)
    
    return {
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }

# These paths are either relative to html_static_path or fully qualified paths (eg. https://...)
html_css_files = [
    # CSS files are now added in the setup function to avoid duplication
]

html_js_files = [
    'https://buttons.github.io/buttons.js',
    # JS files are now added in the setup function to avoid duplication
]

# The suffix of source filenames
source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

# The master toctree document
master_doc = 'index'
root_doc = 'index'

# Theme options
html_theme_options = {
    'logo_only': True,
    'display_version': True,
    'prev_next_buttons_location': 'bottom',
    'style_external_links': True,
    'style_nav_header_background': '#1a2638',
    'collapse_navigation': True,
    'sticky_navigation': True,
    'navigation_depth': 4,
    'includehidden': True,
    'titles_only': False,
    'canonical_url': '',
    'analytics_id': '',
    'analytics_anonymize_ip': False,
    'vcs_pageview_mode': '',
}

# HTML context
html_context = {
    'display_github': True,
    'github_user': 'Vortx-AI',
    'github_repo': 'memories-dev',
    'github_version': 'main',
    'conf_py_path': '/docs/source/',
    'READTHEDOCS': True,
    'using_theme': 'sphinx_rtd_theme',
    'html_theme': 'sphinx_rtd_theme',
    'current_version': '2.0.6',
    'version': '2.0.6',
    'build_id': '2025-03-11',
    'build_url': 'https://readthedocs.org/projects/memories-dev/builds/',
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

# Autodoc settings
autodoc_class_signature = 'separated'
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