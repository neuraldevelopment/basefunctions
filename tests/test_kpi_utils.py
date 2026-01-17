"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Tests for KPI utility functions - group_kpis_by_name()
 Log:
 v1.0 : Initial TDD implementation (RED phase - function does not exist yet)
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
# Standard Library
from typing import Any

# Project modules
from basefunctions.kpi.utils import group_kpis_by_name


# =============================================================================
# TEST CASES
# =============================================================================


def test_group_flat_kpis_into_nested_structure() -> None:
    """
    Test basic 2-level nesting from flat dot-separated names.

    Given flat KPI dict with dot-separated names (e.g., "category.metric"),
    When group_kpis_by_name() is called,
    Then return nested dict preserving structure.
    """
    # Arrange
    kpis = {
        "returns.total": 0.15,
        "returns.annualized": 0.12,
        "risk.volatility": 0.08,
        "risk.sharpe": 1.5,
    }
    expected = {
        "returns": {
            "total": 0.15,
            "annualized": 0.12,
        },
        "risk": {
            "volatility": 0.08,
            "sharpe": 1.5,
        },
    }

    # Act
    result = group_kpis_by_name(kpis)

    # Assert
    assert result == expected, "Nested structure must match expected grouping"


def test_preserves_insertion_order_within_groups() -> None:
    """
    Test CRITICAL requirement - insertion order preservation within groups.

    Given KPIs with reverse alphabetical order within group,
    When group_kpis_by_name() is called,
    Then insertion order MUST be preserved (NOT alphabetical).
    """
    # Arrange
    kpis = {
        "performance.z_metric": 3.0,
        "performance.y_metric": 2.0,
        "performance.x_metric": 1.0,
    }

    # Act
    result = group_kpis_by_name(kpis)

    # Assert
    assert "performance" in result, "Group 'performance' must exist"
    # CRITICAL: Order must be z, y, x (insertion order, NOT alphabetical)
    result_keys = list(result["performance"].keys())
    expected_keys = ["z_metric", "y_metric", "x_metric"]
    assert result_keys == expected_keys, (
        f"Order preservation FAILED - Expected {expected_keys}, got {result_keys}. "
        "Insertion order MUST be preserved!"
    )


def test_deep_nesting_three_levels() -> None:
    """
    Test 3+ level nesting with real-world portfoliofunctions structure.

    Given KPIs with 3-level dot-separated names,
    When group_kpis_by_name() is called,
    Then return deeply nested dict structure.
    """
    # Arrange
    kpis = {
        "portfoliofunctions.activity.total_trades": 150,
        "portfoliofunctions.activity.avg_trade_size": 5000.0,
        "portfoliofunctions.activity.max_position": 25000.0,
        "portfoliofunctions.returns.total": 0.18,
        "portfoliofunctions.returns.sharpe": 1.8,
    }
    expected = {
        "portfoliofunctions": {
            "activity": {
                "total_trades": 150,
                "avg_trade_size": 5000.0,
                "max_position": 25000.0,
            },
            "returns": {
                "total": 0.18,
                "sharpe": 1.8,
            },
        },
    }

    # Act
    result = group_kpis_by_name(kpis)

    # Assert
    assert result == expected, "Deep nesting (3 levels) must work correctly"


def test_empty_dict_returns_empty() -> None:
    """
    Test edge case - empty input dict.

    Given empty KPI dict,
    When group_kpis_by_name() is called,
    Then return empty dict (no error).
    """
    # Arrange
    kpis: dict[str, Any] = {}

    # Act
    result = group_kpis_by_name(kpis)

    # Assert
    assert result == {}, "Empty input must return empty dict"


def test_single_level_stays_flat() -> None:
    """
    Test KPIs without dots remain at top level.

    Given KPIs with no dots in names,
    When group_kpis_by_name() is called,
    Then keys remain at top level (no nesting).
    """
    # Arrange
    kpis = {
        "total_value": 100000.0,
        "total_count": 50,
    }
    expected = {
        "total_value": 100000.0,
        "total_count": 50,
    }

    # Act
    result = group_kpis_by_name(kpis)

    # Assert
    assert result == expected, "Single-level KPIs must remain flat"


def test_mixed_single_and_nested_levels() -> None:
    """
    Test mixture of flat and nested KPI names.

    Given mix of single-level and multi-level KPI names,
    When group_kpis_by_name() is called,
    Then both types coexist in result.
    """
    # Arrange
    kpis = {
        "total": 100.0,
        "performance.return": 0.15,
        "performance.risk": 0.08,
        "count": 50,
    }
    expected = {
        "total": 100.0,
        "performance": {
            "return": 0.15,
            "risk": 0.08,
        },
        "count": 50,
    }

    # Act
    result = group_kpis_by_name(kpis)

    # Assert
    assert result == expected, "Mixed single/nested levels must coexist"


def test_preserves_value_types() -> None:
    """
    Test that value types are preserved during grouping.

    Given KPIs with various value types (int, float, str, None),
    When group_kpis_by_name() is called,
    Then all value types are preserved.
    """
    # Arrange
    kpis = {
        "stats.count": 100,
        "stats.average": 15.5,
        "stats.status": "active",
        "stats.optional": None,
    }

    # Act
    result = group_kpis_by_name(kpis)

    # Assert
    assert result["stats"]["count"] == 100, "int type must be preserved"
    assert result["stats"]["average"] == 15.5, "float type must be preserved"
    assert result["stats"]["status"] == "active", "str type must be preserved"
    assert result["stats"]["optional"] is None, "None type must be preserved"
