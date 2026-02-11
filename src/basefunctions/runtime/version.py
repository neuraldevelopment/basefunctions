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


def _find_package_root_with_pyproject(package_name: str) -> str | None:
    """
    Find package root directory containing pyproject.toml.

    Checks in this order:
    1. Development directory (if CWD is inside it)
    2. Deployment directory (if CWD is inside it)
    3. Any directory containing pyproject.toml with matching package name

    Parameters
    ----------
    package_name : str
        Package name to find

    Returns
    -------
    str | None
        Path to package root containing pyproject.toml, or None if not found
    """
    cwd = os.getcwd()

    # 1. Check Development directory first
    dev_paths = basefunctions.runtime.find_development_path(package_name)
    for dev_path in dev_paths:
        if cwd.startswith(dev_path):
            pyproject = Path(dev_path) / "pyproject.toml"
            if pyproject.exists():
                return str(dev_path)

    # 2. Check Deployment directory
    try:
        deploy_path = basefunctions.runtime.get_deployment_path(package_name)
        if deploy_path and os.path.exists(deploy_path):
            if cwd.startswith(deploy_path):
                pyproject = Path(deploy_path) / "pyproject.toml"
                if pyproject.exists():
                    return str(deploy_path)
    except Exception:
        pass

    return None


def version(package_name: str = "basefunctions") -> str:
    """
    Get version of installed package from metadata with development indicator.

    Reads version from pyproject.toml when available (development or deployment),
    falls back to importlib.metadata for pip-installed packages.

    Parameters
    ----------
    package_name : str
        Name of the package to get version for

    Returns
    -------
    str
        Version string (e.g. "0.5.2" or "0.5.2-dev+3") or "unknown" if not found
    """
    # Try to find package root with pyproject.toml (development or deployment)
    package_root = _find_package_root_with_pyproject(package_name)

    if package_root:
        # Read version from pyproject.toml
        pyproject_path = Path(package_root) / "pyproject.toml"
        try:
            # Try tomllib first (Python 3.11+), then tomli
            try:
                import tomllib
            except ImportError:
                try:
                    import tomli as tomllib  # type: ignore
                except ImportError:
                    tomllib = None

            if tomllib:
                with open(pyproject_path, 'rb') as f:
                    data = tomllib.load(f)
                    base_version = data.get("project", {}).get("version", "unknown")
            else:
                # Fallback: simple regex parsing
                import re
                with open(pyproject_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
                    if match:
                        base_version = match.group(1)
                    else:
                        base_version = "unknown"

            # Add development suffix with commit count
            commits_ahead = _get_git_commits_ahead(package_root)
            if commits_ahead > 0:
                return f"{base_version}-dev+{commits_ahead}"
            return f"{base_version}-dev"

        except Exception:
            pass  # Fall through to importlib.metadata

    # Fallback: use installed version (for pip install)
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

    Uses pyproject.toml from development/deployment when available,
    falls back to importlib.metadata for pip-installed packages.

    Returns
    -------
    Dict[str, str]
        Dictionary mapping package names to version strings
        Example: {"basefunctions": "0.5.2", "dbfunctions": "0.1.1-dev+3"}
    """
    result = {}

    try:
        from importlib.metadata import distributions  # noqa: F401

        # Get list of local neuraldevelopment packages
        deploy_dir = basefunctions.runtime.get_bootstrap_deployment_directory()
        packages_dir = Path(deploy_dir).expanduser().resolve() / "packages"

        if not packages_dir.exists():
            return result

        # Build set of local package names
        local_packages = {p.name for p in packages_dir.iterdir() if p.is_dir()}

        # Get versions for all local packages using version() function
        # This will automatically prefer pyproject.toml when available
        for package_name in local_packages:
            try:
                result[package_name] = version(package_name)
            except Exception:
                # Package not available, skip it
                pass

    except Exception:
        pass

    return result
