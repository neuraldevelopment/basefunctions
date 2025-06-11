"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich
  Project : basefunctions
  Copyright (c) by neuraldevelopment
  All rights reserved.
  Description:
  Demo for DataFrame database operations with OHLC data
 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import pandas as pd
import numpy as np
import datetime
import basefunctions

# -------------------------------------------------------------
# DEFINITIONS REGISTRY
# -------------------------------------------------------------

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------
INSTANCE_NAME = "dev_test_db_postgres"
DATABASE_NAME = "test"
TABLE_NAME = "ohlc_data"

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


def generate_ohlc_data(symbol: str = "AAPL", days: int = 100) -> pd.DataFrame:
    """
    Generate synthetic OHLC (Open, High, Low, Close) data.

    Parameters
    ----------
    symbol : str, optional
        Stock symbol, by default "AAPL"
    days : int, optional
        Number of trading days, by default 100

    Returns
    -------
    pd.DataFrame
        DataFrame with OHLC data
    """
    # Generate date range (business days only)
    end_date = datetime.datetime.now().date()
    start_date = end_date - datetime.timedelta(days=days * 1.5)  # Buffer for weekends

    date_range = pd.bdate_range(start=start_date, end=end_date)[:days]

    # Generate price data with random walk
    np.random.seed(42)  # For reproducible results

    # Starting price
    base_price = 150.0

    # Random daily returns (normal distribution)
    returns = np.random.normal(0.001, 0.02, days)  # 0.1% mean, 2% volatility

    # Calculate cumulative prices
    price_multipliers = np.cumprod(1 + returns)
    close_prices = base_price * price_multipliers

    # Generate OHLC from close prices
    ohlc_data = []

    for i, (date, close) in enumerate(zip(date_range, close_prices)):
        # Add some intraday volatility
        daily_vol = np.random.uniform(0.005, 0.025)  # 0.5% to 2.5% daily range

        # Generate open price (close to previous close)
        if i == 0:
            open_price = close * np.random.uniform(0.995, 1.005)
        else:
            open_price = close_prices[i - 1] * np.random.uniform(0.995, 1.005)

        # Generate high/low based on open and close
        high = max(open_price, close) * (1 + daily_vol)
        low = min(open_price, close) * (1 - daily_vol)

        # Volume (random but realistic)
        volume = int(np.random.uniform(1_000_000, 10_000_000))

        ohlc_data.append(
            {
                "date": date.strftime("%Y-%m-%d"),
                "symbol": symbol,
                "open": round(open_price, 2),
                "high": round(high, 2),
                "low": round(low, 2),
                "close": round(close, 2),
                "volume": volume,
            }
        )

    return pd.DataFrame(ohlc_data)


def ensure_database_exists(instance_name: str, database_name: str) -> bool:
    """
    Ensure target database exists, create if necessary.

    Parameters
    ----------
    instance_name : str
        Database instance name
    database_name : str
        Database name to create

    Returns
    -------
    bool
        True if database exists or was created successfully
    """
    try:
        # Get database instance
        manager = basefunctions.DbManager()
        instance = manager.get_instance(instance_name)

        # Check if database exists
        existing_databases = instance.list_databases()

        if database_name in existing_databases:
            print(f"✓ Database '{database_name}' already exists")
            return True

        # Create database
        print(f"Creating database '{database_name}'...")
        db = instance.add_database(database_name)
        print(f"✓ Database '{database_name}' created successfully")
        return True

    except Exception as e:
        print(f"✗ Failed to ensure database exists: {str(e)}")
        return False


