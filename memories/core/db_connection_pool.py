"""
DuckDB connection pool manager to prevent memory leaks and improve performance.
"""

import duckdb
import threading
import weakref
from typing import Dict, Optional, Any
from contextlib import contextmanager
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class DuckDBConnectionPool:
    """Thread-safe connection pool for DuckDB connections."""
    
    _instance = None
    _lock = threading.Lock()
    _connections: Dict[str, duckdb.DuckDBPyConnection] = {}
    _connection_refs: Dict[str, weakref.ref] = {}
    
    def __new__(cls):
        """Singleton pattern to ensure only one pool instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DuckDBConnectionPool, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the connection pool."""
        if self._initialized:
            return
            
        self._connections = {}
        self._connection_refs = {}
        self._lock = threading.Lock()
        self._initialized = True
        logger.info("Initialized DuckDB connection pool")
    
    @contextmanager
    def get_connection(self, 
                       db_name: str = ":memory:",
                       config: Optional[Dict[str, Any]] = None) -> duckdb.DuckDBPyConnection:
        """Get a connection from the pool with automatic cleanup.
        
        Args:
            db_name: Database name or path (':memory:' for in-memory)
            config: Optional DuckDB configuration parameters
            
        Yields:
            DuckDB connection
        """
        conn = None
        try:
            conn = self._get_or_create_connection(db_name, config)
            yield conn
        except Exception as e:
            logger.error(f"Error using DuckDB connection: {e}")
            # Mark connection as dirty for recreation on next use
            with self._lock:
                if db_name in self._connections:
                    try:
                        self._connections[db_name].close()
                    except Exception:
                        pass
                    del self._connections[db_name]
                    if db_name in self._connection_refs:
                        del self._connection_refs[db_name]
            raise
        finally:
            # Don't close the connection - keep it in the pool
            pass
    
    def _get_or_create_connection(self,
                                 db_name: str,
                                 config: Optional[Dict[str, Any]] = None) -> duckdb.DuckDBPyConnection:
        """Get existing connection or create new one.
        
        Args:
            db_name: Database name or path
            config: Optional DuckDB configuration
            
        Returns:
            DuckDB connection
        """
        with self._lock:
            # Clean up dead connections
            self._cleanup_dead_connections()
            
            # Check if connection exists and is valid
            if db_name in self._connections:
                conn = self._connections[db_name]
                try:
                    # Test if connection is still valid
                    conn.execute("SELECT 1").fetchone()
                    return conn
                except Exception:
                    # Connection is dead, remove it
                    logger.debug(f"Removing dead connection for {db_name}")
                    del self._connections[db_name]
                    if db_name in self._connection_refs:
                        del self._connection_refs[db_name]
            
            # Create new connection
            logger.debug(f"Creating new DuckDB connection for {db_name}")
            
            if db_name == ":memory:":
                conn = duckdb.connect(database=":memory:", read_only=False)
            else:
                # Ensure directory exists for file-based databases
                db_path = Path(db_name)
                if not db_path.parent.exists():
                    db_path.parent.mkdir(parents=True, exist_ok=True)
                conn = duckdb.connect(database=str(db_path), read_only=False)
            
            # Apply configuration
            if config:
                for key, value in config.items():
                    if key == "memory_limit":
                        conn.execute(f"SET memory_limit='{value}'")
                    elif key == "threads":
                        conn.execute(f"SET threads={value}")
                    elif key == "enable_progress_bar":
                        conn.execute(f"SET enable_progress_bar={value}")
                    elif key == "enable_object_cache":
                        conn.execute(f"SET enable_object_cache={value}")
            
            # Store connection and weak reference
            self._connections[db_name] = conn
            self._connection_refs[db_name] = weakref.ref(conn, 
                lambda ref, name=db_name: self._connection_died(name))
            
            return conn
    
    def _connection_died(self, db_name: str):
        """Callback when a connection is garbage collected."""
        logger.debug(f"Connection {db_name} was garbage collected")
        with self._lock:
            if db_name in self._connections:
                del self._connections[db_name]
            if db_name in self._connection_refs:
                del self._connection_refs[db_name]
    
    def _cleanup_dead_connections(self):
        """Remove dead connections from the pool."""
        dead_connections = []
        for db_name, ref in self._connection_refs.items():
            if ref() is None:
                dead_connections.append(db_name)
        
        for db_name in dead_connections:
            logger.debug(f"Cleaning up dead connection: {db_name}")
            if db_name in self._connections:
                del self._connections[db_name]
            del self._connection_refs[db_name]
    
    def close_connection(self, db_name: str):
        """Explicitly close and remove a connection from the pool.
        
        Args:
            db_name: Database name to close
        """
        with self._lock:
            if db_name in self._connections:
                try:
                    self._connections[db_name].close()
                    logger.debug(f"Closed connection: {db_name}")
                except Exception as e:
                    logger.error(f"Error closing connection {db_name}: {e}")
                finally:
                    del self._connections[db_name]
                    if db_name in self._connection_refs:
                        del self._connection_refs[db_name]
    
    def close_all(self):
        """Close all connections in the pool."""
        with self._lock:
            for db_name, conn in list(self._connections.items()):
                try:
                    conn.close()
                    logger.debug(f"Closed connection: {db_name}")
                except Exception as e:
                    logger.error(f"Error closing connection {db_name}: {e}")
            
            self._connections.clear()
            self._connection_refs.clear()
            logger.info("Closed all DuckDB connections")
    
    def get_pool_size(self) -> int:
        """Get the current number of connections in the pool.
        
        Returns:
            Number of active connections
        """
        with self._lock:
            return len(self._connections)
    
    def __del__(self):
        """Cleanup when pool is destroyed."""
        try:
            self.close_all()
        except Exception:
            pass

# Global connection pool instance
_connection_pool = None

def get_connection_pool() -> DuckDBConnectionPool:
    """Get the global connection pool instance.
    
    Returns:
        DuckDBConnectionPool instance
    """
    global _connection_pool
    if _connection_pool is None:
        _connection_pool = DuckDBConnectionPool()
    return _connection_pool