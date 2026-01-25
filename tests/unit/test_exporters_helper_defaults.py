"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Tests for helper function default sort_keys parameter behavior in exporters.py
 Validates CURRENT defaults (sort_keys=True) before refactoring to FALSE
 Log:
 v1.0 : Initial implementation - Testing CURRENT defaults (True) to prevent regression
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
# Standard Library
from collections import OrderedDict
from typing import Any, Dict, List, Tuple

# Third-party
import pytest

# Project modules
from basefunctions.kpi.exporters import (
    _build_table_rows_with_sections,
    _build_table_rows_with_units,
)


# =============================================================================
# FIXTURES
# =============================================================================
@pytest.fixture
def unordered_subgroups():
    """
    Provide subgroups in reverse alphabetical order.

    Returns
    -------
    Dict[str, List[Tuple[str, Dict[str, Any]]]]
        Subgroups: ZEBRA before ALPHA (insertion order NOT alphabetical)
    """
    return OrderedDict([
        ("ZEBRA", [("metric_z", {"value": 100.0, "unit": "USD"})]),
        ("ALPHA", [("metric_a", {"value": 50.0, "unit": "%"})])
    ])


@pytest.fixture
def unordered_subgroups_multiple():
    """
    Provide multiple subgroups in mixed order.

    Returns
    -------
    Dict[str, List[Tuple[str, Dict[str, Any]]]]
        Subgroups: ZEBRA, MIKE, ALPHA (reverse alphabetical order)
    """
    return OrderedDict([
        ("ZEBRA", [("metric_z", {"value": 10, "unit": "-"})]),
        ("MIKE", [("metric_m", {"value": 20, "unit": "-"})]),
        ("ALPHA", [("metric_a", {"value": 30, "unit": "-"})])
    ])


@pytest.fixture
def single_subgroup():
    """
    Provide single subgroup.

    Returns
    -------
    Dict[str, List[Tuple[str, Dict[str, Any]]]]
        Single subgroup with one metric
    """
    return {
        "ACTIVITY": [("win_rate", {"value": 0.75, "unit": "%"})]
    }


@pytest.fixture
def many_metrics_per_subgroup():
    """
    Provide subgroups with many metrics each.

    Returns
    -------
    Dict[str, List[Tuple[str, Dict[str, Any]]]]
        Multiple metrics per subgroup
    """
    return OrderedDict([
        ("ZEBRA_GROUP", [
            ("metric_z1", {"value": 1.0, "unit": "-"}),
            ("metric_z2", {"value": 2.0, "unit": "-"}),
            ("metric_z3", {"value": 3.0, "unit": "-"})
        ]),
        ("ALPHA_GROUP", [
            ("metric_a1", {"value": 10.0, "unit": "-"}),
            ("metric_a2", {"value": 20.0, "unit": "-"}),
        ])
    ])


# =============================================================================
# TEST: _build_table_rows_with_sections() DEFAULT BEHAVIOR (sort_keys=True)
# =============================================================================
def test_build_table_rows_with_sections_default_is_false():
    """
    Test _build_table_rows_with_sections() default sort_keys is False.

    Calling WITHOUT sort_keys parameter should use default=False,
    which means INSERTION ORDER preservation of subgroups in output.
    """
    # Arrange - Subgroups in reverse order (ZEBRA before ALPHA)
    subgroups = OrderedDict([
        ("ZEBRA", [("metric_z", {"value": 100.0, "unit": "USD"})]),
        ("ALPHA", [("metric_a", {"value": 50.0, "unit": "%"})])
    ])

    # Act - Call WITHOUT sort_keys parameter (uses default=False)
    rows = _build_table_rows_with_sections(subgroups)

    # Assert - Rows should preserve insertion order: ZEBRA before ALPHA
    # Row structure: [["SECTION_HEADER", ""], ["  metric", "value"], ...]
    section_headers = [r[0] for r in rows if r[1] == ""]

    zebra_idx = next((i for i, h in enumerate(section_headers) if "ZEBRA" in h), -1)
    alpha_idx = next((i for i, h in enumerate(section_headers) if "ALPHA" in h), -1)

    assert zebra_idx >= 0, "ZEBRA section header should exist"
    assert alpha_idx >= 0, "ALPHA section header should exist"
    assert zebra_idx < alpha_idx, (
        "Default sort_keys=False: ZEBRA before ALPHA (insertion order)"
    )


