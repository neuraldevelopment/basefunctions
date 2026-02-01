"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Tests for demos/demo_cli.py - Interactive REPL demo CLI testing.

 Coverage:
 - DemoCommands.register_commands() - 5 commands (help, list, list-rec, quit, exit)
 - DemoCommands.execute() - all commands + error handling
 - DemoCommands._execute_help() - output verification including quit
 - DemoCommands._execute_list() - recursive and non-recursive modes
 - main() - REPL loop (welcome, input, commands, quit, errors, interrupts)

 Log:
 v2.1.0 : Add mocks for create_file_list and directory parameter tests
 v2.0.0 : Updated for REPL-based CLI (input() instead of sys.argv)
 v1.0.0 : Initial implementation
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
# Standard Library
from pathlib import Path
from unittest.mock import patch, MagicMock
import importlib.util

# Third-party
import pytest

# Project modules
from basefunctions.cli import ContextManager

# Load demo_cli module from file path
demo_cli_path = Path(__file__).parent.parent.parent / "demos" / "demo_cli.py"
spec = importlib.util.spec_from_file_location("demo_cli", demo_cli_path)
if spec is None or spec.loader is None:
    raise ImportError(f"Failed to load demo_cli from {demo_cli_path}")
demo_cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(demo_cli)

DemoCommands = demo_cli.DemoCommands
main = demo_cli.main

# Register demo_cli in sys.modules for patching
import sys
sys.modules['demo_cli'] = demo_cli


# =============================================================================
# FIXTURES
# =============================================================================
@pytest.fixture
def cli_context():
    """Provide CLI context for testing."""
    return ContextManager(app_name="test-demo")


@pytest.fixture
def demo_commands(cli_context):
    """Provide DemoCommands instance for testing."""
    return DemoCommands(cli_context)


# =============================================================================
# TEST: register_commands
# =============================================================================
def test_register_commands_returns_only_list_commands(demo_commands):
    """Test register_commands returns only list commands (no help, quit, exit)."""
    # Arrange & Act
    commands = demo_commands.register_commands()

    # Assert
    assert len(commands) == 2
    assert "list" in commands
    assert "list-rec" in commands
    assert "help" not in commands
    assert "quit" not in commands
    assert "exit" not in commands


def test_register_commands_has_correct_metadata(demo_commands):
    """Test register_commands returns correct metadata for list commands only."""
    # Arrange & Act
    commands = demo_commands.register_commands()

    # Assert - list command
    assert commands["list"].name == "list"
    assert "non-recursive" in commands["list"].description.lower()
    assert commands["list"].usage == "list [directory]"

    # Assert - list-rec command
    assert commands["list-rec"].name == "list-rec"
    assert "recursive" in commands["list-rec"].description.lower()
    assert commands["list-rec"].usage == "list-rec [directory]"


# =============================================================================
# TEST: execute
# =============================================================================
def test_execute_help_command_succeeds(demo_commands, capsys):
    """Test execute with 'help' command prints help output with table format."""
    # Arrange & Act
    demo_commands.execute("help", [])
    captured = capsys.readouterr()

    # Assert - table output with command names (in blue ANSI codes)
    assert "Command" in captured.out  # Table header
    assert "Description" in captured.out  # Table header
    assert "help" in captured.out
    assert "list" in captured.out
    assert "list-rec" in captured.out


@patch('demo_cli.os.path.isdir')
@patch('demo_cli.create_file_list')
@patch('demo_cli.check_if_dir_exists')
def test_execute_list_command_succeeds(
    mock_check_dir, mock_create_file_list, mock_isdir, demo_commands, capsys
):
    """Test execute with 'list' command prints non-recursive listing."""
    # Arrange
    mock_check_dir.return_value = True
    mock_create_file_list.return_value = ['./demos/', './src/', './tests/']
    mock_isdir.return_value = True

    # Act
    demo_commands.execute("list", [])
    captured = capsys.readouterr()

    # Assert
    assert "Non-Recursive Directory Listing" in captured.out
    assert "./demos/ (DIR)" in captured.out
    assert "./src/ (DIR)" in captured.out
    assert "./tests/ (DIR)" in captured.out

    mock_create_file_list.assert_called_once_with(
        dir_name=".",
        recursive=False,
        append_dirs=True,
        add_hidden_files=False
    )


