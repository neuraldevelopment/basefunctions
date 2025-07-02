"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich

  Project : basefunctions

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  Database abstraction layer with high-level operations

  Log:
  v1.0 : Initial implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Dict, List, Optional, Any, Union, Generator
import threading
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


class Db:
    """
    High-level database abstraction with SQL operations and transaction management.
    Uses composition with DbConnector for actual database operations.
    Thread-safe implementation for concurrent access.
    """

    def __init__(self, instance_name: str, database_name: str) -> None:
        """
        Initialize database object with instance and database names.

        parameters
        ----------
        instance_name : str
            name of the database instance
        database_name : str
            name of the database

        raises
        ------
        basefunctions.DbValidationError
            if parameters are invalid
        basefunctions.DbConnectionError
            if connector creation fails
        """
        if not instance_name:
            raise basefunctions.DbValidationError("instance_name cannot be empty")
        if not database_name:
            raise basefunctions.DbValidationError("database_name cannot be empty")

        self.instance_name = instance_name
        self.database_name = database_name
        self.logger = basefunctions.get_logger(__name__)
        self.lock = threading.RLock()

        # Create connector via DbManager
        try:
            manager = basefunctions.DbManager()
            self.connector = manager.get_connector(instance_name, database_name)
        except Exception as e:
            self.logger.critical(f"failed to create connector for '{instance_name}.{database_name}': {str(e)}")
            raise basefunctions.DbConnectionError(
                f"failed to create connector for '{instance_name}.{database_name}': {str(e)}"
            ) from e

    # =================================================================
    # QUERY EXECUTION
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

    def query_one(self, query: str, parameters: Union[tuple, dict] = ()) -> Optional[Dict[str, Any]]:
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

                return self.connector.query_one(query, parameters, new_query=True)
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

                return self.connector.query_all(query, parameters)
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

    def query_iter(self, query: str, parameters: Union[tuple, dict] = ()) -> Generator[Dict[str, Any], None, None]:
        """
        Execute a SQL query and return an iterator for large resultsets.
        Memory-efficient for processing large amounts of data.

        parameters
        ----------
        query : str
            SQL query to execute
        parameters : Union[tuple, dict], optional
            query parameters, by default ()

        yields
        ------
        Dict[str, Any]
            row as dictionary

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

                # Get first row to start iteration
                first_row = self.connector.query_one(query, parameters, new_query=True)
                if first_row is not None:
                    yield first_row

                    # Continue iterating through remaining rows
                    while True:
                        row = self.connector.query_one("", (), new_query=False)
                        if row is None:
                            break
                        yield row

            except (
                basefunctions.DbQueryError,
                basefunctions.DbConnectionError,
                basefunctions.DbValidationError,
            ):
                # Re-raise specific database errors as-is
                raise
            except Exception as e:
                self.logger.critical(f"failed to execute query iterator: {str(e)}")
                raise basefunctions.DbQueryError(f"failed to execute query iterator: {str(e)}") from e

    # =================================================================
    # CONNECTION MANAGEMENT
    # =================================================================

    def connect(self) -> None:
        """
        Establish connection to the database.

        raises
        ------
        basefunctions.DbConnectionError
            if connection cannot be established
        """
        with self.lock:
            try:
                self.connector.connect()
            except basefunctions.DbConnectionError:
                # Re-raise connection errors as-is
                raise
            except Exception as e:
                self.logger.critical(f"failed to connect: {str(e)}")
                raise basefunctions.DbConnectionError(f"failed to connect: {str(e)}") from e

    def disconnect(self) -> None:
        """
        Close database connection.
        """
        with self.lock:
            try:
                self.connector.disconnect()
            except Exception as e:
                self.logger.warning(f"error during disconnect: {str(e)}")

    def is_connected(self) -> bool:
        """
        Check if connection is established.

        returns
        -------
        bool
            True if connected, False otherwise
        """
        try:
            return self.connector.is_connected()
        except Exception as e:
            self.logger.warning(f"error checking connection status: {str(e)}")
            return False

    def get_connection(self) -> Any:
        """
        Get the underlying database connection.

        returns
        -------
        Any
            database connection object

        raises
        ------
        basefunctions.DbConnectionError
            if not connected
        """
        try:
            return self.connector.get_connection()
        except Exception as e:
            self.logger.critical(f"failed to get connection: {str(e)}")
            raise basefunctions.DbConnectionError(f"failed to get connection: {str(e)}") from e

    def get_connector(self) -> "basefunctions.DbConnector":
        """
        Get the underlying database connector.

        returns
        -------
        basefunctions.DbConnector
            database connector instance
        """
        return self.connector

    # =================================================================
    # TRANSACTION MANAGEMENT
    # =================================================================

    def begin_transaction(self) -> None:
        """
        Begin a database transaction.

        raises
        ------
        basefunctions.DbTransactionError
            if transaction cannot be started
        """
        with self.lock:
            try:
                if not self.connector.is_connected():
                    self.connector.connect()

                self.connector.begin_transaction()
            except basefunctions.DbTransactionError:
                # Re-raise transaction errors as-is
                raise
            except Exception as e:
                self.logger.critical(f"failed to begin transaction: {str(e)}")
                raise basefunctions.DbTransactionError(f"failed to begin transaction: {str(e)}") from e

    def commit(self) -> None:
        """
        Commit the current transaction.

        raises
        ------
        basefunctions.DbTransactionError
            if commit fails
        """
        with self.lock:
            try:
                self.connector.commit()
            except basefunctions.DbTransactionError:
                # Re-raise transaction errors as-is
                raise
            except Exception as e:
                self.logger.critical(f"failed to commit transaction: {str(e)}")
                raise basefunctions.DbTransactionError(f"failed to commit transaction: {str(e)}") from e

    def rollback(self) -> None:
        """
        Rollback the current transaction.

        raises
        ------
        basefunctions.DbTransactionError
            if rollback fails
        """
        with self.lock:
            try:
                self.connector.rollback()
            except basefunctions.DbTransactionError:
                # Re-raise transaction errors as-is
                raise
            except Exception as e:
                self.logger.critical(f"failed to rollback transaction: {str(e)}")
                raise basefunctions.DbTransactionError(f"failed to rollback transaction: {str(e)}") from e

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
    # SCHEMA OPERATIONS
    # =================================================================

    def check_if_table_exists(self, table_name: str) -> bool:
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

    def use_schema(self, schema_name: str) -> None:
        """
        Switch to a different schema context.

        parameters
        ----------
        schema_name : str
            name of the schema to switch to

        raises
        ------
        NotImplementedError
            if schema switching is not supported
        basefunctions.DbQueryError
            if schema switch fails
        """
        if not schema_name:
            raise basefunctions.DbValidationError("schema_name cannot be empty")

        with self.lock:
            try:
                if not self.connector.is_connected():
                    self.connector.connect()

                self.connector.use_schema(schema_name)
            except (NotImplementedError, basefunctions.DbQueryError):
                # Re-raise these as-is
                raise
            except Exception as e:
                self.logger.critical(f"failed to switch schema: {str(e)}")
                raise basefunctions.DbQueryError(f"failed to switch schema: {str(e)}") from e

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

                return self.connector.list_tables()
            except Exception as e:
                self.logger.warning(f"error listing tables: {str(e)}")
                return []

    # =================================================================
    # INFO & UTILITY
    # =================================================================

    def get_connection_info(self) -> Dict[str, Any]:
        """
        Get current connection information.

        returns
        -------
        Dict[str, Any]
            connection details
        """
        try:
            return self.connector.get_connection_info()
        except Exception as e:
            self.logger.warning(f"error getting connection info: {str(e)}")
            return {"connected": False, "error": str(e)}

    def __str__(self) -> str:
        """
        String representation for debugging.

        returns
        -------
        str
            database status string
        """
        try:
            connected = "connected" if self.is_connected() else "disconnected"
            db_type = getattr(self.connector, "db_type", "unknown") if self.connector else "none"
            return f"Db[{db_type}, {connected}]"
        except Exception as e:
            return f"Db[error: {str(e)}]"

    def __repr__(self) -> str:
        """
        Detailed representation for debugging.

        returns
        -------
        str
            detailed database information
        """
        try:
            return f"Db(connector={type(self.connector).__name__ if self.connector else None})"
        except Exception as e:
            return f"Db(error='{str(e)}')"
