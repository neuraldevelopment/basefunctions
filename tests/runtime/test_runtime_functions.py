"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.

 Description:
 Pytest test suite for runtime_functions module.
 Tests runtime path detection, bootstrap config, and directory structure creation.

 Log:
 v1.0.0 : Initial test implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
# External imports
import json
import os
from pathlib import Path
from typing import Dict, List
from unittest.mock import Mock

import pytest

# Project imports
from basefunctions.runtime.runtime_functions import (
    _load_bootstrap_config,
    _save_bootstrap_config,
    create_bootstrap_package_structure,
    create_full_package_structure,
    create_root_structure,
    find_development_path,
    get_bootstrap_config_path,
    get_bootstrap_deployment_directory,
    get_bootstrap_development_directories,
    get_deployment_path,
    get_runtime_component_path,
    get_runtime_config_path,
    get_runtime_log_path,
    get_runtime_path,
    get_runtime_template_path,
    BOOTSTRAP_CONFIG_PATH,
    DEFAULT_DEPLOYMENT_DIRECTORIES,
    DEFAULT_PACKAGE_DIRECTORIES,
    BOOTSTRAP_DIRECTORIES,
)

# -------------------------------------------------------------
# FIXTURES
# -------------------------------------------------------------


@pytest.fixture
def mock_bootstrap_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Dict[str, any]:
    """
    Mock bootstrap configuration with temporary paths.

    Parameters
    ----------
    tmp_path : Path
        Pytest builtin fixture for temporary directory
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture

    Returns
    -------
    Dict[str, any]
        Mock bootstrap configuration dictionary

    Notes
    -----
    Patches BOOTSTRAP_CONFIG_PATH to use temporary file
    """
    # ARRANGE
    config_file: Path = tmp_path / "bootstrap.json"
    deploy_dir: Path = tmp_path / "deployment"
    dev_dir1: Path = tmp_path / "dev1"
    dev_dir2: Path = tmp_path / "dev2"

    deploy_dir.mkdir()
    dev_dir1.mkdir()
    dev_dir2.mkdir()

    config: Dict[str, any] = {
        "bootstrap": {
            "paths": {
                "deployment_directory": str(deploy_dir),
                "development_directories": [str(dev_dir1), str(dev_dir2)],
            }
        }
    }

    config_file.write_text(json.dumps(config, indent=2))

    # Mock BOOTSTRAP_CONFIG_PATH
    monkeypatch.setattr(
        "basefunctions.runtime.runtime_functions.BOOTSTRAP_CONFIG_PATH",
        str(config_file),
    )

    # RETURN
    return config


@pytest.fixture
def mock_cwd(monkeypatch: pytest.MonkeyPatch):
    """
    Factory fixture to mock current working directory.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture

    Returns
    -------
    callable
        Function to set current working directory

    Notes
    -----
    Use this to simulate being in different directories
    """

    # RETURN
    def _set_cwd(path: str) -> None:
        monkeypatch.setattr("pathlib.Path.cwd", lambda: Path(path).resolve())

    return _set_cwd


# -------------------------------------------------------------
# TESTS FOR _load_bootstrap_config
# -------------------------------------------------------------


def test_load_bootstrap_config_returns_config_when_exists(mock_bootstrap_config: Dict[str, any]) -> None:
    """Test _load_bootstrap_config returns configuration when file exists."""
    # ACT
    result: dict = _load_bootstrap_config()

    # ASSERT
    assert "bootstrap" in result
    assert "paths" in result["bootstrap"]
    assert "deployment_directory" in result["bootstrap"]["paths"]


def test_load_bootstrap_config_returns_default_when_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test _load_bootstrap_config returns default config when file doesn't exist."""
    # ARRANGE
    nonexistent_file: Path = tmp_path / "nonexistent.json"
    monkeypatch.setattr(
        "basefunctions.runtime.runtime_functions.BOOTSTRAP_CONFIG_PATH",
        str(nonexistent_file),
    )

    # ACT
    result: dict = _load_bootstrap_config()

    # ASSERT
    assert result["bootstrap"]["paths"]["deployment_directory"] == "~/.neuraldevelopment"
    assert isinstance(result["bootstrap"]["paths"]["development_directories"], list)


