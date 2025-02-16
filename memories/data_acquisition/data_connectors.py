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

def parquet_connector(file_path: str, faiss_storage: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Read parquet file metadata and save column names as vectors in FAISS if provided.
    
    Args:
        file_path (str): Path to the parquet file
        faiss_storage (Dict, optional): Dictionary containing FAISS index and instance_id
        
    Returns:
        Dict[str, Any]: Metadata and schema information about the parquet file
    """
    try:
        file_path = Path(file_path)
        
        # Read parquet metadata only
        parquet_file = pq.ParquetFile(str(file_path))
        schema = parquet_file.schema
        
        # Get column information
        columns = [field.name for field in schema]
        
        # Identify location columns
        location_columns = [col for col in columns if col.lower() in 
                         ['geometry', 'geom', 'location', 'point', 'shape', 
                          'latitude', 'longitude', 'lat', 'lon', 'coordinates']]
        
        # Get file stats
        file_stats = file_path.stat()
        
        file_info = {
            "file_name": file_path.name,
            "file_path": str(file_path),
            "relative_path": str(file_path.relative_to(file_path.parent)),
            "size_bytes": file_stats.st_size,
            "columns": columns,
            "location_columns": location_columns,
            "num_row_groups": parquet_file.num_row_groups,
            "metadata": {
                "created": datetime.fromtimestamp(file_stats.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                "format_version": parquet_file.metadata.format_version,
                "num_rows": parquet_file.metadata.num_rows,
                "num_columns": len(columns),
                "schema_arrow": str(schema)
            }
        }
        
        # If FAISS storage is provided, save column names as vectors
        if faiss_storage and 'index' in faiss_storage:
            try:
                initial_vectors = faiss_storage['index'].ntotal
                dimension = faiss_storage['index'].d
                
                # Read the actual data for the columns to create meaningful vectors
                df = pq.read_table(str(file_path)).to_pandas()
                vectors = []
                
                for column in columns:
                    # Create a meaningful vector based on column data
                    if column in df.columns:
                        # Get sample data from the column
                        sample_data = df[column].dropna().head(100).astype(str).tolist()
                        # Create a simple frequency-based vector
                        vector = np.zeros(dimension, dtype='float32')
                        
                        # Fill vector based on data characteristics
                        if sample_data:
                            # Use basic statistics if numerical
                            if df[column].dtype in ['int64', 'float64']:
                                numeric_data = pd.to_numeric(df[column], errors='coerce')
                                vector[:4] = [
                                    numeric_data.mean() if not pd.isna(numeric_data.mean()) else 0,
                                    numeric_data.std() if not pd.isna(numeric_data.std()) else 0,
                                    numeric_data.min() if not pd.isna(numeric_data.min()) else 0,
                                    numeric_data.max() if not pd.isna(numeric_data.max()) else 0
                                ]
                            
                            # Use string characteristics if string
                            str_data = df[column].astype(str)
                            vector[4:8] = [
                                str_data.str.len().mean(),
                                len(str_data.unique()),
                                str_data.str.count('[0-9]').mean(),
                                str_data.str.count('[A-Za-z]').mean()
                            ]
                        
                        # Normalize the vector
                        norm = np.linalg.norm(vector)
                        if norm > 0:
                            vector = vector / norm
                    else:
                        # Fallback to random vector if column not found
                        vector = np.random.rand(dimension).astype('float32')
                        vector = vector / np.linalg.norm(vector)
                    
                    vectors.append(vector)
                
                # Convert to numpy array and add to FAISS
                vectors_array = np.array(vectors, dtype='float32')
                faiss_storage['index'].add(vectors_array)
                
                # Save metadata for each column
                if 'metadata' not in faiss_storage:
                    faiss_storage['metadata'] = []
                
                # Add metadata for each column
                for i, column in enumerate(columns):
                    vector_id = initial_vectors + i
                    faiss_storage['metadata'].append({
                        'column_name': column,
                        'file_path': str(file_path),
                        'file_name': file_path.name,
                        'vector_id': vector_id
                    })
                
                final_vectors = faiss_storage['index'].ntotal
                vectors_added = final_vectors - initial_vectors
                
                print(f"\n[ParquetConnector] FAISS Update for {file_path.name}:")
                print(f"Initial vectors: {initial_vectors}")
                print(f"Vectors added: {vectors_added}")
                print(f"Final vectors: {final_vectors}")
                print(f"Added columns: {', '.join(columns)}")
                
                # Save updated FAISS index
                if 'instance_id' in faiss_storage:
                    faiss_dir = os.path.join(os.getenv("PROJECT_ROOT", ""), "data", "faiss")
                    index_path = os.path.join(faiss_dir, f"index_{faiss_storage['instance_id']}.faiss")
                    faiss.write_index(faiss_storage['index'], index_path)
                    
                    # Save metadata
                    metadata_path = os.path.join(faiss_dir, f"metadata_{faiss_storage['instance_id']}.pkl")
                    with open(metadata_path, 'wb') as f:
                        pickle.dump(faiss_storage['metadata'], f)
                    
                    print(f"[ParquetConnector] Saved FAISS index and metadata for instance: {faiss_storage['instance_id']}")
                
            except Exception as e:
                print(f"Error saving to FAISS: {str(e)}")
        
        print(f"[ParquetConnector] Processed metadata for: {file_path}")
        print(f"[ParquetConnector] Found {len(columns)} columns, {file_info['metadata']['num_rows']} rows")
        
        return file_info
            
    except Exception as e:
        print(f"Error processing parquet file: {str(e)}")
        return {
            "file_name": Path(file_path).name,
            "file_path": str(file_path),
            "error": str(e)
        }

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
