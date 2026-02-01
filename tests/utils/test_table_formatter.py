"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Tests for get_table_format() function and multi-table width synchronization
 from table_renderer module
 Log:
 v1.6 : Add row_separators feature tests (control separator lines between data rows)
 v1.5 : Add multi-table width synchronization tests (return_widths/enforce_widths)
 v1.4 : Updated imports - get_table_format() moved from table_formatter to table_renderer
 v1.3 : Rewritten import pattern - module import FIRST, then patch ConfigHandler
 v1.2 : Fixed circular import with isolated module patch
 v1.1 : Fixed coverage 0% issue - import module before mocking
 v1.0 : Initial implementation
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
# Standard Library
from unittest.mock import MagicMock, patch


# =============================================================================
# TEST FUNCTIONS - get_table_format()
# =============================================================================
def test_get_table_format_returns_default_grid():
    """Test get_table_format() returns default 'grid' format."""
    # Arrange - Import module FIRST
    from basefunctions.utils.table_renderer import get_table_format

    # Then patch ConfigHandler where it's used (in table_renderer module)
    with patch("basefunctions.utils.table_renderer.ConfigHandler") as MockConfigHandler:
        mock_instance = MagicMock()
        mock_instance.get_config_parameter.return_value = "grid"
        MockConfigHandler.return_value = mock_instance

        # Act
        result = get_table_format()

        # Assert
        assert result == "grid"
        mock_instance.get_config_parameter.assert_called_once_with(
            "basefunctions/table_format", default_value="grid"
        )


def test_get_table_format_returns_custom_format_simple():
    """Test get_table_format() returns custom format 'simple' from config."""
    from basefunctions.utils.table_renderer import get_table_format

    with patch("basefunctions.utils.table_renderer.ConfigHandler") as MockConfigHandler:
        mock_instance = MagicMock()
        mock_instance.get_config_parameter.return_value = "simple"
        MockConfigHandler.return_value = mock_instance
        result = get_table_format()
        assert result == "simple"


def test_get_table_format_returns_custom_format_plain():
    """Test get_table_format() returns custom format 'plain' from config."""
    from basefunctions.utils.table_renderer import get_table_format

    with patch("basefunctions.utils.table_renderer.ConfigHandler") as MockConfigHandler:
        mock_instance = MagicMock()
        mock_instance.get_config_parameter.return_value = "plain"
        MockConfigHandler.return_value = mock_instance
        result = get_table_format()
        assert result == "plain"


def test_get_table_format_uses_correct_config_path():
    """Test get_table_format() uses correct config path 'basefunctions/table_format'."""
    from basefunctions.utils.table_renderer import get_table_format

    with patch("basefunctions.utils.table_renderer.ConfigHandler") as MockConfigHandler:
        mock_instance = MagicMock()
        mock_instance.get_config_parameter.return_value = "grid"
        MockConfigHandler.return_value = mock_instance
        get_table_format()
        call_args = mock_instance.get_config_parameter.call_args
        assert call_args[0][0] == "basefunctions/table_format"
        assert call_args[1]["default_value"] == "grid"


def test_get_table_format_returns_default_when_config_missing():
    """Test get_table_format() returns 'grid' when config entry missing (ConfigHandler default)."""
    from basefunctions.utils.table_renderer import get_table_format

    with patch("basefunctions.utils.table_renderer.ConfigHandler") as MockConfigHandler:
        mock_instance = MagicMock()
        mock_instance.get_config_parameter.return_value = "grid"
        MockConfigHandler.return_value = mock_instance
        result = get_table_format()
        assert result == "grid"


def test_get_table_format_returns_default_when_config_none():
    """Test get_table_format() returns 'grid' when config value is None (ConfigHandler default fallback)."""
    from basefunctions.utils.table_renderer import get_table_format

    with patch("basefunctions.utils.table_renderer.ConfigHandler") as MockConfigHandler:
        mock_instance = MagicMock()
        mock_instance.get_config_parameter.return_value = "grid"
        MockConfigHandler.return_value = mock_instance
        result = get_table_format()
        assert result == "grid"


