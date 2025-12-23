"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Tests for type protocols. Verifies structural typing contracts and
 duck-typing behavior for Protocol definitions.
 Log:
 v1.0.0 : Initial test implementation for MetricsSource Protocol
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
# Standard Library
from typing import get_type_hints

# Third-party
import pytest

# Project modules
from basefunctions.utils.protocols import MetricsSource


# =============================================================================
# TEST CLASSES - MOCK IMPLEMENTATIONS
# =============================================================================
class ValidPortfolio:
    """Mock Portfolio implementing MetricsSource without inheritance."""

    def __init__(self) -> None:
        """Initialize portfolio with sample metrics."""
        self.total_return = 0.15
        self.sharpe_ratio = 1.8

    def get_kpis(self) -> dict[str, float]:
        """Return portfolio KPIs."""
        return {
            "total_return": self.total_return,
            "sharpe_ratio": self.sharpe_ratio,
            "max_drawdown": -0.12,
        }


class ValidBacktestResult:
    """Mock BacktestResult implementing MetricsSource without inheritance."""

    def __init__(self) -> None:
        """Initialize backtest result with sample metrics."""
        self.win_rate = 0.62
        self.profit_factor = 1.85

    def get_kpis(self) -> dict[str, float]:
        """Return backtest KPIs."""
        return {
            "win_rate": self.win_rate,
            "profit_factor": self.profit_factor,
            "total_trades": 245.0,
        }


class InvalidNoMethod:
    """Class WITHOUT get_kpis method - should NOT match protocol."""

    def __init__(self) -> None:
        """Initialize without required method."""
        self.value = 42.0


class InvalidWrongSignature:
    """Class with WRONG get_kpis signature - should NOT match protocol."""

    def get_kpis(self, param: str) -> dict[str, float]:
        """Wrong signature - requires parameter."""
        return {"value": 1.0}


# =============================================================================
# PROTOCOL IMPORT TESTS
# =============================================================================
def test_metricssource_protocol_can_be_imported():
    """Test MetricsSource Protocol is importable."""
    # Arrange & Act
    from basefunctions.utils.protocols import MetricsSource

    # Assert
    assert MetricsSource is not None
    assert hasattr(MetricsSource, "get_kpis")


def test_metricssource_protocol_has_correct_method_signature():
    """Test MetricsSource Protocol defines get_kpis with correct signature."""
    # Arrange
    type_hints = get_type_hints(MetricsSource.get_kpis)

    # Act
    return_type = type_hints.get("return")

    # Assert
    assert return_type is not None
    assert str(return_type) == "dict[str, float]"


# =============================================================================
# DUCK TYPING TESTS - VALID IMPLEMENTATIONS
# =============================================================================
def test_valid_portfolio_implements_protocol_without_inheritance():
    """Test Portfolio class implements Protocol via duck-typing."""
    # Arrange
    portfolio = ValidPortfolio()

    # Act
    kpis = portfolio.get_kpis()

    # Assert
    assert isinstance(kpis, dict)
    assert all(isinstance(k, str) for k in kpis.keys())
    assert all(isinstance(v, float) for v in kpis.values())
    assert "total_return" in kpis
    assert "sharpe_ratio" in kpis
    assert "max_drawdown" in kpis


def test_valid_backtest_result_implements_protocol_without_inheritance():
    """Test BacktestResult class implements Protocol via duck-typing."""
    # Arrange
    result = ValidBacktestResult()

    # Act
    kpis = result.get_kpis()

    # Assert
    assert isinstance(kpis, dict)
    assert all(isinstance(k, str) for k in kpis.keys())
    assert all(isinstance(v, float) for v in kpis.values())
    assert "win_rate" in kpis
    assert "profit_factor" in kpis
    assert "total_trades" in kpis


def test_portfolio_get_kpis_returns_correct_values():
    """Test Portfolio get_kpis returns expected values."""
    # Arrange
    portfolio = ValidPortfolio()

    # Act
    kpis = portfolio.get_kpis()

    # Assert
    assert kpis["total_return"] == 0.15
    assert kpis["sharpe_ratio"] == 1.8
    assert kpis["max_drawdown"] == -0.12


def test_backtest_result_get_kpis_returns_correct_values():
    """Test BacktestResult get_kpis returns expected values."""
    # Arrange
    result = ValidBacktestResult()

    # Act
    kpis = result.get_kpis()

    # Assert
    assert kpis["win_rate"] == 0.62
    assert kpis["profit_factor"] == 1.85
    assert kpis["total_trades"] == 245.0


# =============================================================================
# TYPE COMPLIANCE TESTS
# =============================================================================
def test_protocol_accepts_valid_implementation_in_function():
    """Test function with MetricsSource type hint accepts valid implementation."""
    # Arrange
    def display_metrics(source: MetricsSource) -> dict[str, float]:
        """Function accepting MetricsSource Protocol."""
        return source.get_kpis()

    portfolio = ValidPortfolio()

    # Act
    result = display_metrics(portfolio)

    # Assert
    assert isinstance(result, dict)
    assert len(result) > 0
    assert "total_return" in result


