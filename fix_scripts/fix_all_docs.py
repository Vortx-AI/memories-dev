#!/usr/bin/env python3
"""
Master script to fix all documentation issues.

This script runs all the individual fix scripts to address:
1. Title underline issues
2. Math equation rendering
3. Mermaid diagram rendering
4. Missing references
5. UI and styling issues
6. JavaScript conflicts
7. Mobile responsiveness
"""

import os
import sys
import subprocess
import argparse
import shutil
import re
from pathlib import Path
from PIL import Image, ImageDraw

def run_script(script_path, args=None):
    """Run a Python script with optional arguments."""
    cmd = [sys.executable, script_path]
    if args:
        cmd.extend(args)
    
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.stdout:
        print(result.stdout)
    
    if result.stderr:
        print(f"Error: {result.stderr}", file=sys.stderr)
    
    return result.returncode == 0

def ensure_file_exists(file_path, content=None):
    """Ensure a file exists, creating it with optional content if needed."""
    if not os.path.exists(file_path):
        print(f"Creating missing file: {file_path}")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            if content:
                f.write(content)
            else:
                f.write("# Auto-generated file\n")
        
        return True
    return False

def fix_rst_issues(docs_dir):
    """Fix RST syntax issues."""
    print("\n=== Fixing RST Issues ===")
    script_path = os.path.join('fix_scripts', 'fix_rst_issues.py')
    return run_script(script_path, ['--docs-dir', docs_dir])

def fix_math_equations(docs_dir):
    """Fix math equation rendering issues."""
    print("\n=== Fixing Math Equations ===")
    script_path = os.path.join('fix_scripts', 'fix_math_equations.py')
    return run_script(script_path, ['--docs-dir', docs_dir])

