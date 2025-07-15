"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich

 Project : basefunctions

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 Comprehensive test suite for database exception hierarchy

 Log:
 v1.0 : Initial implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import pytest
from typing import Dict, Any
import sys
import os

# Add basefunctions to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from basefunctions.database.db_exceptions import (
    DbError,
    DbConnectionError,
    DbQueryError,
    DbTransactionError,
    DbConfigurationError,
    DbValidationError,
    DbResourceError,
    DbFactoryError,
    DbInstanceError,
    DbDataFrameError,
    DbSchemaError,
    DbAuthenticationError,
    DbTimeoutError,
    DbErrorCodes,
    create_connection_error,
    create_query_error,
    create_transaction_error,
    create_validation_error,
    create_resource_error,
)

# -------------------------------------------------------------
# TEST CLASS DEFINITIONS
# -------------------------------------------------------------


class TestDbError:
    """Test base DbError functionality."""

    def test_basic_initialization(self):
        """Test basic error initialization."""
        error = DbError("Test message")
        assert error.message == "Test message"
        assert error.error_code is None
        assert error.original_error is None

    def test_initialization_with_error_code(self):
        """Test error initialization with error code."""
        error = DbError("Test message", error_code="TEST_001")
        assert error.message == "Test message"
        assert error.error_code == "TEST_001"
        assert error.original_error is None

    def test_initialization_with_original_error(self):
        """Test error initialization with original exception."""
        original = ValueError("Original error")
        error = DbError("Test message", original_error=original)
        assert error.message == "Test message"
        assert error.original_error is original

    def test_str_without_error_code(self):
        """Test string representation without error code."""
        error = DbError("Test message")
        assert str(error) == "Test message"

    def test_str_with_error_code(self):
        """Test string representation with error code."""
        error = DbError("Test message", error_code="TEST_001")
        assert str(error) == "[TEST_001] Test message"

    def test_repr_without_error_code(self):
        """Test detailed representation without error code."""
        error = DbError("Test message")
        assert repr(error) == "DbError(message='Test message')"

    def test_repr_with_error_code(self):
        """Test detailed representation with error code."""
        error = DbError("Test message", error_code="TEST_001")
        assert repr(error) == "DbError(message='Test message', error_code='TEST_001')"


class TestDbConnectionError:
    """Test DbConnectionError functionality."""

    def test_basic_initialization(self):
        """Test basic connection error initialization."""
        error = DbConnectionError("Connection failed")
        assert error.message == "Connection failed"
        assert error.host is None
        assert error.port is None
        assert error.database is None

    def test_initialization_with_connection_details(self):
        """Test initialization with connection context."""
        error = DbConnectionError("Connection failed", host="localhost", port=5432, database="testdb")
        assert error.host == "localhost"
        assert error.port == 5432
        assert error.database == "testdb"

    def test_inheritance_from_db_error(self):
        """Test that DbConnectionError inherits from DbError."""
        error = DbConnectionError("Connection failed")
        assert isinstance(error, DbError)


class TestDbQueryError:
    """Test DbQueryError functionality."""

    def test_basic_initialization(self):
        """Test basic query error initialization."""
        error = DbQueryError("Query failed")
        assert error.message == "Query failed"
        assert error.query is None
        assert error.parameters is None
        assert error.table is None

    def test_initialization_with_query_context(self):
        """Test initialization with query context."""
        query = "SELECT * FROM users WHERE id = ?"
        params = (123,)
        error = DbQueryError("Query failed", query=query, parameters=params, table="users")
        assert error.query == query
        assert error.parameters == params
        assert error.table == "users"


class TestDbTransactionError:
    """Test DbTransactionError functionality."""

    def test_basic_initialization(self):
        """Test basic transaction error initialization."""
        error = DbTransactionError("Transaction failed")
        assert error.message == "Transaction failed"
        assert error.transaction_id is None

    def test_initialization_with_transaction_id(self):
        """Test initialization with transaction context."""
        error = DbTransactionError("Transaction failed", transaction_id="tx_12345")
        assert error.transaction_id == "tx_12345"


