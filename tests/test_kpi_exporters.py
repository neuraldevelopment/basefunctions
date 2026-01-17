"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Tests for KPI exporter functions - KPIValue format support with units
 Log:
 v1.0 : Initial implementation - comprehensive KPIValue format tests
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
# Standard Library
from datetime import datetime
from typing import Any, Dict, List, Tuple

# Third-party
import pytest

# Project modules
from basefunctions.kpi.exporters import (
    _flatten_dict,
    _format_unit_suffix,
    export_by_category,
    export_business_technical_split,
    export_to_dataframe,
)


# =============================================================================
# TEST CASES
# =============================================================================


def test_export_kpi_value_format_without_unit_suffix() -> None:
    """
    Test export_to_dataframe() with KPIValue format, no unit suffixes.

    Given KPI history with KPIValue format {"value": x, "unit": y},
    When export_to_dataframe() is called with include_units_in_columns=False,
    Then DataFrame has plain column names (no unit suffixes).
    """
    # Arrange
    history: List[Tuple[datetime, Dict[str, Any]]] = [
        (
            datetime.now(),
            {
                "portfolio": {
                    "balance": {"value": 100.0, "unit": "USD"},
                    "count": {"value": 5.0, "unit": None},
                }
            },
        )
    ]

    # Act
    df = export_to_dataframe(history, include_units_in_columns=False)

    # Assert
    assert "portfolio.balance" in df.columns, "Plain column name without unit suffix must exist"
    assert "portfolio.count" in df.columns, "Plain column name for None unit must exist"
    assert df["portfolio.balance"].iloc[0] == 100.0, "Value must be extracted correctly"
    assert df["portfolio.count"].iloc[0] == 5.0, "Value must be extracted correctly"


def test_export_kpi_value_format_with_unit_suffix() -> None:
    """
    Test export_to_dataframe() with KPIValue format, unit suffixes enabled.

    Given KPI history with KPIValue format {"value": x, "unit": y},
    When export_to_dataframe() is called with include_units_in_columns=True,
    Then DataFrame has column names with unit suffixes (e.g., "balance_USD").
    """
    # Arrange
    history: List[Tuple[datetime, Dict[str, Any]]] = [
        (
            datetime.now(),
            {
                "portfolio": {
                    "balance": {"value": 100.0, "unit": "USD"},
                    "volatility": {"value": 0.15, "unit": "%"},
                }
            },
        )
    ]

    # Act
    df = export_to_dataframe(history, include_units_in_columns=True)

    # Assert
    assert "portfolio.balance_USD" in df.columns, "Column name with USD suffix must exist"
    assert "portfolio.volatility_pct" in df.columns, "Column name with _pct suffix for % unit must exist"
    assert df["portfolio.balance_USD"].iloc[0] == 100.0, "Value must be extracted correctly"
    assert df["portfolio.volatility_pct"].iloc[0] == 0.15, "Value must be extracted correctly"


def test_unit_suffix_formatting_special_cases() -> None:
    """
    Test _format_unit_suffix() with special unit strings.

    Given various unit strings (%, USD, MB, s, None),
    When _format_unit_suffix() is called,
    Then correct suffixes are returned (% → _pct, others → _{unit}).
    """
    # Arrange & Act & Assert
    assert _format_unit_suffix("%") == "_pct", "Percent sign must be converted to _pct"
    assert _format_unit_suffix("USD") == "_USD", "USD must have _USD suffix"
    assert _format_unit_suffix("MB") == "_MB", "MB must have _MB suffix"
    assert _format_unit_suffix("s") == "_s", "Single letter unit must have underscore suffix"
    assert _format_unit_suffix("EUR") == "_EUR", "EUR must have _EUR suffix"


