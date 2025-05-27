"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich
  Project : database_load_generator
  Copyright (c) by neuraldevelopment
  All rights reserved.
  Description:
  Event-based load generator for database performance testing with OHLCV data
  Uses DbEventBus for proper async processing instead of primitive threading
 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import argparse
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import threading
import basefunctions

# -------------------------------------------------------------
# CONFIGURATION
# -------------------------------------------------------------
DAX_SYMBOLS = [
    "ADS",
    "ALV",
    "BAS",
    "BAYN",
    "BEI",
    "BMW",
    "CON",
    "1COV",
    "DAI",
    "DHER",
    "DTE",
    "EOAN",
    "FRE",
    "FME",
    "HEI",
    "HEN3",
    "IFX",
    "LIN",
    "MRK",
    "MTX",
    "MUV2",
    "NWRG",
    "PAH3",
    "POR",
    "PSM",
    "PUM",
    "QGEN",
    "RHM",
    "RWE",
    "SAP",
    "SHL",
    "SIE",
    "SY1",
    "TKA",
    "VOW3",
    "VNA",
    "WDI",
    "ZAL",
    "DPW",
    "HAB",
]

# Default values
DEFAULT_START_DATE = "1990-01-01"
DEFAULT_NUM_TABLES = 100
DEFAULT_TABLE_PREFIX = "Test"
DEFAULT_NUM_THREADS = 10
DEFAULT_CORELET_POOL_SIZE = 4
DEFAULT_EXECUTION_MODE = "thread"

# Execution mode mapping
EXECUTION_MODES = {"sync": "sync", "thread": "thread", "corelet": "corelet"}


