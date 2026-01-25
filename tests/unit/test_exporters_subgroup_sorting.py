"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Tests for hardcoded subgroup sorting behavior in _build_table_rows_with_sections()
 and _build_table_rows_with_units() helper functions. Validates that subgroups are
 ALWAYS sorted alphabetically, regardless of sort_keys parameter in print_kpi_table().

 These tests document current behavior (hardcoded sorted) to prevent regression
 when refactoring to add sort_keys parameter support to helper functions.
 Log:
 v1.0 : Initial implementation - 5+ test scenarios for subgroup sorting validation
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
# Standard Library
import contextlib
import io
from collections import OrderedDict
from typing import Any, Dict, List, Tuple

# Third-party
import pytest

# Project modules
from basefunctions.kpi.exporters import (
    _build_table_rows_with_sections,
    _build_table_rows_with_units,
    print_kpi_table
)


# =============================================================================
# FIXTURES
# =============================================================================
@pytest.fixture
def unsorted_subgroups_sections() -> Dict[str, List[Tuple[str, Dict[str, Any]]]]:
    """
    Provide unsorted subgroups dict for _build_table_rows_with_sections() testing.

    Returns
    -------
    Dict[str, List[Tuple[str, Dict[str, Any]]]]
        Subgroups in reverse alphabetical order (Z, M, A)
    """
    return {
        "zebra": [("metric_z", {"value": 1.0, "unit": "%"})],
        "mike": [("metric_m", {"value": 2.0, "unit": "%"})],
        "alpha": [("metric_a", {"value": 3.0, "unit": "%"})]
    }


@pytest.fixture
def unsorted_subgroups_units() -> Dict[str, List[Tuple[str, Dict[str, Any]]]]:
    """
    Provide unsorted subgroups dict for _build_table_rows_with_units() testing.

    Returns
    -------
    Dict[str, List[Tuple[str, Dict[str, Any]]]]
        Subgroups in reverse alphabetical order (Z, M, A)
    """
    return {
        "zebra": [("metric_z", {"value": 100.0, "unit": "USD"})],
        "mike": [("metric_m", {"value": 200.0, "unit": "USD"})],
        "alpha": [("metric_a", {"value": 300.0, "unit": "USD"})]
    }


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


# =============================================================================
# TEST GROUP 1: _build_table_rows_with_sections() Subgroup Sorting
# =============================================================================
def test_build_table_rows_with_sections_sorts_subgroups_alphabetically(
    unsorted_subgroups_sections
):
    """
    Test _build_table_rows_with_sections() sorts subgroups alphabetically when sort_keys=True.

    Validates that subgroups input in order (Z, M, A) are output in sorted order (A, M, Z).
    """
    # Arrange
    decimals = 2
    currency = "EUR"

    # Act - EXPLICIT sort_keys=True
    rows = _build_table_rows_with_sections(unsorted_subgroups_sections, decimals, currency, sort_keys=True)

    # Assert - Extract subgroup headers from rows (those with empty value column AND non-empty kpi)
    subgroup_headers = []
    for row in rows:
        if len(row) == 2 and row[1] == "" and row[0] != "":
            # Remove ANSI color codes from header
            header = row[0]
            if "\033[" in header:
                # Strip ANSI codes: "\033[1;33m...\033[0m" → content
                header = header.replace("\033[1;33m", "").replace("\033[0m", "")
            subgroup_headers.append(header)

    # Verify sorted order (A, M, Z)
    expected_order = ["alpha", "mike", "zebra"]
    assert subgroup_headers == expected_order, (
        f"Subgroups not sorted alphabetically. "
        f"Expected {expected_order}, got {subgroup_headers}"
    )


