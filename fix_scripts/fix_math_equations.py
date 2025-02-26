#!/usr/bin/env python3
"""
Fix ReadTheDocs PDF build issues by correcting malformed LaTeX math equations.
"""

import os
import re
import glob

def fix_math_equations(file_path):
    """Fix LaTeX math equations in a single RST file."""
    print(f"Processing: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Fix equations with problematic \text{} commands
    # Find all math blocks
    math_blocks = re.findall(r'\.\.[\s]+math::(.*?)(?=\.\.[\s]+|$)', content, re.DOTALL)
    
    for block in math_blocks:
        fixed_block = block
        
        # Fix \text{precision} to just precision
        fixed_block = re.sub(r'\\text{(\w+)}', r'\1', fixed_block)
        
        # Fix functions like base32_encode to be properly escaped for LaTeX
        fixed_block = re.sub(r'\\text{(\w+)_(\w+)}', r'\\text{\1\\_\2}', fixed_block)
        
        # Fix end{split} issues by making sure it's properly closed and opened
        if '\\begin{split}' in fixed_block and '\\end{split}' in fixed_block:
            # Ensure proper split environment
            split_content = re.search(r'\\begin{split}(.*?)\\end{split}', fixed_block, re.DOTALL)
            if split_content:
                split_text = split_content.group(1)
                # Add alignment points if missing
                if '&' not in split_text:
                    lines = split_text.strip().split('\n')
                    aligned_lines = []
                    for line in lines:
                        line = line.strip()
                        if '=' in line:
                            parts = line.split('=', 1)
                            aligned_lines.append(f"{parts[0].strip()} &= {parts[1].strip()}")
                        else:
                            aligned_lines.append(line)
                    new_split = '\\begin{split}\n' + '\\\\\n'.join(aligned_lines) + '\n\\end{split}'
                    fixed_block = fixed_block.replace(split_content.group(0), new_split)
        
        # Fix other potential issues
        # Remove unnecessary spaces
        fixed_block = re.sub(r'\s+', ' ', fixed_block)
        
        # Replace original block with fixed block
        content = content.replace(block, fixed_block)
    
    # Additional fixes for specific cases
    # Fix geohash equation specifically
    geohash_fix = r'\text{geohash}(lat, lon, precision) = \text{base32\_encode}(\text{interleave\_bits}(lat, lon))'
    content = re.sub(
        r'\\text{geohash}\(lat, lon, \\text{precision}\) = \\text{base32_encode}\(\\text{interleave_bits}\(lat, lon\), \\text{precision}\)', 
        geohash_fix, 
        content
    )
    
    # Write the fixed content back only if changed
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed math equations in: {file_path}")
        return True
    return False

def main():
    """Main function to fix all RST files with math equations."""
    # Find all RST files
    rst_files = glob.glob('docs/source/**/*.rst', recursive=True)
    
    fixed_count = 0
    for file_path in rst_files:
        if fix_math_equations(file_path):
            fixed_count += 1
    
    print(f"Fixed math equations in {fixed_count} RST files")

if __name__ == "__main__":
    main() 