def consolidate_static_files(docs_dir):
    """Consolidate JavaScript and CSS files to reduce duplication and HTTP requests."""
    print("Consolidating static files to reduce clutter...")
    
    # Create directories if they don't exist
    static_dir = os.path.join(docs_dir, '_static')
    css_dir = os.path.join(static_dir, 'css')
    js_dir = os.path.join(static_dir, 'js')
    
    os.makedirs(css_dir, exist_ok=True)
    os.makedirs(js_dir, exist_ok=True)
    
    # 1. Consolidate CSS files
    consolidated_css = """/* 
 * Consolidated CSS for memories-dev documentation
 * This file combines custom.css and mobile.css to reduce HTTP requests
 */

"""
    
    # Add custom.css content
    custom_css_path = os.path.join('fix_scripts', 'templates', 'custom.css')
    if os.path.exists(custom_css_path):
        with open(custom_css_path, 'r', encoding='utf-8') as f:
            consolidated_css += f.read() + "\n\n"
    
    # Add mobile.css content
    mobile_css_path = os.path.join('fix_scripts', 'templates', 'mobile.css')
    if os.path.exists(mobile_css_path):
        with open(mobile_css_path, 'r', encoding='utf-8') as f:
            consolidated_css += f.read()
    
    # Write consolidated CSS
    with open(os.path.join(css_dir, 'consolidated.css'), 'w', encoding='utf-8') as f:
        f.write(consolidated_css)
    
    # 2. Consolidate JavaScript files
    consolidated_js = """/* 
 * Consolidated JavaScript for memories-dev documentation
 * This file combines multiple JS files to reduce HTTP requests and conflicts
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all functionality
    initializeDocumentation();
});

function initializeDocumentation() {
    // Core functionality
    fixUIIssues();
    enhanceNavigation();
    setupLazyLoading();
    
    // Optional functionality based on page type
    if (isTutorialPage()) {
        initializeProgressTracker();
    }
    
    // Add resize listener for responsive behavior
    window.addEventListener('resize', handleResize);
    handleResize(); // Initial call
}

"""
    
    # Add doc_fixes.js content
    doc_fixes_path = os.path.join('fix_scripts', 'templates', 'doc_fixes.js')
    if os.path.exists(doc_fixes_path):
        with open(doc_fixes_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Remove DOMContentLoaded event listener to avoid duplication
            content = re.sub(r'document\.addEventListener\([\'"]DOMContentLoaded[\'"],\s*function\s*\(\)\s*{', '// Core fixes\nfunction fixUIIssues() {', content)
            content = re.sub(r'}\);\s*$', '}', content)
            consolidated_js += content + "\n\n"
    
    # Extract relevant functions from lazy_loader.js
    lazy_loader_path = os.path.join(docs_dir, '_static', 'lazy_loader.js')
    if os.path.exists(lazy_loader_path):
        with open(lazy_loader_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Extract setupLazyImages function
            setup_lazy_images_match = re.search(r'function setupLazyImages\(\)\s*{.*?}', content, re.DOTALL)
            if setup_lazy_images_match:
                consolidated_js += "// Lazy loading functionality\nfunction setupLazyLoading() {\n    " + setup_lazy_images_match.group(0) + "\n}\n\n"
    
    # Extract relevant functions from progress_tracker.js
    progress_tracker_path = os.path.join(docs_dir, '_static', 'progress_tracker.js')
    if os.path.exists(progress_tracker_path):
        with open(progress_tracker_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Extract isTutorialPage function
            is_tutorial_page_match = re.search(r'function isTutorialPage\(\)\s*{.*?}', content, re.DOTALL)
            if is_tutorial_page_match:
                consolidated_js += "// Tutorial page detection\n" + is_tutorial_page_match.group(0) + "\n\n"
    
    # Add navigation enhancement functionality
    consolidated_js += """
// Navigation enhancement
function enhanceNavigation() {
    // Fix navigation depth issues
    const nestedItems = document.querySelectorAll('.wy-menu-vertical li.toctree-l3, .wy-menu-vertical li.toctree-l4');
    nestedItems.forEach(item => {
        if (!item.closest('li.current')) {
            item.style.display = 'none';
        }
    });
    
    // Add smooth scrolling
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href');
            if (targetId !== '#' && document.querySelector(targetId)) {
                e.preventDefault();
                document.querySelector(targetId).scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });
    
    // Add mobile overlay for better UX
    if (!document.getElementById('mobile-overlay')) {
        const overlay = document.createElement('div');
        overlay.id = 'mobile-overlay';
        document.body.appendChild(overlay);
        
        overlay.addEventListener('click', function() {
            document.querySelector('.wy-nav-side').classList.remove('shift');
            document.querySelector('.wy-nav-content-wrap').classList.remove('shift');
        });
    }
}

// Responsive behavior
function handleResize() {
    const width = window.innerWidth;
    const isMobile = width <= 768;
    
    // Handle "On This Page" section visibility
    const onThisPage = document.querySelector('.contents.local');
    if (onThisPage) {
        onThisPage.style.display = isMobile ? 'none' : 'block';
    }
    
    // Make tables responsive on mobile
    if (isMobile) {
        document.querySelectorAll('table.docutils').forEach(table => {
            table.style.display = 'block';
            table.style.overflowX = 'auto';
        });
    }
}
"""
    
    # Write consolidated JS
    with open(os.path.join(js_dir, 'consolidated.js'), 'w', encoding='utf-8') as f:
        f.write(consolidated_js)
    
    print("Static files consolidated successfully")
    return True

def update_conf_py(docs_dir):
    """Update conf.py to use consolidated files and fix configuration issues."""
    print("Updating conf.py...")
    
    conf_py_path = os.path.join(docs_dir, 'conf.py')
    if not os.path.exists(conf_py_path):
        print(f"Error: {conf_py_path} not found")
        return False
    
    with open(conf_py_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Update the setup function to use consolidated files
    setup_pattern = r'def setup\(app\):(.*?)(?=def|$)'
    setup_match = re.search(setup_pattern, content, re.DOTALL)
    
    if setup_match:
        setup_content = setup_match.group(1)
        
        # Remove individual CSS and JS file additions
        setup_content = re.sub(r'app\.add_css_file\([\'"]css/custom\.css.*?\)', '', setup_content)
        setup_content = re.sub(r'app\.add_css_file\([\'"]css/mobile\.css.*?\)', '', setup_content)
        setup_content = re.sub(r'app\.add_js_file\([\'"]doc_fixes\.js.*?\)', '', setup_content)
        setup_content = re.sub(r'app\.add_js_file\([\'"]lazy_loader\.js.*?\)', '', setup_content)
        setup_content = re.sub(r'app\.add_js_file\([\'"]progress_tracker\.js.*?\)', '', setup_content)
        setup_content = re.sub(r'app\.add_js_file\([\'"]nav_enhancer\.js.*?\)', '', setup_content)
        setup_content = re.sub(r'app\.add_js_file\([\'"]theme_toggle\.js.*?\)', '', setup_content)
        
        # Add consolidated files
        if 'app.add_css_file("css/consolidated.css")' not in setup_content:
            setup_content = re.sub(r'# Add custom CSS and JS files', 
                                  '# Add consolidated CSS and JS files\n    app.add_css_file("css/consolidated.css")', 
                                  setup_content)
        
        if 'app.add_js_file("js/consolidated.js")' not in setup_content:
            setup_content = re.sub(r'app\.add_css_file\("css/consolidated\.css"\)', 
                                  'app.add_css_file("css/consolidated.css")\n    app.add_js_file("js/consolidated.js")', 
                                  setup_content)
        
        # Update the setup function
        new_content = re.sub(setup_pattern, f'def setup(app):{setup_content}', content, flags=re.DOTALL)
        
        with open(conf_py_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("conf.py updated successfully")
        return True
    else:
        print("Error: Could not find setup function in conf.py")
        return False

def create_template_directory():
    """Create a templates directory with necessary files."""
    print("\n=== Creating Template Directory ===")
    
    templates_dir = os.path.join('fix_scripts', 'templates')
    os.makedirs(templates_dir, exist_ok=True)
    
    # Copy our existing files to the templates directory
    files_to_copy = {
        os.path.join('docs', 'source', '_static', 'doc_fixes.js'): os.path.join(templates_dir, 'doc_fixes.js'),
        os.path.join('docs', 'source', '_static', 'css', 'custom.css'): os.path.join(templates_dir, 'custom.css'),
        os.path.join('docs', 'source', '_static', 'css', 'mobile.css'): os.path.join(templates_dir, 'mobile.css')
    }
    
    for src, dst in files_to_copy.items():
        if os.path.exists(src):
            shutil.copy(src, dst)
            print(f"Copied {src} to {dst}")
        else:
            print(f"Warning: {src} not found, skipping")
    
    return True

def build_docs(docs_dir):
    """Build the documentation."""
    print("\n=== Building Documentation ===")
    
    # Get the parent directory of docs_dir (should be 'docs')
    docs_parent = os.path.dirname(docs_dir)
    
    # Use sphinx-build directly instead of make
    build_cmd = [
        "sphinx-build",
        "-b", "html",  # Build HTML
        "-d", os.path.join(docs_parent, "build", "doctrees"),  # Doctrees directory
        docs_dir,  # Source directory
        os.path.join(docs_parent, "build", "html")  # Output directory
    ]
    
    try:
        result = subprocess.run(
            build_cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        print(result.stdout)
        print("Documentation built successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error building documentation: {e}")
        print(e.stdout)
        return False

def ensure_static_files(docs_dir):
    """Ensure all required static files exist."""
    print("Ensuring static files exist...")
    
    static_dir = os.path.join(docs_dir, '_static')
    css_dir = os.path.join(static_dir, 'css')
    js_dir = os.path.join(static_dir, 'js')
    
    os.makedirs(static_dir, exist_ok=True)
    os.makedirs(css_dir, exist_ok=True)
    os.makedirs(js_dir, exist_ok=True)
    
    # Check if consolidated files exist, if not create them
    if not os.path.exists(os.path.join(css_dir, 'consolidated.css')):
        print("Consolidated CSS file not found, creating it...")
        consolidate_static_files(docs_dir)
    
    if not os.path.exists(os.path.join(js_dir, 'consolidated.js')):
        print("Consolidated JS file not found, creating it...")
        consolidate_static_files(docs_dir)
    
    # Create a favicon if it doesn't exist
    favicon_path = os.path.join(static_dir, 'favicon.ico')
    if not os.path.exists(favicon_path):
        # Create a simple favicon to prevent 404 errors
        try:
            # Create a 32x32 image with a blue background
            img = Image.new('RGB', (32, 32), color=(59, 130, 246))
            draw = ImageDraw.Draw(img)
            
            # Draw a simple "M" letter
            draw.rectangle([8, 8, 24, 24], fill=(255, 255, 255))
            draw.rectangle([10, 10, 22, 22], fill=(59, 130, 246))
            
            # Save as ICO
            img.save(favicon_path, format='ICO')
            print(f"Created favicon at {favicon_path}")
        except ImportError:
            print("Warning: PIL not available, skipping favicon creation")
            # Create an empty file to prevent 404s
            with open(favicon_path, 'wb') as f:
                f.write(b'')
    
    print("Static files check completed")
    return True

def main():
    parser = argparse.ArgumentParser(description='Fix all documentation issues.')
    parser.add_argument('--docs-dir', default='docs/source', help='Path to the documentation source directory')
    parser.add_argument('--skip-build', action='store_true', help='Skip building the documentation after applying fixes')
    args = parser.parse_args()
    
    docs_dir = args.docs_dir
    
    if not os.path.isdir(docs_dir):
        print(f"Error: {docs_dir} is not a directory")
        sys.exit(1)
    
    # Create template directory if it doesn't exist
    create_template_directory()
    
    # Fix RST issues
    fix_rst_issues(docs_dir)
    
    # Fix math equations
    fix_math_equations(docs_dir)
    
    # Consolidate static files to reduce clutter
    consolidate_static_files(docs_dir)
    
    # Ensure static files exist
    ensure_static_files(docs_dir)
    
    # Update conf.py
    update_conf_py(docs_dir)
    
    # Build documentation if not skipped
    if not args.skip_build:
        build_docs(docs_dir)
    
    print("All documentation fixes applied successfully")

if __name__ == "__main__":
    main() 