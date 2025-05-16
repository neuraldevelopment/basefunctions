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
from typing import Dict, Type
import basefunctions

# -------------------------------------------------------------
# DEFINITIONS REGISTRY
# -------------------------------------------------------------
DB_TYPE_SQLITE = "sqlite3"
DB_TYPE_MYSQL = "mysql"
DB_TYPE_POSTGRESQL = "postgresql"

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------


# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------
class DatabaseFactory:
    """
    Factory for creating database connectors with support for dynamic connector registration.
    """

    _instance = None
    _connector_registry: Dict[str, Type["basefunctions.DatabaseConnector"]] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseFactory, cls).__new__(cls)
            # Register default connectors
            cls._instance._connector_registry[DB_TYPE_SQLITE] = basefunctions.SQLiteConnector
            cls._instance._connector_registry[DB_TYPE_MYSQL] = basefunctions.MySQLConnector
            cls._instance._connector_registry[DB_TYPE_POSTGRESQL] = (
                basefunctions.PostgreSQLConnector
            )
        return cls._instance

    @classmethod
    def register_connector(
        cls, db_type: str, connector_class: Type["basefunctions.DatabaseConnector"]
    ) -> None:
        """
        register a new connector type

        parameters
        ----------
        db_type : str
            unique identifier for the database type
        connector_class : Type[DatabaseConnector]
            connector class implementing DatabaseConnector interface
        """
        instance = cls()
        instance._connector_registry[db_type] = connector_class
        basefunctions.get_logger(__name__).debug(f"registered connector for '{db_type}'")

    @classmethod
    def create_connector(
        cls, db_type: str, parameters: "basefunctions.DatabaseParameters"
    ) -> "basefunctions.DatabaseConnector":
        """
        create a connector instance for the specified database type

        parameters
        ----------
        db_type : str
            database type identifier
        parameters : DatabaseParameters
            connection parameters

        returns
        -------
        DatabaseConnector
            configured connector instance
        """
        instance = cls()

        if db_type not in instance._connector_registry:
            raise ValueError(f"no connector registered for database type '{db_type}'")

        connector_class = instance._connector_registry[db_type]
        connector = connector_class(parameters)
        return connector

    @classmethod
    def get_available_connectors(cls) -> Dict[str, Type["basefunctions.DatabaseConnector"]]:
        """
        get all registered connector types

        returns
        -------
        Dict[str, Type[DatabaseConnector]]
            dictionary of registered connector types
        """
        instance = cls()
        return instance._connector_registry.copy()