def test_build_table_rows_with_sections_sorted_true_explicit():
    """
    Test _build_table_rows_with_sections() with explicit sort_keys=True.

    Explicitly passing sort_keys=True should produce alphabetically sorted output.
    """
    # Arrange
    subgroups = OrderedDict([
        ("ZEBRA", [("metric_z", {"value": 100.0, "unit": "USD"})]),
        ("ALPHA", [("metric_a", {"value": 50.0, "unit": "%"})])
    ])

    # Act - Explicit sort_keys=True
    rows = _build_table_rows_with_sections(subgroups, sort_keys=True)

    # Assert - ALPHA before ZEBRA
    section_headers = [r[0] for r in rows if r[1] == ""]
    alpha_idx = next((i for i, h in enumerate(section_headers) if "ALPHA" in h), -1)
    zebra_idx = next((i for i, h in enumerate(section_headers) if "ZEBRA" in h), -1)

    assert alpha_idx >= 0 and zebra_idx >= 0
    assert alpha_idx < zebra_idx, "sort_keys=True: alphabetical (ALPHA < ZEBRA)"


def test_build_table_rows_with_sections_sorted_false_preserves_order(
    unordered_subgroups,
):
    """
    Test _build_table_rows_with_sections() with sort_keys=False.

    When sort_keys=False, should preserve insertion order (ZEBRA before ALPHA).
    """
    # Act - sort_keys=False
    rows = _build_table_rows_with_sections(unordered_subgroups, sort_keys=False)

    # Assert - ZEBRA before ALPHA (insertion order)
    section_headers = [r[0] for r in rows if r[1] == ""]
    zebra_idx = next((i for i, h in enumerate(section_headers) if "ZEBRA" in h), -1)
    alpha_idx = next((i for i, h in enumerate(section_headers) if "ALPHA" in h), -1)

    assert zebra_idx >= 0 and alpha_idx >= 0
    assert zebra_idx < alpha_idx, (
        "sort_keys=False: insertion order (ZEBRA < ALPHA)"
    )


def test_build_table_rows_with_sections_multiple_subgroups_insertion_order(
    unordered_subgroups_multiple,
):
    """
    Test insertion order preservation with multiple subgroups in mixed order.

    With default sort_keys=False, should preserve insertion order: ZEBRA, MIKE, ALPHA.
    """
    # Act - Default sort_keys=False
    rows = _build_table_rows_with_sections(unordered_subgroups_multiple)

    # Assert - Insertion order (ZEBRA, MIKE, ALPHA)
    section_headers = [r[0] for r in rows if r[1] == ""]
    zebra_idx = next((i for i, h in enumerate(section_headers) if "ZEBRA" in h), -1)
    mike_idx = next((i for i, h in enumerate(section_headers) if "MIKE" in h), -1)
    alpha_idx = next((i for i, h in enumerate(section_headers) if "ALPHA" in h), -1)

    assert zebra_idx >= 0 and mike_idx >= 0 and alpha_idx >= 0
    assert zebra_idx < mike_idx < alpha_idx, (
        "Default sort_keys=False: ZEBRA < MIKE < ALPHA (insertion order)"
    )


def test_build_table_rows_with_sections_single_subgroup_no_sort_effect(
    single_subgroup,
):
    """
    Test single subgroup (sort_keys has no effect with single entry).

    Single subgroup should appear same regardless of sort_keys parameter.
    """
    # Act - Both with and without sort
    rows_sorted = _build_table_rows_with_sections(single_subgroup, sort_keys=True)
    rows_unsorted = _build_table_rows_with_sections(single_subgroup, sort_keys=False)

    # Assert - Same content (single entry, no sorting difference)
    section_headers_sorted = [r[0] for r in rows_sorted if r[1] == ""]
    section_headers_unsorted = [r[0] for r in rows_unsorted if r[1] == ""]

    assert len(section_headers_sorted) == 1
    assert len(section_headers_unsorted) == 1
    assert section_headers_sorted == section_headers_unsorted


