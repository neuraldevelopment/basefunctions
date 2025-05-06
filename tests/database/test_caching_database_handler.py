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
import os
import sys
import sqlite3
from unittest.mock import patch, MagicMock

# add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import basefunctions
from basefunctions import DatabaseParameters, SQLiteConnector

# -------------------------------------------------------------
# FIXTURES
# -------------------------------------------------------------


@pytest.fixture
def mock_db_connector():
    """create a mock database connector for testing"""
    params = DatabaseParameters(database=":memory:")
    connector = SQLiteConnector(params)
    connector.connect()

    # create a test table
    conn = connector.get_connection()
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE test_table (id INTEGER, name TEXT, value REAL)")
    conn.commit()

    return connector


@pytest.fixture
def caching_db_handler(mock_db_connector):
    """create a caching database handler with a registered connector"""
    from basefunctions import CachingDatabaseHandler

    handler = CachingDatabaseHandler()
    # mock the register_connector method to return our mock connector
    with patch.object(handler, "register_connector", return_value=mock_db_connector):
        handler.register_connector("test_db", "sqlite3", DatabaseParameters(database=":memory:"))

    return handler


@pytest.fixture
def sample_dataframes():
    """create sample dataframes for testing"""
    df1 = pd.DataFrame({"id": [1, 2, 3], "name": ["a", "b", "c"], "value": [1.1, 2.2, 3.3]})

    df2 = pd.DataFrame({"id": [4, 5], "name": ["d", "e"], "value": [4.4, 5.5]})

    return [df1, df2]


# -------------------------------------------------------------
# TESTS
# -------------------------------------------------------------


def test_add_dataframe(caching_db_handler, sample_dataframes):
    """test that dataframes are correctly added to the cache"""
    # add first dataframe
    caching_db_handler.add_dataframe("test_db", "test_table", sample_dataframes[0])

    # verify it's in the cache
    assert ("test_db", "test_table") in caching_db_handler.dataframe_cache
    assert len(caching_db_handler.dataframe_cache[("test_db", "test_table")]) == 1

    # add second dataframe
    caching_db_handler.add_dataframe("test_db", "test_table", sample_dataframes[1])

    # verify both are in the cache
    assert len(caching_db_handler.dataframe_cache[("test_db", "test_table")]) == 2


def test_clear_cache(caching_db_handler, sample_dataframes):
    """test that cache clearing works correctly"""
    # add dataframes to cache
    caching_db_handler.add_dataframe("test_db", "test_table", sample_dataframes[0])
    caching_db_handler.add_dataframe("test_db", "other_table", sample_dataframes[1])

    # clear specific table
    caching_db_handler.clear_cache("test_db", "test_table")

    # verify only the specified entry was cleared
    assert ("test_db", "test_table") not in caching_db_handler.dataframe_cache
    assert ("test_db", "other_table") in caching_db_handler.dataframe_cache

    # clear all
    caching_db_handler.clear_cache()

    # verify everything was cleared
    assert len(caching_db_handler.dataframe_cache) == 0


def test_get_cache_info(caching_db_handler, sample_dataframes):
    """test that cache info is correctly reported"""
    # add dataframes to cache
    caching_db_handler.add_dataframe("test_db", "test_table", sample_dataframes[0])
    caching_db_handler.add_dataframe("test_db", "test_table", sample_dataframes[1])

    # get cache info
    info = caching_db_handler.get_cache_info()

    # verify info is correct
    assert ("test_db", "test_table") in info
    assert info[("test_db", "test_table")]["dataframes"] == 2
    assert info[("test_db", "test_table")]["total_rows"] == 5  # 3 + 2 rows


@patch("pandas.DataFrame.to_sql")
def test_flush(mock_to_sql, caching_db_handler, sample_dataframes, mock_db_connector):
    """test that flush correctly writes dataframes to the database"""
    # setup mock for transaction context manager
    with patch.object(mock_db_connector, "transaction") as mock_transaction:
        # setup mock context manager return value
        mock_cm = MagicMock()
        mock_transaction.return_value = mock_cm
        mock_cm.__enter__.return_value = None
        mock_cm.__exit__.return_value = None

        # add dataframes to cache
        caching_db_handler.add_dataframe("test_db", "test_table", sample_dataframes[0])
        caching_db_handler.add_dataframe("test_db", "test_table", sample_dataframes[1])

        # flush cache
        caching_db_handler.flush("test_db", "test_table")

        # verify to_sql was called with correct parameters
        mock_to_sql.assert_called_once()
        args, kwargs = mock_to_sql.call_args

        # first argument should be the table name
        assert args[0] == "test_table"

        # verify transaction was used
        mock_transaction.assert_called_once()

        # verify cache was cleared
        assert ("test_db", "test_table") not in caching_db_handler.dataframe_cache


@patch("pandas.DataFrame.to_sql")
def test_flush_all(mock_to_sql, caching_db_handler, sample_dataframes, mock_db_connector):
    """test that flush with no parameters flushes all cache entries"""
    # setup mock for transaction context manager
    with patch.object(mock_db_connector, "transaction") as mock_transaction:
        # setup mock context manager return value
        mock_cm = MagicMock()
        mock_transaction.return_value = mock_cm
        mock_cm.__enter__.return_value = None
        mock_cm.__exit__.return_value = None

        # add dataframes to different tables
        caching_db_handler.add_dataframe("test_db", "test_table", sample_dataframes[0])
        caching_db_handler.add_dataframe("test_db", "other_table", sample_dataframes[1])

        # flush all cache
        caching_db_handler.flush()

        # verify to_sql was called twice (once for each table)
        assert mock_to_sql.call_count == 2

        # verify cache was cleared
        assert len(caching_db_handler.dataframe_cache) == 0


def test_integration(caching_db_handler, sample_dataframes):
    """integration test with actual database operations"""
    # add dataframes to cache
    caching_db_handler.add_dataframe("test_db", "test_table", sample_dataframes[0])
    caching_db_handler.add_dataframe("test_db", "test_table", sample_dataframes[1])

    # flush cache to database
    caching_db_handler.flush()

    # verify data was written to database
    query = "SELECT COUNT(*) FROM test_table"
    result = caching_db_handler.fetch_one("test_db", query)

    # should have 5 rows (3 from df1 and 2 from df2)
    assert result[0] == 5