class TestDbConfigurationError:
    """Test DbConfigurationError functionality."""

    def test_basic_initialization(self):
        """Test basic configuration error initialization."""
        error = DbConfigurationError("Config error")
        assert error.message == "Config error"
        assert error.config_key is None
        assert error.config_value is None

    def test_initialization_with_config_context(self):
        """Test initialization with configuration context."""
        error = DbConfigurationError("Invalid config", config_key="database.host", config_value="invalid_host")
        assert error.config_key == "database.host"
        assert error.config_value == "invalid_host"


class TestDbValidationError:
    """Test DbValidationError functionality."""

    def test_basic_initialization(self):
        """Test basic validation error initialization."""
        error = DbValidationError("Validation failed")
        assert error.message == "Validation failed"
        assert error.parameter_name is None
        assert error.parameter_value is None
        assert error.expected_type is None

    def test_initialization_with_validation_context(self):
        """Test initialization with validation context."""
        error = DbValidationError(
            "Invalid parameter", parameter_name="port", parameter_value="invalid", expected_type=int
        )
        assert error.parameter_name == "port"
        assert error.parameter_value == "invalid"
        assert error.expected_type is int


class TestDbResourceError:
    """Test DbResourceError functionality."""

    def test_basic_initialization(self):
        """Test basic resource error initialization."""
        error = DbResourceError("Resource exhausted")
        assert error.message == "Resource exhausted"
        assert error.resource_type is None
        assert error.resource_limit is None

    def test_initialization_with_resource_context(self):
        """Test initialization with resource context."""
        error = DbResourceError("Pool exhausted", resource_type="connection_pool", resource_limit=10)
        assert error.resource_type == "connection_pool"
        assert error.resource_limit == 10


class TestDbFactoryError:
    """Test DbFactoryError functionality."""

    def test_basic_initialization(self):
        """Test basic factory error initialization."""
        error = DbFactoryError("Factory error")
        assert error.message == "Factory error"
        assert error.db_type is None
        assert error.connector_class is None

    def test_initialization_with_factory_context(self):
        """Test initialization with factory context."""
        error = DbFactoryError("Connector not found", db_type="oracle", connector_class="OracleConnector")
        assert error.db_type == "oracle"
        assert error.connector_class == "OracleConnector"


class TestDbInstanceError:
    """Test DbInstanceError functionality."""

    def test_basic_initialization(self):
        """Test basic instance error initialization."""
        error = DbInstanceError("Instance error")
        assert error.message == "Instance error"
        assert error.instance_name is None
        assert error.instance_type is None

    def test_initialization_with_instance_context(self):
        """Test initialization with instance context."""
        error = DbInstanceError("Instance not found", instance_name="db_001", instance_type="PostgreSQL")
        assert error.instance_name == "db_001"
        assert error.instance_type == "PostgreSQL"


class TestDbDataFrameError:
    """Test DbDataFrameError functionality."""

    def test_basic_initialization(self):
        """Test basic DataFrame error initialization."""
        error = DbDataFrameError("DataFrame error")
        assert error.message == "DataFrame error"
        assert error.operation is None
        assert error.table_name is None
        assert error.row_count is None

    def test_initialization_with_dataframe_context(self):
        """Test initialization with DataFrame context."""
        error = DbDataFrameError("Write failed", operation="write", table_name="users", row_count=1000)
        assert error.operation == "write"
        assert error.table_name == "users"
        assert error.row_count == 1000


class TestDbSchemaError:
    """Test DbSchemaError functionality."""

    def test_basic_initialization(self):
        """Test basic schema error initialization."""
        error = DbSchemaError("Schema error")
        assert error.message == "Schema error"
        assert error.schema_name is None
        assert error.table_name is None
        assert error.column_name is None

    def test_initialization_with_schema_context(self):
        """Test initialization with schema context."""
        error = DbSchemaError("Column not found", schema_name="public", table_name="users", column_name="email")
        assert error.schema_name == "public"
        assert error.table_name == "users"
        assert error.column_name == "email"


