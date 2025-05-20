"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment , Munich
  Project : basefunctions
  Copyright (c) by neuraldevelopment
  All rights reserved.
  Description:
  Tests for DbConnectionError exception class
 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import pytest
import basefunctions
from basefunctions.database.exceptions import DbConnectionError, DatabaseError

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


class TestDbConnectionError:
    """Test suite for the DbConnectionError exception class."""

    def test_instance(self):
        """Test that DbConnectionError can be instantiated."""
        error = DbConnectionError("Connection failed")
        assert isinstance(error, DbConnectionError)
        assert str(error) == "Connection failed"

    def test_inheritance(self):
        """Test that DbConnectionError inherits from DatabaseError."""
        error = DbConnectionError("Test inheritance")
        assert isinstance(error, DatabaseError)
        assert isinstance(error, Exception)

    def test_empty_message(self):
        """Test DbConnectionError with empty message."""
        error = DbConnectionError()
        assert str(error) == ""

    def test_catch_as_database_error(self):
        """Test that DbConnectionError can be caught as DatabaseError."""
        try:
            raise DbConnectionError("Test catch")
        except DatabaseError as e:
            assert isinstance(e, DbConnectionError)
            assert str(e) == "Test catch"

    def test_catch_as_exception(self):
        """Test that DbConnectionError can be caught as Exception."""
        try:
            raise DbConnectionError("Test catch exception")
        except Exception as e:
            assert isinstance(e, DbConnectionError)
            assert str(e) == "Test catch exception"

    def test_with_nested_exception(self):
        """Test DbConnectionError with a nested exception."""
        original_error = ConnectionRefusedError("Connection refused")

        try:
            try:
                raise original_error
            except ConnectionRefusedError as e:
                raise DbConnectionError("Failed to connect to database") from e
        except DbConnectionError as e:
            assert isinstance(e, DbConnectionError)
            assert str(e) == "Failed to connect to database"
            assert e.__cause__ is original_error
            assert isinstance(e.__cause__, ConnectionRefusedError)

    def test_attributes(self):
        """Test adding custom attributes to DbConnectionError."""
        error = DbConnectionError("Connection failed")
        error.host = "localhost"
        error.port = 5432
        error.attempts = 3

        assert error.host == "localhost"
        assert error.port == 5432
        assert error.attempts == 3
