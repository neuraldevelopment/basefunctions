"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich
  Project : basefunctions
  Copyright (c) by neuraldevelopment
  All rights reserved.
  Description:
  Database transaction context manager for database operations
 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Optional, Any
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

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


class DbTransaction:
    """
    Context manager for database transactions.
    Provides automatic transaction management with commit/rollback handling.
    """

    def __init__(self, connector: "basefunctions.DbConnector") -> None:
        """
        Initialize database transaction context manager.

        parameters
        ----------
        connector : basefunctions.DbConnector
            database connector to manage transactions for
        """
        self.connector = connector
        self.logger = basefunctions.get_logger(__name__)
        self.transaction_started = False

    def __enter__(self) -> "DbTransaction":
        """
        Enter transaction context and begin transaction.

        returns
        -------
        DbTransaction
            self for use in with statement

        raises
        ------
        basefunctions.TransactionError
            if transaction cannot be started
        """
        try:
            self.connector.begin_transaction()
            self.transaction_started = True
            self.logger.debug("transaction started")
            return self
        except Exception as e:
            self.logger.critical(f"failed to start transaction: {str(e)}")
            raise basefunctions.TransactionError(f"failed to start transaction: {str(e)}") from e

    def __exit__(
        self, exc_type: Optional[type], exc_val: Optional[Exception], exc_tb: Optional[Any]
    ) -> bool:
        """
        Exit transaction context with automatic commit/rollback.

        parameters
        ----------
        exc_type : Optional[type]
            exception type if an exception was raised
        exc_val : Optional[Exception]
            exception value if an exception was raised
        exc_tb : Optional[Any]
            traceback if an exception was raised

        returns
        -------
        bool
            False to propagate exceptions
        """
        if not self.transaction_started:
            return False

        try:
            if exc_type is None:
                # No exception occurred, commit the transaction
                self.connector.commit()
                self.logger.debug("transaction committed successfully")
            else:
                # Exception occurred, rollback the transaction
                self.connector.rollback()
                self.logger.warning(
                    f"transaction rolled back due to {exc_type.__name__}: {exc_val}"
                )
        except Exception as e:
            # Error during commit/rollback
            self.logger.critical(f"error during transaction cleanup: {str(e)}")
            try:
                # Attempt rollback as last resort
                self.connector.rollback()
            except Exception as rollback_error:
                self.logger.critical(
                    f"failed to rollback after cleanup error: {str(rollback_error)}"
                )
        finally:
            self.transaction_started = False

        # Return False to propagate the original exception
        return False

    def commit(self) -> None:
        """
        Manually commit the transaction.

        raises
        ------
        basefunctions.TransactionError
            if commit fails or no transaction is active
        """
        if not self.transaction_started:
            raise basefunctions.TransactionError("no active transaction to commit")

        try:
            self.connector.commit()
            self.transaction_started = False
            self.logger.debug("transaction committed manually")
        except Exception as e:
            self.logger.critical(f"failed to commit transaction: {str(e)}")
            raise basefunctions.TransactionError(f"failed to commit transaction: {str(e)}") from e

    def rollback(self) -> None:
        """
        Manually rollback the transaction.

        raises
        ------
        basefunctions.TransactionError
            if rollback fails or no transaction is active
        """
        if not self.transaction_started:
            raise basefunctions.TransactionError("no active transaction to rollback")

        try:
            self.connector.rollback()
            self.transaction_started = False
            self.logger.debug("transaction rolled back manually")
        except Exception as e:
            self.logger.critical(f"failed to rollback transaction: {str(e)}")
            raise basefunctions.TransactionError(
                f"failed to rollback transaction: {str(e)}"
            ) from e

    def is_active(self) -> bool:
        """
        Check if transaction is currently active.

        returns
        -------
        bool
            True if transaction is active, False otherwise
        """
        return self.transaction_started
