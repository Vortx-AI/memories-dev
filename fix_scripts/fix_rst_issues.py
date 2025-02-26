#!/usr/bin/env python3
"""
Script to fix common RST issues in documentation files.

This script addresses:
1. Title underlines that are too short
2. Math directive issues
3. Mermaid directive issues
4. Missing references
5. Other common RST formatting problems
"""

import os
import re
import sys
from pathlib import Path
import argparse

def fix_title_underlines(content):
    """Fix title underlines that are too short."""
    lines = content.split('\n')
    fixed_lines = []
    
    i = 0
    while i < len(lines):
        fixed_lines.append(lines[i])
        
        # Check if this line could be a title
        if i + 1 < len(lines) and lines[i].strip() and all(c in '=-~^"\':.+*#' for c in lines[i+1].strip()):
            title = lines[i].strip()
            underline = lines[i+1].strip()
            
            # If the underline is shorter than the title, fix it
            if len(underline) < len(title) and len(underline) > 0:
                # Use the same character but make it the same length as the title
                fixed_underline = underline[0] * len(title)
                fixed_lines.append(fixed_underline)
                i += 2
                print(f"Fixed title underline: '{title}' -> '{fixed_underline}'")
                continue
        
        i += 1
    
    return '\n'.join(fixed_lines)

def fix_math_directives(content):
    """Fix math directive issues."""
    # Fix math directive with alt option
    content = re.sub(
        r'(\.\. math::)\s+(:alt:.*?)\s+',
        r'\1\n\n',
        content,
        flags=re.DOTALL
    )
    
    # Fix inline math formatting
    content = re.sub(
        r':math:`([^`]+)`',
        r'$\1$',
        content
    )
    
    # Fix display math blocks
    def fix_math_block(match):
        math_content = match.group(1).strip()
        # Split into lines and remove common indentation
        lines = math_content.split('\n')
        if len(lines) > 1:
            # Find minimum indentation
            min_indent = min((len(line) - len(line.lstrip())) for line in lines if line.strip())
            # Remove that indentation from each line
            math_content = '\n'.join(line[min_indent:] if line.strip() else line for line in lines)
        
        return f"\n.. math::\n\n{math_content}\n"
    
    content = re.sub(
        r'\.\. math::(.*?)(?=\n\S|\Z)',
        fix_math_block,
        content,
        flags=re.DOTALL
    )
    
    return content

def fix_mermaid_directives(content):
    """Fix mermaid directive issues."""
    # Fix mermaid directive with too many arguments
    def fix_mermaid_block(match):
        mermaid_content = match.group(1).strip()
        # Remove any arguments after the first line
        lines = mermaid_content.split('\n')
        first_line = lines[0] if lines else ""
        rest_lines = lines[1:] if len(lines) > 1 else []
        
        # Indent the content properly
        indented_content = '\n   '.join([''] + rest_lines)
        
        return f".. mermaid::\n{indented_content}\n"
    
    content = re.sub(
        r'\.\. mermaid::(.*?)(?=\n\S|\Z)',
        fix_mermaid_block,
        content,
        flags=re.DOTALL
    )
    
    return content

def fix_references(content, known_refs):
    """Fix references to nonexistent documents."""
    # Find all references
    ref_pattern = r':ref:`([^`]+)`'
    doc_pattern = r':doc:`([^`]+)`'
    
    # Replace broken references with text
    def replace_ref(match):
        ref = match.group(1)
        if ref not in known_refs:
            # Just use the text without making it a reference
            return f"'{ref}'"
        return match.group(0)
    
    content = re.sub(ref_pattern, replace_ref, content)
    
    # Replace broken document links with text
    def replace_doc(match):
        doc = match.group(1)
        if not os.path.exists(f"docs/source/{doc}.rst"):
            # Just use the text without making it a document link
            return f"'{os.path.basename(doc)}'"
        return match.group(0)
    
    content = re.sub(doc_pattern, replace_doc, content)
    
    return content

def fix_code_blocks(content):
    """Fix code-block directive issues."""
    # Fix code-block with align option
    content = re.sub(
        r'(\.\. code-block::.*?):align:.*?(?=\n\S|\Z)',
        r'\1',
        content,
        flags=re.DOTALL
    )
    
    return content

def fix_rst_file(file_path, known_refs=None):
    """Fix issues in a single RST file."""
    if known_refs is None:
        known_refs = []
    
    print(f"Processing {file_path}...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Apply fixes
    original_content = content
    content = fix_title_underlines(content)
    content = fix_math_directives(content)
    content = fix_mermaid_directives(content)
    content = fix_references(content, known_refs)
    content = fix_code_blocks(content)
    
    # Write back if changed
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed issues in {file_path}")
    else:
        print(f"No issues to fix in {file_path}")

def collect_references(docs_dir):
    """Collect all defined references in the documentation."""
    refs = []
    
    # Find all .. _ref_name: patterns
    ref_pattern = re.compile(r'\.\. _([^:]+):')
    
    for root, _, files in os.walk(docs_dir):
        for file in files:
            if file.endswith('.rst'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    for match in ref_pattern.finditer(content):
                        refs.append(match.group(1))
    
    return refs

def main():
    parser = argparse.ArgumentParser(description='Fix common RST issues in documentation files.')
    parser.add_argument('--docs-dir', default='docs/source', help='Path to the documentation source directory')
    args = parser.parse_args()
    
    docs_dir = args.docs_dir
    
    if not os.path.isdir(docs_dir):
        print(f"Error: {docs_dir} is not a directory")
        sys.exit(1)
    
    # Collect all references
    print("Collecting references...")
    known_refs = collect_references(docs_dir)
    print(f"Found {len(known_refs)} references")
    
    # Process all RST files
    for root, _, files in os.walk(docs_dir):
        for file in files:
            if file.endswith('.rst'):
                file_path = os.path.join(root, file)
                fix_rst_file(file_path, known_refs)
    
    print("All RST files processed")

if __name__ == "__main__":
    main() 