@patch('demo_cli.os.path.isdir')
@patch('demo_cli.create_file_list')
@patch('demo_cli.check_if_dir_exists')
def test_execute_list_rec_command_succeeds(
    mock_check_dir, mock_create_file_list, mock_isdir, demo_commands, capsys
):
    """Test execute with 'list-rec' command prints recursive listing."""
    # Arrange
    mock_check_dir.return_value = True
    mock_create_file_list.return_value = [
        './demos/',
        './demos/demo_cli.py',
        './src/basefunctions/'
    ]
    mock_isdir.side_effect = lambda x: x in ['./demos/', './src/basefunctions/']

    # Act
    demo_commands.execute("list-rec", [])
    captured = capsys.readouterr()

    # Assert
    assert "Recursive Directory Listing" in captured.out
    assert "./demos/ (DIR)" in captured.out
    assert "./demos/demo_cli.py (FILE)" in captured.out
    assert "./src/basefunctions/ (DIR)" in captured.out

    mock_create_file_list.assert_called_once_with(
        dir_name=".",
        recursive=True,
        append_dirs=True,
        add_hidden_files=False
    )


def test_execute_quit_command_returns_none(demo_commands):
    """Test execute with 'quit' command returns None."""
    # Arrange & Act
    result = demo_commands.execute("quit", [])

    # Assert
    assert result is None


def test_execute_exit_command_returns_none(demo_commands):
    """Test execute with 'exit' command returns None."""
    # Arrange & Act
    result = demo_commands.execute("exit", [])

    # Assert
    assert result is None


def test_execute_with_unknown_command_raises_value_error(demo_commands):
    """Test execute with unknown command raises ValueError."""
    # Arrange
    unknown_command = "unknown"

    # Act & Assert
    with pytest.raises(ValueError, match="Unknown command: unknown"):
        demo_commands.execute(unknown_command, [])


# =============================================================================
# TEST: _execute_help
# =============================================================================
def test_execute_help_displays_two_separate_tables(demo_commands, capsys):
    """Test _execute_help displays two tables: COMMANDS and GENERAL."""
    # Arrange & Act
    demo_commands._execute_help()
    captured = capsys.readouterr()

    # Assert - both table headers present
    assert "COMMANDS" in captured.out
    assert "GENERAL" in captured.out


def test_execute_help_commands_table_has_list_commands(demo_commands, capsys):
    """Test _execute_help COMMANDS table contains list commands."""
    # Arrange & Act
    demo_commands._execute_help()
    captured = capsys.readouterr()

    # Assert - COMMANDS table has list commands
    assert "list" in captured.out
    assert "list-rec" in captured.out
    assert "List items" in captured.out


def test_execute_help_general_table_has_help_and_quit(demo_commands, capsys):
    """Test _execute_help GENERAL table has help and quit/exit in one line."""
    # Arrange & Act
    demo_commands._execute_help()
    captured = capsys.readouterr()

    # Assert - GENERAL table has help and quit/exit
    assert "help" in captured.out
    assert "quit/exit" in captured.out or ("quit" in captured.out and "exit" in captured.out)