def demo_dataframe_operations():
    """
    Demonstrate DataFrame database operations.
    """
    basefunctions.set_log_level("WARNING")
    print("=== DataFrame Database Demo ===\n")

    try:
        # Step 1: Ensure database exists
        print("1. Ensuring database exists...")
        if not ensure_database_exists(INSTANCE_NAME, DATABASE_NAME):
            print("✗ Failed to setup database, aborting demo")
            return
        print()

        # Step 2: Generate OHLC data
        print("2. Generating OHLC data...")
        ohlc_df = generate_ohlc_data("AAPL", 50)
        print(f"✓ Generated {len(ohlc_df)} rows of OHLC data")
        print(f"  Date range: {ohlc_df['date'].min()} to {ohlc_df['date'].max()}")
        print(f"  Price range: ${ohlc_df['low'].min():.2f} - ${ohlc_df['high'].max():.2f}")
        print()

        # Step 3: Initialize DataFrame database
        print("3. Initializing DataFrame database...")
        df_db = basefunctions.DataFrameDb(INSTANCE_NAME, DATABASE_NAME)
        print(f"✓ Connected to {INSTANCE_NAME}.{DATABASE_NAME}")
        print()

        # Step 4: Write DataFrame to database
        print("4. Writing DataFrame to database...")
        success = df_db.write(dataframe=ohlc_df, table_name=TABLE_NAME, if_exists="replace")  # Replace table if exists

        if success:
            print(f"✓ Successfully wrote {len(ohlc_df)} rows to table '{TABLE_NAME}'")
        else:
            print("✗ Failed to write DataFrame")
            return
        print()

        # Step 5: Read back DataFrame
        print("5. Reading DataFrame from database...")
        read_df = df_db.read(TABLE_NAME)
        print(f"✓ Successfully read {len(read_df)} rows from table '{TABLE_NAME}'")
        print()

        # Step 6: Verify data integrity
        print("6. Verifying data integrity...")

        # Check row count
        if len(read_df) == len(ohlc_df):
            print("✓ Row count matches")
        else:
            print(f"✗ Row count mismatch: expected {len(ohlc_df)}, got {len(read_df)}")

        # Check columns
        expected_cols = set(ohlc_df.columns)
        actual_cols = set(read_df.columns)
        if expected_cols.issubset(actual_cols):
            print("✓ All expected columns present")
        else:
            missing = expected_cols - actual_cols
            print(f"✗ Missing columns: {missing}")

        # Show sample data
        print("\nSample of written data:")
        print(read_df.head(3).to_string(index=False))
        print()

        # Step 7: Test query functionality
        print("7. Testing query functionality...")
        query_df = df_db.read(
            TABLE_NAME, query=f"SELECT * FROM {TABLE_NAME} WHERE close > 155.0 ORDER BY date DESC LIMIT 5"
        )
        print(f"✓ Query returned {len(query_df)} rows where close > $155.00")

        if len(query_df) > 0:
            print("Top 3 high-price days:")
            print(query_df[["date", "high", "close"]].head(3).to_string(index=False))
        print()

        # Step 8: Demonstrate cached version
        print("8. Testing cached DataFrame database...")
        cached_db = basefunctions.CachedDataFrameDb(INSTANCE_NAME, DATABASE_NAME, cache_ttl=300)  # 5 minutes

        # First read (cache miss)
        cached_df = cached_db.read(TABLE_NAME)
        print(f"✓ Cached read: {len(cached_df)} rows")

        # Second read (cache hit)
        cached_df2 = cached_db.read(TABLE_NAME)
        print(f"✓ Cached read (should be cache hit): {len(cached_df2)} rows")

        # Show cache stats
        stats = cached_db.get_cache_stats()
        print(f"Cache stats: {stats['cache']['hits']} hits, {stats['cache']['misses']} misses")
        print()

        print("=== Demo completed successfully! ===")

    except basefunctions.DataFrameDbError as e:
        print(f"✗ DataFrame database error: {str(e)}")
    except Exception as e:
        print(f"✗ Unexpected error: {str(e)}")


def demo_with_demo_runner():
    """
    Run demo using DemoRunner for formatted output.
    """
    runner = basefunctions.DemoRunner(log_level="WARNING")

    @runner.test("Database Setup")
    def test_database_setup():
        assert ensure_database_exists(INSTANCE_NAME, DATABASE_NAME)

    @runner.test("OHLC Data Generation")
    def test_data_generation():
        df = generate_ohlc_data("AAPL", 10)
        assert len(df) == 10
        assert list(df.columns) == ["date", "symbol", "open", "high", "low", "close", "volume"]

    @runner.test("DataFrame Write Operation")
    def test_write_operation():
        df = generate_ohlc_data("TEST", 5)
        df_db = basefunctions.DataFrameDb(INSTANCE_NAME, DATABASE_NAME)
        result = df_db.write(df, "test_ohlc", if_exists="replace")
        assert result == True

    @runner.test("DataFrame Read Operation")
    def test_read_operation():
        df_db = basefunctions.DataFrameDb(INSTANCE_NAME, DATABASE_NAME)
        df = df_db.read("test_ohlc")
        assert len(df) == 5
        assert "symbol" in df.columns

    @runner.test("Cached DataFrame Operations")
    def test_cached_operations():
        cached_db = basefunctions.CachedDataFrameDb(INSTANCE_NAME, DATABASE_NAME)
        df = cached_db.read("test_ohlc")
        assert len(df) > 0

        stats = cached_db.get_cache_stats()
        assert "cache" in stats

    # Run all tests
    runner.run_all_tests()
    runner.print_results("DataFrame Database Demo Results")


if __name__ == "__main__":
    print("Choose demo mode:")
    print("1. Interactive demo")
    print("2. Test suite with DemoRunner")

    choice = input("Enter choice (1 or 2): ").strip()

    if choice == "2":
        demo_with_demo_runner()
    else:
        demo_dataframe_operations()
