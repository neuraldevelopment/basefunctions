#!/usr/bin/env python3
"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Create Python virtual environment - refactored with VenvUtils
 Log:
 v1.0 : Initial implementation
 v2.0 : Refactored to use VenvUtils for common operations
 v2.1 : Integrated OutputFormatter for consistent output
 v3.0 : Migrated from prodtools to basefunctions
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import sys
import venv
import shutil
from pathlib import Path
from typing import Optional
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
basefunctions.setup_logger(__name__)

# -------------------------------------------------------------
# TYPE DEFINITIONS
# -------------------------------------------------------------


# -------------------------------------------------------------
# EXCEPTION DEFINITIONS
# -------------------------------------------------------------
class CreateVirtualEnvironmentError(Exception):
    """Virtual environment creation failed."""

    pass


# -------------------------------------------------------------
# CLASS OR FUNCTION DEFINITIONS
# -------------------------------------------------------------
class CreateVirtualEnvironment:
    """
    Create and configure Python virtual environments using VenvUtils.
    """

    def __init__(self):
        self.logger = basefunctions.get_logger(__name__)
        self.formatter = basefunctions.OutputFormatter()

    def create(self, directory: Optional[Path] = None, venv_name: str = ".venv") -> Path:
        """
        Create virtual environment in specified directory.

        Parameters
        ----------
        directory : Optional[Path], optional
            Target directory, uses current directory if None
        venv_name : str, optional
            Virtual environment directory name, default '.venv'

        Returns
        -------
        Path
            Path to created virtual environment

        Raises
        ------
        CreateVirtualEnvironmentError
            If virtual environment creation fails
        """
        if directory is None:
            directory = Path.cwd()
        else:
            directory = Path(directory)

        venv_path = directory / venv_name

        self.formatter.show_header(f"Create Virtual Environment: {venv_name}")

        # Check if venv already exists
        if venv_path.exists():
            self.formatter.show_result(f"Virtual environment already exists: {venv_path}", False)
            raise CreateVirtualEnvironmentError(f"Virtual environment already exists: {venv_path}")

        try:
            self.formatter.show_progress("Creating virtual environment")

            # Create virtual environment
            venv.create(venv_path, with_pip=True)

            self.formatter.show_progress("Upgrading pip")
            # Upgrade pip using VenvUtils
            basefunctions.VenvUtils.upgrade_pip(venv_path, capture_output=True)

            details = {
                "venv_path": str(venv_path),
                "activate_script": str(basefunctions.VenvUtils.get_activate_script(venv_path)),
            }
            self.formatter.show_result("Virtual environment created successfully", True, details)
            return venv_path

        except basefunctions.VenvUtilsError as e:
            # Clean up partial creation
            self._cleanup_venv(venv_path)
            self.formatter.show_result(f"Failed to upgrade pip: {e}", False)
            raise CreateVirtualEnvironmentError(f"Failed to upgrade pip: {e}") from e
        except Exception as e:
            # Clean up partial creation
            self._cleanup_venv(venv_path)
            self.formatter.show_result(f"Failed to create virtual environment: {e}", False)
            raise CreateVirtualEnvironmentError(f"Failed to create virtual environment: {e}") from e

    def create_with_requirements(
        self,
        directory: Optional[Path] = None,
        requirements_file: Optional[Path] = None,
        venv_name: str = ".venv",
    ) -> Path:
        """
        Create virtual environment and install requirements.

        Parameters
        ----------
        directory : Optional[Path], optional
            Target directory, uses current directory if None
        requirements_file : Optional[Path], optional
            Requirements file to install, looks for requirements.txt if None
        venv_name : str, optional
            Virtual environment directory name, default '.venv'

        Returns
        -------
        Path
            Path to created virtual environment

        Raises
        ------
        CreateVirtualEnvironmentError
            If creation or requirements installation fails
        """
        # Create base virtual environment
        venv_path = self.create(directory, venv_name)

        # Determine requirements file
        if requirements_file is None:
            base_dir = directory if directory else Path.cwd()
            requirements_file = base_dir / "requirements.txt"

        # Install requirements if file exists
        if requirements_file.exists():
            try:
                self.formatter.show_progress(f"Installing requirements from {requirements_file.name}")
                basefunctions.VenvUtils.install_requirements(venv_path, requirements_file, capture_output=False)
                # Update details with requirements info
                details = {
                    "venv_path": str(venv_path),
                    "requirements_file": str(requirements_file),
                    "activate_script": str(basefunctions.VenvUtils.get_activate_script(venv_path)),
                }
                self.formatter.show_result("Virtual environment with requirements created successfully", True, details)
            except basefunctions.VenvUtilsError as e:
                self.formatter.show_progress(f"Failed to install requirements: {e}")
                # Don't fail completely - venv is still usable

        return venv_path

    def recreate(self, directory: Optional[Path] = None, venv_name: str = ".venv") -> Path:
        """
        Remove existing virtual environment and create fresh one.

        Parameters
        ----------
        directory : Optional[Path], optional
            Target directory, uses current directory if None
        venv_name : str, optional
            Virtual environment directory name, default '.venv'

        Returns
        -------
        Path
            Path to created virtual environment
        """
        if directory is None:
            directory = Path.cwd()
        else:
            directory = Path(directory)

        venv_path = directory / venv_name

        self.formatter.show_header(f"Recreate Virtual Environment: {venv_name}")

        # Remove existing venv
        if venv_path.exists():
            self.formatter.show_progress("Removing existing virtual environment")
            self._cleanup_venv(venv_path)

        # Create fresh venv (use internal create to avoid double header)
        self.formatter.show_progress("Creating fresh virtual environment")

        try:
            # Create virtual environment
            venv.create(venv_path, with_pip=True)

            self.formatter.show_progress("Upgrading pip")
            # Upgrade pip using VenvUtils
            basefunctions.VenvUtils.upgrade_pip(venv_path, capture_output=True)

            details = {
                "venv_path": str(venv_path),
                "activate_script": str(basefunctions.VenvUtils.get_activate_script(venv_path)),
            }
            self.formatter.show_result("Virtual environment recreated successfully", True, details)
            return venv_path

        except basefunctions.VenvUtilsError as e:
            self._cleanup_venv(venv_path)
            self.formatter.show_result(f"Failed to upgrade pip: {e}", False)
            raise CreateVirtualEnvironmentError(f"Failed to upgrade pip: {e}") from e
        except Exception as e:
            self._cleanup_venv(venv_path)
            self.formatter.show_result(f"Failed to recreate virtual environment: {e}", False)
            raise CreateVirtualEnvironmentError(f"Failed to recreate virtual environment: {e}") from e

    def get_venv_info(self, venv_path: Path) -> dict:
        """
        Get information about virtual environment.

        Parameters
        ----------
        venv_path : Path
            Path to virtual environment

        Returns
        -------
        dict
            Virtual environment information
        """
        if not basefunctions.VenvUtils.is_valid_venv(venv_path):
            return {"valid": False, "error": "Invalid virtual environment"}

        try:
            packages = basefunctions.VenvUtils.get_installed_packages(
                venv_path, include_protected=True, capture_output=True
            )
            size = basefunctions.VenvUtils.get_venv_size(venv_path)

            info = {
                "valid": True,
                "path": str(venv_path),
                "python_executable": str(basefunctions.VenvUtils.get_python_executable(venv_path)),
                "pip_executable": str(basefunctions.VenvUtils.get_pip_executable(venv_path)),
                "activate_script": str(basefunctions.VenvUtils.get_activate_script(venv_path)),
                "package_count": len(packages),
                "packages": packages,
                "size_bytes": size,
                "size_formatted": basefunctions.VenvUtils.format_size(size),
            }

            return info

        except basefunctions.VenvUtilsError as e:
            return {"valid": False, "error": str(e)}

    def _cleanup_venv(self, venv_path: Path) -> None:
        """
        Remove virtual environment directory.

        Parameters
        ----------
        venv_path : Path
            Path to virtual environment to remove
        """
        if venv_path.exists():
            shutil.rmtree(venv_path)


