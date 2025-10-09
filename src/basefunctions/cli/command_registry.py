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
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Dict, List, Optional, Tuple
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

# -------------------------------------------------------------
# CLASS OR FUNCTION DEFINITIONS
# -------------------------------------------------------------


class CommandRegistry:
    """
    Command registration and dispatch system.

    Manages command groups, aliases, and routing with
    support for both grouped and root-level commands.
    """

    def __init__(self):
        """Initialize command registry."""
        self.logger = basefunctions.get_logger(__name__)
        self._groups: Dict[str, "basefunctions.cli.BaseCommand"] = {}
        self._aliases: Dict[str, Tuple[str, str]] = {}

    def register_group(self, group_name: str, command_handler: "basefunctions.cli.BaseCommand") -> None:
        """
        Register command group.

        Parameters
        ----------
        group_name : str
            Group name (empty string for root-level commands)
        command_handler : BaseCommand
            Command handler instance
        """
        self._groups[group_name] = command_handler
        self.logger.critical(f"registered command group: {group_name or 'root'}")

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
        self.logger.critical(f"registered alias: {alias} -> {target}")

    def resolve_alias(self, command: str, subcommand: Optional[str]) -> Tuple[str, Optional[str]]:
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

    def get_handler(self, group_name: str) -> Optional["basefunctions.cli.BaseCommand"]:
        """
        Get command handler for group.

        Parameters
        ----------
        group_name : str
            Group name

        Returns
        -------
        Optional[BaseCommand]
            Command handler or None
        """
        return self._groups.get(group_name)

    def get_all_groups(self) -> List[str]:
        """
        Get all registered groups.

        Returns
        -------
        List[str]
            Group names
        """
        return list(self._groups.keys())

    def get_all_aliases(self) -> Dict[str, Tuple[str, str]]:
        """
        Get all registered aliases.

        Returns
        -------
        Dict[str, Tuple[str, str]]
            Alias to (group, command) mapping
        """
        return self._aliases.copy()

    def dispatch(self, group_name: str, command: str, args: List[str]) -> bool:
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
        handler = self.get_handler(group_name)
        if not handler:
            raise ValueError(f"Unknown command group: {group_name}")

        if not handler.validate_command(command):
            available = ", ".join(handler.get_available_commands())
            raise ValueError(f"Unknown command: {command}\nAvailable: {available}")

        handler.execute(command, args)
        return True

    def get_command_metadata(self, group_name: str, command: str) -> Optional["basefunctions.cli.CommandMetadata"]:
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
        handler = self.get_handler(group_name)
        if not handler:
            return None

        return handler.get_command_metadata(command)
