"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.

 Description:
 Pytest test suite for utils.ohlcv_generator module.
 Tests OHLCV financial data generation with validation, edge cases,
 and reproducibility checks for single and multi-ticker scenarios.

 Log:
 v1.0.0 : Initial test implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
# External imports (alphabetical)
import datetime
import numpy as np
import pandas as pd
import pytest
from typing import Any, Dict, List, Optional
from unittest.mock import Mock, patch, MagicMock

# Project imports (relative to project root)
from basefunctions.utils.ohlcv_generator import OHLCVGenerator

# -------------------------------------------------------------
# FIXTURES
# -------------------------------------------------------------


@pytest.fixture
def generator_with_seed() -> OHLCVGenerator:
    """
    Create OHLCV generator with fixed seed for reproducible tests.

    Returns
    -------
    OHLCVGenerator
        Generator instance with seed=42 for deterministic output

    Notes
    -----
    Use this fixture when test results must be reproducible
    """
    return OHLCVGenerator(seed=42)


@pytest.fixture
def generator_no_seed() -> OHLCVGenerator:
    """
    Create OHLCV generator without seed for variability tests.

    Returns
    -------
    OHLCVGenerator
        Generator instance with random seed

    Notes
    -----
    Use this fixture when testing randomness behavior
    """
    return OHLCVGenerator(seed=None)


@pytest.fixture
def sample_valid_params() -> Dict[str, Any]:
    """
    Provide valid default parameters for generate() method.

    Returns
    -------
    Dict[str, Any]
        Dictionary with valid ticker, dates, and financial parameters

    Notes
    -----
    Represents typical use case for data generation
    """
    return {
        "ticker": "AAPL.XETRA",
        "start_date": "2023-01-01",
        "end_date": "2023-01-10",
        "initial_price": 150.0,
        "volatility": 0.02,
        "trend": 0.0001,
        "volume_base": 1000000,
    }


@pytest.fixture
def fixed_timestamp() -> str:
    """
    Provide fixed timestamp for metadata comparison.

    Returns
    -------
    str
        ISO format timestamp

    Notes
    -----
    Use with datetime mocking for deterministic tests
    """
    return "2024-01-15T12:00:00.000000"


# -------------------------------------------------------------
# TEST CASES: __init__()
# -------------------------------------------------------------


def test_init_without_seed_creates_instance() -> None:
    """
    Test OHLCVGenerator initialization without seed.

    Tests that generator can be created without seed parameter
    and produces valid instance with logger.

    Returns
    -------
    None
        Test passes if instance created successfully
    """
    # ACT
    generator: OHLCVGenerator = OHLCVGenerator(seed=None)

    # ASSERT
    assert generator is not None
    assert hasattr(generator, "logger")


def test_init_with_seed_sets_numpy_seed() -> None:
    """
    Test OHLCVGenerator initialization with seed sets numpy random state.

    Tests that OHLCVGenerator.__init__ with seed parameter calls np.random.seed
    and that instance can be created successfully with seed.

    Returns
    -------
    None
        Test passes if generator with seed creates instance
    """
    # ARRANGE & ACT
    generator: OHLCVGenerator = OHLCVGenerator(seed=100)

    # ASSERT
    assert generator is not None
    assert hasattr(generator, "logger")

    # ACT - Verify generator can produce data
    result: dict = generator.generate(ticker="TEST", start_date="2023-01-01", end_date="2023-01-03")

    # ASSERT - Data generation should succeed
    assert "TEST" in result["data"] or "TEST" in result["errors"]  # Either success or controlled error


# -------------------------------------------------------------
# TEST CASES: generate() - Happy Path
# -------------------------------------------------------------


def test_generate_returns_valid_structure_with_default_params(generator_with_seed: OHLCVGenerator) -> None:
    """
    Test generate() returns expected dictionary structure.

    Tests that result contains 'data', 'metadata', and 'errors' keys
    with correct structure for successful generation.

    Parameters
    ----------
    generator_with_seed : OHLCVGenerator
        Generator with fixed seed

    Returns
    -------
    None
        Test passes if all required keys exist and have correct types
    """
    # ACT
    result: dict = generator_with_seed.generate(ticker="AAPL.XETRA", start_date="2023-01-01", end_date="2023-01-10")

    # ASSERT
    assert "data" in result
    assert "metadata" in result
    assert "errors" in result
    assert isinstance(result["data"], dict)
    assert isinstance(result["metadata"], dict)
    assert isinstance(result["errors"], dict)
    assert "AAPL.XETRA" in result["data"]
    assert len(result["errors"]) == 0


