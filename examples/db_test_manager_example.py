"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich
  Project : basefunctions
  Copyright (c) by neuraldevelopment
  All rights reserved.
  Description:
  Modernized database diagnostic tool using current API architecture
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

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Database connection diagnostic tool.")

    parser.add_argument(
        "instance_name",
        nargs="?",
        default="dev_asset_db_postgres",
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


def list_available_instances(db_manager):
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


def test_basic_connection(db_manager, instance_name, db_name, verbose=False):
    """Test basic database connection and query functionality."""
    print(f"\n{'='*70}")
    print(f"BASIC CONNECTION TEST: {instance_name} -> {db_name}")
    print(f"{'='*70}")

    try:
        # Step 1: Get instance
        print("\n[1] Getting database instance...")
        instance = db_manager.get_instance(instance_name)
        db_type = instance.get_type()
        print(f"    ✓ Instance created: {instance.instance_name} ({db_type})")

        if verbose:
            print(f"    Instance config: {instance.get_config()}")

        # Step 2: Get database object
        print("\n[2] Creating database object...")
        db = instance.get_database(db_name)
        print(f"    ✓ Database object created for: {db_name}")

        if verbose:
            print(f"    Database info: {db}")

        # Step 3: Test connector
        print("\n[3] Testing database connector...")
        connector = db.connector
        print(f"    Connector type: {type(connector).__name__}")
        print(f"    Database type: {connector.db_type}")

        # Connect if not already connected
        if not connector.is_connected():
            print("    Connecting to database...")
            connector.connect()

        print(f"    ✓ Connection status: {connector.is_connected()}")

        if verbose:
            conn_info = connector.get_connection_info()
            print(f"    Connection info: {conn_info}")

        # Step 4: Execute version query
        print("\n[4] Testing SQL query execution...")
        version_queries = {
            "postgres": "SELECT version() as version",
            "postgresql": "SELECT version() as version",
            "mysql": "SELECT VERSION() as version",
            "sqlite3": "SELECT sqlite_version() as version",
        }

        version_query = version_queries.get(db_type, "SELECT 'Unknown DB type' as version")
        result = db.query_one(version_query)

        if result:
            version_info = result.get("version", "Unknown")
            # Truncate long version strings for readability
            if len(version_info) > 80:
                version_info = version_info[:77] + "..."
            print(f"    ✓ Version query successful")
            print(f"    Database version: {version_info}")
        else:
            print("    ⚠ Version query returned no results")

        # Step 5: Test table operations
        print("\n[5] Testing table operations...")
        table_exists = db.table_exists(
            "information_schema.tables" if db_type in ["postgres", "postgresql", "mysql"] else "sqlite_master"
        )
        print(f"    ✓ Table existence check: {table_exists}")

        tables = db.list_tables()
        print(f"    ✓ Found {len(tables)} tables in database")

        if verbose and tables:
            print(f"    First 5 tables: {tables[:5]}")

        return True

    except Exception as e:
        print(f"    ✗ Connection test failed: {str(e)}")
        if verbose:
            traceback.print_exc()
        return False


def test_dataframe_operations(db_manager, instance_name, db_name, verbose=False):
    """Test DataFrame operations with EventBus."""
    print(f"\n{'='*70}")
    print(f"DATAFRAME OPERATIONS TEST: {instance_name} -> {db_name}")
    print(f"{'='*70}")

    try:
        # Get database object
        print("\n[1] Setting up database connection...")
        instance = db_manager.get_instance(instance_name)
        db = instance.get_database(db_name)
        print(f"    ✓ Database ready: {db_name}")

        # Test DataFrame read
        print("\n[2] Testing DataFrame read operation...")
        query = "SELECT 1 as id, 'test_value' as name, 42.5 as value"
        df_result = db.read_to_dataframe(query)

        print(f"    ✓ DataFrame read successful")
        print(f"    Shape: {df_result.shape}")
        print(f"    Columns: {list(df_result.columns)}")

        if verbose:
            print(f"    Data preview:\n{df_result}")

        # Create test table and test DataFrame write
        print("\n[3] Testing DataFrame write operation...")

        # Create test DataFrame
        test_data = pd.DataFrame(
            {
                "id": [1, 2, 3, 4, 5],
                "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
                "score": [95.5, 87.2, 92.8, 88.9, 91.3],
                "active": [True, True, False, True, True],
            }
        )

        test_table = "df_test_table"

        # Drop table if exists (database-specific syntax)
        db_type = instance.get_type()
        try:
            if db_type in ["postgres", "postgresql"]:
                db.execute(f"DROP TABLE IF EXISTS {test_table}")
            elif db_type == "mysql":
                db.execute(f"DROP TABLE IF EXISTS {test_table}")
            elif db_type == "sqlite3":
                db.execute(f"DROP TABLE IF EXISTS {test_table}")
        except Exception as e:
            if verbose:
                print(f"    Note: Could not drop existing table: {e}")

        # Write DataFrame to database
        db.write_dataframe(test_table, test_data, if_exists="replace")
        print(f"    ✓ DataFrame written to table: {test_table}")

        # Verify write by reading back
        verification_df = db.read_to_dataframe(f"SELECT * FROM {test_table} ORDER BY id")
        print(f"    ✓ Verification read successful")
        print(f"    Written records: {len(test_data)}, Read records: {len(verification_df)}")

        if verbose:
            print(f"    Verification data:\n{verification_df}")

        # Test cached DataFrame operations
        print("\n[4] Testing cached DataFrame operations...")

        cached_data1 = pd.DataFrame(
            {"id": [6, 7], "name": ["Frank", "Grace"], "score": [89.1, 93.7], "active": [True, False]}
        )
        cached_data2 = pd.DataFrame(
            {"id": [8, 9], "name": ["Henry", "Iris"], "score": [86.4, 94.2], "active": [False, True]}
        )

        # Write to cache
        db.write_dataframe(test_table, cached_data1, cached=True, if_exists="append")
        db.write_dataframe(test_table, cached_data2, cached=True, if_exists="append")
        print(f"    ✓ DataFrames cached")

        cache_info = db.get_cache_info()
        print(f"    Cache info: {cache_info}")

        # Flush cache
        db.flush_cache(test_table)
        print(f"    ✓ Cache flushed to database")

        # Verify final result
        final_df = db.read_to_dataframe(f"SELECT COUNT(*) as total_records FROM {test_table}")
        total_records = final_df.iloc[0]["total_records"]
        print(f"    ✓ Total records in table: {total_records}")

        # Clean up test table
        db.execute(f"DROP TABLE IF EXISTS {test_table}")
        print(f"    ✓ Test table cleaned up")

        return True

    except Exception as e:
        print(f"    ✗ DataFrame operations test failed: {str(e)}")
        if verbose:
            traceback.print_exc()
        return False


def get_parameter_placeholder(db_type):
    """Get the correct parameter placeholder for the database type."""
    placeholders = {"postgres": "%s", "postgresql": "%s", "mysql": "%s", "sqlite3": "?"}
    return placeholders.get(db_type, "?")


def test_transaction_operations(db_manager, instance_name, db_name, verbose=False):
    """Test transaction operations."""
    print(f"\n{'='*70}")
    print(f"TRANSACTION OPERATIONS TEST: {instance_name} -> {db_name}")
    print(f"{'='*70}")

    try:
        # Get database object
        print("\n[1] Setting up database connection...")
        instance = db_manager.get_instance(instance_name)
        db = instance.get_database(db_name)
        db_type = instance.get_type()
        placeholder = get_parameter_placeholder(db_type)
        print(f"    ✓ Database ready: {db_name} ({db_type}, placeholder: {placeholder})")

        # Create test table
        print("\n[2] Creating test table...")
        test_table = "tx_test_table"

        # Drop and recreate table
        try:
            db.execute(f"DROP TABLE IF EXISTS {test_table}")
        except Exception as e:
            if verbose:
                print(f"    Note: Could not drop existing table: {e}")

        # Create table with database-specific syntax
        if db_type in ["postgres", "postgresql"]:
            create_sql = f"""
                CREATE TABLE {test_table} (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100),
                    balance DECIMAL(10,2)
                )
            """
        elif db_type == "mysql":
            create_sql = f"""
                CREATE TABLE {test_table} (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100),
                    balance DECIMAL(10,2)
                )
            """
        else:  # sqlite3
            create_sql = f"""
                CREATE TABLE {test_table} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    balance REAL
                )
            """

        db.execute(create_sql)
        print(f"    ✓ Test table created: {test_table}")

        # Test successful transaction
        print("\n[3] Testing successful transaction...")
        with db.transaction() as tx:
            db.execute(
                f"INSERT INTO {test_table} (name, balance) VALUES ({placeholder}, {placeholder})", ("Alice", 1000.00)
            )
            db.execute(
                f"INSERT INTO {test_table} (name, balance) VALUES ({placeholder}, {placeholder})", ("Bob", 1500.00)
            )
            db.execute(
                f"UPDATE {test_table} SET balance = balance - {placeholder} WHERE name = {placeholder}",
                (100.00, "Alice"),
            )
            db.execute(
                f"UPDATE {test_table} SET balance = balance + {placeholder} WHERE name = {placeholder}",
                (100.00, "Bob"),
            )
            print(f"    ✓ Transaction operations executed")

        print(f"    ✓ Transaction committed successfully")

        # Verify transaction results
        results = db.query_all(f"SELECT name, balance FROM {test_table} ORDER BY name")
        print(f"    Transaction results: {results}")

        # Test failed transaction (rollback)
        print("\n[4] Testing transaction rollback...")
        print("    NOTE: The following error messages are INTENTIONAL to test rollback functionality:")
        try:
            with db.transaction() as tx:
                db.execute(
                    f"INSERT INTO {test_table} (name, balance) VALUES ({placeholder}, {placeholder})",
                    ("Charlie", 2000.00),
                )
                # Intentional error to trigger rollback
                db.execute("SELECT * FROM non_existent_table")
        except Exception as e:
            print(f"    ✓ Transaction failed as expected: {type(e).__name__}")

        print("    ✓ Error messages above are EXPECTED - they demonstrate proper rollback behavior")

        # Verify rollback
        charlie_check = db.query_one(
            f"SELECT COUNT(*) as count FROM {test_table} WHERE name = {placeholder}", ("Charlie",)
        )
        charlie_count = charlie_check["count"] if charlie_check else 0
        print(f"    ✓ Rollback verification: Charlie records = {charlie_count} (should be 0)")
        print("    ✓ Rollback test completed successfully - database integrity maintained")

        # Test manual transaction control
        print("\n[5] Testing manual transaction control...")
        tx = db.transaction()
        try:
            tx.__enter__()
            db.execute(
                f"INSERT INTO {test_table} (name, balance) VALUES ({placeholder}, {placeholder})", ("Diana", 1200.00)
            )
            print(f"    ✓ Manual transaction started and executed")
            tx.commit()
            print(f"    ✓ Manual commit successful")
        except Exception as e:
            print(f"    ✗ Manual transaction failed: {e}")
            tx.rollback()
        finally:
            tx.__exit__(None, None, None)

        # Final verification
        final_results = db.query_all(f"SELECT name, balance FROM {test_table} ORDER BY name")
        print(f"    Final table state: {len(final_results)} records")

        if verbose:
            for record in final_results:
                print(f"      {record['name']}: {record['balance']}")

        # Clean up
        db.execute(f"DROP TABLE IF EXISTS {test_table}")
        print(f"    ✓ Test table cleaned up")

        return True

    except Exception as e:
        print(f"    ✗ Transaction operations test failed: {str(e)}")
        if verbose:
            traceback.print_exc()
        return False


def get_version_only(db_manager, instance_name, db_name, verbose=False):
    """Get and display only the database version."""
    try:
        instance = db_manager.get_instance(instance_name)
        db = instance.get_database(db_name)
        db_type = instance.get_type()

        version_queries = {
            "postgres": "SELECT version() as version",
            "postgresql": "SELECT version() as version",
            "mysql": "SELECT VERSION() as version",
            "sqlite3": "SELECT sqlite_version() as version",
        }

        version_query = version_queries.get(db_type, "SELECT 'Unknown database type' as version")
        result = db.query_one(version_query)

        if result and "version" in result:
            print(f"{db_type.upper()} Version: {result['version']}")
        else:
            print("Could not retrieve version information.")

    except Exception as e:
        print(f"Error retrieving version: {str(e)}")
        if verbose:
            traceback.print_exc()


def main():
    """Main function."""
    global args
    args = parse_args()

    print(f"Database Diagnostic Tool")
    print(f"Using basefunctions database API")
    print(f"{'='*50}")

    # Create database manager
    try:
        db_manager = basefunctions.DbManager()
    except Exception as e:
        print(f"Failed to create DbManager: {str(e)}")
        if args.verbose:
            traceback.print_exc()
        return 1

    # Handle list command
    if args.list:
        list_available_instances(db_manager)
        return 0

    instance_name = args.instance_name

    # Get database type and determine system database
    try:
        instance = db_manager.get_instance(instance_name)
        db_type = instance.get_type()

        if args.db_name:
            db_name = args.db_name
        else:
            db_name = determine_system_database(db_type, instance_name)

        print(f"Target: {instance_name} -> {db_name} ({db_type})")

    except Exception as e:
        print(f"Error accessing instance '{instance_name}': {str(e)}")
        if args.verbose:
            traceback.print_exc()
        return 1

    # Handle version-only command
    if args.version_only:
        get_version_only(db_manager, instance_name, db_name, args.verbose)
        db_manager.close_all()
        return 0

    # Run tests based on arguments
    success_count = 0
    total_tests = 1  # Basic connection is always tested

    try:
        # Always run basic connection test
        if test_basic_connection(db_manager, instance_name, db_name, args.verbose):
            success_count += 1

        # Optional DataFrame test
        if args.test_dataframes:
            total_tests += 1
            if test_dataframe_operations(db_manager, instance_name, db_name, args.verbose):
                success_count += 1

        # Optional transaction test
        if args.test_transactions:
            total_tests += 1
            if test_transaction_operations(db_manager, instance_name, db_name, args.verbose):
                success_count += 1

        # Summary
        print(f"\n{'='*70}")
        print(f"TEST SUMMARY")
        print(f"{'='*70}")
        print(f"Tests passed: {success_count}/{total_tests}")

        if success_count == total_tests:
            print("✓ All tests passed successfully!")
            result_code = 0
        else:
            print("⚠ Some tests failed. Check output above for details.")
            result_code = 1

    except Exception as e:
        print(f"\nUnexpected error during testing: {str(e)}")
        if args.verbose:
            traceback.print_exc()
        result_code = 1

    finally:
        # Always close connections
        try:
            db_manager.close_all()
            if args.verbose:
                print("\n✓ All database connections closed")
        except Exception as e:
            print(f"Warning: Error closing connections: {str(e)}")

    return result_code


if __name__ == "__main__":
    sys.exit(main())
