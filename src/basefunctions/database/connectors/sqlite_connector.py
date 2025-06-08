"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich
  Project : basefunctions
  Copyright (c) by neuraldevelopment
  All rights reserved.
  Description:
  SQLite connector implementation with Registry-based configuration
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
    SQLite-specific connector implementing the base interface with Registry integration.

    Connection Behavior:
    - Connects to single database file (server_database is file path)
    - No server/host concepts (parameters ignored)
    - Database and schema switching not supported
    - Single-file database only

    Thread-safe implementation for concurrent access.
    """

    def __init__(self, parameters: basefunctions.DatabaseParameters) -> None:
        """
        Initialize the SQLite connector with Registry integration.

        parameters
        ----------
        parameters : basefunctions.DatabaseParameters
            connection parameters for the database
        """
        super().__init__(parameters)
        self.db_type = "sqlite3"
        self.engine = None
        self.lock = threading.RLock()

    def connect(self) -> None:
        """
        Establish connection to SQLite database file.
        server_database parameter specifies the file path.

        raises
        ------
        basefunctions.DbConnectionError
            if connection cannot be established
        """
        with self.lock:
            try:
                self._validate_parameters(["server_database"])

                # For SQLite, server_database is the file path
                database_file = self.parameters["server_database"]
                if not database_file:
                    raise basefunctions.DbConnectionError("SQLite database file path is required")

                self.current_database = database_file

                self.connection = sqlite3.connect(
                    database_file,
                    isolation_level=None,
                    check_same_thread=False,  # Allow multi-threading
                )
                if not self.connection:
                    raise basefunctions.DbConnectionError("Failed to establish SQLite connection")

                # Enable foreign keys by default
                self.connection.execute("PRAGMA foreign_keys = ON")

                # Apply custom pragmas if provided
                if "pragmas" in self.parameters and self.parameters["pragmas"]:
                    for pragma, value in self.parameters["pragmas"].items():
                        self.connection.execute(f"PRAGMA {pragma} = {value}")

                self.cursor = self.connection.cursor()
                if not self.cursor:
                    raise basefunctions.DbConnectionError("Failed to create SQLite cursor")

                # Create SQLAlchemy engine
                connection_url = f"sqlite:///{database_file}"
                self.engine = create_engine(connection_url)

                self.logger.debug(f"connected to sqlite database '{database_file}'")
            except Exception as e:
                self.logger.critical(f"failed to connect to sqlite database: {str(e)}")
                raise basefunctions.DbConnectionError(f"failed to connect to sqlite database: {str(e)}") from e

    def execute(self, query: str, parameters: Union[tuple, dict] = ()) -> None:
        """
        Execute a SQL query with Registry-based placeholder replacement.

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
        """
        with self.lock:
            if not self.is_connected():
                self.connect()

            if not self.cursor:
                raise basefunctions.DbQueryError("No cursor available for query execution")
            if not self.connection:
                raise basefunctions.DbQueryError("No connection available for query execution")

            try:
                self.cursor.execute(self.replace_sql_statement(query), parameters)
                if not self.in_transaction:
                    self.connection.commit()
            except Exception as e:
                if not self.in_transaction:
                    self.connection.rollback()
                self.logger.critical(f"failed to execute query: {str(e)}")
                raise basefunctions.DbQueryError(f"failed to execute query: {str(e)}") from e

    def query_one(
        self, query: str, parameters: Union[tuple, dict] = (), new_query: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch a single row from the database with Registry-based query handling.

        parameters
        ----------
        query : str
            SQL query to execute
        parameters : Union[tuple, dict], optional
            query parameters, by default ()
        new_query : bool, optional
            whether to execute a new query or use the last one, by default True

        returns
        -------
        Optional[Dict[str, Any]]
            row as dictionary or None if no row found

        raises
        ------
        basefunctions.DbQueryError
            if query execution fails
        """
        with self.lock:
            if not self.is_connected():
                self.connect()

            if not self.cursor:
                raise basefunctions.DbQueryError("No cursor available for fetch operation")

            try:
                if new_query or self.last_query_string != query:
                    self.cursor.execute(self.replace_sql_statement(query), parameters)
                    self.last_query_string = query

                row = self.cursor.fetchone()
                if not row:
                    return None

                if not self.cursor.description:
                    raise basefunctions.DbQueryError("No column description available")

                columns = [desc[0] for desc in self.cursor.description]
                return dict(zip(columns, row))
            except Exception as e:
                self.logger.critical(f"failed to fetch row: {str(e)}")
                raise basefunctions.DbQueryError(f"failed to fetch row: {str(e)}") from e

    def query_all(self, query: str, parameters: Union[tuple, dict] = ()) -> List[Dict[str, Any]]:
        """
        Fetch all rows from the database with Registry-based query handling.

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
        basefunctions.DbQueryError
            if query execution fails
        """
        with self.lock:
            if not self.is_connected():
                self.connect()

            if not self.cursor:
                raise basefunctions.DbQueryError("No cursor available for fetch operation")

            try:
                self.cursor.execute(self.replace_sql_statement(query), parameters)

                if not self.cursor.description:
                    return []

                columns = [desc[0] for desc in self.cursor.description]
                result = []
                for row in self.cursor.fetchall():
                    result.append(dict(zip(columns, row)))

                return result
            except Exception as e:
                self.logger.critical(f"failed to fetch rows: {str(e)}")
                raise basefunctions.DbQueryError(f"failed to fetch rows: {str(e)}") from e

    def get_connection(self) -> Any:
        """
        Get the underlying database connection.

        returns
        -------
        Any
            SQLAlchemy engine or SQLite connection object

        raises
        ------
        basefunctions.DbConnectionError
            if no connection is available
        """
        if self.engine:
            return self.engine
        if self.connection:
            return self.connection
        raise basefunctions.DbConnectionError("No connection available")

    def begin_transaction(self) -> None:
        """
        Begin a database transaction.

        raises
        ------
        basefunctions.DbTransactionError
            if transaction cannot be started
        """
        with self.lock:
            if not self.is_connected():
                self.connect()

            if not self.connection:
                raise basefunctions.DbTransactionError("No connection available for transaction")

            try:
                self.connection.execute("BEGIN")
                self.in_transaction = True
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
            if not self.connection:
                raise basefunctions.DbTransactionError("No connection available for commit")

            if not self.is_connected():
                raise basefunctions.DbTransactionError("not connected to database")

            try:
                self.connection.commit()
                self.in_transaction = False
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
            if not self.connection:
                raise basefunctions.DbTransactionError("No connection available for rollback")

            if not self.is_connected():
                raise basefunctions.DbTransactionError("not connected to database")

            try:
                self.connection.rollback()
                self.in_transaction = False
            except Exception as e:
                self.logger.critical(f"failed to rollback transaction: {str(e)}")
                raise basefunctions.DbTransactionError(f"failed to rollback transaction: {str(e)}") from e

    def is_connected(self) -> bool:
        """
        Check if connection is established and valid using Registry-based connection test.

        returns
        -------
        bool
            True if connected, False otherwise
        """
        if self.connection is None or self.cursor is None:
            return False

        try:
            # Use Registry-based connection test if available
            test_query = self.get_query_template("connection_test")
            if test_query:
                cursor = self.connection.cursor()
                cursor.execute(test_query)
                cursor.close()
            else:
                # Fallback to simple connection test
                cursor = self.connection.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
            return True
        except Exception as e:
            self.logger.debug(f"connection check failed: {str(e)}")
            return False

    def check_if_table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists using Registry-based query template.

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

            if not self.cursor:
                self.logger.warning("No cursor available for table existence check")
                return False

            try:
                # Use Registry-based table exists query
                table_exists_query = self.get_query_template("table_exists")
                if table_exists_query:
                    self.cursor.execute(table_exists_query, (table_name,))
                else:
                    # Fallback query
                    query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?;"
                    self.cursor.execute(query, (table_name,))

                return self.cursor.fetchone() is not None
            except Exception as e:
                self.logger.warning(f"error checking if table exists: {str(e)}")
                return False

    def use_database(self, database_name: str) -> None:
        """
        Database switching not supported for SQLite.

        parameters
        ----------
        database_name : str
            name of the database (not supported for SQLite)

        raises
        ------
        NotImplementedError
            always, as SQLite uses single-file databases
        """
        raise NotImplementedError(
            "SQLite uses single-file databases. Create a new connector instance "
            "with a different database file instead."
        )

    def use_schema(self, schema_name: str) -> None:
        """
        Schema switching not applicable for SQLite.

        parameters
        ----------
        schema_name : str
            name of the schema (not applicable for SQLite)

        raises
        ------
        NotImplementedError
            always, as SQLite does not support schemas
        """
        raise NotImplementedError(
            "SQLite does not support schemas. Use attached databases if you need " "multiple database contexts."
        )

    def list_tables(self) -> List[str]:
        """
        List all tables using Registry-based query template.

        returns
        -------
        List[str]
            list of table names
        """
        with self.lock:
            if not self.is_connected():
                self.connect()

            if not self.cursor:
                self.logger.warning("No cursor available for listing tables")
                return []

            try:
                # Use Registry-based list tables query
                list_tables_query = self.get_query_template("list_tables")
                if list_tables_query:
                    self.cursor.execute(list_tables_query)
                else:
                    # Fallback query
                    query = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                    self.cursor.execute(query)

                return [row[0] for row in self.cursor.fetchall()]
            except Exception as e:
                self.logger.warning(f"error listing tables: {str(e)}")
                return []
