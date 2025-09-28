"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Common utilities for virtual environment operations
 Log:
 v1.0 : Initial implementation
 v2.0 : Migrated from prodtools to basefunctions with explicit capture_output control
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import sys
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple
import basefunctions

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------
PROTECTED_PACKAGES = ["pip", "setuptools", "wheel"]
DEFAULT_VENV_NAME = ".venv"

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


class VenvUtilsError(Exception):
    """Virtual environment utility operation failed."""

    pass


# -------------------------------------------------------------
# CLASS OR FUNCTION DEFINITIONS
# -------------------------------------------------------------


class VenvUtils:
    """
    Common utilities for virtual environment operations.
    Centralized functions to avoid code duplication across tools.
    """

    @staticmethod
    def get_pip_executable(venv_path: Path) -> Path:
        """
        Get platform-aware pip executable path for virtual environment.

        Parameters
        ----------
        venv_path : Path
            Path to virtual environment directory

        Returns
        -------
        Path
            Path to pip executable
        """
        if sys.platform == "win32":
            return venv_path / "Scripts" / "pip.exe"
        else:
            return venv_path / "bin" / "pip"

    @staticmethod
    def get_python_executable(venv_path: Path) -> Path:
        """
        Get platform-aware python executable path for virtual environment.

        Parameters
        ----------
        venv_path : Path
            Path to virtual environment directory

        Returns
        -------
        Path
            Path to python executable
        """
        if sys.platform == "win32":
            return venv_path / "Scripts" / "python.exe"
        else:
            return venv_path / "bin" / "python"

    @staticmethod
    def get_activate_script(venv_path: Path) -> Path:
        """
        Get platform-aware activate script path for virtual environment.

        Parameters
        ----------
        venv_path : Path
            Path to virtual environment directory

        Returns
        -------
        Path
            Path to activate script
        """
        if sys.platform == "win32":
            return venv_path / "Scripts" / "activate.bat"
        else:
            return venv_path / "bin" / "activate"

    @staticmethod
    def is_virtual_environment() -> bool:
        """
        Check if currently running in a virtual environment.

        Returns
        -------
        bool
            True if in virtual environment
        """
        return hasattr(sys, "real_prefix") or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix)

    @staticmethod
    def is_valid_venv(venv_path: Path) -> bool:
        """
        Check if path contains a valid virtual environment.

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

        # Check for essential executables
        pip_executable = VenvUtils.get_pip_executable(venv_path)
        python_executable = VenvUtils.get_python_executable(venv_path)

        return pip_executable.exists() and python_executable.exists()

    @staticmethod
    def find_venv_in_directory(directory: Path, venv_name: str = DEFAULT_VENV_NAME) -> Optional[Path]:
        """
        Find virtual environment in directory.

        Parameters
        ----------
        directory : Path
            Directory to search in
        venv_name : str, optional
            Virtual environment directory name

        Returns
        -------
        Optional[Path]
            Path to virtual environment if found, None otherwise
        """
        venv_path = directory / venv_name

        if VenvUtils.is_valid_venv(venv_path):
            return venv_path

        return None

    @staticmethod
    def get_installed_packages(
        venv_path: Optional[Path] = None, include_protected: bool = False, capture_output: bool = True
    ) -> List[str]:
        """
        Get list of installed packages in environment.

        Parameters
        ----------
        venv_path : Optional[Path], optional
            Path to virtual environment, uses current if None
        include_protected : bool, optional
            Include protected packages like pip, setuptools
        capture_output : bool
            Whether to capture command output or show live

        Returns
        -------
        List[str]
            List of installed package names

        Raises
        ------
        VenvUtilsError
            If listing packages fails
        """
        if venv_path:
            pip_executable = VenvUtils.get_pip_executable(venv_path)
        else:
            pip_executable = "pip"

        try:
            result = subprocess.run(
                [str(pip_executable), "list", "--format=freeze"],
                capture_output=capture_output,
                text=True,
                timeout=30,
                check=True,
            )

            packages = []
            output = result.stdout if capture_output else ""

            if capture_output:
                for line in output.strip().split("\n"):
                    if "==" in line:
                        package_name = line.split("==")[0]
                        if include_protected or package_name not in PROTECTED_PACKAGES:
                            packages.append(package_name)

            return packages

        except subprocess.CalledProcessError as e:
            raise VenvUtilsError(f"Failed to list packages: {e}")
        except subprocess.TimeoutExpired:
            raise VenvUtilsError("Package listing timed out")

    @staticmethod
    def get_package_info(
        package_name: str, venv_path: Optional[Path] = None, capture_output: bool = True
    ) -> Optional[dict]:
        """
        Get information about installed package.

        Parameters
        ----------
        package_name : str
            Name of the package
        venv_path : Optional[Path], optional
            Path to virtual environment, uses current if None
        capture_output : bool
            Whether to capture command output or show live

        Returns
        -------
        Optional[dict]
            Package information or None if not found
        """
        if venv_path:
            pip_executable = VenvUtils.get_pip_executable(venv_path)
        else:
            pip_executable = "pip"

        try:
            result = subprocess.run(
                [str(pip_executable), "show", package_name],
                capture_output=capture_output,
                text=True,
                timeout=15,
                check=True,
            )

            if not capture_output:
                return None

            info = {}
            for line in result.stdout.strip().split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    info[key.strip()] = value.strip()

            return info if info else None

        except subprocess.CalledProcessError:
            return None

    @staticmethod
    def run_pip_command(
        command: List[str], venv_path: Optional[Path] = None, timeout: int = 300, capture_output: bool = True
    ) -> subprocess.CompletedProcess:
        """
        Run pip command in virtual environment.

        Parameters
        ----------
        command : List[str]
            Pip command arguments (without 'pip')
        venv_path : Optional[Path], optional
            Path to virtual environment, uses current if None
        timeout : int, optional
            Command timeout in seconds
        capture_output : bool
            Whether to capture command output or show live

        Returns
        -------
        subprocess.CompletedProcess
            Command result

        Raises
        ------
        VenvUtilsError
            If command fails
        """
        if venv_path:
            pip_executable = VenvUtils.get_pip_executable(venv_path)
        else:
            pip_executable = "pip"

        full_command = [str(pip_executable)] + command

        try:
            return subprocess.run(full_command, check=True, timeout=timeout, capture_output=capture_output, text=True)
        except subprocess.CalledProcessError as e:
            raise VenvUtilsError(f"Pip command failed: {e}")
        except subprocess.TimeoutExpired:
            raise VenvUtilsError(f"Pip command timed out after {timeout}s")

    @staticmethod
    def upgrade_pip(venv_path: Path, capture_output: bool = True) -> None:
        """
        Upgrade pip in virtual environment.

        Parameters
        ----------
        venv_path : Path
            Path to virtual environment
        capture_output : bool
            Whether to capture command output or show live

        Raises
        ------
        VenvUtilsError
            If pip upgrade fails
        """
        VenvUtils.run_pip_command(
            ["install", "--upgrade", "pip"], venv_path, timeout=120, capture_output=capture_output
        )

    @staticmethod
    def install_requirements(venv_path: Path, requirements_file: Path, capture_output: bool = True) -> None:
        """
        Install requirements file in virtual environment.

        Parameters
        ----------
        venv_path : Path
            Path to virtual environment
        requirements_file : Path
            Path to requirements file
        capture_output : bool
            Whether to capture command output or show live

        Raises
        ------
        VenvUtilsError
            If requirements installation fails
        """
        if not requirements_file.exists():
            raise VenvUtilsError(f"Requirements file not found: {requirements_file}")

        VenvUtils.run_pip_command(["install", "-r", str(requirements_file)], venv_path, capture_output=capture_output)

    @staticmethod
    def uninstall_packages(packages: List[str], venv_path: Optional[Path] = None, capture_output: bool = True) -> None:
        """
        Uninstall packages from virtual environment.

        Parameters
        ----------
        packages : List[str]
            List of package names to uninstall
        venv_path : Optional[Path], optional
            Path to virtual environment, uses current if None
        capture_output : bool
            Whether to capture command output or show live

        Raises
        ------
        VenvUtilsError
            If uninstallation fails
        """
        if not packages:
            return

        command = ["uninstall", "-y"] + packages
        VenvUtils.run_pip_command(command, venv_path, capture_output=capture_output)

    @staticmethod
    def get_venv_size(venv_path: Path) -> int:
        """
        Get virtual environment size in bytes.

        Parameters
        ----------
        venv_path : Path
            Path to virtual environment

        Returns
        -------
        int
            Size in bytes
        """
        if not venv_path.exists():
            return 0

        total_size = 0
        for file_path in venv_path.rglob("*"):
            if file_path.is_file():
                try:
                    total_size += file_path.stat().st_size
                except (OSError, FileNotFoundError):
                    continue

        return total_size

    @staticmethod
    def format_size(size_bytes: int) -> str:
        """
        Format size in human-readable format.

        Parameters
        ----------
        size_bytes : int
            Size in bytes

        Returns
        -------
        str
            Formatted size string
        """
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
