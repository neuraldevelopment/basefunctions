#!/usr/bin/env python3
"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Create Python package structure with templates and GitHub integration
 Log:
 v1.0 : Initial implementation
 v1.1 : Integrated OutputFormatter for consistent output
 v2.0 : Migrated from prodtools to basefunctions
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import os
import subprocess
import shutil
import sys
from pathlib import Path
from typing import List, Optional
import basefunctions

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------
TEMPLATE_VARS = {"package_name": "<package_name>", "author": "<author>", "email": "<email>"}

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
class CreatePythonPackageError(Exception):
    """Python package creation failed."""

    pass


# -------------------------------------------------------------
# CLASS OR FUNCTION DEFINITIONS
# -------------------------------------------------------------
class CreatePythonPackage:
    """
    Create Python package structure with templates, licensing, and GitHub integration.
    """

    def __init__(self):
        self.logger = basefunctions.get_logger(__name__)
        self.formatter = basefunctions.OutputFormatter()
        self.config_handler = basefunctions.ConfigHandler()
        self._ensure_config_loaded()

    def create_package(
        self,
        package_name: Optional[str] = None,
        license_type: Optional[str] = None,
        github_repo: bool = False,
        github_private: bool = True,
        target_directory: Optional[Path] = None,
    ) -> Path:
        """
        Create complete Python package with interactive or programmatic setup.

        Parameters
        ----------
        package_name : Optional[str], optional
            Package name, prompts if None
        license_type : Optional[str], optional
            License type, prompts if None
        github_repo : bool, optional
            Create GitHub repository
        github_private : bool, optional
            Make GitHub repository private
        target_directory : Optional[Path], optional
            Target directory, uses current or package name if None

        Returns
        -------
        Path
            Path to created package

        Raises
        ------
        CreatePythonPackageError
            If package creation fails
        """
        self.formatter.show_header("Create Python Package")

        # Interactive selection if parameters not provided
        if package_name is None:
            package_name = self._select_package_name()

        if license_type is None:
            license_type = self._select_license()

        # Determine target directory
        if target_directory is None:
            current_dir = Path.cwd().name
            if package_name != current_dir:
                target_directory = Path.cwd() / package_name
            else:
                target_directory = Path.cwd()

        try:
            self.formatter.show_progress(f"Creating Python package: {package_name}")

            # Create directory structure
            self._create_directory_structure(target_directory, package_name)

            # Copy and process templates
            self.formatter.show_progress("Processing template files")
            self._process_templates(target_directory, package_name, license_type)

            # Create Python package structure
            self.formatter.show_progress("Creating package structure")
            self._create_package_structure(target_directory, package_name)

            # Initialize Git
            self.formatter.show_progress("Initializing Git repository")
            self._initialize_git(target_directory, package_name)

            # Create virtual environment and install package
            self.formatter.show_progress("Setting up virtual environment")
            self._setup_virtual_environment(target_directory)

            # Create GitHub repository if requested
            if github_repo:
                self.formatter.show_progress("Creating GitHub repository")
                self._create_github_repository(target_directory, package_name, github_private)

            details = {
                "package_name": package_name,
                "location": str(target_directory),
                "license": license_type,
                "github_repo": "Yes" if github_repo else "No",
            }
            self.formatter.show_result("Python package created successfully", True, details)
            return target_directory

        except Exception as e:
            self.formatter.show_result(f"Failed to create package: {e}", False)
            raise CreatePythonPackageError(f"Failed to create package: {e}")

    def list_available_licenses(self) -> List[str]:
        """
        Get list of available license templates by scanning template directory.

        Returns
        -------
        List[str]
            List of license names
        """
        template_path = self._get_template_path()
        licenses_dir = template_path / "licenses"

        if not licenses_dir.exists():
            return []

        licenses = []
        for license_file in licenses_dir.glob("*.license.txt"):
            license_name = license_file.stem.replace(".license", "")
            licenses.append(license_name)

        return sorted(licenses)

    def _ensure_config_loaded(self) -> None:
        """
        Ensure config is loaded for basefunctions package.
        """
        try:
            self.config_handler.load_config_for_package("basefunctions")
        except Exception as e:
            self.logger.critical(f"Failed to load config: {e}")
            raise CreatePythonPackageError(f"Config loading failed: {e}")

    def _get_template_path(self) -> Path:
        """
        Get templates directory path from configuration.

        Returns
        -------
        Path
            Path to templates directory
        """
        template_path = self.config_handler.get_config_parameter(
            "basefunctions/prodtools/create_python_package/template_path", "templates/python_package"
        )

        base_path = basefunctions.runtime.get_runtime_path("basefunctions")
        return Path(base_path) / template_path

    def _select_package_name(self) -> str:
        """
        Interactively select package name.

        Returns
        -------
        str
            Selected package name
        """
        current_dir = Path.cwd().name

        print("\nPackage name selection:")
        print(f"  1) {current_dir} (current directory)")
        print("  2) other (manual input)")

        while True:
            choice = input("Selection (1-2, default: 1): ").strip()
            if not choice:
                choice = "1"

            if choice == "1":
                return current_dir
            elif choice == "2":
                name = input("Enter package name: ").strip()
                if name:
                    return name
                print("Package name cannot be empty")
            else:
                print("Invalid selection")

    def _select_license(self) -> str:
        """
        Interactively select license.

        Returns
        -------
        str
            Selected license type
        """
        licenses = self.list_available_licenses()

        if not licenses:
            default_license = self.config_handler.get_config_parameter(
                "basefunctions/prodtools/create_python_package/default_license", "MIT"
            )
            print(f"No license templates found, using {default_license}")
            return default_license

        print("\nAvailable licenses:")
        for i, license_name in enumerate(licenses, 1):
            print(f"  {chr(96 + i)}) {license_name}")

        while True:
            choice = input(f"License selection (a-{chr(96 + len(licenses))}, default: a): ").strip().lower()
            if not choice:
                choice = "a"

            if choice.isalpha() and len(choice) == 1:
                index = ord(choice) - 97  # Convert 'a' to 0, 'b' to 1, etc.
                if 0 <= index < len(licenses):
                    return licenses[index]

            print("Invalid selection")

    def _create_directory_structure(self, target_directory: Path, package_name: str) -> None:
        """
        Create target directory if needed.

        Parameters
        ----------
        target_directory : Path
            Target directory path
        package_name : str
            Package name
        """
        if target_directory.name == package_name and not target_directory.exists():
            target_directory.mkdir(parents=True)
            os.chdir(target_directory)

    def _process_templates(self, target_directory: Path, package_name: str, license_type: str) -> None:
        """
        Process and copy template files.

        Parameters
        ----------
        target_directory : Path
            Target directory path
        package_name : str
            Package name
        license_type : str
            License type
        """
        # License file
        self._copy_license_file(target_directory, package_name, license_type)

        # Project files
        self._copy_template_file("pyproject.toml", target_directory, package_name)
        self._copy_template_file("README.md", target_directory, package_name)
        self._copy_file("gitignore", target_directory / ".gitignore")

        # VSCode settings
        self._copy_vscode_settings(target_directory)

    def _copy_license_file(self, target_directory: Path, package_name: str, license_type: str) -> None:
        """
        Copy and process license file.

        Parameters
        ----------
        target_directory : Path
            Target directory path
        package_name : str
            Package name
        license_type : str
            License type
        """
        template_path = self._get_template_path()
        license_file = template_path / "licenses" / f"{license_type}.license.txt"

        if license_file.exists():
            content = license_file.read_text(encoding="utf-8")
            content = content.replace(TEMPLATE_VARS["package_name"], package_name)
            (target_directory / "LICENSE").write_text(content, encoding="utf-8")
        else:
            self.logger.critical(f"License template not found: {license_type}")

    def _copy_template_file(self, filename: str, target_directory: Path, package_name: str) -> None:
        """
        Copy and process template file.

        Parameters
        ----------
        filename : str
            Template filename
        target_directory : Path
            Target directory path
        package_name : str
            Package name
        """
        template_path = self._get_template_path()
        template_file = template_path / filename
        target_file = target_directory / filename

        if template_file.exists():
            content = template_file.read_text(encoding="utf-8")
            content = content.replace(TEMPLATE_VARS["package_name"], package_name)
            target_file.write_text(content, encoding="utf-8")
        else:
            self.logger.critical(f"Template not found: {filename}")

    def _copy_file(self, source_name: str, target_path: Path) -> None:
        """
        Copy file without processing.

        Parameters
        ----------
        source_name : str
            Source filename
        target_path : Path
            Target file path
        """
        template_path = self._get_template_path()
        source_file = template_path / source_name

        if source_file.exists():
            shutil.copy2(source_file, target_path)

    def _copy_vscode_settings(self, target_directory: Path) -> None:
        """
        Copy VSCode settings directory.

        Parameters
        ----------
        target_directory : Path
            Target directory path
        """
        template_path = self._get_template_path()
        vscode_source = template_path / "vscode"
        vscode_target = target_directory / ".vscode"

        if vscode_source.exists():
            shutil.copytree(vscode_source, vscode_target, dirs_exist_ok=True)

    def _create_package_structure(self, target_directory: Path, package_name: str) -> None:
        """
        Create Python package structure.

        Parameters
        ----------
        target_directory : Path
            Target directory path
        package_name : str
            Package name
        """
        # Create src directory
        src_dir = target_directory / "src" / package_name
        src_dir.mkdir(parents=True, exist_ok=True)

        # Create __init__.py
        self._create_init_file(src_dir, package_name)

        # Create tests directory
        tests_dir = target_directory / "tests"
        tests_dir.mkdir(exist_ok=True)

        # Create test file
        self._create_test_file(tests_dir, package_name)

    def _create_init_file(self, src_dir: Path, package_name: str) -> None:
        """
        Create __init__.py file.

        Parameters
        ----------
        src_dir : Path
            Source directory path
        package_name : str
            Package name
        """
        template_path = self._get_template_path()
        init_template = template_path / "__init__.py"
        init_file = src_dir / "__init__.py"

        if init_template.exists():
            content = init_template.read_text(encoding="utf-8")
            content = content.replace(TEMPLATE_VARS["package_name"], package_name)
        else:
            content = f'"""{package_name} package."""\n\n__version__ = "0.1.0"\n'

        init_file.write_text(content, encoding="utf-8")

    def _create_test_file(self, tests_dir: Path, package_name: str) -> None:
        """
        Create test file.

        Parameters
        ----------
        tests_dir : Path
            Tests directory path
        package_name : str
            Package name
        """
        template_path = self._get_template_path()
        test_template = template_path / "test_template.py"
        test_file = tests_dir / f"test_{package_name}.py"

        if test_template.exists():
            content = test_template.read_text(encoding="utf-8")
            content = content.replace(TEMPLATE_VARS["package_name"], package_name)
        else:
            content = f'''"""Tests for {package_name} package."""

import pytest


def test_{package_name}_imports():
    """Test that {package_name} can be imported."""
    import {package_name}
    assert {package_name} is not None
'''

        test_file.write_text(content, encoding="utf-8")

    def _initialize_git(self, target_directory: Path, package_name: str) -> None:
        """
        Initialize Git repository.

        Parameters
        ----------
        target_directory : Path
            Target directory path
        package_name : str
            Package name
        """
        try:
            subprocess.run(["git", "init"], cwd=target_directory, check=True, capture_output=True)
            subprocess.run(["git", "add", "."], cwd=target_directory, check=True, capture_output=True)
            subprocess.run(
                ["git", "commit", "-m", f"Initial commit: Python package structure for {package_name}"],
                cwd=target_directory,
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as e:
            self.logger.critical(f"Git initialization failed: {e}")

    def _setup_virtual_environment(self, target_directory: Path) -> None:
        """
        Create virtual environment and install package.

        Parameters
        ----------
        target_directory : Path
            Target directory path
        """
        venv_path = target_directory / ".venv"

        try:
            # Create virtual environment
            subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True, timeout=120)

            # Upgrade pip using VenvUtils
            basefunctions.VenvUtils.upgrade_pip(venv_path, capture_output=True)

            # Install package in editable mode using VenvUtils
            basefunctions.VenvUtils.run_pip_command(["install", "-e", "."], venv_path, capture_output=False)

        except basefunctions.VenvUtilsError as e:
            self.logger.critical(f"Virtual environment setup failed: {e}")
        except Exception as e:
            self.logger.critical(f"Virtual environment setup failed: {e}")

    def _create_github_repository(self, target_directory: Path, package_name: str, private: bool) -> None:
        """
        Create GitHub repository using GitHub CLI.

        Parameters
        ----------
        target_directory : Path
            Target directory path
        package_name : str
            Package name
        private : bool
            Make repository private
        """
        if not shutil.which("gh"):
            self.logger.critical("GitHub CLI not found, skipping repository creation")
            return

        try:
            # Check if gh is authenticated
            subprocess.run(["gh", "auth", "status"], check=True, capture_output=True)

            # Create repository
            visibility_flag = "--private" if private else "--public"
            subprocess.run(
                [
                    "gh",
                    "repo",
                    "create",
                    package_name,
                    visibility_flag,
                    "--description",
                    f"Python package: {package_name}",
                ],
                cwd=target_directory,
                check=True,
                capture_output=True,
            )

            # Add remote and push
            result = subprocess.run(
                ["gh", "api", "user", "--jq", ".login"], capture_output=True, text=True, check=True
            )
            username = result.stdout.strip()

            subprocess.run(
                ["git", "remote", "add", "origin", f"https://github.com/{username}/{package_name}.git"],
                cwd=target_directory,
                check=True,
                capture_output=True,
            )

            subprocess.run(["git", "branch", "-M", "main"], cwd=target_directory, check=True, capture_output=True)
            subprocess.run(
                ["git", "push", "-u", "origin", "main"], cwd=target_directory, check=True, capture_output=True
            )

        except subprocess.CalledProcessError as e:
            self.logger.critical(f"GitHub repository creation failed: {e}")


