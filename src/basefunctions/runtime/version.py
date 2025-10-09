"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Version management utilities using Python package metadata
 Log:
 v1.0 : Initial implementation
 v2.0 : Migrated to importlib.metadata for installed package versions
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from pathlib import Path
from typing import Dict
import basefunctions

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------

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
    Get version of installed package from metadata.

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
        from importlib.metadata import version as get_version

        return get_version(package_name)
    except Exception:
        return "unknown"


def versions() -> Dict[str, str]:
    """
    Get versions of all installed neuraldevelopment packages.
    Only returns packages that exist in deployment/packages directory
    and are installed in current virtual environment.

    Returns
    -------
    Dict[str, str]
        Dictionary mapping package names to version strings
        Example: {"basefunctions": "0.5.2", "dbfunctions": "0.0.1"}
    """
    result = {}

    try:
        from importlib.metadata import distributions

        # Get list of local neuraldevelopment packages
        deploy_dir = basefunctions.runtime.get_bootstrap_deployment_directory()
        packages_dir = Path(deploy_dir).expanduser().resolve() / "packages"

        if not packages_dir.exists():
            return result

        # Build set of local package names
        local_packages = {p.name for p in packages_dir.iterdir() if p.is_dir()}

        # Get versions only for local packages that are installed
        for dist in distributions():
            if dist.name in local_packages:
                result[dist.name] = dist.version

    except Exception:
        pass

    return result
