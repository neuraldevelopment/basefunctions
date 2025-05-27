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
        ValueError
            if required configuration parameters are missing
        """
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
            raise ValueError(f"database type not specified for instance '{instance_name}'")

        # Process credentials using SecretHandler
        self._process_credentials()

    def _process_credentials(self) -> None:
        """
        Process and enhance credentials with SecretHandler if needed.
        Replace placeholders with actual secrets.
        """
        secret_handler = basefunctions.SecretHandler()
        connection_config = self.config.get("connection", {})

        # Check for password placeholder for replacing with secret value
        password = connection_config.get("password")
        if password and password.startswith("${") and password.endswith("}"):
            # Extract secret key from ${SECRET_KEY} format
            secret_key = password[2:-1]
            actual_password = secret_handler.get_secret_value(secret_key)
            if actual_password:
                connection_config["password"] = actual_password
            else:
                self.logger.warning(
                    f"secret '{secret_key}' not found for instance '{self.instance_name}'"
                )

        # Update config with processed values
        self.config["connection"] = connection_config

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
        """
        with self.lock:
            try:
                connection_config = self.config.get("connection", {})
                ports = self.config.get("ports", {})

                # Build DatabaseParameters for the new connector interface
                db_parameters = basefunctions.DatabaseParameters()

                # Server connection parameters
                if self.db_type != "sqlite3":
                    db_parameters["host"] = connection_config.get("host", "localhost")
                    db_parameters["port"] = ports.get("db")
                    db_parameters["user"] = connection_config.get("user")
                    db_parameters["password"] = connection_config.get("password")

                # Database-specific parameters
                if self.db_type == "sqlite3":
                    # For SQLite, db_name is the file path
                    db_parameters["server_database"] = db_name
                else:
                    # For MySQL/PostgreSQL, db_name is the database name
                    db_parameters["server_database"] = db_name

                # Optional parameters
                if "charset" in connection_config:
                    db_parameters["charset"] = connection_config["charset"]

                # SSL parameters
                ssl_config = connection_config.get("ssl", {})
                if ssl_config:
                    if "ca" in ssl_config:
                        db_parameters["ssl_ca"] = ssl_config["ca"]
                    if "cert" in ssl_config:
                        db_parameters["ssl_cert"] = ssl_config["cert"]
                    if "key" in ssl_config:
                        db_parameters["ssl_key"] = ssl_config["key"]
                    if "verify" in ssl_config:
                        db_parameters["ssl_verify"] = ssl_config["verify"]

                # Connection pool parameters
                if "min_connections" in connection_config:
                    db_parameters["min_connections"] = connection_config["min_connections"]
                if "max_connections" in connection_config:
                    db_parameters["max_connections"] = connection_config["max_connections"]

                # SQLite-specific pragmas
                if self.db_type == "sqlite3" and "pragmas" in connection_config:
                    db_parameters["pragmas"] = connection_config["pragmas"]

                # Default schema for PostgreSQL
                if self.db_type == "postgresql" and "default_schema" in connection_config:
                    db_parameters["default_schema"] = connection_config["default_schema"]

                # Create connector using factory
                connector = basefunctions.DbFactory.create_connector(self.db_type, db_parameters)

                self.logger.info(
                    f"created connector for database '{db_name}' on instance '{self.instance_name}' ({self.db_type})"
                )
                return connector

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
        """
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
        """
        return self.db_type

    def set_manager(self, manager: "basefunctions.DbManager") -> None:
        """
        Set the manager reference for this instance.

        parameters
        ----------
        manager : basefunctions.DbManager
            manager that created this instance
        """
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
