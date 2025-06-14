"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich
  Project : basefunctions
  Copyright (c) by neuraldevelopment
  All rights reserved.
  Description:
  Performance comparison demo for DataFrameDb vs CachedDataFrameDb
 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import pandas as pd
import numpy as np
import datetime
import time
import basefunctions

# -------------------------------------------------------------
# DEFINITIONS REGISTRY
# -------------------------------------------------------------

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------
INSTANCE_NAME = "dev_test_db_postgres"
DATABASE_NAME = "test"

# Performance test configuration
PERFORMANCE_CONFIG = {
    "small": {"assets": 5, "days_per_asset": 100, "symbols": ["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA"]},
    "medium": {
        "assets": 20,
        "days_per_asset": 250,
        "symbols": ["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA", "META", "AMZN", "BRK", "JNJ", "V"],
    },
    "large": {
        "assets": 70,
        "days_per_asset": 9000,
        "symbols": [
            "AAPL",
            "GOOGL",
            "MSFT",
            "TSLA",
            "NVDA",
            "META",
            "AMZN",
            "BRK",
            "JNJ",
            "V",
            "UNH",
            "PG",
            "NFLX",
            "DIS",
            "HD",
            "BAC",
            "CRM",
            "XOM",
            "CVX",
            "PFE",
            "ABBV",
            "KO",
            "AVGO",
            "PEP",
            "TMO",
            "COST",
            "ADBE",
            "ACN",
            "NKE",
            "MRK",
            "WMT",
            "JPM",
            "MA",
            "INTC",
            "VZ",
            "T",
            "CSCO",
            "IBM",
            "ORCL",
            "PYPL",
            "QCOM",
            "AMD",
            "TXN",
            "HON",
            "UPS",
            "MDT",
            "LLY",
            "NEE",
            "DHR",
            "BMY",
            "AMGN",
            "PM",
            "RTX",
            "LOW",
            "SPGI",
            "GS",
            "CAT",
            "DE",
            "MMM",
            "AXP",
            "BLK",
            "ISRG",
            "TJX",
            "SYK",
            "ZTS",
            "BKNG",
            "GILD",
            "CI",
            "MU",
            "NOW",
        ],
    },
}

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


class PerformanceTimer:
    """Simple context manager for timing operations."""

    def __init__(self, name: str):
        self.name = name
        self.start_time = None
        self.end_time = None

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.perf_counter()

    @property
    def elapsed(self) -> float:
        """Get elapsed time in seconds."""
        if self.end_time and self.start_time:
            return self.end_time - self.start_time
        return 0.0

    @property
    def elapsed_ms(self) -> float:
        """Get elapsed time in milliseconds."""
        return self.elapsed * 1000


def generate_time_series_data(
    symbol: str, start_date: datetime.date, end_date: datetime.date, freq: str = "1D"
) -> pd.DataFrame:
    """
    Generate time series OHLCV data for performance testing.

    Parameters
    ----------
    symbol : str
        Stock symbol
    start_date : datetime.date
        Start date for data generation
    end_date : datetime.date
        End date for data generation
    freq : str, optional
        Frequency for data generation, by default "1D"

    Returns
    -------
    pd.DataFrame
        DataFrame with OHLCV data
    """
    # Generate date range
    date_range = pd.date_range(start=start_date, end=end_date, freq=freq)
    num_days = len(date_range)

    if num_days == 0:
        return pd.DataFrame()

    # Use symbol hash for reproducible but different data per symbol
    seed = hash(symbol) % 1000000
    np.random.seed(seed)

    # Starting price based on symbol
    base_prices = {
        "AAPL": 150,
        "GOOGL": 2500,
        "MSFT": 300,
        "TSLA": 800,
        "NVDA": 400,
        "META": 300,
        "AMZN": 3000,
        "BRK": 400000,
        "JNJ": 160,
        "V": 220,
    }
    base_price = base_prices.get(symbol, 100)

    # Generate price movements
    returns = np.random.normal(0.0005, 0.02, num_days)  # 0.05% daily return, 2% volatility
    price_multipliers = np.cumprod(1 + returns)
    close_prices = base_price * price_multipliers

    # Generate OHLCV data
    data = []
    for i, (date, close) in enumerate(zip(date_range, close_prices)):
        # Intraday volatility
        daily_vol = np.random.uniform(0.005, 0.025)

        # Generate OHLC
        if i == 0:
            open_price = close * np.random.uniform(0.995, 1.005)
        else:
            open_price = close_prices[i - 1] * np.random.uniform(0.995, 1.005)

        high = max(open_price, close) * (1 + daily_vol)
        low = min(open_price, close) * (1 - daily_vol)
        volume = int(np.random.uniform(500_000, 5_000_000))

        data.append(
            {
                "timestamp": date,
                "symbol": symbol,
                "open": round(open_price, 2),
                "high": round(high, 2),
                "low": round(low, 2),
                "close": round(close, 2),
                "volume": volume,
                "date_str": date.strftime("%Y-%m-%d"),
            }
        )

    return pd.DataFrame(data)


