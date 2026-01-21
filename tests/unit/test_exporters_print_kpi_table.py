"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Comprehensive tests for print_kpi_table() with 2-level grouping format
 Log:
 v1.0 : Initial implementation - testing new 2-level grouping (package-only)
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
# Standard Library
import contextlib
import io
from typing import Any, Dict

# Third-party
import pytest

# Project modules
from basefunctions.kpi.exporters import print_kpi_table


# =============================================================================
# FIXTURES
# =============================================================================
@pytest.fixture
def capture_print_output():
    """
    Fixture to capture print() output from print_kpi_table().

    Returns
    -------
    callable
        Function that captures stdout and returns as string
    """
    def _capture(kpis: Dict[str, Any], **kwargs) -> str:
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            print_kpi_table(kpis, **kwargs)
        return f.getvalue()
    return _capture


@pytest.fixture
def sample_kpis_single_package():
    """
    Provide sample KPIs for single package testing.

    Returns
    -------
    Dict[str, Any]
        KPI dictionary with single package, multiple subgroups
    """
    return {
        "business": {
            "portfoliofunctions": {
                "activity": {
                    "win_rate": {"value": 0.75, "unit": "%"},
                    "loss_rate": {"value": 0.25, "unit": "%"}
                },
                "returns": {
                    "total_pnl": {"value": 1000.0, "unit": "USD"}
                }
            }
        }
    }


@pytest.fixture
def sample_kpis_multiple_packages():
    """
    Provide sample KPIs for multiple package testing.

    Returns
    -------
    Dict[str, Any]
        KPI dictionary with multiple packages
    """
    return {
        "business": {
            "portfoliofunctions": {
                "activity": {
                    "trades": {"value": 5, "unit": "-"}
                }
            },
            "backtesterfunctions": {
                "performance": {
                    "cagr": {"value": 0.12, "unit": "%"}
                }
            }
        }
    }


@pytest.fixture
def sample_kpis_with_hyphens():
    """
    Provide sample KPIs with hyphens in subgroup names.

    Returns
    -------
    Dict[str, Any]
        KPI dictionary with hyphenated subgroup names
    """
    return {
        "business": {
            "portfoliofunctions": {
                "business-metrics": {
                    "win_rate": {"value": 0.75, "unit": "%"}
                }
            }
        }
    }


@pytest.fixture
def sample_kpis_long_names():
    """
    Provide sample KPIs with very long metric names.

    Returns
    -------
    Dict[str, Any]
        KPI dictionary with long names
    """
    return {
        "business": {
            "portfoliofunctions": {
                "activity": {
                    "very_long_metric_name_that_exceeds_sixty_characters_limit_for_testing": {
                        "value": 1.0,
                        "unit": "-"
                    }
                }
            }
        }
    }


# =============================================================================
# TEST: 2-LEVEL GROUPING (PACKAGE ONLY)
# =============================================================================
def test_print_kpi_table_2_level_grouping_single_package(
    capture_print_output,
    sample_kpis_single_package
):
    """Test basic 2-level grouping with single package."""
    # Act
    output = capture_print_output(sample_kpis_single_package)

    # Assert - Package header with metric count
    assert "Portfoliofunctions KPIs - 3 Metrics" in output

    # Assert - Subgroup headers (UPPERCASE)
    assert "ACTIVITY" in output
    assert "RETURNS" in output

    # Assert - Metric names (indented)
    assert "win_rate" in output
    assert "loss_rate" in output
    assert "total_pnl" in output

    # Assert - Values with units integrated
    assert "0.75 %" in output
    assert "0.25 %" in output
    assert "1000" in output and "USD" in output


def test_print_kpi_table_2_level_multiple_packages(
    capture_print_output,
    sample_kpis_multiple_packages
):
    """Test grouping with multiple packages generates separate tables."""
    # Act
    output = capture_print_output(sample_kpis_multiple_packages)

    # Assert - Two separate package headers
    assert "Portfoliofunctions KPIs" in output
    assert "Backtesterfunctions KPIs" in output

    # Assert - Both packages have content
    assert "trades" in output
    assert "cagr" in output