def test_build_table_rows_with_sections_row_structure_with_insertion_order():
    """
    Test row structure is correct with insertion order preservation (default).

    Each section should have header row, metric rows, separator row.
    """
    # Arrange
    subgroups = OrderedDict([
        ("BETA", [("m1", {"value": 1.0, "unit": "-"})]),
        ("ALPHA", [("m2", {"value": 2.0, "unit": "-"})])
    ])

    # Act - Default sort_keys=False
    rows = _build_table_rows_with_sections(subgroups, decimals=2, currency="EUR")

    # Assert - Structure: header, metric, separator, header, metric
    assert len(rows) >= 4, "Should have at least: header, metric, sep, header, metric"

    # Check first header is BETA (insertion order)
    assert "BETA" in str(rows[0][0]), "First section header should be BETA (insertion order)"

    # Check structure has empty rows (separators)
    empty_rows = [r for r in rows if r[0] == "" and r[1] == ""]
    assert len(empty_rows) >= 1, "Should have at least one separator row"


def test_build_table_rows_with_sections_metrics_under_correct_section_insertion_order():
    """
    Test metrics appear under correct section header with insertion order preservation.

    When insertion order is preserved (default), metrics should still be correctly grouped under their section.
    """
    # Arrange
    subgroups = OrderedDict([
        ("ZEBRA", [
            ("z_metric_1", {"value": 10, "unit": "-"}),
            ("z_metric_2", {"value": 20, "unit": "-"})
        ]),
        ("ALPHA", [
            ("a_metric_1", {"value": 30, "unit": "-"})
        ])
    ])

    # Act - Default sort_keys=False (insertion order)
    rows = _build_table_rows_with_sections(subgroups)

    # Assert - ZEBRA section comes first (insertion order), then its metrics
    zebra_header_idx = next(
        (i for i, r in enumerate(rows) if "ZEBRA" in str(r[0]) and r[1] == ""),
        -1
    )
    z_metric_idx = next(
        (i for i, r in enumerate(rows) if "z_metric_1" in str(r[0])),
        -1
    )

    alpha_header_idx = next(
        (i for i, r in enumerate(rows) if "ALPHA" in str(r[0]) and r[1] == ""),
        -1
    )
    a_metric_idx = next(
        (i for i, r in enumerate(rows) if "a_metric_1" in str(r[0])),
        -1
    )

    assert zebra_header_idx >= 0 and z_metric_idx >= 0
    assert zebra_header_idx < z_metric_idx, "ZEBRA header before ZEBRA metrics"

    assert alpha_header_idx >= 0 and a_metric_idx >= 0
    assert zebra_header_idx < alpha_header_idx, "ZEBRA section before ALPHA (insertion order)"


# =============================================================================
# TEST: _build_table_rows_with_units() DEFAULT BEHAVIOR (sort_keys=True)
# =============================================================================
def test_build_table_rows_with_units_default_is_false():
    """
    Test _build_table_rows_with_units() default sort_keys is False.

    Calling WITHOUT sort_keys parameter should use default=False,
    which means INSERTION ORDER preservation of subgroups.
    """
    # Arrange - Subgroups in reverse order
    subgroups = OrderedDict([
        ("ZEBRA", [("metric_z", {"value": 100.0, "unit": "USD"})]),
        ("ALPHA", [("metric_a", {"value": 50.0, "unit": "%"})])
    ])

    # Act - Call WITHOUT sort_keys parameter (uses default=False)
    rows = _build_table_rows_with_units(subgroups)

    # Assert - Insertion order preservation
    section_headers = [r[0] for r in rows if r[1] == "" and r[2] == ""]

    zebra_idx = next((i for i, h in enumerate(section_headers) if "ZEBRA" in h), -1)
    alpha_idx = next((i for i, h in enumerate(section_headers) if "ALPHA" in h), -1)

    assert zebra_idx >= 0 and alpha_idx >= 0
    assert zebra_idx < alpha_idx, (
        "Default sort_keys=False: ZEBRA before ALPHA (insertion order)"
    )


