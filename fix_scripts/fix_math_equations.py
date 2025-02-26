#!/usr/bin/env python3
"""
Script to fix math equation rendering issues in documentation.

This script addresses:
1. Incorrect math directive usage
2. MathJax configuration issues
3. Improper math formatting
4. Missing or incorrect delimiters
"""

import os
import re
import sys
import argparse
from pathlib import Path

def fix_math_directive(content):
    """Fix math directive issues."""
    # Remove unsupported options like 'alt'
    content = re.sub(
        r'(\.\. math::)\s+(:alt:.*?)\s+',
        r'\1\n\n',
        content,
        flags=re.DOTALL
    )
    
    # Fix math directive formatting
    def fix_math_block(match):
        math_content = match.group(1).strip()
        # Split into lines and remove common indentation
        lines = math_content.split('\n')
        if len(lines) > 1:
            # Find minimum indentation (ignoring empty lines)
            indents = [len(line) - len(line.lstrip()) for line in lines if line.strip()]
            if indents:
                min_indent = min(indents)
                # Remove that indentation from each line
                math_content = '\n'.join(line[min_indent:] if line.strip() else line for line in lines)
        
        # Ensure proper indentation for the math content
        indented_content = '\n   '.join([''] + math_content.split('\n'))
        
        return f".. math::{indented_content}\n"
    
    content = re.sub(
        r'\.\. math::(.*?)(?=\n\S|\Z)',
        fix_math_block,
        content,
        flags=re.DOTALL
    )
    
    return content

def fix_inline_math(content):
    """Fix inline math formatting."""
    # Ensure consistent inline math delimiters
    # Convert :math:`...` to $...$
    content = re.sub(
        r':math:`([^`]+)`',
        r'$\1$',
        content
    )
    
    # Fix common issues with inline math
    # Replace spaces around operators
    content = re.sub(
        r'\$([^$]*?)\s*([+\-*/=])\s*([^$]*?)\$',
        r'$\1 \2 \3$',
        content
    )
    
    return content

def fix_display_math(content):
    """Fix display math formatting."""
    # Ensure consistent display math delimiters
    # Convert $$...$$ to proper math directive
    def replace_double_dollar(match):
        math_content = match.group(1).strip()
        indented_content = '\n   '.join([''] + math_content.split('\n'))
        return f"\n.. math::{indented_content}\n"
    
    content = re.sub(
        r'\$\$(.*?)\$\$',
        replace_double_dollar,
        content,
        flags=re.DOTALL
    )
    
    return content

def fix_math_in_rst_file(file_path):
    """Fix math issues in a single RST file."""
    print(f"Processing {file_path}...")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        print(f"Warning: Could not read {file_path} as UTF-8, skipping")
        return
    
    # Apply fixes
    original_content = content
    content = fix_math_directive(content)
    content = fix_inline_math(content)
    content = fix_display_math(content)
    
    # Write back if changed
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed math issues in {file_path}")
    else:
        print(f"No math issues to fix in {file_path}")

def fix_mathjax_config(conf_py_path):
    """Fix MathJax configuration in conf.py."""
    if not os.path.exists(conf_py_path):
        print(f"Warning: {conf_py_path} not found, skipping MathJax config fix")
        return
    
    with open(conf_py_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if we need to update MathJax configuration
    if 'mathjax_config' in content and 'mathjax3_config' not in content:
        # Add proper MathJax v3 configuration
        mathjax3_config = """
# MathJax v3 configuration
mathjax3_config = {
    'tex': {
        'inlineMath': [['$', '$'], ['\\\\(', '\\\\)']],
        'displayMath': [['$$', '$$'], ['\\\\[', '\\\\]']],
        'processEscapes': True,
        'processEnvironments': True
    },
    'options': {
        'ignoreHtmlClass': 'tex2jax_ignore',
        'processHtmlClass': 'tex2jax_process'
    }
}
"""
        # Add after mathjax_config
        content = re.sub(
            r'(mathjax_config\s*=\s*{[^}]*})',
            r'\1\n\n' + mathjax3_config,
            content
        )
        
        with open(conf_py_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Updated MathJax configuration in {conf_py_path}")
    else:
        print(f"MathJax configuration in {conf_py_path} is already up to date")

def main():
    parser = argparse.ArgumentParser(description='Fix math equation rendering issues in documentation.')
    parser.add_argument('--docs-dir', default='docs/source', help='Path to the documentation source directory')
    args = parser.parse_args()
    
    docs_dir = args.docs_dir
    
    if not os.path.isdir(docs_dir):
        print(f"Error: {docs_dir} is not a directory")
        sys.exit(1)
    
    # Fix MathJax configuration
    conf_py_path = os.path.join(docs_dir, 'conf.py')
    fix_mathjax_config(conf_py_path)
    
    # Process all RST files
    for root, _, files in os.walk(docs_dir):
        for file in files:
            if file.endswith('.rst'):
                file_path = os.path.join(root, file)
                fix_math_in_rst_file(file_path)
    
    print("All math equation issues fixed")

if __name__ == "__main__":
    main() 