def test_load_bootstrap_config_creates_default_config_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test _load_bootstrap_config creates default config file when missing."""
    # ARRANGE
    config_file: Path = tmp_path / "config" / "bootstrap.json"
    monkeypatch.setattr(
        "basefunctions.runtime.runtime_functions.BOOTSTRAP_CONFIG_PATH",
        str(config_file),
    )

    # ACT
    result: dict = _load_bootstrap_config()

    # ASSERT
    assert config_file.exists()
    assert config_file.is_file()


def test_load_bootstrap_config_handles_malformed_json_gracefully(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test _load_bootstrap_config handles malformed JSON by returning default config."""
    # ARRANGE
    config_file: Path = tmp_path / "bootstrap.json"
    config_file.write_text("invalid json content {{{")

    monkeypatch.setattr(
        "basefunctions.runtime.runtime_functions.BOOTSTRAP_CONFIG_PATH",
        str(config_file),
    )

    # ACT
    result: dict = _load_bootstrap_config()

    # ASSERT
    assert result["bootstrap"]["paths"]["deployment_directory"] == "~/.neuraldevelopment"


# -------------------------------------------------------------
# TESTS FOR _save_bootstrap_config
# -------------------------------------------------------------


def test_save_bootstrap_config_creates_directory_structure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test _save_bootstrap_config creates parent directories if needed."""
    # ARRANGE
    config_file: Path = tmp_path / "nested" / "config" / "bootstrap.json"
    monkeypatch.setattr(
        "basefunctions.runtime.runtime_functions.BOOTSTRAP_CONFIG_PATH",
        str(config_file),
    )

    config: dict = {"bootstrap": {"paths": {"deployment_directory": "~/.test"}}}

    # ACT
    _save_bootstrap_config(config)

    # ASSERT
    assert config_file.parent.exists()
    assert config_file.exists()


def test_save_bootstrap_config_writes_valid_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test _save_bootstrap_config writes valid JSON content."""
    # ARRANGE
    config_file: Path = tmp_path / "bootstrap.json"
    monkeypatch.setattr(
        "basefunctions.runtime.runtime_functions.BOOTSTRAP_CONFIG_PATH",
        str(config_file),
    )

    config: dict = {"bootstrap": {"paths": {"deployment_directory": str(tmp_path)}}}

    # ACT
    _save_bootstrap_config(config)

    # ASSERT
    saved_content: str = config_file.read_text()
    parsed_config: dict = json.loads(saved_content)
    assert parsed_config == config


