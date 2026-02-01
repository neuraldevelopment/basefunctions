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
 v1.1.0 : Add tests for column_specs, max_width, row_separators parameters
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


def test_format_command_list_accepts_column_specs_parameter(sample_command_metadata: CommandMetadata) -> None:
    """Test format_command_list accepts column_specs parameter and passes to render_table."""
    # ARRANGE
    commands = {"test_cmd": sample_command_metadata}
    column_specs = ["left:20", "left:50"]

    # ACT
    result = HelpFormatter.format_command_list(commands, column_specs=column_specs)

    # ASSERT
    # Table should render with specified column widths
    assert "│" in result or "|" in result
    assert "test_cmd" in result


def test_format_command_list_accepts_max_width_parameter(sample_command_metadata: CommandMetadata) -> None:
    """Test format_command_list accepts max_width parameter and passes to render_table."""
    # ARRANGE
    commands = {"test_cmd": sample_command_metadata}
    max_width = 50

    # ACT
    result = HelpFormatter.format_command_list(commands, max_width=max_width)

    # ASSERT
    # Table should render with max_width constraint
    assert "│" in result or "|" in result
    assert "test_cmd" in result


def test_format_command_list_accepts_row_separators_parameter(sample_command_metadata: CommandMetadata) -> None:
    """Test format_command_list accepts row_separators parameter and passes to render_table."""
    # ARRANGE
    commands = {"test_cmd": sample_command_metadata, "other_cmd": sample_command_metadata}

    # ACT
    # Call with row_separators parameter (functionality is tested in table_renderer tests)
    result = HelpFormatter.format_command_list(commands, row_separators=False)

    # ASSERT
    # Should render as valid table with row_separators parameter accepted
    assert "│" in result or "|" in result
    assert "test_cmd" in result


def test_format_command_list_with_return_widths_returns_tuple(sample_command_metadata: CommandMetadata) -> None:
    """Test format_command_list with return_widths=True returns tuple of (table_str, widths_dict)."""
    # ARRANGE
    commands = {"test_cmd": sample_command_metadata}

    # ACT
    result = HelpFormatter.format_command_list(commands, return_widths=True)

    # ASSERT
    # Should return tuple (str, dict)
    assert isinstance(result, tuple)
    assert len(result) == 2
    table_str, widths_dict = result
    assert isinstance(table_str, str)
    assert isinstance(widths_dict, dict)
    # Dict should contain column_widths and total_width
    assert "column_widths" in widths_dict
    assert "total_width" in widths_dict
    assert isinstance(widths_dict["column_widths"], list)
    assert isinstance(widths_dict["total_width"], int)
    # Table string should still be valid
    assert "│" in table_str or "|" in table_str
    assert "test_cmd" in table_str


def test_format_command_list_with_enforce_widths_uses_specified_widths(sample_command_metadata: CommandMetadata) -> None:
    """Test format_command_list with enforce_widths uses provided column widths."""
    # ARRANGE
    commands = {"test_cmd": sample_command_metadata}
    # Get widths from first table
    _, widths_dict = HelpFormatter.format_command_list(commands, return_widths=True)

    # ACT
    # Create second table with enforced widths
    result = HelpFormatter.format_command_list(commands, enforce_widths=widths_dict)

    # ASSERT
    # Should render as valid table
    assert isinstance(result, str)
    assert "│" in result or "|" in result
    assert "test_cmd" in result


def test_format_command_list_two_tables_synchronized_widths(sample_command_metadata: CommandMetadata) -> None:
    """Test that two tables created with width sync have identical column widths."""
    # ARRANGE
    commands1 = {"test_cmd": sample_command_metadata}
    commands2 = {
        "help": CommandMetadata(
            name="help",
            description="Show help",
            usage="help"
        ),
        "quit": CommandMetadata(
            name="quit",
            description="Exit",
            usage="quit"
        )
    }

    # ACT
    # Create first table with return_widths
    table1_str, widths_dict = HelpFormatter.format_command_list(commands1, return_widths=True)
    # Create second table with enforced widths from first table
    table2_str = HelpFormatter.format_command_list(commands2, enforce_widths=widths_dict)

    # ASSERT
    # Both tables should have identical column widths
    # Check that both tables are valid
    assert "│" in table1_str or "|" in table1_str
    assert "│" in table2_str or "|" in table2_str

    # Extract border lines to verify identical widths
    table1_lines = table1_str.split("\n")
    table2_lines = table2_str.split("\n")

    # Top border should have same length
    table1_top = table1_lines[0]
    table2_top = table2_lines[0]
    assert len(table1_top) == len(table2_top), "Top borders should have identical width"
