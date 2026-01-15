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
