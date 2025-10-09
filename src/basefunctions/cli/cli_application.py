"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Main CLI application orchestrator
 Log:
 v1.0 : Initial implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import sys
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


class CLIApplication:
    """
    Main CLI application orchestrator.

    Coordinates command execution, context management,
    and user interaction through command registry.
    """

    def __init__(self, app_name: str, version: str = "1.0"):
        """
        Initialize CLI application.

        Parameters
        ----------
        app_name : str
            Application name
        version : str
            Application version
        """
        self.app_name = app_name
        self.version = version
        self.running = True

        self.context = basefunctions.cli.ContextManager(app_name)
        self.registry = basefunctions.cli.CommandRegistry()
        self.parser = basefunctions.cli.ArgumentParser()
        self.logger = basefunctions.get_logger(__name__)

    def register_command_group(self, group_name: str, handler: "basefunctions.cli.BaseCommand") -> None:
        """
        Register command group.

        Parameters
        ----------
        group_name : str
            Group name (empty string for root-level)
        handler : BaseCommand
            Command handler instance
        """
        self.registry.register_group(group_name, handler)

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
        self.registry.register_alias(alias, target)

    def run(self) -> None:
        """Run interactive CLI main loop."""
        self._show_welcome()

        while self.running:
            try:
                prompt = self.context.get_prompt()
                command_line = input(prompt).strip()

                if not command_line:
                    continue

                self._execute_command(command_line)

            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except EOFError:
                break

        self._cleanup()

    def _show_welcome(self) -> None:
        """Display welcome message."""
        print(f"{self.app_name} v{self.version}")
        print("Type 'help' for commands or 'quit' to exit")
        print()

    def _execute_command(self, command_line: str) -> None:
        """
        Execute parsed command line.

        Parameters
        ----------
        command_line : str
            Raw command line input
        """
        command, subcommand, args = self.parser.parse_command(command_line)

        if not command:
            return

        if command in ["quit", "exit"]:
            self._cmd_quit()
            return
        elif command == "help":
            self._cmd_help(subcommand, args)
            return

        command, subcommand = self.registry.resolve_alias(command, subcommand)

        if subcommand is None:
            handler = self.registry.get_handler("")
            if handler and handler.validate_command(command):
                try:
                    handler.execute(command, args)
                except Exception as e:
                    self.logger.critical(f"command execution failed: {str(e)}")
                    print(f"Error: {str(e)}")
                return

        try:
            self.registry.dispatch(command, subcommand, args)
        except ValueError as e:
            print(f"Error: {str(e)}")
        except Exception as e:
            self.logger.critical(f"command execution failed: {str(e)}")
            print(f"Error: {str(e)}")

    def _cmd_quit(self) -> None:
        """Exit CLI."""
        print("Goodbye!")
        self.running = False

    def _cmd_help(self, group: str = None, args: list = None) -> None:
        """
        Show help information.

        Parameters
        ----------
        group : str, optional
            Specific command group
        args : list, optional
            Additional arguments
        """
        if not group:
            self._show_general_help()
        elif group == "aliases":
            self._show_aliases()
        else:
            self._show_group_help(group, args)

    def _show_general_help(self) -> None:
        """Show general help for all commands."""
        print("Available commands:\n")

        for group_name in self.registry.get_all_groups():
            handler = self.registry.get_handler(group_name)
            if not handler:
                continue

            if group_name:
                print(f"{group_name.upper()} COMMANDS:")
            else:
                print("ROOT COMMANDS:")

            help_text = handler.get_help()
            for line in help_text.split("\n"):
                if line.strip():
                    print(f" {line}")
            print()

        aliases = self.registry.get_all_aliases()
        if aliases:
            print("ALIASES:")
            for alias, (group, cmd) in sorted(aliases.items()):
                target = f"{group} {cmd}" if group else cmd
                print(f"  {alias:<15} -> {target}")
            print()

        print("GENERAL:")
        print("  help [command]      - Show help")
        print("  quit/exit           - Exit CLI")

    def _show_aliases(self) -> None:
        """Show available aliases."""
        aliases = self.registry.get_all_aliases()
        if aliases:
            print("Available aliases:")
            for alias, (group, cmd) in sorted(aliases.items()):
                target = f"{group} {cmd}" if group else cmd
                print(f"  {alias:<15} -> {target}")
        else:
            print("No aliases configured")

    def _show_group_help(self, group: str, args: list) -> None:
        """
        Show help for command group.

        Parameters
        ----------
        group : str
            Group name
        args : list
            Additional arguments
        """
        handler = self.registry.get_handler(group)
        if not handler:
            print(f"Unknown command: {group}")
            return

        command = args[0] if args else None
        help_text = handler.get_help(command)
        print(help_text)

    def _cleanup(self) -> None:
        """Cleanup resources on exit."""
        self.logger.critical("CLI session ended")
