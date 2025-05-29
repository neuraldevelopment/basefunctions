"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich
  Project : basefunctions
  Copyright (c) by neuraldevelopment
  All rights reserved.
  Description:
  Database abstraction layer with optional DataFrame parallelization support
 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Dict, List, Optional, Any, Union
import threading
import dataclasses
from contextlib import contextmanager
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


@dataclasses.dataclass
class DataFrameQueryData:
    """Structured data for DataFrame query events."""

    query: str
    parameters: Union[tuple, dict] = ()

    def __post_init__(self):
        """Validate query data after initialization."""
        if not self.query:
            raise basefunctions.DbValidationError("query cannot be empty")


@dataclasses.dataclass
class DataFrameWriteData:
    """Structured data for DataFrame write events."""

    table_name: str
    dataframe: pd.DataFrame
    if_exists: str = "append"
    cached: bool = False

    def __post_init__(self):
        """Validate write data after initialization."""
        if not self.table_name:
            raise basefunctions.DbValidationError("table_name cannot be empty")
        if self.dataframe is None:
            raise basefunctions.DbValidationError("dataframe cannot be None")
        if self.if_exists not in ["fail", "replace", "append"]:
            raise basefunctions.DbValidationError(f"invalid if_exists value: {self.if_exists}")


class DataFrameHandler:
    """
    Simple handler for DataFrame operations without EventBus dependency.
    Falls back to direct execution if EventBus is not available.
    """

    def __init__(self, db_instance: "Db"):
        """
        Initialize DataFrame handler.

        parameters
        ----------
        db_instance : Db
            Reference to parent Db instance for connector creation

        raises
        ------
        basefunctions.DbValidationError
            if db_instance is None
        """
        if not db_instance:
            raise basefunctions.DbValidationError("db_instance cannot be None")

        self.db_instance = db_instance
        self.logger = basefunctions.get_logger(__name__)

    @contextmanager
    def _get_dedicated_connector(self):
        """
        Context manager for safe connector resource management.
        Ensures connectors are always properly closed, even on exceptions.

        yields
        ------
        basefunctions.DbConnector
            configured and connected database connector

        raises
        ------
        basefunctions.DbConnectionError
            if connector creation or connection fails
        """
        connector = None
        try:
            # Create dedicated connector for this operation
            connector = self.db_instance.instance.create_connector_for_database(
                self.db_instance.db_name
            )

            # Ensure connection is established
            if not connector.is_connected():
                connector.connect()

            self.logger.debug(f"created dedicated connector for {self.db_instance.db_name}")
            yield connector

        except (
            basefunctions.DbConnectionError,
            basefunctions.DbConfigurationError,
            basefunctions.DbValidationError,
            basefunctions.DbFactoryError,
        ):
            # Re-raise specific database errors as-is
            raise
        except Exception as e:
            self.logger.critical(f"connector creation/connection error: {str(e)}")
            raise basefunctions.DbConnectionError(f"failed to create connector: {str(e)}") from e
        finally:
            # Guarantee connector cleanup regardless of success or failure
            if connector is not None:
                try:
                    connector.close()
                    self.logger.debug("dedicated connector closed successfully")
                except Exception as cleanup_error:
                    # Log cleanup errors but don't raise to avoid masking original exceptions
                    self.logger.warning(
                        f"error closing connector during cleanup: {str(cleanup_error)}"
                    )

    def handle_query(self, query_data: DataFrameQueryData) -> pd.DataFrame:
        """
        Handle DataFrame query operation with guaranteed resource cleanup.

        parameters
        ----------
        query_data : DataFrameQueryData
            Query data structure

        returns
        -------
        pd.DataFrame
            Query result as DataFrame

        raises
        ------
        basefunctions.DbQueryError
            if DataFrame operation fails
        basefunctions.DbConnectionError
            if connection fails
        """
        if not query_data:
            raise basefunctions.DbValidationError("query_data cannot be None")

        try:
            with self._get_dedicated_connector() as connector:
                connection = connector.get_connection()
                if not connection:
                    raise basefunctions.DbConnectionError("connector returned no connection")

                result = pd.read_sql(query_data.query, connection, params=query_data.parameters)
                self.logger.debug(
                    f"DataFrame query executed successfully, returned {len(result)} rows"
                )
                return result

        except (
            basefunctions.DbConnectionError,
            basefunctions.DbConfigurationError,
            basefunctions.DbValidationError,
            basefunctions.DbFactoryError,
        ):
            # Re-raise specific database errors as-is
            raise
        except Exception as e:
            self.logger.critical(f"DataFrame query error: {str(e)}")
            raise basefunctions.DbQueryError(f"DataFrame query failed: {str(e)}") from e

    def handle_write(self, write_data: DataFrameWriteData) -> str:
        """
        Handle DataFrame write operation with guaranteed resource cleanup.

        parameters
        ----------
        write_data : DataFrameWriteData
            Write data structure

        returns
        -------
        str
            Success message

        raises
        ------
        basefunctions.DbQueryError
            if DataFrame operation fails
        basefunctions.DbConnectionError
            if connection fails
        """
        if not write_data:
            raise basefunctions.DbValidationError("write_data cannot be None")

        try:
            with self._get_dedicated_connector() as connector:
                # Use the same database-aware writing logic as original
                self._write_dataframe_to_db(
                    write_data.table_name, write_data.dataframe, write_data.if_exists, connector
                )

                success_msg = f"DataFrame written to {write_data.table_name}"
                self.logger.debug(f"{success_msg} ({len(write_data.dataframe)} rows)")
                return success_msg

        except (
            basefunctions.DbConnectionError,
            basefunctions.DbConfigurationError,
            basefunctions.DbValidationError,
            basefunctions.DbFactoryError,
        ):
            # Re-raise specific database errors as-is
            raise
        except Exception as e:
            self.logger.critical(f"DataFrame write error: {str(e)}")
            raise basefunctions.DbQueryError(f"DataFrame write failed: {str(e)}") from e

    def _write_dataframe_to_db(
        self,
        table_name: str,
        df: pd.DataFrame,
        if_exists: str,
        connector: "basefunctions.DbConnector",
    ) -> None:
        """
        Write DataFrame to database with proper database context.

        parameters
        ----------
        table_name : str
            Target table name
        df : pd.DataFrame
            DataFrame to write
        if_exists : str
            Action if table exists
        connector : basefunctions.DbConnector
            Database connector

        raises
        ------
        basefunctions.DbQueryError
            if write operation fails
        """
        if not connector:
            raise basefunctions.DbValidationError("connector cannot be None")

        try:
            db_type = connector.db_type
            connection = connector.get_connection()
            if not connection:
                raise basefunctions.DbConnectionError("connector returned no connection")

            # Handle database context based on connector type
            if db_type == "mysql":
                # Ensure we're using the correct database
                if hasattr(connector, "use_database"):
                    connector.use_database(self.db_instance.db_name)
                # Use qualified table name as fallback
                qualified_table = f"`{self.db_instance.db_name}`.`{table_name}`"
                df.to_sql(qualified_table, connection, if_exists=if_exists, index=False)

            elif db_type == "postgresql":
                # PostgreSQL connector is already connected to specific database
                # Use schema if available
                if hasattr(connector, "current_schema") and connector.current_schema:
                    qualified_table = f"{connector.current_schema}.{table_name}"
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
            self.logger.critical(f"failed to write DataFrame to database: {str(e)}")
            raise basefunctions.DbQueryError(
                f"DataFrame write to database failed: {str(e)}"
            ) from e


