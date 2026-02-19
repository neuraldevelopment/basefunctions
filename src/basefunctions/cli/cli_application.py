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
 v1.1 : Fixed multi-handler support for root commands
 v1.2 : Fixed root command not found error handling
 v1.3 : Fixed intelligent command parsing with registry lookup
 v1.4 : Fixed group commands that match their own command name
 v1.5 : Fixed group commands with args when command name exists in group
 v1.6 : Integrated automatic tab completion support
 v1.7 : Added comprehensive exception handling
 v1.8 : Added lazy loading support with register_command_group_lazy
 v1.9 : Added tool_name parameter for completion history
 v1.10 : Display ALIASES and GENERAL as tables using format_command_list
 v1.11 : Add _collect_help_sections, refactor _show_general_help to use format_aligned_sections
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


class CLIApplication:
    """
    Main CLI application orchestrator.

    Coordinates command execution, context management,
    and user interaction through command registry.
    """

    def __init__(
        self,
        app_name: str,
        version: str = "1.0",
        enable_completion: bool = True,
        tool_name: str | None = None,
    ):
        """
        Initialize CLI application.

        Parameters
        ----------
        app_name : str
            Application name
        version : str
            Application version
        enable_completion : bool
            Enable tab completion (default: True)
        tool_name : str, optional
            Tool name for completion history (defaults to app_name if None)

        Examples
        --------
        >>> app = CLIApplication("myapp")
        >>> # History: ~/.neuraldevelopment/completion/myapp.completion

        >>> app = CLIApplication("basefunctions", tool_name="ppip")
        >>> # History: ~/.neuraldevelopment/completion/basefunctions_ppip.completion
        """
        self.app_name = app_name
        self.version = version
        self.tool_name = tool_name
        self.running = True

        self.context = basefunctions.cli.ContextManager(app_name)
        self.registry = basefunctions.cli.CommandRegistry()
        self.registry.set_context(self.context)
        self.parser = basefunctions.cli.ArgumentParser()
        self.logger = get_logger(__name__)

        self.completion = None
        if enable_completion:
            self.completion = basefunctions.cli.CompletionHandler(
                self.registry, self.context, self.app_name, tool_name
            )
            self.completion.setup()
            self.logger.info("tab completion enabled")

    def register_command_group(self, group_name: str, handler: basefunctions.cli.BaseCommand) -> None:
        """
        Register command group with eager loading.

        Parameters
        ----------
        group_name : str
            Group name (empty string for root-level)
        handler : BaseCommand
            Command handler instance
        """
        self.registry.register_group(group_name, handler)

    def register_command_group_lazy(self, group_name: str, module_path: str) -> None:
        """
        Register command group with lazy loading.

        Handler will be imported and instantiated on first access.
        Improves startup time by deferring imports until needed.

        Parameters
        ----------
        group_name : str
            Group name (empty string for root-level)
        module_path : str
            Module path in format "module.path:ClassName"
            Example: "dbfunctions.dbadmin.list_commands:ListCommands"

        Raises
        ------
        ValueError
            If module_path format is invalid

        Examples
        --------
        Register a command group that will be loaded on first use:

        >>> app = CLIApplication("myapp")
        >>> app.register_command_group_lazy("db", "myapp.commands.db:DatabaseCommands")

        The DatabaseCommands class will only be imported when a user
        executes a "db" command for the first time.
        """
        self.registry.register_group_lazy(group_name, module_path)

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
            except Exception as e:
                self.logger.critical(f"unexpected error in main loop: {type(e).__name__}: {str(e)}")
                print(f"Error: An unexpected error occurred")
                print("(Exception details logged)")
                # Continue loop - CLI NEVER exits on exception

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
        try:
            part1, part2, rest_args = self.parser.parse_command(command_line)
        except Exception as e:
            self.logger.critical(f"command parsing failed: {type(e).__name__}: {str(e)}")
            print(f"Error: Failed to parse command")
            print("(Exception details logged)")
            return

        if not part1:
            return

        if part1 in ["quit", "exit"]:
            self._cmd_quit()
            return
        elif part1 == "help":
            self._cmd_help(part2, rest_args)
            return

        original_part1 = part1

        try:
            part1, part2 = self.registry.resolve_alias(part1, part2)
        except Exception as e:
            self.logger.critical(f"alias resolution failed: {type(e).__name__}: {str(e)}")
            print(f"Error: Failed to resolve alias")
            print("(Exception details logged)")
            return

        try:
            group_handlers = self.registry.get_handlers(part1)
        except Exception as e:
            self.logger.critical(f"handler retrieval failed: {type(e).__name__}: {str(e)}")
            print(f"Error: Failed to retrieve command handlers")
            print("(Exception details logged)")
            return
        if group_handlers:
            if part2:
                for handler in group_handlers:
                    if handler.validate_command(part1):
                        try:
                            args = [part2] + rest_args
                            handler.execute(part1, args)
                            return
                        except Exception as e:
                            self.logger.critical(f"command execution failed: {str(e)}")
                            print(f"Error: {str(e)}")
                            return

                try:
                    self.registry.dispatch(part1, part2, rest_args)
                    return
                except ValueError as e:
                    print(f"Error: {str(e)}")
                    return
            else:
                for handler in group_handlers:
                    if handler.validate_command(part1):
                        try:
                            handler.execute(part1, [])
                            return
                        except Exception as e:
                            self.logger.critical(f"command execution failed: {str(e)}")
                            print(f"Error: {str(e)}")
                            return

                print(f"Error: '{part1}' requires a subcommand")
                all_commands = []
                for handler in group_handlers:
                    all_commands.extend(handler.get_available_commands())
                if all_commands:
                    print(f"Available: {', '.join(sorted(set(all_commands)))}")
                return

        root_handlers = self.registry.get_handlers("")
        if root_handlers:
            for handler in root_handlers:
                if handler.validate_command(part1):
                    try:
                        args = [part2] + rest_args if part2 else rest_args
                        handler.execute(part1, args)
                        return
                    except Exception as e:
                        self.logger.critical(f"command execution failed: {str(e)}")
                        print(f"Error: {str(e)}")
                        return

        all_root_commands = []
        for handler in root_handlers:
            all_root_commands.extend(handler.get_available_commands())

        all_groups = [g for g in self.registry.get_all_groups() if g]

        print(f"Error: Unknown command: {original_part1}")
        if all_root_commands:
            print(f"Available root commands: {', '.join(sorted(set(all_root_commands)))}")
        if all_groups:
            print(f"Available command groups: {', '.join(sorted(all_groups))}")

    def _cmd_quit(self) -> None:
        """Exit CLI."""
        print("Goodbye!")
        self.running = False

    def _cmd_help(self, group: str | None = None, args: list | None = None) -> None:
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

    def _collect_help_sections(self) -> list[tuple[str, dict]]:
        """
        Collect all help sections as (display_name, commands_dict) tuples.

        Returns
        -------
        list[tuple[str, dict]]
            Sections for all groups, aliases, and general commands.
        """
        sections: list[tuple[str, dict]] = []

        for group_name in self.registry.get_all_groups():
            handlers = self.registry.get_handlers(group_name)
            if not handlers:
                continue
            group_commands: dict = {}
            for handler in handlers:
                for cmd_name in handler.get_available_commands():
                    metadata = handler.get_command_metadata(cmd_name)
                    if metadata:
                        group_commands[cmd_name] = metadata
            if group_commands:
                display_name = f"{group_name.upper()} COMMANDS" if group_name else "ROOT COMMANDS"
                sections.append((display_name, group_commands))

        aliases = self.registry.get_all_aliases()
        if aliases:
            alias_commands: dict = {}
            for alias, (group, cmd) in sorted(aliases.items()):
                target = f"{group} {cmd}" if group else cmd
                alias_commands[alias] = basefunctions.cli.CommandMetadata(
                    name=alias,
                    description=target,
                    usage=alias,
                )
            sections.append(("ALIASES", alias_commands))

        general_commands: dict = {
            "help [command]": basefunctions.cli.CommandMetadata(
                name="help",
                description="Show help",
                usage="help [command]",
            ),
            "quit/exit": basefunctions.cli.CommandMetadata(
                name="quit",
                description="Exit CLI",
                usage="quit/exit",
            ),
        }
        sections.append(("GENERAL", general_commands))

        return sections

    def _show_general_help(self) -> None:
        """Show general help for all commands."""
        print("Available commands:\n")
        sections = self._collect_help_sections()
        rendered = basefunctions.cli.HelpFormatter.format_aligned_sections(sections)
        for text in rendered:
            print(text)
            print()

    def _show_aliases(self) -> None:
        """Show available aliases."""
        aliases = self.registry.get_all_aliases()
        if not aliases:
            print("No aliases configured")
            return
        alias_commands = {}
        for alias, (group, cmd) in sorted(aliases.items()):
            target = f"{group} {cmd}" if group else cmd
            alias_commands[alias] = basefunctions.cli.CommandMetadata(
                name=alias,
                description=target,
                usage=alias,
            )
        help_text = basefunctions.cli.HelpFormatter.format_command_list(
            alias_commands, group_name="ALIASES"
        )
        print(help_text)
        print()

    def _show_group_help(self, group: str, args: list | None) -> None:
        """
        Show help for command group.

        Parameters
        ----------
        group : str
            Group name
        args : list, optional
            Additional arguments
        """
        handlers = self.registry.get_handlers(group)
        if not handlers:
            print(f"Unknown command: {group}")
            return

        command = args[0] if args else None

        for handler in handlers:
            help_text = handler.get_help(command, group_name=group)
            print(help_text)
            if command:
                break

    def _cleanup(self) -> None:
        """Cleanup resources on exit."""
        if self.completion:
            self.completion.cleanup()
        self.logger.info("CLI session ended")
