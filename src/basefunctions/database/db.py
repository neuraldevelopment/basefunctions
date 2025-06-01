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
from typing import Dict, List, Optional, Any, Union, Tuple
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
class DataFrameReadData:
    """Structured data for DataFrame read events."""

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


class DataFrameHandler(basefunctions.EventHandler):
    """
    EventHandler for DataFrame operations with thread-local connection pooling.
    Maintains persistent database connections per worker thread for optimal performance.
    """

    execution_mode = "thread"  # thread execution

    def __init__(self, *args, **kwargs):
        """
        Initialize DataFrame handler without database dependency.

        Parameters
        ----------
        *args
            Unused positional arguments for EventFactory compatibility
        **kwargs
            Unused keyword arguments for EventFactory compatibility

        Notes
        -----
        Handler now works with multiple databases via event.target routing.
        Database connectors are created lazily per thread via context.
        """
        self.logger = basefunctions.get_logger(__name__)

    def handle(
        self, event: basefunctions.Event, context: Optional[basefunctions.EventContext] = None
    ) -> Tuple[bool, Any]:
        """
        Handle DataFrame events with target-based database routing.

        Parameters
        ----------
        event : basefunctions.Event
            DataFrame operation event
        context : basefunctions.EventContext, optional
            Event context with thread_local_data

        Returns
        -------
        Tuple[bool, Any]
            Success flag and result data

        Raises
        ------
        basefunctions.DbQueryError
            If DataFrame operation fails
        """
        try:
            # Validate event target for database routing
            if not event.target:
                return (False, "Event target (database name) is required for DataFrame operations")

            # Get connector for target database using thread-local context
            if context and hasattr(context, "thread_local_data") and context.thread_local_data:
                connector = self._get_connector_for_target(event.target, context.thread_local_data)
            else:
                return (False, "Thread-local context required for DataFrame operations")

            # Route to appropriate handler
            if event.type == "dataframe.read":
                result = self._handle_read(connector, event.data)
                return (True, result)
            elif event.type == "dataframe.write":
                result = self._handle_write(connector, event.data)
                return (True, result)
            else:
                return (False, f"Unknown DataFrame event type: {event.type}")

        except (
            basefunctions.DbConnectionError,
            basefunctions.DbConfigurationError,
            basefunctions.DbValidationError,
            basefunctions.DbFactoryError,
        ) as e:
            self.logger.error(f"DataFrame handler database error: {str(e)}")
            return (False, str(e))
        except Exception as e:
            self.logger.critical(f"DataFrame handler error: {str(e)}")
            return (False, f"DataFrame operation failed: {str(e)}")

    def _get_connector_for_target(self, target: str, thread_local_data) -> "basefunctions.DbConnector":
        """
        Get or create connector for target database using thread-local storage.

        Parameters
        ----------
        target : str
            Target database identifier (instance name)
        thread_local_data : threading.local
            EventBus thread-local data storage

        Returns
        -------
        basefunctions.DbConnector
            Thread-specific database connector for target

        Raises
        ------
        basefunctions.DbConnectionError
            If connector creation or connection fails
        basefunctions.DbValidationError
            If target format is invalid
        basefunctions.DbConfigurationError
            If configuration cannot be found
        """
        if not target:
            raise basefunctions.DbValidationError("target cannot be empty")

        # Initialize databases dict in thread-local storage if needed
        if not hasattr(thread_local_data, "databases"):
            thread_local_data.databases = {}

        # Check if connector already exists for this target
        if target in thread_local_data.databases:
            connector = thread_local_data.databases[target]
            # Ensure connection is active
            if not connector.is_connected():
                connector.connect()
            return connector

        # Create new connector for target using DbFactory
        try:
            # Load config from ConfigHandler and determine db_type
            config_handler = basefunctions.ConfigHandler()
            config = config_handler.get_database_config(target)

            if not config:
                raise basefunctions.DbConfigurationError(f"no configuration found for database instance '{target}'")

            db_type = config.get("type")
            if not db_type:
                raise basefunctions.DbConfigurationError(
                    f"database type not specified in configuration for '{target}'"
                )

            # Create connector via factory (config auto-loaded from ConfigHandler)
            connector = basefunctions.DbFactory.create_connector_for_database(
                db_type=db_type, db_name=target, config=config
            )

            # Connect immediately
            connector.connect()

            # Cache connector in thread-local storage
            thread_local_data.databases[target] = connector

            self.logger.debug(f"Created thread-local connector for target '{target}' (type: {db_type})")
            return connector

        except (
            basefunctions.DbConfigurationError,
            basefunctions.DbValidationError,
            basefunctions.DbFactoryError,
        ):
            # Re-raise specific database errors as-is
            raise
        except Exception as e:
            self.logger.error(f"Failed to create connector for target '{target}': {str(e)}")
            raise basefunctions.DbConnectionError(f"Failed to create connector for target '{target}': {str(e)}") from e

    def _handle_read(self, connector: "basefunctions.DbConnector", read_data: DataFrameReadData) -> pd.DataFrame:
        """
        Handle DataFrame read with persistent connection.

        Parameters
        ----------
        connector : basefunctions.DbConnector
            Thread-local database connector
        read_data : DataFrameReadData
            Read data structure

        Returns
        -------
        pd.DataFrame
            Read result as DataFrame

        Raises
        ------
        basefunctions.DbValidationError
            If read_data is invalid
        basefunctions.DbConnectionError
            If connector has no connection
        basefunctions.DbQueryError
            If SQL execution fails
        """
        if not read_data:
            raise basefunctions.DbValidationError("read_data cannot be None")

        connection = connector.get_connection()

        if not connection:
            raise basefunctions.DbConnectionError("connector returned no connection")

        try:
            result = pd.read_sql(read_data.query, connection, params=read_data.parameters)
            self.logger.debug(f"DataFrame query executed successfully, returned {len(result)} rows")
            return result
        except Exception as e:
            self.logger.error(f"DataFrame read failed: {str(e)}")
            raise basefunctions.DbQueryError(f"DataFrame read failed: {str(e)}") from e

    def _handle_write(self, connector: "basefunctions.DbConnector", write_data: DataFrameWriteData) -> str:
        """
        Handle DataFrame write with persistent connection.

        Parameters
        ----------
        connector : basefunctions.DbConnector
            Thread-local database connector
        write_data : DataFrameWriteData
            Write data structure

        Returns
        -------
        str
            Success message

        Raises
        ------
        basefunctions.DbValidationError
            If write_data is invalid
        basefunctions.DbQueryError
            If write operation fails
        """
        if not write_data:
            raise basefunctions.DbValidationError("write_data cannot be None")

        # Use the database-aware writing logic
        self._write_dataframe_to_db(connector, write_data.table_name, write_data.dataframe, write_data.if_exists)

        success_msg = f"DataFrame written to {write_data.table_name}"
        self.logger.debug(f"{success_msg} ({len(write_data.dataframe)} rows)")

        return success_msg

    def _write_dataframe_to_db(
        self,
        connector: "basefunctions.DbConnector",
        table_name: str,
        df: pd.DataFrame,
        if_exists: str,
    ) -> None:
        """
        Write DataFrame to database with proper database context.

        Parameters
        ----------
        connector : basefunctions.DbConnector
            Database connector
        table_name : str
            Target table name
        df : pd.DataFrame
            DataFrame to write
        if_exists : str
            Action if table exists

        Raises
        ------
        basefunctions.DbValidationError
            If connector is None
        basefunctions.DbQueryError
            If write operation fails
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
                # MySQL connector is already connected to specific database
                df.to_sql(table_name, connection, if_exists=if_exists, index=False)

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
            raise basefunctions.DbQueryError(f"DataFrame write to database failed: {str(e)}") from e


class Db:
    """
    Represents a specific database with EventBus-optimized execution model.
    DataFrame operations utilize thread-local connection pooling for enhanced performance.
    Thread-safe implementation for concurrent access.
    """

    def __init__(self, db_name: str) -> None:
        """
        Initialize database object with EventBus-optimized execution model.

        Parameters
        ----------
        db_name : str
            Name of the database instance (used for ConfigHandler lookup)

        Raises
        ------
        basefunctions.DbValidationError
            If parameters are invalid
        basefunctions.DbConnectionError
            If connector creation fails
        basefunctions.DbConfigurationError
            If configuration cannot be found
        """
        if not db_name:
            raise basefunctions.DbValidationError("db_name cannot be empty")

        self.db_name = db_name
        self.logger = basefunctions.get_logger(__name__)
        self.lock = threading.RLock()

        # Create synchronous connector for SQL operations via DbFactory
        try:
            # Load config and determine db_type
            config_handler = basefunctions.ConfigHandler()
            config = config_handler.get_database_config(db_name)

            if not config:
                raise basefunctions.DbConfigurationError(f"no configuration found for database instance '{db_name}'")

            db_type = config.get("type")
            if not db_type:
                raise basefunctions.DbConfigurationError(
                    f"database type not specified in configuration for '{db_name}'"
                )

            # Create connector via factory
            self.connector = basefunctions.DbFactory.create_connector_for_database(
                db_type=db_type, db_name=db_name, config=config
            )

            self.logger.info(f"created Db instance for '{db_name}' (type: {db_type})")

        except (
            basefunctions.DbConfigurationError,
            basefunctions.DbValidationError,
            basefunctions.DbFactoryError,
        ):
            # Re-raise specific database errors as-is
            raise
        except Exception as e:
            self.logger.critical(f"failed to create connector for database '{db_name}': {str(e)}")
            raise basefunctions.DbConnectionError(
                f"failed to create connector for database '{db_name}': {str(e)}"
            ) from e

        # Register DataFrame handler classes in EventFactory
        basefunctions.EventFactory.register_event_type("dataframe.read", DataFrameHandler)
        basefunctions.EventFactory.register_event_type("dataframe.write", DataFrameHandler)

        self.logger.debug("DataFrame handlers registered in EventFactory")

        # Initialize EventBus for enhanced DataFrame performance
        self._event_bus = basefunctions.EventBus()

    # =================================================================
    # SYNCHRONOUS SQL METHODS
    # =================================================================

    def execute(self, query: str, parameters: Union[tuple, dict] = ()) -> None:
        """
        Execute a SQL query without returning a result.

        Parameters
        ----------
        query : str
            SQL query to execute
        parameters : Union[tuple, dict], optional
            Query parameters, by default ()

        Raises
        ------
        basefunctions.DbQueryError
            If query execution fails
        basefunctions.DbValidationError
            If query is invalid
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

    def query_one(self, query: str, parameters: Union[tuple, dict] = ()) -> Optional[Dict[str, Any]]:
        """
        Execute a SQL query and return a single row.

        Parameters
        ----------
        query : str
            SQL query to execute
        parameters : Union[tuple, dict], optional
            Query parameters, by default ()

        Returns
        -------
        Optional[Dict[str, Any]]
            Single row as dictionary or None if no rows found

        Raises
        ------
        basefunctions.DbQueryError
            If query execution fails
        basefunctions.DbValidationError
            If query is invalid
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

        Parameters
        ----------
        query : str
            SQL query to execute
        parameters : Union[tuple, dict], optional
            Query parameters, by default ()

        Returns
        -------
        List[Dict[str, Any]]
            List of rows as dictionaries

        Raises
        ------
        basefunctions.DbQueryError
            If query execution fails
        basefunctions.DbValidationError
            If query is invalid
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

        Parameters
        ----------
        table_name : str
            Name of the table to check

        Returns
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

        Returns
        -------
        List[str]
            List of table names
        """
        with self.lock:
            try:
                if not self.connector.is_connected():
                    self.connector.connect()

                # Use connector-specific methods
                db_type = self.connector.db_type

                query_map = {
                    "mysql": "SHOW TABLES",
                    "postgresql": "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'",
                    "sqlite3": "SELECT name FROM sqlite_master WHERE type='table'",
                }

                if db_type not in query_map:
                    self.logger.warning(f"unsupported database type '{db_type}' for listing tables")
                    return []

                query = query_map[db_type]
                results = self.connector.fetch_all(query)

                # Extract table names based on database type
                if db_type == "mysql":
                    # MySQL SHOW TABLES returns single column with database-specific name
                    # Try different possible column names
                    if results:
                        first_row = results[0]
                        # Get the first (and only) column value regardless of column name
                        table_name = list(first_row.values())[0] if first_row else None
                        if table_name:
                            return [row[list(row.keys())[0]] for row in results]
                    return []

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

        Returns
        -------
        basefunctions.DbTransaction
            Transaction context manager

        Raises
        ------
        basefunctions.DbConnectionError
            If connection fails

        Example
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
    # DATAFRAME METHODS (EventBus-optimized with thread-local pooling)
    # =================================================================

    def submit_dataframe_read(self, query: str, parameters: Union[tuple, dict] = ()) -> None:
        """
        Submit DataFrame read for async execution.

        Parameters
        ----------
        query : str
            SQL query to execute
        parameters : Union[tuple, dict], optional
            Query parameters, by default ()

        Raises
        ------
        basefunctions.DbValidationError
            If query is invalid
        basefunctions.DbQueryError
            If submission fails
        """
        if not query:
            raise basefunctions.DbValidationError("query cannot be empty")

        try:
            # Create structured event data
            read_data = DataFrameReadData(query=query, parameters=parameters)

            # Create event for async execution
            event = basefunctions.Event(type="dataframe.read", data=read_data, target=self.db_name)

            # Submit to EventBus (non-blocking)
            self._event_bus.publish(event)

        except Exception as e:
            self.logger.critical(f"failed to submit DataFrame read: {str(e)}")
            raise basefunctions.DbQueryError(f"failed to submit DataFrame read: {str(e)}") from e

    def submit_dataframe_read_batch(self, queries: List[Tuple[str, Union[tuple, dict]]]) -> None:
        """
        Submit multiple DataFrame reads efficiently for async execution.

        Parameters
        ----------
        queries : List[Tuple[str, Union[tuple, dict]]]
            List of (query, parameters) tuples to execute

        Raises
        ------
        basefunctions.DbValidationError
            If queries list is invalid or contains invalid queries
        basefunctions.DbQueryError
            If batch submission fails
        """
        if not queries:
            raise basefunctions.DbValidationError("queries list cannot be empty")

        try:
            for query, parameters in queries:
                if not query:
                    raise basefunctions.DbValidationError("query in batch cannot be empty")

                # Create structured event data
                read_data = DataFrameReadData(query=query, parameters=parameters)

                # Create event for async execution
                event = basefunctions.Event(type="dataframe.read", data=read_data, target=self.db_name)

                # Submit to EventBus (non-blocking)
                self._event_bus.publish(event)

        except basefunctions.DbValidationError:
            # Re-raise validation errors as-is
            raise
        except Exception as e:
            self.logger.critical(f"failed to submit DataFrame read batch: {str(e)}")
            raise basefunctions.DbQueryError(f"failed to submit DataFrame read batch: {str(e)}") from e

    def get_dataframe_read_results(self) -> List[pd.DataFrame]:
        """
        Get all results from submitted DataFrame reads.

        Returns
        -------
        List[pd.DataFrame]
            List of DataFrames in submission order

        Raises
        ------
        basefunctions.DbQueryError
            If any DataFrame read failed or no results available
        """
        try:
            # Wait for all pending operations to complete
            self._event_bus.join()

            # Get all results from EventBus
            results, errors = self._event_bus.get_results()

            # Handle errors first
            if errors:
                error_msg = f"DataFrame reads failed: {errors[0]}"
                self.logger.error(error_msg)
                raise basefunctions.DbQueryError(error_msg)

            # Extract DataFrames from results
            dataframes = []
            for result in results:
                if isinstance(result, pd.DataFrame):
                    dataframes.append(result)
                else:
                    self.logger.warning(f"unexpected result type: {type(result).__name__}")

            if not dataframes:
                raise basefunctions.DbQueryError("no DataFrame results available")

            return dataframes

        except basefunctions.DbQueryError:
            # Re-raise database errors as-is
            raise
        except Exception as e:
            self.logger.critical(f"failed to get DataFrame read results: {str(e)}")
            raise basefunctions.DbQueryError(f"failed to get DataFrame read results: {str(e)}") from e

    def submit_dataframe_write(self, table_name: str, df: pd.DataFrame, if_exists: str = "append") -> None:
        """
        Submit DataFrame write for async execution.

        Parameters
        ----------
        table_name : str
            Name of the target table
        df : pd.DataFrame
            DataFrame to write
        if_exists : str, optional
            What to do if table exists ('fail', 'replace', 'append'), by default "append"

        Raises
        ------
        basefunctions.DbValidationError
            If parameters are invalid
        basefunctions.DbQueryError
            If submission fails
        """
        if not table_name:
            raise basefunctions.DbValidationError("table_name cannot be empty")
        if df is None:
            raise basefunctions.DbValidationError("df cannot be None")
        if if_exists not in ["fail", "replace", "append"]:
            raise basefunctions.DbValidationError(f"invalid if_exists value: {if_exists}")

        try:
            # Create structured event data
            write_data = DataFrameWriteData(table_name=table_name, dataframe=df, if_exists=if_exists, cached=False)

            # Create event for async execution
            event = basefunctions.Event(type="dataframe.write", data=write_data, target=self.db_name)

            # Submit to EventBus (non-blocking)
            self._event_bus.publish(event)

        except basefunctions.DbValidationError:
            # Re-raise validation errors as-is
            raise
        except Exception as e:
            self.logger.critical(f"failed to submit DataFrame write: {str(e)}")
            raise basefunctions.DbQueryError(f"failed to submit DataFrame write: {str(e)}") from e

    def submit_dataframe_write_batch(self, writes: List[Tuple[str, pd.DataFrame, str]]) -> None:
        """
        Submit multiple DataFrame writes efficiently for async execution.

        Parameters
        ----------
        writes : List[Tuple[str, pd.DataFrame, str]]
            List of (table_name, dataframe, if_exists) tuples to write

        Raises
        ------
        basefunctions.DbValidationError
            If writes list is invalid or contains invalid write data
        basefunctions.DbQueryError
            If batch submission fails
        """
        if not writes:
            raise basefunctions.DbValidationError("writes list cannot be empty")

        try:
            for table_name, df, if_exists in writes:
                if not table_name:
                    raise basefunctions.DbValidationError("table_name in batch cannot be empty")
                if df is None:
                    raise basefunctions.DbValidationError("dataframe in batch cannot be None")
                if if_exists not in ["fail", "replace", "append"]:
                    raise basefunctions.DbValidationError(f"invalid if_exists value in batch: {if_exists}")

                # Create structured event data
                write_data = DataFrameWriteData(table_name=table_name, dataframe=df, if_exists=if_exists, cached=False)

                # Create event for async execution
                event = basefunctions.Event(type="dataframe.write", data=write_data, target=self.db_name)

                # Submit to EventBus (non-blocking)
                self._event_bus.publish(event)

        except basefunctions.DbValidationError:
            # Re-raise validation errors as-is
            raise
        except Exception as e:
            self.logger.critical(f"failed to submit DataFrame write batch: {str(e)}")
            raise basefunctions.DbQueryError(f"failed to submit DataFrame write batch: {str(e)}") from e

    def get_dataframe_write_results(self) -> List[str]:
        """
        Get all results from submitted DataFrame writes.

        Returns
        -------
        List[str]
            List of success messages in submission order

        Raises
        ------
        basefunctions.DbQueryError
            If any DataFrame write failed or no results available
        """
        try:
            # Wait for all pending operations to complete
            self._event_bus.join()

            # Get all results from EventBus
            results, errors = self._event_bus.get_results()

            # Handle errors first
            if errors:
                error_msg = f"DataFrame writes failed: {errors[0]}"
                self.logger.error(error_msg)
                raise basefunctions.DbQueryError(error_msg)

            # Extract success messages from results
            success_messages = []
            for result in results:
                if isinstance(result, str):
                    success_messages.append(result)
                else:
                    self.logger.warning(f"unexpected write result type: {type(result).__name__}")

            if not success_messages:
                raise basefunctions.DbQueryError("no write results available")

            return success_messages

        except basefunctions.DbQueryError:
            # Re-raise database errors as-is
            raise
        except Exception as e:
            self.logger.critical(f"failed to get DataFrame write results: {str(e)}")
            raise basefunctions.DbQueryError(f"failed to get DataFrame write results: {str(e)}") from e

    # =================================================================
    # UTILITY METHODS
    # =================================================================

    def close(self) -> None:
        """
        Close the database connection and shutdown EventBus.
        """
        with self.lock:
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

    def get_connection_info(self) -> Dict[str, Any]:
        """
        Get current connection information.

        Returns
        -------
        Dict[str, Any]
            Connection details
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

    def __str__(self) -> str:
        """
        String representation for debugging.

        Returns
        -------
        str
            Database status string
        """
        try:
            connected = "connected" if (self.connector and self.connector.is_connected()) else "disconnected"
            db_type = getattr(self.connector, "db_type", "unknown") if self.connector else "none"
            eventbus = "enabled" if self._event_bus is not None else "disabled"

            return f"Db[{self.db_name}, {db_type}, {connected}, eventbus:{eventbus}]"
        except Exception as e:
            return f"Db[{self.db_name}, error: {str(e)}]"

    def __repr__(self) -> str:
        """
        Detailed representation for debugging.

        Returns
        -------
        str
            Detailed database information
        """
        try:
            return (
                f"Db("
                f"db_name='{self.db_name}', "
                f"connector={type(self.connector).__name__ if self.connector else None}"
                f")"
            )
        except Exception as e:
            return f"Db(db_name='{self.db_name}', error='{str(e)}')"
