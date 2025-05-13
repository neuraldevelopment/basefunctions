"""
=============================================================================

 Licensed Materials, Property of neuraldevelopment , Munich

 Project : backtraderfunctions

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 unit tests for postgresql connector implementation

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import pytest
import psycopg2
from sqlalchemy import create_engine
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
    "port": 5432,
}

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


@pytest.fixture
def postgresql_connector():
    """create a postgresql connector instance with test parameters"""
    return basefunctions.PostgreSQLConnector(TEST_PARAMS)


@pytest.fixture
def mock_psycopg2_connection():
    """mock the psycopg2 connection object"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    return mock_conn, mock_cursor


def test_engine_creation(postgresql_connector):
    """test SQLAlchemy engine creation"""
    # Setze die Attribute direkt für den Test
    postgresql_connector.connection = MagicMock()
    postgresql_connector.cursor = MagicMock()
    postgresql_connector.engine = MagicMock()

    # Verify engine is set
    assert postgresql_connector.engine is not None

    # Test get_connection returns the engine
    connection = postgresql_connector.get_connection()
    assert connection == postgresql_connector.engine


def test_connect_failure(postgresql_connector):
    """test failed connection to postgresql database"""
    # Patchen der psycopg2.connect-Funktion innerhalb der Testfunktion
    with patch("psycopg2.connect") as mock_connect:
        mock_connect.side_effect = Exception("Connection error")

        with pytest.raises(ConnectionError) as excinfo:
            postgresql_connector.connect()

        assert "failed to connect to postgresql database" in str(excinfo.value)


@patch.object(basefunctions.PostgreSQLConnector, "is_connected")
@patch.object(basefunctions.PostgreSQLConnector, "connect")
def test_execute_when_not_connected(mock_connect, mock_is_connected, postgresql_connector):
    """test execute method when not connected"""
    mock_is_connected.return_value = False

    postgresql_connector.connection = MagicMock()
    postgresql_connector.cursor = MagicMock()

    query = "SELECT * FROM test"
    postgresql_connector.execute(query)

    mock_connect.assert_called_once()
    postgresql_connector.cursor.execute.assert_called_once_with(
        postgresql_connector.replace_sql_statement(query), ()
    )
    postgresql_connector.connection.commit.assert_called_once()


def test_execute_commit(postgresql_connector):
    """test execute with commit"""
    postgresql_connector.connection = MagicMock()
    postgresql_connector.cursor = MagicMock()
    postgresql_connector.is_connected = MagicMock(return_value=True)
    postgresql_connector.in_transaction = False

    query = "INSERT INTO test VALUES (%s, %s)"
    params = (1, "test")

    postgresql_connector.execute(query, params)

    postgresql_connector.cursor.execute.assert_called_once_with(
        postgresql_connector.replace_sql_statement(query), params
    )
    postgresql_connector.connection.commit.assert_called_once()


def test_execute_in_transaction(postgresql_connector):
    """test execute in transaction"""
    postgresql_connector.connection = MagicMock()
    postgresql_connector.cursor = MagicMock()
    postgresql_connector.is_connected = MagicMock(return_value=True)
    postgresql_connector.in_transaction = True

    query = "INSERT INTO test VALUES (%s, %s)"
    params = (1, "test")

    postgresql_connector.execute(query, params)

    postgresql_connector.cursor.execute.assert_called_once_with(
        postgresql_connector.replace_sql_statement(query), params
    )
    postgresql_connector.connection.commit.assert_not_called()


def test_execute_error(postgresql_connector):
    """test execute with error"""
    postgresql_connector.connection = MagicMock()
    postgresql_connector.cursor = MagicMock()
    postgresql_connector.is_connected = MagicMock(return_value=True)
    postgresql_connector.in_transaction = False

    error_msg = "Query execution failed"
    postgresql_connector.cursor.execute.side_effect = Exception(error_msg)

    with pytest.raises(basefunctions.QueryError) as excinfo:
        postgresql_connector.execute("SELECT * FROM test")

    assert "failed to execute query" in str(excinfo.value)
    postgresql_connector.connection.rollback.assert_called_once()


def test_fetch_one_success(postgresql_connector):
    """test fetch_one successful retrieval"""
    postgresql_connector.connection = MagicMock()
    postgresql_connector.cursor = MagicMock()
    postgresql_connector.is_connected = MagicMock(return_value=True)

    row_data = (1, "test_name")
    postgresql_connector.cursor.fetchone.return_value = row_data
    postgresql_connector.cursor.description = [
        ("id", None, None, None, None, None, None),
        ("name", None, None, None, None, None, None),
    ]

    query = "SELECT id, name FROM test WHERE id = %s"
    params = (1,)

    result = postgresql_connector.fetch_one(query, params, True)

    postgresql_connector.cursor.execute.assert_called_once_with(query, params)
    assert result == {"id": 1, "name": "test_name"}


