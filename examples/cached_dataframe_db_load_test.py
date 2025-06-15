"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich
  Project : basefunctions
  Copyright (c) by neuraldevelopment
  All rights reserved.
  Description:
  Demo for CachedDataFrameDb performance comparison with direct writes
 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import time
from typing import List
import pandas as pd
import basefunctions

# -------------------------------------------------------------
# DEFINITIONS REGISTRY
# -------------------------------------------------------------

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------
NUM_DATAFRAMES = 50
TEST_INSTANCE = "dev_test_postgres"
TEST_DATABASE = "dev_test_postgres"
TEST_TABLE = "stress_test"
SEED = 42

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


def generate_test_data() -> List[pd.DataFrame]:
    """
    Generate test OHLCV DataFrames.

    Returns
    -------
    List[pd.DataFrame]
        List of OHLCV DataFrames with different tickers
    """
    generator = basefunctions.OHLCVGenerator(seed=SEED)
    dataframes = []

    for i in range(NUM_DATAFRAMES):
        ticker = f"TICK{i:03d}.XETRA"
        df = generator.generate(
            ticker=ticker, start_date="2024-01-01", end_date="2024-01-31", initial_price=100.0 + i * 5, volatility=0.02
        )
        dataframes.append(df)

    return dataframes


def test_direct_writes(dataframes: List[pd.DataFrame]) -> float:
    """
    Test direct writes using DataFrameDb.

    Parameters
    ----------
    dataframes : List[pd.DataFrame]
        List of DataFrames to write

    Returns
    -------
    float
        Time taken in seconds
    """
    db = basefunctions.DataFrameDb(TEST_INSTANCE, TEST_DATABASE)

    start_time = time.perf_counter()

    for df in dataframes:
        db.write(df, TEST_TABLE, if_exists="append")

    end_time = time.perf_counter()

    return end_time - start_time


def test_cached_writes(dataframes: List[pd.DataFrame]) -> tuple:
    """
    Test cached writes using CachedDataFrameDb.

    Parameters
    ----------
    dataframes : List[pd.DataFrame]
        List of DataFrames to write

    Returns
    -------
    tuple
        (cache_time, flush_time) in seconds
    """
    cached_db = basefunctions.CachedDataFrameDb(TEST_INSTANCE, TEST_DATABASE)

    # Cache phase
    cache_start = time.perf_counter()

    for df in dataframes:
        cached_db.write(df, TEST_TABLE, if_exists="append")

    cache_end = time.perf_counter()

    # Flush phase
    flush_start = time.perf_counter()
    cached_db.flush(TEST_TABLE)
    flush_end = time.perf_counter()

    cache_time = cache_end - cache_start
    flush_time = flush_end - flush_start

    return cache_time, flush_time


def test_read_cache(cached_db: basefunctions.CachedDataFrameDb) -> tuple:
    """
    Test read cache performance.

    Parameters
    ----------
    cached_db : basefunctions.CachedDataFrameDb
        Cached database instance

    Returns
    -------
    tuple
        (first_read_time, second_read_time) in seconds
    """
    query = f"SELECT * FROM {TEST_TABLE} WHERE Ticker = 'TICK001.XETRA'"

    # First read (cache miss)
    start_time = time.perf_counter()
    df1 = cached_db.read(TEST_TABLE, query)
    first_read_time = time.perf_counter() - start_time

    # Second read (cache hit)
    start_time = time.perf_counter()
    df2 = cached_db.read(TEST_TABLE, query)
    second_read_time = time.perf_counter() - start_time

    # Verify data is identical
    assert df1.equals(df2), "Read cache returned different data"

    return first_read_time, second_read_time


def run_cached_dataframe_demo():
    """Run complete CachedDataFrameDb demo with performance comparison."""
    runner = basefunctions.DemoRunner()

    print("=== CachedDataFrameDb Performance Demo ===")
    print(f"Testing {NUM_DATAFRAMES} DataFrames performance comparison")

    # Test data generation
    def generate_data():
        return generate_test_data()

    runner.run_test("Generating test data", generate_data)
    dataframes = runner.get_last_result()

    print(f"Generated {len(dataframes)} OHLCV DataFrames")
    print(f"Each DataFrame contains {len(dataframes[0])} rows")

    # Clear table before tests
    def clear_table():
        try:
            db = basefunctions.DataFrameDb(TEST_INSTANCE, TEST_DATABASE)
            db.delete(TEST_TABLE)
            return True
        except:
            return True  # Table might not exist

    runner.run_test("Clearing test table", clear_table)

    # Direct writes test
    def direct_write_test():
        return test_direct_writes(dataframes)

    runner.run_test("Direct writes (DataFrameDb)", direct_write_test)
    direct_time = runner.get_last_result()

    # Clear table again
    runner.run_test("Clearing test table", clear_table)

    # Cached writes test
    def cached_write_test():
        return test_cached_writes(dataframes)

    runner.run_test("Cached writes (CachedDataFrameDb)", cached_write_test)
    cache_time, flush_time = runner.get_last_result()
    total_cached_time = cache_time + flush_time

    # Read cache test
    def read_cache_test():
        cached_db = basefunctions.CachedDataFrameDb(TEST_INSTANCE, TEST_DATABASE)
        return test_read_cache(cached_db)

    runner.run_test("Read cache performance", read_cache_test)
    first_read_time, second_read_time = runner.get_last_result()

    # Calculate performance metrics
    speedup_factor = direct_time / total_cached_time if total_cached_time > 0 else 0
    cache_speedup = first_read_time / second_read_time if second_read_time > 0 else 0

    # Performance results
    performance_data = [
        ("DataFrames processed", str(NUM_DATAFRAMES)),
        ("Direct write time", f"{direct_time:.4f}s"),
        ("Cache write time", f"{cache_time:.4f}s"),
        ("Flush time", f"{flush_time:.4f}s"),
        ("Total cached time", f"{total_cached_time:.4f}s"),
        ("Write speedup factor", f"{speedup_factor:.2f}x"),
        ("First read time", f"{first_read_time:.4f}s"),
        ("Second read time", f"{second_read_time:.6f}s"),
        ("Read cache speedup", f"{cache_speedup:.0f}x"),
    ]

    runner.print_performance_table(performance_data, "Performance Comparison Results")

    # Summary
    if speedup_factor > 1:
        print(f"SUCCESS: Cached writes are {speedup_factor:.2f}x faster than direct writes!")
    else:
        print("WARNING: Cached writes did not show expected performance improvement")

    if cache_speedup > 10:
        print(f"SUCCESS: Read cache provides {cache_speedup:.0f}x speedup!")
    else:
        print("WARNING: Read cache speedup lower than expected")

    # Print final results
    runner.print_results()


if __name__ == "__main__":
    run_cached_dataframe_demo()
