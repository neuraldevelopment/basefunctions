"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment , Munich
  Project : basefunctions
  Copyright (c) by neuraldevelopment
  All rights reserved.
  Description:
  Database instance management handling multiple databases on a server
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
    Represents a connection to a database server with support for
    managing multiple databases within that instance.
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
        self.connection = None
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

    def connect(self) -> None:
        """
        Establish connection to the database server.

        raises
        ------
        DbConnectionError
            if connection cannot be established
        """
        with self.lock:
            if self.is_connected():
                return

            try:
                connection_config = self.config.get("connection", {})
                ports = self.config.get("ports", {})

                # Create database parameters
                db_parameters = {
                    "host": connection_config.get("host", "localhost"),
                    "port": ports.get("db"),
                    "user": connection_config.get("user"),
                    "password": connection_config.get("password"),
                    "database": connection_config.get("database", self.instance_name),
                }

                # Create connection using factory
                self.connection = basefunctions.DbFactory.create_connector(
                    self.db_type, db_parameters
                )

                self.logger.warning(
                    f"connected to instance '{self.instance_name}' ({self.db_type})"
                )
            except Exception as e:
                self.logger.critical(
                    f"failed to connect to instance '{self.instance_name}': {str(e)}"
                )
                raise basefunctions.DbConnectionError(
                    f"failed to connect to instance '{self.instance_name}': {str(e)}"
                ) from e

    def close(self) -> None:
        """
        Close connection to the database server and all database connections.
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

            # Close main connection
            if self.connection:
                try:
                    self.connection.close()
                    self.connection = None
                    self.logger.warning(f"closed connection to instance '{self.instance_name}'")
                except Exception as e:
                    self.logger.warning(f"error closing instance connection: {str(e)}")

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
        DbConnectionError
            if not connected to the instance
        """
        with self.lock:
            if not self.is_connected():
                self.connect()

            if db_name in self.databases:
                return self.databases[db_name]

            try:
                # Create new database object
                database = basefunctions.Db(self, db_name)
                self.databases[db_name] = database
                return database
            except Exception as e:
                self.logger.critical(f"failed to get database '{db_name}': {str(e)}")
                raise

    def list_databases(self) -> List[str]:
        """
        List all available databases on the server.

        returns
        -------
        List[str]
            list of database names

        raises
        ------
        DbConnectionError
            if not connected to the instance
        """
        with self.lock:
            if not self.is_connected():
                self.connect()

            try:
                # SQL query depends on database type
                query_map = {
                    "mysql": "SHOW DATABASES",
                    "postgres": "SELECT datname FROM pg_database WHERE datistemplate = false",
                    "sqlite3": "PRAGMA database_list",
                }

                if self.db_type not in query_map:
                    self.logger.warning(
                        f"unsupported database type '{self.db_type}' for listing databases"
                    )
                    return []

                query = query_map[self.db_type]
                results = self.connection.fetch_all(query)

                # Extract database names based on database type
                if self.db_type == "mysql":
                    return [row.get("Database") for row in results if row.get("Database")]
                elif self.db_type == "postgres":
                    return [row.get("datname") for row in results if row.get("datname")]
                elif self.db_type == "sqlite3":
                    return [row.get("name") for row in results if row.get("name")]

                return []
            except Exception as e:
                self.logger.warning(f"error listing databases: {str(e)}")
                return []

    def create_database(self, db_name: str) -> bool:
        """
        Create a new database.

        parameters
        ----------
        db_name : str
            name of the database to create

        returns
        -------
        bool
            True if database was created successfully, False otherwise

        raises
        ------
        DbConnectionError
            if not connected to the instance
        """
        with self.lock:
            if not self.is_connected():
                self.connect()

            # SQLite doesn't support CREATE DATABASE
            if self.db_type == "sqlite3":
                self.logger.warning("SQLite does not support CREATE DATABASE")
                return False

            try:
                # Escape database name to prevent SQL injection
                safe_db_name = db_name.replace("'", "''")
                query_map = {
                    "mysql": f"CREATE DATABASE `{safe_db_name}`",
                    "postgres": f'CREATE DATABASE "{safe_db_name}"',
                }

                if self.db_type not in query_map:
                    self.logger.warning(
                        f"unsupported database type '{self.db_type}' for creating database"
                    )
                    return False

                query = query_map[self.db_type]
                self.connection.execute(query)
                self.logger.warning(f"created database '{db_name}'")
                return True
            except Exception as e:
                self.logger.warning(f"error creating database '{db_name}': {str(e)}")
                return False

    def drop_database(self, db_name: str) -> bool:
        """
        Drop (delete) a database.

        parameters
        ----------
        db_name : str
            name of the database to drop

        returns
        -------
        bool
            True if database was dropped successfully, False otherwise

        raises
        ------
        DbConnectionError
            if not connected to the instance
        """
        with self.lock:
            if not self.is_connected():
                self.connect()

            # SQLite doesn't support DROP DATABASE
            if self.db_type == "sqlite3":
                self.logger.warning("SQLite does not support DROP DATABASE")
                return False

            # Remove database from cache if it exists
            if db_name in self.databases:
                try:
                    self.databases[db_name].close()
                    del self.databases[db_name]
                except Exception as e:
                    self.logger.warning(f"error closing database '{db_name}': {str(e)}")

            try:
                # Escape database name to prevent SQL injection
                safe_db_name = db_name.replace("'", "''")
                query_map = {
                    "mysql": f"DROP DATABASE `{safe_db_name}`",
                    "postgres": f'DROP DATABASE "{safe_db_name}"',
                }

                if self.db_type not in query_map:
                    self.logger.warning(
                        f"unsupported database type '{self.db_type}' for dropping database"
                    )
                    return False

                query = query_map[self.db_type]
                self.connection.execute(query)
                self.logger.warning(f"dropped database '{db_name}'")
                return True
            except Exception as e:
                self.logger.warning(f"error dropping database '{db_name}': {str(e)}")
                return False

    def is_connected(self) -> bool:
        """
        Check if connected to the database server.

        returns
        -------
        bool
            True if connected, False otherwise
        """
        return self.connection is not None and self.connection.is_connected()

    def get_type(self) -> str:
        """
        Get the database type.

        returns
        -------
        str
            database type (sqlite3, mysql, postgres)
        """
        return self.db_type

    def get_connection(self) -> Any:
        """
        Get the underlying database connection.

        returns
        -------
        Any
            database connection object
        """
        return self.connection

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
