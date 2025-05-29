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
    _default_connectors_registered = False

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
            return cls._instance

    @classmethod
    def _register_default_connectors(cls) -> None:
        """
        Register the default set of database connectors with lazy loading.
        Thread-safe implementation prevents double registration.

        raises
        ------
        basefunctions.DbFactoryError
            if connector registration fails
        """
        # Double-checked locking pattern for thread safety
        if cls._default_connectors_registered:
            return

        with cls._lock:
            # Check again inside the lock to prevent race condition
            if cls._default_connectors_registered:
                return

            try:
                # Lazy import to avoid circular dependencies
                # Import from basefunctions.database.connectors submodule
                from basefunctions.database.connectors.sqlite_connector import SQLiteConnector
                from basefunctions.database.connectors.mysql_connector import MySQLConnector
                from basefunctions.database.connectors.postgresql_connector import (
                    PostgreSQLConnector,
                )

                cls._connector_registry[DB_TYPE_SQLITE] = SQLiteConnector
                cls._connector_registry[DB_TYPE_MYSQL] = MySQLConnector
                cls._connector_registry[DB_TYPE_POSTGRESQL] = PostgreSQLConnector

                # Set flag AFTER successful registration to ensure atomicity
                cls._default_connectors_registered = True
                basefunctions.get_logger(__name__).warning(
                    "registered default database connectors"
                )

            except ImportError as e:
                # Ensure flag remains False if registration fails
                cls._default_connectors_registered = False
                basefunctions.get_logger(__name__).critical(
                    f"failed to register default connectors: {str(e)}"
                )
                raise basefunctions.DbFactoryError(
                    f"failed to register default connectors: {str(e)}"
                ) from e

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

        raises
        ------
        basefunctions.DbValidationError
            if parameters are invalid
        """
        if not db_type:
            raise basefunctions.DbValidationError("db_type cannot be empty")
        if not connector_class:
            raise basefunctions.DbValidationError("connector_class cannot be None")

        with cls._lock:
            instance = cls()
            instance._connector_registry[db_type] = connector_class
            basefunctions.get_logger(__name__).warning(f"registered connector for '{db_type}'")

    @classmethod
    def create_connector(
        cls, db_type: str, parameters: "basefunctions.DatabaseParameters"
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
        basefunctions.DbConfigurationError
            if no connector registered for db_type
        basefunctions.DbValidationError
            if parameters are invalid
        basefunctions.DbFactoryError
            if connector creation fails
        """
        if not db_type:
            raise basefunctions.DbValidationError("db_type cannot be empty")
        if not parameters:
            raise basefunctions.DbValidationError("parameters cannot be None")

        with cls._lock:
            instance = cls()

            # Ensure default connectors are registered
            if not cls._default_connectors_registered:
                cls._register_default_connectors()

            if db_type not in instance._connector_registry:
                raise basefunctions.DbConfigurationError(
                    f"no connector registered for database type '{db_type}'"
                )

            try:
                connector_class = instance._connector_registry[db_type]
                connector = connector_class(parameters)
                return connector
            except Exception as e:
                basefunctions.get_logger(__name__).critical(
                    f"failed to create connector for db_type '{db_type}': {str(e)}"
                )
                raise basefunctions.DbFactoryError(
                    f"failed to create connector for db_type '{db_type}': {str(e)}"
                ) from e

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

            # Ensure default connectors are registered
            if not cls._default_connectors_registered:
                cls._register_default_connectors()

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
        if not db_type:
            return False

        with cls._lock:
            instance = cls()

            # Ensure default connectors are registered
            if not cls._default_connectors_registered:
                try:
                    cls._register_default_connectors()
                except basefunctions.DbFactoryError:
                    # If registration fails, we can still check what's available
                    pass

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

            # Ensure default connectors are registered
            if not cls._default_connectors_registered:
                try:
                    cls._register_default_connectors()
                except basefunctions.DbFactoryError:
                    # If registration fails, return whatever is currently registered
                    pass

            return list(instance._connector_registry.keys())

    @classmethod
    def reset_factory(cls) -> None:
        """
        Reset factory state for testing purposes.
        Clears all registered connectors and forces re-registration.
        Thread-safe implementation.
        """
        with cls._lock:
            cls._connector_registry.clear()
            # Use memory barrier to ensure visibility across threads
            cls._default_connectors_registered = False
            basefunctions.get_logger(__name__).warning("factory reset - all connectors cleared")

    @classmethod
    def unregister_connector(cls, db_type: str) -> bool:
        """
        Unregister a connector type.

        parameters
        ----------
        db_type : str
            database type identifier to unregister

        returns
        -------
        bool
            True if connector was unregistered, False if it wasn't registered
        """
        if not db_type:
            return False

        with cls._lock:
            instance = cls()
            if db_type in instance._connector_registry:
                del instance._connector_registry[db_type]
                basefunctions.get_logger(__name__).warning(
                    f"unregistered connector for '{db_type}'"
                )
                return True
            return False
