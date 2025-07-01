"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich
  Project : basefunctions
  Copyright (c) by neuraldevelopment
  All rights reserved.
  Description:
  Unified caching framework with multiple backend support
 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import time
import threading
import fnmatch
import hashlib
import os
import pickle
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable, Tuple, Union
from datetime import datetime, timedelta
import basefunctions

# -------------------------------------------------------------
# DEFINITIONS REGISTRY
# -------------------------------------------------------------

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------
DEFAULT_TTL = 3600  # 1 hour
CACHE_TABLE_NAME = "bf_cache_entries"

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# LOGGING INITIALIZE
# -------------------------------------------------------------
# Enable logging for this module
basefunctions.setup_logger(__name__)

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


class CacheError(Exception):
    """Base exception for cache operations."""

    pass


class CacheBackendError(CacheError):
    """Raised when cache backend operation fails."""

    pass


class CacheEntry:
    """Cache entry with TTL support."""

    __slots__ = ("value", "expires_at", "created_at", "access_count")

    def __init__(self, value: Any, ttl: int):
        self.value = value
        self.created_at = time.time()
        self.expires_at = self.created_at + ttl if ttl > 0 else None
        self.access_count = 0

    def is_expired(self) -> bool:
        """Check if entry has expired."""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at

    def access(self) -> Any:
        """Access entry value and increment counter."""
        self.access_count += 1
        return self.value

    def remaining_ttl(self) -> Optional[int]:
        """Get remaining TTL in seconds."""
        if self.expires_at is None:
            return None
        remaining = self.expires_at - time.time()
        return max(0, int(remaining))


