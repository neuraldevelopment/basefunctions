"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment , Munich
  Project : basefunctions
  Copyright (c) by neuraldevelopment
  All rights reserved.
  Description:
  Database abstraction layer providing direct access to database operations
 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Dict, List, Optional, Any, Union, Tuple
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

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


class Db:
    """
    Represents a specific database within a database instance,
    providing direct access to database operations.
    Thread-safe implementation for concurrent access.
    """

    def __init__(self, instance: "basefunctions.DbInstance", db_name: str) -> None:
        """
        Initialize database object.

        parameters
        ----------
        instance : basefunctions.DbInstance
            parent database instance
        db_name : str
            name of the database
        """
        self.instance = instance
        self.db_name = db_name
        self.logger = basefunctions.get_logger(__name__)
        self.lock = threading.RLock()
        self.dataframe_cache: Dict[str, List[pd.DataFrame]] = {}
        self.max_cache_size = 10
        self.last_query: Optional[str] = None

    def execute(self, query: str, parameters: Union[tuple, dict] = ()) -> None:
        """
        Execute a SQL query without returning a result.

        parameters
        ----------
        query : str
            SQL query to execute
        parameters : Union[tuple, dict], optional
            query parameters, by default ()

        raises
        ------
        basefunctions.QueryError
            if query execution fails
        """
        with self.lock:
            if not self.instance.is_connected():
                self.instance.connect()

            try:
                # For SQLite, we need to ensure we're using the right database
                if self.instance.get_type() == "sqlite3":
                    # SQLite connection already points to a specific database file
                    self.instance.get_connection().execute(query, parameters)
                else:
                    # MySQL/PostgreSQL: use the specific database
                    db_prefix = (
                        f"USE `{self.db_name}`;"
                        if self.instance.get_type() == "mysql"
                        else f'SET search_path TO "{self.db_name}";'
                    )
                    full_query = f"{db_prefix} {query}"
                    self.instance.get_connection().execute(full_query, parameters)

                self.last_query = query
            except Exception as e:
                self.logger.critical(f"failed to execute query: {str(e)}")
                raise basefunctions.QueryError(f"failed to execute query: {str(e)}") from e

    def query_one(
        self, query: str, parameters: Union[tuple, dict] = ()
    ) -> Optional[Dict[str, Any]]:
        """
        Execute a SQL query and return a single row.

        parameters
        ----------
        query : str
            SQL query to execute
        parameters : Union[tuple, dict], optional
            query parameters, by default ()

        returns
        -------
        Optional[Dict[str, Any]]
            single row as dictionary or None if no rows found

        raises
        ------
        basefunctions.QueryError
            if query execution fails
        """
        with self.lock:
            if not self.instance.is_connected():
                self.instance.connect()

            try:
                # For SQLite, we need to ensure we're using the right database
                if self.instance.get_type() == "sqlite3":
                    # SQLite connection already points to a specific database file
                    result = self.instance.get_connection().fetch_one(query, parameters)
                else:
                    # MySQL/PostgreSQL: use the specific database
                    db_prefix = (
                        f"USE `{self.db_name}`;"
                        if self.instance.get_type() == "mysql"
                        else f'SET search_path TO "{self.db_name}";'
                    )
                    full_query = f"{db_prefix} {query}"
                    result = self.instance.get_connection().fetch_one(full_query, parameters)

                self.last_query = query
                return result
            except Exception as e:
                self.logger.critical(f"failed to execute query: {str(e)}")
                raise basefunctions.QueryError(f"failed to execute query: {str(e)}") from e

    def query_all(self, query: str, parameters: Union[tuple, dict] = ()) -> List[Dict[str, Any]]:
        """
        Execute a SQL query and return all rows.

        parameters
        ----------
        query : str
            SQL query to execute
        parameters : Union[tuple, dict], optional
            query parameters, by default ()

        returns
        -------
        List[Dict[str, Any]]
            list of rows as dictionaries

        raises
        ------
        basefunctions.QueryError
            if query execution fails
        """
        with self.lock:
            if not self.instance.is_connected():
                self.instance.connect()

            try:
                # For SQLite, we need to ensure we're using the right database
                if self.instance.get_type() == "sqlite3":
                    # SQLite connection already points to a specific database file
                    result = self.instance.get_connection().fetch_all(query, parameters)
                else:
                    # MySQL/PostgreSQL: use the specific database
                    db_prefix = (
                        f"USE `{self.db_name}`;"
                        if self.instance.get_type() == "mysql"
                        else f'SET search_path TO "{self.db_name}";'
                    )
                    full_query = f"{db_prefix} {query}"
                    result = self.instance.get_connection().fetch_all(full_query, parameters)

                self.last_query = query
                return result
            except Exception as e:
                self.logger.critical(f"failed to execute query: {str(e)}")
                raise basefunctions.QueryError(f"failed to execute query: {str(e)}") from e

    def transaction(self) -> "basefunctions.DbTransactionProxy":
        """
        Start a transaction context.

        returns
        -------
        basefunctions.DbTransactionProxy
            transaction context manager

        example
        -------
        with db.transaction():
            db.execute("INSERT INTO users (name) VALUES (?)", ("John",))
            db.execute("UPDATE stats SET user_count = user_count + 1")
        """
        if not self.instance.is_connected():
            self.instance.connect()

        # Get transaction manager from connector
        transaction = self.instance.get_connection().transaction()

        # Return this so the context manager uses the right database
        return basefunctions.DbTransactionProxy(self, transaction)

    def table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists in the database.

        parameters
        ----------
        table_name : str
            name of the table to check

        returns
        -------
        bool
            True if table exists, False otherwise
        """
        with self.lock:
            if not self.instance.is_connected():
                self.instance.connect()

            try:
                return self.instance.get_connection().check_if_table_exists(table_name)
            except Exception as e:
                self.logger.warning(f"error checking if table exists: {str(e)}")
                return False

    def list_tables(self) -> List[str]:
        """
        List all tables in the database.

        returns
        -------
        List[str]
            list of table names
        """
        with self.lock:
            if not self.instance.is_connected():
                self.instance.connect()

            try:
                query_map = {
                    "mysql": "SHOW TABLES",
                    "postgres": "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'",
                    "sqlite3": "SELECT name FROM sqlite_master WHERE type='table'",
                }

                db_type = self.instance.get_type()
                if db_type not in query_map:
                    self.logger.warning(
                        f"unsupported database type '{db_type}' for listing tables"
                    )
                    return []

                query = query_map[db_type]
                results = self.query_all(query)

                # Extract table names based on database type
                if db_type == "mysql":
                    key = f"Tables_in_{self.db_name}"
                    return [row.get(key) for row in results if row.get(key)]
                elif db_type == "postgres":
                    return [row.get("table_name") for row in results if row.get("table_name")]
                elif db_type == "sqlite3":
                    return [row.get("name") for row in results if row.get("name")]

                return []
            except Exception as e:
                self.logger.warning(f"error listing tables: {str(e)}")
                return []

    def add_dataframe(self, table_name: str, df: pd.DataFrame, cached: bool = False) -> None:
        """
        Add a DataFrame to a database table with optional caching.

        parameters
        ----------
        table_name : str
            name of the target table
        df : pd.DataFrame
            dataframe to write
        cached : bool, optional
            whether to cache the dataframe for batch writing, by default False
        """
        with self.lock:
            if cached:
                # Add to cache for later batch writing
                if table_name not in self.dataframe_cache:
                    self.dataframe_cache[table_name] = []

                self.dataframe_cache[table_name].append(df)

                # Auto-flush if cache is too large
                if len(self.dataframe_cache[table_name]) >= self.max_cache_size:
                    self.flush_dataframe_cache(table_name)
            else:
                # Write immediately
                try:
                    if not self.instance.is_connected():
                        self.instance.connect()

                    connection = self.instance.get_connection().get_connection()

                    # When using SQLAlchemy engine with to_sql, the 'search_path' or 'USE' is not needed
                    df.to_sql(table_name, connection, if_exists="append", index=False)
                except Exception as e:
                    self.logger.critical(
                        f"failed to write dataframe to table '{table_name}': {str(e)}"
                    )
                    raise

    def flush_dataframe_cache(self, table_name: Optional[str] = None) -> None:
        """
        Write all cached DataFrames for a table (or all tables) to the database.

        parameters
        ----------
        table_name : Optional[str], optional
            specific table to flush, or all tables if None, by default None
        """
        with self.lock:
            tables_to_flush = [table_name] if table_name else list(self.dataframe_cache.keys())

            for table in tables_to_flush:
                if table not in self.dataframe_cache or not self.dataframe_cache[table]:
                    continue

                try:
                    # Concatenate all dataframes for this table
                    frames = self.dataframe_cache[table]
                    combined_df = pd.concat(frames, ignore_index=True)

                    # Write to database
                    if not self.instance.is_connected():
                        self.instance.connect()

                    connection = self.instance.get_connection().get_connection()

                    # When using SQLAlchemy engine with to_sql, the 'search_path' or 'USE' is not needed
                    combined_df.to_sql(table, connection, if_exists="append", index=False)

                    # Clear cache after successful write
                    self.dataframe_cache[table] = []
                except Exception as e:
                    self.logger.critical(
                        f"failed to flush dataframe cache for table '{table}': {str(e)}"
                    )
                    raise

    def clear_dataframe_cache(self, table_name: Optional[str] = None) -> None:
        """
        Clear the DataFrame cache for a table (or all tables) without writing to the database.

        parameters
        ----------
        table_name : Optional[str], optional
            specific table to clear, or all tables if None, by default None
        """
        with self.lock:
            if table_name:
                if table_name in self.dataframe_cache:
                    self.dataframe_cache[table_name] = []
            else:
                self.dataframe_cache.clear()

    def get_dataframe_cache_stats(self) -> Dict[str, Dict[str, int]]:
        """
        Get statistics about the DataFrame cache.

        returns
        -------
        Dict[str, Dict[str, int]]
            Dictionary with table names as keys and cache statistics as values
        """
        with self.lock:
            stats = {}
            for table, frames in self.dataframe_cache.items():
                stats[table] = {"frames": len(frames), "total_rows": sum(len(df) for df in frames)}
            return stats

    def configure_dataframe_cache(self, max_cache_size: int) -> None:
        """
        Configure the DataFrame cache.

        parameters
        ----------
        max_cache_size : int
            maximum number of DataFrames per table before auto-flush
        """
        with self.lock:
            self.max_cache_size = max_cache_size

    def query_to_dataframe(self, query: str, parameters: Union[tuple, dict] = ()) -> pd.DataFrame:
        """
        Execute a SQL query and return the result as a DataFrame.

        parameters
        ----------
        query : str
            SQL query to execute
        parameters : Union[tuple, dict], optional
            query parameters, by default ()

        returns
        -------
        pd.DataFrame
            query result as DataFrame

        raises
        ------
        basefunctions.QueryError
            if query execution fails
        """
        with self.lock:
            try:
                # Get results as list of dictionaries
                results = self.query_all(query, parameters)

                # Convert to DataFrame
                return pd.DataFrame(results)
            except Exception as e:
                self.logger.critical(f"failed to execute query to DataFrame: {str(e)}")
                raise basefunctions.QueryError(
                    f"failed to execute query to DataFrame: {str(e)}"
                ) from e

    def submit_async_query(
        self, query: str, parameters: Union[tuple, dict] = (), callback: Optional[callable] = None
    ) -> str:
        """
        Submit a query for asynchronous execution.

        parameters
        ----------
        query : str
            SQL query to execute
        parameters : Union[tuple, dict], optional
            query parameters, by default ()
        callback : Optional[callable], optional
            function to call with results, by default None

        returns
        -------
        str
            task ID for the submitted query

        raises
        ------
        RuntimeError
            if ThreadPool is not configured
        """
        with self.lock:
            # Get ThreadPool from parent instance's manager
            threadpool = self.instance.get_manager().get_threadpool()

            if threadpool is None:
                self.logger.critical("ThreadPool not configured for async operations")
                raise RuntimeError("ThreadPool not configured for async operations")

            try:
                # Create task content
                task_content = {
                    "database": self.db_name,
                    "instance_name": self.instance.instance_name,
                    "query": query,
                    "parameters": parameters,
                    "callback": callback,
                }

                # Submit task to ThreadPool
                task_id = threadpool.submit_task("database_query", task_content)
                return task_id
            except Exception as e:
                self.logger.critical(f"failed to submit async query: {str(e)}")
                raise

    def close(self) -> None:
        """
        Close the database connection and flush any cached data.
        """
        with self.lock:
            # Flush any remaining cached DataFrames
            try:
                for table in list(self.dataframe_cache.keys()):
                    if self.dataframe_cache[table]:
                        self.flush_dataframe_cache(table)
            except Exception as e:
                self.logger.warning(f"error flushing dataframe cache: {str(e)}")

            # Clear caches
            self.dataframe_cache.clear()
            self.last_query = None
