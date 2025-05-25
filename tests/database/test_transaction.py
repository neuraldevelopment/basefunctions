"""
=============================================================================

 Licensed Materials, Property of neuraldevelopment , Munich

 Project : basefunctions

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 Tests for transaction context managers

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import pytest
from unittest.mock import MagicMock, patch, call
import basefunctions
from basefunctions import TransactionContextManager, DbTransactionProxy, TransactionError


# -------------------------------------------------------------
# FIXTURES
# -------------------------------------------------------------
@pytest.fixture
def mock_connector():
    """Create a mock database connector"""
    connector = MagicMock()
    connector.begin_transaction = MagicMock()
    connector.commit = MagicMock()
    connector.rollback = MagicMock()
    return connector


@pytest.fixture
def transaction_manager(mock_connector):
    """Create a transaction manager with mock connector"""
    return TransactionContextManager(mock_connector)


@pytest.fixture
def mock_database():
    """Create a mock Db object with mock instance"""
    db = MagicMock()
    db.db_name = "test_db"
    db.instance = MagicMock()
    db.instance.get_type = MagicMock(return_value="mysql")
    return db


# -------------------------------------------------------------
# TESTS FOR TransactionContextManager
# -------------------------------------------------------------
class TestTransactionContextManager:
    """Tests for transaction context manager functionality"""

    def test_enter(self, transaction_manager, mock_connector):
        """Test __enter__ method starts transaction"""
        result = transaction_manager.__enter__()

        # Verify transaction was started
        mock_connector.begin_transaction.assert_called_once()

        # Verify the context manager returned itself
        assert result is transaction_manager

    def test_exit_success(self, transaction_manager, mock_connector):
        """Test __exit__ method commits transaction on success"""
        # Call __exit__ with None for exception parameters (success case)
        transaction_manager.__exit__(None, None, None)

        # Verify commit was called
        mock_connector.commit.assert_called_once()
        mock_connector.rollback.assert_not_called()

    def test_exit_exception(self, transaction_manager, mock_connector):
        """Test __exit__ method rolls back transaction on exception"""
        # Call __exit__ with Exception parameters (failure case)
        exc_type = Exception
        exc_val = Exception("Test exception")
        exc_tb = None

        transaction_manager.__exit__(exc_type, exc_val, exc_tb)

        # Verify rollback was called
        mock_connector.rollback.assert_called_once()
        mock_connector.commit.assert_not_called()

    def test_context_manager_success(self, mock_connector):
        """Test normal usage of the context manager"""
        # Create transaction manager
        transaction_manager = TransactionContextManager(mock_connector)

        # Use in with statement
        with transaction_manager:
            # Simulate some database operations
            mock_connector.execute = MagicMock()
            mock_connector.execute("INSERT INTO test VALUES (1)")

        # Verify the correct methods were called
        mock_connector.begin_transaction.assert_called_once()
        mock_connector.commit.assert_called_once()
        mock_connector.rollback.assert_not_called()

    def test_context_manager_exception(self, mock_connector):
        """Test context manager with exception"""
        # Create transaction manager
        transaction_manager = TransactionContextManager(mock_connector)

        # Use in with statement with exception
        with pytest.raises(ValueError):
            with transaction_manager:
                # Simulate an exception during database operations
                raise ValueError("Test exception")

        # Verify the correct methods were called
        mock_connector.begin_transaction.assert_called_once()
        mock_connector.rollback.assert_called_once()
        mock_connector.commit.assert_not_called()

    def test_exception_propagation(self, mock_connector):
        """Test that exceptions are properly propagated"""
        # Create transaction manager
        transaction_manager = TransactionContextManager(mock_connector)

        # Define a specific exception to check propagation
        class CustomException(Exception):
            pass

        # Use in with statement with custom exception
        with pytest.raises(CustomException) as excinfo:
            with transaction_manager:
                raise CustomException("Custom test exception")

        # Verify the exception was propagated correctly
        assert str(excinfo.value) == "Custom test exception"
        mock_connector.rollback.assert_called_once()


# -------------------------------------------------------------
# TESTS FOR DbTransactionProxy
# -------------------------------------------------------------
class TestDbTransactionProxy:
    """Tests for database transaction proxy functionality"""

    def test_init(self, mock_database, transaction_manager):
        """Test initialization of transaction proxy"""
        proxy = DbTransactionProxy(mock_database, transaction_manager)

        assert proxy.database is mock_database
        assert proxy.transaction_manager is transaction_manager

    def test_enter_mysql(self, mock_database, transaction_manager):
        """Test __enter__ method for MySQL database"""
        # Setup MySQL database type
        mock_database.instance.get_type.return_value = "mysql"

        # Mock the transaction manager's __enter__ method
        transaction_manager.__enter__ = MagicMock()

        # Create transaction proxy
        proxy = DbTransactionProxy(mock_database, transaction_manager)

        # Call __enter__
        result = proxy.__enter__()

        # Verify the database context was set correctly
        transaction_manager.connector.execute.assert_called_once_with("USE `test_db`")

        # Verify the transaction was started
        transaction_manager.__enter__.assert_called_once()

        # Verify the proxy returned itself
        assert result is proxy

    def test_enter_postgres(self, mock_database, transaction_manager):
        """Test __enter__ method for PostgreSQL database"""
        # Setup PostgreSQL database type
        mock_database.instance.get_type.return_value = "postgres"

        # Mock the transaction manager's __enter__ method
        transaction_manager.__enter__ = MagicMock()

        # Create transaction proxy
        proxy = DbTransactionProxy(mock_database, transaction_manager)

        # Call __enter__
        proxy.__enter__()

        # Verify the database context was set correctly
        transaction_manager.connector.execute.assert_called_once_with(
            'SET search_path TO "test_db"'
        )

        # Verify the transaction was started
        transaction_manager.__enter__.assert_called_once()

    def test_enter_sqlite(self, mock_database, transaction_manager):
        """Test __enter__ method for SQLite database"""
        # Setup SQLite database type
        mock_database.instance.get_type.return_value = "sqlite3"

        # Mock the transaction manager's __enter__ method
        transaction_manager.__enter__ = MagicMock()

        # Create transaction proxy
        proxy = DbTransactionProxy(mock_database, transaction_manager)

        # Call __enter__
        proxy.__enter__()

        # Verify no database context was set (SQLite doesn't need USE statements)
        transaction_manager.connector.execute.assert_not_called()

        # Verify the transaction was started
        transaction_manager.__enter__.assert_called_once()

    def test_exit(self, mock_database, transaction_manager):
        """Test __exit__ method delegates to transaction manager"""
        # Create proxy
        proxy = DbTransactionProxy(mock_database, transaction_manager)

        # Mock the transaction manager's __exit__ method
        transaction_manager.__exit__ = MagicMock()

        # Call __exit__ with test parameters
        exc_type = ValueError
        exc_val = ValueError("Test exception")
        exc_tb = None

        proxy.__exit__(exc_type, exc_val, exc_tb)

        # Verify exit was delegated to transaction manager
        transaction_manager.__exit__.assert_called_once_with(exc_type, exc_val, exc_tb)

    def test_context_manager(self, mock_database, mock_connector):
        """Test usage as context manager"""
        # Create transaction manager with real implementation
        transaction_manager = TransactionContextManager(mock_connector)

        # Mock the transaction manager's methods
        transaction_manager.__enter__ = MagicMock()
        transaction_manager.__exit__ = MagicMock()

        # Create proxy
        proxy = DbTransactionProxy(mock_database, transaction_manager)

        # Use in with statement
        with proxy:
            # Simulate some database operations
            pass

        # For MySQL databases, check the order of method calls
        if mock_database.instance.get_type() == "mysql":
            # Verify execute was called with the correct database context
            mock_connector.execute.assert_called_with("USE `test_db`")

    def test_context_manager_exception_handling(self, mock_database, mock_connector):
        """Test context manager handles exceptions correctly"""
        # Create transaction manager
        transaction_manager = TransactionContextManager(mock_connector)

        # Use in with statement with exception
        with pytest.raises(ValueError):
            with DbTransactionProxy(mock_database, transaction_manager):
                raise ValueError("Test exception")

        # Verify rollback was called after exception
        mock_connector.rollback.assert_called_once()