def test_save_bootstrap_config_handles_write_failure_gracefully(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test _save_bootstrap_config handles write failures gracefully without raising."""
    # ARRANGE
    invalid_path: Path = Path("/invalid/path/bootstrap.json")
    monkeypatch.setattr(
        "basefunctions.runtime.runtime_functions.BOOTSTRAP_CONFIG_PATH",
        str(invalid_path),
    )

    config: dict = {"test": "data"}

    # ACT (should not raise)
    _save_bootstrap_config(config)

    # ASSERT
    # No exception raised


# -------------------------------------------------------------
# TESTS FOR get_runtime_path
# -------------------------------------------------------------


def test_get_runtime_path_returns_dev_path_when_in_dev_directory(
    mock_bootstrap_config: Dict[str, any], mock_cwd
) -> None:  # CRITICAL TEST
    """Test get_runtime_path returns development path when CWD is in development directory."""
    # ARRANGE
    package_name: str = "testpackage"
    dev_dir: str = mock_bootstrap_config["bootstrap"]["paths"]["development_directories"][0]
    package_path: Path = Path(dev_dir) / package_name
    package_path.mkdir(parents=True)

    mock_cwd(str(package_path))

    # ACT
    result: str = get_runtime_path(package_name)

    # ASSERT
    assert result == str(package_path)


def test_get_runtime_path_returns_deploy_path_when_not_in_dev(
    mock_bootstrap_config: Dict[str, any], mock_cwd
) -> None:  # CRITICAL TEST
    """Test get_runtime_path returns deployment path when CWD is not in development directory."""
    # ARRANGE
    package_name: str = "testpackage"
    other_dir: str = "/tmp/other_directory"

    mock_cwd(other_dir)

    # ACT
    result: str = get_runtime_path(package_name)

    # ASSERT
    deploy_dir: str = mock_bootstrap_config["bootstrap"]["paths"]["deployment_directory"]
    expected_path: str = str(Path(deploy_dir) / "packages" / package_name)
    assert result == expected_path


def test_get_runtime_path_handles_config_load_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mock_cwd
) -> None:  # CRITICAL TEST
    """Test get_runtime_path returns fallback path when config loading fails."""
    # ARRANGE
    package_name: str = "testpackage"
    mock_cwd(str(tmp_path))

    # Force config load to fail
    monkeypatch.setattr(
        "basefunctions.runtime.runtime_functions._load_bootstrap_config",
        Mock(side_effect=Exception("Config error")),
    )

    # ACT
    result: str = get_runtime_path(package_name)

    # ASSERT
    fallback_path: str = str(Path("~/.neuraldevelopment").expanduser().resolve() / "packages" / package_name)
    assert result == fallback_path


def test_get_runtime_path_prefers_longest_matching_dev_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mock_cwd
) -> None:
    """Test get_runtime_path prefers longest (most specific) matching development directory."""
    # ARRANGE
    package_name: str = "testpackage"

    # Create nested dev directories
    short_dev: Path = tmp_path / "dev"
    long_dev: Path = tmp_path / "dev" / "nested"
    short_dev.mkdir()
    long_dev.mkdir()

    package_in_long: Path = long_dev / package_name
    package_in_long.mkdir()

    config: dict = {
        "bootstrap": {
            "paths": {
                "deployment_directory": str(tmp_path / "deploy"),
                "development_directories": [str(short_dev), str(long_dev)],
            }
        }
    }

    config_file: Path = tmp_path / "bootstrap.json"
    config_file.write_text(json.dumps(config))
    monkeypatch.setattr("basefunctions.runtime.runtime_functions.BOOTSTRAP_CONFIG_PATH", str(config_file))

    mock_cwd(str(package_in_long))

    # ACT
    result: str = get_runtime_path(package_name)

    # ASSERT
    assert result == str(package_in_long)


# -------------------------------------------------------------
# TESTS FOR find_development_path
# -------------------------------------------------------------


def test_find_development_path_returns_all_matching_paths(
    mock_bootstrap_config: Dict[str, any]
) -> None:  # CRITICAL TEST
    """Test find_development_path returns all paths where package exists."""
    # ARRANGE
    package_name: str = "testpackage"

    dev_dirs: List[str] = mock_bootstrap_config["bootstrap"]["paths"]["development_directories"]
    package_path1: Path = Path(dev_dirs[0]) / package_name
    package_path2: Path = Path(dev_dirs[1]) / package_name

    package_path1.mkdir(parents=True)
    package_path2.mkdir(parents=True)

    # ACT
    result: List[str] = find_development_path(package_name)

    # ASSERT
    assert len(result) == 2
    assert str(package_path1) in result
    assert str(package_path2) in result


def test_find_development_path_returns_empty_when_not_found(
    mock_bootstrap_config: Dict[str, any]
) -> None:  # CRITICAL TEST
    """Test find_development_path returns empty list when package not found."""
    # ARRANGE
    package_name: str = "nonexistent_package"

    # ACT
    result: List[str] = find_development_path(package_name)

    # ASSERT
    assert result == []


def test_find_development_path_resolves_tilde_in_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test find_development_path correctly expands tilde (~) in development directories."""
    # ARRANGE
    package_name: str = "testpackage"

    # Mock home directory
    mock_home: Path = tmp_path / "home"
    mock_home.mkdir()
    dev_dir: Path = mock_home / "dev"
    dev_dir.mkdir()

    package_path: Path = dev_dir / package_name
    package_path.mkdir()

    config: dict = {
        "bootstrap": {
            "paths": {
                "deployment_directory": str(tmp_path / "deploy"),
                "development_directories": ["~/dev"],
            }
        }
    }

    config_file: Path = tmp_path / "bootstrap.json"
    config_file.write_text(json.dumps(config))
    monkeypatch.setattr("basefunctions.runtime.runtime_functions.BOOTSTRAP_CONFIG_PATH", str(config_file))
    monkeypatch.setenv("HOME", str(mock_home))

    # ACT
    result: List[str] = find_development_path(package_name)

    # ASSERT
    assert len(result) == 1
    assert package_name in result[0]


# -------------------------------------------------------------
# TESTS FOR create_root_structure
# -------------------------------------------------------------


def test_create_root_structure_creates_deployment_directories(
    mock_bootstrap_config: Dict[str, any]
) -> None:  # CRITICAL TEST
    """Test create_root_structure creates all deployment directories."""
    # ARRANGE
    deploy_dir: Path = Path(mock_bootstrap_config["bootstrap"]["paths"]["deployment_directory"])

    # Remove if exists
    if deploy_dir.exists():
        import shutil

        shutil.rmtree(deploy_dir)

    # ACT
    create_root_structure()

    # ASSERT
    assert deploy_dir.exists()
    for dir_name in DEFAULT_DEPLOYMENT_DIRECTORIES:
        expected_dir: Path = deploy_dir / dir_name
        assert expected_dir.exists(), f"Expected directory not created: {dir_name}"


def test_create_root_structure_handles_existing_directories_gracefully(mock_bootstrap_config: Dict[str, any]) -> None:
    """Test create_root_structure handles existing directories without errors."""
    # ARRANGE
    deploy_dir: Path = Path(mock_bootstrap_config["bootstrap"]["paths"]["deployment_directory"])
    deploy_dir.mkdir(parents=True, exist_ok=True)

    # ACT (should not raise)
    create_root_structure()

    # ASSERT
    assert deploy_dir.exists()


# -------------------------------------------------------------
# TESTS FOR create_bootstrap_package_structure
# -------------------------------------------------------------


def test_create_bootstrap_package_structure_creates_directories(
    mock_bootstrap_config: Dict[str, any], mock_cwd
) -> None:  # CRITICAL TEST
    """Test create_bootstrap_package_structure creates bootstrap directories."""
    # ARRANGE
    package_name: str = "testpackage"
    deploy_dir: Path = Path(mock_bootstrap_config["bootstrap"]["paths"]["deployment_directory"])
    package_path: Path = deploy_dir / "packages" / package_name

    mock_cwd(str(deploy_dir))

    # ACT
    create_bootstrap_package_structure(package_name)

    # ASSERT
    for dir_name in BOOTSTRAP_DIRECTORIES:
        expected_dir: Path = package_path / dir_name
        assert expected_dir.exists(), f"Expected bootstrap directory not created: {dir_name}"


def test_create_bootstrap_package_structure_raises_error_when_name_empty() -> None:  # CRITICAL TEST
    """Test create_bootstrap_package_structure raises ValueError when package name is empty."""
    # ARRANGE
    empty_name: str = ""

    # ACT & ASSERT
    with pytest.raises(ValueError, match="Package name must be provided and cannot be empty"):
        create_bootstrap_package_structure(empty_name)


def test_create_bootstrap_package_structure_raises_error_when_name_none() -> None:  # CRITICAL TEST
    """Test create_bootstrap_package_structure raises ValueError when package name is None."""
    # ARRANGE
    none_name: None = None

    # ACT & ASSERT
    with pytest.raises(ValueError, match="Package name must be provided and cannot be empty"):
        create_bootstrap_package_structure(none_name)


# -------------------------------------------------------------
# TESTS FOR create_full_package_structure
# -------------------------------------------------------------


def test_create_full_package_structure_creates_all_directories(
    mock_bootstrap_config: Dict[str, any], mock_cwd
) -> None:  # CRITICAL TEST
    """Test create_full_package_structure creates all default package directories."""
    # ARRANGE
    package_name: str = "testpackage"
    deploy_dir: Path = Path(mock_bootstrap_config["bootstrap"]["paths"]["deployment_directory"])
    package_path: Path = deploy_dir / "packages" / package_name

    mock_cwd(str(deploy_dir))

    # ACT
    create_full_package_structure(package_name)

    # ASSERT
    for dir_name in DEFAULT_PACKAGE_DIRECTORIES:
        expected_dir: Path = package_path / dir_name
        assert expected_dir.exists(), f"Expected package directory not created: {dir_name}"


def test_create_full_package_structure_uses_custom_directories(
    mock_bootstrap_config: Dict[str, any], mock_cwd
) -> None:  # CRITICAL TEST
    """Test create_full_package_structure uses custom directories when provided."""
    # ARRANGE
    package_name: str = "testpackage"
    custom_dirs: List[str] = ["custom1", "custom2/nested"]
    deploy_dir: Path = Path(mock_bootstrap_config["bootstrap"]["paths"]["deployment_directory"])
    package_path: Path = deploy_dir / "packages" / package_name

    mock_cwd(str(deploy_dir))

    # ACT
    create_full_package_structure(package_name, custom_directories=custom_dirs)

    # ASSERT
    for dir_name in custom_dirs:
        expected_dir: Path = package_path / dir_name
        assert expected_dir.exists(), f"Expected custom directory not created: {dir_name}"


def test_create_full_package_structure_raises_error_when_name_empty() -> None:  # CRITICAL TEST
    """Test create_full_package_structure raises ValueError when package name is empty."""
    # ARRANGE
    empty_name: str = ""

    # ACT & ASSERT
    with pytest.raises(ValueError, match="Package name must be provided and cannot be empty"):
        create_full_package_structure(empty_name)


# -------------------------------------------------------------
# TESTS FOR get_deployment_path
# -------------------------------------------------------------


def test_get_deployment_path_returns_correct_path(mock_bootstrap_config: Dict[str, any]) -> None:
    """Test get_deployment_path returns correct deployment directory path."""
    # ARRANGE
    package_name: str = "testpackage"
    deploy_dir: str = mock_bootstrap_config["bootstrap"]["paths"]["deployment_directory"]

    # ACT
    result: str = get_deployment_path(package_name)

    # ASSERT
    expected_path: str = str(Path(deploy_dir).expanduser().resolve() / "packages" / package_name)
    assert result == expected_path


def test_get_deployment_path_expands_tilde(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_deployment_path correctly expands tilde in deployment directory."""
    # ARRANGE
    package_name: str = "testpackage"
    mock_home: Path = tmp_path / "home"
    mock_home.mkdir()

    config: dict = {"bootstrap": {"paths": {"deployment_directory": "~/.neuraldevelopment"}}}

    config_file: Path = tmp_path / "bootstrap.json"
    config_file.write_text(json.dumps(config))
    monkeypatch.setattr("basefunctions.runtime.runtime_functions.BOOTSTRAP_CONFIG_PATH", str(config_file))
    monkeypatch.setenv("HOME", str(mock_home))

    # ACT
    result: str = get_deployment_path(package_name)

    # ASSERT
    assert "~" not in result
    assert package_name in result


# -------------------------------------------------------------
# TESTS FOR get_runtime_component_path
# -------------------------------------------------------------


def test_get_runtime_component_path_returns_correct_path(mock_bootstrap_config: Dict[str, any], mock_cwd) -> None:
    """Test get_runtime_component_path returns correct component path."""
    # ARRANGE
    package_name: str = "testpackage"
    component: str = "config"
    deploy_dir: Path = Path(mock_bootstrap_config["bootstrap"]["paths"]["deployment_directory"])

    mock_cwd(str(deploy_dir))

    # ACT
    result: str = get_runtime_component_path(package_name, component)

    # ASSERT
    expected_path: str = str(deploy_dir / "packages" / package_name / component)
    assert result == expected_path


# -------------------------------------------------------------
# TESTS FOR convenience path functions
# -------------------------------------------------------------


def test_get_runtime_config_path_returns_config_directory(mock_bootstrap_config: Dict[str, any], mock_cwd) -> None:
    """Test get_runtime_config_path returns correct config directory path."""
    # ARRANGE
    package_name: str = "testpackage"
    deploy_dir: Path = Path(mock_bootstrap_config["bootstrap"]["paths"]["deployment_directory"])

    mock_cwd(str(deploy_dir))

    # ACT
    result: str = get_runtime_config_path(package_name)

    # ASSERT
    assert result.endswith("config")
    assert package_name in result


def test_get_runtime_log_path_returns_logs_directory(mock_bootstrap_config: Dict[str, any], mock_cwd) -> None:
    """Test get_runtime_log_path returns correct logs directory path."""
    # ARRANGE
    package_name: str = "testpackage"
    deploy_dir: Path = Path(mock_bootstrap_config["bootstrap"]["paths"]["deployment_directory"])

    mock_cwd(str(deploy_dir))

    # ACT
    result: str = get_runtime_log_path(package_name)

    # ASSERT
    assert result.endswith("logs")
    assert package_name in result


def test_get_runtime_template_path_returns_templates_config_directory(
    mock_bootstrap_config: Dict[str, any], mock_cwd
) -> None:
    """Test get_runtime_template_path returns correct templates/config directory path."""
    # ARRANGE
    package_name: str = "testpackage"
    deploy_dir: Path = Path(mock_bootstrap_config["bootstrap"]["paths"]["deployment_directory"])

    mock_cwd(str(deploy_dir))

    # ACT
    result: str = get_runtime_template_path(package_name)

    # ASSERT
    assert "templates" in result
    assert "config" in result
    assert package_name in result


# -------------------------------------------------------------
# TESTS FOR get_bootstrap_config_path
# -------------------------------------------------------------


def test_get_bootstrap_config_path_returns_constant() -> None:
    """Test get_bootstrap_config_path returns BOOTSTRAP_CONFIG_PATH constant."""
    # ACT
    result: str = get_bootstrap_config_path()

    # ASSERT
    assert result == BOOTSTRAP_CONFIG_PATH


# -------------------------------------------------------------
# TESTS FOR get_bootstrap_deployment_directory
# -------------------------------------------------------------


def test_get_bootstrap_deployment_directory_returns_configured_path(mock_bootstrap_config: Dict[str, any]) -> None:
    """Test get_bootstrap_deployment_directory returns configured deployment directory."""
    # ACT
    result: str = get_bootstrap_deployment_directory()

    # ASSERT
    expected: str = mock_bootstrap_config["bootstrap"]["paths"]["deployment_directory"]
    assert result == expected


def test_get_bootstrap_deployment_directory_returns_default_when_config_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test get_bootstrap_deployment_directory returns default when config is missing."""
    # ARRANGE
    nonexistent_file: Path = tmp_path / "nonexistent.json"
    monkeypatch.setattr("basefunctions.runtime.runtime_functions.BOOTSTRAP_CONFIG_PATH", str(nonexistent_file))

    # ACT
    result: str = get_bootstrap_deployment_directory()

    # ASSERT
    assert result == "~/.neuraldevelopment"


# -------------------------------------------------------------
# TESTS FOR get_bootstrap_development_directories
# -------------------------------------------------------------


def test_get_bootstrap_development_directories_returns_configured_paths(mock_bootstrap_config: Dict[str, any]) -> None:
    """Test get_bootstrap_development_directories returns configured development directories."""
    # ACT
    result: list = get_bootstrap_development_directories()

    # ASSERT
    expected: list = mock_bootstrap_config["bootstrap"]["paths"]["development_directories"]
    assert result == expected


def test_get_bootstrap_development_directories_returns_default_when_config_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test get_bootstrap_development_directories returns default when config is missing."""
    # ARRANGE
    nonexistent_file: Path = tmp_path / "nonexistent.json"
    monkeypatch.setattr("basefunctions.runtime.runtime_functions.BOOTSTRAP_CONFIG_PATH", str(nonexistent_file))

    # ACT
    result: list = get_bootstrap_development_directories()

    # ASSERT
    assert isinstance(result, list)
    assert len(result) > 0
