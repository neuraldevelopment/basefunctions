"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich
  Project : database_load_generator
  Copyright (c) by neuraldevelopment
  All rights reserved.
  Description:
  Database load generator for performance testing with OHLCV data
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
from tabulate import tabulate
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

DEFAULT_START_DATE = "2023-01-01"
DEFAULT_NUM_TABLES = 5
DEFAULT_TABLE_PREFIX = "test"


# -------------------------------------------------------------
# DATA GENERATION
# -------------------------------------------------------------
def generate_ohlcv_data(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Generate realistic OHLCV data for a given symbol and date range."""
    # Create date range
    dates = pd.date_range(start=start_date, end=end_date, freq="D")
    dates = dates[dates.weekday < 5]  # Remove weekends

    num_days = len(dates)
    if num_days == 0:
        return pd.DataFrame(columns=["symbol", "date", "open", "high", "low", "close", "volume"])

    # Generate realistic price data using random walk
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
# LOAD GENERATOR
# -------------------------------------------------------------
class SimpleLoadGenerator:
    """Simplified load generator - ONLY uses write_dataframe."""

    def __init__(self, instance_name: str, start_date: str, num_tables: int, table_prefix: str):
        self.instance_name = instance_name
        self.start_date = start_date
        self.num_tables = num_tables
        self.table_prefix = table_prefix

        # Initialize database
        self.db_manager = basefunctions.DbManager()
        instance = self.db_manager.get_instance(instance_name)

        # Create unique database
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.db_name = f"loadtest_{timestamp}"

        try:
            # Try to create separate test database
            main_db = instance.get_database(instance_name)
            main_db.execute(f"CREATE DATABASE {self.db_name}")
            main_db.close()
            self.db = instance.get_database(self.db_name)
        except:
            # Fallback to main database with prefix
            self.db_name = instance_name
            self.db = instance.get_database(instance_name)
            self.table_prefix = f"{table_prefix}_{timestamp}_"

    def create_table(self, table_name: str):
        """Create a single table."""
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
        self.db.execute(sql)

    def run_test(self, cached: bool) -> Dict[str, Any]:
        """Run test with specified caching strategy."""
        strategy = "cached" if cached else "direct"
        end_date = datetime.now().strftime("%Y-%m-%d")

        start_time = time.time()
        total_rows = 0

        # Create tables
        table_start = time.time()
        for table_num in range(1, self.num_tables + 1):
            table_name = f"{self.table_prefix}{table_num:03d}".lower()
            self.create_table(table_name)
        table_time = time.time() - table_start

        # Write data
        write_start = time.time()
        for table_num in range(1, self.num_tables + 1):
            table_name = f"{self.table_prefix}{table_num:03d}".lower()

            for symbol in DAX_SYMBOLS:
                df = generate_ohlcv_data(symbol, self.start_date, end_date)

                if len(df) > 0:
                    # ✅ ONLY write_dataframe - DB handles everything else
                    self.db.write_dataframe(
                        table_name=table_name,
                        df=df,
                        cached=cached,  # ONLY difference between tests
                        if_exists="append",  # Always append
                    )
                    total_rows += len(df)

        write_time = time.time() - write_start

        # Flush caches if cached
        flush_start = time.time()
        if cached:
            self.db.flush_cache()  # Flush all caches
        flush_time = time.time() - flush_start

        total_time = time.time() - start_time

        return {
            "strategy": strategy,
            "database_name": self.db_name,
            "total_time": total_time,
            "table_time": table_time,
            "write_time": write_time,
            "flush_time": flush_time,
            "total_rows": total_rows,
            "rows_per_second": total_rows / total_time if total_time > 0 else 0,
            "tables_created": self.num_tables,
            "dataframes_written": self.num_tables * len(DAX_SYMBOLS),
            "config": {
                "start_date": self.start_date,
                "num_tables": self.num_tables,
                "table_prefix": self.table_prefix,
                "symbols": len(DAX_SYMBOLS),
            },
        }

    def cleanup(self):
        """Clean up resources."""
        try:
            if self.db:
                self.db.close()
            if self.db_manager:
                self.db_manager.close_all()
        except:
            pass


# -------------------------------------------------------------
# RESULTS WITH TABULATE
# -------------------------------------------------------------
def print_results(cached_results: Dict[str, Any], direct_results: Dict[str, Any]):
    """Print results using tabulate."""

    print("\n" + "=" * 60)
    print("DATABASE LOAD TEST RESULTS")
    print("=" * 60)

    # Configuration
    config = cached_results["config"]
    config_data = [
        ["Start Date", config["start_date"]],
        ["Tables", f"{config['num_tables']:,}"],
        ["Symbols", f"{config['symbols']:,}"],
        ["Table Prefix", config["table_prefix"]],
    ]

    print("\nCONFIGURATION:")
    print(tabulate(config_data, headers=["Parameter", "Value"], tablefmt="grid"))

    # Performance comparison
    performance_data = [
        [
            "Cached",
            f"{cached_results['total_time']:.1f}s",
            f"{cached_results['total_rows']:,}",
            f"{cached_results['rows_per_second']:,.0f}",
            f"{cached_results['write_time']:.1f}s",
            f"{cached_results['flush_time']:.1f}s",
        ],
        [
            "Direct",
            f"{direct_results['total_time']:.1f}s",
            f"{direct_results['total_rows']:,}",
            f"{direct_results['rows_per_second']:,.0f}",
            f"{direct_results['write_time']:.1f}s",
            f"{direct_results['flush_time']:.1f}s",
        ],
    ]

    print("\nPERFORMANCE COMPARISON:")
    print(
        tabulate(
            performance_data,
            headers=["Strategy", "Total Time", "Rows", "Rows/sec", "Write Time", "Flush Time"],
            tablefmt="grid",
        )
    )

    # Performance gains
    if cached_results["total_time"] > 0 and direct_results["total_time"] > 0:
        speed_gain = direct_results["total_time"] / cached_results["total_time"]
        throughput_gain = cached_results["rows_per_second"] / direct_results["rows_per_second"]
        time_saved = direct_results["total_time"] - cached_results["total_time"]

        gain_data = [
            ["Speed Improvement", f"{speed_gain:.1f}x faster"],
            ["Throughput Improvement", f"{throughput_gain:.1f}x higher"],
            ["Time Saved", f"{time_saved:.1f}s"],
        ]

        print("\nPERFORMANCE GAINS:")
        print(tabulate(gain_data, headers=["Metric", "Cached vs Direct"], tablefmt="grid"))

    # Database info
    db_data = [
        ["Cached Test DB", cached_results["database_name"]],
        ["Direct Test DB", direct_results["database_name"]],
    ]
    print("\nDATABASE INFORMATION:")
    print(tabulate(db_data, headers=["Test", "Database Name"], tablefmt="grid"))


# -------------------------------------------------------------
# COMMAND LINE INTERFACE
# -------------------------------------------------------------
def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Simple Database Load Generator")

    parser.add_argument(
        "instance_name", nargs="?", default="dev_test_db_postgres", help="Database instance name"
    )

    parser.add_argument(
        "--tables",
        type=int,
        default=DEFAULT_NUM_TABLES,
        help=f"Number of tables (default: {DEFAULT_NUM_TABLES})",
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

    parser.add_argument("--cached-only", action="store_true", help="Run only cached test")

    parser.add_argument("--direct-only", action="store_true", help="Run only direct test")

    parser.add_argument("--quiet", action="store_true", help="Disable logging")

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
    args = parse_arguments()

    # Configure logging
    if args.quiet:
        logging.disable(logging.CRITICAL)
    else:
        logging.getLogger().setLevel(logging.WARNING)

    # Validate date
    if not validate_date_format(args.start_date):
        return

    cached_results = None
    direct_results = None

    try:
        # Run cached test
        if not args.direct_only:
            print("Running cached test...")
            generator = SimpleLoadGenerator(
                args.instance_name, args.start_date, args.tables, args.table_prefix
            )
            cached_results = generator.run_test(cached=True)  # ✅ CACHED
            generator.cleanup()

        # Run direct test
        if not args.cached_only:
            print("Running direct test...")
            generator = SimpleLoadGenerator(
                args.instance_name, args.start_date, args.tables, args.table_prefix
            )
            direct_results = generator.run_test(cached=False)  # ✅ DIRECT
            generator.cleanup()

        # Print results
        if cached_results and direct_results:
            print_results(cached_results, direct_results)
        elif cached_results:
            result_data = [
                [
                    "Cached",
                    f"{cached_results['total_time']:.1f}s",
                    f"{cached_results['total_rows']:,}",
                    f"{cached_results['rows_per_second']:,.0f}",
                ]
            ]
            print("\nCACHED TEST RESULTS:")
            print(
                tabulate(
                    result_data, headers=["Strategy", "Time", "Rows", "Rows/sec"], tablefmt="grid"
                )
            )
        elif direct_results:
            result_data = [
                [
                    "Direct",
                    f"{direct_results['total_time']:.1f}s",
                    f"{direct_results['total_rows']:,}",
                    f"{direct_results['rows_per_second']:,.0f}",
                ]
            ]
            print("\nDIRECT TEST RESULTS:")
            print(
                tabulate(
                    result_data, headers=["Strategy", "Time", "Rows", "Rows/sec"], tablefmt="grid"
                )
            )

    except KeyboardInterrupt:
        print("\nTest interrupted")
    except Exception as e:
        print(f"\nTest failed: {str(e)}")
        import traceback

        traceback.print_exc()

    print("\nTest completed")


if __name__ == "__main__":
    main()
