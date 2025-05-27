"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich
  Project : database_example
  Copyright (c) by neuraldevelopment
  All rights reserved.
  Description:
  Enhanced debugging example for database connection issues with Event-System support
 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import basefunctions
import argparse
import sys
import time
import basefunctions


# -------------------------------------------------------------
# ARGUMENT PARSING
# -------------------------------------------------------------
def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Database connection diagnostic tool.")

    parser.add_argument(
        "instance_name",
        nargs="?",  # Make it optional
        default="dev_asset_db_postgres",  # Default value
        help="Name of the database instance to connect to",
    )

    parser.add_argument(
        "--list", "-l", action="store_true", help="List all available database instances"
    )

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
        "--async-test",
        "-a",
        action="store_true",
        help="Test asynchronous database operations using the new Event system",
    )

    parser.add_argument(
        "--eventbus-threads",
        type=int,
        default=3,
        help="Number of threads for EventBus (default: 3)",
    )

    parser.add_argument(
        "--eventbus-corelets",
        type=int,
        default=2,
        help="Number of corelet processes for EventBus (default: 2)",
    )

    return parser.parse_args()


# -------------------------------------------------------------
# UTILITY FUNCTIONS
# -------------------------------------------------------------
def list_available_instances(db_manager):
    """List all available database instances."""
    print("\n=== Available Database Instances ===\n")

    try:
        # Try to load configurations
        config_handler = basefunctions.ConfigHandler()
        config = config_handler.get_config()

        if "databases" in config:
            instances = config["databases"]
            if instances:
                print(f"Found {len(instances)} configured instances:")
                for idx, (name, details) in enumerate(instances.items(), 1):
                    db_type = details.get("type", "unknown")
                    host = details.get("connection", {}).get("host", "localhost")
                    port = details.get("ports", {}).get("db", "default")
                    print(f"{idx}. {name} ({db_type} on {host}:{port})")
            else:
                print("No database instances found in configuration.")
        else:
            print("No 'databases' section found in configuration.")

        print("\nUse: python db_diagnostic.py <instance_name> to connect to a specific instance.")
        print("Use: python db_diagnostic.py <instance_name> --async-test to test Event system.")
    except Exception as e:
        print(f"Error listing instances: {str(e)}")


def test_async_operations(db_manager, instance_name, db_name):
    """Test asynchronous database operations using the Event system."""
    print("\n" + "=" * 70)
    print("TESTING ASYNCHRONOUS DATABASE OPERATIONS")
    print("=" * 70)

    try:
        # Configure EventBus
        print("\nStep 1: Configuring EventBus...")
        args = parse_args()
        db_manager.configure_eventbus(
            num_threads=args.eventbus_threads, corelet_pool_size=args.eventbus_corelets
        )

        event_bus = db_manager.get_event_bus()
        if event_bus:
            print(f"EventBus configured successfully")
            stats = event_bus.get_stats()
            print(f"EventBus stats: {stats}")
        else:
            print("Failed to configure EventBus")
            return

        # Test async query
        print("\nStep 2: Testing async query...")

        def query_callback(success, result):
            if success:
                print(f"Async query completed successfully: {result}")
            else:
                print(f"Async query failed: {result}")

        # Get database instance and database
        instance = db_manager.get_instance(instance_name)
        db = instance.get_database(db_name)

        # Submit async query using the database object
        task_id = db.submit_async_query(
            query="SELECT 1 as test_value, 'async test' as message",
            query_type="all",
            callback=query_callback,
            execution_mode="thread",
        )
        print(f"Submitted async query with task ID: {task_id}")

        # Test async DataFrame operation
        print("\nStep 3: Testing async DataFrame operation...")

        def dataframe_callback(success, result):
            if success:
                print(f"Async DataFrame operation completed: {result}")
            else:
                print(f"Async DataFrame operation failed: {result}")

        task_id2 = db.submit_async_dataframe_operation(
            operation="query_to_dataframe",
            query="SELECT 1 as id, 'test' as name",
            callback=dataframe_callback,
            execution_mode="thread",
        )
        print(f"Submitted async DataFrame operation with task ID: {task_id2}")

        # Test transaction
        print("\nStep 4: Testing async transaction...")

        def transaction_callback(success, result):
            if success:
                print(f"Async transaction completed: {result}")
            else:
                print(f"Async transaction failed: {result}")

        transaction_queries = [
            {"query": "SELECT 1 as step1", "type": "all"},
            {"query": "SELECT 2 as step2", "type": "all"},
        ]

        task_id3 = db.submit_async_transaction(
            queries=transaction_queries, callback=transaction_callback
        )
        print(f"Submitted async transaction with task ID: {task_id3}")

        # Wait for operations to complete
        print("\nStep 5: Waiting for operations to complete...")
        completed = event_bus.wait_for_completion(timeout=10.0)
        if completed:
            print("All operations completed successfully")
        else:
            print("Some operations did not complete within timeout")

        # Get and display results
        print("\nStep 6: Collecting results...")
        results = event_bus.get_results()
        if isinstance(results, tuple):
            success_results, error_results = results
            print(f"Success results: {len(success_results)}")
            print(f"Error results: {len(error_results)}")

            for i, result in enumerate(success_results):
                print(f"Success {i+1}: {result}")

            for i, error in enumerate(error_results):
                print(f"Error {i+1}: {error}")
        else:
            print(f"Results: {results}")

        # Display final EventBus stats
        print("\nStep 7: Final EventBus statistics...")
        final_stats = event_bus.get_stats()
        print(f"Final EventBus stats: {final_stats}")

    except Exception as e:
        print(f"Error in async operations test: {str(e)}")
        import traceback

        traceback.print_exc()


