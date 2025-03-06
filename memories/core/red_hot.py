"""
Red hot memory implementation using FAISS.
"""

import logging
from typing import Dict, Any, Optional, List, Union, Tuple
import numpy as np
import faiss
import torch
from pathlib import Path
import json
from datetime import datetime
import os
import shutil
import duckdb
import pandas as pd
import yaml

logger = logging.getLogger(__name__)

class RedHotMemory:
    """Red hot memory layer using FAISS for ultra-fast vector similarity search."""
    
    def __init__(self, vector_dim: int = 384, max_size: int = 10000, gpu_id: int = 0, force_cpu: bool = True, index_type: str = 'L2'):
        """Initialize red-hot memory with FAISS index.
        
        Args:
            vector_dim: Dimension of vectors to store
            max_size: Maximum number of vectors to store
            gpu_id: GPU device ID to use (if available)
            force_cpu: Whether to force CPU usage even if GPU is available
            index_type: Type of FAISS index to use ('L2' or 'IP')
        """
        self.vector_dim = vector_dim
        self.max_size = max_size
        self.gpu_id = gpu_id
        self.force_cpu = force_cpu
        self.index_type = index_type
        self.metadata = {}
        self.using_gpu = False
        
        # Set up storage path
        project_root = Path(__file__).parent.parent.parent
        self.storage_path = os.path.join(project_root, "data", "red_hot")
        
        # Create storage directory if it doesn't exist
        if not os.path.exists(self.storage_path):
            os.makedirs(self.storage_path)
            
        logger.info(f"Initialized RedHotMemory with storage at: {self.storage_path}")
        
        # Initialize DuckDB connection for schema storage
        self.con = duckdb.connect(database=':memory:')
        self._initialize_schema_storage()
        
        # Try to load existing state, or initialize new if none exists
        self._load_state()

    def _initialize_schema_storage(self):
        """Initialize tables for storing schema information."""
        self.con.execute("""
            CREATE SEQUENCE IF NOT EXISTS file_id_seq;
            
            CREATE TABLE IF NOT EXISTS file_metadata (
                file_id INTEGER DEFAULT nextval('file_id_seq'),
                file_path VARCHAR UNIQUE,
                file_name VARCHAR,
                file_type VARCHAR,
                last_modified TIMESTAMP,
                size_bytes BIGINT,
                row_count BIGINT,
                source_type VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (file_id)
            )
        """)
        
        self.con.execute("""
            CREATE SEQUENCE IF NOT EXISTS column_id_seq;
            
            CREATE TABLE IF NOT EXISTS column_metadata (
                column_id INTEGER DEFAULT nextval('column_id_seq'),
                file_id INTEGER,
                column_name VARCHAR,
                data_type VARCHAR,
                is_nullable BOOLEAN,
                description TEXT,
                statistics JSON,
                PRIMARY KEY (column_id),
                FOREIGN KEY (file_id) REFERENCES file_metadata(file_id)
            )
        """)
        
        # Create indexes for faster querying
        self.con.execute("CREATE INDEX IF NOT EXISTS idx_file_path ON file_metadata(file_path)")
        self.con.execute("CREATE INDEX IF NOT EXISTS idx_column_name ON column_metadata(column_name)")

    def _init_index(self):
        """Initialize a new FAISS index."""
        if self.index_type == 'L2':
            self.index = faiss.IndexFlatL2(self.vector_dim)
        else:  # Inner Product
            self.index = faiss.IndexFlatIP(self.vector_dim)
            
        # Try to use GPU if available and not forced to CPU
        if not self.force_cpu:
            try:
                res = faiss.StandardGpuResources()
                self.index = faiss.index_cpu_to_gpu(res, self.gpu_id, self.index)
                self.using_gpu = True
                logger.info(f"Using GPU {self.gpu_id} for FAISS index")
            except Exception as e:
                logger.warning(f"Failed to use GPU, falling back to CPU: {e}")
                self.using_gpu = False
                
        self.metadata = {}
        logger.info(f"Initialized new FAISS index of type {self.index_type}")

    def _save_state(self):
        """Save FAISS index and metadata to disk."""
        try:
            # Convert to CPU index if using GPU
            if self.using_gpu:
                cpu_index = faiss.index_gpu_to_cpu(self.index)
            else:
                cpu_index = self.index
                
            # Save FAISS index
            index_path = os.path.join(self.storage_path, "index.faiss")
            faiss.write_index(cpu_index, index_path)
            
            # Save metadata
            metadata_path = os.path.join(self.storage_path, "metadata.json")
            with open(metadata_path, 'w') as f:
                json.dump(self.metadata, f)
                
            logger.debug(f"Saved state to {self.storage_path}")
            
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
            raise

    def _load_state(self):
        """Load FAISS index and metadata from disk."""
        index_path = os.path.join(self.storage_path, "index.faiss")
        metadata_path = os.path.join(self.storage_path, "metadata.json")
        
        if os.path.exists(index_path) and os.path.exists(metadata_path):
            try:
                # Load FAISS index
                self.index = faiss.read_index(index_path)
                
                # Move to GPU if needed
                if not self.force_cpu:
                    try:
                        res = faiss.StandardGpuResources()
                        self.index = faiss.index_cpu_to_gpu(res, self.gpu_id, self.index)
                        self.using_gpu = True
                    except Exception as e:
                        logger.warning(f"Failed to move index to GPU: {e}")
                        self.using_gpu = False
                
                # Load metadata
                with open(metadata_path, 'r') as f:
                    self.metadata = json.load(f)
                    
                logger.info(f"Loaded existing state from {self.storage_path}")
                
            except Exception as e:
                logger.error(f"Failed to load state: {e}")
                self._init_index()
        else:
            logger.info("No existing state found, initializing new index")
            self._init_index()

    def add_file_schema(self, file_path: str, schema: List[Tuple[str, Any]], additional_info: Dict = None):
        """Add file schema information to red-hot memory."""
        try:
            # Get file metadata
            file_info = {
                'file_path': file_path,
                'file_name': os.path.basename(file_path),
                'file_type': os.path.splitext(file_path)[1],
                'last_modified': pd.Timestamp.fromtimestamp(os.path.getmtime(file_path)),
                'size_bytes': os.path.getsize(file_path),
                'row_count': additional_info.get('row_count') if additional_info else None,
                'source_type': additional_info.get('source_type') if additional_info else 'unknown',
                'created_at': pd.Timestamp(additional_info.get('created_at')) if additional_info and additional_info.get('created_at') else None
            }
            
            # First try to get existing file_id
            existing = self.con.execute("""
                SELECT file_id FROM file_metadata 
                WHERE file_path = ?
            """, [file_path]).fetchone()

            if existing:
                # Update existing record
                self.con.execute("""
                    UPDATE file_metadata 
                    SET 
                        file_name = ?,
                        file_type = ?,
                        last_modified = ?,
                        size_bytes = ?,
                        row_count = ?,
                        source_type = ?,
                        created_at = ?
                    WHERE file_path = ?
                """, [
                    file_info['file_name'],
                    file_info['file_type'],
                    file_info['last_modified'],
                    file_info['size_bytes'],
                    file_info['row_count'],
                    file_info['source_type'],
                    file_info['created_at'],
                    file_path
                ])
                file_id = existing[0]
            else:
                # Insert new record
                self.con.execute("""
                    INSERT INTO file_metadata (
                        file_path, file_name, file_type, last_modified, 
                        size_bytes, row_count, source_type, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    file_info['file_path'],
                    file_info['file_name'],
                    file_info['file_type'],
                    file_info['last_modified'],
                    file_info['size_bytes'],
                    file_info['row_count'],
                    file_info['source_type'],
                    file_info['created_at']
                ])
                
                file_id = self.con.execute("""
                    SELECT file_id FROM file_metadata 
                    WHERE file_path = ?
                """, [file_path]).fetchone()[0]
            
            # Delete existing column metadata for this file
            self.con.execute("DELETE FROM column_metadata WHERE file_id = ?", [file_id])
            
            # Insert column metadata
            for col_name, col_type in schema:
                stats = {}
                if additional_info and 'column_stats' in additional_info:
                    stats = additional_info['column_stats'].get(str(col_name), {})
                
                self.con.execute("""
                    INSERT INTO column_metadata (
                        file_id, column_name, data_type, is_nullable, 
                        description, statistics
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                """, [
                    file_id,
                    str(col_name),
                    str(col_type),
                    True,  # is_nullable default
                    None,  # description default
                    json.dumps(stats)
                ])
                
            logger.info(f"Added schema information for {file_path}")
            
        except Exception as e:
            logger.error(f"Error adding schema information for {file_path}: {e}")

    def get_file_schema(self, file_path: str) -> pd.DataFrame:
        """Get schema information for a specific file."""
        return self.con.execute("""
            SELECT 
                cm.column_name,
                cm.data_type,
                cm.is_nullable,
                cm.description,
                cm.statistics
            FROM column_metadata cm
            JOIN file_metadata fm ON cm.file_id = fm.file_id
            WHERE fm.file_path = ?
            ORDER BY cm.column_id
        """, [file_path]).df()

    def search_columns(self, pattern: str) -> pd.DataFrame:
        """Search for columns matching a pattern across all files."""
        return self.con.execute("""
            SELECT 
                fm.file_path,
                fm.file_name,
                cm.column_name,
                cm.data_type,
                cm.description
            FROM column_metadata cm
            JOIN file_metadata fm ON cm.file_id = fm.file_id
            WHERE cm.column_name LIKE ?
            ORDER BY fm.file_path, cm.column_name
        """, [f"%{pattern}%"]).df()

    def get_file_metadata(self, pattern: str = None) -> pd.DataFrame:
        """Get metadata for all files or files matching a pattern."""
        query = """
            SELECT 
                file_path,
                file_name,
                file_type,
                last_modified,
                size_bytes,
                row_count,
                source_type,
                created_at
            FROM file_metadata
        """
        if pattern:
            query += " WHERE file_path LIKE ?"
            return self.con.execute(query, [f"%{pattern}%"]).df()
        return self.con.execute(query).df()

    def store(self, key: str, vector_data: Union[np.ndarray, torch.Tensor], metadata: Optional[Dict[str, Any]] = None) -> None:
        """Store vector data with metadata.
        
        Args:
            key: Unique identifier for the vector
            vector_data: Vector to store (numpy array or PyTorch tensor)
            metadata: Optional metadata to store with the vector
        """
        try:
            # Convert PyTorch tensor to numpy if needed
            if isinstance(vector_data, torch.Tensor):
                vector_data = vector_data.detach().cpu().numpy()
            
            # Ensure vector is 1D and correct dimension
            vector_data = vector_data.reshape(-1)
            if len(vector_data) != self.vector_dim:
                raise ValueError(f"Vector dimension mismatch. Expected {self.vector_dim}, got {len(vector_data)}")
            
            # Initialize index if not already done
            if not hasattr(self, 'index') or self.index is None:
                self._init_index()
            
            # Add vector to index
            self.index.add(vector_data.reshape(1, -1))
            
            # Store metadata with timestamp
            self.metadata[key] = {
                'metadata': metadata or {},
                'timestamp': datetime.now().isoformat(),
                'index': len(self.metadata)  # Store the index position
            }
            
            # Save state periodically (every 100 entries)
            if len(self.metadata) % 100 == 0:
                self._save_state()
                
        except Exception as e:
            logger.error(f"Failed to store vector: {e}")
            raise

    def search(self, query_vector: Union[np.ndarray, torch.Tensor], k: int = 5, metadata_filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search for similar vectors.
        
        Args:
            query_vector: Query vector
            k: Number of results to return
            metadata_filter: Optional filter for metadata
            
        Returns:
            List of dictionaries containing similar vectors and their metadata
        """
        try:
            # Convert PyTorch tensor to numpy if needed
            if isinstance(query_vector, torch.Tensor):
                query_vector = query_vector.detach().cpu().numpy()
            
            # Reshape query vector
            query_vector = query_vector.reshape(1, -1)
            
            if not hasattr(self, 'index') or self.index is None:
                logger.warning("No index available for search")
                return []
            
            # Perform search
            distances, indices = self.index.search(query_vector, k)
            
            # Format results
            results = []
            for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
                if idx != -1:  # Valid index
                    # Find metadata for this index
                    for key, meta in self.metadata.items():
                        if meta['index'] == idx:
                            result = {
                                'key': key,
                                'distance': float(dist),
                                'metadata': meta['metadata'],
                                'timestamp': meta['timestamp']
                            }
                            
                            # Apply metadata filter if provided
                            if metadata_filter:
                                if all(meta['metadata'].get(k) == v for k, v in metadata_filter.items()):
                                    results.append(result)
                            else:
                                results.append(result)
                            
                            break
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to search vectors: {e}")
            return []
    
    def _remove_oldest(self):
        """Remove oldest vectors when size limit is reached."""
        try:
            # Sort by timestamp
            sorted_items = sorted(
                self.metadata.items(),
                key=lambda x: x[1]["timestamp"]
            )
            
            # Remove oldest item
            oldest_key = sorted_items[0][0]
            oldest_idx = self.metadata[oldest_key]["index"]
            
            # Remove from metadata
            del self.metadata[oldest_key]
            
            # Update indices for remaining items
            for key, data in self.metadata.items():
                if data["index"] > oldest_idx:
                    data["index"] -= 1
            
            # Save state
            self._save_state()
            
            logger.info(f"Removed oldest vector with key: {oldest_key}")
            
        except Exception as e:
            logger.error(f"Failed to remove oldest vector: {e}")
            raise

    def __len__(self):
        """Return number of vectors in storage."""
        return self.index.ntotal if self.index is not None else 0

    def cleanup(self) -> None:
        """Clean up resources and close connections."""
        try:
            # Close DuckDB connection
            if hasattr(self, 'con') and self.con:
                self.con.close()
                self.con = None

            # Save state before cleanup
            self._save_state()

            # Delete FAISS index
            if hasattr(self, 'index'):
                del self.index

            # Clear metadata
            self.metadata = {}
            
            logger.info("Cleaned up red hot memory")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def reset(self) -> bool:
        """
        Reset the entire storage directory.
        WARNING: This will delete everything in the storage directory.
        """
        try:
            if os.path.exists(self.storage_path):
                shutil.rmtree(self.storage_path)
            os.makedirs(self.storage_path)
            
            # Reinitialize empty index
            self.index = faiss.IndexFlatL2(self.vector_dim)
            self.metadata = {}
            
            logger.info("Successfully reset red-hot memory storage")
            return True
            
        except Exception as e:
            logger.error(f"Error resetting red-hot memory: {e}")
            return False
    
    def __del__(self):
        """Destructor to ensure cleanup is performed."""
        self.cleanup() 