def test_get_table_format_creates_config_handler_instance():
    """Test get_table_format() creates ConfigHandler instance."""
    from basefunctions.utils.table_renderer import get_table_format

    with patch("basefunctions.utils.table_renderer.ConfigHandler") as MockConfigHandler:
        mock_instance = MagicMock()
        mock_instance.get_config_parameter.return_value = "grid"
        MockConfigHandler.return_value = mock_instance
        get_table_format()
        MockConfigHandler.assert_called_once()


def test_get_table_format_supports_github_markdown_format():
    """Test get_table_format() returns 'github' format (GitHub Markdown tables)."""
    from basefunctions.utils.table_renderer import get_table_format

    with patch("basefunctions.utils.table_renderer.ConfigHandler") as MockConfigHandler:
        mock_instance = MagicMock()
        mock_instance.get_config_parameter.return_value = "github"
        MockConfigHandler.return_value = mock_instance
        result = get_table_format()
        assert result == "github"


def test_get_table_format_supports_fancy_grid_format():
    """Test get_table_format() returns 'fancy_grid' format (box-drawing characters)."""
    from basefunctions.utils.table_renderer import get_table_format

    with patch("basefunctions.utils.table_renderer.ConfigHandler") as MockConfigHandler:
        mock_instance = MagicMock()
        mock_instance.get_config_parameter.return_value = "fancy_grid"
        MockConfigHandler.return_value = mock_instance
        result = get_table_format()
        assert result == "fancy_grid"


def test_get_table_format_supports_pipe_format():
    """Test get_table_format() returns 'pipe' format (Markdown pipe tables)."""
    from basefunctions.utils.table_renderer import get_table_format

    with patch("basefunctions.utils.table_renderer.ConfigHandler") as MockConfigHandler:
        mock_instance = MagicMock()
        mock_instance.get_config_parameter.return_value = "pipe"
        MockConfigHandler.return_value = mock_instance
        result = get_table_format()
        assert result == "pipe"


def test_get_table_format_returns_string():
    """Test get_table_format() always returns string type."""
    from basefunctions.utils.table_renderer import get_table_format

    with patch("basefunctions.utils.table_renderer.ConfigHandler") as MockConfigHandler:
        mock_instance = MagicMock()
        mock_instance.get_config_parameter.return_value = "grid"
        MockConfigHandler.return_value = mock_instance
        result = get_table_format()
        assert isinstance(result, str)


# =============================================================================
# EDGE CASE TESTS
# =============================================================================
def test_get_table_format_with_empty_string_returns_empty():
    """Test get_table_format() returns empty string when config has empty string."""
    from basefunctions.utils.table_renderer import get_table_format

    with patch("basefunctions.utils.table_renderer.ConfigHandler") as MockConfigHandler:
        mock_instance = MagicMock()
        mock_instance.get_config_parameter.return_value = ""
        MockConfigHandler.return_value = mock_instance
        result = get_table_format()
        assert result == ""


def test_get_table_format_with_whitespace_string():
    """Test get_table_format() returns whitespace when config has whitespace string."""
    from basefunctions.utils.table_renderer import get_table_format

    with patch("basefunctions.utils.table_renderer.ConfigHandler") as MockConfigHandler:
        mock_instance = MagicMock()
        mock_instance.get_config_parameter.return_value = "   "
        MockConfigHandler.return_value = mock_instance
        result = get_table_format()
        assert result == "   "


def test_get_table_format_thread_safe_singleton():
    """Test get_table_format() works with ConfigHandler thread-safe singleton."""
    from basefunctions.utils.table_renderer import get_table_format

    with patch("basefunctions.utils.table_renderer.ConfigHandler") as MockConfigHandler:
        mock_instance = MagicMock()
        mock_instance.get_config_parameter.return_value = "grid"
        MockConfigHandler.return_value = mock_instance
        result1 = get_table_format()
        result2 = get_table_format()
        assert result1 == result2
        assert result1 == "grid"


