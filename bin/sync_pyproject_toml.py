#!/usr/bin/env python3
"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Sync pyproject.toml files in Python projects with template configuration
 Log:
 v1.0.0 : Initial implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import argparse
import shutil
import sys
import tomllib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import basefunctions

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------
DEFAULT_SEARCH_PATH = Path.home() / "Code"

TOML_MULTILINE_THRESHOLD = 3  # Lists with more than 3 items use multiline format

# Sections to preserve from existing pyproject.toml
PRESERVE_SECTIONS = [
    ("project", "name"),
    ("project", "version"),
    ("project", "description"),
    ("project", "dependencies"),
]

# Sections to sync from template
SYNC_SECTIONS = [
    ("project", "authors"),
    ("project", "readme"),
    ("project", "license"),
    ("project", "requires-python"),
    ("project", "optional-dependencies"),
    ("build-system",),
    ("tool", "setuptools"),
    ("tool", "setuptools", "packages", "find"),
    ("tool", "setuptools", "package-data"),
    ("tool", "pytest", "ini_options"),
]

# -------------------------------------------------------------
# LOGGING
# -------------------------------------------------------------
basefunctions.setup_logger(__name__)

# -------------------------------------------------------------
# TYPE DEFINITIONS
# -------------------------------------------------------------


# -------------------------------------------------------------
# EXCEPTION DEFINITIONS
# -------------------------------------------------------------
class SyncPyprojectTomlError(Exception):
    """Pyproject.toml synchronization failed."""

    pass