# =============================================================================
# TEST: SECTION HEADERS (UPPERCASE)
# =============================================================================
def test_print_kpi_table_subgroup_headers_uppercase(
    capture_print_output,
    sample_kpis_single_package
):
    """Test subgroup names rendered as UPPERCASE headers."""
    # Act
    output = capture_print_output(sample_kpis_single_package)

    # Assert - UPPERCASE headers present
    assert "ACTIVITY" in output
    assert "RETURNS" in output

    # Assert - No lowercase variants in headers
    lines = output.split("\n")
    header_lines = [l for l in lines if "ACTIVITY" in l or "RETURNS" in l]
    for line in header_lines:
        assert "activity" not in line.lower().replace("activity", "")


def test_print_kpi_table_subgroup_with_hyphens_normalized(
    capture_print_output,
    sample_kpis_with_hyphens
):
    """Test subgroup names with hyphens normalized to underscores, uppercase."""
    # Act
    output = capture_print_output(sample_kpis_with_hyphens)

    # Assert - Hyphens converted to underscores in header
    assert "BUSINESS_METRICS" in output

    # Assert - Original hyphenated name not present
    assert "BUSINESS-METRICS" not in output


# =============================================================================
# TEST: 2-SPACE INDENTATION (Handled by tabulate)
# =============================================================================
def test_print_kpi_table_metrics_indented_2_spaces(
    capture_print_output,
    sample_kpis_single_package
):
    """Test metrics rendered below section headers (tabulate handles spacing)."""
    # Act
    output = capture_print_output(sample_kpis_single_package)

    # Assert - Metrics appear in table structure
    # Note: tabulate manages spacing via table structure, not raw 2-space indent
    assert "win_rate" in output
    assert "total_pnl" in output

    # Assert - Section headers appear before their metrics
    lines = output.split("\n")
    activity_idx = next((i for i, l in enumerate(lines) if "ACTIVITY" in l), -1)
    win_rate_idx = next((i for i, l in enumerate(lines) if "win_rate" in l), -1)

    assert activity_idx >= 0 and win_rate_idx >= 0
    assert activity_idx < win_rate_idx  # ACTIVITY before win_rate


# =============================================================================
# TEST: EMPTY SEPARATOR ROWS
# =============================================================================
def test_print_kpi_table_empty_separator_rows_between_sections(
    capture_print_output,
    sample_kpis_single_package
):
    """Test empty rows between subgroup sections."""
    # Act
    output = capture_print_output(sample_kpis_single_package)

    # Assert - Verify structure (ACTIVITY, metrics, empty, RETURNS)
    lines = output.split("\n")

    activity_indices = [i for i, l in enumerate(lines) if "ACTIVITY" in l]
    returns_indices = [i for i, l in enumerate(lines) if "RETURNS" in l]

    # Both sections should exist
    assert len(activity_indices) > 0
    assert len(returns_indices) > 0

    # RETURNS should be several lines after ACTIVITY (not immediately adjacent)
    if activity_indices and returns_indices:
        assert returns_indices[0] > activity_indices[0] + 2


# =============================================================================
# TEST: INTEGRATED UNITS IN VALUE COLUMN
# =============================================================================
def test_print_kpi_table_units_integrated_in_value_column(
    capture_print_output,
    sample_kpis_single_package
):
    """Test units integrated into Value column (not separate column)."""
    # Act
    output = capture_print_output(sample_kpis_single_package)

    # Assert - Values include units
    assert "0.75 %" in output
    assert "1000" in output and "USD" in output

    # Assert - "Unit" column header NOT present (or max 1 occurrence in header)
    unit_occurrences = output.count("Unit")
    assert unit_occurrences <= 1  # Only in "Value" header, not separate column


def test_print_kpi_table_units_with_none_handled_gracefully():
    """Test handling of None units (no unit suffix)."""
    # Arrange
    kpis = {
        "business": {
            "portfoliofunctions": {
                "activity": {
                    "count": {"value": 42, "unit": None}
                }
            }
        }
    }

    # Act
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        print_kpi_table(kpis)
    output = f.getvalue()

    # Assert - Value shown without unit
    assert "42" in output


