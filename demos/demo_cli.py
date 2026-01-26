"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Interactive REPL demo for basefunctions.cli framework showing command patterns.

 Demonstrates:
 - Interactive REPL with prompt-based input
 - BaseCommand subclass implementation
 - CLIApplication registration and execution
 - Commands: help, list, list-rec, quit, exit
 - Error handling for user input and interrupts

 Usage:
   python demos/demo_cli.py
   demo_cli> help
   demo_cli> list
   demo_cli> list-rec
   demo_cli> quit

 Log:
 v2.3 : Add command history support (readline, 50 entries limit)
 v2.2 : Add optional directory parameter to list commands
 v2.1 : Use basefunctions.io.create_file_list for real filesystem operations
 v2.0 : Interactive REPL
 v1.0 : Initial implementation
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
# Standard Library
import os
import readline
from pathlib import Path
from typing import Any, Dict

# Project modules
from basefunctions.cli import BaseCommand, CLIApplication, CommandMetadata
from basefunctions.io import create_file_list, check_if_dir_exists


# =============================================================================
# CLASS DEFINITIONS
# =============================================================================
class DemoCommands(BaseCommand):
    """
    Demo command group for interactive CLI operations.

    Implements commands:
    - help: Show available commands
    - list: List items (non-recursive)
    - list-rec: List items (recursive)
    - quit/exit: Exit REPL
    """

    def register_commands(self) -> Dict[str, CommandMetadata]:
        """
        Register available demo commands including quit/exit.

        Returns
        -------
        Dict[str, CommandMetadata]
            Command metadata dictionary with command names as keys

        Examples
        --------
        >>> commands = DemoCommands()
        >>> metadata = commands.register_commands()
        >>> 'help' in metadata
        True
        >>> 'quit' in metadata
        True
        """
        return {
            "help": CommandMetadata(
                name="help",
                description="Show available commands and usage information",
                usage="help"
            ),
            "list": CommandMetadata(
                name="list",
                description="List items in directory (non-recursive)",
                usage="list [directory]"
            ),
            "list-rec": CommandMetadata(
                name="list-rec",
                description="List items in directory recursively",
                usage="list-rec [directory]"
            ),
            "quit": CommandMetadata(
                name="quit",
                description="Exit the interactive REPL",
                usage="quit"
            ),
            "exit": CommandMetadata(
                name="exit",
                description="Exit the interactive REPL (alias for quit)",
                usage="exit"
            )
        }

    def execute(self, command: str, _args: list[str]) -> Any:
        """
        Execute a demo command.

        Parameters
        ----------
        command : str
            Command name to execute
        _args : list[str]
            Command arguments (directory path for list commands)

        Returns
        -------
        Any
            Command execution result

        Raises
        ------
        ValueError
            If command is not recognized

        Examples
        --------
        >>> commands = DemoCommands(context)
        >>> commands.execute("help", [])
        Available Commands:
        ...
        """
        # Handle quit/exit at execute level
        if command == "quit":
            return None

        if command == "exit":
            return None

        if command == "help":
            return self._execute_help()
        elif command == "list":
            directory = _args[0] if _args else "."
            return self._execute_list(recursive=False, directory=directory)
        elif command == "list-rec":
            directory = _args[0] if _args else "."
            return self._execute_list(recursive=True, directory=directory)
        else:
            raise ValueError(f"Unknown command: {command}")

    def _execute_help(self) -> None:
        """
        Execute help command.

        Displays available commands and usage information including quit.

        Returns
        -------
        None
        """
        print("\n" + "=" * 70)
        print("Demo CLI - Available Commands")
        print("=" * 70)

        commands = self.register_commands()

        print("\nAvailable Commands:")
        for name, metadata in commands.items():
            print(f"\n  {name}")
            print(f"    {metadata.description}")

        print("\nUsage:")
        print("  Enter command at prompt: demo_cli> <command>")

        print("\nExamples:")
        print("  demo_cli> help")
        print("  demo_cli> list")
        print("  demo_cli> list ..")
        print("  demo_cli> list demos")
        print("  demo_cli> list-rec src")
        print("  demo_cli> quit")
        print("\n" + "=" * 70 + "\n")

    def _execute_list(self, recursive: bool = False, directory: str = ".") -> None:
        """
        Execute list command using basefunctions.io.create_file_list().

        Lists items in specified directory with type indicators (FILE/DIR).

        Parameters
        ----------
        recursive : bool, default False
            If True, list recursively; if False, list current level only
        directory : str, default "."
            Directory to list (can be relative like ".." for parent)

        Returns
        -------
        None

        Raises
        ------
        ValueError
            If directory does not exist
        """
        # Validate directory exists
        if not check_if_dir_exists(directory):
            raise ValueError(f"Directory not found: {directory}")

        mode = "Recursive" if recursive else "Non-Recursive"
        print(f"\n{mode} Directory Listing: {directory}")
        print("=" * 70)

        # Get file list from basefunctions
        items = create_file_list(
            dir_name=directory,
            recursive=recursive,
            append_dirs=True,
            add_hidden_files=False
        )

        if not items:
            print("\n(empty)")
        else:
            print()
            for item in items:
                item_type = "DIR" if os.path.isdir(item) else "FILE"
                print(f"{item} ({item_type})")

        print("\n" + "=" * 70 + "\n")