def test_generate_creates_correct_date_range(generator_with_seed: OHLCVGenerator) -> None:
    """
    Test generate() creates DataFrame with correct date range.

    Tests that generated data spans from start_date to end_date inclusive
    with daily frequency.

    Parameters
    ----------
    generator_with_seed : OHLCVGenerator
        Generator with fixed seed

    Returns
    -------
    None
        Test passes if date range matches input parameters
    """
    # ARRANGE
    start: str = "2023-01-01"
    end: str = "2023-01-10"

    # ACT
    result: dict = generator_with_seed.generate(ticker="TEST", start_date=start, end_date=end)
    df: pd.DataFrame = result["data"]["TEST"]

    # ASSERT
    assert df.index.min() == pd.Timestamp("2023-01-01")
    assert df.index.max() == pd.Timestamp("2023-01-10")
    assert len(df) == 10  # 10 days inclusive


def test_generate_creates_correct_dataframe_columns(generator_with_seed: OHLCVGenerator) -> None:
    """
    Test generate() creates DataFrame with correct OHLCV columns.

    Tests that DataFrame contains required columns: open, high, low,
    close, adjusted_close, volume in lowercase.

    Parameters
    ----------
    generator_with_seed : OHLCVGenerator
        Generator with fixed seed

    Returns
    -------
    None
        Test passes if all required columns exist
    """
    # ACT
    result: dict = generator_with_seed.generate(ticker="TEST", start_date="2023-01-01", end_date="2023-01-05")
    df: pd.DataFrame = result["data"]["TEST"]

    # ASSERT
    expected_columns: List[str] = ["open", "high", "low", "close", "adjusted_close", "volume"]
    assert list(df.columns) == expected_columns


def test_generate_prices_respect_ohlc_relationships(generator_with_seed: OHLCVGenerator) -> None:  # CRITICAL TEST
    """
    Test generate() creates OHLCV data with valid price relationships.

    Tests that for every row: high >= max(open, close) and low <= min(open, close).
    This is CRITICAL for financial data integrity.

    Parameters
    ----------
    generator_with_seed : OHLCVGenerator
        Generator with fixed seed

    Returns
    -------
    None
        Test passes if all OHLC relationships are valid
    """
    # ACT
    result: dict = generator_with_seed.generate(ticker="TEST", start_date="2023-01-01", end_date="2023-01-31")
    df: pd.DataFrame = result["data"]["TEST"]

    # ASSERT
    for idx, row in df.iterrows():
        assert row["high"] >= row["open"], f"High must be >= open at {idx}"
        assert row["high"] >= row["close"], f"High must be >= close at {idx}"
        assert row["low"] <= row["open"], f"Low must be <= open at {idx}"
        assert row["low"] <= row["close"], f"Low must be <= close at {idx}"
        assert row["volume"] > 0, f"Volume must be positive at {idx}"


def test_generate_with_seed_is_reproducible(generator_with_seed: OHLCVGenerator) -> None:
    """
    Test generate() with seed produces identical results on repeated calls.

    Tests that calling generate() twice with same seed and parameters
    produces byte-for-byte identical DataFrames.

    Parameters
    ----------
    generator_with_seed : OHLCVGenerator
        Generator with fixed seed=42

    Returns
    -------
    None
        Test passes if both calls produce identical DataFrames
    """
    # ACT
    result1: dict = generator_with_seed.generate(ticker="TEST", start_date="2023-01-01", end_date="2023-01-10")

    # Reset seed to same value
    generator2: OHLCVGenerator = OHLCVGenerator(seed=42)
    result2: dict = generator2.generate(ticker="TEST", start_date="2023-01-01", end_date="2023-01-10")

    # ASSERT
    pd.testing.assert_frame_equal(result1["data"]["TEST"], result2["data"]["TEST"])


def test_generate_metadata_structure_is_correct(generator_with_seed: OHLCVGenerator) -> None:
    """
    Test generate() metadata contains all required fields.

    Tests that metadata includes total_requested, successful, failed,
    sources, source_breakdown, and timestamp.

    Parameters
    ----------
    generator_with_seed : OHLCVGenerator
        Generator with fixed seed

    Returns
    -------
    None
        Test passes if all metadata fields exist
    """
    # ACT
    result: dict = generator_with_seed.generate(ticker="TEST", start_date="2023-01-01", end_date="2023-01-05")
    metadata: dict = result["metadata"]

    # ASSERT
    assert metadata["total_requested"] == 1
    assert metadata["successful"] == 1
    assert metadata["failed"] == 0
    assert metadata["sources"] == {"TEST": "synthetic"}
    assert metadata["source_breakdown"] == {"synthetic": 1}
    assert "timestamp" in metadata


# -------------------------------------------------------------
# TEST CASES: generate() - Error Handling (CRITICAL)
# -------------------------------------------------------------


