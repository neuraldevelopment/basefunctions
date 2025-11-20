"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Command line argument parser with context resolution
 Log:
 v1.0 : Initial implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import shlex
from typing import TYPE_CHECKING, List, Optional, Tuple
from basefunctions.utils.logging import setup_logger

if TYPE_CHECKING:
    from basefunctions.cli.command_metadata import ArgumentSpec, CommandMetadata
    from basefunctions.cli.context_manager import ContextManager

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


class ArgumentParser:
    """
    Command line argument parser with context resolution.

    Handles parsing of command lines into structured components
    with proper handling of quoted arguments and shell-like syntax.
    """

    @staticmethod
    def parse_command(
        command_line: str,
    ) -> Tuple[Optional[str], Optional[str], List[str]]:
        """
        Parse command line into components.

        Parameters
        ----------
        command_line : str
            Raw command line input

        Returns
        -------
        Tuple[Optional[str], Optional[str], List[str]]
            (command_group, subcommand, args) or (None, None, []) on error
        """
        if not command_line or not command_line.strip():
            return None, None, []

        try:
            parts = shlex.split(command_line.strip())
            if not parts:
                return None, None, []

            if len(parts) == 1:
                return parts[0], None, []
            else:
                return parts[0], parts[1], parts[2:]

        except ValueError as e:
            print(f"Error: Invalid command syntax - {str(e)}")
            return None, None, []

    @staticmethod
    def validate_args(metadata: "CommandMetadata", args: List[str]) -> bool:
        """
        Validate arguments against metadata.

        Parameters
        ----------
        metadata : CommandMetadata
            Command metadata
        args : List[str]
            Provided arguments

        Returns
        -------
        bool
            True if valid
        """
        required_count = len(metadata.get_required_args())
        total_count = len(metadata.args)
        provided_count = len(args)

        if provided_count < required_count:
            return False
        if provided_count > total_count:
            return False

        return True

    @staticmethod
    def resolve_argument_with_context(
        arg: Optional[str],
        arg_spec: "ArgumentSpec",
        context_manager: "ContextManager",
    ) -> Optional[str]:
        """
        Resolve argument with context fallback.

        Parameters
        ----------
        arg : Optional[str]
            Provided argument
        arg_spec : ArgumentSpec
            Argument specification
        context_manager : ContextManager
            Context manager instance

        Returns
        -------
        Optional[str]
            Resolved argument value

        Raises
        ------
        ValueError
            If required argument cannot be resolved
        """
        if arg:
            return arg

        if arg_spec.context_key:
            value = context_manager.get(arg_spec.context_key)
            if value:
                return value

        if arg_spec.required:
            raise ValueError(f"Required argument '{arg_spec.name}' not provided and no context available")

        return None

    @staticmethod
    def split_compound_argument(arg: str) -> Tuple[str, Optional[str]]:
        """
        Split compound argument (e.g., "instance.database").

        Parameters
        ----------
        arg : str
            Compound argument

        Returns
        -------
        Tuple[str, Optional[str]]
            (primary, secondary) parts
        """
        if "." in arg:
            parts = arg.split(".", 1)
            return parts[0], parts[1]
        return arg, None
