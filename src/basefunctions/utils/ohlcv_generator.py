"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich

 Project : basefunctions

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 OHLCV data generator for financial market data with pandas DataFrame output

 Log:
 v1.0 : Initial implementation
 v1.0.1 : Format correction - lowercase columns, adjusted_close added, ticker removed from DataFrame
 v1.0.2 : Complete format overhaul - dict return with data/metadata/errors structure
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Optional
import datetime

import numpy as np
import pandas as pd

from basefunctions.utils.logging import setup_logger, get_logger

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# LOGGING INITIALIZE
# -------------------------------------------------------------
setup_logger(__name__)

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


class OHLCVGenerator:
    """
    Generate OHLCV (Open, High, Low, Close, Volume) financial data.

    Creates realistic financial market data for testing and simulation purposes.
    Uses random walk model with configurable volatility and trend parameters.
    """

    def __init__(self, seed: Optional[int] = None) -> None:
        """
        Initialize OHLCV data generator.

        Parameters
        ----------
        seed : Optional[int], optional
            Random seed for reproducible data generation
        """
        self.logger = get_logger(__name__)

        if seed is not None:
            np.random.seed(seed)

        self.logger.debug(f"OHLCVGenerator initialized with seed: {seed}")

    def generate(
        self,
        ticker: str = "AAPL.XETRA",
        start_date: str = "2020-01-01",
        end_date: Optional[str] = None,
        initial_price: float = 100.0,
        volatility: float = 0.02,
        trend: float = 0.0001,
        volume_base: int = 1000000,
    ) -> dict:
        """
        Generate OHLCV data for specified ticker and date range.

        Parameters
        ----------
        ticker : str, optional
            Stock ticker symbol (e.g., 'AAPL', 'MSFT'), by default "AAPL.XETRA"
        start_date : str, optional
            Start date for data generation in format 'YYYY-MM-DD', by default "2020-01-01"
        end_date : Optional[str], optional
            End date for data generation in format 'YYYY-MM-DD', by default None (yesterday)
        initial_price : float, optional
            Starting price for the ticker, by default 100.0
        volatility : float, optional
            Daily volatility (standard deviation), by default 0.02
        trend : float, optional
            Daily trend (drift), by default 0.0001
        volume_base : int, optional
            Base volume for calculations, by default 1000000

        Returns
        -------
        dict
            Dictionary with structure:
            {
                'data': {ticker: DataFrame},
                'metadata': {...},
                'errors': {}
            }

        Raises
        ------
        ValueError
            If dates or parameters are invalid
        """
        timestamp = datetime.datetime.now().isoformat()

        # Input validation
        if not ticker or not isinstance(ticker, str):
            return {
                "data": {},
                "metadata": {
                    "total_requested": 1,
                    "successful": 0,
                    "failed": 1,
                    "sources": {},
                    "source_breakdown": {"synthetic": 0},
                    "timestamp": timestamp,
                },
                "errors": {ticker: "ticker must be a non-empty string"},
            }

        # Parse and validate dates
        try:
            parsed_start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return {
                "data": {},
                "metadata": {
                    "total_requested": 1,
                    "successful": 0,
                    "failed": 1,
                    "sources": {},
                    "source_breakdown": {"synthetic": 0},
                    "timestamp": timestamp,
                },
                "errors": {ticker: f"start_date must be in format 'YYYY-MM-DD', got: {start_date}"},
            }

        if end_date is None:
            parsed_end_date = (datetime.datetime.now() - datetime.timedelta(days=1)).date()
        else:
            try:
                parsed_end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
            except (ValueError, TypeError):
                return {
                    "data": {},
                    "metadata": {
                        "total_requested": 1,
                        "successful": 0,
                        "failed": 1,
                        "sources": {},
                        "source_breakdown": {"synthetic": 0},
                        "timestamp": timestamp,
                    },
                    "errors": {ticker: f"end_date must be in format 'YYYY-MM-DD', got: {end_date}"},
                }

        if parsed_start_date >= parsed_end_date:
            return {
                "data": {},
                "metadata": {
                    "total_requested": 1,
                    "successful": 0,
                    "failed": 1,
                    "sources": {},
                    "source_breakdown": {"synthetic": 0},
                    "timestamp": timestamp,
                },
                "errors": {ticker: "start_date must be before end_date"},
            }

        if initial_price <= 0:
            return {
                "data": {},
                "metadata": {
                    "total_requested": 1,
                    "successful": 0,
                    "failed": 1,
                    "sources": {},
                    "source_breakdown": {"synthetic": 0},
                    "timestamp": timestamp,
                },
                "errors": {ticker: "initial_price must be positive"},
            }

        if volatility < 0:
            return {
                "data": {},
                "metadata": {
                    "total_requested": 1,
                    "successful": 0,
                    "failed": 1,
                    "sources": {},
                    "source_breakdown": {"synthetic": 0},
                    "timestamp": timestamp,
                },
                "errors": {ticker: "volatility must be non-negative"},
            }

        if volume_base <= 0:
            return {
                "data": {},
                "metadata": {
                    "total_requested": 1,
                    "successful": 0,
                    "failed": 1,
                    "sources": {},
                    "source_breakdown": {"synthetic": 0},
                    "timestamp": timestamp,
                },
                "errors": {ticker: "volume_base must be positive"},
            }

        try:
            # Generate date range
            date_range = pd.date_range(start=parsed_start_date, end=parsed_end_date, freq="D")
            num_days = len(date_range)

            if num_days == 0:
                return {
                    "data": {},
                    "metadata": {
                        "total_requested": 1,
                        "successful": 0,
                        "failed": 1,
                        "sources": {},
                        "source_breakdown": {"synthetic": 0},
                        "timestamp": timestamp,
                    },
                    "errors": {ticker: "Date range resulted in zero trading days"},
                }

            # Generate price movements using random walk
            returns = np.random.normal(trend, volatility, num_days)

            # Calculate cumulative prices
            cumulative_returns = np.cumsum(returns)
            prices = initial_price * np.exp(cumulative_returns)

            # Generate OHLC data
            ohlc_data = []

            for i, price in enumerate(prices):
                if i == 0:
                    open_price = initial_price
                else:
                    open_price = ohlc_data[i - 1]["close"]

                # Generate intraday volatility
                intraday_vol = volatility * np.random.uniform(0.5, 1.5)

                # High and Low relative to the closing price
                high_factor = 1 + abs(np.random.normal(0, intraday_vol))
                low_factor = 1 - abs(np.random.normal(0, intraday_vol))

                close_price = price
                high_price = max(open_price, close_price) * high_factor
                low_price = min(open_price, close_price) * low_factor

                # Ensure logical OHLC relationships
                high_price = max(high_price, open_price, close_price)
                low_price = min(low_price, open_price, close_price)

                # Generate volume based on price movement
                price_change = abs(close_price - open_price) / open_price
                volume_multiplier = 1 + price_change * 2
                volume = int(volume_base * volume_multiplier * np.random.uniform(0.5, 2.0))

                ohlc_data.append(
                    {
                        "date": date_range[i],
                        "open": round(open_price, 2),
                        "high": round(high_price, 2),
                        "low": round(low_price, 2),
                        "close": round(close_price, 2),
                        "adjusted_close": round(close_price, 2),
                        "volume": volume,
                    }
                )

            # Create DataFrame
            df = pd.DataFrame(ohlc_data)
            df.set_index("date", inplace=True)

            return {
                "data": {ticker: df},
                "metadata": {
                    "total_requested": 1,
                    "successful": 1,
                    "failed": 0,
                    "sources": {ticker: "synthetic"},
                    "source_breakdown": {"synthetic": 1},
                    "timestamp": timestamp,
                },
                "errors": {},
            }

        except Exception as e:
            self.logger.error(f"Error generating OHLCV data for {ticker}: {str(e)}")
            return {
                "data": {},
                "metadata": {
                    "total_requested": 1,
                    "successful": 0,
                    "failed": 1,
                    "sources": {},
                    "source_breakdown": {"synthetic": 0},
                    "timestamp": timestamp,
                },
                "errors": {ticker: str(e)},
            }

    def generate_multiple(
        self,
        tickers: list,
        start_date: str = "2020-01-01",
        end_date: Optional[str] = None,
        **kwargs,
    ) -> dict:
        """
        Generate OHLCV data for multiple tickers.

        Parameters
        ----------
        tickers : list
            List of ticker symbols
        start_date : str, optional
            Start date for data generation in format 'YYYY-MM-DD', by default "2020-01-01"
        end_date : Optional[str], optional
            End date for data generation in format 'YYYY-MM-DD', by default None (yesterday)
        **kwargs
            Additional parameters passed to generate() method

        Returns
        -------
        dict
            Dictionary with structure:
            {
                'data': {ticker: DataFrame, ...},
                'metadata': {...},
                'errors': {...}
            }

        Raises
        ------
        ValueError
            If tickers list is empty or invalid
        """
        timestamp = datetime.datetime.now().isoformat()

        if not tickers or not isinstance(tickers, list):
            return {
                "data": {},
                "metadata": {
                    "total_requested": 0,
                    "successful": 0,
                    "failed": 0,
                    "sources": {},
                    "source_breakdown": {"synthetic": 0},
                    "timestamp": timestamp,
                },
                "errors": {"_global": "tickers must be a non-empty list"},
            }

        data = {}
        errors = {}
        sources = {}
        successful = 0
        failed = 0

        for ticker in tickers:
            try:
                result = self.generate(ticker, start_date, end_date, **kwargs)

                if result["data"]:
                    data[ticker] = result["data"][ticker]
                    sources[ticker] = "synthetic"
                    successful += 1
                else:
                    errors[ticker] = result["errors"].get(ticker, "Unknown error")
                    failed += 1

            except Exception as e:
                self.logger.warning(f"Failed to generate data for {ticker}: {str(e)}")
                errors[ticker] = str(e)
                failed += 1

        return {
            "data": data,
            "metadata": {
                "total_requested": len(tickers),
                "successful": successful,
                "failed": failed,
                "sources": sources,
                "source_breakdown": {"synthetic": successful},
                "timestamp": timestamp,
            },
            "errors": errors,
        }

    def get_summary_stats(self, df: "pd.DataFrame") -> dict:
        """
        Calculate summary statistics for generated OHLCV data.

        Parameters
        ----------
        df : pd.DataFrame
            OHLCV DataFrame

        Returns
        -------
        dict
            Summary statistics
        """
        if df.empty:
            return {}

        stats = {
            "total_records": len(df),
            "date_range": {"start": df.index.min(), "end": df.index.max()},
            "price_stats": {
                "min_low": df["low"].min(),
                "max_high": df["high"].max(),
                "avg_close": df["close"].mean(),
                "total_volume": df["volume"].sum(),
            },
        }

        return stats
