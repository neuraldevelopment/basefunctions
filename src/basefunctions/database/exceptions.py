"""
=============================================================================

  Licensed Materials, Property of neuraldevelopment , Munich

  Project : basefunctions

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  Exception classes for database operations

 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------

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


class DatabaseError(Exception):
    """
    Base class for all database-related exceptions.
    Subclasses should provide more specific error details.
    """

    pass


class QueryError(DatabaseError):
    """
    Error executing a database query.
    Raised when a SQL query fails to execute properly.
    """

    pass


class TransactionError(DatabaseError):
    """
    Error handling a database transaction.
    Raised for problems with begin, commit, or rollback.
    """

    pass


class DbConnectionError(DatabaseError):
    """
    Error establishing or maintaining a database connection.
    Raised when connecting to a database server fails.
    """

    pass


class ConfigurationError(DatabaseError):
    """
    Error in database configuration.
    Raised when required configuration values are missing or invalid.
    """

    pass


class DataFrameError(DatabaseError):
    """
    Error processing DataFrames with database operations.
    Raised when dataframe operations cannot be completed.
    """

    pass


class NoSuchDatabaseError(DatabaseError):
    """
    Requested database does not exist.
    Raised when trying to access a database that is not available.
    """

    pass


class NoSuchTableError(DatabaseError):
    """
    Requested table does not exist.
    Raised when trying to access a table that is not available.
    """

    pass


class AuthenticationError(DbConnectionError):
    """
    Authentication to the database failed.
    Raised when credentials are invalid or insufficient.
    """

    pass


class ThreadPoolError(DatabaseError):
    """
    Error in asynchronous database operations.
    Raised when ThreadPool operations fail.
    """

    pass
