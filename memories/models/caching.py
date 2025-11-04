"""Caching mechanisms for model responses."""

import hashlib
import json
import logging
import pickle
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional, Union
import sqlite3
from collections import OrderedDict

logger = logging.getLogger(__name__)


class CacheEntry:
    """Represents a single cache entry."""

    def __init__(self, key: str, value: Any, metadata: Dict[str, Any]):
        """Initialize cache entry.

        Args:
            key: Cache key
            value: Cached value
            metadata: Entry metadata
        """
        self.key = key
        self.value = value
        self.metadata = metadata
        self.created_at = datetime.now()
        self.last_accessed = datetime.now()
        self.access_count = 0

    def update_access(self):
        """Update access statistics."""
        self.last_accessed = datetime.now()
        self.access_count += 1

    def is_expired(self, ttl: int) -> bool:
        """Check if entry is expired.

        Args:
            ttl: Time to live in seconds

        Returns:
            True if expired, False otherwise
        """
        age = (datetime.now() - self.created_at).total_seconds()
        return age > ttl

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "key": self.key,
            "value": self.value,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "access_count": self.access_count
        }


class InMemoryCache:
    """In-memory LRU cache for model responses."""

    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        """Initialize in-memory cache.

        Args:
            max_size: Maximum number of entries
            ttl: Time to live in seconds (default: 1 hour)
        """
        self.max_size = max_size
        self.ttl = ttl
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.hits = 0
        self.misses = 0

    def _generate_key(self, prompt: str, **kwargs) -> str:
        """Generate cache key from prompt and parameters.

        Args:
            prompt: Input prompt
            **kwargs: Additional parameters

        Returns:
            Cache key
        """
        # Create a deterministic key
        key_data = {
            "prompt": prompt,
            "params": {k: v for k, v in sorted(kwargs.items())}
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()

    def get(self, prompt: str, **kwargs) -> Optional[Any]:
        """Get cached response.

        Args:
            prompt: Input prompt
            **kwargs: Additional parameters

        Returns:
            Cached value or None if not found
        """
        key = self._generate_key(prompt, **kwargs)

        if key in self.cache:
            entry = self.cache[key]

            # Check if expired
            if entry.is_expired(self.ttl):
                self.cache.pop(key)
                self.misses += 1
                return None

            # Update access stats
            entry.update_access()

            # Move to end (most recently used)
            self.cache.move_to_end(key)

            self.hits += 1
            logger.debug(f"Cache hit for key: {key[:8]}...")
            return entry.value

        self.misses += 1
        logger.debug(f"Cache miss for key: {key[:8]}...")
        return None

    def set(self, prompt: str, value: Any, metadata: Optional[Dict[str, Any]] = None, **kwargs):
        """Set cached response.

        Args:
            prompt: Input prompt
            value: Response value to cache
            metadata: Optional metadata
            **kwargs: Additional parameters
        """
        key = self._generate_key(prompt, **kwargs)

        # Remove oldest entry if at capacity
        if len(self.cache) >= self.max_size and key not in self.cache:
            oldest_key = next(iter(self.cache))
            self.cache.pop(oldest_key)
            logger.debug(f"Evicted oldest entry: {oldest_key[:8]}...")

        # Create and store entry
        entry = CacheEntry(key, value, metadata or {})
        self.cache[key] = entry

        logger.debug(f"Cached response for key: {key[:8]}...")

    def clear(self):
        """Clear all cache entries."""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
        logger.info("Cache cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dict with cache statistics
        """
        total_requests = self.hits + self.misses
        hit_rate = self.hits / total_requests if total_requests > 0 else 0

        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate,
            "ttl": self.ttl
        }


class DiskCache:
    """Persistent disk-based cache using SQLite."""

    def __init__(self, cache_dir: str = "./cache", ttl: int = 86400):
        """Initialize disk cache.

        Args:
            cache_dir: Directory for cache storage
            ttl: Time to live in seconds (default: 24 hours)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = ttl
        self.db_path = self.cache_dir / "cache.db"
        self.hits = 0
        self.misses = 0

        # Initialize database
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                value BLOB,
                metadata TEXT,
                created_at TEXT,
                last_accessed TEXT,
                access_count INTEGER
            )
        """)

        conn.commit()
        conn.close()

    def _generate_key(self, prompt: str, **kwargs) -> str:
        """Generate cache key from prompt and parameters.

        Args:
            prompt: Input prompt
            **kwargs: Additional parameters

        Returns:
            Cache key
        """
        key_data = {
            "prompt": prompt,
            "params": {k: v for k, v in sorted(kwargs.items())}
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()

    def get(self, prompt: str, **kwargs) -> Optional[Any]:
        """Get cached response.

        Args:
            prompt: Input prompt
            **kwargs: Additional parameters

        Returns:
            Cached value or None if not found
        """
        key = self._generate_key(prompt, **kwargs)

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute(
            "SELECT value, created_at, access_count FROM cache WHERE key = ?",
            (key,)
        )
        row = cursor.fetchone()

        if row:
            value_blob, created_at_str, access_count = row
            created_at = datetime.fromisoformat(created_at_str)

            # Check if expired
            age = (datetime.now() - created_at).total_seconds()
            if age > self.ttl:
                cursor.execute("DELETE FROM cache WHERE key = ?", (key,))
                conn.commit()
                conn.close()
                self.misses += 1
                return None

            # Update access stats
            cursor.execute(
                """UPDATE cache
                   SET last_accessed = ?, access_count = ?
                   WHERE key = ?""",
                (datetime.now().isoformat(), access_count + 1, key)
            )
            conn.commit()
            conn.close()

            # Deserialize value
            value = pickle.loads(value_blob)
            self.hits += 1
            logger.debug(f"Disk cache hit for key: {key[:8]}...")
            return value

        conn.close()
        self.misses += 1
        logger.debug(f"Disk cache miss for key: {key[:8]}...")
        return None

    def set(self, prompt: str, value: Any, metadata: Optional[Dict[str, Any]] = None, **kwargs):
        """Set cached response.

        Args:
            prompt: Input prompt
            value: Response value to cache
            metadata: Optional metadata
            **kwargs: Additional parameters
        """
        key = self._generate_key(prompt, **kwargs)

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # Serialize value
        value_blob = pickle.dumps(value)
        metadata_json = json.dumps(metadata or {})
        now = datetime.now().isoformat()

        cursor.execute(
            """INSERT OR REPLACE INTO cache
               (key, value, metadata, created_at, last_accessed, access_count)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (key, value_blob, metadata_json, now, now, 0)
        )

        conn.commit()
        conn.close()

        logger.debug(f"Cached response to disk for key: {key[:8]}...")

    def clear(self):
        """Clear all cache entries."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cache")
        conn.commit()
        conn.close()

        self.hits = 0
        self.misses = 0
        logger.info("Disk cache cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dict with cache statistics
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM cache")
        size = cursor.fetchone()[0]

        cursor.execute("SELECT SUM(access_count) FROM cache")
        total_accesses = cursor.fetchone()[0] or 0

        conn.close()

        total_requests = self.hits + self.misses
        hit_rate = self.hits / total_requests if total_requests > 0 else 0

        return {
            "size": size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate,
            "total_accesses": total_accesses,
            "ttl": self.ttl
        }


class TieredCache:
    """Two-level cache with memory and disk tiers."""

    def __init__(
        self,
        memory_size: int = 1000,
        memory_ttl: int = 3600,
        disk_cache_dir: str = "./cache",
        disk_ttl: int = 86400
    ):
        """Initialize tiered cache.

        Args:
            memory_size: Max entries in memory cache
            memory_ttl: Memory cache TTL in seconds
            disk_cache_dir: Directory for disk cache
            disk_ttl: Disk cache TTL in seconds
        """
        self.memory_cache = InMemoryCache(max_size=memory_size, ttl=memory_ttl)
        self.disk_cache = DiskCache(cache_dir=disk_cache_dir, ttl=disk_ttl)

    def get(self, prompt: str, **kwargs) -> Optional[Any]:
        """Get cached response from memory or disk.

        Args:
            prompt: Input prompt
            **kwargs: Additional parameters

        Returns:
            Cached value or None if not found
        """
        # Try memory cache first
        value = self.memory_cache.get(prompt, **kwargs)
        if value is not None:
            return value

        # Try disk cache
        value = self.disk_cache.get(prompt, **kwargs)
        if value is not None:
            # Promote to memory cache
            self.memory_cache.set(prompt, value, **kwargs)
            return value

        return None

    def set(self, prompt: str, value: Any, metadata: Optional[Dict[str, Any]] = None, **kwargs):
        """Set cached response in both tiers.

        Args:
            prompt: Input prompt
            value: Response value to cache
            metadata: Optional metadata
            **kwargs: Additional parameters
        """
        self.memory_cache.set(prompt, value, metadata, **kwargs)
        self.disk_cache.set(prompt, value, metadata, **kwargs)

    def clear(self):
        """Clear both cache tiers."""
        self.memory_cache.clear()
        self.disk_cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get combined cache statistics.

        Returns:
            Dict with cache statistics
        """
        return {
            "memory": self.memory_cache.get_stats(),
            "disk": self.disk_cache.get_stats()
        }
