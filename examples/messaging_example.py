"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment , Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Performance comparison between messaging framework and brute force approach
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


# -------------------------------------------------------------
# DATA GENERATION
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


# -------------------------------------------------------------
# EVENT DEFINITIONS
# -------------------------------------------------------------
class OHLCVDataEvent(basefunctions.Event):
    """Event containing OHLCV data for a specific ticker and date."""

    __slots__ = ("dataframe", "ticker_id", "current_date")

    def __init__(self, dataframe, ticker_id, current_date):
        """
        Initialize OHLCV event with business data.

        Parameters
        ----------
        dataframe : pd.DataFrame
            The OHLCV dataframe for a single ticker
        ticker_id : int
            The ID of the ticker
        current_date : datetime
            The current date in the simulation
        """
        # Set event type and system data
        self.type = "ohlcv_data"
        self.source = None
        self.timestamp = datetime.now()

        # Set business data
        self.dataframe = dataframe
        self.ticker_id = ticker_id
        self.current_date = current_date


# -------------------------------------------------------------
# HANDLER DEFINITIONS
# -------------------------------------------------------------
class OHLCVDataHandler(basefunctions.EventHandler):
    """Handler for OHLCV data events."""

    def __init__(self):
        """Initialize the handler."""
        self.processed_count = 0
        self.total_rows_processed = 0

    def handle(self, event: basefunctions.Event) -> None:
        """
        Handle OHLCV data event.

        Parameters
        ----------
        event : Event
            The event containing OHLCV data
        """
        if isinstance(event, OHLCVDataEvent):
            # Direct access to business data - NO MORE NESTING!
            date_slice = event.dataframe.loc[: event.current_date]
            self.total_rows_processed += len(date_slice)
            self.processed_count += 1
            return date_slice


# -------------------------------------------------------------
# METHOD 1: MESSAGING FRAMEWORK IMPLEMENTATION
# -------------------------------------------------------------
def method1_messaging_framework(dataframes, sample_dates):
    """
    Process OHLCV data using the messaging framework.

    Parameters
    ----------
    dataframes : dict
        Dictionary of dataframes with ticker IDs as keys
    sample_dates : list
        List of dates to process

    Returns
    -------
    tuple
        (execution_time, events_published, rows_processed)
    """
    print("METHOD 1: Using Messaging Framework")

    # Setup messaging system
    event_bus = basefunctions.EventBus()
    handler = OHLCVDataHandler()
    event_bus.register("ohlcv_data", handler)

    # Run the test
    start_time = time.time()
    event_count = 0

    # Iterate over all trading days (or sample)
    for current_date in sample_dates:
        # For each day, iterate over all dataframes
        for ticker_id, df in dataframes.items():
            # Create event - SINGLE OBJECT CREATION!
            event = OHLCVDataEvent(dataframe=df, ticker_id=ticker_id, current_date=current_date)
            event_bus.publish(event)
            event_count += 1

    end_time = time.time()
    execution_time = end_time - start_time

    print(f"Execution time: {execution_time:.2f} seconds")
    print(f"Events published: {event_count}")
    print(f"Events processed by handler: {handler.processed_count}")
    print(f"Total data rows processed: {handler.total_rows_processed}")
    print(f"Events per second: {event_count/execution_time:.2f}")

    return execution_time, event_count, handler.total_rows_processed


# -------------------------------------------------------------
# METHOD 2: BRUTE FORCE IMPLEMENTATION
# -------------------------------------------------------------
def method2_brute_force(dataframes, sample_dates):
    """
    Process OHLCV data using brute force (direct calculation).

    Parameters
    ----------
    dataframes : dict
        Dictionary of dataframes with ticker IDs as keys
    sample_dates : list
        List of dates to process

    Returns
    -------
    tuple
        (execution_time, iterations_processed, rows_processed)
    """
    print("METHOD 2: Using Brute Force")

    # Run the test
    start_time = time.time()
    iteration_count = 0
    rows_processed = 0

    # Iterate over all trading days (or sample)
    for current_date in sample_dates:
        # For each day, iterate over all dataframes
        for ticker_id, df in dataframes.items():
            # Directly calculate the slice without messaging framework
            date_slice = df.loc[:current_date]
            rows_processed += len(date_slice)
            iteration_count += 1

    end_time = time.time()
    execution_time = end_time - start_time

    print(f"Execution time: {execution_time:.2f} seconds")
    print(f"Iterations processed: {iteration_count}")
    print(f"Total data rows processed: {rows_processed}")
    print(f"Iterations per second: {iteration_count/execution_time:.2f}")

    return execution_time, iteration_count, rows_processed


# -------------------------------------------------------------
# PERFORMANCE COMPARISON
# -------------------------------------------------------------
def run_performance_comparison():
    """Run performance comparison between messaging framework and brute force."""
    print("Starting performance comparison...")

    # Setup dates
    start_date = "1990-01-01"
    end_date = datetime.now().strftime("%Y-%m-%d")

    # Generate data
    print("Generating 50 OHLCV dataframes...")
    start_time = time.time()
    dataframes = {}
    for i in range(50):
        dataframes[i] = generate_random_ohlcv_data(start_date, end_date, i)
    data_gen_time = time.time() - start_time
    print(f"Data generation completed in {data_gen_time:.2f} seconds")

    # Get sample dataframe info
    sample_df = dataframes[0]
    total_dates = len(sample_df.index)
    print(f"Each dataframe contains {total_dates} trading days from {start_date} to {end_date}")

    # For faster testing, use a sample of dates (every 20th date)
    sample_dates = sample_df.index[::20]
    print(f"Using a sample of {len(sample_dates)} dates for testing")
    print(f"Total expected events/iterations: {len(sample_dates) * 50}")

    # Run method 1: Messaging Framework
    print("\n" + "=" * 50)
    time1, events1, rows1 = method1_messaging_framework(dataframes, sample_dates)

    # Run method 2: Brute Force
    print("\n" + "=" * 50)
    time2, iterations2, rows2 = method2_brute_force(dataframes, sample_dates)

    # Compare results
    print("\n" + "=" * 50)
    print("PERFORMANCE COMPARISON")
    print("=" * 50)
    print(f"Messaging Framework time: {time1:.4f} seconds")
    print(f"Brute Force time: {time2:.4f} seconds")
    print(f"Overhead: {time1 - time2:.4f} seconds ({(time1/time2 - 1)*100:.2f}% slower)")
    print(f"Events/iterations processed: {events1}")
    print(f"Rows processed: {rows1}")

    # Run full test if the sample test was quick
    if time1 < 10 and time2 < 10:
        print("\n" + "=" * 50)
        print("Running FULL TEST with all dates...")

        # Run method 1: Messaging Framework (full)
        print("\n" + "=" * 50)
        full_time1, full_events1, full_rows1 = method1_messaging_framework(
            dataframes, sample_df.index
        )

        # Run method 2: Brute Force (full)
        print("\n" + "=" * 50)
        full_time2, full_iterations2, full_rows2 = method2_brute_force(dataframes, sample_df.index)

        # Compare full results
        print("\n" + "=" * 50)
        print("FULL TEST PERFORMANCE COMPARISON")
        print("=" * 50)
        print(f"Messaging Framework time: {full_time1:.4f} seconds")
        print(f"Brute Force time: {full_time2:.4f} seconds")
        print(
            f"Overhead: {full_time1 - full_time2:.4f} seconds ({(full_time1/full_time2 - 1)*100:.2f}% slower)"
        )
        print(f"Events processed: {full_events1}")
        print(f"Rows processed: {full_rows1}")


if __name__ == "__main__":
    run_performance_comparison()