def main():
    """
    CLI entry point for virtual environment creation.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Create Python virtual environment")
    parser.add_argument("--directory", "-d", type=Path, help="Target directory (default: current directory)")
    parser.add_argument("--name", "-n", default=".venv", help="Virtual environment name (default: .venv)")
    parser.add_argument("--requirements", "-r", type=Path, help="Requirements file to install")
    parser.add_argument("--recreate", action="store_true", help="Remove existing venv and create fresh one")
    parser.add_argument("--info", action="store_true", help="Show information about existing venv")

    args = parser.parse_args()

    creator = CreateVirtualEnvironment()

    try:
        if args.info:
            formatter = basefunctions.OutputFormatter()
            formatter.show_header("Virtual Environment Information")

            directory = args.directory if args.directory else Path.cwd()
            venv_path = directory / args.name

            formatter.show_progress("Analyzing virtual environment")
            info = creator.get_venv_info(venv_path)

            if info["valid"]:
                details = {
                    "path": info["path"],
                    "python": info["python_executable"],
                    "packages": info["package_count"],
                    "size": info["size_formatted"],
                    "activate": info["activate_script"],
                }
                formatter.show_result("Virtual environment analysis complete", True, details)

                if info["packages"]:
                    print("\nInstalled packages:")
                    for package in sorted(info["packages"]):
                        print(f"  - {package}")
            else:
                formatter.show_result(f"Error: {info['error']}", False)
                sys.exit(1)

        elif args.recreate:
            venv_path = creator.recreate(args.directory, args.name)

        elif args.requirements:
            venv_path = creator.create_with_requirements(args.directory, args.requirements, args.name)

        else:
            venv_path = creator.create(args.directory, args.name)

    except CreateVirtualEnvironmentError as e:
        formatter = basefunctions.OutputFormatter()
        formatter.show_result(str(e), False)
        sys.exit(1)


if __name__ == "__main__":
    main()