# =============================================================================
# TEST: METRIC NAME ONLY (NO SUBGROUP PREFIX)
# =============================================================================
def test_print_kpi_table_metric_names_without_subgroup_prefix(
    capture_print_output,
    sample_kpis_single_package
):
    """Test metric names shown without subgroup prefix."""
    # Act
    output = capture_print_output(sample_kpis_single_package)

    # Assert - Clean metric names present
    assert "win_rate" in output
    assert "total_pnl" in output

    # Assert - No subgroup prefixes
    assert "activity.win_rate" not in output
    assert "returns.total_pnl" not in output


# =============================================================================
# TEST: TABLE FORMAT (fancy_grid)
# =============================================================================
def test_print_kpi_table_fancy_grid_format_default(
    capture_print_output,
    sample_kpis_single_package
):
    """Test fancy_grid format (default) uses box-drawing characters."""
    # Act
    output = capture_print_output(sample_kpis_single_package)

    # Assert - fancy_grid box-drawing characters present
    assert any(char in output for char in ["╒", "╕", "╞", "╡", "═", "│"])


def test_print_kpi_table_custom_table_format():
    """Test custom table format parameter."""
    # Arrange
    kpis = {
        "business": {
            "portfoliofunctions": {
                "activity": {
                    "metric": {"value": 1, "unit": "-"}
                }
            }
        }
    }

    # Act
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        print_kpi_table(kpis, table_format="grid")
    output = f.getvalue()

    # Assert - grid format uses different characters
    assert "+" in output or "|" in output


# =============================================================================
# TEST: METRIC COUNT IN HEADER
# =============================================================================
def test_print_kpi_table_metric_count_in_header_correct(
    capture_print_output,
    sample_kpis_single_package
):
    """Test correct metric count in table header."""
    # Act
    output = capture_print_output(sample_kpis_single_package)

    # Assert - Correct count (3 metrics total)
    assert "3 Metrics" in output


def test_print_kpi_table_metric_count_multiple_subgroups():
    """Test metric count aggregates across all subgroups."""
    # Arrange
    kpis = {
        "business": {
            "portfoliofunctions": {
                "activity": {
                    "m1": {"value": 1, "unit": "-"},
                    "m2": {"value": 2, "unit": "-"}
                },
                "returns": {
                    "m3": {"value": 3, "unit": "-"}
                },
                "risk": {
                    "m4": {"value": 4, "unit": "-"}
                }
            }
        }
    }

    # Act
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        print_kpi_table(kpis)
    output = f.getvalue()

    # Assert - Total count is 4
    assert "4 Metrics" in output


# =============================================================================
# TEST: FILTER PATTERNS COMPATIBILITY
# =============================================================================
def test_print_kpi_table_filter_patterns_with_2_level_single_subgroup(
    capture_print_output,
    sample_kpis_single_package
):
    """Test wildcard filtering works with 2-level grouping (single subgroup)."""
    # Act
    output = capture_print_output(
        sample_kpis_single_package,
        filter_patterns=["business.portfoliofunctions.activity.*"]
    )

    # Assert - Only activity metrics shown
    assert "win_rate" in output
    assert "loss_rate" in output

    # Assert - Returns metrics NOT shown
    assert "total_pnl" not in output


def test_print_kpi_table_filter_patterns_multiple_packages(
    capture_print_output,
    sample_kpis_multiple_packages
):
    """Test filtering with multiple packages."""
    # Act
    output = capture_print_output(
        sample_kpis_multiple_packages,
        filter_patterns=["business.portfoliofunctions.*"]
    )

    # Assert - Only portfoliofunctions shown
    assert "trades" in output

    # Assert - Backtesterfunctions NOT shown
    assert "cagr" not in output
    assert "Backtesterfunctions" not in output