def test_export_mixed_units() -> None:
    """
    Test KPIs with different units in same history entry.

    Given KPIs with mixed units (USD, %, None),
    When export_to_dataframe() is called with include_units_in_columns=True,
    Then all units are correctly formatted in column names.
    """
    # Arrange
    history: List[Tuple[datetime, Dict[str, Any]]] = [
        (
            datetime.now(),
            {
                "portfolio": {
                    "balance": {"value": 100.0, "unit": "USD"},
                    "volatility": {"value": 0.15, "unit": "%"},
                    "count": {"value": 5.0, "unit": None},
                }
            },
        )
    ]

    # Act
    df = export_to_dataframe(history, include_units_in_columns=True)

    # Assert
    assert "portfolio.balance_USD" in df.columns, "USD unit must be in column name"
    assert "portfolio.volatility_pct" in df.columns, "Percent must be converted to _pct"
    assert "portfolio.count" in df.columns, "None unit must NOT add suffix"
    assert "portfolio.count_None" not in df.columns, "None unit must NOT result in _None suffix"


def test_backward_compatibility_plain_values() -> None:
    """
    Test export still works with plain float/int values (pre-KPIValue format).

    Given KPI history with plain numeric values (old format),
    When export_to_dataframe() is called,
    Then DataFrame is created successfully without errors.
    """
    # Arrange - old format without KPIValue structure
    history: List[Tuple[datetime, Dict[str, Any]]] = [
        (datetime.now(), {"portfolio": {"balance": 100.0, "count": 5.0}})
    ]

    # Act
    df = export_to_dataframe(history, include_units_in_columns=False)

    # Assert
    assert "portfolio.balance" in df.columns, "Plain value must work without KPIValue format"
    assert "portfolio.count" in df.columns, "Plain value must work without KPIValue format"
    assert df["portfolio.balance"].iloc[0] == 100.0, "Plain value must be extracted correctly"
    assert df["portfolio.count"].iloc[0] == 5.0, "Plain value must be extracted correctly"


def test_no_suffix_when_unit_is_none() -> None:
    """
    Test that unit=None does not add suffix to column name.

    Given KPIValue with unit=None,
    When export_to_dataframe() is called with include_units_in_columns=True,
    Then column name has NO suffix (not "_None").
    """
    # Arrange
    history: List[Tuple[datetime, Dict[str, Any]]] = [
        (datetime.now(), {"stats": {"count": {"value": 5.0, "unit": None}}})
    ]

    # Act
    df = export_to_dataframe(history, include_units_in_columns=True)

    # Assert
    assert "stats.count" in df.columns, "Column name must NOT have suffix for None unit"
    assert "stats.count_None" not in df.columns, "None unit must NOT result in _None suffix"
    assert df["stats.count"].iloc[0] == 5.0, "Value must be extracted correctly"


def test_export_by_category_with_kpi_value_format() -> None:
    """
    Test export_by_category() with KPIValue format and unit suffixes.

    Given KPI history with business/technical KPIs in KPIValue format,
    When export_by_category() is called with include_units_in_columns=True,
    Then filtered DataFrame has correct columns with unit suffixes.
    """
    # Arrange
    history: List[Tuple[datetime, Dict[str, Any]]] = [
        (
            datetime.now(),
            {
                "business.revenue": {"value": 1000.0, "unit": "USD"},
                "business.orders": {"value": 50.0, "unit": None},
                "technical.cpu_usage": {"value": 50.0, "unit": "%"},
                "technical.memory": {"value": 512.0, "unit": "MB"},
            },
        )
    ]

    # Act
    df = export_by_category(history, "business", include_units_in_columns=True)

    # Assert
    assert "business.revenue_USD" in df.columns, "Business KPI with USD unit must be present"
    assert "business.orders" in df.columns, "Business KPI with None unit must be present (no suffix)"
    assert "technical.cpu_usage_pct" not in df.columns, "Technical KPI must NOT be in business DataFrame"
    assert df["business.revenue_USD"].iloc[0] == 1000.0, "Value must be extracted correctly"
    assert df["business.orders"].iloc[0] == 50.0, "Value must be extracted correctly"