def test_fetch_one_no_results(postgresql_connector):
    """test fetch_one with no results"""
    postgresql_connector.connection = MagicMock()
    postgresql_connector.cursor = MagicMock()
    postgresql_connector.is_connected = MagicMock(return_value=True)

    postgresql_connector.cursor.fetchone.return_value = None

    query = "SELECT id, name FROM test WHERE id = %s"
    params = (999,)

    result = postgresql_connector.fetch_one(query, params, True)

    assert result is None


def test_fetch_all_success(postgresql_connector):
    """test fetch_all successful retrieval"""
    postgresql_connector.connection = MagicMock()
    postgresql_connector.cursor = MagicMock()
    postgresql_connector.is_connected = MagicMock(return_value=True)

    rows_data = [(1, "name1"), (2, "name2")]
    postgresql_connector.cursor.fetchall.return_value = rows_data
    postgresql_connector.cursor.description = [
        ("id", None, None, None, None, None, None),
        ("name", None, None, None, None, None, None),
    ]

    query = "SELECT id, name FROM test"

    result = postgresql_connector.fetch_all(query)

    postgresql_connector.cursor.execute.assert_called_once_with(query, ())
    assert result == [{"id": 1, "name": "name1"}, {"id": 2, "name": "name2"}]


def test_get_connection(postgresql_connector):
    """test get_connection method returns engine when available"""
    # Test with engine available
    postgresql_connector.engine = MagicMock()
    postgresql_connector.connection = MagicMock()

    result = postgresql_connector.get_connection()
    assert result == postgresql_connector.engine

    # Test fallback to connection when engine is None
    postgresql_connector.engine = None
    result = postgresql_connector.get_connection()
    assert result == postgresql_connector.connection


def test_transaction_management(postgresql_connector):
    """test transaction management methods"""
    postgresql_connector.connection = MagicMock()
    postgresql_connector.is_connected = MagicMock(return_value=True)

    # Test begin_transaction
    postgresql_connector.begin_transaction()
    assert postgresql_connector.connection.autocommit is False
    assert postgresql_connector.in_transaction is True

    # Test commit
    postgresql_connector.commit()
    postgresql_connector.connection.commit.assert_called_once()
    assert postgresql_connector.in_transaction is False

    # Test rollback
    postgresql_connector.begin_transaction()  # Set in_transaction to True again
    postgresql_connector.rollback()
    postgresql_connector.connection.rollback.assert_called_once()
    assert postgresql_connector.in_transaction is False


def test_is_connected(postgresql_connector):
    """test is_connected method"""
    # Test when both connection and cursor exist
    postgresql_connector.connection = MagicMock()
    postgresql_connector.cursor = MagicMock()
    assert postgresql_connector.is_connected() is True

    # Test when connection exists but cursor is None
    postgresql_connector.connection = MagicMock()
    postgresql_connector.cursor = None
    assert postgresql_connector.is_connected() is False

    # Test when connection is None
    postgresql_connector.connection = None
    postgresql_connector.cursor = MagicMock()
    assert postgresql_connector.is_connected() is False


def test_check_if_table_exists(postgresql_connector):
    """test check_if_table_exists method"""
    postgresql_connector.connection = MagicMock()
    postgresql_connector.cursor = MagicMock()
    postgresql_connector.is_connected = MagicMock(return_value=True)

    # Test table exists
    postgresql_connector.cursor.fetchone.return_value = (True,)
    assert postgresql_connector.check_if_table_exists("test_table") is True

    # PostgreSQL query for checking table existence
    expected_query = "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name=%s);"
    postgresql_connector.cursor.execute.assert_called_with(expected_query, ("test_table",))

    # Test table doesn't exist
    postgresql_connector.cursor.fetchone.return_value = (False,)
    assert postgresql_connector.check_if_table_exists("nonexistent_table") is False

    # Test query error
    postgresql_connector.cursor.execute.side_effect = Exception("Query error")
    assert postgresql_connector.check_if_table_exists("test_table") is False


def test_postgresql_specific_features(postgresql_connector):
    """test postgresql-specific features like SQLAlchemy engine"""
    # Setze die Attribute direkt für den Test
    postgresql_connector.connection = MagicMock()
    postgresql_connector.engine = MagicMock()

    # Test SQLAlchemy engine access through get_connection
    assert postgresql_connector.get_connection() == postgresql_connector.engine

    # Test fallback to connection when engine is None
    postgresql_connector.engine = None
    assert postgresql_connector.get_connection() == postgresql_connector.connection
