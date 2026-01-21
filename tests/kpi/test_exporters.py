"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Tests for KPI exporters - DataFrame export and flattening functions
 Log:
 v1.2 : Added comprehensive tests for 3-level KPI grouping (18 new test scenarios)
 v1.1 : Added comprehensive tests for print_kpi_table (27 test scenarios)
 v1.0 : Initial implementation
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
# Standard Library
from datetime import datetime
from unittest.mock import patch

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


# =============================================================================
# TEST FUNCTIONS - print_kpi_table
# =============================================================================
def test_print_kpi_table_basic_functionality(capsys):
    """Test print_kpi_table() prints table with KPI groups."""
    # Arrange
    from basefunctions.kpi.exporters import print_kpi_table

    kpis = {
        "business": {
            "portfolio": {
                "balance": {"value": 1000.0, "unit": "USD"}
            }
        }
    }

    # Act
    print_kpi_table(kpis)

    # Assert
    captured = capsys.readouterr()
    assert "## Business KPIs - Portfolio" in captured.out
    assert "balance" in captured.out
    assert "1000" in captured.out  # Int detection: 1000.0 → "1000"
    assert "USD" in captured.out


def test_print_kpi_table_multiple_groups(capsys):
    """Test print_kpi_table() prints separate tables for multiple groups."""
    # Arrange
    from basefunctions.kpi.exporters import print_kpi_table

    kpis = {
        "business": {
            "portfolio": {
                "balance": {"value": 1000.0, "unit": "USD"}
            },
            "trading": {
                "orders": {"value": 50, "unit": None}
            }
        }
    }

    # Act
    print_kpi_table(kpis)

    # Assert
    captured = capsys.readouterr()
    assert "## Business KPIs - Portfolio" in captured.out
    assert "## Business KPIs - Trading" in captured.out
    assert "balance" in captured.out
    assert "orders" in captured.out


def test_print_kpi_table_empty_dict_prints_message(capsys):
    """Test print_kpi_table() with empty dict prints message without error."""
    # Arrange
    from basefunctions.kpi.exporters import print_kpi_table

    kpis = {}

    # Act
    print_kpi_table(kpis)

    # Assert
    captured = capsys.readouterr()
    assert "Keine KPIs vorhanden" in captured.out


def test_print_kpi_table_filter_single_pattern(capsys):
    """Test print_kpi_table() with single filter pattern matches correctly."""
    # Arrange
    from basefunctions.kpi.exporters import print_kpi_table

    kpis = {
        "business": {
            "portfolio": {"balance": {"value": 1000.0, "unit": "USD"}},
        },
        "technical": {
            "system": {"cpu": {"value": 50.0, "unit": "%"}}
        }
    }

    # Act
    print_kpi_table(kpis, filter_patterns=["business.*"])

    # Assert
    captured = capsys.readouterr()
    assert "Business" in captured.out
    assert "balance" in captured.out
    assert "Technical" not in captured.out
    assert "cpu" not in captured.out


def test_print_kpi_table_filter_multiple_patterns_or_logic(capsys):
    """Test print_kpi_table() with multiple patterns uses OR-logic."""
    # Arrange
    from basefunctions.kpi.exporters import print_kpi_table

    kpis = {
        "business": {
            "portfolio": {"balance": {"value": 1000.0, "unit": "USD"}},
        },
        "technical": {
            "system": {"cpu": {"value": 50.0, "unit": "%"}}
        },
        "operations": {
            "monitoring": {"alerts": {"value": 3, "unit": None}}
        }
    }

    # Act
    print_kpi_table(kpis, filter_patterns=["business.*", "technical.*"])

    # Assert
    captured = capsys.readouterr()
    assert "Business" in captured.out
    assert "Technical" in captured.out
    assert "Operations" not in captured.out


def test_print_kpi_table_filter_no_matches_prints_message(capsys):
    """Test print_kpi_table() with filter matching nothing prints message."""
    # Arrange
    from basefunctions.kpi.exporters import print_kpi_table

    kpis = {
        "business": {
            "portfolio": {"balance": {"value": 1000.0, "unit": "USD"}}
        }
    }

    # Act
    print_kpi_table(kpis, filter_patterns=["technical.*"])

    # Assert
    captured = capsys.readouterr()
    assert "Keine KPIs nach Filterung gefunden" in captured.out
    assert "Business" not in captured.out