class TestDbAuthenticationError:
    """Test DbAuthenticationError functionality."""

    def test_basic_initialization(self):
        """Test basic authentication error initialization."""
        error = DbAuthenticationError("Auth failed")
        assert error.message == "Auth failed"
        assert error.username is None
        assert error.auth_method is None

    def test_initialization_with_auth_context(self):
        """Test initialization with authentication context."""
        error = DbAuthenticationError("Invalid credentials", username="testuser", auth_method="password")
        assert error.username == "testuser"
        assert error.auth_method == "password"


class TestDbTimeoutError:
    """Test DbTimeoutError functionality."""

    def test_basic_initialization(self):
        """Test basic timeout error initialization."""
        error = DbTimeoutError("Operation timeout")
        assert error.message == "Operation timeout"
        assert error.timeout_seconds is None
        assert error.operation is None

    def test_initialization_with_timeout_context(self):
        """Test initialization with timeout context."""
        error = DbTimeoutError("Query timeout", timeout_seconds=30, operation="SELECT")
        assert error.timeout_seconds == 30
        assert error.operation == "SELECT"


class TestDbErrorCodes:
    """Test DbErrorCodes constants."""

    def test_connection_error_codes(self):
        """Test connection error codes exist."""
        assert hasattr(DbErrorCodes, "CONNECTION_FAILED")
        assert hasattr(DbErrorCodes, "CONNECTION_LOST")
        assert hasattr(DbErrorCodes, "CONNECTION_TIMEOUT")

    def test_query_error_codes(self):
        """Test query error codes exist."""
        assert hasattr(DbErrorCodes, "QUERY_FAILED")
        assert hasattr(DbErrorCodes, "QUERY_SYNTAX_ERROR")
        assert hasattr(DbErrorCodes, "TABLE_NOT_FOUND")

    def test_transaction_error_codes(self):
        """Test transaction error codes exist."""
        assert hasattr(DbErrorCodes, "TRANSACTION_FAILED")
        assert hasattr(DbErrorCodes, "TRANSACTION_DEADLOCK")
        assert hasattr(DbErrorCodes, "TRANSACTION_ROLLBACK")


class TestFactoryFunctions:
    """Test exception factory functions."""

    def test_create_connection_error(self):
        """Test connection error factory."""
        error = create_connection_error("Connection failed", host="localhost", port=5432, database="testdb")
        assert isinstance(error, DbConnectionError)
        assert error.message == "Connection failed (host=localhost, port=5432, database=testdb)"
        assert error.host == "localhost"
        assert error.port == 5432
        assert error.database == "testdb"

    def test_create_query_error(self):
        """Test query error factory."""
        query = "SELECT * FROM users"
        error = create_query_error("Query failed", query=query, table="users")
        assert isinstance(error, DbQueryError)
        assert error.message == "Query failed (table: users)"
        assert error.query == query
        assert error.table == "users"

    def test_create_transaction_error(self):
        """Test transaction error factory."""
        error = create_transaction_error("Transaction failed", transaction_id="tx_123")
        assert isinstance(error, DbTransactionError)
        assert error.message == "Transaction failed (transaction: tx_123)"
        assert error.transaction_id == "tx_123"

    def test_create_validation_error(self):
        """Test validation error factory."""
        error = create_validation_error(
            "Validation failed", parameter_name="port", parameter_value="invalid", expected_type=int
        )
        assert isinstance(error, DbValidationError)
        assert error.message == "Validation failed (parameter: port, value: invalid, expected: int)"
        assert error.parameter_name == "port"
        assert error.parameter_value == "invalid"
        assert error.expected_type is int

    def test_create_resource_error(self):
        """Test resource error factory."""
        error = create_resource_error("Resource exhausted", resource_type="memory", resource_limit=1000)
        assert isinstance(error, DbResourceError)
        assert error.message == "Resource exhausted"
        assert error.resource_type == "memory"
        assert error.resource_limit == 1000