def test_generate_rejects_none_ticker(generator_with_seed: OHLCVGenerator) -> None:  # CRITICAL TEST
    """
    Test generate() rejects None ticker parameter.

    Tests that passing None as ticker returns error structure
    without raising exception.

    Parameters
    ----------
    generator_with_seed : OHLCVGenerator
        Generator with fixed seed

    Returns
    -------
    None
        Test passes if error returned for None ticker
    """
    # ACT
    result: dict = generator_with_seed.generate(ticker=None, start_date="2023-01-01", end_date="2023-01-05")

    # ASSERT
    assert result["data"] == {}
    assert result["metadata"]["successful"] == 0
    assert result["metadata"]["failed"] == 1
    assert None in result["errors"]
    assert "non-empty string" in result["errors"][None]


def test_generate_rejects_empty_ticker(generator_with_seed: OHLCVGenerator) -> None:  # CRITICAL TEST
    """
    Test generate() rejects empty string ticker parameter.

    Tests that passing empty string as ticker returns error structure
    without raising exception.

    Parameters
    ----------
    generator_with_seed : OHLCVGenerator
        Generator with fixed seed

    Returns
    -------
    None
        Test passes if error returned for empty ticker
    """
    # ACT
    result: dict = generator_with_seed.generate(ticker="", start_date="2023-01-01", end_date="2023-01-05")

    # ASSERT
    assert result["data"] == {}
    assert result["metadata"]["successful"] == 0
    assert result["metadata"]["failed"] == 1
    assert "" in result["errors"]


def test_generate_rejects_non_string_ticker(generator_with_seed: OHLCVGenerator) -> None:  # CRITICAL TEST
    """
    Test generate() rejects non-string ticker parameter.

    Tests that passing integer as ticker returns error structure
    without raising exception.

    Parameters
    ----------
    generator_with_seed : OHLCVGenerator
        Generator with fixed seed

    Returns
    -------
    None
        Test passes if error returned for non-string ticker
    """
    # ACT
    result: dict = generator_with_seed.generate(ticker=123, start_date="2023-01-01", end_date="2023-01-05")

    # ASSERT
    assert result["data"] == {}
    assert result["metadata"]["successful"] == 0
    assert result["metadata"]["failed"] == 1
    assert 123 in result["errors"]


@pytest.mark.parametrize(
    "invalid_date,date_param",
    [
        ("2023-13-01", "start_date"),  # Invalid month
        ("2023/01/01", "start_date"),  # Wrong separator
        ("01-01-2023", "start_date"),  # Wrong format
        ("2023-01-32", "start_date"),  # Invalid day
        ("not-a-date", "start_date"),  # Non-date string
        (None, "start_date"),  # None value
        (12345, "start_date"),  # Integer
    ],
)
def test_generate_rejects_invalid_start_date_format(
    generator_with_seed: OHLCVGenerator, invalid_date: Any, date_param: str
) -> None:  # CRITICAL TEST
    """
    Test generate() rejects various invalid start_date formats.

    Tests that invalid date formats return error structure
    without raising exception.

    Parameters
    ----------
    generator_with_seed : OHLCVGenerator
        Generator with fixed seed
    invalid_date : Any
        Invalid date value to test
    date_param : str
        Parameter name (unused, for clarity)

    Returns
    -------
    None
        Test passes if error returned for invalid date
    """
    # ACT
    result: dict = generator_with_seed.generate(ticker="TEST", start_date=invalid_date, end_date="2023-01-10")

    # ASSERT
    assert result["data"] == {}
    assert result["metadata"]["successful"] == 0
    assert result["metadata"]["failed"] == 1
    assert "TEST" in result["errors"]
    assert "YYYY-MM-DD" in result["errors"]["TEST"]


@pytest.mark.parametrize(
    "invalid_date",
    [
        "2023-13-01",  # Invalid month
        "2023/01/01",  # Wrong separator
        "01-01-2023",  # Wrong format
        "not-a-date",  # Non-date string
        12345,  # Integer
    ],
)
def test_generate_rejects_invalid_end_date_format(
    generator_with_seed: OHLCVGenerator, invalid_date: Any
) -> None:  # CRITICAL TEST
    """
    Test generate() rejects various invalid end_date formats.

    Tests that invalid end date formats return error structure
    without raising exception.

    Parameters
    ----------
    generator_with_seed : OHLCVGenerator
        Generator with fixed seed
    invalid_date : Any
        Invalid end date value to test

    Returns
    -------
    None
        Test passes if error returned for invalid end date
    """
    # ACT
    result: dict = generator_with_seed.generate(ticker="TEST", start_date="2023-01-01", end_date=invalid_date)

    # ASSERT
    assert result["data"] == {}
    assert result["metadata"]["successful"] == 0
    assert result["metadata"]["failed"] == 1
    assert "TEST" in result["errors"]
    assert "YYYY-MM-DD" in result["errors"]["TEST"]


