"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Tests for multiline input functionality with completion callbacks
 Log:
 v1.0.0 : Initial implementation
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================

from unittest.mock import patch

from basefunctions.cli.multiline_input import read_multiline_input

# =============================================================================
# TEST FUNCTIONS
# =============================================================================


@patch("builtins.input")
def test_single_line_completion(mock_input):
    """Test that input completes on first line when is_complete returns True."""
    # Arrange
    mock_input.return_value = "SELECT * FROM users;"

    # Act
    result = read_multiline_input(
        prompt="SQL> ",
        continuation_prompt="...> ",
        is_complete=lambda b: ";" in b,
    )

    # Assert
    assert result == "SELECT * FROM users;"
    assert mock_input.call_count == 1


@patch("builtins.input")
def test_multiline_accumulation(mock_input):
    """Test that multiple lines are accumulated with newlines preserved."""
    # Arrange
    mock_input.side_effect = ["SELECT", "  *", "FROM foo;"]

    # Act
    result = read_multiline_input(
        prompt="SQL> ",
        continuation_prompt="...> ",
        is_complete=lambda b: ";" in b,
    )

    # Assert
    assert result == "SELECT\n  *\nFROM foo;"
    assert mock_input.call_count == 3


@patch("builtins.input")
def test_prompt_switching(mock_input):
    """Test that prompt switches from initial to continuation prompt."""
    # Arrange
    mock_input.side_effect = ["SELECT", "FROM foo;"]

    # Act
    result = read_multiline_input(
        prompt="SQL> ",
        continuation_prompt="...> ",
        is_complete=lambda b: ";" in b,
    )

    # Assert
    assert result == "SELECT\nFROM foo;"
    # Verify first call used initial prompt, second used continuation
    assert mock_input.call_args_list[0][0][0] == "SQL> "
    assert mock_input.call_args_list[1][0][0] == "...> "


@patch("builtins.input")
def test_eof_handling(mock_input):
    """Test that EOFError returns empty string."""
    # Arrange
    mock_input.side_effect = EOFError()

    # Act
    result = read_multiline_input(
        prompt="SQL> ",
        continuation_prompt="...> ",
        is_complete=lambda b: ";" in b,
    )

    # Assert
    assert result == ""


@patch("builtins.input")
def test_keyboard_interrupt_handling(mock_input):
    """Test that KeyboardInterrupt returns empty string."""
    # Arrange
    mock_input.side_effect = KeyboardInterrupt()

    # Act
    result = read_multiline_input(
        prompt="SQL> ",
        continuation_prompt="...> ",
        is_complete=lambda b: ";" in b,
    )

    # Assert
    assert result == ""


@patch("builtins.input")
def test_empty_lines_preserved(mock_input):
    """Test that empty lines are preserved in the buffer."""
    # Arrange
    mock_input.side_effect = ["SELECT", "", "FROM foo;"]

    # Act
    result = read_multiline_input(
        prompt="SQL> ",
        continuation_prompt="...> ",
        is_complete=lambda b: ";" in b,
    )

    # Assert
    assert result == "SELECT\n\nFROM foo;"
    assert mock_input.call_count == 3


@patch("builtins.input")
def test_whitespace_preservation(mock_input):
    """Test that whitespace within lines is preserved, only final buffer is stripped."""
    # Arrange
    mock_input.side_effect = ["  SELECT  ", "    *  ", "FROM foo;"]

    # Act
    result = read_multiline_input(
        prompt="SQL> ",
        continuation_prompt="...> ",
        is_complete=lambda b: ";" in b,
    )

    # Assert
    # Whitespace within lines is preserved, only leading/trailing whitespace of final buffer removed
    assert result == "SELECT  \n    *  \nFROM foo;"
    assert mock_input.call_count == 3


@patch("builtins.input")
def test_completion_callback_receives_accumulated_buffer(mock_input):
    """Test that is_complete receives the accumulated buffer after each line."""
    # Arrange
    mock_input.side_effect = ["SELECT", "FROM", "users;"]
    buffers_received = []

    def track_is_complete(buffer: str) -> bool:
        buffers_received.append(buffer)
        return ";" in buffer

    # Act
    result = read_multiline_input(
        prompt="SQL> ",
        continuation_prompt="...> ",
        is_complete=track_is_complete,
    )

    # Assert
    assert result == "SELECT\nFROM\nusers;"
    assert buffers_received == ["SELECT\n", "SELECT\nFROM\n", "SELECT\nFROM\nusers;\n"]
