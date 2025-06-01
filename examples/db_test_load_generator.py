"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich
  Project : database_load_generator
  Copyright (c) by neuraldevelopment
  All rights reserved.
  Description:
  Database load generator for performance testing with OHLCV data using DemoRunner
 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import argparse
import time
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any
import logging
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

DEFAULT_START_DATE = "2013-01-01"
DEFAULT_NUM_TABLES = 20
DEFAULT_TABLE_PREFIX = "loadtest"

# -------------------------------------------------------------
# SETUP
# -------------------------------------------------------------
basefunctions.DemoRunner.init_logging()

# Global variables for test functions
database = None
args = None
test_config = None
test_results = {}


# -------------------------------------------------------------
# DATA GENERATION
# -------------------------------------------------------------
def generate_ohlcv_data(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Generate realistic OHLCV data for a given symbol and date range."""
    dates = pd.date_range(start=start_date, end=end_date, freq="D")
    dates = dates[dates.weekday < 5]  # Remove weekends

    num_days = len(dates)
    if num_days == 0:
        return pd.DataFrame(columns=["symbol", "date", "open", "high", "low", "close", "volume"])

    # Generate realistic price data
    np.random.seed(hash(symbol) % 2**32)
    start_price = np.random.uniform(20, 200)
    daily_returns = np.random.normal(0.0005, 0.02, num_days)
    close_prices = start_price * np.cumprod(1 + daily_returns)

    # Generate OHLC
    open_prices = np.zeros(num_days)
    high_prices = np.zeros(num_days)
    low_prices = np.zeros(num_days)

    open_prices[0] = start_price
    for i in range(1, num_days):
        gap = np.random.normal(0, 0.005)
        open_prices[i] = close_prices[i - 1] * (1 + gap)

    for i in range(num_days):
        intraday_volatility = np.random.uniform(0.01, 0.05)
        base_high = max(open_prices[i], close_prices[i])
        high_prices[i] = base_high * (1 + np.random.uniform(0, intraday_volatility))
        base_low = min(open_prices[i], close_prices[i])
        low_prices[i] = base_low * (1 - np.random.uniform(0, intraday_volatility))

    # Generate volume
    volumes = np.random.lognormal(mean=13, sigma=1, size=num_days).astype(int)

    return pd.DataFrame(
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


# -------------------------------------------------------------
# TEST FUNCTIONS
# -------------------------------------------------------------
def test_eventbus_writes():
    """Test EventBus async DataFrame writes."""
    global database, test_config, test_results

    start_time = time.time()
    total_rows = 0
    end_date = datetime.now().strftime("%Y-%m-%d")

    # Calculate total operations for progress bar
    total_operations = test_config["num_tables"] * len(DAX_SYMBOLS[:10])
    current_operation = 0

    print(f"    Starting EventBus writes ({total_operations} operations)...")

    # Submit all writes via EventBus
    for table_num in range(1, test_config["num_tables"] + 1):
        table_name = f"{test_config['table_prefix']}{table_num:03d}".lower()

        for symbol in DAX_SYMBOLS[:10]:  # Limit symbols for faster testing
            df = generate_ohlcv_data(symbol, test_config["start_date"], end_date)

            if len(df) > 0:
                database.submit_dataframe_write(table_name, df, "append")
                total_rows += len(df)

            # Update progress
            current_operation += 1
            progress = (current_operation / total_operations) * 100
            bar_length = 30
            filled_length = int(bar_length * current_operation // total_operations)
            bar = "█" * filled_length + "░" * (bar_length - filled_length)
            print(
                f"\r    Progress: [{bar}] {progress:.1f}% ({current_operation}/{total_operations})", end="", flush=True
            )

    print()  # New line after progress bar
    print("    Waiting for EventBus results...")

    # Get results
    results = database.get_dataframe_write_results()
    if not results:
        raise Exception("No EventBus write results returned")

    elapsed_time = time.time() - start_time
    test_results["eventbus"] = {
        "time": elapsed_time,
        "rows": total_rows,
        "rows_per_sec": total_rows / elapsed_time if elapsed_time > 0 else 0,
    }

    print(f"    Completed: {total_rows:,} rows in {elapsed_time:.1f}s")


def test_direct_writes():
    """Test direct sync DataFrame writes."""
    global database, test_config, test_results

    start_time = time.time()
    total_rows = 0
    end_date = datetime.now().strftime("%Y-%m-%d")

    # Calculate total operations for progress bar
    total_operations = test_config["num_tables"] * len(DAX_SYMBOLS[:10])
    current_operation = 0

    print(f"    Starting direct writes ({total_operations} operations)...")

    # Clear existing data from tables to avoid unique constraint violations
    print("    Clearing existing data from tables...")
    for table_num in range(1, test_config["num_tables"] + 1):
        table_name = f"{test_config['table_prefix']}{table_num:03d}".lower()
        try:
            database.execute(f"DELETE FROM {table_name}")
        except Exception as e:
            print(f"    Warning: Could not clear table {table_name}: {e}")

    # Direct writes via connector
    connection = database.connector.get_connection()

    for table_num in range(1, test_config["num_tables"] + 1):
        table_name = f"{test_config['table_prefix']}{table_num:03d}".lower()

        for symbol in DAX_SYMBOLS[:10]:  # Limit symbols for faster testing
            df = generate_ohlcv_data(symbol, test_config["start_date"], end_date)

            if len(df) > 0:
                df.to_sql(table_name, connection, if_exists="append", index=False)
                total_rows += len(df)

            # Update progress
            current_operation += 1
            progress = (current_operation / total_operations) * 100
            bar_length = 30
            filled_length = int(bar_length * current_operation // total_operations)
            bar = "█" * filled_length + "░" * (bar_length - filled_length)
            print(
                f"\r    Progress: [{bar}] {progress:.1f}% ({current_operation}/{total_operations})", end="", flush=True
            )

    print()  # New line after progress bar

    elapsed_time = time.time() - start_time
    test_results["direct"] = {
        "time": elapsed_time,
        "rows": total_rows,
        "rows_per_sec": total_rows / elapsed_time if elapsed_time > 0 else 0,
    }

    print(f"    Completed: {total_rows:,} rows in {elapsed_time:.1f}s")


def test_setup():
    """Setup test environment and create tables."""
    global database, test_config

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    table_prefix = f"{test_config['table_prefix']}_{timestamp}_"

    print(f"    Creating {test_config['num_tables']} tables...")

    # Create tables with progress
    for table_num in range(1, test_config["num_tables"] + 1):
        table_name = f"{table_prefix}{table_num:03d}".lower()

        sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
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
        """
        database.execute(sql)

        # Simple progress indicator
        progress = (table_num / test_config["num_tables"]) * 100
        bar_length = 20
        filled_length = int(bar_length * table_num // test_config["num_tables"])
        bar = "█" * filled_length + "░" * (bar_length - filled_length)
        print(f"\r    Progress: [{bar}] {progress:.0f}% ({table_num}/{test_config['num_tables']})", end="", flush=True)

    print()  # New line after progress bar
    test_config["table_prefix"] = table_prefix
    print(f"    Tables created with prefix: {table_prefix}")


def test_verify_data():
    """Verify that data was written correctly."""
    global database, test_config

    print(f"    Verifying data in {test_config['num_tables']} tables...")

    total_count = 0

    for table_num in range(1, test_config["num_tables"] + 1):
        table_name = f"{test_config['table_prefix']}{table_num:03d}".lower()

        result = database.query_one(f"SELECT COUNT(*) as count FROM {table_name}")
        if not result:
            raise Exception(f"Could not count rows in table {table_name}")

        total_count += result["count"]

        # Progress indicator
        progress = (table_num / test_config["num_tables"]) * 100
        bar_length = 20
        filled_length = int(bar_length * table_num // test_config["num_tables"])
        bar = "█" * filled_length + "░" * (bar_length - filled_length)
        print(f"\r    Progress: [{bar}] {progress:.0f}% ({table_num}/{test_config['num_tables']})", end="", flush=True)

    print()  # New line after progress bar

    if total_count == 0:
        raise Exception("No data found in any table")

    print(f"    Verified: {total_count:,} total rows across all tables")


def test_cleanup():
    """Clean up test tables and databases."""
    global database, test_config

    print(f"    Cleaning up {test_config['num_tables']} tables...")

    # First, drop all test tables
    for table_num in range(1, test_config["num_tables"] + 1):
        table_name = f"{test_config['table_prefix']}{table_num:03d}".lower()
        try:
            database.execute(f"DROP TABLE IF EXISTS {table_name}")
        except Exception as e:
            print(f"Warning: Could not drop table {table_name}: {e}")

        # Progress indicator
        progress = (table_num / test_config["num_tables"]) * 100
        bar_length = 20
        filled_length = int(bar_length * table_num // test_config["num_tables"])
        bar = "█" * filled_length + "░" * (bar_length - filled_length)
        print(f"\r    Progress: [{bar}] {progress:.0f}% ({table_num}/{test_config['num_tables']})", end="", flush=True)

    print()  # New line after progress bar
    print("    Tables cleanup completed")


def test_final_cleanup():
    """Final cleanup - remove any remaining test artifacts."""
    global database, test_config

    print("    Performing final cleanup...")

    try:
        # Get database type for cleanup strategy
        db_type = None
        config_handler = basefunctions.ConfigHandler()
        config = config_handler.get_database_config(args.instance_name)
        if config:
            db_type = config.get("type")

        # Clean up any remaining test tables with our prefix pattern
        cleanup_patterns = [
            f"{DEFAULT_TABLE_PREFIX}_%",  # Our standard pattern
            "loadtest_%",  # Alternative pattern
        ]

        tables_dropped = 0

        for pattern in cleanup_patterns:
            try:
                if db_type in ["postgres", "postgresql"]:
                    # PostgreSQL: Find tables matching pattern
                    query = """
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name LIKE %s
                    """
                    result = database.query_all(query, (pattern,))

                elif db_type == "mysql":
                    # MySQL: Find tables matching pattern
                    query = f"SHOW TABLES LIKE '{pattern}'"
                    result = database.query_all(query)

                elif db_type == "sqlite3":
                    # SQLite: Find tables matching pattern
                    query = "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE ?"
                    result = database.query_all(query, (pattern,))

                else:
                    print(f"    Unknown database type '{db_type}', skipping pattern cleanup")
                    continue

                # Drop found tables
                for row in result:
                    if db_type in ["postgres", "postgresql"]:
                        table_name = row.get("table_name")
                    elif db_type == "mysql":
                        # MySQL SHOW TABLES returns different column names
                        table_name = list(row.values())[0] if row else None
                    elif db_type == "sqlite3":
                        table_name = row.get("name")

                    if table_name:
                        try:
                            database.execute(f"DROP TABLE IF EXISTS {table_name}")
                            tables_dropped += 1
                            print(f"    Dropped orphaned table: {table_name}")
                        except Exception as e:
                            print(f"    Warning: Could not drop table {table_name}: {e}")

            except Exception as e:
                print(f"    Warning: Error during pattern cleanup for '{pattern}': {e}")

        if tables_dropped > 0:
            print(f"    Final cleanup: Dropped {tables_dropped} orphaned test tables")
        else:
            print("    Final cleanup: No orphaned test tables found")

        # Additional cleanup for PostgreSQL: drop any test databases if we created them
        if db_type in ["postgres", "postgresql"]:
            try:
                # Look for test databases with our naming pattern
                query = """
                SELECT datname FROM pg_database 
                WHERE datname LIKE 'loadtest_%' AND datname != current_database()
                """
                result = database.query_all(query)

                for row in result:
                    db_name = row.get("datname")
                    if db_name:
                        try:
                            # Terminate connections to the database first
                            database.execute(
                                f"""
                                SELECT pg_terminate_backend(pid) 
                                FROM pg_stat_activity 
                                WHERE datname = '{db_name}' AND pid <> pg_backend_pid()
                            """
                            )
                            # Drop the database
                            database.execute(f"DROP DATABASE IF EXISTS {db_name}")
                            print(f"    Dropped test database: {db_name}")
                        except Exception as e:
                            print(f"    Warning: Could not drop database {db_name}: {e}")

            except Exception as e:
                print(f"    Note: Could not check for test databases: {e}")

    except Exception as e:
        print(f"    Warning: Error during final cleanup: {e}")

    print("    Final cleanup completed")


# -------------------------------------------------------------
# COMMAND LINE INTERFACE
# -------------------------------------------------------------
def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Database Load Generator with DemoRunner")

    parser.add_argument("instance_name", nargs="?", default="dev_test_db_postgres", help="Database instance name")

    parser.add_argument(
        "--tables", type=int, default=DEFAULT_NUM_TABLES, help=f"Number of tables (default: {DEFAULT_NUM_TABLES})"
    )

    parser.add_argument(
        "--start-date",
        type=str,
        default=DEFAULT_START_DATE,
        help=f"Start date YYYY-MM-DD (default: {DEFAULT_START_DATE})",
    )

    parser.add_argument(
        "--table-prefix",
        type=str,
        default=DEFAULT_TABLE_PREFIX,
        help=f"Table prefix (default: {DEFAULT_TABLE_PREFIX})",
    )

    parser.add_argument("--setup-only", action="store_true", help="Only run setup test")
    parser.add_argument("--eventbus-only", action="store_true", help="Only run EventBus test")
    parser.add_argument("--direct-only", action="store_true", help="Only run direct test")
    parser.add_argument("--no-cleanup", action="store_true", help="Skip cleanup")

    return parser.parse_args()


def validate_date_format(date_string: str) -> bool:
    """Validate date format."""
    try:
        date_obj = datetime.strptime(date_string, "%Y-%m-%d")
        if date_obj > datetime.now():
            print(f"Error: Start date {date_string} is in the future")
            return False
        if date_obj.year < 1900:
            print(f"Error: Start date {date_string} is too far in the past")
            return False
        return True
    except ValueError:
        print(f"Error: Invalid date format '{date_string}'. Use YYYY-MM-DD format.")
        return False


# -------------------------------------------------------------
# MAIN FUNCTION
# -------------------------------------------------------------
def main():
    """Main function."""
    global args, database, test_config, test_results
    args = parse_arguments()

    # Validate date
    if not validate_date_format(args.start_date):
        return 1

    # Setup test configuration
    test_config = {
        "start_date": args.start_date,
        "num_tables": args.tables,
        "table_prefix": args.table_prefix,
        "symbols": len(DAX_SYMBOLS[:10]),  # Limited for testing
    }

    try:
        # Load configuration and setup database
        config_handler = basefunctions.ConfigHandler()
        config_handler.load_default_config("basefunctions")

        # Create database directly
        database = basefunctions.Db(args.instance_name)

        # Setup demo runner
        demo = basefunctions.DemoRunner(max_width=150)

        # Register tests based on arguments
        demo.test("Setup Tables")(test_setup)

        if not args.direct_only:
            demo.test("EventBus DataFrame Writes")(test_eventbus_writes)

        if not args.eventbus_only:
            demo.test("Direct DataFrame Writes")(test_direct_writes)

        if not args.setup_only:
            demo.test("Verify Data")(test_verify_data)

        if not args.no_cleanup:
            demo.test("Cleanup Tables")(test_cleanup)
            demo.test("Final Cleanup")(test_final_cleanup)

        # Run all tests
        demo.run_all_tests()

        # Display results
        demo.print_results(f"Database Load Test Results - {args.instance_name}")

        # Create and display performance summary table using new method
        if "eventbus" in test_results or "direct" in test_results:
            print(f"\n{'='*80}")
            print("PERFORMANCE SUMMARY")
            print(f"{'='*80}")

            # Prepare performance data as list of tuples
            performance_data = []

            if "eventbus" in test_results and "direct" in test_results:
                # Both tests ran - show comparison
                eb_result = test_results["eventbus"]
                direct_result = test_results["direct"]

                # Add individual results
                performance_data.append(("EventBus Time", f"{eb_result['time']:.1f}s"))
                performance_data.append(("EventBus Rows", f"{eb_result['rows']:,}"))
                performance_data.append(("EventBus Throughput", f"{eb_result['rows_per_sec']:,.0f} rows/sec"))
                performance_data.append(("Direct Time", f"{direct_result['time']:.1f}s"))
                performance_data.append(("Direct Rows", f"{direct_result['rows']:,}"))
                performance_data.append(("Direct Throughput", f"{direct_result['rows_per_sec']:,.0f} rows/sec"))

                # Calculate and add performance gains
                if direct_result["time"] > 0 and eb_result["time"] > 0:
                    speedup = direct_result["time"] / eb_result["time"]
                    throughput_gain = eb_result["rows_per_sec"] / direct_result["rows_per_sec"]
                    time_saved = direct_result["time"] - eb_result["time"]

                    performance_data.append(("Speed Improvement", f"{speedup:.1f}x faster"))
                    performance_data.append(("Throughput Improvement", f"{throughput_gain:.1f}x higher"))
                    performance_data.append(("Time Saved", f"{time_saved:.1f}s"))

            elif "eventbus" in test_results:
                # Only EventBus test ran
                eb_result = test_results["eventbus"]
                performance_data.append(("EventBus Time", f"{eb_result['time']:.1f}s"))
                performance_data.append(("EventBus Rows", f"{eb_result['rows']:,}"))
                performance_data.append(("EventBus Throughput", f"{eb_result['rows_per_sec']:,.0f} rows/sec"))

            elif "direct" in test_results:
                # Only Direct test ran
                direct_result = test_results["direct"]
                performance_data.append(("Direct Time", f"{direct_result['time']:.1f}s"))
                performance_data.append(("Direct Rows", f"{direct_result['rows']:,}"))
                performance_data.append(("Direct Throughput", f"{direct_result['rows_per_sec']:,.0f} rows/sec"))

            # Add configuration info
            performance_data.append(("Tables Created", f"{test_config['num_tables']}"))
            performance_data.append(("Symbols Processed", f"{test_config['symbols']}"))
            performance_data.append(("Date Range", f"From {test_config['start_date']}"))

            # Print the performance table using new method
            demo.print_performance_table(performance_data, "Performance Analysis")

        return 1 if demo.has_failures() else 0

    except Exception as e:
        print(f"\nTest failed: {str(e)}")
        import traceback

        traceback.print_exc()
        return 1

    finally:
        # Always close connections
        try:
            if database:
                database.close()
        except Exception as e:
            print(f"Warning: Error closing connection: {e}")


if __name__ == "__main__":
    exit(main())
