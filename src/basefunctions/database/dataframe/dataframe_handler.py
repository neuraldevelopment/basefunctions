"""
=============================================================================

  Licensed Materials, Property of neuraldevelopment , Munich

  Project : basefunctions

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  DataFrame operations for database handling with caching and batch processing

 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Dict, List, Optional, Any, Union, Tuple, Callable
import threading
import pandas as pd
import basefunctions

# -------------------------------------------------------------
# DEFINITIONS REGISTRY
# -------------------------------------------------------------

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------
DEFAULT_CACHE_SIZE = 10
DEFAULT_BATCH_SIZE = 1000

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


class DataFrameHandler:
    """
    Handler for DataFrame operations with databases.
    Provides caching, batch processing, and async capabilities.
    Thread-safe implementation for concurrent access.
    """

    def __init__(
        self,
        db: Optional["basefunctions.Db"] = None,
        max_cache_size: int = DEFAULT_CACHE_SIZE,
        batch_size: int = DEFAULT_BATCH_SIZE,
    ) -> None:
        """
        Initialize DataFrame handler.

        parameters
        ----------
        db : Optional[basefunctions.Db], optional
            database to use, by default None
        max_cache_size : int, optional
            maximum number of DataFrames per table before auto-flush, by default 10
        batch_size : int, optional
            maximum rows per batch when processing large DataFrames, by default 1000
        """
        self.db = db
        self.max_cache_size = max_cache_size
        self.batch_size = batch_size
        self.dataframe_cache: Dict[str, List[pd.DataFrame]] = {}
        self.logger = basefunctions.get_logger(__name__)
        self.lock = threading.RLock()

    def set_database(self, db: "basefunctions.Db") -> None:
        """
        Set the database to use for operations.

        parameters
        ----------
        db : basefunctions.Db
            database to use
        """
        with self.lock:
            self.db = db

    def add_dataframe(
        self,
        table_name: str,
        df: pd.DataFrame,
        cached: bool = True,
        async_write: bool = False,
        callback: Optional[Callable[[bool, str], None]] = None,
    ) -> str:
        """
        Add a DataFrame to a database table.

        parameters
        ----------
        table_name : str
            name of the target table
        df : pd.DataFrame
            dataframe to add
        cached : bool, optional
            whether to cache the dataframe for batch writing, by default True
        async_write : bool, optional
            whether to write asynchronously using ThreadPool, by default False
        callback : Optional[Callable[[bool, str], None]], optional
            callback function called after async write completes, by default None

        returns
        -------
        str
            operation ID (for async operations) or empty string

        raises
        ------
        ValueError
            if no database set and not provided
        """
        with self.lock:
            if self.db is None:
                raise ValueError("no database set for DataFrameHandler")

            if df is None or df.empty:
                self.logger.warning("empty dataframe provided, nothing to add")
                return ""

            if cached:
                # Add to cache for later batch writing
                if table_name not in self.dataframe_cache:
                    self.dataframe_cache[table_name] = []

                self.dataframe_cache[table_name].append(df)

                # Auto-flush if cache is too large
                if len(self.dataframe_cache[table_name]) >= self.max_cache_size:
                    return self.flush_cache(table_name, async_write, callback)

                return ""

            # Direct write (not cached)
            if async_write:
                # Get ThreadPool from instance manager
                threadpool = self._get_threadpool()
                if threadpool is None:
                    self.logger.warning(
                        "threadpool not configured, falling back to synchronous write"
                    )
                    self._write_dataframe_direct(table_name, df)
                    return ""

                # Create task content
                task_content = {
                    "operation": "write_dataframe",
                    "table_name": table_name,
                    "dataframe": df,
                    "db_instance": self.db.instance.instance_name,
                    "db_name": self.db.db_name,
                    "callback": callback,
                }

                # Submit task to ThreadPool
                task_id = threadpool.submit_task("dataframe_operation", task_content)
                return task_id

            # Synchronous direct write
            self._write_dataframe_direct(table_name, df)
            return ""

    def _write_dataframe_direct(self, table_name: str, df: pd.DataFrame) -> None:
        """
        Write a DataFrame directly to the database.

        parameters
        ----------
        table_name : str
            name of the target table
        df : pd.DataFrame
            dataframe to write
        """
        try:
            # Use pandas to_sql for direct write
            connection = self.db.instance.get_connection().get_connection()

            # Check if DataFrame is large, if so split into batches
            if len(df) > self.batch_size:
                total_rows = len(df)
                self.logger.warning(f"splitting large dataframe ({total_rows} rows) into batches")

                # Process in batches
                for i in range(0, total_rows, self.batch_size):
                    end_idx = min(i + self.batch_size, total_rows)
                    batch = df.iloc[i:end_idx]

                    # Determine if this is the first batch (or only batch)
                    if_exists = (
                        "append"
                        if i > 0
                        else "replace" if getattr(self, "_replace_table", False) else "append"
                    )

                    batch.to_sql(table_name, connection, if_exists=if_exists, index=False)

                    # After first batch, always append
                    if i == 0 and if_exists == "replace":
                        self._replace_table = False
            else:
                # Small DataFrame, write directly
                if_exists = "replace" if getattr(self, "_replace_table", False) else "append"
                df.to_sql(table_name, connection, if_exists=if_exists, index=False)

                # Reset replace flag if it was set
                if if_exists == "replace":
                    self._replace_table = False

        except Exception as e:
            self.logger.critical(f"failed to write dataframe to {table_name}: {str(e)}")
            raise basefunctions.DataFrameError(
                f"failed to write dataframe to {table_name}: {str(e)}"
            ) from e

    def flush_cache(
        self,
        table_name: Optional[str] = None,
        async_write: bool = False,
        callback: Optional[Callable[[bool, str], None]] = None,
    ) -> str:
        """
        Flush cached DataFrames to the database.

        parameters
        ----------
        table_name : Optional[str], optional
            name of the table to flush, or all tables if None, by default None
        async_write : bool, optional
            whether to write asynchronously using ThreadPool, by default False
        callback : Optional[Callable[[bool, str], None]], optional
            callback function called after async write completes, by default None

        returns
        -------
        str
            operation ID (for async operations) or empty string

        raises
        ------
        ValueError
            if no database set
        """
        with self.lock:
            if self.db is None:
                raise ValueError("no database set for DataFrameHandler")

            # Determine which tables to flush
            tables_to_flush = [table_name] if table_name else list(self.dataframe_cache.keys())

            if not tables_to_flush or all(
                not self.dataframe_cache.get(t, []) for t in tables_to_flush
            ):
                # Nothing to flush
                return ""

            if async_write:
                # Get ThreadPool from instance manager
                threadpool = self._get_threadpool()
                if threadpool is None:
                    self.logger.warning(
                        "threadpool not configured, falling back to synchronous flush"
                    )
                    self._flush_cache_sync(tables_to_flush)
                    return ""

                # Create a copy of cache to avoid race conditions
                cache_copy = {}
                for table in tables_to_flush:
                    if table in self.dataframe_cache and self.dataframe_cache[table]:
                        cache_copy[table] = self.dataframe_cache[table].copy()
                        # Clear cache after copying
                        self.dataframe_cache[table] = []

                # Create task content
                task_content = {
                    "operation": "flush_cache",
                    "cache": cache_copy,
                    "db_instance": self.db.instance.instance_name,
                    "db_name": self.db.db_name,
                    "callback": callback,
                }

                # Submit task to ThreadPool
                task_id = threadpool.submit_task("dataframe_operation", task_content)
                return task_id

            # Synchronous flush
            self._flush_cache_sync(tables_to_flush)
            return ""

    def _flush_cache_sync(self, tables: List[str]) -> None:
        """
        Synchronously flush cached DataFrames to the database.

        parameters
        ----------
        tables : List[str]
            list of tables to flush
        """
        for table in tables:
            if table not in self.dataframe_cache or not self.dataframe_cache[table]:
                continue

            try:
                # Combine all DataFrames for this table
                frames = self.dataframe_cache[table]
                if not frames:
                    continue

                combined_df = pd.concat(frames, ignore_index=True)

                # Write combined DataFrame to database
                self._write_dataframe_direct(table, combined_df)

                # Clear cache after successful write
                self.dataframe_cache[table] = []
            except Exception as e:
                self.logger.critical(f"failed to flush cache for table {table}: {str(e)}")
                # Don't clear cache on error so it can be retried
                raise basefunctions.DataFrameError(
                    f"failed to flush cache for table {table}: {str(e)}"
                ) from e

    def clear_cache(self, table_name: Optional[str] = None) -> None:
        """
        Clear DataFrame cache without writing to the database.

        parameters
        ----------
        table_name : Optional[str], optional
            name of the table to clear, or all tables if None, by default None
        """
        with self.lock:
            if table_name:
                # Clear specific table
                if table_name in self.dataframe_cache:
                    self.dataframe_cache[table_name] = []
            else:
                # Clear all tables
                self.dataframe_cache.clear()

    def get_cache_stats(self) -> Dict[str, Dict[str, int]]:
        """
        Get statistics about the DataFrame cache.

        returns
        -------
        Dict[str, Dict[str, int]]
            dictionary with table names as keys and cache statistics as values
        """
        with self.lock:
            stats = {}
            for table, frames in self.dataframe_cache.items():
                stats[table] = {"frames": len(frames), "total_rows": sum(len(df) for df in frames)}
            return stats

    def has_cached_data(self) -> bool:
        """
        Check if there is any cached data.

        returns
        -------
        bool
            True if cache contains any data, False otherwise
        """
        with self.lock:
            return any(frames for frames in self.dataframe_cache.values())

    def set_replace_mode(self, replace: bool = True) -> None:
        """
        Set whether to replace (overwrite) tables instead of appending.

        parameters
        ----------
        replace : bool, optional
            whether to replace tables when writing, by default True
        """
        with self.lock:
            self._replace_table = replace

    def query_to_dataframe(
        self,
        query: str,
        parameters: Union[tuple, dict] = (),
        async_query: bool = False,
        callback: Optional[Callable[[bool, pd.DataFrame], None]] = None,
    ) -> Union[pd.DataFrame, str]:
        """
        Execute SQL query and return results as DataFrame.

        parameters
        ----------
        query : str
            SQL query to execute
        parameters : Union[tuple, dict], optional
            query parameters, by default ()
        async_query : bool, optional
            whether to execute query asynchronously, by default False
        callback : Optional[Callable[[bool, pd.DataFrame], None]], optional
            callback function called after async query completes, by default None

        returns
        -------
        Union[pd.DataFrame, str]
            DataFrame with query results or task ID for async operations

        raises
        ------
        ValueError
            if no database set
        """
        with self.lock:
            if self.db is None:
                raise ValueError("no database set for DataFrameHandler")

            if async_query:
                # Get ThreadPool from instance manager
                threadpool = self._get_threadpool()
                if threadpool is None:
                    self.logger.warning(
                        "threadpool not configured, falling back to synchronous query"
                    )
                    return self.db.query_to_dataframe(query, parameters)

                # Create task content
                task_content = {
                    "operation": "query_to_dataframe",
                    "query": query,
                    "parameters": parameters,
                    "db_instance": self.db.instance.instance_name,
                    "db_name": self.db.db_name,
                    "callback": callback,
                }

                # Submit task to ThreadPool
                task_id = threadpool.submit_task("dataframe_operation", task_content)
                return task_id

            # Synchronous query
            return self.db.query_to_dataframe(query, parameters)

    def _get_threadpool(self) -> Optional["basefunctions.DbThreadPool"]:
        """
        Get ThreadPool from database instance manager.

        returns
        -------
        Optional[basefunctions.DbThreadPool]
            ThreadPool or None if not configured
        """
        if self.db is None or self.db.instance is None:
            return None

        manager = self.db.instance.get_manager()
        if manager is None:
            return None

        return manager.get_threadpool()
