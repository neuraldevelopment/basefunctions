"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich
  Project : basefunctions
  Copyright (c) by neuraldevelopment
  All rights reserved.
  Description:
  Cached DataFrame database with automatic batching and optimization
 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Optional, List, Dict, Any
import pandas as pd
import hashlib
import basefunctions

# -------------------------------------------------------------
# DEFINITIONS REGISTRY
# -------------------------------------------------------------

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------
DEFAULT_CACHE_TTL = 3600  # 1 hour
DEFAULT_BATCH_SIZE = 1000  # Rows per batch

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


class CachedDataFrameDb(basefunctions.DataFrameDb):
    """
    Enhanced DataFrame database with caching and write optimization.

    Features:
    - Memory caching for read operations
    - Write batching with automatic DataFrame concatenation
    - Optimized flush operations for identical table writes
    - Cache statistics and management
    """

    def __init__(
        self,
        instance_name: str,
        database_name: str,
        cache_ttl: int = DEFAULT_CACHE_TTL,
        batch_size: int = DEFAULT_BATCH_SIZE,
    ) -> None:
        """
        Initialize cached DataFrame database interface.

        Parameters
        ----------
        instance_name : str
            Name of the database instance
        database_name : str
            Name of the database
        cache_ttl : int, optional
            Cache time-to-live in seconds, by default 3600
        batch_size : int, optional
            Maximum rows per batch write, by default 1000

        Raises
        ------
        DataFrameValidationError
            If parameters are invalid
        DataFrameCacheError
            If cache initialization fails
        """
        super().__init__(instance_name, database_name)

        self.cache_ttl = cache_ttl
        self.batch_size = batch_size

        # Initialize cache manager
        try:
            self.cache_manager = basefunctions.get_cache("memory", max_size=10000)
        except Exception as e:
            raise basefunctions.create_cache_error(
                "Failed to initialize cache manager", cache_operation="init", original_error=e
            )

        # Write buffer for batching operations
        self._write_buffer: Dict[str, List[pd.DataFrame]] = {}

        self.logger.debug(f"CachedDataFrameDb initialized with TTL={cache_ttl}s, batch_size={batch_size}")

    def _generate_cache_key(self, table_name: str, query: Optional[str] = None, params: Optional[List] = None) -> str:
        """
        Generate cache key for read operations.

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
        key_components = [self.instance_name, self.database_name, table_name, query or "full_table", str(params or [])]

        key_string = "|".join(key_components)
        return hashlib.md5(key_string.encode()).hexdigest()

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
        Read DataFrame with caching support.

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
            # Bypass cache, use parent implementation
            return super().read(table_name, query, params, timeout, max_retries)

        try:
            # Generate cache key
            cache_key = self._generate_cache_key(table_name, query, params)

            # Try to get from cache first
            cached_result = self.cache_manager.get(cache_key)
            if cached_result is not None:
                self.logger.debug(f"Cache hit for table '{table_name}'")
                return cached_result.copy()  # Return copy to prevent modifications

            # Cache miss - read from database
            self.logger.debug(f"Cache miss for table '{table_name}' - reading from database")
            dataframe = super().read(table_name, query, params, timeout, max_retries)

            # Store in cache
            try:
                self.cache_manager.set(cache_key, dataframe.copy(), ttl=self.cache_ttl)
                self.logger.debug(f"Cached result for table '{table_name}' (TTL={self.cache_ttl}s)")
            except Exception as e:
                # Cache storage failure shouldn't break the read operation
                self.logger.warning(f"Failed to cache result: {str(e)}")

            return dataframe

        except Exception as e:
            if isinstance(e, (basefunctions.DataFrameValidationError, basefunctions.DataFrameCacheError)):
                raise
            raise basefunctions.create_cache_error(
                f"Cached read operation failed: {str(e)}",
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
        Write DataFrame with batching support.

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
            Whether to write immediately or buffer, by default False

        Returns
        -------
        bool
            True if operation was successful (buffered or written)

        Raises
        ------
        DataFrameValidationError
            If parameters are invalid
        DataFrameCacheError
            If cache operation fails
        """
        # Validate inputs (same as parent)
        if not isinstance(dataframe, pd.DataFrame):
            raise basefunctions.create_validation_error(
                "dataframe parameter must be pandas DataFrame",
                error_code=basefunctions.DataFrameDbErrorCodes.TYPE_MISMATCH,
            )

        if not table_name:
            raise basefunctions.create_validation_error(
                "table_name cannot be empty", error_code=basefunctions.DataFrameDbErrorCodes.INVALID_STRUCTURE
            )

        if dataframe.empty:
            raise basefunctions.create_validation_error(
                "Cannot write empty DataFrame",
                dataframe_shape=dataframe.shape,
                error_code=basefunctions.DataFrameDbErrorCodes.EMPTY_DATAFRAME,
            )

        try:
            if immediate:
                # Write immediately, bypass buffering
                result = super().write(dataframe, table_name, if_exists, index, method, timeout, max_retries)
                self._invalidate_cache(table_name)
                return result

            # Add to write buffer for batching
            if table_name not in self._write_buffer:
                self._write_buffer[table_name] = []

            # Store DataFrame with metadata
            buffered_df = dataframe.copy()
            buffered_df._cached_write_params = {
                "if_exists": if_exists,
                "index": index,
                "method": method,
                "timeout": timeout,
                "max_retries": max_retries,
            }

            self._write_buffer[table_name].append(buffered_df)

            self.logger.debug(
                f"Buffered {len(dataframe)} rows for table '{table_name}' "
                f"(total buffered: {len(self._write_buffer[table_name])} DataFrames)"
            )

            # Auto-flush if buffer gets too large
            total_rows = sum(len(df) for df in self._write_buffer[table_name])
            if total_rows >= self.batch_size:
                self.logger.debug(f"Auto-flushing table '{table_name}' (reached {total_rows} rows)")
                return self._flush_table(table_name)

            return True

        except Exception as e:
            if isinstance(e, (basefunctions.DataFrameValidationError, basefunctions.DataFrameCacheError)):
                raise
            raise basefunctions.create_cache_error(
                f"Cached write operation failed: {str(e)}", cache_operation="write", original_error=e
            )

    def flush(self, force: bool = False) -> int:
        """
        Flush all buffered DataFrames to database with optimization.

        Parameters
        ----------
        force : bool, optional
            Force flush even small buffers, by default False

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
            flushed_tables = 0
            tables_to_flush = list(self._write_buffer.keys())

            for table_name in tables_to_flush:
                if force or len(self._write_buffer[table_name]) > 0:
                    if self._flush_table(table_name):
                        flushed_tables += 1

            self.logger.debug(f"Flushed {flushed_tables} tables")
            return flushed_tables

        except Exception as e:
            raise basefunctions.create_cache_error("Flush operation failed", cache_operation="flush", original_error=e)

    def _flush_table(self, table_name: str) -> bool:
        """
        Flush buffered DataFrames for a specific table.

        Parameters
        ----------
        table_name : str
            Name of table to flush

        Returns
        -------
        bool
            True if flush was successful
        """
        if table_name not in self._write_buffer or not self._write_buffer[table_name]:
            return False

        try:
            buffered_dfs = self._write_buffer[table_name]

            # Concatenate all DataFrames for this table
            if len(buffered_dfs) == 1:
                combined_df = buffered_dfs[0]
            else:
                combined_df = pd.concat(buffered_dfs, ignore_index=True)
                self.logger.debug(f"Concatenated {len(buffered_dfs)} DataFrames into {len(combined_df)} rows")

            # Get write parameters from first DataFrame (assuming they're consistent)
            write_params = getattr(buffered_dfs[0], "_cached_write_params", {})

            # Write combined DataFrame
            result = super().write(
                combined_df,
                table_name,
                write_params.get("if_exists", "append"),
                write_params.get("index", False),
                write_params.get("method"),
                write_params.get("timeout", 30),
                write_params.get("max_retries", 3),
            )

            if result:
                # Clear buffer for this table
                del self._write_buffer[table_name]
                # Invalidate cache
                self._invalidate_cache(table_name)
                self.logger.debug(f"Successfully flushed table '{table_name}'")

            return result

        except Exception as e:
            self.logger.error(f"Failed to flush table '{table_name}': {str(e)}")
            raise basefunctions.create_cache_error(
                f"Failed to flush table '{table_name}'", cache_operation="flush", original_error=e
            )

    def _invalidate_cache(self, table_name: str) -> None:
        """
        Invalidate cache entries for a table.

        Parameters
        ----------
        table_name : str
            Name of table to invalidate
        """
        try:
            # Pattern to match cache keys for this table
            pattern = f"*{table_name}*"
            invalidated = self.cache_manager.clear(pattern)
            if invalidated > 0:
                self.logger.debug(f"Invalidated {invalidated} cache entries for table '{table_name}'")
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

        Raises
        ------
        DataFrameCacheError
            If cache clear operation fails
        """
        try:
            cleared = self.cache_manager.clear(table_pattern)
            self.logger.debug(f"Cleared {cleared} cache entries matching pattern '{table_pattern}'")
            return cleared
        except Exception as e:
            raise basefunctions.create_cache_error(
                f"Failed to clear cache with pattern '{table_pattern}'", cache_operation="clear", original_error=e
            )

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics and buffer information.

        Returns
        -------
        Dict[str, Any]
            Cache and buffer statistics
        """
        try:
            cache_stats = self.cache_manager.stats()

            # Add buffer statistics
            buffer_stats = {}
            total_buffered_rows = 0
            for table_name, dfs in self._write_buffer.items():
                rows = sum(len(df) for df in dfs)
                buffer_stats[table_name] = {"dataframes": len(dfs), "rows": rows}
                total_buffered_rows += rows

            return {
                "cache": cache_stats,
                "write_buffer": {
                    "tables": len(self._write_buffer),
                    "total_dataframes": sum(len(dfs) for dfs in self._write_buffer.values()),
                    "total_rows": total_buffered_rows,
                    "by_table": buffer_stats,
                },
                "config": {"cache_ttl": self.cache_ttl, "batch_size": self.batch_size},
            }
        except Exception as e:
            self.logger.warning(f"Failed to get cache stats: {str(e)}")
            return {"error": str(e)}

    def __str__(self) -> str:
        """
        String representation for debugging.

        Returns
        -------
        str
            String representation
        """
        buffered_tables = len(self._write_buffer)
        return f"CachedDataFrameDb[{self.instance_name}.{self.database_name}, buffered_tables={buffered_tables}]"

    def __repr__(self) -> str:
        """
        Detailed representation for debugging.

        Returns
        -------
        str
            Detailed representation
        """
        return (
            f"CachedDataFrameDb(instance_name='{self.instance_name}', "
            f"database_name='{self.database_name}', cache_ttl={self.cache_ttl}, "
            f"batch_size={self.batch_size})"
        )