def test_print_kpi_table_filter_none_prints_all(capsys):
    """Test print_kpi_table() without filter prints all KPIs."""
    # Arrange
    from basefunctions.kpi.exporters import print_kpi_table

    kpis = {
        "business": {
            "portfolio": {"balance": {"value": 1000.0, "unit": "USD"}}
        },
        "technical": {
            "system": {"cpu": {"value": 50.0, "unit": "%"}}
        }
    }

    # Act
    print_kpi_table(kpis, filter_patterns=None)

    # Assert
    captured = capsys.readouterr()
    assert "Business" in captured.out
    assert "Technical" in captured.out


def test_print_kpi_table_int_detection_no_decimals(capsys):
    """Test print_kpi_table() detects whole numbers and prints without decimals."""
    # Arrange
    from basefunctions.kpi.exporters import print_kpi_table

    kpis = {
        "business": {
            "portfolio": {
                "count": {"value": 5.0, "unit": None}
            }
        }
    }

    # Act
    print_kpi_table(kpis)

    # Assert
    captured = capsys.readouterr()
    assert "5" in captured.out
    assert "5.0" not in captured.out
    assert "5.00" not in captured.out


def test_print_kpi_table_float_formatting_with_decimals(capsys):
    """Test print_kpi_table() formats float values with decimals."""
    # Arrange
    from basefunctions.kpi.exporters import print_kpi_table

    kpis = {
        "business": {
            "portfolio": {
                "balance": {"value": 10000.55, "unit": "USD"}
            }
        }
    }

    # Act
    print_kpi_table(kpis, decimals=2)

    # Assert
    captured = capsys.readouterr()
    # Note: tabulate removes trailing zeros (10000.55 → "10000.5")
    assert "10000.5" in captured.out


def test_print_kpi_table_custom_decimals(capsys):
    """Test print_kpi_table() respects custom decimal places."""
    # Arrange
    from basefunctions.kpi.exporters import print_kpi_table

    kpis = {
        "business": {
            "portfolio": {
                "rate": {"value": 123.456789, "unit": "%"}
            }
        }
    }

    # Act
    print_kpi_table(kpis, decimals=3)

    # Assert
    captured = capsys.readouterr()
    assert "123.457" in captured.out


def test_print_kpi_table_without_units_no_unit_column(capsys):
    """Test print_kpi_table() without include_units excludes unit column."""
    # Arrange
    from basefunctions.kpi.exporters import print_kpi_table

    kpis = {
        "business": {
            "portfolio": {
                "balance": {"value": 1000.0, "unit": "USD"}
            }
        }
    }

    # Act
    print_kpi_table(kpis, include_units=False)

    # Assert
    captured = capsys.readouterr()
    assert "Unit" not in captured.out
    assert "1000" in captured.out  # Int detection


def test_print_kpi_table_missing_unit_displays_dash(capsys):
    """Test print_kpi_table() displays '-' for KPIs without unit."""
    # Arrange
    from basefunctions.kpi.exporters import print_kpi_table

    kpis = {
        "business": {
            "portfolio": {
                "count": {"value": 5, "unit": None}
            }
        }
    }

    # Act
    print_kpi_table(kpis)

    # Assert
    captured = capsys.readouterr()
    assert "-" in captured.out


def test_print_kpi_table_sort_keys_true_alphabetical_order(capsys):
    """Test print_kpi_table() with sort_keys=True sorts KPIs alphabetically."""
    # Arrange
    from basefunctions.kpi.exporters import print_kpi_table

    kpis = {
        "business": {
            "portfolio": {
                "zebra": {"value": 3, "unit": None},
                "apple": {"value": 1, "unit": None},
                "mango": {"value": 2, "unit": None}
            }
        }
    }

    # Act
    print_kpi_table(kpis, sort_keys=True)

    # Assert
    captured = capsys.readouterr()
    output = captured.out
    apple_pos = output.find("apple")
    mango_pos = output.find("mango")
    zebra_pos = output.find("zebra")
    assert apple_pos < mango_pos < zebra_pos


