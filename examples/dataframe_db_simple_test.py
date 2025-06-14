"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich
  Project : basefunctions
  Copyright (c) by neuraldevelopment
  All rights reserved.
  Description:
  Test suite for DataFrameDb with OHLCV data generation and PostgreSQL integration
 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
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
DB_INSTANCE_NAME = "dev_test_postgres"
DB_NAME = "test_database"
TEST_TABLE_NAME = "ohlcv_test"

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


def test_ohlcv_generation():
    """
    Test OHLCV data generation with fixed seed for reproducible results.

    Returns
    -------
    bool
        True if generation successful and data structure valid

    Raises
    ------
    Exception
        If generation fails or data structure invalid
    """
    generator = basefunctions.OHLCVGenerator(seed=42)
    df = generator.generate(
        ticker="TEST.XETRA", start_date="2024-01-01", end_date="2024-01-31", initial_price=150.0, volatility=0.025
    )

    # Validate DataFrame structure - raise exceptions on failure
    expected_columns = {"Open", "High", "Low", "Close", "Volume", "Ticker"}
    if not expected_columns.issubset(df.columns):
        raise Exception(f"Missing columns. Expected: {expected_columns}, Got: {set(df.columns)}")

    if len(df) == 0:
        raise Exception("Generated DataFrame is empty")

    if df.index.name != "Date":
        raise Exception(f"Expected index name 'Date', got '{df.index.name}'")

    return True


def test_dataframe_write():
    """
    Test writing DataFrame to PostgreSQL database via DataFrameDb.

    Returns
    -------
    bool
        True if write operation successful

    Raises
    ------
    Exception
        If write operation fails
    """
    # Generate test data
    generator = basefunctions.OHLCVGenerator(seed=42)
    df = generator.generate(
        ticker="AAPL.XETRA", start_date="2024-01-01", end_date="2024-01-31", initial_price=180.0, volatility=0.02
    )

    # Write to database
    df_db = basefunctions.DataFrameDb(DB_INSTANCE_NAME, DB_NAME)
    success = df_db.write(df, TEST_TABLE_NAME, if_exists="replace", index=True)

    if not success:
        raise Exception("DataFrame write operation returned False")

    return True


def test_dataframe_read():
    """
    Test reading DataFrame from PostgreSQL database via DataFrameDb.

    Returns
    -------
    bool
        True if read operation successful and data valid

    Raises
    ------
    Exception
        If read operation fails or data invalid
    """
    df_db = basefunctions.DataFrameDb(DB_INSTANCE_NAME, DB_NAME)
    df = df_db.read(TEST_TABLE_NAME)

    # Validate read data
    required_columns = ["Open", "High", "Low", "Close", "Volume", "Ticker"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise Exception(f"Missing required columns: {missing_columns}")

    if len(df) == 0:
        raise Exception("Read DataFrame is empty")

    if "AAPL.XETRA" not in df["Ticker"].values:
        raise Exception("Expected AAPL.XETRA ticker not found in data")

    return True


def test_dataframe_read_with_query():
    """
    Test reading DataFrame with custom SQL query.

    Returns
    -------
    bool
        True if query execution successful

    Raises
    ------
    Exception
        If query execution fails
    """
    df_db = basefunctions.DataFrameDb(DB_INSTANCE_NAME, DB_NAME)

    # Read with custom query - high volume days
    df = df_db.read(
        TEST_TABLE_NAME, query=f'SELECT * FROM {TEST_TABLE_NAME} WHERE "Volume" > ? ORDER BY "Date"', params=[1000000]
    )

    # Validate filtered data - may be empty but should not fail
    if len(df) > 0:
        # If we have data, all volumes should be > 1000000
        low_volume_rows = df[df["Volume"] <= 1000000]
        if len(low_volume_rows) > 0:
            raise Exception(f"Query filter failed: found {len(low_volume_rows)} rows with Volume <= 1000000")

    return True


def test_dataframe_delete():
    """
    Test deleting data from PostgreSQL database via DataFrameDb.

    Returns
    -------
    bool
        True if delete operation successful

    Raises
    ------
    Exception
        If delete operation fails
    """
    df_db = basefunctions.DataFrameDb(DB_INSTANCE_NAME, DB_NAME)

    # Delete high volume records
    success = df_db.delete(TEST_TABLE_NAME, where_clause='"Volume" > ?', params=[1500000])

    if not success:
        raise Exception("DataFrame delete operation returned False")

    return True


def test_multiple_ticker_operations():
    """
    Test operations with multiple tickers in same table.

    Returns
    -------
    bool
        True if multi-ticker operations successful

    Raises
    ------
    Exception
        If multi-ticker operations fail
    """
    # Generate data for multiple tickers
    generator = basefunctions.OHLCVGenerator(seed=123)

    # Generate and append different tickers
    tickers = ["MSFT.XETRA", "GOOGL.XETRA"]
    df_db = basefunctions.DataFrameDb(DB_INSTANCE_NAME, DB_NAME)

    for ticker in tickers:
        df = generator.generate(ticker=ticker, start_date="2024-02-01", end_date="2024-02-15", initial_price=200.0)

        # Append to existing table
        success = df_db.write(df, TEST_TABLE_NAME, if_exists="append", index=True)
        if not success:
            raise Exception(f"Failed to write data for ticker {ticker}")

    # Read back and verify multiple tickers
    df_combined = df_db.read(TEST_TABLE_NAME)
    unique_tickers = df_combined["Ticker"].unique()

    if len(unique_tickers) < 3:  # Should have AAPL + MSFT + GOOGL
        raise Exception(f"Expected at least 3 tickers, found: {list(unique_tickers)}")

    return True


def test_database_setup():
    """
    Test database existence and create if necessary.

    Returns
    -------
    bool
        True if database exists or was created successfully

    Raises
    ------
    Exception
        If database setup fails
    """
    # Get database instance - let exceptions bubble up
    manager = basefunctions.DbManager()
    instance = manager.get_instance(DB_INSTANCE_NAME)
    print("1")
    # List existing databases - let exceptions bubble up
    existing_databases = instance.list_databases()
    print("2")
    if DB_NAME in existing_databases:
        return True
    print("3")
    # Create database if it doesn't exist - let exceptions bubble up
    instance.add_database(DB_NAME)
    print("4")
    # Verify database was created
    updated_databases = instance.list_databases()
    if DB_NAME not in updated_databases:
        raise Exception(f"Database '{DB_NAME}' was not created successfully")

    return True


def main():
    """
    Main function to run all DataFrame database tests using DemoRunner.
    """
    # Disable logging for cleaner test output
    basefunctions.DemoRunner.disable_global_logging()

    # Initialize test runner
    runner = basefunctions.DemoRunner()

    # Run all tests
    runner.run_test("Database Setup", test_database_setup)
    runner.run_test("OHLCV Generation", test_ohlcv_generation)
    runner.run_test("DataFrame Write", test_dataframe_write)
    runner.run_test("DataFrame Read", test_dataframe_read)
    runner.run_test("DataFrame Query Read", test_dataframe_read_with_query)
    runner.run_test("DataFrame Delete", test_dataframe_delete)
    runner.run_test("Multi-Ticker Operations", test_multiple_ticker_operations)

    # Display results
    runner.print_results()


if __name__ == "__main__":
    main()