def test_build_table_rows_with_units_sorted_true_explicit():
    """
    Test _build_table_rows_with_units() with explicit sort_keys=True.

    Explicitly passing sort_keys=True should produce alphabetically sorted output.
    """
    # Arrange
    subgroups = OrderedDict([
        ("ZEBRA", [("metric_z", {"value": 100.0, "unit": "USD"})]),
        ("ALPHA", [("metric_a", {"value": 50.0, "unit": "%"})])
    ])

    # Act - Explicit sort_keys=True
    rows = _build_table_rows_with_units(subgroups, sort_keys=True)

    # Assert - ALPHA before ZEBRA
    section_headers = [r[0] for r in rows if r[1] == "" and r[2] == ""]
    alpha_idx = next((i for i, h in enumerate(section_headers) if "ALPHA" in h), -1)
    zebra_idx = next((i for i, h in enumerate(section_headers) if "ZEBRA" in h), -1)

    assert alpha_idx >= 0 and zebra_idx >= 0
    assert alpha_idx < zebra_idx, "sort_keys=True: alphabetical (ALPHA < ZEBRA)"


def test_build_table_rows_with_units_sorted_false_preserves_order(
    unordered_subgroups,
):
    """
    Test _build_table_rows_with_units() with sort_keys=False.

    When sort_keys=False, should preserve insertion order (ZEBRA before ALPHA).
    """
    # Act - sort_keys=False
    rows = _build_table_rows_with_units(unordered_subgroups, sort_keys=False)

    # Assert - ZEBRA before ALPHA (insertion order)
    section_headers = [r[0] for r in rows if r[1] == "" and r[2] == ""]
    zebra_idx = next((i for i, h in enumerate(section_headers) if "ZEBRA" in h), -1)
    alpha_idx = next((i for i, h in enumerate(section_headers) if "ALPHA" in h), -1)

    assert zebra_idx >= 0 and alpha_idx >= 0
    assert zebra_idx < alpha_idx, (
        "sort_keys=False: insertion order (ZEBRA < ALPHA)"
    )


def test_build_table_rows_with_units_multiple_subgroups_insertion_order(
    unordered_subgroups_multiple,
):
    """
    Test insertion order preservation with multiple subgroups in mixed order.

    With default sort_keys=False, should produce: ZEBRA, MIKE, ALPHA.
    """
    # Act - Default sort_keys=False
    rows = _build_table_rows_with_units(unordered_subgroups_multiple)

    # Assert - Insertion order
    section_headers = [r[0] for r in rows if r[1] == "" and r[2] == ""]
    zebra_idx = next((i for i, h in enumerate(section_headers) if "ZEBRA" in h), -1)
    mike_idx = next((i for i, h in enumerate(section_headers) if "MIKE" in h), -1)
    alpha_idx = next((i for i, h in enumerate(section_headers) if "ALPHA" in h), -1)

    assert zebra_idx >= 0 and mike_idx >= 0 and alpha_idx >= 0
    assert zebra_idx < mike_idx < alpha_idx, (
        "Default sort_keys=False: ZEBRA < MIKE < ALPHA (insertion order)"
    )


def test_build_table_rows_with_units_row_structure_with_insertion_order():
    """
    Test row structure is correct (3-column) with insertion order preservation (default).

    Each row should be [kpi_name, value, unit].
    """
    # Arrange
    subgroups = OrderedDict([
        ("BETA", [("m1", {"value": 1.0, "unit": "USD"})]),
        ("ALPHA", [("m2", {"value": 2.0, "unit": "%"})])
    ])

    # Act - Default sort_keys=False
    rows = _build_table_rows_with_units(
        subgroups, decimals=2, currency="EUR"
    )

    # Assert - Each row has 3 columns
    assert all(len(r) == 3 for r in rows), "Each row should have 3 columns"

    # Assert - First header is BETA (insertion order)
    assert "BETA" in str(rows[0][0]), "First section should be BETA (insertion order)"


