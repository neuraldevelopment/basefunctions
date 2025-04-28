"""
=============================================================================

  Licensed Materials, Property of Ralph Vogl, Munich

  Project : basefunctions

  Copyright (c) by Ralph Vogl

  All rights reserved.

  Description:

  a simple framework for base functionalities in python

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Any
from pathlib import Path
from typing import Optional
import yaml
import basefunctions

# -------------------------------------------------------------
#  FUNCTION DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# DEFINITIONS REGISTRY
# -------------------------------------------------------------

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------
DEFAULT_PATHNAME = ".config"

# -------------------------------------------------------------
# VARIABLE DEFINTIONS
# -------------------------------------------------------------


# -------------------------------------------------------------
# CLASS DEFINITIONS
# -------------------------------------------------------------
@basefunctions.singleton
class ConfigHandler:
    """
    The ConfigHandler class is a singleton designed to handle and
    abstract configuration management. It reads configurations from
    YAML files and stores them in a dictionary, allowing access by
    package name and configuration element name.

    Configurations are stored in a YAML file format, with the
    package name as the filename.

    Example:
    ```
    config_handler.ConfigHandler().load_config("configs/config.yaml")
    ```
    """

    def __init__(self):
        self.config = {}  # Dictionary to store configurations

    def load_config(self, file_path: str) -> None:
        """
        Load a YAML configuration file into the configs dictionary.

        Parameters:
        -----------
            file_path: str
                Path to the YAML configuration file.

        Raises:
        -------
            FileNotFoundError: If the specified file does not exist.
            yaml.YAMLError: If there is an error in parsing the YAML file.
            ValueError: If the YAML file is empty or invalid.
            RuntimeError: If there is an unexpected error.
        """
        try:
            if not file_path.endswith(".yaml"):
                raise ValueError(f"The file '{file_path}' is not a valid YAML file.")

            with open(file_path, "r", encoding="utf-8") as file:
                config = yaml.safe_load(file)
                if not isinstance(config, dict):
                    raise ValueError(f"Invalid config format in '{file_path}'")
                self.config.update(config)
        except FileNotFoundError as exc:
            raise FileNotFoundError(f"File not found: '{file_path}'") from exc
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Error parsing YAML file at '{file_path}': {e}")
        except Exception as exc:
            raise RuntimeError(f"Unexpected error: {exc}") from exc

    def load_default_config(self, package_name: str) -> None:
        """
        Load the default configuration for a given package.

        Parameters:
        -----------
            package_name: str
                The name of the package to load the default configuration for.

        Raises:
        -------
            FileNotFoundError: If the default configuration file does not exist.
        """

        file_name = (
            Path(basefunctions.get_home_path())
            / DEFAULT_PATHNAME
            / package_name
            / f"{package_name}.yaml"
        )
        if not basefunctions.check_if_file_exists(file_name):
            self.create_default_config(package_name)
        self.load_config(str(file_name))

    def create_default_config(self, package_name: str) -> None:
        """
        Create a default configuration file for a given package.

        Parameters:
        -----------
            package_name: str
                The name of the package to create the default configuration for.

        Raises:
        -------
            ValueError: If the package name is not provided.
        """
        if not package_name:
            raise ValueError("Package name must be provided.")

        config_directory = Path(basefunctions.get_home_path()) / DEFAULT_PATHNAME / package_name
        basefunctions.create_directory(config_directory)

        with open(config_directory / f"{package_name}.yaml", "w", encoding="utf-8") as file:
            yaml.dump({package_name: None}, file)

    def get_config_value(self, path: str, default_value: Any = None) -> Any:
        """
        Retrieve the value of a configuration element by its path.

        Parameters:
        -----------
            path: str
                The path to the configuration element (e.g., "key/subkey").
            default_value: Any
                The default value to return if the path is not found.

        Returns:
        --------
            Any
                The value of the configuration element or default_value if not found.
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
        Retrieve the configuration settings, optionally for a specific package.

        Parameters:
        -----------
            package: Optional[str], optional
                The name of the package to retrieve configuration for. Default is None.

        Returns:
        --------
            dict
                A dictionary containing the configuration settings.
        """
        if package is None:
            return self.config
        return self.config.get(package, {})

    def list_available_paths(self) -> list[str]:
        """
        List all available configuration paths.

        Returns:
        --------
            list[str]
                A list of all configuration paths in 'key/subkey' format.
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