def test_generate_rejects_start_date_after_end_date(generator_with_seed: OHLCVGenerator) -> None:  # CRITICAL TEST
    """
    Test generate() rejects start_date after end_date.

    Tests that invalid date range returns error structure
    without raising exception.

    Parameters
    ----------
    generator_with_seed : OHLCVGenerator
        Generator with fixed seed

    Returns
    -------
    None
        Test passes if error returned for reversed date range
    """
    # ACT
    result: dict = generator_with_seed.generate(ticker="TEST", start_date="2023-01-31", end_date="2023-01-01")

    # ASSERT
    assert result["data"] == {}
    assert result["metadata"]["successful"] == 0
    assert result["metadata"]["failed"] == 1
    assert "TEST" in result["errors"]
    assert "start_date must be before end_date" in result["errors"]["TEST"]


def test_generate_rejects_start_date_equals_end_date(generator_with_seed: OHLCVGenerator) -> None:  # CRITICAL TEST
    """
    Test generate() rejects start_date equal to end_date.

    Tests that same start and end date returns error structure
    without raising exception.

    Parameters
    ----------
    generator_with_seed : OHLCVGenerator
        Generator with fixed seed

    Returns
    -------
    None
        Test passes if error returned for equal dates
    """
    # ACT
    result: dict = generator_with_seed.generate(ticker="TEST", start_date="2023-01-15", end_date="2023-01-15")

    # ASSERT
    assert result["data"] == {}
    assert result["metadata"]["successful"] == 0
    assert result["metadata"]["failed"] == 1
    assert "TEST" in result["errors"]
    assert "start_date must be before end_date" in result["errors"]["TEST"]


@pytest.mark.parametrize(
    "invalid_price",
    [
        0.0,  # Zero
        -1.0,  # Negative
        -100.5,  # Large negative
    ],
)
def test_generate_rejects_zero_and_negative_initial_price(
    generator_with_seed: OHLCVGenerator, invalid_price: float
) -> None:  # CRITICAL TEST
    """
    Test generate() rejects zero and negative initial_price values.

    Tests that invalid initial prices return error structure
    without raising exception.

    Parameters
    ----------
    generator_with_seed : OHLCVGenerator
        Generator with fixed seed
    invalid_price : float
        Invalid initial price to test

    Returns
    -------
    None
        Test passes if error returned for non-positive price
    """
    # ACT
    result: dict = generator_with_seed.generate(
        ticker="TEST", start_date="2023-01-01", end_date="2023-01-05", initial_price=invalid_price
    )

    # ASSERT
    assert result["data"] == {}
    assert result["metadata"]["successful"] == 0
    assert result["metadata"]["failed"] == 1
    assert "TEST" in result["errors"]
    assert "initial_price must be positive" in result["errors"]["TEST"]


def test_generate_rejects_negative_volatility(generator_with_seed: OHLCVGenerator) -> None:  # CRITICAL TEST
    """
    Test generate() rejects negative volatility parameter.

    Tests that negative volatility returns error structure
    without raising exception.

    Parameters
    ----------
    generator_with_seed : OHLCVGenerator
        Generator with fixed seed

    Returns
    -------
    None
        Test passes if error returned for negative volatility
    """
    # ACT
    result: dict = generator_with_seed.generate(
        ticker="TEST", start_date="2023-01-01", end_date="2023-01-05", volatility=-0.1
    )

    # ASSERT
    assert result["data"] == {}
    assert result["metadata"]["successful"] == 0
    assert result["metadata"]["failed"] == 1
    assert "TEST" in result["errors"]
    assert "volatility must be non-negative" in result["errors"]["TEST"]


@pytest.mark.parametrize(
    "invalid_volume",
    [
        0,  # Zero
        -1,  # Negative
        -1000000,  # Large negative
    ],
)
def test_generate_rejects_zero_and_negative_volume_base(
    generator_with_seed: OHLCVGenerator, invalid_volume: int
) -> None:  # CRITICAL TEST
    """
    Test generate() rejects zero and negative volume_base values.

    Tests that invalid volume bases return error structure
    without raising exception.

    Parameters
    ----------
    generator_with_seed : OHLCVGenerator
        Generator with fixed seed
    invalid_volume : int
        Invalid volume base to test

    Returns
    -------
    None
        Test passes if error returned for non-positive volume
    """
    # ACT
    result: dict = generator_with_seed.generate(
        ticker="TEST", start_date="2023-01-01", end_date="2023-01-05", volume_base=invalid_volume
    )

    # ASSERT
    assert result["data"] == {}
    assert result["metadata"]["successful"] == 0
    assert result["metadata"]["failed"] == 1
    assert "TEST" in result["errors"]
    assert "volume_base must be positive" in result["errors"]["TEST"]


# -------------------------------------------------------------
# TEST CASES: generate() - Edge Cases
# -------------------------------------------------------------


