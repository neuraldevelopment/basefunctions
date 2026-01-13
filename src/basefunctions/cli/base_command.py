"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Abstract base command class for CLI framework
 Log:
 v1.0 : Initial implementation
=============================================================================
"""

from __future__ import annotations

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from abc import ABC, abstractmethod
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


class BaseCommand(ABC):
    """
    Abstract base class for CLI command groups.

    Provides common infrastructure for command registration,
    execution, and help generation.
    """

    def __init__(self, context_manager):
        """
        Initialize base command.

        Parameters
        ----------
        context_manager : ContextManager
            Shared context manager instance
        """
        self.context = context_manager
        self.logger = get_logger(__name__)
        self._commands: dict[str, basefunctions.cli.CommandMetadata] = {}
        self._register_commands()

    @abstractmethod
    def register_commands(self) -> dict[str, basefunctions.cli.CommandMetadata]:
        """
        Register available commands with metadata.

        Returns
        -------
        Dict[str, CommandMetadata]
            Command name to metadata mapping
        """
        pass

    @abstractmethod
    def execute(self, command: str, args: list[str]) -> None:
        """
        Execute specific command.

        Parameters
        ----------
        command : str
            Command name
        args : List[str]
            Command arguments
        """
        pass

    def _register_commands(self) -> None:
        """Register commands from subclass."""
        self._commands = self.register_commands()

    def get_available_commands(self) -> list[str]:
        """
        Get list of available commands.

        Returns
        -------
        List[str]
            Command names
        """
        return list(self._commands.keys())

    def get_command_metadata(self, command: str) -> basefunctions.cli.CommandMetadata:
        """
        Get metadata for specific command.

        Parameters
        ----------
        command : str
            Command name

        Returns
        -------
        CommandMetadata
            Command metadata or None
        """
        return self._commands.get(command)

    def validate_command(self, command: str) -> bool:
        """
        Validate if command exists.

        Parameters
        ----------
        command : str
            Command name

        Returns
        -------
        bool
            True if command exists
        """
        return command in self._commands

    def get_help(self, command: str | None = None) -> str:
        """
        Generate help text.

        Parameters
        ----------
        command : str, optional
            Specific command help

        Returns
        -------
        str
            Formatted help text
        """
        if command:
            return self._get_specific_help(command)
        return self._get_general_help()

    def _get_general_help(self) -> str:
        """
        Generate general help for all commands.

        Returns
        -------
        str
            Formatted help text
        """
        if not self._commands:
            return "No commands available"

        lines = []
        for cmd_name, metadata in self._commands.items():
            lines.append(f"  {metadata.usage:<40} - {metadata.description}")

        return "\n".join(lines)

    def _get_specific_help(self, command: str) -> str:
        """
        Generate detailed help for command.

        Parameters
        ----------
        command : str
            Command name

        Returns
        -------
        str
            Formatted help text
        """
        metadata = self._commands.get(command)
        if not metadata:
            return f"Unknown command: {command}"

        lines = [
            f"Command: {metadata.name}",
            f"Description: {metadata.description}",
            f"Usage: {metadata.usage}",
        ]

        if metadata.examples:
            lines.append("Examples:")
            for example in metadata.examples:
                lines.append(f"  {example}")

        return "\n".join(lines)

    def _handle_error(self, command: str, error: Exception) -> None:
        """
        Handle command execution error.

        Parameters
        ----------
        command : str
            Command that failed
        error : Exception
            Error that occurred
        """
        self.logger.critical(f"command '{command}' failed: {str(error)}")
        print(f"Error: {str(error)}")

    def _confirm_action(self, message: str) -> bool:
        """
        Get user confirmation.

        Parameters
        ----------
        message : str
            Confirmation message

        Returns
        -------
        bool
            True if confirmed
        """
        try:
            response = input(f"{message} (y/N): ").strip().lower()
            return response == "y"
        except (KeyboardInterrupt, EOFError):
            return False
