"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich
  Project : basefunctions
  Copyright (c) by neuraldevelopment
  All rights reserved.
  Description:
  Bulk test for DataFrameDb with 50 OHLCV DataFrames - write, read, validate
 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import time
import pandas as pd
import basefunctions

# -------------------------------------------------------------
# DEFINITIONS REGISTRY
# -------------------------------------------------------------

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------
DB_INSTANCE_NAME = "dev_test_postgres"
DB_NAME = "dev_test_postgres"
BULK_TABLE_NAME = "dataframe_db_load_test"
NUM_DATAFRAMES = 1000

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


def generate_test_dataframes():
    """
    Generate 1000 OHLCV DataFrames with different tickers and seeds.

    Returns
    -------
    dict
        Dictionary mapping ticker to DataFrame
    """
    dataframes = {}

    for i in range(1, NUM_DATAFRAMES + 1):
        try:
            # Each DataFrame gets its own generator with unique seed
            generator = basefunctions.OHLCVGenerator(seed=42 + i)
            ticker = f"TEST_{i:02d}.XETRA"

            df = generator.generate(
                ticker=ticker,
                start_date="2024-01-01",
                end_date="2024-12-31",  # Full year
                initial_price=max(50.0, 100.0 + i),  # Ensure minimum price > 0
                volatility=min(0.05, 0.02 + (i * 0.0001)),  # Cap volatility
            )
            dataframes[ticker] = df
        except Exception as e:
            print(f"Error generating OHLCV data for {ticker}: {str(e)}")
            # Skip problematic DataFrames
            continue

    return dataframes


def write_all_dataframes(df_db, original_dfs):
    """
    Write all DataFrames to database table using parallel operations.

    Parameters
    ----------
    df_db : basefunctions.DataFrameDb
        Database connection
    original_dfs : dict
        Dictionary of DataFrames to write

    Returns
    -------
    bool
        True if all writes successful

    Raises
    ------
    Exception
        If any write operation fails
    """
    # Create table with first DataFrame
    first_ticker = list(original_dfs.keys())[0]
    first_df = original_dfs[first_ticker]

    setup_event_id = df_db.write(first_df, BULK_TABLE_NAME, if_exists="replace", index=True)
    if not setup_event_id:
        raise Exception("Failed to create table")

    # Wait for table creation
    setup_results = df_db.get_results()
    if not setup_results[setup_event_id]["success"]:
        raise Exception(f"Table creation failed: {setup_results[setup_event_id]['error']}")

    # Now append remaining DataFrames in parallel
    write_mapping = {}
    remaining_dfs = {k: v for k, v in original_dfs.items() if k != first_ticker}

    for ticker, df in remaining_dfs.items():
        event_id = df_db.write(df, BULK_TABLE_NAME, if_exists="append", index=True)

        if not event_id:
            raise Exception(f"Failed to get event_id for ticker {ticker}")

        write_mapping[event_id] = {"ticker": ticker, "dataframe": df}

    # Get results for all write operations
    results = df_db.get_results()

    # Validate all write operations
    failed_writes = []
    for event_id, result in results.items():
        if event_id in write_mapping:
            ticker = write_mapping[event_id]["ticker"]
            if not result["success"]:
                failed_writes.append(f"Write failed for {ticker}: {result['error']}")

    if failed_writes:
        raise Exception(f"Write operations failed:\n" + "\n".join(failed_writes))

    return True


def read_all_dataframes(df_db, original_dfs):
    """
    Read all DataFrames from database by ticker using parallel operations.

    Parameters
    ----------
    df_db : basefunctions.DataFrameDb
        Database connection
    original_dfs : dict
        Dictionary with ticker keys to read

    Returns
    -------
    dict
        Dictionary mapping ticker to read DataFrame

    Raises
    ------
    Exception
        If any read operation fails
    """
    # Event-ID zu Ticker mapping
    read_mapping = {}

    for ticker in original_dfs.keys():
        event_id = df_db.read(
            BULK_TABLE_NAME,
            query=f'SELECT * FROM {BULK_TABLE_NAME} WHERE "Ticker" = %s ORDER BY "Date"',
            params=[ticker],
        )

        if not event_id:
            raise Exception(f"Failed to get event_id for ticker {ticker}")

        read_mapping[event_id] = {"ticker": ticker, "original_df": original_dfs[ticker]}

    # Get results for all read operations
    results = df_db.get_results()

    # Process read results
    read_dfs = {}
    failed_reads = []

    for event_id, result in results.items():
        if event_id in read_mapping:
            ticker = read_mapping[event_id]["ticker"]

            if result["success"]:
                df = result["data"]

                if df.empty:
                    failed_reads.append(f"No data found for ticker {ticker}")
                    continue

                # Set Date as index to match original structure
                if "Date" in df.columns:
                    df = df.set_index("Date")
                    # Convert index to datetime.date to match original
                    df.index = pd.to_datetime(df.index).date

                read_dfs[ticker] = df
            else:
                failed_reads.append(f"Read failed for {ticker}: {result['error']}")

    if failed_reads:
        raise Exception(f"Read operations failed:\n" + "\n".join(failed_reads))

    if len(read_dfs) != NUM_DATAFRAMES:
        raise Exception(f"Expected {NUM_DATAFRAMES} DataFrames, got {len(read_dfs)}")

    return read_dfs


