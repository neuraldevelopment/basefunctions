"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Tests for KPI exporters - DataFrame export and flattening functions
 Log:
 v1.0 : Initial implementation
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
# Standard Library
from datetime import datetime

# Third-party
import pytest

# Project modules
from basefunctions.kpi.exporters import _flatten_dict, export_to_dataframe


# =============================================================================
# TEST FUNCTIONS - _flatten_dict
# =============================================================================
def test_flatten_dict_with_flat_dict():
    """Test _flatten_dict() with flat dictionary."""
    # Arrange
    data = {"balance": 100.0, "profit": 50.0}

    # Act
    result = _flatten_dict(data)

    # Assert
    assert result == {"balance": 100.0, "profit": 50.0}


def test_flatten_dict_with_nested_dict():
    """Test _flatten_dict() with nested dictionary (dot notation)."""
    # Arrange
    data = {"balance": 100.0, "portfolio": {"sub_balance": 25.0}}

    # Act
    result = _flatten_dict(data)

    # Assert
    assert result == {"balance": 100.0, "portfolio.sub_balance": 25.0}


def test_flatten_dict_with_deeply_nested_dict():
    """Test _flatten_dict() with deeply nested dictionary (3 levels)."""
    # Arrange
    data = {
        "level1": 100.0,
        "nested": {"level2": 50.0, "deep": {"level3": 10.0}},
    }

    # Act
    result = _flatten_dict(data)

    # Assert
    assert result == {
        "level1": 100.0,
        "nested.level2": 50.0,
        "nested.deep.level3": 10.0,
    }


def test_flatten_dict_with_empty_dict():
    """Test _flatten_dict() with empty dictionary."""
    # Arrange
    data = {}

    # Act
    result = _flatten_dict(data)

    # Assert
    assert result == {}


def test_flatten_dict_with_multiple_branches():
    """Test _flatten_dict() with multiple nested branches."""
    # Arrange
    data = {
        "balance": 5000.0,
        "portfolio": {"value": 1000.0},
        "risk": {"var": 50.0, "sharpe": 1.5},
    }

    # Act
    result = _flatten_dict(data)

    # Assert
    assert result == {
        "balance": 5000.0,
        "portfolio.value": 1000.0,
        "risk.var": 50.0,
        "risk.sharpe": 1.5,
    }


def test_flatten_dict_converts_to_float():
    """Test _flatten_dict() converts values to float."""
    # Arrange
    data = {"int_val": 100, "float_val": 123.456}

    # Act
    result = _flatten_dict(data)

    # Assert
    assert result["int_val"] == 100.0
    assert isinstance(result["int_val"], float)
    assert result["float_val"] == 123.456


def test_flatten_dict_with_prefix():
    """Test _flatten_dict() with custom prefix."""
    # Arrange
    data = {"balance": 100.0, "sub": {"value": 25.0}}

    # Act
    result = _flatten_dict(data, prefix="root")

    # Assert
    assert result == {"root.balance": 100.0, "root.sub.value": 25.0}


# =============================================================================
# TEST FUNCTIONS - export_to_dataframe
# =============================================================================
def test_export_to_dataframe_with_simple_history():
    """Test export_to_dataframe() with simple flat history."""
    # Arrange
    pytest.importorskip("pandas")
    import pandas as pd

    history = [
        (datetime(2024, 1, 1, 10, 0, 0), {"balance": 100.0, "profit": 50.0}),
        (datetime(2024, 1, 1, 11, 0, 0), {"balance": 150.0, "profit": 75.0}),
    ]

    # Act
    df = export_to_dataframe(history)

    # Assert
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert list(df.columns) == ["balance", "profit"]
    assert df.index.name == "timestamp"
    assert df.iloc[0]["balance"] == 100.0
    assert df.iloc[1]["balance"] == 150.0


