"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich
  Project : basefunctions
  Copyright (c) by neuraldevelopment
  All rights reserved.

  Description:
  Pytest test suite for secret_handler module.
  Tests SecretHandler singleton class for secure credential management.

  Log:
  v1.0.0 : Initial test implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
# Standard library imports
import os
from pathlib import Path
from typing import Any, Dict, Generator, Optional
from unittest.mock import Mock

# External imports
import pytest

# Project imports
from basefunctions.config.secret_handler import SecretHandler

# -------------------------------------------------------------
# FIXTURES
# -------------------------------------------------------------


@pytest.fixture
def reset_singleton() -> Generator[None, None, None]:
    """
    Reset SecretHandler singleton between tests.

    Yields
    ------
    None
        Yields control to test, cleans up singleton after

    Notes
    -----
    Critical for ensuring test isolation with singleton pattern.
    The singleton decorator stores instances by the original class,
    so we need to find and delete the right key.
    """
    # ARRANGE - Clear singleton instances dict
    from basefunctions.utils.decorators import _singleton_instances

    # Find and delete SecretHandler singleton (key is the wrapped class)
    keys_to_delete = [k for k in _singleton_instances.keys()
                      if k.__name__ == 'SecretHandler']
    for key in keys_to_delete:
        del _singleton_instances[key]

    # YIELD
    yield

    # CLEANUP
    keys_to_delete = [k for k in _singleton_instances.keys()
                      if k.__name__ == 'SecretHandler']
    for key in keys_to_delete:
        del _singleton_instances[key]


@pytest.fixture
def temp_env_file(tmp_path: Path) -> Path:
    """
    Create temporary .env file with sample secrets.

    Parameters
    ----------
    tmp_path : Path
        Pytest builtin fixture for temporary directory

    Returns
    -------
    Path
        Path to temporary .env file

    Notes
    -----
    Creates .env file with multiple key-value pairs
    """
    # ARRANGE
    env_file: Path = tmp_path / ".env"
    env_content: str = """
API_KEY=secret_key_12345
DATABASE_URL=postgresql://localhost:5432/testdb
DEBUG_MODE=true
MAX_CONNECTIONS=10
EMPTY_VALUE=
"""

    # ACT
    env_file.write_text(env_content.strip(), encoding="utf-8")

    # RETURN
    return env_file


@pytest.fixture
def empty_env_file(tmp_path: Path) -> Path:
    """
    Create empty .env file.

    Parameters
    ----------
    tmp_path : Path
        Pytest builtin fixture for temporary directory

    Returns
    -------
    Path
        Path to empty .env file

    Notes
    -----
    Used for testing handler with no secrets
    """
    # ARRANGE
    env_file: Path = tmp_path / ".env"

    # ACT
    env_file.write_text("", encoding="utf-8")

    # RETURN
    return env_file


@pytest.fixture
def malformed_env_file(tmp_path: Path) -> Path:
    """
    Create .env file with malformed content.

    Parameters
    ----------
    tmp_path : Path
        Pytest builtin fixture for temporary directory

    Returns
    -------
    Path
        Path to .env file with invalid syntax

    Notes
    -----
    Contains lines with invalid formats to test robustness
    """
    # ARRANGE
    env_file: Path = tmp_path / ".env"
    malformed_content: str = """
VALID_KEY=valid_value
INVALID LINE WITHOUT EQUALS
=NO_KEY_BEFORE_EQUALS
ANOTHER_VALID=value123
"""

    # ACT
    env_file.write_text(malformed_content.strip(), encoding="utf-8")

    # RETURN
    return env_file


@pytest.fixture
def mock_basefunctions_logger(monkeypatch: pytest.MonkeyPatch) -> Mock:
    """
    Mock basefunctions logging to avoid import issues.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture

    Returns
    -------
    Mock
        Mock logger object

    Notes
    -----
    Prevents logging setup during tests
    """
    # ARRANGE
    mock_logger: Mock = Mock()

    # ACT
    monkeypatch.setattr("basefunctions.setup_logger", Mock())
    monkeypatch.setattr("basefunctions.get_logger", lambda x: mock_logger)

    # RETURN
    return mock_logger


# -------------------------------------------------------------
# TEST CASES - __init__
# -------------------------------------------------------------