# =============================================================================
# TEST: _execute_list
# =============================================================================
@patch('demo_cli.os.path.isdir')
@patch('demo_cli.create_file_list')
@patch('demo_cli.check_if_dir_exists')
def test_execute_list_non_recursive_mode(
    mock_check_dir, mock_create_file_list, mock_isdir, demo_commands, capsys
):
    """Test _execute_list with recursive=False shows non-recursive listing."""
    # Arrange
    mock_check_dir.return_value = True
    mock_create_file_list.return_value = ['./demos/', './src/', './README.md']
    mock_isdir.side_effect = lambda x: x in ['./demos/', './src/']

    # Act
    demo_commands._execute_list(recursive=False, directory=".")
    captured = capsys.readouterr()

    # Assert
    assert "Non-Recursive Directory Listing: ." in captured.out
    assert "./demos/ (DIR)" in captured.out
    assert "./src/ (DIR)" in captured.out
    assert "./README.md (FILE)" in captured.out

    mock_check_dir.assert_called_once_with(".")
    mock_create_file_list.assert_called_once_with(
        dir_name=".",
        recursive=False,
        append_dirs=True,
        add_hidden_files=False
    )


@patch('demo_cli.os.path.isdir')
@patch('demo_cli.create_file_list')
@patch('demo_cli.check_if_dir_exists')
def test_execute_list_recursive_mode(
    mock_check_dir, mock_create_file_list, mock_isdir, demo_commands, capsys
):
    """Test _execute_list with recursive=True shows recursive listing."""
    # Arrange
    mock_check_dir.return_value = True
    mock_create_file_list.return_value = [
        './demos/',
        './demos/demo_cli.py',
        './src/basefunctions/',
        './src/basefunctions/cli/',
        './src/basefunctions/cli/base.py'
    ]
    mock_isdir.side_effect = lambda x: x in [
        './demos/', './src/basefunctions/', './src/basefunctions/cli/'
    ]

    # Act
    demo_commands._execute_list(recursive=True, directory=".")
    captured = capsys.readouterr()

    # Assert
    assert "Recursive Directory Listing: ." in captured.out
    assert "./demos/ (DIR)" in captured.out
    assert "./demos/demo_cli.py (FILE)" in captured.out
    assert "./src/basefunctions/ (DIR)" in captured.out
    assert "./src/basefunctions/cli/ (DIR)" in captured.out
    assert "./src/basefunctions/cli/base.py (FILE)" in captured.out

    mock_check_dir.assert_called_once_with(".")
    mock_create_file_list.assert_called_once_with(
        dir_name=".",
        recursive=True,
        append_dirs=True,
        add_hidden_files=False
    )


@patch('demo_cli.os.path.isdir')
@patch('demo_cli.create_file_list')
@patch('demo_cli.check_if_dir_exists')
def test_execute_list_with_custom_directory(
    mock_check_dir, mock_create_file_list, mock_isdir, demo_commands, capsys
):
    """Test _execute_list with custom directory parameter."""
    # Arrange
    mock_check_dir.return_value = True
    mock_create_file_list.return_value = ['demos/demo_cli.py']
    mock_isdir.return_value = False

    # Act
    demo_commands._execute_list(recursive=False, directory="demos")
    captured = capsys.readouterr()

    # Assert
    assert "Non-Recursive Directory Listing: demos" in captured.out
    assert "demos/demo_cli.py (FILE)" in captured.out

    mock_check_dir.assert_called_once_with("demos")
    mock_create_file_list.assert_called_once_with(
        dir_name="demos",
        recursive=False,
        append_dirs=True,
        add_hidden_files=False
    )


@patch('demo_cli.os.path.isdir')
@patch('demo_cli.create_file_list')
@patch('demo_cli.check_if_dir_exists')
def test_execute_list_with_parent_directory(
    mock_check_dir, mock_create_file_list, mock_isdir, demo_commands, capsys
):
    """Test _execute_list with parent directory (..) parameter."""
    # Arrange
    mock_check_dir.return_value = True
    mock_create_file_list.return_value = ['../basefunctions', '../tickerhub']
    mock_isdir.return_value = True

    # Act
    demo_commands._execute_list(recursive=False, directory="..")
    captured = capsys.readouterr()

    # Assert
    assert "Non-Recursive Directory Listing: .." in captured.out
    assert "../basefunctions (DIR)" in captured.out
    assert "../tickerhub (DIR)" in captured.out

    mock_check_dir.assert_called_once_with("..")
    mock_create_file_list.assert_called_once_with(
        dir_name="..",
        recursive=False,
        append_dirs=True,
        add_hidden_files=False
    )


