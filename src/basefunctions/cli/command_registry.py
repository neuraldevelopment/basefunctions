"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Command registration and dispatch system
 Log:
 v1.0 : Initial implementation
 v1.1 : Fixed multi-handler support for same group
=============================================================================
"""

from __future__ import annotations

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from basefunctions.utils.logging import setup_logger, get_logger
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


class CommandRegistry:
    """
    Command registration and dispatch system.

    Manages command groups, aliases, and routing with
    support for both grouped and root-level commands.
    Supports multiple handlers per group.
    """

    def __init__(self):
        """Initialize command registry."""
        self.logger = get_logger(__name__)
        self._groups: dict[str, list[basefunctions.cli.BaseCommand]] = {}
        self._aliases: dict[str, tuple[str, str]] = {}

    def register_group(self, group_name: str, command_handler: basefunctions.cli.BaseCommand) -> None:
        """
        Register command group.

        Parameters
        ----------
        group_name : str
            Group name (empty string for root-level commands)
        command_handler : BaseCommand
            Command handler instance
        """
        if group_name not in self._groups:
            self._groups[group_name] = []

        self._groups[group_name].append(command_handler)
        self.logger.info(
            f"registered command group: {group_name or 'root'} (handler #{len(self._groups[group_name])})"
        )

    def register_alias(self, alias: str, target: str) -> None:
        """
        Register command alias.

        Parameters
        ----------
        alias : str
            Alias name
        target : str
            Target command (format: "group command" or "command")
        """
        parts = target.split(None, 1)
        if len(parts) == 2:
            self._aliases[alias] = (parts[0], parts[1])
        else:
            self._aliases[alias] = ("", parts[0])
        self.logger.info(f"registered alias: {alias} -> {target}")

    def resolve_alias(self, command: str, subcommand: str | None) -> tuple[str, str | None]:
        """
        Resolve command alias.

        Parameters
        ----------
        command : str
            Command name
        subcommand : Optional[str]
            Subcommand name

        Returns
        -------
        Tuple[str, Optional[str]]
            (resolved_command, resolved_subcommand)
        """
        if command in self._aliases and subcommand is None:
            return self._aliases[command]
        return command, subcommand

    def get_handlers(self, group_name: str) -> list[basefunctions.cli.BaseCommand]:
        """
        Get all command handlers for group.

        Parameters
        ----------
        group_name : str
            Group name

        Returns
        -------
        List[BaseCommand]
            List of command handlers (empty list if none found)
        """
        return self._groups.get(group_name, [])

    def get_handler(self, group_name: str) -> basefunctions.cli.BaseCommand | None:
        """
        Get first command handler for group.

        DEPRECATED: Use get_handlers() instead for multi-handler support.

        Parameters
        ----------
        group_name : str
            Group name

        Returns
        -------
        Optional[BaseCommand]
            First command handler or None
        """
        handlers = self.get_handlers(group_name)
        return handlers[0] if handlers else None

    def get_all_groups(self) -> list[str]:
        """
        Get all registered groups.

        Returns
        -------
        List[str]
            Group names
        """
        return list(self._groups.keys())

    def get_all_aliases(self) -> dict[str, tuple[str, str]]:
        """
        Get all registered aliases.

        Returns
        -------
        Dict[str, Tuple[str, str]]
            Alias to (group, command) mapping
        """
        return self._aliases.copy()

    def dispatch(self, group_name: str, command: str, args: list[str]) -> bool:
        """
        Dispatch command to handler.

        Parameters
        ----------
        group_name : str
            Group name
        command : str
            Command name
        args : List[str]
            Command arguments

        Returns
        -------
        bool
            True if dispatched successfully

        Raises
        ------
        ValueError
            If group or command not found
        """
        handlers = self.get_handlers(group_name)
        if not handlers:
            raise ValueError(f"Unknown command group: {group_name}")

        for handler in handlers:
            if handler.validate_command(command):
                handler.execute(command, args)
                return True

        all_commands = []
        for handler in handlers:
            all_commands.extend(handler.get_available_commands())

        available = ", ".join(sorted(set(all_commands)))
        raise ValueError(f"Unknown command: {command}\nAvailable: {available}")

    def get_command_metadata(self, group_name: str, command: str) -> basefunctions.cli.CommandMetadata | None:
        """
        Get command metadata.

        Parameters
        ----------
        group_name : str
            Group name
        command : str
            Command name

        Returns
        -------
        Optional[CommandMetadata]
            Command metadata or None
        """
        handlers = self.get_handlers(group_name)

        for handler in handlers:
            metadata = handler.get_command_metadata(command)
            if metadata:
                return metadata

        return None
