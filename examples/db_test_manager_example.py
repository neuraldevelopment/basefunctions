"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich
  Project : basefunctions
  Copyright (c) by neuraldevelopment
  All rights reserved.
  Description:
  Modernized database diagnostic tool using current API architecture with DemoRunner
 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import basefunctions
import argparse
import sys
import time
import traceback
import pandas as pd

# -------------------------------------------------------------
# DEFINITIONS REGISTRY
# -------------------------------------------------------------

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------

# Global variables for test functions
db_manager = None
instance = None
database = None
args = None

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------

basefunctions.DemoRunner.init_logging()


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Database connection diagnostic tool.")

    parser.add_argument(
        "instance_name",
        nargs="?",
        default="dev_test_db_postgres",
        help="Name of the database instance to connect to",
    )

    parser.add_argument("--list", "-l", action="store_true", help="List all available database instances")

    parser.add_argument(
        "--version-only",
        "-v",
        action="store_true",
        help="Only retrieve and print the database version",
    )

    parser.add_argument(
        "--db-name",
        help="Specific database name to use (defaults to system database for the instance type)",
    )

    parser.add_argument(
        "--test-dataframes",
        "-df",
        action="store_true",
        help="Test DataFrame operations with EventBus",
    )

    parser.add_argument(
        "--test-transactions",
        "-tx",
        action="store_true",
        help="Test transaction operations",
    )

    parser.add_argument(
        "--verbose",
        "-vv",
        action="store_true",
        help="Enable verbose output",
    )

    return parser.parse_args()


def list_available_instances():
    """List all available database instances."""
    print("\n=== Available Database Instances ===\n")

    try:
        config_handler = basefunctions.ConfigHandler()
        config = config_handler.get_config()

        if "databases" in config:
            instances = config["databases"]
            if instances:
                print(f"Found {len(instances)} configured instances:")
                for idx, (name, details) in enumerate(instances.items(), 1):
                    db_type = details.get("type", "unknown")
                    connection = details.get("connection", {})
                    host = connection.get("host", "localhost")
                    ports = details.get("ports", {})
                    port = ports.get("db", "default")
                    print(f"{idx:2}. {name:<25} ({db_type:<10} on {host}:{port})")
            else:
                print("No database instances found in configuration.")
        else:
            print("No 'databases' section found in configuration.")

        print("\nUsage examples:")
        print("  python db_test_manager.py <instance_name>")
        print("  python db_test_manager.py <instance_name> --version-only")
        print("  python db_test_manager.py <instance_name> --test-dataframes")
        print("  python db_test_manager.py <instance_name> --test-transactions")

    except Exception as e:
        print(f"Error listing instances: {str(e)}")
        if args.verbose:
            traceback.print_exc()


def determine_system_database(db_type, instance_name):
    """Determine the appropriate system database for each database type."""
    system_databases = {
        "postgres": "postgres",
        "postgresql": "postgres",
        "mysql": "mysql",
        "sqlite3": instance_name,  # For SQLite, use instance name as database
    }
    return system_databases.get(db_type, "main")


def test_connection():
    """Test basic database connection and query functionality."""
    global database, instance

    # Force connection by executing a simple query
    try:
        database.query_one("SELECT 1 as test")
    except Exception as e:
        raise Exception(f"Could not establish connection: {str(e)}")

    # Now check connection info
    info = database.get_connection_info()
    if not info.get("connected"):
        raise Exception("Database reports not connected after successful query")

    # Test version query
    db_type = instance.get_type()
    version_queries = {
        "postgres": "SELECT version() as version",
        "postgresql": "SELECT version() as version",
        "mysql": "SELECT VERSION() as version",
        "sqlite3": "SELECT sqlite_version() as version",
    }

    version_query = version_queries.get(db_type, "SELECT 'Unknown DB type' as version")
    result = database.query_one(version_query)

    if not result or "version" not in result:
        raise Exception("Version query failed")


def test_table_operations():
    """Test table operations."""
    global database, instance

    db_type = instance.get_type()

    # For PostgreSQL, try a simpler approach first
    if db_type in ["postgres", "postgresql"]:
        # Test with a query instead of table_exists for system tables
        result = database.query_one("SELECT COUNT(*) as count FROM information_schema.tables LIMIT 1")
        if not result or "count" not in result:
            raise Exception("Could not query information_schema.tables")
    else:
        # Test table existence check for other DB types
        system_table = {"mysql": "information_schema.tables", "sqlite3": "sqlite_master"}.get(db_type, "sqlite_master")

        table_exists = database.table_exists(system_table)
        if not table_exists:
            raise Exception(f"System table {system_table} not found")

    # Test list tables
    tables = database.list_tables()
    if not isinstance(tables, list):
        raise Exception("list_tables() did not return a list")


