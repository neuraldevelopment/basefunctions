"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Help text formatter for CLI commands
 Log:
 v1.0 : Initial implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import List, Dict
from basefunctions.utils.logging import setup_logger
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
setup_logger(__name__)

# -------------------------------------------------------------
# TYPE DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# EXCEPTION DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# CLASS OR FUNCTION DEFINITIONS
# -------------------------------------------------------------


class HelpFormatter:
    """
    Help text formatter for CLI commands.

    Generates formatted help output from command metadata
    with consistent styling and layout.
    """

    @staticmethod
    def format_command_list(commands: Dict[str, "basefunctions.cli.CommandMetadata"]) -> str:
        """
        Format list of commands.

        Parameters
        ----------
        commands : Dict[str, CommandMetadata]
            Command metadata dictionary

        Returns
        -------
        str
            Formatted command list
        """
        if not commands:
            return "No commands available"

        lines = []
        for cmd_name, metadata in sorted(commands.items()):
            usage = metadata.usage.ljust(40)
            lines.append(f"  {usage} - {metadata.description}")

        return "\n".join(lines)

    @staticmethod
    def format_command_details(metadata: "basefunctions.cli.CommandMetadata") -> str:
        """
        Format detailed command help.

        Parameters
        ----------
        metadata : CommandMetadata
            Command metadata

        Returns
        -------
        str
            Formatted help text
        """
        lines = [f"Command: {metadata.name}", f"Description: {metadata.description}", f"Usage: {metadata.usage}", ""]

        if metadata.args:
            lines.append("Arguments:")
            for arg in metadata.args:
                required = "required" if arg.required else "optional"
                arg_line = f"  {arg.name:<20} ({arg.arg_type}, {required})"
                if arg.description:
                    arg_line += f" - {arg.description}"
                if arg.context_key:
                    arg_line += f" [context: {arg.context_key}]"
                lines.append(arg_line)
            lines.append("")

        if metadata.examples:
            lines.append("Examples:")
            for example in metadata.examples:
                lines.append(f"  {example}")
            lines.append("")

        if metadata.aliases:
            lines.append(f"Aliases: {', '.join(metadata.aliases)}")

        return "\n".join(lines)

    @staticmethod
    def format_group_help(group_name: str, handler: "basefunctions.cli.BaseCommand", command: str = None) -> str:
        """
        Format help for command group.

        Parameters
        ----------
        group_name : str
            Group name
        handler : BaseCommand
            Command handler
        command : str, optional
            Specific command

        Returns
        -------
        str
            Formatted help text
        """
        if command:
            metadata = handler.get_command_metadata(command)
            if not metadata:
                return f"Unknown command: {command}"
            return HelpFormatter.format_command_details(metadata)

        lines = []
        if group_name:
            lines.append(f"{group_name.upper()} COMMANDS:")
        else:
            lines.append("ROOT COMMANDS:")

        lines.append("")

        commands = {}
        for cmd_name in handler.get_available_commands():
            metadata = handler.get_command_metadata(cmd_name)
            if metadata:
                commands[cmd_name] = metadata

        lines.append(HelpFormatter.format_command_list(commands))

        return "\n".join(lines)

    @staticmethod
    def format_aliases(aliases: Dict[str, tuple]) -> str:
        """
        Format alias list.

        Parameters
        ----------
        aliases : Dict[str, tuple]
            Alias to (group, command) mapping

        Returns
        -------
        str
            Formatted alias list
        """
        if not aliases:
            return "No aliases configured"

        lines = ["Available aliases:", ""]
        for alias, (group, cmd) in sorted(aliases.items()):
            target = f"{group} {cmd}" if group else cmd
            lines.append(f"  {alias:<15} -> {target}")

        return "\n".join(lines)

    @staticmethod
    def format_error(message: str, suggestion: str = None) -> str:
        """
        Format error message.

        Parameters
        ----------
        message : str
            Error message
        suggestion : str, optional
            Suggestion for user

        Returns
        -------
        str
            Formatted error message
        """
        lines = [f"Error: {message}"]
        if suggestion:
            lines.append(f"Try: {suggestion}")
        return "\n".join(lines)
