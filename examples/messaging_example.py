"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Performance comparison between sync, thread, corelet modes and brute force
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import time
import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

import basefunctions
from ohlcv_all import OHLCVDataEvent, OHLCVSyncHandler, OHLCVThreadHandler, OHLCVCoreletHandler

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


def generate_random_ohlcv_data(start_date, end_date, ticker_id):
    """Generate random OHLCV data for the given date range."""
    # Create date range
    dates = pd.date_range(start=start_date, end=end_date, freq="B")  # Business days

    # Initial price
    base_price = random.uniform(10, 1000)

    # Generate random prices
    n = len(dates)
    closes = [base_price]
    for i in range(1, n):
        # Random daily return between -2% and 2%
        daily_return = random.uniform(-0.02, 0.02)
        closes.append(closes[-1] * (1 + daily_return))

    # Generate OHLCV data
    data = []
    for i, date in enumerate(dates):
        close = closes[i]
        # Random values around close price
        high = close * random.uniform(1, 1.02)
        low = close * random.uniform(0.98, 1)
        open_price = close * random.uniform(0.99, 1.01)
        # Random volume
        volume = int(random.uniform(100000, 1000000))

        data.append([date, open_price, high, low, close, volume])

    # Create DataFrame
    df = pd.DataFrame(data, columns=["date", "open", "high", "low", "close", "volume"])
    df.set_index("date", inplace=True)
    df.name = f"df_{ticker_id}"

    return df


def method1_sync_messaging(dataframes, sample_dates):
    """Process OHLCV data using sync messaging framework."""
    print("METHOD 1: Using Sync Messaging Framework")

    # Setup messaging system
    event_bus = basefunctions.get_event_bus()
    handler = OHLCVSyncHandler()
    event_bus.register("ohlcv_data", handler)

    # Run the test
    start_time = time.time()
    event_count = 0

    for current_date in sample_dates:
        for ticker_id, df in dataframes.items():
            event = OHLCVDataEvent(dataframe=df, ticker_id=ticker_id, current_date=current_date)
            event_bus.publish(event)
            event_count += 1

    # Get results with new API
    success_results, error_results = event_bus.get_results()
    end_time = time.time()
    execution_time = end_time - start_time

    total_rows = sum(result for result in success_results if isinstance(result, int))

    print(f"Execution time: {execution_time:.4f} seconds")
    print(f"Events published: {event_count}")
    print(f"Events processed: {len(success_results) + len(error_results)}")
    print(f"Successful events: {len(success_results)}")
    print(f"Failed events: {len(error_results)}")
    print(f"Total data rows processed: {total_rows}")
    print(f"Events per second: {event_count/execution_time:.2f}")

    return execution_time, event_count, total_rows


def method2_thread_messaging(dataframes, sample_dates):
    """Process OHLCV data using thread messaging framework."""
    print("METHOD 2: Using Thread Messaging Framework")

    # Setup messaging system with threads (auto-detect cores)
    event_bus = basefunctions.EventBus()
    handler = OHLCVThreadHandler()
    event_bus.register("ohlcv_data", handler)

    # Run the test
    start_time = time.time()
    event_count = 0

    for current_date in sample_dates:
        for ticker_id, df in dataframes.items():
            event = OHLCVDataEvent(dataframe=df, ticker_id=ticker_id, current_date=current_date)
            event_bus.publish(event)
            event_count += 1

    # Wait for completion and get results
    event_bus.join()
    success_results, error_results = event_bus.get_results()
    end_time = time.time()
    execution_time = end_time - start_time

    total_rows = sum(result for result in success_results if isinstance(result, int))

    print(f"Execution time: {execution_time:.4f} seconds")
    print(f"Events published: {event_count}")
    print(f"Events processed: {len(success_results) + len(error_results)}")
    print(f"Successful events: {len(success_results)}")
    print(f"Failed events: {len(error_results)}")
    print(f"Total data rows processed: {total_rows}")
    print(f"Events per second: {event_count/execution_time:.2f}")

    return execution_time, event_count, total_rows


