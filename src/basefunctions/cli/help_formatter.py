"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Help text formatter for CLI commands - uses TableRenderer with ANSI colors
 Log:
 v1.4.0 : Add format_aligned_sections for synchronized multi-table rendering
 v1.3.0 : Add return_widths and enforce_widths for multi-table width synchronization
 v1.2.0 : Add column_specs, max_width, row_separators parameters to format_command_list
 v1.1.0 : Refactor to use TableRenderer with ANSI light blue colors
 v1.0.0 : Initial implementation
=============================================================================
"""

from __future__ import annotations

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Any, Dict, List, Optional, Tuple, Union
from basefunctions.utils.logging import setup_logger
from basefunctions.utils.table_renderer import render_table, get_default_theme
import basefunctions

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# CONSTANTS
# -------------------------------------------------------------
ANSI_LIGHT_BLUE = "\033[94m"
ANSI_RESET = "\033[0m"

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
    def _build_help_rows(groups_data: dict[str, dict[str, basefunctions.cli.CommandMetadata]]) -> list[list[str]]:
        """
        Build table rows for multi-group command display.

        Parameters
        ----------
        groups_data : Dict[str, Dict[str, CommandMetadata]]
            Nested dict: group_name -> {cmd_name -> metadata}

        Returns
        -------
        List[List[str]]
            Table rows with group headers and colored commands
        """
        rows = []

        for group_name, commands in groups_data.items():
            # Add group header row
            rows.append([group_name, ""])

            # Add commands for this group
            for cmd_name, metadata in sorted(commands.items()):
                colored_usage = f"{ANSI_LIGHT_BLUE}{metadata.usage}{ANSI_RESET}"
                rows.append([colored_usage, metadata.description])

        return rows

    @staticmethod
    def format_command_list(
        commands: dict[str, basefunctions.cli.CommandMetadata],
        group_name: str | None = None,
        column_specs: list[str] | None = None,
        max_width: int | None = None,
        row_separators: bool = True,
        wrap_text: bool = True,
        return_widths: bool = False,
        enforce_widths: dict[str, Any] | None = None,
    ) -> Union[str, Tuple[str, Dict[str, Any]]]:
        """
        Format list of commands.

        Parameters
        ----------
        commands : Dict[str, CommandMetadata]
            Command metadata dictionary
        group_name : str, optional
            Group name to display in table
        column_specs : List[str], optional
            Column format specifications (passed to render_table)
        max_width : int, optional
            Maximum table width (passed to render_table)
        row_separators : bool, default True
            Whether to render row separators (passed to render_table)
        wrap_text : bool, default True
            If True, wrap long descriptions into multiple lines.
            Default is True for help text to improve readability.
        return_widths : bool, default False
            If True, returns tuple (table_str, widths_dict) instead of just table_str.
            widths_dict contains 'column_widths' (list) and 'total_width' (int).
        enforce_widths : dict[str, Any], optional
            Force specific column widths instead of auto-calculating. Dict must contain
            'column_widths' key with list of integers. Used for multi-table synchronization.

        Returns
        -------
        str or Tuple[str, Dict[str, Any]]
            If return_widths=False: Formatted command list as string.
            If return_widths=True: Tuple of (table_str, widths_dict) where widths_dict
            contains 'column_widths' (List[int]) and 'total_width' (int).
        """
        if not commands:
            return "No commands available"

        # Build table data with ANSI colors for command names
        table_data = []

        # Add group header if provided
        if group_name:
            table_data.append([group_name, ""])

        # Add commands
        for cmd_name, metadata in sorted(commands.items()):
            # Apply light blue color to command name only
            colored_usage = f"{ANSI_LIGHT_BLUE}{metadata.usage}{ANSI_RESET}"
            table_data.append([colored_usage, metadata.description])

        # Render table with user-configured theme (falls back to 'grid' if not set)
        headers = ["Command", "Description"]
        theme = get_default_theme()

        return render_table(
            table_data,
            headers=headers,
            theme=theme,
            column_specs=column_specs,
            max_width=max_width,
            row_separators=row_separators,
            wrap_text=wrap_text,
            return_widths=return_widths,
            enforce_widths=enforce_widths,
        )

    @staticmethod
    def format_aligned_sections(
        sections: list[tuple[str, dict[str, basefunctions.cli.CommandMetadata]]],
    ) -> list[str]:
        """
        Render multiple command tables with synchronized column widths.

        Performs a two-pass rendering:
        Pass 1 measures each section to find the maximum width per column.
        Pass 2 renders all sections with enforced uniform column widths.

        Parameters
        ----------
        sections : list[tuple[str, dict[str, CommandMetadata]]]
            List of (display_name, commands_dict) tuples. display_name is used
            as group_name in the table header. Empty commands dicts are skipped.

        Returns
        -------
        list[str]
            Rendered table strings, one per non-empty section, all with identical
            column widths.
        """
        # filter out empty sections
        valid = [(name, cmds) for name, cmds in sections if cmds]
        if not valid:
            return []

        # Pass 1: measure column widths
        all_col_widths: list[list[int]] = []
        for display_name, commands in valid:
            result = HelpFormatter.format_command_list(
                commands,
                group_name=display_name if display_name else None,  # type: ignore[arg-type]
                return_widths=True,
            )
            # result is (str, widths_dict) when return_widths=True
            _, widths = result  # type: ignore[misc]
            widths_dict: Dict[str, Any] = widths  # type: ignore[assignment]
            all_col_widths.append(widths_dict["column_widths"])

        # compute max width per column
        num_cols = len(all_col_widths[0])
        max_col_widths = [
            max(w[i] for w in all_col_widths) for i in range(num_cols)
        ]

        # Pass 2: render with enforced widths
        rendered: list[str] = []
        for display_name, commands in valid:
            text = HelpFormatter.format_command_list(
                commands,
                group_name=display_name if display_name else None,  # type: ignore[arg-type]
                enforce_widths={"column_widths": max_col_widths},
            )
            rendered.append(text)  # type: ignore[arg-type]

        return rendered

    @staticmethod
    def format_command_details(metadata: basefunctions.cli.CommandMetadata) -> str:
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
        lines = [
            f"Command: {metadata.name}",
            f"Description: {metadata.description}",
            f"Usage: {metadata.usage}",
            "",
        ]

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
    def format_group_help(group_name: str, handler: basefunctions.cli.BaseCommand, command: str | None = None) -> str:
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

        commands = {}
        for cmd_name in handler.get_available_commands():
            metadata = handler.get_command_metadata(cmd_name)
            if metadata:
                commands[cmd_name] = metadata

        # Format group name for display
        display_name = f"{group_name.upper()} COMMANDS" if group_name else "ROOT COMMANDS"

        result = HelpFormatter.format_command_list(commands, group_name=display_name)
        return result if isinstance(result, str) else result[0]

    @staticmethod
    def format_aliases(aliases: dict[str, tuple]) -> str:
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
    def format_error(message: str, suggestion: str | None = None) -> str:
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
