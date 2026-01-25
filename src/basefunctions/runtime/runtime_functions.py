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
  v1.5 : Ported to pathlib for modern path handling
  v1.6 : Added get_runtime_completion_path() for shell completion files
=============================================================================
"""

from __future__ import annotations

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import json
from pathlib import Path

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
    bootstrap_path = Path(BOOTSTRAP_CONFIG_PATH).expanduser()

    if bootstrap_path.exists():
        try:
            with open(bootstrap_path, encoding="utf-8") as file:
                return json.load(file)
        except Exception:
            pass

    # Return default config if file doesn't exist or can't be loaded
    default_config = {
        "bootstrap": {
            "paths": {
                "deployment_directory": "~/.neuraldevelopment",
                "development_directories": ["~/Code", "~/Development"],
            }
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
        bootstrap_path = Path(BOOTSTRAP_CONFIG_PATH).expanduser()
        bootstrap_path.parent.mkdir(parents=True, exist_ok=True)

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

    return bootstrap_config.get("bootstrap", {}).get("paths", {}).get("deployment_directory", "~/.neuraldevelopment")


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
        Deployment path for package (always ~/.neuraldevelopment/packages/PACKAGE_NAME)
    """
    deploy_dir = get_bootstrap_deployment_directory()
    normalized_deploy_dir = Path(deploy_dir).expanduser().resolve()
    return str(normalized_deploy_dir / "packages" / package_name)


def find_development_path(package_name: str) -> list[str]:
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
        dev_path = Path(dev_dir).expanduser().resolve()
        package_path = dev_path / package_name

        if package_path.exists():
            found_paths.append(str(package_path))

    return found_paths


def create_root_structure() -> None:
    """
    Create initial deployment root directory structure.
    Called during bootstrap to ensure base directories exist.
    """
    try:
        deploy_dir = get_bootstrap_deployment_directory()
        normalized_deploy_dir = Path(deploy_dir).expanduser().resolve()

        # Create deployment base directory
        normalized_deploy_dir.mkdir(parents=True, exist_ok=True)

        # Create main deployment directories
        for dir_name in DEFAULT_DEPLOYMENT_DIRECTORIES:
            dir_path = normalized_deploy_dir / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)

    except Exception:
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
        package_base_path = Path(get_runtime_path(package_name))

        # Create minimal bootstrap directories only
        for dir_name in BOOTSTRAP_DIRECTORIES:
            dir_path = package_base_path / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)

    except Exception:
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
        package_base_path = Path(get_runtime_path(package_name))

        directories = custom_directories if custom_directories else DEFAULT_PACKAGE_DIRECTORIES

        # Create all specified directories
        for dir_name in directories:
            dir_path = package_base_path / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)

    except Exception:
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
    base_path = Path(get_runtime_path(package_name))
    return str(base_path / component)


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


def get_runtime_log_path(package_name: str) -> str:
    """
    Get runtime log path for a package.

    Parameters
    ----------
    package_name : str
        Package name to get log path for

    Returns
    -------
    str
        Complete path to package log directory
    """
    return get_runtime_component_path(package_name, "logs")


def get_runtime_completion_path(package_name: str, tool_name: str | None = None) -> str:
    """
    Get runtime path for shell completion files.

    Parameters
    ----------
    package_name : str
        Package name to get completion path for
    tool_name : str, optional
        Tool name for completion file, defaults to package_name if None

    Returns
    -------
    str
        Complete path to completion file

    Examples
    --------
    >>> # In development (~/Code/neuraldev/basefunctions/)
    >>> get_runtime_completion_path("basefunctions", "ppip")
    '~/Code/neuraldev/basefunctions/.cli/basefunctions_ppip.completion'

    >>> # In deployment
    >>> get_runtime_completion_path("basefunctions", "ppip")
    '~/.neuraldevelopment/completion/basefunctions_ppip_completion'

    >>> # Without tool_name
    >>> get_runtime_completion_path("basefunctions")
    '~/Code/neuraldev/basefunctions/.cli/basefunctions.completion'
    """
    try:
        # Get bootstrap config paths
        dev_dirs = get_bootstrap_development_directories()
        deploy_dir = get_bootstrap_deployment_directory()

        # Normalize paths
        normalized_dev_dirs = [Path(d).expanduser().resolve() for d in dev_dirs if d]
        normalized_dev_dirs.sort(key=lambda p: len(str(p)), reverse=True)
        normalized_deploy_dir = Path(deploy_dir).expanduser().resolve()

        current_dir = Path.cwd().resolve()

        # Check if in development environment
        for dev_dir in normalized_dev_dirs:
            package_dir = dev_dir / package_name
            if current_dir == package_dir or package_dir in current_dir.parents:
                # Development: PROJECT_ROOT/.cli/
                cli_dir = package_dir / ".cli"
                cli_dir.mkdir(parents=True, exist_ok=True)

                if tool_name:
                    filename = f"{package_name}_{tool_name}.completion"
                else:
                    filename = f"{package_name}.completion"

                return str(cli_dir / filename)

        # Deployment: ~/.neuraldevelopment/completion/
        completion_dir = normalized_deploy_dir / "completion"
        completion_dir.mkdir(parents=True, exist_ok=True)

        if tool_name:
            filename = f"{package_name}_{tool_name}_completion"
        else:
            filename = f"{package_name}_completion"

        return str(completion_dir / filename)

    except Exception:
        # Fallback to deployment path
        fallback_dir = Path("~/.neuraldevelopment/completion").expanduser().resolve()
        fallback_dir.mkdir(parents=True, exist_ok=True)

        if tool_name:
            filename = f"{package_name}_{tool_name}_completion"
        else:
            filename = f"{package_name}_completion"

        return str(fallback_dir / filename)


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

    except Exception:
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
        normalized_dev_dirs = [Path(d).expanduser().resolve() for d in dev_dirs if d]
        normalized_dev_dirs.sort(key=lambda p: len(str(p)), reverse=True)
        normalized_deploy_dir = Path(deploy_dir).expanduser().resolve()

        current_dir = Path.cwd().resolve()

        # Check if current directory is within any development directory
        for dev_dir in normalized_dev_dirs:
            package_dir = dev_dir / package_name
            if current_dir == package_dir or package_dir in current_dir.parents:
                return str(package_dir)

        # Default to deployment directory
        deploy_package_dir = normalized_deploy_dir / "packages" / package_name
        return str(deploy_package_dir)

    except Exception:
        # Fallback to deployment path if config fails
        fallback_path = Path("~/.neuraldevelopment").expanduser().resolve() / "packages" / package_name
        return str(fallback_path)
