"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich

 Project : basefunctions

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 Pytest test suite for DbConnector abstract base class

 Log:
 v1.0 : Initial implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import pytest
from unittest.mock import Mock, patch
from abc import ABC

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
# TYPE DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# EXCEPTION DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


class MockDbConnector(basefunctions.DbConnector):
    """Mock implementation of DbConnector for testing."""

    def connect(self):
        self.connection = Mock()
        self.cursor = Mock()

    def execute(self, query, parameters=()):
        pass

    def query_one(self, query, parameters=(), new_query=True):
        return {"id": 1, "name": "test"}

    def query_all(self, query, parameters=()):
        return [{"id": 1, "name": "test1"}, {"id": 2, "name": "test2"}]

    def get_connection(self):
        return self.connection

    def begin_transaction(self):
        self.in_transaction = True

    def commit(self):
        self.in_transaction = False

    def rollback(self):
        self.in_transaction = False

    def is_connected(self):
        return self.connection is not None

    def check_if_table_exists(self, table_name):
        return True

    def use_database(self, database_name):
        self.current_database = database_name

    def use_schema(self, schema_name):
        self.current_schema = schema_name

    def list_tables(self):
        return ["table1", "table2"]


class TestDbConnector:
    """Test suite for DbConnector abstract base class."""

    def setup_method(self):
        """Setup for each test method."""
        self.test_parameters = basefunctions.DatabaseParameters(
            host="localhost", port=5432, database="test_db", username="test_user", password="test_pass"
        )

    # =================================================================
    # INITIALIZATION TESTS
    # =================================================================

    def test_init_with_parameters(self):
        """Test initialization with database parameters."""
        connector = MockDbConnector(self.test_parameters)

        assert connector.parameters == self.test_parameters
        assert connector.connection is None
        assert connector.cursor is None
        assert connector.last_query_string is None
        assert connector.db_type is None
        assert connector.in_transaction is False
        assert connector.current_database is None
        assert connector.current_schema is None

    def test_init_sets_logger(self):
        """Test that logger is properly initialized."""
        connector = MockDbConnector(self.test_parameters)

        assert connector.logger is not None
        assert hasattr(connector, "registry")

    # =================================================================
    # CONTEXT MANAGER TESTS
    # =================================================================

    def test_context_manager_connects_and_disconnects(self):
        """Test context manager connects on enter and disconnects on exit."""
        connector = MockDbConnector(self.test_parameters)

        with (
            patch.object(connector, "connect") as mock_connect,
            patch.object(connector, "disconnect") as mock_disconnect,
            patch.object(connector, "is_connected", return_value=False),
        ):

            with connector:
                mock_connect.assert_called_once()

            mock_disconnect.assert_called_once()

    def test_context_manager_skips_connect_if_already_connected(self):
        """Test context manager skips connect if already connected."""
        connector = MockDbConnector(self.test_parameters)

        with (
            patch.object(connector, "connect") as mock_connect,
            patch.object(connector, "disconnect") as mock_disconnect,
            patch.object(connector, "is_connected", return_value=True),
        ):

            with connector:
                mock_connect.assert_not_called()

            mock_disconnect.assert_called_once()

    def test_context_manager_returns_self(self):
        """Test context manager returns self."""
        connector = MockDbConnector(self.test_parameters)

        with patch.object(connector, "is_connected", return_value=True):
            with connector as ctx:
                assert ctx is connector

    def test_context_manager_propagates_exceptions(self):
        """Test context manager propagates exceptions and still disconnects."""
        connector = MockDbConnector(self.test_parameters)

        with (
            patch.object(connector, "disconnect") as mock_disconnect,
            patch.object(connector, "is_connected", return_value=True),
        ):

            with pytest.raises(ValueError):
                with connector:
                    raise ValueError("test error")

            mock_disconnect.assert_called_once()

    # =================================================================
    # PARAMETER VALIDATION TESTS
    # =================================================================

    def test_validate_parameters_success(self):
        """Test parameter validation with all required keys present."""
        connector = MockDbConnector(self.test_parameters)
        required_keys = ["host", "port", "database"]

        # Should not raise exception
        connector._validate_parameters(required_keys)

    def test_validate_parameters_missing_keys(self):
        """Test parameter validation raises error for missing keys."""
        connector = MockDbConnector(self.test_parameters)
        required_keys = ["host", "port", "missing_key"]

        with pytest.raises(basefunctions.DbValidationError, match="missing required parameters: missing_key"):
            connector._validate_parameters(required_keys)

    def test_validate_parameters_multiple_missing_keys(self):
        """Test parameter validation with multiple missing keys."""
        connector = MockDbConnector(self.test_parameters)
        required_keys = ["host", "missing1", "missing2"]

        with pytest.raises(basefunctions.DbValidationError, match="missing required parameters: missing1, missing2"):
            connector._validate_parameters(required_keys)

    def test_validate_parameters_empty_required_keys(self):
        """Test parameter validation with empty required keys list."""
        connector = MockDbConnector(self.test_parameters)

        # Should not raise exception
        connector._validate_parameters([])

    # =================================================================
    # DISCONNECT CLEANUP TESTS
    # =================================================================

    def test_disconnect_cleanup(self):
        """Test disconnect properly cleans up connection and cursor."""
        connector = MockDbConnector(self.test_parameters)
        mock_connection = Mock()
        mock_cursor = Mock()
        connector.connection = mock_connection
        connector.cursor = mock_cursor
        connector.current_database = "test_db"
        connector.current_schema = "test_schema"
        connector.in_transaction = True

        connector.disconnect()

        mock_connection.close.assert_called_once()
        mock_cursor.close.assert_called_once()
        assert connector.connection is None
        assert connector.cursor is None
        assert connector.current_database is None
        assert connector.current_schema is None
        assert connector.in_transaction is False

    def test_disconnect_handles_cursor_close_error(self):
        """Test disconnect handles cursor close errors gracefully."""
        connector = MockDbConnector(self.test_parameters)
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.close.side_effect = Exception("cursor close error")
        connector.connection = mock_connection
        connector.cursor = mock_cursor

        # Should not raise exception
        connector.disconnect()

        mock_cursor.close.assert_called_once()
        mock_connection.close.assert_called_once()

    def test_disconnect_handles_connection_close_error(self):
        """Test disconnect handles connection close errors gracefully."""
        connector = MockDbConnector(self.test_parameters)
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.close.side_effect = Exception("connection close error")
        connector.connection = mock_connection
        connector.cursor = mock_cursor

        # Should not raise exception
        connector.disconnect()

        mock_cursor.close.assert_called_once()
        mock_connection.close.assert_called_once()

    def test_disconnect_with_none_connection_and_cursor(self):
        """Test disconnect when connection and cursor are None."""
        connector = MockDbConnector(self.test_parameters)
        connector.connection = None
        connector.cursor = None

        # Should not raise exception
        connector.disconnect()

    # =================================================================
    # ABSTRACT BASE CLASS TESTS
    # =================================================================

    def test_cannot_instantiate_abstract_class(self):
        """Test that DbConnector cannot be instantiated directly."""
        with pytest.raises(TypeError):
            basefunctions.DbConnector(self.test_parameters)

    def test_abstract_methods_exist(self):
        """Test that all expected abstract methods exist."""
        abstract_methods = {
            "connect",
            "execute",
            "query_one",
            "query_all",
            "get_connection",
            "begin_transaction",
            "commit",
            "rollback",
            "is_connected",
            "check_if_table_exists",
            "use_database",
            "use_schema",
            "list_tables",
        }

        # Get abstract methods from the class
        actual_abstract_methods = basefunctions.DbConnector.__abstractmethods__

        assert abstract_methods.issubset(actual_abstract_methods)

    # =================================================================
    # MOCK IMPLEMENTATION TESTS
    # =================================================================

    def test_mock_connector_basic_functionality(self):
        """Test that mock connector implements all required methods."""
        connector = MockDbConnector(self.test_parameters)

        # Test connection methods
        connector.connect()
        assert connector.is_connected() is True

        # Test query methods
        result_one = connector.query_one("SELECT * FROM test")
        assert result_one == {"id": 1, "name": "test"}

        result_all = connector.query_all("SELECT * FROM test")
        assert len(result_all) == 2

        # Test transaction methods
        connector.begin_transaction()
        assert connector.in_transaction is True

        connector.commit()
        assert connector.in_transaction is False

        # Test database/schema methods
        connector.use_database("new_db")
        assert connector.current_database == "new_db"

        connector.use_schema("new_schema")
        assert connector.current_schema == "new_schema"

        # Test utility methods
        assert connector.check_if_table_exists("test_table") is True
        tables = connector.list_tables()
        assert "table1" in tables
        assert "table2" in tables
