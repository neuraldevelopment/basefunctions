"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich
  Project : basefunctions
  Copyright (c) by neuraldevelopment
  All rights reserved.
  Description:
  OHLCV data generator for financial market data with pandas DataFrame output
 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Optional
import datetime
import pandas as pd
import numpy as np
import basefunctions

# -------------------------------------------------------------
# DEFINITIONS REGISTRY
# -------------------------------------------------------------

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------

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
        self.logger = basefunctions.get_logger(__name__)

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
    ) -> pd.DataFrame:
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
        pd.DataFrame
            DataFrame with columns: Date, Open, High, Low, Close, Volume, Ticker

        Raises
        ------
        ValueError
            If dates or parameters are invalid
        """
        # Input validation
        if not ticker or not isinstance(ticker, str):
            raise ValueError("ticker must be a non-empty string")

        # Parse and validate dates
        try:
            parsed_start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
        except (ValueError, TypeError) as e:
            raise ValueError(f"start_date must be in format 'YYYY-MM-DD', got: {start_date}") from e

        if end_date is None:
            # Use yesterday as default end date
            parsed_end_date = (datetime.datetime.now() - datetime.timedelta(days=1)).date()
        else:
            try:
                parsed_end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
            except (ValueError, TypeError) as e:
                raise ValueError(f"end_date must be in format 'YYYY-MM-DD', got: {end_date}") from e

        if parsed_start_date >= parsed_end_date:
            raise ValueError("start_date must be before end_date")

        if initial_price <= 0:
            raise ValueError("initial_price must be positive")

        if volatility < 0:
            raise ValueError("volatility must be non-negative")

        if volume_base <= 0:
            raise ValueError("volume_base must be positive")

        try:
            # Generate date range
            date_range = pd.date_range(start=parsed_start_date, end=parsed_end_date, freq="D")
            num_days = len(date_range)

            if num_days == 0:
                raise ValueError("Date range resulted in zero trading days")

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
                    open_price = ohlc_data[i - 1]["Close"]

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
                volume_multiplier = 1 + price_change * 2  # Higher volume on bigger moves
                volume = int(volume_base * volume_multiplier * np.random.uniform(0.5, 2.0))

                ohlc_data.append(
                    {
                        "Date": date_range[i].date(),
                        "Open": round(open_price, 2),
                        "High": round(high_price, 2),
                        "Low": round(low_price, 2),
                        "Close": round(close_price, 2),
                        "Volume": volume,
                        "Ticker": ticker,
                    }
                )

            # Create DataFrame
            df = pd.DataFrame(ohlc_data)

            # Set Date as index
            df.set_index("Date", inplace=True)

            self.logger.debug(f"Generated {len(df)} OHLCV records for {ticker}")

            return df

        except Exception as e:
            self.logger.error(f"Error generating OHLCV data for {ticker}: {str(e)}")
            raise

    def generate_multiple(
        self, tickers: list, start_date: str = "2020-01-01", end_date: Optional[str] = None, **kwargs
    ) -> pd.DataFrame:
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
        pd.DataFrame
            Combined DataFrame with all tickers

        Raises
        ------
        ValueError
            If tickers list is empty or invalid
        """
        if not tickers or not isinstance(tickers, list):
            raise ValueError("tickers must be a non-empty list")

        all_data = []

        for ticker in tickers:
            try:
                ticker_data = self.generate(ticker, start_date, end_date, **kwargs)
                all_data.append(ticker_data)

            except Exception as e:
                self.logger.warning(f"Failed to generate data for {ticker}: {str(e)}")
                continue

        if not all_data:
            raise ValueError("No valid data generated for any ticker")

        # Combine all DataFrames
        combined_df = pd.concat(all_data, ignore_index=False)
        combined_df.sort_values(["Date", "Ticker"], inplace=True)

        self.logger.info(f"Generated data for {len(tickers)} tickers")

        return combined_df

    def get_summary_stats(self, df: pd.DataFrame) -> dict:
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
                "min_low": df["Low"].min(),
                "max_high": df["High"].max(),
                "avg_close": df["Close"].mean(),
                "total_volume": df["Volume"].sum(),
            },
        }

        if "Ticker" in df.columns:
            stats["tickers"] = df["Ticker"].unique().tolist()
            stats["ticker_count"] = len(stats["tickers"])

        return stats
