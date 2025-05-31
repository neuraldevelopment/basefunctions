"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich
  Project : database_debug_test
  Copyright (c) by neuraldevelopment
  All rights reserved.
  Description:
  Debug test to identify DataFrame persistence issues
 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import pandas as pd
import numpy as np
import basefunctions
import psycopg2

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


def create_simple_dataframe() -> pd.DataFrame:
    """Create a minimal test DataFrame."""
    data = {"id": [1, 2, 3], "name": ["Alice", "Bob", "Charlie"], "value": [100.5, 200.0, 300.25]}
    return pd.DataFrame(data)


def test_raw_postgresql_connection():
    """Test direct PostgreSQL connection to verify table existence."""
    try:
        # Direct psycopg2 connection
        conn = psycopg2.connect(
            host="localhost",
            port=2004,
            database="dev_test_db_postgres",
            user="postgres",  # Adjust as needed
            password="test",  # Adjust as needed
        )

        cursor = conn.cursor()

        # Check if test_users table exists
        cursor.execute(
            """
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'test_users'
            )
        """
        )

        table_exists = cursor.fetchone()[0]
        print(f"🔍 Raw PostgreSQL check - Table 'test_users' exists: {table_exists}")

        # List all tables
        cursor.execute(
            """
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """
        )

        tables = [row[0] for row in cursor.fetchall()]
        print(f"📋 All tables in database: {tables}")

        cursor.close()
        conn.close()

        return table_exists

    except Exception as e:
        print(f"❌ Raw PostgreSQL connection failed: {str(e)}")
        return False


def debug_dataframe_operations():
    """Debug DataFrame operations step by step."""
    print("🐛 Starting DataFrame Debug Test")
    print("=" * 50)

    # Step 1: Create test data
    df = create_simple_dataframe()
    print(f"✅ Created DataFrame:\n{df}")

    # Step 2: Setup database
    db_manager = basefunctions.DbManager()
    db_instance = db_manager.get_instance("dev_test_db_postgres")
    database = db_instance.get_database("dev_test_db_postgres")

    print(f"🔗 Database connection info: {database.get_connection_info()}")

    # Step 3: Check table before write
    print(f"\n📋 Before write:")
    print(f"  - Table exists (basefunctions): {database.table_exists('debug_test')}")
    test_raw_postgresql_connection()

    # Step 4: Write DataFrame with explicit transaction
    print(f"\n📝 Writing DataFrame with explicit transaction...")
    try:
        with database.transaction():
            database.write_dataframe(
                table_name="debug_test", df=df, cached=False, if_exists="replace"
            )
            print("  - DataFrame write completed within transaction")

            # Check within transaction
            print(f"  - Table exists within transaction: {database.table_exists('debug_test')}")

        print("✅ Transaction committed")

    except Exception as e:
        print(f"❌ Transaction failed: {str(e)}")

    # Step 5: Check table after write
    print(f"\n📋 After write:")
    print(f"  - Table exists (basefunctions): {database.table_exists('debug_test')}")
    table_exists_raw = test_raw_postgresql_connection()

    # Step 6: Try to read data
    if database.table_exists("debug_test"):
        print(f"\n📖 Reading data back...")
        try:
            result_df = database.query_to_dataframe("SELECT * FROM debug_test ORDER BY id")
            print(f"✅ Read {len(result_df)} rows:")
            print(result_df)
        except Exception as e:
            print(f"❌ Read failed: {str(e)}")

    # Step 7: Alternative write method - using main connector
    print(f"\n🔄 Testing alternative write method...")
    try:
        # Get the main connector and keep it alive
        connector = database.connector
        if not connector.is_connected():
            connector.connect()

        print(f"  - Connector info: {connector.get_connection_info()}")

        # Write using pandas to_sql directly
        connection = connector.get_connection()
        df.to_sql("debug_test_alt", connection, if_exists="replace", index=False)
        print("  - Alternative write completed")

        # Check immediately
        print(f"  - Alt table exists: {database.table_exists('debug_test_alt')}")

    except Exception as e:
        print(f"❌ Alternative write failed: {str(e)}")

    # Step 8: Final status check (no cleanup)
    print(f"\n📋 Final status:")
    print(f"  - debug_test exists (basefunctions): {database.table_exists('debug_test')}")
    print(f"  - debug_test_alt exists (basefunctions): {database.table_exists('debug_test_alt')}")
    test_raw_postgresql_connection()

    print(f"\n💡 Tables left in database for manual inspection:")
    print(f"  - debug_test")
    print(f"  - debug_test_alt")
    print(f"  - Connect manually to check: psql -h localhost -p 2004 -d dev_test_db_postgres")

    database.close()


if __name__ == "__main__":
    debug_dataframe_operations()
