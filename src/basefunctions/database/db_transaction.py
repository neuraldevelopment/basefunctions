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

        raises
        ------
        basefunctions.DbValidationError
            if connector is None
        """
        if not connector:
            raise basefunctions.DbValidationError("connector cannot be None")

        self.connector = connector
        self.logger = basefunctions.get_logger(__name__)
        self.transaction_started = False
        self.transaction_id = None

    def __enter__(self) -> "DbTransaction":
        """
        Enter transaction context and begin transaction.

        returns
        -------
        DbTransaction
            self for use in with statement

        raises
        ------
        basefunctions.DbTransactionError
            if transaction cannot be started
        """
        if self.transaction_started:
            raise basefunctions.DbTransactionError("transaction already started")

        try:
            self.connector.begin_transaction()
            self.transaction_started = True

            # Generate simple transaction ID for logging
            import time

            self.transaction_id = f"tx_{int(time.time() * 1000) % 1000000}"

            self.logger.debug(f"transaction started ({self.transaction_id})")
            return self
        except basefunctions.DbTransactionError:
            # Re-raise transaction errors as-is
            raise
        except Exception as e:
            self.logger.critical(f"failed to start transaction: {str(e)}")
            raise basefunctions.DbTransactionError(f"failed to start transaction: {str(e)}") from e

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
                self._commit_internal()
                self.logger.debug(f"transaction committed successfully ({self.transaction_id})")
            else:
                # Exception occurred, rollback the transaction
                self._rollback_internal()
                self.logger.warning(
                    f"transaction rolled back due to {exc_type.__name__}: {exc_val} ({self.transaction_id})"
                )
        except Exception as cleanup_error:
            # Error during commit/rollback
            self.logger.critical(
                f"error during transaction cleanup ({self.transaction_id}): {str(cleanup_error)}"
            )
            try:
                # Attempt rollback as last resort
                self._rollback_internal()
                self.logger.warning(f"emergency rollback attempted ({self.transaction_id})")
            except Exception as rollback_error:
                self.logger.critical(
                    f"failed to rollback after cleanup error ({self.transaction_id}): {str(rollback_error)}"
                )
        finally:
            self.transaction_started = False
            self.transaction_id = None

        # Return False to propagate the original exception
        return False

    def commit(self) -> None:
        """
        Manually commit the transaction.

        raises
        ------
        basefunctions.DbTransactionError
            if commit fails or no transaction is active
        """
        if not self.transaction_started:
            raise basefunctions.DbTransactionError("no active transaction to commit")

        try:
            self._commit_internal()
            self.transaction_started = False
            self.logger.debug(f"transaction committed manually ({self.transaction_id})")
            self.transaction_id = None
        except basefunctions.DbTransactionError:
            # Re-raise transaction errors as-is
            raise
        except Exception as e:
            self.logger.critical(f"failed to commit transaction ({self.transaction_id}): {str(e)}")
            raise basefunctions.DbTransactionError(
                f"failed to commit transaction: {str(e)}"
            ) from e

    def rollback(self) -> None:
        """
        Manually rollback the transaction.

        raises
        ------
        basefunctions.DbTransactionError
            if rollback fails or no transaction is active
        """
        if not self.transaction_started:
            raise basefunctions.DbTransactionError("no active transaction to rollback")

        try:
            self._rollback_internal()
            self.transaction_started = False
            self.logger.debug(f"transaction rolled back manually ({self.transaction_id})")
            self.transaction_id = None
        except basefunctions.DbTransactionError:
            # Re-raise transaction errors as-is
            raise
        except Exception as e:
            self.logger.critical(
                f"failed to rollback transaction ({self.transaction_id}): {str(e)}"
            )
            raise basefunctions.DbTransactionError(
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

    def get_transaction_id(self) -> Optional[str]:
        """
        Get the current transaction ID for logging purposes.

        returns
        -------
        Optional[str]
            transaction ID if active, None otherwise
        """
        return self.transaction_id if self.transaction_started else None

    def _commit_internal(self) -> None:
        """
        Internal commit method without state management.

        raises
        ------
        basefunctions.DbTransactionError
            if commit fails
        """
        if not self.connector:
            raise basefunctions.DbTransactionError("connector is not available")

        self.connector.commit()

    def _rollback_internal(self) -> None:
        """
        Internal rollback method without state management.

        raises
        ------
        basefunctions.DbTransactionError
            if rollback fails
        """
        if not self.connector:
            raise basefunctions.DbTransactionError("connector is not available")

        self.connector.rollback()

    def execute_in_transaction(self, operation_func, *args, **kwargs) -> Any:
        """
        Execute a function within this transaction context.
        If transaction is not active, starts one automatically.

        parameters
        ----------
        operation_func : callable
            function to execute within transaction
        *args
            positional arguments for the function
        **kwargs
            keyword arguments for the function

        returns
        -------
        Any
            result of the operation function

        raises
        ------
        basefunctions.DbTransactionError
            if transaction management fails
        basefunctions.DbValidationError
            if operation_func is not callable
        """
        if not callable(operation_func):
            raise basefunctions.DbValidationError("operation_func must be callable")

        if self.transaction_started:
            # Transaction already active, just execute
            try:
                return operation_func(*args, **kwargs)
            except Exception as e:
                self.logger.warning(
                    f"operation failed in active transaction ({self.transaction_id}): {str(e)}"
                )
                raise
        else:
            # Start transaction, execute, and commit/rollback
            with self:
                try:
                    result = operation_func(*args, **kwargs)
                    self.logger.debug(
                        f"operation completed successfully in transaction ({self.transaction_id})"
                    )
                    return result
                except Exception as e:
                    self.logger.warning(
                        f"operation failed, transaction will rollback ({self.transaction_id}): {str(e)}"
                    )
                    raise

    def __str__(self) -> str:
        """
        String representation for debugging.

        returns
        -------
        str
            transaction status string
        """
        status = "active" if self.transaction_started else "inactive"
        tx_id = f" ({self.transaction_id})" if self.transaction_id else ""
        connector_type = (
            getattr(self.connector, "db_type", "unknown") if self.connector else "none"
        )
        return f"DbTransaction[{status}, {connector_type}{tx_id}]"

    def __repr__(self) -> str:
        """
        Detailed representation for debugging.

        returns
        -------
        str
            detailed transaction information
        """
        return (
            f"DbTransaction("
            f"active={self.transaction_started}, "
            f"id={self.transaction_id}, "
            f"connector={type(self.connector).__name__ if self.connector else None}"
            f")"
        )
