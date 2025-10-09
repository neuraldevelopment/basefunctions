"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Version management utilities for deployed packages
 Log:
 v1.0 : Initial implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import os
from pathlib import Path
from typing import Dict
import basefunctions

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------
VERSION_FILENAME = "VERSION"

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


def version(package_name: str = "basefunctions") -> str:
    """
    Get version of specified package.

    Parameters
    ----------
    package_name : str
        Name of the package to get version for

    Returns
    -------
    str
        Version string (e.g. "0.5.2") or "unknown" if not found
    """
    try:
        deployment_path = basefunctions.runtime.get_deployment_path(package_name)
        version_file = Path(deployment_path) / VERSION_FILENAME

        if not version_file.exists():
            return "unknown"

        with open(version_file, "r", encoding="utf-8") as f:
            return f.read().strip()

    except Exception:
        return "unknown"


def versions() -> Dict[str, str]:
    """
    Get versions of all deployed packages.

    Returns
    -------
    Dict[str, str]
        Dictionary mapping package names to version strings
        Example: {"basefunctions": "0.5.2", "dbfunctions": "0.0.1"}
    """
    result = {}

    try:
        deploy_dir = basefunctions.runtime.get_bootstrap_deployment_directory()
        packages_dir = Path(deploy_dir).expanduser().resolve() / "packages"

        if not packages_dir.exists():
            return result

        for package_path in packages_dir.iterdir():
            if not package_path.is_dir():
                continue

            package_name = package_path.name
            version_file = package_path / VERSION_FILENAME

            if version_file.exists():
                try:
                    with open(version_file, "r", encoding="utf-8") as f:
                        result[package_name] = f.read().strip()
                except Exception:
                    result[package_name] = "unknown"
            else:
                result[package_name] = "unknown"

    except Exception:
        pass

    return result
