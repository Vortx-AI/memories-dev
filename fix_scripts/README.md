# Documentation Fix System

This system provides a comprehensive solution for fixing common documentation rendering issues in Sphinx-based documentation. It addresses various problems such as:

1. Title underline issues
2. Math equation rendering problems
3. Mermaid diagram rendering
4. Missing references
5. UI and styling issues
6. JavaScript conflicts
7. Mobile responsiveness

## Quick Start

To fix all documentation issues at once, run:

```bash
python fix_scripts/fix_all_docs.py
```

This will:
1. Fix RST syntax issues
2. Fix math equation rendering
3. Ensure all required static files exist
4. Update conf.py with necessary fixes
5. Build the documentation to verify fixes

## Available Scripts

- `fix_all_docs.py`: Master script that runs all fixes
- `fix_rst_issues.py`: Fixes common RST syntax issues
- `fix_math_equations.py`: Fixes math equation rendering issues

## Configuration

You can customize the behavior of the fix scripts by editing the templates in the `fix_scripts/templates` directory:

- `custom.css`: General styling improvements
- `mobile.css`: Mobile-specific styling
- `doc_fixes.js`: JavaScript fixes for various issues

## Usage Options

```bash
# Fix all issues with default options
python fix_scripts/fix_all_docs.py

# Specify a custom documentation directory
python fix_scripts/fix_all_docs.py --docs-dir path/to/docs/source

# Skip building the documentation after applying fixes
python fix_scripts/fix_all_docs.py --skip-build

# Fix only RST issues
python fix_scripts/fix_rst_issues.py --docs-dir path/to/docs/source

# Fix only math equation issues
python fix_scripts/fix_math_equations.py --docs-dir path/to/docs/source
```

## How It Works

1. **RST Fixes**: Corrects title underlines, math directives, mermaid directives, and references in RST files.
2. **Math Fixes**: Ensures proper rendering of math equations by fixing directives and MathJax configuration.
3. **Static Files**: Adds custom CSS and JavaScript files to improve styling and functionality.
4. **conf.py Updates**: Modifies the Sphinx configuration to include necessary fixes and configurations.

## Troubleshooting

If you encounter issues after running the fix scripts:

1. Check the console output for any error messages
2. Verify that all required dependencies are installed
3. Make sure the documentation directory structure is correct
4. Try running individual fix scripts to isolate the problem

## Requirements

- Python 3.6+
- Sphinx
- docutils

## Contributing

To contribute to this fix system:

1. Add new fix scripts to the `fix_scripts` directory
2. Update the `fix_all_docs.py` script to include your new fixes
3. Add templates for any new CSS or JavaScript files
4. Update this README with information about your new fixes 