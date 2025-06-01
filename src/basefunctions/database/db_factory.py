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
from typing import Dict, Type, Any, Optional
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
    def create_connector_for_database(
        cls, db_type: str, db_name: str, config: Optional[Dict[str, Any]] = None
    ) -> "basefunctions.DbConnector":
        """
        Create a connector for a specific database using configuration.

        Parameters
        ----------
        db_type : str
            Database type (sqlite3, mysql, postgres)
        db_name : str
            Name of the database
        config : Optional[Dict[str, Any]], optional
            Database instance configuration. If None, loads from ConfigHandler.

        Returns
        -------
        basefunctions.DbConnector
            Configured connector instance for the database

        Raises
        ------
        basefunctions.DbConnectionError
            If connector creation fails
        basefunctions.DbValidationError
            If parameters are invalid
        basefunctions.DbConfigurationError
            If configuration cannot be found
        """
        if not db_type:
            raise basefunctions.DbValidationError("db_type cannot be empty")
        if not db_name:
            raise basefunctions.DbValidationError("db_name cannot be empty")

        # Load config from ConfigHandler if not provided
        if config is None:
            try:
                config_handler = basefunctions.ConfigHandler()
                config = config_handler.get_database_config(db_name)

                if not config:
                    raise basefunctions.DbConfigurationError(
                        f"no configuration found for database instance '{db_name}' in ConfigHandler"
                    )
            except Exception as e:
                raise basefunctions.DbConfigurationError(
                    f"failed to load configuration for database '{db_name}': {str(e)}"
                ) from e

        try:
            connection_config = config.get("connection", {})
            ports = config.get("ports", {})

            # Build DatabaseParameters for the connector interface
            db_parameters = basefunctions.DatabaseParameters()

            # Server connection parameters
            if db_type != "sqlite3":
                db_parameters["host"] = connection_config.get("host", "localhost")
                port = ports.get("db")
                if port is not None:
                    db_parameters["port"] = port

                user = connection_config.get("user")
                if user:
                    db_parameters["user"] = user

                password = connection_config.get("password")
                if password:
                    db_parameters["password"] = password

            # Database-specific parameters
            if db_type == "sqlite3":
                # For SQLite, db_name is the file path
                db_parameters["server_database"] = db_name
            else:
                # For MySQL/PostgreSQL, db_name is the database name
                db_parameters["server_database"] = db_name

            # Optional parameters
            charset = connection_config.get("charset")
            if charset:
                db_parameters["charset"] = charset

            # SSL parameters
            ssl_config = connection_config.get("ssl", {})
            if ssl_config:
                ssl_ca = ssl_config.get("ca")
                if ssl_ca:
                    db_parameters["ssl_ca"] = ssl_ca

                ssl_cert = ssl_config.get("cert")
                if ssl_cert:
                    db_parameters["ssl_cert"] = ssl_cert

                ssl_key = ssl_config.get("key")
                if ssl_key:
                    db_parameters["ssl_key"] = ssl_key

                if "verify" in ssl_config:
                    db_parameters["ssl_verify"] = ssl_config["verify"]

            # Connection pool parameters
            min_connections = connection_config.get("min_connections")
            if min_connections is not None:
                db_parameters["min_connections"] = min_connections

            max_connections = connection_config.get("max_connections")
            if max_connections is not None:
                db_parameters["max_connections"] = max_connections

            # SQLite-specific pragmas
            if db_type == "sqlite3":
                pragmas = connection_config.get("pragmas")
                if pragmas:
                    db_parameters["pragmas"] = pragmas

            # Default schema for PostgreSQL
            if db_type == "postgres":
                default_schema = connection_config.get("default_schema")
                if default_schema:
                    db_parameters["default_schema"] = default_schema

            # Create connector using existing factory method
            connector = cls.create_connector(db_type, db_parameters)

            logger = basefunctions.get_logger(__name__)
            logger.info(f"created connector for database '{db_name}' of type '{db_type}'")

            return connector

        except (
            basefunctions.DbConfigurationError,
            basefunctions.DbValidationError,
            basefunctions.DbFactoryError,
        ):
            # Re-raise specific database errors as-is
            raise
        except Exception as e:
            logger = basefunctions.get_logger(__name__)
            logger.critical(f"failed to create connector for database '{db_name}': {str(e)}")
            raise basefunctions.DbConnectionError(
                f"failed to create connector for database '{db_name}': {str(e)}"
            ) from e

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
