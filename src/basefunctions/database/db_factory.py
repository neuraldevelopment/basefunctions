"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich
  Project : basefunctions
  Copyright (c) by neuraldevelopment
  All rights reserved.
  Description:
  Factory for creating database connectors with dynamic registration
 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Dict, Type, Any
import threading
import basefunctions

# -------------------------------------------------------------
# DEFINITIONS REGISTRY
# -------------------------------------------------------------
DB_TYPE_SQLITE = "sqlite3"
DB_TYPE_MYSQL = "mysql"
DB_TYPE_POSTGRESQL = "postgres"

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


class DbFactory:
    """
    Factory for creating database connectors with support for
    dynamic connector registration. Implements the Singleton pattern.
    Thread-safe implementation for concurrent access.
    """

    _instance = None
    _lock = threading.RLock()
    _connector_registry: Dict[str, Type["basefunctions.DbConnector"]] = {}

    def __new__(cls) -> "DbFactory":
        """
        Singleton implementation for the factory.

        returns
        -------
        DbFactory
            singleton instance
        """
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DbFactory, cls).__new__(cls)
                # Register default connectors
                cls._register_default_connectors()
            return cls._instance

    @classmethod
    def _register_default_connectors(cls) -> None:
        """
        Register the default set of database connectors.
        """
        cls._connector_registry[DB_TYPE_SQLITE] = basefunctions.SQLiteConnector
        cls._connector_registry[DB_TYPE_MYSQL] = basefunctions.MySQLConnector
        cls._connector_registry[DB_TYPE_POSTGRESQL] = basefunctions.PostgreSQLConnector

        basefunctions.get_logger(__name__).warning("registered default database connectors")

    @classmethod
    def register_connector(
        cls, db_type: str, connector_class: Type["basefunctions.DbConnector"]
    ) -> None:
        """
        Register a new connector type.

        parameters
        ----------
        db_type : str
            unique identifier for the database type (sqlite3, mysql, postgres)
        connector_class : Type[basefunctions.DbConnector]
            connector class implementing DbConnector interface
        """
        with cls._lock:
            instance = cls()
            instance._connector_registry[db_type] = connector_class
            basefunctions.get_logger(__name__).warning(f"registered connector for '{db_type}'")

    @classmethod
    def create_connector(
        cls, db_type: str, parameters: basefunctions.DatabaseParameters
    ) -> "basefunctions.DbConnector":
        """
        Create a connector instance for the specified database type.

        parameters
        ----------
        db_type : str
            database type identifier (sqlite3, mysql, postgres)
        parameters : basefunctions.DatabaseParameters
            connection parameters using new DatabaseParameters format

        returns
        -------
        basefunctions.DbConnector
            configured connector instance

        raises
        ------
        ValueError
            if no connector registered for db_type
        """
        with cls._lock:
            instance = cls()

            if db_type not in instance._connector_registry:
                raise ValueError(f"no connector registered for database type '{db_type}'")

            connector_class = instance._connector_registry[db_type]
            connector = connector_class(parameters)
            return connector

    @classmethod
    def get_available_connectors(cls) -> Dict[str, Type["basefunctions.DbConnector"]]:
        """
        Get all registered connector types.

        returns
        -------
        Dict[str, Type[basefunctions.DbConnector]]
            dictionary of registered connector types
        """
        with cls._lock:
            instance = cls()
            return instance._connector_registry.copy()

    @classmethod
    def is_connector_available(cls, db_type: str) -> bool:
        """
        Check if a connector is available for the specified database type.

        parameters
        ----------
        db_type : str
            database type identifier

        returns
        -------
        bool
            True if connector is available, False otherwise
        """
        with cls._lock:
            instance = cls()
            return db_type in instance._connector_registry

    @classmethod
    def get_supported_db_types(cls) -> list[str]:
        """
        Get list of all supported database types.

        returns
        -------
        list[str]
            list of supported database type identifiers
        """
        with cls._lock:
            instance = cls()
            return list(instance._connector_registry.keys())