def test_export_to_dataframe_with_nested_history():
    """Test export_to_dataframe() with nested KPI data (flattens)."""
    # Arrange
    pytest.importorskip("pandas")
    import pandas as pd

    history = [
        (
            datetime(2024, 1, 1, 10, 0, 0),
            {"balance": 100.0, "portfolio": {"sub_balance": 25.0}},
        ),
    ]

    # Act
    df = export_to_dataframe(history)

    # Assert
    assert isinstance(df, pd.DataFrame)
    assert "balance" in df.columns
    assert "portfolio.sub_balance" in df.columns
    assert df.iloc[0]["balance"] == 100.0
    assert df.iloc[0]["portfolio.sub_balance"] == 25.0


def test_export_to_dataframe_with_deeply_nested_history():
    """Test export_to_dataframe() with deeply nested data."""
    # Arrange
    pytest.importorskip("pandas")

    history = [
        (
            datetime(2024, 1, 1, 10, 0, 0),
            {
                "level1": 100.0,
                "nested": {"level2": 50.0, "deep": {"level3": 10.0}},
            },
        ),
    ]

    # Act
    df = export_to_dataframe(history)

    # Assert
    assert "level1" in df.columns
    assert "nested.level2" in df.columns
    assert "nested.deep.level3" in df.columns
    assert df.iloc[0]["nested.deep.level3"] == 10.0


def test_export_to_dataframe_with_empty_history_raises_value_error():
    """Test export_to_dataframe() with empty history raises ValueError."""
    # Arrange
    pytest.importorskip("pandas")
    history = []

    # Act & Assert
    with pytest.raises(ValueError, match="History ist leer"):
        export_to_dataframe(history)


def test_export_to_dataframe_without_pandas_raises_import_error():
    """Test export_to_dataframe() without pandas raises ImportError."""
    # Arrange
    import sys
    from unittest.mock import patch

    history = [(datetime(2024, 1, 1, 10, 0, 0), {"balance": 100.0})]

    # Act & Assert
    with patch.dict(sys.modules, {"pandas": None}):
        with pytest.raises(ImportError, match="pandas ist nicht installiert"):
            # Force reimport to trigger ImportError
            import importlib
            import basefunctions.kpi.exporters

            importlib.reload(basefunctions.kpi.exporters)
            from basefunctions.kpi.exporters import export_to_dataframe

            export_to_dataframe(history)


def test_export_to_dataframe_index_is_timestamp():
    """Test export_to_dataframe() sets timestamp as index."""
    # Arrange
    pytest.importorskip("pandas")

    ts1 = datetime(2024, 1, 1, 10, 0, 0)
    ts2 = datetime(2024, 1, 1, 11, 0, 0)
    history = [
        (ts1, {"balance": 100.0}),
        (ts2, {"balance": 150.0}),
    ]

    # Act
    df = export_to_dataframe(history)

    # Assert
    assert df.index[0] == ts1
    assert df.index[1] == ts2
    assert df.index.name == "timestamp"


def test_export_to_dataframe_with_multiple_nested_branches():
    """Test export_to_dataframe() with multiple nested branches."""
    # Arrange
    pytest.importorskip("pandas")

    history = [
        (
            datetime(2024, 1, 1, 10, 0, 0),
            {
                "balance": 5000.0,
                "portfolio": {"value": 1000.0},
                "risk": {"var": 50.0, "sharpe": 1.5},
            },
        ),
    ]

    # Act
    df = export_to_dataframe(history)

    # Assert
    assert "balance" in df.columns
    assert "portfolio.value" in df.columns
    assert "risk.var" in df.columns
    assert "risk.sharpe" in df.columns
    assert df.iloc[0]["balance"] == 5000.0
    assert df.iloc[0]["portfolio.value"] == 1000.0
    assert df.iloc[0]["risk.var"] == 50.0
    assert df.iloc[0]["risk.sharpe"] == 1.5


