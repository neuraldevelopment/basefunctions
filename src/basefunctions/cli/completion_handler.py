"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Tab completion handler for CLI commands
 Log:
 v1.0 : Initial implementation
 v1.1 : Fixed multi-handler support for completion
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import List, Optional, Callable
import basefunctions

try:
    import readline
except ImportError:
    try:
        import pyreadline as readline
    except ImportError:
        readline = None

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


class CompletionHandler:
    """
    Tab completion handler for CLI commands.

    Provides intelligent tab completion based on command
    context, metadata, and custom completion functions.
    """

    def __init__(self, registry: "basefunctions.cli.CommandRegistry", context: "basefunctions.cli.ContextManager"):
        """
        Initialize completion handler.

        Parameters
        ----------
        registry : CommandRegistry
            Command registry instance
        context : ContextManager
            Context manager instance
        """
        self.registry = registry
        self.context = context
        self.logger = basefunctions.get_logger(__name__)

    def complete(self, text: str, state: int) -> Optional[str]:
        """
        Main completion handler for readline.

        Parameters
        ----------
        text : str
            Current text being completed
        state : int
            Completion state (0 for first match, incrementing)

        Returns
        -------
        Optional[str]
            Completion suggestion or None
        """
        if not readline:
            return None

        try:
            line = readline.get_line_buffer()
            parts = line.split()

            if not parts or (len(parts) == 1 and not line.endswith(" ")):
                matches = self._complete_command_groups(text)
            else:
                matches = self._complete_arguments(parts, text, line.endswith(" "))

            return matches[state] if state < len(matches) else None

        except Exception:
            return None

    def _complete_command_groups(self, text: str) -> List[str]:
        """
        Complete command group names and aliases.

        Parameters
        ----------
        text : str
            Text to complete

        Returns
        -------
        List[str]
            Matching command groups and aliases
        """
        groups = self.registry.get_all_groups()
        aliases = list(self.registry.get_all_aliases().keys())
        special = ["help", "quit", "exit"]

        all_commands = [g for g in groups if g] + aliases + special
        return [cmd for cmd in all_commands if cmd.startswith(text)]

    def _complete_arguments(self, parts: List[str], text: str, has_space: bool) -> List[str]:
        """
        Complete command arguments.

        Parameters
        ----------
        parts : List[str]
            Parsed command parts
        text : str
            Text to complete
        has_space : bool
            Whether line ends with space

        Returns
        -------
        List[str]
            Matching completions
        """
        if len(parts) < 1:
            return []

        command = parts[0]
        subcommand = parts[1] if len(parts) > 1 else None

        command, subcommand = self.registry.resolve_alias(command, subcommand)

        if command in ["help", "quit", "exit"]:
            return []

        handlers = self.registry.get_handlers(command)
        if not handlers:
            handlers = self.registry.get_handlers("")

        if not handlers:
            return []

        if not subcommand or (len(parts) == 2 and not has_space):
            all_commands = []
            for handler in handlers:
                all_commands.extend(handler.get_available_commands())
            return [cmd for cmd in all_commands if cmd.startswith(text)]

        for handler in handlers:
            if handler.validate_command(subcommand):
                return self._complete_command_args(handler, subcommand, parts, text, has_space)

        return []

    def _complete_command_args(
        self, handler: "basefunctions.cli.BaseCommand", command: str, parts: List[str], text: str, has_space: bool
    ) -> List[str]:
        """
        Complete command arguments based on metadata.

        Parameters
        ----------
        handler : BaseCommand
            Command handler
        command : str
            Command name
        parts : List[str]
            Command parts
        text : str
            Text to complete
        has_space : bool
            Whether line ends with space

        Returns
        -------
        List[str]
            Matching completions
        """
        metadata = handler.get_command_metadata(command)
        if not metadata:
            return []

        arg_index = len(parts) - 2 if not has_space else len(parts) - 1

        if arg_index < 0 or arg_index >= len(metadata.args):
            return []

        arg_spec = metadata.args[arg_index]

        if arg_spec.completion_func:
            try:
                return arg_spec.completion_func(text, self.context)
            except Exception:
                return []

        if arg_spec.choices:
            return [choice for choice in arg_spec.choices if choice.startswith(text)]

        return []

    def setup(self) -> None:
        """Setup readline with tab completion."""
        if not readline:
            return

        readline.set_completer(self.complete)
        readline.parse_and_bind("tab: complete")

        try:
            readline.read_history_file()
        except FileNotFoundError:
            pass

    def cleanup(self) -> None:
        """Save readline history on exit."""
        if not readline:
            return

        try:
            readline.write_history_file()
        except Exception:
            pass


def setup_completion(handler: CompletionHandler) -> None:
    """
    Setup tab completion.

    Parameters
    ----------
    handler : CompletionHandler
        Completion handler instance
    """
    handler.setup()


def cleanup_completion(handler: CompletionHandler) -> None:
    """
    Cleanup completion on exit.

    Parameters
    ----------
    handler : CompletionHandler
        Completion handler instance
    """
    handler.cleanup()
