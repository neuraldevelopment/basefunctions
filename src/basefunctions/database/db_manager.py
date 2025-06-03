"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich
  Project : basefunctions
  Copyright (c) by neuraldevelopment
  All rights reserved.
  Description:
  Central database instance management with DbDockerManager integration
 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Dict, List, Optional, Any
import os
import json
import threading
import basefunctions

# -------------------------------------------------------------
# DEFINITIONS REGISTRY
# -------------------------------------------------------------
DB_BASE = os.path.expanduser("~/.databases")
CONFIG_DIR = os.path.join(DB_BASE, "config")
INSTANCES_DIR = os.path.join(DB_BASE, "instances")
TEMPLATE_BASE = os.path.join(DB_BASE, "templates")

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


class DbManager:
    """
    Central database instance management with DbDockerManager integration.
    Manages both local Docker instances and remote database connections.
    Thread-safe implementation for concurrent environments.
    """

    def __init__(self) -> None:
        """
        Initialize the DbManager and ensure directory structure exists.

        raises
        ------
        basefunctions.DbConfigurationError
            if initialization fails
        """
        self.instances: Dict[str, "basefunctions.DbInstance"] = {}
        self.logger = basefunctions.get_logger(__name__)
        self.lock = threading.RLock()

        # Initialize DbDockerManager for Docker operations
        self.docker_manager = basefunctions.DbDockerManager()

        # Ensure database directory structure exists
        self._ensure_directory_structure()

    def _ensure_directory_structure(self) -> None:
        """
        Ensure necessary directories exist.

        raises
        ------
        basefunctions.DbConfigurationError
            if directory creation fails
        """
        try:
            # Create directories using basefunctions
            basefunctions.create_directory(CONFIG_DIR)
            basefunctions.create_directory(INSTANCES_DIR)
            basefunctions.create_directory(TEMPLATE_BASE)

            # Create template subdirectories for each database type
            for db_type in ["postgres", "mysql", "sqlite3"]:
                template_subdir = os.path.join(TEMPLATE_BASE, "docker", db_type)
                basefunctions.create_directory(template_subdir)

        except Exception as e:
            self.logger.critical(f"failed to ensure directory structure: {str(e)}")
            raise basefunctions.DbConfigurationError(f"failed to ensure directory structure: {str(e)}") from e

    # =================================================================
    # CORE MANAGEMENT
    # =================================================================

    def list_instances(self) -> List[str]:
        """
        Scan ~/.databases/instances/ for all available database instances.

        returns
        -------
        List[str]
            list of instance names
        """
        try:
            if not basefunctions.check_if_dir_exists(INSTANCES_DIR):
                return []

            # Get all directories in instances directory
            instances = []
            for item in os.listdir(INSTANCES_DIR):
                item_path = os.path.join(INSTANCES_DIR, item)
                if basefunctions.check_if_dir_exists(item_path):
                    instances.append(item)

            return sorted(instances)

        except Exception as e:
            self.logger.warning(f"error listing instances: {str(e)}")
            return []

    def has_instance(self, instance_name: str) -> bool:
        """
        Check if an instance exists.

        parameters
        ----------
        instance_name : str
            name of the instance to check

        returns
        -------
        bool
            True if instance exists, False otherwise
        """
        if not instance_name:
            return False

        instance_path = os.path.join(INSTANCES_DIR, instance_name)
        return basefunctions.check_if_dir_exists(instance_path)

    def get_instance(self, instance_name: str) -> "basefunctions.DbInstance":
        """
        Get a DbInstance, creating it if it doesn't exist in cache.

        parameters
        ----------
        instance_name : str
            name of the database instance

        returns
        -------
        basefunctions.DbInstance
            configured database instance

        raises
        ------
        basefunctions.DbConfigurationError
            if no configuration was found for the instance
        basefunctions.DbValidationError
            if instance_name is invalid
        basefunctions.DbInstanceError
            if instance creation fails
        """
        if not instance_name:
            raise basefunctions.DbValidationError("instance_name cannot be empty")

        with self.lock:
            if instance_name in self.instances:
                return self.instances[instance_name]

            # Load configuration from instance directory
            try:
                config = self._load_instance_config(instance_name)
            except Exception as e:
                self.logger.critical(f"failed to load configuration for instance '{instance_name}': {str(e)}")
                raise basefunctions.DbConfigurationError(
                    f"failed to load configuration for instance '{instance_name}': {str(e)}"
                ) from e

            if not config:
                raise basefunctions.DbConfigurationError(
                    f"no configuration found for database instance '{instance_name}'"
                )

            # Create instance
            try:
                instance = basefunctions.DbInstance(instance_name, config)
                self.instances[instance_name] = instance
                self.logger.info(f"created instance '{instance_name}' of type '{config.get('type', 'unknown')}'")
                return instance
            except (basefunctions.DbConfigurationError, basefunctions.DbValidationError):
                # Re-raise configuration and validation errors as-is
                raise
            except Exception as e:
                self.logger.critical(f"error creating instance '{instance_name}': {str(e)}")
                raise basefunctions.DbInstanceError(f"error creating instance '{instance_name}': {str(e)}") from e

    def add_instance(self, instance_name: str, config: Dict[str, Any]) -> "basefunctions.DbInstance":
        """
        Register a remote database instance with provided configuration.

        parameters
        ----------
        instance_name : str
            name of the database instance
        config : Dict[str, Any]
            configuration parameters for the instance

        returns
        -------
        basefunctions.DbInstance
            configured database instance

        raises
        ------
        basefunctions.DbValidationError
            if parameters are invalid
        basefunctions.DbInstanceError
            if instance creation fails
        """
        if not instance_name:
            raise basefunctions.DbValidationError("instance_name cannot be empty")
        if not config:
            raise basefunctions.DbValidationError("config cannot be None or empty")

        with self.lock:
            try:
                # Create instance
                instance = basefunctions.DbInstance(instance_name, config)
                self.instances[instance_name] = instance

                # Save configuration to instance directory
                self._save_instance_config(instance_name, config)

                self.logger.info(f"registered instance '{instance_name}' of type '{config.get('type', 'unknown')}'")
                return instance
            except (basefunctions.DbConfigurationError, basefunctions.DbValidationError):
                # Re-raise configuration and validation errors as-is
                raise
            except Exception as e:
                self.logger.critical(f"error registering instance '{instance_name}': {str(e)}")
                raise basefunctions.DbInstanceError(f"error registering instance '{instance_name}': {str(e)}") from e

    # =================================================================
    # DIRECT ACCESS
    # =================================================================

    def get_database(self, instance_name: str, database_name: str) -> "basefunctions.Db":
        """
        Get a database directly without going through DbInstance.

        parameters
        ----------
        instance_name : str
            name of the database instance
        database_name : str
            name of the database

        returns
        -------
        basefunctions.Db
            database object

        raises
        ------
        basefunctions.DbValidationError
            if parameters are invalid
        basefunctions.DbConnectionError
            if database creation fails
        """
        if not instance_name:
            raise basefunctions.DbValidationError("instance_name cannot be empty")
        if not database_name:
            raise basefunctions.DbValidationError("database_name cannot be empty")

        try:
            return basefunctions.Db(instance_name, database_name)
        except Exception as e:
            self.logger.critical(f"failed to get database '{instance_name}.{database_name}': {str(e)}")
            raise basefunctions.DbConnectionError(
                f"failed to get database '{instance_name}.{database_name}': {str(e)}"
            ) from e

    def get_connector(self, instance_name: str, database_name: str) -> "basefunctions.DbConnector":
        """
        Get a database connector directly (low-level access).

        parameters
        ----------
        instance_name : str
            name of the database instance
        database_name : str
            name of the database

        returns
        -------
        basefunctions.DbConnector
            database connector

        raises
        ------
        basefunctions.DbValidationError
            if parameters are invalid
        basefunctions.DbConnectionError
            if connector creation fails
        """
        if not instance_name:
            raise basefunctions.DbValidationError("instance_name cannot be empty")
        if not database_name:
            raise basefunctions.DbValidationError("database_name cannot be empty")

        try:
            # Load config and determine db_type
            config = self._load_instance_config(instance_name)
            if not config:
                raise basefunctions.DbConfigurationError(f"no configuration found for instance '{instance_name}'")

            db_type = config.get("type")
            if not db_type:
                raise basefunctions.DbConfigurationError(
                    f"database type not specified in configuration for '{instance_name}'"
                )

            # Build DatabaseParameters for the connector
            db_parameters = basefunctions.DatabaseParameters()
            connection_config = config.get("connection", {})
            ports = config.get("ports", {})

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
                # For SQLite, database_name is the file path
                db_parameters["server_database"] = database_name
            else:
                # For MySQL/PostgreSQL, database_name is the database name
                db_parameters["server_database"] = database_name

            # Create connector using factory pattern
            if db_type == "postgresql":
                from basefunctions.database.connectors.postgresql_connector import PostgreSQLConnector

                connector = PostgreSQLConnector(db_parameters)
            elif db_type == "mysql":
                from basefunctions.database.connectors.mysql_connector import MySQLConnector

                connector = MySQLConnector(db_parameters)
            elif db_type == "sqlite3":
                from basefunctions.database.connectors.sqlite_connector import SQLiteConnector

                connector = SQLiteConnector(db_parameters)
            else:
                raise basefunctions.DbFactoryError(f"unsupported database type: {db_type}")

            self.logger.debug(f"created connector for '{instance_name}.{database_name}' (type: {db_type})")
            return connector

        except (
            basefunctions.DbConfigurationError,
            basefunctions.DbValidationError,
            basefunctions.DbFactoryError,
        ):
            # Re-raise specific database errors as-is
            raise
        except Exception as e:
            self.logger.critical(f"failed to create connector for '{instance_name}.{database_name}': {str(e)}")
            raise basefunctions.DbConnectionError(
                f"failed to create connector for '{instance_name}.{database_name}': {str(e)}"
            ) from e

    # =================================================================
    # DOCKER LIFECYCLE (Delegation to DbDockerManager)
    # =================================================================

    def create_docker_instance(self, db_type: str, instance_name: str, password: str) -> "basefunctions.DbInstance":
        """
        Create a complete Docker-based database instance.

        parameters
        ----------
        db_type : str
            database type (postgres, mysql, sqlite3)
        instance_name : str
            name for the new instance
        password : str
            database password

        returns
        -------
        basefunctions.DbInstance
            created database instance

        raises
        ------
        basefunctions.DbValidationError
            if parameters are invalid
        basefunctions.DbInstanceError
            if instance creation fails
        """
        try:
            # Delegate to DbDockerManager
            instance = self.docker_manager.create_instance(db_type, instance_name, password)

            # Cache the instance
            with self.lock:
                self.instances[instance_name] = instance

            return instance
        except Exception as e:
            self.logger.critical(f"failed to create Docker instance '{instance_name}': {str(e)}")
            raise

    def delete_docker_instance(self, instance_name: str) -> bool:
        """
        Delete a Docker instance completely.

        parameters
        ----------
        instance_name : str
            name of the instance to delete

        returns
        -------
        bool
            True if instance was deleted, False if it didn't exist
        """
        try:
            # Remove from cache first
            with self.lock:
                if instance_name in self.instances:
                    del self.instances[instance_name]

            # Delegate to DbDockerManager
            return self.docker_manager.delete_instance(instance_name)
        except Exception as e:
            self.logger.warning(f"error deleting Docker instance '{instance_name}': {str(e)}")
            return False

    def start_docker_instance(self, instance_name: str) -> bool:
        """
        Start a Docker instance.

        parameters
        ----------
        instance_name : str
            name of the instance to start

        returns
        -------
        bool
            True if instance was started, False otherwise
        """
        return self.docker_manager.start_instance(instance_name)

    def stop_docker_instance(self, instance_name: str) -> bool:
        """
        Stop a Docker instance.

        parameters
        ----------
        instance_name : str
            name of the instance to stop

        returns
        -------
        bool
            True if instance was stopped, False otherwise
        """
        return self.docker_manager.stop_instance(instance_name)

    # =================================================================
    # PRIVATE HELPER METHODS
    # =================================================================

    def _load_instance_config(self, instance_name: str) -> Optional[Dict[str, Any]]:
        """
        Load instance configuration from instance directory.

        parameters
        ----------
        instance_name : str
            name of the instance

        returns
        -------
        Optional[Dict[str, Any]]
            configuration dictionary or None if not found
        """
        instance_config_file = os.path.join(INSTANCES_DIR, instance_name, "config.json")
        if basefunctions.check_if_file_exists(instance_config_file):
            try:
                with open(instance_config_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"failed to load instance config file: {str(e)}")

        return None

    def _save_instance_config(self, instance_name: str, config: Dict[str, Any]) -> None:
        """
        Save instance configuration to instance directory.

        parameters
        ----------
        instance_name : str
            name of the instance
        config : Dict[str, Any]
            configuration to save

        raises
        ------
        basefunctions.DbConfigurationError
            if saving fails
        """
        try:
            instance_dir = os.path.join(INSTANCES_DIR, instance_name)
            basefunctions.create_directory(instance_dir)

            instance_config_file = os.path.join(instance_dir, "config.json")
            with open(instance_config_file, "w") as f:
                json.dump(config, f, indent=2)

        except Exception as e:
            self.logger.critical(f"failed to save instance config: {str(e)}")
            raise basefunctions.DbConfigurationError(f"failed to save instance config: {str(e)}") from e
