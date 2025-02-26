#!/usr/bin/env python3
"""
Fix ReadTheDocs PDF build issues by converting text file references to code blocks.
This script finds all .rst files with .txt images and converts them to code blocks.
"""

import os
import re
import glob
from pathlib import Path

def read_txt_file(txt_path):
    """Read the content of a text file as a diagram."""
    try:
        with open(txt_path, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        # Try to locate in build/latex directory
        alt_path = os.path.join('docs/build/latex', os.path.basename(txt_path))
        try:
            with open(alt_path, 'r') as f:
                return f.read().strip()
        except FileNotFoundError:
            return "# Diagram content not found"

def fix_rst_file(file_path):
    """Fix a single RST file by replacing image references to text files with code blocks."""
    print(f"Processing: {file_path}")
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Find all image directives referencing .txt files
    pattern = r'\.\.[\s]+image::[\s]+([^\n]+\.txt)([^\n]*)\n(?:[\s]+:([^\n]*)\n)*'
    
    def replace_match(match):
        img_path = match.group(1).strip()
        img_options = match.group(2) if match.group(2) else ''
        
        # Extract options from subsequent lines
        options = []
        if match.group(3):
            options.append(match.group(3))
        
        # Check if there are multiple options
        remainder = match.string[match.end():]
        i = 0
        while remainder[i:i+4] == '    :':
            end_of_line = remainder[i:].find('\n')
            if end_of_line == -1:
                break
            options.append(remainder[i+4:i+end_of_line].strip())
            i += end_of_line + 1
            if not remainder[i:].startswith('    :'):
                break
        
        # Extract the actual file path from the image reference
        if img_path.startswith('/'):
            # It's an absolute path within the documentation
            basename = os.path.basename(img_path)
            txt_path = f"docs/build/latex/{basename}"
        else:
            # It's a relative path
            txt_path = os.path.join(os.path.dirname(file_path), img_path)
        
        # Read the diagram content
        diagram_content = read_txt_file(txt_path)
        
        # Determine caption from alt or other options
        caption = ""
        for opt in options:
            if opt.startswith('alt:'):
                caption = opt.replace('alt:', 'caption:').strip()
                break
        
        if not caption and options:
            for opt in options:
                if not opt.startswith(('align:', 'width:', 'height:', 'scale:')):
                    caption = f"caption: {opt}"
                    break
        
        # Create the code block
        code_block = ".. code-block:: text\n"
        if caption:
            code_block += f"   :{caption}\n"
        for opt in options:
            if opt.startswith('align:'):
                code_block += f"   :{opt}\n"
        
        code_block += "\n"
        for line in diagram_content.split('\n'):
            code_block += f"   {line}\n"
        
        return code_block
    
    # Replace all matches
    updated_content = re.sub(pattern, replace_match, content)
    
    # Write the fixed content back
    if content != updated_content:
        with open(file_path, 'w') as f:
            f.write(updated_content)
        print(f"Fixed: {file_path}")
        return True
    return False

def main():
    """Main function to fix all RST files."""
    # Find all RST files
    rst_files = glob.glob('docs/source/**/*.rst', recursive=True)
    
    fixed_count = 0
    for file_path in rst_files:
        if fix_rst_file(file_path):
            fixed_count += 1
    
    print(f"Fixed {fixed_count} RST files")

if __name__ == "__main__":
    main() 