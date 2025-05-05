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
from typing import Optional, Any, List, Dict
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


class DatabaseHandler:
    """
    Central database interface for managing multiple database connectors.
    """

    def __init__(self):
        self.connectors: Dict[str, basefunctions.DatabaseConnector] = {}

    def register_connector(
        self, connector_id: str, db_type: str, parameters: basefunctions.DatabaseParameters
    ) -> basefunctions.DatabaseConnector:
        """
        register a new database connector

        parameters
        ----------
        connector_id : str
            unique identifier for the connector
        db_type : str
            database type (sqlite3, mysql, postgresql)
        parameters : DatabaseParameters
            connection parameters

        returns
        -------
        DatabaseConnector
            registered connector instance

        raises
        ------
        ValueError
            if db_type is not supported
        """
        connector_map = {
            "sqlite3": basefunctions.SQLiteConnector,
            "mysql": basefunctions.MySQLConnector,
            "postgresql": basefunctions.PostgreSQLConnector,
        }
        db_type = db_type.lower()
        if db_type not in connector_map:
            raise ValueError(f"unsupported db_type '{db_type}'")
        self.connectors[connector_id] = connector_map[db_type](parameters)
        basefunctions.get_logger(__name__).info(
            f"registered db connector '{connector_id}' ({db_type})"
        )
        return self.connectors[connector_id]

    def get_connector(self, connector_id: str) -> basefunctions.DatabaseConnector:
        """
        get a registered connector by id

        parameters
        ----------
        connector_id : str
            connector identifier

        returns
        -------
        DatabaseConnector
            connector instance

        raises
        ------
        KeyError
            if connector is not registered
        """
        if connector_id not in self.connectors:
            raise KeyError(f"connector '{connector_id}' not registered.")
        return self.connectors[connector_id]

    def connect(self, connector_id: str) -> None:
        """
        connect to database using a registered connector

        parameters
        ----------
        connector_id : str
            connector identifier
        """
        self.get_connector(connector_id).connect()

    def close(self, connector_id: str) -> None:
        """
        close connection of a registered connector

        parameters
        ----------
        connector_id : str
            connector identifier
        """
        self.get_connector(connector_id).close()

    def close_all(self) -> None:
        """close all registered connections"""
        for connector in self.connectors.values():
            connector.close()

    def execute(self, connector_id: str, query: str, parameters: tuple = ()) -> None:
        """
        execute a sql query using a registered connector

        parameters
        ----------
        connector_id : str
            connector identifier
        query : str
            sql query to execute
        parameters : tuple, optional
            query parameters, by default ()
        """
        self.get_connector(connector_id).execute(query, parameters)

    def fetch_one(
        self, connector_id: str, query: str, parameters: tuple = (), new_query: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        fetch a single row using a registered connector

        parameters
        ----------
        connector_id : str
            connector identifier
        query : str
            sql query to execute
        parameters : tuple, optional
            query parameters, by default ()
        new_query : bool, optional
            whether to execute a new query, by default False

        returns
        -------
        Optional[Dict[str, Any]]
            row as dictionary or None if no row found
        """
        return self.get_connector(connector_id).fetch_one(query, parameters, new_query)

    def fetch_all(
        self, connector_id: str, query: str, parameters: tuple = ()
    ) -> List[Dict[str, Any]]:
        """
        fetch all rows using a registered connector

        parameters
        ----------
        connector_id : str
            connector identifier
        query : str
            sql query to execute
        parameters : tuple, optional
            query parameters, by default ()

        returns
        -------
        List[Dict[str, Any]]
            rows as list of dictionaries
        """
        return self.get_connector(connector_id).fetch_all(query, parameters)

    def begin_transaction(self, connector_id: str) -> None:
        """
        begin a transaction using a registered connector

        parameters
        ----------
        connector_id : str
            connector identifier
        """
        self.get_connector(connector_id).begin_transaction()

    def commit(self, connector_id: str) -> None:
        """
        commit a transaction using a registered connector

        parameters
        ----------
        connector_id : str
            connector identifier
        """
        self.get_connector(connector_id).commit()

    def rollback(self, connector_id: str) -> None:
        """
        rollback a transaction using a registered connector

        parameters
        ----------
        connector_id : str
            connector identifier
        """
        self.get_connector(connector_id).rollback()

    def is_connected(self, connector_id: str) -> bool:
        """
        check if a connector is connected

        parameters
        ----------
        connector_id : str
            connector identifier

        returns
        -------
        bool
            true if connected, false otherwise
        """
        return self.get_connector(connector_id).is_connected()

    def check_if_table_exists(self, connector_id: str, table_name: str) -> bool:
        """
        check if a table exists using a registered connector

        parameters
        ----------
        connector_id : str
            connector identifier
        table_name : str
            name of the table to check

        returns
        -------
        bool
            true if table exists, false otherwise
        """
        return self.get_connector(connector_id).check_if_table_exists(table_name)

    def get_connection(self, connector_id: str) -> Any:
        """
        get the underlying connection object of a registered connector

        parameters
        ----------
        connector_id : str
            connector identifier

        returns
        -------
        Any
            database connection object
        """
        return self.get_connector(connector_id).get_connection()

    def transaction(self, connector_id: str) -> basefunctions.TransactionContextManager:
        """
        get a transaction context manager for a registered connector

        parameters
        ----------
        connector_id : str
            connector identifier

        returns
        -------
        TransactionContextManager
            transaction context manager

        example
        -------
        with db_handler.transaction('my_db'):
            db_handler.execute('my_db', "INSERT INTO users (name) VALUES (?)", ("John",))
            db_handler.execute('my_db', "INSERT INTO logs (action) VALUES (?)", ("User created",))
        """
        return self.get_connector(connector_id).transaction()