def test_build_table_rows_with_sections_subgroup_sorting_independent_of_input_order():
    """
    Test subgroup sorting is independent of input dictionary order.

    Creates input with various orderings to verify alphabetical sort is applied
    regardless of input order (proves sorted() is applied, not relying on dict order).
    """
    # Arrange - Multiple orderings
    orderings = [
        {"z": [("m1", {"value": 1, "unit": "-"})],
         "a": [("m2", {"value": 2, "unit": "-"})],
         "m": [("m3", {"value": 3, "unit": "-"})]},
        {"a": [("m1", {"value": 1, "unit": "-"})],
         "z": [("m2", {"value": 2, "unit": "-"})],
         "m": [("m3", {"value": 3, "unit": "-"})]},
        {"m": [("m1", {"value": 1, "unit": "-"})],
         "a": [("m2", {"value": 2, "unit": "-"})],
         "z": [("m3", {"value": 3, "unit": "-"})]}
    ]

    expected_headers = ["a", "m", "z"]

    # Act & Assert
    for grouped in orderings:
        rows = _build_table_rows_with_sections(grouped, decimals=2, sort_keys=True)

        # Extract headers (skip separator rows)
        headers = []
        for row in rows:
            if len(row) == 2 and row[1] == "" and row[0] != "":
                header = row[0].replace("\033[1;33m", "").replace("\033[0m", "")
                headers.append(header)

        assert headers == expected_headers, (
            f"Subgroup order should always be alphabetical regardless of input. "
            f"Got {headers}, expected {expected_headers}"
        )


def test_build_table_rows_with_sections_subgroup_sorting_with_numeric_metrics():
    """
    Test subgroup sorting with various numeric values to ensure sorting not affected by data.
    """
    # Arrange
    subgroups = {
        "zebra": [("m1", {"value": 1000.5, "unit": "USD"})],
        "alpha": [("m2", {"value": 0.001, "unit": "%"})],
        "mike": [("m3", {"value": -50.0, "unit": "EUR"})]
    }

    # Act - EXPLICIT sort_keys=True
    rows = _build_table_rows_with_sections(subgroups, decimals=2, sort_keys=True)

    # Assert
    headers = []
    for row in rows:
        if len(row) == 2 and row[1] == "" and row[0] != "":
            header = row[0].replace("\033[1;33m", "").replace("\033[0m", "")
            headers.append(header)

    assert headers == ["alpha", "mike", "zebra"]


# =============================================================================
# TEST GROUP 2: _build_table_rows_with_units() Subgroup Sorting
# =============================================================================
def test_build_table_rows_with_units_sorts_subgroups_alphabetically(
    unsorted_subgroups_units
):
    """
    Test _build_table_rows_with_units() sorts subgroups alphabetically (current behavior).

    Validates that subgroups input in order (Z, M, A) are output in sorted order (A, M, Z).
    This documents the hardcoded sorted() call at line 921.
    """
    # Arrange
    decimals = 2
    currency = "EUR"

    # Act - EXPLICIT sort_keys=True
    rows = _build_table_rows_with_units(unsorted_subgroups_units, decimals, currency, sort_keys=True)

    # Assert - Extract subgroup headers (3-column rows with value and unit empty, non-empty kpi)
    subgroup_headers = []
    for row in rows:
        if len(row) == 3 and row[1] == "" and row[2] == "" and row[0] != "":
            header = row[0].replace("\033[1;33m", "").replace("\033[0m", "")
            subgroup_headers.append(header)

    expected_order = ["alpha", "mike", "zebra"]
    assert subgroup_headers == expected_order, (
        f"Subgroups not sorted alphabetically. "
        f"Expected {expected_order}, got {subgroup_headers}"
    )


def test_build_table_rows_with_units_subgroup_sorting_independent_of_input_order():
    """
    Test subgroup sorting is independent of input dictionary order (3-column variant).
    """
    # Arrange
    orderings = [
        {"z": [("m1", {"value": 1, "unit": "%"})],
         "a": [("m2", {"value": 2, "unit": "%"})],
         "m": [("m3", {"value": 3, "unit": "%"})]},
        {"a": [("m1", {"value": 1, "unit": "%"})],
         "m": [("m2", {"value": 2, "unit": "%"})],
         "z": [("m3", {"value": 3, "unit": "%"})]}
    ]

    expected_headers = ["a", "m", "z"]

    # Act & Assert
    for grouped in orderings:
        rows = _build_table_rows_with_units(grouped, decimals=2, sort_keys=True)

        headers = []
        for row in rows:
            if len(row) == 3 and row[1] == "" and row[2] == "" and row[0] != "":
                header = row[0].replace("\033[1;33m", "").replace("\033[0m", "")
                headers.append(header)

        assert headers == expected_headers


