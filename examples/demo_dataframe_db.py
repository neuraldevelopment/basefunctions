"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich

  Project : basefunctions

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  DataFrame DB roundtrip test demo

  Log:
  v1.0 : Initial implementation
  v1.1 : Fixed index=False parameter for write operation
  v1.2 : Fixed EventResult API compatibility (attributes instead of dict keys)
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import pandas as pd
import basefunctions

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# LOGGING INITIALIZE
# -------------------------------------------------------------

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


@basefunctions.run("DataFrame DB Tests")
class DataFrameDbTests:
    """Test suite for DataFrame database operations."""

    def setup(self):
        """Initialize test environment."""
        print("=== Setting up DataFrame DB Tests ===")
        self.test_df = None
        self.df_db = None
        self.manager = None
        self.instance = None

    def teardown(self):
        """Clean up test environment."""
        print("=== Cleaning up DataFrame DB Tests ===")
        # Optional: Clean up test table
        try:
            if self.df_db:
                delete_event_id = self.df_db.delete("ohlcv_test")
                results = self.df_db.get_results()
                delete_result = results.get(delete_event_id)
                if delete_result and delete_result.success:
                    print("Test table cleaned up")
                else:
                    print(f"Cleanup warning: {delete_result.exception if delete_result else 'No result'}")
        except:
            pass

    @basefunctions.test("Database Connection")
    def test_database_connection(self):
        """Test database connection and prepare test database."""
        print("Testing database connection...")

        # Connection Verification
        try:
            self.manager = basefunctions.DbManager()
            self.instance = self.manager.get_instance("dev_test_postgres")

            if self.instance.is_reachable():
                print("Database Connection: CONNECTED")
            else:
                print("Database Connection: FAILED")
                raise Exception("Cannot connect to database")

        except Exception as e:
            print(f"Database Connection: FAILED - {str(e)}")
            raise

        # Database Preparation
        try:
            databases = self.instance.list_databases()
            if "dataframe_test" in databases:
                print("Database dataframe_test: EXISTS")
            else:
                print("Database dataframe_test: CREATING")
                self.instance.add_database("dataframe_test")
        except Exception as e:
            print(f"Database preparation failed: {str(e)}")
            raise

        # Initialize DataFrameDb
        self.df_db = basefunctions.DataFrameDb("dev_test_postgres", "dataframe_test")
        print("Database setup completed")

    @basefunctions.test("OHLC Generate and Write")
    def test_ohlc_generate_and_write(self):
        """Generate OHLC data and write to database."""
        print("Generating OHLC data and writing to database...")

        if self.df_db is None:
            raise Exception("Database not initialized - connection test must run first")

        # Generate test data
        generator = basefunctions.OHLCVGenerator(seed=42)
        self.test_df = generator.generate(
            ticker="AAPL.XETRA", start_date="2024-01-01", end_date="2024-01-30", initial_price=150.0
        )
        print(f"Generated DataFrame with {len(self.test_df)} rows, {len(self.test_df.columns)} columns")

        # Write Operation
        print(f"Writing DataFrame with {len(self.test_df)} rows...")
        try:
            write_event_id = self.df_db.write(self.test_df, "ohlcv_test", if_exists="replace", index=True)
            results = self.df_db.get_results()

            write_result = results.get(write_event_id)
            if write_result and write_result.success:
                print(f"Write successful: {write_result.data} rows written")
            else:
                error_msg = (
                    str(write_result.exception)
                    if write_result and write_result.exception
                    else (write_result.data if write_result else "No result received")
                )
                print(f"Write failed: {error_msg}")
                raise Exception(f"Write operation failed: {error_msg}")

        except Exception as e:
            print(f"Write operation failed: {str(e)}")
            raise

    @basefunctions.test("Read and Compare")
    def test_read_and_compare(self):
        """Read data from database and compare with original."""
        print("Reading data from database and comparing...")

        if self.df_db is None:
            raise Exception("Database not initialized")

        if self.test_df is None:
            raise Exception("Original DataFrame not available")

        # Read Operation
        print("Reading DataFrame from database...")
        try:
            read_event_id = self.df_db.read("ohlcv_test")
            results = self.df_db.get_results()

            read_result = results.get(read_event_id)
            if read_result and read_result.success:
                read_df = read_result.data
                print(f"Read successful: {len(read_df)} rows retrieved")
            else:
                error_msg = (
                    str(read_result.exception)
                    if read_result and read_result.exception
                    else (read_result.data if read_result else "No result received")
                )
                print(f"Read failed: {error_msg}")
                raise Exception(f"Read operation failed: {error_msg}")

        except Exception as e:
            print(f"Read operation failed: {str(e)}")
            raise

        # Verification
        print("Comparing original and read DataFrames...")
        try:
            # Set Date column as index for read DataFrame to match original structure
            if "Date" in read_df.columns:
                read_df = read_df.set_index("Date")
                read_df.index = pd.to_datetime(read_df.index).date
                read_df.index.name = "Date"

            # Compare shapes
            if self.test_df.shape == read_df.shape:
                print(f"Shape comparison: IDENTICAL ({self.test_df.shape})")
            else:
                error_msg = f"Shape comparison: DIFFERENT - Original: {self.test_df.shape}, Read: {read_df.shape}"
                print(error_msg)
                raise Exception(error_msg)

            # Compare columns
            if list(self.test_df.columns) == list(read_df.columns):
                print("Columns comparison: IDENTICAL")
            else:
                error_msg = f"Columns comparison: DIFFERENT - Original: {list(self.test_df.columns)}, Read: {list(read_df.columns)}"
                print(error_msg)
                raise Exception(error_msg)

            # Compare data content
            pd.testing.assert_frame_equal(self.test_df.reset_index(), read_df.reset_index(), check_dtype=False)
            print("DataFrame comparison: IDENTICAL")
            print("Complete roundtrip test PASSED")

        except AssertionError as e:
            error_msg = f"DataFrame comparison: DIFFERENT - {str(e)}"
            print(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            print(f"Comparison failed: {str(e)}")
            raise
