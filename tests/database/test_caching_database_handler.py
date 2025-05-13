"""
=============================================================================

 Licensed Materials, Property of neuraldevelopment , Munich

 Project : backtraderfunctions

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 Tests for CachingDatabaseHandler class

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


class TestCachingDatabaseHandler:
    """tests for the caching database handler"""

    @pytest.fixture
    def handler(self):
        """fixture providing a caching database handler instance"""
        return basefunctions.CachingDatabaseHandler()

    @pytest.fixture
    def sample_df(self):
        """fixture providing a sample dataframe"""
        return pd.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})

    def test_init(self, handler):
        """test initialization of handler"""
        assert isinstance(handler, basefunctions.DatabaseHandler)
        assert handler.dataframe_cache == {}
        assert handler.logger is not None

    def test_add_dataframe(self, handler, sample_df):
        """test adding dataframe to cache"""
        # when
        handler.add_dataframe("test_conn", "test_table", sample_df)

        # then
        assert ("test_conn", "test_table") in handler.dataframe_cache
        assert len(handler.dataframe_cache[("test_conn", "test_table")]) == 1
        pd.testing.assert_frame_equal(
            handler.dataframe_cache[("test_conn", "test_table")][0], sample_df
        )

    def test_add_multiple_dataframes(self, handler, sample_df):
        """test adding multiple dataframes to same key"""
        # when
        handler.add_dataframe("test_conn", "test_table", sample_df)
        handler.add_dataframe("test_conn", "test_table", sample_df)

        # then
        assert len(handler.dataframe_cache[("test_conn", "test_table")]) == 2

    def test_get_cache_info(self, handler, sample_df):
        """test getting cache info"""
        # given
        handler.add_dataframe("conn1", "table1", sample_df)
        handler.add_dataframe("conn1", "table1", sample_df)
        handler.add_dataframe("conn2", "table2", sample_df)

        # when
        info = handler.get_cache_info()

        # then
        assert len(info) == 2
        assert info[("conn1", "table1")]["dataframes"] == 2
        assert info[("conn1", "table1")]["total_rows"] == 6
        assert info[("conn2", "table2")]["dataframes"] == 1
        assert info[("conn2", "table2")]["total_rows"] == 3

    def test_clear_cache_all(self, handler, sample_df):
        """test clearing entire cache"""
        # given
        handler.add_dataframe("conn1", "table1", sample_df)
        handler.add_dataframe("conn2", "table2", sample_df)

        # when
        handler.clear_cache()

        # then
        assert len(handler.dataframe_cache) == 0

    def test_clear_cache_specific_connector(self, handler, sample_df):
        """test clearing cache for specific connector"""
        # given
        handler.add_dataframe("conn1", "table1", sample_df)
        handler.add_dataframe("conn2", "table2", sample_df)

        # when
        handler.clear_cache(connector_id="conn1")

        # then
        assert ("conn1", "table1") not in handler.dataframe_cache
        assert ("conn2", "table2") in handler.dataframe_cache

    def test_clear_cache_specific_table(self, handler, sample_df):
        """test clearing cache for specific table"""
        # given
        handler.add_dataframe("conn1", "table1", sample_df)
        handler.add_dataframe("conn1", "table2", sample_df)

        # when
        handler.clear_cache(table_name="table1")

        # then
        assert ("conn1", "table1") not in handler.dataframe_cache
        assert ("conn1", "table2") in handler.dataframe_cache

    @patch("basefunctions.DatabaseHandler.get_connection")
    @patch("basefunctions.DatabaseHandler.transaction")
    @patch("pandas.DataFrame.to_sql")
    def test_flush_all(
        self, mock_to_sql, mock_transaction, mock_get_connection, handler, sample_df
    ):
        """test flushing all cache to database"""
        # given
        mock_conn = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_transaction_ctx = MagicMock()
        mock_transaction.return_value.__enter__.return_value = mock_transaction_ctx
        mock_transaction.return_value.__exit__.return_value = None

        handler.add_dataframe("conn1", "table1", sample_df)
        handler.add_dataframe("conn1", "table1", sample_df)
        handler.add_dataframe("conn2", "table2", sample_df)

        # when
        handler.flush()

        # then
        assert len(handler.dataframe_cache) == 0
        assert mock_transaction.call_count == 2
        assert mock_get_connection.call_count == 2
        assert mock_to_sql.call_count == 2
        # überprüfen der parameter für den ersten aufruf
        args1, kwargs1 = mock_to_sql.call_args_list[0]
        assert args1[0] in ["table1", "table2"]
        assert kwargs1["if_exists"] == "append"
        assert kwargs1["index"] == False

    @patch("basefunctions.DatabaseHandler.get_connection")
    @patch("basefunctions.DatabaseHandler.transaction")
    @patch("pandas.DataFrame.to_sql")
    def test_flush_specific_connector(
        self, mock_to_sql, mock_transaction, mock_get_connection, handler, sample_df
    ):
        """test flushing specific connector to database"""
        # given
        mock_conn = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_transaction_ctx = MagicMock()
        mock_transaction.return_value.__enter__.return_value = mock_transaction_ctx
        mock_transaction.return_value.__exit__.return_value = None

        handler.add_dataframe("conn1", "table1", sample_df)
        handler.add_dataframe("conn2", "table2", sample_df)

        # when
        handler.flush(connector_id="conn1")

        # then
        assert ("conn1", "table1") not in handler.dataframe_cache
        assert ("conn2", "table2") in handler.dataframe_cache
        assert mock_transaction.call_count == 1
        mock_transaction.assert_called_with("conn1")
        assert mock_to_sql.call_count == 1

    @patch("basefunctions.DatabaseHandler.get_connection")
    @patch("basefunctions.DatabaseHandler.transaction")
    @patch("pandas.DataFrame.to_sql")
    def test_flush_specific_table(
        self, mock_to_sql, mock_transaction, mock_get_connection, handler, sample_df
    ):
        """test flushing specific table to database"""
        # given
        mock_conn = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_transaction_ctx = MagicMock()
        mock_transaction.return_value.__enter__.return_value = mock_transaction_ctx
        mock_transaction.return_value.__exit__.return_value = None

        handler.add_dataframe("conn1", "table1", sample_df)
        handler.add_dataframe("conn1", "table2", sample_df)

        # when
        handler.flush(table_name="table1")

        # then
        assert ("conn1", "table1") not in handler.dataframe_cache
        assert ("conn1", "table2") in handler.dataframe_cache
        assert mock_to_sql.call_count == 1
        mock_to_sql.assert_called_once()

    @patch("basefunctions.ThreadPool")
    def test_init_with_threadpool(self, mock_threadpool):
        """test initialization with threadpool enabled"""
        # Setup mock
        mock_threadpool_instance = MagicMock()
        mock_threadpool.return_value = mock_threadpool_instance

        # when
        handler = basefunctions.CachingDatabaseHandler(use_threadpool=True)

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
        handler = basefunctions.CachingDatabaseHandler(use_threadpool=True)

        # then
        assert handler.use_threadpool is False
        assert handler.threadpool is None
        mock_logger.error.assert_called_once()
        assert "failed to initialize threadpool" in mock_logger.error.call_args[0][0]

    @patch("basefunctions.ThreadPool")
    @patch("pandas.concat")
    def test_flush_with_threadpool(self, mock_concat, mock_threadpool, handler, sample_df):
        """test flushing with threadpool enabled"""
        # Setup mocks
        mock_threadpool_instance = MagicMock()
        mock_threadpool.return_value = mock_threadpool_instance
        mock_concat.return_value = sample_df

        # Add dataframe to cache
        handler.add_dataframe("conn1", "table1", sample_df)

        # Enable threadpool manually for this test
        handler.use_threadpool = True
        handler.threadpool = mock_threadpool_instance

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
    def test_flush_with_threadpool_specific_connector(self, mock_threadpool, handler, sample_df):
        """test flushing specific connector with threadpool"""
        # Setup mock
        mock_threadpool_instance = MagicMock()
        mock_threadpool.return_value = mock_threadpool_instance

        # Add dataframes to cache
        handler.add_dataframe("conn1", "table1", sample_df)
        handler.add_dataframe("conn2", "table2", sample_df)

        # Enable threadpool manually for this test
        handler.use_threadpool = True
        handler.threadpool = mock_threadpool_instance

        # when
        handler.flush(connector_id="conn1")

        # then
        assert ("conn1", "table1") not in handler.dataframe_cache
        assert ("conn2", "table2") in handler.dataframe_cache
        mock_threadpool_instance.submit_task.assert_called_once()
        call_args = mock_threadpool_instance.submit_task.call_args[1]
        assert call_args["content"]["connector_id"] == "conn1"
