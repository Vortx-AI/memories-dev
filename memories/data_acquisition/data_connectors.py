import os
from pathlib import Path
import json
import pandas as pd
import pyarrow.parquet as pq
import faiss
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime
from gensim.models import KeyedVectors
import pickle

def parquet_connector(file_path: str, faiss_storage: Optional[Dict] = None, word_vectors: Optional[KeyedVectors] = None) -> Dict[str, Any]:
    """
    Read parquet file metadata and save column names to FAISS using word embeddings.
    
    Args:
        file_path (str): Path to the parquet file
        faiss_storage (Dict, optional): Dictionary containing FAISS index and instance_id
        word_vectors (KeyedVectors, optional): Loaded word vectors model for embeddings
        
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
        
        # If FAISS storage is provided, save column names using word embeddings
        if faiss_storage and 'index' in faiss_storage and word_vectors:
            try:
                initial_vectors = faiss_storage['index'].ntotal
                
                # Get dimension from FAISS index
                dimension = faiss_storage['index'].d
                
                # Create word embeddings for each column name
                vectors = []
                for column in columns:
                    # Get word embedding for column name
                    vector = get_word_embedding(column, word_vectors, dimension)
                    vectors.append(vector)
                
                # Convert to numpy array
                vectors = np.array(vectors).astype('float32')
                
                # Add vectors to FAISS index
                faiss_storage['index'].add(vectors)
                
                # Save metadata for each column
                if 'metadata' not in faiss_storage:
                    faiss_storage['metadata'] = []
                
                # Add metadata for each column
                for i, column in enumerate(columns):
                    faiss_storage['metadata'].append({
                        'column_name': column,
                        'file_path': str(file_path),
                        'file_name': file_path.name,
                        'vector_id': initial_vectors + i
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
                    file_info = parquet_connector(str(file_path))
                    
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

def get_word_embedding(word: str, word_vectors: KeyedVectors, vector_size: int = 300) -> np.ndarray:
    """
    Get word embedding for a single word, handling multi-word phrases by averaging.
    
    Args:
        word (str): Word or phrase to get embedding for
        word_vectors (KeyedVectors): Loaded word vectors model
        vector_size (int): Size of the word vectors
        
    Returns:
        np.ndarray: Word embedding vector
    """
    # Convert to lowercase and split into words
    words = word.lower().split('_')
    vectors = []
    
    for w in words:
        try:
            # Try to get vector for the word
            vector = word_vectors[w]
            vectors.append(vector)
        except KeyError:
            print(f"Warning: '{w}' not found in vocabulary")
            continue
    
    if vectors:
        # Average the vectors if we found any
        avg_vector = np.mean(vectors, axis=0)
        # Normalize the vector
        norm = np.linalg.norm(avg_vector)
        if norm > 0:
            avg_vector = avg_vector / norm
        return avg_vector
    else:
        # Return zero vector if no words were found
        return np.zeros(vector_size)

def create_column_embeddings(metadata: list, word_vectors: KeyedVectors) -> pd.DataFrame:
    """
    Create embeddings for all column names in metadata.
    
    Args:
        metadata (list): List of metadata dictionaries containing column_name
        word_vectors (KeyedVectors): Loaded word vectors model
        
    Returns:
        pd.DataFrame: DataFrame with column names and their embeddings
    """
    # Create list to store results
    embedding_data = []
    
    # Process each metadata entry
    for meta in metadata:
        column_name = meta.get('column_name', '')
        if column_name:
            # Get embedding for column name
            vector = get_word_embedding(column_name, word_vectors)
            
            # Store result
            embedding_data.append({
                'column_name': column_name,
                'vector': vector,
                'file_name': meta.get('file_name', ''),
                'file_path': meta.get('file_path', '')
            })
    
    # Create DataFrame
    df = pd.DataFrame(embedding_data)
    return df

def find_similar_columns(query_word: str, df: pd.DataFrame, word_vectors: KeyedVectors, top_k: int = 5) -> pd.DataFrame:
    """
    Find columns most similar to a query word.
    
    Args:
        query_word (str): Word to find similar columns for
        df (pd.DataFrame): DataFrame with column embeddings
        word_vectors (KeyedVectors): Loaded word vectors model
        top_k (int): Number of top similar results to return
        
    Returns:
        pd.DataFrame: Top similar columns with similarity scores
    """
    # Get query vector
    query_vector = get_word_embedding(query_word, word_vectors)
    
    # Calculate similarities
    similarities = []
    for vector in df['vector']:
        similarity = np.dot(query_vector, vector)
        similarities.append(similarity)
    
    # Add similarities to DataFrame
    results_df = df.copy()
    results_df['similarity'] = similarities
    
    # Sort by similarity and get top k results
    results_df = results_df.sort_values('similarity', ascending=False).head(top_k)
    
    return results_df[['column_name', 'file_name', 'file_path', 'similarity']]

if __name__ == "__main__":
    # Example usage for single parquet
    file_path = "/path/to/your/file.parquet"
    single_index = parquet_connector(file_path)
    
    # Example usage for multiple parquets
    folder_path = "/path/to/parquet/folder"
    multiple_index = multiple_parquet_connector(folder_path, "my_multiple_parquet_index")
