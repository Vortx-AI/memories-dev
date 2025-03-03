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
        
        # Get cold storage path and connection
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
                # Get relative path for storage
                rel_path = file_path.relative_to(cold_path)
                
                # Read parquet schema
                parquet_file = pq.ParquetFile(file_path)
                schema = parquet_file.schema
                
                # Get DuckDB table information
                table_name = f"parquet_data_{results['processed_files']}"
                
                # Query DuckDB for table metadata if available
                duckdb_metadata = {}
                if memory_manager.cold and memory_manager.cold.con:
                    try:
                        # Get table info
                        table_info = memory_manager.cold.con.execute(f"""
                            SELECT * FROM duckdb_tables() 
                            WHERE table_name = '{table_name}'
                        """).fetchone()
                        
                        if table_info:
                            duckdb_metadata["table_info"] = {
                                "table_name": table_info[0],
                                "schema_name": table_info[1],
                                "internal_name": table_info[2],
                                "temporary": table_info[3]
                            }
                            
                        # Get column info
                        column_info = memory_manager.cold.con.execute(f"""
                            SELECT * FROM duckdb_columns() 
                            WHERE table_name = '{table_name}'
                        """).fetchall()
                        
                        if column_info:
                            duckdb_metadata["columns"] = [{
                                "name": col[2],
                                "type": col[3],
                                "null": col[4],
                                "default": col[5],
                                "primary_key": col[6]
                            } for col in column_info]
                            
                        # Get table statistics if available
                        try:
                            stats = memory_manager.cold.con.execute(f"""
                                ANALYZE {table_name};
                                SELECT * FROM duckdb_statistics() 
                                WHERE table_name = '{table_name}'
                            """).fetchall()
                            
                            if stats:
                                duckdb_metadata["statistics"] = [{
                                    "column_name": stat[2],
                                    "has_null": stat[3],
                                    "distinct_count": stat[4],
                                    "min_value": stat[5],
                                    "max_value": stat[6]
                                } for stat in stats]
                        except Exception as e:
                            logger.warning(f"Could not get statistics for {table_name}: {e}")
                            
                    except Exception as e:
                        logger.warning(f"Could not get DuckDB metadata for {table_name}: {e}")
                
                # Process each column
                for i, field in enumerate(schema):
                    column_name = field.name
                    column_type = str(field.type)
                    
                    # Add to batch
                    column_batch.append(column_name)
                    metadata_batch.append({
                        "file_path": str(rel_path),
                        "absolute_path": str(file_path),
                        "table_name": table_name,
                        "column_index": i,
                        "column_type": column_type,
                        "column_metadata": field.metadata if field.metadata else {},
                        "duckdb_metadata": duckdb_metadata,
                        "file_stats": {
                            "num_row_groups": parquet_file.num_row_groups,
                            "num_rows": parquet_file.metadata.num_rows,
                            "created_by": parquet_file.metadata.created_by,
                            "format_version": parquet_file.metadata.format_version,
                            "size_bytes": file_path.stat().st_size
                        }
                    })
                    
                    # Process batch if full
                    if len(column_batch) >= batch_size:
                        _process_embedding_batch(memory_manager, encoder, column_batch, metadata_batch)
                        results["stored_columns"] += len(column_batch)
                        column_batch = []
                        metadata_batch = []
                
                results["processed_files"] += 1
                
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {e}")
                results["errors"].append(str(file_path))
                continue
        
        # Process any remaining columns
        if column_batch:
            _process_embedding_batch(memory_manager, encoder, column_batch, metadata_batch)
            results["stored_columns"] += len(column_batch)
        
        return results
        
    except Exception as e:
        logger.error(f"Error storing schema embeddings: {e}")
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
            key = f"schema_{metadata['table_name']}_{column_name}"
            
            # Store in red hot memory
            memory_manager.add_to_tier(
                tier="red_hot",
                data=embeddings[i].cpu().numpy(),
                key=key,
                metadata={
                    "column_name": column_name,
                    "table_name": metadata["table_name"],
                    "parquet_file": metadata["absolute_path"],
                    "relative_path": metadata["file_path"],
                    "column_index": metadata["column_index"],
                    "column_type": metadata["column_type"],
                    "column_metadata": metadata["column_metadata"],
                    "duckdb_metadata": metadata["duckdb_metadata"],
                    "file_stats": metadata["file_stats"]
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