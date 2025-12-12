#!/usr/bin/env python3
"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Sync files from DevonThink Inbox with unified config system
 Log:
 v1.0 : Initial implementation
 v1.1 : Integrated OutputFormatter for consistent output
 v2.0 : Migrated to unified basefunctions config system
 v3.0 : Migrated from prodtools to basefunctions
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import sys
import hashlib
import shutil
from pathlib import Path
from typing import Dict, Optional
import basefunctions

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------
DEFAULT_CONFIG = {
    "source": "~/Library/Application Support/DEVONthink/Inbox.dtBase2/Files.noindex",
    "target": "~/Files/00-DevonThink",
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
class DevonthinkSyncError(Exception):
    """DevonThink sync operation failed."""

    pass


# -------------------------------------------------------------
# CLASS OR FUNCTION DEFINITIONS
# -------------------------------------------------------------
class DevonthinkSync:
    """
    Sync files from DevonThink Inbox with intelligent change detection and unique naming.
    """

    def __init__(self):
        self.logger = basefunctions.get_logger(__name__)
        self.formatter = basefunctions.OutputFormatter()
        self.config_handler = basefunctions.ConfigHandler()
        self._ensure_config_loaded()
        self.files_copied = 0
        self.files_checked = 0

    def sync(self) -> Dict[str, int]:
        """
        Perform sync operation.

        Returns
        -------
        Dict[str, int]
            Sync statistics

        Raises
        ------
        DevonthinkSyncError
            If sync fails
        """
        source_path = Path(self._get_config_value("source")).expanduser()
        target_path = Path(self._get_config_value("target")).expanduser()

        self.formatter.show_header("DevonThink Sync")

        if not source_path.exists():
            self.formatter.show_result(f"Source directory not found: {source_path}", False)
            raise DevonthinkSyncError(f"Source directory not found: {source_path}")

        # Create target directory if needed
        target_path.mkdir(parents=True, exist_ok=True)

        try:
            self.formatter.show_progress("Scanning source files")
            self._sync_files(source_path, target_path)

            stats = {"files_checked": self.files_checked, "files_copied": self.files_copied}

            details = {
                "files_checked": self.files_checked,
                "files_copied": self.files_copied,
                "source": str(source_path),
                "target": str(target_path),
            }

            # Only show success if files were actually processed
            if self.files_checked > 0:
                success_msg = "Sync completed successfully"
                if self.files_copied == 0:
                    success_msg = "Sync completed - no new files to copy"
                self.formatter.show_result(success_msg, True, details)
            else:
                self.formatter.show_result("No files found to sync", True, details)

            return stats

        except Exception as e:
            error_details = {
                "files_checked": self.files_checked,
                "files_copied": self.files_copied,
                "error": str(e),
            }
            self.formatter.show_result("Sync operation failed", False, error_details)
            raise DevonthinkSyncError(f"Sync operation failed: {e}")

    def get_config(self) -> Dict[str, str]:
        """
        Get current configuration.

        Returns
        -------
        Dict[str, str]
            Current configuration
        """
        return {
            "source": self._get_config_value("source"),
            "target": self._get_config_value("target"),
        }

    def update_config(self, source: Optional[str] = None, target: Optional[str] = None) -> None:
        """
        Update configuration.

        Parameters
        ----------
        source : Optional[str], optional
            New source path
        target : Optional[str], optional
            New target path
        """
        # Note: This would require implementing config writing in basefunctions
        # For now, we'll show the values that would be updated
        current_source = self._get_config_value("source")
        current_target = self._get_config_value("target")

        if source is not None:
            self.logger.critical(f"Would update source from '{current_source}' to '{source}'")
        if target is not None:
            self.logger.critical(f"Would update target from '{current_target}' to '{target}'")

        self.logger.critical("Note: Config updates require manual editing of config.json")

    def _ensure_config_loaded(self) -> None:
        """
        Ensure config is loaded for basefunctions package.
        """
        try:
            self.config_handler.load_config_for_package("basefunctions")
        except Exception as e:
            self.logger.critical(f"Failed to load config, using defaults: {e}")

    def _get_config_value(self, key: str) -> str:
        """
        Get config value with fallback to defaults.

        Parameters
        ----------
        key : str
            Config key (source or target)

        Returns
        -------
        str
            Config value
        """
        value = self.config_handler.get_config_parameter(f"basefunctions/devonthink_sync/{key}")
        if value is None:
            return DEFAULT_CONFIG.get(key, "")
        return value

    def _sync_files(self, source_path: Path, target_path: Path) -> None:
        """
        Sync files from source to target.

        Parameters
        ----------
        source_path : Path
            Source directory
        target_path : Path
            Target directory
        """
        for file_path in source_path.rglob("*"):
            if not file_path.is_file():
                continue

            # Skip hidden files
            if file_path.name.startswith("."):
                continue

            self.files_checked += 1

            # Generate unique filename
            unique_filename = self._generate_unique_filename(file_path, source_path)
            target_file = target_path / unique_filename

            # Check if file needs copying
            if self._is_file_newer_or_missing(file_path, target_file):
                try:
                    if self.files_copied == 0:
                        self.formatter.show_progress("Copying new/updated files")

                    shutil.copy2(file_path, target_file)
                    self.files_copied += 1

                    # Log individual file copies for debugging
                    self.logger.critical(f"COPY: {unique_filename}")
                except Exception as e:
                    self.logger.critical(f"ERROR: Failed to copy {unique_filename}: {e}")
                    raise

    def _generate_unique_filename(self, source_file: Path, source_root: Path) -> str:
        """
        Generate unique filename with hash-based naming.

        Parameters
        ----------
        source_file : Path
            Source file path
        source_root : Path
            Source root directory

        Returns
        -------
        str
            Unique filename
        """
        # Get relative path from source root
        try:
            relative_path = source_file.relative_to(source_root)
        except ValueError:
            # File not under source root - use filename
            relative_path = source_file

        # Get original filename
        original_name = source_file.name

        # Extract hash directory (e.g., "ab" from "pdf/ab/document.pdf")
        path_parts = relative_path.parts
        if len(path_parts) >= 2:
            hash_dir = path_parts[-2]  # Parent directory
        else:
            hash_dir = original_name

        # Generate 6-character hash
        short_hash = self._generate_short_hash(hash_dir)

        # Split filename into name and extension
        stem = source_file.stem
        suffix = source_file.suffix

        if suffix:
            return f"{stem}-{short_hash}{suffix}"
        else:
            return f"{original_name}-{short_hash}"

    def _generate_short_hash(self, input_string: str) -> str:
        """
        Generate 6-character hash from input string.

        Parameters
        ----------
        input_string : str
            Input string to hash

        Returns
        -------
        str
            6-character hash
        """
        hash_bytes = hashlib.sha256(input_string.encode("utf-8")).digest()
        return hash_bytes[:3].hex()  # 6 characters (3 bytes as hex)

    def _is_file_newer_or_missing(self, source_file: Path, target_file: Path) -> bool:
        """
        Check if source file is newer than target or target is missing.

        Parameters
        ----------
        source_file : Path
            Source file path
        target_file : Path
            Target file path

        Returns
        -------
        bool
            True if file should be copied
        """
        # Target doesn't exist - copy needed
        if not target_file.exists():
            return True

        try:
            # Get modification times
            source_mtime = source_file.stat().st_mtime
            target_mtime = target_file.stat().st_mtime

            # Source is newer or equal - copy needed
            return source_mtime >= target_mtime

        except (OSError, FileNotFoundError):
            # If we can't get timestamps, assume copy needed
            return True

    def get_sync_status(self) -> Dict[str, any]:
        """
        Get current sync status and statistics.

        Returns
        -------
        Dict[str, any]
            Sync status information
        """
        source_path = Path(self._get_config_value("source")).expanduser()
        target_path = Path(self._get_config_value("target")).expanduser()

        status = {
            "source_exists": source_path.exists(),
            "source_path": str(source_path),
            "target_exists": target_path.exists(),
            "target_path": str(target_path),
            "config_loaded": True,
        }

        if source_path.exists():
            # Count source files
            source_files = list(source_path.rglob("*"))
            source_files = [f for f in source_files if f.is_file() and not f.name.startswith(".")]
            status["source_file_count"] = len(source_files)
        else:
            status["source_file_count"] = 0

        if target_path.exists():
            # Count target files
            target_files = list(target_path.glob("*"))
            target_files = [f for f in target_files if f.is_file()]
            status["target_file_count"] = len(target_files)
        else:
            status["target_file_count"] = 0

        return status


def main():
    """
    CLI entry point for DevonThink sync.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Sync files from DevonThink Inbox")
    parser.add_argument("--config", "-c", action="store_true", help="Show current configuration")
    parser.add_argument("--status", "-s", action="store_true", help="Show sync status")
    parser.add_argument("--source", help="Update source path")
    parser.add_argument("--target", help="Update target path")
    parser.add_argument("--dry-run", "-n", action="store_true", help="Show what would be synced without doing it")

    args = parser.parse_args()

    syncer = DevonthinkSync()

    try:
        if args.config:
            formatter = basefunctions.OutputFormatter()
            formatter.show_header("DevonThink Sync Configuration")
            formatter.show_progress("Loading configuration")

            config = syncer.get_config()
            details = {"source": config["source"], "target": config["target"]}
            formatter.show_result("Configuration loaded", True, details)
            return

        if args.status:
            formatter = basefunctions.OutputFormatter()
            formatter.show_header("DevonThink Sync Status")
            formatter.show_progress("Analyzing sync directories")

            status = syncer.get_sync_status()
            details = {
                "source_exists": "Yes" if status["source_exists"] else "No",
                "source_files": status["source_file_count"],
                "target_exists": "Yes" if status["target_exists"] else "No",
                "target_files": status["target_file_count"],
            }
            formatter.show_result("Status analysis complete", True, details)

            print("\nPaths:")
            print(f"  Source: {status['source_path']}")
            print(f"  Target: {status['target_path']}")
            return

        if args.source or args.target:
            formatter = basefunctions.OutputFormatter()
            formatter.show_header("Update Configuration")
            formatter.show_progress("Updating sync configuration")

            syncer.update_config(source=args.source, target=args.target)
            formatter.show_result("Configuration update info displayed", True)
            return

        if args.dry_run:
            formatter = basefunctions.OutputFormatter()
            formatter.show_result("Dry run mode not implemented yet", False)
            return

        # Perform sync
        syncer.sync()

    except DevonthinkSyncError as e:
        formatter = basefunctions.OutputFormatter()
        formatter.show_result(str(e), False)
        sys.exit(1)


if __name__ == "__main__":
    main()