def test_build_table_rows_with_units_subgroup_sorting_with_currency_units():
    """
    Test subgroup sorting with various currency units (validates sorting not affected by unit type).
    """
    # Arrange
    subgroups = {
        "zebra": [("m1", {"value": 100, "unit": "USD"})],
        "alpha": [("m2", {"value": 200, "unit": "GBP"})],
        "mike": [("m3", {"value": 300, "unit": "JPY"})]
    }

    # Act - EXPLICIT sort_keys=True
    rows = _build_table_rows_with_units(subgroups, decimals=2, currency="EUR", sort_keys=True)

    # Assert
    headers = []
    for row in rows:
        if len(row) == 3 and row[1] == "" and row[2] == "" and row[0] != "":
            header = row[0].replace("\033[1;33m", "").replace("\033[0m", "")
            headers.append(header)

    assert headers == ["alpha", "mike", "zebra"]


# =============================================================================
# TEST GROUP 3: print_kpi_table() with sort_keys=False (Still Sorts Subgroups)
# =============================================================================
def test_print_kpi_table_sort_keys_false_still_sorts_subgroups(
    capture_print_output
):
    """
    Test print_kpi_table() with sort_keys=False STILL sorts subgroups alphabetically.

    CRITICAL: This proves subgroup sorting is hardcoded and not controlled by sort_keys.
    With sort_keys=False, packages maintain insertion order but subgroups are always sorted.
    """
    # Arrange - Packages in insertion order, subgroups intentionally unsorted
    kpis = {
        "business": {
            "portfolio": {
                "zebra_subgroup": {"metric_z": {"value": 1, "unit": "-"}},
                "alpha_subgroup": {"metric_a": {"value": 2, "unit": "-"}},
                "mike_subgroup": {"metric_m": {"value": 3, "unit": "-"}}
            }
        }
    }

    # Act - EXPLICIT sort_keys=False
    output = capture_print_output(kpis, sort_keys=False)

    # Assert - Subgroups maintain insertion order (NEW behavior with refactoring)
    # Insertion order in dict: zebra (line 295), alpha (line 297), mike (line 299)
    # Expected output order: Z, A, M
    lines = output.split("\n")

    # Find line numbers for each subgroup header
    zebra_lines = [i for i, l in enumerate(lines) if "ZEBRA_SUBGROUP" in l]
    alpha_lines = [i for i, l in enumerate(lines) if "ALPHA_SUBGROUP" in l]
    mike_lines = [i for i, l in enumerate(lines) if "MIKE_SUBGROUP" in l]

    assert zebra_lines and alpha_lines and mike_lines, (
        "All subgroups should be present in output"
    )

    # Verify insertion order: ZEBRA < ALPHA < MIKE
    z_line = zebra_lines[0]
    a_line = alpha_lines[0]
    m_line = mike_lines[0]

    assert z_line < a_line < m_line, (
        f"Subgroups should appear in insertion order (Z < A < M) "
        f"with sort_keys=False. Got Z={z_line}, A={a_line}, M={m_line}"
    )


