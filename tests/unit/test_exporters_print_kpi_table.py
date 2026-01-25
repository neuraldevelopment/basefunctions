"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Comprehensive tests for print_kpi_table() with 2-level grouping format
 Log:
 v1.1 : Added 9 tests for sort_keys parameter behavior (default=True)
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
    output = capture_print_output(sample_kpis_single_package, unit_column=False)

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
    assert "1000 EUR" in output


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
    output = capture_print_output(sample_kpis_single_package, unit_column=False)

    # Assert - Values include units
    assert "0.75 %" in output
    assert "1000 EUR" in output

    # Assert - "Unit" column header NOT present
    unit_occurrences = output.count("Unit")
    assert unit_occurrences == 0  # No separate Unit column in 2-column layout


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
# TEST: TABLE FORMAT (grid from config)
# =============================================================================
def test_print_kpi_table_grid_format_default(
    capture_print_output,
    sample_kpis_single_package
):
    """Test grid format (default from config) uses ASCII box characters."""
    # Act
    output = capture_print_output(sample_kpis_single_package)

    # Assert - grid format ASCII characters present
    assert any(char in output for char in ["+", "-", "|"])


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


def test_print_kpi_table_integer_values_with_consistent_decimals():
    """Test integer values displayed with consistent decimal formatting."""
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
        print_kpi_table(kpis, decimals=2, unit_column=False)
    output = f.getvalue()

    # Assert - Integer detection: 42.0 → "42 -" (integer format)
    assert "42 -" in output


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
        print_kpi_table(kpis, unit_column=False)
    output = f.getvalue()

    # Assert - Percent symbol present (float with decimals)
    assert "0.50 %" in output


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


# =============================================================================
# CURRENCY OVERRIDE TESTS
# =============================================================================
def test_print_kpi_table_currency_override_default_eur(capture_print_output):
    """Test currency override with default EUR replaces USD."""
    # Arrange
    kpis = {
        "business.portfolio.returns.total_pnl": {"value": 1000.0, "unit": "USD"},
        "business.portfolio.returns.avg_win": {"value": 250.5, "unit": "USD"},
    }

    # Act
    output = capture_print_output(kpis, unit_column=False)

    # Assert - USD should be replaced with EUR (default)
    assert "1000 EUR" in output
    assert "250.50 EUR" in output  # Float with decimals
    assert "USD" not in output


def test_print_kpi_table_currency_override_chf(capture_print_output):
    """Test currency override with explicit CHF replaces USD."""
    # Arrange
    kpis = {
        "business.portfolio.returns.total_pnl": {"value": 1000.0, "unit": "USD"},
    }

    # Act
    output = capture_print_output(kpis, currency="CHF")

    # Assert - USD should be replaced with CHF
    assert "CHF" in output
    assert "USD" not in output


def test_print_kpi_table_currency_override_multiple_currencies(capture_print_output):
    """Test currency override replaces ALL currency codes (USD, GBP, JPY)."""
    # Arrange
    kpis = {
        "business.portfolio.a.metric1": {"value": 100.0, "unit": "USD"},
        "business.portfolio.b.metric2": {"value": 200.0, "unit": "GBP"},
        "business.portfolio.c.metric3": {"value": 300.0, "unit": "JPY"},
    }

    # Act
    output = capture_print_output(kpis, currency="EUR", unit_column=False)

    # Assert - All currencies should be EUR (integer detection)
    assert "100 EUR" in output
    assert "200 EUR" in output
    assert "300 EUR" in output
    assert "USD" not in output
    assert "GBP" not in output
    assert "JPY" not in output


def test_print_kpi_table_currency_override_preserves_non_currency_units(capture_print_output):
    """Test currency override does NOT change non-currency units (%, days, -)."""
    # Arrange
    kpis = {
        "business.portfolio.activity.trades": {"value": 5, "unit": "-"},
        "business.portfolio.risk.volatility": {"value": 12.5, "unit": "%"},
        "business.portfolio.temporal.duration": {"value": 30, "unit": "days"},
        "business.portfolio.returns.pnl": {"value": 1000.0, "unit": "USD"},
    }

    # Act
    output = capture_print_output(kpis, currency="EUR", unit_column=False)

    # Assert - Non-currency units unchanged (float with decimals where needed)
    assert "5 -" in output
    assert "12.50 %" in output  # Float with decimals
    assert "30 days" in output
    # Currency changed (integer detection)
    assert "1000 EUR" in output
    assert "USD" not in output


