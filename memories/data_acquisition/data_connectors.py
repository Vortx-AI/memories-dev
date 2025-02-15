import os
from pathlib import Path
import json
import pandas as pd
import pyarrow.parquet as pq
from typing import Dict, List, Any
from datetime import datetime
import uuid

def parquet_connector(file_path: str) -> List[Dict[str, Any]]:
    """
    Read a parquet file and return its data.
    
    Args:
        file_path (str): Path to the parquet file
        
    Returns:
        List[Dict[str, Any]]: Data from the parquet file
    """
    try:
        # Read the parquet file
        df = pd.read_parquet(file_path)
        
        # Convert to list of dictionaries
        return df.to_dict('records')
        
    except Exception as e:
        print(f"Error processing parquet file: {str(e)}")
        return []

def multiple_parquet_connector(folder_path: str, output_file_name: str = None) -> Dict[str, Any]:
    """
    Create detailed index of all parquet files in a folder and its subfolders.
    
    Args:
        folder_path (str): Path to the folder containing parquet files
        output_file_name (str, optional): Name for the output JSON file (without .json extension)
                                        If not provided, generates a unique name
        
    Returns:
        Dict containing detailed information about all parquet files
    """
    # Convert folder_path to Path object
    folder_path = Path(folder_path)
    
    # Set up data directory path relative to project root
    data_dir = Path(__file__).parents[3] / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique output name if not provided
    if output_file_name is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        output_file_name = f"multiple_parquet_index_{timestamp}_{unique_id}"
    
    results = {
        "processed_files": [],
        "error_files": [],
        "metadata": {
            "total_size": 0,
            "file_count": 0,
            "base_folder": str(folder_path)
        }
    }
    
    # Walk through all files in the directory and subdirectories
    for root, _, files in os.walk(folder_path):
        for file_name in files:
            if file_name.endswith('.parquet'):
                file_path = Path(root) / file_name
                
                # Update file count and size
                results["metadata"]["file_count"] += 1
                results["metadata"]["total_size"] += file_path.stat().st_size
                
                try:
                    # Read parquet file
                    table = pq.read_table(str(file_path))
                    df = table.to_pandas()
                    
                    # Get column information
                    columns = list(df.columns)
                    
                    # Identify location columns
                    location_columns = [col for col in columns if col.lower() in 
                                     ['geometry', 'geom', 'location', 'point', 'shape', 
                                      'latitude', 'longitude', 'lat', 'lon', 'coordinates']]
                    
                    # Get sample data (first row)
                    sample_data = {}
                    first_row = df.iloc[0]
                    for col in columns:
                        # Convert to string representation, handle geometry objects
                        val = first_row[col]
                        try:
                            if 'geometry' in str(type(val)).lower():
                                sample_data[col] = str(val)
                            else:
                                sample_data[col] = val
                        except:
                            sample_data[col] = str(val)
                    
                    file_info = {
                        "file_name": file_name,
                        "file_path": str(file_path),
                        "relative_path": str(file_path.relative_to(folder_path)),
                        "size_bytes": file_path.stat().st_size,
                        "columns": columns,
                        "location_columns": location_columns,
                        "sample_data": sample_data,
                        "row_count": len(df)
                    }
                    
                    results["processed_files"].append(file_info)
                    print(f"Processed: {file_path}")
                    
                except Exception as e:
                    results["error_files"].append({
                        "file_name": file_name,
                        "file_path": str(file_path),
                        "relative_path": str(file_path.relative_to(folder_path)),
                        "error": str(e),
                        "size_bytes": file_path.stat().st_size
                    })
                    print(f"Error processing {file_path}: {str(e)}")
    
    # Create output path with provided or generated name
    output_path = data_dir / f"{output_file_name}.json"
    
    # Save results to JSON file in project's data directory
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nAnalysis saved to: {output_path}")
    
    # Print summary
    print("\nSummary:")
    print(f"Base folder: {results['metadata']['base_folder']}")
    print(f"Total parquet files found: {results['metadata']['file_count']}")
    print(f"Total size: {results['metadata']['total_size'] / (1024*1024):.2f} MB")
    print(f"Successfully processed: {len(results['processed_files'])}")
    print(f"Errors encountered: {len(results['error_files'])}")
    
    return results

if __name__ == "__main__":
    # Example usage for single parquet
    file_path = "/path/to/your/file.parquet"
    single_index = parquet_connector(file_path)
    
    # Example usage for multiple parquets
    folder_path = "/path/to/parquet/folder"
    multiple_index = multiple_parquet_connector(folder_path, "my_multiple_parquet_index")
