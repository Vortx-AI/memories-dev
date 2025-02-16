import os
from pathlib import Path
import json
import pandas as pd
import pyarrow.parquet as pq
import faiss
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime
import pickle
from transformers import LoadModel

def parquet_connector(file_path: str, faiss_storage: Dict = None, model: LoadModel = None) -> Dict:
    """
    Process parquet file and update FAISS storage
    
    Args:
        file_path (str): Path to parquet file
        faiss_storage (Dict): FAISS storage dictionary
        model (LoadModel): Model for generating embeddings
        
    Returns:
        Dict: Updated FAISS storage
    """
    try:
        # Read parquet file
        df = pd.read_parquet(file_path)
        print(f"\nProcessing columns for FAISS vectors...")
        
        # Get column names
        columns = df.columns.tolist()
        
        # Generate embeddings for column names
        column_embeddings = model.get_embeddings(columns)
        
        # Add vectors to FAISS index
        for col_name, embedding in zip(columns, column_embeddings):
            try:
                # Add vector to FAISS
                faiss_storage['index'].add(np.array([embedding], dtype=np.float32))
                
                # Store metadata
                faiss_storage['metadata'].append({
                    'column_name': col_name,
                    'file_path': file_path,
                    'file_name': os.path.basename(file_path)
                })
                
            except Exception as e:
                print(f"Warning: Error processing column {col_name}: {str(e)}")
                continue
                
        return faiss_storage
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def multiple_parquet_connector(folder_path: str, faiss_storage: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Create detailed index of all parquet files in a folder and its subfolders.
    
    Args:
        folder_path (str): Path to the folder containing parquet files
        faiss_storage (Dict, optional): Dictionary containing FAISS index and instance_id
        
    Returns:
        Dict containing detailed information about all parquet files
    """
    results = {
        "processed_files": [],
        "error_files": [],
        "metadata": {
            "total_size": 0,
            "file_count": 0,
            "base_folder": str(folder_path)
        }
    }
    
    try:
        # Walk through all files in the directory and subdirectories
        for root, _, files in os.walk(folder_path):
            for file_name in files:
                if file_name.endswith('.parquet'):
                    file_path = Path(root) / file_name
                    
                    # Get file metadata and save to FAISS if provided
                    file_info = parquet_connector(str(file_path), faiss_storage)
                    
                    if "error" in file_info:
                        results["error_files"].append(file_info)
                    else:
                        results["processed_files"].append(file_info)
                        results["metadata"]["total_size"] += file_info["size_bytes"]
                        results["metadata"]["file_count"] += 1
        
        print("\nSummary:")
        print(f"Base folder: {results['metadata']['base_folder']}")
        print(f"Total parquet files found: {results['metadata']['file_count']}")
        print(f"Total size: {results['metadata']['total_size'] / (1024*1024):.2f} MB")
        print(f"Successfully processed: {len(results['processed_files'])}")
        print(f"Errors encountered: {len(results['error_files'])}")
        
        return results
        
    except Exception as e:
        print(f"Error in multiple_parquet_connector: {str(e)}")
        return results

if __name__ == "__main__":
    # Example usage for single parquet
    file_path = "/path/to/your/file.parquet"
    single_index = parquet_connector(file_path)
    
    # Example usage for multiple parquets
    folder_path = "/path/to/parquet/folder"
    multiple_index = multiple_parquet_connector(folder_path, "my_multiple_parquet_index")