def test_multiple_implementations_work_with_same_function():
    """Test function accepts different Protocol implementations."""
    # Arrange
    def get_first_metric(source: MetricsSource) -> float:
        """Extract first metric value from source."""
        kpis = source.get_kpis()
        return next(iter(kpis.values()))

    portfolio = ValidPortfolio()
    backtest = ValidBacktestResult()

    # Act
    portfolio_metric = get_first_metric(portfolio)
    backtest_metric = get_first_metric(backtest)

    # Assert
    assert isinstance(portfolio_metric, float)
    assert isinstance(backtest_metric, float)
    assert portfolio_metric == 0.15  # total_return
    assert backtest_metric == 0.62  # win_rate


# =============================================================================
# NEGATIVE TESTS - INVALID IMPLEMENTATIONS
# =============================================================================
def test_class_without_get_kpis_method_missing_attribute():
    """Test class without get_kpis method lacks required attribute."""
    # Arrange
    invalid = InvalidNoMethod()

    # Act & Assert
    assert not hasattr(invalid, "get_kpis")


def test_class_with_wrong_signature_has_different_method():
    """Test class with wrong signature has incompatible method."""
    # Arrange
    invalid = InvalidWrongSignature()

    # Act & Assert
    # Method exists but signature is incompatible
    assert hasattr(invalid, "get_kpis")
    # Calling without param should raise TypeError
    with pytest.raises(TypeError, match="missing 1 required positional argument"):
        invalid.get_kpis()  # type: ignore[call-arg]


# =============================================================================
# EDGE CASE TESTS
# =============================================================================
def test_get_kpis_with_empty_dict_is_valid():
    """Test get_kpis returning empty dict is valid (edge case)."""

    # Arrange
    class EmptyMetrics:
        """Mock class returning empty metrics."""

        def get_kpis(self) -> dict[str, float]:
            """Return empty KPIs."""
            return {}

    empty = EmptyMetrics()

    # Act
    kpis = empty.get_kpis()

    # Assert
    assert isinstance(kpis, dict)
    assert len(kpis) == 0


def test_get_kpis_with_single_metric_is_valid():
    """Test get_kpis returning single metric is valid (edge case)."""

    # Arrange
    class SingleMetric:
        """Mock class returning single metric."""

        def get_kpis(self) -> dict[str, float]:
            """Return single KPI."""
            return {"value": 42.0}

    single = SingleMetric()

    # Act
    kpis = single.get_kpis()

    # Assert
    assert isinstance(kpis, dict)
    assert len(kpis) == 1
    assert kpis["value"] == 42.0


def test_get_kpis_with_many_metrics_is_valid():
    """Test get_kpis returning many metrics is valid (edge case)."""

    # Arrange
    class ManyMetrics:
        """Mock class returning many metrics."""

        def get_kpis(self) -> dict[str, float]:
            """Return many KPIs."""
            return {f"metric_{i}": float(i) for i in range(100)}

    many = ManyMetrics()

    # Act
    kpis = many.get_kpis()

    # Assert
    assert isinstance(kpis, dict)
    assert len(kpis) == 100
    assert all(isinstance(v, float) for v in kpis.values())


def test_get_kpis_with_negative_values_is_valid():
    """Test get_kpis with negative values is valid (drawdown, losses)."""

    # Arrange
    class NegativeMetrics:
        """Mock class with negative metrics."""

        def get_kpis(self) -> dict[str, float]:
            """Return negative KPIs."""
            return {
                "drawdown": -0.35,
                "loss": -1250.50,
                "negative_skew": -0.8,
            }

    negative = NegativeMetrics()

    # Act
    kpis = negative.get_kpis()

    # Assert
    assert all(v < 0 for v in kpis.values())
    assert kpis["drawdown"] == -0.35
    assert kpis["loss"] == -1250.50


def test_get_kpis_with_zero_values_is_valid():
    """Test get_kpis with zero values is valid (neutral performance)."""

    # Arrange
    class ZeroMetrics:
        """Mock class with zero metrics."""

        def get_kpis(self) -> dict[str, float]:
            """Return zero KPIs."""
            return {
                "return": 0.0,
                "alpha": 0.0,
                "beta": 0.0,
            }

    zero = ZeroMetrics()

    # Act
    kpis = zero.get_kpis()

    # Assert
    assert all(v == 0.0 for v in kpis.values())


def test_get_kpis_with_extreme_values_is_valid():
    """Test get_kpis with extreme float values is valid (boundaries)."""

    # Arrange
    class ExtremeMetrics:
        """Mock class with extreme metrics."""

        def get_kpis(self) -> dict[str, float]:
            """Return extreme KPIs."""
            return {
                "very_large": 1e100,
                "very_small": 1e-100,
                "max_float": float("inf"),
                "min_float": float("-inf"),
            }

    extreme = ExtremeMetrics()

    # Act
    kpis = extreme.get_kpis()

    # Assert
    assert kpis["very_large"] == 1e100
    assert kpis["very_small"] == 1e-100
    assert kpis["max_float"] == float("inf")
    assert kpis["min_float"] == float("-inf")