# -------------------------------------------------------------
# CLASS OR FUNCTION DEFINITIONS
# -------------------------------------------------------------
class SyncPyprojectToml:
    """
    Synchronize pyproject.toml files in Python projects with template configuration.

    Attributes
    ----------
    logger : logging.Logger
        Logger instance for this class
    formatter : basefunctions.OutputFormatter
        Output formatter for CLI display
    template_path : Path
        Path to pyproject.toml template file
    """

    def __init__(self):
        self.logger = basefunctions.get_logger(__name__)
        self.formatter = basefunctions.OutputFormatter()
        self.template_path = self._get_template_path()

    def find_projects(self, search_path: Path) -> List[Path]:
        """
        Find all basefunctions Python projects in search path.

        Parameters
        ----------
        search_path : Path
            Directory to search for projects

        Returns
        -------
        List[Path]
            List of project directories

        Raises
        ------
        OSError
            If search path cannot be accessed
        PermissionError
            If directory permissions prevent access
        """
        if not search_path.exists():
            self.logger.warning(f"Search path does not exist: {search_path}")
            return []

        projects = []
        for item in search_path.rglob("pyproject.toml"):
            project_dir = item.parent
            if self.is_basefunctions_project(project_dir):
                projects.append(project_dir)

        return sorted(projects)

    def is_basefunctions_project(self, path: Path) -> bool:
        """
        Check if path is a basefunctions project.

        Recognition criteria:
        - pyproject.toml exists
        - src/ directory exists
        - .vscode/settings.json exists
        - .claude/settings.local.json exists

        Parameters
        ----------
        path : Path
            Project directory path

        Returns
        -------
        bool
            True if basefunctions project

        Raises
        ------
        OSError
            If project path cannot be accessed
        """
        required_files = [
            path / "pyproject.toml",
            path / "src",
            path / ".vscode" / "settings.json",
            path / ".claude" / "settings.local.json",
        ]

        return all(f.exists() for f in required_files)

    def sync_project(self, project_path: Path, dry_run: bool = False) -> Dict[str, Any]:
        """
        Sync pyproject.toml for specific project.

        Parameters
        ----------
        project_path : Path
            Project directory path
        dry_run : bool, optional
            Show changes without execution (default: False)

        Returns
        -------
        Dict[str, Any]
            Sync result with status and details

        Raises
        ------
        SyncPyprojectTomlError
            If synchronization fails
        """
        pyproject_path = project_path / "pyproject.toml"

        if not pyproject_path.exists():
            raise SyncPyprojectTomlError(f"pyproject.toml not found: {pyproject_path}")

        try:
            # Load template
            template_data = self._load_template()

            # Load target pyproject.toml
            target_data = self._load_pyproject(pyproject_path)

            # Detect package name
            package_name = self._detect_package_name(project_path, target_data)

            # Create merged data
            merged_data = self._merge_data(target_data, template_data, package_name)

            # Detect changes
            changes = self._detect_changes(target_data, merged_data)

            if not dry_run and changes:
                # Create backup
                backup_path = self._backup_pyproject(pyproject_path)

                # Write merged data
                self._write_pyproject(pyproject_path, merged_data)

                return {
                    "status": "synced",
                    "project": str(project_path),
                    "changes": changes,
                    "backup": str(backup_path),
                }
            elif dry_run and changes:
                return {
                    "status": "would_sync",
                    "project": str(project_path),
                    "changes": changes,
                }
            else:
                return {
                    "status": "up_to_date",
                    "project": str(project_path),
                    "changes": [],
                }

        except Exception as e:
            raise SyncPyprojectTomlError(f"Failed to sync {project_path}: {e}")

    def sync_all(self, search_path: Path, dry_run: bool = False) -> List[Dict[str, Any]]:
        """
        Sync all projects in search path.

        Parameters
        ----------
        search_path : Path
            Directory to search for projects
        dry_run : bool, optional
            Show changes without execution (default: False)

        Returns
        -------
        List[Dict[str, Any]]
            List of sync results
        """
        projects = self.find_projects(search_path)

        if not projects:
            self.logger.warning(f"No basefunctions projects found in: {search_path}")
            return []

        results = []
        for project in projects:
            try:
                result = self.sync_project(project, dry_run=dry_run)
                results.append(result)
            except SyncPyprojectTomlError as e:
                self.logger.error(f"Failed to sync {project}: {e}")
                results.append(
                    {
                        "status": "error",
                        "project": str(project),
                        "error": str(e),
                    }
                )

        return results

    def get_sync_status(self, project_path: Path) -> Dict[str, Any]:
        """
        Get sync status for specific project.

        Parameters
        ----------
        project_path : Path
            Project directory path

        Returns
        -------
        Dict[str, Any]
            Sync status with details
        """
        pyproject_path = project_path / "pyproject.toml"

        if not pyproject_path.exists():
            return {
                "status": "not_found",
                "project": str(project_path),
            }

        try:
            # Load template and target
            template_data = self._load_template()
            target_data = self._load_pyproject(pyproject_path)

            # Detect package name
            package_name = self._detect_package_name(project_path, target_data)

            # Create merged data
            merged_data = self._merge_data(target_data, template_data, package_name)

            # Detect changes
            changes = self._detect_changes(target_data, merged_data)

            if changes:
                return {
                    "status": "out_of_sync",
                    "project": str(project_path),
                    "changes": changes,
                }
            else:
                return {
                    "status": "in_sync",
                    "project": str(project_path),
                }

        except Exception as e:
            return {
                "status": "error",
                "project": str(project_path),
                "error": str(e),
            }

    def backup_pyproject(self, path: Path) -> Path:
        """
        Create backup of pyproject.toml file.

        Parameters
        ----------
        path : Path
            Path to pyproject.toml file

        Returns
        -------
        Path
            Path to backup file

        Raises
        ------
        SyncPyprojectTomlError
            If backup creation fails
        """
        return self._backup_pyproject(path)

    def _get_template_path(self) -> Path:
        """
        Get path to pyproject.toml template.

        Returns
        -------
        Path
            Path to template file
        """
        runtime_path = basefunctions.runtime.get_runtime_path("basefunctions")
        template_path = Path(runtime_path) / "templates" / "python_package" / "project" / "pyproject.toml"

        if not template_path.exists():
            raise SyncPyprojectTomlError(f"Template not found: {template_path}")

        return template_path

    def _load_template(self) -> Dict[str, Any]:
        """
        Load pyproject.toml template.

        Returns
        -------
        Dict[str, Any]
            Template data

        Raises
        ------
        FileNotFoundError
            If template file does not exist
        tomllib.TOMLDecodeError
            If template TOML syntax is invalid
        """
        with open(self.template_path, "rb") as f:
            return tomllib.load(f)

    def _load_pyproject(self, path: Path) -> Dict[str, Any]:
        """
        Load pyproject.toml file.

        Parameters
        ----------
        path : Path
            Path to pyproject.toml file

        Returns
        -------
        Dict[str, Any]
            Pyproject data

        Raises
        ------
        FileNotFoundError
            If pyproject.toml file does not exist
        tomllib.TOMLDecodeError
            If TOML syntax is invalid
        PermissionError
            If file cannot be read due to permissions
        """
        with open(path, "rb") as f:
            return tomllib.load(f)

    def _detect_package_name(self, project_path: Path, target_data: Dict[str, Any]) -> str:
        """
        Detect package name from project.

        Parameters
        ----------
        project_path : Path
            Project directory path
        target_data : Dict[str, Any]
            Target pyproject.toml data

        Returns
        -------
        str
            Package name

        Raises
        ------
        OSError
            If src directory cannot be accessed
        SyncPyprojectTomlError
            If package name cannot be detected
        """
        # First try to get from pyproject.toml
        if "project" in target_data and "name" in target_data["project"]:
            return target_data["project"]["name"]

        # Fallback: scan src/ directory
        src_dir = project_path / "src"
        if src_dir.exists():
            for item in src_dir.iterdir():
                if item.is_dir() and not item.name.startswith("."):
                    return item.name

        # Last resort: use project directory name
        return project_path.name

    def _merge_data(
        self, target_data: Dict[str, Any], template_data: Dict[str, Any], package_name: str
    ) -> Dict[str, Any]:
        """
        Merge target and template data.

        Parameters
        ----------
        target_data : Dict[str, Any]
            Target pyproject.toml data
        template_data : Dict[str, Any]
            Template data
        package_name : str
            Package name

        Returns
        -------
        Dict[str, Any]
            Merged data
        """
        # Start with template as base
        merged = self._deep_copy(template_data)

        # Preserve specified sections from target
        for section_path in PRESERVE_SECTIONS:
            value = self._get_nested_value(target_data, section_path)
            if value is not None:
                self._set_nested_value(merged, section_path, value)

        # Replace <package_name> placeholder in package-data
        if "tool" in merged and "setuptools" in merged["tool"] and "package-data" in merged["tool"]["setuptools"]:
            package_data = merged["tool"]["setuptools"]["package-data"]
            if "<package_name>" in package_data:
                package_data[package_name] = package_data.pop("<package_name>")

        return merged

    def _detect_changes(self, target_data: Dict[str, Any], merged_data: Dict[str, Any]) -> List[str]:
        """
        Detect changes between target and merged data.

        Parameters
        ----------
        target_data : Dict[str, Any]
            Target data
        merged_data : Dict[str, Any]
            Merged data

        Returns
        -------
        List[str]
            List of changed section paths
        """
        changes = []

        for section_path in SYNC_SECTIONS:
            target_value = self._get_nested_value(target_data, section_path)
            merged_value = self._get_nested_value(merged_data, section_path)

            if target_value != merged_value:
                changes.append(".".join(section_path))

        return changes

    def _backup_pyproject(self, path: Path) -> Path:
        """
        Create backup of pyproject.toml file.

        Parameters
        ----------
        path : Path
            Path to pyproject.toml file

        Returns
        -------
        Path
            Path to backup file

        Raises
        ------
        SyncPyprojectTomlError
            If backup creation fails
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = path.with_name(f"pyproject.toml.backup_{timestamp}")

        try:
            shutil.copy2(path, backup_path)
            return backup_path
        except Exception as e:
            raise SyncPyprojectTomlError(f"Failed to create backup: {e}")

    def _write_pyproject(self, path: Path, data: Dict[str, Any]) -> None:
        """
        Write pyproject.toml file.

        Parameters
        ----------
        path : Path
            Path to pyproject.toml file
        data : Dict[str, Any]
            Pyproject data

        Raises
        ------
        SyncPyprojectTomlError
            If write fails
        """
        try:
            # Convert to TOML format
            content = self._dict_to_toml(data)

            # Write to file
            path.write_text(content, encoding="utf-8")
        except Exception as e:
            raise SyncPyprojectTomlError(f"Failed to write pyproject.toml: {e}")

    def _dict_to_toml(self, data: Dict[str, Any], prefix: str = "") -> str:
        """
        Convert dictionary to TOML format string.

        Parameters
        ----------
        data : Dict[str, Any]
            Data to convert
        prefix : str, optional
            Section prefix (default: "")

        Returns
        -------
        str
            TOML formatted string

        Raises
        ------
        TypeError
            If data contains unsupported types for TOML serialization
        """
        lines = []

        # Separate simple values and tables
        simple_values = {}
        tables = {}

        for key, value in data.items():
            if isinstance(value, dict):
                tables[key] = value
            else:
                simple_values[key] = value

        # Write simple values first
        for key, value in simple_values.items():
            lines.append(f"{key} = {self._value_to_toml(value)}")

        # Write tables
        for key, value in tables.items():
            if prefix:
                section_name = f"{prefix}.{key}"
            else:
                section_name = key

            # Check if this is a simple table or has nested tables
            has_nested_tables = any(isinstance(v, dict) for v in value.values())

            if has_nested_tables:
                # Write recursively
                if lines:
                    lines.append("")
                lines.append(self._dict_to_toml(value, prefix=section_name))
            else:
                # Write as simple table
                if lines:
                    lines.append("")
                lines.append(f"[{section_name}]")
                for k, v in value.items():
                    lines.append(f"{k} = {self._value_to_toml(v)}")

        return "\n".join(lines)

    def _value_to_toml(self, value: Any) -> str:
        """
        Convert Python value to TOML format.

        Parameters
        ----------
        value : Any
            Value to convert

        Returns
        -------
        str
            TOML formatted value

        Raises
        ------
        TypeError
            If value type is not supported for TOML serialization
        """
        if isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, str):
            # Escape quotes and backslashes
            escaped = value.replace("\\", "\\\\").replace('"', '\\"')
            return f'"{escaped}"'
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, list):
            if not value:
                return "[]"
            # Format list items
            items = [self._value_to_toml(item) for item in value]
            # Multiline for lists with more than 3 items
            if len(items) > TOML_MULTILINE_THRESHOLD:
                formatted_items = ",\n    ".join(items)
                return f"[\n    {formatted_items},\n]"
            else:
                return f"[{', '.join(items)}]"
        elif isinstance(value, dict):
            if not value:
                return "{}"
            items = [f"{{ {k}={self._value_to_toml(v)} }}" for k, v in value.items()]
            return f"[{', '.join(items)}]"
        else:
            return str(value)

    def _get_nested_value(self, data: Dict[str, Any], path: tuple) -> Any:
        """
        Get nested value from dictionary.

        Parameters
        ----------
        data : Dict[str, Any]
            Source dictionary
        path : tuple
            Path to value

        Returns
        -------
        Any
            Value or None if not found
        """
        current = data
        for key in path:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        return current

    def _set_nested_value(self, data: Dict[str, Any], path: tuple, value: Any) -> None:
        """
        Set nested value in dictionary.

        Parameters
        ----------
        data : Dict[str, Any]
            Target dictionary
        path : tuple
            Path to value
        value : Any
            Value to set
        """
        current = data
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[path[-1]] = value

    def _deep_copy(self, data: Any) -> Any:
        """
        Deep copy data structure.

        Parameters
        ----------
        data : Any
            Data to copy

        Returns
        -------
        Any
            Deep copied data
        """
        if isinstance(data, dict):
            return {k: self._deep_copy(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._deep_copy(item) for item in data]
        else:
            return data


def main():
    """
    CLI entry point for pyproject.toml synchronization.
    """
    parser = argparse.ArgumentParser(description="Sync pyproject.toml files in Python projects")
    parser.add_argument("--all", "-a", action="store_true", help="Sync all found projects")
    parser.add_argument("--project", "-p", type=Path, help="Sync specific project")
    parser.add_argument("--dry-run", "-n", action="store_true", help="Show changes without execution")
    parser.add_argument("--status", "-s", action="store_true", help="Show sync status of all projects")
    parser.add_argument("--list", "-l", action="store_true", help="List all found projects")
    parser.add_argument(
        "--search-path",
        type=Path,
        default=DEFAULT_SEARCH_PATH,
        help=f"Where to search for projects (default: {DEFAULT_SEARCH_PATH})",
    )

    args = parser.parse_args()

    syncer = SyncPyprojectToml()

    try:
        if args.list:
            syncer.formatter.show_header("List Python Projects")
            syncer.formatter.show_progress(f"Scanning {args.search_path}")

            projects = syncer.find_projects(args.search_path)

            details = {
                "projects_found": len(projects),
                "search_path": str(args.search_path),
            }
            syncer.formatter.show_result("Project scan complete", True, details)

            if projects:
                print("\nFound projects:")
                for project in projects:
                    print(f"  {project}")
            else:
                print("\nNo basefunctions projects found")

        elif args.status:
            syncer.formatter.show_header("Sync Status")
            syncer.formatter.show_progress(f"Checking projects in {args.search_path}")

            projects = syncer.find_projects(args.search_path)

            if not projects:
                syncer.formatter.show_result("No projects found", False)
                return

            in_sync_count = 0
            out_of_sync_count = 0
            error_count = 0

            print("\nSync status:")
            for project in projects:
                status = syncer.get_sync_status(project)
                if status["status"] == "in_sync":
                    print(f"  {project.name}: IN SYNC")
                    in_sync_count += 1
                elif status["status"] == "out_of_sync":
                    print(f"  {project.name}: OUT OF SYNC")
                    print(f"    Changes: {', '.join(status['changes'])}")
                    out_of_sync_count += 1
                else:
                    print(f"  {project.name}: ERROR")
                    error_count += 1

            details = {
                "in_sync": in_sync_count,
                "out_of_sync": out_of_sync_count,
                "errors": error_count,
            }
            syncer.formatter.show_result("Status check complete", True, details)

        elif args.project:
            action = "Dry Run" if args.dry_run else "Sync Project"
            syncer.formatter.show_header(action)

            syncer.formatter.show_progress(f"Processing {args.project}")

            result = syncer.sync_project(args.project, dry_run=args.dry_run)

            if result["status"] == "synced":
                details = {
                    "changes": len(result["changes"]),
                    "backup": result["backup"],
                }
                syncer.formatter.show_result("Project synced successfully", True, details)
                print("\nSynced sections:")
                for change in result["changes"]:
                    print(f"  {change}")

            elif result["status"] == "would_sync":
                details = {"changes": len(result["changes"])}
                syncer.formatter.show_result("Project would be synced", True, details)
                print("\nWould sync sections:")
                for change in result["changes"]:
                    print(f"  {change}")

            elif result["status"] == "up_to_date":
                syncer.formatter.show_result("Project is already up to date", True)

        elif args.all:
            action = "Dry Run All" if args.dry_run else "Sync All Projects"
            syncer.formatter.show_header(action)

            syncer.formatter.show_progress(f"Finding projects in {args.search_path}")

            results = syncer.sync_all(args.search_path, dry_run=args.dry_run)

            if not results:
                syncer.formatter.show_result("No projects found", False)
                return

            synced_count = sum(1 for r in results if r["status"] == "synced")
            would_sync_count = sum(1 for r in results if r["status"] == "would_sync")
            up_to_date_count = sum(1 for r in results if r["status"] == "up_to_date")
            error_count = sum(1 for r in results if r["status"] == "error")

            details = {
                "total": len(results),
                "synced": synced_count if not args.dry_run else would_sync_count,
                "up_to_date": up_to_date_count,
                "errors": error_count,
            }

            if args.dry_run:
                syncer.formatter.show_result("Dry run complete", True, details)
            else:
                syncer.formatter.show_result("Sync complete", True, details)

            # Show details for each result
            print("\nResults:")
            for result in results:
                project_name = Path(result["project"]).name
                if result["status"] in ["synced", "would_sync"]:
                    status_text = "WOULD SYNC" if args.dry_run else "SYNCED"
                    print(f"  {project_name}: {status_text} ({len(result['changes'])} changes)")
                elif result["status"] == "up_to_date":
                    print(f"  {project_name}: UP TO DATE")
                else:
                    print(f"  {project_name}: ERROR - {result.get('error', 'Unknown error')}")

        else:
            parser.print_help()

    except SyncPyprojectTomlError as e:
        syncer.formatter.show_result(str(e), False)
        sys.exit(1)


if __name__ == "__main__":
    main()