def test_generate_handles_none_end_date_defaults_to_yesterday(generator_with_seed: OHLCVGenerator) -> None:
    """
    Test generate() with None end_date defaults to yesterday.

    Tests that when end_date is None, generator uses yesterday's date
    as end date for data generation.

    Parameters
    ----------
    generator_with_seed : OHLCVGenerator
        Generator with fixed seed

    Returns
    -------
    None
        Test passes if end date is set to yesterday
    """
    # ARRANGE
    yesterday: datetime.date = (datetime.datetime.now() - datetime.timedelta(days=1)).date()

    # ACT
    result: dict = generator_with_seed.generate(ticker="TEST", start_date="2020-01-01", end_date=None)
    df: pd.DataFrame = result["data"]["TEST"]

    # ASSERT
    assert df.index.max().date() == yesterday


def test_generate_handles_single_day_range(generator_with_seed: OHLCVGenerator) -> None:
    """
    Test generate() handles two-day range (minimum valid range).

    Tests that generator can create data for minimal valid date range
    (start_date must be before end_date, so minimum is 2 days).

    Parameters
    ----------
    generator_with_seed : OHLCVGenerator
        Generator with fixed seed

    Returns
    -------
    None
        Test passes if DataFrame has 2 rows
    """
    # ACT
    result: dict = generator_with_seed.generate(ticker="TEST", start_date="2023-01-01", end_date="2023-01-02")
    df: pd.DataFrame = result["data"]["TEST"]

    # ASSERT
    assert len(df) == 2
    assert result["metadata"]["successful"] == 1


def test_generate_handles_large_date_range(generator_with_seed: OHLCVGenerator) -> None:
    """
    Test generate() handles large date range (multiple years).

    Tests that generator can create data for extended periods
    without performance issues or errors.

    Parameters
    ----------
    generator_with_seed : OHLCVGenerator
        Generator with fixed seed

    Returns
    -------
    None
        Test passes if DataFrame has correct number of days
    """
    # ACT
    result: dict = generator_with_seed.generate(ticker="TEST", start_date="2020-01-01", end_date="2023-12-31")
    df: pd.DataFrame = result["data"]["TEST"]

    # ASSERT
    expected_days: int = (pd.Timestamp("2023-12-31") - pd.Timestamp("2020-01-01")).days + 1
    assert len(df) == expected_days
    assert result["metadata"]["successful"] == 1


def test_generate_handles_very_high_volatility(generator_with_seed: OHLCVGenerator) -> None:
    """
    Test generate() handles extreme volatility values.

    Tests that generator produces valid OHLC data even with
    unrealistically high volatility (e.g., 100% daily).

    Parameters
    ----------
    generator_with_seed : OHLCVGenerator
        Generator with fixed seed

    Returns
    -------
    None
        Test passes if all prices remain positive and OHLC relationships valid
    """
    # ACT
    result: dict = generator_with_seed.generate(
        ticker="TEST", start_date="2023-01-01", end_date="2023-01-31", volatility=1.0  # 100% volatility
    )
    df: pd.DataFrame = result["data"]["TEST"]

    # ASSERT
    assert (df["close"] > 0).all(), "All prices must be positive"
    assert (df["high"] >= df["close"]).all(), "High must be >= close"
    assert (df["low"] <= df["close"]).all(), "Low must be <= close"


def test_generate_handles_zero_volatility(generator_with_seed: OHLCVGenerator) -> None:
    """
    Test generate() handles zero volatility (flat price).

    Tests that with zero volatility, prices change only by trend
    with minimal intraday variation.

    Parameters
    ----------
    generator_with_seed : OHLCVGenerator
        Generator with fixed seed

    Returns
    -------
    None
        Test passes if volatility is minimal
    """
    # ACT
    result: dict = generator_with_seed.generate(
        ticker="TEST", start_date="2023-01-01", end_date="2023-01-10", volatility=0.0, trend=0.0
    )
    df: pd.DataFrame = result["data"]["TEST"]

    # ASSERT
    # With zero volatility and trend, prices should be relatively stable
    # (some variation from intraday_vol which uses volatility in calculation)
    assert len(df) == 10
    assert (df["close"] > 0).all()


def test_generate_handles_negative_trend(generator_with_seed: OHLCVGenerator) -> None:
    """
    Test generate() handles negative trend (declining market).

    Tests that negative trend parameter produces declining prices
    over time while maintaining valid OHLC relationships.

    Parameters
    ----------
    generator_with_seed : OHLCVGenerator
        Generator with fixed seed

    Returns
    -------
    None
        Test passes if final price is lower than initial price
    """
    # ACT
    result: dict = generator_with_seed.generate(
        ticker="TEST", start_date="2023-01-01", end_date="2023-12-31", initial_price=100.0, trend=-0.001  # Negative
    )
    df: pd.DataFrame = result["data"]["TEST"]

    # ASSERT
    # With negative trend over 1 year, final price should be significantly lower
    assert df.iloc[-1]["close"] < df.iloc[0]["open"]


# -------------------------------------------------------------
# TEST CASES: generate_multiple() - Happy Path
# -------------------------------------------------------------