# =============================================================================
# BACKWARD COMPATIBILITY TESTS
# =============================================================================
def test_get_table_format_backward_compatibility_grid_default():
    """Test get_table_format() maintains backward compatibility with 'grid' as default."""
    from basefunctions.utils.table_renderer import get_table_format

    with patch("basefunctions.utils.table_renderer.ConfigHandler") as MockConfigHandler:
        mock_instance = MagicMock()
        mock_instance.get_config_parameter.return_value = "grid"
        MockConfigHandler.return_value = mock_instance
        result = get_table_format()
        assert result == "grid"


# =============================================================================
# MULTI-TABLE WIDTH SYNCHRONIZATION TESTS
# =============================================================================
def test_render_table_with_return_widths_true():
    """Test render_table() with return_widths=True returns tuple (str, dict)."""
    # Arrange
    from basefunctions.utils.table_renderer import render_table

    with patch("basefunctions.utils.table_renderer.ConfigHandler") as MockConfigHandler:
        mock_instance = MagicMock()
        mock_instance.get_config_parameter.return_value = "grid"
        MockConfigHandler.return_value = mock_instance

        data = [["Alice", "24"], ["Bob", "19"]]
        headers = ["Name", "Age"]

        # Act
        result = render_table(data, headers=headers, return_widths=True)

        # Assert
        assert isinstance(result, tuple), "return_widths=True must return tuple"
        assert len(result) == 2, "Tuple must have 2 elements (str, dict)"

        table_str, widths_dict = result
        assert isinstance(table_str, str), "First element must be string"
        assert isinstance(widths_dict, dict), "Second element must be dict"

        # Assert dict structure
        assert "column_widths" in widths_dict, "Dict must have 'column_widths' key"
        assert "total_width" in widths_dict, "Dict must have 'total_width' key"

        # Assert column_widths is list
        assert isinstance(widths_dict["column_widths"], list), "column_widths must be list"

        # Assert total_width is int
        assert isinstance(widths_dict["total_width"], int), "total_width must be int"

        # Assert values are correct
        assert len(widths_dict["column_widths"]) == 2, "Must have 2 column widths"
        assert all(w > 0 for w in widths_dict["column_widths"]), "All widths must be positive"
        assert widths_dict["total_width"] > 0, "Total width must be positive"


def test_render_table_with_return_widths_false():
    """Test render_table() with return_widths=False (default) returns only string."""
    # Arrange
    from basefunctions.utils.table_renderer import render_table

    with patch("basefunctions.utils.table_renderer.ConfigHandler") as MockConfigHandler:
        mock_instance = MagicMock()
        mock_instance.get_config_parameter.return_value = "grid"
        MockConfigHandler.return_value = mock_instance

        data = [["Alice", "24"], ["Bob", "19"]]
        headers = ["Name", "Age"]

        # Act - explicitly False
        result_false = render_table(data, headers=headers, return_widths=False)

        # Act - default (no parameter)
        result_default = render_table(data, headers=headers)

        # Assert
        assert isinstance(result_false, str), "return_widths=False must return str, not tuple"
        assert not isinstance(result_false, tuple), "Must NOT be tuple"

        assert isinstance(result_default, str), "Default (no param) must return str"
        assert not isinstance(result_default, tuple), "Default must NOT be tuple"

        # Both should return same table
        assert result_false == result_default, "False and default should be identical"


def test_render_table_with_enforce_widths():
    """Test render_table() with enforce_widths synchronizes column widths across tables."""
    # Arrange
    from basefunctions.utils.table_renderer import render_table

    with patch("basefunctions.utils.table_renderer.ConfigHandler") as MockConfigHandler:
        mock_instance = MagicMock()
        mock_instance.get_config_parameter.return_value = "grid"
        MockConfigHandler.return_value = mock_instance

        # Table 1 - reference table
        data1 = [["Alice", "24"], ["Bob", "19"]]
        headers1 = ["Name", "Age"]

        # Table 2 - same columns, should get same widths
        data2 = [["Charlie", "30"], ["Diana", "25"]]
        headers2 = ["Name", "Age"]

        # Act
        # Render table 1 and extract widths
        table1, widths = render_table(data1, headers=headers1, return_widths=True)

        # Render table 2 with enforced widths
        table2 = render_table(data2, headers=headers2, enforce_widths=widths)

        # Assert
        # Table 2 should be string
        assert isinstance(table2, str), "enforce_widths should return string, not tuple"

        # Extract actual widths from both tables by parsing output
        # Both tables should have identical column widths
        # Split by newlines and check row length consistency
        lines1 = table1.split("\n")
        lines2 = table2.split("\n")

        # Top border lines should have identical length
        assert len(lines1[0]) == len(lines2[0]), "Tables must have identical total width"

        # Verify widths dict was respected
        assert "column_widths" in widths
        assert len(widths["column_widths"]) == 2


