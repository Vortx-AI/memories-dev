# Configuration file for the Sphinx documentation builder.
import os
import sys

sys.path.insert(0, os.path.abspath('../..'))

# Project information
project = 'Memory Codex'
copyright = '2024, Memory Codex'
author = 'Memory Codex Team'
version = '2.0.2'
release = '2.0.2'

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

# HTML Theme settings
html_theme = 'sphinx_rtd_theme'
html_theme_options = {
    'display_version': True,
    'prev_next_buttons_location': 'both',
    'style_nav_header_background': '#2c3e50',
    'collapse_navigation': False,
    'sticky_navigation': True,
    'navigation_depth': 4,
}

# These folders are copied to the documentation's HTML output
html_static_path = ['_static']
html_css_files = ['css/custom.css']
html_js_files = ['js/book.js']

# LaTeX settings for PDF output
latex_elements = {
    'papersize': 'letterpaper',
    'pointsize': '11pt',
    'figure_align': 'htbp',
    'preamble': r'''
        \usepackage{fontspec}
        \setmainfont{Crimson Pro}
        \setsansfont{Source Sans Pro}
        \setmonofont{Source Code Pro}
        
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

latex_documents = [
    (master_doc, 'memory_codex.tex', 'Memory Codex',
     author, 'manual'),
]

# PDF output settings
pdf_documents = [(master_doc, 'memory_codex', 'Memory Codex', author)]
pdf_stylesheets = ['sphinx', 'kerning', 'a4']
pdf_use_index = False
pdf_toc_depth = 3

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
