import os
from pathlib import Path
import json
import pandas as pd
import pyarrow.parquet as pq
from typing import Dict, List, Any

def analyze_parquet_files(base_path: str = "parquet folder path",
                         output_dir: str = "./") -> Dict[str, List[str]]:
    """
    Traverse through parquet files and record errors.
    
    Args:
        base_path (str): Base directory path containing parquet files
        output_dir (str): Directory to save the output JSON file
        
    Returns:
        Dict[str, List[str]]: Dictionary containing processed files and errors
        
    Raises:
        ValueError: If base_path does not exist or is not a directory
    """
    base_path = Path(base_path)
    if not base_path.exists() or not base_path.is_dir():
        raise ValueError(f"Base path '{base_path}' does not exist or is not a directory")
    
    results = {
        'processed_files': [],
        'error_files': []
    }
    
    output_dir = Path(output_dir)
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Walk through all directories and files
    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file.endswith('.parquet'):
                file_path = str(Path(root) / file)
                try:
                    # Try reading the parquet file without the 'rows' parameter
                    table = pq.read_table(file_path)
                    results['processed_files'].append({
                        'file_name': file,
                        'file_path': file_path
                    })
                except Exception as e:
                    results['error_files'].append({
                        'file_name': file,
                        'file_path': file_path,
                        'error': str(e)
                    })
                    print(f"Error processing {file}: {str(e)}")

    # Save results to JSON file in the specified output directory
    output_path = output_dir / "parquet_errors.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nAnalysis saved to: {output_path}")
    
    return results