# =============================================================================
# FUNCTION DEFINITIONS
# =============================================================================
def main() -> None:
    """
    Main entry point for interactive demo CLI REPL with command history.

    Creates CLIApplication, registers demo command group, and runs
    interactive REPL loop with prompt-based command execution.

    Loads command history from .cli/demo_cli_history on startup and saves
    on exit. History is limited to 50 entries (consistent with CompletionHandler).

    Handles:
    - Welcome/Goodbye messages
    - Command input via prompt with history support
    - Command execution
    - Error handling (ValueError, KeyboardInterrupt, EOFError)
    - Quit/Exit commands

    Returns
    -------
    None

    Examples
    --------
    Run from command line:
        $ python demos/demo_cli.py
        Welcome to Demo CLI!
        Type 'help' for available commands, 'quit' to exit.

        demo_cli> help
        ...
        demo_cli> quit
        Goodbye!
    """
    # Create CLI application
    app = CLIApplication(app_name="demo-cli", version="2.0.0")

    # Register demo command group (app.registry has context)
    demo_commands = DemoCommands(app.context)
    app.register_command_group("demo", demo_commands)

    # Setup command history
    history_file = Path(".cli/demo_cli_history")
    history_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        readline.read_history_file(str(history_file))
        readline.set_history_length(50)  # Consistent with CompletionHandler
    except FileNotFoundError:
        pass  # First run, no history file yet

    # Print welcome message
    print("\n" + "=" * 70)
    print("Welcome to Demo CLI!")
    print("Type 'help' for available commands, 'quit' to exit.")
    print("=" * 70 + "\n")

    try:
        # Interactive REPL loop
        while True:
            try:
                # Get user input
                user_input = input("demo_cli> ").strip()

                # Skip empty input
                if not user_input:
                    continue

                # Check for quit/exit
                if user_input in ("quit", "exit"):
                    print("\nGoodbye!\n")
                    break

                # Parse command and arguments
                parts = user_input.split()
                command = parts[0]
                args = parts[1:] if len(parts) > 1 else []

                # Execute command
                demo_commands.execute(command, args)

            except ValueError as e:
                # Unknown command
                print(f"\nError: {e}")
                print("Type 'help' for available commands.\n")

            except (KeyboardInterrupt, EOFError):
                # Handle Ctrl+C or Ctrl+D
                print("\n\nGoodbye!\n")
                break
    finally:
        # Save command history
        try:
            readline.write_history_file(str(history_file))
        except Exception:
            pass  # Ignore write errors


if __name__ == "__main__":
    main()