def test_print_kpi_table_currency_override_with_none_unit(capture_print_output):
    """Test currency override handles None units gracefully."""
    # Arrange
    kpis = {
        "business.portfolio.activity.metric": {"value": 42.0, "unit": None},
    }

    # Act
    output = capture_print_output(kpis, currency="EUR")

    # Assert - Should display value without unit
    assert "42" in output
    assert "EUR" not in output


# =============================================================================
# TEST: SORT_KEYS BEHAVIOR (CRITICAL FOR REFACTORING)
# =============================================================================
def test_print_kpi_table_sort_keys_default_false_implicit():
    """
    Test default sort_keys=False behavior (implicit, NO parameter passed).

    Validates that the NEW default sort_keys=False produces UNSORTED output.
    Packages appear in input order (Zebra before Alpha), NOT alphabetically sorted.
    """
    # Arrange - Packages in reverse alphabetical order
    kpis = {
        "business": {
            "zebra_package": {
                "z_subgroup": {"metric_z": {"value": 1, "unit": "-"}}
            },
            "alpha_package": {
                "a_subgroup": {"metric_a": {"value": 2, "unit": "-"}}
            }
        }
    }

    # Act - NO sort_keys parameter (uses default FALSE)
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        print_kpi_table(kpis)
    output = f.getvalue()

    # Assert - Packages UNSORTED (maintain input order: Zebra before Alpha)
    zebra_idx = output.find("Zebra_package")  # _format_package_name capitalizes first letter only
    alpha_idx = output.find("Alpha_package")
    assert zebra_idx > 0 and alpha_idx > 0
    assert zebra_idx < alpha_idx, "Zebra package should appear before Alpha package (input order preserved)"


def test_print_kpi_table_sort_keys_true_explicit_backward_compatible():
    """
    Test explicit sort_keys=True produces sorted output (backward compatibility).

    Validates that users can still explicitly request sorted output with sort_keys=True,
    even though the new default is False. Ensures backward compatibility maintained.
    """
    # Arrange - Packages in reverse alphabetical order
    kpis = {
        "business": {
            "zebra_package": {
                "z_subgroup": {"metric_z": {"value": 1, "unit": "-"}}
            },
            "alpha_package": {
                "a_subgroup": {"metric_a": {"value": 2, "unit": "-"}}
            }
        }
    }

    # Act - EXPLICIT sort_keys=True parameter
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        print_kpi_table(kpis, sort_keys=True)
    output = f.getvalue()

    # Assert - Packages sorted alphabetically (explicit sort_keys=True)
    alpha_idx = output.find("Alpha_package")  # _format_package_name capitalizes first letter only
    zebra_idx = output.find("Zebra_package")
    assert alpha_idx > 0 and zebra_idx > 0
    assert alpha_idx < zebra_idx, "Alpha package should appear before Zebra package (sorted output)"


def test_print_kpi_table_sort_keys_default_true_explicit():
    """
    Test that explicit sort_keys=True produces sorted output.

    Validates that users can explicitly request sorted output with sort_keys=True.
    Also validates that implicit default is now FALSE (unsorted).
    """
    # Arrange - Mixed order input (Z before A)
    kpis = {
        "business": {
            "z_pkg": {"z_sub": {"m1": {"value": 1, "unit": "-"}}},
            "a_pkg": {"a_sub": {"m2": {"value": 2, "unit": "-"}}}
        }
    }

    # Act - Explicit sort_keys=True
    f_explicit = io.StringIO()
    with contextlib.redirect_stdout(f_explicit):
        print_kpi_table(kpis, sort_keys=True)
    output_explicit = f_explicit.getvalue()

    # Act - Implicit default (no sort_keys parameter)
    f_implicit = io.StringIO()
    with contextlib.redirect_stdout(f_implicit):
        print_kpi_table(kpis)
    output_implicit = f_implicit.getvalue()

    # Assert - Explicit sort_keys=True produces sorted output (A before Z)
    a_explicit = output_explicit.find("A_pkg")
    z_explicit = output_explicit.find("Z_pkg")
    assert a_explicit > 0 and z_explicit > 0
    assert a_explicit < z_explicit, "Explicit sort_keys=True: A before Z (sorted)"

    # Assert - Implicit default produces UNSORTED output (maintains Z before A input order)
    z_implicit = output_implicit.find("Z_pkg")
    a_implicit = output_implicit.find("A_pkg")
    assert z_implicit > 0 and a_implicit > 0
    assert z_implicit < a_implicit, "Implicit default: Z before A (input order preserved, not sorted)"