def generate_market_data(config: dict) -> pd.DataFrame:
    """
    Generate comprehensive market data for multiple assets in a single DataFrame.

    Parameters
    ----------
    config : dict
        Configuration with 'assets', 'days_per_asset', 'symbols'

    Returns
    -------
    pd.DataFrame
        Combined DataFrame with all market data
    """
    all_data = []
    symbols = config["symbols"]
    num_assets = config["assets"]
    days_per_asset = config["days_per_asset"]

    # Use full historical date range from 1990 to 2025 (35 years)
    start_date = datetime.date(1990, 1, 1)
    end_date = datetime.date(2025, 12, 31)

    print(f"  Generating data for {num_assets} assets with {days_per_asset} days each...")

    for i in range(num_assets):
        symbol = symbols[i % len(symbols)]

        # Each asset gets full historical data
        asset_start = start_date
        asset_end = min(start_date + datetime.timedelta(days=days_per_asset), end_date)

        asset_data = generate_time_series_data(symbol, asset_start, asset_end)

        # Add asset identifier to distinguish multiple instances of same symbol
        asset_data["asset_id"] = f"{symbol}_{i:03d}"
        asset_data["asset_group"] = i // 10  # Group assets for queries

        all_data.append(asset_data)

        if (i + 1) % 10 == 0:
            print(f"    Generated {i + 1}/{num_assets} assets...")

    # Combine all asset data into single DataFrame
    combined_df = pd.concat(all_data, ignore_index=True)

    # Add additional columns for realistic financial data
    combined_df["sector"] = combined_df["asset_id"].apply(lambda x: f"sector_{hash(x) % 10}")
    combined_df["market_cap"] = (
        combined_df["close"] * combined_df["volume"] * np.random.uniform(0.1, 10.0, len(combined_df))
    )

    # Sort by date for realistic time series structure
    combined_df = combined_df.sort_values(["asset_id", "timestamp"]).reset_index(drop=True)

    print(f"  Generated combined dataset: {len(combined_df):,} rows across {num_assets} assets")
    return combined_df


def cleanup_test_tables(instance_name: str, database_name: str, table_prefix: str = "market_data") -> None:
    """
    Clean up test tables after performance testing.

    Parameters
    ----------
    instance_name : str
        Database instance name
    database_name : str
        Database name
    table_prefix : str, optional
        Prefix for test tables, by default "market_data"
    """
    try:
        db = basefunctions.Db(instance_name, database_name)

        # Get all tables and drop those starting with prefix
        tables = db.list_tables()
        test_tables = [table for table in tables if table.startswith(table_prefix)]

        for table in test_tables:
            try:
                db.execute(f"DROP TABLE IF EXISTS {table}")
                print(f"  Cleaned up table: {table}")
            except Exception as e:
                print(f"  Warning: Could not drop table {table}: {str(e)}")

        if test_tables:
            print(f"✓ Cleaned up {len(test_tables)} test tables")
        else:
            print("✓ No test tables to clean up")

    except Exception as e:
        print(f"✗ Cleanup failed: {str(e)}")


