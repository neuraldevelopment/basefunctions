"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment , Munich
  Project : basefunctions
  Copyright (c) by neuraldevelopment
  All rights reserved.
  Description:
  SQLite connector implementation for the database abstraction layer
 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import sqlite3
import threading
from typing import Optional, Any, List, Dict, Union
from sqlalchemy import create_engine
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


class SQLiteConnector(basefunctions.DbConnector):
    """
    SQLite-specific connector implementing the base interface with improved
    error handling and connection management.
    Thread-safe implementation for concurrent access.
    """

    def __init__(self, parameters: Dict[str, Any]) -> None:
        """
        Initialize the SQLite connector.

        parameters
        ----------
        parameters : Dict[str, Any]
            connection parameters for the database
        """
        super().__init__(parameters)
        self.db_type = "sqlite3"
        self.engine = None
        self.lock = threading.RLock()

    def connect(self) -> None:
        """
        Establish connection to SQLite database.

        raises
        ------
        basefunctions.DbConnectionError
            if connection cannot be established
        """
        with self.lock:
            try:
                self._validate_parameters(["database"])
                self.connection = sqlite3.connect(
                    self.parameters["database"], isolation_level=None
                )

                # Enable foreign keys by default
                self.connection.execute("PRAGMA foreign_keys = ON")

                # Apply pragmas from parameters if provided
                if "pragmas" in self.parameters:
                    for pragma, value in self.parameters["pragmas"].items():
                        self.connection.execute(f"PRAGMA {pragma} = {value}")

                self.cursor = self.connection.cursor()

                # Create SQLAlchemy engine for advanced operations
                connection_url = f"sqlite:///{self.parameters['database']}"
                self.engine = create_engine(connection_url)

                self.logger.warning(
                    f"connected to sqlite database '{self.parameters['database']}'"
                )
            except Exception as e:
                self.logger.critical(f"failed to connect to sqlite database: {str(e)}")
                raise basefunctions.DbConnectionError(
                    f"failed to connect to sqlite database: {str(e)}"
                ) from e

    def execute(self, query: str, parameters: Union[tuple, dict] = ()) -> None:
        """
        Execute a SQL query.

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
            if not self.is_connected():
                self.connect()

            try:
                self.cursor.execute(self.replace_sql_statement(query), parameters)
                if not self.in_transaction:
                    self.connection.commit()
            except Exception as e:
                if not self.in_transaction:
                    self.connection.rollback()
                self.logger.critical(f"failed to execute query: {str(e)}")
                raise basefunctions.QueryError(f"failed to execute query: {str(e)}") from e

    def fetch_one(
        self, query: str, parameters: Union[tuple, dict] = (), new_query: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch a single row from the database.

        parameters
        ----------
        query : str
            SQL query to execute
        parameters : Union[tuple, dict], optional
            query parameters, by default ()
        new_query : bool, optional
            whether to execute a new query or use the last one, by default False

        returns
        -------
        Optional[Dict[str, Any]]
            row as dictionary or None if no row found

        raises
        ------
        basefunctions.QueryError
            if query execution fails
        """
        with self.lock:
            if not self.is_connected():
                self.connect()

            try:
                if new_query or self.last_query_string != query:
                    self.cursor.execute(self.replace_sql_statement(query), parameters)
                    self.last_query_string = query

                row = self.cursor.fetchone()
                if not row:
                    return None

                # Get column names from cursor description
                columns = [desc[0] for desc in self.cursor.description]
                return dict(zip(columns, row))
            except Exception as e:
                self.logger.critical(f"failed to fetch row: {str(e)}")
                raise basefunctions.QueryError(f"failed to fetch row: {str(e)}") from e

    def fetch_all(self, query: str, parameters: Union[tuple, dict] = ()) -> List[Dict[str, Any]]:
        """
        Fetch all rows from the database.

        parameters
        ----------
        query : str
            SQL query to execute
        parameters : Union[tuple, dict], optional
            query parameters, by default ()

        returns
        -------
        List[Dict[str, Any]]
            rows as list of dictionaries

        raises
        ------
        basefunctions.QueryError
            if query execution fails
        """
        with self.lock:
            if not self.is_connected():
                self.connect()

            try:
                self.cursor.execute(self.replace_sql_statement(query), parameters)

                # Get column names from cursor description
                columns = [desc[0] for desc in self.cursor.description]

                # Convert rows to dictionaries
                result = []
                for row in self.cursor.fetchall():
                    result.append(dict(zip(columns, row)))

                return result
            except Exception as e:
                self.logger.critical(f"failed to fetch rows: {str(e)}")
                raise basefunctions.QueryError(f"failed to fetch rows: {str(e)}") from e

    def get_connection(self) -> Any:
        """
        Get the underlying database connection.

        returns
        -------
        Any
            SQLAlchemy engine or SQLite connection object
        """
        return self.engine or self.connection

    def begin_transaction(self) -> None:
        """
        Begin a database transaction.

        raises
        ------
        basefunctions.TransactionError
            if transaction cannot be started
        """
        with self.lock:
            if not self.is_connected():
                self.connect()

            try:
                self.connection.execute("BEGIN")
                self.in_transaction = True
            except Exception as e:
                self.logger.critical(f"failed to begin transaction: {str(e)}")
                raise basefunctions.TransactionError(
                    f"failed to begin transaction: {str(e)}"
                ) from e

    def commit(self) -> None:
        """
        Commit the current transaction.

        raises
        ------
        basefunctions.TransactionError
            if commit fails
        """
        with self.lock:
            if not self.is_connected():
                raise basefunctions.TransactionError("not connected to database")

            try:
                self.connection.commit()
                self.in_transaction = False
            except Exception as e:
                self.logger.critical(f"failed to commit transaction: {str(e)}")
                raise basefunctions.TransactionError(
                    f"failed to commit transaction: {str(e)}"
                ) from e

    def rollback(self) -> None:
        """
        Rollback the current transaction.

        raises
        ------
        basefunctions.TransactionError
            if rollback fails
        """
        with self.lock:
            if not self.is_connected():
                raise basefunctions.TransactionError("not connected to database")

            try:
                self.connection.rollback()
                self.in_transaction = False
            except Exception as e:
                self.logger.critical(f"failed to rollback transaction: {str(e)}")
                raise basefunctions.TransactionError(
                    f"failed to rollback transaction: {str(e)}"
                ) from e

    def is_connected(self) -> bool:
        """
        Check if connection is established and valid.

        returns
        -------
        bool
            True if connected, False otherwise
        """
        if self.connection is None or self.cursor is None:
            return False

        try:
            # Simple test query to verify connection
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            return True
        except Exception as e:
            self.logger.debug(f"connection check failed: {str(e)}")
            return False

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
        with self.lock:
            if not self.is_connected():
                self.connect()

            try:
                query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?;"
                self.cursor.execute(query, (table_name,))
                return self.cursor.fetchone() is not None
            except Exception as e:
                self.logger.warning(f"error checking if table exists: {str(e)}")
                return False

    def get_database_size(self) -> int:
        """
        Get the size of the database file in bytes.

        returns
        -------
        int
            size in bytes or -1 if error
        """
        try:
            import os

            return os.path.getsize(self.parameters["database"])
        except Exception as e:
            self.logger.warning(f"error getting database size: {str(e)}")
            return -1
