#!/usr/bin/env python3
"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Sync template files (claude, vscode, pre-commit) to Python projects
 Log:
 v1.0 : Initial implementation - simple recursive sync
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import re
import shutil
import sys
from pathlib import Path
from typing import List, Optional
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


class TemplateSyncError(Exception):
    """Template sync operation failed."""

    pass


# -------------------------------------------------------------
# CLASS OR FUNCTION DEFINITIONS
# -------------------------------------------------------------


class TemplateSyncer:
    """
    Sync template files to Python projects with pyproject.toml.
    """

    def __init__(self):
        self.logger = basefunctions.get_logger(__name__)
        self.formatter = basefunctions.OutputFormatter()
        self.projects_found = 0
        self.projects_synced = 0

    def _find_projects(self, root: Path) -> List[Path]:
        """
        Find all Python projects (directories with pyproject.toml).

        Recursively searches directories. Stops recursion when pyproject.toml found.
        Skips hidden directories (starting with .).

        Parameters
        ----------
        root : Path
            Root directory to search from

        Returns
        -------
        List[Path]
            List of project directories
        """
        projects = []

        # Check if current directory is a Python project
        if (root / "pyproject.toml").exists():
            self.logger.info(f"Found Python project: {root}")
            return [root]

        # Not a project, scan subdirectories
        try:
            for subdir in root.iterdir():
                # Skip hidden directories and files
                if subdir.name.startswith("."):
                    continue

                if subdir.is_dir():
                    projects.extend(self._find_projects(subdir))
        except PermissionError:
            self.logger.warning(f"Permission denied: {root}")

        return projects

    def _get_template_base(self) -> Path:
        """
        Get base path for templates.

        Returns
        -------
        Path
            Path to templates/python_package directory

        Raises
        ------
        TemplateSyncError
            If template directory not found
        """
        runtime_path = basefunctions.runtime.get_runtime_path("basefunctions")
        template_path = Path(runtime_path) / "templates" / "python_package"

        if not template_path.exists():
            raise TemplateSyncError(f"Template directory not found: {template_path}")

        return template_path

    def _extract_optional_dependencies(self, template_toml_path: Path) -> Optional[str]:
        """
        Extract [project.optional-dependencies] section from template.

        Parameters
        ----------
        template_toml_path : Path
            Path to template pyproject.toml

        Returns
        -------
        Optional[str]
            The optional-dependencies section content, or None if not found
        """
        try:
            with open(template_toml_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Find [project.optional-dependencies] section
            pattern = r"(\[project\.optional-dependencies\].*?)(?=\n\[|\Z)"
            match = re.search(pattern, content, re.DOTALL)

            if match:
                return match.group(1).strip()

            return None

        except Exception as e:
            self.logger.warning(f"Failed to extract optional-dependencies: {e}")
            return None

    def _patch_pyproject_toml(self, project_path: Path, template_section: str, dry_run: bool = False) -> bool:
        """
        Patch pyproject.toml with template optional-dependencies.

        Parameters
        ----------
        project_path : Path
            Path to project directory
        template_section : str
            The [project.optional-dependencies] section from template
        dry_run : bool, optional
            If True, only show what would be done

        Returns
        -------
        bool
            True if patched successfully
        """
        pyproject_path = project_path / "pyproject.toml"

        if not pyproject_path.exists():
            self.logger.warning(f"pyproject.toml not found: {pyproject_path}")
            return False

        try:
            with open(pyproject_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Check if [project.optional-dependencies] exists
            pattern = r"\[project\.optional-dependencies\].*?(?=\n\[|\Z)"
            existing_match = re.search(pattern, content, re.DOTALL)

            if existing_match:
                # Replace existing section
                if dry_run:
                    self.logger.info("[DRY-RUN] Would replace [project.optional-dependencies] section")
                else:
                    updated_content = re.sub(pattern, template_section, content, flags=re.DOTALL)
            else:
                # Add section before [build-system] or at end
                if dry_run:
                    self.logger.info("[DRY-RUN] Would add [project.optional-dependencies] section")
                else:
                    # Try to insert before [build-system]
                    build_system_match = re.search(r"\n\[build-system\]", content)
                    if build_system_match:
                        insert_pos = build_system_match.start()
                        updated_content = content[:insert_pos] + "\n" + template_section + "\n" + content[insert_pos:]
                    else:
                        # Add at end
                        updated_content = content.rstrip() + "\n\n" + template_section + "\n"

            if not dry_run:
                with open(pyproject_path, "w", encoding="utf-8") as f:
                    f.write(updated_content)
                self.logger.info("Patched: pyproject.toml [project.optional-dependencies]")

            return True

        except Exception as e:
            self.logger.error(f"Failed to patch pyproject.toml: {e}")
            return False

    def _sync_project(self, project_path: Path, dry_run: bool = False) -> None:
        """
        Sync templates to a single project.

        Parameters
        ----------
        project_path : Path
            Path to project directory
        dry_run : bool, optional
            If True, only show what would be done

        Raises
        ------
        TemplateSyncError
            If sync operation fails
        """
        try:
            template_base = self._get_template_base()

            files_synced = 0

            # 1. Claude settings
            claude_source = template_base / "claude"
            claude_target = project_path / ".claude"

            if claude_source.exists():
                if dry_run:
                    self.logger.info(f"[DRY-RUN] Would copy: {claude_source} → {claude_target}")
                else:
                    shutil.copytree(claude_source, claude_target, dirs_exist_ok=True)
                    self.logger.info("Synced: .claude/")
                files_synced += 1
            else:
                self.logger.warning(f"Template not found: {claude_source}")

            # 2. VSCode settings
            vscode_source = template_base / "vscode" / "settings.json"
            vscode_target_dir = project_path / ".vscode"
            vscode_target = vscode_target_dir / "settings.json"

            if vscode_source.exists():
                if dry_run:
                    self.logger.info(f"[DRY-RUN] Would copy: {vscode_source} → {vscode_target}")
                else:
                    vscode_target_dir.mkdir(exist_ok=True)
                    shutil.copy2(vscode_source, vscode_target)
                    self.logger.info("Synced: .vscode/settings.json")
                files_synced += 1
            else:
                self.logger.warning(f"Template not found: {vscode_source}")

            # 3. Pre-commit config
            precommit_source = template_base / "precommit" / "pre-commit-config.yaml"
            precommit_target = project_path / ".pre-commit-config.yaml"

            if precommit_source.exists():
                if dry_run:
                    self.logger.info(f"[DRY-RUN] Would copy: {precommit_source} → {precommit_target}")
                else:
                    shutil.copy2(precommit_source, precommit_target)
                    self.logger.info("Synced: .pre-commit-config.yaml")
                files_synced += 1
            else:
                self.logger.warning(f"Template not found: {precommit_source}")

            # 4. Patch pyproject.toml with optional-dependencies
            template_pyproject = template_base / "project" / "pyproject.toml"
            if template_pyproject.exists():
                template_section = self._extract_optional_dependencies(template_pyproject)
                if template_section:
                    if self._patch_pyproject_toml(project_path, template_section, dry_run):
                        files_synced += 1
                else:
                    self.logger.warning("Could not extract [project.optional-dependencies] from template")
            else:
                self.logger.warning(f"Template pyproject.toml not found: {template_pyproject}")

            if files_synced > 0:
                self.projects_synced += 1

        except Exception as e:
            raise TemplateSyncError(f"Failed to sync project {project_path}: {e}")

    def sync_all(self, root: Path, dry_run: bool = False) -> None:
        """
        Sync templates to all Python projects under root directory.

        Parameters
        ----------
        root : Path
            Root directory to search
        dry_run : bool, optional
            If True, only show what would be done

        Raises
        ------
        TemplateSyncError
            If sync operation fails
        """
        self.formatter.show_header("Template Sync")

        # Find all projects
        self.formatter.show_progress(f"Scanning for Python projects in: {root}")
        projects = self._find_projects(root)
        self.projects_found = len(projects)

        if not projects:
            self.formatter.show_result("No Python projects found", False)
            return

        details = {"projects_found": self.projects_found, "scan_root": str(root)}
        self.formatter.show_result("Projects found", True, details)

        # Sync each project
        for project in projects:
            self.formatter.show_progress(f"Syncing templates to: {project.name}")
            try:
                self._sync_project(project, dry_run)
            except TemplateSyncError as e:
                self.logger.error(str(e))
                continue

        # Summary
        sync_details = {
            "projects_synced": self.projects_synced,
            "projects_found": self.projects_found,
            "dry_run": "Yes" if dry_run else "No",
        }
        self.formatter.show_result("Sync complete", True, sync_details)


def main():
    """CLI entry point for template sync."""
    import argparse

    parser = argparse.ArgumentParser(description="Sync template files to Python projects with pyproject.toml")
    parser.add_argument(
        "--directory",
        "-d",
        type=Path,
        default=Path.cwd(),
        help="Root directory to scan (default: current directory)",
    )
    parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="Show what would be done without making changes",
    )

    args = parser.parse_args()

    syncer = TemplateSyncer()

    try:
        syncer.sync_all(args.directory, dry_run=args.dry_run)

    except TemplateSyncError as e:
        formatter = basefunctions.OutputFormatter()
        formatter.show_result(str(e), False)
        sys.exit(1)


if __name__ == "__main__":
    main()
