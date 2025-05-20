"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment , Munich
  Project : basefunctions
  Copyright (c) by neuraldevelopment
  All rights reserved.
  Description:
  MySQL connector implementation for the database abstraction layer
 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import threading
from typing import Optional, Any, List, Dict, Union
import mysql.connector
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


class MySQLConnector(basefunctions.DbConnector):
    """
    MySQL-specific connector implementing the base interface with improved
    error handling and connection management.
    Thread-safe implementation for concurrent access.
    """

    def __init__(self, parameters: Dict[str, Any]) -> None:
        """
        Initialize the MySQL connector.

        parameters
        ----------
        parameters : Dict[str, Any]
            connection parameters for the database
        """
        super().__init__(parameters)
        self.db_type = "mysql"
        self.engine = None
        self.lock = threading.RLock()

    def connect(self) -> None:
        """
        Establish connection to MySQL database.

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
                    "port": self.parameters.get("port", 3306),
                    "charset": self.parameters.get("charset", "utf8mb4"),
                    "use_pure": True,  # Use pure Python implementation for thread safety
                    "autocommit": True,  # Default to autocommit
                }

                # Add optional ssl parameters if available
                if self.parameters.get("ssl_ca"):
                    connect_args["ssl_ca"] = self.parameters["ssl_ca"]
                if self.parameters.get("ssl_cert"):
                    connect_args["ssl_cert"] = self.parameters["ssl_cert"]
                if self.parameters.get("ssl_key"):
                    connect_args["ssl_key"] = self.parameters["ssl_key"]
                if "ssl_verify" in self.parameters:
                    connect_args["ssl_verify_cert"] = self.parameters["ssl_verify"]

                # Establish connection
                self.connection = mysql.connector.connect(**connect_args)
                self.cursor = self.connection.cursor(dictionary=True)

                # Create SQLAlchemy engine for advanced operations (pandas)
                conn_url_parts = [
                    f"mysql+pymysql://{self.parameters['user']}",
                    f":{self.parameters['password']}@{self.parameters['host']}",
                    f":{self.parameters.get('port', 3306)}/{self.parameters['database']}",
                ]

                connection_url = "".join(conn_url_parts)
                self.engine = create_engine(connection_url)

                self.logger.warning(
                    f"connected to mysql database '{self.parameters['database']}' "
                    f"at {self.parameters['host']}:{self.parameters.get('port', 3306)}"
                )
            except Exception as e:
                self.logger.critical(f"failed to connect to mysql database: {str(e)}")
                raise basefunctions.DbConnectionError(
                    f"failed to connect to mysql database: {str(e)}"
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

                # Since we use dictionary=True for cursor, result is already a dictionary
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
            SQLAlchemy engine or MySQL connection object
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
                # Start a transaction and set autocommit mode off
                self.connection.autocommit = False
                self.connection.start_transaction()
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
                # Reset autocommit mode to True after commit
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
                # Reset autocommit mode to True after rollback
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
        if self.connection is None:
            return False

        try:
            return self.connection.is_connected()
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
                query = "SHOW TABLES LIKE %s"
                self.cursor.execute(query, (table_name,))
                return self.cursor.fetchone() is not None
            except Exception as e:
                self.logger.warning(f"error checking if table exists: {str(e)}")
                return False

    def get_server_version(self) -> str:
        """
        Get the MySQL server version.

        returns
        -------
        str
            MySQL server version
        """
        if not self.is_connected():
            self.connect()

        try:
            return self.connection.get_server_info()
        except Exception as e:
            self.logger.warning(f"error getting server version: {str(e)}")
            return "Unknown"