def test_enforce_widths_respects_exact_column_widths():
    """Test enforce_widths forces exact same column widths across multiple tables."""
    # Arrange
    from basefunctions.utils.table_renderer import render_table

    with patch("basefunctions.utils.table_renderer.ConfigHandler") as MockConfigHandler:
        mock_instance = MagicMock()
        mock_instance.get_config_parameter.return_value = "grid"
        MockConfigHandler.return_value = mock_instance

        # Table 1 - short data
        data1 = [["A", "1"]]
        headers1 = ["Name", "Value"]

        # Table 2 - longer data
        data2 = [["Very Long Name", "12345"]]
        headers2 = ["Name", "Value"]

        # Table 3 - medium data
        data3 = [["Medium", "999"]]
        headers3 = ["Name", "Value"]

        # Act
        # Render table 1 and extract widths
        table1, widths1 = render_table(data1, headers=headers1, return_widths=True)

        # All tables should use widths from table 1
        table2 = render_table(data2, headers=headers2, enforce_widths=widths1)
        table3 = render_table(data3, headers=headers3, enforce_widths=widths1)

        # Extract widths from table 2 with return_widths
        table2_check, widths2 = render_table(data2, headers=headers2, enforce_widths=widths1, return_widths=True)

        # Assert
        # All tables must have identical total width
        lines1 = table1.split("\n")
        lines2 = table2.split("\n")
        lines3 = table3.split("\n")

        assert len(lines1[0]) == len(lines2[0]) == len(lines3[0]), "All tables must have identical width"

        # Verify widths from table2_check match widths1
        assert widths2["column_widths"] == widths1["column_widths"], "enforce_widths must preserve exact widths"
        assert widths2["total_width"] == widths1["total_width"], "Total width must match"


def test_enforce_widths_with_different_data_lengths():
    """Test enforce_widths handles data longer than enforced width (truncation/padding)."""
    # Arrange
    from basefunctions.utils.table_renderer import render_table

    with patch("basefunctions.utils.table_renderer.ConfigHandler") as MockConfigHandler:
        mock_instance = MagicMock()
        mock_instance.get_config_parameter.return_value = "grid"
        MockConfigHandler.return_value = mock_instance

        # Table 1 - very short data, establishes narrow columns
        data1 = [["X", "Y"]]
        headers1 = ["A", "B"]

        # Table 2 - much longer data
        data2 = [["Very Long Text That Exceeds Width", "Another Long Value"]]
        headers2 = ["A", "B"]

        # Act
        # Get narrow widths from table 1
        table1, widths = render_table(data1, headers=headers1, return_widths=True)

        # Enforce those narrow widths on table 2 with longer text
        table2 = render_table(data2, headers=headers2, enforce_widths=widths)

        # Assert
        # Both tables must have same total width
        lines1 = table1.split("\n")
        lines2 = table2.split("\n")

        assert len(lines1[0]) == len(lines2[0]), "Tables must have identical width despite different data lengths"

        # Verify table 2 is valid (not empty, has content)
        assert len(table2) > 0, "Table 2 must be rendered"
        assert "│" in table2, "Table 2 must have borders"


