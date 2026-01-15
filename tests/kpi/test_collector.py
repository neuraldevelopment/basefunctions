"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Tests for KPICollector - Recursive collection and history management
 Log:
 v1.0 : Initial implementation
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
# Standard Library
from datetime import datetime

# Project modules
from basefunctions.kpi.collector import KPICollector


# =============================================================================
# TEST FUNCTIONS
# =============================================================================
def test_collect_with_flat_provider(flat_provider):
    """Test collect() with flat provider (no subproviders)."""
    # Arrange
    collector = KPICollector()

    # Act
    result = collector.collect(flat_provider)

    # Assert
    assert result == {"balance": 100.0, "profit": 50.0}


def test_collect_with_nested_provider(nested_provider):
    """Test collect() with nested provider (recursive)."""
    # Arrange
    collector = KPICollector()

    # Act
    result = collector.collect(nested_provider)

    # Assert
    assert result["balance"] == 100.0
    assert "portfolio" in result
    assert result["portfolio"]["sub_balance"] == 25.0


def test_collect_with_deeply_nested_provider(deeply_nested_provider):
    """Test collect() with deeply nested provider (3 levels)."""
    # Arrange
    collector = KPICollector()

    # Act
    result = collector.collect(deeply_nested_provider)

    # Assert
    assert result["level1_value"] == 100.0
    assert "level2" in result
    assert result["level2"]["level2_value"] == 50.0
    assert "level3" in result["level2"]
    assert result["level2"]["level3"]["level3_value"] == 10.0


def test_collect_with_multiple_subproviders(multi_subprovider):
    """Test collect() with multiple subproviders."""
    # Arrange
    collector = KPICollector()

    # Act
    result = collector.collect(multi_subprovider)

    # Assert
    assert result["balance"] == 5000.0
    assert "portfolio" in result
    assert result["portfolio"]["portfolio_value"] == 1000.0
    assert "risk" in result
    assert result["risk"]["var"] == 50.0
    assert result["risk"]["sharpe"] == 1.5


def test_collect_and_store_adds_to_history(flat_provider):
    """Test collect_and_store() adds entry to history."""
    # Arrange
    collector = KPICollector()

    # Act
    result = collector.collect_and_store(flat_provider)
    history = collector.get_history()

    # Assert
    assert result == {"balance": 100.0, "profit": 50.0}
    assert len(history) == 1
    assert history[0][1] == {"balance": 100.0, "profit": 50.0}
    assert isinstance(history[0][0], datetime)


def test_collect_and_store_multiple_times(flat_provider):
    """Test collect_and_store() multiple times builds history."""
    # Arrange
    collector = KPICollector()

    # Act
    collector.collect_and_store(flat_provider)
    collector.collect_and_store(flat_provider)
    collector.collect_and_store(flat_provider)
    history = collector.get_history()

    # Assert
    assert len(history) == 3
    for timestamp, kpis in history:
        assert isinstance(timestamp, datetime)
        assert kpis == {"balance": 100.0, "profit": 50.0}


def test_get_history_returns_empty_list_initially():
    """Test get_history() returns empty list for new collector."""
    # Arrange
    collector = KPICollector()

    # Act
    history = collector.get_history()

    # Assert
    assert history == []


def test_get_history_with_since_filters_entries(flat_provider):
    """Test get_history(since=datetime) filters old entries."""
    # Arrange
    collector = KPICollector()

    # Act - add first entry
    collector.collect_and_store(flat_provider)

    # Set cutoff after first entry
    import time
    time.sleep(0.01)
    cutoff = datetime.now()
    time.sleep(0.01)

    # Add entries after cutoff
    collector.collect_and_store(flat_provider)
    collector.collect_and_store(flat_provider)

    # Get filtered history
    history = collector.get_history(since=cutoff)

    # Assert - should get 2 entries (after cutoff)
    assert len(history) == 2


def test_get_history_without_since_returns_all(flat_provider):
    """Test get_history() without since returns all entries."""
    # Arrange
    collector = KPICollector()

    # Act
    collector.collect_and_store(flat_provider)
    collector.collect_and_store(flat_provider)
    history = collector.get_history()

    # Assert
    assert len(history) == 2


def test_get_history_preserves_chronological_order(flat_provider):
    """Test get_history() maintains chronological order."""
    # Arrange
    collector = KPICollector()

    # Act
    collector.collect_and_store(flat_provider)
    import time
    time.sleep(0.01)
    collector.collect_and_store(flat_provider)
    time.sleep(0.01)
    collector.collect_and_store(flat_provider)

    history = collector.get_history()

    # Assert
    assert len(history) == 3
    timestamps = [ts for ts, _ in history]
    assert timestamps == sorted(timestamps)  # Chronological order


def test_clear_history_empties_history_list(flat_provider):
    """Test clear_history() removes all entries."""
    # Arrange
    collector = KPICollector()
    collector.collect_and_store(flat_provider)
    collector.collect_and_store(flat_provider)

    # Act
    collector.clear_history()
    history = collector.get_history()

    # Assert
    assert history == []


def test_clear_history_on_empty_collector():
    """Test clear_history() on empty collector (no error)."""
    # Arrange
    collector = KPICollector()

    # Act
    collector.clear_history()
    history = collector.get_history()

    # Assert
    assert history == []


def test_collect_with_empty_kpis_provider(empty_provider):
    """Test collect() with provider returning empty KPI dict."""
    # Arrange
    collector = KPICollector()

    # Act
    result = collector.collect(empty_provider)

    # Assert
    assert result == {}


def test_collect_with_empty_subproviders_dict(empty_subprovider):
    """Test collect() with provider returning empty subproviders dict."""
    # Arrange
    collector = KPICollector()

    # Act
    result = collector.collect(empty_subprovider)

    # Assert
    assert result == {"balance": 100.0}


def test_collect_preserves_numeric_types(numeric_provider):
    """Test collect() preserves various numeric values."""
    # Arrange
    collector = KPICollector()

    # Act
    result = collector.collect(numeric_provider)

    # Assert
    assert result["int_value"] == 100.0
    assert result["float_value"] == 123.456
    assert result["zero"] == 0.0
    assert result["negative"] == -50.5


def test_get_history_returns_copy_not_reference(flat_provider):
    """Test get_history() returns copy, not internal reference."""
    # Arrange
    collector = KPICollector()
    collector.collect_and_store(flat_provider)

    # Act
    history1 = collector.get_history()
    history2 = collector.get_history()

    # Assert
    assert history1 == history2
    assert history1 is not history2  # Different list objects


def test_collect_and_store_with_nested_data(nested_provider):
    """Test collect_and_store() correctly stores nested KPI structure."""
    # Arrange
    collector = KPICollector()

    # Act
    collector.collect_and_store(nested_provider)
    history = collector.get_history()

    # Assert
    assert len(history) == 1
    _, kpis = history[0]
    assert kpis["balance"] == 100.0
    assert kpis["portfolio"]["sub_balance"] == 25.0