def validate_dataframes(original_dfs, read_dfs):
    """
    Validate that original and read DataFrames are identical.

    Parameters
    ----------
    original_dfs : dict
        Original DataFrames
    read_dfs : dict
        DataFrames read from database

    Returns
    -------
    bool
        True if all DataFrames match

    Raises
    ------
    Exception
        If validation fails
    """
    mismatches = []

    for ticker in original_dfs.keys():
        if ticker not in read_dfs:
            mismatches.append(f"Ticker {ticker} missing in read data")
            continue

        original_df = original_dfs[ticker]
        read_df = read_dfs[ticker]

        # Compare DataFrames
        if not original_df.equals(read_df):
            # Detailed mismatch analysis
            if original_df.shape != read_df.shape:
                mismatches.append(f"{ticker}: Shape mismatch - Original: {original_df.shape}, Read: {read_df.shape}")
            elif not original_df.columns.equals(read_df.columns):
                mismatches.append(f"{ticker}: Column mismatch")
            elif not original_df.index.equals(read_df.index):
                mismatches.append(f"{ticker}: Index mismatch")
            else:
                mismatches.append(f"{ticker}: Data values mismatch")

    if mismatches:
        raise Exception(f"DataFrame validation failed:\n" + "\n".join(mismatches))

    return True


def test_bulk_operations():
    """
    Test bulk write/read operations with 50 DataFrames using parallel processing.

    Returns
    -------
    bool
        True if all operations successful

    Raises
    ------
    Exception
        If any operation fails
    """
    # Setup database connection
    df_db = basefunctions.DataFrameDb(DB_INSTANCE_NAME, DB_NAME)

    # Phase 1: Generate DataFrames
    print(f"Generating {NUM_DATAFRAMES} DataFrames...")
    start_time = time.time()
    original_dfs = generate_test_dataframes()
    generation_time = time.time() - start_time

    total_rows = sum(len(df) for df in original_dfs.values())
    print(f"Generated {len(original_dfs)} DataFrames with {total_rows} total rows in {generation_time:.2f}s")

    # Phase 2: Write all DataFrames (parallel)
    print(f"Writing {NUM_DATAFRAMES} DataFrames to database (parallel)...")
    start_time = time.time()
    write_all_dataframes(df_db, original_dfs)
    write_time = time.time() - start_time

    write_throughput = total_rows / write_time if write_time > 0 else 0
    print(f"Wrote {total_rows} rows in {write_time:.2f}s ({write_throughput:.0f} rows/sec)")

    # Phase 3: Read all DataFrames (parallel)
    print(f"Reading {NUM_DATAFRAMES} DataFrames from database (parallel)...")
    start_time = time.time()
    read_dfs = read_all_dataframes(df_db, original_dfs)
    read_time = time.time() - start_time

    read_throughput = total_rows / read_time if read_time > 0 else 0
    print(f"Read {total_rows} rows in {read_time:.2f}s ({read_throughput:.0f} rows/sec)")

    # Phase 4: Validate DataFrames
    print(f"Validating {NUM_DATAFRAMES} DataFrames...")
    start_time = time.time()
    validate_dataframes(original_dfs, read_dfs)
    validation_time = time.time() - start_time

    print(f"Validation completed in {validation_time:.2f}s")

    # Summary
    total_time = generation_time + write_time + read_time + validation_time
    print(f"Total test time: {total_time:.2f}s")
    print(f"Performance improvement: Parallel processing of {NUM_DATAFRAMES} operations")

    return True


def test_database_setup():
    """
    Ensure database exists for bulk testing.

    Returns
    -------
    bool
        True if database setup successful
    """
    manager = basefunctions.DbManager()
    instance = manager.get_instance(DB_INSTANCE_NAME)

    existing_databases = instance.list_databases()
    if DB_NAME not in existing_databases:
        instance.add_database(DB_NAME)
        updated_databases = instance.list_databases()
        if DB_NAME not in updated_databases:
            raise Exception(f"Database '{DB_NAME}' creation failed")

    return True


def main():
    """
    Main function to run bulk DataFrame tests.
    """
    # Disable logging for cleaner output
    basefunctions.DemoRunner.disable_global_logging()

    # Initialize test runner
    runner = basefunctions.DemoRunner()

    # Run tests
    runner.run_test("Database Setup", test_database_setup)
    runner.run_test(f"Bulk Operations ({NUM_DATAFRAMES} DataFrames)", test_bulk_operations)

    # Display results
    runner.print_results()


if __name__ == "__main__":
    main()