@patch('demo_cli.check_if_dir_exists')
def test_execute_list_nonexistent_directory_raises_error(
    mock_check_dir, demo_commands
):
    """Test _execute_list raises ValueError for nonexistent directory."""
    # Arrange
    mock_check_dir.return_value = False

    # Act & Assert
    with pytest.raises(ValueError, match="Directory not found: /nonexistent"):
        demo_commands._execute_list(recursive=False, directory="/nonexistent")

    mock_check_dir.assert_called_once_with("/nonexistent")


@patch('demo_cli.create_file_list')
@patch('demo_cli.check_if_dir_exists')
def test_execute_list_empty_directory(
    mock_check_dir, mock_create_file_list, demo_commands, capsys
):
    """Test _execute_list handles empty directory correctly."""
    # Arrange
    mock_check_dir.return_value = True
    mock_create_file_list.return_value = []

    # Act
    demo_commands._execute_list(recursive=False, directory=".")
    captured = capsys.readouterr()

    # Assert
    assert "Non-Recursive Directory Listing: ." in captured.out
    assert "(empty)" in captured.out

    mock_check_dir.assert_called_once_with(".")
    mock_create_file_list.assert_called_once_with(
        dir_name=".",
        recursive=False,
        append_dirs=True,
        add_hidden_files=False
    )


# =============================================================================
# TEST: main - REPL Input/Output
# =============================================================================
def test_main_displays_welcome_message(capsys):
    """Test main displays welcome message on startup."""
    # Arrange & Act
    with patch('builtins.input', return_value='quit'):
        main()

    captured = capsys.readouterr()

    # Assert
    assert "Welcome to Demo CLI!" in captured.out
    assert "Type 'help' for available commands" in captured.out


def test_main_displays_goodbye_message_on_quit(capsys):
    """Test main displays goodbye message when user types 'quit'."""
    # Arrange & Act
    with patch('builtins.input', return_value='quit'):
        main()

    captured = capsys.readouterr()

    # Assert
    assert "Goodbye!" in captured.out


def test_main_displays_goodbye_message_on_exit(capsys):
    """Test main displays goodbye message when user types 'exit'."""
    # Arrange & Act
    with patch('builtins.input', return_value='exit'):
        main()

    captured = capsys.readouterr()

    # Assert
    assert "Goodbye!" in captured.out


def test_main_empty_input_continues_repl(capsys):
    """Test main skips empty input and continues REPL loop."""
    # Arrange - empty string then quit
    inputs = iter(['', '', 'quit'])

    # Act
    with patch('builtins.input', side_effect=inputs):
        main()

    captured = capsys.readouterr()

    # Assert - no error messages, clean exit
    assert "Goodbye!" in captured.out
    assert "Error:" not in captured.out


# =============================================================================
# TEST: main - REPL Commands
# =============================================================================
def test_main_repl_help_command(capsys):
    """Test main executes 'help' command via REPL input with table output."""
    # Arrange - help then quit
    inputs = iter(['help', 'quit'])

    # Act
    with patch('builtins.input', side_effect=inputs):
        main()

    captured = capsys.readouterr()

    # Assert - table output with help command
    assert "Command" in captured.out
    assert "Description" in captured.out
    assert "help" in captured.out
    assert "Goodbye!" in captured.out


