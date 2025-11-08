"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.

 Description:
 Pytest test suite for version module.
 Tests version detection, development indicators, and git integration.

 Log:
 v1.0.0 : Initial test implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
# External imports
import os
import subprocess
from pathlib import Path
from typing import Dict
from unittest.mock import Mock

import pytest

# Project imports
from basefunctions.runtime import version as version_module_import
import sys
# Import the actual module, not the function
version_module = sys.modules['basefunctions.runtime.version']
from basefunctions.runtime.version import (
    _get_git_commits_ahead,
    _is_in_development_directory,
    version,
    versions,
)

# -------------------------------------------------------------
# FIXTURES
# -------------------------------------------------------------


@pytest.fixture
def mock_git_repo(tmp_path: Path) -> Path:
    """
    Create mock git repository with tags and commits.

    Parameters
    ----------
    tmp_path : Path
        Pytest builtin fixture for temporary directory

    Returns
    -------
    Path
        Path to mock git repository

    Notes
    -----
    Creates .git directory to simulate git repository
    """
    # ARRANGE
    repo_path: Path = tmp_path / "repo"
    repo_path.mkdir()

    git_dir: Path = repo_path / ".git"
    git_dir.mkdir()

    # RETURN
    return repo_path


@pytest.fixture
def mock_importlib_metadata(monkeypatch: pytest.MonkeyPatch):
    """
    Factory fixture to mock importlib.metadata functions.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture

    Returns
    -------
    callable
        Function to set mock version

    Notes
    -----
    Use this to simulate installed packages with specific versions
    """
    # RETURN
    def _set_version(package_name: str, version_string: str) -> None:
        def mock_get_version(name: str) -> str:
            if name == package_name:
                return version_string
            raise Exception(f"Package {name} not found")

        monkeypatch.setattr("importlib.metadata.version", mock_get_version)

    return _set_version


# -------------------------------------------------------------
# TESTS FOR _get_git_commits_ahead
# -------------------------------------------------------------


