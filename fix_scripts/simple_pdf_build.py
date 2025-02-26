#!/usr/bin/env python3
"""
Script to build a PDF version of documentation without requiring LaTeX.
This script uses rst2pdf to convert RST files to PDF directly.
"""

import os
import sys
import subprocess
import shutil
from glob import glob

def check_requirements():
    """Check if required packages are installed and install them if not."""
    required_packages = [
        "rst2pdf>=0.103.1",
        "reportlab>=4.3.1",
        "smartypants>=2.0.1",
        "docutils>=0.20.1"
    ]
    
    # First check if the packages are already installed
    missing_packages = []
    for pkg in required_packages:
        pkg_name = pkg.split('>=')[0]
        try:
            __import__(pkg_name)
            print(f"{pkg_name} is already installed.")
        except ImportError:
            print(f"{pkg_name} is not installed.")
            missing_packages.append(pkg)
    
    # Install missing packages if any
    if missing_packages:
        print(f"Installing missing packages: {', '.join(missing_packages)}")
        # Create a temporary requirements file for pip
        temp_req_file = "temp_requirements.txt"
        with open(temp_req_file, "w") as f:
            f.write("\n".join(missing_packages))
        
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", temp_req_file])
            print("All required packages installed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error installing packages: {e}")
            print("Continuing anyway, as packages might be installed by ReadTheDocs...")
        finally:
            # Clean up temporary file
            if os.path.exists(temp_req_file):
                os.remove(temp_req_file)

def update_conf_py():
    """Update conf.py to enable rst2pdf extension."""
    conf_path = "docs/source/conf.py"
    with open(conf_path, 'r') as f:
        content = f.read()
    
    # Add rst2pdf to extensions if not already there
    if "rst2pdf.pdfbuilder" not in content:
        print("Adding rst2pdf extension to conf.py...")
        if "extensions = [" in content:
            content = content.replace(
                "extensions = [", 
                "extensions = [\n    'rst2pdf.pdfbuilder',")
        else:
            print("WARNING: Could not find extensions list in conf.py")
            print("Adding extensions list manually...")
            content += """
# -- Options for PDF output --------------------------------------------------
extensions.append('rst2pdf.pdfbuilder')
"""
    
    # Add pdf_documents configuration
    if "pdf_documents" not in content:
        print("Adding pdf_documents configuration to conf.py...")
        content += """
# -- Options for PDF output using rst2pdf ---------------------------------
pdf_documents = [
    ('index', 'memories-dev', 'Memories-Dev Documentation', 'Memories-Dev Team'),
]
pdf_stylesheets = ['sphinx', 'letter']
pdf_style_path = ['.', '_styles']
pdf_language = 'en_US'
pdf_fit_mode = "shrink"
pdf_break_level = 0
pdf_verbosity = 0
pdf_use_index = False
pdf_use_modindex = False
pdf_use_coverpage = True
"""
    
    # Write the updated conf.py
    with open(conf_path, 'w') as f:
        f.write(content)

def create_style_file():
    """Create a custom style file for better PDF formatting."""
    styles_dir = "docs/source/_styles"
    os.makedirs(styles_dir, exist_ok=True)
    
    style_file = os.path.join(styles_dir, "custom.style")
    with open(style_file, 'w') as f:
        f.write("""
{
    "pageSetup": {
        "size": "letter",
        "width": null,
        "height": null,
        "margin-top": "2cm",
        "margin-bottom": "2cm",
        "margin-left": "2cm",
        "margin-right": "2cm",
        "margin-gutter": "0cm",
        "spacing-header": "5mm",
        "spacing-footer": "5mm",
        "firstTemplate": "oneColumn"
    },
    "pageTemplates": {
        "oneColumn": {
            "frames": [
                ["0", "0", "100%", "100%"]
            ],
            "showHeader": true,
            "showFooter": true,
            "defaultFooter": "###Page###",
            "defaultHeader": "Memories-Dev Documentation"
        }
    },
    "fontsAlias": {
        "stdFont": "Helvetica",
        "stdBold": "Helvetica-Bold",
        "stdItalic": "Helvetica-Oblique",
        "stdBoldItalic": "Helvetica-BoldOblique",
        "stdMono": "Courier",
        "stdMonoBold": "Courier-Bold",
        "stdMonoItalic": "Courier-Oblique",
        "stdMonoBoldItalic": "Courier-BoldOblique"
    },
    "styles": {
        "base": {
            "fontName": "stdFont",
            "fontSize": 10,
            "leading": 12
        },
        "heading1": {
            "fontName": "stdBold",
            "fontSize": 24,
            "leading": 28,
            "spaceAfter": 12
        },
        "heading2": {
            "fontName": "stdBold",
            "fontSize": 18,
            "leading": 22,
            "spaceAfter": 10
        },
        "heading3": {
            "fontName": "stdBold",
            "fontSize": 14,
            "leading": 18,
            "spaceAfter": 8
        },
        "code": {
            "fontName": "stdMono",
            "fontSize": 8,
            "leading": 10
        }
    }
}
""")
    
    # Update pdf_stylesheets in conf.py to include custom style
    conf_path = "docs/source/conf.py"
    with open(conf_path, 'r') as f:
        content = f.read()
    
    if "pdf_stylesheets = ['sphinx', 'letter']" in content:
        content = content.replace(
            "pdf_stylesheets = ['sphinx', 'letter']",
            "pdf_stylesheets = ['sphinx', 'letter', '_styles/custom']"
        )
    
    with open(conf_path, 'w') as f:
        f.write(content)

