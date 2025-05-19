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


class MySQLConnector(basefunctions.DatabaseConnector):
    """
    mysql-specific connector implementing the base interface with improved
    error handling and connection management.
    """

    def __init__(self, parameters: dict):
        super().__init__(parameters)
        self.db_type = "mysql"
        self.engine = None

    def connect(self) -> None:
        """
        establish connection to mysql database

        raises
        ------
        ConnectionError
            if connection cannot be established
        """
        try:
            self._validate_parameters(["user", "password", "host", "database"])
            self.connection = mysql.connector.connect(
                user=self.parameters["user"],
                password=self.parameters["password"],
                host=self.parameters["host"],
                port=self.parameters.get("port", 3306),
                database=self.parameters["database"],
            )
            self.cursor = self.connection.cursor()

            # Create SQLAlchemy engine for advanced operations
            connection_url = (
                f"mysql+pymysql://{self.parameters['user']}:"
                f"{self.parameters['password']}@{self.parameters['host']}:"
                f"{self.parameters.get('port', 3306)}/{self.parameters['database']}"
            )
            self.engine = create_engine(connection_url)

            self._log(
                "info",
                "connected to mysql database '%s' at %s:%s",
                self.parameters["database"],
                self.parameters["host"],
                self.parameters.get("port", 3306),
            )
        except Exception as e:
            raise ConnectionError(f"failed to connect to mysql database: {str(e)}") from e

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
        if not self.is_connected():
            self.connect()

        try:
            self.cursor.execute(self.replace_sql_statement(query), parameters)
            if not self.in_transaction:
                self.connection.commit()
        except Exception as e:
            if not self.in_transaction:
                self.connection.rollback()
            raise basefunctions.QueryError(f"failed to execute query: {str(e)}") from e

    def fetch_one(self, query: str, parameters: tuple = (), new_query: bool = False) -> dict:
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
        dict
            row as dictionary or None if no row found

        raises
        ------
        QueryError
            if query execution fails
        """
        if not self.is_connected():
            self.connect()

        try:
            if new_query or self.last_query_string != query:
                self.cursor.execute(query, parameters)
                self.last_query_string = query

            row = self.cursor.fetchone()
            if not row:
                return None

            columns = [desc[0] for desc in self.cursor.description]
            return dict(zip(columns, row))
        except Exception as e:
            raise basefunctions.QueryError(f"failed to fetch row: {str(e)}") from e

    def fetch_all(self, query: str, parameters: tuple = ()) -> list:
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
        list
            rows as list of dictionaries

        raises
        ------
        QueryError
            if query execution fails
        """
        if not self.is_connected():
            self.connect()

        try:
            self.cursor.execute(query, parameters)
            columns = [desc[0] for desc in self.cursor.description]
            return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
        except Exception as e:
            raise basefunctions.QueryError(f"failed to fetch rows: {str(e)}") from e

    def get_connection(self) -> object:
        """
        get the underlying database connection or SQLAlchemy engine

        returns
        -------
        object
            database connection or engine object
        """
        return self.engine or self.connection

    def begin_transaction(self) -> None:
        """
        begin a database transaction

        raises
        ------
        TransactionError
            if transaction cannot be started
        """
        if not self.is_connected():
            self.connect()

        try:
            self.connection.start_transaction()
            self.in_transaction = True
        except Exception as e:
            raise basefunctions.TransactionError(f"failed to begin transaction: {str(e)}") from e

    def commit(self) -> None:
        """
        commit the current transaction

        raises
        ------
        TransactionError
            if commit fails
        """
        if not self.is_connected():
            raise basefunctions.TransactionError("not connected to database")

        try:
            self.connection.commit()
            self.in_transaction = False
        except Exception as e:
            raise basefunctions.TransactionError(f"failed to commit transaction: {str(e)}") from e

    def rollback(self) -> None:
        """
        rollback the current transaction

        raises
        ------
        TransactionError
            if rollback fails
        """
        if not self.is_connected():
            raise basefunctions.TransactionError("not connected to database")

        try:
            self.connection.rollback()
            self.in_transaction = False
        except Exception as e:
            raise basefunctions.TransactionError(
                f"failed to rollback transaction: {str(e)}"
            ) from e

    def is_connected(self) -> bool:
        """
        check if connection is established

        returns
        -------
        bool
            true if connected, false otherwise
        """
        return self.connection.is_connected() if self.connection else False

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
        if not self.is_connected():
            self.connect()

        try:
            query = "SHOW TABLES LIKE %s;"
            self.cursor.execute(query, (table_name,))
            return self.cursor.fetchone() is not None
        except Exception as e:
            self._log("error", "error checking if table exists: %s", str(e))
            return False
