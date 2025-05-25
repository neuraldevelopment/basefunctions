"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich
  Project : basefunctions
  Copyright (c) by neuraldevelopment
  All rights reserved.
  Description:
  Central database instance management with unified interface
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
        self.event_bus = None
        self.lock = threading.RLock()  # Reentrant lock for thread safety

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
                except Exception as e:
                    self.logger.warning(f"error closing instance '{name}': {str(e)}")

            if self.event_bus:
                try:
                    self.event_bus.shutdown()
                except Exception as e:
                    self.logger.warning(f"error shutting down EventBus: {str(e)}")

    def configure_eventbus(self, num_threads: int = 5, corelet_pool_size: int = 4) -> None:
        """
        Configure the EventBus for asynchronous database operations.

        parameters
        ----------
        num_threads : int, optional
            number of threads in the pool, default is 5
        corelet_pool_size : int, optional
            number of corelet processes, default is 4
        """
        with self.lock:
            if self.event_bus is None:
                try:
                    from basefunctions.database.eventbus import DbEventBus

                    self.event_bus = DbEventBus(num_threads, corelet_pool_size)
                    self.logger.warning(
                        f"EventBus initialized with {num_threads} threads and {corelet_pool_size} corelets"
                    )
                except Exception as e:
                    self.logger.critical(f"error initializing EventBus: {str(e)}")
                    raise

    def get_event_bus(self) -> Optional[Any]:
        """
        Get the configured EventBus.

        returns
        -------
        Optional[Any]
            EventBus instance or None if not configured
        """
        with self.lock:
            return self.event_bus

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
                    "connected": instance.is_connected(),
                    "type": instance.get_type(),
                    "databases": instance.list_databases() if instance.is_connected() else [],
                }
            return result
