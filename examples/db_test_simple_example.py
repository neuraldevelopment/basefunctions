"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich
  Project : database_debug_test
  Copyright (c) by neuraldevelopment
  All rights reserved.
  Description:
  Database demo showing decorator pattern with DemoRunner and new DB interface
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

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------

# Initialize logging before any other imports
basefunctions.DemoRunner.disable_global_logging()

# Global database reference for test functions
database = None
manager = None


def test_instance_management():
    """Test database instance management."""
    # List available instances
    instances = manager.list_instances()

    # Check if our existing instance exists
    if not manager.has_instance("dev_test_db_postgres"):
        raise Exception("Existing instance 'dev_test_db_postgres' not found")

    # Get instance
    instance = manager.get_instance("dev_test_db_postgres")
    config = instance.get_config()
    if config.get("type") != "postgresql":
        raise Exception("Instance type mismatch")


def test_connection():
    """Test database connection."""
    # Connect to database
    database.connect()

    # Check connection status
    if not database.is_connected():
        raise Exception("Database connection failed")

    # Get connection info
    info = database.get_connection_info()
    if not info.get("connected", False):
        raise Exception("Connection info reports disconnected")


def test_table_operations():
    """Test table existence operations."""
    # Test checking for nonexistent table
    exists = database.check_if_table_exists("nonexistent_table")
    if exists:
        raise Exception("Nonexistent table reported as existing")

    # Create a test table
    database.execute(
        """
        CREATE TABLE IF NOT EXISTS demo_test (
            id <PRIMARYKEY>,
            name VARCHAR(100),
            value DECIMAL(10,2)
        )
    """
    )

    # Check if table now exists
    exists = database.check_if_table_exists("demo_test")
    if not exists:
        raise Exception("Created table not found")


def test_basic_sql_operations():
    """Test basic SQL operations."""
    # Clear table
    database.execute("DELETE FROM demo_test")

    # Insert test data
    database.execute("INSERT INTO demo_test (name, value) VALUES (%s, %s)", ("Alice", 100.5))
    database.execute("INSERT INTO demo_test (name, value) VALUES (%s, %s)", ("Bob", 200.0))
    database.execute("INSERT INTO demo_test (name, value) VALUES (%s, %s)", ("Charlie", 300.25))

    # Test query_one
    row = database.query_one("SELECT COUNT(*) as cnt FROM demo_test")
    if not row or row["cnt"] != 3:
        raise Exception("query_one failed or wrong count")

    # Test query_all
    rows = database.query_all("SELECT * FROM demo_test ORDER BY name")
    if len(rows) != 3 or rows[0]["name"] != "Alice":
        raise Exception("query_all failed or wrong data")


def test_query_iterator():
    """Test query iterator for large resultsets."""
    # Test iterator
    count = 0
    for row in database.query_iter("SELECT * FROM demo_test ORDER BY name"):
        count += 1
        if not row.get("name"):
            raise Exception("Iterator returned invalid row")

    if count != 3:
        raise Exception(f"Iterator returned {count} rows, expected 3")


def test_transaction_management():
    """Test database transaction operations."""
    # Test transaction context manager
    with database.transaction():
        database.execute("INSERT INTO demo_test (name, value) VALUES (%s, %s)", ("Transaction Test", 999.99))

        # Check data exists within transaction
        row = database.query_one("SELECT COUNT(*) as cnt FROM demo_test WHERE name = %s", ("Transaction Test",))
        if not row or row["cnt"] != 1:
            raise Exception("Transaction data not found within transaction")

    # Check data persisted after commit
    row = database.query_one("SELECT COUNT(*) as cnt FROM demo_test WHERE name = %s", ("Transaction Test",))
    if not row or row["cnt"] != 1:
        raise Exception("Transaction data not persisted after commit")

    # Test rollback on exception
    try:
        with database.transaction():
            database.execute("INSERT INTO demo_test (name, value) VALUES (%s, %s)", ("Rollback Test", 888.88))
            raise Exception("Intentional rollback")
    except Exception as e:
        if "Intentional rollback" not in str(e):
            raise Exception("Unexpected exception during rollback test")

    # Check rollback worked
    row = database.query_one("SELECT COUNT(*) as cnt FROM demo_test WHERE name = %s", ("Rollback Test",))
    if not row or row["cnt"] != 0:
        raise Exception("Transaction rollback failed")