def test_sync_sql():
    """Test synchronous SQL operations."""
    global database

    # Test simple query
    result = database.query_one("SELECT 1 as test_value")
    if not result or result.get("test_value") != 1:
        raise Exception("Simple query failed")

    # Test query_all
    results = database.query_all("SELECT 1 as id UNION SELECT 2 as id ORDER BY id")
    if len(results) != 2:
        raise Exception("query_all failed")


def test_dataframe_write():
    """Test DataFrame write operations."""
    global database

    # Create test DataFrame
    test_df = pd.DataFrame({"id": [1, 2, 3], "name": ["Alice", "Bob", "Charlie"], "value": [100.5, 200.0, 300.25]})

    # Submit write
    database.submit_dataframe_write("test_df_table", test_df, "replace")
    results = database.get_dataframe_write_results()

    if not results:
        raise Exception("No write results returned")


def test_dataframe_read():
    """Test DataFrame read operations."""
    global database

    # Submit read
    database.submit_dataframe_read("SELECT * FROM test_df_table ORDER BY id")
    dataframes = database.get_dataframe_read_results()

    if not dataframes or len(dataframes[0]) != 3:
        raise Exception("DataFrame read failed or wrong row count")


def test_transactions():
    """Test transaction operations."""
    global database

    with database.transaction():
        database.execute("CREATE TEMP TABLE tx_test (id INT)")
        database.execute("INSERT INTO tx_test VALUES (1)")
        count = database.query_one("SELECT COUNT(*) as cnt FROM tx_test")
        if count["cnt"] != 1:
            raise Exception("Transaction test failed")


def test_eventbus():
    """Test EventBus integration."""
    global database

    info = database.get_connection_info()
    if not info.get("eventbus_available"):
        raise Exception("EventBus not available")


def get_version_only():
    """Get and display only the database version."""
    global database, instance

    try:
        db_type = instance.get_type()

        version_queries = {
            "postgres": "SELECT version() as version",
            "postgresql": "SELECT version() as version",
            "mysql": "SELECT VERSION() as version",
            "sqlite3": "SELECT sqlite_version() as version",
        }

        version_query = version_queries.get(db_type, "SELECT 'Unknown database type' as version")
        result = database.query_one(version_query)

        if result and "version" in result:
            print(f"{db_type.upper()} Version: {result['version']}")
        else:
            print("Could not retrieve version information.")

    except Exception as e:
        print(f"Error retrieving version: {str(e)}")
        if args.verbose:
            traceback.print_exc()


def main():
    """Main function."""
    global args, db_manager, instance, database
    args = parse_args()

    print(f"Database Diagnostic Tool")
    print(f"{'='*50}")

    # Handle list command
    if args.list:
        list_available_instances()
        return 0

    instance_name = args.instance_name

    try:
        # Load configuration and setup database
        config_handler = basefunctions.ConfigHandler()
        config_handler.load_default_config("basefunctions")

        # Create database directly via new Db constructor
        database = basefunctions.Db(instance_name)

        # For compatibility, create fake instance to get db_type
        config = config_handler.get_database_config(instance_name)
        if not config:
            raise Exception(f"No configuration found for instance '{instance_name}'")

        class FakeInstance:
            def get_type(self):
                return config.get("type", "unknown")

        instance = FakeInstance()

    except Exception as e:
        print(f"Error setting up database '{instance_name}': {str(e)}")
        if args.verbose:
            traceback.print_exc()
        return 1

    # Handle version-only command
    if args.version_only:
        get_version_only()
        database.close()
        return 0

    # Setup demo runner
    demo = basefunctions.DemoRunner(max_width=150)

    # Register basic tests
    demo.test("Connection Check")(test_connection)
    demo.test("Table Operations")(test_table_operations)
    demo.test("Sync SQL")(test_sync_sql)
    demo.test("EventBus Integration")(test_eventbus)

    # Register optional tests based on arguments
    if args.test_dataframes:
        demo.test("DataFrame Write")(test_dataframe_write)
        demo.test("DataFrame Read")(test_dataframe_read)

    if args.test_transactions:
        demo.test("Transactions")(test_transactions)

    try:
        # Run all tests
        demo.run_all_tests()

        # Display results
        demo.print_results(f"Database Diagnostic Results - {instance_name}")

        # Return appropriate exit code
        return 1 if demo.has_failures() else 0

    except Exception as e:
        print(f"\nUnexpected error during testing: {str(e)}")
        if args.verbose:
            traceback.print_exc()
        return 1

    finally:
        # Always close connections
        try:
            database.close()
            if args.verbose:
                print("\n✓ Database connection closed")
        except Exception as e:
            print(f"Warning: Error closing connection: {str(e)}")


if __name__ == "__main__":
    sys.exit(main())
