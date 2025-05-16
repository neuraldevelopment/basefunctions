"""
=============================================================================

 Licensed Materials, Property of neuraldevelopment , Munich

 Project : basefunctions

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 Tests for DatabaseHandler class

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import pytest
import pandas as pd
import basefunctions
from unittest.mock import patch, MagicMock

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


class TestDatabaseHandler:
    """tests for the database handler"""

    @pytest.fixture
    def cached_handler(self):
        """fixture providing a database handler instance with caching enabled"""
        handler = basefunctions.DatabaseHandler(cached=True)
        # Mock the connector registration to avoid database connection
        params = MagicMock()
        handler.register_connector("conn1", "sqlite3", params)
        handler.register_connector("conn2", "sqlite3", params)
        return handler

    @pytest.fixture
    def non_cached_handler(self):
        """fixture providing a database handler instance with caching disabled"""
        handler = basefunctions.DatabaseHandler(cached=False)
        # Mock the connector registration to avoid database connection
        params = MagicMock()
        handler.register_connector("conn1", "sqlite3", params)
        handler.register_connector("conn2", "sqlite3", params)
        return handler

    @pytest.fixture
    def sample_df(self):
        """fixture providing a sample dataframe"""
        return pd.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})

    def test_init_cached(self, cached_handler):
        """test initialization of handler with caching enabled"""
        assert isinstance(cached_handler, basefunctions.BaseDatabaseHandler)
        assert cached_handler.cached is True
        assert cached_handler.use_threadpool is False
        assert cached_handler.dataframe_cache == {}
        assert cached_handler.logger is not None

    def test_init_non_cached(self, non_cached_handler):
        """test initialization of handler with caching disabled"""
        assert isinstance(non_cached_handler, basefunctions.BaseDatabaseHandler)
        assert non_cached_handler.cached is False
        assert non_cached_handler.use_threadpool is False

    def test_init_with_max_cache_size(self):
        """test initialization with custom max cache size"""
        handler = basefunctions.DatabaseHandler(cached=True, max_cache_size=5)
        assert handler.max_cache_size == 5

    def test_add_dataframe_cached(self, cached_handler, sample_df):
        """test adding dataframe to cache in cached mode"""
        # when
        cached_handler.add_dataframe("test_conn", "test_table", sample_df)

        # then
        assert ("test_conn", "test_table") in cached_handler.dataframe_cache
        assert len(cached_handler.dataframe_cache[("test_conn", "test_table")]) == 1
        pd.testing.assert_frame_equal(
            cached_handler.dataframe_cache[("test_conn", "test_table")][0], sample_df
        )

    @patch.object(basefunctions.DatabaseHandler, "_write_dataframe_direct_without_threadpool")
    def test_add_dataframe_non_cached(self, mock_write, non_cached_handler, sample_df):
        """test adding dataframe with caching disabled"""
        # when
        non_cached_handler.add_dataframe("test_conn", "test_table", sample_df)

        # then
        mock_write.assert_called_once_with("test_conn", "test_table", sample_df)
        assert (
            not hasattr(non_cached_handler, "dataframe_cache")
            or len(non_cached_handler.dataframe_cache) == 0
        )

    @patch.object(basefunctions.DatabaseHandler, "_write_dataframe_direct_with_threadpool")
    def test_add_dataframe_non_cached_with_threadpool(self, mock_write, sample_df):
        """test adding dataframe with caching disabled but threadpool enabled"""
        # given
        handler = basefunctions.DatabaseHandler(cached=False, use_threadpool=True)

        # when
        handler.add_dataframe("test_conn", "test_table", sample_df)

        # then
        mock_write.assert_called_once_with("test_conn", "test_table", sample_df)

    def test_add_multiple_dataframes_cached(self, cached_handler, sample_df):
        """test adding multiple dataframes to same key in cached mode"""
        # when
        cached_handler.add_dataframe("test_conn", "test_table", sample_df)
        cached_handler.add_dataframe("test_conn", "test_table", sample_df)

        # then
        assert len(cached_handler.dataframe_cache[("test_conn", "test_table")]) == 2

    def test_get_cache_info_cached(self, cached_handler, sample_df):
        """test getting cache info in cached mode"""
        # given
        cached_handler.add_dataframe("conn1", "table1", sample_df)
        cached_handler.add_dataframe("conn1", "table1", sample_df)
        cached_handler.add_dataframe("conn2", "table2", sample_df)

        # when
        info = cached_handler.get_cache_info()

        # then
        assert len(info) == 2
        assert info[("conn1", "table1")]["dataframes"] == 2
        assert info[("conn1", "table1")]["total_rows"] == 6
        assert info[("conn2", "table2")]["dataframes"] == 1
        assert info[("conn2", "table2")]["total_rows"] == 3

    def test_get_cache_info_non_cached(self, non_cached_handler):
        """test getting cache info in non-cached mode"""
        # when
        info = non_cached_handler.get_cache_info()

        # then
        assert info == {}

    def test_clear_cache_all_cached(self, cached_handler, sample_df):
        """test clearing entire cache in cached mode"""
        # given
        cached_handler.add_dataframe("conn1", "table1", sample_df)
        cached_handler.add_dataframe("conn2", "table2", sample_df)

        # when
        cached_handler.clear_cache()

        # then
        assert len(cached_handler.dataframe_cache) == 0

    def test_clear_cache_specific_connector_cached(self, cached_handler, sample_df):
        """test clearing cache for specific connector in cached mode"""
        # given
        cached_handler.add_dataframe("conn1", "table1", sample_df)
        cached_handler.add_dataframe("conn2", "table2", sample_df)

        # when
        cached_handler.clear_cache(connector_id="conn1")

        # then
        assert ("conn1", "table1") not in cached_handler.dataframe_cache
        assert ("conn2", "table2") in cached_handler.dataframe_cache

    def test_clear_cache_specific_table_cached(self, cached_handler, sample_df):
        """test clearing cache for specific table in cached mode"""
        # given
        cached_handler.add_dataframe("conn1", "table1", sample_df)
        cached_handler.add_dataframe("conn1", "table2", sample_df)

        # when
        cached_handler.clear_cache(table_name="table1")

        # then
        assert ("conn1", "table1") not in cached_handler.dataframe_cache
        assert ("conn1", "table2") in cached_handler.dataframe_cache

    def test_clear_cache_non_cached(self, non_cached_handler):
        """test clearing cache in non-cached mode does nothing"""
        # when/then - should not raise any exceptions
        non_cached_handler.clear_cache()

    @patch("basefunctions.BaseDatabaseHandler.get_connection")
    @patch("basefunctions.BaseDatabaseHandler.transaction")
    @patch("pandas.DataFrame.to_sql")
    def test_write_dataframe_direct_without_threadpool(
        self, mock_to_sql, mock_transaction, mock_get_connection, non_cached_handler, sample_df
    ):
        """test direct writing dataframe without threadpool"""
        # given
        mock_conn = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_transaction_ctx = MagicMock()
        mock_transaction.return_value.__enter__.return_value = mock_transaction_ctx
        mock_transaction.return_value.__exit__.return_value = None

        # when
        non_cached_handler._write_dataframe_direct_without_threadpool("conn1", "table1", sample_df)

        # then
        mock_transaction.assert_called_once_with("conn1")
        mock_get_connection.assert_called_once_with("conn1")
        mock_to_sql.assert_called_once()
        args, kwargs = mock_to_sql.call_args
        assert args[0] == "table1"
        assert kwargs["if_exists"] == "append"
        assert kwargs["index"] is False

    @patch("basefunctions.ThreadPool")
    def test_write_dataframe_direct_with_threadpool(self, mock_threadpool, sample_df):
        """test direct writing dataframe with threadpool"""
        # Setup mock
        mock_threadpool_instance = MagicMock()
        mock_threadpool.return_value = mock_threadpool_instance
        mock_threadpool_instance.submit_task.return_value = "task-id-123"

        # given
        handler = basefunctions.DatabaseHandler(cached=False, use_threadpool=True)
        handler.threadpool = mock_threadpool_instance

        # when
        task_id = handler._write_dataframe_direct_with_threadpool("conn1", "table1", sample_df)

        # then
        assert task_id == "task-id-123"
        mock_threadpool_instance.submit_task.assert_called_once()
        call_args = mock_threadpool_instance.submit_task.call_args[1]
        assert call_args["message_type"] == "flush_dataframe"
        assert call_args["content"]["connector_id"] == "conn1"
        assert call_args["content"]["table_name"] == "table1"
        assert call_args["content"]["dataframe"] is sample_df

    @patch("basefunctions.BaseDatabaseHandler.get_connection")
    @patch("basefunctions.BaseDatabaseHandler.transaction")
    @patch("pandas.DataFrame.to_sql")
    def test_flush_all_cached(
        self, mock_to_sql, mock_transaction, mock_get_connection, cached_handler, sample_df
    ):
        """test flushing all cache to database in cached mode"""
        # given
        mock_conn = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_transaction_ctx = MagicMock()
        mock_transaction.return_value.__enter__.return_value = mock_transaction_ctx
        mock_transaction.return_value.__exit__.return_value = None

        cached_handler.add_dataframe("conn1", "table1", sample_df)
        cached_handler.add_dataframe("conn1", "table1", sample_df)
        cached_handler.add_dataframe("conn2", "table2", sample_df)

        # when
        cached_handler.flush()

        # then
        assert len(cached_handler.dataframe_cache) == 0
        assert mock_transaction.call_count == 2
        assert mock_get_connection.call_count == 2
        assert mock_to_sql.call_count == 2
        # Check parameters for the first call
        args1, kwargs1 = mock_to_sql.call_args_list[0]
        assert args1[0] in ["table1", "table2"]
        assert kwargs1["if_exists"] == "append"
        assert kwargs1["index"] is False

    def test_flush_non_cached(self, non_cached_handler):
        """test flush does nothing in non-cached mode"""
        # when/then - should not raise any exceptions
        non_cached_handler.flush()

    @patch("basefunctions.BaseDatabaseHandler.get_connection")
    @patch("basefunctions.BaseDatabaseHandler.transaction")
    @patch("pandas.DataFrame.to_sql")
    def test_flush_specific_connector_cached(
        self, mock_to_sql, mock_transaction, mock_get_connection, cached_handler, sample_df
    ):
        """test flushing specific connector to database in cached mode"""
        # given
        mock_conn = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_transaction_ctx = MagicMock()
        mock_transaction.return_value.__enter__.return_value = mock_transaction_ctx
        mock_transaction.return_value.__exit__.return_value = None

        cached_handler.add_dataframe("conn1", "table1", sample_df)
        cached_handler.add_dataframe("conn2", "table2", sample_df)

        # when
        cached_handler.flush(connector_id="conn1")

        # then
        assert ("conn1", "table1") not in cached_handler.dataframe_cache
        assert ("conn2", "table2") in cached_handler.dataframe_cache
        assert mock_transaction.call_count == 1
        mock_transaction.assert_called_with("conn1")
        assert mock_to_sql.call_count == 1

    @patch("basefunctions.BaseDatabaseHandler.get_connection")
    @patch("basefunctions.BaseDatabaseHandler.transaction")
    @patch("pandas.DataFrame.to_sql")
    def test_flush_specific_table_cached(
        self, mock_to_sql, mock_transaction, mock_get_connection, cached_handler, sample_df
    ):
        """test flushing specific table to database in cached mode"""
        # given
        mock_conn = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_transaction_ctx = MagicMock()
        mock_transaction.return_value.__enter__.return_value = mock_transaction_ctx
        mock_transaction.return_value.__exit__.return_value = None

        cached_handler.add_dataframe("conn1", "table1", sample_df)
        cached_handler.add_dataframe("conn1", "table2", sample_df)

        # when
        cached_handler.flush(table_name="table1")

        # then
        assert ("conn1", "table1") not in cached_handler.dataframe_cache
        assert ("conn1", "table2") in cached_handler.dataframe_cache
        assert mock_to_sql.call_count == 1
        mock_to_sql.assert_called_once()

    @patch("basefunctions.ThreadPool")
    def test_init_with_threadpool(self, mock_threadpool):
        """test initialization with threadpool enabled"""
        # Setup mock
        mock_threadpool_instance = MagicMock()
        mock_threadpool.return_value = mock_threadpool_instance

        # when
        handler = basefunctions.DatabaseHandler(cached=True, use_threadpool=True)

        # Mock connectors to avoid db operations
        params = MagicMock()
        handler.register_connector("conn1", "sqlite3", params)

        # then
        assert handler.use_threadpool is True
        assert handler.threadpool is mock_threadpool_instance
        mock_threadpool_instance.register_handler.assert_called_once()
        assert mock_threadpool_instance.register_handler.call_args[0][0] == "flush_dataframe"
        assert mock_threadpool_instance.register_handler.call_args[0][2] == "thread"

    @patch("basefunctions.ThreadPool")
    @patch("basefunctions.get_logger")
    def test_init_threadpool_failure(self, mock_get_logger, mock_threadpool):
        """test handling of threadpool initialization failure"""
        # Setup mocks
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_threadpool.side_effect = Exception("ThreadPool error")

        # when
        handler = basefunctions.DatabaseHandler(cached=True, use_threadpool=True)

        # Mock connector registration
        params = MagicMock()
        handler.register_connector("conn1", "sqlite3", params)

        # then
        assert handler.use_threadpool is False
        assert handler.threadpool is None
        mock_logger.error.assert_called_once()
        assert "failed to initialize threadpool" in mock_logger.error.call_args[0][0]

    @patch("basefunctions.ThreadPool")
    @patch("pandas.concat")
    def test_flush_with_threadpool(self, mock_concat, mock_threadpool, sample_df):
        """test flushing with threadpool enabled"""
        # Setup mocks
        mock_threadpool_instance = MagicMock()
        mock_threadpool.return_value = mock_threadpool_instance
        mock_concat.return_value = sample_df

        # given
        handler = basefunctions.DatabaseHandler(cached=True, use_threadpool=True)
        handler.threadpool = mock_threadpool_instance

        # Mock connector registration
        params = MagicMock()
        handler.register_connector("conn1", "sqlite3", params)
        handler.register_connector("conn2", "sqlite3", params)

        # Add dataframe to cache
        handler.add_dataframe("conn1", "table1", sample_df)

        # when
        handler.flush()

        # then
        assert len(handler.dataframe_cache) == 0
        mock_threadpool_instance.submit_task.assert_called_once()
        call_args = mock_threadpool_instance.submit_task.call_args[1]
        assert call_args["message_type"] == "flush_dataframe"
        assert call_args["content"]["connector_id"] == "conn1"
        assert call_args["content"]["table_name"] == "table1"
        assert call_args["content"]["dataframe"] is sample_df

    @patch("basefunctions.ThreadPool")
    def test_flush_with_threadpool_specific_connector(self, mock_threadpool, sample_df):
        """test flushing specific connector with threadpool"""
        # Setup mock
        mock_threadpool_instance = MagicMock()
        mock_threadpool.return_value = mock_threadpool_instance

        # given
        handler = basefunctions.DatabaseHandler(cached=True, use_threadpool=True)
        handler.threadpool = mock_threadpool_instance

        # Mock connector registration
        params = MagicMock()
        handler.register_connector("conn1", "sqlite3", params)
        handler.register_connector("conn2", "sqlite3", params)

        # Add dataframes to cache
        handler.add_dataframe("conn1", "table1", sample_df)
        handler.add_dataframe("conn2", "table2", sample_df)

        # when
        handler.flush(connector_id="conn1")

        # then
        assert ("conn1", "table1") not in handler.dataframe_cache
        assert ("conn2", "table2") in handler.dataframe_cache
        mock_threadpool_instance.submit_task.assert_called_once()
        call_args = mock_threadpool_instance.submit_task.call_args[1]
        assert call_args["content"]["connector_id"] == "conn1"

    def test_check_cache_size(self, cached_handler, sample_df):
        """test cache size checking"""
        # given
        cached_handler.max_cache_size = 2
        key = ("conn1", "table1")

        # Patch the flush method to prevent actual flushing
        with patch.object(cached_handler, "flush"):
            # when/then - below limit
            cached_handler.add_dataframe("conn1", "table1", sample_df)
            assert cached_handler._check_cache_size(key) is False

            # when/then - at limit
            cached_handler.add_dataframe("conn1", "table1", sample_df)
            assert cached_handler._check_cache_size(key) is True

    @patch("basefunctions.DatabaseHandler.flush")
    def test_auto_flush_when_exceeding_max_cache_size(self, mock_flush, sample_df):
        """test auto-flushing when cache size exceeds limit"""
        # given
        handler = basefunctions.DatabaseHandler(cached=True, max_cache_size=2)

        # Mock connector registration
        params = MagicMock()
        handler.register_connector("conn1", "sqlite3", params)

        # Mock check_cache_size to return False then True
        with patch.object(handler, "_check_cache_size", side_effect=[False, True]):
            # when - add dataframes
            handler.add_dataframe("conn1", "table1", sample_df)
            assert mock_flush.call_count == 0

            # when - trigger flush
            handler.add_dataframe("conn1", "table1", sample_df)
            mock_flush.assert_called_once_with("conn1", "table1")
