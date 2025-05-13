"""
=============================================================================

 Licensed Materials, Property of neuraldevelopment , Munich

 Project : backtraderfunctions

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 An improved database abstraction layer for SQLite, MySQL, and PostgreSQL

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Optional, Any, List, Dict, TypedDict, Tuple, Union, Type
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


class DatabaseError(Exception):
    """Base class for database exceptions"""

    pass


class QueryError(DatabaseError):
    """Error executing query"""

    pass


class TransactionError(DatabaseError):
    """Error handling transactions"""

    pass


class DatabaseParameters(TypedDict, total=False):
    """Type definition for database connection parameters"""

    database: str
    user: Optional[str]
    password: Optional[str]
    host: Optional[str]
    port: Optional[int]
    min_connections: Optional[int]
    max_connections: Optional[int]


class TransactionContextManager:
    """Context manager for database transactions"""

    def __init__(self, connector: "DatabaseConnector"):
        self.connector = connector

    def __enter__(self):
        self.connector.begin_transaction()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.connector.commit()
        else:
            self.connector.rollback()
            basefunctions.get_logger(__name__).error(
                "transaction rolled back due to: %s", str(exc_val)
            )
        return False  # Let exceptions propagate


class DatabaseConnector:
    """
    Abstract base class for database connectors with improved error handling,
    connection management, and consistent interface.
    """

    def __init__(self, parameters: DatabaseParameters):
        self.parameters = parameters
        self.connection: Optional[Any] = None
        self.cursor: Optional[Any] = None
        self.last_query_string: Optional[str] = None
        self.db_type: Optional[str] = None
        self.in_transaction: bool = False

    def __enter__(self):
        """Context manager entry point"""
        if not self.is_connected():
            self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit point"""
        self.close()
        return False  # Let exceptions propagate

    def _validate_parameters(self, required_keys: List[str]) -> None:
        """
        validate that all required parameters are present

        parameters
        ----------
        required_keys : List[str]
            list of required parameter keys

        raises
        ------
        ValueError
            if any required key is missing
        """
        missing_keys = [key for key in required_keys if key not in self.parameters]
        if missing_keys:
            raise ValueError(f"missing required parameters: {', '.join(missing_keys)}")

    def connect(self) -> None:
        """
        establish connection to the database

        raises
        ------
        ConnectionError
            if connection cannot be established
        """
        raise NotImplementedError

    def close(self) -> None:
        """close database connection and cursor"""
        try:
            if self.cursor:
                self.cursor.close()
        except Exception as e:
            self._log("warning", "error closing cursor: %s", str(e))
        try:
            if self.connection:
                self.connection.close()
        except Exception as e:
            self._log("warning", "error closing connection: %s", str(e))
        self.cursor = self.connection = None
        self._log("info", "connection closed (%s)", self.db_type)

    def execute(self, query: str, parameters: tuple = ()) -> None:
        """
        execute a sql query

        parameters
        ----------
        query : str
            sql query to execute
        parameters : tuple, optional
            query parameters, by default ()

        raises
        ------
        QueryError
            if query execution fails
        """
        raise NotImplementedError

    def fetch_one(
        self, query: str, parameters: tuple = (), new_query: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        fetch a single row from the database

        parameters
        ----------
        query : str
            sql query to execute
        parameters : tuple, optional
            query parameters, by default ()
        new_query : bool, optional
            whether to execute a new query or use the last one, by default False

        returns
        -------
        Optional[Dict[str, Any]]
            row as dictionary or None if no row found

        raises
        ------
        QueryError
            if query execution fails
        """
        raise NotImplementedError

    def fetch_all(self, query: str, parameters: tuple = ()) -> List[Dict[str, Any]]:
        """
        fetch all rows from the database

        parameters
        ----------
        query : str
            sql query to execute
        parameters : tuple, optional
            query parameters, by default ()

        returns
        -------
        List[Dict[str, Any]]
            rows as list of dictionaries

        raises
        ------
        QueryError
            if query execution fails
        """
        raise NotImplementedError

    def get_connection(self) -> Any:
        """
        get the underlying database connection

        returns
        -------
        Any
            database connection object
        """
        raise NotImplementedError

    def begin_transaction(self) -> None:
        """
        begin a database transaction

        raises
        ------
        TransactionError
            if transaction cannot be started
        """
        raise NotImplementedError

    def commit(self) -> None:
        """
        commit the current transaction

        raises
        ------
        TransactionError
            if commit fails
        """
        raise NotImplementedError

    def rollback(self) -> None:
        """
        rollback the current transaction

        raises
        ------
        TransactionError
            if rollback fails
        """
        raise NotImplementedError

    def is_connected(self) -> bool:
        """
        check if connection is established

        returns
        -------
        bool
            true if connected, false otherwise
        """
        raise NotImplementedError

    def check_if_table_exists(self, table_name: str) -> bool:
        """
        check if a table exists in the database

        parameters
        ----------
        table_name : str
            name of the table to check

        returns
        -------
        bool
            true if table exists, false otherwise
        """
        raise NotImplementedError

    def replace_sql_statement(self, sql_statement: str) -> str:
        """
        safe replacement of sql placeholders

        parameters
        ----------
        sql_statement : str
            sql statement with placeholders

        returns
        -------
        str
            sql statement with placeholders replaced
        """
        return sql_statement.replace("<PRIMARYKEY>", self._get_primary_key_syntax())

    def _get_primary_key_syntax(self) -> str:
        """
        get database-specific primary key syntax

        returns
        -------
        str
            primary key syntax
        """
        primary_key_map = {
            "sqlite3": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "mysql": "SERIAL AUTO_INCREMENT PRIMARY KEY",
            "postgresql": "BIGSERIAL PRIMARY KEY",
        }
        return primary_key_map.get(self.db_type, "BIGSERIAL PRIMARY KEY")

    def _log(self, level: str, message: str, *args) -> None:
        """
        log a message using the basefunctions logger

        parameters
        ----------
        level : str
            log level (debug, info, warning, error, critical)
        message : str
            log message
        *args
            arguments for message formatting
        """
        logger = basefunctions.get_logger(__name__)
        getattr(logger, level.lower())(message, *args)

    def transaction(self) -> TransactionContextManager:
        """
        return a transaction context manager

        returns
        -------
        TransactionContextManager
            transaction context manager

        example
        -------
        with connector.transaction():
            connector.execute("INSERT INTO users (name) VALUES (?)", ("John",))
            connector.execute("INSERT INTO logs (action) VALUES (?)", ("User created",))
        """
        return TransactionContextManager(self)
