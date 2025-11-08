"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.

 Description:
 Pytest test suite for BaseCommand.
 Tests abstract command base class functionality.

 Log:
 v1.0.0 : Initial test implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
# External imports
import pytest
from unittest.mock import patch

# Project imports
from basefunctions.cli import BaseCommand

# -------------------------------------------------------------
# TESTS
# -------------------------------------------------------------


def test_get_available_commands_returns_list(concrete_base_command: BaseCommand) -> None:
    """Test get_available_commands returns command names."""
    # ACT
    commands = concrete_base_command.get_available_commands()

    # ASSERT
    assert "test" in commands
    assert "other" in commands


def test_validate_command_returns_true_when_exists(concrete_base_command: BaseCommand) -> None:
    """Test validate_command returns True for existing command."""
    # ACT
    result = concrete_base_command.validate_command("test")

    # ASSERT
    assert result is True


def test_validate_command_returns_false_when_not_exists(concrete_base_command: BaseCommand) -> None:
    """Test validate_command returns False for non-existent command."""
    # ACT
    result = concrete_base_command.validate_command("nonexistent")

    # ASSERT
    assert result is False


def test_confirm_action_returns_true_when_yes(concrete_base_command: BaseCommand) -> None:
    """Test _confirm_action returns True when user inputs 'y'."""
    # ARRANGE
    with patch('builtins.input', return_value='y'):
        # ACT
        result = concrete_base_command._confirm_action("Confirm?")

        # ASSERT
        assert result is True


def test_confirm_action_returns_false_when_no(concrete_base_command: BaseCommand) -> None:
    """Test _confirm_action returns False when user inputs 'n'."""
    # ARRANGE
    with patch('builtins.input', return_value='n'):
        # ACT
        result = concrete_base_command._confirm_action("Confirm?")

        # ASSERT
        assert result is False


def test_confirm_action_handles_keyboard_interrupt(concrete_base_command: BaseCommand) -> None:  # CRITICAL TEST
    """Test _confirm_action handles KeyboardInterrupt gracefully."""
    # ARRANGE
    with patch('builtins.input', side_effect=KeyboardInterrupt()):
        # ACT
        result = concrete_base_command._confirm_action("Confirm?")

        # ASSERT
        assert result is False
