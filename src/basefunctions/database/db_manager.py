"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich
  Project : basefunctions
  Copyright (c) by neuraldevelopment
  All rights reserved.
  Description:
  Central database instance management with simplified interface
 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Dict, Optional, Any
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


class DbManager:
    """
    Central class for managing database instances with simplified access.
    Thread-safe implementation for concurrent environments.
    """

    def __init__(self) -> None:
        """
        Initialize the DbManager and load available configurations.

        raises
        ------
        basefunctions.DbConfigurationError
            if ConfigHandler initialization fails
        """
        self.instances: Dict[str, "basefunctions.DbInstance"] = {}
        self.logger = basefunctions.get_logger(__name__)
        self.lock = threading.RLock()

        try:
            self.config_handler = basefunctions.ConfigHandler()
        except Exception as e:
            self.logger.critical(f"failed to initialize ConfigHandler: {str(e)}")
            raise basefunctions.DbConfigurationError(
                f"failed to initialize ConfigHandler: {str(e)}"
            ) from e

    def get_instance(self, instance_name: str) -> "basefunctions.DbInstance":
        """
        Get a DbInstance for a configured name.
        Creates the instance if it doesn't exist yet.

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

            # Load configuration
            try:
                db_config = self.config_handler.get_database_config(instance_name)
            except Exception as e:
                self.logger.critical(
                    f"failed to load configuration for instance '{instance_name}': {str(e)}"
                )
                raise basefunctions.DbConfigurationError(
                    f"failed to load configuration for instance '{instance_name}': {str(e)}"
                ) from e

            if not db_config:
                self.logger.warning(f"no configuration found for instance '{instance_name}'")
                raise basefunctions.DbConfigurationError(
                    f"no configuration found for database instance '{instance_name}'"
                )

            # Create instance
            try:
                instance = basefunctions.DbInstance(instance_name, db_config)
                instance.set_manager(self)
                self.instances[instance_name] = instance
                self.logger.info(
                    f"created instance '{instance_name}' of type '{db_config.get('type', 'unknown')}'"
                )
                return instance
            except (basefunctions.DbConfigurationError, basefunctions.DbValidationError):
                # Re-raise configuration and validation errors as-is
                raise
            except Exception as e:
                self.logger.critical(f"error creating instance '{instance_name}': {str(e)}")
                raise basefunctions.DbInstanceError(
                    f"error creating instance '{instance_name}': {str(e)}"
                ) from e

    def register_instance(
        self, instance_name: str, config: Dict[str, Any]
    ) -> "basefunctions.DbInstance":
        """
        Register a new database instance with provided configuration.

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
            if instance_name in self.instances:
                self.logger.warning(
                    f"instance '{instance_name}' already registered, will be overwritten"
                )

            try:
                instance = basefunctions.DbInstance(instance_name, config)
                instance.set_manager(self)
                self.instances[instance_name] = instance
                self.logger.info(
                    f"registered instance '{instance_name}' of type '{config.get('type', 'unknown')}'"
                )
                return instance
            except (basefunctions.DbConfigurationError, basefunctions.DbValidationError):
                # Re-raise configuration and validation errors as-is
                raise
            except Exception as e:
                self.logger.critical(f"error registering instance '{instance_name}': {str(e)}")
                raise basefunctions.DbInstanceError(
                    f"error registering instance '{instance_name}': {str(e)}"
                ) from e

    def close_all(self) -> None:
        """
        Close all registered database connections.
        """
        with self.lock:
            for name, instance in self.instances.items():
                try:
                    instance.close()
                    self.logger.info(f"closed instance '{name}'")
                except Exception as e:
                    self.logger.warning(f"error closing instance '{name}': {str(e)}")

            self.instances.clear()
            self.logger.warning("closed all database instances")

    def list_instances(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all registered instances.

        returns
        -------
        Dict[str, Dict[str, Any]]
            dictionary with instance name as key and status information as value
        """
        with self.lock:
            result = {}
            for name, instance in self.instances.items():
                try:
                    instance_config = instance.get_config()
                    connection_config = instance_config.get("connection", {})
                    ports_config = instance_config.get("ports", {})

                    result[name] = {
                        "type": instance.get_type(),
                        "active_databases": instance.list_active_databases(),
                        "database_count": instance.get_database_count(),
                        "config": {
                            "host": connection_config.get("host"),
                            "port": ports_config.get("db"),
                            "user": connection_config.get("user"),
                        },
                    }
                except Exception as e:
                    self.logger.warning(f"error getting info for instance '{name}': {str(e)}")
                    result[name] = {
                        "type": "error",
                        "active_databases": [],
                        "database_count": 0,
                        "config": {},
                        "error": str(e),
                    }
            return result

    def remove_instance(self, instance_name: str) -> bool:
        """
        Remove and close a database instance.

        parameters
        ----------
        instance_name : str
            name of the instance to remove

        returns
        -------
        bool
            True if instance was removed, False if it didn't exist
        """
        if not instance_name:
            return False

        with self.lock:
            if instance_name not in self.instances:
                self.logger.warning(f"instance '{instance_name}' not found for removal")
                return False

            try:
                instance = self.instances[instance_name]
                instance.close()
                del self.instances[instance_name]
                self.logger.info(f"removed instance '{instance_name}'")
                return True
            except Exception as e:
                self.logger.warning(f"error removing instance '{instance_name}': {str(e)}")
                return False

    def get_instance_names(self) -> list[str]:
        """
        Get list of all registered instance names.

        returns
        -------
        list[str]
            list of instance names
        """
        with self.lock:
            return list(self.instances.keys())

    def has_instance(self, instance_name: str) -> bool:
        """
        Check if an instance is registered.

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

        with self.lock:
            return instance_name in self.instances

    def get_total_database_count(self) -> int:
        """
        Get total number of active databases across all instances.

        returns
        -------
        int
            total number of active database connections
        """
        with self.lock:
            total = 0
            for instance in self.instances.values():
                try:
                    total += instance.get_database_count()
                except Exception as e:
                    self.logger.warning(f"error getting database count from instance: {str(e)}")
            return total

    def get_instances_by_type(self, db_type: str) -> Dict[str, "basefunctions.DbInstance"]:
        """
        Get all instances of a specific database type.

        parameters
        ----------
        db_type : str
            database type to filter by (sqlite3, mysql, postgresql)

        returns
        -------
        Dict[str, basefunctions.DbInstance]
            dictionary of instances matching the type
        """
        if not db_type:
            return {}

        with self.lock:
            result = {}
            for name, instance in self.instances.items():
                try:
                    if instance.get_type() == db_type:
                        result[name] = instance
                except Exception as e:
                    self.logger.warning(f"error checking type for instance '{name}': {str(e)}")
            return result

    def get_instance_status(self, instance_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed status information for a specific instance.

        parameters
        ----------
        instance_name : str
            name of the instance

        returns
        -------
        Optional[Dict[str, Any]]
            status information or None if instance doesn't exist
        """
        if not instance_name:
            return None

        with self.lock:
            if instance_name not in self.instances:
                return None

            instance = self.instances[instance_name]
            try:
                return {
                    "name": instance_name,
                    "type": instance.get_type(),
                    "active_databases": instance.list_active_databases(),
                    "database_count": instance.get_database_count(),
                    "config": instance.get_config(),
                    "manager": self.__class__.__name__,
                    "status": "active",
                }
            except Exception as e:
                self.logger.warning(
                    f"error getting status for instance '{instance_name}': {str(e)}"
                )
                return {"name": instance_name, "status": "error", "error": str(e)}

    def reload_instance(self, instance_name: str) -> bool:
        """
        Reload an instance configuration from ConfigHandler.

        parameters
        ----------
        instance_name : str
            name of the instance to reload

        returns
        -------
        bool
            True if instance was reloaded successfully, False otherwise
        """
        if not instance_name:
            return False

        with self.lock:
            try:
                # Close existing instance if it exists
                if instance_name in self.instances:
                    self.instances[instance_name].close()
                    del self.instances[instance_name]

                # Reload from configuration
                self.get_instance(instance_name)
                self.logger.info(f"reloaded instance '{instance_name}'")
                return True
            except Exception as e:
                self.logger.warning(f"error reloading instance '{instance_name}': {str(e)}")
                return False