def test_export_business_technical_split_with_units() -> None:
    """
    Test export_business_technical_split() with unit suffixes.

    Given KPI history with mixed business/technical KPIs,
    When export_business_technical_split() is called with include_units_in_columns=True,
    Then both DataFrames have correct unit suffixes.
    """
    # Arrange
    history: List[Tuple[datetime, Dict[str, Any]]] = [
        (
            datetime.now(),
            {
                "business.revenue": {"value": 1000.0, "unit": "USD"},
                "business.orders": {"value": 50.0, "unit": None},
                "technical.cpu_usage": {"value": 50.0, "unit": "%"},
                "technical.memory": {"value": 512.0, "unit": "MB"},
            },
        )
    ]

    # Act
    business_df, technical_df = export_business_technical_split(
        history, include_units_in_columns=True
    )

    # Assert - Business DataFrame
    assert "business.revenue_USD" in business_df.columns, "Business revenue with USD unit must be present"
    assert "business.orders" in business_df.columns, "Business orders with None unit must be present (no suffix)"
    assert business_df["business.revenue_USD"].iloc[0] == 1000.0, "Business value must be correct"

    # Assert - Technical DataFrame
    assert "technical.cpu_usage_pct" in technical_df.columns, "Technical CPU with _pct unit must be present"
    assert "technical.memory_MB" in technical_df.columns, "Technical memory with MB unit must be present"
    assert technical_df["technical.cpu_usage_pct"].iloc[0] == 50.0, "Technical value must be correct"


def test_deep_nesting_with_kpi_value_format() -> None:
    """
    Test deeply nested KPIs (3+ levels) with KPIValue format.

    Given KPI history with 3+ nesting levels using KPIValue format,
    When export_to_dataframe() is called,
    Then flattening works correctly with dot notation.
    """
    # Arrange
    history: List[Tuple[datetime, Dict[str, Any]]] = [
        (
            datetime.now(),
            {
                "portfoliofunctions": {
                    "activity": {
                        "total_trades": {"value": 150.0, "unit": None},
                        "avg_trade_size": {"value": 5000.0, "unit": "USD"},
                    },
                    "returns": {
                        "total": {"value": 0.18, "unit": "%"},
                        "sharpe": {"value": 1.8, "unit": None},
                    },
                }
            },
        )
    ]

    # Act
    df = export_to_dataframe(history, include_units_in_columns=True)

    # Assert
    assert "portfoliofunctions.activity.total_trades" in df.columns, "Deep nesting (3 levels) must work"
    assert "portfoliofunctions.activity.avg_trade_size_USD" in df.columns, "Deep nesting with unit suffix must work"
    assert "portfoliofunctions.returns.total_pct" in df.columns, "Deep nesting with % unit must work"
    assert "portfoliofunctions.returns.sharpe" in df.columns, "Deep nesting with None unit must work (no suffix)"
    assert df["portfoliofunctions.activity.total_trades"].iloc[0] == 150.0, "Value must be correct"
    assert df["portfoliofunctions.activity.avg_trade_size_USD"].iloc[0] == 5000.0, "Value must be correct"


def test_empty_history_raises_value_error() -> None:
    """
    Test that empty history raises ValueError.

    Given empty history list,
    When export_to_dataframe() is called,
    Then ValueError is raised with clear message.
    """
    # Arrange
    history: List[Tuple[datetime, Dict[str, Any]]] = []

    # Act & Assert
    with pytest.raises(ValueError, match="History ist leer"):
        export_to_dataframe(history)


def test_flatten_dict_with_kpi_value_format() -> None:
    """
    Test _flatten_dict() helper with KPIValue format directly.

    Given nested dict with KPIValue format,
    When _flatten_dict() is called,
    Then flattening works correctly with optional unit suffixes.
    """
    # Arrange
    kpis = {
        "portfolio": {
            "balance": {"value": 100.0, "unit": "USD"},
            "count": {"value": 5.0, "unit": None},
        }
    }

    # Act - without units in columns
    result_plain = _flatten_dict(kpis, include_units_in_columns=False)

    # Assert - plain column names
    assert "portfolio.balance" in result_plain, "Plain column name must exist"
    assert "portfolio.count" in result_plain, "Plain column name must exist"
    assert result_plain["portfolio.balance"] == 100.0, "Value must be extracted correctly"

    # Act - with units in columns
    result_with_units = _flatten_dict(kpis, include_units_in_columns=True)

    # Assert - column names with unit suffixes
    assert "portfolio.balance_USD" in result_with_units, "Column name with USD suffix must exist"
    assert "portfolio.count" in result_with_units, "Column name for None unit must exist (no suffix)"
    assert result_with_units["portfolio.balance_USD"] == 100.0, "Value must be extracted correctly"


