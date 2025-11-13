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
 v2.1 : Added .gitignore template copy functionality
 v2.2 : Added .vscode/settings.json copy and dev tools installation
 v2.3 : Refactored template directory structure
 v2.4 : Added .claude directory copy functionality
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

            # Copy .gitignore template
            self._copy_gitignore_template(target_directory)

            # Copy .vscode/settings.json template
            self._copy_vscode_settings(target_directory)

            # Copy .claude directory
            self._copy_claude_settings(target_directory)

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
            if not choice or choice == "1":
                return current_dir
            elif choice == "2":
                package_name = input("Package name: ").strip()
                if package_name:
                    return package_name
                print("Error: Package name cannot be empty")
            else:
                print("Error: Invalid selection")

    def _select_license(self) -> str:
        """
        Interactively select license type.

        Returns
        -------
        str
            Selected license type
        """
        licenses = self.list_available_licenses()

        if not licenses:
            return "mit"

        print("\nAvailable licenses:")
        for i, license_name in enumerate(licenses, 1):
            print(f"  {chr(96 + i)}) {license_name}")

        while True:
            choice = input(f"Selection (a-{chr(96 + len(licenses))}, default: a): ").strip().lower()
            if not choice:
                return licenses[0]

            if len(choice) == 1 and ord("a") <= ord(choice) <= ord(chr(96 + len(licenses))):
                index = ord(choice) - ord("a")
                return licenses[index]

            print("Error: Invalid selection")

    def _create_directory_structure(self, target_directory: Path, package_name: str) -> None:
        """
        Create basic directory structure.

        Parameters
        ----------
        target_directory : Path
            Target directory path
        package_name : str
            Package name
        """
        # Create main directories
        target_directory.mkdir(parents=True, exist_ok=True)
        (target_directory / "src" / package_name).mkdir(parents=True, exist_ok=True)
        (target_directory / "tests").mkdir(exist_ok=True)
        (target_directory / "docs").mkdir(exist_ok=True)
        (target_directory / ".vscode").mkdir(exist_ok=True)
        (target_directory / ".claude").mkdir(exist_ok=True)

    def _copy_gitignore_template(self, target_directory: Path) -> None:
        """
        Copy .gitignore template to target directory.

        Parameters
        ----------
        target_directory : Path
            Target directory path
        """
        template_path = self._get_template_path()
        gitignore_template = template_path / "project" / "gitignore"
        gitignore_target = target_directory / ".gitignore"

        if gitignore_template.exists():
            shutil.copy2(gitignore_template, gitignore_target)
        else:
            self.logger.warning(f"Template not found: {gitignore_template}")

    def _copy_vscode_settings(self, target_directory: Path) -> None:
        """
        Copy .vscode/settings.json template to target directory.

        Parameters
        ----------
        target_directory : Path
            Target directory path
        """
        template_path = self._get_template_path()
        vscode_template = template_path / "vscode" / "settings.json"
        vscode_target = target_directory / ".vscode" / "settings.json"

        if vscode_template.exists():
            shutil.copy2(vscode_template, vscode_target)
        else:
            self.logger.warning(f"Template not found: {vscode_template}")

    def _copy_claude_settings(self, target_directory: Path) -> None:
        """
        Copy .claude directory with settings to target directory.

        Parameters
        ----------
        target_directory : Path
            Target directory path
        """
        template_path = self._get_template_path()
        claude_template_dir = template_path / "claude"
        claude_target_dir = target_directory / ".claude"

        if claude_template_dir.exists():
            # Copy entire claude directory
            shutil.copytree(claude_template_dir, claude_target_dir, dirs_exist_ok=True)
        else:
            self.logger.warning(f"Template directory not found: {claude_template_dir}")

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
        template_path = self._get_template_path()

        # Copy and process README.md
        self._process_template_file(
            template_path / "project" / "README.md", target_directory / "README.md", package_name
        )

        # Copy and process pyproject.toml
        self._process_template_file(
            template_path / "project" / "pyproject.toml", target_directory / "pyproject.toml", package_name
        )

        # Copy license
        license_file = template_path / "licenses" / f"{license_type}.license.txt"
        if license_file.exists():
            shutil.copy2(license_file, target_directory / "LICENSE")
        else:
            self.logger.warning(f"License template not found: {license_file}")

    def _process_template_file(self, template_file: Path, target_file: Path, package_name: str) -> None:
        """
        Process template file and replace variables.

        Parameters
        ----------
        template_file : Path
            Template file path
        target_file : Path
            Target file path
        package_name : str
            Package name
        """
        if not template_file.exists():
            self.logger.warning(f"Template not found: {template_file}")
            return

        content = template_file.read_text(encoding="utf-8")

        # Replace template variables
        for var_name, var_value in TEMPLATE_VARS.items():
            if var_name == "package_name":
                content = content.replace(var_value, package_name)
            # Add more replacements here if needed

        target_file.write_text(content, encoding="utf-8")

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
        # Create src package directory
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
        init_template = template_path / "package" / "__init__.py"
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
        test_template = template_path / "tests" / "test_template.py"
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
        Create virtual environment and install package with dev dependencies.

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

            # Install package in editable mode with dev dependencies using VenvUtils
            basefunctions.VenvUtils.run_pip_command(
                ["install", "-e", ".[dev]"], venv_path, cwd=target_directory, capture_output=False
            )

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

            # Create repository with source flag to automatically link local repo
            visibility_flag = "--private" if private else "--public"
            subprocess.run(
                [
                    "gh",
                    "repo",
                    "create",
                    package_name,
                    visibility_flag,
                    "--source=.",
                    "--remote=origin",
                    "--description",
                    f"Python package: {package_name}",
                ],
                cwd=target_directory,
                check=True,
                capture_output=True,
            )

            # Push to GitHub
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
    parser.add_argument("name", nargs="?", help="Package name (interactive if not provided)")
    parser.add_argument("--license", "-l", help="License type (interactive if not provided)")
    parser.add_argument("--no-github", action="store_true", help="Skip GitHub repository creation")
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
            github_repo=not args.no_github,
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