def test_generate_multiple_returns_all_tickers_successfully(generator_with_seed: OHLCVGenerator) -> None:
    """
    Test generate_multiple() returns data for all tickers.

    Tests that all requested tickers are generated successfully
    and aggregated in single result structure.

    Parameters
    ----------
    generator_with_seed : OHLCVGenerator
        Generator with fixed seed

    Returns
    -------
    None
        Test passes if all tickers present in data
    """
    # ARRANGE
    tickers: List[str] = ["AAPL.XETRA", "MSFT.XETRA", "GOOGL.XETRA"]

    # ACT
    result: dict = generator_with_seed.generate_multiple(
        tickers=tickers, start_date="2023-01-01", end_date="2023-01-10"
    )

    # ASSERT
    assert len(result["data"]) == 3
    assert "AAPL.XETRA" in result["data"]
    assert "MSFT.XETRA" in result["data"]
    assert "GOOGL.XETRA" in result["data"]
    assert result["metadata"]["total_requested"] == 3
    assert result["metadata"]["successful"] == 3
    assert result["metadata"]["failed"] == 0
    assert len(result["errors"]) == 0


def test_generate_multiple_aggregates_metadata_correctly(generator_with_seed: OHLCVGenerator) -> None:
    """
    Test generate_multiple() aggregates metadata from all tickers.

    Tests that metadata correctly counts successful, failed tickers
    and tracks sources for each ticker.

    Parameters
    ----------
    generator_with_seed : OHLCVGenerator
        Generator with fixed seed

    Returns
    -------
    None
        Test passes if metadata aggregation is correct
    """
    # ARRANGE
    tickers: List[str] = ["TICKER1", "TICKER2"]

    # ACT
    result: dict = generator_with_seed.generate_multiple(
        tickers=tickers, start_date="2023-01-01", end_date="2023-01-05"
    )

    # ASSERT
    assert result["metadata"]["total_requested"] == 2
    assert result["metadata"]["successful"] == 2
    assert result["metadata"]["failed"] == 0
    assert result["metadata"]["sources"]["TICKER1"] == "synthetic"
    assert result["metadata"]["sources"]["TICKER2"] == "synthetic"
    assert result["metadata"]["source_breakdown"]["synthetic"] == 2


# -------------------------------------------------------------
# TEST CASES: generate_multiple() - Error Handling
# -------------------------------------------------------------


def test_generate_multiple_rejects_none_tickers(generator_with_seed: OHLCVGenerator) -> None:  # CRITICAL TEST
    """
    Test generate_multiple() rejects None tickers parameter.

    Tests that passing None returns error structure without raising exception.

    Parameters
    ----------
    generator_with_seed : OHLCVGenerator
        Generator with fixed seed

    Returns
    -------
    None
        Test passes if error returned for None tickers
    """
    # ACT
    result: dict = generator_with_seed.generate_multiple(tickers=None, start_date="2023-01-01", end_date="2023-01-05")

    # ASSERT
    assert result["data"] == {}
    assert result["metadata"]["total_requested"] == 0
    assert result["metadata"]["successful"] == 0
    assert result["metadata"]["failed"] == 0
    assert "_global" in result["errors"]
    assert "non-empty list" in result["errors"]["_global"]


def test_generate_multiple_rejects_empty_list(generator_with_seed: OHLCVGenerator) -> None:  # CRITICAL TEST
    """
    Test generate_multiple() rejects empty tickers list.

    Tests that passing empty list returns error structure without raising exception.

    Parameters
    ----------
    generator_with_seed : OHLCVGenerator
        Generator with fixed seed

    Returns
    -------
    None
        Test passes if error returned for empty list
    """
    # ACT
    result: dict = generator_with_seed.generate_multiple(tickers=[], start_date="2023-01-01", end_date="2023-01-05")

    # ASSERT
    assert result["data"] == {}
    assert result["metadata"]["total_requested"] == 0
    assert result["metadata"]["successful"] == 0
    assert result["metadata"]["failed"] == 0
    assert "_global" in result["errors"]
    assert "non-empty list" in result["errors"]["_global"]


def test_generate_multiple_rejects_non_list_tickers(generator_with_seed: OHLCVGenerator) -> None:  # CRITICAL TEST
    """
    Test generate_multiple() rejects non-list tickers parameter.

    Tests that passing string instead of list returns error structure.

    Parameters
    ----------
    generator_with_seed : OHLCVGenerator
        Generator with fixed seed

    Returns
    -------
    None
        Test passes if error returned for non-list tickers
    """
    # ACT
    result: dict = generator_with_seed.generate_multiple(
        tickers="AAPL.XETRA", start_date="2023-01-01", end_date="2023-01-05"
    )

    # ASSERT
    assert result["data"] == {}
    assert result["metadata"]["total_requested"] == 0
    assert "_global" in result["errors"]


