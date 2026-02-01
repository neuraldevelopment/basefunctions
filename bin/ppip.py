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
 v2.1 : Added two-pass dependency installation for local packages
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

# Conditional TOML library import (Python 3.11+ has tomllib, older versions need tomli)
try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None  # TOML parsing not available

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

    def _parse_local_package_dependencies(self, package_name: str) -> List[str]:
        """
        Parse dependencies from local package's pyproject.toml.

        Parameters
        ----------
        package_name : str
            Package name

        Returns
        -------
        List[str]
            List of dependency package names (no version specifiers)
        """
        pyproject_file = self.packages_dir / package_name / "pyproject.toml"

        if not pyproject_file.exists():
            return []

        if tomllib is None:
            # TOML parser not available - skip dependency resolution
            return []

        try:
            with open(pyproject_file, "rb") as f:
                data = tomllib.load(f)

            dependencies = data.get("project", {}).get("dependencies", [])

            packages = []
            for dep in dependencies:
                if isinstance(dep, str):
                    # Remove version specifiers and extras
                    pkg_name = dep.split(">=")[0].split("==")[0].split("~=")[0]
                    pkg_name = pkg_name.split("<")[0].split(">")[0].split("[")[0].strip()
                    packages.append(pkg_name)

            return packages
        except Exception:
            return []

    def install_packages_with_dependencies(self, package_names: List[str]) -> Dict[str, bool]:
        """
        Install packages with their local dependencies (two-pass approach).

        Parameters
        ----------
        package_names : List[str]
            List of package names to install

        Returns
        -------
        Dict[str, bool]
            Dictionary mapping package names to success status
        """
        if not self.is_in_virtual_env():
            raise PersonalPipError("Not in virtual environment - activate venv first")

        local_packages = set(self.discover_local_packages())
        installed_versions = self.get_installed_versions()

        # Collect all local dependencies
        all_local_deps = set()
        for pkg in package_names:
            if pkg not in local_packages:
                continue

            deps = self._parse_local_package_dependencies(pkg)
            local_deps = [d for d in deps if d in local_packages]
            all_local_deps.update(local_deps)

        # Remove already-installed and explicitly-requested packages
        to_install_deps = [d for d in all_local_deps if d not in package_names and d not in installed_versions]

        results = {}

        # Install dependencies first
        if to_install_deps:
            print(f"\nInstalling {len(to_install_deps)} local dependencies first...")
            for dep in to_install_deps:
                try:
                    success = self.install_package(dep)
                    results[dep] = success
                except PersonalPipError as e:
                    print(f"Dependency installation failed: {dep}: {e}")
                    results[dep] = False

        # Install requested packages
        for pkg in package_names:
            try:
                success = self.install_package(pkg)
                results[pkg] = success
            except PersonalPipError as e:
                print(f"Package installation failed: {pkg}: {e}")
                results[pkg] = False

        return results

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

    def get_package_status(self, local_version: Optional[str], installed_version: Optional[str]) -> str:
        """
        Determine package status by comparing versions.

        Parameters
        ----------
        local_version : Optional[str]
            Version from local package pyproject.toml (e.g., "1.2.3")
        installed_version : Optional[str]
            Version from installed package (e.g., "1.2.3")

        Returns
        -------
        str
            One of: "current", "update_available", "not_installed", "pypi"
        """
        # Both None -> not_installed
        if local_version is None and installed_version is None:
            return "not_installed"

        # Local version only (no installed) -> not_installed
        if local_version is not None and installed_version is None:
            return "not_installed"

        # Installed version only (no local) -> pypi
        if local_version is None and installed_version is not None:
            return "pypi"

        # Both exist -> compare versions
        local_parts = [int(x) for x in local_version.split(".")]
        installed_parts = [int(x) for x in installed_version.split(".")]

        # Compare major, minor, patch
        for local_part, installed_part in zip(local_parts, installed_parts):
            if local_part > installed_part:
                return "update_available"
            elif local_part < installed_part:
                return "current"

        # All parts equal -> current
        return "current"

    def format_package_table(self, packages: List[tuple]) -> str:
        """
        Format packages as a colored table with emoji indicators.

        Parameters
        ----------
        packages : List[tuple]
            List of package tuples: (name, available, installed, status)

        Returns
        -------
        str
            Formatted table string with ANSI colors and Unicode box drawing
        """
        # Status to emoji and color mapping
        STATUS_EMOJI = {
            "current": "✅",
            "update_available": "🟠",
            "not_installed": "❌",
            "pypi": "📦",
        }

        STATUS_COLOR = {
            "current": "\033[32m",  # Green
            "update_available": "\033[33m",  # Orange/Yellow
            "not_installed": "\033[31m",  # Red
            "pypi": "\033[34m",  # Blue
        }

        RESET_COLOR = "\033[0m"

        # Calculate column widths (skip separator entries)
        if packages:
            regular_packages = [pkg for pkg in packages if pkg[0] != "__separator__"]

            if regular_packages:
                name_width = max(len(pkg[0]) for pkg in regular_packages)
                name_width = max(name_width, 12)  # Minimum 12 chars

                available_width = max(len(pkg[1] or "-") for pkg in regular_packages)
                available_width = max(available_width, 12)

                installed_width = max(len(pkg[2] or "-") for pkg in regular_packages)
                installed_width = max(installed_width, 12)

                status_width = max(len(f"{STATUS_EMOJI[pkg[3]]} {pkg[3].replace('_', ' ').title()}") for pkg in regular_packages)
                status_width = max(status_width, 12)
            else:
                name_width = available_width = installed_width = status_width = 12
        else:
            name_width = available_width = installed_width = status_width = 12

        # Calculate total table width
        total_width = name_width + available_width + installed_width + status_width + 11  # +11 for borders & padding

        # Build table
        lines = []

        # Title - centered with decorative dashes, same width as table
        title_text = "Local & Installed Packages"
        padding = total_width - len(title_text) - 6  # -6 for "─── " and " ───"
        left_padding = padding // 2
        right_padding = padding - left_padding
        title_line = f"{'─' * 3} {' ' * left_padding}{title_text}{' ' * right_padding} {'─' * 3}"
        lines.append(title_line)

        # Top border
        lines.append(f"┌{'─' * (name_width + 2)}┬{'─' * (available_width + 2)}┬{'─' * (installed_width + 2)}┬{'─' * (status_width + 2)}┐")

        # Header
        lines.append(
            f"│ {'Package':<{name_width}} │ {'Available':<{available_width}} │ {'Installed':<{installed_width}} │ {'Status':<{status_width}} │"
        )

        # Header separator
        lines.append(f"├{'─' * (name_width + 2)}┼{'─' * (available_width + 2)}┼{'─' * (installed_width + 2)}┼{'─' * (status_width + 2)}┤")

        # Data rows
        for pkg in packages:
            name, available, installed, status = pkg

            # Check if this is the separator
            if name == "__separator__":
                # Render separator line
                lines.append(f"├{'─' * (name_width + 2)}┼{'─' * (available_width + 2)}┼{'─' * (installed_width + 2)}┼{'─' * (status_width + 2)}┤")
                continue

            available_str = available or "-"
            installed_str = installed or "-"

            emoji = STATUS_EMOJI[status]
            color = STATUS_COLOR[status]
            status_text = status.replace("_", " ").title()
            status_display = f"{color}{emoji} {status_text}{RESET_COLOR}"

            # Calculate display width for status (without ANSI codes)
            status_display_width = len(f"{emoji} {status_text}")
            padding = status_width - status_display_width

            lines.append(
                f"│ {name:<{name_width}} │ {available_str:>{available_width}} │ {installed_str:>{installed_width}} │ {status_display}{' ' * padding} │"
            )

        # Bottom border
        lines.append(f"└{'─' * (name_width + 2)}┴{'─' * (available_width + 2)}┴{'─' * (installed_width + 2)}┴{'─' * (status_width + 2)}┘")

        return "\n".join(lines)

    def sort_packages_for_display(self, packages: List[tuple]) -> List[tuple]:
        """
        Sort packages for display priority.

        Parameters
        ----------
        packages : List[tuple]
            List of package tuples: (name, available, installed, status)

        Returns
        -------
        List[tuple]
            Sorted packages list with separator between local and PyPI packages
        """
        # Status priority order
        STATUS_PRIORITY = {
            "update_available": 1,
            "not_installed": 2,
            "current": 3,
            "pypi": 4,
        }

        # Separate local and PyPI packages
        local_packages = [pkg for pkg in packages if pkg[3] != "pypi"]
        pypi_packages = [pkg for pkg in packages if pkg[3] == "pypi"]

        # Sort local packages by status priority, then alphabetically
        sorted_local = sorted(local_packages, key=lambda pkg: (STATUS_PRIORITY[pkg[3]], pkg[0].lower()))

        # Sort PyPI packages alphabetically
        sorted_pypi = sorted(pypi_packages, key=lambda pkg: pkg[0].lower())

        # Combine with separator if both groups exist
        if sorted_local and sorted_pypi:
            return sorted_local + [("__separator__", None, None, None)] + sorted_pypi
        elif sorted_local:
            return sorted_local
        else:
            return sorted_pypi

    def list_packages(self) -> None:
        """
        List local and installed packages with versions.
        """
        local_packages = self.discover_local_packages()
        installed_versions = self.get_installed_versions()

        # Build package list with status
        packages = []

        # Add local packages
        for package in local_packages:
            local_version = self.get_local_package_version(package)
            installed_version = installed_versions.get(package)
            status = self.get_package_status(local_version, installed_version)
            packages.append((package, local_version, installed_version, status))

        # Add PyPI-only packages (not in local packages)
        for package, version in installed_versions.items():
            if package not in local_packages:
                packages.append((package, None, version, "pypi"))

        # Sort packages for display
        packages = self.sort_packages_for_display(packages)

        # Format and print table
        table = self.format_package_table(packages)
        print(table)

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

            # Use dependency-aware installation
            results = ppip.install_packages_with_dependencies(package_names)

            failed = [pkg for pkg, success in results.items() if not success]
            successful = [pkg for pkg, success in results.items() if success]

            if failed:
                print(f"\n{len(successful)} package(s) installed successfully")
                print("\nFailed installations:")
                for pkg in failed:
                    print(f"  {pkg}")
                sys.exit(1)
            else:
                print(f"\nSummary: {len(successful)} package(s) installed successfully")

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
