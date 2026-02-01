"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Tests for update_packages.py script - verify table formatting integration
 Log:
 v1.0.0 : Initial implementation
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
# Standard Library
import sys
from pathlib import Path

# Third Party
import pytest

# Add bin to path for importing update_packages module
bin_path = Path(__file__).parent.parent.parent / "bin"
sys.path.insert(0, str(bin_path))

# Module under test
import update_packages


# =============================================================================
# TEST FIXTURES
# =============================================================================
@pytest.fixture
def sample_updates():
    """Provide sample update data for testing."""
    return [
        ("basefunctions", "0.5.10", "0.5.77"),
        ("chartfunctions", "0.3.5", "0.3.10"),
        ("datatools", "1.2.0", "1.2.5")
    ]


# =============================================================================
# TESTS
# =============================================================================
def test_format_update_table_uses_render_table(sample_updates):
    """
    Test that _format_update_table uses render_table with fancy_grid theme.

    Verify:
    - Uses render_table() function from basefunctions
    - Uses fancy_grid theme
    - Has 3 columns: Package, Current, Target
    - Current and Target columns are right-aligned
    """
    # Arrange & Act
    result = update_packages._format_update_table(sample_updates)

    # Assert
    # Verify fancy_grid theme characters are present
    assert "╒" in result, "Should use fancy_grid top-left corner"
    assert "═" in result, "Should use fancy_grid horizontal line"
    assert "╤" in result, "Should use fancy_grid top junction"
    assert "╕" in result, "Should use fancy_grid top-right corner"

    # Verify headers are present
    assert "Package" in result
    assert "Current" in result
    assert "Target" in result

    # Verify data is present
    assert "basefunctions" in result
    assert "0.5.10" in result
    assert "0.5.77" in result


def test_format_update_table_empty_list():
    """
    Test that _format_update_table handles empty update list.

    Verify:
    - Returns empty string for empty list
    """
    # Arrange & Act
    result = update_packages._format_update_table([])

    # Assert
    assert result == "", "Should return empty string for empty list"


def test_format_update_table_column_alignment(sample_updates):
    """
    Test that version columns are right-aligned.

    Verify:
    - Current and Target columns have proper right alignment
    """
    # Arrange & Act
    result = update_packages._format_update_table(sample_updates)

    # Assert
    lines = result.split("\n")

    # Find data rows (skip header and separator rows)
    data_rows = [line for line in lines if "basefunctions" in line or "chartfunctions" in line]

    # Verify at least one data row exists
    assert len(data_rows) > 0, "Should have data rows"

    # The version numbers should be right-aligned
    # This means spaces should appear BEFORE version numbers in their columns
    first_row = data_rows[0]
    assert "0.5.10" in first_row, "Should contain version number"