def test_print_kpi_table_sort_keys_false_subgroup_sorting_multiple_packages():
    """
    Test subgroup sorting with multiple packages and sort_keys=False.

    Packages should maintain insertion order (Z before A), and subgroups
    within each package should ALSO maintain insertion order (NEW behavior).
    """
    # Arrange
    kpis = {
        "business": {
            "z_package": {
                "zulu": {"m1": {"value": 1, "unit": "-"}},
                "alpha": {"m2": {"value": 2, "unit": "-"}}
            },
            "a_package": {
                "zulu": {"m3": {"value": 3, "unit": "-"}},
                "alpha": {"m4": {"value": 4, "unit": "-"}}
            }
        }
    }

    # Act
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        print_kpi_table(kpis, sort_keys=False)
    output = f.getvalue()

    # Assert - Packages in insertion order (Z before A)
    z_pkg_idx = output.find("Z_package")
    a_pkg_idx = output.find("A_package")
    assert z_pkg_idx > 0 and a_pkg_idx > 0
    assert z_pkg_idx < a_pkg_idx, (
        "Packages should maintain insertion order (Z before A) with sort_keys=False"
    )

    # Assert - Subgroups within each package are in insertion order (ZULU before ALPHA)
    # NEW behavior after refactoring: insertion order is preserved when sort_keys=False
    # Within Z_package section
    lines = output.split("\n")
    z_pkg_line = next((i for i, l in enumerate(lines) if "Z_package" in l), -1)
    a_pkg_line = next((i for i, l in enumerate(lines) if "A_package" in l), -1)

    # Find first ZULU and ALPHA subgroup headers between packages
    zulu_subs = [i for i, l in enumerate(lines) if "ZULU" in l and z_pkg_line < i < a_pkg_line]
    alpha_subs = [i for i, l in enumerate(lines) if "ALPHA" in l and z_pkg_line < i < a_pkg_line]

    if zulu_subs and alpha_subs:
        assert zulu_subs[0] < alpha_subs[0], (
            "Subgroups within package should maintain insertion order (ZULU before ALPHA) "
            "with sort_keys=False (NEW behavior after refactoring)"
        )


# =============================================================================
# TEST GROUP 4: print_kpi_table() with sort_keys=True (Also Sorts Subgroups)
# =============================================================================
def test_print_kpi_table_sort_keys_true_sorts_subgroups(
    capture_print_output
):
    """
    Test print_kpi_table() with sort_keys=True sorts subgroups alphabetically.

    Validates consistency: subgroups sorted regardless of sort_keys value.
    """
    # Arrange
    kpis = {
        "business": {
            "package": {
                "zebra_sub": {"m1": {"value": 1, "unit": "-"}},
                "alpha_sub": {"m2": {"value": 2, "unit": "-"}},
                "mike_sub": {"m3": {"value": 3, "unit": "-"}}
            }
        }
    }

    # Act - EXPLICIT sort_keys=True
    output = capture_print_output(kpis, sort_keys=True)

    # Assert - Subgroups sorted alphabetically (A, M, Z)
    alpha_idx = output.find("ALPHA_SUB")
    mike_idx = output.find("MIKE_SUB")
    zebra_idx = output.find("ZEBRA_SUB")

    assert alpha_idx > 0 and mike_idx > 0 and zebra_idx > 0
    assert alpha_idx < mike_idx < zebra_idx, (
        "Subgroups should be sorted alphabetically with sort_keys=True"
    )


def test_print_kpi_table_sort_keys_parameter_independent_of_subgroup_sorting():
    """
    Test that sort_keys parameter affects packages but NOT subgroups.

    Demonstrates that subgroup sorting is hardcoded and independent of sort_keys.
    """
    # Arrange
    kpis = {
        "business": {
            "z_pkg": {
                "z_sub": {"m1": {"value": 1, "unit": "-"}},
                "a_sub": {"m2": {"value": 2, "unit": "-"}}
            }
        }
    }

    # Act - sort_keys=True
    f_true = io.StringIO()
    with contextlib.redirect_stdout(f_true):
        print_kpi_table(kpis, sort_keys=True)
    output_true = f_true.getvalue()

    # Act - sort_keys=False
    f_false = io.StringIO()
    with contextlib.redirect_stdout(f_false):
        print_kpi_table(kpis, sort_keys=False)
    output_false = f_false.getvalue()

    # Assert - sort_keys=True: subgroups sorted (A before Z)
    lines_true = output_true.split("\n")
    a_true = [i for i, l in enumerate(lines_true) if "A_SUB" in l]
    z_true = [i for i, l in enumerate(lines_true) if "Z_SUB" in l]
    assert a_true and z_true
    assert a_true[0] < z_true[0], (
        "With sort_keys=True: subgroups should be sorted (A before Z)"
    )

    # Assert - sort_keys=False: subgroups in insertion order (Z before A)
    lines_false = output_false.split("\n")
    a_false = [i for i, l in enumerate(lines_false) if "A_SUB" in l]
    z_false = [i for i, l in enumerate(lines_false) if "Z_SUB" in l]
    assert a_false and z_false
    assert z_false[0] < a_false[0], (
        "With sort_keys=False: subgroups should be in insertion order (Z before A)"
    )


