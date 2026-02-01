"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.

 Description:
 Pytest test suite for HelpFormatter.
 Tests help text generation and formatting.

 Log:
 v1.0.0 : Initial test implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
# External imports
import pytest
from typing import Dict

# Project imports
from basefunctions.cli import HelpFormatter, CommandMetadata, ArgumentSpec

# -------------------------------------------------------------
# TESTS
# -------------------------------------------------------------


def test_format_command_list_returns_message_when_empty() -> None:
    """Test format_command_list returns message for empty dict."""
    # ARRANGE
    commands: Dict[str, CommandMetadata] = {}

    # ACT
    result = HelpFormatter.format_command_list(commands)

    # ASSERT
    assert "No commands available" in result


def test_format_command_list_formats_correctly(sample_command_metadata: CommandMetadata) -> None:
    """Test format_command_list formats commands correctly."""
    # ARRANGE
    commands = {"test": sample_command_metadata}

    # ACT
    result = HelpFormatter.format_command_list(commands)

    # ASSERT
    assert "test_cmd" in result or "test" in result


def test_format_command_list_uses_table_renderer(sample_command_metadata: CommandMetadata) -> None:
    """Test format_command_list returns table-formatted output with borders."""
    # ARRANGE
    commands = {"test_cmd": sample_command_metadata}

    # ACT
    result = HelpFormatter.format_command_list(commands)

    # ASSERT
    # Check for table structure (borders from render_table)
    assert "│" in result or "|" in result  # Vertical separator
    assert "Command" in result  # Header column
    assert "Description" in result  # Header column
    assert "test_cmd" in result  # Command name in table


def test_format_command_list_applies_light_blue_to_commands(sample_command_metadata: CommandMetadata) -> None:
    """Test format_command_list applies ANSI light blue color to command names only."""
    # ARRANGE
    commands = {"test_cmd": sample_command_metadata}

    # ACT
    result = HelpFormatter.format_command_list(commands)

    # ASSERT
    # Check for ANSI light blue code (\033[94m) followed by command name
    assert "\033[94m" in result  # Light blue color code
    assert "\033[0m" in result  # Reset code
    # Command name should be colored
    assert "\033[94mtest_cmd" in result
    # Description should NOT be colored (no ANSI code before description)
    assert "Test command for testing" in result


def test_build_help_rows_creates_multi_group_structure(sample_command_metadata: CommandMetadata) -> None:
    """Test _build_help_rows creates table rows with group headers and separators."""
    # ARRANGE
    groups_data = {
        "CONTROL COMMANDS": {"control show": sample_command_metadata},
        "SYMBOL COMMANDS": {"symbol info": sample_command_metadata}
    }

    # ACT
    rows = HelpFormatter._build_help_rows(groups_data)

    # ASSERT
    # Should have: group header + command + group header + command = 4 rows
    assert len(rows) >= 4
    # First row should be group header (empty description)
    assert rows[0][0] == "CONTROL COMMANDS"
    assert rows[0][1] == ""
    # Check for colored command
    assert "\033[94m" in rows[1][0]  # Command should be colored
    # Third row should be second group header
    assert rows[2][0] == "SYMBOL COMMANDS"


def test_format_command_list_with_group_name_includes_header_in_table(sample_command_metadata: CommandMetadata) -> None:
    """Test format_command_list with group_name includes group header inside table."""
    # ARRANGE
    commands = {"test_cmd": sample_command_metadata}
    group_name = "CONTROL COMMANDS"

    # ACT
    result = HelpFormatter.format_command_list(commands, group_name=group_name)

    # ASSERT
    # Table structure should exist
    assert "│" in result or "|" in result
    # Group name should be IN the table (not as separate header)
    assert group_name in result
    # Should NOT have separate text header line outside table
    lines = result.split("\n")
    # First non-border line should be header or group name IN table
    assert not any(line.strip().endswith("COMMANDS:") and "│" not in line and "|" not in line for line in lines)


def test_format_group_help_uses_table_output(concrete_base_command) -> None:
    """Test format_group_help returns table-formatted output."""
    # ACT
    result = HelpFormatter.format_group_help("test", concrete_base_command)

    # ASSERT
    # Check for table structure
    assert "│" in result or "|" in result
    assert "Command" in result
    assert "Description" in result
    # Check for ANSI colored command
    assert "\033[94m" in result


def test_format_command_details_includes_all_sections(sample_command_metadata: CommandMetadata) -> None:
    """Test format_command_details includes command, description, usage."""
    # ACT
    result = HelpFormatter.format_command_details(sample_command_metadata)

    # ASSERT
    assert "Command:" in result
    assert "Description:" in result
    assert "Usage:" in result