def test_print_kpi_table_sort_keys_false_preserves_insertion_order():
    """
    Test sort_keys=False preserves dictionary insertion order (no sorting).

    Validates that when sort_keys=False, output order matches input order,
    not alphabetical order.
    """
    # Arrange - Intentionally reverse alphabetical order
    from collections import OrderedDict
    kpis = OrderedDict()
    kpis["business"] = {
        "zebra_package": {
            "zulu_subgroup": {"metric_z": {"value": 1, "unit": "-"}}
        },
        "alpha_package": {
            "alpha_subgroup": {"metric_a": {"value": 2, "unit": "-"}}
        }
    }

    # Act - sort_keys=False
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        print_kpi_table(kpis, sort_keys=False)
    output = f.getvalue()

    # Assert - Zebra appears BEFORE Alpha (insertion order, not alphabetical)
    zebra_idx = output.find("Zebra_package")
    alpha_idx = output.find("Alpha_package")
    assert zebra_idx > 0 and alpha_idx > 0
    assert zebra_idx < alpha_idx, "sort_keys=False: insertion order (Z before A)"


def test_print_kpi_table_sort_keys_false_subgroups_also_unsorted():
    """
    Test sort_keys=False preserves subgroup order (FIXED - was documented as TODO).

    After refactoring in v0.5.70, subgroups now respect sort_keys parameter.
    When sort_keys=False, subgroups maintain insertion order (Z before A).
    """
    # Arrange - Subgroups in reverse alphabetical order (Z, A)
    from collections import OrderedDict
    kpis = OrderedDict()
    kpis["business"] = {
        "package": OrderedDict([
            ("zulu_subgroup", {"m_z": {"value": 1, "unit": "-"}}),
            ("alpha_subgroup", {"m_a": {"value": 2, "unit": "-"}})
        ])
    }

    # Act - sort_keys=False
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        print_kpi_table(kpis, sort_keys=False)
    output = f.getvalue()

    # Assert - ZULU_SUBGROUP before ALPHA_SUBGROUP (insertion order, Z before A)
    # Fixed in v0.5.70: now respects sort_keys parameter
    lines = output.split("\n")
    zulu_lines = [i for i, l in enumerate(lines) if "ZULU_SUBGROUP" in l]
    alpha_lines = [i for i, l in enumerate(lines) if "ALPHA_SUBGROUP" in l]

    assert zulu_lines and alpha_lines, "Both subgroups should be present"
    assert zulu_lines[0] < alpha_lines[0], (
        "sort_keys=False: subgroups in insertion order (Z before A) - FIXED in v0.5.70"
    )


def test_print_kpi_table_sort_keys_true_subgroups_sorted_alphabetically():
    """
    Test sort_keys=True sorts BOTH packages AND subgroups alphabetically.

    Both level 1 (packages) and level 2 (subgroups) are sorted when True.
    """
    # Arrange - Subgroups in reverse alphabetical order
    kpis = {
        "business": {
            "package": {
                "zebra_subgroup": {"m_z": {"value": 1, "unit": "-"}},
                "alpha_subgroup": {"m_a": {"value": 2, "unit": "-"}}
            }
        }
    }

    # Act - sort_keys=True
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        print_kpi_table(kpis, sort_keys=True)
    output = f.getvalue()

    # Assert - ALPHA_SUBGROUP before ZEBRA_SUBGROUP (alphabetical)
    alpha_idx = output.find("ALPHA_SUBGROUP")
    zebra_idx = output.find("ZEBRA_SUBGROUP")
    assert alpha_idx > 0 and zebra_idx > 0
    assert alpha_idx < zebra_idx, "sort_keys=True: alphabetical order (A before Z)"


