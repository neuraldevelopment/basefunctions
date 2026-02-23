"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich

  Project : basefunctions

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  Configuration management with single config file containing multiple package sections

  Log:
  v1.0 : Initial implementation
  v1.1 : Added bootstrap config support to break circular dependency
  v2.0 : Complete redesign with bootstrap-first approach
  v3.0 : Single config.json file with multiple package sections
  v3.1 : Two-phase package structure with custom directories support
  v3.2 : Thread-safe implementation for Event System compatibility
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from __future__ import annotations
from typing import Any
import json
import os
import shutil
import threading
from basefunctions.utils.logging import get_logger, get_logger
import basefunctions

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------
CONFIG_FILENAME = "config.json"

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# LOGGING INITIALIZE
# -------------------------------------------------------------
get_logger(__name__)

# -------------------------------------------------------------
# TYPE DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# EXCEPTION DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# CLASS OR FUNCTION DEFINITIONS
# -------------------------------------------------------------


@basefunctions.singleton
class ConfigHandler:
    """
    Thread-safe singleton for handling JSON-based configuration management with single config file.
    """

    def __init__(self) -> None:
        self.config: dict[str, Any] = {}
        self._lock: threading.RLock = threading.RLock()
        self.logger = get_logger(__name__)

        # Create root structure
        basefunctions.create_root_structure()

    def load_config_file(self, file_path: str) -> None:
        """
        Load a JSON configuration file from specified path.

        Parameters
        ----------
        file_path : str
            Path to the JSON configuration file
        """
        with self._lock:
            if not file_path.endswith(".json"):
                raise ValueError(f"The file '{file_path}' is not a valid JSON file.")

            try:
                with open(file_path, encoding="utf-8") as file:
                    config = json.load(file)
                    if not isinstance(config, dict):
                        raise ValueError(f"Invalid config format in '{file_path}'")
                    self.config.update(config)
                    self.logger.info(f"Loaded config from {file_path}")
            except FileNotFoundError as exc:
                raise FileNotFoundError(f"File not found: '{file_path}'") from exc
            except json.JSONDecodeError as e:
                raise json.JSONDecodeError(f"Error parsing JSON file at '{file_path}': {e}", e.doc, e.pos) from e
            except Exception as exc:
                raise RuntimeError(f"Unexpected error: {exc}") from exc

    def create_config_from_template(self, package_name: str) -> None:
        """
        Create central config.json from template or create empty config if template missing.

        Parameters
        ----------
        package_name : str
            Name of the package (used for path detection)
        """
        with self._lock:
            if not package_name:
                raise ValueError("Package name must be provided.")

            config_path = basefunctions.get_runtime_config_path(package_name)
            config_file = os.path.join(config_path, CONFIG_FILENAME)

            template_path = basefunctions.get_runtime_template_path(package_name)
            template_file = os.path.join(template_path, CONFIG_FILENAME)

            # Create directories
            os.makedirs(config_path, exist_ok=True)
            os.makedirs(template_path, exist_ok=True)

            try:
                # Create template if it doesn't exist
                if not os.path.exists(template_file):
                    empty_config = {package_name: {}}
                    with open(template_file, "w", encoding="utf-8") as file:
                        json.dump(empty_config, file, indent=2)
                    self.logger.info(f"Created empty template for {package_name}")

                # Copy template to config
                shutil.copy2(template_file, config_file)
                self.logger.info(f"Created config for {package_name} from template")

            except Exception as e:
                self.logger.critical(f"Failed to create config for {package_name}: {e}")
                raise

    def load_config_for_package(self, package_name: str) -> None:
        """
        Load the central config.json file for a package context and scan database instances.

        Parameters
        ----------
        package_name : str
            Name of the package (used for path detection)
        """
        with self._lock:
            # Ensure bootstrap package structure exists
            basefunctions.ensure_bootstrap_package_structure(package_name)

            # Get config path using unified system
            config_path = basefunctions.get_runtime_config_path(package_name)
            config_file = os.path.join(config_path, CONFIG_FILENAME)

            # Create config from template if it doesn't exist
            if not os.path.exists(config_file):
                self.create_config_from_template(package_name)

            # Load the config file
            self.load_config_file(config_file)

            # Create full package structure after config is loaded
            self._create_full_package_structure(package_name)

    def _create_full_package_structure(self, package_name: str) -> None:
        """
        Create full package directory structure after config is loaded.

        Parameters
        ----------
        package_name : str
            Name of the package
        """
        try:
            # Get custom directories from config
            custom_dirs = self.get_config_parameter("package_structure/directories")

            # Create full structure with custom or default directories
            basefunctions.create_full_package_structure(package_name, custom_dirs)

            if custom_dirs:
                self.logger.info(
                    f"Created custom package structure for {package_name} with {len(custom_dirs)} directories"
                )
            else:
                self.logger.info(f"Created default package structure for {package_name}")

        except Exception as e:
            self.logger.critical(f"Failed to create full package structure for {package_name}: {e}")
            # Continue execution - this is not critical for basic functionality

    def create_config_for_package(self, package_name: str) -> None:
        """
        Create a central config.json file for a package context.

        Parameters
        ----------
        package_name : str
            Name of the package (used for path detection)
        """
        # Delegate to template-based creation
        self.create_config_from_template(package_name)

    def get_config_for_package(self, package: str | None = None) -> dict[str, Any]:
        """
        Get configuration for a package section or all configurations.

        Parameters
        ----------
        package : Optional[str], optional
            Package name, if None returns all configurations

        Returns
        -------
        dict[str, Any]
            Configuration dictionary
        """
        with self._lock:
            if package is None:
                return self.config.copy()
            return self.config.get(package, {}).copy()

    def get_config_parameter(self, path: str, default_value: Any = None) -> Any:
        """
        Get a configuration parameter by path using slash-separated navigation.

        Parameters
        ----------
        path : str
            Configuration path separated by '/' (e.g., 'basefunctions/logging/level')
        default_value : Any, optional
            Default value if path is not found

        Returns
        -------
        Any
            Configuration parameter value
        """
        with self._lock:
            keys = path.split("/")
            value = self.config

            for key in keys:
                if not isinstance(value, dict):
                    return default_value
                value = value.get(key, default_value)

            return value