def run_performance_tests():
    """
    Run comprehensive performance tests using DemoRunner.
    """
    # Initialize logging with higher level to reduce noise
    basefunctions.DemoRunner.init_logging("WARNING")
    runner = basefunctions.DemoRunner(log_level="WARNING")

    # Performance results storage
    performance_results = []
    test_config = PERFORMANCE_CONFIG["large"]  # Use large config for meaningful results
    market_data = None

    @runner.test("Test Data Generation")
    def test_data_generation():
        nonlocal market_data
        market_data = generate_market_data(test_config)
        assert len(market_data) > 0
        assert len(market_data["asset_id"].unique()) == test_config["assets"]
        print(f"  Generated market data: {len(market_data):,} rows for {test_config['assets']} assets")
        print(f"  Date range: {market_data['timestamp'].min()} to {market_data['timestamp'].max()}")
        print(f"  Unique assets: {len(market_data['asset_id'].unique())}")
        print(f"  Memory usage: ~{market_data.memory_usage(deep=True).sum() / 1024 / 1024:.1f} MB")

    @runner.test("Database Setup")
    def test_database_setup():
        # Ensure database exists
        manager = basefunctions.DbManager()
        instance = manager.get_instance(INSTANCE_NAME)
        databases = instance.list_databases()

        if DATABASE_NAME not in databases:
            instance.add_database(DATABASE_NAME)
            print(f"  Created database: {DATABASE_NAME}")
        else:
            print(f"  Database {DATABASE_NAME} already exists")

    @runner.test("Standard DataFrameDb Write Performance")
    def test_standard_write():
        df_db = basefunctions.DataFrameDb(INSTANCE_NAME, DATABASE_NAME)

        with PerformanceTimer("standard_write") as timer:
            df_db.write(market_data, "market_data_standard", if_exists="replace")

        total_rows = len(market_data)
        rows_per_sec = total_rows / timer.elapsed

        performance_results.append(("Standard Write Total Time", f"{timer.elapsed:.2f} seconds"))
        performance_results.append(("Standard Write Rows/Second", f"{rows_per_sec:.0f} rows/sec"))
        performance_results.append(("Standard Write Total Rows", f"{total_rows:,} rows"))

        print(f"  Wrote {total_rows:,} rows in {timer.elapsed:.2f}s ({rows_per_sec:.0f} rows/sec)")

    @runner.test("Standard DataFrameDb Read Performance")
    def test_standard_read():
        df_db = basefunctions.DataFrameDb(INSTANCE_NAME, DATABASE_NAME)

        with PerformanceTimer("standard_read") as timer:
            df_read = df_db.read("market_data_standard")
            assert len(df_read) > 0

        rows_per_sec = len(df_read) / timer.elapsed

        performance_results.append(("Standard Read Total Time", f"{timer.elapsed:.2f} seconds"))
        performance_results.append(("Standard Read Rows/Second", f"{rows_per_sec:.0f} rows/sec"))
        performance_results.append(("Standard Read Total Rows", f"{len(df_read):,} rows"))

        print(f"  Read {len(df_read):,} rows in {timer.elapsed:.2f}s ({rows_per_sec:.0f} rows/sec)")

    @runner.test("Cached DataFrameDb Write Performance")
    def test_cached_write():
        cached_db = basefunctions.CachedDataFrameDb(INSTANCE_NAME, DATABASE_NAME, cache_ttl=3600)

        with PerformanceTimer("cached_write_buffer") as timer:
            # Write to buffer (should be fast)
            cached_db.write(market_data, "market_data_cached", if_exists="replace", immediate=False)

        buffer_time = timer.elapsed

        with PerformanceTimer("cached_write_flush") as timer:
            # Flush all buffers (actual DB write)
            flushed_tables = cached_db.flush(force=True)

        flush_time = timer.elapsed
        total_time = buffer_time + flush_time
        total_rows = len(market_data)
        rows_per_sec = total_rows / total_time

        performance_results.append(("Cached Write Buffer Time", f"{buffer_time:.3f} seconds"))
        performance_results.append(("Cached Write Flush Time", f"{flush_time:.2f} seconds"))
        performance_results.append(("Cached Write Total Time", f"{total_time:.2f} seconds"))
        performance_results.append(("Cached Write Rows/Second", f"{rows_per_sec:.0f} rows/sec"))
        performance_results.append(("Cached Write Tables Flushed", f"{flushed_tables} tables"))

        print(f"  Buffered {total_rows:,} rows in {buffer_time:.3f}s")
        print(f"  Flushed {flushed_tables} tables in {flush_time:.2f}s")
        print(f"  Total: {total_time:.2f}s ({rows_per_sec:.0f} rows/sec)")

    @runner.test("Cached DataFrameDb Read Performance (Cold Cache)")
    def test_cached_read_cold():
        cached_db = basefunctions.CachedDataFrameDb(INSTANCE_NAME, DATABASE_NAME, cache_ttl=3600)

        # Clear cache first to ensure cold start
        cached_db.clear_cache()

        with PerformanceTimer("cached_read_cold") as timer:
            df_read = cached_db.read("market_data_cached")
            assert len(df_read) > 0

        rows_per_sec = len(df_read) / timer.elapsed
        cache_stats = cached_db.get_cache_stats()

        performance_results.append(("Cached Read Cold Total Time", f"{timer.elapsed:.2f} seconds"))
        performance_results.append(("Cached Read Cold Rows/Second", f"{rows_per_sec:.0f} rows/sec"))
        performance_results.append(("Cache Misses (Cold)", f"{cache_stats['cache']['misses']} misses"))

        print(f"  Cold read {len(df_read):,} rows in {timer.elapsed:.2f}s ({rows_per_sec:.0f} rows/sec)")
        print(f"  Cache stats: {cache_stats['cache']['misses']} misses, {cache_stats['cache']['hits']} hits")

        # Store cache_db instance for warm read test
        global cached_db_instance
        cached_db_instance = cached_db

    @runner.test("Cached DataFrameDb Read Performance (Warm Cache)")
    def test_cached_read_warm():
        # Reuse same cached_db instance from cold read test (cache should be populated)
        cached_db = cached_db_instance

        with PerformanceTimer("cached_read_warm") as timer:
            df_read = cached_db.read("market_data_cached")
            assert len(df_read) > 0

        rows_per_sec = len(df_read) / timer.elapsed
        cache_stats = cached_db.get_cache_stats()

        performance_results.append(("Cached Read Warm Total Time", f"{timer.elapsed:.2f} seconds"))
        performance_results.append(("Cached Read Warm Rows/Second", f"{rows_per_sec:.0f} rows/sec"))
        performance_results.append(("Cache Hits (Warm)", f"{cache_stats['cache']['hits']} hits"))
        performance_results.append(("Cache Hit Rate", f"{cache_stats['cache']['hit_rate_percent']:.1f}%"))

        print(f"  Warm read {len(df_read):,} rows in {timer.elapsed:.2f}s ({rows_per_sec:.0f} rows/sec)")
        print(f"  Cache stats: {cache_stats['cache']['hits']} hits, {cache_stats['cache']['misses']} misses")
        print(f"  Hit rate: {cache_stats['cache']['hit_rate_percent']:.1f}%")

    @runner.test("Cleanup Test Data")
    def test_cleanup():
        cleanup_test_tables(INSTANCE_NAME, DATABASE_NAME, "market_data")

    # Execute all tests
    print("=== DataFrame Performance Demo ===\n")
    print(f"Configuration: {test_config['assets']} assets × {test_config['days_per_asset']} days each")
    print(f"Total data volume: {test_config['assets'] * test_config['days_per_asset']:,} rows")
    print(f"Symbols: {', '.join(test_config['symbols'][:10])}{'...' if len(test_config['symbols']) > 10 else ''}")
    print(f"Target Database: {INSTANCE_NAME}.{DATABASE_NAME}")
    print(f"Date Range: 1990-2025 (35 years of historical data)")
    print(f"Test Approach: Single table with multi-asset data (realistic scenario)\n")

    runner.run_all_tests()
    runner.print_results("Performance Test Results")

    # Show performance comparison
    if performance_results:
        print()
        runner.print_performance_table(performance_results, "Performance Metrics")

        # Calculate and show speedup ratios
        print("\n=== Performance Analysis ===")
        try:
            standard_write_time = next(
                float(val.split()[0]) for key, val in performance_results if "Standard Write Total Time" in key
            )
            cached_write_time = next(
                float(val.split()[0]) for key, val in performance_results if "Cached Write Total Time" in key
            )

            standard_read_time = next(
                float(val.split()[0]) for key, val in performance_results if "Standard Read Total Time" in key
            )
            cached_read_cold_time = next(
                float(val.split()[0]) for key, val in performance_results if "Cached Read Cold Total Time" in key
            )
            cached_read_warm_time = next(
                float(val.split()[0]) for key, val in performance_results if "Cached Read Warm Total Time" in key
            )

            write_speedup = standard_write_time / cached_write_time
            read_cold_slowdown = cached_read_cold_time / standard_read_time
            read_warm_speedup = standard_read_time / cached_read_warm_time

            print(
                f"Write Performance: Cached is {write_speedup:.1f}x {'faster' if write_speedup > 1 else 'slower'} than standard"
            )
            print(f"Read Performance (Cold): Cached is {read_cold_slowdown:.1f}x slower than standard (expected)")
            print(f"Read Performance (Warm): Cached is {read_warm_speedup:.1f}x faster than standard")

        except Exception as e:
            print(f"Could not calculate speedup ratios: {str(e)}")

    return runner.get_summary()


if __name__ == "__main__":
    try:
        passed, total = run_performance_tests()
        print(f"\n=== Final Results ===")
        print(f"Tests passed: {passed}/{total}")

        if passed == total:
            print("🎉 All performance tests completed successfully!")
        else:
            print(f"⚠️  {total - passed} tests failed")

    except Exception as e:
        print(f"💥 Performance demo failed: {str(e)}")
