"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment , Munich
  Project : basefunctions
  Copyright (c) by neuraldevelopment
  All rights reserved.
  Description:
  Tests for DbTransactionProxy context manager for database transactions
 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import pytest
from unittest.mock import MagicMock, patch, call
import basefunctions
from basefunctions.database.transaction import DbTransactionProxy

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


class TestDbTransactionProxy:
    """Test suite for the DbTransactionProxy class."""

    @pytest.fixture
    def mock_database(self):
        """Create a mock database object."""
        mock_db = MagicMock()
        mock_instance = MagicMock()
        mock_db.instance = mock_instance
        mock_db.db_name = "test_db"
        mock_db.logger = MagicMock()

        return mock_db

    @pytest.fixture
    def mock_transaction_manager(self):
        """Create a mock transaction context manager."""
        mock_manager = MagicMock()
        mock_manager.__enter__.return_value = mock_manager
        mock_manager.__exit__.return_value = False  # Don't suppress exceptions

        return mock_manager

    def test_init(self, mock_database, mock_transaction_manager):
        """Test initialization of DbTransactionProxy."""
        # Patch the get_logger function
        with patch("basefunctions.get_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            # Create proxy
            proxy = DbTransactionProxy(mock_database, mock_transaction_manager)

            # Verify attributes
            assert proxy.database is mock_database
            assert proxy.transaction_manager is mock_transaction_manager

            # Verify get_logger was called with the correct module name
            mock_get_logger.assert_called_once_with("basefunctions.database.transaction")

            # Verify logger is the mock returned by get_logger
            assert proxy.logger is mock_logger

    def test_enter_sqlite(self, mock_database, mock_transaction_manager):
        """Test __enter__ method for SQLite database."""
        # Setup SQLite database type
        mock_database.instance.get_type.return_value = "sqlite3"

        # Create proxy
        proxy = DbTransactionProxy(mock_database, mock_transaction_manager)

        # Call __enter__
        result = proxy.__enter__()

        # Verify result
        assert result is proxy

        # For SQLite, no need to set database context
        mock_transaction_manager.connector.execute.assert_not_called()

        # Verify transaction manager's __enter__ was called
        mock_transaction_manager.__enter__.assert_called_once()

    def test_enter_mysql(self, mock_database, mock_transaction_manager):
        """Test __enter__ method for MySQL database."""
        # Setup MySQL database type
        mock_database.instance.get_type.return_value = "mysql"

        # Create proxy
        proxy = DbTransactionProxy(mock_database, mock_transaction_manager)

        # Call __enter__
        result = proxy.__enter__()

        # Verify result
        assert result is proxy

        # Verify MySQL context was set
        mock_transaction_manager.connector.execute.assert_called_once_with("USE `test_db`")

        # Verify transaction manager's __enter__ was called
        mock_transaction_manager.__enter__.assert_called_once()

    def test_enter_postgres(self, mock_database, mock_transaction_manager):
        """Test __enter__ method for PostgreSQL database."""
        # Setup PostgreSQL database type
        mock_database.instance.get_type.return_value = "postgres"

        # Create proxy
        proxy = DbTransactionProxy(mock_database, mock_transaction_manager)

        # Call __enter__
        result = proxy.__enter__()

        # Verify result
        assert result is proxy

        # Verify PostgreSQL context was set
        mock_transaction_manager.connector.execute.assert_called_once_with(
            'SET search_path TO "test_db"'
        )

        # Verify transaction manager's __enter__ was called
        mock_transaction_manager.__enter__.assert_called_once()

    def test_enter_unknown_type(self, mock_database, mock_transaction_manager):
        """Test __enter__ method for unknown database type."""
        # Setup unknown database type
        mock_database.instance.get_type.return_value = "unknown"

        # Create proxy
        proxy = DbTransactionProxy(mock_database, mock_transaction_manager)

        # Call __enter__
        result = proxy.__enter__()

        # Verify result
        assert result is proxy

        # For unknown type, no context setting should happen
        mock_transaction_manager.connector.execute.assert_not_called()

        # Verify transaction manager's __enter__ was called
        mock_transaction_manager.__enter__.assert_called_once()

    def test_enter_db_context_error(self, mock_database, mock_transaction_manager):
        """Test __enter__ method when database context setting fails."""
        # Setup MySQL database type
        mock_database.instance.get_type.return_value = "mysql"

        # Setup error during context setting
        mock_transaction_manager.connector.execute.side_effect = Exception("Context error")

        # Patch the get_logger function
        with patch("basefunctions.get_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            # Create proxy
            proxy = DbTransactionProxy(mock_database, mock_transaction_manager)

            # Call __enter__ should propagate the error
            with pytest.raises(Exception) as excinfo:
                proxy.__enter__()

            # Verify error was propagated
            assert "Context error" in str(excinfo.value)

            # Verify logger critical was called on the proxy's logger (not database.logger)
            mock_logger.critical.assert_called_once()
            assert (
                "failed to set database context for transaction"
                in mock_logger.critical.call_args[0][0]
            )

    def test_exit_no_exception(self, mock_database, mock_transaction_manager):
        """Test __exit__ method with no exception."""
        # Create proxy
        proxy = DbTransactionProxy(mock_database, mock_transaction_manager)

        # Call __exit__ with no exception
        result = proxy.__exit__(None, None, None)

        # Verify result is from transaction manager's __exit__
        assert result == mock_transaction_manager.__exit__.return_value

        # Verify transaction manager's __exit__ was called with correct args
        mock_transaction_manager.__exit__.assert_called_once_with(None, None, None)

    def test_exit_with_exception(self, mock_database, mock_transaction_manager):
        """Test __exit__ method with an exception."""
        # Create proxy
        proxy = DbTransactionProxy(mock_database, mock_transaction_manager)

        # Create test exception
        exc_type = ValueError
        exc_val = ValueError("Test error")
        exc_tb = MagicMock()  # Mock traceback

        # Call __exit__ with exception
        result = proxy.__exit__(exc_type, exc_val, exc_tb)

        # Verify result is from transaction manager's __exit__
        assert result == mock_transaction_manager.__exit__.return_value

        # Verify transaction manager's __exit__ was called with correct args
        mock_transaction_manager.__exit__.assert_called_once_with(exc_type, exc_val, exc_tb)

    def test_exit_transaction_manager_returns_true(self, mock_database, mock_transaction_manager):
        """Test __exit__ when transaction manager's __exit__ returns True (suppressing exception)."""
        # Setup transaction manager to suppress exceptions
        mock_transaction_manager.__exit__.return_value = True

        # Create proxy
        proxy = DbTransactionProxy(mock_database, mock_transaction_manager)

        # Create test exception
        exc_type = ValueError
        exc_val = ValueError("Test error")
        exc_tb = MagicMock()  # Mock traceback

        # Call __exit__ with exception
        result = proxy.__exit__(exc_type, exc_val, exc_tb)

        # Verify result is True (exception suppressed)
        assert result is True

        # Verify transaction manager's __exit__ was called with correct args
        mock_transaction_manager.__exit__.assert_called_once_with(exc_type, exc_val, exc_tb)
