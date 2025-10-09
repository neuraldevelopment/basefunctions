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
 v2.1 : Added development version detection with commit counting
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import os
import subprocess
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


def _get_git_commits_ahead(dev_path: str) -> int:
    """
    Get number of commits ahead of latest tag.

    Parameters
    ----------
    dev_path : str
        Development directory path

    Returns
    -------
    int
        Number of commits ahead, 0 if at tag or on error
    """
    try:
        # Get latest tag
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=dev_path,
        )

        if result.returncode != 0:
            return 0

        latest_tag = result.stdout.strip()

        # Count commits since tag
        result = subprocess.run(
            ["git", "rev-list", f"{latest_tag}..HEAD", "--count"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=dev_path,
        )

        if result.returncode == 0:
            return int(result.stdout.strip())

        return 0

    except Exception:
        return 0


def _is_in_development_directory(package_name: str) -> tuple:
    """
    Check if current directory is in development path for package.

    Parameters
    ----------
    package_name : str
        Package name to check

    Returns
    -------
    tuple
        (bool, str) - (is_in_dev, dev_path)
    """
    dev_paths = basefunctions.runtime.find_development_path(package_name)
    cwd = os.getcwd()

    for dev_path in dev_paths:
        if cwd.startswith(dev_path):
            return True, dev_path

    return False, None


def version(package_name: str = "basefunctions") -> str:
    """
    Get version of installed package from metadata with development indicator.

    Parameters
    ----------
    package_name : str
        Name of the package to get version for

    Returns
    -------
    str
        Version string (e.g. "0.5.2" or "0.5.2-dev+3") or "unknown" if not found
    """
    try:
        from importlib.metadata import version as get_version

        base_version = get_version(package_name)
    except Exception:
        base_version = "unknown"

    # Check if we're in development directory
    in_dev, dev_path = _is_in_development_directory(package_name)

    if not in_dev:
        return base_version

    # Get commits ahead of latest tag
    commits_ahead = _get_git_commits_ahead(dev_path)

    if commits_ahead > 0:
        return f"{base_version}-dev+{commits_ahead}"

    return f"{base_version}-dev"


def versions() -> Dict[str, str]:
    """
    Get versions of all installed neuraldevelopment packages.
    Only returns packages that exist in deployment/packages directory
    and are installed in current virtual environment.
    Adds development indicators for packages in development directories.

    Returns
    -------
    Dict[str, str]
        Dictionary mapping package names to version strings
        Example: {"basefunctions": "0.5.2", "dbfunctions": "0.1.1-dev+3"}
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
                # Check if package is in development
                in_dev, dev_path = _is_in_development_directory(dist.name)

                if in_dev:
                    # Get commits ahead
                    commits_ahead = _get_git_commits_ahead(dev_path)

                    if commits_ahead > 0:
                        result[dist.name] = f"{dist.version}-dev+{commits_ahead}"
                    else:
                        result[dist.name] = f"{dist.version}-dev"
                else:
                    result[dist.name] = dist.version

    except Exception:
        pass

    return result