# =============================================================================
# TEST GROUP 5: Subgroup Sorting Independent of Package Sorting
# =============================================================================
def test_subgroup_sorting_independent_of_package_sorting(
    capture_print_output
):
    """
    Test that subgroup sorting respects sort_keys parameter.

    When sort_keys=False: packages unsorted, subgroups also unsorted (insertion order).
    When sort_keys=True: packages sorted, subgroups also sorted.
    Proves subgroup sorting is now parametrized (NEW behavior after refactoring).
    """
    # Arrange
    kpis = {
        "business": {
            "z_package": {
                "z_sub": {"m1": {"value": 1, "unit": "-"}},
                "a_sub": {"m2": {"value": 2, "unit": "-"}}
            },
            "a_package": {
                "z_sub": {"m3": {"value": 3, "unit": "-"}},
                "a_sub": {"m4": {"value": 4, "unit": "-"}}
            }
        }
    }

    # Act - sort_keys=False
    output_unsorted = capture_print_output(kpis, sort_keys=False)

    # Act - sort_keys=True
    output_sorted = capture_print_output(kpis, sort_keys=True)

    # Helper function to find subgroup indices
    def get_subgroup_indices(output):
        lines = output.split("\n")
        a_indices = [i for i, l in enumerate(lines) if "A_SUB" in l]
        z_indices = [i for i, l in enumerate(lines) if "Z_SUB" in l]
        return a_indices, z_indices

    a_unsorted, z_unsorted = get_subgroup_indices(output_unsorted)
    a_sorted, z_sorted = get_subgroup_indices(output_sorted)

    # Assert - Package ordering differs (Z before A with sort_keys=False)
    z_pkg_unsorted = output_unsorted.find("Z_package")
    a_pkg_unsorted = output_unsorted.find("A_package")
    z_pkg_sorted = output_sorted.find("Z_package")
    a_pkg_sorted = output_sorted.find("A_package")

    assert z_pkg_unsorted < a_pkg_unsorted, (
        "sort_keys=False: packages in input order (Z before A)"
    )
    assert a_pkg_sorted < z_pkg_sorted, (
        "sort_keys=True: packages alphabetically sorted (A before Z)"
    )

    # Assert - Subgroup ordering ALSO differs based on sort_keys (NEW behavior)
    if z_unsorted and a_unsorted:
        assert z_unsorted[0] < a_unsorted[0], (
            "sort_keys=False: subgroups in insertion order (Z before A)"
        )
    if a_sorted and z_sorted:
        assert a_sorted[0] < z_sorted[0], (
            "sort_keys=True: subgroups alphabetically sorted (A before Z)"
        )


