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

# The master toctree document
master_doc = 'index'
root_doc = 'index'

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
    'sphinxcontrib.mermaid',
    'sphinx_design',           # Enhanced UI components
    'sphinx_tabs.tabs',        # Tabbed content
    'sphinx_togglebutton',     # Toggle buttons
    'sphinx_favicon',          # Multiple favicons
    'sphinx.ext.duration',     # Build duration tracking
    'sphinx_sitemap',          # Sitemap generation
    'sphinx_last_updated_by_git', # Last updated date from git
]

# LaTeX configuration for PDF output
latex_documents = [
    (master_doc, 'memories-dev.tex', 'Memories-Dev Documentation',
     'Memories-Dev', 'manual', True)
]

latex_elements = {
    'papersize': 'a4paper',
    'pointsize': '11pt',
    'figure_align': 'htbp',
    'fontpkg': r'''
        \usepackage{helvet}
        \usepackage[scaled]{beramono}
        \usepackage{inconsolata}
        \renewcommand{\familydefault}{\sfdefault}
    ''',
    'preamble': r'''
        \usepackage{graphicx}
        \usepackage{xcolor}
        \usepackage{fancyhdr}
        \usepackage{hyperref}
        \usepackage{multicol}
        \usepackage{amsmath}
        \usepackage{amssymb}
        \usepackage{enumitem}
        \usepackage{adjustbox}
        \usepackage{longtable}
        \usepackage{tabulary}
        \usepackage{booktabs}
        
        % Define company colors
        \definecolor{primary}{RGB}{15, 23, 42}  % Dark blue
        \definecolor{secondary}{RGB}{59, 130, 246}  % Blue
        
        % Custom header and footer
        \pagestyle{fancy}
        \fancyhead{}
        \fancyhead[L]{\textcolor{primary}{\leftmark}}
        \fancyhead[R]{\textcolor{primary}{\thepage}}
        \fancyfoot{}
        \fancyfoot[C]{\textcolor{primary}{Memories-Dev Documentation}}
        
        % Title page customization
        \makeatletter
        \def\maketitle{
            \begin{titlepage}
                \centering
                \vspace*{2cm}
                {\Huge\textcolor{primary}{\textbf{\@title}}\par}
                \vspace{2cm}
                {\Large\textcolor{secondary}{Version \version}\par}
                \vspace{1.5cm}
                {\large\textcolor{primary}{\@author}\par}
                \vspace{1cm}
                {\large\textcolor{primary}{\@date}\par}
                \vfill
                {\large\textcolor{primary}{© 2025 Memories-Dev. All rights reserved.}\par}
            \end{titlepage}
        }
        \makeatother
        
        % Configure code blocks
        \fvset{fontsize=\small}
        \RecustomVerbatimEnvironment{Verbatim}{Verbatim}{
            frame=single,
            framesep=3mm,
            rulecolor=\color{gray!40},
            fontsize=\small
        }
    ''',
    'sphinxsetup': '\
        verbatimwithframe=false,\
        VerbatimColor={rgb}{0.97,0.97,0.97},\
        TitleColor={rgb}{0.06,0.09,0.16},\
        hmargin={1in,1in},\
        vmargin={1in,1in},\
        verbatimhintsturnover=false,\
        verbatimsep=3pt,\
        verbatimcontinuedrdots=false\
    ',
    'maketitle': r'\maketitle',
    'tableofcontents': r'\tableofcontents',
    'printindex': r'\printindex',
    'extraclassoptions': 'openany,oneside',
    'babel': '\\usepackage[english]{babel}',
    'passoptionstopackages': r'\PassOptionsToPackage{svgnames}{xcolor}',
    'fncychap': r'\usepackage[Bjarne]{fncychap}',
    'geometry': r'\usepackage[margin=1in,includefoot]{geometry}'
}

# Grouping the document tree into LaTeX files
latex_additional_files = []

# If true, show page references after internal links
latex_show_pagerefs = False

# If true, show URL addresses after external links
latex_show_urls = 'footnote'

# Documents to append as an appendix to all manuals
latex_appendices = []

# If false, no module index is generated
latex_domain_indices = True

# -- Options for manual page output ---------------------------------------

# One entry per manual page
man_pages = [
    (master_doc, 'memories-dev', 'Memories-Dev Documentation',
     [author], 1)
]

# If true, show URL addresses after external links
man_show_urls = True

# -- Options for Texinfo output -------------------------------------------

# Grouping the document tree into Texinfo files
texinfo_documents = [
    (master_doc, 'memories-dev', 'Memories-Dev Documentation',
     author, 'memories-dev', 'Collective Memory Infrastructure for AGI.',
     'Miscellaneous'),
]

# Documents to append as an appendix to all manuals
texinfo_appendices = []

# If false, no module index is generated
texinfo_domain_indices = True

# How to display URL addresses: 'footnote', 'no', or 'inline'
texinfo_show_urls = 'footnote'

# If true, do not generate a @detailmenu in the "Top" node's menu
texinfo_no_detailmenu = False

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

# List of patterns to exclude
exclude_patterns = [
    '_build',
    'Thumbs.db',
    '.DS_Store',
    '**.ipynb_checkpoints',
    'env',
    'venv',
]

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
    'style_nav_header_background': '#0f172a',
    'collapse_navigation': False,
    'sticky_navigation': True,
    'navigation_depth': 4,
    'includehidden': True,
    'titles_only': False,
    'body_max_width': '1200px',
    'navigation_with_keys': True,
}

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
mermaid_output_format = 'png'
mermaid_params = ['--theme', 'default', '--width', '100%']

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
    "numpy", "pandas", "matplotlib", "PIL", "requests", "yaml",
    "dotenv", "tqdm", "pyarrow", "nltk", "langchain", "pydantic",
    "shapely", "geopandas", "rasterio", "pyproj", "pystac",
    "mercantile", "folium", "rtree", "geopy", "osmnx", "py6s",
    "redis", "xarray", "dask", "aiohttp", "memories",
    "cudf", "cuspatial", "faiss", "torch", "transformers"
]

# Intersphinx configuration
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
    'pandas': ('https://pandas.pydata.org/docs/', None),
    'matplotlib': ('https://matplotlib.org/stable/', None),
} 