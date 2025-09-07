"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich

  Project : basefunctions

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  Runtime path utilities for development and deployment environment detection

  Log:
  v1.0 : Initial implementation
  v1.2 : Removed all circular dependencies, bootstrap is now fully autonomous
  v1.3 : Added two-phase package structure creation
  v1.4 : Extended with deployment-specific path functions
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import os
import json
from typing import List

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------
DEFAULT_DEPLOYMENT_DIRECTORIES = ["bin", "packages"]
DEFAULT_PACKAGE_DIRECTORIES = ["config", "logs", "templates/config"]
BOOTSTRAP_DIRECTORIES = ["config", "templates/config"]
BOOTSTRAP_CONFIG_PATH = "~/.config/basefunctions/bootstrap.json"

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# LOGGING INITIALIZE
# -------------------------------------------------------------

# -------------------------------------------------------------
# TYPE DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# EXCEPTION DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# CLASS OR FUNCTION DEFINITIONS
# -------------------------------------------------------------


def _load_bootstrap_config() -> dict:
    """
    Load bootstrap configuration from file.

    Returns
    -------
    dict
        Bootstrap configuration
    """
    bootstrap_path = os.path.expanduser(BOOTSTRAP_CONFIG_PATH)

    if os.path.exists(bootstrap_path):
        try:
            with open(bootstrap_path, "r", encoding="utf-8") as file:
                return json.load(file)
        except Exception:
            pass

    # Return default config if file doesn't exist or can't be loaded
    default_config = {
        "bootstrap": {
            "paths": {"deployment_directory": "~/.neuraldev", "development_directories": ["~/Code", "~/Development"]}
        }
    }

    # Try to save default config
    _save_bootstrap_config(default_config)
    return default_config


def _save_bootstrap_config(config: dict) -> None:
    """
    Save bootstrap configuration to file.

    Parameters
    ----------
    config : dict
        Bootstrap configuration to save
    """
    try:
        bootstrap_path = os.path.expanduser(BOOTSTRAP_CONFIG_PATH)
        os.makedirs(os.path.dirname(bootstrap_path), exist_ok=True)

        with open(bootstrap_path, "w", encoding="utf-8") as file:
            json.dump(config, file, indent=2)
    except Exception:
        pass


def get_bootstrap_config_path() -> str:
    """
    Get bootstrap configuration file path.

    Returns
    -------
    str
        Bootstrap configuration file path
    """
    return BOOTSTRAP_CONFIG_PATH


def get_bootstrap_deployment_directory() -> str:
    """
    Get deployment directory from bootstrap config.

    Returns
    -------
    str
        Deployment directory path
    """
    bootstrap_config = _load_bootstrap_config()

    return bootstrap_config.get("bootstrap", {}).get("paths", {}).get("deployment_directory", "~/.neuraldev")


def get_bootstrap_development_directories() -> list:
    """
    Get development directories from bootstrap config.

    Returns
    -------
    list
        List of development directory paths
    """
    bootstrap_config = _load_bootstrap_config()

    return (
        bootstrap_config.get("bootstrap", {})
        .get("paths", {})
        .get("development_directories", ["~/Code/neuraldev", "~/Code/neuraldev-utils"])
    )


def get_deployment_path(package_name: str) -> str:
    """
    Get deployment path for package - ALWAYS returns deployment directory.

    Parameters
    ----------
    package_name : str
        Package name to get deployment path for

    Returns
    -------
    str
        Deployment path for package (always ~/.neuraldev/packages/PACKAGE_NAME)
    """
    deploy_dir = get_bootstrap_deployment_directory()
    normalized_deploy_dir = os.path.abspath(os.path.expanduser(deploy_dir))
    return os.path.join(normalized_deploy_dir, "packages", package_name)


def find_development_path(package_name: str) -> List[str]:
    """
    Find all development paths for package by searching all development directories.

    Parameters
    ----------
    package_name : str
        Package name to find

    Returns
    -------
    List[str]
        List of development paths where package exists (can be multiple!)
        Empty list if package not found anywhere
    """
    found_paths = []

    for dev_dir in get_bootstrap_development_directories():
        dev_path = os.path.abspath(os.path.expanduser(dev_dir))
        package_path = os.path.join(dev_path, package_name)

        if os.path.exists(package_path):
            found_paths.append(package_path)

    return found_paths


