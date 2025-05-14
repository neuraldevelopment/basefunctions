"""
=============================================================================

 Licensed Materials, Property of neuraldevelopment , Munich

 Project : backtraderfunctions

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 Test program for writing DataFrames to SQLite without using ThreadPool

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import os
import time
import pandas as pd
import random
import basefunctions
from typing import Dict, Any, List

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------
SQLITE_DB_PATH = "test_dataframes.db"
NUM_DATAFRAMES = 100


# -------------------------------------------------------------
# FUNCTION DEFINITIONS
# -------------------------------------------------------------
def create_test_dataframe(df_id: int) -> pd.DataFrame:
    """
    create a test dataframe with random data

    parameters
    ----------
    df_id : int
        identifier for the dataframe

    returns
    -------
    pd.DataFrame
        randomly generated dataframe
    """
    rows = random.randint(10, 50)
    data = {
        "id": list(range(rows)),
        "df_id": [df_id] * rows,
        "value_a": [random.random() * 100 for _ in range(rows)],
        "value_b": [random.random() * 100 for _ in range(rows)],
        "category": [random.choice(["A", "B", "C", "D"]) for _ in range(rows)],
    }
    return pd.DataFrame(data)


def setup_database() -> None:
    """
    setup test database and table
    """
    # Remove existing database if present
    if os.path.exists(SQLITE_DB_PATH):
        os.remove(SQLITE_DB_PATH)
        print(f"Removed existing database: {SQLITE_DB_PATH}")

    # Create database parameters
    sqlite_params = basefunctions.DatabaseParameters(database=SQLITE_DB_PATH)

    # Create handler for initialization
    db_handler = basefunctions.BaseDatabaseHandler()
    db_handler.register_connector("test_db", "sqlite3", sqlite_params)

    # Create test table
    db_handler.execute(
        "test_db",
        """
        CREATE TABLE IF NOT EXISTS test_data (
            id INTEGER,
            df_id INTEGER,
            value_a REAL,
            value_b REAL,
            category TEXT
        )
        """,
    )

    # Verify table creation
    table_exists = db_handler.check_if_table_exists("test_db", "test_data")
    print(f"Table test_data created: {table_exists}")

    db_handler.close_all()


def check_results() -> Dict[str, Any]:
    """
    check database after test

    returns
    -------
    Dict[str, Any]
        statistics about written data
    """
    db_handler = basefunctions.BaseDatabaseHandler()
    sqlite_params = basefunctions.DatabaseParameters(database=SQLITE_DB_PATH)
    db_handler.register_connector("test_db", "sqlite3", sqlite_params)

    # Count total rows
    result = db_handler.fetch_one("test_db", "SELECT COUNT(*) as total FROM test_data")
    total_rows = result["total"] if result else 0

    # Count unique df_ids
    result = db_handler.fetch_one(
        "test_db", "SELECT COUNT(DISTINCT df_id) as total_dfs FROM test_data"
    )
    total_dfs = result["total_dfs"] if result else 0

    # Sample a few rows
    sample_rows = db_handler.fetch_all("test_db", "SELECT * FROM test_data LIMIT 5")

    db_handler.close_all()

    return {"total_rows": total_rows, "total_dataframes": total_dfs, "sample_rows": sample_rows}


def batch_process_dataframes(dataframes: List[pd.DataFrame], batch_size: int = 10) -> None:
    """
    process a list of dataframes in batches for better performance

    parameters
    ----------
    dataframes : List[pd.DataFrame]
        list of dataframes to process
    batch_size : int, optional
        number of dataframes to process in one batch, by default 10
    """
    # Create database handler
    db_handler = basefunctions.DatabaseHandler(
        cached=True,  # Use caching for better performance
        use_threadpool=False,  # Do not use threadpool
        max_cache_size=batch_size,  # Flush after batch_size dataframes
    )

    # Register connector
    sqlite_params = basefunctions.DatabaseParameters(database=SQLITE_DB_PATH)
    db_handler.register_connector("test_db", "sqlite3", sqlite_params)

    # Process dataframes
    for i, df in enumerate(dataframes):
        try:
            db_handler.add_dataframe("test_db", "test_data", df)
            if i % 10 == 0 and i > 0:
                print(f"Processed {i}/{len(dataframes)} dataframes")
        except Exception as e:
            print(f"Error processing dataframe {i}: {e}")

    # Make sure to flush any remaining dataframes in cache
    print("Flushing remaining dataframes...")
    db_handler.flush()

    db_handler.close_all()


# -------------------------------------------------------------
# MAIN TEST FUNCTION
# -------------------------------------------------------------
def main() -> None:
    """
    main test function
    """
    print("Setting up test database...")
    setup_database()

    print(f"Creating {NUM_DATAFRAMES} dataframes...")

    # Generate all dataframes first
    dataframes = []
    for i in range(NUM_DATAFRAMES):
        df = create_test_dataframe(i)
        dataframes.append(df)

    # Add special test dataframe
    test_df = create_test_dataframe(999)
    dataframes.append(test_df)

    print(f"Generated {len(dataframes)} dataframes")

    # Time the database writing operation
    start_time = time.time()
    print("Starting to write dataframes to database...")

    # Process dataframes in batches
    batch_process_dataframes(dataframes, batch_size=20)

    elapsed_time = time.time() - start_time
    print(f"All dataframes written in {elapsed_time:.2f} seconds")

    # Check results
    print("\nChecking results...")
    results = check_results()

    print(f"Total rows written: {results['total_rows']}")
    print(f"Total dataframes processed: {results['total_dataframes']}")
    print("\nSample rows:")
    for row in results["sample_rows"]:
        print(row)

    print(f"\nTest completed in {elapsed_time:.2f} seconds")


if __name__ == "__main__":
    main()
