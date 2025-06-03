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
from typing import Dict, List, Optional, Any
import threading
import subprocess
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
    for creating database-specific connections.
    Supports docker, local, and remote database instances.
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
        self.mode = config.get("mode", "remote")  # default to remote

        # Validate configuration
        if not self.db_type:
            self.logger.critical(f"database type not specified for instance '{instance_name}'")
            raise basefunctions.DbConfigurationError(f"database type not specified for instance '{instance_name}'")

        if self.mode not in ["docker", "local", "remote"]:
            self.logger.critical(f"invalid mode '{self.mode}' for instance '{instance_name}'")
            raise basefunctions.DbConfigurationError(f"invalid mode '{self.mode}' for instance '{instance_name}'")

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
                    self.logger.warning(f"secret '{secret_key}' not found for instance '{self.instance_name}'")

            # Update config with processed values
            self.config["connection"] = connection_config

        except Exception as e:
            self.logger.critical(f"failed to process credentials for instance '{self.instance_name}': {str(e)}")
            raise basefunctions.DbConfigurationError(
                f"failed to process credentials for instance '{self.instance_name}': {str(e)}"
            ) from e

    # =================================================================
    # AVAILABILITY INTERFACE
    # =================================================================

    def is_reachable(self) -> bool:
        """
        Test if database instance is reachable.
        Works for all modes (docker, local, remote).

        returns
        -------
        bool
            True if instance is reachable, False otherwise
        """
        try:
            # Create a test connector to check reachability
            manager = basefunctions.DbManager()
            connector = manager.get_connector(self.instance_name, "postgres")  # Use system DB for test

            # Try to establish connection
            connector.connect()
            is_reachable = connector.is_connected()
            connector.disconnect()

            return is_reachable
        except Exception as e:
            self.logger.debug(f"instance '{self.instance_name}' not reachable: {str(e)}")
            return False

    # =================================================================
    # INSTANCE INFO
    # =================================================================

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
            raise basefunctions.DbInstanceError(f"database type not set for instance '{self.instance_name}'")
        return self.db_type

    def get_config(self) -> Dict[str, Any]:
        """
        Get the instance configuration.

        returns
        -------
        Dict[str, Any]
            instance configuration dictionary
        """
        return self.config.copy()

    def get_status(self) -> Dict[str, Any]:
        """
        Get current status of the instance.

        returns
        -------
        Dict[str, Any]
            status information including reachability, docker status (if applicable), and databases
        """
        status = {"reachable": self.is_reachable(), "databases": self.list_databases()}

        # Add docker status only for docker instances
        if self.mode == "docker":
            status["running"] = self._is_docker_running()

        return status

    def _is_docker_running(self) -> bool:
        """
        Check if docker container is running (only for docker mode).

        returns
        -------
        bool
            True if docker container is running, False otherwise
        """
        if self.mode != "docker":
            return False

        try:
            # Check if container is running
            container_name = f"{self.instance_name}_postgres"  # Assuming postgres naming convention
            result = subprocess.run(
                ["docker", "ps", "--filter", f"name={container_name}", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                check=False,
            )
            return container_name in result.stdout
        except Exception as e:
            self.logger.debug(f"error checking docker status for '{self.instance_name}': {str(e)}")
            return False

    # =================================================================
    # DATABASE MANAGEMENT
    # =================================================================

    def list_databases(self) -> List[str]:
        """
        List all databases on this instance.

        returns
        -------
        List[str]
            list of database names
        """
        try:
            # Create connector to system database for querying available databases
            manager = basefunctions.DbManager()

            # Use appropriate system database based on type
            if self.db_type == "postgresql":
                system_db = "postgres"
            elif self.db_type == "mysql":
                system_db = "mysql"
            elif self.db_type == "sqlite3":
                # SQLite is file-based, return empty list or handle differently
                return []
            else:
                return []

            connector = manager.get_connector(self.instance_name, system_db)
            connector.connect()

            # Query for available databases
            if self.db_type == "postgresql":
                query = "SELECT datname FROM pg_database WHERE datistemplate = false"
                results = connector.query_all(query)
                databases = [row.get("datname") for row in results if row.get("datname")]
            elif self.db_type == "mysql":
                query = "SHOW DATABASES"
                results = connector.query_all(query)
                # MySQL SHOW DATABASES returns different column names
                databases = []
                for row in results:
                    # Get first column value regardless of column name
                    if row:
                        db_name = list(row.values())[0]
                        if db_name not in ["information_schema", "performance_schema", "mysql", "sys"]:
                            databases.append(db_name)
            else:
                databases = []

            connector.disconnect()
            return databases

        except Exception as e:
            self.logger.warning(f"error listing databases for instance '{self.instance_name}': {str(e)}")
            return []

    def get_database(self, db_name: str) -> "basefunctions.Db":
        """
        Get a database by name, creating it if it doesn't exist in cache.

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
                # Create new database object
                database = basefunctions.Db(self.instance_name, db_name)
                self.databases[db_name] = database
                return database
            except Exception as e:
                self.logger.critical(f"failed to get database '{db_name}': {str(e)}")
                raise

    def add_database(self, db_name: str) -> "basefunctions.Db":
        """
        Create a new database on the server and return Db object.

        parameters
        ----------
        db_name : str
            name of the database to create

        returns
        -------
        basefunctions.Db
            database object for the newly created database

        raises
        ------
        basefunctions.DbValidationError
            if db_name is invalid
        basefunctions.DbQueryError
            if database creation fails
        """
        if not db_name:
            raise basefunctions.DbValidationError("db_name cannot be empty")

        try:
            # Create connector to system database for creating new database
            manager = basefunctions.DbManager()

            if self.db_type == "postgresql":
                system_db = "postgres"
                create_query = f'CREATE DATABASE "{db_name}"'
            elif self.db_type == "mysql":
                system_db = "mysql"
                create_query = f"CREATE DATABASE `{db_name}`"
            elif self.db_type == "sqlite3":
                # SQLite databases are created automatically when accessed
                return self.get_database(db_name)
            else:
                raise basefunctions.DbQueryError(f"database creation not supported for type '{self.db_type}'")

            connector = manager.get_connector(self.instance_name, system_db)
            connector.connect()
            connector.execute(create_query)
            connector.disconnect()

            self.logger.info(f"created database '{db_name}' on instance '{self.instance_name}'")

            # Return Db object for the new database
            return self.get_database(db_name)

        except Exception as e:
            self.logger.critical(f"failed to create database '{db_name}': {str(e)}")
            raise basefunctions.DbQueryError(f"failed to create database '{db_name}': {str(e)}") from e

    def remove_database(self, db_name: str) -> bool:
        """
        Remove a database from the server.

        parameters
        ----------
        db_name : str
            name of the database to remove

        returns
        -------
        bool
            True if database was removed, False if it didn't exist
        """
        if not db_name:
            return False

        try:
            # Remove from cache first
            with self.lock:
                if db_name in self.databases:
                    self.databases[db_name].disconnect()
                    del self.databases[db_name]

            # Drop database on server
            manager = basefunctions.DbManager()

            if self.db_type == "postgresql":
                system_db = "postgres"
                drop_query = f'DROP DATABASE IF EXISTS "{db_name}"'
            elif self.db_type == "mysql":
                system_db = "mysql"
                drop_query = f"DROP DATABASE IF EXISTS `{db_name}`"
            elif self.db_type == "sqlite3":
                # SQLite: would need to delete file, skip for now
                return True
            else:
                return False

            connector = manager.get_connector(self.instance_name, system_db)
            connector.connect()
            connector.execute(drop_query)
            connector.disconnect()

            self.logger.info(f"removed database '{db_name}' from instance '{self.instance_name}'")
            return True

        except Exception as e:
            self.logger.warning(f"error removing database '{db_name}': {str(e)}")
            return False

    def remove_databases(self, db_names: List[str]) -> int:
        """
        Remove multiple databases from the server.

        parameters
        ----------
        db_names : List[str]
            list of database names to remove

        returns
        -------
        int
            number of databases successfully removed
        """
        if not db_names:
            return 0

        removed_count = 0
        for db_name in db_names:
            if self.remove_database(db_name):
                removed_count += 1

        return removed_count

    def remove_all_databases(self) -> int:
        """
        Remove all databases from the server.

        returns
        -------
        int
            number of databases removed
        """
        databases = self.list_databases()

        # Filter out system databases
        user_databases = []
        for db_name in databases:
            if self.db_type == "postgresql":
                if db_name not in ["postgres", "template0", "template1"]:
                    user_databases.append(db_name)
            elif self.db_type == "mysql":
                if db_name not in ["information_schema", "performance_schema", "mysql", "sys"]:
                    user_databases.append(db_name)
            else:
                user_databases.append(db_name)

        return self.remove_databases(user_databases)
