# Configuration file for the Sphinx documentation builder.
import os
import sys

sys.path.insert(0, os.path.abspath('../..'))

# Project information
project = 'Memory Codex'
copyright = '2025, memories-dev'
author = 'memories-dev Team'
version = '2.0.5'
release = '2.0.5'

# The master toctree document
master_doc = 'index'
root_doc = 'index'

# Essential Sphinx extensions
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.mathjax',
    'sphinx_rtd_theme',
    'sphinx_copybutton',
    'myst_parser',
    'sphinx.ext.autosummary',
    'sphinxcontrib.mermaid',
    'sphinx.ext.githubpages',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.ifconfig',
    'sphinx_design',
    'sphinx_tabs.tabs',
    'sphinx_togglebutton',
    'nbsphinx',
]

# Configure MyST-Parser for markdown support
myst_enable_extensions = [
    "dollarmath",
    "amsmath",
    "colon_fence",
    "smartquotes",
    "substitution",
]

# Mermaid configuration
mermaid_version = "latest"
mermaid_init_js = """
    mermaid.initialize({
        startOnLoad: true,
        theme: 'default',
        flowchart: {
            useMaxWidth: true,
            htmlLabels: true,
            curve: 'basis'
        }
    });
"""

# HTML Theme settings
html_theme = 'sphinx_rtd_theme'
html_theme_options = {
    'display_version': True,
    'prev_next_buttons_location': 'both',
    'style_nav_header_background': '#2c3e50',
    'collapse_navigation': True,
    'sticky_navigation': True,
    'navigation_depth': 2,
    'titles_only': True,
}

# Custom context to ensure light theme is default
html_context = {
    'default_theme': 'light',
}

# These folders are copied to the documentation's HTML output
html_static_path = ['_static']
html_css_files = [
    'css/custom.css',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css',
]
html_js_files = [
    'js/book.js',
    'js/mermaid-init.js',
    ('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/js/all.min.js', {'crossorigin': 'anonymous'}),
    ('https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js', {'crossorigin': 'anonymous'})
]

# Ensure light theme is set by default
def setup(app):
    app.add_js_file('js/force-light-theme.js')

# LaTeX settings for PDF output
latex_engine = 'pdflatex'
latex_elements = {
    'papersize': 'letterpaper',
    'pointsize': '11pt',
    'figure_align': 'htbp',
    'preamble': r'''
        \usepackage[T1]{fontenc}
        \usepackage{times}  % Use Times font instead
        \usepackage{helvet}  % For sans serif
        \usepackage{courier}  % For monospace
        
        \usepackage{geometry}
        \geometry{
            letterpaper,
            top=2.5cm,
            bottom=2.5cm,
            left=2.5cm,
            right=2.5cm,
            marginparwidth=1.5cm,
            marginparsep=0.5cm
        }
        
        \usepackage{microtype}
        \usepackage{titlesec}
        \usepackage{fancyhdr}
        \usepackage{enumitem}
        \usepackage{tocloft}
        
        % Chapter style
        \titleformat{\chapter}[display]
            {\normalfont\huge\bfseries\centering}
            {\chaptertitlename\ \thechapter}
            {20pt}
            {\Huge}
        
        % Section style
        \titleformat{\section}
            {\normalfont\Large\bfseries}
            {\thesection}
            {1em}
            {}[\titlerule]
        
        % Subsection style
        \titleformat{\subsection}
            {\normalfont\large\bfseries}
            {\thesubsection}
            {1em}
            {}
        
        % Page style
        \pagestyle{fancy}
        \fancyhf{}
        \fancyhead[LE,RO]{\thepage}
        \fancyhead[RE]{\leftmark}
        \fancyhead[LO]{\rightmark}
        \renewcommand{\headrulewidth}{0.4pt}
        
        % Table of contents style
        \renewcommand{\cftsecleader}{\cftdotfill{\cftdotsep}}
        \setcounter{tocdepth}{2}
        \setcounter{secnumdepth}{3}
    ''',
}

# Single PDF output configuration
latex_documents = [
    (master_doc, 'memory_codex.tex', 'Memory Codex Documentation',
     author, 'manual', True)
]

# Remove unused options
html_theme_path = []
html_short_title = None
html_additional_pages = {}
html_domain_indices = False
html_use_index = False
html_split_index = False
html_show_sourcelink = False
html_show_sphinx = False
html_show_copyright = True
html_copy_source = False
html_use_smartypants = True
