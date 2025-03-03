"""
Utility functions for adding cold memory schema to FAISS index.
"""

import logging
from typing import Dict, Any, List, Optional, Union, Tuple
from pathlib import Path
import pyarrow.parquet as pq
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import json
from datetime import datetime

from memories.core.memory_manager import MemoryManager

logger = logging.getLogger(__name__)

def get_cold_schema_info(memory_manager: MemoryManager) -> List[Dict[str, Any]]:
    """
    Get schema information for all parquet files in cold storage.
    
    Args:
        memory_manager: Initialized MemoryManager instance
        
    Returns:
        List of dictionaries containing schema information for each column
    """
    try:
        if not memory_manager.cold or not memory_manager.cold.con:
            raise ValueError("Cold storage not initialized in memory manager")
            
        # Get cold storage path
        cold_path = memory_manager.get_memory_path("cold")
        if not cold_path:
            raise ValueError("Cold memory path not found")
            
        schema_info = []
        
        # Get all tables from cold storage
        tables = memory_manager.cold.list_tables()
        
        for table in tables:
            table_name = table["table_name"]
            
            try:
                # Get DuckDB table metadata
                table_info = memory_manager.cold.con.execute(f"""
                    SELECT * FROM duckdb_tables() 
                    WHERE table_name = '{table_name}'
                """).fetchone()
                
                # Get column information
                column_info = memory_manager.cold.con.execute(f"""
                    SELECT * FROM duckdb_columns() 
                    WHERE table_name = '{table_name}'
                """).fetchall()
                
                # Get table statistics
                stats = memory_manager.cold.con.execute(f"""
                    ANALYZE {table_name};
                    SELECT * FROM duckdb_statistics() 
                    WHERE table_name = '{table_name}'
                """).fetchall()
                
                # Process each column
                for col in column_info:
                    col_stats = next((s for s in stats if s[2] == col[2]), None) if stats else None
                    
                    schema_info.append({
                        "table_name": table_name,
                        "file_path": table["file_path"],
                        "column_name": col[2],
                        "column_type": col[3],
                        "nullable": col[4],
                        "default": col[5],
                        "primary_key": col[6],
                        "statistics": {
                            "has_null": col_stats[3] if col_stats else None,
                            "distinct_count": col_stats[4] if col_stats else None,
                            "min_value": col_stats[5] if col_stats else None,
                            "max_value": col_stats[6] if col_stats else None
                        } if col_stats else None,
                        "table_metadata": {
                            "schema_name": table_info[1] if table_info else None,
                            "internal_name": table_info[2] if table_info else None,
                            "temporary": table_info[3] if table_info else None,
                            "num_rows": table.get("num_rows"),
                            "num_columns": table.get("num_columns"),
                            "theme": table.get("theme"),
                            "tag": table.get("tag")
                        }
                    })
                    
            except Exception as e:
                logger.warning(f"Error getting metadata for table {table_name}: {e}")
                continue
                
        return schema_info
        
    except Exception as e:
        logger.error(f"Error getting cold schema info: {e}")
        raise

def add_cold_schema_to_faiss(
    memory_manager: MemoryManager,
    embedding_model: str = "all-MiniLM-L6-v2",
    batch_size: int = 32,
    force_cpu: bool = True
) -> Dict[str, Any]:
    """
    Add schema information from cold storage to FAISS index in red hot memory.
    
    Args:
        memory_manager: Initialized MemoryManager instance
        embedding_model: Name of the sentence transformer model to use
        batch_size: Batch size for processing embeddings
        force_cpu: Whether to force CPU usage for FAISS
        
    Returns:
        Dict containing:
            processed_tables: Number of tables processed
            processed_columns: Number of columns processed
            errors: List of errors encountered
    """
    try:
        results = {
            "processed_tables": 0,
            "processed_columns": 0,
            "errors": []
        }
        
        # Get schema information
        schema_info = get_cold_schema_info(memory_manager)
        
        if not schema_info:
            logger.warning("No schema information found in cold storage")
            return results
            
        # Initialize embedding model
        encoder = SentenceTransformer(embedding_model)
        
        # Process in batches
        for i in range(0, len(schema_info), batch_size):
            batch = schema_info[i:i + batch_size]
            
            try:
                # Prepare column names and metadata
                column_names = [f"{info['table_name']}.{info['column_name']}" for info in batch]
                
                # Generate embeddings
                embeddings = encoder.encode(column_names, convert_to_tensor=True)
                
                # Store each embedding with its metadata
                for j, (embedding, info) in enumerate(zip(embeddings, batch)):
                    key = f"schema_{info['table_name']}_{info['column_name']}"
                    
                    # Store in red hot memory
                    memory_manager.add_to_tier(
                        tier="red_hot",
                        data=embedding.cpu().numpy(),
                        key=key,
                        metadata={
                            "table_name": info["table_name"],
                            "column_name": info["column_name"],
                            "file_path": info["file_path"],
                            "column_type": info["column_type"],
                            "nullable": info["nullable"],
                            "default": info["default"],
                            "primary_key": info["primary_key"],
                            "statistics": info["statistics"],
                            "table_metadata": info["table_metadata"],
                            "indexed_at": datetime.now().isoformat()
                        }
                    )
                
                # Update counts
                results["processed_columns"] += len(batch)
                processed_tables = {info["table_name"] for info in batch}
                results["processed_tables"] = len(processed_tables)
                
            except Exception as e:
                logger.error(f"Error processing batch: {e}")
                results["errors"].append(str(e))
                continue
        
        logger.info(f"Added {results['processed_columns']} columns from {results['processed_tables']} tables to FAISS")
        return results
        
    except Exception as e:
        logger.error(f"Error adding cold schema to FAISS: {e}")
        raise

def find_similar_columns(
    memory_manager: MemoryManager,
    query: str,
    embedding_model: str = "all-MiniLM-L6-v2",
    k: int = 5,
    threshold: float = 0.5,
    type_filter: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Find similar columns in the FAISS index based on semantic similarity.
    
    Args:
        memory_manager: Initialized MemoryManager instance
        query: Search query (column name or description)
        embedding_model: Name of the sentence transformer model to use
        k: Number of results to return
        threshold: Similarity threshold (0-1)
        type_filter: Optional filter for column type
        
    Returns:
        List of similar columns with their metadata and similarity scores
    """
    try:
        # Initialize embedding model
        encoder = SentenceTransformer(embedding_model)
        
        # Generate query embedding
        query_embedding = encoder.encode([query], convert_to_tensor=True)[0]
        
        # Define metadata filter if type_filter is provided
        metadata_filter = None
        if type_filter:
            metadata_filter = lambda meta: meta["column_type"].lower() == type_filter.lower()
        
        # Search in red hot memory
        results = memory_manager.search_vectors(
            query_vector=query_embedding.cpu().numpy(),
            k=k,
            metadata_filter=metadata_filter
        )
        
        # Process results
        similar_columns = []
        for result in results:
            similarity = 1 - result.distance
            if similarity >= threshold:
                similar_columns.append({
                    "table_name": result.metadata["table_name"],
                    "column_name": result.metadata["column_name"],
                    "similarity": float(similarity),
                    "metadata": result.metadata
                })
        
        return similar_columns
        
    except Exception as e:
        logger.error(f"Error finding similar columns: {e}")
        raise 