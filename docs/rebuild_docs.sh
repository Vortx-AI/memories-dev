#!/bin/bash

# Memory Codex Documentation Rebuild Script
# This script rebuilds the documentation with the enhanced book experience

echo "=== Memory Codex Documentation Builder ==="
echo "Starting documentation build process..."

# Navigate to the docs directory
cd "$(dirname "$0")"

# Clean previous build
echo "Cleaning previous build..."
rm -rf build/

# Create required directories if they don't exist
echo "Setting up directory structure..."
mkdir -p source/_static/css
mkdir -p source/_static/js
mkdir -p source/_static/images
mkdir -p source/_templates

# Check if CSS and JS files exist in the expected locations
if [ ! -f "source/_static/css/enhanced_book.css" ]; then
    echo "Warning: Enhanced book CSS file not found! Building documentation might fail."
fi

if [ ! -f "source/_static/js/enhanced_book.js" ]; then
    echo "Warning: Enhanced book JavaScript file not found! Building documentation might fail."
fi

if [ ! -f "source/_templates/layout.html" ]; then
    echo "Warning: Custom layout template not found! Building documentation might fail."
fi

# Build the documentation
echo "Building HTML documentation..."
make html

# Check build result
if [ $? -eq 0 ]; then
    echo "Documentation built successfully!"
    echo "HTML pages are available in the build/html directory."
    
    # Optional: Open documentation in browser
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "Opening documentation in browser..."
        open build/html/index.html
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "To view documentation, open build/html/index.html in your browser."
        # Uncomment to open automatically on Linux
        # xdg-open build/html/index.html
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        echo "Opening documentation in browser..."
        start build/html/index.html
    fi
else
    echo "Error: Documentation build failed. See above for details."
    exit 1
fi

echo "=== Build process complete ===" 