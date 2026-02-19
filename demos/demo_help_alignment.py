"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Demo: format_aligned_sections() — synchronized column widths across help tables
 Log:
 v1.0 : Initial demo
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import basefunctions
from basefunctions.cli import CommandMetadata, HelpFormatter, CLIApplication, BaseCommand

# =============================================================================
# DEMO COMMANDS (varied content lengths to show alignment)
# =============================================================================

SHORT_CMDS = {
    "ls": CommandMetadata(name="ls", description="List items", usage="ls"),
    "cd": CommandMetadata(name="cd", description="Change directory", usage="cd [path]"),
}

LONG_CMDS = {
    "describe-environment": CommandMetadata(
        name="describe-environment",
        description="Show full environment configuration including all registered modules",
        usage="describe-environment [--verbose]",
    ),
    "export-config": CommandMetadata(
        name="export-config",
        description="Export current configuration to file",
        usage="export-config <output-path>",
    ),
    "reset": CommandMetadata(
        name="reset",
        description="Reset to defaults",
        usage="reset",
    ),
}

ALIAS_CMDS = {
    "ll": CommandMetadata(name="ll", description="ls --long", usage="ll"),
    "cfg": CommandMetadata(name="cfg", description="export-config", usage="cfg"),
}

GENERAL_CMDS = {
    "help [command]": CommandMetadata(name="help", description="Show help", usage="help [command]"),
    "quit/exit": CommandMetadata(name="quit", description="Exit CLI", usage="quit/exit"),
}

# =============================================================================
# MAIN
# =============================================================================

def demo_format_aligned_sections() -> None:
    """Show format_aligned_sections() output directly."""
    print("\n" + "=" * 70)
    print("DEMO: HelpFormatter.format_aligned_sections()")
    print("=" * 70)
    print("Sections have very different content widths — columns must align.\n")

    sections = [
        ("SHORT COMMANDS", SHORT_CMDS),
        ("LONG COMMANDS", LONG_CMDS),
        ("ALIASES", ALIAS_CMDS),
        ("GENERAL", GENERAL_CMDS),
    ]

    rendered = HelpFormatter.format_aligned_sections(sections)
    for text in rendered:
        print(text)
        print()


def demo_cli_help() -> None:
    """Show _show_general_help() via CLIApplication (end-to-end)."""

    class ShortCommands(BaseCommand):
        def register_commands(self):
            return SHORT_CMDS
        def execute(self, command, args):
            pass

    class LongCommands(BaseCommand):
        def register_commands(self):
            return LONG_CMDS
        def execute(self, command, args):
            pass

    print("=" * 70)
    print("DEMO: CLIApplication._show_general_help() end-to-end")
    print("=" * 70 + "\n")

    app = CLIApplication(app_name="demo-align", version="1.0.0")
    app.register_command_group("nav", ShortCommands(app.context))
    app.register_command_group("env", LongCommands(app.context))
    app._show_general_help()


if __name__ == "__main__":
    demo_format_aligned_sections()
    demo_cli_help()