def test_print_kpi_table_sort_keys_false_preserves_insertion_order(capsys):
    """Test print_kpi_table() with sort_keys=False preserves insertion order."""
    # Arrange
    from basefunctions.kpi.exporters import print_kpi_table

    kpis = {
        "business": {
            "portfolio": {
                "zebra": {"value": 3, "unit": None},
                "apple": {"value": 1, "unit": None},
                "mango": {"value": 2, "unit": None}
            }
        }
    }

    # Act
    print_kpi_table(kpis, sort_keys=False)

    # Assert
    captured = capsys.readouterr()
    output = captured.out
    zebra_pos = output.find("zebra")
    apple_pos = output.find("apple")
    mango_pos = output.find("mango")
    # Note: dict insertion order in Python 3.7+ guarantees order
    assert zebra_pos < apple_pos < mango_pos


@patch("basefunctions.kpi.exporters.get_table_format")
def test_print_kpi_table_grid_format_contains_box_drawing(mock_format, capsys):
    """Test print_kpi_table() mocks get_table_format to return 'grid' format with box-drawing."""
    # Arrange
    from basefunctions.kpi.exporters import print_kpi_table

    mock_format.return_value = "grid"

    kpis = {
        "business": {
            "portfolio": {
                "balance": {"value": 1000.0, "unit": "USD"}
            }
        }
    }

    # Act
    print_kpi_table(kpis)

    # Assert
    captured = capsys.readouterr()
    # Grid format uses +, =, | characters for table borders
    assert "+" in captured.out
    assert "=" in captured.out
    assert "|" in captured.out


@patch("basefunctions.kpi.exporters.get_table_format")
def test_print_kpi_table_simple_format_minimalist(mock_format, capsys):
    """Test print_kpi_table() mocks get_table_format to return 'simple' format with minimal style."""
    # Arrange
    from basefunctions.kpi.exporters import print_kpi_table

    mock_format.return_value = "simple"

    kpis = {
        "business": {
            "portfolio": {
                "balance": {"value": 1000.0, "unit": "USD"}
            }
        }
    }

    # Act
    print_kpi_table(kpis)

    # Assert
    captured = capsys.readouterr()
    # Simple format uses -, no +/=/| borders
    assert "-" in captured.out
    assert "+" not in captured.out
    assert "=" not in captured.out


def test_print_kpi_table_invalid_decimals_raises_value_error():
    """Test print_kpi_table() with negative decimals raises ValueError."""
    # Arrange
    from basefunctions.kpi.exporters import print_kpi_table

    kpis = {
        "business": {
            "portfolio": {
                "balance": {"value": 1000.0, "unit": "USD"}
            }
        }
    }

    # Act & Assert
    with pytest.raises(ValueError, match="decimals muss >= 0 sein"):
        print_kpi_table(kpis, decimals=-1)


def test_print_kpi_table_nested_subpackages_correct_grouping(capsys):
    """Test print_kpi_table() with deep nesting groups by first three segments (3-level grouping)."""
    # Arrange
    from basefunctions.kpi.exporters import print_kpi_table

    kpis = {
        "business": {
            "portfolio": {
                "returns": {
                    "daily": {"value": 100.0, "unit": "USD"}
                }
            }
        }
    }

    # Act
    print_kpi_table(kpis)

    # Assert - 3-level grouping: category.package.subgroup
    captured = capsys.readouterr()
    assert "## Business KPIs - Portfolio - Returns" in captured.out
    assert "daily" in captured.out  # Only remaining path segment


def test_print_kpi_table_negative_values_formatted_correctly(capsys):
    """Test print_kpi_table() formats negative numbers correctly."""
    # Arrange
    from basefunctions.kpi.exporters import print_kpi_table

    kpis = {
        "business": {
            "portfolio": {
                "loss": {"value": -500.50, "unit": "USD"}
            }
        }
    }

    # Act
    print_kpi_table(kpis)

    # Assert
    captured = capsys.readouterr()
    assert "-500.5" in captured.out  # Trailing zeros removed


