"""
=============================================================================

  Licensed Materials, Property of Ralph Vogl, Munich

  Project : basefunctions

  Copyright (c) by Ralph Vogl

  All rights reserved.

  Description:

  pytest file for testing bf.SecretHandler class

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import os
import tempfile
import pytest
import basefunctions as bf

# -------------------------------------------------------------
# DEFINITIONS REGISTRY
# -------------------------------------------------------------


# -------------------------------------------------------------
# DEFINITIONS (Konstanten, Variablen)
# -------------------------------------------------------------


# -------------------------------------------------------------
# FUNCTION DEFINITIONS
# -------------------------------------------------------------
@pytest.fixture
def temp_env_file():
    """
    Fixture to create a temporary .env file for testing.
    """
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tmp:
        tmp.write("TEMP_SECRET_KEY=tempvalue\n")
        tmp.flush()
        yield tmp.name
    os.remove(tmp.name)


@pytest.fixture(autouse=True)
def setup_env(monkeypatch):
    """
    Fixture to set up default environment variables for testing.
    """
    monkeypatch.setenv("TEST_SECRET_KEY", "supersecret")
    monkeypatch.delenv("NON_EXISTENT_KEY", raising=False)


def test_get_existing_secret_default_env():
    """
    Test getting an existing secret key from the default environment.
    """
    handler = bf.SecretHandler()
    assert handler.get_secret_value("TEST_SECRET_KEY") == "supersecret"


def test_get_nonexistent_secret_with_default_default_env():
    """
    Test getting a non-existent secret key with a default value from the default environment.
    """
    handler = bf.SecretHandler()
    assert handler.get_secret_value("NON_EXISTENT_KEY", default_value="default") == "default"


def test_get_nonexistent_secret_without_default_default_env():
    """
    Test getting a non-existent secret key without providing a default value from the default environment.
    """
    handler = bf.SecretHandler()
    assert handler.get_secret_value("NON_EXISTENT_KEY") is None


def test_dict_style_access_default_env():
    """
    Test accessing a secret key using dict-style access from the default environment.
    """
    handler = bf.SecretHandler()
    assert handler["TEST_SECRET_KEY"] == "supersecret"


def test_load_specific_env_file(temp_env_file):
    """
    Test loading secrets from a specific temporary .env file.
    """
    # Direkt nochmal laden und Variablen überschreiben
    from dotenv import load_dotenv

    load_dotenv(temp_env_file, override=True)

    handler = bf.SecretHandler(env_file=temp_env_file)
    assert handler.get_secret_value("TEMP_SECRET_KEY") == "tempvalue"


def test_load_nonexistent_env_file(tmp_path):
    """
    Test behavior when trying to load a non-existent .env file.
    """
    fake_env_path = tmp_path / "nonexistent.env"
    handler = bf.SecretHandler(env_file=str(fake_env_path))
    assert handler.get_secret_value("ANY_KEY") is None
