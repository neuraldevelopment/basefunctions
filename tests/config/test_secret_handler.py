"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich

 Project : basefunctions

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 Pytest test suite for SecretHandler class

 Log:
 v1.0 : Initial implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import pytest
import os
from unittest.mock import patch

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


class TestSecretHandler:
    """Test suite for SecretHandler class."""

    def setup_method(self):
        """Setup for each test method."""
        # Reset singleton instance for each test
        if hasattr(basefunctions.SecretHandler, "_instances"):
            basefunctions.SecretHandler._instances.clear()
        # Clear test environment variables
        self.test_keys = ["TEST_SECRET", "API_KEY", "NONEXISTENT_KEY"]
        for key in self.test_keys:
            if key in os.environ:
                del os.environ[key]

    def teardown_method(self):
        """Cleanup after each test method."""
        # Reset singleton instance
        if hasattr(basefunctions.SecretHandler, "_instances"):
            basefunctions.SecretHandler._instances.clear()
        # Clean up test environment variables
        for key in self.test_keys:
            if key in os.environ:
                del os.environ[key]

    # =================================================================
    # SINGLETON TESTS
    # =================================================================

    def test_singleton_behavior(self):
        """Test that SecretHandler implements singleton pattern correctly."""
        handler1 = basefunctions.SecretHandler()
        handler2 = basefunctions.SecretHandler()

        assert handler1 is handler2

    # =================================================================
    # GET SECRET VALUE TESTS
    # =================================================================

    def test_get_secret_value_existing_key(self):
        """Test retrieving existing secret values."""
        os.environ["TEST_SECRET"] = "secret_value_123"

        handler = basefunctions.SecretHandler()
        result = handler.get_secret_value("TEST_SECRET")

        assert result == "secret_value_123"

    def test_get_secret_value_nonexistent_key_with_default(self):
        """Test retrieving nonexistent key returns default value."""
        handler = basefunctions.SecretHandler()
        result = handler.get_secret_value("NONEXISTENT_KEY", "default_value")

        assert result == "default_value"

    def test_get_secret_value_nonexistent_key_no_default(self):
        """Test retrieving nonexistent key returns None when no default."""
        handler = basefunctions.SecretHandler()
        result = handler.get_secret_value("NONEXISTENT_KEY")

        assert result is None

    def test_get_secret_value_empty_string(self):
        """Test retrieving key with empty string value."""
        os.environ["TEST_SECRET"] = ""

        handler = basefunctions.SecretHandler()
        result = handler.get_secret_value("TEST_SECRET", "default")

        assert result == ""

    # =================================================================
    # DICT-STYLE ACCESS TESTS
    # =================================================================

    def test_getitem_existing_key(self):
        """Test dict-style access for existing keys."""
        os.environ["API_KEY"] = "api_key_123"

        handler = basefunctions.SecretHandler()
        result = handler["API_KEY"]

        assert result == "api_key_123"

    def test_getitem_nonexistent_key(self):
        """Test dict-style access for nonexistent keys returns None."""
        handler = basefunctions.SecretHandler()
        result = handler["NONEXISTENT_KEY"]

        assert result is None

    def test_getitem_calls_get_secret_value(self):
        """Test that __getitem__ delegates to get_secret_value."""
        handler = basefunctions.SecretHandler()

        with patch.object(handler, "get_secret_value", return_value="mocked") as mock_get_secret:
            result = handler["TEST_KEY"]

            mock_get_secret.assert_called_once_with("TEST_KEY")
            assert result == "mocked"

    # =================================================================
    # INTEGRATION TESTS
    # =================================================================

    def test_multiple_secrets(self):
        """Test handling multiple environment variables."""
        test_secrets = {
            "DATABASE_URL": "postgresql://localhost:5432/test",
            "API_KEY": "test_api_key_123",
            "DEBUG": "true",
            "PORT": "8080",
        }

        for key, value in test_secrets.items():
            os.environ[key] = value

        handler = basefunctions.SecretHandler()

        for key, expected_value in test_secrets.items():
            assert handler.get_secret_value(key) == expected_value
            assert handler[key] == expected_value

    def test_special_characters_in_values(self):
        """Test handling values with special characters."""
        special_value = "password!@#$%^&*()_+-={}[]|:;'<>?,./"
        os.environ["SPECIAL_PASSWORD"] = special_value

        handler = basefunctions.SecretHandler()
        result = handler.get_secret_value("SPECIAL_PASSWORD")

        assert result == special_value
