"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich
  Project : basefunctions
  Copyright (c) by neuraldevelopment
  All rights reserved.
  Description:
  Central database instance management with Registry-based dynamic connector loading
 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Dict, List, Optional, Any
import os
import json
import threading
import importlib
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
    Central database instance management with Registry-based dynamic connector loading.
    Manages both local Docker instances and remote database connections.
    Thread-safe implementation for concurrent environments.
    """

    def __init__(self) -> None:
        """
        Initialize the DbManager with lazy directory structure creation.

        raises
        ------
        basefunctions.DbConfigurationError
            if initialization fails
        """
        self.instances: Dict[str, "basefunctions.DbInstance"] = {}
        self.logger = basefunctions.get_logger(__name__)
        self.lock = threading.RLock()
        self.registry = basefunctions.get_registry()

        # Lazy initialization flags
        self._directories_ensured = False
        self._docker_manager = None
        self._init_lock = threading.Lock()

    def _ensure_directory_structure(self) -> None:
        """
        Ensure necessary directories exist - only once per instance.

        raises
        ------
        basefunctions.DbConfigurationError
            if directory creation fails
        """
        if self._directories_ensured:
            return

        with self._init_lock:
            if self._directories_ensured:
                return

            try:
                # Create directories using basefunctions
                basefunctions.create_directory(CONFIG_DIR)
                basefunctions.create_directory(INSTANCES_DIR)
                basefunctions.create_directory(TEMPLATE_BASE)

                # Create template subdirectories for each supported database type
                for db_type in self.registry.get_supported_types():
                    if self.registry.has_templates(db_type):
                        template_subdir = os.path.join(TEMPLATE_BASE, "docker", db_type)
                        basefunctions.create_directory(template_subdir)

                self._directories_ensured = True

            except Exception as e:
                self.logger.critical(f"failed to ensure directory structure: {str(e)}")
                raise basefunctions.DbConfigurationError(f"failed to ensure directory structure: {str(e)}") from e

    @property
    def docker_manager(self) -> "basefunctions.DbDockerManager":
        """
        Get DockerManager instance with lazy initialization.

        returns
        -------
        basefunctions.DbDockerManager
            docker manager instance
        """
        if self._docker_manager is None:
            with self._init_lock:
                if self._docker_manager is None:
                    self._docker_manager = basefunctions.DbDockerManager()
        return self._docker_manager

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
        self._ensure_directory_structure()

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

        self._ensure_directory_structure()

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

            self._ensure_directory_structure()

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

        self._ensure_directory_structure()

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
        Get a database connector directly (low-level access) using Registry-based dynamic loading.

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

            # Validate db_type using Registry
            self.registry.validate_db_type(db_type)

            # Build DatabaseParameters for the connector
            db_parameters = basefunctions.DatabaseParameters()
            connection_config = config.get("connection", {})
            ports = config.get("ports", {})

            # Get db_config from Registry
            db_config = self.registry.get_db_config(db_type)

            # Server connection parameters (skip for file-based databases)
            if db_config.get("default_port") is not None:
                db_parameters["host"] = connection_config.get("host", "localhost")
                port = ports.get("db") or db_config.get("default_port")
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
            elif db_type == "redis":
                # Redis doesn't use traditional database names
                if database_name != "default":
                    self.logger.warning(
                        f"Redis instance '{instance_name}' using default database, ignoring '{database_name}'"
                    )
            else:
                # For MySQL/PostgreSQL, database_name is the database name
                db_parameters["server_database"] = database_name

            # Create connector using Registry-based dynamic loading
            connector = self._create_connector_dynamic(db_type, db_parameters)

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

    def _create_connector_dynamic(
        self, db_type: str, db_parameters: "basefunctions.DatabaseParameters"
    ) -> "basefunctions.DbConnector":
        """
        Create database connector using Registry-based dynamic loading.

        parameters
        ----------
        db_type : str
            database type
        db_parameters : basefunctions.DatabaseParameters
            connection parameters

        returns
        -------
        basefunctions.DbConnector
            database connector instance

        raises
        ------
        basefunctions.DbFactoryError
            if connector creation fails
        """
        try:
            # Get connector info from Registry
            connector_class_name, connector_module_path = self.registry.get_connector_info(db_type)

            # Dynamic import of connector module
            try:
                connector_module = importlib.import_module(connector_module_path)
            except ImportError as e:
                raise basefunctions.DbFactoryError(
                    f"failed to import connector module '{connector_module_path}' for {db_type}: {str(e)}"
                ) from e

            # Get connector class from module
            try:
                connector_class = getattr(connector_module, connector_class_name)
            except AttributeError as e:
                raise basefunctions.DbFactoryError(
                    f"connector class '{connector_class_name}' not found in module '{connector_module_path}': {str(e)}"
                ) from e

            # Instantiate connector
            try:
                connector = connector_class(db_parameters)
                return connector
            except Exception as e:
                raise basefunctions.DbFactoryError(
                    f"failed to instantiate connector '{connector_class_name}' for {db_type}: {str(e)}"
                ) from e

        except basefunctions.DbFactoryError:
            # Re-raise factory errors as-is
            raise
        except Exception as e:
            raise basefunctions.DbFactoryError(f"unexpected error creating connector for {db_type}: {str(e)}") from e

    # =================================================================
    # DOCKER LIFECYCLE (Delegation to DbDockerManager)
    # =================================================================

    def create_docker_instance(self, db_type: str, instance_name: str, password: str) -> "basefunctions.DbInstance":
        """
        Create a complete Docker-based database instance using Registry validation.

        parameters
        ----------
        db_type : str
            database type (validated against Registry)
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
            # Validate db_type using Registry before delegating
            self.registry.validate_db_type(db_type)

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
