"""
Schema embeddings utility for extracting and storing parquet schema information.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import pyarrow.parquet as pq
import numpy as np
from sentence_transformers import SentenceTransformer
from memories.core.memory_manager import MemoryManager

logger = logging.getLogger(__name__)

def store_schema_embeddings(
    memory_manager: MemoryManager,
    embedding_model: str = "all-MiniLM-L6-v2",
    batch_size: int = 32
) -> Dict[str, Any]:
    """
    Extract schema from parquet files in cold memory and store column embeddings in red hot memory.
    Uses fast schema reading without loading entire files.
    
    Args:
        memory_manager: Initialized MemoryManager instance
        embedding_model: Name of the sentence transformer model to use
        batch_size: Batch size for processing embeddings
        
    Returns:
        Dict containing:
            processed_files: Number of files processed
            stored_columns: Number of column embeddings stored
            errors: List of files that had errors
    """
    try:
        # Initialize results
        results = {
            "processed_files": 0,
            "stored_columns": 0,
            "errors": []
        }
        
        # Get cold storage path
        cold_path = memory_manager.get_memory_path("cold")
        if not cold_path:
            raise ValueError("Cold memory path not found")
            
        # Initialize embedding model
        encoder = SentenceTransformer(embedding_model)
        
        # Find all parquet files
        parquet_files = list(cold_path.rglob("*.parquet"))
        if not parquet_files:
            logger.warning("No parquet files found in cold storage")
            return results
            
        # Process files in batches
        column_batch = []
        metadata_batch = []
        
        for file_path in parquet_files:
            try:
                # Read only schema (fast operation)
                schema = pq.read_schema(file_path)
                
                # Get relative path for metadata
                rel_path = file_path.relative_to(cold_path)
                abs_path = str(file_path.absolute())
                
                # Process each column
                for field in schema:
                    column_name = field.name
                    column_batch.append(column_name)
                    
                    # Prepare metadata
                    metadata = {
                        "file_path": str(rel_path),
                        "absolute_path": abs_path,
                        "column_type": str(field.type),
                        "nullable": field.nullable,
                        "field_metadata": field.metadata if field.metadata else {},
                        "schema_path": [str(p) for p in field.path],
                    }
                    metadata_batch.append(metadata)
                    
                    # Process batch if size reached
                    if len(column_batch) >= batch_size:
                        _process_embedding_batch(
                            memory_manager,
                            encoder,
                            column_batch,
                            metadata_batch
                        )
                        column_batch = []
                        metadata_batch = []
                        
                results["processed_files"] += 1
                results["stored_columns"] += len(schema)
                
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                results["errors"].append(str(file_path))
                continue
                
        # Process remaining batch
        if column_batch:
            _process_embedding_batch(
                memory_manager,
                encoder,
                column_batch,
                metadata_batch
            )
            
        logger.info(f"Schema embeddings stored: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Failed to store schema embeddings: {e}")
        raise

def _process_embedding_batch(
    memory_manager: MemoryManager,
    encoder: SentenceTransformer,
    column_batch: List[str],
    metadata_batch: List[Dict[str, Any]]
) -> None:
    """Process a batch of column names and store their embeddings."""
    try:
        # Generate embeddings for the batch
        embeddings = encoder.encode(column_batch, convert_to_tensor=True)
        
        # Store each embedding with its metadata
        for i, (column_name, metadata) in enumerate(zip(column_batch, metadata_batch)):
            # Generate unique key
            key = f"schema_{metadata['file_path']}_{column_name}"
            
            # Store in red hot memory
            memory_manager.add_to_tier(
                tier="red_hot",
                data=embeddings[i].cpu().numpy(),
                key=key,
                metadata={
                    "column_name": column_name,
                    "parquet_file": metadata["absolute_path"],
                    "relative_path": metadata["file_path"],
                    "schema_info": metadata
                }
            )
            
    except Exception as e:
        logger.error(f"Error processing embedding batch: {e}")
        raise

def find_similar_columns(
    memory_manager: MemoryManager,
    column_name: str,
    embedding_model: str = "all-MiniLM-L6-v2",
    similarity_threshold: float = 0.3,
    max_results: int = 10
) -> List[Dict[str, Any]]:
    """
    Find columns with similar names to the input. Returns exact match if found,
    otherwise returns all columns with distance less than threshold.
    
    Args:
        memory_manager: Initialized MemoryManager instance
        column_name: Column name to search for
        embedding_model: Name of the sentence transformer model to use
        similarity_threshold: Maximum distance threshold for similarity (default: 0.3)
        max_results: Maximum number of results to return if no exact match
        
    Returns:
        List of dictionaries containing:
            column_name: Name of the similar column
            parquet_file: Path to the parquet file
            similarity: Similarity score
            metadata: Additional column metadata
    """
    try:
        # Initialize embedding model
        encoder = SentenceTransformer(embedding_model)
        
        # Generate embedding for query
        query_embedding = encoder.encode([column_name], convert_to_tensor=True)[0]
        
        # Search in red hot memory
        results = memory_manager.search_vectors(
            query_vector=query_embedding.cpu().numpy(),
            k=max_results,
            metadata_filter=None  # No filtering, we want all columns
        )
        
        if not results:
            logger.info(f"No similar columns found for '{column_name}'")
            return []
            
        # Process results
        similar_columns = []
        exact_match = None
        
        for result in results:
            similarity = 1 - result.distance  # Convert distance to similarity
            
            # Skip if below threshold
            if similarity < (1 - similarity_threshold):
                continue
                
            match_info = {
                "column_name": result.metadata["column_name"],
                "parquet_file": result.metadata["parquet_file"],
                "similarity": float(similarity),  # Convert to native Python float
                "metadata": result.metadata["schema_info"]
            }
            
            # Check for exact match (case-insensitive)
            if result.metadata["column_name"].lower() == column_name.lower():
                exact_match = match_info
            else:
                similar_columns.append(match_info)
        
        # Return only exact match if found
        if exact_match:
            logger.info(f"Found exact match for column '{column_name}'")
            return [exact_match]
            
        # Sort by similarity and return all matches above threshold
        similar_columns.sort(key=lambda x: x["similarity"], reverse=True)
        
        if similar_columns:
            logger.info(f"Found {len(similar_columns)} similar columns for '{column_name}'")
        else:
            logger.info(f"No columns found within similarity threshold for '{column_name}'")
            
        return similar_columns
        
    except Exception as e:
        logger.error(f"Error finding similar columns: {e}")
        raise 