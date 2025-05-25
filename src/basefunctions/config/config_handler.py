"""
=============================================================================

  Licensed Materials, Property of neuraldevelopment, Munich

  Project : basefunctions

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  a simple framework for base functionalities in python

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Any, Optional, Dict
from pathlib import Path
import json
import os
import basefunctions

# -------------------------------------------------------------
# DEFINITIONS REGISTRY
# -------------------------------------------------------------

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------
DEFAULT_PATHNAME = ".config"
DATABASES_BASE_PATH = "~/.databases/instances"

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------


# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------
@basefunctions.singleton
class ConfigHandler:
    """
    Singleton for handling JSON-based configuration management with database instance integration.
    """

    def __init__(self):
        self.config = {}
        self.logger = basefunctions.get_logger(__name__)

    def load_config(self, file_path: str) -> None:
        """
        Load a JSON configuration file.

        Parameters
        ----------
        file_path : str
            Path to the JSON configuration file
        """
        if not file_path.endswith(".json"):
            raise ValueError(f"The file '{file_path}' is not a valid JSON file.")

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                config = json.load(file)
                if not isinstance(config, dict):
                    raise ValueError(f"Invalid config format in '{file_path}'")
                self.config.update(config)
                self.logger.info(f"Loaded config from {file_path}")
        except FileNotFoundError as exc:
            raise FileNotFoundError(f"File not found: '{file_path}'") from exc
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Error parsing JSON file at '{file_path}': {e}", e.doc, e.pos
            ) from e
        except Exception as exc:
            raise RuntimeError(f"Unexpected error: {exc}") from exc

    def load_default_config(self, package_name: str) -> None:
        """
        Load the default configuration file for a package and scan database instances.

        Parameters
        ----------
        package_name : str
            Name of the package
        """
        file_name = (
            Path(basefunctions.get_home_path())
            / DEFAULT_PATHNAME
            / package_name
            / f"{package_name}.json"
        )
        if not basefunctions.check_if_file_exists(file_name):
            self.create_default_config(package_name)
        self.load_config(str(file_name))

        # Load database configurations
        self.load_database_configs()

    def create_default_config(self, package_name: str) -> None:
        """
        Create a default configuration file for a package.

        Parameters
        ----------
        package_name : str
            Name of the package
        """
        if not package_name:
            raise ValueError("Package name must be provided.")

        config_directory = Path(basefunctions.get_home_path()) / DEFAULT_PATHNAME / package_name
        basefunctions.create_directory(config_directory)

        with open(config_directory / f"{package_name}.json", "w", encoding="utf-8") as file:
            json.dump({package_name: {}}, file, indent=2)

    def scan_database_instances(self) -> None:
        """
        Scan all database instances and load their configurations.
        """
        databases_path = Path(os.path.expanduser(DATABASES_BASE_PATH))

        if not databases_path.exists():
            self.logger.debug("Database instances directory not found")
            return

        database_configs = {}

        for instance_dir in databases_path.iterdir():
            if not instance_dir.is_dir():
                continue

            instance_name = instance_dir.name
            config_file = instance_dir / "config" / "instance.json"

            if config_file.exists():
                try:
                    with open(config_file, "r", encoding="utf-8") as f:
                        instance_config = json.load(f)
                        database_configs[instance_name] = instance_config
                        self.logger.debug(f"Loaded database config for instance: {instance_name}")
                except Exception as e:
                    self.logger.warning(f"Failed to load config for instance {instance_name}: {e}")
            else:
                self.logger.debug(f"No config file found for instance: {instance_name}")

        # Store database configs in main config
        if database_configs:
            self.config["databases"] = database_configs
            self.logger.info(f"Loaded {len(database_configs)} database instance configurations")

    def load_database_configs(self) -> None:
        """
        Load all database instance configurations.
        """
        self.scan_database_instances()

    def get_database_config(self, instance_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific database instance.

        Parameters
        ----------
        instance_name : str
            Name of the database instance

        Returns
        -------
        Dict[str, Any]
            Configuration dictionary for the instance
        """
        databases = self.config.get("databases", {})
        if instance_name not in databases:
            self.logger.warning(f"Database instance '{instance_name}' not found in config")
            return {}

        return databases[instance_name]

    def get_config_value(self, path: str, default_value: Any = None) -> Any:
        """
        Get a configuration value by path.

        Parameters
        ----------
        path : str
            Configuration path separated by '/'
        default_value : Any, optional
            Default value if path is not found

        Returns
        -------
        Any
            Configuration value
        """
        keys = path.split("/")
        value = self.config

        for key in keys:
            if not isinstance(value, dict):
                return default_value
            value = value.get(key, default_value)

        return value

    def get_config(self, package: Optional[str] = None) -> dict:
        """
        Get configuration for a package or all configurations.

        Parameters
        ----------
        package : Optional[str], optional
            Package name, if None returns all configurations

        Returns
        -------
        dict
            Configuration dictionary
        """
        if package is None:
            return self.config
        return self.config.get(package, {})

    def list_available_paths(self) -> list[str]:
        """
        List all available configuration paths.

        Returns
        -------
        list[str]
            List of configuration paths
        """
        paths = []

        def _walk(d: dict, parent_key: str = ""):
            if not isinstance(d, dict):
                return
            for key, value in d.items():
                full_key = f"{parent_key}/{key}" if parent_key else key
                paths.append(full_key)
                _walk(value, full_key)

        _walk(self.config)
        return paths