def test_export_to_dataframe_handles_varying_columns():
    """Test export_to_dataframe() handles varying columns across time (NaN for missing)."""
    # Arrange
    pytest.importorskip("pandas")
    import pandas as pd

    history = [
        (datetime(2024, 1, 1, 10, 0, 0), {"balance": 100.0}),
        (datetime(2024, 1, 1, 11, 0, 0), {"balance": 150.0, "profit": 25.0}),
    ]

    # Act
    df = export_to_dataframe(history)

    # Assert
    assert len(df) == 2
    assert "balance" in df.columns
    assert "profit" in df.columns
    assert pd.isna(df.iloc[0]["profit"])  # First entry has no profit
    assert df.iloc[1]["profit"] == 25.0


# =============================================================================
# TEST FUNCTIONS - export_by_category
# =============================================================================
def test_export_by_category_filters_business_kpis():
    """Test export_by_category() exports only business KPIs."""
    # Arrange
    pytest.importorskip("pandas")
    import pandas as pd
    from basefunctions.kpi.exporters import export_by_category

    history = [
        (
            datetime(2024, 1, 1, 10, 0, 0),
            {
                "business.revenue": 10000.0,
                "business.orders": 50.0,
                "technical.cpu": 75.0,
            },
        ),
    ]

    # Act
    df = export_by_category(history, "business")

    # Assert
    assert isinstance(df, pd.DataFrame)
    assert "business.revenue" in df.columns
    assert "business.orders" in df.columns
    assert "technical.cpu" not in df.columns
    assert df.iloc[0]["business.revenue"] == 10000.0


def test_export_by_category_filters_technical_kpis():
    """Test export_by_category() exports only technical KPIs."""
    # Arrange
    pytest.importorskip("pandas")
    from basefunctions.kpi.exporters import export_by_category

    history = [
        (
            datetime(2024, 1, 1, 10, 0, 0),
            {
                "business.revenue": 10000.0,
                "technical.cpu": 75.0,
                "technical.memory": 512.0,
            },
        ),
    ]

    # Act
    df = export_by_category(history, "technical")

    # Assert
    assert "technical.cpu" in df.columns
    assert "technical.memory" in df.columns
    assert "business.revenue" not in df.columns
    assert df.iloc[0]["technical.cpu"] == 75.0


def test_export_by_category_with_empty_history_raises_value_error():
    """Test export_by_category() with empty history raises ValueError."""
    # Arrange
    pytest.importorskip("pandas")
    from basefunctions.kpi.exporters import export_by_category

    history = []

    # Act & Assert
    with pytest.raises(ValueError, match="Keine KPIs mit Präfix 'business'"):
        export_by_category(history, "business")


def test_export_by_category_with_no_matching_kpis_raises_value_error():
    """Test export_by_category() raises ValueError when no KPIs match category."""
    # Arrange
    pytest.importorskip("pandas")
    from basefunctions.kpi.exporters import export_by_category

    history = [
        (datetime(2024, 1, 1, 10, 0, 0), {"technical.cpu": 75.0}),
    ]

    # Act & Assert
    with pytest.raises(ValueError, match="Keine KPIs mit Präfix 'business'"):
        export_by_category(history, "business")


def test_export_by_category_with_multiple_timestamps():
    """Test export_by_category() with multiple time entries filters correctly."""
    # Arrange
    pytest.importorskip("pandas")
    from basefunctions.kpi.exporters import export_by_category

    history = [
        (
            datetime(2024, 1, 1, 10, 0, 0),
            {"business.revenue": 1000.0, "technical.cpu": 50.0},
        ),
        (
            datetime(2024, 1, 1, 11, 0, 0),
            {"business.revenue": 1500.0, "technical.cpu": 60.0},
        ),
    ]

    # Act
    df = export_by_category(history, "business")

    # Assert
    assert len(df) == 2
    assert "business.revenue" in df.columns
    assert "technical.cpu" not in df.columns
    assert df.iloc[0]["business.revenue"] == 1000.0
    assert df.iloc[1]["business.revenue"] == 1500.0


