# Documentation Theme Structure

This directory contains the CSS and JavaScript files for the Memories-Dev documentation theme.

## Consolidated Structure

The theme has been consolidated to reduce duplication and improve maintainability:

### CSS Structure

- `css/consolidated/main.css`: Main CSS file that imports all other CSS files
- `css/consolidated/theme.css`: Base theme variables and styles
- `css/consolidated/components.css`: Styles for UI components (tables, admonitions, etc.)
- `css/consolidated/diagrams.css`: Styles for Mermaid diagrams and MathJax
- `css/consolidated/book-style.css`: Book-like styling and decorative elements
- `css/consolidated/dark-mode.css`: Dark mode styles

### JavaScript Structure

- `js/consolidated/main.js`: Main JavaScript file that loads all other scripts
- `js/consolidated/diagrams.js`: Handles Mermaid diagrams and MathJax rendering
- `js/consolidated/dark-mode.js`: Handles dark mode toggle functionality
- `js/consolidated/book-features.js`: Handles book-like features (chapter navigation, etc.)

## Usage

The consolidated files are loaded in `conf.py` using:

```python
def setup(app):
    # Add consolidated CSS file (contains all styles)
    app.add_css_file('css/consolidated/main.css')
    
    # Add web fonts
    app.add_css_file('https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,700;1,400;1,700&display=swap')
    app.add_css_file('https://fonts.googleapis.com/css2?family=Source+Code+Pro:wght@400;600&display=swap')
    
    # Add consolidated JS file (loads all other scripts)
    app.add_js_file('https://cdn.jsdelivr.net/npm/mermaid@9.4.3/dist/mermaid.min.js')
    app.add_js_file('js/consolidated/main.js')
```

## Legacy Files

The legacy CSS and JavaScript files are still present but are no longer used:

- `custom.css`, `theme_fix.css`, `enhanced_theme.css`, `book_theme.css`, etc.
- `direct-mermaid-fix.js`, `diagram-math-fix.js`, `book.js`, etc.

These files can be removed once the consolidated structure is confirmed to be working correctly. 