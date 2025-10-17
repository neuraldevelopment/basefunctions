#!/usr/bin/env python3
"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Personal pip - local packages first, then PyPI fallback (standalone)
 Log:
 v1.0 : Initial implementation
 v2.0 : Standalone version without basefunctions dependency
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import sys
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
import re

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------
BOOTSTRAP_CONFIG_PATH = Path("~/.config/basefunctions/bootstrap.json").expanduser()

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
class PersonalPipError(Exception):
    """Personal pip operation failed."""

    pass


# -------------------------------------------------------------
# CLASS OR FUNCTION DEFINITIONS
# -------------------------------------------------------------
class PersonalPip:
    """
    Personal pip wrapper - local packages first, then PyPI.
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

        Raises
        ------
        PersonalPipError
            If config cannot be read
        """
        if not BOOTSTRAP_CONFIG_PATH.exists():
            raise PersonalPipError(f"Bootstrap config not found at {BOOTSTRAP_CONFIG_PATH}")

        try:
            with open(BOOTSTRAP_CONFIG_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)

            deploy_dir = config["bootstrap"]["paths"]["deployment_directory"]
            return Path(deploy_dir).expanduser().resolve()
        except (KeyError, json.JSONDecodeError) as e:
            raise PersonalPipError(f"Failed to read deployment directory from config: {e}")

    def discover_local_packages(self) -> List[str]:
        """
        Discover available local packages.

        Returns
        -------
        List[str]
            List of local package names
        """
        if not self.packages_dir.exists():
            return []

        packages = []
        for item in self.packages_dir.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                packages.append(item.name)

        return sorted(packages)

    def get_local_package_version(self, package_name: str) -> Optional[str]:
        """
        Get version from local package pyproject.toml.

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

    def get_installed_versions(self) -> Dict[str, str]:
        """
        Get versions of installed packages in current environment.

        Returns
        -------
        Dict[str, str]
            Dictionary mapping package names to versions
        """
        try:
            from importlib.metadata import distributions

            result = {}
            for dist in distributions():
                result[dist.name] = dist.version
            return result
        except Exception:
            return {}

    def is_in_virtual_env(self) -> bool:
        """
        Check if running in virtual environment.

        Returns
        -------
        bool
            True if in virtual environment
        """
        return hasattr(sys, "real_prefix") or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix)

    def install_package(self, package_name: str) -> bool:
        """
        Install package - local first, then PyPI.

        Parameters
        ----------
        package_name : str
            Package name to install

        Returns
        -------
        bool
            True if successful

        Raises
        ------
        PersonalPipError
            If installation fails
        """
        if not self.is_in_virtual_env():
            raise PersonalPipError("Not in virtual environment - activate venv first")

        local_packages = self.discover_local_packages()

        if package_name in local_packages:
            package_path = self.packages_dir / package_name
            print(f"Installing {package_name} from local packages...")

            try:
                result = subprocess.run(["pip", "install", str(package_path)], check=True)
                if result.returncode == 0:
                    print(f"✓ Successfully installed {package_name} (local)")
                    return True
            except subprocess.CalledProcessError as e:
                print(f"Local installation failed, trying PyPI: {e}")

        print(f"Installing {package_name} from PyPI...")
        try:
            result = subprocess.run(["pip", "install", package_name], check=True)
            if result.returncode == 0:
                print(f"✓ Successfully installed {package_name} (PyPI)")
                return True
        except subprocess.CalledProcessError as e:
            raise PersonalPipError(f"Installation failed: {e}")

        return False

    def list_packages(self) -> None:
        """
        List local and installed packages with versions.
        """
        local_packages = self.discover_local_packages()
        installed_versions = self.get_installed_versions()

        if local_packages:
            print("\nLocal Packages (available):")
            for package in sorted(local_packages, key=str.lower):
                version = self.get_local_package_version(package)
                version_str = f"v{version}" if version else "unknown"

                if package in installed_versions:
                    installed_ver = installed_versions[package]
                    print(f"  {package:<20} {version_str:<12} [installed: {installed_ver}]")
                else:
                    print(f"  {package:<20} {version_str:<12} [not installed]")
        else:
            print("\nLocal Packages: none")

        if installed_versions:
            print("\nInstalled Packages:")
            for package, version in sorted(installed_versions.items(), key=lambda x: x[0].lower()):
                if package in local_packages:
                    continue
                print(f"  {package:<20} {version:<12} [PyPI]")

    def forward_to_pip(self, args: List[str]) -> int:
        """
        Forward command to regular pip.

        Parameters
        ----------
        args : List[str]
            Command arguments to forward

        Returns
        -------
        int
            Exit code from pip
        """
        try:
            result = subprocess.run(["pip"] + args)
            return result.returncode
        except Exception as e:
            print(f"Error forwarding to pip: {e}")
            return 1


def main():
    """
    CLI entry point for personal pip.
    """
    if len(sys.argv) < 2:
        print("Usage: ppip <command> [args...]")
        print("\nCommands:")
        print("  install <package> [<package>...]  - Install packages (local first, then PyPI)")
        print("  list                              - List local and installed packages")
        print("  <anything else>                   - Forward to regular pip")
        sys.exit(1)

    command = sys.argv[1]

    try:
        ppip = PersonalPip()

        if command == "install":
            if len(sys.argv) < 3:
                print("Error: package name(s) required")
                print("Usage: ppip install <package> [<package>...]")
                sys.exit(1)

            package_names = sys.argv[2:]
            failed_packages = []
            successful_count = 0

            for package_name in package_names:
                try:
                    ppip.install_package(package_name)
                    successful_count += 1
                except PersonalPipError as e:
                    failed_packages.append((package_name, str(e)))

            if failed_packages:
                print(f"\n{successful_count} package(s) installed successfully")
                print("\nFailed installations:")
                for pkg, error in failed_packages:
                    print(f"  {pkg}: {error}")
                sys.exit(1)
            else:
                print(f"\nSummary: {successful_count} package(s) installed successfully")

        elif command == "list":
            ppip.list_packages()

        else:
            exit_code = ppip.forward_to_pip(sys.argv[1:])
            sys.exit(exit_code)

    except PersonalPipError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nAborted")
        sys.exit(130)


if __name__ == "__main__":
    main()