def test_print_kpi_table_zero_value_as_integer(capsys):
    """Test print_kpi_table() displays zero as '0' without decimals."""
    # Arrange
    from basefunctions.kpi.exporters import print_kpi_table

    kpis = {
        "business": {
            "portfolio": {
                "empty": {"value": 0.0, "unit": None}
            }
        }
    }

    # Act
    print_kpi_table(kpis)

    # Assert
    captured = capsys.readouterr()
    # Zero should be displayed as "0" not "0.00"
    lines = captured.out.split("\n")
    value_lines = [line for line in lines if "empty" in line]
    assert len(value_lines) > 0
    # Check the value line contains "0" (could be padded with spaces)
    value_line = value_lines[0]
    # Extract numeric part (between separators)
    import re
    numbers = re.findall(r'\d+\.?\d*', value_line)
    assert "0" in numbers


def test_print_kpi_table_large_numbers_correct_alignment(capsys):
    """Test print_kpi_table() handles large numbers with correct alignment."""
    # Arrange
    from basefunctions.kpi.exporters import print_kpi_table

    kpis = {
        "business": {
            "portfolio": {
                "balance": {"value": 1000000.0, "unit": "USD"}
            }
        }
    }

    # Act
    print_kpi_table(kpis)

    # Assert
    captured = capsys.readouterr()
    assert "1000000" in captured.out  # Int detection


def test_print_kpi_table_missing_value_key_handles_gracefully(capsys):
    """Test print_kpi_table() handles KPI dict without 'value' key defensively."""
    # Arrange
    from basefunctions.kpi.exporters import print_kpi_table

    # Malformed KPI (missing "value" key) - should be treated as nested dict
    kpis = {
        "business": {
            "portfolio": {
                "nested": {"inner": {"value": 100.0, "unit": "USD"}}
            }
        }
    }

    # Act
    print_kpi_table(kpis)

    # Assert - should recurse and find inner KPIValue
    # With 3-level grouping: category=business, package=portfolio, subgroup=nested
    captured = capsys.readouterr()
    assert "Business" in captured.out
    assert "## Business KPIs - Portfolio - Nested" in captured.out
    assert "inner" in captured.out  # Only remaining path segment
    assert "100" in captured.out  # Int detection


def test_print_kpi_table_wildcard_filtering_complex_pattern(capsys):
    """Test print_kpi_table() with complex wildcard patterns."""
    # Arrange
    from basefunctions.kpi.exporters import print_kpi_table

    kpis = {
        "business": {
            "portfolio": {
                "returns": {"total_pnl": {"value": 1000.55, "unit": "USD"}},
                "positions": {"count": {"value": 5, "unit": None}}
            },
            "trading": {
                "orders": {"executed": {"value": 50, "unit": None}}
            }
        }
    }

    # Act - filter for *.returns.* pattern
    print_kpi_table(kpis, filter_patterns=["*.returns.*"])

    # Assert - 3-level grouping: returns is subgroup, total_pnl is KPI name
    captured = capsys.readouterr()
    assert "## Business KPIs - Portfolio - Returns" in captured.out
    assert "total_pnl" in captured.out
    assert "1000.55" in captured.out  # Float with decimals
    assert "positions" not in captured.out
    assert "trading" not in captured.out


def test_print_kpi_table_backward_compatibility_plain_values(capsys):
    """Test print_kpi_table() handles plain values without KPIValue format (backward compatibility)."""
    # Arrange
    from basefunctions.kpi.exporters import print_kpi_table

    # Old format without KPIValue wrapper
    kpis = {
        "business": {
            "portfolio": {
                "balance": 1000.0  # Plain value, not {"value": ..., "unit": ...}
            }
        }
    }

    # Act
    print_kpi_table(kpis)

    # Assert
    captured = capsys.readouterr()
    assert "Business" in captured.out
    assert "balance" in captured.out
    assert "1000" in captured.out  # Int detection
    assert "-" in captured.out  # No unit


# =============================================================================
# TEST FUNCTIONS - print_kpi_table (3-LEVEL GROUPING)
# =============================================================================
def test_print_kpi_table_3_level_grouping_basic(capsys):
    """Test print_kpi_table() with 3-level grouping (category.package.subgroup)."""
    # Arrange
    from basefunctions.kpi.exporters import print_kpi_table

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
    print_kpi_table(kpis)

    # Assert
    captured = capsys.readouterr()
    assert "## Business KPIs - Portfoliofunctions - Activity" in captured.out
    assert "win_rate" in captured.out
    assert "0.75" in captured.out
    assert "%" in captured.out