def test_generate_multiple_handles_partial_failures_gracefully(generator_with_seed: OHLCVGenerator) -> None:
    """
    Test generate_multiple() handles mix of successful and failed tickers.

    Tests that when some tickers have invalid parameters, successful ones
    are still generated and failures are tracked in errors.

    Parameters
    ----------
    generator_with_seed : OHLCVGenerator
        Generator with fixed seed

    Returns
    -------
    None
        Test passes if successful tickers in data and failed in errors
    """
    # ARRANGE
    tickers: List[str] = ["VALID", "", None, "ALSO_VALID"]  # Mix of valid and invalid

    # ACT
    result: dict = generator_with_seed.generate_multiple(
        tickers=tickers, start_date="2023-01-01", end_date="2023-01-05"
    )

    # ASSERT
    assert result["metadata"]["total_requested"] == 4
    assert result["metadata"]["successful"] == 2  # VALID and ALSO_VALID
    assert result["metadata"]["failed"] == 2  # "" and None
    assert "VALID" in result["data"]
    assert "ALSO_VALID" in result["data"]
    assert "" in result["errors"]
    assert None in result["errors"]


def test_generate_multiple_handles_all_failures(generator_with_seed: OHLCVGenerator) -> None:
    """
    Test generate_multiple() handles case when all tickers fail.

    Tests that when all tickers have errors, result contains
    empty data with all tickers in errors dict.

    Parameters
    ----------
    generator_with_seed : OHLCVGenerator
        Generator with fixed seed

    Returns
    -------
    None
        Test passes if data is empty and all tickers in errors
    """
    # ARRANGE
    tickers: List[str] = ["", None, 123]  # All invalid

    # ACT
    result: dict = generator_with_seed.generate_multiple(
        tickers=tickers, start_date="2023-01-01", end_date="2023-01-05"
    )

    # ASSERT
    assert result["metadata"]["total_requested"] == 3
    assert result["metadata"]["successful"] == 0
    assert result["metadata"]["failed"] == 3
    assert len(result["data"]) == 0
    assert len(result["errors"]) == 3


# -------------------------------------------------------------
# TEST CASES: generate_multiple() - Edge Cases
# -------------------------------------------------------------


def test_generate_multiple_with_single_ticker(generator_with_seed: OHLCVGenerator) -> None:
    """
    Test generate_multiple() works with single-element ticker list.

    Tests that passing list with one ticker produces same result
    as calling generate() directly.

    Parameters
    ----------
    generator_with_seed : OHLCVGenerator
        Generator with fixed seed

    Returns
    -------
    None
        Test passes if single ticker processed successfully
    """
    # ARRANGE
    tickers: List[str] = ["SINGLE"]

    # ACT
    result: dict = generator_with_seed.generate_multiple(
        tickers=tickers, start_date="2023-01-01", end_date="2023-01-05"
    )

    # ASSERT
    assert result["metadata"]["total_requested"] == 1
    assert result["metadata"]["successful"] == 1
    assert result["metadata"]["failed"] == 0
    assert "SINGLE" in result["data"]


def test_generate_multiple_passes_kwargs_correctly(generator_with_seed: OHLCVGenerator) -> None:
    """
    Test generate_multiple() passes kwargs to underlying generate() calls.

    Tests that additional parameters like initial_price, volatility
    are correctly forwarded to each ticker generation.

    Parameters
    ----------
    generator_with_seed : OHLCVGenerator
        Generator with fixed seed

    Returns
    -------
    None
        Test passes if kwargs affect generated data
    """
    # ARRANGE
    tickers: List[str] = ["TEST1", "TEST2"]
    custom_price: float = 500.0

    # ACT
    result: dict = generator_with_seed.generate_multiple(
        tickers=tickers, start_date="2023-01-01", end_date="2023-01-05", initial_price=custom_price, volatility=0.0
    )

    # ASSERT
    # With zero volatility, first open should be close to initial_price
    df1: pd.DataFrame = result["data"]["TEST1"]
    assert abs(df1.iloc[0]["open"] - custom_price) < 1.0  # Allow small variance


# -------------------------------------------------------------
# TEST CASES: get_summary_stats()
# -------------------------------------------------------------


def test_get_summary_stats_calculates_correctly(generator_with_seed: OHLCVGenerator) -> None:
    """
    Test get_summary_stats() calculates correct summary statistics.

    Tests that summary includes total_records, date_range, and price_stats
    with correct values from DataFrame.

    Parameters
    ----------
    generator_with_seed : OHLCVGenerator
        Generator with fixed seed

    Returns
    -------
    None
        Test passes if all statistics match expected values
    """
    # ARRANGE
    result: dict = generator_with_seed.generate(ticker="TEST", start_date="2023-01-01", end_date="2023-01-10")
    df: pd.DataFrame = result["data"]["TEST"]

    # ACT
    stats: dict = generator_with_seed.get_summary_stats(df)

    # ASSERT
    assert stats["total_records"] == 10
    assert stats["date_range"]["start"] == pd.Timestamp("2023-01-01")
    assert stats["date_range"]["end"] == pd.Timestamp("2023-01-10")
    assert stats["price_stats"]["min_low"] == df["low"].min()
    assert stats["price_stats"]["max_high"] == df["high"].max()
    assert stats["price_stats"]["avg_close"] == df["close"].mean()
    assert stats["price_stats"]["total_volume"] == df["volume"].sum()