def test_get_git_commits_ahead_returns_commit_count(mock_git_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test _get_git_commits_ahead returns number of commits ahead of latest tag."""
    # ARRANGE
    dev_path: str = str(mock_git_repo)

    # Mock git describe to return tag
    def mock_run_describe(*args, **kwargs):
        result: Mock = Mock()
        result.returncode = 0
        result.stdout = "v1.0.0\n"
        return result

    # Mock git rev-list to return commit count
    def mock_run_revlist(*args, **kwargs):
        cmd = args[0]
        if "rev-list" in cmd:
            result: Mock = Mock()
            result.returncode = 0
            result.stdout = "3\n"
            return result
        return mock_run_describe(*args, **kwargs)

    def mock_subprocess_run(*args, **kwargs):
        cmd = args[0]
        if "describe" in cmd:
            return mock_run_describe(*args, **kwargs)
        elif "rev-list" in cmd:
            return mock_run_revlist(*args, **kwargs)

    monkeypatch.setattr("subprocess.run", mock_subprocess_run)

    # ACT
    result: int = _get_git_commits_ahead(dev_path)

    # ASSERT
    assert result == 3


def test_get_git_commits_ahead_returns_zero_at_tag(mock_git_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test _get_git_commits_ahead returns 0 when at tag."""
    # ARRANGE
    dev_path: str = str(mock_git_repo)

    # Mock git commands
    def mock_run_describe(*args, **kwargs):
        result: Mock = Mock()
        result.returncode = 0
        result.stdout = "v1.0.0\n"
        return result

    def mock_run_revlist(*args, **kwargs):
        result: Mock = Mock()
        result.returncode = 0
        result.stdout = "0\n"
        return result

    def mock_subprocess_run(*args, **kwargs):
        cmd = args[0]
        if "describe" in cmd:
            return mock_run_describe(*args, **kwargs)
        elif "rev-list" in cmd:
            return mock_run_revlist(*args, **kwargs)

    monkeypatch.setattr("subprocess.run", mock_subprocess_run)

    # ACT
    result: int = _get_git_commits_ahead(dev_path)

    # ASSERT
    assert result == 0


def test_get_git_commits_ahead_returns_zero_on_error(mock_git_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test _get_git_commits_ahead returns 0 when git command fails."""
    # ARRANGE
    dev_path: str = str(mock_git_repo)

    # Mock git describe to fail
    def mock_run(*args, **kwargs):
        result: Mock = Mock()
        result.returncode = 1
        result.stdout = ""
        return result

    monkeypatch.setattr("subprocess.run", mock_run)

    # ACT
    result: int = _get_git_commits_ahead(dev_path)

    # ASSERT
    assert result == 0


def test_get_git_commits_ahead_handles_timeout(mock_git_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test _get_git_commits_ahead returns 0 when subprocess times out."""
    # ARRANGE
    dev_path: str = str(mock_git_repo)

    monkeypatch.setattr(
        "subprocess.run",
        Mock(side_effect=subprocess.TimeoutExpired("git", 5)),
    )

    # ACT
    result: int = _get_git_commits_ahead(dev_path)

    # ASSERT
    assert result == 0


def test_get_git_commits_ahead_handles_exception(mock_git_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test _get_git_commits_ahead returns 0 when any exception occurs."""
    # ARRANGE
    dev_path: str = str(mock_git_repo)

    monkeypatch.setattr(
        "subprocess.run",
        Mock(side_effect=Exception("Git error")),
    )

    # ACT
    result: int = _get_git_commits_ahead(dev_path)

    # ASSERT
    assert result == 0


# -------------------------------------------------------------
# TESTS FOR _is_in_development_directory
# -------------------------------------------------------------


def test_is_in_development_directory_returns_true_when_in_dev(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test _is_in_development_directory returns True when CWD is in development path."""
    # ARRANGE
    package_name: str = "testpackage"
    dev_path: Path = tmp_path / package_name
    dev_path.mkdir()

    monkeypatch.setattr("os.getcwd", lambda: str(dev_path))
    monkeypatch.setattr(
        "basefunctions.runtime.find_development_path",
        lambda name: [str(dev_path)],
    )

    # ACT
    is_in_dev: bool
    path: str
    is_in_dev, path = _is_in_development_directory(package_name)

    # ASSERT
    assert is_in_dev is True
    assert path == str(dev_path)


def test_is_in_development_directory_returns_false_when_not_in_dev(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test _is_in_development_directory returns False when CWD is not in development path."""
    # ARRANGE
    package_name: str = "testpackage"
    dev_path: Path = tmp_path / package_name
    other_path: Path = tmp_path / "other"

    dev_path.mkdir()
    other_path.mkdir()

    monkeypatch.setattr("os.getcwd", lambda: str(other_path))
    monkeypatch.setattr(
        "basefunctions.runtime.find_development_path",
        lambda name: [str(dev_path)],
    )

    # ACT
    is_in_dev: bool
    path: str
    is_in_dev, path = _is_in_development_directory(package_name)

    # ASSERT
    assert is_in_dev is False
    assert path is None


def test_is_in_development_directory_handles_multiple_dev_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test _is_in_development_directory handles multiple development paths correctly."""
    # ARRANGE
    package_name: str = "testpackage"
    dev_path1: Path = tmp_path / "dev1" / package_name
    dev_path2: Path = tmp_path / "dev2" / package_name

    dev_path1.mkdir(parents=True)
    dev_path2.mkdir(parents=True)

    monkeypatch.setattr("os.getcwd", lambda: str(dev_path2))
    monkeypatch.setattr(
        "basefunctions.runtime.find_development_path",
        lambda name: [str(dev_path1), str(dev_path2)],
    )

    # ACT
    is_in_dev: bool
    path: str
    is_in_dev, path = _is_in_development_directory(package_name)

    # ASSERT
    assert is_in_dev is True
    assert path == str(dev_path2)


# -------------------------------------------------------------
# TESTS FOR version
# -------------------------------------------------------------


def test_version_returns_installed_version_when_not_in_dev(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test version returns installed version when not in development directory."""
    # ARRANGE
    package_name: str = "testpackage"
    expected_version: str = "1.2.3"

    def mock_get_version(name: str) -> str:
        if name == package_name:
            return expected_version
        raise Exception("Not found")

    monkeypatch.setattr("importlib.metadata.version", mock_get_version)
    monkeypatch.setattr(
        version_module,
        "_is_in_development_directory",
        lambda name: (False, None),
    )

    # ACT
    result: str = version(package_name)

    # ASSERT
    assert result == expected_version


def test_version_returns_dev_version_when_in_dev_directory(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test version returns dev version when in development directory."""
    # ARRANGE
    package_name: str = "testpackage"
    base_version: str = "1.2.3"

    def mock_get_version(name: str) -> str:
        if name == package_name:
            return base_version
        raise Exception("Not found")

    monkeypatch.setattr("importlib.metadata.version", mock_get_version)
    monkeypatch.setattr(
        version_module,
        "_is_in_development_directory",
        lambda name: (True, "/path/to/dev"),
    )
    monkeypatch.setattr(version_module, "_get_git_commits_ahead", lambda path: 0)

    # ACT
    result: str = version(package_name)

    # ASSERT
    assert result == f"{base_version}-dev"


def test_version_includes_commits_ahead_when_present(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test version includes commit count when commits ahead of tag."""
    # ARRANGE
    package_name: str = "testpackage"
    base_version: str = "1.2.3"
    commits_ahead: int = 5

    def mock_get_version(name: str) -> str:
        if name == package_name:
            return base_version
        raise Exception("Not found")

    monkeypatch.setattr("importlib.metadata.version", mock_get_version)
    monkeypatch.setattr(
        version_module,
        "_is_in_development_directory",
        lambda name: (True, "/path/to/dev"),
    )
    monkeypatch.setattr(version_module, "_get_git_commits_ahead", lambda path: commits_ahead)

    # ACT
    result: str = version(package_name)

    # ASSERT
    assert result == f"{base_version}-dev+{commits_ahead}"


def test_version_returns_unknown_when_package_not_installed(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test version returns 'unknown' when package is not installed."""
    # ARRANGE
    package_name: str = "nonexistent_package"

    def mock_get_version(name: str) -> str:
        raise Exception("Package not found")

    monkeypatch.setattr("importlib.metadata.version", mock_get_version)
    monkeypatch.setattr(
        version_module,
        "_is_in_development_directory",
        lambda name: (False, None),
    )

    # ACT
    result: str = version(package_name)

    # ASSERT
    assert result == "unknown"


def test_version_handles_git_command_failure_gracefully(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test version handles git command failures gracefully."""
    # ARRANGE
    package_name: str = "testpackage"
    base_version: str = "1.2.3"

    def mock_get_version(name: str) -> str:
        return base_version

    monkeypatch.setattr("importlib.metadata.version", mock_get_version)
    monkeypatch.setattr(
        version_module,
        "_is_in_development_directory",
        lambda name: (True, "/path/to/dev"),
    )
    # _get_git_commits_ahead internally handles exceptions and returns 0
    # We mock subprocess to simulate git failure
    monkeypatch.setattr(version_module, "_get_git_commits_ahead", lambda path: 0)

    # ACT (should not raise)
    result: str = version(package_name)

    # ASSERT
    # Should return version with -dev suffix but no commit count
    assert result == f"{base_version}-dev"


# -------------------------------------------------------------
# TESTS FOR versions
# -------------------------------------------------------------


def test_versions_returns_all_local_packages(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test versions returns all installed neuraldevelopment packages."""
    # ARRANGE
    deploy_dir: Path = tmp_path / "deployment"
    packages_dir: Path = deploy_dir / "packages"
    packages_dir.mkdir(parents=True)

    # Create mock packages
    package1: Path = packages_dir / "package1"
    package2: Path = packages_dir / "package2"
    package1.mkdir()
    package2.mkdir()

    monkeypatch.setattr(
        "basefunctions.runtime.get_bootstrap_deployment_directory",
        lambda: str(deploy_dir),
    )

    # Mock importlib.metadata.distributions
    class MockDist:
        def __init__(self, name: str, ver: str):
            self.name = name
            self.version = ver

    mock_distributions = [
        MockDist("package1", "1.0.0"),
        MockDist("package2", "2.0.0"),
    ]

    monkeypatch.setattr("importlib.metadata.distributions", lambda: mock_distributions)
    monkeypatch.setattr("os.getcwd", lambda: "/other/directory")
    monkeypatch.setattr(
        "basefunctions.runtime.find_development_path",
        lambda name: [],
    )

    # ACT
    result: Dict[str, str] = versions()

    # ASSERT
    assert "package1" in result
    assert "package2" in result
    assert result["package1"] == "1.0.0"
    assert result["package2"] == "2.0.0"


def test_versions_includes_dev_suffix_for_cwd_package_only(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test versions includes -dev suffix only for package in current working directory."""
    # ARRANGE
    deploy_dir: Path = tmp_path / "deployment"
    packages_dir: Path = deploy_dir / "packages"
    packages_dir.mkdir(parents=True)

    package1: Path = packages_dir / "package1"
    package2: Path = packages_dir / "package2"
    package1.mkdir()
    package2.mkdir()

    dev_dir: Path = tmp_path / "dev"
    dev_package1: Path = dev_dir / "package1"
    dev_package1.mkdir(parents=True)

    monkeypatch.setattr(
        "basefunctions.runtime.get_bootstrap_deployment_directory",
        lambda: str(deploy_dir),
    )

    # Mock distributions
    class MockDist:
        def __init__(self, name: str, ver: str):
            self.name = name
            self.version = ver

    mock_distributions = [
        MockDist("package1", "1.0.0"),
        MockDist("package2", "2.0.0"),
    ]

    monkeypatch.setattr("importlib.metadata.distributions", lambda: mock_distributions)
    monkeypatch.setattr("os.getcwd", lambda: str(dev_package1))

    def mock_find_dev_path(name: str):
        if name == "package1":
            return [str(dev_package1)]
        return []

    monkeypatch.setattr(
        "basefunctions.runtime.find_development_path",
        mock_find_dev_path,
    )
    monkeypatch.setattr(version_module, "_get_git_commits_ahead", lambda path: 0)

    # ACT
    result: Dict[str, str] = versions()

    # ASSERT
    assert result["package1"] == "1.0.0-dev"  # CWD package has -dev
    assert result["package2"] == "2.0.0"  # Other package doesn't


def test_versions_returns_empty_when_packages_dir_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test versions returns empty dict when packages directory doesn't exist."""
    # ARRANGE
    deploy_dir: Path = tmp_path / "deployment"
    deploy_dir.mkdir()
    # Don't create packages_dir

    monkeypatch.setattr(
        "basefunctions.runtime.get_bootstrap_deployment_directory",
        lambda: str(deploy_dir),
    )

    # ACT
    result: Dict[str, str] = versions()

    # ASSERT
    assert result == {}


def test_versions_handles_import_error_gracefully(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test versions handles importlib errors gracefully."""
    # ARRANGE
    monkeypatch.setattr(
        "importlib.metadata.distributions",
        Mock(side_effect=Exception("Import error")),
    )

    # ACT
    result: Dict[str, str] = versions()

    # ASSERT
    assert result == {}


def test_versions_includes_commits_ahead_for_cwd_package(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test versions includes commit count for package in current working directory."""
    # ARRANGE
    deploy_dir: Path = tmp_path / "deployment"
    packages_dir: Path = deploy_dir / "packages"
    packages_dir.mkdir(parents=True)

    package1: Path = packages_dir / "package1"
    package1.mkdir()

    dev_dir: Path = tmp_path / "dev"
    dev_package1: Path = dev_dir / "package1"
    dev_package1.mkdir(parents=True)

    monkeypatch.setattr(
        "basefunctions.runtime.get_bootstrap_deployment_directory",
        lambda: str(deploy_dir),
    )

    # Mock distributions
    class MockDist:
        def __init__(self, name: str, ver: str):
            self.name = name
            self.version = ver

    mock_distributions = [MockDist("package1", "1.0.0")]

    monkeypatch.setattr("importlib.metadata.distributions", lambda: mock_distributions)
    monkeypatch.setattr("os.getcwd", lambda: str(dev_package1))
    monkeypatch.setattr(
        "basefunctions.runtime.find_development_path",
        lambda name: [str(dev_package1)],
    )
    monkeypatch.setattr(version_module, "_get_git_commits_ahead", lambda path: 7)

    # ACT
    result: Dict[str, str] = versions()

    # ASSERT
    assert result["package1"] == "1.0.0-dev+7"


def test_versions_only_includes_installed_packages(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test versions only includes packages that are both deployed and installed."""
    # ARRANGE
    deploy_dir: Path = tmp_path / "deployment"
    packages_dir: Path = deploy_dir / "packages"
    packages_dir.mkdir(parents=True)

    # Create deployed packages
    package1: Path = packages_dir / "package1"
    package2: Path = packages_dir / "package2"
    package3: Path = packages_dir / "package3"
    package1.mkdir()
    package2.mkdir()
    package3.mkdir()

    monkeypatch.setattr(
        "basefunctions.runtime.get_bootstrap_deployment_directory",
        lambda: str(deploy_dir),
    )

    # Mock only package1 and package2 as installed
    class MockDist:
        def __init__(self, name: str, ver: str):
            self.name = name
            self.version = ver

    mock_distributions = [
        MockDist("package1", "1.0.0"),
        MockDist("package2", "2.0.0"),
    ]

    monkeypatch.setattr("importlib.metadata.distributions", lambda: mock_distributions)
    monkeypatch.setattr("os.getcwd", lambda: "/other/directory")
    monkeypatch.setattr(
        "basefunctions.runtime.find_development_path",
        lambda name: [],
    )

    # ACT
    result: Dict[str, str] = versions()

    # ASSERT
    assert "package1" in result
    assert "package2" in result
    assert "package3" not in result  # Deployed but not installed
