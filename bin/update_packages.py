#!/usr/bin/env python3
"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Update local neuraldevelopment packages in active venv or all deployments
 (standalone version without basefunctions dependency)
 Log:
 v1.0 : Initial implementation
 v2.0 : Standalone version for batch mode support
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import sys
import os
import re
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------
BOOTSTRAP_CONFIG_PATH = Path("~/.config/basefunctions/bootstrap.json").expanduser()
PROTECTED_PACKAGES = ["pip", "setuptools", "wheel"]

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


class PackageUpdateError(Exception):
    """Package update operation failed."""

    pass


# -------------------------------------------------------------
# STANDALONE FUNCTIONS (no basefunctions dependency)
# -------------------------------------------------------------


def _format_update_table(updates: List[Tuple[str, str, str]]) -> str:
    """
    Format updates as ASCII table.

    Parameters
    ----------
    updates : List[Tuple[str, str, str]]
        List of (package_name, current_version, target_version)

    Returns
    -------
    str
        Formatted table
    """
    if not updates:
        return ""

    # Calculate column widths
    col1_width = max(len("Package"), max(len(u[0]) for u in updates))
    col2_width = max(len("Current"), max(len(u[1]) for u in updates))
    col3_width = max(len("Target"), max(len(u[2]) for u in updates))

    # Build table
    lines = []
    separator = "+" + "-" * (col1_width + 2) + "+" + "-" * (col2_width + 2) + "+" + "-" * (col3_width + 2) + "+"

    # Header
    lines.append(separator)
    lines.append(f"| {'Package':<{col1_width}} | {'Current':<{col2_width}} | {'Target':<{col3_width}} |")
    lines.append(separator)

    # Rows
    for pkg, current, target in updates:
        lines.append(f"| {pkg:<{col1_width}} | {current:<{col2_width}} | {target:<{col3_width}} |")

    lines.append(separator)

    return "\n".join(lines)


def _load_bootstrap_config() -> dict:
    """
    Load bootstrap configuration from file.

    Returns
    -------
    dict
        Bootstrap configuration
    """
    if BOOTSTRAP_CONFIG_PATH.exists():
        try:
            with open(BOOTSTRAP_CONFIG_PATH, "r", encoding="utf-8") as file:
                return json.load(file)
        except Exception:
            pass

    # Return default config
    return {
        "bootstrap": {
            "paths": {
                "deployment_directory": "~/.neuraldevelopment",
                "development_directories": ["~/Code", "~/Development"],
            }
        }
    }


def _get_deployment_directory() -> Path:
    """
    Get deployment directory from bootstrap config.

    Returns
    -------
    Path
        Deployment directory path
    """
    config = _load_bootstrap_config()
    deploy_dir = config.get("bootstrap", {}).get("paths", {}).get("deployment_directory", "~/.neuraldevelopment")
    return Path(deploy_dir).expanduser().resolve()


def _get_development_directories() -> List[Path]:
    """
    Get development directories from bootstrap config.

    Returns
    -------
    List[Path]
        List of development directory paths
    """
    config = _load_bootstrap_config()
    dev_dirs = config.get("bootstrap", {}).get("paths", {}).get("development_directories", ["~/Code", "~/Development"])
    return [Path(d).expanduser().resolve() for d in dev_dirs]


def _find_development_path(package_name: str) -> List[str]:
    """
    Find all development paths for package.

    Parameters
    ----------
    package_name : str
        Package name to find

    Returns
    -------
    List[str]
        List of development paths where package exists
    """
    found_paths = []

    for dev_dir in _get_development_directories():
        package_path = dev_dir / package_name
        if package_path.exists():
            found_paths.append(str(package_path))

    return found_paths


def _get_pip_executable(venv_path: Path) -> Path:
    """
    Get platform-aware pip executable path.

    Parameters
    ----------
    venv_path : Path
        Virtual environment path

    Returns
    -------
    Path
        Path to pip executable
    """
    if sys.platform == "win32":
        return venv_path / "Scripts" / "pip.exe"
    else:
        return venv_path / "bin" / "pip"


