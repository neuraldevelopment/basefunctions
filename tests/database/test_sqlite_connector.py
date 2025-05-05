"""
=============================================================================

 Licensed Materials, Property of neuraldevelopment , Munich

 Project : backtraderfunctions

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 unit tests for mysql connector implementation

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import pytest
import mysql.connector
from unittest.mock import MagicMock, patch
import basefunctions
import sys

# -------------------------------------------------------------
# DEFINITIONS REGISTRY
# -------------------------------------------------------------

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------
TEST_PARAMS = {
    "user": "testuser",
    "password": "testpassword",
    "host": "localhost",
    "database": "testdb",
    "port": 3306,
}

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


@pytest.fixture
def mysql_connector():
    """create a mysql connector instance with test parameters"""
    return basefunctions.MySQLConnector(TEST_PARAMS)


@pytest.fixture
def mock_mysql_connection():
    """mock the mysql connection object"""
    mock_conn = MagicMock()
    mock_conn.is_connected.return_value = True
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    return mock_conn, mock_cursor


@patch("mysql.connector.connect")
def test_connect_success(mock_connect, mysql_connector):
    """test successful connection to mysql database"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_connect.return_value = mock_conn

    mysql_connector.connect()

    mock_connect.assert_called_once_with(
        user=TEST_PARAMS["user"],
        password=TEST_PARAMS["password"],
        host=TEST_PARAMS["host"],
        port=TEST_PARAMS["port"],
        database=TEST_PARAMS["database"],
    )
    assert mysql_connector.connection == mock_conn
    assert mysql_connector.cursor == mock_cursor


@patch("mysql.connector.connect")
def test_connect_failure(mock_connect, mysql_connector):
    """test failed connection to mysql database"""
    mock_connect.side_effect = Exception("Connection error")

    with pytest.raises(basefunctions.ConnectionError) as excinfo:
        mysql_connector.connect()

    assert "failed to connect to mysql database" in str(excinfo.value)


@patch.object(basefunctions.MySQLConnector, "is_connected")
@patch.object(basefunctions.MySQLConnector, "connect")
def test_execute_when_not_connected(mock_connect, mock_is_connected, mysql_connector):
    """test execute method when not connected"""
    mock_is_connected.return_value = False

    mysql_connector.connection = MagicMock()
    mysql_connector.cursor = MagicMock()

    query = "SELECT * FROM test"
    mysql_connector.execute(query)

    mock_connect.assert_called_once()
    mysql_connector.cursor.execute.assert_called_once_with(
        mysql_connector.replace_sql_statement(query), ()
    )
    mysql_connector.connection.commit.assert_called_once()


def test_execute_commit(mysql_connector):
    """test execute with commit"""
    mysql_connector.connection = MagicMock()
    mysql_connector.cursor = MagicMock()
    mysql_connector.is_connected = MagicMock(return_value=True)
    mysql_connector.in_transaction = False

    query = "INSERT INTO test VALUES (%s, %s)"
    params = (1, "test")

    mysql_connector.execute(query, params)

    mysql_connector.cursor.execute.assert_called_once_with(
        mysql_connector.replace_sql_statement(query), params
    )
    mysql_connector.connection.commit.assert_called_once()


def test_execute_in_transaction(mysql_connector):
    """test execute in transaction"""
    mysql_connector.connection = MagicMock()
    mysql_connector.cursor = MagicMock()
    mysql_connector.is_connected = MagicMock(return_value=True)
    mysql_connector.in_transaction = True

    query = "INSERT INTO test VALUES (%s, %s)"
    params = (1, "test")

    mysql_connector.execute(query, params)

    mysql_connector.cursor.execute.assert_called_once_with(
        mysql_connector.replace_sql_statement(query), params
    )
    mysql_connector.connection.commit.assert_not_called()


def test_execute_error(mysql_connector):
    """test execute with error"""
    mysql_connector.connection = MagicMock()
    mysql_connector.cursor = MagicMock()
    mysql_connector.is_connected = MagicMock(return_value=True)
    mysql_connector.in_transaction = False

    error_msg = "Query execution failed"
    mysql_connector.cursor.execute.side_effect = Exception(error_msg)

    with pytest.raises(basefunctions.QueryError) as excinfo:
        mysql_connector.execute("SELECT * FROM test")

    assert "failed to execute query" in str(excinfo.value)
    mysql_connector.connection.rollback.assert_called_once()