def test_return_widths_with_ansi_codes():
    """Test return_widths correctly calculates widths ignoring ANSI color codes."""
    # Arrange
    from basefunctions.utils.table_renderer import render_table

    with patch("basefunctions.utils.table_renderer.ConfigHandler") as MockConfigHandler:
        mock_instance = MagicMock()
        mock_instance.get_config_parameter.return_value = "grid"
        MockConfigHandler.return_value = mock_instance

        # Data with ANSI codes
        red_text = "\033[31mRed\033[0m"  # "Red" in red, but visible width = 3
        green_text = "\033[32mGreen\033[0m"  # "Green" in green, visible width = 5

        data = [[red_text, green_text]]
        headers = ["Color1", "Color2"]

        # Act
        table, widths = render_table(data, headers=headers, return_widths=True)

        # Assert
        # Widths should be based on visible text, not including ANSI codes
        # "Color1" = 6 chars, "Red" = 3 chars -> width should be 6
        # "Color2" = 6 chars, "Green" = 5 chars -> width should be 6
        assert widths["column_widths"][0] >= 3, "First column must fit 'Red' (3 visible chars)"
        assert widths["column_widths"][1] >= 5, "Second column must fit 'Green' (5 visible chars)"

        # Verify headers are considered
        assert widths["column_widths"][0] >= 6, "First column must fit 'Color1' header"
        assert widths["column_widths"][1] >= 6, "Second column must fit 'Color2' header"

        # total_width should not count ANSI codes
        assert widths["total_width"] > 0
        assert isinstance(widths["total_width"], int)


def test_enforce_widths_invalid_input():
    """Test enforce_widths raises ValueError with invalid input."""
    # Arrange
    import pytest
    from basefunctions.utils.table_renderer import render_table

    with patch("basefunctions.utils.table_renderer.ConfigHandler") as MockConfigHandler:
        mock_instance = MagicMock()
        mock_instance.get_config_parameter.return_value = "grid"
        MockConfigHandler.return_value = mock_instance

        data = [["A", "B"]]
        headers = ["Col1", "Col2"]

        # Act & Assert - empty dict
        with pytest.raises(ValueError, match="column_widths"):
            render_table(data, headers=headers, enforce_widths={})

        # Act & Assert - missing column_widths key
        with pytest.raises(ValueError, match="column_widths"):
            render_table(data, headers=headers, enforce_widths={"total_width": 20})

        # Valid case - should not raise
        valid_widths = {"column_widths": [10, 10]}
        result = render_table(data, headers=headers, enforce_widths=valid_widths)
        assert isinstance(result, str)


def test_total_width_calculation():
    """Test total_width is correctly calculated and preserved across enforce_widths."""
    # Arrange
    from basefunctions.utils.table_renderer import render_table

    with patch("basefunctions.utils.table_renderer.ConfigHandler") as MockConfigHandler:
        mock_instance = MagicMock()
        mock_instance.get_config_parameter.return_value = "grid"
        MockConfigHandler.return_value = mock_instance

        data1 = [["Alice", "24"], ["Bob", "19"]]
        headers1 = ["Name", "Age"]

        data2 = [["Charlie", "30"]]
        headers2 = ["Name", "Age"]

        data3 = [["Diana", "25"], ["Eve", "22"], ["Frank", "28"]]
        headers3 = ["Name", "Age"]

        # Act
        # Get total_width from table 1
        table1, widths1 = render_table(data1, headers=headers1, return_widths=True)

        # Apply to tables 2 and 3
        table2, widths2 = render_table(data2, headers=headers2, enforce_widths=widths1, return_widths=True)
        table3, widths3 = render_table(data3, headers=headers3, enforce_widths=widths1, return_widths=True)

        # Assert
        # All total_widths must be identical
        assert widths1["total_width"] == widths2["total_width"], "Table 2 total_width must match table 1"
        assert widths1["total_width"] == widths3["total_width"], "Table 3 total_width must match table 1"

        # Verify actual rendered table widths match
        lines1 = table1.split("\n")
        lines2 = table2.split("\n")
        lines3 = table3.split("\n")

        assert len(lines1[0]) == widths1["total_width"], "Rendered width must match total_width"
        assert len(lines2[0]) == widths2["total_width"], "Rendered width must match total_width"
        assert len(lines3[0]) == widths3["total_width"], "Rendered width must match total_width"