def test_init_loads_env_file_when_provided(
    reset_singleton: None,
    temp_env_file: Path,
    mock_basefunctions_logger: Mock
) -> None:  # CRITICAL TEST
    """
    Test __init__ loads env file when provided.

    Tests that SecretHandler correctly loads and parses provided .env file.

    Parameters
    ----------
    reset_singleton : None
        Resets singleton state
    temp_env_file : Path
        Temporary .env file fixture
    mock_basefunctions_logger : Mock
        Mocked logger

    Returns
    -------
    None
        Test passes if secrets are loaded
    """
    # ACT
    handler: SecretHandler = SecretHandler(env_file=str(temp_env_file))

    # ASSERT
    assert handler._env_file == str(temp_env_file)
    assert "API_KEY" in handler._secrets_dict
    assert handler._secrets_dict["API_KEY"] == "secret_key_12345"


def test_init_uses_default_home_env_when_none(
    reset_singleton: None,
    mock_basefunctions_logger: Mock
) -> None:  # CRITICAL TEST
    """
    Test __init__ uses default ~/.env when env_file is None.

    Tests that handler defaults to home directory .env file.

    Parameters
    ----------
    reset_singleton : None
        Resets singleton state
    mock_basefunctions_logger : Mock
        Mocked logger

    Returns
    -------
    None
        Test passes if default .env path is used
    """
    # ACT
    handler: SecretHandler = SecretHandler()

    # ASSERT - Check that default .env path is constructed
    assert handler._env_file is not None
    assert handler._env_file.endswith(f"{os.path.sep}.env")
    assert os.path.isabs(handler._env_file)  # Should be absolute path


def test_init_handles_nonexistent_file_gracefully(
    reset_singleton: None,
    tmp_path: Path,
    mock_basefunctions_logger: Mock
) -> None:  # CRITICAL TEST
    """
    Test __init__ handles nonexistent file without error.

    Tests that missing .env file doesn't crash initialization.

    Parameters
    ----------
    reset_singleton : None
        Resets singleton state
    tmp_path : Path
        Temporary directory fixture
    mock_basefunctions_logger : Mock
        Mocked logger

    Returns
    -------
    None
        Test passes if handler initializes with empty secrets
    """
    # ARRANGE
    nonexistent_file: Path = tmp_path / "does_not_exist.env"

    # ACT
    handler: SecretHandler = SecretHandler(env_file=str(nonexistent_file))

    # ASSERT
    assert handler._env_file == str(nonexistent_file)
    assert handler._secrets_dict == {}


def test_init_handles_invalid_env_file_path(
    reset_singleton: None,
    mock_basefunctions_logger: Mock
) -> None:  # CRITICAL TEST
    """
    Test __init__ handles invalid env file path.

    Tests that handler doesn't crash with invalid path.

    Parameters
    ----------
    reset_singleton : None
        Resets singleton state
    mock_basefunctions_logger : Mock
        Mocked logger

    Returns
    -------
    None
        Test passes if handler initializes gracefully
    """
    # ARRANGE
    invalid_path: str = "/invalid/path/that/does/not/exist/.env"

    # ACT
    handler: SecretHandler = SecretHandler(env_file=invalid_path)

    # ASSERT
    assert handler._env_file == invalid_path
    assert handler._secrets_dict == {}


def test_init_loads_empty_env_file_without_error(
    reset_singleton: None,
    empty_env_file: Path,
    mock_basefunctions_logger: Mock
) -> None:  # CRITICAL TEST
    """
    Test __init__ loads empty env file without error.

    Tests that empty .env file is valid.

    Parameters
    ----------
    reset_singleton : None
        Resets singleton state
    empty_env_file : Path
        Empty .env file fixture
    mock_basefunctions_logger : Mock
        Mocked logger

    Returns
    -------
    None
        Test passes if handler initializes with empty secrets dict
    """
    # ACT
    handler: SecretHandler = SecretHandler(env_file=str(empty_env_file))

    # ASSERT
    assert handler._env_file == str(empty_env_file)
    assert handler._secrets_dict == {}


def test_init_stores_env_file_path_correctly(
    reset_singleton: None,
    temp_env_file: Path,
    mock_basefunctions_logger: Mock
) -> None:  # CRITICAL TEST
    """
    Test __init__ stores env file path correctly.

    Tests that provided path is stored in _env_file attribute.

    Parameters
    ----------
    reset_singleton : None
        Resets singleton state
    temp_env_file : Path
        Temporary .env file fixture
    mock_basefunctions_logger : Mock
        Mocked logger

    Returns
    -------
    None
        Test passes if path is stored correctly
    """
    # ACT
    handler: SecretHandler = SecretHandler(env_file=str(temp_env_file))

    # ASSERT
    assert handler._env_file == str(temp_env_file)


