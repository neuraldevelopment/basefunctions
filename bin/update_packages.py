#!/usr/bin/env python3
"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Update local neuraldevelopment packages in active venv or all deployments
 Log:
 v1.0 : Initial implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import sys
import os
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
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


class PackageUpdateError(Exception):
    """Package update operation failed."""

    pass


# -------------------------------------------------------------
# CLASS OR FUNCTION DEFINITIONS
# -------------------------------------------------------------


class PackageUpdater:
    """
    Update local neuraldevelopment packages in venv or deployments.
    """

    def __init__(self):
        self.deploy_dir = self._get_deployment_directory()
        self.packages_dir = self.deploy_dir / "packages"

    def _get_deployment_directory(self) -> Path:
        """
        Get deployment directory from bootstrap config.

        Returns
        -------
        Path
            Deployment directory path
        """
        deploy_dir = basefunctions.get_bootstrap_deployment_directory()
        return Path(deploy_dir).expanduser().resolve()

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

    def _update_package(self, package_name: str, venv_path: Optional[Path] = None) -> bool:
        """
        Update package in virtual environment.

        Parameters
        ----------
        package_name : str
            Package name to update
        venv_path : Optional[Path]
            Virtual environment path, uses current if None

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
            basefunctions.VenvUtils.run_pip_command(
                ["install", str(package_path)], venv_path, timeout=300, capture_output=False
            )
            return True
        except basefunctions.VenvUtilsError as e:
            raise PackageUpdateError(f"Failed to update {package_name}: {e}")

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

        if not basefunctions.VenvUtils.is_valid_venv(venv_path):
            raise PackageUpdateError(f"Invalid virtual environment: {venv_path}")

        # Block updates from basefunctions development directory
        cwd = Path.cwd()
        dev_paths = basefunctions.find_development_path("basefunctions")

        for dev_path in dev_paths:
            dev_path_resolved = Path(dev_path).resolve()
            if cwd == dev_path_resolved or dev_path_resolved in cwd.parents:
                raise PackageUpdateError("Cannot update from basefunctions development directory")

        print("Mode: Single venv update")
        print(f"Checking: {venv_path}\n")

        # Get installed packages
        installed = basefunctions.VenvUtils.get_installed_packages(
            venv_path, include_protected=False, capture_output=True
        )

        # Get available local packages
        available_local = self._get_available_local_packages()

        # Detect current development package to exclude it
        cwd = Path.cwd()
        current_package = None

        for pkg_name in available_local:
            dev_paths = basefunctions.find_development_path(pkg_name)
            for dev_path in dev_paths:
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

        print("Updates available:")

        updated = 0
        skipped = 0
        errors = []

        for package_name in sorted(to_check):
            try:
                # Get installed version
                pkg_info = basefunctions.VenvUtils.get_package_info(package_name, venv_path, capture_output=True)
                if not pkg_info:
                    print(f"  {package_name}: Could not read installed version")
                    errors.append((package_name, "Version read failed"))
                    continue

                installed_version = pkg_info.get("Version", "")

                # Get deployed version
                deployed_version = self._get_deployed_version(package_name)
                if not deployed_version:
                    print(f"  {package_name}: Could not read deployed version")
                    errors.append((package_name, "Deployed version not found"))
                    continue

                # Compare versions
                comparison = self._compare_versions(installed_version, deployed_version)

                if comparison < 0:
                    # Update needed
                    print(f"  {package_name}: {installed_version} → {deployed_version} ", end="")
                    self._update_package(package_name, venv_path)
                    print("✓")
                    updated += 1
                else:
                    # Already up-to-date
                    print(f"  {package_name}: {installed_version} (already up-to-date)")
                    skipped += 1

            except PackageUpdateError as e:
                print(f"  {package_name}: ✗ {e}")
                errors.append((package_name, str(e)))

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

            if not basefunctions.VenvUtils.is_valid_venv(venv_path):
                continue

            package_name = package_dir.name
            print(f"{package_name}:")

            try:
                # Get installed packages in this deployment venv
                installed = basefunctions.VenvUtils.get_installed_packages(
                    venv_path, include_protected=False, capture_output=True
                )

                # Build intersection
                to_check = [pkg for pkg in installed if pkg in available_local and pkg != package_name]

                if not to_check:
                    print("  (no local dependencies)\n")
                    continue

                updated_this = 0

                for dep_name in sorted(to_check):
                    try:
                        # Get installed version
                        pkg_info = basefunctions.VenvUtils.get_package_info(dep_name, venv_path, capture_output=True)
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
                            # Update needed
                            print(f"  {dep_name}: {installed_version} → {deployed_version} ", end="")
                            self._update_package(dep_name, venv_path)
                            print("✓")
                            updated_this += 1
                            total_updated += 1

                    except PackageUpdateError as e:
                        print(f"  {dep_name}: ✗ {e}")
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
