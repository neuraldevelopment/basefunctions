"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich
  Project : database_debug_test
  Copyright (c) by neuraldevelopment
  All rights reserved.
  Description:
  Database demo showing decorator pattern with DemoRunner
 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import pandas as pd
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

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------

basefunctions.DemoRunner.init_logging()

# Global database reference for test functions
database = None


def create_test_dataframe() -> pd.DataFrame:
    """Create test DataFrame."""
    return pd.DataFrame({"id": [1, 2, 3], "name": ["Alice", "Bob", "Charlie"], "value": [100.5, 200.0, 300.25]})


def test_connection():
    """Test database connection and EventBus availability."""
    info = database.get_connection_info()
    if not info.get("eventbus_available"):
        raise Exception("EventBus not available")


def test_table_ops():
    """Test table existence operations."""
    exists = database.table_exists("nonexistent_table")
    if exists:
        raise Exception("Nonexistent table reported as existing")


def test_async_write():
    """Test asynchronous DataFrame write operations."""
    df = create_test_dataframe()
    database.submit_dataframe_write("demo_test", df, "replace")
    results = database.get_dataframe_write_results()
    if not results:
        raise Exception("No write results returned")


def test_async_read():
    """Test asynchronous DataFrame read operations."""
    database.submit_dataframe_read("SELECT * FROM demo_test ORDER BY id")
    dataframes = database.get_dataframe_read_results()
    if not dataframes or len(dataframes[0]) != 3:
        raise Exception("Read failed or wrong row count")


def test_sync_sql():
    """Test synchronous SQL operations."""
    rows = database.query_all("SELECT COUNT(*) as cnt FROM demo_test")
    if not rows or rows[0]["cnt"] != 3:
        raise Exception("Sync SQL failed or wrong count")


def test_batch_write():
    """Test batch DataFrame write operations."""
    df1 = pd.DataFrame({"id": [1], "val": [100]})
    df2 = pd.DataFrame({"id": [2], "val": [200]})
    writes = [("batch_test", df1, "replace"), ("batch_test", df2, "append")]
    database.submit_dataframe_write_batch(writes)
    results = database.get_dataframe_write_results()
    if len(results) != 2:
        raise Exception("Expected 2 write results")


def test_batch_read():
    """Test batch DataFrame read operations."""
    queries = [("SELECT * FROM batch_test WHERE id = 1", ()), ("SELECT * FROM batch_test WHERE id = 2", ())]
    database.submit_dataframe_read_batch(queries)
    dataframes = database.get_dataframe_read_results()
    if len(dataframes) != 2:
        raise Exception("Expected 2 dataframes")


def test_transaction():
    """Test database transaction operations."""
    with database.transaction():
        database.execute("CREATE TEMP TABLE tx_test (id INT)")
        database.execute("INSERT INTO tx_test VALUES (1)")
        count = database.query_one("SELECT COUNT(*) as cnt FROM tx_test")
        if count["cnt"] != 1:
            raise Exception("Transaction failed")


def test_eventbus():
    """Test EventBus integration."""
    info = database.get_connection_info()
    if not (info.get("eventbus_available") and info.get("connected", False)):
        raise Exception("EventBus not properly configured")


def database_demo():
    """Database functionality demo using decorator pattern."""
    global database

    # Load configuration and setup database
    config_handler = basefunctions.ConfigHandler()
    config_handler.load_default_config("basefunctions")

    # Create database directly via new Db constructor
    database = basefunctions.Db("dev_test_db_postgres")

    # Setup demo runner with CLI argument support
    demo = basefunctions.DemoRunner(max_width=100)

    # Register all test functions using decorator pattern
    demo.test("Connection Check")(test_connection)
    demo.test("Table Operations")(test_table_ops)
    demo.test("Async Write")(test_async_write)
    demo.test("Async Read")(test_async_read)
    demo.test("Sync SQL")(test_sync_sql)
    demo.test("Batch Write")(test_batch_write)
    demo.test("Batch Read")(test_batch_read)
    demo.test("Transaction")(test_transaction)
    demo.test("EventBus Integration")(test_eventbus)

    # Run all decorator tests
    demo.run_all_tests()

    # Display results
    demo.print_results("Database Demo Suite")

    # Cleanup
    database.close()

    return demo.has_failures()


if __name__ == "__main__":
    failed = database_demo()
    exit(1 if failed else 0)