def test_init_handles_malformed_env_file_robustly(
    reset_singleton: None,
    malformed_env_file: Path,
    mock_basefunctions_logger: Mock
) -> None:  # CRITICAL TEST
    """
    Test __init__ handles malformed env file robustly.

    Tests that dotenv parser handles invalid lines gracefully.

    Parameters
    ----------
    reset_singleton : None
        Resets singleton state
    malformed_env_file : Path
        Malformed .env file fixture
    mock_basefunctions_logger : Mock
        Mocked logger

    Returns
    -------
    None
        Test passes if valid lines are loaded, invalid ignored
    """
    # ACT
    handler: SecretHandler = SecretHandler(env_file=str(malformed_env_file))

    # ASSERT
    assert "VALID_KEY" in handler._secrets_dict
    assert "ANOTHER_VALID" in handler._secrets_dict
    # Invalid lines should be ignored by dotenv parser


# -------------------------------------------------------------
# TEST CASES - get_secret_value
# -------------------------------------------------------------


def test_get_secret_value_retrieves_existing_secret(
    reset_singleton: None,
    temp_env_file: Path,
    mock_basefunctions_logger: Mock,
    monkeypatch: pytest.MonkeyPatch
) -> None:  # CRITICAL TEST
    """
    Test get_secret_value retrieves existing secret.

    Tests that existing environment variable is returned.

    Parameters
    ----------
    reset_singleton : None
        Resets singleton state
    temp_env_file : Path
        Temporary .env file fixture
    mock_basefunctions_logger : Mock
        Mocked logger
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture

    Returns
    -------
    None
        Test passes if secret value is retrieved
    """
    # ARRANGE
    handler: SecretHandler = SecretHandler(env_file=str(temp_env_file))

    # ACT
    result: str = handler.get_secret_value("API_KEY")

    # ASSERT
    assert result == "secret_key_12345"


def test_get_secret_value_returns_default_when_missing(
    reset_singleton: None,
    temp_env_file: Path,
    mock_basefunctions_logger: Mock
) -> None:  # CRITICAL TEST
    """
    Test get_secret_value returns default when key missing.

    Tests that default value is returned for non-existent key.

    Parameters
    ----------
    reset_singleton : None
        Resets singleton state
    temp_env_file : Path
        Temporary .env file fixture
    mock_basefunctions_logger : Mock
        Mocked logger

    Returns
    -------
    None
        Test passes if default value is returned
    """
    # ARRANGE
    handler: SecretHandler = SecretHandler(env_file=str(temp_env_file))
    default_val: str = "fallback_value"

    # ACT
    result: str = handler.get_secret_value("NONEXISTENT_KEY", default_val)

    # ASSERT
    assert result == default_val


def test_get_secret_value_handles_none_key(
    reset_singleton: None,
    temp_env_file: Path,
    mock_basefunctions_logger: Mock
) -> None:  # CRITICAL TEST
    """
    Test get_secret_value raises TypeError for None key.

    Tests that None key is rejected (os.getenv doesn't accept None).

    Parameters
    ----------
    reset_singleton : None
        Resets singleton state
    temp_env_file : Path
        Temporary .env file fixture
    mock_basefunctions_logger : Mock
        Mocked logger

    Returns
    -------
    None
        Test passes if TypeError is raised for None key
    """
    # ARRANGE
    handler: SecretHandler = SecretHandler(env_file=str(temp_env_file))
    default_val: str = "default"

    # ACT & ASSERT - os.getenv() rejects None keys
    with pytest.raises(TypeError):
        result: str = handler.get_secret_value(None, default_val)


def test_get_secret_value_handles_empty_string_key(
    reset_singleton: None,
    temp_env_file: Path,
    mock_basefunctions_logger: Mock
) -> None:  # CRITICAL TEST
    """
    Test get_secret_value handles empty string key.

    Tests that empty string key returns default value.

    Parameters
    ----------
    reset_singleton : None
        Resets singleton state
    temp_env_file : Path
        Temporary .env file fixture
    mock_basefunctions_logger : Mock
        Mocked logger

    Returns
    -------
    None
        Test passes if default is returned
    """
    # ARRANGE
    handler: SecretHandler = SecretHandler(env_file=str(temp_env_file))
    default_val: str = "default"

    # ACT
    result: str = handler.get_secret_value("", default_val)

    # ASSERT
    assert result == default_val