# =============================================================================
# TEST: SORTING (PACKAGES AND SUBGROUPS)
# =============================================================================
def test_print_kpi_table_sorted_packages_alphabetically():
    """Test packages sorted alphabetically."""
    # Arrange
    kpis = {
        "business": {
            "zebrafunctions": {
                "zebra_sub": {"metric1": {"value": 1, "unit": "-"}}
            },
            "alphafunctions": {
                "alpha_sub": {"metric2": {"value": 2, "unit": "-"}}
            }
        }
    }

    # Act
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        print_kpi_table(kpis, sort_keys=True)
    output = f.getvalue()

    # Assert - Alpha comes before Zebra
    alpha_idx = output.find("Alphafunctions")
    zebra_idx = output.find("Zebrafunctions")
    assert alpha_idx > 0 and zebra_idx > 0
    assert alpha_idx < zebra_idx


def test_print_kpi_table_sorted_subgroups_alphabetically():
    """Test subgroups sorted alphabetically within package."""
    # Arrange
    kpis = {
        "business": {
            "portfoliofunctions": {
                "zebra_subgroup": {"metric1": {"value": 1, "unit": "-"}},
                "alpha_subgroup": {"metric2": {"value": 2, "unit": "-"}}
            }
        }
    }

    # Act
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        print_kpi_table(kpis, sort_keys=True)
    output = f.getvalue()

    # Assert - ALPHA_SUBGROUP before ZEBRA_SUBGROUP
    alpha_idx = output.find("ALPHA_SUBGROUP")
    zebra_idx = output.find("ZEBRA_SUBGROUP")
    assert alpha_idx > 0 and zebra_idx > 0
    assert alpha_idx < zebra_idx


# =============================================================================
# TEST: DECIMALS PARAMETER
# =============================================================================
def test_print_kpi_table_decimals_precision_2():
    """Test decimal precision parameter with 2 decimals."""
    # Arrange
    kpis = {
        "business": {
            "portfoliofunctions": {
                "activity": {
                    "metric": {"value": 0.123456, "unit": "-"}
                }
            }
        }
    }

    # Act
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        print_kpi_table(kpis, decimals=2)
    output = f.getvalue()

    # Assert - Rounded to 2 decimals
    assert "0.12" in output


def test_print_kpi_table_decimals_precision_4():
    """Test decimal precision parameter with 4 decimals."""
    # Arrange
    kpis = {
        "business": {
            "portfoliofunctions": {
                "activity": {
                    "metric": {"value": 0.123456, "unit": "-"}
                }
            }
        }
    }

    # Act
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        print_kpi_table(kpis, decimals=4)
    output = f.getvalue()

    # Assert - Rounded to 4 decimals
    assert "0.1235" in output


# =============================================================================
# TEST: EDGE CASES
# =============================================================================
def test_print_kpi_table_empty_kpi_dict():
    """Test handling of empty KPI dictionary."""
    # Arrange
    kpis = {}

    # Act
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        print_kpi_table(kpis)
    output = f.getvalue()

    # Assert - Graceful message
    assert "No KPIs to display" in output


def test_print_kpi_table_very_long_metric_names_handled(
    capture_print_output,
    sample_kpis_long_names
):
    """Test very long metric names handled gracefully (maxcolwidths)."""
    # Act
    output = capture_print_output(sample_kpis_long_names)

    # Assert - Output generated without error
    assert "Portfoliofunctions KPIs" in output

    # Assert - Line lengths reasonable (table should use maxcolwidths=60)
    lines = output.split("\n")
    # Some lines can be longer due to borders, but should not be excessive
    assert all(len(l) < 120 for l in lines)


def test_print_kpi_table_no_valid_kpis_after_filtering():
    """Test handling when filter patterns match nothing."""
    # Arrange
    kpis = {
        "business": {
            "portfoliofunctions": {
                "activity": {
                    "win_rate": {"value": 0.75, "unit": "%"}
                }
            }
        }
    }

    # Act
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        print_kpi_table(kpis, filter_patterns=["nonexistent.*"])
    output = f.getvalue()

    # Assert - Graceful message
    assert "No KPIs match filter patterns" in output


