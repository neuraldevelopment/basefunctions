"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich
  Project : basefunctions
  Copyright (c) by neuraldevelopment
  All rights reserved.

  Description:
  Pytest test suite for config_handler module.
  Tests ConfigHandler singleton class for thread-safe configuration management.

  Log:
  v1.0.0 : Initial test implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
# Standard library imports
import json
import threading
from pathlib import Path
from typing import Any, Dict, Generator

# External imports
import pytest
from unittest.mock import Mock

# Project imports
from basefunctions.config.config_handler import ConfigHandler, CONFIG_FILENAME

# -------------------------------------------------------------
# FIXTURES
# -------------------------------------------------------------


@pytest.fixture
def reset_singleton() -> Generator[None, None, None]:
    """
    Reset ConfigHandler singleton between tests.

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

    # Find and delete ConfigHandler singleton (key is the wrapped class)
    keys_to_delete = [k for k in _singleton_instances.keys()
                      if k.__name__ == 'ConfigHandler']
    for key in keys_to_delete:
        del _singleton_instances[key]

    # YIELD
    yield

    # CLEANUP
    keys_to_delete = [k for k in _singleton_instances.keys()
                      if k.__name__ == 'ConfigHandler']
    for key in keys_to_delete:
        del _singleton_instances[key]


@pytest.fixture
def mock_basefunctions(monkeypatch: pytest.MonkeyPatch) -> Mock:
    """
    Create mock for all basefunctions dependencies.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture

    Returns
    -------
    Mock
        Mock object for basefunctions module

    Notes
    -----
    Mocks: create_root_structure, ensure_bootstrap_package_structure,
    create_full_package_structure, get_runtime_config_path, get_runtime_template_path
    """
    # ARRANGE
    mock_bf = Mock()
    mock_bf.create_root_structure = Mock()
    mock_bf.ensure_bootstrap_package_structure = Mock()
    mock_bf.create_full_package_structure = Mock()
    mock_bf.get_runtime_config_path = Mock(return_value="/mock/config/path")
    mock_bf.get_runtime_template_path = Mock(return_value="/mock/template/path")
    mock_bf.setup_logger = Mock(return_value=None)
    mock_bf.get_logger = Mock(return_value=Mock())

    # ACT
    monkeypatch.setattr(
        "basefunctions.create_root_structure", mock_bf.create_root_structure
    )
    monkeypatch.setattr(
        "basefunctions.ensure_bootstrap_package_structure",
        mock_bf.ensure_bootstrap_package_structure,
    )
    monkeypatch.setattr(
        "basefunctions.create_full_package_structure",
        mock_bf.create_full_package_structure,
    )
    monkeypatch.setattr(
        "basefunctions.get_runtime_config_path", mock_bf.get_runtime_config_path
    )
    monkeypatch.setattr(
        "basefunctions.get_runtime_template_path",
        mock_bf.get_runtime_template_path,
    )
    monkeypatch.setattr("basefunctions.setup_logger", mock_bf.setup_logger)
    monkeypatch.setattr("basefunctions.get_logger", mock_bf.get_logger)

    # RETURN
    return mock_bf


@pytest.fixture
def temp_config_file(tmp_path: Path) -> Path:
    """
    Create temporary JSON config file for testing.

    Parameters
    ----------
    tmp_path : Path
        Pytest builtin fixture for temporary directory

    Returns
    -------
    Path
        Path to temporary config file

    Notes
    -----
    Creates valid JSON config with basefunctions section
    """
    # ARRANGE
    config_file: Path = tmp_path / "config.json"
    config_data: Dict[str, Any] = {
        "basefunctions": {
            "logging": {"level": "INFO"},
            "database": {"host": "localhost"}
        }
    }

    # ACT
    config_file.write_text(json.dumps(config_data, indent=2), encoding="utf-8")

    # RETURN
    return config_file


@pytest.fixture
def invalid_json_file(tmp_path: Path) -> Path:
    """
    Create file with malformed JSON.

    Parameters
    ----------
    tmp_path : Path
        Pytest builtin fixture for temporary directory

    Returns
    -------
    Path
        Path to file with invalid JSON

    Notes
    -----
    Contains syntax error - missing closing brace
    """
    # ARRANGE
    invalid_file: Path = tmp_path / "invalid.json"

    # ACT
    invalid_file.write_text('{"key": "value"', encoding="utf-8")

    # RETURN
    return invalid_file


@pytest.fixture
def sample_config_data() -> Dict[str, Any]:
    """
    Provide sample configuration dictionary.

    Returns
    -------
    Dict[str, Any]
        Sample configuration with nested structure

    Notes
    -----
    Includes multiple packages and nested parameters
    """
    # RETURN
    return {
        "basefunctions": {
            "logging": {"level": "DEBUG", "format": "json"},
            "database": {"host": "localhost", "port": 5432}
        },
        "myapp": {
            "feature_flags": {"new_ui": True}
        }
    }


# -------------------------------------------------------------
# TEST CASES - load_config_file
# -------------------------------------------------------------


def test_load_config_file_loads_valid_json_successfully(
    reset_singleton: None,
    mock_basefunctions: Mock,
    temp_config_file: Path
) -> None:  # CRITICAL TEST
    """
    Test load_config_file loads valid JSON successfully.

    Tests that load_config_file correctly reads and parses
    a valid JSON configuration file.

    Parameters
    ----------
    reset_singleton : None
        Resets singleton state
    mock_basefunctions : Mock
        Mocked basefunctions dependencies
    temp_config_file : Path
        Temporary config file fixture

    Returns
    -------
    None
        Test passes if config is loaded correctly
    """
    # ARRANGE
    handler: ConfigHandler = ConfigHandler()
    expected_data: Dict[str, Any] = json.loads(temp_config_file.read_text())

    # ACT
    handler.load_config_file(str(temp_config_file))

    # ASSERT - Check that expected data was loaded (config.update merges)
    assert "basefunctions" in handler.config
    assert handler.config["basefunctions"]["logging"]["level"] == "INFO"
    assert handler.config["basefunctions"]["database"]["host"] == "localhost"


def test_load_config_file_updates_existing_config(
    reset_singleton: None,
    mock_basefunctions: Mock,
    tmp_path: Path
) -> None:  # CRITICAL TEST
    """
    Test load_config_file updates existing config with new data.

    Tests that loading a second config file merges with existing configuration.

    Parameters
    ----------
    reset_singleton : None
        Resets singleton state
    mock_basefunctions : Mock
        Mocked basefunctions dependencies
    tmp_path : Path
        Temporary directory fixture

    Returns
    -------
    None
        Test passes if configs are merged correctly
    """
    # ARRANGE
    handler: ConfigHandler = ConfigHandler()

    config1_file: Path = tmp_path / "config1.json"
    config1_file.write_text(json.dumps({"pkg1": {"key": "value1"}}), encoding="utf-8")

    config2_file: Path = tmp_path / "config2.json"
    config2_file.write_text(json.dumps({"pkg2": {"key": "value2"}}), encoding="utf-8")

    # ACT
    handler.load_config_file(str(config1_file))
    handler.load_config_file(str(config2_file))

    # ASSERT
    assert "pkg1" in handler.config
    assert "pkg2" in handler.config
    assert handler.config["pkg1"]["key"] == "value1"
    assert handler.config["pkg2"]["key"] == "value2"


def test_load_config_file_raises_value_error_when_not_json_extension(
    reset_singleton: None,
    mock_basefunctions: Mock,
    tmp_path: Path
) -> None:  # CRITICAL TEST
    """
    Test load_config_file raises ValueError for non-JSON file extension.

    Tests that function rejects files without .json extension.

    Parameters
    ----------
    reset_singleton : None
        Resets singleton state
    mock_basefunctions : Mock
        Mocked basefunctions dependencies
    tmp_path : Path
        Temporary directory fixture

    Returns
    -------
    None
        Test passes if ValueError is raised
    """
    # ARRANGE
    handler: ConfigHandler = ConfigHandler()
    txt_file: Path = tmp_path / "config.txt"
    txt_file.write_text('{"key": "value"}', encoding="utf-8")

    # ACT & ASSERT
    with pytest.raises(ValueError, match="not a valid JSON file"):
        handler.load_config_file(str(txt_file))


def test_load_config_file_raises_file_not_found_when_missing(
    reset_singleton: None,
    mock_basefunctions: Mock
) -> None:  # CRITICAL TEST
    """
    Test load_config_file raises FileNotFoundError when file missing.

    Tests that function raises appropriate error for non-existent file.

    Parameters
    ----------
    reset_singleton : None
        Resets singleton state
    mock_basefunctions : Mock
        Mocked basefunctions dependencies

    Returns
    -------
    None
        Test passes if FileNotFoundError is raised
    """
    # ARRANGE
    handler: ConfigHandler = ConfigHandler()
    nonexistent_file: str = "/tmp/does_not_exist_12345.json"

    # ACT & ASSERT
    with pytest.raises(FileNotFoundError, match="File not found"):
        handler.load_config_file(nonexistent_file)


def test_load_config_file_raises_json_decode_error_when_malformed(
    reset_singleton: None,
    mock_basefunctions: Mock,
    invalid_json_file: Path
) -> None:  # CRITICAL TEST
    """
    Test load_config_file raises JSONDecodeError for malformed JSON.

    Tests that function properly handles and reports JSON syntax errors.

    Parameters
    ----------
    reset_singleton : None
        Resets singleton state
    mock_basefunctions : Mock
        Mocked basefunctions dependencies
    invalid_json_file : Path
        File with invalid JSON

    Returns
    -------
    None
        Test passes if JSONDecodeError is raised
    """
    # ARRANGE
    handler: ConfigHandler = ConfigHandler()

    # ACT & ASSERT
    with pytest.raises(json.JSONDecodeError):
        handler.load_config_file(str(invalid_json_file))


def test_load_config_file_raises_value_error_when_not_dict(
    reset_singleton: None,
    mock_basefunctions: Mock,
    tmp_path: Path
) -> None:  # CRITICAL TEST
    """
    Test load_config_file raises error when JSON is not a dict.

    Tests that function rejects JSON arrays or primitives.

    Parameters
    ----------
    reset_singleton : None
        Resets singleton state
    mock_basefunctions : Mock
        Mocked basefunctions dependencies
    tmp_path : Path
        Temporary directory fixture

    Returns
    -------
    None
        Test passes if RuntimeError is raised
    """
    # ARRANGE
    handler: ConfigHandler = ConfigHandler()
    array_file: Path = tmp_path / "array.json"
    array_file.write_text('["item1", "item2"]', encoding="utf-8")

    # ACT & ASSERT - ValueError is wrapped in RuntimeError
    with pytest.raises(RuntimeError, match="Invalid config format"):
        handler.load_config_file(str(array_file))


def test_load_config_file_handles_empty_dict_correctly(
    reset_singleton: None,
    mock_basefunctions: Mock,
    tmp_path: Path
) -> None:  # CRITICAL TEST
    """
    Test load_config_file handles empty dict without error.

    Tests that empty configuration is valid.

    Parameters
    ----------
    reset_singleton : None
        Resets singleton state
    mock_basefunctions : Mock
        Mocked basefunctions dependencies
    tmp_path : Path
        Temporary directory fixture

    Returns
    -------
    None
        Test passes if empty dict loads successfully
    """
    # ARRANGE
    handler: ConfigHandler = ConfigHandler()
    empty_file: Path = tmp_path / "empty.json"
    empty_file.write_text('{}', encoding="utf-8")

    # ACT
    handler.load_config_file(str(empty_file))

    # ASSERT
    assert isinstance(handler.config, dict)


def test_load_config_file_thread_safe_concurrent_loads(
    reset_singleton: None,
    mock_basefunctions: Mock,
    tmp_path: Path
) -> None:  # CRITICAL TEST
    """
    Test load_config_file is thread-safe with concurrent loads.

    Tests that multiple threads can safely load configs simultaneously.

    Parameters
    ----------
    reset_singleton : None
        Resets singleton state
    mock_basefunctions : Mock
        Mocked basefunctions dependencies
    tmp_path : Path
        Temporary directory fixture

    Returns
    -------
    None
        Test passes if all threads complete without errors
    """
    # ARRANGE
    handler: ConfigHandler = ConfigHandler()
    config_files: list[Path] = []

    for i in range(10):
        config_file: Path = tmp_path / f"config{i}.json"
        config_file.write_text(json.dumps({f"pkg{i}": {"value": i}}), encoding="utf-8")
        config_files.append(config_file)

    errors: list[Exception] = []

    def load_config(path: Path) -> None:
        try:
            handler.load_config_file(str(path))
        except Exception as e:
            errors.append(e)

    # ACT
    threads: list[threading.Thread] = []
    for config_file in config_files:
        thread: threading.Thread = threading.Thread(target=load_config, args=(config_file,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    # ASSERT
    assert len(errors) == 0
    # Check that all 10 packages were loaded (config may have other entries)
    for i in range(10):
        assert f"pkg{i}" in handler.config
        assert handler.config[f"pkg{i}"]["value"] == i


# -------------------------------------------------------------
# TEST CASES - create_config_from_template
# -------------------------------------------------------------


def test_create_config_from_template_creates_config_successfully(
    reset_singleton: None,
    mock_basefunctions: Mock,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch
) -> None:  # CRITICAL TEST
    """
    Test create_config_from_template creates config successfully.

    Tests complete workflow: template creation, directory setup, file copy.

    Parameters
    ----------
    reset_singleton : None
        Resets singleton state
    mock_basefunctions : Mock
        Mocked basefunctions dependencies
    tmp_path : Path
        Temporary directory fixture
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture

    Returns
    -------
    None
        Test passes if config is created from template
    """
    # ARRANGE
    handler: ConfigHandler = ConfigHandler()

    config_path: Path = tmp_path / "config"
    template_path: Path = tmp_path / "templates"

    mock_basefunctions.get_runtime_config_path.return_value = str(config_path)
    mock_basefunctions.get_runtime_template_path.return_value = str(template_path)

    # Create existing template
    template_path.mkdir(parents=True)
    template_file: Path = template_path / CONFIG_FILENAME
    template_file.write_text(json.dumps({"testpkg": {"key": "value"}}), encoding="utf-8")

    # ACT
    handler.create_config_from_template("testpkg")

    # ASSERT
    config_file: Path = config_path / CONFIG_FILENAME
    assert config_file.exists()
    config_content: Dict[str, Any] = json.loads(config_file.read_text())
    assert "testpkg" in config_content


def test_create_config_from_template_creates_empty_template_when_missing(
    reset_singleton: None,
    mock_basefunctions: Mock,
    tmp_path: Path
) -> None:  # CRITICAL TEST
    """
    Test create_config_from_template creates empty template when missing.

    Tests that function generates template if it doesn't exist.

    Parameters
    ----------
    reset_singleton : None
        Resets singleton state
    mock_basefunctions : Mock
        Mocked basefunctions dependencies
    tmp_path : Path
        Temporary directory fixture

    Returns
    -------
    None
        Test passes if empty template is created
    """
    # ARRANGE
    handler: ConfigHandler = ConfigHandler()

    config_path: Path = tmp_path / "config"
    template_path: Path = tmp_path / "templates"

    mock_basefunctions.get_runtime_config_path.return_value = str(config_path)
    mock_basefunctions.get_runtime_template_path.return_value = str(template_path)

    # ACT
    handler.create_config_from_template("newpkg")

    # ASSERT
    template_file: Path = template_path / CONFIG_FILENAME
    assert template_file.exists()
    template_content: Dict[str, Any] = json.loads(template_file.read_text())
    assert "newpkg" in template_content
    assert template_content["newpkg"] == {}


def test_create_config_from_template_raises_value_error_when_package_name_empty(
    reset_singleton: None,
    mock_basefunctions: Mock
) -> None:  # CRITICAL TEST
    """
    Test create_config_from_template raises ValueError for empty package name.

    Tests that function rejects empty package names.

    Parameters
    ----------
    reset_singleton : None
        Resets singleton state
    mock_basefunctions : Mock
        Mocked basefunctions dependencies

    Returns
    -------
    None
        Test passes if ValueError is raised
    """
    # ARRANGE
    handler: ConfigHandler = ConfigHandler()

    # ACT & ASSERT
    with pytest.raises(ValueError, match="Package name must be provided"):
        handler.create_config_from_template("")


def test_create_config_from_template_uses_existing_template_when_present(
    reset_singleton: None,
    mock_basefunctions: Mock,
    tmp_path: Path
) -> None:  # CRITICAL TEST
    """
    Test create_config_from_template uses existing template.

    Tests that existing template is used without modification.

    Parameters
    ----------
    reset_singleton : None
        Resets singleton state
    mock_basefunctions : Mock
        Mocked basefunctions dependencies
    tmp_path : Path
        Temporary directory fixture

    Returns
    -------
    None
        Test passes if existing template is preserved and copied
    """
    # ARRANGE
    handler: ConfigHandler = ConfigHandler()

    config_path: Path = tmp_path / "config"
    template_path: Path = tmp_path / "templates"
    template_path.mkdir(parents=True)

    mock_basefunctions.get_runtime_config_path.return_value = str(config_path)
    mock_basefunctions.get_runtime_template_path.return_value = str(template_path)

    # Create existing template with custom content
    template_file: Path = template_path / CONFIG_FILENAME
    custom_template: Dict[str, Any] = {"existingpkg": {"custom": "data"}}
    template_file.write_text(json.dumps(custom_template), encoding="utf-8")

    # ACT
    handler.create_config_from_template("existingpkg")

    # ASSERT
    config_file: Path = config_path / CONFIG_FILENAME
    config_content: Dict[str, Any] = json.loads(config_file.read_text())
    assert config_content == custom_template


# -------------------------------------------------------------
# TEST CASES - load_config_for_package
# -------------------------------------------------------------


def test_load_config_for_package_loads_existing_config(
    reset_singleton: None,
    mock_basefunctions: Mock,
    tmp_path: Path
) -> None:  # CRITICAL TEST
    """
    Test load_config_for_package loads existing config.

    Tests complete package config loading workflow.

    Parameters
    ----------
    reset_singleton : None
        Resets singleton state
    mock_basefunctions : Mock
        Mocked basefunctions dependencies
    tmp_path : Path
        Temporary directory fixture

    Returns
    -------
    None
        Test passes if package config is loaded
    """
    # ARRANGE
    handler: ConfigHandler = ConfigHandler()

    config_path: Path = tmp_path / "config"
    config_path.mkdir(parents=True)

    mock_basefunctions.get_runtime_config_path.return_value = str(config_path)

    # Create existing config
    config_file: Path = config_path / CONFIG_FILENAME
    config_data: Dict[str, Any] = {"loadpkg": {"setting": "value"}}
    config_file.write_text(json.dumps(config_data), encoding="utf-8")

    # ACT
    handler.load_config_for_package("loadpkg")

    # ASSERT
    assert "loadpkg" in handler.config
    assert handler.config["loadpkg"]["setting"] == "value"
    mock_basefunctions.ensure_bootstrap_package_structure.assert_called_once_with("loadpkg")


def test_load_config_for_package_creates_config_when_missing(
    reset_singleton: None,
    mock_basefunctions: Mock,
    tmp_path: Path
) -> None:  # CRITICAL TEST
    """
    Test load_config_for_package creates config when missing.

    Tests that missing config triggers template creation.

    Parameters
    ----------
    reset_singleton : None
        Resets singleton state
    mock_basefunctions : Mock
        Mocked basefunctions dependencies
    tmp_path : Path
        Temporary directory fixture

    Returns
    -------
    None
        Test passes if config is created and loaded
    """
    # ARRANGE
    handler: ConfigHandler = ConfigHandler()

    config_path: Path = tmp_path / "config"
    template_path: Path = tmp_path / "templates"

    mock_basefunctions.get_runtime_config_path.return_value = str(config_path)
    mock_basefunctions.get_runtime_template_path.return_value = str(template_path)

    # ACT
    handler.load_config_for_package("newpkg")

    # ASSERT
    config_file: Path = config_path / CONFIG_FILENAME
    assert config_file.exists()
    assert "newpkg" in handler.config


# -------------------------------------------------------------
# TEST CASES - get_config_for_package
# -------------------------------------------------------------


def test_get_config_for_package_returns_all_when_none(
    reset_singleton: None,
    mock_basefunctions: Mock,
    sample_config_data: Dict[str, Any]
) -> None:  # IMPORTANT TEST
    """
    Test get_config_for_package returns all config when package is None.

    Tests that None parameter returns complete configuration.

    Parameters
    ----------
    reset_singleton : None
        Resets singleton state
    mock_basefunctions : Mock
        Mocked basefunctions dependencies
    sample_config_data : Dict[str, Any]
        Sample configuration data

    Returns
    -------
    None
        Test passes if all config is returned
    """
    # ARRANGE
    handler: ConfigHandler = ConfigHandler()
    handler.config = sample_config_data.copy()

    # ACT
    result: Dict[str, Any] = handler.get_config_for_package(None)

    # ASSERT
    assert result == sample_config_data
    assert "basefunctions" in result
    assert "myapp" in result


def test_get_config_for_package_returns_specific_package_config(
    reset_singleton: None,
    mock_basefunctions: Mock,
    sample_config_data: Dict[str, Any]
) -> None:  # IMPORTANT TEST
    """
    Test get_config_for_package returns specific package config.

    Tests that specific package name returns only that section.

    Parameters
    ----------
    reset_singleton : None
        Resets singleton state
    mock_basefunctions : Mock
        Mocked basefunctions dependencies
    sample_config_data : Dict[str, Any]
        Sample configuration data

    Returns
    -------
    None
        Test passes if specific package config is returned
    """
    # ARRANGE
    handler: ConfigHandler = ConfigHandler()
    handler.config = sample_config_data.copy()

    # ACT
    result: Dict[str, Any] = handler.get_config_for_package("basefunctions")

    # ASSERT
    assert "logging" in result
    assert "database" in result
    assert "myapp" not in result


def test_get_config_for_package_returns_empty_dict_when_package_missing(
    reset_singleton: None,
    mock_basefunctions: Mock,
    sample_config_data: Dict[str, Any]
) -> None:  # IMPORTANT TEST
    """
    Test get_config_for_package returns empty dict for missing package.

    Tests that non-existent package returns empty dict instead of error.

    Parameters
    ----------
    reset_singleton : None
        Resets singleton state
    mock_basefunctions : Mock
        Mocked basefunctions dependencies
    sample_config_data : Dict[str, Any]
        Sample configuration data

    Returns
    -------
    None
        Test passes if empty dict is returned
    """
    # ARRANGE
    handler: ConfigHandler = ConfigHandler()
    handler.config = sample_config_data.copy()

    # ACT
    result: Dict[str, Any] = handler.get_config_for_package("nonexistent")

    # ASSERT
    assert result == {}


def test_get_config_for_package_returns_copy_not_reference(
    reset_singleton: None,
    mock_basefunctions: Mock,
    sample_config_data: Dict[str, Any]
) -> None:  # IMPORTANT TEST
    """
    Test get_config_for_package returns copy, not reference.

    Tests that modifying returned config doesn't affect internal state.

    Parameters
    ----------
    reset_singleton : None
        Resets singleton state
    mock_basefunctions : Mock
        Mocked basefunctions dependencies
    sample_config_data : Dict[str, Any]
        Sample configuration data

    Returns
    -------
    None
        Test passes if returned value is independent copy
    """
    # ARRANGE
    handler: ConfigHandler = ConfigHandler()
    handler.config = sample_config_data.copy()

    # ACT
    result: Dict[str, Any] = handler.get_config_for_package("basefunctions")
    result["modified"] = "value"

    # ASSERT
    assert "modified" not in handler.config.get("basefunctions", {})


# -------------------------------------------------------------
# TEST CASES - get_config_parameter
# -------------------------------------------------------------


def test_get_config_parameter_retrieves_nested_value(
    reset_singleton: None,
    mock_basefunctions: Mock,
    sample_config_data: Dict[str, Any]
) -> None:  # IMPORTANT TEST
    """
    Test get_config_parameter retrieves nested value correctly.

    Tests slash-separated path navigation through nested dicts.

    Parameters
    ----------
    reset_singleton : None
        Resets singleton state
    mock_basefunctions : Mock
        Mocked basefunctions dependencies
    sample_config_data : Dict[str, Any]
        Sample configuration data

    Returns
    -------
    None
        Test passes if nested value is retrieved
    """
    # ARRANGE
    handler: ConfigHandler = ConfigHandler()
    handler.config = sample_config_data.copy()

    # ACT
    result: str = handler.get_config_parameter("basefunctions/logging/level")

    # ASSERT
    assert result == "DEBUG"


def test_get_config_parameter_retrieves_top_level_value(
    reset_singleton: None,
    mock_basefunctions: Mock,
    sample_config_data: Dict[str, Any]
) -> None:  # IMPORTANT TEST
    """
    Test get_config_parameter retrieves top-level value.

    Tests single-level path retrieval.

    Parameters
    ----------
    reset_singleton : None
        Resets singleton state
    mock_basefunctions : Mock
        Mocked basefunctions dependencies
    sample_config_data : Dict[str, Any]
        Sample configuration data

    Returns
    -------
    None
        Test passes if top-level value is retrieved
    """
    # ARRANGE
    handler: ConfigHandler = ConfigHandler()
    handler.config = sample_config_data.copy()

    # ACT
    result: Dict[str, Any] = handler.get_config_parameter("basefunctions")

    # ASSERT
    assert "logging" in result
    assert "database" in result


def test_get_config_parameter_returns_default_when_path_not_found(
    reset_singleton: None,
    mock_basefunctions: Mock,
    sample_config_data: Dict[str, Any]
) -> None:  # IMPORTANT TEST
    """
    Test get_config_parameter returns default when path not found.

    Tests that missing paths return specified default value.

    Parameters
    ----------
    reset_singleton : None
        Resets singleton state
    mock_basefunctions : Mock
        Mocked basefunctions dependencies
    sample_config_data : Dict[str, Any]
        Sample configuration data

    Returns
    -------
    None
        Test passes if default value is returned
    """
    # ARRANGE
    handler: ConfigHandler = ConfigHandler()
    handler.config = sample_config_data.copy()
    default_val: str = "default_value"

    # ACT
    result: str = handler.get_config_parameter("nonexistent/path/here", default_val)

    # ASSERT
    assert result == default_val


def test_get_config_parameter_returns_default_when_intermediate_not_dict(
    reset_singleton: None,
    mock_basefunctions: Mock
) -> None:  # IMPORTANT TEST
    """
    Test get_config_parameter returns default when intermediate value not dict.

    Tests that path traversal stops when encountering non-dict value.

    Parameters
    ----------
    reset_singleton : None
        Resets singleton state
    mock_basefunctions : Mock
        Mocked basefunctions dependencies

    Returns
    -------
    None
        Test passes if default is returned
    """
    # ARRANGE
    handler: ConfigHandler = ConfigHandler()
    handler.config = {"pkg": {"setting": "value"}}
    default_val: str = "fallback"

    # ACT - trying to traverse into string value
    result: str = handler.get_config_parameter("pkg/setting/nested", default_val)

    # ASSERT
    assert result == default_val


@pytest.mark.parametrize("path,expected", [
    ("basefunctions/logging/level", "DEBUG"),
    ("basefunctions/database/port", 5432),
    ("myapp/feature_flags/new_ui", True),
    ("nonexistent", None),
    ("basefunctions/nonexistent/key", None),
])
def test_get_config_parameter_various_paths(
    reset_singleton: None,
    mock_basefunctions: Mock,
    sample_config_data: Dict[str, Any],
    path: str,
    expected: Any
) -> None:  # IMPORTANT TEST
    """
    Test get_config_parameter with various path configurations.

    Tests multiple valid and invalid paths with different data types.

    Parameters
    ----------
    reset_singleton : None
        Resets singleton state
    mock_basefunctions : Mock
        Mocked basefunctions dependencies
    sample_config_data : Dict[str, Any]
        Sample configuration data
    path : str
        Configuration path to test
    expected : Any
        Expected return value

    Returns
    -------
    None
        Test passes if correct value is retrieved
    """
    # ARRANGE
    handler: ConfigHandler = ConfigHandler()
    handler.config = sample_config_data.copy()

    # ACT
    result: Any = handler.get_config_parameter(path)

    # ASSERT
    assert result == expected


# -------------------------------------------------------------
# TEST CASES - Singleton Pattern
# -------------------------------------------------------------


def test_config_handler_singleton_returns_same_instance(
    reset_singleton: None,
    mock_basefunctions: Mock
) -> None:  # IMPORTANT TEST
    """
    Test ConfigHandler singleton returns same instance.

    Tests that multiple instantiations return identical object.

    Parameters
    ----------
    reset_singleton : None
        Resets singleton state
    mock_basefunctions : Mock
        Mocked basefunctions dependencies

    Returns
    -------
    None
        Test passes if instances are identical
    """
    # ACT
    instance1: ConfigHandler = ConfigHandler()
    instance2: ConfigHandler = ConfigHandler()

    # ASSERT
    assert instance1 is instance2


def test_config_handler_singleton_thread_safe_initialization(
    reset_singleton: None,
    mock_basefunctions: Mock
) -> None:  # IMPORTANT TEST
    """
    Test ConfigHandler singleton initialization is thread-safe.

    Tests that concurrent instantiations produce single instance.

    Parameters
    ----------
    reset_singleton : None
        Resets singleton state
    mock_basefunctions : Mock
        Mocked basefunctions dependencies

    Returns
    -------
    None
        Test passes if all threads get same instance
    """
    # ARRANGE
    instances: list[ConfigHandler] = []
    lock: threading.Lock = threading.Lock()

    def create_instance() -> None:
        instance: ConfigHandler = ConfigHandler()
        with lock:
            instances.append(instance)

    # ACT
    threads: list[threading.Thread] = []
    for _ in range(10):
        thread: threading.Thread = threading.Thread(target=create_instance)
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    # ASSERT
    assert len(instances) == 10
    assert all(inst is instances[0] for inst in instances)