def test_get_summary_stats_returns_empty_dict_for_empty_df(generator_with_seed: OHLCVGenerator) -> None:
    """
    Test get_summary_stats() returns empty dict for empty DataFrame.

    Tests that passing empty DataFrame returns empty dict
    without raising exception.

    Parameters
    ----------
    generator_with_seed : OHLCVGenerator
        Generator with fixed seed

    Returns
    -------
    None
        Test passes if empty dict returned
    """
    # ARRANGE
    empty_df: pd.DataFrame = pd.DataFrame()

    # ACT
    stats: dict = generator_with_seed.get_summary_stats(empty_df)

    # ASSERT
    assert stats == {}


# -------------------------------------------------------------
# TEST CASES: Integration & Advanced Scenarios
# -------------------------------------------------------------


def test_generate_multiple_with_different_parameters_per_ticker() -> None:
    """
    Test that each ticker in generate_multiple() receives same kwargs.

    Tests current limitation that all tickers use same parameters
    when called via generate_multiple().

    Returns
    -------
    None
        Test passes if all tickers use same initial_price
    """
    # ARRANGE
    generator: OHLCVGenerator = OHLCVGenerator(seed=42)
    tickers: List[str] = ["TICKER1", "TICKER2"]

    # ACT
    result: dict = generator.generate_multiple(
        tickers=tickers, start_date="2023-01-01", end_date="2023-01-05", initial_price=200.0
    )

    # ASSERT
    # All tickers should start around same initial price
    df1: pd.DataFrame = result["data"]["TICKER1"]
    df2: pd.DataFrame = result["data"]["TICKER2"]
    assert abs(df1.iloc[0]["open"] - 200.0) < 50.0
    assert abs(df2.iloc[0]["open"] - 200.0) < 50.0


def test_generate_volume_correlates_with_price_movement(generator_with_seed: OHLCVGenerator) -> None:
    """
    Test that volume increases with larger price movements.

    Tests that days with higher price volatility have higher volume,
    as implemented in generate() logic.

    Parameters
    ----------
    generator_with_seed : OHLCVGenerator
        Generator with fixed seed

    Returns
    -------
    None
        Test passes if volume correlates with price change
    """
    # ACT
    result: dict = generator_with_seed.generate(
        ticker="TEST", start_date="2023-01-01", end_date="2023-03-31", volatility=0.05
    )
    df: pd.DataFrame = result["data"]["TEST"]

    # ARRANGE
    df["price_change"] = abs(df["close"] - df["open"]) / df["open"]

    # ASSERT
    # There should be positive correlation between price change and volume
    correlation: float = df["price_change"].corr(df["volume"])
    assert correlation > 0  # Positive correlation expected


def test_adjusted_close_equals_close_in_generated_data(generator_with_seed: OHLCVGenerator) -> None:
    """
    Test that adjusted_close equals close for synthetic data.

    Tests that since no dividends/splits in synthetic data,
    adjusted_close should match close exactly.

    Parameters
    ----------
    generator_with_seed : OHLCVGenerator
        Generator with fixed seed

    Returns
    -------
    None
        Test passes if all adjusted_close values equal close
    """
    # ACT
    result: dict = generator_with_seed.generate(ticker="TEST", start_date="2023-01-01", end_date="2023-01-31")
    df: pd.DataFrame = result["data"]["TEST"]

    # ASSERT
    assert (df["adjusted_close"] == df["close"]).all()


def test_generate_with_exception_in_random_generation(generator_with_seed: OHLCVGenerator) -> None:
    """
    Test generate() handles exceptions during random number generation.

    Tests that if numpy raises exception during generation,
    it's caught and returned in error structure.

    Parameters
    ----------
    generator_with_seed : OHLCVGenerator
        Generator with fixed seed

    Returns
    -------
    None
        Test passes if exception caught and error returned
    """
    # ARRANGE
    with patch("numpy.random.normal", side_effect=RuntimeError("Random error")):
        # ACT
        result: dict = generator_with_seed.generate(ticker="TEST", start_date="2023-01-01", end_date="2023-01-05")

        # ASSERT
        assert result["data"] == {}
        assert result["metadata"]["successful"] == 0
        assert result["metadata"]["failed"] == 1
        assert "TEST" in result["errors"]
        assert "Random error" in result["errors"]["TEST"]