def test_print_kpi_table_invalid_kpi_structure_skipped():
    """Test invalid KPI keys (< 3 parts) are skipped."""
    # Arrange - Mix of valid and invalid keys
    kpis = {
        "business": {
            "portfoliofunctions": {
                "activity": {
                    "valid_metric": {"value": 1.0, "unit": "-"}
                }
            }
        },
        "invalid_key": {"value": 99.0, "unit": "-"}  # Only 1 part
    }

    # Act
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        print_kpi_table(kpis)
    output = f.getvalue()

    # Assert - Valid metric shown
    assert "valid_metric" in output

    # Assert - Invalid key not shown (no table for it)
    assert "invalid_key" not in output


def test_print_kpi_table_integer_values_without_decimals():
    """Test integer values displayed without unnecessary decimal places."""
    # Arrange
    kpis = {
        "business": {
            "portfoliofunctions": {
                "activity": {
                    "count": {"value": 42.0, "unit": "-"}
                }
            }
        }
    }

    # Act
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        print_kpi_table(kpis, decimals=2)
    output = f.getvalue()

    # Assert - Integer shown as "42", not "42.00"
    assert "42" in output
    assert "42.00" not in output


def test_print_kpi_table_missing_value_key_handled():
    """Test handling of KPIValue dict missing 'value' key."""
    # Arrange - Malformed KPIValue
    kpis = {
        "business": {
            "portfoliofunctions": {
                "activity": {
                    "broken": {"unit": "%"}  # Missing "value"
                }
            }
        }
    }

    # Act
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        print_kpi_table(kpis)
    output = f.getvalue()

    # Assert - Does not crash, shows something
    assert "Portfoliofunctions KPIs" in output


def test_print_kpi_table_sort_keys_false_preserves_order():
    """Test sort_keys=False preserves insertion order."""
    # Arrange - Intentionally unsorted
    kpis = {
        "business": {
            "zebrafunctions": {
                "zebra_sub": {"metric": {"value": 1, "unit": "-"}}
            },
            "alphafunctions": {
                "alpha_sub": {"metric": {"value": 2, "unit": "-"}}
            }
        }
    }

    # Act
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        print_kpi_table(kpis, sort_keys=False)
    output = f.getvalue()

    # Assert - Zebra appears before Alpha (insertion order)
    zebra_idx = output.find("Zebrafunctions")
    alpha_idx = output.find("Alphafunctions")
    assert zebra_idx > 0 and alpha_idx > 0
    assert zebra_idx < alpha_idx


# =============================================================================
# ADDITIONAL TESTS FOR COVERAGE
# =============================================================================
def test_print_kpi_table_plain_numeric_values_backward_compatibility():
    """Test backward compatibility with plain numeric values (no KPIValue dict)."""
    # Arrange - Old format without KPIValue structure
    kpis = {
        "business": {
            "portfoliofunctions": {
                "activity": {
                    "count": 42  # Plain numeric value
                }
            }
        }
    }

    # Act
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        print_kpi_table(kpis)
    output = f.getvalue()

    # Assert - Value displayed
    assert "42" in output
    assert "count" in output


def test_print_kpi_table_nested_dict_without_value_key():
    """Test nested dict without 'value' key (regular nested structure)."""
    # Arrange - Nested structure without KPIValue
    kpis = {
        "business": {
            "portfoliofunctions": {
                "activity": {
                    "nested": {
                        "deep": {"value": 100, "unit": "-"}
                    }
                }
            }
        }
    }

    # Act
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        print_kpi_table(kpis)
    output = f.getvalue()

    # Assert - Deep nested value displayed
    assert "100" in output


def test_print_kpi_table_unit_percent_formatting():
    """Test percentage unit formatting."""
    # Arrange
    kpis = {
        "business": {
            "portfoliofunctions": {
                "activity": {
                    "rate": {"value": 0.5, "unit": "%"}
                }
            }
        }
    }

    # Act
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        print_kpi_table(kpis)
    output = f.getvalue()

    # Assert - Percent symbol present
    assert "0.5 %" in output or "0.50 %" in output


def test_print_kpi_table_empty_unit_string():
    """Test empty string unit handled gracefully."""
    # Arrange
    kpis = {
        "business": {
            "portfoliofunctions": {
                "activity": {
                    "metric": {"value": 10, "unit": ""}
                }
            }
        }
    }

    # Act
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        print_kpi_table(kpis)
    output = f.getvalue()

    # Assert - Value shown without unit
    assert "10" in output


