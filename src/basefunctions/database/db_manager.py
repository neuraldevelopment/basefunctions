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
        """
        self.instances: Dict[str, "basefunctions.DbInstance"] = {}
        self.config_handler = basefunctions.ConfigHandler()
        self.logger = basefunctions.get_logger(__name__)
        self.lock = threading.RLock()

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
        ValueError
            if no configuration was found for the instance
        """
        with self.lock:
            if instance_name in self.instances:
                return self.instances[instance_name]

            # Load configuration
            db_config = self.config_handler.get_database_config(instance_name)
            if not db_config:
                self.logger.warning(f"no configuration found for instance '{instance_name}'")
                raise ValueError(f"no configuration found for database instance '{instance_name}'")

            # Create instance
            try:
                instance = basefunctions.DbInstance(instance_name, db_config)
                instance.set_manager(self)
                self.instances[instance_name] = instance
                return instance
            except Exception as e:
                self.logger.critical(f"error creating instance '{instance_name}': {str(e)}")
                raise

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
        """
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
                    f"registered instance '{instance_name}' of type '{config.get('type')}'"
                )
                return instance
            except Exception as e:
                self.logger.critical(f"error registering instance '{instance_name}': {str(e)}")
                raise

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
                result[name] = {
                    "type": instance.get_type(),
                    "active_databases": instance.list_active_databases(),
                    "database_count": instance.get_database_count(),
                    "config": {
                        "host": instance.get_config().get("connection", {}).get("host"),
                        "port": instance.get_config().get("ports", {}).get("db"),
                        "user": instance.get_config().get("connection", {}).get("user"),
                    },
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
            return sum(instance.get_database_count() for instance in self.instances.values())
