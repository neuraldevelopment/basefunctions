#!/usr/bin/env python3
"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Create new projects with configurable directory structure and templates
 Log:
 v1.0 : Initial implementation
 v1.1 : Integrated OutputFormatter for consistent output
 v2.0 : Migrated to unified basefunctions config system
 v3.0 : Migrated from prodtools to basefunctions with namespace preservation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import os
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import basefunctions

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------
DEFAULT_PROJECT_TYPE = "generic"
PROJECTS_ROOT = Path.home() / "Projects"
ACTIVE_DIR = PROJECTS_ROOT / "10-Planning"

DEFAULT_CONFIG = {
    "project_types": {
        "generic": {
            "directories": ["00-Planning", "20-Documents", "30-Assets", "40-Work", "50-Deliverables", "90-Archive"]
        },
        "code": {
            "directories": [
                "00-Planning",
                "10-Code",
                "20-Documents",
                "30-Assets",
                "40-Work",
                "50-Deliverables",
                "90-Archive",
            ]
        },
    }
}

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


class CreateProjectError(Exception):
    """Project creation failed."""

    pass


# -------------------------------------------------------------
# CLASS OR FUNCTION DEFINITIONS
# -------------------------------------------------------------


class CreateProject:
    """
    Create new projects with configurable directory structure and Git integration.
    """

    def __init__(self):
        self.logger = basefunctions.get_logger(__name__)
        self.formatter = basefunctions.OutputFormatter()
        self.config_handler = basefunctions.ConfigHandler()
        self._ensure_config_loaded()

    def create_project(
        self,
        name: str,
        project_type: str = DEFAULT_PROJECT_TYPE,
        enable_git: bool = False,
        target_directory: Optional[Path] = None,
    ) -> Path:
        """
        Create new project with specified configuration.

        Parameters
        ----------
        name : str
            Project name
        project_type : str, optional
            Project type from configuration
        enable_git : bool, optional
            Initialize Git repository
        target_directory : Optional[Path], optional
            Target directory, uses ACTIVE_DIR if None

        Returns
        -------
        Path
            Path to created project

        Raises
        ------
        CreateProjectError
            If project creation fails
        """
        self.formatter.show_header(f"Create Project: {name}")

        # Validate inputs
        self._validate_project_name(name)
        self._validate_project_type(project_type)

        # Generate project name with date
        full_project_name = self._generate_project_name(name)

        # Determine target directory
        if target_directory is None:
            target_directory = ACTIVE_DIR

        project_path = target_directory / full_project_name

        # Check if project already exists
        if project_path.exists():
            self.formatter.show_result(f"Project already exists: {project_path}", False)
            raise CreateProjectError(f"Project already exists: {project_path}")

        try:
            self.formatter.show_progress(f"Creating project structure: {full_project_name}")

            # Create project structure
            self._create_project_structure(project_path, project_type)

            # Create README
            self.formatter.show_progress("Creating README.md")
            self._create_readme(project_path, name, project_type)

            # Initialize Git if requested
            if enable_git:
                self.formatter.show_progress("Initializing Git repository")
                self._initialize_git(project_path)

            details = {
                "project_name": full_project_name,
                "location": str(project_path),
                "type": project_type,
                "git_enabled": "Yes" if enable_git else "No",
            }
            self.formatter.show_result("Project created successfully", True, details)
            return project_path

        except Exception as e:
            # Cleanup on error
            if project_path.exists():
                shutil.rmtree(project_path)
            self.formatter.show_result(f"Failed to create project: {e}", False)
            raise CreateProjectError(f"Failed to create project: {e}")

    def list_project_types(self) -> List[str]:
        """
        Get list of available project types.

        Returns
        -------
        List[str]
            List of project type names
        """
        project_types = self._get_project_types_config()
        return list(project_types.keys())

    def get_project_type_directories(self, project_type: str) -> List[str]:
        """
        Get directories for specific project type.

        Parameters
        ----------
        project_type : str
            Project type name

        Returns
        -------
        List[str]
            List of directory names

        Raises
        ------
        CreateProjectError
            If project type not found
        """
        project_types = self._get_project_types_config()

        if project_type not in project_types:
            raise CreateProjectError(f"Unknown project type: {project_type}")

        return project_types[project_type]["directories"]

    def add_project_type(self, name: str, directories: List[str]) -> None:
        """
        Add new project type to configuration.

        Note: This requires manual editing of config.json as basefunctions
        does not support config writing.

        Parameters
        ----------
        name : str
            Project type name
        directories : List[str]
            List of directory names
        """
        self.logger.critical(f"To add project type '{name}', manually edit config.json:")
        self.logger.critical(f"Add to basefunctions/prodtools/create_project/project_types section")
        self.logger.critical(f"Directories: {directories}")
        print(f"\nTo add project type '{name}', manually edit config.json:")
        print(f"Add the following to basefunctions/prodtools/create_project/project_types:")
        print(f'"{name}": {{"directories": {directories}}}')

    def _ensure_config_loaded(self) -> None:
        """Ensure config is loaded for basefunctions package."""
        try:
            self.config_handler.load_config_for_package("basefunctions")
        except Exception as e:
            self.logger.critical(f"Failed to load config, using defaults: {e}")

    def _get_project_types_config(self) -> Dict:
        """
        Get project types configuration with fallback to defaults.

        Returns
        -------
        Dict
            Project types configuration
        """
        project_types = self.config_handler.get_config_parameter(
            "basefunctions/prodtools/create_project/project_types"
        )
        if project_types is None:
            return DEFAULT_CONFIG["project_types"]
        return project_types

    def _validate_project_name(self, name: str) -> None:
        """
        Validate project name.

        Parameters
        ----------
        name : str
            Project name to validate

        Raises
        ------
        CreateProjectError
            If name is invalid
        """
        if not name:
            raise CreateProjectError("Project name cannot be empty")

        # Check for invalid characters
        import re

        if not re.match(r"^[a-zA-Z0-9_-]+$", name):
            raise CreateProjectError(
                "Project name contains invalid characters. Use only letters, numbers, underscore and dash."
            )

    def _validate_project_type(self, project_type: str) -> None:
        """
        Validate project type.

        Parameters
        ----------
        project_type : str
            Project type to validate

        Raises
        ------
        CreateProjectError
            If project type is invalid
        """
        project_types = self._get_project_types_config()

        if project_type not in project_types:
            available_types = list(project_types.keys())
            raise CreateProjectError(f"Unknown project type: {project_type}. Available: {available_types}")

    def _generate_project_name(self, name: str) -> str:
        """
        Generate full project name with date.

        Parameters
        ----------
        name : str
            Base project name

        Returns
        -------
        str
            Full project name with date
        """
        date = datetime.now().strftime("%Y-%m-%d")
        return f"{name}_{date}"

    def _create_project_structure(self, project_path: Path, project_type: str) -> None:
        """
        Create project directory structure.

        Parameters
        ----------
        project_path : Path
            Path to project
        project_type : str
            Project type
        """
        # Create main project directory
        project_path.mkdir(parents=True, exist_ok=True)

        # Get directories for project type
        directories = self.get_project_type_directories(project_type)

        # Create each directory
        for directory in directories:
            dir_path = project_path / directory
            dir_path.mkdir(parents=True, exist_ok=True)

    def _create_readme(self, project_path: Path, project_name: str, project_type: str) -> None:
        """
        Create README.md file.

        Parameters
        ----------
        project_path : Path
            Path to project
        project_name : str
            Original project name
        project_type : str
            Project type
        """
        creation_date = datetime.now().strftime("%Y-%m-%d")
        directories = self.get_project_type_directories(project_type)

        readme_content = f"""# {project_name}

**Status:** Planung  
**Typ:** {project_type}  
**Erstellt:** {creation_date}

## Beschreibung

[Hier die Projektbeschreibung einfügen]

## Struktur

Dieses Projekt folgt der {project_type} Projektstruktur:

"""

        # Add directory listing
        for directory in directories:
            readme_content += f"- **{directory}/**: [Zweck beschreiben]\n"

        readme_content += """
## Notizen

[Wichtige Notizen, Entscheidungen oder Links hier einfügen]
"""

        readme_path = project_path / "README.md"
        readme_path.write_text(readme_content, encoding="utf-8")

    def _initialize_git(self, project_path: Path) -> None:
        """
        Initialize Git repository.

        Parameters
        ----------
        project_path : Path
            Path to project

        Raises
        ------
        CreateProjectError
            If Git initialization fails
        """
        if not shutil.which("git"):
            self.logger.critical("Git not found, skipping repository initialization")
            return

        try:
            # Initialize git repository
            subprocess.run(["git", "init"], cwd=project_path, check=True, capture_output=True)

            # Create initial commit
            subprocess.run(["git", "add", "."], cwd=project_path, check=True, capture_output=True)

            subprocess.run(
                ["git", "commit", "-m", "Initial project structure"], cwd=project_path, check=True, capture_output=True
            )

        except subprocess.CalledProcessError as e:
            raise CreateProjectError(f"Git initialization failed: {e}")