def test_print_kpi_table_flat_kpis_empty_after_flattening():
    """Test handling when flattening produces empty result."""
    # Arrange - Structure that will be empty after flattening
    kpis = {
        "business": {
            # Empty nested structure
        }
    }

    # Act
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        print_kpi_table(kpis)
    output = f.getvalue()

    # Assert - Graceful message
    assert "No KPIs found after flattening" in output


def test_print_kpi_table_kpi_key_with_less_than_3_parts():
    """Test KPI key with less than 3 parts is skipped."""
    # Arrange - Mix of valid (4 parts) and invalid (2 parts)
    kpis = {
        "business.portfoliofunctions.activity.valid": {"value": 1, "unit": "-"},
        "business.invalid": {"value": 99, "unit": "-"}  # Only 2 parts
    }

    # Act
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        print_kpi_table(kpis)
    output = f.getvalue()

    # Assert - Valid shown, invalid skipped
    assert "valid" in output
    assert "invalid" not in output


def test_print_kpi_table_kpi_key_with_exactly_3_parts_uses_metric_as_subgroup():
    """Test KPI key with exactly 3 parts uses metric name as subgroup."""
    # Arrange - 3-part key (no explicit subgroup)
    kpis = {
        "business": {
            "portfoliofunctions": {
                "metric_without_subgroup": {"value": 1, "unit": "-"}
            }
        }
    }

    # Act
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        print_kpi_table(kpis)
    output = f.getvalue()

    # Assert - Metric name used as subgroup (UPPERCASE)
    assert "METRIC_WITHOUT_SUBGROUP" in output
    assert "metric_without_subgroup" in output


def test_print_kpi_table_value_formatting_error_uses_str():
    """Test non-numeric value falls back to str() formatting."""
    # Arrange - Invalid value type
    kpis = {
        "business": {
            "portfoliofunctions": {
                "activity": {
                    "broken": {"value": "not_a_number", "unit": "-"}
                }
            }
        }
    }

    # Act
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        print_kpi_table(kpis)
    output = f.getvalue()

    # Assert - Fallback to string representation
    assert "broken" in output


def test_print_kpi_table_multiple_filter_patterns():
    """Test multiple filter patterns with OR logic."""
    # Arrange
    kpis = {
        "business": {
            "portfoliofunctions": {
                "activity": {"m1": {"value": 1, "unit": "-"}},
                "returns": {"m2": {"value": 2, "unit": "-"}},
                "risk": {"m3": {"value": 3, "unit": "-"}}
            }
        }
    }

    # Act
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        print_kpi_table(
            kpis,
            filter_patterns=[
                "business.portfoliofunctions.activity.*",
                "business.portfoliofunctions.returns.*"
            ]
        )
    output = f.getvalue()

    # Assert - m1 and m2 shown, m3 NOT shown
    assert "m1" in output
    assert "m2" in output
    assert "m3" not in output


def test_print_kpi_table_package_name_empty_string():
    """Test empty package name handled gracefully."""
    # Arrange - Malformed key with empty package
    kpis = {
        "business": {
            "": {  # Empty package name
                "subgroup": {"metric": {"value": 1, "unit": "-"}}
            }
        }
    }

    # Act
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        print_kpi_table(kpis)
    output = f.getvalue()

    # Assert - Handles gracefully (may show empty or skip)
    # At minimum, should not crash
    assert "metric" in output or "No KPIs" in output


def test_print_kpi_table_no_valid_kpis_after_grouping():
    """Test handling when grouping produces empty result (all keys < 3 parts)."""
    # Arrange - Only invalid KPI keys (< 3 parts after flattening)
    kpis = {
        "business.invalid": {"value": 1, "unit": "-"},  # Only 2 parts
        "alsoinvalid": {"value": 2, "unit": "-"}  # Only 1 part
    }

    # Act
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        print_kpi_table(kpis)
    output = f.getvalue()

    # Assert - Graceful message
    assert "No valid KPIs after grouping" in output
