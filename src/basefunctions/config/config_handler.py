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
from typing import Any, Optional
from pathlib import Path
import yaml
import basefunctions as bf

# -------------------------------------------------------------
# FUNCTION DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# DEFINITIONS REGISTRY
# -------------------------------------------------------------

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------
DEFAULT_PATHNAME = ".config"

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------


# -------------------------------------------------------------
# CLASS DEFINITIONS
# -------------------------------------------------------------
@bf.singleton
class ConfigHandler:
    """
    Singleton for handling YAML-based configuration management.
    """

    def __init__(self):
        self.config = {}

    def load_config(self, file_path: str) -> None:
        if not file_path.endswith(".yaml"):
            raise ValueError(f"The file '{file_path}' is not a valid YAML file.")
        try:
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
        file_name = (
            Path(bf.get_home_path()) / DEFAULT_PATHNAME / package_name / f"{package_name}.yaml"
        )
        if not bf.check_if_file_exists(file_name):
            self.create_default_config(package_name)
        self.load_config(str(file_name))

    def create_default_config(self, package_name: str) -> None:
        if not package_name:
            raise ValueError("Package name must be provided.")
        config_directory = Path(bf.get_home_path()) / DEFAULT_PATHNAME / package_name
        bf.create_directory(config_directory)
        with open(config_directory / f"{package_name}.yaml", "w", encoding="utf-8") as file:
            yaml.dump({package_name: {}}, file)

    def get_config_value(self, path: str, default_value: Any = None) -> Any:
        keys = path.split("/")
        value = self.config
        for key in keys:
            if not isinstance(value, dict):
                return default_value
            value = value.get(key, default_value)
        return value

    def get_config(self, package: Optional[str] = None) -> dict:
        if package is None:
            return self.config
        return self.config.get(package, {})

    def list_available_paths(self) -> list[str]:
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