def test_get_secret_value_returns_none_default_when_not_specified(
    reset_singleton: None,
    temp_env_file: Path,
    mock_basefunctions_logger: Mock
) -> None:  # CRITICAL TEST
    """
    Test get_secret_value returns None when no default specified.

    Tests that missing key with no default returns None.

    Parameters
    ----------
    reset_singleton : None
        Resets singleton state
    temp_env_file : Path
        Temporary .env file fixture
    mock_basefunctions_logger : Mock
        Mocked logger

    Returns
    -------
    None
        Test passes if None is returned
    """
    # ARRANGE
    handler: SecretHandler = SecretHandler(env_file=str(temp_env_file))

    # ACT
    result: Optional[str] = handler.get_secret_value("MISSING_KEY")

    # ASSERT
    assert result is None


@pytest.mark.parametrize("key,expected", [
    ("API_KEY", "secret_key_12345"),
    ("DATABASE_URL", "postgresql://localhost:5432/testdb"),
    ("DEBUG_MODE", "true"),
    ("MAX_CONNECTIONS", "10"),
    ("NONEXISTENT", None),
])
def test_get_secret_value_various_keys(
    reset_singleton: None,
    temp_env_file: Path,
    mock_basefunctions_logger: Mock,
    key: str,
    expected: Optional[str]
) -> None:  # CRITICAL TEST
    """
    Test get_secret_value with various keys.

    Tests multiple valid and invalid keys.

    Parameters
    ----------
    reset_singleton : None
        Resets singleton state
    temp_env_file : Path
        Temporary .env file fixture
    mock_basefunctions_logger : Mock
        Mocked logger
    key : str
        Secret key to retrieve
    expected : Optional[str]
        Expected value

    Returns
    -------
    None
        Test passes if correct value is retrieved
    """
    # ARRANGE
    handler: SecretHandler = SecretHandler(env_file=str(temp_env_file))

    # ACT
    result: Optional[str] = handler.get_secret_value(key)

    # ASSERT
    assert result == expected


# -------------------------------------------------------------
# TEST CASES - __getitem__
# -------------------------------------------------------------


def test_getitem_retrieves_secret_via_bracket_notation(
    reset_singleton: None,
    temp_env_file: Path,
    mock_basefunctions_logger: Mock
) -> None:  # IMPORTANT TEST
    """
    Test __getitem__ retrieves secret via bracket notation.

    Tests that handler[key] syntax works correctly.

    Parameters
    ----------
    reset_singleton : None
        Resets singleton state
    temp_env_file : Path
        Temporary .env file fixture
    mock_basefunctions_logger : Mock
        Mocked logger

    Returns
    -------
    None
        Test passes if bracket notation returns correct value
    """
    # ARRANGE
    handler: SecretHandler = SecretHandler(env_file=str(temp_env_file))

    # ACT
    result: str = handler["API_KEY"]

    # ASSERT
    assert result == "secret_key_12345"


def test_getitem_returns_none_for_missing_key(
    reset_singleton: None,
    temp_env_file: Path,
    mock_basefunctions_logger: Mock
) -> None:  # IMPORTANT TEST
    """
    Test __getitem__ returns None for missing key.

    Tests that missing key via bracket notation returns None.

    Parameters
    ----------
    reset_singleton : None
        Resets singleton state
    temp_env_file : Path
        Temporary .env file fixture
    mock_basefunctions_logger : Mock
        Mocked logger

    Returns
    -------
    None
        Test passes if None is returned
    """
    # ARRANGE
    handler: SecretHandler = SecretHandler(env_file=str(temp_env_file))

    # ACT
    result: Optional[str] = handler["MISSING_KEY"]

    # ASSERT
    assert result is None


def test_getitem_same_behavior_as_get_secret_value(
    reset_singleton: None,
    temp_env_file: Path,
    mock_basefunctions_logger: Mock
) -> None:  # IMPORTANT TEST
    """
    Test __getitem__ has same behavior as get_secret_value.

    Tests that both access methods return identical results.

    Parameters
    ----------
    reset_singleton : None
        Resets singleton state
    temp_env_file : Path
        Temporary .env file fixture
    mock_basefunctions_logger : Mock
        Mocked logger

    Returns
    -------
    None
        Test passes if both methods return same value
    """
    # ARRANGE
    handler: SecretHandler = SecretHandler(env_file=str(temp_env_file))
    test_key: str = "DATABASE_URL"

    # ACT
    method_result: str = handler.get_secret_value(test_key)
    bracket_result: str = handler[test_key]

    # ASSERT
    assert method_result == bracket_result


# -------------------------------------------------------------
# TEST CASES - get_all_secrets
# -------------------------------------------------------------


