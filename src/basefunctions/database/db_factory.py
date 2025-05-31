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
    dynamic connector registration. Pure class-based implementation.
    Thread-safe implementation for concurrent access.
    """

    _lock = threading.RLock()
    _connector_registry: Dict[str, Type["basefunctions.DbConnector"]] = {}
    _initialized = False

    @classmethod
    def _ensure_initialized(cls) -> None:
        """
        Ensure default connectors are registered.
        Thread-safe and idempotent implementation.
        """
        if cls._initialized:
            return

        with cls._lock:
            if cls._initialized:  # Double-check locking
                return

            try:
                # Lazy import to avoid circular dependencies
                from basefunctions.database.connectors.sqlite_connector import SQLiteConnector
                from basefunctions.database.connectors.mysql_connector import MySQLConnector
                from basefunctions.database.connectors.postgresql_connector import PostgreSQLConnector

                cls._connector_registry[DB_TYPE_SQLITE] = SQLiteConnector
                cls._connector_registry[DB_TYPE_MYSQL] = MySQLConnector
                cls._connector_registry[DB_TYPE_POSTGRESQL] = PostgreSQLConnector

                cls._initialized = True

            except ImportError as e:
                raise basefunctions.DbFactoryError(f"failed to register default connectors: {str(e)}") from e

    @classmethod
    def create_connector(
        cls, db_type: str, parameters: "basefunctions.DatabaseParameters"
    ) -> "basefunctions.DbConnector":
        """Create a connector instance for the specified database type."""
        cls._ensure_initialized()  # Ensure registry is populated

        if not db_type:
            raise basefunctions.DbValidationError("db_type cannot be empty")
        if not parameters:
            raise basefunctions.DbValidationError("parameters cannot be None")

        with cls._lock:
            if db_type not in cls._connector_registry:
                raise basefunctions.DbConfigurationError(f"no connector registered for database type '{db_type}'")

            try:
                connector_class = cls._connector_registry[db_type]
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
    def register_connector(cls, db_type: str, connector_class: Type["basefunctions.DbConnector"]) -> None:
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
            cls._connector_registry[db_type] = connector_class

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
            return cls._connector_registry.copy()

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
            return db_type in cls._connector_registry

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
            return list(cls._connector_registry.keys())
