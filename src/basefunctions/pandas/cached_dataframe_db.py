"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich
  Project : basefunctions
  Copyright (c) by neuraldevelopment
  All rights reserved.
  Description:
  Cached DataFrame database with Write-Back cache pattern implementation
 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Optional, List, Dict, Any
import pandas as pd
import basefunctions

# -------------------------------------------------------------
# DEFINITIONS REGISTRY
# -------------------------------------------------------------

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------
DEFAULT_CACHE_TTL = 3600  # 1 hour

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


class CacheEntry:
    """Cache entry with dirty flag for write-back pattern."""

    def __init__(self, dataframe: pd.DataFrame, table_name: str, is_dirty: bool = False):
        self.dataframe = dataframe.copy()
        self.table_name = table_name
        self.is_dirty = is_dirty
        self.write_params = {"if_exists": "append", "index": False, "method": None, "timeout": 30, "max_retries": 3}


class CachedDataFrameDb(basefunctions.DataFrameDb):
    """
    DataFrame database with Write-Back cache pattern.

    Write-Back Cache Pattern:
    - write() stores DataFrame in cache (dirty)
    - read() returns from cache or loads from DB
    - flush() writes all dirty entries to DB
    """

    def __init__(
        self,
        instance_name: str,
        database_name: str,
        cache_ttl: int = DEFAULT_CACHE_TTL,
    ) -> None:
        """
        Initialize cached DataFrame database with Write-Back pattern.

        Parameters
        ----------
        instance_name : str
            Name of the database instance
        database_name : str
            Name of the database
        cache_ttl : int, optional
            Cache time-to-live in seconds, by default 3600

        Raises
        ------
        DataFrameValidationError
            If parameters are invalid
        DataFrameCacheError
            If cache initialization fails
        """
        super().__init__(instance_name, database_name)

        self.cache_ttl = cache_ttl

        # Unified cache for DataFrames (Write-Back pattern)
        self._cache: Dict[str, CacheEntry] = {}

        self.logger.debug(f"CachedDataFrameDb initialized with Write-Back pattern (TTL={cache_ttl}s)")

    def _generate_cache_key(self, table_name: str, query: Optional[str] = None, params: Optional[List] = None) -> str:
        """
        Generate cache key for operations.

        Parameters
        ----------
        table_name : str
            Name of the table
        query : Optional[str], optional
            SQL query
        params : Optional[List], optional
            Query parameters

        Returns
        -------
        str
            Cache key
        """
        # Use simple readable key format instead of MD5 hash
        query_part = query or "full_table"
        params_part = str(params or [])
        return f"{self.instance_name}:{self.database_name}:{table_name}:{query_part}:{params_part}"

    def read(
        self,
        table_name: str,
        query: Optional[str] = None,
        params: Optional[List] = None,
        timeout: int = 30,
        max_retries: int = 3,
        use_cache: bool = True,
    ) -> pd.DataFrame:
        """
        Read DataFrame with Write-Back cache support.

        Parameters
        ----------
        table_name : str
            Name of the table to read from
        query : Optional[str], optional
            Custom SQL query. If None, reads entire table
        params : Optional[List], optional
            Parameters for SQL query
        timeout : int, optional
            Timeout in seconds, by default 30
        max_retries : int, optional
            Maximum retry attempts, by default 3
        use_cache : bool, optional
            Whether to use cache, by default True

        Returns
        -------
        pd.DataFrame
            DataFrame containing query results

        Raises
        ------
        DataFrameValidationError
            If parameters are invalid
        DataFrameCacheError
            If cache operation fails
        """
        if not use_cache:
            return super().read(table_name, query, params, timeout, max_retries)

        try:
            cache_key = self._generate_cache_key(table_name, query, params)

            # Check cache first
            if cache_key in self._cache:
                self.logger.debug(f"Cache hit for table '{table_name}'")
                return self._cache[cache_key].dataframe.copy()

            # Cache miss - load from database
            self.logger.debug(f"Cache miss for table '{table_name}' - reading from database")
            dataframe = super().read(table_name, query, params, timeout, max_retries)

            # Store in cache (clean entry)
            self._cache[cache_key] = CacheEntry(dataframe, table_name, is_dirty=False)
            self.logger.debug(f"Cached result for table '{table_name}' (clean)")

            return dataframe.copy()

        except Exception as e:
            if isinstance(e, (basefunctions.DataFrameValidationError, basefunctions.DataFrameCacheError)):
                raise
            raise basefunctions.DataFrameCacheError(
                f"Cached read operation failed: {str(e)}",
                error_code=basefunctions.DataFrameDbErrorCodes.CACHE_WRITE_FAILED,
                cache_key=cache_key if "cache_key" in locals() else None,
                cache_operation="read",
                original_error=e,
            )

    def write(
        self,
        dataframe: pd.DataFrame,
        table_name: str,
        if_exists: str = "append",
        index: bool = False,
        method: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        immediate: bool = False,
    ) -> bool:
        """
        Write DataFrame using Write-Back cache pattern.

        Parameters
        ----------
        dataframe : pd.DataFrame
            DataFrame to write to database
        table_name : str
            Name of the target table
        if_exists : str, optional
            What to do if table exists, by default "append"
        index : bool, optional
            Whether to write DataFrame index, by default False
        method : Optional[str], optional
            Insertion method, by default None
        timeout : int, optional
            Timeout in seconds, by default 30
        max_retries : int, optional
            Maximum retry attempts, by default 3
        immediate : bool, optional
            Whether to write immediately or cache, by default False

        Returns
        -------
        bool
            True if operation was successful

        Raises
        ------
        DataFrameValidationError
            If parameters are invalid
        DataFrameCacheError
            If cache operation fails
        """
        # Validate inputs
        if not isinstance(dataframe, pd.DataFrame):
            raise basefunctions.DataFrameValidationError(
                "dataframe parameter must be pandas DataFrame",
                error_code=basefunctions.DataFrameDbErrorCodes.TYPE_MISMATCH,
            )

        if not table_name:
            raise basefunctions.DataFrameValidationError(
                "table_name cannot be empty", error_code=basefunctions.DataFrameDbErrorCodes.INVALID_STRUCTURE
            )

        if dataframe.empty:
            raise basefunctions.DataFrameValidationError(
                "Cannot write empty DataFrame",
                error_code=basefunctions.DataFrameDbErrorCodes.EMPTY_DATAFRAME,
                dataframe_shape=dataframe.shape,
            )

        try:
            if immediate:
                # Write immediately, bypass cache
                result = super().write(dataframe, table_name, if_exists, index, method, timeout, max_retries)
                # Invalidate cache for this table
                self._invalidate_cache(table_name)
                return result

            # Write-Back: Store in cache as dirty
            cache_key = self._generate_cache_key(table_name)

            if cache_key in self._cache and if_exists == "append":
                # Append to existing cached DataFrame
                existing_entry = self._cache[cache_key]
                existing_df = existing_entry.dataframe
                combined_df = pd.concat([existing_df, dataframe], ignore_index=True)
                self._cache[cache_key] = CacheEntry(combined_df, table_name, is_dirty=True)
                self.logger.debug(
                    f"Appended {len(dataframe)} rows to cached table '{table_name}' (total: {len(combined_df)})"
                )
            else:
                # New or replace - create new cache entry
                cache_entry = CacheEntry(dataframe, table_name, is_dirty=True)
                cache_entry.write_params = {
                    "if_exists": if_exists,
                    "index": index,
                    "method": method,
                    "timeout": timeout,
                    "max_retries": max_retries,
                }
                self._cache[cache_key] = cache_entry
                self.logger.debug(f"Cached {len(dataframe)} rows for table '{table_name}' (dirty)")

            return True

        except Exception as e:
            if isinstance(e, (basefunctions.DataFrameValidationError, basefunctions.DataFrameCacheError)):
                raise
            raise basefunctions.DataFrameCacheError(
                f"Cached write operation failed: {str(e)}",
                error_code=basefunctions.DataFrameDbErrorCodes.CACHE_WRITE_FAILED,
                cache_operation="write",
                original_error=e,
            )

    def flush(self, force: bool = False) -> int:
        """
        Flush all dirty cache entries to database.

        Parameters
        ----------
        force : bool, optional
            Force flush even clean entries, by default False

        Returns
        -------
        int
            Number of tables flushed

        Raises
        ------
        DataFrameCacheError
            If flush operation fails
        """
        try:
            flushed_count = 0

            for cache_key, cache_entry in list(self._cache.items()):
                if cache_entry.is_dirty or force:
                    try:
                        # Write to database
                        result = super().write(
                            cache_entry.dataframe,
                            cache_entry.table_name,
                            cache_entry.write_params["if_exists"],
                            cache_entry.write_params["index"],
                            cache_entry.write_params["method"],
                            cache_entry.write_params["timeout"],
                            cache_entry.write_params["max_retries"],
                        )

                        if result:
                            # Mark as clean
                            cache_entry.is_dirty = False
                            flushed_count += 1
                            self.logger.debug(f"Flushed cache entry to database (key: {cache_key[:8]}...)")

                    except Exception as e:
                        self.logger.error(f"Failed to flush cache entry {cache_key[:8]}...: {str(e)}")
                        raise

            self.logger.debug(f"Flushed {flushed_count} cache entries to database")
            return flushed_count

        except Exception as e:
            raise basefunctions.DataFrameCacheError(
                "Flush operation failed",
                error_code=basefunctions.DataFrameDbErrorCodes.FLUSH_FAILED,
                cache_operation="flush",
                original_error=e,
            )

    def _extract_table_name_from_key(self, cache_key: str) -> str:
        """
        Extract table name from cache key.

        Parameters
        ----------
        cache_key : str
            Cache key in format: instance:database:table:query:params

        Returns
        -------
        str
            Table name
        """
        try:
            parts = cache_key.split(":")
            if len(parts) >= 3:
                return parts[2]  # table_name is third part
            return "unknown_table"
        except Exception:
            return "unknown_table"

    def _invalidate_cache(self, table_name: str) -> None:
        """
        Invalidate cache entries for a table.

        Parameters
        ----------
        table_name : str
            Name of table to invalidate
        """
        try:
            keys_to_remove = []
            for cache_key, cache_entry in self._cache.items():
                # Check if this cache entry belongs to the table
                if cache_entry.table_name == table_name:
                    keys_to_remove.append(cache_key)

            for key in keys_to_remove:
                del self._cache[key]

            if keys_to_remove:
                self.logger.debug(f"Invalidated {len(keys_to_remove)} cache entries for table '{table_name}'")

        except Exception as e:
            self.logger.warning(f"Failed to invalidate cache for table '{table_name}': {str(e)}")

    def clear_cache(self, table_pattern: str = "*") -> int:
        """
        Clear cache entries matching pattern.

        Parameters
        ----------
        table_pattern : str, optional
            Pattern to match table names, by default "*"

        Returns
        -------
        int
            Number of cache entries cleared
        """
        try:
            if table_pattern == "*":
                count = len(self._cache)
                self._cache.clear()
                self.logger.debug(f"Cleared all {count} cache entries")
                return count

            keys_to_remove = []
            for cache_key in self._cache.keys():
                if table_pattern in cache_key:
                    keys_to_remove.append(cache_key)

            for key in keys_to_remove:
                del self._cache[key]

            self.logger.debug(f"Cleared {len(keys_to_remove)} cache entries matching pattern '{table_pattern}'")
            return len(keys_to_remove)

        except Exception as e:
            raise basefunctions.DataFrameCacheError(
                f"Failed to clear cache with pattern '{table_pattern}'",
                error_code=basefunctions.DataFrameDbErrorCodes.CACHE_WRITE_FAILED,
                cache_operation="clear",
                original_error=e,
            )

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns
        -------
        Dict[str, Any]
            Cache statistics
        """
        try:
            dirty_count = sum(1 for entry in self._cache.values() if entry.is_dirty)
            clean_count = len(self._cache) - dirty_count
            total_rows = sum(len(entry.dataframe) for entry in self._cache.values())

            return {
                "cache": {
                    "total_entries": len(self._cache),
                    "dirty_entries": dirty_count,
                    "clean_entries": clean_count,
                    "total_rows_cached": total_rows,
                },
                "config": {"cache_ttl": self.cache_ttl, "pattern": "Write-Back Cache"},
            }

        except Exception as e:
            self.logger.warning(f"Failed to get cache stats: {str(e)}")
            return {"error": str(e)}

    def __str__(self) -> str:
        """String representation for debugging."""
        dirty_count = sum(1 for entry in self._cache.values() if entry.is_dirty)
        return f"CachedDataFrameDb[{self.instance_name}.{self.database_name}, cached={len(self._cache)}, dirty={dirty_count}]"

    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return (
            f"CachedDataFrameDb(instance_name='{self.instance_name}', "
            f"database_name='{self.database_name}', cache_ttl={self.cache_ttl})"
        )