def test_multiple_timestamps_with_kpi_value_format() -> None:
    """
    Test export with multiple timestamps using KPIValue format.

    Given KPI history with multiple timestamps,
    When export_to_dataframe() is called,
    Then DataFrame has correct shape and all timestamps.
    """
    # Arrange
    ts1 = datetime(2025, 1, 1, 10, 0, 0)
    ts2 = datetime(2025, 1, 1, 11, 0, 0)
    ts3 = datetime(2025, 1, 1, 12, 0, 0)

    history: List[Tuple[datetime, Dict[str, Any]]] = [
        (ts1, {"portfolio": {"balance": {"value": 100.0, "unit": "USD"}}}),
        (ts2, {"portfolio": {"balance": {"value": 105.0, "unit": "USD"}}}),
        (ts3, {"portfolio": {"balance": {"value": 110.0, "unit": "USD"}}}),
    ]

    # Act
    df = export_to_dataframe(history, include_units_in_columns=True)

    # Assert
    assert len(df) == 3, "DataFrame must have 3 rows for 3 timestamps"
    assert df.index.name == "timestamp", "Index must be named 'timestamp'"
    assert list(df.index) == [ts1, ts2, ts3], "Timestamps must match history"
    assert list(df["portfolio.balance_USD"]) == [100.0, 105.0, 110.0], "Values must match history order"


def test_export_by_category_without_unit_suffix() -> None:
    """
    Test export_by_category() with KPIValue format, no unit suffixes.

    Given KPI history with business/technical KPIs in KPIValue format,
    When export_by_category() is called with include_units_in_columns=False,
    Then filtered DataFrame has plain column names (no unit suffixes).
    """
    # Arrange
    history: List[Tuple[datetime, Dict[str, Any]]] = [
        (
            datetime.now(),
            {
                "business.revenue": {"value": 1000.0, "unit": "USD"},
                "technical.cpu_usage": {"value": 50.0, "unit": "%"},
            },
        )
    ]

    # Act
    df = export_by_category(history, "business", include_units_in_columns=False)

    # Assert
    assert "business.revenue" in df.columns, "Plain column name without unit suffix must exist"
    assert "business.revenue_USD" not in df.columns, "Column name with USD suffix must NOT exist"
    assert df["business.revenue"].iloc[0] == 1000.0, "Value must be extracted correctly"


def test_export_business_technical_split_without_units() -> None:
    """
    Test export_business_technical_split() without unit suffixes.

    Given KPI history with mixed business/technical KPIs,
    When export_business_technical_split() is called with include_units_in_columns=False,
    Then both DataFrames have plain column names (no unit suffixes).
    """
    # Arrange
    history: List[Tuple[datetime, Dict[str, Any]]] = [
        (
            datetime.now(),
            {
                "business.revenue": {"value": 1000.0, "unit": "USD"},
                "technical.cpu_usage": {"value": 50.0, "unit": "%"},
            },
        )
    ]

    # Act
    business_df, technical_df = export_business_technical_split(
        history, include_units_in_columns=False
    )

    # Assert - Business DataFrame
    assert "business.revenue" in business_df.columns, "Plain column name must exist"
    assert "business.revenue_USD" not in business_df.columns, "Column name with unit suffix must NOT exist"

    # Assert - Technical DataFrame
    assert "technical.cpu_usage" in technical_df.columns, "Plain column name must exist"
    assert "technical.cpu_usage_pct" not in technical_df.columns, "Column name with unit suffix must NOT exist"


def test_export_by_category_raises_value_error_for_missing_category() -> None:
    """
    Test that export_by_category() raises ValueError when category not found.

    Given KPI history without any KPIs matching the category,
    When export_by_category() is called,
    Then ValueError is raised with clear message.
    """
    # Arrange
    history: List[Tuple[datetime, Dict[str, Any]]] = [
        (datetime.now(), {"other.metric": {"value": 100.0, "unit": "USD"}})
    ]

    # Act & Assert
    with pytest.raises(ValueError, match="Keine KPIs mit Präfix 'business' in History gefunden"):
        export_by_category(history, "business")