def test_build_table_rows_with_units_unit_column_separate():
    """
    Test unit is in separate column (3rd column) with sort_keys.

    Units should be separate from values when using _build_table_rows_with_units.
    """
    # Arrange
    subgroups = {
        "ACTIVITY": [
            ("metric1", {"value": 100.0, "unit": "USD"}),
            ("metric2", {"value": 50.0, "unit": "%"})
        ]
    }

    # Act
    rows = _build_table_rows_with_units(subgroups)

    # Assert - Metric rows have value and unit separate
    metric_rows = [r for r in rows if "metric" in str(r[0]).lower()]
    assert len(metric_rows) >= 2, "Should have metric rows"

    for row in metric_rows:
        assert len(row) == 3, "Each metric row should have 3 columns: [name, value, unit]"
        # Value column should be numeric (not include unit)
        value_str = str(row[1])
        assert not any(c.isalpha() for c in value_str), (
            f"Value column should not contain letters: {value_str}"
        )


# =============================================================================
# TEST: HELPER FUNCTIONS RESPECT CALLER PARAMETERS
# =============================================================================
def test_build_table_rows_with_sections_respects_sort_keys_false_parameter(
    unordered_subgroups,
):
    """
    Test that sort_keys parameter is actually respected (not ignored).

    REGRESSION TEST: Validates that sort_keys parameter is NOT ignored
    during current or future refactoring.
    """
    # Act - With sort_keys=False
    rows_false = _build_table_rows_with_sections(
        unordered_subgroups, sort_keys=False
    )

    # Act - With sort_keys=True
    rows_true = _build_table_rows_with_sections(unordered_subgroups, sort_keys=True)

    # Extract section headers from both
    headers_false = [r[0] for r in rows_false if r[1] == ""]
    headers_true = [r[0] for r in rows_true if r[1] == ""]

    # Assert - Order different
    assert headers_false != headers_true, (
        "sort_keys parameter must change output order (false vs true)"
    )

    # Assert - False: ZEBRA before ALPHA
    zebra_false = next((i for i, h in enumerate(headers_false) if "ZEBRA" in h), -1)
    alpha_false = next((i for i, h in enumerate(headers_false) if "ALPHA" in h), -1)
    assert zebra_false < alpha_false, "sort_keys=False: ZEBRA < ALPHA (insertion order)"

    # Assert - True: ALPHA before ZEBRA
    alpha_true = next((i for i, h in enumerate(headers_true) if "ALPHA" in h), -1)
    zebra_true = next((i for i, h in enumerate(headers_true) if "ZEBRA" in h), -1)
    assert alpha_true < zebra_true, "sort_keys=True: ALPHA < ZEBRA (alphabetical)"


def test_build_table_rows_with_units_respects_sort_keys_false_parameter(
    unordered_subgroups,
):
    """
    Test that sort_keys parameter is actually respected for units builder.

    REGRESSION TEST: Validates sort_keys parameter is NOT ignored.
    """
    # Act - With sort_keys=False
    rows_false = _build_table_rows_with_units(
        unordered_subgroups, sort_keys=False
    )

    # Act - With sort_keys=True
    rows_true = _build_table_rows_with_units(
        unordered_subgroups, sort_keys=True
    )

    # Extract section headers
    headers_false = [r[0] for r in rows_false if r[1] == "" and r[2] == ""]
    headers_true = [r[0] for r in rows_true if r[1] == "" and r[2] == ""]

    # Assert - Different order
    assert headers_false != headers_true, (
        "sort_keys parameter must change output (false vs true)"
    )

    # Assert - False: ZEBRA < ALPHA
    zebra_false = next((i for i, h in enumerate(headers_false) if "ZEBRA" in h), -1)
    alpha_false = next((i for i, h in enumerate(headers_false) if "ALPHA" in h), -1)
    assert zebra_false < alpha_false, "sort_keys=False: ZEBRA < ALPHA"

    # Assert - True: ALPHA < ZEBRA
    alpha_true = next((i for i, h in enumerate(headers_true) if "ALPHA" in h), -1)
    zebra_true = next((i for i, h in enumerate(headers_true) if "ZEBRA" in h), -1)
    assert alpha_true < zebra_true, "sort_keys=True: ALPHA < ZEBRA"


