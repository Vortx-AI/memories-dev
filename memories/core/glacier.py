import duckdb
import geopandas as gpd
from pathlib import Path
import logging
from typing import Optional, List, Dict, Any
import pyarrow as pa
import pyarrow.parquet as pq
from shapely.geometry import shape
import json
import uuid
import zlib
from datetime import datetime

class GlacierMemory:
    def __init__(self, db_path: str = "glacier.duckdb", compression_level: int = 9):
        """
        Initialize Glacier Memory with DuckDB and GeoParquet support.
        
        Args:
            db_path (str): Path to DuckDB database file
            compression_level (int): Compression level (1-9, default 9 for maximum)
        """
        self.db_path = db_path
        self.compression_level = compression_level
        self.logger = logging.getLogger(__name__)
        self.conn = self._initialize_db()

    def _initialize_db(self) -> duckdb.DuckDBPyConnection:
        """Initialize DuckDB connection and required extensions."""
        conn = duckdb.connect(self.db_path)
        conn.install_extension("spatial")
        conn.load_extension("spatial")
        
        # Create tables if they don't exist
        conn.execute("""
            CREATE TABLE IF NOT EXISTS glacier_data (
                id VARCHAR PRIMARY KEY,
                data BLOB,
                metadata JSON,
                geometry JSON,
                created_at TIMESTAMP,
                archived_at TIMESTAMP,
                last_accessed TIMESTAMP,
                compression_level INTEGER,
                original_size BIGINT,
                compressed_size BIGINT,
                tags VARCHAR[],
                archive_status VARCHAR
            )
        """)
        return conn

    def archive(self, 
                gdf: gpd.GeoDataFrame, 
                metadata: Dict[str, Any] = None, 
                tags: List[str] = None) -> str:
        """
        Archive new entry in glacier storage with compression.
        
        Args:
            gdf (GeoDataFrame): GeoDataFrame to store
            metadata (dict): Additional metadata
            tags (list): List of tags for searching
        
        Returns:
            str: ID of archived entry
        """
        try:
            # Convert GeoDataFrame to Parquet bytes
            parquet_bytes = self._gdf_to_parquet_bytes(gdf)
            original_size = len(parquet_bytes)
            
            # Compress the data
            compressed_data = zlib.compress(parquet_bytes, level=self.compression_level)
            compressed_size = len(compressed_data)
            
            # Convert geometry to GeoJSON
            geometry_json = json.dumps(gdf.geometry.iloc[0].__geo_interface__)
            
            # Generate ID
            entry_id = str(uuid.uuid4())
            
            # Insert data
            self.conn.execute("""
                INSERT INTO glacier_data (
                    id, data, metadata, geometry, created_at, archived_at,
                    last_accessed, compression_level, original_size,
                    compressed_size, tags, archive_status
                )
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
                        CURRENT_TIMESTAMP, ?, ?, ?, ?, 'ARCHIVED')
            """, (
                entry_id,
                compressed_data,
                json.dumps(metadata or {}),
                geometry_json,
                self.compression_level,
                original_size,
                compressed_size,
                tags or []
            ))
            
            return entry_id
            
        except Exception as e:
            self.logger.error(f"Error archiving entry: {str(e)}")
            raise

    def retrieve(self, id: str) -> Optional[gpd.GeoDataFrame]:
        """
        Retrieve entry from glacier storage.
        
        Args:
            id (str): Entry ID
            
        Returns:
            GeoDataFrame or None
        """
        try:
            result = self.conn.execute("""
                SELECT data
                FROM glacier_data
                WHERE id = ?
            """, [id]).fetchone()
            
            if result is None:
                return None
            
            # Update last accessed timestamp
            self.conn.execute("""
                UPDATE glacier_data
                SET last_accessed = CURRENT_TIMESTAMP
                WHERE id = ?
            """, [id])
            
            # Decompress and convert data
            compressed_data = result[0]
            parquet_bytes = zlib.decompress(compressed_data)
            gdf = self._parquet_bytes_to_gdf(parquet_bytes)
            
            return gdf
            
        except Exception as e:
            self.logger.error(f"Error retrieving entry {id}: {str(e)}")
            return None

    def update_metadata(self, 
                       id: str,
                       metadata: Optional[Dict[str, Any]] = None,
                       tags: Optional[List[str]] = None) -> bool:
        """
        Update metadata of archived entry.
        
        Args:
            id (str): Entry ID
            metadata (dict, optional): New metadata
            tags (list, optional): New tags
            
        Returns:
            bool: Success status
        """
        try:
            updates = []
            params = []
            
            if metadata is not None:
                updates.append("metadata = ?")
                params.append(json.dumps(metadata))
                
            if tags is not None:
                updates.append("tags = ?")
                params.append(tags)
                
            if not updates:
                return True
                
            params.append(id)
            
            self.conn.execute(f"""
                UPDATE glacier_data
                SET {', '.join(updates)}
                WHERE id = ?
            """, params)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating metadata for entry {id}: {str(e)}")
            return False

    def delete(self, id: str) -> bool:
        """
        Delete entry from glacier storage.
        
        Args:
            id (str): Entry ID
            
        Returns:
            bool: Success status
        """
        try:
            self.conn.execute("DELETE FROM glacier_data WHERE id = ?", [id])
            return True
        except Exception as e:
            self.logger.error(f"Error deleting entry {id}: {str(e)}")
            return False

    def search(self, 
               tags: Optional[List[str]] = None,
               bbox: Optional[List[float]] = None,
               archived_before: Optional[datetime] = None,
               accessed_before: Optional[datetime] = None,
               limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search archived entries by various criteria.
        
        Args:
            tags (list, optional): Tags to search for
            bbox (list, optional): Bounding box [minx, miny, maxx, maxy]
            archived_before (datetime, optional): Filter by archive date
            accessed_before (datetime, optional): Filter by last access date
            limit (int): Maximum number of results
            
        Returns:
            list: List of matching entry metadata
        """
        try:
            query = """
                SELECT id, metadata, geometry, archived_at, last_accessed,
                       original_size, compressed_size, tags
                FROM glacier_data 
                WHERE 1=1
            """
            params = []
            
            if tags:
                query += " AND tags && ?"
                params.append(tags)
                
            if bbox:
                query += """ 
                    AND ST_Intersects(
                        ST_GeomFromGeoJSON(geometry),
                        ST_MakeEnvelope(?, ?, ?, ?)
                    )
                """
                params.extend(bbox)
                
            if archived_before:
                query += " AND archived_at < ?"
                params.append(archived_before)
                
            if accessed_before:
                query += " AND last_accessed < ?"
                params.append(accessed_before)
                
            query += f" LIMIT {limit}"
            
            results = self.conn.execute(query, params).fetchall()
            
            return [
                {
                    'id': r[0],
                    'metadata': json.loads(r[1]),
                    'geometry': json.loads(r[2]),
                    'archived_at': r[3],
                    'last_accessed': r[4],
                    'original_size': r[5],
                    'compressed_size': r[6],
                    'tags': r[7]
                }
                for r in results
            ]
            
        except Exception as e:
            self.logger.error(f"Error searching entries: {str(e)}")
            return []

    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        try:
            stats = self.conn.execute("""
                SELECT 
                    COUNT(*) as total_entries,
                    SUM(original_size) as total_original_size,
                    SUM(compressed_size) as total_compressed_size,
                    AVG(CAST(compressed_size AS FLOAT) / NULLIF(original_size, 0)) as avg_compression_ratio
                FROM glacier_data
            """).fetchone()
            
            return {
                'total_entries': stats[0],
                'total_original_size': stats[1],
                'total_compressed_size': stats[2],
                'avg_compression_ratio': stats[3]
            }
        except Exception as e:
            self.logger.error(f"Error getting storage stats: {str(e)}")
            return {}

    def _gdf_to_parquet_bytes(self, gdf: gpd.GeoDataFrame) -> bytes:
        """Convert GeoDataFrame to Parquet bytes."""
        buffer = pa.BufferOutputStream()
        gdf.to_parquet(buffer)
        return buffer.getvalue().to_pybytes()

    def _parquet_bytes_to_gdf(self, parquet_bytes: bytes) -> gpd.GeoDataFrame:
        """Convert Parquet bytes back to GeoDataFrame."""
        table = pq.read_table(pa.BufferReader(parquet_bytes))
        return gpd.GeoDataFrame.from_arrow(table)

    def close(self):
        """Close database connection."""
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
