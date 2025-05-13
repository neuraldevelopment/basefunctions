"""
=============================================================================

 Licensed Materials, Property of neuraldevelopment , Munich

 Project : backtraderfunctions

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 mysql-specific unit tests for database connector implementation

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import pytest
import mysql.connector
from unittest.mock import MagicMock, patch
import basefunctions

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
def test_mysql_connection_params(mock_connect, mysql_connector):
    """test that correct mysql-specific connection parameters are used"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_connect.return_value = mock_conn

    mysql_connector.connect()

    # verify mysql.connector.connect was called with correct parameters
    mock_connect.assert_called_once_with(
        user=TEST_PARAMS["user"],
        password=TEST_PARAMS["password"],
        host=TEST_PARAMS["host"],
        port=TEST_PARAMS["port"],
        database=TEST_PARAMS["database"],
    )

    # verify db_type is set correctly for mysql
    assert mysql_connector.db_type == "mysql"


def test_mysql_show_tables_query(mysql_connector):
    """test mysql-specific show tables query"""
    mysql_connector.connection = MagicMock()
    mysql_connector.cursor = MagicMock()
    mysql_connector.is_connected = MagicMock(return_value=True)

    table_name = "test_table"
    mysql_connector.check_if_table_exists(table_name)

    # verify the mysql-specific SHOW TABLES query was executed
    mysql_connector.cursor.execute.assert_called_once_with("SHOW TABLES LIKE %s;", (table_name,))


@patch.object(basefunctions.MySQLConnector, "is_connected")
@patch.object(basefunctions.MySQLConnector, "connect")
def test_mysql_transaction_methods(mock_connect, mock_is_connected, mysql_connector):
    """test mysql-specific transaction methods"""
    mock_is_connected.return_value = True

    mysql_connector.connection = MagicMock()

    # Test begin_transaction uses mysql's start_transaction
    mysql_connector.begin_transaction()
    mysql_connector.connection.start_transaction.assert_called_once()
    assert mysql_connector.in_transaction is True


@patch("mysql.connector.connect")
def test_mysql_cursor_description_for_columns(mock_connect, mysql_connector):
    """test handling of mysql cursor description for column names"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_connect.return_value = mock_conn

    # mysql cursor description format [(name, type_code, display_size, internal_size, precision, scale, null_ok), ...]
    mock_cursor.description = [
        ("id", 3, None, None, None, None, 0),  # INT
        ("name", 253, None, None, None, None, 0),  # VARCHAR
        ("price", 246, None, None, None, None, 1),  # DECIMAL, nullable
    ]
    mock_cursor.fetchone.return_value = (1, "Product A", 19.99)

    mysql_connector.connection = mock_conn
    mysql_connector.cursor = mock_cursor
    mysql_connector.is_connected = MagicMock(return_value=True)
    mysql_connector.last_query_string = "SELECT * FROM products WHERE id = 1"

    # Test fetch_one extracts columns correctly from mysql cursor description
    result = mysql_connector.fetch_one("SELECT * FROM products WHERE id = 1")

    assert result == {"id": 1, "name": "Product A", "price": 19.99}


def test_mysql_specific_error_handling(mysql_connector):
    """test handling of mysql-specific errors"""
    mysql_connector.connection = MagicMock()
    mysql_connector.cursor = MagicMock()
    mysql_connector.is_connected = MagicMock(return_value=True)

    # Simulate mysql.connector.Error (table doesn't exist)
    mysql_error = mysql.connector.Error(msg="Table 'testdb.nonexistent' doesn't exist")
    mysql_connector.cursor.execute.side_effect = mysql_error

    with pytest.raises(basefunctions.QueryError) as excinfo:
        mysql_connector.execute("SELECT * FROM nonexistent")

    assert "failed to execute query" in str(excinfo.value)
    assert "Table 'testdb.nonexistent' doesn't exist" in str(excinfo.value)


@patch("mysql.connector.connect")
def test_mysql_replace_sql_statement(mock_connect, mysql_connector):
    """test mysql-specific sql statement replacements"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_connect.return_value = mock_conn

    mysql_connector.connection = mock_conn
    mysql_connector.cursor = mock_cursor
    mysql_connector.is_connected = MagicMock(return_value=True)

    # Test execute with a query that might need MySQL-specific replacements
    query = "SELECT * FROM test LIMIT :limit OFFSET :offset"
    params = (10, 20)

    # Mock the replace_sql_statement method to simulate MySQL replacements
    mysql_connector.replace_sql_statement = MagicMock(
        return_value="SELECT * FROM test LIMIT %s OFFSET %s"
    )

    mysql_connector.execute(query, params)

    # Verify the SQL statement was replaced and executed with parameters
    mysql_connector.replace_sql_statement.assert_called_once_with(query)
    mysql_connector.cursor.execute.assert_called_once_with(
        "SELECT * FROM test LIMIT %s OFFSET %s", params
    )


def test_fetch_all_mysql_result_format(mysql_connector):
    """test fetch_all with mysql-specific result format"""
    mysql_connector.connection = MagicMock()
    mysql_connector.cursor = MagicMock()
    mysql_connector.is_connected = MagicMock(return_value=True)

    # MySQL cursor returns tuples for each row
    mysql_connector.cursor.fetchall.return_value = [
        (1, "Product A", 19.99),
        (2, "Product B", 29.99),
        (3, "Product C", 39.99),
    ]

    mysql_connector.cursor.description = [
        ("id", 3, None, None, None, None, 0),
        ("name", 253, None, None, None, None, 0),
        ("price", 246, None, None, None, None, 1),
    ]

    query = "SELECT id, name, price FROM products"

    result = mysql_connector.fetch_all(query)

    mysql_connector.cursor.execute.assert_called_once_with(query, ())
    assert len(result) == 3
    assert result[0] == {"id": 1, "name": "Product A", "price": 19.99}
    assert result[1] == {"id": 2, "name": "Product B", "price": 29.99}
    assert result[2] == {"id": 3, "name": "Product C", "price": 39.99}


@patch("mysql.connector.connect")
def test_mysql_connector_validation(mock_connect):
    """test validation of mysql-specific connection parameters"""
    # Missing required parameters
    incomplete_params = {
        "user": "testuser",
        "password": "testpassword",
        # missing host and database
    }

    connector = basefunctions.MySQLConnector(incomplete_params)

    with pytest.raises(ConnectionError) as excinfo:
        connector.connect()

    assert "missing required parameter" in str(excinfo.value).lower()


def test_mysql_query_with_last_query_caching(mysql_connector):
    """test mysql connector's query caching behavior with last_query_string"""
    mysql_connector.connection = MagicMock()
    mysql_connector.cursor = MagicMock()
    mysql_connector.is_connected = MagicMock(return_value=True)

    # Initial query execution
    query1 = "SELECT * FROM products WHERE id = %s"
    params1 = (1,)

    mysql_connector.last_query_string = ""
    mysql_connector.fetch_one(query1, params1, new_query=False)

    # Verify execute was called since it's a new query
    mysql_connector.cursor.execute.assert_called_once_with(query1, params1)
    mysql_connector.cursor.execute.reset_mock()

    # Same query, should not execute again
    mysql_connector.last_query_string = query1
    mysql_connector.fetch_one(query1, params1, new_query=False)

    # Verify execute was not called
    mysql_connector.cursor.execute.assert_not_called()

    # Force new query execution with new_query=True
    mysql_connector.fetch_one(query1, params1, new_query=True)

    # Verify execute was called again
    mysql_connector.cursor.execute.assert_called_once_with(query1, params1)