def test_export_by_category_without_pandas_raises_import_error():
    """Test export_by_category() without pandas raises ImportError."""
    # Arrange
    import sys
    from unittest.mock import patch

    from basefunctions.kpi.exporters import export_by_category

    history = [
        (datetime(2024, 1, 1, 10, 0, 0), {"business.revenue": 1000.0}),
    ]

    # Act & Assert
    with patch.dict(sys.modules, {"pandas": None}):
        with pytest.raises(ImportError, match="pandas ist nicht installiert"):
            export_by_category(history, "business")


# =============================================================================
# TEST FUNCTIONS - export_business_technical_split
# =============================================================================
def test_export_business_technical_split_returns_two_dataframes():
    """Test export_business_technical_split() returns tuple of (business_df, technical_df)."""
    # Arrange
    pytest.importorskip("pandas")
    import pandas as pd
    from basefunctions.kpi.exporters import export_business_technical_split

    history = [
        (
            datetime(2024, 1, 1, 10, 0, 0),
            {
                "business.revenue": 10000.0,
                "business.orders": 50.0,
                "technical.cpu": 75.0,
                "technical.memory": 512.0,
            },
        ),
    ]

    # Act
    business_df, technical_df = export_business_technical_split(history)

    # Assert
    assert isinstance(business_df, pd.DataFrame)
    assert isinstance(technical_df, pd.DataFrame)


def test_export_business_technical_split_splits_kpis_correctly():
    """Test export_business_technical_split() correctly splits KPIs by category."""
    # Arrange
    pytest.importorskip("pandas")
    from basefunctions.kpi.exporters import export_business_technical_split

    history = [
        (
            datetime(2024, 1, 1, 10, 0, 0),
            {
                "business.revenue": 10000.0,
                "business.orders": 50.0,
                "technical.cpu": 75.0,
                "technical.memory": 512.0,
            },
        ),
    ]

    # Act
    business_df, technical_df = export_business_technical_split(history)

    # Assert - business DataFrame
    assert "business.revenue" in business_df.columns
    assert "business.orders" in business_df.columns
    assert "technical.cpu" not in business_df.columns
    assert business_df.iloc[0]["business.revenue"] == 10000.0

    # Assert - technical DataFrame
    assert "technical.cpu" in technical_df.columns
    assert "technical.memory" in technical_df.columns
    assert "business.revenue" not in technical_df.columns
    assert technical_df.iloc[0]["technical.cpu"] == 75.0


def test_export_business_technical_split_with_multiple_timestamps():
    """Test export_business_technical_split() with multiple time entries."""
    # Arrange
    pytest.importorskip("pandas")
    from basefunctions.kpi.exporters import export_business_technical_split

    history = [
        (
            datetime(2024, 1, 1, 10, 0, 0),
            {"business.revenue": 1000.0, "technical.cpu": 50.0},
        ),
        (
            datetime(2024, 1, 1, 11, 0, 0),
            {"business.revenue": 1500.0, "technical.cpu": 60.0},
        ),
    ]

    # Act
    business_df, technical_df = export_business_technical_split(history)

    # Assert
    assert len(business_df) == 2
    assert len(technical_df) == 2
    assert business_df.iloc[0]["business.revenue"] == 1000.0
    assert business_df.iloc[1]["business.revenue"] == 1500.0
    assert technical_df.iloc[0]["technical.cpu"] == 50.0
    assert technical_df.iloc[1]["technical.cpu"] == 60.0


def test_export_business_technical_split_with_missing_business_raises_value_error():
    """Test export_business_technical_split() raises ValueError when business KPIs missing."""
    # Arrange
    pytest.importorskip("pandas")
    from basefunctions.kpi.exporters import export_business_technical_split

    history = [
        (datetime(2024, 1, 1, 10, 0, 0), {"technical.cpu": 75.0}),
    ]

    # Act & Assert
    with pytest.raises(ValueError, match="Keine KPIs mit Präfix 'business'"):
        export_business_technical_split(history)


