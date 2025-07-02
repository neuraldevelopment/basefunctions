"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich

  Project : basefunctions

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  Cached DataFrame database abstraction with performance-optimized batch operations

  Log:
  v1.0 : Initial implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Optional, Any, List, Dict
import threading
import hashlib
import pandas as pd
import basefunctions

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------

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


class CachedDataFrameDb:
    """
    Cached DataFrame database abstraction with batch write optimization.

    Provides write caching for batch operations and read caching for query optimization.
    Uses composition with DataFrameDb for actual database operations.
    """

    def __init__(self, instance_name: str, database_name: str) -> None:
        """
        Initialize cached DataFrame database interface.

        Parameters
        ----------
        instance_name : str
            Name of the database instance
        database_name : str
            Name of the database

        Raises
        ------
        DataFrameValidationError
            If parameters are invalid
        """
        self.dataframe_db = basefunctions.DataFrameDb(instance_name, database_name)
        self.logger = basefunctions.get_logger(__name__)

        # Write cache: table_name -> list of DataFrames
        self._write_cache: Dict[str, List[pd.DataFrame]] = {}
        self._write_lock = threading.RLock()

        # Read cache: query_hash -> DataFrame
        self._read_cache: Dict[str, pd.DataFrame] = {}
        self._read_lock = threading.RLock()

    def _generate_query_hash(self, table_name: str, query: Optional[str] = None, params: Optional[List] = None) -> str:
        """
        Generate cache key from query parameters.

        Parameters
        ----------
        table_name : str
            Name of the table
        query : Optional[str]
            SQL query string
        params : Optional[List]
            Query parameters

        Returns
        -------
        str
            SHA256 hash of query components
        """
        components = [table_name]
        if query:
            components.append(query)
        if params:
            components.extend(str(p) for p in params)

        hash_input = "|".join(components).encode("utf-8")
        return hashlib.sha256(hash_input).hexdigest()

    def write(
        self,
        dataframe: pd.DataFrame,
        table_name: str,
        if_exists: str = "append",
        index: bool = False,
        method: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
    ) -> str:
        """
        Cache DataFrame for batch write operation (non-blocking).

        Parameters
        ----------
        dataframe : pd.DataFrame
            DataFrame to write
        table_name : str
            Target table name
        if_exists : str, optional
            How to handle existing table, by default "append"
        index : bool, optional
            Whether to write index, by default False
        method : Optional[str], optional
            Write method, by default None
        timeout : int, optional
            Operation timeout, by default 30
        max_retries : int, optional
            Maximum retries, by default 3

        Returns
        -------
        str
            Cache operation ID (for consistency with DataFrameDb)

        Raises
        ------
        DataFrameValidationError
            If DataFrame is invalid
        """
        if dataframe.empty:
            raise basefunctions.DataFrameValidationError(
                "Cannot cache empty DataFrame",
                error_code=basefunctions.DataFrameDbErrorCodes.EMPTY_DATAFRAME,
                dataframe_shape=dataframe.shape,
            )

        with self._write_lock:
            if table_name not in self._write_cache:
                self._write_cache[table_name] = []

            self._write_cache[table_name].append(dataframe.copy())
            self.logger.debug(
                f"Cached DataFrame for table '{table_name}', cache size: {len(self._write_cache[table_name])}"
            )

        # Return synthetic ID for cached operation
        return f"cache_{table_name}_{len(self._write_cache[table_name])}"

    def read(
        self,
        table_name: str,
        query: Optional[str] = None,
        params: Optional[List] = None,
        timeout: int = 30,
        max_retries: int = 3,
    ) -> str:
        """
        Read DataFrame with caching support (non-blocking).

        Parameters
        ----------
        table_name : str
            Name of the table to read
        query : Optional[str], optional
            SQL query string, by default None
        params : Optional[List], optional
            Query parameters, by default None
        timeout : int, optional
            Operation timeout, by default 30
        max_retries : int, optional
            Maximum retries, by default 3

        Returns
        -------
        str
            Event ID for result tracking

        Raises
        ------
        DataFrameDbError
            If read operation fails
        """
        query_hash = self._generate_query_hash(table_name, query, params)

        # Check read cache
        with self._read_lock:
            if query_hash in self._read_cache:
                self.logger.debug(f"Cache hit for query hash: {query_hash[:16]}...")
                # Return synthetic ID for cached result
                return f"cache_hit_{query_hash[:16]}"

        # Cache miss - delegate to DataFrameDb
        self.logger.debug(f"Cache miss for query hash: {query_hash[:16]}...")
        return self.dataframe_db.read(table_name, query, params, timeout, max_retries)

    def flush(self, table_name: Optional[str] = None) -> List[str]:
        """
        Flush cached DataFrames to database using batch operations (non-blocking).

        Parameters
        ----------
        table_name : Optional[str], optional
            Specific table to flush, None for all tables, by default None

        Returns
        -------
        List[str]
            List of event IDs from flush operations

        Raises
        ------
        DataFrameCacheError
            If flush operation fails
        """
        with self._write_lock:
            tables_to_flush = [table_name] if table_name else list(self._write_cache.keys())

            if not tables_to_flush:
                self.logger.debug("No tables to flush")
                return []

            event_ids = []
            try:
                for table in tables_to_flush:
                    if table not in self._write_cache or not self._write_cache[table]:
                        continue

                    # Concatenate all DataFrames for this table
                    dataframes = self._write_cache[table]
                    if len(dataframes) == 1:
                        combined_df = dataframes[0]
                    else:
                        combined_df = pd.concat(dataframes, ignore_index=True)

                    # Write to database (non-blocking)
                    event_id = self.dataframe_db.write(combined_df, table)
                    event_ids.append(event_id)

                    # Clear cache for this table after submit
                    del self._write_cache[table]
                    self.logger.debug(f"Flushed {len(dataframes)} DataFrames for table '{table}'")

                return event_ids

            except Exception as e:
                raise basefunctions.DataFrameCacheError(
                    f"Flush operation failed: {str(e)}",
                    error_code=basefunctions.DataFrameDbErrorCodes.DATAFRAME_CACHE_ERROR,
                    cache_operation="flush",
                    original_error=e,
                )

    def get_results(self) -> Dict[str, Any]:
        """
        Get results from underlying DataFrameDb and merge with cache hits.

        Returns
        -------
        Dict[str, Any]
            Combined results from EventBus and cache operations
        """
        # Wait for completion and get results from DataFrameDb
        results = self.dataframe_db.get_results()

        # Add cache hit results
        with self._read_lock:
            for query_hash, dataframe in self._read_cache.items():
                cache_id = f"cache_hit_{query_hash[:16]}"
                if cache_id not in results:
                    results[cache_id] = {"success": True, "data": dataframe.copy(), "error": None}

        return results

    def clear_write_cache(self, table_name: Optional[str] = None) -> None:
        """
        Clear write cache without writing to database.

        Parameters
        ----------
        table_name : Optional[str], optional
            Specific table to clear, None for all tables, by default None
        """
        with self._write_lock:
            if table_name:
                if table_name in self._write_cache:
                    del self._write_cache[table_name]
                    self.logger.debug(f"Cleared write cache for table '{table_name}'")
            else:
                self._write_cache.clear()
                self.logger.debug("Cleared all write cache")

    def clear_read_cache(self) -> None:
        """Clear read cache."""
        with self._read_lock:
            self._read_cache.clear()
            self.logger.debug("Cleared read cache")

    def clear_cache(self) -> None:
        """Clear both caches."""
        self.clear_write_cache()
        self.clear_read_cache()

    def __str__(self) -> str:
        """String representation for debugging."""
        return f"CachedDataFrameDb[{self.dataframe_db.instance_name}.{self.dataframe_db.database_name}]"

    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return f"CachedDataFrameDb(instance_name='{self.dataframe_db.instance_name}', database_name='{self.dataframe_db.database_name}')"
