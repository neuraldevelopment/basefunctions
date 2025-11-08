"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.

 Description:
 Pytest test suite for CompletionHandler.
 Tests tab completion with security considerations.

 Log:
 v1.0.0 : Initial test implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
# External imports
import pytest
from unittest.mock import Mock, patch

# Project imports
from basefunctions.cli import CompletionHandler, CommandRegistry, ContextManager

# -------------------------------------------------------------
# FIXTURES
# -------------------------------------------------------------


@pytest.fixture
def completion_handler(mock_command_registry: CommandRegistry, mock_context_manager: ContextManager) -> CompletionHandler:
    """Provide CompletionHandler instance."""
    return CompletionHandler(mock_command_registry, mock_context_manager)


# -------------------------------------------------------------
# TESTS: Completion - CRITICAL
# -------------------------------------------------------------


def test_complete_returns_none_when_readline_unavailable(completion_handler: CompletionHandler) -> None:  # CRITICAL TEST
    """Test complete handles missing readline gracefully."""
    # ARRANGE
    with patch('basefunctions.cli.completion_handler.readline', None):
        # ACT
        result = completion_handler.complete("test", 0)

        # ASSERT
        assert result is None


def test_complete_returns_none_on_exception(completion_handler: CompletionHandler) -> None:  # CRITICAL TEST
    """Test complete handles exceptions gracefully."""
    # ARRANGE
    with patch('basefunctions.cli.completion_handler.readline') as mock_rl:
        mock_rl.get_line_buffer.side_effect = Exception("Test error")

        # ACT
        result = completion_handler.complete("test", 0)

        # ASSERT
        assert result is None


def test_complete_command_groups_includes_special_commands(completion_handler: CompletionHandler) -> None:
    """Test _complete_command_groups includes help, quit, exit."""
    # ACT
    matches = completion_handler._complete_command_groups("")

    # ASSERT
    assert "help" in matches
    assert "quit" in matches
    assert "exit" in matches


def test_setup_handles_missing_history_file_gracefully(completion_handler: CompletionHandler) -> None:  # CRITICAL TEST
    """Test setup handles missing history file."""
    # ARRANGE
    with patch('basefunctions.cli.completion_handler.readline') as mock_rl:
        mock_rl.read_history_file.side_effect = FileNotFoundError()

        # ACT & ASSERT - Should not raise
        completion_handler.setup()


def test_cleanup_handles_write_exception_gracefully(completion_handler: CompletionHandler) -> None:  # CRITICAL TEST
    """Test cleanup handles write errors gracefully."""
    # ARRANGE
    with patch('basefunctions.cli.completion_handler.readline') as mock_rl:
        mock_rl.write_history_file.side_effect = Exception("Write error")

        # ACT & ASSERT - Should not raise
        completion_handler.cleanup()
