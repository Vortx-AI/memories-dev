import faiss
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
import time
import yaml
import os
from pathlib import Path
import logging
import duckdb
import json
import pandas as pd

logger = logging.getLogger(__name__)

class RedHotMemory:
    def __init__(self, config_path: str = None):
        """Initialize FAISS-based red-hot memory.
        
        Args:
            config_path: Path to db_config.yml
        """
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Initialize FAISS parameters from config
        self.vector_dim = self.config.get('red_hot', {}).get('vector_dim', 128)
        self.max_size = self.config.get('red_hot', {}).get('max_size', 10000)
        self.index_type = self.config.get('red_hot', {}).get('index_type', 'L2')
        
        # Initialize FAISS index based on config
        self.index = self._create_index()
        
        # Storage for metadata and vectors
        self.metadata: Dict[int, Dict] = {}
        self.vectors: Dict[int, np.ndarray] = {}
        self.last_access: Dict[int, float] = {}
        self.current_id = 0
        
        # Initialize DuckDB connection for schema storage
        self.con = duckdb.connect(database=':memory:')
        self._initialize_schema_storage()
        
        logger.info(f"Initialized RedHotMemory with dim={self.vector_dim}, max_size={self.max_size}")

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

    def _load_config(self, config_path: Optional[str] = None) -> dict:
        """Load configuration from db_config.yml."""
        if not config_path:
            config_path = os.path.join(
                Path(__file__).parent.parent.parent,
                'config',
                'db_config.yml'
            )
        
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            logger.error(f"Error loading config from {config_path}: {e}")
            return {}

    def _create_index(self) -> faiss.Index:
        """Create FAISS index based on configuration."""
        if self.index_type == 'L2':
            return faiss.IndexFlatL2(self.vector_dim)
        elif self.index_type == 'IVF':
            # IVF index for faster search with approximate results
            quantizer = faiss.IndexFlatL2(self.vector_dim)
            nlist = self.config.get('red_hot', {}).get('nlist', 100)
            return faiss.IndexIVFFlat(quantizer, self.vector_dim, nlist)
        else:
            logger.warning(f"Unknown index type {self.index_type}, falling back to L2")
            return faiss.IndexFlatL2(self.vector_dim)

    def add_item(self, vector: np.ndarray, metadata: Dict[str, Any] = None):
        """Add an item to red-hot memory.
        
        Args:
            vector: Feature vector
            metadata: Associated metadata (e.g., geometry, properties)
        """
        try:
            if len(self.metadata) >= self.max_size:
                self._evict()
                
            # Ensure vector is the right shape and type
            vector = np.asarray(vector, dtype=np.float32).reshape(1, self.vector_dim)
            
            # Add to FAISS index
            self.index.add(vector)
            
            # Store metadata and vector
            self.metadata[self.current_id] = metadata or {}
            self.vectors[self.current_id] = vector
            self.last_access[self.current_id] = time.time()
            
            self.current_id += 1
            
        except Exception as e:
            logger.error(f"Error adding item to red-hot memory: {e}")

    def search_knn(self, query_vector: np.ndarray, k: int = 5) -> List[Dict]:
        """Search for k nearest neighbors.
        
        Args:
            query_vector: Query vector
            k: Number of nearest neighbors to return
            
        Returns:
            List of metadata for nearest neighbors
        """
        try:
            # Ensure query vector is the right shape
            query_vector = np.asarray(query_vector, dtype=np.float32).reshape(1, self.vector_dim)
            
            # Search FAISS index
            distances, indices = self.index.search(query_vector, k)
            
            # Update access times and prepare results
            results = []
            for idx in indices[0]:  # indices is a 2D array
                if idx != -1 and idx in self.metadata:
                    self.last_access[idx] = time.time()
                    results.append({
                        'metadata': self.metadata[idx],
                        'distance': float(distances[0][list(indices[0]).index(idx)])
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching red-hot memory: {e}")
            return []

    def _evict(self):
        """Evict least recently used items when memory is full."""
        if not self.metadata:
            return
            
        # Find oldest accessed item
        oldest_id = min(self.last_access.items(), key=lambda x: x[1])[0]
        
        # Remove from all storage
        del self.metadata[oldest_id]
        del self.vectors[oldest_id]
        del self.last_access[oldest_id]
        
        # Rebuild FAISS index (since FAISS doesn't support removal)
        self.index = self._create_index()
        vectors = np.vstack([v for v in self.vectors.values()])
        if len(vectors) > 0:
            self.index.add(vectors)

    def clear(self):
        """Clear all data from red-hot memory."""
        self.metadata.clear()
        self.vectors.clear()
        self.last_access.clear()
        self.index = self._create_index()
        self.current_id = 0

    def get_storage_stats(self) -> dict:
        """Get statistics about the data stored in red-hot memory."""
        try:
            file_count = self.con.execute("""
                SELECT COUNT(*) FROM file_metadata
            """).fetchone()[0]
            
            column_count = self.con.execute("""
                SELECT COUNT(*) FROM column_metadata
            """).fetchone()[0]
            
            source_type_stats = self.con.execute("""
                SELECT 
                    source_type,
                    COUNT(*) as file_count,
                    SUM(row_count) as total_rows,
                    SUM(size_bytes) as total_size
                FROM file_metadata
                GROUP BY source_type
            """).df()
            
            return {
                'total_files': file_count,
                'total_columns': column_count,
                'source_type_stats': source_type_stats.to_dict('records')
            }
            
        except Exception as e:
            logger.error(f"Error getting storage stats: {e}")
            return {} 