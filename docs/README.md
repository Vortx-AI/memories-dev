# Memories-Dev Documentation

This directory contains the documentation for the Memories-Dev framework, built using Sphinx and deployed on Read the Docs.

## Overview

The documentation is designed to be:

- **Lean**: Only showing content when needed to prevent UI clutter
- **Organized**: Using a clear hierarchy with a maximum navigation depth of 2
- **Responsive**: Working well on both desktop and mobile devices
- **Fast**: Using lazy loading for images and optimized JavaScript

## Directory Structure

- `source/`: Contains all the source files for the documentation
  - `_static/`: Static assets including CSS and JavaScript
  - `_templates/`: Custom templates
  - `api_reference/`: API documentation files
  - `core_concepts/`: Core concepts of the framework
  - `earth_memory/`: Earth memory documentation
  - Other directories for specific sections
- `build/`: Generated documentation (not checked into git)
- `Makefile`: Commands to build documentation
- `requirements.txt`: Python dependencies for documentation

## Building the Documentation

To build the documentation locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Build HTML documentation
make html

# Build PDF documentation (requires additional dependencies)
make latexpdf
```

## Common Issues and Fixes

### UI and Navigation Issues

If you encounter UI bugs or navigation problems:

1. **Depth Issues**: Navigation depth is limited to 2 levels by default. If the TOC becomes too deep and causes UI issues, update the `html_theme_options` in `source/conf.py`:
   ```python
   html_theme_options = {
       'navigation_depth': 2,  # Adjust if needed
       'collapse_navigation': False,
       # ... other options
   }
   ```

2. **UI Rendering Issues**: Check and update the CSS in `source/_static/css/custom.css`

3. **Mobile Responsiveness**: Ensure the theme is properly configured for mobile in `conf.py` and `custom.css`

### Lazy Loading Problems

If images or content don't load properly:

1. Check the JavaScript in `source/_static/lazy_loader.js`
2. Ensure images have proper classes for lazy loading
3. Verify the JS files are included in `conf.py`:
   ```python
   html_js_files = [
       'progress_tracker.js',
       'lazy_loader.js',
   ]
   ```

### Read the Docs Specific Issues

For Read the Docs deployment issues:

1. Check `.readthedocs.yaml` in the project root for build configuration
2. Verify that pre-build and post-build scripts are running correctly
3. Ensure all dependencies are properly specified in `docs/requirements.txt`

## Best Practices

1. **Keep TOC Shallow**: Use a maximum depth of 2 in table of contents to prevent navigation issues
2. **Optimize Images**: Compress images before adding them to the documentation
3. **Consistent Styling**: Follow the established style patterns for headers, code blocks, and notes
4. **Test on Mobile**: Always test documentation changes on both desktop and mobile
5. **Fix Warnings**: Regularly check for and fix Sphinx warnings to maintain documentation quality

## Custom Scripts

The following custom scripts are available to fix documentation issues:

1. `fix_scripts/fix_txt_diagrams.py`: Fixes text diagrams in RST files
2. `fix_scripts/fix_math_equations.py`: Fixes math equation rendering issues
3. `fix_scripts/simple_pdf_build.py`: Builds PDF documentation using rst2pdf instead of LaTeX
4. `fix_scripts/fix_latexmk_build.sh`: Fixes LaTeX build issues for PDF generation

To apply all fixes before publishing:

```bash
python fix_scripts/simple_pdf_build.py
``` 