"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich
  Project : basefunctions
  Copyright (c) by neuraldevelopment
  All rights reserved.
  Description:
  SQLite connector implementation with explicit connection semantics
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
    SQLite-specific connector implementing the base interface.

    Connection Behavior:
    - Connects to single database file (server_database is file path)
    - No server/host concepts (parameters ignored)
    - Database and schema switching not supported
    - Single-file database only

    Thread-safe implementation for concurrent access.
    """

    def __init__(self, parameters: basefunctions.DatabaseParameters) -> None:
        """
        Initialize the SQLite connector.

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
                self.current_database = database_file

                self.connection = sqlite3.connect(
                    database_file,
                    isolation_level=None,
                    check_same_thread=False,  # Allow multi-threading
                )

                # Enable foreign keys by default
                self.connection.execute("PRAGMA foreign_keys = ON")

                # Apply custom pragmas if provided
                if "pragmas" in self.parameters:
                    for pragma, value in self.parameters["pragmas"].items():
                        self.connection.execute(f"PRAGMA {pragma} = {value}")

                self.cursor = self.connection.cursor()

                # Create SQLAlchemy engine
                connection_url = f"sqlite:///{database_file}"
                self.engine = create_engine(connection_url)

                self.logger.warning(f"connected to sqlite database '{database_file}'")
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

                columns = [desc[0] for desc in self.cursor.description]
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
            "SQLite does not support schemas. Use attached databases if you need "
            "multiple database contexts."
        )

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

            return os.path.getsize(self.current_database)
        except Exception as e:
            self.logger.warning(f"error getting database size: {str(e)}")
            return -1

    def attach_database(self, database_file: str, alias: str) -> None:
        """
        Attach another SQLite database file.

        parameters
        ----------
        database_file : str
            path to the database file to attach
        alias : str
            alias name for the attached database

        raises
        ------
        basefunctions.QueryError
            if database attachment fails
        """
        with self.lock:
            if not self.is_connected():
                self.connect()

            try:
                self.cursor.execute(f"ATTACH DATABASE ? AS {alias}", (database_file,))
                self.logger.info(f"attached database {database_file} as {alias}")
            except Exception as e:
                self.logger.critical(f"failed to attach database {database_file}: {str(e)}")
                raise basefunctions.QueryError(
                    f"failed to attach database {database_file}: {str(e)}"
                ) from e

    def detach_database(self, alias: str) -> None:
        """
        Detach a previously attached database.

        parameters
        ----------
        alias : str
            alias name of the database to detach

        raises
        ------
        basefunctions.QueryError
            if database detachment fails
        """
        with self.lock:
            if not self.is_connected():
                self.connect()

            try:
                self.cursor.execute(f"DETACH DATABASE {alias}")
                self.logger.info(f"detached database {alias}")
            except Exception as e:
                self.logger.critical(f"failed to detach database {alias}: {str(e)}")
                raise basefunctions.QueryError(
                    f"failed to detach database {alias}: {str(e)}"
                ) from e

    def list_attached_databases(self) -> List[Dict[str, Any]]:
        """
        List all attached databases.

        returns
        -------
        List[Dict[str, Any]]
            list of attached databases with seq, name, and file
        """
        with self.lock:
            if not self.is_connected():
                self.connect()

            try:
                self.cursor.execute("PRAGMA database_list")
                columns = [desc[0] for desc in self.cursor.description]
                result = []
                for row in self.cursor.fetchall():
                    result.append(dict(zip(columns, row)))
                return result
            except Exception as e:
                self.logger.warning(f"error listing attached databases: {str(e)}")
                return []
