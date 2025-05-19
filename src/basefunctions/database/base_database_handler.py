"""
=============================================================================

 Licensed Materials, Property of neuraldevelopment , Munich

 Project : basefunctions

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


class BaseDatabaseHandler:
    """
    Central database interface for managing multiple database connectors.
    """

    def __init__(self):
        self.connectors: Dict[str, basefunctions.DatabaseConnector] = {}

    def connect_to_database(
        self, instance_name: str, connect: bool = True
    ) -> basefunctions.DatabaseConnector:
        """
        Connect to a database instance using configuration from ConfigHandler.

        parameters
        ----------
        instance_name : str
            name of the database instance (must exist in config)
        connect : bool, optional
            whether to automatically establish connection, by default True

        returns
        -------
        DatabaseConnector
            configured and optionally connected database connector

        raises
        ------
        ValueError
            if instance is not found or has invalid configuration
        RuntimeError
            if connector creation fails
        """
        # Check if connector already exists
        if instance_name in self.connectors:
            connector = self.connectors[instance_name]
            if connect and not connector.is_connected():
                connector.connect()
            return connector

        # Get database configuration from ConfigHandler
        config_handler = basefunctions.ConfigHandler()
        db_config = config_handler.get_database_config(instance_name)

        if not db_config:
            raise ValueError(f"database instance '{instance_name}' not found in configuration")

        # Extract required fields - no mapping needed now!
        db_type = db_config.get("type")
        if not db_type:
            raise ValueError(f"database type not specified for instance '{instance_name}'")

        connection_config = db_config.get("connection", {})
        ports = db_config.get("ports", {})

        # Create database parameters
        db_parameters = basefunctions.DatabaseParameters(
            database=connection_config.get("database", instance_name),
            user=connection_config.get("user"),
            password=connection_config.get("password"),
            host=connection_config.get("host", "localhost"),
            port=ports.get("db"),
        )

        # Create connector using factory - db_type can be used directly now!
        try:
            connector = basefunctions.DatabaseFactory.create_connector(db_type, db_parameters)

            # Register connector
            self.connectors[instance_name] = connector

            # Connect if requested
            if connect:
                connector.connect()
                basefunctions.get_logger(__name__).info(
                    f"connected to database instance '{instance_name}' ({db_type})"
                )
            else:
                basefunctions.get_logger(__name__).info(
                    f"created connector for database instance '{instance_name}' ({db_type})"
                )

            return connector

        except Exception as e:
            raise RuntimeError(
                f"failed to create connector for instance '{instance_name}': {str(e)}"
            ) from e

    def create_connector(
        self, instance_name: str, db_type: str, parameters: basefunctions.DatabaseParameters
    ) -> basefunctions.DatabaseConnector:
        """
        create a new database connector

        parameters
        ----------
        instance_name : str
            unique identifier for the connector
        db_type : str
            database type (sqlite3, mysql, postgres)
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
            "postgres": basefunctions.PostgreSQLConnector,
        }
        db_type = db_type.lower()
        if db_type not in connector_map:
            raise ValueError(f"unsupported db_type '{db_type}'")
        self.connectors[instance_name] = connector_map[db_type](parameters)
        basefunctions.get_logger(__name__).info(
            f"registered db connector '{instance_name}' ({db_type})"
        )
        return self.connectors[instance_name]

    def get_connector(self, instance_name: str) -> basefunctions.DatabaseConnector:
        """
        get a registered connector by instance name

        parameters
        ----------
        instance_name : str
            instance name identifier

        returns
        -------
        DatabaseConnector
            connector instance

        raises
        ------
        KeyError
            if connector is not registered
        """
        if instance_name not in self.connectors:
            raise KeyError(f"connector '{instance_name}' not registered.")
        return self.connectors[instance_name]

    def connect(self, instance_name: str) -> None:
        """
        connect to database using a registered connector

        parameters
        ----------
        instance_name : str
            instance name identifier
        """
        self.get_connector(instance_name).connect()

    def close(self, instance_name: str) -> None:
        """
        close connection of a registered connector

        parameters
        ----------
        instance_name : str
            instance name identifier
        """
        self.get_connector(instance_name).close()

    def close_all(self) -> None:
        """close all registered connections"""
        for connector in self.connectors.values():
            connector.close()

    def execute(self, instance_name: str, query: str, parameters: tuple = ()) -> None:
        """
        execute a sql query using a registered connector

        parameters
        ----------
        instance_name : str
            instance name identifier
        query : str
            sql query to execute
        parameters : tuple, optional
            query parameters, by default ()
        """
        self.get_connector(instance_name).execute(query, parameters)

    def fetch_one(
        self, instance_name: str, query: str, parameters: tuple = (), new_query: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        fetch a single row using a registered connector

        parameters
        ----------
        instance_name : str
            instance name identifier
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
        return self.get_connector(instance_name).fetch_one(query, parameters, new_query)

    def fetch_all(
        self, instance_name: str, query: str, parameters: tuple = ()
    ) -> List[Dict[str, Any]]:
        """
        fetch all rows using a registered connector

        parameters
        ----------
        instance_name : str
            instance name identifier
        query : str
            sql query to execute
        parameters : tuple, optional
            query parameters, by default ()

        returns
        -------
        List[Dict[str, Any]]
            rows as list of dictionaries
        """
        return self.get_connector(instance_name).fetch_all(query, parameters)

    def begin_transaction(self, instance_name: str) -> None:
        """
        begin a transaction using a registered connector

        parameters
        ----------
        instance_name : str
            instance name identifier
        """
        self.get_connector(instance_name).begin_transaction()

    def commit(self, instance_name: str) -> None:
        """
        commit a transaction using a registered connector

        parameters
        ----------
        instance_name : str
            instance name identifier
        """
        self.get_connector(instance_name).commit()

    def rollback(self, instance_name: str) -> None:
        """
        rollback a transaction using a registered connector

        parameters
        ----------
        instance_name : str
            instance name identifier
        """
        self.get_connector(instance_name).rollback()

    def is_connected(self, instance_name: str) -> bool:
        """
        check if a connector is connected

        parameters
        ----------
        instance_name : str
            instance name identifier

        returns
        -------
        bool
            true if connected, false otherwise
        """
        return self.get_connector(instance_name).is_connected()

    def check_if_table_exists(self, instance_name: str, table_name: str) -> bool:
        """
        check if a table exists using a registered connector

        parameters
        ----------
        instance_name : str
            instance name identifier
        table_name : str
            name of the table to check

        returns
        -------
        bool
            true if table exists, false otherwise
        """
        return self.get_connector(instance_name).check_if_table_exists(table_name)

    def get_connection(self, instance_name: str) -> Any:
        """
        get the underlying connection object of a registered connector

        parameters
        ----------
        instance_name : str
            instance name identifier

        returns
        -------
        Any
            database connection object
        """
        return self.get_connector(instance_name).get_connection()

    def transaction(self, instance_name: str) -> basefunctions.TransactionContextManager:
        """
        get a transaction context manager for a registered connector

        parameters
        ----------
        instance_name : str
            instance name identifier

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
        return self.get_connector(instance_name).transaction()
