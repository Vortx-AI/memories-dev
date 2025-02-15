import os
from pathlib import Path
import json
import pandas as pd
import pyarrow.parquet as pq
from typing import Dict, List, Any

def index_overture_parquet(base_path: str = "./overture_data") -> Dict[str, List[str]]:
    """
    Analyze Overture local parquet files and record any processing errors.
    
    Args:
        base_path (str): Base directory containing Overture parquet files
        
    Returns:
        Dict containing lists of processed and error files
    """
    # Convert base_path to Path object
    base_path = Path(base_path)
    
    # Set up data directory path relative to project root
    data_dir = Path(__file__).parents[3] / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    results = {
        "processed_files": [],
        "error_files": []
    }
    
    # Walk through all files in the directory
    for root, _, files in os.walk(base_path):
        for file_name in files:
            if file_name.endswith('.parquet'):
                file_path = Path(root) / file_name
                
                try:
                    # Try reading the parquet file
                    table = pq.read_table(str(file_path))
                    results["processed_files"].append({
                        "file_name": file_name,
                        "file_path": str(file_path)
                    })
                except Exception as e:
                    results["error_files"].append({
                        "file_name": file_name,
                        "file_path": str(file_path),
                        "error": str(e)
                    })
                    print(f"Error processing {file_name}: {str(e)}")
    
    # Save results to JSON file in project's data directory
    output_path = data_dir / "overture_parquet_index.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nAnalysis saved to: {output_path}")
    
    # Print summary
    print("\nSummary:")
    print(f"Total processed files: {len(results['processed_files'])}")
    print(f"Total error files: {len(results['error_files'])}")
    
    return results

if __name__ == "__main__":
    # Run the analysis
    error_details = index_overture_parquet()
