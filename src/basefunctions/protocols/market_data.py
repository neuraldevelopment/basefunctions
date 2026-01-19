"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Abstract interface for market data access in portfolio and backtesting
 systems. Enables portfolio functions to work independently from concrete
 data providers (backtest engines, live trading, mock data).
 Log:
 v1.0.0 : Initial implementation
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
from typing import Dict, Protocol, runtime_checkable

import pandas as pd


# =============================================================================
# PROTOCOLS
# =============================================================================
@runtime_checkable
class MarketDataProvider(Protocol):
    """
    Abstract interface for market data access.

    This protocol defines the contract that market data providers must
    implement to work with portfolio functions. It enables structural
    typing (duck-typing) with type-checker support, allowing portfolio
    code to remain independent from concrete data provider implementations.

    The protocol supports both current and historical price lookups,
    enabling backtesting, live trading, and mock data implementations
    to work seamlessly without code changes.

    Notes
    -----
    This protocol is designed for implementations such as:
    - Backtest engines: Historical price data from bars
    - Live trading systems: Real-time price feeds
    - Mock data providers: Test fixtures for unit tests
    - Market data feeds: External data source integrations

    The protocol uses runtime_checkable for structural typing, meaning
    any class that implements these methods will be compatible, regardless
    of explicit inheritance.

    Examples
    --------
    Backtest implementation example:

    >>> class BacktestDataProvider:
    ...     def __init__(self, data_df):
    ...         self.data = data_df
    ...         self._current_bar = 0
    ...
    ...     def get_current_prices(self, column: str = 'close') -> dict[str, float]:
    ...         bar_data = self.data.iloc[self._current_bar]
    ...         return bar_data[column].to_dict()
    ...
    ...     def get_prices_at_bar(self, bar: int, column: str = 'close') -> dict[str, float]:
    ...         bar_data = self.data.iloc[bar]
    ...         return bar_data[column].to_dict()
    ...
    ...     @property
    ...     def current_bar(self) -> int:
    ...         return self._current_bar
    ...
    ...     @property
    ...     def current_date(self) -> pd.Timestamp:
    ...         return self.data.index[self._current_bar]

    Using the protocol for portfolio functions:

    >>> def calculate_portfolio_value(
    ...     provider: MarketDataProvider,
    ...     holdings: dict[str, float]
    ... ) -> float:
    ...     prices = provider.get_current_prices()
    ...     return sum(holdings[sym] * prices.get(sym, 0) for sym in holdings)
    """

    def get_current_prices(self, column: str = "close") -> Dict[str, float]:
        """
        Get current prices for all symbols.

        Returns the prices for the current bar in the data stream. Used
        to obtain up-to-date market prices for portfolio valuation and
        position management.

        Parameters
        ----------
        column : str, default "close"
            Column name in the market data to retrieve prices from.
            Common values are "close", "open", "high", "low", but
            custom columns are supported.

        Returns
        -------
        Dict[str, float]
            Dictionary mapping symbol names to their current prices.
            Format: {"AAPL": 150.25, "MSFT": 380.50, ...}

        Notes
        -----
        The returned prices correspond to the bar indicated by the
        current_bar property. All symbols in the data source are
        included in the result.

        Examples
        --------
        >>> provider = BacktestDataProvider(ohlcv_data)
        >>> prices = provider.get_current_prices()
        >>> print(prices)
        {'AAPL': 150.25, 'MSFT': 380.50}

        Using custom column:

        >>> prices_high = provider.get_current_prices(column='high')
        >>> print(prices_high)
        {'AAPL': 151.00, 'MSFT': 381.25}
        """
        ...

    def get_prices_at_bar(
        self, bar: int, column: str = "close"
    ) -> Dict[str, float]:
        """
        Get historical prices at a specific bar index.

        Returns prices for a past bar in the data stream. Used for
        historical price lookups and backtesting scenarios where
        portfolio functions need to inspect prices at past points
        in time.

        Parameters
        ----------
        bar : int
            Zero-based bar index in the historical data stream.
            Must be >= 0 and < total bars available.
        column : str, default "close"
            Column name in the market data to retrieve prices from.
            Common values are "close", "open", "high", "low", but
            custom columns are supported.

        Returns
        -------
        Dict[str, float]
            Dictionary mapping symbol names to their prices at the
            specified bar. Format: {"AAPL": 150.25, "MSFT": 380.50, ...}

        Raises
        ------
        IndexError
            If bar index is out of range (negative or >= total bars)
        KeyError
            If column does not exist in the data source

        Notes
        -----
        Bar indexing is zero-based, with bar 0 being the oldest
        (first) bar and bar N-1 being the current bar at completion.

        Examples
        --------
        >>> provider = BacktestDataProvider(ohlcv_data)
        >>> prices_at_bar_10 = provider.get_prices_at_bar(10)
        >>> print(prices_at_bar_10)
        {'AAPL': 148.75, 'MSFT': 378.25}

        Using custom column:

        >>> high_prices_at_bar_50 = provider.get_prices_at_bar(50, column='high')
        >>> print(high_prices_at_bar_50)
        {'AAPL': 152.00, 'MSFT': 382.00}
        """
        ...

    @property
    def current_bar(self) -> int:
        """
        Current bar index in the data stream.

        Returns the zero-based index of the current bar being
        processed. This index corresponds to the bar whose prices
        are returned by get_current_prices().

        Returns
        -------
        int
            Zero-based index of the current bar. Value range is 0 to
            (total_bars - 1). At the start of a backtest or trading
            session, this is typically 0.

        Notes
        -----
        The current_bar index is a read-only property that reflects
        the internal state of the data provider. Portfolio functions
        use this to track position in the data stream and detect
        the end of available data.

        Examples
        --------
        >>> provider = BacktestDataProvider(ohlcv_data)
        >>> print(provider.current_bar)
        0

        Tracking progress through backtest:

        >>> while provider.current_bar < len(data):
        ...     prices = provider.get_current_prices()
        ...     # Process portfolio at current bar
        ...     provider.advance_bar()  # Provider implementation detail
        """
        ...

    @property
    def current_date(self) -> pd.Timestamp:
        """
        Current date in the data stream.

        Returns the timestamp associated with the current bar. This
        represents the date (and optionally time) of the market data
        for the bar indicated by current_bar.

        Returns
        -------
        pd.Timestamp
            Timestamp corresponding to the current bar. Format depends
            on the data source (date only, datetime, etc.). Always a
            valid pandas Timestamp object.

        Notes
        -----
        The current_date is derived from the index of the underlying
        data source and advances as the provider processes bars.
        Portfolio functions use this to track timeline of events and
        match prices with historical dates.

        Examples
        --------
        >>> provider = BacktestDataProvider(ohlcv_data)
        >>> print(provider.current_date)
        2023-01-01 00:00:00

        Using in portfolio decision logic:

        >>> if provider.current_date >= pd.Timestamp('2023-06-01'):
        ...     # Make portfolio changes after June 1st
        ...     rebalance_portfolio()
        """
        ...
