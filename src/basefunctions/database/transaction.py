"""
=============================================================================

  Licensed Materials, Property of neuraldevelopment , Munich

  Project : basefunctions

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  Transaction context managers for database operations

 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Any, Optional
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


class TransactionContextManager:
    """
    Context manager for database transactions.
    Ensures proper transaction handling with automatic commit/rollback.
    """

    def __init__(self, connector: "basefunctions.DbConnector") -> None:
        """
        Initialize transaction manager.

        parameters
        ----------
        connector : basefunctions.DbConnector
            database connector to use for transaction
        """
        self.connector = connector
        self.logger = basefunctions.get_logger(__name__)

    def __enter__(self) -> "TransactionContextManager":
        """
        Start transaction when entering context.

        returns
        -------
        TransactionContextManager
            self for use in with statement
        """
        self.connector.begin_transaction()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        """
        Commit or rollback transaction when exiting context based on exception state.

        parameters
        ----------
        exc_type : Any
            exception type if an exception was raised
        exc_val : Any
            exception value if an exception was raised
        exc_tb : Any
            traceback if an exception was raised

        returns
        -------
        bool
            False to propagate exceptions
        """
        if exc_type is None:
            # If no exception occurred, commit the transaction
            self.connector.commit()
        else:
            # If an exception occurred, rollback the transaction
            self.connector.rollback()
            self.logger.warning(f"transaction rolled back due to: {str(exc_val)}")
        return False  # Let exceptions propagate


class DbTransactionProxy:
    """
    Proxy for transaction context manager that handles database-specific logic.
    Used to ensure correct database selection during transactions.
    """

    def __init__(
        self, database: "basefunctions.Db", transaction_manager: TransactionContextManager
    ) -> None:
        """
        Initialize transaction proxy.

        parameters
        ----------
        database : basefunctions.Db
            database object that initiated the transaction
        transaction_manager : TransactionContextManager
            the underlying transaction manager
        """
        self.database = database
        self.transaction_manager = transaction_manager
        self.logger = basefunctions.get_logger(__name__)

    def __enter__(self) -> "DbTransactionProxy":
        """
        Start transaction when entering context.

        returns
        -------
        DbTransactionProxy
            self for use in with statement
        """
        # First prepare the database context (e.g., USE database)
        db_type = self.database.instance.get_type()
        if db_type != "sqlite3":  # SQLite doesn't need USE statements
            # Set the correct database context before entering transaction
            db_name = self.database.db_name
            try:
                if db_type == "mysql":
                    self.transaction_manager.connector.execute(f"USE `{db_name}`")
                elif db_type == "postgres":
                    self.transaction_manager.connector.execute(f'SET search_path TO "{db_name}"')
            except Exception as e:
                self.logger.critical(f"failed to set database context for transaction: {str(e)}")
                raise

        # Now enter the actual transaction
        self.transaction_manager.__enter__()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        """
        Commit or rollback transaction when exiting context.

        parameters
        ----------
        exc_type : Any
            exception type if an exception was raised
        exc_val : Any
            exception value if an exception was raised
        exc_tb : Any
            traceback if an exception was raised

        returns
        -------
        bool
            False to propagate exceptions
        """
        # Delegate to the underlying transaction manager
        return self.transaction_manager.__exit__(exc_type, exc_val, exc_tb)
