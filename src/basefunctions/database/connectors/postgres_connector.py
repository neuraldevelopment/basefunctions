"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment , Munich
  Project : basefunctions
  Copyright (c) by neuraldevelopment
  All rights reserved.
  Description:
  PostgreSQL connector implementation for the database abstraction layer
 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import threading
from typing import Optional, Any, List, Dict, Union
import psycopg2
import psycopg2.extras
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


class PostgreSQLConnector(basefunctions.DbConnector):
    """
    PostgreSQL-specific connector implementing the base interface with improved
    error handling and connection management.
    Thread-safe implementation for concurrent access.
    """

    def __init__(self, parameters: Dict[str, Any]) -> None:
        """
        Initialize the PostgreSQL connector.

        parameters
        ----------
        parameters : Dict[str, Any]
            connection parameters for the database
        """
        super().__init__(parameters)
        self.db_type = "postgresql"
        self.engine = None
        self.lock = threading.RLock()

    def connect(self) -> None:
        """
        Establish connection to PostgreSQL database.

        raises
        ------
        basefunctions.DbConnectionError
            if connection cannot be established
        """
        with self.lock:
            try:
                self._validate_parameters(["user", "password", "host", "database"])

                # Prepare connection arguments
                connect_args = {
                    "user": self.parameters["user"],
                    "password": self.parameters["password"],
                    "host": self.parameters["host"],
                    "database": self.parameters["database"],
                    "port": self.parameters.get("port", 5432),
                }

                # Add optional ssl parameters if available
                if self.parameters.get("ssl_ca"):
                    connect_args["sslrootcert"] = self.parameters["ssl_ca"]
                if self.parameters.get("ssl_cert"):
                    connect_args["sslcert"] = self.parameters["ssl_cert"]
                if self.parameters.get("ssl_key"):
                    connect_args["sslkey"] = self.parameters["ssl_key"]
                if "ssl_verify" in self.parameters and not self.parameters["ssl_verify"]:
                    connect_args["sslmode"] = "require"  # Skip verification
                elif any(key in self.parameters for key in ["ssl_ca", "ssl_cert", "ssl_key"]):
                    connect_args["sslmode"] = "verify-ca"

                # Add client encoding if specified
                if "charset" in self.parameters:
                    connect_args["client_encoding"] = self.parameters["charset"]

                # Establish connection
                self.connection = psycopg2.connect(**connect_args)
                self.connection.autocommit = True  # Default to autocommit

                # Use RealDictCursor to get results as dictionaries
                self.cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

                # Create SQLAlchemy engine for advanced operations (pandas)
                conn_url_parts = [
                    f"postgresql+psycopg2://{self.parameters['user']}",
                    f":{self.parameters['password']}@{self.parameters['host']}",
                    f":{self.parameters.get('port', 5432)}/{self.parameters['database']}",
                ]

                connection_url = "".join(conn_url_parts)
                self.engine = create_engine(connection_url)

                self.logger.warning(
                    f"connected to postgresql database '{self.parameters['database']}' "
                    f"at {self.parameters['host']}:{self.parameters.get('port', 5432)}"
                )
            except Exception as e:
                self.logger.critical(f"failed to connect to postgresql database: {str(e)}")
                raise basefunctions.DbConnectionError(
                    f"failed to connect to postgresql database: {str(e)}"
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

                # Using RealDictCursor, results are already dictionaries
                return self.cursor.fetchone()
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
                return list(self.cursor.fetchall())  # Convert to list to ensure it's fully loaded
            except Exception as e:
                self.logger.critical(f"failed to fetch rows: {str(e)}")
                raise basefunctions.QueryError(f"failed to fetch rows: {str(e)}") from e

    def get_connection(self) -> Any:
        """
        Get the underlying database connection.

        returns
        -------
        Any
            SQLAlchemy engine or PostgreSQL connection object
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
                # Turn off autocommit to begin a transaction
                self.connection.autocommit = False
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
                # Turn autocommit back on
                self.connection.autocommit = True
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
                # Turn autocommit back on
                self.connection.autocommit = True
                self.in_transaction = False
            except Exception as e:
                self.logger.critical(f"failed to rollback transaction: {str(e)}")
                raise basefunctions.TransactionError(
                    f"failed to rollback transaction: {str(e)}"
                ) from e

    def is_connected(self) -> bool:
        """
        Check if connection is established.

        returns
        -------
        bool
            True if connected, False otherwise
        """
        if not self.connection:
            return False

        try:
            # Test if connection is alive by executing a simple query
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            return True
        except:
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
                # PostgreSQL specific query to check if table exists
                query = (
                    "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = %s)"
                )
                self.cursor.execute(query, (table_name,))
                result = self.cursor.fetchone()
                return result and result.get("exists", False)
            except Exception as e:
                self.logger.warning(f"error checking if table exists: {str(e)}")
                return False

    def get_server_version(self) -> str:
        """
        Get the PostgreSQL server version.

        returns
        -------
        str
            PostgreSQL server version
        """
        if not self.is_connected():
            self.connect()

        try:
            # Get server version
            self.cursor.execute("SHOW server_version")
            result = self.cursor.fetchone()
            return result.get("server_version", "Unknown")
        except Exception as e:
            self.logger.warning(f"error getting server version: {str(e)}")
            return "Unknown"