def test_export_business_technical_split_with_missing_technical_raises_value_error():
    """Test export_business_technical_split() raises ValueError when technical KPIs missing."""
    # Arrange
    pytest.importorskip("pandas")
    from basefunctions.kpi.exporters import export_business_technical_split

    history = [
        (datetime(2024, 1, 1, 10, 0, 0), {"business.revenue": 10000.0}),
    ]

    # Act & Assert
    with pytest.raises(ValueError, match="Keine KPIs mit Präfix 'technical'"):
        export_business_technical_split(history)


def test_export_business_technical_split_with_empty_history_raises_value_error():
    """Test export_business_technical_split() raises ValueError with empty history."""
    # Arrange
    pytest.importorskip("pandas")
    from basefunctions.kpi.exporters import export_business_technical_split

    history = []

    # Act & Assert
    with pytest.raises(ValueError, match="Keine KPIs mit Präfix"):
        export_business_technical_split(history)


def test_export_business_technical_split_preserves_timestamp_index():
    """Test export_business_technical_split() preserves timestamp as index in both DataFrames."""
    # Arrange
    pytest.importorskip("pandas")
    from basefunctions.kpi.exporters import export_business_technical_split

    ts1 = datetime(2024, 1, 1, 10, 0, 0)
    ts2 = datetime(2024, 1, 1, 11, 0, 0)
    history = [
        (ts1, {"business.revenue": 1000.0, "technical.cpu": 50.0}),
        (ts2, {"business.revenue": 1500.0, "technical.cpu": 60.0}),
    ]

    # Act
    business_df, technical_df = export_business_technical_split(history)

    # Assert
    assert business_df.index.name == "timestamp"
    assert technical_df.index.name == "timestamp"
    assert business_df.index[0] == ts1
    assert business_df.index[1] == ts2
    assert technical_df.index[0] == ts1
    assert technical_df.index[1] == ts2


# =============================================================================
# TEST FUNCTIONS - _filter_history_by_prefix (internal)
# =============================================================================
def test_filter_history_by_prefix_filters_correctly():
    """Test _filter_history_by_prefix() filters history entries by prefix."""
    # Arrange
    from basefunctions.kpi.exporters import _filter_history_by_prefix

    history = [
        (
            datetime(2024, 1, 1, 10, 0, 0),
            {"business.revenue": 1000.0, "technical.cpu": 50.0},
        ),
    ]

    # Act
    filtered = _filter_history_by_prefix(history, "business")

    # Assert
    assert len(filtered) == 1
    _, kpis = filtered[0]
    assert "business.revenue" in kpis
    assert "technical.cpu" not in kpis


def test_filter_history_by_prefix_with_multiple_entries():
    """Test _filter_history_by_prefix() filters multiple history entries."""
    # Arrange
    from basefunctions.kpi.exporters import _filter_history_by_prefix

    history = [
        (datetime(2024, 1, 1, 10, 0, 0), {"business.revenue": 1000.0}),
        (datetime(2024, 1, 1, 11, 0, 0), {"technical.cpu": 50.0}),
        (datetime(2024, 1, 1, 12, 0, 0), {"business.orders": 25.0}),
    ]

    # Act
    filtered = _filter_history_by_prefix(history, "business")

    # Assert
    assert len(filtered) == 2  # Only entries with business KPIs
    assert filtered[0][1] == {"business.revenue": 1000.0}
    assert filtered[1][1] == {"business.orders": 25.0}


def test_filter_history_by_prefix_with_empty_history():
    """Test _filter_history_by_prefix() with empty history returns empty list."""
    # Arrange
    from basefunctions.kpi.exporters import _filter_history_by_prefix

    history = []

    # Act
    filtered = _filter_history_by_prefix(history, "business")

    # Assert
    assert filtered == []


def test_filter_history_by_prefix_with_no_matches():
    """Test _filter_history_by_prefix() returns empty list when no KPIs match."""
    # Arrange
    from basefunctions.kpi.exporters import _filter_history_by_prefix

    history = [
        (datetime(2024, 1, 1, 10, 0, 0), {"technical.cpu": 50.0}),
    ]

    # Act
    filtered = _filter_history_by_prefix(history, "business")

    # Assert
    assert filtered == []