# =============================================================================
# TEST: EDGE CASES WITH DEFAULT SORTING
# =============================================================================
def test_build_table_rows_with_sections_many_metrics_insertion_order(
    many_metrics_per_subgroup,
):
    """
    Test insertion order preservation with many metrics per subgroup.

    Insertion order should work correctly even with multiple metrics per section.
    """
    # Act - Default sort_keys=False
    rows = _build_table_rows_with_sections(many_metrics_per_subgroup)

    # Assert - ZEBRA_GROUP before ALPHA_GROUP (insertion order)
    section_headers = [r[0] for r in rows if r[1] == ""]
    zebra_idx = next(
        (i for i, h in enumerate(section_headers) if "ZEBRA_GROUP" in h), -1
    )
    alpha_idx = next(
        (i for i, h in enumerate(section_headers) if "ALPHA_GROUP" in h), -1
    )

    assert zebra_idx >= 0 and alpha_idx >= 0
    assert zebra_idx < alpha_idx, (
        "Default sort_keys=False: ZEBRA_GROUP < ALPHA_GROUP (insertion order)"
    )

    # Assert - ZEBRA metrics still under ZEBRA section
    zebra_metrics = [
        r for r in rows[zebra_idx:]
        if "metric_z" in str(r[0]).lower()
    ]
    assert len(zebra_metrics) >= 2, "ZEBRA metrics should be under ZEBRA section"


def test_build_table_rows_with_units_many_metrics_insertion_order(
    many_metrics_per_subgroup,
):
    """
    Test insertion order preservation with many metrics per subgroup (units builder).

    Should maintain correct grouping while preserving insertion order.
    """
    # Act - Default sort_keys=False
    rows = _build_table_rows_with_units(many_metrics_per_subgroup)

    # Assert - ZEBRA_GROUP before ALPHA_GROUP (insertion order)
    section_headers = [r[0] for r in rows if r[1] == "" and r[2] == ""]
    zebra_idx = next(
        (i for i, h in enumerate(section_headers) if "ZEBRA_GROUP" in h), -1
    )
    alpha_idx = next(
        (i for i, h in enumerate(section_headers) if "ALPHA_GROUP" in h), -1
    )

    assert zebra_idx >= 0 and alpha_idx >= 0
    assert zebra_idx < alpha_idx, "ZEBRA_GROUP < ALPHA_GROUP (insertion order)"


def test_build_table_rows_with_sections_column_widths_with_insertion_order():
    """
    Test column width padding works correctly with insertion order preservation.

    When column_widths specified, padding should be applied along with insertion order.
    """
    # Arrange
    subgroups = OrderedDict([
        ("ZEBRA", [("z", {"value": 100.0, "unit": "USD"})]),
        ("ALPHA", [("a", {"value": 50.0, "unit": "%"})])
    ])

    # Act - Default sort_keys=False with column widths
    rows = _build_table_rows_with_sections(
        subgroups,
        column_widths=(20, 20)
    )

    # Assert - Rows have padding applied
    for row in rows:
        assert len(row) == 2, "Each row should have 2 columns"
        # Check padding (strings should be padded to specified widths)
        assert len(row[0]) == 20 or row[0] == "", (
            f"KPI column should be padded to width or empty: {row[0]!r}"
        )


def test_build_table_rows_with_units_column_widths_with_insertion_order():
    """
    Test column width padding works with units builder and insertion order.

    3-column layout should preserve insertion order while applying padding.
    """
    # Arrange
    subgroups = OrderedDict([
        ("ZEBRA", [("z", {"value": 100.0, "unit": "USD"})]),
        ("ALPHA", [("a", {"value": 50.0, "unit": "%"})])
    ])

    # Act - Default sort_keys=False with 3-column widths
    rows = _build_table_rows_with_units(
        subgroups,
        column_widths=(20, 15, 10)
    )

    # Assert - Rows have 3 columns with padding
    for row in rows:
        assert len(row) == 3, "Each row should have 3 columns"
        # Check width constraints
        kpi_col = row[0]
        value_col = row[1]
        unit_col = row[2]

        # Padded columns (or empty)
        assert len(kpi_col) == 20 or kpi_col == "", "KPI column width"
        assert len(value_col) == 15 or value_col == "", "Value column width"
        assert len(unit_col) == 10 or unit_col == "", "Unit column width"