def test_manual_transaction():
    """Test manual transaction control."""
    # Begin transaction manually
    database.begin_transaction()

    try:
        database.execute("INSERT INTO demo_test (name, value) VALUES (%s, %s)", ("Manual TX", 777.77))

        # Commit manually
        database.commit()

        # Verify data persisted
        row = database.query_one("SELECT COUNT(*) as cnt FROM demo_test WHERE name = %s", ("Manual TX",))
        if not row or row["cnt"] != 1:
            raise Exception("Manual transaction commit failed")

    except Exception as e:
        database.rollback()
        raise


def test_schema_operations():
    """Test schema and table listing operations."""
    # List tables
    tables = database.list_tables()
    if "demo_test" not in tables:
        raise Exception("demo_test table not found in table list")

    # Try schema operations (if supported)
    try:
        database.use_schema("public")  # This will work for PostgreSQL, fail for others
    except NotImplementedError:
        # Expected for MySQL and SQLite
        pass


def test_connector_access():
    """Test low-level connector access."""
    # Get connector
    connector = database.get_connector()
    if not connector:
        raise Exception("Failed to get connector")

    # Test connector connection
    if not connector.is_connected():
        raise Exception("Connector reports disconnected")

    # Get connection info
    info = connector.get_connection_info()
    if not info.get("connected", False):
        raise Exception("Connector connection info invalid")


def test_direct_manager_access():
    """Test direct manager access to databases."""
    # Get database directly from manager
    direct_db = manager.get_database("dev_test_db_postgres", "postgres")

    # Test connection
    direct_db.connect()
    if not direct_db.is_connected():
        raise Exception("Direct database access failed")

    # Test query
    row = direct_db.query_one("SELECT 1 as test")
    if not row or row["test"] != 1:
        raise Exception("Direct database query failed")

    # Cleanup
    direct_db.disconnect()


def test_performance_metrics():
    """Test and measure basic performance."""
    import time

    # Measure query performance
    start_time = time.time()
    for _ in range(10):
        database.query_one("SELECT COUNT(*) as cnt FROM demo_test")
    end_time = time.time()

    query_time = (end_time - start_time) * 1000  # Convert to milliseconds
    if query_time > 1000:  # More than 1 second for 10 queries seems slow
        raise Exception(f"Query performance too slow: {query_time:.2f}ms for 10 queries")


def database_demo():
    """Database functionality demo using decorator pattern with new DB interface."""
    global database, manager

    # Setup demo runner with CLI argument support
    demo = basefunctions.DemoRunner(max_width=120)

    try:
        # Initialize database manager
        manager = basefunctions.DbManager()

        # Use existing instance instead of creating new one
        instance = manager.get_instance("dev_test_db_postgres")

        # Get specific database from existing instance
        database = instance.get_database("postgres")

        # Register all test functions using decorator pattern
        demo.test("Instance Management")(test_instance_management)
        demo.test("Connection Test")(test_connection)
        demo.test("Table Operations")(test_table_operations)
        demo.test("Basic SQL Operations")(test_basic_sql_operations)
        demo.test("Query Iterator")(test_query_iterator)
        demo.test("Transaction Management")(test_transaction_management)
        demo.test("Manual Transaction")(test_manual_transaction)
        demo.test("Schema Operations")(test_schema_operations)
        demo.test("Connector Access")(test_connector_access)
        demo.test("Direct Manager Access")(test_direct_manager_access)
        demo.test("Performance Metrics")(test_performance_metrics)

        # Run all decorator tests
        demo.run_all_tests()

        # Display results
        demo.print_results("Database Demo Suite - New Interface")

        # Add performance data
        if database.is_connected():
            info = database.get_connection_info()
            performance_data = [
                ("Database Type", info.get("db_type", "Unknown")),
                ("Connection Status", "Connected" if info.get("connected") else "Disconnected"),
                ("Current Database", info.get("current_database", "Unknown")),
                ("Current Schema", info.get("current_schema", "None")),
                ("In Transaction", "Yes" if info.get("in_transaction") else "No"),
                ("Host", f"{info.get('host', 'N/A')}:{info.get('port', 'N/A')}"),
            ]
            demo.print_performance_table(performance_data, "Database Connection Info")

    except Exception as e:
        demo.add_result("Setup", False, str(e))
        demo.print_results("Database Demo Suite - Setup Failed")
        return True

    finally:
        # Cleanup
        try:
            if database:
                database.disconnect()
        except Exception:
            pass

    return demo.has_failures()


if __name__ == "__main__":
    failed = database_demo()
    exit(1 if failed else 0)
