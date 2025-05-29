"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich
  Project : basefunctions
  Copyright (c) by neuraldevelopment
  All rights reserved.
  Description:
  Database instance management as server configuration and database factory
 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Dict, List, Optional, Any, Union
import threading
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


class DbInstance:
    """
    Represents a database server configuration and acts as factory
    for creating database-specific connectors.
    Thread-safe implementation for concurrent access.
    """

    def __init__(self, instance_name: str, config: Dict[str, Any]) -> None:
        """
        Initialize a database instance with the given configuration.

        parameters
        ----------
        instance_name : str
            name of the database instance
        config : Dict[str, Any]
            configuration parameters for the instance

        raises
        ------
        basefunctions.DbConfigurationError
            if required configuration parameters are missing
        basefunctions.DbValidationError
            if parameters are invalid
        """
        if not instance_name:
            raise basefunctions.DbValidationError("instance_name cannot be empty")
        if not config:
            raise basefunctions.DbValidationError("config cannot be None or empty")

        self.instance_name = instance_name
        self.config = config
        self.logger = basefunctions.get_logger(__name__)
        self.lock = threading.RLock()
        self.databases: Dict[str, "basefunctions.Db"] = {}
        self.db_type = config.get("type")
        self.manager = None

        # Validate configuration
        if not self.db_type:
            self.logger.critical(f"database type not specified for instance '{instance_name}'")
            raise basefunctions.DbConfigurationError(
                f"database type not specified for instance '{instance_name}'"
            )

        # Process credentials using SecretHandler
        self._process_credentials()

    def _process_credentials(self) -> None:
        """
        Process and enhance credentials with SecretHandler if needed.
        Replace placeholders with actual secrets.

        raises
        ------
        basefunctions.DbConfigurationError
            if secret processing fails
        """
        try:
            secret_handler = basefunctions.SecretHandler()
            connection_config = self.config.get("connection", {})

            # Check for password placeholder for replacing with secret value
            password = connection_config.get("password")
            if password and password.startswith("${") and password.endswith("}"):
                # Extract secret key from ${SECRET_KEY} format
                secret_key = password[2:-1]
                if not secret_key:
                    raise basefunctions.DbConfigurationError(
                        f"empty secret key in password placeholder for instance '{self.instance_name}'"
                    )

                actual_password = secret_handler.get_secret_value(secret_key)
                if actual_password:
                    connection_config["password"] = actual_password
                else:
                    self.logger.warning(
                        f"secret '{secret_key}' not found for instance '{self.instance_name}'"
                    )

            # Update config with processed values
            self.config["connection"] = connection_config

        except Exception as e:
            self.logger.critical(
                f"failed to process credentials for instance '{self.instance_name}': {str(e)}"
            )
            raise basefunctions.DbConfigurationError(
                f"failed to process credentials for instance '{self.instance_name}': {str(e)}"
            ) from e

    def create_connector_for_database(self, db_name: str) -> "basefunctions.DbConnector":
        """
        Create a connector for a specific database.

        parameters
        ----------
        db_name : str
            name of the database

        returns
        -------
        basefunctions.DbConnector
            configured connector instance for the database

        raises
        ------
        basefunctions.DbConnectionError
            if connector creation fails
        basefunctions.DbValidationError
            if db_name is invalid
        """
        if not db_name:
            raise basefunctions.DbValidationError("db_name cannot be empty")

        with self.lock:
            try:
                connection_config = self.config.get("connection", {})
                ports = self.config.get("ports", {})

                # Build DatabaseParameters for the new connector interface
                db_parameters = basefunctions.DatabaseParameters()

                # Server connection parameters
                if self.db_type != "sqlite3":
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
                if self.db_type == "sqlite3":
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
                if self.db_type == "sqlite3":
                    pragmas = connection_config.get("pragmas")
                    if pragmas:
                        db_parameters["pragmas"] = pragmas

                # Default schema for PostgreSQL
                if self.db_type == "postgresql":
                    default_schema = connection_config.get("default_schema")
                    if default_schema:
                        db_parameters["default_schema"] = default_schema

                # Create connector using factory
                connector = basefunctions.DbFactory.create_connector(self.db_type, db_parameters)

                self.logger.info(
                    f"created connector for database '{db_name}' on instance '{self.instance_name}' ({self.db_type})"
                )
                return connector

            except (
                basefunctions.DbConfigurationError,
                basefunctions.DbValidationError,
                basefunctions.DbFactoryError,
            ):
                # Re-raise configuration and validation errors as-is
                raise
            except Exception as e:
                self.logger.critical(
                    f"failed to create connector for database '{db_name}' on instance '{self.instance_name}': {str(e)}"
                )
                raise basefunctions.DbConnectionError(
                    f"failed to create connector for database '{db_name}': {str(e)}"
                ) from e

    def close(self) -> None:
        """
        Close all database connections managed by this instance.
        """
        with self.lock:
            # Close all database connections
            for db_name, database in self.databases.items():
                try:
                    database.close()
                except Exception as e:
                    self.logger.warning(f"error closing database '{db_name}': {str(e)}")

            # Clear database cache
            self.databases.clear()
            self.logger.warning(f"closed all connections for instance '{self.instance_name}'")

    def get_database(self, db_name: str) -> "basefunctions.Db":
        """
        Get a database by name, creating it if it doesn't exist.

        parameters
        ----------
        db_name : str
            name of the database to get

        returns
        -------
        basefunctions.Db
            database object

        raises
        ------
        basefunctions.DbConnectionError
            if database creation fails
        basefunctions.DbValidationError
            if db_name is invalid
        """
        if not db_name:
            raise basefunctions.DbValidationError("db_name cannot be empty")

        with self.lock:
            if db_name in self.databases:
                return self.databases[db_name]

            try:
                # Create new database object - it will create its own connector
                database = basefunctions.Db(self, db_name)
                self.databases[db_name] = database
                return database
            except Exception as e:
                self.logger.critical(f"failed to get database '{db_name}': {str(e)}")
                raise

    def get_type(self) -> str:
        """
        Get the database type.

        returns
        -------
        str
            database type (sqlite3, mysql, postgresql)

        raises
        ------
        basefunctions.DbInstanceError
            if database type is not set
        """
        if not self.db_type:
            raise basefunctions.DbInstanceError(
                f"database type not set for instance '{self.instance_name}'"
            )
        return self.db_type

    def set_manager(self, manager: "basefunctions.DbManager") -> None:
        """
        Set the manager reference for this instance.

        parameters
        ----------
        manager : basefunctions.DbManager
            manager that created this instance

        raises
        ------
        basefunctions.DbValidationError
            if manager is None
        """
        if not manager:
            raise basefunctions.DbValidationError("manager cannot be None")
        self.manager = manager

    def get_manager(self) -> Optional["basefunctions.DbManager"]:
        """
        Get the manager reference for this instance.

        returns
        -------
        Optional[basefunctions.DbManager]
            manager that created this instance or None
        """
        return self.manager

    def get_config(self) -> Dict[str, Any]:
        """
        Get the instance configuration.

        returns
        -------
        Dict[str, Any]
            instance configuration dictionary
        """
        return self.config.copy()

    def list_active_databases(self) -> List[str]:
        """
        List all currently active (cached) databases.

        returns
        -------
        List[str]
            list of active database names
        """
        with self.lock:
            return list(self.databases.keys())

    def get_database_count(self) -> int:
        """
        Get the number of active database connections.

        returns
        -------
        int
            number of active databases
        """
        with self.lock:
            return len(self.databases)

    def is_database_active(self, db_name: str) -> bool:
        """
        Check if a database is currently active (cached).

        parameters
        ----------
        db_name : str
            name of the database to check

        returns
        -------
        bool
            True if database is active, False otherwise
        """
        if not db_name:
            return False

        with self.lock:
            return db_name in self.databases

    def remove_database(self, db_name: str) -> bool:
        """
        Remove and close a specific database connection.

        parameters
        ----------
        db_name : str
            name of the database to remove

        returns
        -------
        bool
            True if database was removed, False if it wasn't active
        """
        if not db_name:
            return False

        with self.lock:
            if db_name not in self.databases:
                return False

            try:
                database = self.databases[db_name]
                database.close()
                del self.databases[db_name]
                self.logger.info(
                    f"removed database '{db_name}' from instance '{self.instance_name}'"
                )
                return True
            except Exception as e:
                self.logger.warning(f"error removing database '{db_name}': {str(e)}")
                return False
