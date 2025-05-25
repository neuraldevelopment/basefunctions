"""
=============================================================================

 Licensed Materials, Property of neuraldevelopment , Munich

 Project : basefunctions

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 Tests for Db class (database abstraction layer)

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import pytest
import pandas as pd
from unittest.mock import MagicMock, patch, PropertyMock
import basefunctions
from basefunctions.database.db import Db
from basefunctions.database.exceptions import QueryError, DbConnectionError

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


class TestDb:
    """Test suite for the Db class."""

    @pytest.fixture
    def mock_instance(self):
        """Create a mock DbInstance for testing."""
        mock_instance = MagicMock()
        mock_instance.instance_name = "test_instance"
        mock_instance.get_type.return_value = "sqlite3"
        mock_instance.is_connected.return_value = True
        mock_connector = MagicMock()
        mock_instance.get_connection.return_value = mock_connector
        return mock_instance

    @pytest.fixture
    def db(self, mock_instance):
        """Create a Db instance for testing."""
        return Db(mock_instance, "test_db")

    def test_init(self, db, mock_instance):
        """Test initialization of Db object."""
        assert db.instance == mock_instance
        assert db.db_name == "test_db"

        # Check that lock exists and has the expected methods
        assert hasattr(db, "lock")
        assert hasattr(db.lock, "acquire")
        assert hasattr(db.lock, "release")

        assert isinstance(db.dataframe_cache, dict)
        assert db.max_cache_size == 10
        assert db.last_query is None

    def test_execute(self, db, mock_instance):
        """Test execution of SQL query."""
        db.execute("SELECT * FROM test")

        # For SQLite, no need to set database context
        mock_instance.get_connection.return_value.execute.assert_called_once_with(
            "SELECT * FROM test", ()
        )
        assert db.last_query == "SELECT * FROM test"

    def test_execute_with_parameters(self, db, mock_instance):
        """Test execution of SQL query with parameters."""
        params = (1, "test")
        db.execute("SELECT * FROM test WHERE id = ? AND name = ?", params)

        mock_instance.get_connection.return_value.execute.assert_called_once_with(
            "SELECT * FROM test WHERE id = ? AND name = ?", params
        )

    def test_execute_mysql(self, mock_instance):
        """Test execution of SQL query for MySQL."""
        mock_instance.get_type.return_value = "mysql"
        db = Db(mock_instance, "test_db")

        db.execute("SELECT * FROM test")

        # For MySQL, should prefix with USE statement
        mock_instance.get_connection.return_value.execute.assert_called_once_with(
            "USE `test_db`; SELECT * FROM test", ()
        )

    def test_execute_postgres(self, mock_instance):
        """Test execution of SQL query for PostgreSQL."""
        mock_instance.get_type.return_value = "postgres"
        db = Db(mock_instance, "test_db")

        db.execute("SELECT * FROM test")

        # For PostgreSQL, should set search_path
        mock_instance.get_connection.return_value.execute.assert_called_once_with(
            'SET search_path TO "test_db"; SELECT * FROM test', ()
        )

    def test_query_one(self, db, mock_instance):
        """Test fetching a single row from database."""
        expected_result = {"id": 1, "name": "test"}
        mock_instance.get_connection.return_value.fetch_one.return_value = expected_result

        result = db.query_one("SELECT * FROM test WHERE id = 1")

        assert result == expected_result
        mock_instance.get_connection.return_value.fetch_one.assert_called_once()

    def test_query_all(self, db, mock_instance):
        """Test fetching all rows from database."""
        expected_results = [{"id": 1, "name": "test1"}, {"id": 2, "name": "test2"}]
        mock_instance.get_connection.return_value.fetch_all.return_value = expected_results

        results = db.query_all("SELECT * FROM test")

        assert results == expected_results
        mock_instance.get_connection.return_value.fetch_all.assert_called_once()

    def test_transaction(self, db, mock_instance):
        """Test transaction context manager."""
        mock_transaction = MagicMock()
        mock_instance.get_connection.return_value.transaction.return_value = mock_transaction

        with patch("basefunctions.DbTransactionProxy") as mock_proxy:
            transaction_result = db.transaction()

            mock_instance.get_connection.return_value.transaction.assert_called_once()
            mock_proxy.assert_called_once_with(db, mock_transaction)

    def test_table_exists(self, db, mock_instance):
        """Test checking if a table exists."""
        mock_instance.get_connection.return_value.check_if_table_exists.return_value = True

        assert db.table_exists("test_table") is True
        mock_instance.get_connection.return_value.check_if_table_exists.assert_called_once_with(
            "test_table"
        )

    def test_list_tables(self, db, mock_instance):
        """Test listing all tables in the database."""
        # Setup for SQLite
        expected_tables = ["table1", "table2"]

        # Mock the query_all method
        with patch.object(db, "query_all") as mock_query_all:
            mock_query_all.return_value = [{"name": "table1"}, {"name": "table2"}]

            tables = db.list_tables()

            assert tables == expected_tables
            mock_query_all.assert_called_once_with(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )

    def test_add_dataframe(self, db, mock_instance):
        """Test adding a DataFrame to a database table."""
        df = pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})
        mock_conn = mock_instance.get_connection.return_value.get_connection.return_value

        with patch.object(df, "to_sql") as mock_to_sql:
            db.add_dataframe("test_table", df)

            mock_to_sql.assert_called_once_with(
                "test_table", mock_conn, if_exists="append", index=False
            )

    def test_add_dataframe_cached(self, db):
        """Test adding a DataFrame to cache."""
        df = pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})

        db.add_dataframe("test_table", df, cached=True)

        assert "test_table" in db.dataframe_cache
        assert len(db.dataframe_cache["test_table"]) == 1
        pd.testing.assert_frame_equal(db.dataframe_cache["test_table"][0], df)

    def test_flush_dataframe_cache(self, db, mock_instance):
        """Test flushing the DataFrame cache."""
        df1 = pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})
        df2 = pd.DataFrame({"col1": [3, 4], "col2": ["c", "d"]})

        # Add DataFrames to cache
        db.dataframe_cache["test_table"] = [df1, df2]

        # Mock pandas concat
        with patch("pandas.concat") as mock_concat:
            mock_concat.return_value = pd.DataFrame(
                {"col1": [1, 2, 3, 4], "col2": ["a", "b", "c", "d"]}
            )

            # Mock to_sql
            mock_df = mock_concat.return_value
            with patch.object(mock_df, "to_sql") as mock_to_sql:
                db.flush_dataframe_cache("test_table")

                # Check that concat was called with the right frames
                mock_concat.assert_called_once()
                args, _ = mock_concat.call_args
                assert len(args[0]) == 2
                pd.testing.assert_frame_equal(args[0][0], df1)
                pd.testing.assert_frame_equal(args[0][1], df2)

                # Check that to_sql was called
                mock_to_sql.assert_called_once()

                # Check that the cache was cleared
                assert db.dataframe_cache["test_table"] == []

    def test_query_to_dataframe(self, db):
        """Test executing a query and returning the result as DataFrame."""
        query_results = [{"col1": 1, "col2": "a"}, {"col1": 2, "col2": "b"}]

        with patch.object(db, "query_all") as mock_query_all:
            mock_query_all.return_value = query_results

            # Mock pandas DataFrame constructor
            with patch("pandas.DataFrame") as mock_df_constructor:
                mock_df = MagicMock()
                mock_df_constructor.return_value = mock_df

                result = db.query_to_dataframe("SELECT * FROM test")

                mock_query_all.assert_called_once_with("SELECT * FROM test", ())
                mock_df_constructor.assert_called_once_with(query_results)
                assert result == mock_df

    def test_submit_async_query(self, db, mock_instance):
        """Test submitting a query for asynchronous execution."""
        # Setup mock threadpool
        mock_manager = MagicMock()
        mock_threadpool = MagicMock()
        mock_manager.get_threadpool.return_value = mock_threadpool
        mock_instance.get_manager.return_value = mock_manager

        # Mock threadpool submit_task
        mock_threadpool.submit_task.return_value = "task-123"

        task_id = db.submit_async_query("SELECT * FROM test", (1, 2))

        # Check that threadpool.submit_task was called with correct arguments
        mock_threadpool.submit_task.assert_called_once()
        args, kwargs = mock_threadpool.submit_task.call_args
        assert args[0] == "database_query"
        task_content = args[1]
        assert task_content["database"] == "test_db"
        assert task_content["instance_name"] == "test_instance"
        assert task_content["query"] == "SELECT * FROM test"
        assert task_content["parameters"] == (1, 2)

        # Check return value
        assert task_id == "task-123"

    def test_close(self, db):
        """Test closing the database connection."""
        # Setup mock dataframe cache with data
        df = pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})
        db.dataframe_cache["test_table"] = [df]
        db.last_query = "SELECT * FROM test"

        # Mock flush_dataframe_cache
        with patch.object(db, "flush_dataframe_cache") as mock_flush:
            db.close()

            # Check that flush_dataframe_cache was called
            mock_flush.assert_called_once_with("test_table")

            # Check that cache and last_query were cleared
            assert db.dataframe_cache == {}
            assert db.last_query is None
