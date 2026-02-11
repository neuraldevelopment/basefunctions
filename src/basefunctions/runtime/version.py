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
 v2.2 : Fixed to only show dev status for CWD package (honest version)
=============================================================================
"""

from __future__ import annotations

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import os
import subprocess
from pathlib import Path
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
    # Check if we're in development directory
    in_dev, dev_path = _is_in_development_directory(package_name)

    if in_dev:
        # In development: read version from pyproject.toml (most current)
        pyproject_path = Path(dev_path) / "pyproject.toml"
        if pyproject_path.exists():
            try:
                # Try tomllib first (Python 3.11+), then tomli
                try:
                    import tomllib
                except ImportError:
                    try:
                        import tomli as tomllib
                    except ImportError:
                        tomllib = None

                if tomllib:
                    with open(pyproject_path, 'rb') as f:
                        data = tomllib.load(f)
                        base_version = data.get("project", {}).get("version", "unknown")
                else:
                    # Fallback: simple regex parsing
                    with open(pyproject_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        import re
                        match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
                        if match:
                            base_version = match.group(1)
                        else:
                            base_version = "unknown"

                # Add development suffix with commit count
                commits_ahead = _get_git_commits_ahead(dev_path)
                if commits_ahead > 0:
                    return f"{base_version}-dev+{commits_ahead}"
                return f"{base_version}-dev"

            except Exception:
                pass  # Fall through to importlib.metadata

    # Not in development or pyproject.toml read failed: use installed version
    try:
        from importlib.metadata import version as get_version
        return get_version(package_name)
    except Exception:
        return "unknown"


def versions() -> dict[str, str]:
    """
    Get versions of all installed neuraldevelopment packages.
    Only returns packages that exist in deployment/packages directory
    and are installed in current virtual environment.
    Adds development indicator ONLY for package where CWD is located.

    Returns
    -------
    Dict[str, str]
        Dictionary mapping package names to version strings
        Example: {"basefunctions": "0.5.2", "dbfunctions": "0.1.1-dev+3"}
        Note: -dev suffix only shows for package in current working directory
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

        # Detect which package CWD is in (if any)
        cwd = os.getcwd()
        cwd_package = None
        cwd_dev_path = None

        for package_name in local_packages:
            dev_paths = basefunctions.runtime.find_development_path(package_name)
            for dev_path in dev_paths:
                if cwd.startswith(dev_path):
                    cwd_package = package_name
                    cwd_dev_path = dev_path
                    break
            if cwd_package:
                break

        # Get versions for all local packages
        for package_name in local_packages:
            # Check if this is the CWD package and we're in development
            if package_name == cwd_package and cwd_dev_path:
                # Use version() function which reads from pyproject.toml in dev mode
                result[package_name] = version(package_name)
            else:
                # For other packages: use installed version from metadata
                try:
                    from importlib.metadata import version as get_version
                    result[package_name] = get_version(package_name)
                except Exception:
                    # Package not installed, skip it
                    pass

    except Exception:
        pass

    return result
