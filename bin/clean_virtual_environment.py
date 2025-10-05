#!/usr/bin/env python3
"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : prodtools
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Clean Python environment by uninstalling packages
 Log:
 v1.0 : Initial implementation
 v2.0 : Refactored to use VenvUtils for common operations
 v2.1 : Integrated OutputFormatter for consistent output
 v2.2 : Fixed virtual environment detection logic
 v3.0 : Standalone implementation using only standard library
 v4.0 : Simple approach - direct package uninstall
 v5.0 : Removed venv restriction, added safety confirmation for global envs
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import argparse
import subprocess
import sys
from pathlib import Path

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------
PROTECTED = {"pip", "setuptools", "wheel"}

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
class CleanVirtualEnvironmentError(Exception):
    pass


# -------------------------------------------------------------
# CLASS OR FUNCTION DEFINITIONS
# -------------------------------------------------------------
class CleanVirtualEnvironment:

    def __init__(self):
        pass

    def is_project_venv(self, venv_path=None):
        """
        Check if current environment is a project virtual environment.
        Parameters
        ----------
        venv_path : Path, optional
            Path to check, defaults to sys.prefix
        Returns
        -------
        bool
            True if pyvenv.cfg exists
        """
        if venv_path is None:
            venv_path = Path(sys.prefix)
        return (venv_path / "pyvenv.cfg").exists()

    def get_packages(self, venv_path=None):
        """
        Get list of installed packages.
        Parameters
        ----------
        venv_path : Path, optional
            Virtual environment path
        Returns
        -------
        list
            Package names excluding protected packages
        """
        if venv_path:
            pip_exe = venv_path / ("Scripts/pip.exe" if sys.platform == "win32" else "bin/pip")
            cmd = [str(pip_exe), "list", "--format=freeze"]
        else:
            cmd = ["pip", "list", "--format=freeze"]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Failed to list packages: {result.stderr}")
            return []

        packages = []
        for line in result.stdout.strip().split("\n"):
            if "==" in line:
                pkg = line.split("==")[0].strip()
                if pkg.lower() not in PROTECTED:
                    packages.append(pkg)

        return packages

    def uninstall_package(self, pkg, venv_path=None):
        """
        Uninstall a package.
        Parameters
        ----------
        pkg : str
            Package name
        venv_path : Path, optional
            Virtual environment path
        Returns
        -------
        bool
            True if successful
        """
        if venv_path:
            pip_exe = venv_path / ("Scripts/pip.exe" if sys.platform == "win32" else "bin/pip")
            cmd = [str(pip_exe), "uninstall", "--yes", pkg]
        else:
            cmd = ["pip", "uninstall", "--yes", pkg]

        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0

    def confirm_cleanup(self):
        """
        Ask user for confirmation.
        Returns
        -------
        bool
            True if user confirms
        """
        response = input("This appears to be a global environment. Really clean? [y/N]: ")
        return response.lower() == "y"

    def clean_current_environment(self, skip_confirmation=False):
        """
        Clean current environment.
        Parameters
        ----------
        skip_confirmation : bool
            Skip confirmation prompt
        Returns
        -------
        int
            Number of removed packages
        """
        packages = self.get_packages()
        if not packages:
            print("No packages to remove")
            return 0

        if not self.is_project_venv() and not skip_confirmation:
            if not self.confirm_cleanup():
                print("Aborted")
                return 0

        print(f"Removing {len(packages)} packages")
        removed = 0

        for pkg in packages:
            if self.uninstall_package(pkg):
                removed += 1
                print(f"Removed {pkg}")
            else:
                print(f"Failed to remove {pkg}")

        return removed

    def clean_environment_at_path(self, venv_path, skip_confirmation=False):
        """
        Clean environment at specific path.
        Parameters
        ----------
        venv_path : Path
            Virtual environment path
        skip_confirmation : bool
            Skip confirmation prompt
        Returns
        -------
        int
            Number of removed packages
        """
        packages = self.get_packages(venv_path)
        if not packages:
            print("No packages to remove")
            return 0

        if not self.is_project_venv(venv_path) and not skip_confirmation:
            if not self.confirm_cleanup():
                print("Aborted")
                return 0

        print(f"Removing {len(packages)} packages")
        removed = 0

        for pkg in packages:
            if self.uninstall_package(pkg, venv_path):
                removed += 1
                print(f"Removed {pkg}")
            else:
                print(f"Failed to remove {pkg}")

        return removed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--venv", type=Path)
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--yes", action="store_true", help="Skip confirmation prompt")

    args = parser.parse_args()

    cleaner = CleanVirtualEnvironment()

    if args.list:
        packages = cleaner.get_packages(args.venv)
        if packages:
            print(f"Packages to remove ({len(packages)}):")
            for pkg in packages:
                print(f"  {pkg}")
        else:
            print("No packages to remove")
    else:
        if args.venv:
            removed = cleaner.clean_environment_at_path(args.venv, args.yes)
        else:
            removed = cleaner.clean_current_environment(args.yes)
        print(f"Removed {removed} packages")


if __name__ == "__main__":
    main()
