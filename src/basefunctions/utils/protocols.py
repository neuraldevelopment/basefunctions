"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Type protocols for interface definitions. Provides structural typing
 contracts that enable duck-typing with full IDE and type-checker support.
 Log:
 v1.0.0 : Initial implementation - MetricsSource Protocol
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
from typing import Protocol


# =============================================================================
# TYPE DEFINITIONS
# =============================================================================
class MetricsSource(Protocol):
    """
    Protocol for objects that provide Key Performance Indicator (KPI) metrics.

    This protocol defines a standard interface for objects that can report
    performance metrics as a dictionary. Classes implementing this protocol
    must provide a `get_kpis()` method that returns metrics as key-value pairs.

    The protocol uses structural typing (duck-typing) which means any class
    that implements the required method signature will be considered compatible,
    regardless of explicit inheritance. This provides flexibility while
    maintaining type safety with IDE autocomplete and static type checking.

    Notes
    -----
    This protocol is designed to be implemented by classes that track and
    report performance metrics, such as:
    - Portfolio tracking systems (total return, volatility, Sharpe ratio, etc.)
    - Backtesting results (win rate, profit factor, max drawdown, etc.)
    - Trading strategies (signal accuracy, trades per day, etc.)

    The protocol does NOT enforce specific metric names or values - that is
    left to the implementing class. This allows maximum flexibility for
    different use cases while maintaining a consistent interface.

    Examples
    --------
    Portfolio implementation example:

    >>> class Portfolio:
    ...     def __init__(self):
    ...         self.total_return = 0.15
    ...         self.sharpe_ratio = 1.8
    ...
    ...     def get_kpis(self) -> dict[str, float]:
    ...         return {
    ...             'total_return': self.total_return,
    ...             'sharpe_ratio': self.sharpe_ratio,
    ...             'max_drawdown': -0.12
    ...         }

    BacktestResult implementation example:

    >>> class BacktestResult:
    ...     def __init__(self):
    ...         self.win_rate = 0.62
    ...         self.profit_factor = 1.85
    ...
    ...     def get_kpis(self) -> dict[str, float]:
    ...         return {
    ...             'win_rate': self.win_rate,
    ...             'profit_factor': self.profit_factor,
    ...             'total_trades': 245.0
    ...         }

    Using the protocol for type hints:

    >>> def display_metrics(source: MetricsSource) -> None:
    ...     metrics = source.get_kpis()
    ...     for key, value in metrics.items():
    ...         print(f"{key}: {value:.2f}")
    """

    def get_kpis(self) -> dict[str, float]:
        """
        Return Key Performance Indicators as a dictionary.

        This method must be implemented by any class claiming to be a
        MetricsSource. The returned dictionary should contain metric names
        as keys and their corresponding numerical values as floats.

        Returns
        -------
        dict[str, float]
            Dictionary mapping metric names to their values. Keys are
            descriptive metric names (e.g., 'total_return', 'sharpe_ratio').
            Values are the corresponding numerical metrics as floats.

        Notes
        -----
        The specific metrics returned are implementation-dependent. Common
        patterns include:
        - Financial metrics: return, volatility, drawdown, Sharpe ratio
        - Trading metrics: win rate, profit factor, total trades
        - Performance metrics: accuracy, precision, recall

        Examples
        --------
        >>> portfolio = Portfolio()
        >>> kpis = portfolio.get_kpis()
        >>> kpis['sharpe_ratio']
        1.8
        """
        ...
