"""
=============================================================================

  Licensed Materials, Property of neuraldevelopment , Munich

  Project : basefunctions

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  Tests for DbConnector abstract base class

 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import pytest
from unittest.mock import MagicMock, patch
from abc import ABC
import basefunctions
from basefunctions.database.db_connector import DbConnector, DatabaseParameters
from basefunctions.database.db_connector import (
    DatabaseError,
    QueryError,
    TransactionError,
)

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


class MockDbConnectorImplementation(DbConnector):
    """Concrete implementation of DbConnector for testing purposes."""

    def connect(self):
        """Implement abstract method connect."""
        self.connection = MagicMock()
        self.cursor = MagicMock()
        self.db_type = "test_db"

    def execute(self, query, parameters=()):
        """Implement abstract method execute."""
        self.last_query_string = query
        return self.cursor.execute(query, parameters)

    def fetch_one(self, query, parameters=(), new_query=False):
        """Implement abstract method fetch_one."""
        if new_query or self.last_query_string != query:
            self.execute(query, parameters)
        return self.cursor.fetchone()

    def fetch_all(self, query, parameters=()):
        """Implement abstract method fetch_all."""
        self.execute(query, parameters)
        return self.cursor.fetchall()

    def get_connection(self):
        """Implement abstract method get_connection."""
        return self.connection

    def begin_transaction(self):
        """Implement abstract method begin_transaction."""
        self.in_transaction = True

    def commit(self):
        """Implement abstract method commit."""
        self.in_transaction = False

    def rollback(self):
        """Implement abstract method rollback."""
        self.in_transaction = False

    def is_connected(self):
        """Implement abstract method is_connected."""
        return self.connection is not None

    def check_if_table_exists(self, table_name):
        """Implement abstract method check_if_table_exists."""
        return table_name in ["existing_table", "users", "logs"]


class TestDbConnector:
    """Test suite for the DbConnector abstract base class."""

    @pytest.fixture
    def connector(self):
        """Create a test connector instance."""
        params = {"database": "test_db", "user": "test_user", "password": "test_pass"}
        return MockDbConnectorImplementation(params)

    def test_abstract_class(self):
        """Test that DbConnector is an abstract class that cannot be instantiated directly."""
        with pytest.raises(TypeError):
            DbConnector({"database": "test_db"})

    def test_init(self, connector):
        """Test initialization of DbConnector object."""
        assert connector.parameters == {
            "database": "test_db",
            "user": "test_user",
            "password": "test_pass",
        }
        assert connector.connection is None
        assert connector.cursor is None
        assert connector.last_query_string is None
        assert connector.db_type is None
        assert connector.in_transaction is False

    def test_validate_parameters(self, connector):
        """Test parameter validation."""
        # Valid case - all required parameters present
        connector._validate_parameters(["database", "user"])

        # Invalid case - missing required parameter
        with pytest.raises(ValueError) as excinfo:
            connector._validate_parameters(["database", "user", "host", "port"])

        assert "missing required parameters" in str(excinfo.value)
        assert "host, port" in str(excinfo.value)

    def test_context_manager(self):
        """Test context manager functionality."""
        params = {"database": "test_db"}
        connector = MockDbConnectorImplementation(params)

        # Mock connect and close methods
        connector.connect = MagicMock()
        connector.close = MagicMock()

        # Use as context manager
        with connector as conn:
            assert conn is connector
            connector.connect.assert_called_once()

        # Should call close on exit
        connector.close.assert_called_once()

    def test_sql_replacement(self, connector):
        """Test SQL statement placeholder replacement."""
        # Set db_type for proper replacement
        connector.db_type = "sqlite3"

        sql = "CREATE TABLE users (id <PRIMARYKEY>, name TEXT)"
        replaced_sql = connector.replace_sql_statement(sql)

        assert replaced_sql == "CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)"

        # Test with different db_type
        connector.db_type = "mysql"
        replaced_sql = connector.replace_sql_statement(sql)

        assert replaced_sql == "CREATE TABLE users (id SERIAL AUTO_INCREMENT PRIMARY KEY, name TEXT)"

        # Test with PostgreSQL
        connector.db_type = "postgres"
        replaced_sql = connector.replace_sql_statement(sql)

        assert replaced_sql == "CREATE TABLE users (id BIGSERIAL PRIMARY KEY, name TEXT)"

    def test_get_primary_key_syntax(self, connector):
        """Test getting database-specific primary key syntax."""
        connector.db_type = "sqlite3"
        assert connector._get_primary_key_syntax() == "INTEGER PRIMARY KEY AUTOINCREMENT"

        connector.db_type = "mysql"
        assert connector._get_primary_key_syntax() == "SERIAL AUTO_INCREMENT PRIMARY KEY"

        connector.db_type = "postgres"
        assert connector._get_primary_key_syntax() == "BIGSERIAL PRIMARY KEY"

        # Test with unknown db_type
        connector.db_type = "unknown"
        assert connector._get_primary_key_syntax() == "BIGSERIAL PRIMARY KEY"  # Default

    def test_close(self, connector):
        """Test close method."""
        # Connect first
        connector.connect()

        # Store references to mocked objects before closing
        cursor = connector.cursor
        connection = connector.connection

        # Mock cursor and connection close methods
        cursor.close = MagicMock()
        connection.close = MagicMock()

        # Call close
        connector.close()

        # Verify both cursor and connection were closed
        cursor.close.assert_called_once()
        connection.close.assert_called_once()

        # Verify references are cleared
        assert connector.cursor is None
        assert connector.connection is None

    def test_transaction(self, connector):
        """Test transaction context manager."""
        with patch("basefunctions.TransactionContextManager") as mock_tcm:
            mock_tcm_instance = MagicMock()
            mock_tcm.return_value = mock_tcm_instance

            result = connector.transaction()

            # Verify TransactionContextManager was called with correct args
            mock_tcm.assert_called_once_with(connector)
            assert result is mock_tcm_instance

    def test_connection_error_handling(self, connector):
        """Test error handling during connection."""

        # Override connect to raise an exception
        def mock_connect_error():
            raise ConnectionRefusedError("Connection refused")

        connector.connect = mock_connect_error

        # Test context manager with connection error
        with pytest.raises(ConnectionRefusedError):
            with connector:
                pass  # Should not execute due to connection error