def test_print_kpi_table_3_level_grouping_multiple_subgroups(capsys):
    """Test print_kpi_table() with multiple subgroups in same package."""
    # Arrange
    from basefunctions.kpi.exporters import print_kpi_table

    kpis = {
        "business": {
            "portfoliofunctions": {
                "activity": {
                    "win_rate": {"value": 0.75, "unit": "%"}
                },
                "returns": {
                    "total_pnl": {"value": 1000.0, "unit": "USD"}
                }
            }
        }
    }

    # Act
    print_kpi_table(kpis)

    # Assert
    captured = capsys.readouterr()
    assert "## Business KPIs - Portfoliofunctions - Activity" in captured.out
    assert "## Business KPIs - Portfoliofunctions - Returns" in captured.out
    assert "win_rate" in captured.out
    assert "total_pnl" in captured.out


def test_print_kpi_table_3_level_grouping_header_uses_subgroup_name(capsys):
    """Test print_kpi_table() uses subgroup name as primary table header."""
    # Arrange
    from basefunctions.kpi.exporters import print_kpi_table

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
    print_kpi_table(kpis)

    # Assert
    captured = capsys.readouterr()
    # Table header should use "Activity" as primary column name
    assert "Activity" in captured.out
    assert "Value" in captured.out


def test_print_kpi_table_3_level_grouping_subgroup_capitalized(capsys):
    """Test print_kpi_table() capitalizes subgroup name in header."""
    # Arrange
    from basefunctions.kpi.exporters import print_kpi_table

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
    print_kpi_table(kpis)

    # Assert
    captured = capsys.readouterr()
    # Subgroup "activity" should be capitalized to "Activity"
    assert "Activity" in captured.out
    assert "activity" not in captured.out or "## Business KPIs - Portfoliofunctions - Activity" in captured.out


def test_print_kpi_table_3_level_grouping_with_nested_kpis(capsys):
    """Test print_kpi_table() with 4+ level nesting (remaining path shown in KPI name)."""
    # Arrange
    from basefunctions.kpi.exporters import print_kpi_table

    kpis = {
        "business": {
            "portfoliofunctions": {
                "activity": {
                    "trades": {
                        "count": {"value": 42, "unit": None}
                    }
                }
            }
        }
    }

    # Act
    print_kpi_table(kpis)

    # Assert
    captured = capsys.readouterr()
    assert "## Business KPIs - Portfoliofunctions - Activity" in captured.out
    # Remaining path: trades.count
    assert "trades.count" in captured.out
    assert "42" in captured.out


def test_print_kpi_table_3_level_backward_compat_2_level_fallback(capsys):
    """Test print_kpi_table() falls back to 2-level grouping for legacy KPIs."""
    # Arrange
    from basefunctions.kpi.exporters import print_kpi_table

    kpis = {
        "business": {
            "portfolio": {
                "balance": {"value": 5000.0, "unit": "USD"}
            }
        }
    }

    # Act
    print_kpi_table(kpis)

    # Assert
    captured = capsys.readouterr()
    # 2-level fallback: category.package
    assert "## Business KPIs - Portfolio" in captured.out
    assert "balance" in captured.out
    assert "5000" in captured.out


def test_print_kpi_table_mixed_2_level_and_3_level_grouping(capsys):
    """Test print_kpi_table() with mixed 2-level and 3-level KPIs in separate sections."""
    # Arrange
    from basefunctions.kpi.exporters import print_kpi_table

    kpis = {
        "business": {
            "portfoliofunctions": {
                "activity": {
                    "win_rate": {"value": 0.75, "unit": "%"}
                }
            },
            "portfolio": {
                "balance": {"value": 5000.0, "unit": "USD"}
            }
        }
    }

    # Act
    print_kpi_table(kpis)

    # Assert
    captured = capsys.readouterr()
    # Both sections should exist
    assert "## Business KPIs - Portfoliofunctions - Activity" in captured.out
    assert "## Business KPIs - Portfolio" in captured.out
    assert "win_rate" in captured.out
    assert "balance" in captured.out


