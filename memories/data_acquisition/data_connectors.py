import os
from pathlib import Path
import json
import pandas as pd
import pyarrow.parquet as pq
import dask.dataframe as dd
from typing import Dict, List, Any, Generator, Optional
from datetime import datetime
import uuid
import numpy as np
from gensim.models import Word2Vec, KeyedVectors
import faiss
import pickle

def get_word_embedding(word: str, word_vectors, vector_size: int = 100) -> np.ndarray:
    """
    Get word embedding for a word/phrase using the provided GloVe model.
    
    Args:
        word (str): The word or phrase.
        word_vectors: Gensim KeyedVectors instance for GloVe.
        vector_size (int): Expected dimension of the embeddings (default 100, matching glove.6B.100d).
        
    Returns:
        np.ndarray: The normalized embedding vector.
    """
    try:
        words = word.lower().split('_')  # Support underscore-separated words
        vectors = []
        for w in words:
            try:
                vector = word_vectors[w]
                vectors.append(vector)
            except KeyError:
                print(f"Warning: '{w}' not found in GloVe vocabulary.")
        if vectors:
            avg_vector = np.mean(vectors, axis=0)
            norm = np.linalg.norm(avg_vector)
            if norm > 0:
                return (avg_vector / norm).astype('float32')
            return avg_vector.astype('float32')
        else:
            print(f"No vectors found for word '{word}', returning zero vector.")
            return np.zeros(vector_size, dtype='float32')
    except Exception as e:
        print(f"Error in get_word_embedding for word '{word}': {str(e)}")
        return np.zeros(vector_size, dtype='float32')

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
        
        # Read parquet metadata
        parquet_file = pq.ParquetFile(str(file_path))
        schema = parquet_file.schema
        columns = [field.name for field in schema]
        
        # Process FAISS storage if provided
        if faiss_storage and word_vectors and 'index' in faiss_storage:
            try:
                initial_vectors = faiss_storage['index'].ntotal
                dimension = faiss_storage['index'].d
                
                print(f"\nProcessing {len(columns)} columns for FAISS storage...")
                print(f"FAISS dimension: {dimension}")
                print(f"Word vectors dimension: {word_vectors.vector_size}")
                
                # Create embeddings for column names
                vectors = []
                valid_columns = []
                
                for column in columns:
                    try:
                        print(f"\nProcessing column: {column}")
                        vector = get_word_embedding(column, word_vectors, dimension)
                        
                        # Verify vector is valid
                        if not np.all(vector == 0) and len(vector) == dimension:
                            print(f"Created valid vector for '{column}' with dimension {len(vector)}")
                            vectors.append(vector)
                            valid_columns.append(column)
                        else:
                            print(f"Skipping invalid vector for '{column}'")
                    except Exception as e:
                        print(f"Error processing column '{column}': {str(e)}")
                        continue
                
                if vectors:
                    vectors = np.array(vectors).astype('float32')
                    print(f"\nCreated {len(vectors)} valid vectors with shape {vectors.shape}")
                    
                    # Verify vector dimensions
                    if vectors.shape[1] != dimension:
                        print(f"Warning: Vector dimension mismatch. Expected {dimension}, got {vectors.shape[1]}")
                        vectors = np.pad(vectors, ((0, 0), (0, dimension - vectors.shape[1])))
                        print(f"Padded vectors to shape {vectors.shape}")
                    
                    # Add vectors to FAISS index
                    try:
                        print("\nAdding vectors to FAISS index...")
                        faiss_storage['index'].add(vectors)
                        
                        # Initialize metadata list if not exists
                        if 'metadata' not in faiss_storage:
                            faiss_storage['metadata'] = []
                        
                        # Identify location columns
                        location_columns = [col for col in columns if col.lower() in 
                                         ['geometry', 'geom', 'location', 'point', 'shape', 
                                          'latitude', 'longitude', 'lat', 'lon', 'coordinates']]
                        
                        # Get geometry column and type; here we set it explicitly
                        geometry_column = 'geom' if 'geom' in columns else None
                        geometry_type = 'point'  # Set default geometry type as point
                        
                        # Add metadata for each column
                        for i, column in enumerate(valid_columns):
                            faiss_storage['metadata'].append({
                                'column_name': column,
                                'file_path': str(file_path),
                                'file_name': file_path.name,
                                'vector_id': initial_vectors + i,
                                'geometry_column': geometry_column,
                                'geometry_type': geometry_type
                            })
                        
                        final_vectors = faiss_storage['index'].ntotal
                        vectors_added = final_vectors - initial_vectors
                        
                        print(f"\n[ParquetConnector] FAISS Update for {file_path.name}:")
                        print(f"Initial vectors: {initial_vectors}")
                        print(f"Vectors added: {vectors_added}")
                        print(f"Final vectors: {final_vectors}")
                        print(f"Added columns: {', '.join(valid_columns)}")
                        
                    except Exception as e:
                        print(f"Error adding vectors to FAISS: {str(e)}")
                        print(f"Vector shape: {vectors.shape}")
                        print(f"FAISS dimension: {dimension}")
                else:
                    print("No valid vectors created for columns")
                
                # Save FAISS index and metadata
                if 'instance_id' in faiss_storage:
                    try:
                        faiss_dir = Path(os.getenv("PROJECT_ROOT", "")) / "data" / "faiss"
                        faiss_dir.mkdir(parents=True, exist_ok=True)
                        
                        index_path = faiss_dir / f"index_{faiss_storage['instance_id']}.faiss"
                        metadata_path = faiss_dir / f"metadata_{faiss_storage['instance_id']}.pkl"
                        
                        faiss.write_index(faiss_storage['index'], str(index_path))
                        with open(metadata_path, 'wb') as f:
                            pickle.dump(faiss_storage['metadata'], f)
                        
                        print(f"[ParquetConnector] Saved FAISS index and metadata for instance: {faiss_storage['instance_id']}")
                    except Exception as e:
                        print(f"Error saving FAISS index and metadata: {str(e)}")
                
            except Exception as e:
                print(f"Error in FAISS processing: {str(e)}")
                import traceback
                traceback.print_exc()
        
        # Identify location columns
        location_columns = [col for col in columns if col.lower() in 
                         ['geometry', 'geom', 'location', 'point', 'shape', 
                          'latitude', 'longitude', 'lat', 'lon', 'coordinates']]
        
        # Get geometry column and type
        geometry_column = 'geom' if 'geom' in columns else None
        geometry_type = 'point'  # Set default geometry type as point
        
        # Get file stats
        file_stats = file_path.stat()
        
        file_info = {
            "file_name": file_path.name,
            "file_path": str(file_path),
            "relative_path": str(file_path.relative_to(file_path.parent)),
            "size_bytes": file_stats.st_size,
            "columns": columns,
            "location_columns": location_columns,
            "geometry_column": geometry_column,
            "geometry_type": geometry_type,
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
        import traceback
        traceback.print_exc()
        return {
            "file_name": Path(file_path).name,
            "file_path": str(file_path),
            "error": str(e)
        }

def multiple_parquet_connector(
    folder_path: str,
    faiss_storage: Optional[Dict[str, Any]] = None,
    word_vectors: Optional[Any] = None,
    output_file_name: Optional[str] = None
) -> Dict[str, Any]:
    """Process multiple parquet files recursively."""
    
    # Add debug prints
    print(f"Searching for parquet files in: {folder_path}")
    print("Directory exists:", os.path.exists(folder_path))
    print("Is directory:", os.path.isdir(folder_path))
    
    # List all files in directory for debugging
    print("\nFiles in directory:")
    for root, dirs, files in os.walk(folder_path):
        print(f"\nIn directory: {root}")
        print("Subdirectories:", dirs)
        print("Files:", files)
    
    # Get project root and set up data directory
    project_root = os.getenv("PROJECT_ROOT")
    if not project_root:
        raise ValueError("PROJECT_ROOT environment variable not set")
    
    data_dir = Path(project_root) / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    results = {
        "processed_files": [],
        "error_files": [],
        "metadata": {
            "total_size": 0,
            "file_count": 0,
            "base_folder": str(folder_path)
        }
    }
    
    folder_path_obj = Path(folder_path)
    
    # If no specific output file name is provided, create one using a timestamp
    if output_file_name is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file_name = f"multiple_parquet_schema_index_{timestamp}.json"
    
    # Use rglob to find all files ending in .parquet (case-insensitive)
    for file_path in folder_path_obj.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() == ".parquet":
            print(f"\nProcessing file: {file_path}")
            results["metadata"]["file_count"] += 1
            results["metadata"]["total_size"] += file_path.stat().st_size
            
            try:
                file_info = parquet_connector(str(file_path), faiss_storage, word_vectors)
                results["processed_files"].append(file_info)
                
                # Display the cumulative number of vectors added after processing this file
                if faiss_storage is not None:
                    total_vectors = faiss_storage['index'].ntotal
                    print(f"Total vectors after processing: {total_vectors}")
            except Exception as e:
                err_info = {
                    "file_name": file_path.name,
                    "file_path": str(file_path),
                    "error": str(e)
                }
                results["error_files"].append(err_info)
                print(f"Error processing {file_path}: {e}")
    
    # Save the aggregated result into a JSON file in the project's data directory
    output_path = data_dir / output_file_name
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\nSchema analysis saved to: {output_path}")
    print("\nSummary:")
    print(f"Base folder: {results['metadata']['base_folder']}")
    print(f"Total parquet files found: {results['metadata']['file_count']}")
    print(f"Total size: {results['metadata']['total_size'] / (1024*1024):.2f} MB")
    print(f"Successfully processed: {len(results['processed_files'])}")
    print(f"Errors encountered: {len(results['error_files'])}")
    
    if faiss_storage:
        print(f"\nFAISS index instance_id: {faiss_storage.get('instance_id', 'N/A')}")
        print(f"Total vectors stored: {faiss_storage['index'].ntotal}")
    
    return results

if __name__ == "__main__":
    # Example usage
    try:
        # Load word vectors - using same GloVe embeddings as Agent_L1
        models_dir = os.path.join(os.getenv("PROJECT_ROOT", ""), "data", "models")
        vectors_path = os.path.join(models_dir, "glove.6B.100d.txt.word2vec")
        print(f"Loading word vectors from {vectors_path}")
        word_vectors = KeyedVectors.load_word2vec_format(vectors_path)
        print("Word vectors loaded successfully")
        
        # Process multiple parquet files
        folder_path = "/path/to/parquet/folder"
        results = multiple_parquet_connector(folder_path, word_vectors)
        
    except Exception as e:
        print(f"Error in main execution: {str(e)}")