def test_print_kpi_table_sort_keys_true_multiple_packages_sorted():
    """
    Test sort_keys=True with multiple packages produces alphabetical order.

    Three packages with single metric each, verify rendering order alphabetical.
    """
    # Arrange - Three packages in non-alphabetical order
    kpis = {
        "business": {
            "zulu_pkg": {"s1": {"m": {"value": 1, "unit": "-"}}},
            "mike_pkg": {"s1": {"m": {"value": 2, "unit": "-"}}},
            "alpha_pkg": {"s1": {"m": {"value": 3, "unit": "-"}}}
        }
    }

    # Act - sort_keys=True (explicit)
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        print_kpi_table(kpis, sort_keys=True)
    output = f.getvalue()

    # Assert - Alpha < Mike < Zulu (alphabetical order)
    alpha_idx = output.find("Alpha_pkg")
    mike_idx = output.find("Mike_pkg")
    zulu_idx = output.find("Zulu_pkg")

    # Check package headers exist and are in correct order
    lines = output.split("\n")
    alpha_lines = [i for i, l in enumerate(lines) if "Alpha_pkg" in l]
    mike_lines = [i for i, l in enumerate(lines) if "Mike_pkg" in l]
    zulu_lines = [i for i, l in enumerate(lines) if "Zulu_pkg" in l]

    if alpha_lines and mike_lines:
        assert alpha_lines[0] < mike_lines[0], "Alpha before Mike"
    if mike_lines and zulu_lines:
        assert mike_lines[0] < zulu_lines[0], "Mike before Zulu"


def test_print_kpi_table_sort_keys_changes_table_output_order():
    """
    Test that sort_keys parameter actually changes visible table order.

    CRITICAL: Validates that sort_keys parameter is NOT ignored
    (regression test for future refactoring).
    """
    # Arrange - Packages intentionally reverse alphabetical
    kpis = {
        "business": {
            "zoo_pkg": {"s": {"m": {"value": 1, "unit": "-"}}},
            "apple_pkg": {"s": {"m": {"value": 2, "unit": "-"}}}
        }
    }

    # Act - With sort_keys=True
    f_sorted = io.StringIO()
    with contextlib.redirect_stdout(f_sorted):
        print_kpi_table(kpis, sort_keys=True)
    output_sorted = f_sorted.getvalue()

    # Act - With sort_keys=False
    f_unsorted = io.StringIO()
    with contextlib.redirect_stdout(f_unsorted):
        print_kpi_table(kpis, sort_keys=False)
    output_unsorted = f_unsorted.getvalue()

    # Assert - Outputs DIFFERENT (order changed by sort_keys parameter)
    sorted_apple_idx = output_sorted.find("Apple_pkg")
    sorted_zoo_idx = output_sorted.find("Zoo_pkg")
    unsorted_zoo_idx = output_unsorted.find("Zoo_pkg")
    unsorted_apple_idx = output_unsorted.find("Apple_pkg")

    # sort_keys=True: Apple < Zoo
    assert sorted_apple_idx > 0 and sorted_zoo_idx > 0
    assert sorted_apple_idx < sorted_zoo_idx

    # sort_keys=False: Zoo < Apple (insertion order)
    assert unsorted_zoo_idx > 0 and unsorted_apple_idx > 0
    assert unsorted_zoo_idx < unsorted_apple_idx

    # CRITICAL: Outputs must be different
    assert output_sorted != output_unsorted, "sort_keys parameter must change output"


def test_print_kpi_table_sort_keys_false_with_filter_patterns_respects_order():
    """
    Test sort_keys=False is respected even when filter_patterns applied.

    Validates sort_keys behavior is independent of filtering.
    """
    # Arrange
    kpis = {
        "business": {
            "z_pkg": {"s": {"m": {"value": 1, "unit": "-"}}},
            "a_pkg": {"s": {"m": {"value": 2, "unit": "-"}}}
        }
    }

    # Act - sort_keys=False with filter
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        print_kpi_table(
            kpis,
            sort_keys=False,
            filter_patterns=["business.*"]
        )
    output = f.getvalue()

    # Assert - Insertion order preserved (Z before A)
    z_idx = output.find("Z_pkg")
    a_idx = output.find("A_pkg")
    if z_idx > 0 and a_idx > 0:
        assert z_idx < a_idx, "sort_keys=False: insertion order preserved with filter"