def main():
    """CLI entry point for project creation."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Create new project with configurable structure")
    parser.add_argument("name", help="Project name")
    parser.add_argument(
        "--type", "-t", default=DEFAULT_PROJECT_TYPE, help=f"Project type (default: {DEFAULT_PROJECT_TYPE})"
    )
    parser.add_argument("--git", "-g", action="store_true", help="Initialize Git repository")
    parser.add_argument("--directory", "-d", type=Path, help="Target directory (default: ~/Projects/10-Planning)")
    parser.add_argument("--list-types", "-l", action="store_true", help="List available project types")

    args = parser.parse_args()

    creator = CreateProject()

    try:
        if args.list_types:
            formatter = basefunctions.OutputFormatter()
            formatter.show_header("Project Types")
            formatter.show_progress("Loading project type configuration")

            types = creator.list_project_types()
            details = {"available_types": len(types)}
            formatter.show_result("Project types loaded", True, details)

            print("\nAvailable project types:")
            for project_type in types:
                directories = creator.get_project_type_directories(project_type)
                print(f"  - {project_type}: {len(directories)} directories")
            return

        if not args.name:
            parser.error("Project name is required")

        project_path = creator.create_project(
            name=args.name, project_type=args.type, enable_git=args.git, target_directory=args.directory
        )

        print(f"\nNext steps:")
        print(f'  cd "{project_path}"')
        print(f"  Edit README.md to add project description")

    except CreateProjectError as e:
        formatter = basefunctions.OutputFormatter()
        formatter.show_result(str(e), False)
        sys.exit(1)


if __name__ == "__main__":
    main()
