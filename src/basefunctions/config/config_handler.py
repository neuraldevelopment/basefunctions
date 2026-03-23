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
  v3.3 : Logging audit - critical→error, add warning before raises, remove duplicate import
  v3.4 : App-controlled config loading — remove deprecated methods (load_config_for_package, create_config_for_package, create_config_from_template, _create_full_package_structure)
  v3.5 : Add register_package_defaults + _deep_merge for proper nested config merging
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from __future__ import annotations
from pathlib import Path
from typing import Any
import json
import threading
from basefunctions.utils.logging import get_logger
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


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """
    Recursively merge override into base dict, with override taking precedence.

    For dict values at the same key, recurse. For all other values, override wins.

    Parameters
    ----------
    base : dict[str, Any]
        Base configuration dict
    override : dict[str, Any]
        Override configuration dict (wins on conflict)

    Returns
    -------
    dict[str, Any]
        Merged configuration dict (new object, base is not mutated)
    """
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


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
                self.logger.warning("Invalid config file path '%s': must be a .json file", file_path)
                raise ValueError(f"The file '{file_path}' is not a valid JSON file.")

            try:
                with open(file_path, encoding="utf-8") as file:
                    config = json.load(file)
                    if not isinstance(config, dict):
                        self.logger.warning("Invalid config format in '%s': expected dict, got %s", file_path, type(config).__name__)
                        raise ValueError(f"Invalid config format in '{file_path}'")
                    self.config = _deep_merge(self.config, config)
                    self.logger.info("Loaded config from %s", file_path)
            except FileNotFoundError as exc:
                raise FileNotFoundError(f"File not found: '{file_path}'") from exc
            except json.JSONDecodeError as e:
                raise json.JSONDecodeError(f"Error parsing JSON file at '{file_path}': {e}", e.doc, e.pos) from e
            except Exception as exc:
                raise RuntimeError(f"Unexpected error: {exc}") from exc

    def register_package_defaults(self, package_name: str, config_path: str | Path) -> None:
        """
        Register package default configuration by immediately loading from config directory.

        Loads config/config.json from the given path if it exists.
        Silently ignores missing config files — packages work without app config.

        Parameters
        ----------
        package_name : str
            Name of the package (used for logging only)
        config_path : str | Path
            Directory path containing config.json defaults

        Returns
        -------
        None
        """
        path = Path(config_path) / CONFIG_FILENAME
        with self._lock:
            if not path.exists():
                self.logger.debug("No default config found for '%s' at '%s'", package_name, path)
                return
            try:
                with open(path, encoding="utf-8") as f:
                    config = json.load(f)
                if isinstance(config, dict):
                    self.config = _deep_merge(self.config, config)
                    self.logger.info("Registered defaults for '%s' from '%s'", package_name, path)
            except (json.JSONDecodeError, OSError) as exc:
                self.logger.warning("Failed to load defaults for '%s': %s", package_name, exc)

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