class CacheBackend(ABC):
    """Abstract base class for cache backends."""

    def __init__(self):
        self.stats = {"hits": 0, "misses": 0, "sets": 0, "deletes": 0, "clears": 0}
        self._lock = threading.RLock()

    @abstractmethod
    def _get_raw(self, key: str) -> Optional[CacheEntry]:
        """Get raw cache entry."""
        pass

    @abstractmethod
    def _set_raw(self, key: str, entry: CacheEntry) -> None:
        """Set raw cache entry."""
        pass

    @abstractmethod
    def _delete_raw(self, key: str) -> bool:
        """Delete raw cache entry."""
        pass

    @abstractmethod
    def _clear_raw(self) -> int:
        """Clear all entries."""
        pass

    @abstractmethod
    def _keys_raw(self) -> List[str]:
        """Get all keys."""
        pass

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self._lock:
            entry = self._get_raw(key)

            if entry is None:
                self.stats["misses"] += 1
                return None

            if entry.is_expired():
                self._delete_raw(key)
                self.stats["misses"] += 1
                return None

            self.stats["hits"] += 1
            return entry.access()

    def set(self, key: str, value: Any, ttl: int = DEFAULT_TTL) -> None:
        """Set value in cache."""
        with self._lock:
            entry = CacheEntry(value, ttl)
            self._set_raw(key, entry)
            self.stats["sets"] += 1

    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        with self._lock:
            success = self._delete_raw(key)
            if success:
                self.stats["deletes"] += 1
            return success

    def exists(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        return self.get(key) is not None

    def clear(self, pattern: str = "*") -> int:
        """Clear cache entries matching pattern."""
        with self._lock:
            if pattern == "*":
                count = self._clear_raw()
                self.stats["clears"] += 1
                return count

            # Pattern-based clearing
            keys_to_delete = []
            for key in self._keys_raw():
                if fnmatch.fnmatch(key, pattern):
                    keys_to_delete.append(key)

            for key in keys_to_delete:
                self._delete_raw(key)

            if keys_to_delete:
                self.stats["clears"] += 1

            return len(keys_to_delete)

    def keys(self, pattern: str = "*") -> List[str]:
        """Get all keys matching pattern."""
        with self._lock:
            all_keys = self._keys_raw()

            if pattern == "*":
                return all_keys

            return [key for key in all_keys if fnmatch.fnmatch(key, pattern)]

    def size(self) -> int:
        """Get number of cached entries."""
        with self._lock:
            return len(self._keys_raw())

    def expire(self, key: str, ttl: int) -> bool:
        """Set TTL for existing key."""
        with self._lock:
            entry = self._get_raw(key)
            if entry is None or entry.is_expired():
                return False

            # Create new entry with updated TTL
            new_entry = CacheEntry(entry.value, ttl)
            new_entry.created_at = entry.created_at
            new_entry.access_count = entry.access_count

            self._set_raw(key, new_entry)
            return True

    def ttl(self, key: str) -> Optional[int]:
        """Get remaining TTL for key."""
        with self._lock:
            entry = self._get_raw(key)
            if entry is None or entry.is_expired():
                return None
            return entry.remaining_ttl()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_requests = self.stats["hits"] + self.stats["misses"]
            hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0

            return {
                **self.stats,
                "total_requests": total_requests,
                "hit_rate_percent": round(hit_rate, 2),
                "size": self.size(),
            }


class MemoryBackend(CacheBackend):
    """In-memory cache backend."""

    def __init__(self, max_size: int = 1000):
        super().__init__()
        self.max_size = max_size
        self._cache: Dict[str, CacheEntry] = {}

    def _get_raw(self, key: str) -> Optional[CacheEntry]:
        return self._cache.get(key)

    def _set_raw(self, key: str, entry: CacheEntry) -> None:
        # Evict expired entries if at capacity
        if len(self._cache) >= self.max_size:
            self._evict_expired()

        # LRU eviction if still at capacity
        if len(self._cache) >= self.max_size:
            self._evict_lru()

        self._cache[key] = entry

    def _delete_raw(self, key: str) -> bool:
        return self._cache.pop(key, None) is not None

    def _clear_raw(self) -> int:
        count = len(self._cache)
        self._cache.clear()
        return count

    def _keys_raw(self) -> List[str]:
        return list(self._cache.keys())

    def _evict_expired(self) -> None:
        """Remove expired entries."""
        expired_keys = [key for key, entry in self._cache.items() if entry.is_expired()]
        for key in expired_keys:
            del self._cache[key]

    def _evict_lru(self) -> None:
        """Remove least recently used entry."""
        if not self._cache:
            return

        # Find entry with oldest access time
        lru_key = min(self._cache.keys(), key=lambda k: self._cache[k].created_at - self._cache[k].access_count)
        del self._cache[lru_key]


class DatabaseBackend(CacheBackend):
    """Database cache backend using basefunctions.Db."""

    def __init__(self, instance_name: str, database_name: str):
        super().__init__()
        self.instance_name = instance_name
        self.database_name = database_name
        self.db = basefunctions.Db(instance_name, database_name)
        self._ensure_table()

    def _ensure_table(self) -> None:
        """Create cache table if it doesn't exist."""
        try:
            if not self.db.check_if_table_exists(CACHE_TABLE_NAME):
                # Get database type for SQL adaptation
                connector = self.db.get_connector()
                db_type = getattr(connector, "db_type", "unknown")

                # Database-specific binary data type
                if db_type == "postgres":
                    blob_type = "BYTEA"
                    timestamp_default = "CURRENT_TIMESTAMP"
                elif db_type == "mysql":
                    blob_type = "LONGBLOB"
                    timestamp_default = "CURRENT_TIMESTAMP"
                else:  # SQLite and others
                    blob_type = "BLOB"
                    timestamp_default = "CURRENT_TIMESTAMP"

                create_sql = f"""
                CREATE TABLE {CACHE_TABLE_NAME} (
                    cache_key VARCHAR(255) PRIMARY KEY,
                    cache_value {blob_type},
                    expires_at TIMESTAMP NULL,
                    created_at TIMESTAMP DEFAULT {timestamp_default},
                    access_count INTEGER DEFAULT 0
                )
                """
                self.db.execute(create_sql)
        except Exception as e:
            raise CacheBackendError(f"Failed to create cache table: {str(e)}") from e

    def _get_raw(self, key: str) -> Optional[CacheEntry]:
        try:
            # Database-specific parameter syntax
            connector = self.db.get_connector()
            db_type = getattr(connector, "db_type", "unknown")

            placeholder = "%s" if db_type == "postgres" else "?"

            result = self.db.query_one(
                f"SELECT cache_value, expires_at, created_at, access_count FROM {CACHE_TABLE_NAME} WHERE cache_key = {placeholder}",
                (key,),
            )

            if result is None:
                return None

            # Deserialize value
            value = pickle.loads(result["cache_value"])

            # Create entry
            entry = CacheEntry(value, 0)  # TTL will be calculated from expires_at
            entry.created_at = result["created_at"].timestamp() if result["created_at"] else time.time()
            entry.access_count = result["access_count"] or 0

            if result["expires_at"]:
                entry.expires_at = result["expires_at"].timestamp()
            else:
                entry.expires_at = None

            return entry

        except Exception as e:
            raise CacheBackendError(f"Failed to get cache entry: {str(e)}") from e

    def _set_raw(self, key: str, entry: CacheEntry) -> None:
        try:
            # Serialize value
            cache_value = pickle.dumps(entry.value)

            # Convert timestamps
            expires_at = datetime.fromtimestamp(entry.expires_at) if entry.expires_at else None
            created_at = datetime.fromtimestamp(entry.created_at)

            # Database-specific upsert syntax
            connector = self.db.get_connector()
            db_type = getattr(connector, "db_type", "unknown")

            if db_type == "postgres":
                # PostgreSQL uses ON CONFLICT
                upsert_sql = f"""
                INSERT INTO {CACHE_TABLE_NAME} 
                (cache_key, cache_value, expires_at, created_at, access_count)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (cache_key) 
                DO UPDATE SET 
                    cache_value = EXCLUDED.cache_value,
                    expires_at = EXCLUDED.expires_at,
                    access_count = EXCLUDED.access_count
                """
                params = (key, cache_value, expires_at, created_at, entry.access_count)
            else:
                # SQLite and MySQL use INSERT OR REPLACE
                upsert_sql = f"""
                INSERT OR REPLACE INTO {CACHE_TABLE_NAME} 
                (cache_key, cache_value, expires_at, created_at, access_count)
                VALUES (?, ?, ?, ?, ?)
                """
                params = (key, cache_value, expires_at, created_at, entry.access_count)

            self.db.execute(upsert_sql, params)

        except Exception as e:
            raise CacheBackendError(f"Failed to set cache entry: {str(e)}") from e

    def _delete_raw(self, key: str) -> bool:
        try:
            # Database-specific parameter syntax
            connector = self.db.get_connector()
            db_type = getattr(connector, "db_type", "unknown")

            placeholder = "%s" if db_type == "postgres" else "?"

            self.db.execute(f"DELETE FROM {CACHE_TABLE_NAME} WHERE cache_key = {placeholder}", (key,))
            # Note: Can't easily determine if row was actually deleted without extra query
            return True
        except Exception as e:
            raise CacheBackendError(f"Failed to delete cache entry: {str(e)}") from e

    def _clear_raw(self) -> int:
        try:
            # Get count before deletion
            result = self.db.query_one(f"SELECT COUNT(*) as count FROM {CACHE_TABLE_NAME}")
            count = result["count"] if result else 0

            self.db.execute(f"DELETE FROM {CACHE_TABLE_NAME}")
            return count

        except Exception as e:
            raise CacheBackendError(f"Failed to clear cache: {str(e)}") from e

    def _keys_raw(self) -> List[str]:
        try:
            results = self.db.query_all(f"SELECT cache_key FROM {CACHE_TABLE_NAME}")
            return [row["cache_key"] for row in results]

        except Exception as e:
            raise CacheBackendError(f"Failed to get cache keys: {str(e)}") from e


class FileBackend(CacheBackend):
    """File-based cache backend."""

    def __init__(self, cache_dir: str = "/tmp/basefunctions_cache"):
        super().__init__()
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

    def _get_cache_path(self, key: str) -> str:
        """Get file path for cache key."""
        # Hash key to avoid filesystem issues
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{key_hash}.cache")

    def _get_raw(self, key: str) -> Optional[CacheEntry]:
        cache_path = self._get_cache_path(key)

        if not os.path.exists(cache_path):
            return None

        try:
            with open(cache_path, "rb") as f:
                return pickle.load(f)
        except Exception:
            # Corrupted file, remove it
            try:
                os.remove(cache_path)
            except:
                pass
            return None

    def _set_raw(self, key: str, entry: CacheEntry) -> None:
        cache_path = self._get_cache_path(key)

        try:
            with open(cache_path, "wb") as f:
                pickle.dump(entry, f)
        except Exception as e:
            raise CacheBackendError(f"Failed to write cache file: {str(e)}") from e

    def _delete_raw(self, key: str) -> bool:
        cache_path = self._get_cache_path(key)

        if os.path.exists(cache_path):
            try:
                os.remove(cache_path)
                return True
            except Exception:
                return False
        return False

    def _clear_raw(self) -> int:
        count = 0
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith(".cache"):
                    file_path = os.path.join(self.cache_dir, filename)
                    try:
                        os.remove(file_path)
                        count += 1
                    except:
                        pass
        except Exception:
            pass
        return count

    def _keys_raw(self) -> List[str]:
        # Note: We can't easily reconstruct original keys from hashed filenames
        # This is a limitation of the file backend
        keys = []
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith(".cache"):
                    keys.append(filename[:-6])  # Remove .cache extension
        except Exception:
            pass
        return keys


class MultiLevelBackend(CacheBackend):
    """Multi-level cache backend (L1 -> L2 -> L3)."""

    def __init__(self, backends: List[Tuple[str, Dict[str, Any]]]):
        super().__init__()
        self.backends: List[CacheBackend] = []

        # Create backend instances
        factory = CacheFactory()
        for backend_type, config in backends:
            backend = factory._create_backend(backend_type, **config)
            self.backends.append(backend)

    def _get_raw(self, key: str) -> Optional[CacheEntry]:
        # Try each backend in order
        for i, backend in enumerate(self.backends):
            entry = backend._get_raw(key)
            if entry is not None and not entry.is_expired():
                # Promote to higher levels
                for j in range(i):
                    self.backends[j]._set_raw(key, entry)
                return entry
        return None

    def _set_raw(self, key: str, entry: CacheEntry) -> None:
        # Set in all backends
        for backend in self.backends:
            backend._set_raw(key, entry)

    def _delete_raw(self, key: str) -> bool:
        # Delete from all backends
        deleted = False
        for backend in self.backends:
            if backend._delete_raw(key):
                deleted = True
        return deleted

    def _clear_raw(self) -> int:
        total_count = 0
        for backend in self.backends:
            total_count += backend._clear_raw()
        return total_count

    def _keys_raw(self) -> List[str]:
        # Union of all keys
        all_keys = set()
        for backend in self.backends:
            all_keys.update(backend._keys_raw())
        return list(all_keys)


class CacheManager:
    """High-level cache manager interface."""

    def __init__(self, backend: CacheBackend):
        self.backend = backend

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        return self.backend.get(key)

    def set(self, key: str, value: Any, ttl: int = DEFAULT_TTL) -> None:
        """Set value in cache."""
        self.backend.set(key, value, ttl)

    def get_or_set(self, key: str, callable_func: Callable[[], Any], ttl: int = DEFAULT_TTL) -> Any:
        """Get value or compute and cache it."""
        value = self.backend.get(key)
        if value is not None:
            return value

        # Compute value
        computed_value = callable_func()
        self.backend.set(key, computed_value, ttl)
        return computed_value

    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        return self.backend.delete(key)

    def exists(self, key: str) -> bool:
        """Check if key exists."""
        return self.backend.exists(key)

    def clear(self, pattern: str = "*") -> int:
        """Clear cache entries."""
        return self.backend.clear(pattern)

    def keys(self, pattern: str = "*") -> List[str]:
        """Get all keys matching pattern."""
        return self.backend.keys(pattern)

    def size(self) -> int:
        """Get cache size."""
        return self.backend.size()

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return self.backend.get_stats()

    def expire(self, key: str, ttl: int) -> bool:
        """Set TTL for existing key."""
        return self.backend.expire(key, ttl)

    def ttl(self, key: str) -> Optional[int]:
        """Get remaining TTL."""
        return self.backend.ttl(key)

    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate keys matching pattern."""
        return self.backend.clear(pattern)


@basefunctions.singleton
class CacheFactory:
    """Factory for creating cache instances."""

    def __init__(self):
        self._backends: Dict[str, type] = {
            "memory": MemoryBackend,
            "database": DatabaseBackend,
            "file": FileBackend,
            "multi": MultiLevelBackend,
        }

    def get_cache(self, backend: str = "memory", **config) -> CacheManager:
        """
        Create cache manager with specified backend.

        Parameters
        ----------
        backend : str, optional
            Backend type (memory, database, file, multi), by default "memory"
        **config
            Backend-specific configuration

        Returns
        -------
        CacheManager
            Configured cache manager
        """
        backend_instance = self._create_backend(backend, **config)
        return CacheManager(backend_instance)

    def _create_backend(self, backend: str, **config) -> CacheBackend:
        """Create backend instance."""
        if backend not in self._backends:
            available = ", ".join(self._backends.keys())
            raise CacheError(f"Unknown backend '{backend}'. Available: {available}")

        backend_class = self._backends[backend]

        try:
            return backend_class(**config)
        except Exception as e:
            raise CacheError(f"Failed to create {backend} backend: {str(e)}") from e

    def register_backend(self, name: str, backend_class: type) -> None:
        """Register custom cache backend."""
        if not issubclass(backend_class, CacheBackend):
            raise TypeError("backend_class must be subclass of CacheBackend")

        self._backends[name] = backend_class


# -------------------------------------------------------------
# CONVENIENCE FUNCTIONS
# -------------------------------------------------------------


def get_cache(backend: str = "memory", **config) -> CacheManager:
    """
    Convenience function to get cache manager.

    Parameters
    ----------
    backend : str, optional
        Backend type, by default "memory"
    **config
        Backend configuration

    Returns
    -------
    CacheManager
        Cache manager instance
    """
    factory = CacheFactory()
    return factory.get_cache(backend, **config)