def method3_corelet_messaging(dataframes, sample_dates):
    """Process OHLCV data using corelet messaging framework."""
    print("METHOD 3: Using Corelet Messaging Framework")

    # Setup messaging system with corelets
    event_bus = basefunctions.EventBus()
    handler = OHLCVCoreletHandler()
    event_bus.register("ohlcv_data", handler)

    # Run the test
    start_time = time.time()
    event_count = 0

    for current_date in sample_dates:
        for ticker_id, df in dataframes.items():
            event = OHLCVDataEvent(dataframe=df, ticker_id=ticker_id, current_date=current_date)
            event_bus.publish(event)
            event_count += 1

    # Wait for completion and get results
    event_bus.join()
    success_results, error_results = event_bus.get_results()
    end_time = time.time()
    execution_time = end_time - start_time

    total_rows = sum(result for result in success_results if isinstance(result, int))

    print(f"Execution time: {execution_time:.4f} seconds")
    print(f"Events published: {event_count}")
    print(f"Events processed: {len(success_results) + len(error_results)}")
    print(f"Successful events: {len(success_results)}")
    print(f"Failed events: {len(error_results)}")
    print(f"Total data rows processed: {total_rows}")
    print(f"Events per second: {event_count/execution_time:.2f}")

    return execution_time, event_count, total_rows


def method4_brute_force(dataframes, sample_dates):
    """Process OHLCV data using brute force (direct calculation)."""
    print("METHOD 4: Using Brute Force")

    # Run the test
    start_time = time.time()
    iteration_count = 0
    rows_processed = 0

    for current_date in sample_dates:
        for ticker_id, df in dataframes.items():
            date_slice = df.loc[:current_date]
            rows_processed += len(date_slice)
            iteration_count += 1

    end_time = time.time()
    execution_time = end_time - start_time

    print(f"Execution time: {execution_time:.4f} seconds")
    print(f"Iterations processed: {iteration_count}")
    print(f"Total data rows processed: {rows_processed}")
    print(f"Iterations per second: {iteration_count/execution_time:.2f}")

    return execution_time, iteration_count, rows_processed


def run_performance_comparison():
    """Run performance comparison between all methods."""
    print("Starting comprehensive performance comparison...")

    # Setup dates
    start_date = "2023-01-01"
    end_date = "2023-12-31"

    # Generate data
    print("Generating 20 OHLCV dataframes...")
    start_time = time.time()
    dataframes = {}
    for i in range(20):
        dataframes[i] = generate_random_ohlcv_data(start_date, end_date, i)
    data_gen_time = time.time() - start_time
    print(f"Data generation completed in {data_gen_time:.2f} seconds")

    # Get sample dataframe info
    sample_df = dataframes[0]
    total_dates = len(sample_df.index)
    print(f"Each dataframe contains {total_dates} trading days from {start_date} to {end_date}")

    # For testing, use every 10th date to keep test reasonable
    sample_dates = sample_df.index[::10]
    print(f"Using a sample of {len(sample_dates)} dates for testing")
    print(f"Total expected events/iterations: {len(sample_dates) * len(dataframes)}")

    # Store results
    results = {}

    # Run method 1: Sync Messaging
    print("\n" + "=" * 60)
    time1, events1, rows1 = method1_sync_messaging(dataframes, sample_dates)
    results["Sync"] = (time1, events1, rows1)

    # Run method 2: Thread Messaging
    print("\n" + "=" * 60)
    time2, events2, rows2 = method2_thread_messaging(dataframes, sample_dates)
    results["Thread"] = (time2, events2, rows2)

    # Run method 3: Corelet Messaging
    print("\n" + "=" * 60)
    time3, events3, rows3 = method3_corelet_messaging(dataframes, sample_dates)
    results["Corelet"] = (time3, events3, rows3)

    # Run method 4: Brute Force
    print("\n" + "=" * 60)
    time4, iterations4, rows4 = method4_brute_force(dataframes, sample_dates)
    results["Brute Force"] = (time4, iterations4, rows4)

    # Compare results
    print("\n" + "=" * 60)
    print("COMPREHENSIVE PERFORMANCE COMPARISON")
    print("=" * 60)

    baseline_time = results["Brute Force"][0]

    for method, (exec_time, operations, rows) in results.items():
        overhead = exec_time - baseline_time
        overhead_pct = (exec_time / baseline_time - 1) * 100 if baseline_time > 0 else 0

        print(
            f"{method:12}: {exec_time:8.4f}s | {operations:6d} ops | {rows:8d} rows | "
            f"Overhead: {overhead:+7.4f}s ({overhead_pct:+6.2f}%)"
        )

    print("=" * 60)
    print("Notes:")
    print("- Sync: Direct handler execution in main thread")
    print("- Thread: Handlers run in worker thread pool")
    print("- Corelet: Handlers run in separate processes with pool optimization")
    print("- Brute Force: Direct computation without framework")

    # Print system stats
    print("\n" + "=" * 60)
    print("SYSTEM STATISTICS")
    print("=" * 60)

    # Get stats from last used event bus (corelet system)
    final_event_bus = basefunctions.get_event_bus()
    stats = final_event_bus.get_stats()

    for key, value in stats.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    run_performance_comparison()