# -------------------------------------------------------------
# MAIN FUNCTION
# -------------------------------------------------------------
def main():
    """Main function."""
    # Parse command line arguments
    args = parse_args()

    # Create database manager
    db_manager = basefunctions.DbManager()

    # If --list flag is provided, show available instances and exit
    if args.list:
        list_available_instances(db_manager)
        return

    # Get instance name from arguments
    instance_name = args.instance_name

    # Version-only mode
    if args.version_only:
        try:
            instance = db_manager.get_instance(instance_name)
            instance.connect()

            # Select appropriate database
            db_type = instance.get_type()
            if args.db_name:
                db_name = args.db_name
            else:
                if db_type == "postgres":
                    db_name = "postgres"
                elif db_type == "mysql":
                    db_name = "mysql"
                elif db_type == "sqlite3":
                    db_name = instance_name
                else:
                    db_name = "main"

            # Get database and version
            db = instance.get_database(db_name)

            version_queries = {
                "postgres": "SELECT version();",
                "mysql": "SELECT VERSION();",
                "sqlite3": "SELECT sqlite_version();",
            }

            version_query = version_queries.get(db_type, "SELECT 'Unknown database type'")
            result = db.query_one(version_query)

            if result:
                # Extract version value (handles different return formats)
                if isinstance(result, dict):
                    # Try common column names for version
                    for key in ["version", "VERSION", "sqlite_version", "version()", "VERSION()"]:
                        if key in result:
                            print(f"{db_type} Version: {result[key]}")
                            break
                    else:
                        # If none of the expected keys found, print the whole result
                        print(f"Version info: {result}")
                else:
                    print(f"Version info: {result}")
            else:
                print("Could not retrieve version information.")

            # Close all connections
            db_manager.close_all()
            return
        except Exception as e:
            print(f"Error retrieving version: {str(e)}")
            return

    # Determine database name for tests
    db_type = None
    db_name = None

    try:
        instance = db_manager.get_instance(instance_name)
        db_type = instance.get_type()

        if args.db_name:
            db_name = args.db_name
        else:
            if db_type == "postgres":
                db_name = "postgres"
            elif db_type == "mysql":
                db_name = "mysql"
            elif db_type == "sqlite3":
                db_name = instance_name
            else:
                db_name = "main"
    except Exception as e:
        print(f"Error determining database info: {str(e)}")
        return

    # Async test mode
    if args.async_test:
        test_async_operations(db_manager, instance_name, db_name)
        db_manager.close_all()
        return

    # Full diagnostic mode (original functionality)
    try:
        print("=" * 70)
        print(f"DETAILED CONNECTION DEBUGGING FOR: {instance_name}")
        print("=" * 70)

        # Get instance
        print("\nStep 1: Getting instance...")
        try:
            instance = db_manager.get_instance(instance_name)
            print(f"Instance object created: {instance}")
            print(f"Instance type: {type(instance).__name__}")
            print(f"Initial connection object: {instance.connection}")
            print(f"Initial connection status: {instance.is_connected()}")
        except basefunctions.DbConnectionError as e:
            print(f"Failed to get instance: {str(e)}")
            return
        except basefunctions.DatabaseError as e:
            print(f"Database error: {str(e)}")
            return
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return

        # Connect to instance with detailed tracing
        print("\nStep 2: Explicitly connecting to instance...")
        try:
            instance.connect()
            print(f"After connect() - Instance: {instance.instance_name}")
            print(f"After connect() - Connection object ID: {id(instance.connection)}")
            print(
                f"After connect() - Connection object type: {type(instance.connection).__name__}"
            )
            print(f"After connect() - Is instance connected: {instance.is_connected()}")
            print(
                f"After connect() - Is connection object available: {instance.connection is not None}"
            )
        except Exception as e:
            print(f"Connection failed: {str(e)}")
            return

        if instance.connection:
            print("\nStep 3: Inspecting connection object attributes...")
            print(
                f"Connection has is_connected method: {hasattr(instance.connection, 'is_connected')}"
            )
            if hasattr(instance.connection, "is_connected"):
                is_connected_result = instance.connection.is_connected()
                print(f"Connection.is_connected() result: {is_connected_result}")
                print(f"Type of is_connected() result: {type(is_connected_result).__name__}")

            print(f"Connection has connect method: {hasattr(instance.connection, 'connect')}")
            print(f"Connection has cursor: {hasattr(instance.connection, 'cursor')}")

            # Try to directly test the connection
            print("\nStep 4: Direct connection test...")
            try:
                # Generic approach using connector's methods directly
                if hasattr(instance.connection, "fetch_one"):
                    test_result = instance.connection.fetch_one("SELECT 1 AS test")
                    print(f"Test using connector's fetch_one(): {test_result}")
                    print("Direct test successful")
                # Try to access underlying connection
                elif hasattr(instance.connection, "connection"):
                    db_connection = instance.connection.connection
                    print(f"Found underlying connection of type: {type(db_connection).__name__}")

                    # Generic database-specific approach
                    db_type = instance.get_type()

                    # Handle different database types
                    if db_type == "postgres":
                        try:
                            cursor = db_connection.cursor()
                            cursor.execute("SELECT 1 AS test")
                            test_result = cursor.fetchone()
                            print(f"PostgreSQL test result: {test_result}")
                            cursor.close()
                        except AttributeError:
                            # Alternative approach for psycopg2
                            cursor = db_connection.cursor(cursor_factory=None)
                            cursor.execute("SELECT 1 AS test")
                            test_result = cursor.fetchone()
                            print(f"PostgreSQL test result (raw cursor): {test_result}")
                            cursor.close()
                    elif db_type == "mysql":
                        cursor = db_connection.cursor(dictionary=True)
                        cursor.execute("SELECT 1 AS test")
                        test_result = cursor.fetchone()
                        print(f"MySQL test result: {test_result}")
                        cursor.close()
                    elif db_type == "sqlite3":
                        cursor = db_connection.cursor()
                        cursor.execute("SELECT 1 AS test")
                        test_result = cursor.fetchone()
                        print(f"SQLite test result: {test_result}")
                        cursor.close()
                    else:
                        print(f"Unknown database type: {db_type}")

                    print("Direct test successful")
                else:
                    print("Connector has neither fetch_one method nor connection attribute")
                    print("Using generic approach with function attributes...")

                    # Very generic approach - inspect all attributes to find something usable
                    for attr_name in dir(instance.connection):
                        if attr_name.startswith("_"):
                            continue
                        attr = getattr(instance.connection, attr_name)
                        print(f"  - Found attribute: {attr_name} (type: {type(attr).__name__})")
            except Exception as e:
                print(f"Direct test failed: {str(e)}")
                import traceback

                traceback.print_exc()

        # Get database type
        print("\nStep 5: Checking database type...")
        db_type = instance.get_type()
        print(f"Database type: {db_type}")

        # Get database object with detailed tracing
        print("\nStep 6: Getting database object...")
        print(f"Before get_database() - Connection status: {instance.is_connected()}")
        print(f"Before get_database() - Connection object ID: {id(instance.connection)}")

        print(f"Using database name: {db_name}")
        db = instance.get_database(db_name)

        print(f"After get_database() - Connection status: {instance.is_connected()}")
        print(f"After get_database() - Connection object ID: {id(instance.connection)}")
        print(
            f"After get_database() - Is original connection preserved: {instance.connection is instance.get_connection()}"
        )

        # Execute a query with detailed tracing - use appropriate version query
        print("\nStep 7: Executing query...")
        print(f"Before query - Connection status: {instance.is_connected()}")

        version_queries = {
            "postgres": "SELECT version();",
            "mysql": "SELECT VERSION();",
            "sqlite3": "SELECT sqlite_version();",
        }

        version_query = version_queries.get(db_type, "SELECT 'Unknown database type'")
        result = db.query_one(version_query)

        print(f"After query - Connection status: {instance.is_connected()}")
        print(f"Query result: {result}")

        # Test connector-specific methods if available
        print("\nStep 8: Using connector-specific methods...")
        print(f"Before connector methods - Connection status: {instance.is_connected()}")

        connector = instance.get_connection()

        # Check for different connector-specific methods
        connector_methods = ["get_server_version", "get_database_size", "get_server_info"]

        for method_name in connector_methods:
            if hasattr(connector, method_name):
                try:
                    method = getattr(connector, method_name)
                    result = method()
                    print(f"{method_name}() result: {result}")
                except Exception as e:
                    print(f"Error calling {method_name}(): {str(e)}")

        print(f"After connector methods - Connection status: {instance.is_connected()}")

        # Check final connection state
        print("\nStep 9: Final connection check...")
        print(f"Final connection status: {instance.is_connected()}")
        print(f"Final connection object ID: {id(instance.connection)}")

    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback

        traceback.print_exc()
    finally:
        # Close all connections
        print("\nStep 10: Closing all connections...")
        db_manager.close_all()
        print("Connections closed")


# -------------------------------------------------------------
# SCRIPT ENTRY POINT
# -------------------------------------------------------------
if __name__ == "__main__":
    main()