def test_subgroup_sorting_consistent_across_multiple_packages():
    """
    Test that subgroup sorting is applied consistently across all packages.

    With 3 packages each having unsorted subgroups, verify all packages
    have subgroups sorted identically.
    """
    # Arrange
    kpis = {
        "business": {
            "pkg1": {
                "z": {"m1": {"value": 1, "unit": "-"}},
                "a": {"m2": {"value": 2, "unit": "-"}}
            },
            "pkg2": {
                "z": {"m3": {"value": 3, "unit": "-"}},
                "a": {"m4": {"value": 4, "unit": "-"}}
            },
            "pkg3": {
                "z": {"m5": {"value": 5, "unit": "-"}},
                "a": {"m6": {"value": 6, "unit": "-"}}
            }
        }
    }

    # Act
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        print_kpi_table(kpis, sort_keys=False)
    output = f.getvalue()

    # Assert - Every package has A_SUB before Z_SUB
    lines = output.split("\n")

    # Find package boundaries
    pkg_lines = [(i, l) for i, l in enumerate(lines) if "pkg" in l.lower()]

    # Check subgroup order within each package
    for idx, (pkg_line_num, pkg_line) in enumerate(pkg_lines):
        # Determine range until next package or end
        if idx < len(pkg_lines) - 1:
            next_pkg_line = pkg_lines[idx + 1][0]
        else:
            next_pkg_line = len(lines)

        # Find A and Z subgroups in this package range
        a_subs = [i for i, l in enumerate(lines[pkg_line_num:next_pkg_line]) if "A" in l.upper()]
        z_subs = [i for i, l in enumerate(lines[pkg_line_num:next_pkg_line]) if "Z" in l.upper()]

        # Convert back to absolute indices
        a_subs = [i + pkg_line_num for i in a_subs]
        z_subs = [i + pkg_line_num for i in z_subs]

        # If both exist, A should come before Z
        if a_subs and z_subs:
            assert a_subs[0] < z_subs[0], (
                f"Package at line {pkg_line_num}: subgroups not sorted"
            )


# =============================================================================
# ADDITIONAL EDGE CASE TESTS
# =============================================================================
def test_build_table_rows_with_sections_single_subgroup():
    """Test with single subgroup (no sorting needed but validated)."""
    # Arrange
    subgroups = {"single": [("metric", {"value": 42, "unit": "-"})]}

    # Act - EXPLICIT sort_keys=True
    rows = _build_table_rows_with_sections(subgroups, decimals=2, sort_keys=True)

    # Assert
    assert any("single" in row[0].lower() for row in rows)
    assert any("metric" in row[0] for row in rows)


def test_build_table_rows_with_units_single_subgroup():
    """Test with single subgroup (3-column variant)."""
    # Arrange
    subgroups = {"single": [("metric", {"value": 42, "unit": "%"})]}

    # Act
    rows = _build_table_rows_with_units(subgroups, decimals=2)

    # Assert
    assert any("single" in row[0].lower() for row in rows)
    assert any("metric" in row[0] for row in rows)


def test_subgroup_sorting_with_special_characters():
    """Test sorting with subgroup names containing special characters."""
    # Arrange
    subgroups = {
        "zebra_group": [("m1", {"value": 1, "unit": "-"})],
        "alpha-group": [("m2", {"value": 2, "unit": "-"})],
        "mike.group": [("m3", {"value": 3, "unit": "-"})]
    }

    # Act - EXPLICIT sort_keys=True
    rows = _build_table_rows_with_sections(subgroups, decimals=2, sort_keys=True)

    # Assert - All subgroups present and sorted lexicographically
    headers = []
    for row in rows:
        if len(row) == 2 and row[1] == "" and row[0] != "":
            header = row[0].replace("\033[1;33m", "").replace("\033[0m", "")
            headers.append(header)

    # Should contain all three variants sorted by Python's default string sort
    assert len(headers) == 3
    assert headers == sorted(["zebra_group", "alpha-group", "mike.group"])


def test_subgroup_sorting_with_numeric_suffixes():
    """Test sorting with numeric suffixes to verify lexicographic sort."""
    # Arrange
    subgroups = {
        "subgroup_10": [("m1", {"value": 1, "unit": "-"})],
        "subgroup_2": [("m2", {"value": 2, "unit": "-"})],
        "subgroup_1": [("m3", {"value": 3, "unit": "-"})]
    }

    # Act - EXPLICIT sort_keys=True
    rows = _build_table_rows_with_sections(subgroups, decimals=2, sort_keys=True)

    # Assert - Lexicographic sort (not numeric): "1", "10", "2"
    headers = []
    for row in rows:
        if len(row) == 2 and row[1] == "" and row[0] != "":
            header = row[0].replace("\033[1;33m", "").replace("\033[0m", "")
            headers.append(header)

    expected = sorted(["subgroup_10", "subgroup_2", "subgroup_1"])
    assert headers == expected