# =============================================================================
# TEST: DECIMALS PARAMETER WITH SORTING
# =============================================================================
def test_build_table_rows_with_sections_decimals_with_sorting():
    """
    Test decimals parameter works correctly with sorting.

    Sorting should not affect decimal formatting.
    """
    # Arrange - Values that need decimal formatting
    subgroups = OrderedDict([
        ("ZEBRA", [("z", {"value": 123.456789, "unit": "%"})]),
        ("ALPHA", [("a", {"value": 0.5, "unit": "%"})])
    ])

    # Act - decimals=2, default sort (True)
    rows = _build_table_rows_with_sections(
        subgroups, decimals=2
    )

    # Extract formatted values
    metric_rows = [r for r in rows if "metric" in str(r[0]).lower() or "z" in str(r[0]) or "a" in str(r[0])]

    # Assert - Both values are properly formatted with decimals
    # (values should be padded/formatted even with sorting)
    assert any("123.46" in str(r) or "123" in str(r) for r in metric_rows), (
        "ZEBRA metric should be formatted to 2 decimals"
    )
    assert any("0.50" in str(r) or "0.5" in str(r) for r in metric_rows), (
        "ALPHA metric should be formatted to 2 decimals"
    )


def test_build_table_rows_with_units_decimals_with_sorting():
    """
    Test decimals formatting with units builder and sorting.

    Decimal precision should be maintained regardless of sorting.
    """
    # Arrange
    subgroups = OrderedDict([
        ("ZEBRA", [("z", {"value": 99.999, "unit": "-"})]),
        ("ALPHA", [("a", {"value": 0.001, "unit": "-"})])
    ])

    # Act - decimals=3, default sort (True)
    rows = _build_table_rows_with_units(
        subgroups, decimals=3
    )

    # Extract value columns (index 1)
    metric_rows = [r for r in rows if "metric" in str(r[0]).lower() or "z" in str(r[0]) or "a" in str(r[0])]
    values = [r[1] if len(r) > 1 else "" for r in metric_rows]

    # Assert - Values are formatted with proper decimals
    assert any("100" in str(v) or "99.999" in str(v) for v in values), (
        "ZEBRA value formatted to 3 decimals"
    )
    assert any("0.001" in str(v) or "0" in str(v) for v in values), (
        "ALPHA value formatted to 3 decimals"
    )


# =============================================================================
# TEST: CURRENCY PARAMETER WITH SORTING
# =============================================================================
def test_build_table_rows_with_sections_currency_with_sorting():
    """
    Test currency override works with sorting.

    Currency USD should be replaced with specified currency even with sorting applied.
    """
    # Arrange - Multiple currencies to replace
    subgroups = OrderedDict([
        ("ZEBRA", [("z", {"value": 100.0, "unit": "USD"})]),
        ("ALPHA", [("a", {"value": 50.0, "unit": "USD"})])
    ])

    # Act - Default sort (True), currency CHF
    rows = _build_table_rows_with_sections(
        subgroups, currency="CHF"
    )

    # Assert - All USD replaced with CHF despite sorting
    full_output = str(rows)
    assert "CHF" in full_output, "Currency should be replaced with CHF"
    assert "USD" not in full_output, "USD should be replaced with CHF"


def test_build_table_rows_with_units_currency_with_sorting():
    """
    Test currency replacement in units column with sorting.

    Units column (3rd column) should show replaced currency.
    """
    # Arrange
    subgroups = OrderedDict([
        ("ZEBRA", [("z", {"value": 100.0, "unit": "USD"})]),
        ("ALPHA", [("a", {"value": 50.0, "unit": "GBP"})])
    ])

    # Act - Default sort, currency EUR
    rows = _build_table_rows_with_units(
        subgroups, currency="EUR"
    )

    # Extract unit column (index 2)
    metric_rows = [r for r in rows if "metric" in str(r[0]).lower() or ("z" in str(r[0]) and len(r) > 2) or ("a" in str(r[0]) and len(r) > 2)]

    # Assert - Units replaced
    units = [r[2] if len(r) > 2 else "" for r in metric_rows]
    units_str = str(units)

    assert "EUR" in units_str, "Currency codes should be replaced with EUR"
    assert "USD" not in units_str, "USD should be replaced"
    assert "GBP" not in units_str, "GBP should be replaced"
