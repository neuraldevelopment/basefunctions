"""
=============================================================================

  Licensed Materials, Property of neuraldevelopment , Munich

  Project : basefunctions

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  Tests for DatabaseError exception class

 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import pytest
import basefunctions
from basefunctions.database.exceptions import DatabaseError

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


class TestDatabaseError:
    """Test suite for the DatabaseError exception class."""

    def test_instance(self):
        """Test that DatabaseError can be instantiated."""
        error = DatabaseError("Test error message")
        assert isinstance(error, DatabaseError)
        assert str(error) == "Test error message"

    def test_inheritance(self):
        """Test that DatabaseError inherits from Exception."""
        error = DatabaseError("Test inheritance")
        assert isinstance(error, Exception)

    def test_empty_message(self):
        """Test DatabaseError with empty message."""
        error = DatabaseError()
        assert str(error) == ""

    def test_catch_as_exception(self):
        """Test that DatabaseError can be caught as Exception."""
        try:
            raise DatabaseError("Test catch")
        except Exception as e:
            assert isinstance(e, DatabaseError)
            assert str(e) == "Test catch"

    def test_with_nested_exception(self):
        """Test DatabaseError with a nested exception."""
        try:
            try:
                raise ValueError("Original error")
            except ValueError as ve:
                raise DatabaseError("Wrapped error") from ve
        except DatabaseError as e:
            assert isinstance(e, DatabaseError)
            assert str(e) == "Wrapped error"
            assert isinstance(e.__cause__, ValueError)
            assert str(e.__cause__) == "Original error"

    def test_attributes(self):
        """Test adding custom attributes to DatabaseError."""
        error = DatabaseError("Error with attributes")
        error.code = 500
        error.details = {"source": "database", "operation": "connect"}

        assert error.code == 500
        assert error.details["source"] == "database"
        assert error.details["operation"] == "connect"
