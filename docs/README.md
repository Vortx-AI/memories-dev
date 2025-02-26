# Memories-Dev Documentation

This directory contains the documentation for the Memories-Dev framework, built using Sphinx and deployed on Read the Docs.

## 📚 Book-Like Documentation Experience

The documentation is designed to provide a book-like reading experience with:

- **Elegant Book Design**: A beautiful book-styled homepage with visual flourishes
- **Chapter-Based Organization**: Content organized as chapters and sections
- **Reading Progress Tracker**: Visual indication of reading progress
- **Dark/Light Theme Toggle**: Comfortable reading in any environment
- **Enhanced Navigation**: Collapsible sections and smooth scrolling
- **Interactive Elements**: Click-to-copy code blocks and interactive diagrams

## 🚀 Quick Start

To build the documentation locally:

```bash
# Navigate to the docs directory
cd docs

# Install only the documentation dependencies (recommended)
pip install -r requirements-docs.txt

# Or use the make setup target
make setup

# Build HTML documentation
make html

# View the documentation in your browser
open build/html/index.html
```

## 📂 Directory Structure

- `source/`: Source files for the documentation
  - `_static/`: Static assets including CSS and JavaScript
  - `_templates/`: Custom templates
  - Various content directories for different chapters
- `build/`: Generated documentation (not committed to git)
- `Makefile`: Commands to build documentation
- `requirements-docs.txt`: Minimal Python dependencies for documentation
- `requirements.txt`: Full dependencies list (use requirements-docs.txt instead)

## 📑 Enhanced Features

The documentation includes several enhancements:

1. **JavaScript Enhancements**:
   - `lazy_loader.js`: Improves page load performance
   - `nav_enhancer.js`: Enhanced navigation experience
   - `progress_tracker.js`: Visual reading progress
   - `theme_toggle.js`: Dark/light theme switching
   - `doc_fixes.js`: Fixes common documentation issues

2. **CSS Enhancements**:
   - Responsive design for all device sizes
   - Book-like styling elements
   - Improved code block presentation
   - Optimized table layouts

3. **Interactive Elements**:
   - Copy buttons for code blocks
   - Anchor links for sharing specific sections
   - Collapsible table of contents

## 🛠️ Troubleshooting

### Dependency Conflicts

If you encounter dependency conflicts:

1. Use the `requirements-docs.txt` file which has carefully pinned versions
2. Create a fresh virtual environment: `python -m venv venv && source venv/bin/activate`
3. Install only what's needed: `pip install -r requirements-docs.txt`

### Build Issues

For build issues:

1. Clean the build directory: `make clean`
2. Use the debug option: `make html SPHINXOPTS="-v"`
3. Check for warnings in the build output

## 📖 Best Practices

1. **Keep TOC Shallow**: Use a maximum depth of 2 in table of contents
2. **Optimize Images**: Compress images before adding them to docs
3. **Use Book-like Elements**: Maintain the book metaphor in new content
4. **Test on Multiple Devices**: Ensure content looks good everywhere
5. **Fix Warnings**: Regularly address Sphinx warnings

## 📝 License

The documentation is licensed under the same terms as the Memories-Dev project. 