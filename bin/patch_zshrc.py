#!/usr/bin/env python3
"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Patch ~/.zshrc with pyenv setup and basefunctions configuration
 Log:
 v1.0 : Initial implementation
 v1.1 : Integrated OutputFormatter for consistent output
 v2.0 : Migrated from prodtools to basefunctions
 v2.1 : Added activate function for virtual environment activation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
import basefunctions

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------
ZSHRC_PATH = Path.home() / ".zshrc"
ALIASES_FILENAME = "aliases.txt"

PATCH_SECTIONS = {
    "pyenv": {
        "title": "PYENV SETUP",
        "content": """export PYENV_ROOT="$HOME/.pyenv"
eval "$(pyenv init -)\"""",
    },
    "basefunctions": {
        "title": "BASEFUNCTIONS",
        "content_template": """export PATH="{deployment_bin_path}:$PATH"
{aliases_content}""",
    },
    "activate": {
        "title": "VIRTUAL ENVIRONMENT ACTIVATION",
        "content": """activate() {
  if [ -d ".venv" ]; then
    source .venv/bin/activate
  elif [ -d "venv" ]; then
    source venv/bin/activate
  else
    echo "No virtual environment found (.venv or venv)"
    return 1
  fi
}""",
    },
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
class PatchZshrcError(Exception):
    """Zshrc patching failed."""

    pass


# -------------------------------------------------------------
# CLASS OR FUNCTION DEFINITIONS
# -------------------------------------------------------------
class PatchZshrc:
    """
    Patch ~/.zshrc with pyenv and basefunctions configuration using marker-based sections.
    """

    def __init__(self):
        self.logger = basefunctions.get_logger(__name__)
        self.formatter = basefunctions.OutputFormatter()
        self.aliases_path = self._get_aliases_path()

    def patch_all(self) -> None:
        """
        Patch all sections in zshrc.

        Raises
        ------
        PatchZshrcError
            If patching fails
        """
        self.formatter.show_header("Patch All Zshrc Sections")

        try:
            self.formatter.show_progress("Creating backup of .zshrc")
            backup_path = self.backup_zshrc()

            patched_sections = []
            for section_name in PATCH_SECTIONS.keys():
                self.formatter.show_progress(f"Patching section: {section_name}")
                self.patch_section(section_name, silent=True)
                patched_sections.append(section_name)

            details = {
                "sections_patched": len(patched_sections),
                "backup_created": str(backup_path),
                "sections": ", ".join(patched_sections),
            }
            self.formatter.show_result("All sections patched successfully", True, details)

        except Exception as e:
            self.formatter.show_result(f"Failed to patch all sections: {e}", False)
            raise PatchZshrcError(f"Failed to patch all sections: {e}")

    def patch_section(self, section_name: str, silent: bool = False) -> None:
        """
        Patch specific section in zshrc.

        Parameters
        ----------
        section_name : str
            Section name to patch
        silent : bool, optional
            Skip individual formatter output for batch operations

        Raises
        ------
        PatchZshrcError
            If section patching fails
        """
        if section_name not in PATCH_SECTIONS:
            error_msg = f"Unknown section: {section_name}"
            if not silent:
                self.formatter.show_result(error_msg, False)
            raise PatchZshrcError(error_msg)

        if not silent:
            self.formatter.show_header(f"Patch Zshrc Section: {section_name}")

        try:
            if not silent:
                self.formatter.show_progress("Creating backup of .zshrc")
                self.backup_zshrc()

            if not silent:
                self.formatter.show_progress(f"Generating content for {section_name}")
            content = self._get_section_content(section_name)

            if not silent:
                self.formatter.show_progress(f"Applying {section_name} section")
            self._patch_section_content(section_name, content)

            if not silent:
                details = {"section": section_name}
                self.formatter.show_result("Section patched successfully", True, details)

        except Exception as e:
            error_msg = f"Failed to patch section {section_name}: {e}"
            if not silent:
                self.formatter.show_result(error_msg, False)
            raise PatchZshrcError(error_msg)

    def remove_section(self, section_name: str) -> None:
        """
        Remove section from zshrc.

        Parameters
        ----------
        section_name : str
            Section name to remove

        Raises
        ------
        PatchZshrcError
            If section removal fails
        """
        if section_name not in PATCH_SECTIONS:
            self.formatter.show_result(f"Unknown section: {section_name}", False)
            raise PatchZshrcError(f"Unknown section: {section_name}")

        self.formatter.show_header(f"Remove Zshrc Section: {section_name}")

        try:
            self.formatter.show_progress("Creating backup of .zshrc")
            backup_path = self.backup_zshrc()

            self.formatter.show_progress(f"Removing {section_name} section")
            self._remove_section_content(section_name)

            details = {"section": section_name, "backup_created": str(backup_path)}
            self.formatter.show_result("Section removed successfully", True, details)

        except Exception as e:
            self.formatter.show_result(f"Failed to remove section {section_name}: {e}", False)
            raise PatchZshrcError(f"Failed to remove section {section_name}: {e}")

    def backup_zshrc(self) -> Path:
        """
        Create backup of zshrc file.

        Returns
        -------
        Path
            Path to backup file

        Raises
        ------
        PatchZshrcError
            If backup creation fails
        """
        if not ZSHRC_PATH.exists():
            ZSHRC_PATH.touch()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = ZSHRC_PATH.with_suffix(f".zshrc.backup_{timestamp}")

        try:
            shutil.copy2(ZSHRC_PATH, backup_path)
            return backup_path

        except Exception as e:
            raise PatchZshrcError(f"Failed to create backup: {e}")

    def get_section_status(self) -> Dict[str, bool]:
        """
        Check which sections are currently patched.

        Returns
        -------
        Dict[str, bool]
            Status of each section
        """
        if not ZSHRC_PATH.exists():
            return {name: False for name in PATCH_SECTIONS.keys()}

        try:
            content = ZSHRC_PATH.read_text(encoding="utf-8")

            status = {}
            for section_name in PATCH_SECTIONS.keys():
                start_marker = f"# >>> {section_name} >>>"
                end_marker = f"# <<< {section_name} <<<"
                status[section_name] = start_marker in content and end_marker in content

            return status

        except Exception as e:
            self.logger.critical(f"Failed to check section status: {e}")
            return {name: False for name in PATCH_SECTIONS.keys()}

    def _get_aliases_path(self) -> Path:
        """
        Get path to aliases.txt file.

        Returns
        -------
        Path
            Path to aliases.txt file
        """
        config_dir = basefunctions.runtime.get_runtime_config_path("basefunctions")
        return Path(config_dir) / ALIASES_FILENAME

    def _get_section_content(self, section_name: str) -> str:
        """
        Get content for specific section.

        Parameters
        ----------
        section_name : str
            Section name

        Returns
        -------
        str
            Section content
        """
        section_config = PATCH_SECTIONS[section_name]

        if section_name == "basefunctions":
            # Dynamic content for basefunctions
            deployment_dir = basefunctions.runtime.get_bootstrap_deployment_directory()
            deployment_bin_path = os.path.join(os.path.expanduser(deployment_dir), "bin")

            aliases_content = self._load_aliases_content()

            return section_config["content_template"].format(
                deployment_bin_path=deployment_bin_path, aliases_content=aliases_content
            )
        else:
            # Static content
            return section_config["content"]

    def _load_aliases_content(self) -> str:
        """
        Load aliases from aliases.txt file.

        Returns
        -------
        str
            Aliases content
        """
        if not self.aliases_path.exists():
            self.logger.critical(f"Aliases file not found: {self.aliases_path}")
            return "# No aliases file found"

        try:
            content = self.aliases_path.read_text(encoding="utf-8").strip()
            return content if content else "# No aliases defined"

        except Exception as e:
            self.logger.critical(f"Failed to load aliases: {e}")
            return "# Error loading aliases"

    def _patch_section_content(self, section_name: str, content: str) -> None:
        """
        Patch section content in zshrc file.

        Parameters
        ----------
        section_name : str
            Section name
        content : str
            Section content
        """
        if not ZSHRC_PATH.exists():
            ZSHRC_PATH.touch()

        current_content = ZSHRC_PATH.read_text(encoding="utf-8")

        # Get content before any patches
        base_content = self._get_content_before_patches(current_content)

        # Strip base content
        base_content = base_content.strip()

        # Generate new section block
        section_title = PATCH_SECTIONS[section_name]["title"]
        section_block = self._generate_section_block(section_name, section_title, content)

        # Build new content: base + all sections
        new_content = base_content

        # Add all sections at the end
        for existing_section in PATCH_SECTIONS.keys():
            if existing_section == section_name:
                # Add the section we're updating
                new_content += "\n\n" + section_block
            else:
                # Check if other section exists and re-add it
                existing_content = self._extract_existing_section(current_content, existing_section)
                if existing_content:
                    new_content += "\n\n" + existing_content

        ZSHRC_PATH.write_text(new_content, encoding="utf-8")

    def _remove_section_content(self, section_name: str) -> None:
        """
        Remove section content from zshrc file.

        Parameters
        ----------
        section_name : str
            Section name
        """
        if not ZSHRC_PATH.exists():
            return

        current_content = ZSHRC_PATH.read_text(encoding="utf-8")

        # Get content before any patches
        base_content = self._get_content_before_patches(current_content)

        # Strip base content
        base_content = base_content.strip()

        # Build new content: base + remaining sections
        new_content = base_content

        # Add all sections except the one to remove
        for existing_section in PATCH_SECTIONS.keys():
            if existing_section != section_name:
                existing_content = self._extract_existing_section(current_content, existing_section)
                if existing_content:
                    new_content += "\n\n" + existing_content

        ZSHRC_PATH.write_text(new_content, encoding="utf-8")

    def _get_content_before_patches(self, content: str) -> str:
        """
        Get content before any patch sections.

        Parameters
        ----------
        content : str
            Full content

        Returns
        -------
        str
            Content before first patch section
        """
        lines = content.split("\n")

        for i, line in enumerate(lines):
            # Check for any section start marker
            for section_name in PATCH_SECTIONS.keys():
                if f"# >>> {section_name} >>>" in line:
                    return "\n".join(lines[:i])

        # No patches found, return all content
        return content

    def _extract_existing_section(self, content: str, section_name: str) -> str:
        """
        Extract existing section content if it exists.

        Parameters
        ----------
        content : str
            Full content
        section_name : str
            Section name to extract

        Returns
        -------
        str
            Section content or empty string
        """
        start_marker = f"# >>> {section_name} >>>"
        end_marker = f"# <<< {section_name} <<<"

        lines = content.split("\n")
        section_lines = []
        in_section = False

        for line in lines:
            if start_marker in line:
                in_section = True
                section_lines.append(line)
            elif end_marker in line:
                section_lines.append(line)
                break
            elif in_section:
                section_lines.append(line)

        return "\n".join(section_lines) if section_lines else ""

    def _generate_section_block(self, section_name: str, title: str, content: str) -> str:
        """
        Generate formatted section block.

        Parameters
        ----------
        section_name : str
            Section name
        title : str
            Section title
        content : str
            Section content

        Returns
        -------
        str
            Formatted section block
        """
        separator = "-" * 66

        return f"""# >>> {section_name} >>>
# {separator}
# {title}
# {separator}
{content}
# <<< {section_name} <<<"""


def main():
    """
    CLI entry point for zshrc patching.
    """
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Patch ~/.zshrc with pyenv and basefunctions configuration")
    parser.add_argument("--all", "-a", action="store_true", help="Patch all sections")
    parser.add_argument("--section", "-s", choices=list(PATCH_SECTIONS.keys()), help="Patch specific section")
    parser.add_argument("--remove", "-r", choices=list(PATCH_SECTIONS.keys()), help="Remove specific section")
    parser.add_argument("--status", action="store_true", help="Show section status")
    parser.add_argument("--backup", "-b", action="store_true", help="Create backup only")

    args = parser.parse_args()

    patcher = PatchZshrc()

    try:
        if args.status:
            formatter = basefunctions.OutputFormatter()
            formatter.show_header("Zshrc Section Status")
            formatter.show_progress("Checking section status")

            status = patcher.get_section_status()
            patched_count = sum(1 for is_patched in status.values() if is_patched)

            details = {"sections_patched": f"{patched_count}/{len(status)}", "zshrc_path": str(ZSHRC_PATH)}
            formatter.show_result("Status check complete", True, details)

            print("\nSection status:")
            for section, is_patched in status.items():
                status_text = "PATCHED" if is_patched else "NOT PATCHED"
                print(f"  {section}: {status_text}")

        elif args.backup:
            formatter = basefunctions.OutputFormatter()
            formatter.show_header("Create Zshrc Backup")
            formatter.show_progress("Creating backup file")

            backup_path = patcher.backup_zshrc()
            details = {"backup_path": str(backup_path)}
            formatter.show_result("Backup created successfully", True, details)

        elif args.section:
            patcher.patch_section(args.section)
            print("Restart your terminal or run: source ~/.zshrc")

        elif args.remove:
            patcher.remove_section(args.remove)
            print("Restart your terminal or run: source ~/.zshrc")

        else:
            # Default action: patch all sections
            patcher.patch_all()
            print("Restart your terminal or run: source ~/.zshrc")

    except PatchZshrcError as e:
        formatter = basefunctions.OutputFormatter()
        formatter.show_result(str(e), False)
        sys.exit(1)


if __name__ == "__main__":
    main()
