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
 v3.0 : Redesigned list output to KPI-style with alphabetical sorting
 v3.1 : Added --all flag to list command (default: local only, --all: includes PyPI)
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import json
import re
import subprocess
import sys
from importlib.metadata import distributions
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# Basefunctions modules (only if available)
try:
    from basefunctions.utils.table_renderer import render_table
except ImportError:
    render_table = None

# Conditional TOML library import (Python 3.11+ has tomllib, older versions need tomli)
try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # type: ignore[import-not-found]
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
        assert local_version is not None and installed_version is not None
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

    def format_package_output(self, packages: List[tuple]) -> str:
        """
        Format packages as KPI-style output with two sections.

        Parameters
        ----------
        packages : List[tuple]
            List of package tuples: (name, available, installed, status)

        Returns
        -------
        str
            Formatted output string with Local Packages and PyPI Packages sections
        """
        # Status to emoji and text mapping
        STATUS_EMOJI = {
            "current": "✅",
            "update_available": "🟠",
            "not_installed": "❌",
            "pypi": "📦",
        }

        STATUS_TEXT = {
            "current": "Current",
            "update_available": "Update Available",
            "not_installed": "Not Installed",
            "pypi": "PyPI",
        }

        if not packages:
            return ""

        lines = []

        # Split packages into local and PyPI sections
        local_packages = []
        pypi_packages = []

        for pkg in packages:
            if pkg[0] == "__separator__":
                continue
            # Check status to determine section
            if pkg[3] == "pypi":
                pypi_packages.append(pkg)
            else:
                local_packages.append(pkg)

        # Calculate column widths for local packages
        if local_packages:
            name_width = max(len(pkg[0]) for pkg in local_packages)
            name_width = max(name_width, 20)  # Minimum 20 chars
        else:
            name_width = 20

        # Local Packages section
        if local_packages:
            lines.append("Local Packages")
            lines.append("")
            for pkg in local_packages:
                name, available, installed, status = pkg
                available_str = available or "-"
                installed_str = installed or "-"
                emoji = STATUS_EMOJI[status]
                status_text = STATUS_TEXT[status]

                # Format: "  {name:<20}  {available:>8}  →  {installed:>8}  {emoji} {status}"
                line = f"  {name:<{name_width}}  {available_str:>8}  →  {installed_str:>8}  {emoji} {status_text}"
                lines.append(line)

        # Blank separator between sections
        if local_packages and pypi_packages:
            lines.append("")

        # PyPI Packages section
        if pypi_packages:
            lines.append("PyPI Packages")
            lines.append("")

            # Calculate width for PyPI packages
            pypi_name_width = max(len(pkg[0]) for pkg in pypi_packages)
            pypi_name_width = max(pypi_name_width, 20)

            for pkg in pypi_packages:
                name, _, installed, _ = pkg
                installed_str = installed or "-"

                # Format: "  {name:<20}  {version:>8}"
                line = f"  {name:<{pypi_name_width}}  {installed_str:>8}"
                lines.append(line)

        return "\n".join(lines)

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
        Sort packages alphabetically within local and PyPI groups.

        Parameters
        ----------
        packages : List[tuple]
            List of package tuples: (name, available, installed, status)

        Returns
        -------
        List[tuple]
            Sorted packages list with separator between local and PyPI packages
        """
        # Separate local and PyPI packages
        local_packages = [pkg for pkg in packages if pkg[3] != "pypi"]
        pypi_packages = [pkg for pkg in packages if pkg[3] == "pypi"]

        # Sort local packages alphabetically (case-insensitive)
        sorted_local = sorted(local_packages, key=lambda pkg: pkg[0].lower())

        # Sort PyPI packages alphabetically (case-insensitive)
        sorted_pypi = sorted(pypi_packages, key=lambda pkg: pkg[0].lower())

        # Combine with separator if both groups exist
        if sorted_local and sorted_pypi:
            return sorted_local + [("__separator__", None, None, None)] + sorted_pypi
        elif sorted_local:
            return sorted_local
        else:
            return sorted_pypi

    def _format_packages_as_grid(self, packages: List[tuple]) -> str:
        """Format packages using KPI-style output."""
        return self.format_package_output(packages)

    def _format_status(self, status: str) -> str:
        """
        Format status string with emoji and text.

        Parameters
        ----------
        status : str
            Status code: "current", "update_available", "not_installed"

        Returns
        -------
        str
            Formatted status with emoji and text (e.g., "✅ Current")
        """
        STATUS_EMOJI = {
            "current": "✅",
            "update_available": "🟠",
            "not_installed": "❌",
        }

        STATUS_TEXT = {
            "current": "Current",
            "update_available": "Update Available",
            "not_installed": "Not Installed",
        }

        emoji = STATUS_EMOJI.get(status, "")
        text = STATUS_TEXT.get(status, status)

        return f"{emoji} {text}"

    def _format_local_packages_table(
        self,
        packages: List[tuple],
        return_widths: bool = False
    ) -> Union[str, Tuple[str, Dict[str, Any]]]:
        """
        Format local packages as table using render_table().

        Parameters
        ----------
        packages : List[tuple]
            List of package tuples: (name, available, installed, status)
            Only packages with status != "pypi" should be included.
        return_widths : bool, default False
            If True, return tuple of (table_string, widths_dict).
            If False, return only table_string.

        Returns
        -------
        str or tuple
            If return_widths=False: Formatted table string with 4 columns.
            If return_widths=True: Tuple of (table_string, widths_dict).
        """
        if render_table is None:
            # Fallback if basefunctions not available
            return ("", {}) if return_widths else ""

        # Filter local packages (status != "pypi" and not separator)
        local_pkgs = [p for p in packages if p[3] != "pypi" and p[0] != "__separator__"]

        if not local_pkgs:
            return ("", {}) if return_widths else ""

        # Build data rows
        headers = ["Package", "Available", "Installed", "Status"]
        data = []

        for name, available, installed, status in local_pkgs:
            status_text = self._format_status(status)
            data.append([name, available or "-", installed or "-", status_text])

        # Define column specifications for better version column width
        # Package: auto-width, Available: min 12 chars (right-aligned),
        # Installed: min 15 chars (right-aligned), Status: auto-width
        column_specs = [None, "right:12", "right:15", None]

        # Render table with fancy_grid theme and row_separators=False
        return render_table(
            data,
            headers,
            column_specs=column_specs,
            theme="fancy_grid",
            return_widths=return_widths,
            row_separators=False
        )

    def _format_pypi_packages_table(
        self,
        packages: List[tuple],
        enforce_widths: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Format PyPI packages as table using render_table().

        Parameters
        ----------
        packages : List[tuple]
            List of package tuples: (name, available, installed, status)
            Only packages with status == "pypi" should be included.
        enforce_widths : dict, optional
            Widths dict from local table to enforce same column widths.
            If provided, PyPI table will use same widths as local table.

        Returns
        -------
        str
            Formatted table string with 4 columns (Package, Available, Installed, Status).
            Available column is empty, Status shows "📦 PyPI" for all packages.
        """
        if render_table is None:
            # Fallback if basefunctions not available
            return ""

        # Filter PyPI packages (status == "pypi" and not separator)
        pypi_pkgs = [p for p in packages if p[3] == "pypi" and p[0] != "__separator__"]

        if not pypi_pkgs:
            return ""

        # Build data rows with 4 columns (same as local table)
        headers = ["Package", "Available", "Installed", "Status"]
        data = []

        for name, _, installed, _ in pypi_pkgs:
            # Empty Available column, Status shows PyPI indicator
            data.append([name, "", installed or "-", "📦 PyPI"])

        # Define column specifications (same as local table)
        column_specs = [None, "right:12", "right:15", None]

        # Render table with fancy_grid theme and row_separators=False
        if enforce_widths:
            return render_table(
                data,
                headers,
                column_specs=column_specs,
                theme="fancy_grid",
                enforce_widths=enforce_widths,
                row_separators=False
            )
        else:
            return render_table(
                data,
                headers,
                column_specs=column_specs,
                theme="fancy_grid",
                row_separators=False
            )

    def _format_packages_as_tables(self, packages: List[tuple]) -> str:
        """
        Format packages as separate local and PyPI tables with synchronized widths.

        Parameters
        ----------
        packages : List[tuple]
            List of package tuples: (name, available, installed, status)

        Returns
        -------
        str
            Formatted output with separate tables for local and PyPI packages.
            Both tables have identical widths when both are present.
        """
        if render_table is None:
            # Fallback to old format if basefunctions not available
            return self.format_package_output(packages)

        lines = []

        # Separate packages (filter out separator)
        local_packages = [p for p in packages if p[3] != "pypi" and p[0] != "__separator__"]
        pypi_packages = [p for p in packages if p[3] == "pypi" and p[0] != "__separator__"]

        if local_packages:
            if pypi_packages:
                # Both local and PyPI packages - synchronize widths
                # Render local table with return_widths=True
                result = self._format_local_packages_table(
                    local_packages,
                    return_widths=True
                )
                # Type guard: when return_widths=True, result is always a tuple
                if isinstance(result, tuple):
                    local_output, widths = result
                else:
                    # Fallback (should never happen)
                    local_output = result
                    widths = None

                lines.append(local_output)
                lines.append("")  # Blank line separator
                lines.append("PyPI Packages")

                # Render PyPI table with enforce_widths
                pypi_output = self._format_pypi_packages_table(
                    pypi_packages,
                    enforce_widths=widths
                )
                lines.append(pypi_output)
            else:
                # Only local packages - no width synchronization needed
                local_output = self._format_local_packages_table(local_packages)
                lines.append(local_output)

        elif pypi_packages:
            # Only PyPI packages
            lines.append("PyPI Packages")
            pypi_output = self._format_pypi_packages_table(pypi_packages)
            lines.append(pypi_output)

        return "\n".join(lines)


    def list_packages(self, show_all: bool = False) -> None:
        """
        List local and installed packages with versions using grid table format.

        Parameters
        ----------
        show_all : bool, default False
            If True, includes PyPI-only packages. If False, shows only local packages.
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

        # Add PyPI-only packages (not in local packages) ONLY if show_all=True
        if show_all:
            for package, version in installed_versions.items():
                if package not in local_packages:
                    packages.append((package, None, version, "pypi"))

        # Sort packages for display
        packages = self.sort_packages_for_display(packages)

        # Format and print using new table format with width synchronization
        output = self._format_packages_as_tables(packages)
        print(output)

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
        print("  list                              - List local packages only")
        print("  list --all                        - List local and PyPI packages")
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
            # Check for --all flag
            show_all = "--all" in sys.argv[2:]
            ppip.list_packages(show_all=show_all)

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
