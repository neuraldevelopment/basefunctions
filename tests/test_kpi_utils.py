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
 v1.1 : Update all tests to use KPIValue format (Breaking Change)
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
        "returns.total": {"value": 0.15, "unit": None},
        "returns.annualized": {"value": 0.12, "unit": "%"},
        "risk.volatility": {"value": 0.08, "unit": "%"},
        "risk.sharpe": {"value": 1.5, "unit": None},
    }
    expected = {
        "returns": {
            "total": {"value": 0.15, "unit": None},
            "annualized": {"value": 0.12, "unit": "%"},
        },
        "risk": {
            "volatility": {"value": 0.08, "unit": "%"},
            "sharpe": {"value": 1.5, "unit": None},
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
        "performance.z_metric": {"value": 3.0, "unit": None},
        "performance.y_metric": {"value": 2.0, "unit": None},
        "performance.x_metric": {"value": 1.0, "unit": None},
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
        "portfoliofunctions.activity.total_trades": {"value": 150.0, "unit": None},
        "portfoliofunctions.activity.avg_trade_size": {"value": 5000.0, "unit": "USD"},
        "portfoliofunctions.activity.max_position": {"value": 25000.0, "unit": "USD"},
        "portfoliofunctions.returns.total": {"value": 0.18, "unit": "%"},
        "portfoliofunctions.returns.sharpe": {"value": 1.8, "unit": None},
    }
    expected = {
        "portfoliofunctions": {
            "activity": {
                "total_trades": {"value": 150.0, "unit": None},
                "avg_trade_size": {"value": 5000.0, "unit": "USD"},
                "max_position": {"value": 25000.0, "unit": "USD"},
            },
            "returns": {
                "total": {"value": 0.18, "unit": "%"},
                "sharpe": {"value": 1.8, "unit": None},
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
        "total_value": {"value": 100000.0, "unit": "USD"},
        "total_count": {"value": 50.0, "unit": None},
    }
    expected = {
        "total_value": {"value": 100000.0, "unit": "USD"},
        "total_count": {"value": 50.0, "unit": None},
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
        "total": {"value": 100.0, "unit": "USD"},
        "performance.return": {"value": 0.15, "unit": "%"},
        "performance.risk": {"value": 0.08, "unit": "%"},
        "count": {"value": 50.0, "unit": None},
    }
    expected = {
        "total": {"value": 100.0, "unit": "USD"},
        "performance": {
            "return": {"value": 0.15, "unit": "%"},
            "risk": {"value": 0.08, "unit": "%"},
        },
        "count": {"value": 50.0, "unit": None},
    }

    # Act
    result = group_kpis_by_name(kpis)

    # Assert
    assert result == expected, "Mixed single/nested levels must coexist"


def test_preserves_kpi_value_structure() -> None:
    """
    Test that KPIValue structure is preserved during grouping.

    Given KPIs with KPIValue format (dict with value and unit),
    When group_kpis_by_name() is called,
    Then KPIValue structure is preserved at all levels.
    """
    # Arrange
    kpis = {
        "stats.count": {"value": 100.0, "unit": None},
        "stats.average": {"value": 15.5, "unit": "%"},
        "stats.total": {"value": 1000.0, "unit": "USD"},
        "stats.ratio": {"value": 0.42, "unit": None},
    }

    # Act
    result = group_kpis_by_name(kpis)

    # Assert
    assert result["stats"]["count"] == {"value": 100.0, "unit": None}, "KPIValue with unit=None must be preserved"
    assert result["stats"]["average"] == {"value": 15.5, "unit": "%"}, "KPIValue with unit='%' must be preserved"
    assert result["stats"]["total"] == {"value": 1000.0, "unit": "USD"}, "KPIValue with unit='USD' must be preserved"
    assert result["stats"]["ratio"] == {"value": 0.42, "unit": None}, "KPIValue structure must be preserved"


def test_sort_keys_alphabetically() -> None:
    """
    Test sort_keys=True sorts keys alphabetically at all levels.

    Given KPIs with reverse alphabetical order,
    When group_kpis_by_name(sort_keys=True) is called,
    Then keys are sorted alphabetically at all nesting levels.
    """
    # Arrange
    kpis = {
        "performance.z_metric": {"value": 3.0, "unit": None},
        "performance.y_metric": {"value": 2.0, "unit": "%"},
        "performance.x_metric": {"value": 1.0, "unit": None},
        "activity.total": {"value": 100.0, "unit": None},
        "activity.count": {"value": 50.0, "unit": None},
    }

    # Act
    result = group_kpis_by_name(kpis, sort_keys=True)

    # Assert - top level should be alphabetical
    top_level_keys = list(result.keys())
    assert top_level_keys == ["activity", "performance"], (
        f"Top level keys must be sorted alphabetically, got {top_level_keys}"
    )

    # Assert - nested level should be alphabetical
    performance_keys = list(result["performance"].keys())
    assert performance_keys == ["x_metric", "y_metric", "z_metric"], (
        f"Nested keys must be sorted alphabetically, got {performance_keys}"
    )

    activity_keys = list(result["activity"].keys())
    assert activity_keys == ["count", "total"], (
        f"Nested keys must be sorted alphabetically, got {activity_keys}"
    )


def test_sort_keys_deep_nesting() -> None:
    """
    Test sort_keys=True with deep nesting (3+ levels).

    Given KPIs with 3-level nesting in reverse alphabetical order,
    When group_kpis_by_name(sort_keys=True) is called,
    Then all levels are sorted alphabetically.
    """
    # Arrange
    kpis = {
        "portfoliofunctions.returns.total": {"value": 0.18, "unit": "%"},
        "portfoliofunctions.returns.sharpe": {"value": 1.8, "unit": None},
        "portfoliofunctions.activity.total_trades": {"value": 150.0, "unit": None},
        "portfoliofunctions.activity.avg_trade_size": {"value": 5000.0, "unit": "USD"},
    }

    # Act
    result = group_kpis_by_name(kpis, sort_keys=True)

    # Assert - level 2 should be sorted
    level2_keys = list(result["portfoliofunctions"].keys())
    assert level2_keys == ["activity", "returns"], (
        f"Level 2 keys must be sorted alphabetically, got {level2_keys}"
    )

    # Assert - level 3 should be sorted
    activity_keys = list(result["portfoliofunctions"]["activity"].keys())
    assert activity_keys == ["avg_trade_size", "total_trades"], (
        f"Level 3 activity keys must be sorted alphabetically, got {activity_keys}"
    )

    returns_keys = list(result["portfoliofunctions"]["returns"].keys())
    assert returns_keys == ["sharpe", "total"], (
        f"Level 3 returns keys must be sorted alphabetically, got {returns_keys}"
    )


def test_sort_keys_default_false_preserves_order() -> None:
    """
    Test backward compatibility - default sort_keys=False preserves insertion order.

    Given KPIs with reverse alphabetical order,
    When group_kpis_by_name() is called without sort_keys parameter,
    Then insertion order is preserved (backward compatible).
    """
    # Arrange
    kpis = {
        "performance.z_metric": {"value": 3.0, "unit": None},
        "performance.y_metric": {"value": 2.0, "unit": "%"},
        "performance.x_metric": {"value": 1.0, "unit": None},
    }

    # Act
    result = group_kpis_by_name(kpis)  # No sort_keys parameter

    # Assert - insertion order must be preserved
    result_keys = list(result["performance"].keys())
    expected_keys = ["z_metric", "y_metric", "x_metric"]
    assert result_keys == expected_keys, (
        f"Default behavior must preserve insertion order - Expected {expected_keys}, got {result_keys}"
    )


def test_kpi_values_with_different_units() -> None:
    """
    Test KPIValue format with various unit types.

    Given KPIs with different units (%, USD, None),
    When group_kpis_by_name() is called,
    Then all units are preserved correctly.
    """
    # Arrange
    kpis = {
        "performance.win_rate": {"value": 0.60, "unit": "%"},
        "performance.total_pnl": {"value": 319.0, "unit": "USD"},
        "performance.trade_count": {"value": 5.0, "unit": None},
        "risk.volatility": {"value": 0.08, "unit": "%"},
    }

    # Act
    result = group_kpis_by_name(kpis)

    # Assert
    assert result["performance"]["win_rate"] == {"value": 0.60, "unit": "%"}, "Win rate with % unit must be preserved"
    assert result["performance"]["total_pnl"] == {"value": 319.0, "unit": "USD"}, "Total PnL with USD unit must be preserved"
    assert result["performance"]["trade_count"] == {"value": 5.0, "unit": None}, "Trade count with None unit must be preserved"
    assert result["risk"]["volatility"] == {"value": 0.08, "unit": "%"}, "Volatility with % unit must be preserved"