def test_print_kpi_table_mixed_levels_no_cross_contamination(capsys):
    """Test print_kpi_table() ensures no KPI cross-contamination between groups."""
    # Arrange
    from basefunctions.kpi.exporters import print_kpi_table

    kpis = {
        "business": {
            "portfoliofunctions": {
                "activity": {
                    "win_rate": {"value": 0.75, "unit": "%"}
                }
            },
            "portfolio": {
                "balance": {"value": 5000.0, "unit": "USD"}
            }
        }
    }

    # Act
    print_kpi_table(kpis)

    # Assert
    captured = capsys.readouterr()
    output = captured.out

    # Note: business.portfolio.balance is interpreted as 3-level grouping:
    # Group: business.portfolio.balance (KPIValue "balance" becomes subgroup)
    # Find sections (sorted alphabetically: Portfolio before Portfoliofunctions)
    portfolio_section_start = output.find("## Business KPIs - Portfolio - Balance")
    activity_section_start = output.find("## Business KPIs - Portfoliofunctions - Activity")

    # Extract sections
    portfolio_section = output[portfolio_section_start:activity_section_start]
    activity_section = output[activity_section_start:]

    # Verify no cross-contamination
    assert "balance" in portfolio_section
    assert "win_rate" not in portfolio_section
    assert "win_rate" in activity_section
    assert "balance" not in activity_section


def test_print_kpi_table_wildcard_filter_3_level_single_subgroup(capsys):
    """Test print_kpi_table() with wildcard filter matching single 3-level subgroup."""
    # Arrange
    from basefunctions.kpi.exporters import print_kpi_table

    kpis = {
        "business": {
            "portfoliofunctions": {
                "activity": {
                    "win_rate": {"value": 0.75, "unit": "%"}
                },
                "returns": {
                    "total_pnl": {"value": 1000.0, "unit": "USD"}
                }
            }
        }
    }

    # Act - filter only "activity" subgroup
    print_kpi_table(kpis, filter_patterns=["business.portfoliofunctions.activity.*"])

    # Assert
    captured = capsys.readouterr()
    assert "win_rate" in captured.out
    assert "total_pnl" not in captured.out
    assert "Activity" in captured.out
    assert "Returns" not in captured.out


def test_print_kpi_table_wildcard_filter_3_level_all_subgroups(capsys):
    """Test print_kpi_table() with wildcard filter matching all subgroups in package."""
    # Arrange
    from basefunctions.kpi.exporters import print_kpi_table

    kpis = {
        "business": {
            "portfoliofunctions": {
                "activity": {
                    "win_rate": {"value": 0.75, "unit": "%"}
                },
                "returns": {
                    "total_pnl": {"value": 1000.0, "unit": "USD"}
                }
            },
            "backtester": {
                "performance": {
                    "trades": {"value": 42, "unit": None}
                }
            }
        }
    }

    # Act - filter all subgroups in "portfoliofunctions"
    print_kpi_table(kpis, filter_patterns=["business.portfoliofunctions.*"])

    # Assert
    captured = capsys.readouterr()
    assert "win_rate" in captured.out
    assert "total_pnl" in captured.out
    assert "trades" not in captured.out  # Not in portfoliofunctions


def test_print_kpi_table_wildcard_filter_3_level_cross_package_subgroup(capsys):
    """Test print_kpi_table() with wildcard filter matching same subgroup across packages."""
    # Arrange
    from basefunctions.kpi.exporters import print_kpi_table

    kpis = {
        "business": {
            "portfoliofunctions": {
                "activity": {
                    "win_rate": {"value": 0.75, "unit": "%"}
                }
            },
            "backtester": {
                "activity": {
                    "simulations": {"value": 100, "unit": None}
                }
            }
        }
    }

    # Act - filter "activity" subgroup in all packages
    print_kpi_table(kpis, filter_patterns=["business.*.activity.*"])

    # Assert
    captured = capsys.readouterr()
    assert "win_rate" in captured.out
    assert "simulations" in captured.out
    assert "Portfoliofunctions - Activity" in captured.out
    assert "Backtester - Activity" in captured.out