def main():
    """
    CLI entry point for Python package creation.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Create Python package structure")
    parser.add_argument("--name", "-n", help="Package name (interactive if not provided)")
    parser.add_argument("--license", "-l", help="License type (interactive if not provided)")
    parser.add_argument("--github", "-g", action="store_true", help="Create GitHub repository")
    parser.add_argument("--public", action="store_true", help="Make GitHub repository public")
    parser.add_argument("--directory", "-d", type=Path, help="Target directory")
    parser.add_argument("--list-licenses", action="store_true", help="List available licenses")

    args = parser.parse_args()

    creator = CreatePythonPackage()

    try:
        if args.list_licenses:
            formatter = basefunctions.OutputFormatter()
            formatter.show_header("Available Licenses")
            formatter.show_progress("Scanning license templates")

            licenses = creator.list_available_licenses()
            if licenses:
                details = {"license_count": len(licenses)}
                formatter.show_result("License templates found", True, details)
                print("\nAvailable licenses:")
                for i, license_name in enumerate(licenses, 1):
                    print(f"  {chr(96 + i)}) {license_name}")
            else:
                formatter.show_result("No license templates found", False)
            return

        package_path = creator.create_package(
            package_name=args.name,
            license_type=args.license,
            github_repo=args.github,
            github_private=not args.public,
            target_directory=args.directory,
        )

        print(f"\nNext steps:")
        print("  1. source .venv/bin/activate")
        print(f"  2. Start coding in src/{package_path.name}/")

    except CreatePythonPackageError as e:
        formatter = basefunctions.OutputFormatter()
        formatter.show_result(str(e), False)
        sys.exit(1)


if __name__ == "__main__":
    main()
