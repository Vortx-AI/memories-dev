"""
Utility functions for transferring cold storage schema to red hot memory.
"""

import logging
from typing import Dict, Any, List, Optional, Union, Tuple
from pathlib import Path
import pyarrow.parquet as pq
import numpy as np
import faiss
import json
from datetime import datetime
import argparse
import os
import tempfile
import shutil

# Set up temporary directory
def setup_temp_dir():
    """Create and set up a temporary directory for the script."""
    temp_dir = Path.home() / '.memories_temp'
    temp_dir.mkdir(exist_ok=True)
    os.environ['TMPDIR'] = str(temp_dir)
    os.environ['TEMP'] = str(temp_dir)
    os.environ['TMP'] = str(temp_dir)
    tempfile.tempdir = str(temp_dir)
    return temp_dir

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set up temporary directory before importing sentence_transformers
temp_dir = setup_temp_dir()
try:
    from sentence_transformers import SentenceTransformer
except Exception as e:
    logger.error(f"Error importing SentenceTransformer: {e}")
    raise

from memories.core.memory_manager import MemoryManager

def get_cold_schema_info(memory_manager: MemoryManager) -> List[Dict[str, Any]]:
    """
    Extract schema information from all parquet files in cold storage.
    
    Args:
        memory_manager: Initialized MemoryManager instance with cold storage enabled
        
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

def transfer_to_redhot(
    memory_manager: MemoryManager,
    embedding_model: str = "all-MiniLM-L6-v2",
    batch_size: int = 32,
    force_cpu: bool = True
) -> Dict[str, Any]:
    """
    Transfer schema information from cold storage to red hot memory for fast semantic search.
    Creates embeddings for each column and stores them in FAISS index with metadata.
    
    Args:
        memory_manager: Initialized MemoryManager instance with both cold and red hot enabled
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
        if not memory_manager.red_hot:
            raise ValueError("Red hot storage not initialized in memory manager")
            
        results = {
            "processed_tables": 0,
            "processed_columns": 0,
            "errors": []
        }
        
        # Get schema information from cold storage
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
        
        logger.info(f"Transferred {results['processed_columns']} columns from {results['processed_tables']} tables to red hot memory")
        return results
        
    except Exception as e:
        logger.error(f"Error transferring to red hot memory: {e}")
        raise

def search_redhot_schema(
    memory_manager: MemoryManager,
    query: str,
    embedding_model: str = "all-MiniLM-L6-v2",
    k: int = 5,
    threshold: float = 0.5,
    type_filter: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Search for similar columns in red hot memory using semantic similarity.
    
    Args:
        memory_manager: Initialized MemoryManager instance with red hot enabled
        query: Search query (column name or description)
        embedding_model: Name of the sentence transformer model to use
        k: Number of results to return
        threshold: Similarity threshold (0-1)
        type_filter: Optional filter for column type
        
    Returns:
        List of similar columns with their metadata and similarity scores
    """
    try:
        if not memory_manager.red_hot:
            raise ValueError("Red hot storage not initialized in memory manager")
            
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
        logger.error(f"Error searching red hot schema: {e}")
        raise

def main():
    """Main function to run cold to red hot transfer operations."""
    parser = argparse.ArgumentParser(description='Transfer schema from cold storage to red hot memory')
    parser.add_argument('--storage-path', type=str, default='data',
                      help='Base storage path for memory tiers (default: data)')
    parser.add_argument('--embedding-model', type=str, default='all-MiniLM-L6-v2',
                      help='Name of the sentence transformer model to use')
    parser.add_argument('--batch-size', type=int, default=32,
                      help='Batch size for processing embeddings')
    parser.add_argument('--force-cpu', action='store_true',
                      help='Force CPU usage for FAISS')
    parser.add_argument('--search', type=str,
                      help='Search query to find similar columns after transfer')
    parser.add_argument('--type-filter', type=str,
                      help='Filter search results by column type')
    parser.add_argument('--threshold', type=float, default=0.5,
                      help='Similarity threshold for search results (0-1)')
    parser.add_argument('--max-results', type=int, default=5,
                      help='Maximum number of search results to return')
    parser.add_argument('--temp-dir', type=str,
                      help='Custom temporary directory path (optional)')
    
    args = parser.parse_args()
    
    try:
        # Use custom temp directory if provided
        if args.temp_dir:
            temp_dir = Path(args.temp_dir)
            temp_dir.mkdir(exist_ok=True)
            os.environ['TMPDIR'] = str(temp_dir)
            os.environ['TEMP'] = str(temp_dir)
            os.environ['TMP'] = str(temp_dir)
            tempfile.tempdir = str(temp_dir)
            
        # Initialize memory manager with both cold and red hot storage
        storage_path = Path(args.storage_path)
        
        logger.info(f"Initializing MemoryManager with storage path: {storage_path}")
        memory_manager = MemoryManager(
            storage_path=storage_path,
            vector_encoder=None,  # Not needed for schema transfer
            enable_red_hot=True,
            enable_hot=False,
            enable_cold=True,
            enable_warm=False,
            enable_glacier=False
        )
        
        # Transfer schema to red hot memory
        logger.info("Starting schema transfer to red hot memory...")
        results = transfer_to_redhot(
            memory_manager=memory_manager,
            embedding_model=args.embedding_model,
            batch_size=args.batch_size,
            force_cpu=args.force_cpu
        )
        
        # Print transfer results
        logger.info("Transfer Results:")
        logger.info(f"- Processed tables: {results['processed_tables']}")
        logger.info(f"- Processed columns: {results['processed_columns']}")
        if results['errors']:
            logger.warning("Errors encountered:")
            for error in results['errors']:
                logger.warning(f"- {error}")
                
        # Perform search if requested
        if args.search:
            logger.info(f"\nSearching for columns similar to: {args.search}")
            search_results = search_redhot_schema(
                memory_manager=memory_manager,
                query=args.search,
                embedding_model=args.embedding_model,
                k=args.max_results,
                threshold=args.threshold,
                type_filter=args.type_filter
            )
            
            if search_results:
                logger.info("\nSearch Results:")
                for i, result in enumerate(search_results, 1):
                    logger.info(f"\n{i}. {result['table_name']}.{result['column_name']}")
                    logger.info(f"   Similarity: {result['similarity']:.3f}")
                    logger.info(f"   Type: {result['metadata']['column_type']}")
                    if result['metadata']['statistics']:
                        logger.info(f"   Distinct Values: {result['metadata']['statistics']['distinct_count']}")
            else:
                logger.info("No matching columns found")
                
    except Exception as e:
        logger.error(f"Error: {e}")
        raise
    finally:
        # Cleanup temporary directory
        try:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
        except Exception as e:
            logger.warning(f"Error cleaning up temporary directory: {e}")

if __name__ == "__main__":
    main() 