def test_get_all_secrets_returns_all_loaded_secrets(
    reset_singleton: None,
    temp_env_file: Path,
    mock_basefunctions_logger: Mock
) -> None:  # CRITICAL TEST
    """
    Test get_all_secrets returns all loaded secrets.

    Tests that all secrets from .env file are returned.

    Parameters
    ----------
    reset_singleton : None
        Resets singleton state
    temp_env_file : Path
        Temporary .env file fixture
    mock_basefunctions_logger : Mock
        Mocked logger

    Returns
    -------
    None
        Test passes if all secrets are in returned dict
    """
    # ARRANGE
    handler: SecretHandler = SecretHandler(env_file=str(temp_env_file))

    # ACT
    all_secrets: Dict[str, str] = handler.get_all_secrets()

    # ASSERT
    assert "API_KEY" in all_secrets
    assert "DATABASE_URL" in all_secrets
    assert "DEBUG_MODE" in all_secrets
    assert all_secrets["API_KEY"] == "secret_key_12345"


def test_get_all_secrets_returns_empty_dict_when_no_secrets(
    reset_singleton: None,
    empty_env_file: Path,
    mock_basefunctions_logger: Mock
) -> None:  # CRITICAL TEST
    """
    Test get_all_secrets returns empty dict when no secrets.

    Tests that empty .env file results in empty dict.

    Parameters
    ----------
    reset_singleton : None
        Resets singleton state
    empty_env_file : Path
        Empty .env file fixture
    mock_basefunctions_logger : Mock
        Mocked logger

    Returns
    -------
    None
        Test passes if empty dict is returned
    """
    # ARRANGE
    handler: SecretHandler = SecretHandler(env_file=str(empty_env_file))

    # ACT
    all_secrets: Dict[str, str] = handler.get_all_secrets()

    # ASSERT
    assert all_secrets == {}


def test_get_all_secrets_returns_copy_not_reference(
    reset_singleton: None,
    temp_env_file: Path,
    mock_basefunctions_logger: Mock
) -> None:  # CRITICAL TEST
    """
    Test get_all_secrets returns copy, not reference.

    Tests that modifying returned dict doesn't affect internal state.

    Parameters
    ----------
    reset_singleton : None
        Resets singleton state
    temp_env_file : Path
        Temporary .env file fixture
    mock_basefunctions_logger : Mock
        Mocked logger

    Returns
    -------
    None
        Test passes if returned value is independent copy
    """
    # ARRANGE
    handler: SecretHandler = SecretHandler(env_file=str(temp_env_file))

    # ACT
    all_secrets: Dict[str, str] = handler.get_all_secrets()
    all_secrets["INJECTED_KEY"] = "malicious_value"

    # ASSERT
    assert "INJECTED_KEY" not in handler._secrets_dict


def test_get_all_secrets_does_not_expose_internal_dict(
    reset_singleton: None,
    temp_env_file: Path,
    mock_basefunctions_logger: Mock
) -> None:  # CRITICAL TEST
    """
    Test get_all_secrets does not expose internal dict.

    Tests that internal _secrets_dict is protected from external modification.

    Parameters
    ----------
    reset_singleton : None
        Resets singleton state
    temp_env_file : Path
        Temporary .env file fixture
    mock_basefunctions_logger : Mock
        Mocked logger

    Returns
    -------
    None
        Test passes if internal dict is not exposed
    """
    # ARRANGE
    handler: SecretHandler = SecretHandler(env_file=str(temp_env_file))
    original_count: int = len(handler._secrets_dict)

    # ACT
    all_secrets: Dict[str, str] = handler.get_all_secrets()
    all_secrets.clear()

    # ASSERT
    assert len(handler._secrets_dict) == original_count


# -------------------------------------------------------------
# TEST CASES - Singleton Pattern
# -------------------------------------------------------------


def test_secret_handler_singleton_returns_same_instance(
    reset_singleton: None,
    mock_basefunctions_logger: Mock,
    tmp_path: Path
) -> None:  # IMPORTANT TEST
    """
    Test SecretHandler singleton returns same instance.

    Tests that multiple instantiations return identical object.

    Parameters
    ----------
    reset_singleton : None
        Resets singleton state
    mock_basefunctions_logger : Mock
        Mocked logger
    tmp_path : Path
        Temporary directory fixture

    Returns
    -------
    None
        Test passes if instances are identical

    Notes
    -----
    Note: Singleton pattern with __init__ parameters is tricky.
    First instantiation sets the env_file, subsequent calls use same instance.
    """
    # ARRANGE
    env_file: Path = tmp_path / ".env"
    env_file.write_text("KEY=value", encoding="utf-8")

    # ACT
    instance1: SecretHandler = SecretHandler(env_file=str(env_file))
    instance2: SecretHandler = SecretHandler(env_file=str(env_file))

    # ASSERT
    assert instance1 is instance2