def fix_documentation_issues():
    """Run the existing fix scripts to ensure documentation is cleaned up."""
    print("Running fix_txt_diagrams.py...")
    subprocess.call([sys.executable, "fix_scripts/fix_txt_diagrams.py"])
    
    print("Running fix_math_equations.py...")
    subprocess.call([sys.executable, "fix_scripts/fix_math_equations.py"])
    
    print("Ensuring static CSS directory exists...")
    css_dir = "docs/source/_static/css"
    if not os.path.exists(css_dir):
        os.makedirs(css_dir)
    
    print("Applying UI fixes...")
    # Ensure the JS files are properly included
    copy_if_not_exists("docs/source/_static/lazy_loader.js", "docs/build/html/_static/lazy_loader.js")
    copy_if_not_exists("docs/source/_static/css/custom.css", "docs/build/html/_static/css/custom.css")
    
    # Fix depth display issues in generated HTML
    fix_toc_depth_issues("docs/build/html")
    
    print("Documentation fixes applied successfully.")

def copy_if_not_exists(src, dst):
    """Copy a file if it exists at source and not at destination."""
    if os.path.exists(src) and not os.path.exists(dst):
        # Create destination directory if needed
        dst_dir = os.path.dirname(dst)
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)
        shutil.copy2(src, dst)
        print(f"Copied {src} to {dst}")

def fix_toc_depth_issues(html_dir):
    """Fix TOC depth display issues in HTML files."""
    # Find all HTML files
    for root, _, files in os.walk(html_dir):
        for file in files:
            if file.endswith(".html"):
                html_path = os.path.join(root, file)
                try:
                    # Read the HTML content
                    with open(html_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Fix deep TOC nesting issues
                    # Add CSS classes to control TOC depth visibility
                    content = content.replace(
                        '<div class="wy-menu wy-menu-vertical"',
                        '<div class="wy-menu wy-menu-vertical" data-max-depth="2"'
                    )
                    
                    # Write the updated content
                    with open(html_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                except Exception as e:
                    print(f"Error processing {html_path}: {str(e)}")

def build_pdf():
    """Build the PDF using rst2pdf directly."""
    # Create build directory if it doesn't exist
    pdf_dir = "docs/build/pdf"
    os.makedirs(pdf_dir, exist_ok=True)
    
    # Build the PDF
    print("Building PDF...")
    index_rst = "docs/source/index.rst"
    output_pdf = os.path.join(pdf_dir, "memories-dev.pdf")
    
    cmd = [
        sys.executable, "-m", "rst2pdf.createpdf",
        index_rst,
        "-o", output_pdf,
        "--stylesheets=sphinx,letter,_styles/custom",
        "--break-level=1",
        "--fit-mode=shrink",
        "--smart-quotes=1"
    ]
    
    subprocess.call(cmd, cwd="docs")
    
    # Copy PDF to _readthedocs/html
    rtd_dir = "_readthedocs/html"
    os.makedirs(rtd_dir, exist_ok=True)
    
    if os.path.exists(output_pdf):
        shutil.copy(output_pdf, os.path.join(rtd_dir, "memories-dev.pdf"))
        print(f"PDF successfully built and copied to {rtd_dir}/memories-dev.pdf")
    else:
        print("Failed to build PDF. Check for errors.")

def update_readthedocs_yaml():
    """Update .readthedocs.yaml to use rst2pdf instead of latex."""
    rtd_yaml_path = ".readthedocs.yaml"
    if not os.path.exists(rtd_yaml_path):
        print(f"Warning: {rtd_yaml_path} not found. Skipping update.")
        return
    
    with open(rtd_yaml_path, 'r') as f:
        content = f.read()
    
    # Replace latexpdf with pdf
    content = content.replace("make latexpdf", "python -m fix_scripts.simple_pdf_build")
    
    with open(rtd_yaml_path, 'w') as f:
        f.write(content)
    
    print("Updated .readthedocs.yaml to use simple_pdf_build.py")

def main():
    """Main function to execute the script."""
    # Change to the project root directory
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    os.chdir(project_root)
    print(f"Working directory: {os.getcwd()}")
    
    # Check requirements
    check_requirements()
    
    # Fix documentation issues
    fix_documentation_issues()
    
    # Update configuration
    update_conf_py()
    create_style_file()
    update_readthedocs_yaml()
    
    # Build PDF
    build_pdf()
    
    print("PDF build process completed.")

if __name__ == "__main__":
    main() 