# =============================================================================
# ROW_SEPARATORS TESTS
# =============================================================================
def test_render_table_without_row_separators():
    """Test render_table() with row_separators=False renders no separators between data rows."""
    # Arrange
    from basefunctions.utils.table_renderer import render_table

    with patch("basefunctions.utils.table_renderer.ConfigHandler") as MockConfigHandler:
        mock_instance = MagicMock()
        mock_instance.get_config_parameter.return_value = "fancy_grid"
        MockConfigHandler.return_value = mock_instance

        data = [["A", "1"], ["B", "2"], ["C", "3"]]
        headers = ["Col1", "Col2"]

        # Act
        result = render_table(data, headers=headers, row_separators=False)

        # Assert
        # Result must be a string
        assert isinstance(result, str), "Output must be string"

        # Split into lines
        lines = result.split("\n")

        # Must have at least 6 lines: top, header, header_sep, row1, row2, row3, bottom
        # Without row_separators: top, header, header_sep, row1, row2, row3, bottom = 7 lines
        assert len(lines) == 7, f"Expected 7 lines without row separators, got {len(lines)}"

        # Header separator MUST exist (fancy_grid uses ╞═══╪═══╡)
        header_sep_pattern = "╞"
        assert any(header_sep_pattern in line for line in lines), "Header separator must exist"

        # Row separators (├───┼───┤) MUST NOT exist between data rows
        row_sep_pattern = "├"
        row_sep_count = sum(1 for line in lines if row_sep_pattern in line)
        assert row_sep_count == 0, f"Expected 0 row separators, found {row_sep_count}"

        # Outer borders MUST exist
        assert "╒" in lines[0], "Top border must exist"
        assert "╘" in lines[-1], "Bottom border must exist"

        # Data rows must exist
        assert "│" in lines[3], "Row 1 must have vertical borders"
        assert "│" in lines[4], "Row 2 must have vertical borders"
        assert "│" in lines[5], "Row 3 must have vertical borders"


def test_render_table_with_row_separators_true():
    """Test render_table() with row_separators=True (default) renders separators between all data rows."""
    # Arrange
    from basefunctions.utils.table_renderer import render_table

    with patch("basefunctions.utils.table_renderer.ConfigHandler") as MockConfigHandler:
        mock_instance = MagicMock()
        mock_instance.get_config_parameter.return_value = "fancy_grid"
        MockConfigHandler.return_value = mock_instance

        data = [["A", "1"], ["B", "2"], ["C", "3"]]
        headers = ["Col1", "Col2"]

        # Act - explicit True
        result_true = render_table(data, headers=headers, row_separators=True)

        # Act - default (no parameter)
        result_default = render_table(data, headers=headers)

        # Assert
        # Both must be strings
        assert isinstance(result_true, str), "row_separators=True must return string"
        assert isinstance(result_default, str), "Default must return string"

        # Both must be identical
        assert result_true == result_default, "row_separators=True must equal default behavior"

        # Split into lines
        lines_true = result_true.split("\n")
        lines_default = result_default.split("\n")

        # With row_separators: top, header, header_sep, row1, sep1, row2, sep2, row3, bottom = 9 lines
        assert len(lines_true) == 9, f"Expected 9 lines with row separators, got {len(lines_true)}"
        assert len(lines_default) == 9, f"Expected 9 lines (default), got {len(lines_default)}"

        # Header separator MUST exist
        assert any("╞" in line for line in lines_true), "Header separator must exist"

        # Row separators (├───┼───┤) MUST exist between data rows
        row_sep_pattern = "├"
        row_sep_count = sum(1 for line in lines_true if row_sep_pattern in line)
        assert row_sep_count == 2, f"Expected 2 row separators, found {row_sep_count}"

        # Outer borders MUST exist
        assert "╒" in lines_true[0], "Top border must exist"
        assert "╘" in lines_true[-1], "Bottom border must exist"