def create_root_structure() -> None:
    """
    Create initial deployment root directory structure.
    Called during bootstrap to ensure base directories exist.
    """
    try:
        deploy_dir = get_bootstrap_deployment_directory()
        normalized_deploy_dir = os.path.abspath(os.path.expanduser(deploy_dir))

        # Create deployment base directory
        os.makedirs(normalized_deploy_dir, exist_ok=True)

        # Create main deployment directories
        for dir_name in DEFAULT_DEPLOYMENT_DIRECTORIES:
            dir_path = os.path.join(normalized_deploy_dir, dir_name)
            os.makedirs(dir_path, exist_ok=True)

    except Exception as e:
        raise


def create_bootstrap_package_structure(package_name: str) -> None:
    """
    Create minimal package directory structure (bootstrap phase).

    Parameters
    ----------
    package_name : str
        Package name for which to create structure

    Raises
    ------
    ValueError
        If package_name is None or empty
    """
    if not package_name:
        raise ValueError("Package name must be provided and cannot be empty")

    try:
        # Get the correct runtime path for this package
        package_base_path = get_runtime_path(package_name)

        # Create minimal bootstrap directories only
        for dir_name in BOOTSTRAP_DIRECTORIES:
            dir_path = os.path.join(package_base_path, dir_name)
            os.makedirs(dir_path, exist_ok=True)

    except Exception as e:
        raise


def create_full_package_structure(package_name: str, custom_directories: list = None) -> None:
    """
    Create full package directory structure with custom or default directories.

    Parameters
    ----------
    package_name : str
        Package name for which to create structure
    custom_directories : list, optional
        Custom directories list, uses DEFAULT_PACKAGE_DIRECTORIES if None

    Raises
    ------
    ValueError
        If package_name is None or empty
    """
    if not package_name:
        raise ValueError("Package name must be provided and cannot be empty")

    try:
        # Get the correct runtime path for this package
        package_base_path = get_runtime_path(package_name)

        directories = custom_directories if custom_directories else DEFAULT_PACKAGE_DIRECTORIES

        # Create all specified directories
        for dir_name in directories:
            dir_path = os.path.join(package_base_path, dir_name)
            os.makedirs(dir_path, exist_ok=True)

    except Exception as e:
        raise


def get_runtime_component_path(package_name: str, component: str) -> str:
    """
    Get runtime path for a specific package component.

    Parameters
    ----------
    package_name : str
        Package name to get path for
    component : str
        Component name (config, logs, data, etc.)

    Returns
    -------
    str
        Complete path to package component
    """
    base_path = get_runtime_path(package_name)
    return os.path.join(base_path, component)


def get_runtime_template_path(package_name: str) -> str:
    """
    Get runtime template config path for a package.

    Parameters
    ----------
    package_name : str
        Package name to get template path for

    Returns
    -------
    str
        Complete path to package template config directory
    """
    return get_runtime_component_path(package_name, "templates/config")


def get_runtime_config_path(package_name: str) -> str:
    """
    Get runtime config path for a package.

    Parameters
    ----------
    package_name : str
        Package name to get config path for

    Returns
    -------
    str
        Complete path to package config directory
    """
    return get_runtime_component_path(package_name, "config")


def ensure_bootstrap_package_structure(package_name: str) -> None:
    """
    Ensure bootstrap package structure exists before using it.

    Parameters
    ----------
    package_name : str
        Package name to ensure structure for
    """
    try:
        # Create bootstrap package structure using unified path system
        create_bootstrap_package_structure(package_name)

    except Exception as e:
        raise


def get_runtime_path(package_name: str) -> str:
    """
    Get runtime base path for package based on environment detection.

    Parameters
    ----------
    package_name : str
        Package name to get path for

    Returns
    -------
    str
        Base runtime path for package
    """
    try:
        # Get bootstrap config paths directly
        dev_dirs = get_bootstrap_development_directories()
        deploy_dir = get_bootstrap_deployment_directory()

        # Normalize paths and sort by length (longest first for specificity)
        normalized_dev_dirs = [os.path.abspath(os.path.expanduser(d)) for d in dev_dirs if d]
        normalized_dev_dirs.sort(key=len, reverse=True)
        normalized_deploy_dir = os.path.abspath(os.path.expanduser(deploy_dir))

        current_dir = os.path.abspath(os.getcwd())

        # Check if current directory is within any development directory
        for dev_dir in normalized_dev_dirs:
            package_dir = os.path.join(dev_dir, package_name)
            if current_dir.startswith(package_dir + os.sep) or current_dir == package_dir:
                return package_dir

        # Default to deployment directory
        deploy_package_dir = os.path.join(normalized_deploy_dir, "packages", package_name)
        return deploy_package_dir

    except Exception:
        # Fallback to deployment path if config fails
        fallback_path = os.path.join(os.path.expanduser("~/.neuraldev"), "packages", package_name)
        return os.path.abspath(fallback_path)