def _get_python_executable(venv_path: Path) -> Path:
    """
    Get platform-aware python executable path.

    Parameters
    ----------
    venv_path : Path
        Virtual environment path

    Returns
    -------
    Path
        Path to python executable
    """
    if sys.platform == "win32":
        return venv_path / "Scripts" / "python.exe"
    else:
        return venv_path / "bin" / "python"


def _is_valid_venv(venv_path: Path) -> bool:
    """
    Check if path contains valid virtual environment.

    Parameters
    ----------
    venv_path : Path
        Path to check

    Returns
    -------
    bool
        True if valid virtual environment
    """
    if not venv_path.exists() or not venv_path.is_dir():
        return False

    pip_executable = _get_pip_executable(venv_path)
    python_executable = _get_python_executable(venv_path)

    return pip_executable.exists() and python_executable.exists()


def _get_installed_packages(venv_path: Path) -> List[str]:
    """
    Get list of installed packages in environment.

    Parameters
    ----------
    venv_path : Path
        Virtual environment path

    Returns
    -------
    List[str]
        List of installed package names
    """
    pip_executable = _get_pip_executable(venv_path)

    try:
        result = subprocess.run(
            [str(pip_executable), "list", "--format=freeze"],
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        )

        packages = []
        for line in result.stdout.strip().split("\n"):
            if "==" in line:
                package_name = line.split("==")[0]
                if package_name not in PROTECTED_PACKAGES:
                    packages.append(package_name)

        return packages

    except Exception:
        return []


def _get_package_info(package_name: str, venv_path: Path) -> Optional[dict]:
    """
    Get information about installed package.

    Parameters
    ----------
    package_name : str
        Package name
    venv_path : Path
        Virtual environment path

    Returns
    -------
    Optional[dict]
        Package information or None if not found
    """
    pip_executable = _get_pip_executable(venv_path)

    try:
        result = subprocess.run(
            [str(pip_executable), "show", package_name],
            capture_output=True,
            text=True,
            timeout=15,
            check=True,
        )

        info = {}
        for line in result.stdout.strip().split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                info[key.strip()] = value.strip()

        return info if info else None

    except Exception:
        return None


def _run_pip_command(command: List[str], venv_path: Path) -> None:
    """
    Run pip command in virtual environment.

    Parameters
    ----------
    command : List[str]
        Pip command arguments (without 'pip')
    venv_path : Path
        Virtual environment path

    Raises
    ------
    PackageUpdateError
        If command fails
    """
    pip_executable = _get_pip_executable(venv_path)
    full_command = [str(pip_executable)] + command

    try:
        subprocess.run(full_command, check=True, timeout=300)
    except subprocess.CalledProcessError as e:
        raise PackageUpdateError(f"Pip command failed: {e}")
    except subprocess.TimeoutExpired:
        raise PackageUpdateError("Pip command timed out")


# -------------------------------------------------------------
# CLASS OR FUNCTION DEFINITIONS
# -------------------------------------------------------------