class Db:
    """
    Represents a specific database with simplified execution model.
    All operations are synchronous without EventBus dependency.
    Thread-safe implementation for concurrent access.
    """

    def __init__(self, instance: "basefunctions.DbInstance", db_name: str) -> None:
        """
        Initialize database object with simplified execution model.

        parameters
        ----------
        instance : basefunctions.DbInstance
            parent database instance
        db_name : str
            name of the database

        raises
        ------
        basefunctions.DbValidationError
            if parameters are invalid
        basefunctions.DbConnectionError
            if connector creation fails
        """
        if not instance:
            raise basefunctions.DbValidationError("instance cannot be None")
        if not db_name:
            raise basefunctions.DbValidationError("db_name cannot be empty")

        self.instance = instance
        self.db_name = db_name
        self.logger = basefunctions.get_logger(__name__)
        self.lock = threading.RLock()
        self.dataframe_cache: Dict[str, List[tuple[pd.DataFrame, str]]] = {}
        self.max_cache_size = 10

        # Create synchronous connector for SQL operations
        try:
            self.connector = instance.create_connector_for_database(db_name)
        except Exception as e:
            self.logger.critical(f"failed to create connector for database '{db_name}': {str(e)}")
            raise

        # Setup DataFrame handler (without EventBus dependency)
        self._dataframe_handler = DataFrameHandler(self)

        # Try to initialize EventBus if available
        self._event_bus = None
        self._eventbus_available = False
        try:
            # Optional EventBus initialization for enhanced performance
            if hasattr(basefunctions, "EventBus"):
                self._event_bus = basefunctions.EventBus(num_threads=4)
                self._eventbus_available = True

                # Register DataFrame handlers if EventBus is available
                if hasattr(basefunctions, "Event"):
                    self._event_bus.register(
                        "dataframe.query", self._create_eventbus_handler("query")
                    )
                    self._event_bus.register(
                        "dataframe.write", self._create_eventbus_handler("write")
                    )

                self.logger.info(f"EventBus initialized for database '{db_name}' (enhanced mode)")
            else:
                self.logger.info(
                    f"EventBus not available for database '{db_name}' (fallback mode)"
                )
        except Exception as e:
            self.logger.warning(f"EventBus initialization failed, using fallback mode: {str(e)}")
            self._event_bus = None
            self._eventbus_available = False

    def _create_eventbus_handler(self, operation_type: str):
        """Create EventBus-compatible handler wrapper."""

        def handler(event, context=None):
            try:
                if operation_type == "query":
                    return self._dataframe_handler.handle_query(event.data)
                elif operation_type == "write":
                    return self._dataframe_handler.handle_write(event.data)
                else:
                    raise basefunctions.DbValidationError(
                        f"unknown operation type: {operation_type}"
                    )
            except Exception as e:
                self.logger.critical(f"EventBus handler error for {operation_type}: {str(e)}")
                raise

        return handler

    # =================================================================
    # SYNCHRONOUS SQL METHODS
    # =================================================================

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
        basefunctions.DbQueryError
            if query execution fails
        basefunctions.DbValidationError
            if query is invalid
        """
        if not query:
            raise basefunctions.DbValidationError("query cannot be empty")

        with self.lock:
            try:
                if not self.connector.is_connected():
                    self.connector.connect()

                self.connector.execute(query, parameters)
            except (
                basefunctions.DbQueryError,
                basefunctions.DbConnectionError,
                basefunctions.DbValidationError,
            ):
                # Re-raise specific database errors as-is
                raise
            except Exception as e:
                self.logger.critical(f"failed to execute query: {str(e)}")
                raise basefunctions.DbQueryError(f"failed to execute query: {str(e)}") from e

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
        basefunctions.DbQueryError
            if query execution fails
        basefunctions.DbValidationError
            if query is invalid
        """
        if not query:
            raise basefunctions.DbValidationError("query cannot be empty")

        with self.lock:
            try:
                if not self.connector.is_connected():
                    self.connector.connect()

                return self.connector.fetch_one(query, parameters)
            except (
                basefunctions.DbQueryError,
                basefunctions.DbConnectionError,
                basefunctions.DbValidationError,
            ):
                # Re-raise specific database errors as-is
                raise
            except Exception as e:
                self.logger.critical(f"failed to execute query: {str(e)}")
                raise basefunctions.DbQueryError(f"failed to execute query: {str(e)}") from e

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
        basefunctions.DbQueryError
            if query execution fails
        basefunctions.DbValidationError
            if query is invalid
        """
        if not query:
            raise basefunctions.DbValidationError("query cannot be empty")

        with self.lock:
            try:
                if not self.connector.is_connected():
                    self.connector.connect()

                return self.connector.fetch_all(query, parameters)
            except (
                basefunctions.DbQueryError,
                basefunctions.DbConnectionError,
                basefunctions.DbValidationError,
            ):
                # Re-raise specific database errors as-is
                raise
            except Exception as e:
                self.logger.critical(f"failed to execute query: {str(e)}")
                raise basefunctions.DbQueryError(f"failed to execute query: {str(e)}") from e

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
        if not table_name:
            return False

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

                if db_type == "mysql" and hasattr(self.connector, "use_database"):
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

    def transaction(self) -> "basefunctions.DbTransaction":
        """
        Start a transaction context.

        returns
        -------
        basefunctions.DbTransaction
            transaction context manager

        raises
        ------
        basefunctions.DbConnectionError
            if connection fails

        example
        -------
        with db.transaction():
            db.execute("INSERT INTO users (name) VALUES (?)", ("John",))
            db.execute("UPDATE stats SET user_count = user_count + 1")
        """
        try:
            if not self.connector.is_connected():
                self.connector.connect()

            return basefunctions.DbTransaction(self.connector)
        except Exception as e:
            self.logger.critical(f"failed to create transaction: {str(e)}")
            raise basefunctions.DbConnectionError(f"failed to create transaction: {str(e)}") from e

    # =================================================================
    # DATAFRAME METHODS (with fallback support)
    # =================================================================

    def query_to_dataframe(self, query: str, parameters: Union[tuple, dict] = ()) -> pd.DataFrame:
        """
        Execute a SQL query and return the result as a DataFrame.
        Uses EventBus if available, otherwise falls back to direct execution.

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
        basefunctions.DbQueryError
            if query execution fails
        basefunctions.DbValidationError
            if query is invalid
        """
        if not query:
            raise basefunctions.DbValidationError("query cannot be empty")

        try:
            # Create structured event data
            query_data = DataFrameQueryData(query=query, parameters=parameters)

            if self._eventbus_available and self._event_bus:
                # Use EventBus for enhanced performance
                event = basefunctions.Event(
                    type="dataframe.query", data=query_data, target=self.db_name
                )
                self._event_bus.publish(event)
                self._event_bus.join()

                # Get results
                results, errors = self._event_bus.get_results()
                if errors:
                    raise basefunctions.DbQueryError(f"DataFrame query failed: {errors[0]}")
                if not results:
                    raise basefunctions.DbQueryError("No results returned from DataFrame query")
                return results[0]
            else:
                # Fallback to direct execution
                return self._dataframe_handler.handle_query(query_data)

        except (
            basefunctions.DbQueryError,
            basefunctions.DbConnectionError,
            basefunctions.DbValidationError,
        ):
            # Re-raise specific database errors as-is
            raise
        except Exception as e:
            self.logger.critical(f"failed to execute query to DataFrame: {str(e)}")
            raise basefunctions.DbQueryError(
                f"failed to execute query to DataFrame: {str(e)}"
            ) from e

    def write_dataframe(
        self, table_name: str, df: pd.DataFrame, cached: bool = False, if_exists: str = "append"
    ) -> None:
        """
        Write a DataFrame to a database table.
        Uses EventBus if available, otherwise falls back to direct execution.

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

        raises
        ------
        basefunctions.DbQueryError
            if write operation fails
        basefunctions.DbValidationError
            if parameters are invalid
        """
        if not table_name:
            raise basefunctions.DbValidationError("table_name cannot be empty")
        if df is None:
            raise basefunctions.DbValidationError("df cannot be None")

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
                # Write immediately
                write_data = DataFrameWriteData(
                    table_name=table_name, dataframe=df, if_exists=if_exists, cached=False
                )

                if self._eventbus_available and self._event_bus:
                    # Use EventBus for enhanced performance
                    event = basefunctions.Event(
                        type="dataframe.write", data=write_data, target=self.db_name
                    )
                    self._event_bus.publish(event)
                    self._event_bus.join()

                    # Check for errors
                    results, errors = self._event_bus.get_results()
                    if errors:
                        raise basefunctions.DbQueryError(f"DataFrame write failed: {errors[0]}")
                else:
                    # Fallback to direct execution
                    self._dataframe_handler.handle_write(write_data)

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
                        write_data = DataFrameWriteData(table, last_replace_df, "replace", False)
                        if self._eventbus_available and self._event_bus:
                            event = basefunctions.Event(
                                "dataframe.write", data=write_data, target=self.db_name
                            )
                            self._event_bus.publish(event)
                        else:
                            self._dataframe_handler.handle_write(write_data)

                    # Handle append operations (concatenate all)
                    if append_frames:
                        combined_append_df = pd.concat(append_frames, ignore_index=True)
                        write_data = DataFrameWriteData(table, combined_append_df, "append", False)
                        if self._eventbus_available and self._event_bus:
                            event = basefunctions.Event(
                                "dataframe.write", data=write_data, target=self.db_name
                            )
                            self._event_bus.publish(event)
                        else:
                            self._dataframe_handler.handle_write(write_data)

                    # Handle fail operations (write each individually)
                    for fail_df in fail_frames:
                        write_data = DataFrameWriteData(table, fail_df, "fail", False)
                        if self._eventbus_available and self._event_bus:
                            event = basefunctions.Event(
                                "dataframe.write", data=write_data, target=self.db_name
                            )
                            self._event_bus.publish(event)
                        else:
                            self._dataframe_handler.handle_write(write_data)

                    # Wait for all operations to complete if using EventBus
                    if self._eventbus_available and self._event_bus:
                        self._event_bus.join()
                        results, errors = self._event_bus.get_results()
                        if errors:
                            raise basefunctions.DbQueryError(f"Flush operations failed: {errors}")

                    # Clear cache after successful write
                    self.dataframe_cache[table] = []

                except Exception as e:
                    self.logger.critical(
                        f"failed to flush dataframe cache for table '{table}': {str(e)}"
                    )
                    raise

    # =================================================================
    # UTILITY METHODS
    # =================================================================

    def close(self) -> None:
        """
        Close the database connection and shutdown EventBus if available.
        """
        with self.lock:
            # Flush any remaining cached DataFrames
            try:
                for table in list(self.dataframe_cache.keys()):
                    if self.dataframe_cache[table]:
                        self.flush_cache(table)
            except Exception as e:
                self.logger.warning(f"error flushing dataframe cache: {str(e)}")

            # Shutdown EventBus if available
            try:
                if self._event_bus:
                    self._event_bus.shutdown()
            except Exception as e:
                self.logger.warning(f"error shutting down EventBus: {str(e)}")

            # Close main connector
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
        info = {"connected": False, "db_name": self.db_name}

        if self.connector:
            try:
                info.update(self.connector.get_connection_info())
            except Exception as e:
                self.logger.warning(f"error getting connection info: {str(e)}")
                info["error"] = str(e)

        # Add EventBus stats if available
        if self._event_bus:
            try:
                info["eventbus_stats"] = self._event_bus.get_stats()
                info["eventbus_available"] = True
            except Exception:
                info["eventbus_available"] = False
        else:
            info["eventbus_available"] = False

        return info

    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get information about DataFrame cache status.

        returns
        -------
        Dict[str, Any]
            cache information
        """
        with self.lock:
            cache_info = {
                "max_cache_size": self.max_cache_size,
                "total_cached_tables": len(self.dataframe_cache),
                "tables": {},
            }

            for table_name, frames in self.dataframe_cache.items():
                cache_info["tables"][table_name] = {
                    "cached_frames": len(frames),
                    "total_rows": sum(len(df) for df, _ in frames),
                }

            return cache_info

    def clear_cache(self, table_name: Optional[str] = None) -> None:
        """
        Clear DataFrame cache without writing to database.

        parameters
        ----------
        table_name : Optional[str], optional
            specific table to clear, or all tables if None, by default None
        """
        with self.lock:
            if table_name:
                if table_name in self.dataframe_cache:
                    del self.dataframe_cache[table_name]
                    self.logger.info(f"cleared DataFrame cache for table '{table_name}'")
            else:
                self.dataframe_cache.clear()
                self.logger.info("cleared all DataFrame caches")

    def __str__(self) -> str:
        """
        String representation for debugging.

        returns
        -------
        str
            database status string
        """
        try:
            connected = (
                "connected"
                if (self.connector and self.connector.is_connected())
                else "disconnected"
            )
            db_type = getattr(self.connector, "db_type", "unknown") if self.connector else "none"
            cached_tables = len(self.dataframe_cache)
            eventbus = "enabled" if self._eventbus_available else "disabled"

            return f"Db[{self.db_name}, {db_type}, {connected}, cache:{cached_tables}, eventbus:{eventbus}]"
        except Exception as e:
            return f"Db[{self.db_name}, error: {str(e)}]"

    def __repr__(self) -> str:
        """
        Detailed representation for debugging.

        returns
        -------
        str
            detailed database information
        """
        try:
            return (
                f"Db("
                f"db_name='{self.db_name}', "
                f"instance='{self.instance.instance_name}', "
                f"connector={type(self.connector).__name__ if self.connector else None}, "
                f"cached_tables={len(self.dataframe_cache)}, "
                f"eventbus_available={self._eventbus_available}"
                f")"
            )
        except Exception as e:
            return f"Db(db_name='{self.db_name}', error='{str(e)}')"
