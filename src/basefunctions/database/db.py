"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich
  Project : basefunctions
  Copyright (c) by neuraldevelopment
  All rights reserved.
  Description:
  Database abstraction layer with own connector per database instance
 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Dict, List, Optional, Any, Union
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
    Represents a specific database with its own connector.
    Provides direct access to database operations.
    Thread-safe implementation for concurrent access.
    """

    def __init__(self, instance: "basefunctions.DbInstance", db_name: str) -> None:
        """
        Initialize database object with own connector.

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

        # Create own connector for this database
        self.connector = instance.create_connector_for_database(db_name)

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
            try:
                if not self.connector.is_connected():
                    self.connector.connect()

                self.connector.execute(query, parameters)
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
            try:
                if not self.connector.is_connected():
                    self.connector.connect()

                return self.connector.fetch_one(query, parameters)
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
            try:
                if not self.connector.is_connected():
                    self.connector.connect()

                return self.connector.fetch_all(query, parameters)
            except Exception as e:
                self.logger.critical(f"failed to execute query: {str(e)}")
                raise basefunctions.QueryError(f"failed to execute query: {str(e)}") from e

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
                results = self.query_all(query, parameters)
                return pd.DataFrame(results)
            except Exception as e:
                self.logger.critical(f"failed to execute query to DataFrame: {str(e)}")
                raise basefunctions.QueryError(
                    f"failed to execute query to DataFrame: {str(e)}"
                ) from e

    def write_dataframe(
        self, table_name: str, df: pd.DataFrame, cached: bool = False, if_exists: str = "append"
    ) -> None:
        """
        Write a DataFrame to a database table.

        parameters
        ----------
        table_name : str
            name of the target table
        df : pd.DataFrame
            dataframe to write
        cached : bool, optional
            whether to cache the dataframe for batch writing, by default False
        if_exists : str, optional
            what to do if table exists ('fail', 'replace', 'append'), by default "append"
        """
        with self.lock:
            if cached:
                # Add to cache for later batch writing
                if table_name not in self.dataframe_cache:
                    self.dataframe_cache[table_name] = []

                self.dataframe_cache[table_name].append((df, if_exists))

                # Auto-flush if cache is too large
                if len(self.dataframe_cache[table_name]) >= self.max_cache_size:
                    self.flush_cache(table_name)
            else:
                # Write immediately using database-aware method
                self._write_dataframe_direct(table_name, df, if_exists)

    def flush_cache(self, table_name: Optional[str] = None) -> None:
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
                    # Process cached dataframes with their individual if_exists settings
                    frames_data = self.dataframe_cache[table]

                    # Group by if_exists setting
                    replace_frames = [
                        df for df, if_exists in frames_data if if_exists == "replace"
                    ]
                    append_frames = [df for df, if_exists in frames_data if if_exists == "append"]
                    fail_frames = [df for df, if_exists in frames_data if if_exists == "fail"]

                    # Handle replace operations (only use the last one)
                    if replace_frames:
                        last_replace_df = replace_frames[-1]
                        self._write_dataframe_direct(table, last_replace_df, "replace")

                    # Handle append operations (concatenate all)
                    if append_frames:
                        combined_append_df = pd.concat(append_frames, ignore_index=True)
                        self._write_dataframe_direct(table, combined_append_df, "append")

                    # Handle fail operations (write each individually)
                    for fail_df in fail_frames:
                        self._write_dataframe_direct(table, fail_df, "fail")

                    # Clear cache after successful write
                    self.dataframe_cache[table] = []
                except Exception as e:
                    self.logger.critical(
                        f"failed to flush dataframe cache for table '{table}': {str(e)}"
                    )
                    raise

    def transaction(self) -> "basefunctions.DbTransaction":
        """
        Start a transaction context.

        returns
        -------
        basefunctions.DbTransaction
            transaction context manager

        example
        -------
        with db.transaction():
            db.execute("INSERT INTO users (name) VALUES (?)", ("John",))
            db.execute("UPDATE stats SET user_count = user_count + 1")
        """
        if not self.connector.is_connected():
            self.connector.connect()

        return self.connector.transaction()

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
            try:
                if not self.connector.is_connected():
                    self.connector.connect()

                return self.connector.check_if_table_exists(table_name)
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
            try:
                if not self.connector.is_connected():
                    self.connector.connect()

                # Use connector-specific methods if available
                db_type = self.connector.db_type

                if db_type == "mysql" and hasattr(self.connector, "list_databases"):
                    # For MySQL, we might need to switch to the database first
                    self.connector.use_database(self.db_name)

                query_map = {
                    "mysql": "SHOW TABLES",
                    "postgresql": "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'",
                    "sqlite3": "SELECT name FROM sqlite_master WHERE type='table'",
                }

                if db_type not in query_map:
                    self.logger.warning(
                        f"unsupported database type '{db_type}' for listing tables"
                    )
                    return []

                query = query_map[db_type]
                results = self.connector.fetch_all(query)

                # Extract table names based on database type
                if db_type == "mysql":
                    key = f"Tables_in_{self.db_name}"
                    return [
                        row.get(key) or row.get("Tables_in_" + self.db_name.lower())
                        for row in results
                        if row.get(key) or row.get("Tables_in_" + self.db_name.lower())
                    ]
                elif db_type == "postgresql":
                    return [row.get("table_name") for row in results if row.get("table_name")]
                elif db_type == "sqlite3":
                    return [row.get("name") for row in results if row.get("name")]

                return []
            except Exception as e:
                self.logger.warning(f"error listing tables: {str(e)}")
                return []

    def close(self) -> None:
        """
        Close the database connection and flush any cached data.
        """
        with self.lock:
            # Flush any remaining cached DataFrames
            try:
                for table in list(self.dataframe_cache.keys()):
                    if self.dataframe_cache[table]:
                        self.flush_cache(table)
            except Exception as e:
                self.logger.warning(f"error flushing dataframe cache: {str(e)}")

            # Close connector
            try:
                if self.connector:
                    self.connector.close()
            except Exception as e:
                self.logger.warning(f"error closing connector: {str(e)}")

            # Clear caches
            self.dataframe_cache.clear()

    def get_connection_info(self) -> Dict[str, Any]:
        """
        Get current connection information.

        returns
        -------
        Dict[str, Any]
            connection details
        """
        if self.connector:
            return self.connector.get_connection_info()
        return {"connected": False, "db_name": self.db_name}

    def _write_dataframe_direct(
        self, table_name: str, df: pd.DataFrame, if_exists: str = "append"
    ) -> None:
        """
        Write DataFrame directly to database with proper database context.

        parameters
        ----------
        table_name : str
            name of the target table
        df : pd.DataFrame
            dataframe to write
        if_exists : str, optional
            what to do if table exists ('fail', 'replace', 'append'), by default "append"

        raises
        ------
        Exception
            if writing fails
        """
        try:
            if not self.connector.is_connected():
                self.connector.connect()

            db_type = self.connector.db_type
            connection = self.connector.get_connection()

            # Handle database context based on connector type
            if db_type == "mysql":
                # Ensure we're using the correct database
                if hasattr(self.connector, "use_database"):
                    self.connector.use_database(self.db_name)
                # Use qualified table name as fallback
                qualified_table = f"`{self.db_name}`.`{table_name}`"
                df.to_sql(qualified_table, connection, if_exists=if_exists, index=False)

            elif db_type == "postgresql":
                # PostgreSQL connector is already connected to specific database
                # Use schema if available
                if hasattr(self.connector, "current_schema") and self.connector.current_schema:
                    qualified_table = f"{self.connector.current_schema}.{table_name}"
                else:
                    qualified_table = table_name
                df.to_sql(qualified_table, connection, if_exists=if_exists, index=False)

            elif db_type == "sqlite3":
                # SQLite connector is already connected to specific database file
                df.to_sql(table_name, connection, if_exists=if_exists, index=False)

            else:
                # Fallback for unknown database types
                df.to_sql(table_name, connection, if_exists=if_exists, index=False)

        except Exception as e:
            self.logger.critical(f"failed to write dataframe to table '{table_name}': {str(e)}")
            raise