class PackageUpdater:
    """
    Update local neuraldevelopment packages in venv or deployments.
    """

    def __init__(self):
        self.deploy_dir = _get_deployment_directory()
        self.packages_dir = self.deploy_dir / "packages"

    def _get_available_local_packages(self) -> List[str]:
        """
        Get list of available local packages from deployment directory.

        Returns
        -------
        List[str]
            List of package names
        """
        if not self.packages_dir.exists():
            return []

        packages = []
        for item in self.packages_dir.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                packages.append(item.name)

        return sorted(packages)

    def _get_deployed_version(self, package_name: str) -> Optional[str]:
        """
        Get version from deployed package pyproject.toml.

        Parameters
        ----------
        package_name : str
            Package name

        Returns
        -------
        Optional[str]
            Version string or None if not found
        """
        pyproject_file = self.packages_dir / package_name / "pyproject.toml"

        if not pyproject_file.exists():
            return None

        try:
            content = pyproject_file.read_text(encoding="utf-8")
            match = re.search(r'^version\s*=\s*"([0-9]+\.[0-9]+\.[0-9]+)"', content, re.MULTILINE)
            return match.group(1) if match else None
        except Exception:
            return None

    def _compare_versions(self, v1: str, v2: str) -> int:
        """
        Compare two version strings.

        Parameters
        ----------
        v1 : str
            First version (e.g. "0.5.10" or "0.5.11-dev+3")
        v2 : str
            Second version (e.g. "0.5.11")

        Returns
        -------
        int
            -1 if v1 < v2, 0 if equal, 1 if v1 > v2
        """

        # Parse versions and dev suffix
        def parse_version(v: str) -> Tuple[tuple, bool]:
            # Split off dev suffix if present
            if "-dev" in v:
                base = v.split("-dev")[0]
                has_dev = True
            else:
                base = v
                has_dev = False

            parts = tuple(int(x) for x in base.split("."))
            return parts, has_dev

        parts1, dev1 = parse_version(v1)
        parts2, dev2 = parse_version(v2)

        # Compare base versions
        if parts1 < parts2:
            return -1
        elif parts1 > parts2:
            return 1
        else:
            # Base versions equal - dev suffix wins
            if dev1 and not dev2:
                return 1
            elif not dev1 and dev2:
                return -1
            else:
                return 0

    def _update_package(self, package_name: str, venv_path: Path) -> bool:
        """
        Update package in virtual environment.

        Parameters
        ----------
        package_name : str
            Package name to update
        venv_path : Path
            Virtual environment path

        Returns
        -------
        bool
            True if successful

        Raises
        ------
        PackageUpdateError
            If update fails
        """
        package_path = self.packages_dir / package_name

        if not package_path.exists():
            raise PackageUpdateError(f"Package path not found: {package_path}")

        try:
            _run_pip_command(["install", str(package_path)], venv_path)
            return True
        except PackageUpdateError:
            raise

    def update_single_venv(self) -> Dict:
        """
        Update packages in current active virtual environment.

        Returns
        -------
        Dict
            Update statistics
        """
        # Check if VIRTUAL_ENV is set (original user venv)
        venv_path_str = os.environ.get("VIRTUAL_ENV")
        if not venv_path_str:
            raise PackageUpdateError("Not in virtual environment - activate venv first")

        venv_path = Path(venv_path_str)

        if not _is_valid_venv(venv_path):
            raise PackageUpdateError(f"Invalid virtual environment: {venv_path}")

        # Block updates from basefunctions development directory
        cwd = Path.cwd()
        dev_paths = _find_development_path("basefunctions")

        for dev_path in dev_paths:
            dev_path_resolved = Path(dev_path).resolve()
            if cwd == dev_path_resolved or dev_path_resolved in cwd.parents:
                raise PackageUpdateError("Cannot update from basefunctions development directory")

        print("Mode: Single venv update")
        print(f"Checking: {venv_path}\n")

        # Get installed packages
        installed = _get_installed_packages(venv_path)

        # Get available local packages
        available_local = self._get_available_local_packages()

        # Detect current development package to exclude it
        current_package = None

        for pkg_name in available_local:
            pkg_dev_paths = _find_development_path(pkg_name)
            for dev_path in pkg_dev_paths:
                dev_path_resolved = Path(dev_path).resolve()
                if cwd == dev_path_resolved or dev_path_resolved in cwd.parents:
                    current_package = pkg_name
                    break
            if current_package:
                break

        # Build intersection - exclude current package
        to_check = [pkg for pkg in installed if pkg in available_local and pkg != current_package]

        if not to_check:
            if current_package:
                print(f"No local dependencies to update (skipping {current_package})")
            else:
                print("No local packages found in current venv")
            return {"updated": 0, "skipped": 0, "errors": 0}

        # Collect planned updates
        planned_updates = []
        errors = []

        for package_name in sorted(to_check):
            try:
                # Get installed version
                pkg_info = _get_package_info(package_name, venv_path)
                if not pkg_info:
                    errors.append((package_name, "Version read failed"))
                    continue

                installed_version = pkg_info.get("Version", "")

                # Get deployed version
                deployed_version = self._get_deployed_version(package_name)
                if not deployed_version:
                    errors.append((package_name, "Deployed version not found"))
                    continue

                # Compare versions
                comparison = self._compare_versions(installed_version, deployed_version)

                if comparison < 0:
                    planned_updates.append((package_name, installed_version, deployed_version))

            except Exception as e:
                errors.append((package_name, str(e)))

        if not planned_updates and not errors:
            print("All packages are up-to-date")
            return {"updated": 0, "skipped": len(to_check), "errors": 0}

        # Show planned updates table
        if planned_updates:
            print("Planned updates:")
            print(_format_update_table(planned_updates))
            print("\nProceeding with updates...")

        # Execute updates
        updated = 0

        for package_name, installed_version, deployed_version in planned_updates:
            try:
                print(f"  {package_name}: {installed_version} -> {deployed_version} ", end="", flush=True)
                self._update_package(package_name, venv_path)
                print("done")
                updated += 1
            except PackageUpdateError as e:
                print(f"failed ({e})")
                errors.append((package_name, str(e)))

        skipped = len(to_check) - len(planned_updates)

        print(f"\nSummary: {updated} updated, {skipped} skipped, {len(errors)} errors")

        if errors:
            print("\nErrors:")
            for pkg, error in errors:
                print(f"  {pkg}: {error}")

        return {"updated": updated, "skipped": skipped, "errors": len(errors)}

    def update_all_deployments(self) -> Dict:
        """
        Update packages in all deployment virtual environments.

        Returns
        -------
        Dict
            Update statistics
        """
        print("Mode: Batch update all deployments")
        print(f"Scanning: {self.packages_dir}\n")

        if not self.packages_dir.exists():
            print("No packages directory found")
            return {"updated": 0, "deployments": 0, "errors": 0}

        available_local = self._get_available_local_packages()
        total_updated = 0
        deployments_updated = 0
        total_errors = []

        # Iterate over all deployed packages
        for package_dir in sorted(self.packages_dir.iterdir()):
            if not package_dir.is_dir() or package_dir.name.startswith("."):
                continue

            venv_path = package_dir / "venv"

            if not _is_valid_venv(venv_path):
                continue

            package_name = package_dir.name
            print(f"{package_name}:")

            try:
                # Get installed packages in this deployment venv
                installed = _get_installed_packages(venv_path)

                # Build intersection - exclude the package itself
                to_check = [pkg for pkg in installed if pkg in available_local and pkg != package_name]

                if not to_check:
                    print("  (no local dependencies)\n")
                    continue

                # Collect planned updates for this deployment
                planned_updates = []

                for dep_name in sorted(to_check):
                    try:
                        # Get installed version
                        pkg_info = _get_package_info(dep_name, venv_path)
                        if not pkg_info:
                            continue

                        installed_version = pkg_info.get("Version", "")

                        # Get deployed version
                        deployed_version = self._get_deployed_version(dep_name)
                        if not deployed_version:
                            continue

                        # Compare versions
                        comparison = self._compare_versions(installed_version, deployed_version)

                        if comparison < 0:
                            planned_updates.append((dep_name, installed_version, deployed_version))

                    except Exception:
                        pass

                if not planned_updates:
                    print("  (all up-to-date)\n")
                    continue

                # Show planned updates table
                print(_format_update_table(planned_updates))
                print("\n  Proceeding with updates...")

                # Execute updates
                updated_this = 0

                for dep_name, installed_version, deployed_version in planned_updates:
                    try:
                        print(f"    {dep_name}: {installed_version} -> {deployed_version} ", end="", flush=True)
                        self._update_package(dep_name, venv_path)
                        print("done")
                        updated_this += 1
                        total_updated += 1
                    except PackageUpdateError as e:
                        print(f"failed ({e})")
                        total_errors.append((package_name, dep_name, str(e)))

                if updated_this > 0:
                    deployments_updated += 1

                print()

            except Exception as e:
                print(f"  Error scanning deployment: {e}\n")
                total_errors.append((package_name, "scan", str(e)))

        print(f"Summary: {total_updated} packages updated across {deployments_updated} deployments")

        if total_errors:
            print(f"\nErrors: {len(total_errors)}")
            for pkg, dep, error in total_errors:
                print(f"  {pkg}/{dep}: {error}")

        return {"updated": total_updated, "deployments": deployments_updated, "errors": len(total_errors)}


def main():
    """
    CLI entry point for package updater.
    """
    try:
        updater = PackageUpdater()

        # Check for VIRTUAL_ENV instead of is_virtual_environment()
        if os.environ.get("VIRTUAL_ENV"):
            updater.update_single_venv()
        else:
            updater.update_all_deployments()

    except PackageUpdateError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nAborted")
        sys.exit(130)


if __name__ == "__main__":
    main()