# -------------------------------------------------------------
# DATA GENERATION
# -------------------------------------------------------------
def generate_ohlcv_data(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Generate realistic OHLCV data for a given symbol and date range.

    Parameters
    ----------
    symbol : str
        Stock symbol (e.g., 'BMW')
    start_date : str
        Start date in YYYY-MM-DD format
    end_date : str
        End date in YYYY-MM-DD format

    Returns
    -------
    pd.DataFrame
        DataFrame with columns: symbol, date, open, high, low, close, volume
    """
    # Create date range
    dates = pd.date_range(start=start_date, end=end_date, freq="D")

    # Remove weekends (Saturday=5, Sunday=6)
    dates = dates[dates.weekday < 5]

    num_days = len(dates)

    if num_days == 0:
        # Return empty DataFrame with correct structure
        return pd.DataFrame(columns=["symbol", "date", "open", "high", "low", "close", "volume"])

    # Generate realistic price data using random walk
    np.random.seed(hash(symbol) % 2**32)  # Consistent seed per symbol

    # Starting price between 20 and 200 EUR
    start_price = np.random.uniform(20, 200)

    # Daily returns (normal distribution with realistic volatility)
    daily_returns = np.random.normal(0.0005, 0.02, num_days)  # ~0.05% daily return, 2% volatility

    # Calculate closing prices using cumulative returns
    close_prices = start_price * np.cumprod(1 + daily_returns)

    # Generate OHLC from close prices
    open_prices = np.zeros(num_days)
    high_prices = np.zeros(num_days)
    low_prices = np.zeros(num_days)

    open_prices[0] = start_price
    for i in range(1, num_days):
        # Open is previous close with small gap
        gap = np.random.normal(0, 0.005)  # 0.5% average gap
        open_prices[i] = close_prices[i - 1] * (1 + gap)

    for i in range(num_days):
        # High and low based on intraday volatility
        intraday_volatility = np.random.uniform(0.01, 0.05)  # 1-5% intraday range

        # High is the maximum of open/close plus some upward movement
        base_high = max(open_prices[i], close_prices[i])
        high_prices[i] = base_high * (1 + np.random.uniform(0, intraday_volatility))

        # Low is the minimum of open/close minus some downward movement
        base_low = min(open_prices[i], close_prices[i])
        low_prices[i] = base_low * (1 - np.random.uniform(0, intraday_volatility))

    # Generate volume (log-normal distribution)
    volumes = np.random.lognormal(mean=13, sigma=1, size=num_days).astype(
        int
    )  # ~400k average volume

    # Create DataFrame
    df = pd.DataFrame(
        {
            "symbol": symbol,
            "date": dates,
            "open": np.round(open_prices, 2),
            "high": np.round(high_prices, 2),
            "low": np.round(low_prices, 2),
            "close": np.round(close_prices, 2),
            "volume": volumes,
        }
    )

    return df


def calculate_trading_days(start_date: str, end_date: str) -> int:
    """Calculate approximate number of trading days between two dates."""
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    total_days = (end - start).days

    if total_days <= 0:
        return 0

    # Approximate: 5 trading days per week, minus ~5% for holidays
    trading_days = int(total_days * 5 / 7 * 0.95)
    return max(trading_days, 1)


def estimate_operation_time(
    start_date: str, num_tables: int, num_threads: int, execution_mode: str
) -> Dict[str, Any]:
    """
    Estimate total operation time based on data size, threading and execution mode.

    Parameters
    ----------
    start_date : str
        Start date for data generation
    num_tables : int
        Number of tables to create
    num_threads : int
        Number of worker threads
    execution_mode : str
        Execution mode (sync, thread, corelet)

    Returns
    -------
    Dict[str, Any]
        Estimation results
    """
    end_date = datetime.now().strftime("%Y-%m-%d")

    # Calculate trading days
    trading_days = calculate_trading_days(start_date, end_date)

    # Data size calculations
    rows_per_symbol = trading_days
    total_symbols = len(DAX_SYMBOLS)
    total_tables = num_tables
    total_rows = rows_per_symbol * total_symbols * total_tables

    # Size estimates
    row_size_bytes = 8 + 10 + 4 * 8 + 8  # symbol(8) + date(10) + 4*float(8) + volume(8) ≈ 70 bytes
    total_data_mb = (total_rows * row_size_bytes) / (1024 * 1024)

    # Performance estimates based on execution mode and threading
    if execution_mode == "sync":
        # Synchronous execution - single threaded
        base_inserts_cached = 5000
        base_inserts_direct = 2000
        threading_factor = 1.0
    elif execution_mode == "thread":
        # Thread execution - scales with thread count
        base_inserts_cached = 8000
        base_inserts_direct = 3000
        threading_factor = min(num_threads * 0.8, 20)  # Diminishing returns after 20 threads
    elif execution_mode == "corelet":
        # Process execution - best for CPU intensive operations
        base_inserts_cached = 12000
        base_inserts_direct = 4000
        threading_factor = min(num_threads * 0.9, 25)  # Better scaling for process-based
    else:
        # Default to thread mode
        base_inserts_cached = 8000
        base_inserts_direct = 3000
        threading_factor = min(num_threads * 0.8, 20)

    inserts_per_second_cached = int(base_inserts_cached * threading_factor)
    inserts_per_second_direct = int(base_inserts_direct * threading_factor)

    estimated_time_cached = total_rows / inserts_per_second_cached
    estimated_time_direct = total_rows / inserts_per_second_direct

    print(f"\n=== OPERATION SIZE ESTIMATION ===")
    print(f"Date range: {start_date} to {end_date}")
    print(f"Trading days per symbol: {trading_days:,}")
    print(f"DAX symbols: {total_symbols}")
    print(f"Tables to create: {total_tables}")
    print(f"Total rows to insert: {total_rows:,}")
    print(f"Estimated data size: {total_data_mb:.1f} MB")

    print(f"\n=== EXECUTION CONFIGURATION ===")
    print(f"Execution mode: {execution_mode}")
    print(f"Worker threads: {num_threads}")
    print(f"Threading factor: {threading_factor:.1f}x")

    print(f"\n=== TIME ESTIMATION ===")
    print(f"With caching: ~{estimated_time_cached/60:.1f} minutes")
    print(f"Without caching: ~{estimated_time_direct/60:.1f} minutes")
    print(
        f"Performance gain: ~{estimated_time_direct/estimated_time_cached:.1f}x faster with caching"
    )

    # Additional scaling information
    print(f"\n=== PERFORMANCE METRICS ===")
    print(f"Estimated rows per minute (cached): {inserts_per_second_cached * 60:,}")
    print(f"Estimated rows per minute (direct): {inserts_per_second_direct * 60:,}")
    print(
        f"Data processing rate (cached): ~{(total_data_mb / (estimated_time_cached/60)):.1f} MB/min"
    )
    print(
        f"Data processing rate (direct): ~{(total_data_mb / (estimated_time_direct/60)):.1f} MB/min"
    )

    return {
        "start_date": start_date,
        "end_date": end_date,
        "trading_days": trading_days,
        "total_rows": total_rows,
        "data_size_mb": total_data_mb,
        "estimated_time_cached": estimated_time_cached,
        "estimated_time_direct": estimated_time_direct,
        "total_tables": total_tables,
        "total_symbols": total_symbols,
        "execution_mode": execution_mode,
        "num_threads": num_threads,
        "threading_factor": threading_factor,
        "inserts_per_second_cached": inserts_per_second_cached,
        "inserts_per_second_direct": inserts_per_second_direct,
    }


# -------------------------------------------------------------
# PERFORMANCE STATISTICS
# -------------------------------------------------------------
class PerformanceStats:
    """
    Thread-safe performance statistics collector for event-based operations.
    """

    def __init__(self):
        self.lock = threading.RLock()
        self.reset()

    def reset(self):
        """Reset all statistics."""
        with self.lock:
            self.start_time = None
            self.end_time = None

            # Event tracking
            self.events_submitted = 0
            self.events_completed = 0
            self.events_failed = 0

            # Table operations
            self.tables_created = 0
            self.table_creation_times = []
            self.table_creation_errors = []

            # DataFrame operations
            self.dataframes_written = 0
            self.dataframe_write_times = []
            self.dataframe_write_errors = []
            self.total_rows_written = 0

            # Cache operations
            self.caches_flushed = 0
            self.cache_flush_times = []
            self.cache_flush_errors = []

            # General timing
            self.operation_times = []
            self.event_ids = []

    def start_test(self):
        """Mark test start time."""
        with self.lock:
            self.start_time = time.time()

    def end_test(self):
        """Mark test end time."""
        with self.lock:
            self.end_time = time.time()

    def add_event_submitted(self, event_id: str):
        """Track submitted event."""
        with self.lock:
            self.events_submitted += 1
            self.event_ids.append(event_id)

    def add_table_created(self, execution_time: float):
        """Track successful table creation."""
        with self.lock:
            self.tables_created += 1
            self.table_creation_times.append(execution_time)
            self.events_completed += 1

    def add_table_error(self, error: str):
        """Track table creation error."""
        with self.lock:
            self.table_creation_errors.append(error)
            self.events_failed += 1

    def add_dataframe_written(self, execution_time: float, rows_count: int):
        """Track successful DataFrame write."""
        with self.lock:
            self.dataframes_written += 1
            self.dataframe_write_times.append(execution_time)
            self.total_rows_written += rows_count
            self.events_completed += 1

    def add_dataframe_error(self, error: str):
        """Track DataFrame write error."""
        with self.lock:
            self.dataframe_write_errors.append(error)
            self.events_failed += 1

    def add_cache_flushed(self, execution_time: float):
        """Track successful cache flush."""
        with self.lock:
            self.caches_flushed += 1
            self.cache_flush_times.append(execution_time)
            self.events_completed += 1

    def add_cache_error(self, error: str):
        """Track cache flush error."""
        with self.lock:
            self.cache_flush_errors.append(error)
            self.events_failed += 1

    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive statistics summary."""
        with self.lock:
            total_time = (
                (self.end_time - self.start_time) if self.start_time and self.end_time else 0
            )

            return {
                "total_time": total_time,
                "events_submitted": self.events_submitted,
                "events_completed": self.events_completed,
                "events_failed": self.events_failed,
                "completion_rate": (
                    (self.events_completed / self.events_submitted * 100)
                    if self.events_submitted > 0
                    else 0
                ),
                "tables_created": self.tables_created,
                "avg_table_creation_time": (
                    np.mean(self.table_creation_times) if self.table_creation_times else 0
                ),
                "table_creation_errors": len(self.table_creation_errors),
                "dataframes_written": self.dataframes_written,
                "total_rows_written": self.total_rows_written,
                "avg_dataframe_write_time": (
                    np.mean(self.dataframe_write_times) if self.dataframe_write_times else 0
                ),
                "rows_per_second": (self.total_rows_written / total_time) if total_time > 0 else 0,
                "dataframe_write_errors": len(self.dataframe_write_errors),
                "caches_flushed": self.caches_flushed,
                "avg_cache_flush_time": (
                    np.mean(self.cache_flush_times) if self.cache_flush_times else 0
                ),
                "cache_flush_errors": len(self.cache_flush_errors),
            }


# -------------------------------------------------------------
# EVENT-BASED LOAD GENERATOR
# -------------------------------------------------------------
class EventBasedLoadGenerator:
    """
    Event-based load generator using DbEventBus for proper async processing.
    """

    def __init__(
        self,
        instance_name: str,
        start_date: str,
        num_tables: int,
        table_prefix: str,
        num_threads: int,
        corelet_pool_size: int,
        execution_mode: str,
    ):
        self.instance_name = instance_name
        self.start_date = start_date
        self.num_tables = num_tables
        self.table_prefix = table_prefix
        self.execution_mode = execution_mode

        # Initialize database manager and event bus
        self.db_manager = basefunctions.DbManager()
        self.db_manager.configure_eventbus(
            num_threads=num_threads, corelet_pool_size=corelet_pool_size
        )
        self.event_bus = self.db_manager.get_event_bus()

        # Statistics tracking
        self.stats = PerformanceStats()
        self.logger = basefunctions.get_logger(__name__)

        # Test database
        self.test_database = None

        # Event tracking
        self.pending_events = set()
        self.completed_events = set()

        self.logger.info(f"Initialized EventBasedLoadGenerator:")
        self.logger.info(f"  Instance: {instance_name}")
        self.logger.info(f"  Tables: {num_tables}")
        self.logger.info(f"  Start Date: {start_date}")
        self.logger.info(f"  Execution Mode: {execution_mode}")
        self.logger.info(f"  Threads: {num_threads}")
        self.logger.info(f"  Corelet Pool: {corelet_pool_size}")

    def create_test_database(self) -> str:
        """Create test database synchronously."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        db_name = f"loadtest_{timestamp}"

        self.logger.info(f"Creating test database: {db_name}")

        instance = self.db_manager.get_instance(self.instance_name)
        success = instance.create_database(db_name)

        if not success:
            raise Exception(f"Failed to create database {db_name}")

        self.test_database = db_name
        return db_name

    def get_table_schema_sql(self, table_name: str) -> str:
        """Generate CREATE TABLE SQL for OHLCV data with proper PostgreSQL schema."""
        return f"""
        CREATE TABLE public.{table_name} (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(10) NOT NULL,
            date DATE NOT NULL,
            open DECIMAL(10,2) NOT NULL,
            high DECIMAL(10,2) NOT NULL,
            low DECIMAL(10,2) NOT NULL,
            close DECIMAL(10,2) NOT NULL,
            volume BIGINT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(symbol, date)
        );
        CREATE INDEX idx_{table_name}_symbol_date ON public.{table_name}(symbol, date);
        """

    # -------------------------------------------------------------
    # CALLBACK FUNCTIONS
    # -------------------------------------------------------------
    def table_creation_callback(self, success: bool, result: Dict[str, Any]):
        """Callback for table creation events."""
        task_id = result.get("task_id")
        if task_id in self.pending_events:
            self.pending_events.remove(task_id)
            self.completed_events.add(task_id)

        if success:
            execution_time = result.get("execution_time", 0)
            self.stats.add_table_created(execution_time)
            self.logger.debug(f"Table created successfully: {task_id}")
        else:
            error = result.get("error", "Unknown error")
            self.stats.add_table_error(error)
            self.logger.error(f"Table creation failed: {task_id} - {error}")

    def dataframe_write_callback(self, success: bool, result: Dict[str, Any]):
        """Callback for DataFrame write events."""
        task_id = result.get("task_id")
        if task_id in self.pending_events:
            self.pending_events.remove(task_id)
            self.completed_events.add(task_id)

        if success:
            execution_time = result.get("execution_time", 0)
            rows_count = result.get("rows_count", 0)
            self.stats.add_dataframe_written(execution_time, rows_count)
            self.logger.debug(f"DataFrame written successfully: {task_id} - {rows_count} rows")
        else:
            error = result.get("error", "Unknown error")
            self.stats.add_dataframe_error(error)
            self.logger.error(f"DataFrame write failed: {task_id} - {error}")

    def cache_flush_callback(self, success: bool, result: Dict[str, Any]):
        """Callback for cache flush events."""
        task_id = result.get("task_id")
        if task_id in self.pending_events:
            self.pending_events.remove(task_id)
            self.completed_events.add(task_id)

        if success:
            execution_time = result.get("execution_time", 0)
            self.stats.add_cache_flushed(execution_time)
            self.logger.debug(f"Cache flushed successfully: {task_id}")
        else:
            error = result.get("error", "Unknown error")
            self.stats.add_cache_error(error)
            self.logger.error(f"Cache flush failed: {task_id} - {error}")

    # -------------------------------------------------------------
    # TEST EXECUTION METHODS
    # -------------------------------------------------------------
    def run_cached_test(self) -> Dict[str, Any]:
        """
        Run load test with caching strategy using event-based processing.

        Returns
        -------
        Dict[str, Any]
            Test results and statistics
        """
        self.logger.info("Starting cached strategy test using EventBus")

        # Create test database
        db_name = self.create_test_database()
        end_date = datetime.now().strftime("%Y-%m-%d")

        # Reset statistics
        self.stats.reset()
        self.stats.start_test()

        # Phase 1: Submit table creation events
        self.logger.info("Phase 1: Submitting table creation events")
        for table_num in range(1, self.num_tables + 1):
            table_name = f"{self.table_prefix}{table_num:03d}"
            schema_sql = self.get_table_schema_sql(table_name)

            task_id = self.event_bus.submit_query_async(
                instance_name=self.instance_name,
                database=db_name,
                query=schema_sql,
                query_type="execute",
                callback=self.table_creation_callback,
                execution_mode=self.execution_mode,
            )

            self.pending_events.add(task_id)
            self.stats.add_event_submitted(task_id)

        self.logger.info(f"Submitted {len(self.pending_events)} table creation events")

        # Phase 2: Submit DataFrame write events (cached)
        self.logger.info("Phase 2: Submitting DataFrame write events (cached)")
        for table_num in range(1, self.num_tables + 1):
            table_name = f"{self.table_prefix}{table_num:03d}"

            for symbol in DAX_SYMBOLS:
                # Generate OHLCV data
                df = generate_ohlcv_data(symbol, self.start_date, end_date)

                if len(df) > 0:
                    # Create event data with cached parameter
                    event_data = {
                        "operation": "write",
                        "table_name": table_name,
                        "dataframe": df,
                        "cached": True,  # Add cached to event data
                        "if_exists": "append",
                    }

                    task_id = self.event_bus.submit_dataframe_operation(
                        instance_name=self.instance_name,
                        database=db_name,
                        **event_data,
                        callback=self.dataframe_write_callback,
                        execution_mode=self.execution_mode,
                    )

                    self.pending_events.add(task_id)
                    self.stats.add_event_submitted(task_id)

        self.logger.info(
            f"Submitted {len(self.pending_events) - self.stats.tables_created} DataFrame write events"
        )

        # Phase 3: Submit cache flush events
        self.logger.info("Phase 3: Submitting cache flush events")
        for table_num in range(1, self.num_tables + 1):
            table_name = f"{self.table_prefix}{table_num:03d}"

            task_id = self.event_bus.submit_dataframe_operation(
                instance_name=self.instance_name,
                database=db_name,
                operation="flush_cache",
                table_name=table_name,
                callback=self.cache_flush_callback,
                execution_mode=self.execution_mode,
            )

            self.pending_events.add(task_id)
            self.stats.add_event_submitted(task_id)

        self.logger.info(f"Total events submitted: {self.stats.events_submitted}")

        # Phase 4: Wait for completion
        self.logger.info("Phase 4: Waiting for all events to complete")
        self._wait_for_completion()

        self.stats.end_test()

        return {
            "strategy": "cached",
            "database_name": db_name,
            "stats": self.stats.get_summary(),
            "execution_mode": self.execution_mode,
            "config": {
                "start_date": self.start_date,
                "num_tables": self.num_tables,
                "table_prefix": self.table_prefix,
                "symbols": len(DAX_SYMBOLS),
            },
        }

    def run_direct_test(self) -> Dict[str, Any]:
        """
        Run load test with direct writing strategy using event-based processing.

        Returns
        -------
        Dict[str, Any]
            Test results and statistics
        """
        self.logger.info("Starting direct strategy test using EventBus")

        # Create test database
        db_name = self.create_test_database()
        end_date = datetime.now().strftime("%Y-%m-%d")

        # Reset statistics
        self.stats.reset()
        self.stats.start_test()

        # Phase 1: Submit table creation events
        self.logger.info("Phase 1: Submitting table creation events")
        for table_num in range(1, self.num_tables + 1):
            table_name = f"{self.table_prefix}{table_num:03d}"
            schema_sql = self.get_table_schema_sql(table_name)

            task_id = self.event_bus.submit_query_async(
                instance_name=self.instance_name,
                database=db_name,
                query=schema_sql,
                query_type="execute",
                callback=self.table_creation_callback,
                execution_mode=self.execution_mode,
            )

            self.pending_events.add(task_id)
            self.stats.add_event_submitted(task_id)

        self.logger.info(f"Submitted {len(self.pending_events)} table creation events")

        # Phase 2: Submit DataFrame write events (direct)
        self.logger.info("Phase 2: Submitting DataFrame write events (direct)")
        for table_num in range(1, self.num_tables + 1):
            table_name = f"{self.table_prefix}{table_num:03d}"

            for symbol in DAX_SYMBOLS:
                # Generate OHLCV data
                df = generate_ohlcv_data(symbol, self.start_date, end_date)

                if len(df) > 0:
                    # Create event data with cached parameter
                    event_data = {
                        "operation": "write",
                        "table_name": table_name,
                        "dataframe": df,
                        "cached": False,  # Direct writing
                        "if_exists": "append",
                    }

                    task_id = self.event_bus.submit_dataframe_operation(
                        instance_name=self.instance_name,
                        database=db_name,
                        **event_data,
                        callback=self.dataframe_write_callback,
                        execution_mode=self.execution_mode,
                    )

                    self.pending_events.add(task_id)
                    self.stats.add_event_submitted(task_id)

        self.logger.info(f"Total events submitted: {self.stats.events_submitted}")

        # Phase 3: Wait for completion (no cache flush needed for direct writes)
        self.logger.info("Phase 3: Waiting for all events to complete")
        self._wait_for_completion()

        self.stats.end_test()

        return {
            "strategy": "direct",
            "database_name": db_name,
            "stats": self.stats.get_summary(),
            "execution_mode": self.execution_mode,
            "config": {
                "start_date": self.start_date,
                "num_tables": self.num_tables,
                "table_prefix": self.table_prefix,
                "symbols": len(DAX_SYMBOLS),
            },
        }

    def _wait_for_completion(self):
        """Wait for all pending events to complete."""
        timeout = 3600  # 1 hour max timeout
        start_wait = time.time()
        last_progress = time.time()

        while self.pending_events and (time.time() - start_wait) < timeout:
            time.sleep(1)

            # Progress update every 10 seconds
            if time.time() - last_progress > 10:
                completed = len(self.completed_events)
                total = self.stats.events_submitted
                progress = (completed / total * 100) if total > 0 else 0

                self.logger.info(
                    f"Progress: {completed}/{total} events completed ({progress:.1f}%)"
                )
                last_progress = time.time()

        # Final wait for EventBus to complete
        self.event_bus.wait_for_completion(timeout=10)

        if self.pending_events:
            self.logger.warning(f"Timeout: {len(self.pending_events)} events still pending")

    def cleanup(self):
        """Clean up resources."""
        try:
            self.db_manager.close_all()
            self.logger.info("Database connections closed")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")


# -------------------------------------------------------------
# RESULTS COMPARISON
# -------------------------------------------------------------
def print_test_results(cached_results: Dict[str, Any], direct_results: Dict[str, Any]):
    """Print comprehensive test results comparison."""
    print("\n" + "=" * 80)
    print("EVENT-BASED LOAD TEST RESULTS COMPARISON")
    print("=" * 80)

    # Extract stats
    cached_stats = cached_results["stats"]
    direct_stats = direct_results["stats"]

    print(f"\n=== CONFIGURATION ===")
    config = cached_results.get("config", {})
    print(f"Start Date: {config.get('start_date', 'Unknown')}")
    print(f"Tables: {config.get('num_tables', 'Unknown')}")
    print(f"Symbols: {config.get('symbols', 'Unknown')}")
    print(f"Table Prefix: {config.get('table_prefix', 'Unknown')}")
    print(f"Execution Mode: {cached_results.get('execution_mode', 'Unknown')}")

    print(f"\n=== OVERALL PERFORMANCE ===")
    print(
        f"{'Strategy':<15} {'Time(s)':<10} {'Events':<8} {'Rows':<12} {'Rows/sec':<12} {'Completion%':<12}"
    )
    print("-" * 80)

    cached_completion = cached_stats.get("completion_rate", 0)
    direct_completion = direct_stats.get("completion_rate", 0)

    print(
        f"{'Cached':<15} {cached_stats['total_time']:<10.1f} {cached_stats['events_completed']:<8} {cached_stats['total_rows_written']:<12,} {cached_stats['rows_per_second']:<12,.0f} {cached_completion:<12.1f}"
    )
    print(
        f"{'Direct':<15} {direct_stats['total_time']:<10.1f} {direct_stats['events_completed']:<8} {direct_stats['total_rows_written']:<12,} {direct_stats['rows_per_second']:<12,.0f} {direct_completion:<12.1f}"
    )

    # Performance gain calculation
    if cached_stats["total_time"] > 0 and direct_stats["total_time"] > 0:
        performance_gain = direct_stats["total_time"] / cached_stats["total_time"]
        print(f"\nCached strategy is {performance_gain:.1f}x faster than direct writing")

    print(f"\n=== EVENT SYSTEM PERFORMANCE ===")
    print(
        f"{'Strategy':<15} {'Submitted':<10} {'Completed':<10} {'Failed':<8} {'Success Rate':<12}"
    )
    print("-" * 65)
    print(
        f"{'Cached':<15} {cached_stats['events_submitted']:<10} {cached_stats['events_completed']:<10} {cached_stats['events_failed']:<8} {cached_completion:<12.1f}%"
    )
    print(
        f"{'Direct':<15} {direct_stats['events_submitted']:<10} {direct_stats['events_completed']:<10} {direct_stats['events_failed']:<8} {direct_completion:<12.1f}%"
    )

    print(f"\n=== OPERATION BREAKDOWN ===")
    print(f"{'Strategy':<15} {'Tables':<8} {'DataFrames':<12} {'Cache Flushes':<12}")
    print("-" * 50)
    print(
        f"{'Cached':<15} {cached_stats['tables_created']:<8} {cached_stats['dataframes_written']:<12} {cached_stats['caches_flushed']:<12}"
    )
    print(
        f"{'Direct':<15} {direct_stats['tables_created']:<8} {direct_stats['dataframes_written']:<12} {direct_stats['caches_flushed']:<12}"
    )

    print(f"\n=== AVERAGE OPERATION TIMES ===")
    print(f"{'Strategy':<15} {'Table Create':<12} {'DataFrame Write':<15} {'Cache Flush':<12}")
    print("-" * 55)
    print(
        f"{'Cached':<15} {cached_stats['avg_table_creation_time']:<12.3f} {cached_stats['avg_dataframe_write_time']:<15.3f} {cached_stats['avg_cache_flush_time']:<12.3f}"
    )
    print(
        f"{'Direct':<15} {direct_stats['avg_table_creation_time']:<12.3f} {direct_stats['avg_dataframe_write_time']:<15.3f} {direct_stats['avg_cache_flush_time']:<12.3f}"
    )

    # Error summary
    total_cached_errors = (
        cached_stats["table_creation_errors"]
        + cached_stats["dataframe_write_errors"]
        + cached_stats["cache_flush_errors"]
    )
    total_direct_errors = (
        direct_stats["table_creation_errors"]
        + direct_stats["dataframe_write_errors"]
        + direct_stats["cache_flush_errors"]
    )

    if total_cached_errors > 0 or total_direct_errors > 0:
        print(f"\n=== ERROR SUMMARY ===")
        print(f"Cached strategy total errors: {total_cached_errors}")
        print(f"Direct strategy total errors: {total_direct_errors}")

    print(f"\n=== DATABASE INFORMATION ===")
    print(f"Cached test database: {cached_results['database_name']}")
    print(f"Direct test database: {direct_results['database_name']}")


# -------------------------------------------------------------
# COMMAND LINE INTERFACE
# -------------------------------------------------------------
def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Event-Based Database Load Generator for OHLCV Data"
    )

    parser.add_argument(
        "instance_name",
        nargs="?",
        default="dev_test_db_postgres",
        help="Database instance name (default: dev_test_db_postgres)",
    )

    parser.add_argument(
        "--threads",
        type=int,
        default=DEFAULT_NUM_THREADS,
        help=f"Number of worker threads for EventBus (default: {DEFAULT_NUM_THREADS})",
    )

    parser.add_argument(
        "--corelet-pool-size",
        type=int,
        default=DEFAULT_CORELET_POOL_SIZE,
        help=f"Number of corelet processes for heavy operations (default: {DEFAULT_CORELET_POOL_SIZE})",
    )

    parser.add_argument(
        "--execution-mode",
        choices=list(EXECUTION_MODES.keys()),
        default=DEFAULT_EXECUTION_MODE,
        help=f"Execution mode for events (default: {DEFAULT_EXECUTION_MODE})",
    )

    parser.add_argument(
        "--tables",
        type=int,
        default=DEFAULT_NUM_TABLES,
        help=f"Number of tables to create (default: {DEFAULT_NUM_TABLES})",
    )

    parser.add_argument(
        "--start-date",
        type=str,
        default=DEFAULT_START_DATE,
        help=f"Start date for data generation in YYYY-MM-DD format (default: {DEFAULT_START_DATE})",
    )

    parser.add_argument(
        "--table-prefix",
        type=str,
        default=DEFAULT_TABLE_PREFIX,
        help=f"Prefix for table names (default: {DEFAULT_TABLE_PREFIX})",
    )

    parser.add_argument(
        "--estimate-only",
        action="store_true",
        help="Only show time estimation, don't run actual tests",
    )

    parser.add_argument("--cached-only", action="store_true", help="Run only cached strategy test")

    parser.add_argument(
        "--direct-only", action="store_true", help="Run only direct writing strategy test"
    )

    parser.add_argument(
        "--quick-test",
        action="store_true",
        help="Run quick test (10 tables, 2020-01-01 start date, optimized settings)",
    )

    parser.add_argument(
        "--validate-date", action="store_true", help="Validate start date format and exit"
    )

    parser.add_argument(
        "--show-eventbus-stats",
        action="store_true",
        help="Show detailed EventBus statistics during and after test",
    )

    return parser.parse_args()


def validate_date_format(date_string: str) -> bool:
    """Validate date format and check if date is reasonable."""
    try:
        date_obj = datetime.strptime(date_string, "%Y-%m-%d")

        # Check if date is not in the future
        if date_obj > datetime.now():
            print(f"Error: Start date {date_string} is in the future")
            return False

        # Check if date is not too far in the past (before 1980)
        if date_obj.year < 1980:
            print(f"Warning: Start date {date_string} is quite far in the past")

        # Check if date is reasonable for stock data
        if date_obj.year < 1900:
            print(f"Error: Start date {date_string} is too far in the past for stock data")
            return False

        return True

    except ValueError:
        print(f"Error: Invalid date format '{date_string}'. Use YYYY-MM-DD format.")
        return False


def validate_execution_mode(mode: str) -> bool:
    """Validate execution mode."""
    if mode not in EXECUTION_MODES:
        print(
            f"Error: Invalid execution mode '{mode}'. Valid modes: {list(EXECUTION_MODES.keys())}"
        )
        return False
    return True


# -------------------------------------------------------------
# MAIN FUNCTION
# -------------------------------------------------------------
def main():
    """Main function."""
    args = parse_arguments()

    # Quick test override
    if args.quick_test:
        print("=" * 60)
        print("QUICK TEST MODE ENABLED")
        print("=" * 60)
        args.tables = 10
        args.start_date = "2020-01-01"
        args.threads = 8
        args.execution_mode = "thread"
        print(f"Overriding settings: {args.tables} tables, start date: {args.start_date}")
        print(f"Threads: {args.threads}, execution mode: {args.execution_mode}")

    # Validate inputs
    if not validate_date_format(args.start_date):
        return

    if not validate_execution_mode(args.execution_mode):
        return

    if args.validate_date:
        print(f"Date format validation successful: {args.start_date}")
        return

    print("=" * 80)
    print("EVENT-BASED DATABASE LOAD GENERATOR - OHLCV PERFORMANCE TEST")
    print("=" * 80)
    print(f"Instance: {args.instance_name}")
    print(f"Execution Mode: {args.execution_mode}")
    print(f"Worker Threads: {args.threads}")
    print(f"Corelet Pool Size: {args.corelet_pool_size}")
    print(f"Tables: {args.tables}")
    print(f"Start Date: {args.start_date}")
    print(f"Table Prefix: {args.table_prefix}")
    print(f"Symbols: {len(DAX_SYMBOLS)}")

    # Show estimation
    estimates = estimate_operation_time(
        args.start_date, args.tables, args.threads, args.execution_mode
    )

    if args.estimate_only:
        print("\nEstimation complete. Use --help for options to run actual tests.")
        return

    # Initialize event-based load generator
    generator = EventBasedLoadGenerator(
        instance_name=args.instance_name,
        start_date=args.start_date,
        num_tables=args.tables,
        table_prefix=args.table_prefix,
        num_threads=args.threads,
        corelet_pool_size=args.corelet_pool_size,
        execution_mode=args.execution_mode,
    )

    cached_results = None
    direct_results = None

    try:
        # Show initial EventBus stats
        if args.show_eventbus_stats:
            initial_stats = generator.event_bus.get_stats()
            print(f"\nInitial EventBus Stats: {initial_stats}")

        # Run tests based on arguments
        if not args.direct_only:
            print(f"\n{'-'*60}")
            print("RUNNING CACHED STRATEGY TEST (EVENT-BASED)")
            print(f"{'-'*60}")
            cached_results = generator.run_cached_test()

            if args.show_eventbus_stats:
                eventbus_stats = generator.event_bus.get_stats()
                print(f"EventBus Stats after cached test: {eventbus_stats}")

        if not args.cached_only:
            print(f"\n{'-'*60}")
            print("RUNNING DIRECT STRATEGY TEST (EVENT-BASED)")
            print(f"{'-'*60}")

            # Create new generator instance for fresh stats
            generator = EventBasedLoadGenerator(
                instance_name=args.instance_name,
                start_date=args.start_date,
                num_tables=args.tables,
                table_prefix=args.table_prefix,
                num_threads=args.threads,
                corelet_pool_size=args.corelet_pool_size,
                execution_mode=args.execution_mode,
            )

            direct_results = generator.run_direct_test()

            if args.show_eventbus_stats:
                eventbus_stats = generator.event_bus.get_stats()
                print(f"EventBus Stats after direct test: {eventbus_stats}")

        # Print comparison if both tests were run
        if cached_results and direct_results:
            print_test_results(cached_results, direct_results)
        elif cached_results:
            stats = cached_results["stats"]
            print(f"\nCached test completed in {stats['total_time']:.1f}s")
            print(f"Total rows processed: {stats['total_rows_written']:,}")
            print(f"Processing rate: {stats['rows_per_second']:.0f} rows/sec")
            print(
                f"Events completed: {stats['events_completed']}/{stats['events_submitted']} ({stats['completion_rate']:.1f}%)"
            )
        elif direct_results:
            stats = direct_results["stats"]
            print(f"\nDirect test completed in {stats['total_time']:.1f}s")
            print(f"Total rows processed: {stats['total_rows_written']:,}")
            print(f"Processing rate: {stats['rows_per_second']:.0f} rows/sec")
            print(
                f"Events completed: {stats['events_completed']}/{stats['events_submitted']} ({stats['completion_rate']:.1f}%)"
            )

    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\nTest failed with error: {str(e)}")
        import traceback

        traceback.print_exc()
    finally:
        # Clean up
        generator.cleanup()
        print("\nEvent-based load test completed")


if __name__ == "__main__":
    main()