def test_fetch_one_success(mysql_connector):
    """test fetch_one successful retrieval"""
    mysql_connector.connection = MagicMock()
    mysql_connector.cursor = MagicMock()
    mysql_connector.is_connected = MagicMock(return_value=True)

    row_data = (1, "test_name")
    mysql_connector.cursor.fetchone.return_value = row_data
    mysql_connector.cursor.description = [
        ("id", None, None, None, None, None, None),
        ("name", None, None, None, None, None, None),
    ]

    query = "SELECT id, name FROM test WHERE id = %s"
    params = (1,)

    result = mysql_connector.fetch_one(query, params, True)

    mysql_connector.cursor.execute.assert_called_once_with(query, params)
    assert result == {"id": 1, "name": "test_name"}


def test_fetch_one_no_results(mysql_connector):
    """test fetch_one with no results"""
    mysql_connector.connection = MagicMock()
    mysql_connector.cursor = MagicMock()
    mysql_connector.is_connected = MagicMock(return_value=True)

    mysql_connector.cursor.fetchone.return_value = None

    query = "SELECT id, name FROM test WHERE id = %s"
    params = (999,)

    result = mysql_connector.fetch_one(query, params, True)

    assert result is None


def test_fetch_all_success(mysql_connector):
    """test fetch_all successful retrieval"""
    mysql_connector.connection = MagicMock()
    mysql_connector.cursor = MagicMock()
    mysql_connector.is_connected = MagicMock(return_value=True)

    rows_data = [(1, "name1"), (2, "name2")]
    mysql_connector.cursor.fetchall.return_value = rows_data
    mysql_connector.cursor.description = [
        ("id", None, None, None, None, None, None),
        ("name", None, None, None, None, None, None),
    ]

    query = "SELECT id, name FROM test"

    result = mysql_connector.fetch_all(query)

    mysql_connector.cursor.execute.assert_called_once_with(query, ())
    assert result == [{"id": 1, "name": "name1"}, {"id": 2, "name": "name2"}]


def test_transaction_management(mysql_connector):
    """test transaction management methods"""
    mysql_connector.connection = MagicMock()
    mysql_connector.is_connected = MagicMock(return_value=True)

    # Test begin_transaction
    mysql_connector.begin_transaction()
    mysql_connector.connection.start_transaction.assert_called_once()
    assert mysql_connector.in_transaction is True

    # Test commit
    mysql_connector.commit()
    mysql_connector.connection.commit.assert_called_once()
    assert mysql_connector.in_transaction is False

    # Test rollback
    mysql_connector.begin_transaction()  # Set in_transaction to True again
    mysql_connector.rollback()
    mysql_connector.connection.rollback.assert_called_once()
    assert mysql_connector.in_transaction is False


def test_is_connected(mysql_connector):
    """test is_connected method"""
    # Test when connection exists
    mock_conn = MagicMock()
    mock_conn.is_connected.return_value = True
    mysql_connector.connection = mock_conn

    assert mysql_connector.is_connected() is True

    # Test when connection exists but is closed
    mock_conn.is_connected.return_value = False
    assert mysql_connector.is_connected() is False

    # Test when connection doesn't exist
    mysql_connector.connection = None
    assert mysql_connector.is_connected() is False


def test_check_if_table_exists(mysql_connector):
    """test check_if_table_exists method"""
    mysql_connector.connection = MagicMock()
    mysql_connector.cursor = MagicMock()
    mysql_connector.is_connected = MagicMock(return_value=True)

    # Test table exists
    mysql_connector.cursor.fetchone.return_value = ["test_table"]
    assert mysql_connector.check_if_table_exists("test_table") is True

    # Test table doesn't exist
    mysql_connector.cursor.fetchone.return_value = None
    assert mysql_connector.check_if_table_exists("nonexistent_table") is False

    # Test query error
    mysql_connector.cursor.execute.side_effect = Exception("Query error")
    assert mysql_connector.check_if_table_exists("test_table") is False