def test_render_table_row_separators_with_enforce_widths():
    """Test row_separators=False works correctly with enforce_widths parameter."""
    # Arrange
    from basefunctions.utils.table_renderer import render_table

    with patch("basefunctions.utils.table_renderer.ConfigHandler") as MockConfigHandler:
        mock_instance = MagicMock()
        mock_instance.get_config_parameter.return_value = "fancy_grid"
        MockConfigHandler.return_value = mock_instance

        # Table 1 - reference table WITH row_separators
        data1 = [["Alice", "24"], ["Bob", "19"], ["Charlie", "30"]]
        headers1 = ["Name", "Age"]

        # Table 2 - same structure WITHOUT row_separators, using enforced widths
        data2 = [["Diana", "25"], ["Eve", "22"], ["Frank", "28"]]
        headers2 = ["Name", "Age"]

        # Act
        # Render table 1 WITH separators and extract widths
        table1, widths = render_table(data1, headers=headers1, row_separators=True, return_widths=True)

        # Render table 2 WITHOUT separators but WITH enforced widths from table 1
        table2 = render_table(data2, headers=headers2, row_separators=False, enforce_widths=widths)

        # Assert
        # Table 2 must be string
        assert isinstance(table2, str), "Result must be string"

        # Both tables must have same total width
        lines1 = table1.split("\n")
        lines2 = table2.split("\n")

        assert len(lines1[0]) == len(lines2[0]), "Both tables must have identical total width"

        # Table 1 has row separators (9 lines: top, header, header_sep, row1, sep, row2, sep, row3, bottom)
        assert len(lines1) == 9, f"Table 1 should have 9 lines with separators, got {len(lines1)}"

        # Table 2 has NO row separators (7 lines: top, header, header_sep, row1, row2, row3, bottom)
        assert len(lines2) == 7, f"Table 2 should have 7 lines without separators, got {len(lines2)}"

        # Verify no row separators in table 2
        row_sep_count = sum(1 for line in lines2 if "├" in line)
        assert row_sep_count == 0, f"Table 2 must have 0 row separators, found {row_sep_count}"

        # Verify widths were enforced (both tables have same column structure)
        assert "column_widths" in widths
        assert len(widths["column_widths"]) == 2


def test_render_table_row_separators_with_return_widths():
    """Test row_separators=False works correctly with return_widths=True parameter."""
    # Arrange
    from basefunctions.utils.table_renderer import render_table

    with patch("basefunctions.utils.table_renderer.ConfigHandler") as MockConfigHandler:
        mock_instance = MagicMock()
        mock_instance.get_config_parameter.return_value = "fancy_grid"
        MockConfigHandler.return_value = mock_instance

        data = [["Alice", "24"], ["Bob", "19"], ["Charlie", "30"]]
        headers = ["Name", "Age"]

        # Act
        # Render WITHOUT row_separators but WITH return_widths
        result = render_table(data, headers=headers, row_separators=False, return_widths=True)

        # Assert
        # Result must be tuple (str, dict)
        assert isinstance(result, tuple), "return_widths=True must return tuple"
        assert len(result) == 2, "Tuple must have 2 elements"

        table_str, widths_dict = result

        # First element must be string
        assert isinstance(table_str, str), "First element must be string"

        # Second element must be dict with correct structure
        assert isinstance(widths_dict, dict), "Second element must be dict"
        assert "column_widths" in widths_dict, "Dict must have 'column_widths' key"
        assert "total_width" in widths_dict, "Dict must have 'total_width' key"

        # Verify table has NO row separators
        lines = table_str.split("\n")
        assert len(lines) == 7, f"Expected 7 lines without separators, got {len(lines)}"

        row_sep_count = sum(1 for line in lines if "├" in line)
        assert row_sep_count == 0, f"Must have 0 row separators, found {row_sep_count}"

        # Verify widths dict values
        assert len(widths_dict["column_widths"]) == 2, "Must have 2 column widths"
        assert all(w > 0 for w in widths_dict["column_widths"]), "All widths must be positive"
        assert widths_dict["total_width"] > 0, "Total width must be positive"

        # Verify total_width matches rendered table width
        assert len(lines[0]) == widths_dict["total_width"], "Rendered width must match total_width"