@patch('demo_cli.os.path.isdir')
@patch('demo_cli.create_file_list')
@patch('demo_cli.check_if_dir_exists')
def test_main_repl_list_command(
    mock_check_dir, mock_create_file_list, mock_isdir, capsys
):
    """Test main executes 'list' command via REPL input."""
    # Arrange - list then quit
    inputs = iter(['list', 'quit'])
    mock_check_dir.return_value = True
    mock_create_file_list.return_value = ['./demos/', './src/']
    mock_isdir.return_value = True

    # Act
    with patch('builtins.input', side_effect=inputs):
        main()

    captured = capsys.readouterr()

    # Assert
    assert "Non-Recursive Directory Listing" in captured.out
    assert "Goodbye!" in captured.out
    mock_create_file_list.assert_called_once_with(
        dir_name=".",
        recursive=False,
        append_dirs=True,
        add_hidden_files=False
    )


@patch('demo_cli.os.path.isdir')
@patch('demo_cli.create_file_list')
@patch('demo_cli.check_if_dir_exists')
def test_main_repl_list_rec_command(
    mock_check_dir, mock_create_file_list, mock_isdir, capsys
):
    """Test main executes 'list-rec' command via REPL input."""
    # Arrange - list-rec then quit
    inputs = iter(['list-rec', 'quit'])
    mock_check_dir.return_value = True
    mock_create_file_list.return_value = ['./demos/', './demos/demo_cli.py']
    mock_isdir.side_effect = lambda x: x == './demos/'

    # Act
    with patch('builtins.input', side_effect=inputs):
        main()

    captured = capsys.readouterr()

    # Assert
    assert "Recursive Directory Listing" in captured.out
    assert "Goodbye!" in captured.out
    mock_create_file_list.assert_called_once_with(
        dir_name=".",
        recursive=True,
        append_dirs=True,
        add_hidden_files=False
    )


@patch('demo_cli.os.path.isdir')
@patch('demo_cli.create_file_list')
@patch('demo_cli.check_if_dir_exists')
def test_main_repl_multiple_commands_sequence(
    mock_check_dir, mock_create_file_list, mock_isdir, capsys
):
    """Test main executes multiple commands in sequence."""
    # Arrange - help, list, list-rec, quit
    inputs = iter(['help', 'list', 'list-rec', 'quit'])
    mock_check_dir.return_value = True
    mock_create_file_list.return_value = ['./file1.txt']
    mock_isdir.return_value = False

    # Act
    with patch('builtins.input', side_effect=inputs):
        main()

    captured = capsys.readouterr()

    # Assert - all commands executed
    assert "Command" in captured.out  # help table header
    assert "Non-Recursive Directory Listing" in captured.out
    assert "Recursive Directory Listing" in captured.out
    assert "Goodbye!" in captured.out


# =============================================================================
# TEST: main - REPL Error Handling
# =============================================================================
def test_main_repl_unknown_command_shows_error(capsys):
    """Test main shows error message for unknown command."""
    # Arrange - unknown command then quit
    inputs = iter(['unknown', 'quit'])

    # Act
    with patch('builtins.input', side_effect=inputs):
        main()

    captured = capsys.readouterr()

    # Assert
    assert "Error: Unknown command: unknown" in captured.out
    assert "Type 'help' for available commands" in captured.out
    assert "Goodbye!" in captured.out


def test_main_repl_handles_keyboard_interrupt(capsys):
    """Test main handles KeyboardInterrupt (Ctrl+C) gracefully."""
    # Arrange - simulate Ctrl+C
    with patch('builtins.input', side_effect=KeyboardInterrupt):
        # Act
        main()

    captured = capsys.readouterr()

    # Assert
    assert "Goodbye!" in captured.out


def test_main_repl_handles_eof_error(capsys):
    """Test main handles EOFError (Ctrl+D) gracefully."""
    # Arrange - simulate Ctrl+D
    with patch('builtins.input', side_effect=EOFError):
        # Act
        main()

    captured = capsys.readouterr()

    # Assert
    assert "Goodbye!" in captured.out