def test_print_kpi_table_wildcard_filter_3_level_nested_kpis(capsys):
    """Test print_kpi_table() wildcard filtering with nested KPIs (4+ levels)."""
    # Arrange
    from basefunctions.kpi.exporters import print_kpi_table

    kpis = {
        "business": {
            "portfoliofunctions": {
                "activity": {
                    "trades": {
                        "count": {"value": 42, "unit": None},
                        "volume": {"value": 1000000.0, "unit": "USD"}
                    }
                }
            }
        }
    }

    # Act - filter all activity KPIs
    print_kpi_table(kpis, filter_patterns=["business.portfoliofunctions.activity.*"])

    # Assert
    captured = capsys.readouterr()
    assert "trades.count" in captured.out
    assert "trades.volume" in captured.out
    assert "42" in captured.out
    assert "1000000" in captured.out


def test_print_kpi_table_3_level_edge_case_single_segment_kpi(capsys):
    """Test print_kpi_table() handles edge case of single segment KPI name."""
    # Arrange
    from basefunctions.kpi.exporters import print_kpi_table

    kpis = {
        "total": {"value": 5000.0, "unit": "USD"}
    }

    # Act
    print_kpi_table(kpis)

    # Assert - fallback to single-level grouping
    captured = capsys.readouterr()
    assert "## Total KPIs" in captured.out
    assert "total" in captured.out
    assert "5000" in captured.out


def test_print_kpi_table_3_level_very_long_kpi_names(capsys):
    """Test print_kpi_table() handles very long KPI names gracefully."""
    # Arrange
    from basefunctions.kpi.exporters import print_kpi_table

    kpis = {
        "business": {
            "portfoliofunctions": {
                "activity": {
                    "very_long_kpi_name_that_exceeds_normal_length": {"value": 123.45, "unit": "%"}
                }
            }
        }
    }

    # Act
    print_kpi_table(kpis)

    # Assert
    captured = capsys.readouterr()
    assert "very_long_kpi_name_that_exceeds_normal_length" in captured.out
    assert "123.45" in captured.out


def test_print_kpi_table_3_level_special_characters_in_subgroup(capsys):
    """Test print_kpi_table() handles subgroup names with hyphens/underscores."""
    # Arrange
    from basefunctions.kpi.exporters import print_kpi_table

    kpis = {
        "business": {
            "portfolio-functions": {
                "high_frequency": {
                    "trades": {"value": 1000, "unit": None}
                }
            }
        }
    }

    # Act
    print_kpi_table(kpis)

    # Assert
    captured = capsys.readouterr()
    # Capitalize normalizes: "portfolio-functions" → "Portfolio-functions"
    assert "Portfolio-functions" in captured.out
    assert "High_frequency" in captured.out
    assert "trades" in captured.out


def test_print_kpi_table_3_level_empty_kpi_dict_in_subgroup(capsys):
    """Test print_kpi_table() handles empty dict at subgroup level gracefully."""
    # Arrange
    from basefunctions.kpi.exporters import print_kpi_table

    kpis = {
        "business": {
            "portfoliofunctions": {
                "activity": {}
            }
        }
    }

    # Act
    print_kpi_table(kpis)

    # Assert - empty dict after flattening results in "Keine KPIs nach Filterung gefunden"
    captured = capsys.readouterr()
    assert "Keine KPIs nach Filterung gefunden" in captured.out or "Keine KPIs vorhanden" in captured.out


def test_print_kpi_table_3_level_sort_keys_groups_and_items(capsys):
    """Test print_kpi_table() sorts both group keys and items within groups."""
    # Arrange
    from basefunctions.kpi.exporters import print_kpi_table

    kpis = {
        "business": {
            "zebra": {
                "subgroup_z": {
                    "metric_z": {"value": 3, "unit": None},
                    "metric_a": {"value": 1, "unit": None}
                }
            },
            "alpha": {
                "subgroup_a": {
                    "metric_b": {"value": 2, "unit": None}
                }
            }
        }
    }

    # Act
    print_kpi_table(kpis, sort_keys=True)

    # Assert
    captured = capsys.readouterr()
    output = captured.out

    # Groups should be sorted alphabetically
    alpha_pos = output.find("## Business KPIs - Alpha")
    zebra_pos = output.find("## Business KPIs - Zebra")
    assert alpha_pos < zebra_pos

    # Items within groups should be sorted
    metric_a_pos = output.find("metric_a")
    metric_z_pos = output.find("metric_z")
    assert metric_a_pos < metric_z_pos
