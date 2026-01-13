"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Comprehensive tests for CLIApplication exception handling and edge cases
 Log:
 v1.0 : Initial implementation - captures CURRENT behavior
=============================================================================
"""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard Library
from unittest.mock import Mock, patch

# Third-party
import pytest

# Project modules
from basefunctions.cli.cli_application import CLIApplication
from basefunctions.cli.base_command import BaseCommand


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def mock_context_manager():
    """Provide mocked ContextManager."""
    with patch("basefunctions.cli.cli_application.basefunctions.cli.ContextManager") as mock:
        mock_instance = Mock()
        mock_instance.get_prompt.return_value = "test> "
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def cli_app():
    """Provide CLIApplication instance with mocked dependencies."""
    with patch("basefunctions.cli.cli_application.basefunctions.cli.ContextManager"):
        with patch("basefunctions.cli.cli_application.basefunctions.cli.CompletionHandler"):
            app = CLIApplication("TestCLI", "1.0", enable_completion=False)
            return app


@pytest.fixture
def mock_command_handler():
    """Provide mocked command handler."""
    handler = Mock(spec=BaseCommand)
    handler.validate_command.return_value = True
    handler.get_available_commands.return_value = ["test_cmd"]
    handler.get_help.return_value = "Test command help"
    return handler


@pytest.fixture
def failing_command_handler():
    """Provide command handler that raises exceptions."""
    handler = Mock(spec=BaseCommand)
    handler.validate_command.return_value = True
    handler.get_available_commands.return_value = ["failing_cmd"]
    handler.get_help.return_value = "Failing command help"
    return handler


# =============================================================================
# TEST CASES: COMMAND EXECUTION EXCEPTIONS
# =============================================================================


class TestCommandExecutionExceptions:
    """Test exception handling during command execution."""

    def test_execute_command_with_generic_exception_logs_and_displays_error(
        self, cli_app, failing_command_handler, capsys
    ):
        """Test generic Exception during execute() is caught, logged, and displayed."""
        # Arrange
        failing_command_handler.execute.side_effect = Exception("Something went wrong")
        cli_app.register_command_group("test", failing_command_handler)

        # Act
        cli_app._execute_command("test failing_cmd")

        # Assert
        captured = capsys.readouterr()
        assert "Error: Something went wrong" in captured.out
        failing_command_handler.execute.assert_called_once()

    def test_execute_command_with_value_error_logs_and_displays_error(
        self, cli_app, failing_command_handler, capsys
    ):
        """Test ValueError during execute() is caught, logged, and displayed."""
        # Arrange
        failing_command_handler.execute.side_effect = ValueError("Invalid value provided")
        cli_app.register_command_group("test", failing_command_handler)

        # Act
        cli_app._execute_command("test failing_cmd")

        # Assert
        captured = capsys.readouterr()
        assert "Error: Invalid value provided" in captured.out
        failing_command_handler.execute.assert_called_once()

    def test_execute_command_with_runtime_error_logs_and_displays_error(
        self, cli_app, failing_command_handler, capsys
    ):
        """Test RuntimeError during execute() is caught, logged, and displayed."""
        # Arrange
        failing_command_handler.execute.side_effect = RuntimeError("Runtime failure")
        cli_app.register_command_group("test", failing_command_handler)

        # Act
        cli_app._execute_command("test failing_cmd")

        # Assert
        captured = capsys.readouterr()
        assert "Error: Runtime failure" in captured.out
        failing_command_handler.execute.assert_called_once()

    def test_execute_command_with_type_error_logs_and_displays_error(
        self, cli_app, failing_command_handler, capsys
    ):
        """Test TypeError during execute() is caught, logged, and displayed."""
        # Arrange
        failing_command_handler.execute.side_effect = TypeError("Wrong type")
        cli_app.register_command_group("test", failing_command_handler)

        # Act
        cli_app._execute_command("test failing_cmd")

        # Assert
        captured = capsys.readouterr()
        assert "Error: Wrong type" in captured.out
        failing_command_handler.execute.assert_called_once()

    def test_execute_root_command_with_exception_logs_and_displays_error(
        self, cli_app, failing_command_handler, capsys
    ):
        """Test Exception in root-level command is caught and displayed."""
        # Arrange
        failing_command_handler.execute.side_effect = Exception("Root command failed")
        cli_app.register_command_group("", failing_command_handler)

        # Act
        cli_app._execute_command("failing_cmd")

        # Assert
        captured = capsys.readouterr()
        assert "Error: Root command failed" in captured.out
        failing_command_handler.execute.assert_called_once()

    def test_execute_command_with_args_exception_logs_and_displays_error(
        self, cli_app, failing_command_handler, capsys
    ):
        """Test Exception in command with arguments is caught and displayed."""
        # Arrange
        failing_command_handler.execute.side_effect = Exception("Args processing failed")
        cli_app.register_command_group("test", failing_command_handler)

        # Act
        cli_app._execute_command("test failing_cmd arg1 arg2")

        # Assert
        captured = capsys.readouterr()
        assert "Error: Args processing failed" in captured.out
        # CURRENT behavior: group commands pass part2 as first arg when handler validates command
        failing_command_handler.execute.assert_called_once_with("test", ["failing_cmd", "arg1", "arg2"])

    def test_cli_continues_running_after_command_exception(
        self, cli_app, failing_command_handler
    ):
        """Test CLI continues accepting commands after exception."""
        # Arrange
        failing_command_handler.execute.side_effect = Exception("First failure")
        cli_app.register_command_group("test", failing_command_handler)

        # Act - first command fails
        cli_app._execute_command("test failing_cmd")

        # Reset side effect for second command
        failing_command_handler.execute.side_effect = None

        # Act - second command succeeds
        cli_app._execute_command("test failing_cmd")

        # Assert - both commands were attempted
        assert failing_command_handler.execute.call_count == 2


# =============================================================================
# TEST CASES: REGISTRY EXCEPTIONS
# =============================================================================


class TestRegistryExceptions:
    """Test exception handling during registry operations."""

    def test_dispatch_with_unknown_group_raises_value_error(self, cli_app, capsys):
        """Test dispatching to unknown group raises ValueError."""
        # Arrange - no handlers registered

        # Act
        cli_app._execute_command("unknown_group unknown_cmd")

        # Assert
        captured = capsys.readouterr()
        assert "Error: Unknown command: unknown_group" in captured.out

    def test_dispatch_with_invalid_subcommand_displays_error(
        self, cli_app, mock_command_handler, capsys
    ):
        """Test dispatching invalid subcommand displays error."""
        # Arrange
        mock_command_handler.validate_command.return_value = False
        cli_app.register_command_group("test", mock_command_handler)

        # Act
        cli_app._execute_command("test invalid_cmd")

        # Assert
        captured = capsys.readouterr()
        assert "Error: Unknown command: invalid_cmd" in captured.out

    def test_group_without_subcommand_displays_error(
        self, cli_app, mock_command_handler, capsys
    ):
        """Test group command without subcommand displays error message."""
        # Arrange
        mock_command_handler.validate_command.return_value = False
        cli_app.register_command_group("test", mock_command_handler)

        # Act
        cli_app._execute_command("test")

        # Assert
        captured = capsys.readouterr()
        assert "Error: 'test' requires a subcommand" in captured.out
        assert "Available: test_cmd" in captured.out

    def test_alias_resolution_with_registered_root_handler(
        self, cli_app, mock_command_handler
    ):
        """Test alias resolution executes when root handler exists."""
        # Arrange
        cli_app.register_alias("alias_cmd", "test_cmd")
        cli_app.register_command_group("", mock_command_handler)

        # Act
        cli_app._execute_command("alias_cmd")

        # Assert - alias resolves and executes
        mock_command_handler.execute.assert_called_once()


# =============================================================================
# TEST CASES: INPUT HANDLING
# =============================================================================


class TestInputHandling:
    """Test handling of various input edge cases."""

    def test_empty_input_is_ignored(self, cli_app, capsys):
        """Test empty input does not trigger command execution."""
        # Arrange - nothing

        # Act
        cli_app._execute_command("")

        # Assert - no output, no errors
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_whitespace_only_input_is_ignored(self, cli_app, capsys):
        """Test whitespace-only input is ignored after strip."""
        # Arrange - nothing

        # Act
        with patch.object(cli_app.parser, "parse_command", return_value=("", None, [])):
            cli_app._execute_command("   ")

        # Assert - no output, no errors
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_command_with_special_characters(
        self, cli_app, mock_command_handler
    ):
        """Test command with special characters in arguments."""
        # Arrange
        cli_app.register_command_group("test", mock_command_handler)

        # Act
        cli_app._execute_command('test test_cmd "arg with spaces" arg@special')

        # Assert - command is executed (special chars handled by parser)
        mock_command_handler.execute.assert_called_once()

    def test_unknown_root_command_displays_available_commands(
        self, cli_app, capsys
    ):
        """Test unknown root command displays available root commands."""
        # Arrange
        handler = Mock(spec=BaseCommand)
        handler.validate_command.side_effect = lambda cmd: cmd == "test_cmd"
        handler.get_available_commands.return_value = ["test_cmd"]
        handler.get_help.return_value = "Test command help"

        cli_app.register_command_group("", handler)
        cli_app.register_command_group("test", handler)

        # Act
        cli_app._execute_command("unknown")

        # Assert
        captured = capsys.readouterr()
        assert "Error: Unknown command: unknown" in captured.out
        assert "Available root commands: test_cmd" in captured.out
        assert "Available command groups: test" in captured.out

    def test_quit_command_stops_application(self, cli_app, capsys):
        """Test 'quit' command sets running flag to False."""
        # Arrange
        assert cli_app.running is True

        # Act
        cli_app._execute_command("quit")

        # Assert
        assert cli_app.running is False
        captured = capsys.readouterr()
        assert "Goodbye!" in captured.out

    def test_exit_command_stops_application(self, cli_app, capsys):
        """Test 'exit' command sets running flag to False."""
        # Arrange
        assert cli_app.running is True

        # Act
        cli_app._execute_command("exit")

        # Assert
        assert cli_app.running is False
        captured = capsys.readouterr()
        assert "Goodbye!" in captured.out


# =============================================================================
# TEST CASES: HELP COMMAND
# =============================================================================


class TestHelpCommand:
    """Test help command functionality."""

    def test_help_without_args_shows_general_help(
        self, cli_app, mock_command_handler, capsys
    ):
        """Test 'help' without arguments shows general help."""
        # Arrange
        cli_app.register_command_group("test", mock_command_handler)

        # Act
        cli_app._execute_command("help")

        # Assert
        captured = capsys.readouterr()
        assert "Available commands:" in captured.out
        assert "Test command help" in captured.out

    def test_help_with_group_shows_group_help(
        self, cli_app, mock_command_handler, capsys
    ):
        """Test 'help <group>' shows group-specific help."""
        # Arrange
        cli_app.register_command_group("test", mock_command_handler)

        # Act
        cli_app._execute_command("help test")

        # Assert
        captured = capsys.readouterr()
        assert "Test command help" in captured.out

    def test_help_aliases_shows_all_aliases(self, cli_app, capsys):
        """Test 'help aliases' shows all registered aliases."""
        # Arrange
        cli_app.register_alias("alias1", "test cmd1")
        cli_app.register_alias("alias2", "cmd2")

        # Act
        cli_app._execute_command("help aliases")

        # Assert
        captured = capsys.readouterr()
        assert "Available aliases:" in captured.out
        assert "alias1" in captured.out
        assert "alias2" in captured.out

    def test_help_unknown_group_shows_error(self, cli_app, capsys):
        """Test 'help <unknown_group>' shows error message."""
        # Arrange - no handlers

        # Act
        cli_app._execute_command("help unknown_group")

        # Assert
        captured = capsys.readouterr()
        assert "Unknown command: unknown_group" in captured.out


# =============================================================================
# TEST CASES: MULTIPLE HANDLERS
# =============================================================================


class TestMultipleHandlers:
    """Test behavior with multiple handlers for same group."""

    def test_multiple_handlers_first_valid_executes(self, cli_app):
        """Test first valid handler executes when multiple handlers registered."""
        # Arrange
        handler1 = Mock(spec=BaseCommand)
        handler1.validate_command.return_value = False
        handler1.get_available_commands.return_value = ["cmd1"]

        handler2 = Mock(spec=BaseCommand)
        handler2.validate_command.return_value = True
        handler2.get_available_commands.return_value = ["cmd2"]

        cli_app.register_command_group("test", handler1)
        cli_app.register_command_group("test", handler2)

        # Act
        cli_app._execute_command("test cmd2")

        # Assert
        handler1.execute.assert_not_called()
        handler2.execute.assert_called_once()

    def test_multiple_handlers_exception_in_first_stops_chain(self, cli_app, capsys):
        """Test exception in first handler stops execution chain."""
        # Arrange
        handler1 = Mock(spec=BaseCommand)
        handler1.validate_command.return_value = True
        handler1.execute.side_effect = Exception("Handler 1 failed")
        handler1.get_available_commands.return_value = ["cmd"]

        handler2 = Mock(spec=BaseCommand)
        handler2.validate_command.return_value = True
        handler2.get_available_commands.return_value = ["cmd"]

        cli_app.register_command_group("test", handler1)
        cli_app.register_command_group("test", handler2)

        # Act
        cli_app._execute_command("test cmd")

        # Assert
        captured = capsys.readouterr()
        assert "Error: Handler 1 failed" in captured.out
        handler1.execute.assert_called_once()
        handler2.execute.assert_not_called()


# =============================================================================
# TEST CASES: EDGE CASES
# =============================================================================


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_command_with_many_arguments(
        self, cli_app, mock_command_handler
    ):
        """Test command with many arguments passes all to handler."""
        # Arrange
        cli_app.register_command_group("test", mock_command_handler)

        # Act
        cli_app._execute_command("test test_cmd arg1 arg2 arg3 arg4 arg5")

        # Assert
        # CURRENT behavior: group name is passed as command, part2+args as arguments
        mock_command_handler.execute.assert_called_once_with(
            "test", ["test_cmd", "arg1", "arg2", "arg3", "arg4", "arg5"]
        )

    def test_command_with_no_arguments(
        self, cli_app, mock_command_handler
    ):
        """Test command with no arguments passes empty list."""
        # Arrange
        cli_app.register_command_group("test", mock_command_handler)

        # Act
        cli_app._execute_command("test test_cmd")

        # Assert
        # CURRENT behavior: group name is passed as command, part2 as first argument
        mock_command_handler.execute.assert_called_once_with("test", ["test_cmd"])

    def test_root_command_with_arguments(
        self, cli_app, mock_command_handler
    ):
        """Test root-level command with arguments."""
        # Arrange
        cli_app.register_command_group("", mock_command_handler)

        # Act
        cli_app._execute_command("test_cmd arg1 arg2")

        # Assert
        mock_command_handler.execute.assert_called_once_with("test_cmd", ["arg1", "arg2"])

    def test_empty_group_name_handlers(self, cli_app, mock_command_handler):
        """Test handlers registered with empty group name work as root."""
        # Arrange
        cli_app.register_command_group("", mock_command_handler)

        # Act
        cli_app._execute_command("test_cmd")

        # Assert
        mock_command_handler.execute.assert_called_once()

    def test_exception_message_with_special_characters(
        self, cli_app, failing_command_handler, capsys
    ):
        """Test exception message with special characters is displayed correctly."""
        # Arrange
        failing_command_handler.execute.side_effect = Exception(
            "Error: Invalid format <test@example.com>"
        )
        cli_app.register_command_group("test", failing_command_handler)

        # Act
        cli_app._execute_command("test failing_cmd")

        # Assert
        captured = capsys.readouterr()
        assert "Error: Invalid format <test@example.com>" in captured.out


# =============================================================================
# TEST CASES: CLEANUP AND LIFECYCLE
# =============================================================================


class TestLifecycle:
    """Test application lifecycle and cleanup."""

    def test_cleanup_calls_completion_cleanup_when_enabled(self):
        """Test cleanup() calls completion handler cleanup when enabled."""
        # Arrange
        with patch("basefunctions.cli.cli_application.basefunctions.cli.CompletionHandler") as mock_completion:
            mock_handler = Mock()
            mock_completion.return_value = mock_handler
            cli_app = CLIApplication("TestCLI", "1.0", enable_completion=True)

            # Act
            cli_app._cleanup()

            # Assert
            mock_handler.cleanup.assert_called_once()

    def test_cleanup_without_completion_does_not_fail(self):
        """Test cleanup() works when completion is disabled."""
        # Arrange
        with patch("basefunctions.cli.cli_application.basefunctions.cli.CompletionHandler"):
            cli_app = CLIApplication("TestCLI", "1.0", enable_completion=False)

            # Act - should not raise
            cli_app._cleanup()

            # Assert - no exceptions raised

    def test_show_welcome_displays_app_info(self, cli_app, capsys):
        """Test welcome message displays app name and version."""
        # Arrange - nothing

        # Act
        cli_app._show_welcome()

        # Assert
        captured = capsys.readouterr()
        assert "TestCLI v1.0" in captured.out
        assert "Type 'help' for commands" in captured.out
