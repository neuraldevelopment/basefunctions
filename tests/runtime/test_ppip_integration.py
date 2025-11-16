"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.

 Description:
 Pytest test suite for ppip (PersonalPip) dependency resolution.
 Tests two-pass installation with local package dependencies and VenvUtils integration.

 Log:
 v1.0.0 : Initial test implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
# External imports
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List
from unittest.mock import Mock, patch, MagicMock

import pytest

# Project imports - import from bin/ppip.py as standalone module
# We'll mock the PersonalPip class methods directly

# -------------------------------------------------------------
# FIXTURES
# -------------------------------------------------------------


@pytest.fixture
def mock_bootstrap_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """
    Create mock bootstrap config file.

    Parameters
    ----------
    tmp_path : Path
        Pytest builtin fixture for temporary directory
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture

    Returns
    -------
    Path
        Path to deployment directory

    Notes
    -----
    Creates bootstrap.json with deployment directory configuration
    """
    # ARRANGE
    config_dir: Path = tmp_path / ".config" / "basefunctions"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file: Path = config_dir / "bootstrap.json"

    deploy_dir: Path = tmp_path / "deployment"
    deploy_dir.mkdir(parents=True, exist_ok=True)

    config_data = {
        "bootstrap": {
            "paths": {
                "deployment_directory": str(deploy_dir)
            }
        }
    }

    config_file.write_text(json.dumps(config_data), encoding="utf-8")

    # Patch BOOTSTRAP_CONFIG_PATH to use our temp config
    monkeypatch.setenv("HOME", str(tmp_path))

    # RETURN
    return deploy_dir


@pytest.fixture
def mock_packages_dir(mock_bootstrap_config: Path) -> Path:
    """
    Create mock packages directory structure.

    Parameters
    ----------
    mock_bootstrap_config : Path
        Deployment directory from bootstrap config fixture

    Returns
    -------
    Path
        Path to packages directory

    Notes
    -----
    Creates packages/ directory with sample package structures
    """
    # ARRANGE
    packages_dir: Path = mock_bootstrap_config / "packages"
    packages_dir.mkdir(parents=True, exist_ok=True)

    # RETURN
    return packages_dir


@pytest.fixture
def sample_package_with_deps(mock_packages_dir: Path) -> Path:
    """
    Create sample package with dependencies in pyproject.toml.

    Parameters
    ----------
    mock_packages_dir : Path
        Packages directory from fixture

    Returns
    -------
    Path
        Path to sample package directory

    Notes
    -----
    Creates package with pyproject.toml containing dependencies
    """
    # ARRANGE
    package_dir: Path = mock_packages_dir / "mypackage"
    package_dir.mkdir(parents=True)

    pyproject_content = """
[project]
name = "mypackage"
version = "1.0.0"
dependencies = [
    "requests>=2.28.0",
    "dep1>=1.0.0",
    "dep2==2.0.0",
    "dep3~=3.0",
    "dep4[extras]>=4.0.0",
]
"""
    pyproject_file: Path = package_dir / "pyproject.toml"
    pyproject_file.write_text(pyproject_content)

    # RETURN
    return package_dir


@pytest.fixture
def sample_package_no_deps(mock_packages_dir: Path) -> Path:
    """
    Create sample package without dependencies.

    Parameters
    ----------
    mock_packages_dir : Path
        Packages directory from fixture

    Returns
    -------
    Path
        Path to sample package directory

    Notes
    -----
    Creates package with pyproject.toml but no dependencies section
    """
    # ARRANGE
    package_dir: Path = mock_packages_dir / "simple_package"
    package_dir.mkdir(parents=True)

    pyproject_content = """
[project]
name = "simple_package"
version = "1.0.0"
"""
    pyproject_file: Path = package_dir / "pyproject.toml"
    pyproject_file.write_text(pyproject_content)

    # RETURN
    return package_dir


@pytest.fixture
def mock_ppip_instance(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """
    Create PersonalPip instance with mocked dependencies.

    Parameters
    ----------
    tmp_path : Path
        Pytest temporary path
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture

    Returns
    -------
    PersonalPip
        Mocked PersonalPip instance

    Notes
    -----
    Sets up mock bootstrap config and creates PersonalPip instance
    """
    # ARRANGE - Load ppip.py dynamically from repo structure
    import importlib.util
    test_file_path = Path(__file__)
    repo_root = test_file_path.parent.parent.parent  # tests/runtime/ -> tests/ -> basefunctions/
    ppip_path = repo_root / "bin" / "ppip.py"

    if not ppip_path.exists():
        pytest.fail(f"ppip.py not found at {ppip_path}")

    spec = importlib.util.spec_from_file_location("ppip", str(ppip_path))
    ppip_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ppip_module)

    # Setup mock config
    config_dir: Path = tmp_path / ".config" / "basefunctions"
    config_dir.mkdir(parents=True)
    config_file: Path = config_dir / "bootstrap.json"

    deploy_dir: Path = tmp_path / "deployment"
    deploy_dir.mkdir(parents=True, exist_ok=True)
    (deploy_dir / "packages").mkdir(parents=True)

    config_data = {
        "bootstrap": {
            "paths": {
                "deployment_directory": str(deploy_dir)
            }
        }
    }

    config_file.write_text(json.dumps(config_data), encoding="utf-8")

    # Patch BOOTSTRAP_CONFIG_PATH
    monkeypatch.setattr(ppip_module, "BOOTSTRAP_CONFIG_PATH", config_file)

    # Create instance
    ppip = ppip_module.PersonalPip()

    # Store reference to module for testing purposes
    ppip._ppip_module = ppip_module

    # RETURN
    return ppip


# -------------------------------------------------------------
# TESTS FOR _parse_local_package_dependencies
# -------------------------------------------------------------


def test_parse_dependencies_simple(mock_ppip_instance) -> None:
    """Test parsing dependencies from valid pyproject.toml."""
    # ARRANGE
    package_name = "mypackage"

    # Create package in ppip packages directory
    package_dir = mock_ppip_instance.packages_dir / package_name
    package_dir.mkdir(parents=True, exist_ok=True)

    pyproject_content = """
[project]
name = "mypackage"
version = "1.0.0"
dependencies = [
    "requests>=2.28.0",
    "pytest>=7.0.0",
]
"""
    (package_dir / "pyproject.toml").write_text(pyproject_content)

    # ACT
    result: List[str] = mock_ppip_instance._parse_local_package_dependencies(package_name)

    # ASSERT
    assert "requests" in result
    assert "pytest" in result
    assert len(result) == 2


def test_parse_dependencies_no_file(mock_ppip_instance) -> None:
    """Test handling missing pyproject.toml gracefully."""
    # ARRANGE
    package_name = "nonexistent_package"

    # ACT
    result: List[str] = mock_ppip_instance._parse_local_package_dependencies(package_name)

    # ASSERT
    assert result == []


def test_parse_dependencies_no_deps(mock_ppip_instance) -> None:
    """Test handling pyproject.toml without dependencies."""
    # ARRANGE
    package_name = "simple_package"

    package_dir = mock_ppip_instance.packages_dir / package_name
    package_dir.mkdir(parents=True)

    pyproject_content = """
[project]
name = "simple_package"
version = "1.0.0"
"""
    (package_dir / "pyproject.toml").write_text(pyproject_content)

    # ACT
    result: List[str] = mock_ppip_instance._parse_local_package_dependencies(package_name)

    # ASSERT
    assert result == []


def test_parse_dependencies_with_version_specs(mock_ppip_instance) -> None:
    """Test stripping version specifiers from dependencies."""
    # ARRANGE
    package_name = "versioned_package"

    package_dir = mock_ppip_instance.packages_dir / package_name
    package_dir.mkdir(parents=True)

    pyproject_content = """
[project]
name = "versioned_package"
version = "1.0.0"
dependencies = [
    "dep1>=1.0.0",
    "dep2==2.0.0",
    "dep3~=3.0.0",
    "dep4<5.0.0",
    "dep5>1.0.0",
]
"""
    (package_dir / "pyproject.toml").write_text(pyproject_content)

    # ACT
    result: List[str] = mock_ppip_instance._parse_local_package_dependencies(package_name)

    # ASSERT
    assert "dep1" in result
    assert "dep2" in result
    assert "dep3" in result
    assert "dep4" in result
    assert "dep5" in result
    # Ensure no version specs remain
    assert all(">" not in dep and "<" not in dep and "=" not in dep for dep in result)


def test_parse_dependencies_with_extras(mock_ppip_instance) -> None:
    """Test stripping extras like [dev] from dependencies."""
    # ARRANGE
    package_name = "extras_package"

    package_dir = mock_ppip_instance.packages_dir / package_name
    package_dir.mkdir(parents=True)

    pyproject_content = """
[project]
name = "extras_package"
version = "1.0.0"
dependencies = [
    "dep1[dev]>=1.0.0",
    "dep2[test,doc]>=2.0.0",
    "dep3",
]
"""
    (package_dir / "pyproject.toml").write_text(pyproject_content)

    # ACT
    result: List[str] = mock_ppip_instance._parse_local_package_dependencies(package_name)

    # ASSERT
    assert "dep1" in result
    assert "dep2" in result
    assert "dep3" in result
    # Ensure no extras remain
    assert all("[" not in dep for dep in result)


def test_parse_dependencies_no_tomli(mock_ppip_instance, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test handling missing tomllib/tomli gracefully."""
    # ARRANGE
    package_name = "test_package"

    package_dir = mock_ppip_instance.packages_dir / package_name
    package_dir.mkdir(parents=True)

    pyproject_content = """
[project]
name = "test_package"
version = "1.0.0"
dependencies = ["requests>=2.28.0"]
"""
    (package_dir / "pyproject.toml").write_text(pyproject_content)

    # Get the ppip module from the stored reference in the fixture
    ppip_module = mock_ppip_instance._ppip_module

    # Mock the module-level tomllib variable to None (simulating unavailable TOML parser)
    monkeypatch.setattr(ppip_module, "tomllib", None)

    # ACT
    result: List[str] = mock_ppip_instance._parse_local_package_dependencies(package_name)

    # ASSERT
    assert result == []  # Should return empty list when toml library unavailable


# -------------------------------------------------------------
# TESTS FOR install_packages_with_dependencies
# -------------------------------------------------------------


def test_install_with_dependencies_simple(mock_ppip_instance, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test installing package with one local dependency."""
    # ARRANGE
    # Create dep1 package (local)
    dep1_dir = mock_ppip_instance.packages_dir / "dep1"
    dep1_dir.mkdir(parents=True)
    (dep1_dir / "pyproject.toml").write_text("""
[project]
name = "dep1"
version = "1.0.0"
""")

    # Create main package with dep1 dependency
    main_dir = mock_ppip_instance.packages_dir / "mainpackage"
    main_dir.mkdir(parents=True)
    (main_dir / "pyproject.toml").write_text("""
[project]
name = "mainpackage"
version = "1.0.0"
dependencies = ["dep1>=1.0.0"]
""")

    # Mock virtual environment check
    monkeypatch.setattr(mock_ppip_instance, "is_in_virtual_env", lambda: True)

    # Mock install_package to track calls
    install_calls = []

    def mock_install(pkg_name):
        install_calls.append(pkg_name)
        return True

    monkeypatch.setattr(mock_ppip_instance, "install_package", mock_install)

    # ACT
    result: Dict[str, bool] = mock_ppip_instance.install_packages_with_dependencies(["mainpackage"])

    # ASSERT
    assert "dep1" in install_calls
    assert "mainpackage" in install_calls
    # dep1 should be installed before mainpackage
    assert install_calls.index("dep1") < install_calls.index("mainpackage")
    assert result["dep1"] is True
    assert result["mainpackage"] is True


def test_install_with_dependencies_multiple(mock_ppip_instance, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test installing multiple packages with shared dependencies."""
    # ARRANGE
    # Create shared dependency
    shared_dep_dir = mock_ppip_instance.packages_dir / "shared_dep"
    shared_dep_dir.mkdir(parents=True)
    (shared_dep_dir / "pyproject.toml").write_text("""
[project]
name = "shared_dep"
version = "1.0.0"
""")

    # Create pkg1 depending on shared_dep
    pkg1_dir = mock_ppip_instance.packages_dir / "pkg1"
    pkg1_dir.mkdir(parents=True)
    (pkg1_dir / "pyproject.toml").write_text("""
[project]
name = "pkg1"
version = "1.0.0"
dependencies = ["shared_dep>=1.0.0"]
""")

    # Create pkg2 depending on shared_dep
    pkg2_dir = mock_ppip_instance.packages_dir / "pkg2"
    pkg2_dir.mkdir(parents=True)
    (pkg2_dir / "pyproject.toml").write_text("""
[project]
name = "pkg2"
version = "1.0.0"
dependencies = ["shared_dep>=1.0.0"]
""")

    # Mock virtual environment check
    monkeypatch.setattr(mock_ppip_instance, "is_in_virtual_env", lambda: True)

    # Mock install_package
    install_calls = []

    def mock_install(pkg_name):
        install_calls.append(pkg_name)
        return True

    monkeypatch.setattr(mock_ppip_instance, "install_package", mock_install)

    # ACT
    result: Dict[str, bool] = mock_ppip_instance.install_packages_with_dependencies(["pkg1", "pkg2"])

    # ASSERT
    # shared_dep should be installed only once, before pkg1 and pkg2
    assert install_calls.count("shared_dep") == 1
    assert "shared_dep" in install_calls
    assert "pkg1" in install_calls
    assert "pkg2" in install_calls
    shared_dep_idx = install_calls.index("shared_dep")
    assert install_calls.index("pkg1") > shared_dep_idx
    assert install_calls.index("pkg2") > shared_dep_idx


def test_install_with_dependencies_already_installed(mock_ppip_instance, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test skipping already-installed packages."""
    # ARRANGE
    # Create dependency package
    dep_dir = mock_ppip_instance.packages_dir / "installed_dep"
    dep_dir.mkdir(parents=True)
    (dep_dir / "pyproject.toml").write_text("""
[project]
name = "installed_dep"
version = "1.0.0"
""")

    # Create main package
    main_dir = mock_ppip_instance.packages_dir / "mainpkg"
    main_dir.mkdir(parents=True)
    (main_dir / "pyproject.toml").write_text("""
[project]
name = "mainpkg"
version = "1.0.0"
dependencies = ["installed_dep>=1.0.0"]
""")

    # Mock virtual environment check
    monkeypatch.setattr(mock_ppip_instance, "is_in_virtual_env", lambda: True)

    # Mock get_installed_versions to show installed_dep already installed
    monkeypatch.setattr(
        mock_ppip_instance,
        "get_installed_versions",
        lambda: {"installed_dep": "1.0.0"}
    )

    # Mock install_package
    install_calls = []

    def mock_install(pkg_name):
        install_calls.append(pkg_name)
        return True

    monkeypatch.setattr(mock_ppip_instance, "install_package", mock_install)

    # ACT
    result: Dict[str, bool] = mock_ppip_instance.install_packages_with_dependencies(["mainpkg"])

    # ASSERT
    # installed_dep should NOT be installed (already present)
    assert "installed_dep" not in install_calls
    assert "mainpkg" in install_calls
    assert "installed_dep" not in result  # Not in results because skipped


def test_install_with_dependencies_no_local_deps(mock_ppip_instance, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test handling packages with no local dependencies."""
    # ARRANGE
    # Create package with only PyPI dependencies
    pkg_dir = mock_ppip_instance.packages_dir / "pypi_only_pkg"
    pkg_dir.mkdir(parents=True)
    (pkg_dir / "pyproject.toml").write_text("""
[project]
name = "pypi_only_pkg"
version = "1.0.0"
dependencies = ["requests>=2.28.0", "pytest>=7.0.0"]
""")

    # Mock virtual environment check
    monkeypatch.setattr(mock_ppip_instance, "is_in_virtual_env", lambda: True)

    # Mock install_package
    install_calls = []

    def mock_install(pkg_name):
        install_calls.append(pkg_name)
        return True

    monkeypatch.setattr(mock_ppip_instance, "install_package", mock_install)

    # ACT
    result: Dict[str, bool] = mock_ppip_instance.install_packages_with_dependencies(["pypi_only_pkg"])

    # ASSERT
    # Only main package should be installed (no local deps)
    assert install_calls == ["pypi_only_pkg"]
    assert result["pypi_only_pkg"] is True


def test_install_with_dependencies_not_in_venv(mock_ppip_instance, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test raising error when not in virtual environment."""
    # ARRANGE
    # Mock virtual environment check to return False
    monkeypatch.setattr(mock_ppip_instance, "is_in_virtual_env", lambda: False)

    # ACT & ASSERT
    # The specific exception type is PersonalPipError but since it's dynamically loaded
    # we test for Exception base class with the expected message
    with pytest.raises(Exception, match="Not in virtual environment"):
        mock_ppip_instance.install_packages_with_dependencies(["anypackage"])


# -------------------------------------------------------------
# TESTS FOR VenvUtils.install_with_ppip
# -------------------------------------------------------------


def test_install_with_ppip_available(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test using ppip when available via venv python."""
    # ARRANGE
    from basefunctions.runtime.venv_utils import VenvUtils

    packages: List[str] = ["testpackage"]
    venv_path: Path = tmp_path / ".venv"

    # Mock shutil.which to return ppip path
    mock_ppip_path = "/usr/local/bin/ppip"
    monkeypatch.setattr("shutil.which", lambda cmd: mock_ppip_path if cmd == "ppip" else None)

    # Mock subprocess.run
    mock_run: Mock = Mock()
    mock_run.return_value = Mock(returncode=0)
    monkeypatch.setattr("subprocess.run", mock_run)

    # ACT
    VenvUtils.install_with_ppip(packages, venv_path)

    # ASSERT
    assert mock_run.called
    call_args = mock_run.call_args[0][0]
    # ppip is now called via venv's python: [venv_python, ppip_path, "install", packages...]
    assert str(call_args[0]).endswith("/bin/python")  # venv python
    assert call_args[1] == mock_ppip_path  # ppip path
    assert call_args[2] == "install"
    assert "testpackage" in call_args


def test_install_with_ppip_not_available_fallback(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test fallback to pip when ppip not found."""
    # ARRANGE
    from basefunctions.runtime.venv_utils import VenvUtils

    packages: List[str] = ["testpackage"]
    venv_path: Path = tmp_path / ".venv"

    # Create mock venv structure
    bin_dir = venv_path / "bin"
    bin_dir.mkdir(parents=True)
    (bin_dir / "pip").write_text("#!/bin/bash\necho pip")

    # Mock shutil.which to return None (ppip not found)
    monkeypatch.setattr("shutil.which", lambda cmd: None)

    # Mock run_pip_command
    run_pip_command_calls = []

    def mock_run_pip_command(command, venv, **kwargs):
        run_pip_command_calls.append((command, venv))
        return Mock(returncode=0)

    monkeypatch.setattr(VenvUtils, "run_pip_command", mock_run_pip_command)

    # ACT
    VenvUtils.install_with_ppip(packages, venv_path, fallback_to_pip=True)

    # ASSERT
    assert len(run_pip_command_calls) == 1
    command, venv = run_pip_command_calls[0]
    assert command == ["install", "testpackage"]
    assert venv == venv_path


def test_install_with_ppip_not_available_no_fallback(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test raising error when ppip not found and fallback disabled."""
    # ARRANGE
    from basefunctions.runtime.venv_utils import VenvUtils, VenvUtilsError

    packages: List[str] = ["testpackage"]
    venv_path: Path = tmp_path / ".venv"

    # Mock shutil.which to return None (ppip not found)
    monkeypatch.setattr("shutil.which", lambda cmd: None)

    # ACT & ASSERT
    with pytest.raises(VenvUtilsError, match="ppip not found and fallback disabled"):
        VenvUtils.install_with_ppip(packages, venv_path, fallback_to_pip=False)


def test_install_with_ppip_raises_on_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test raising VenvUtilsError when ppip installation fails."""
    # ARRANGE
    from basefunctions.runtime.venv_utils import VenvUtils, VenvUtilsError

    packages: List[str] = ["testpackage"]
    venv_path: Path = tmp_path / ".venv"

    # Mock shutil.which to return ppip path
    mock_ppip_path = "/usr/local/bin/ppip"
    monkeypatch.setattr("shutil.which", lambda cmd: mock_ppip_path if cmd == "ppip" else None)

    # Mock subprocess.run to raise CalledProcessError
    monkeypatch.setattr(
        "subprocess.run",
        Mock(side_effect=subprocess.CalledProcessError(1, "ppip"))
    )

    # ACT & ASSERT
    with pytest.raises(VenvUtilsError, match="ppip installation failed"):
        VenvUtils.install_with_ppip(packages, venv_path)


def test_install_with_ppip_raises_on_timeout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test raising VenvUtilsError when ppip installation times out."""
    # ARRANGE
    from basefunctions.runtime.venv_utils import VenvUtils, VenvUtilsError

    packages: List[str] = ["testpackage"]
    venv_path: Path = tmp_path / ".venv"

    # Mock shutil.which to return ppip path
    mock_ppip_path = "/usr/local/bin/ppip"
    monkeypatch.setattr("shutil.which", lambda cmd: mock_ppip_path if cmd == "ppip" else None)

    # Mock subprocess.run to raise TimeoutExpired
    monkeypatch.setattr(
        "subprocess.run",
        Mock(side_effect=subprocess.TimeoutExpired("ppip", 300))
    )

    # ACT & ASSERT
    with pytest.raises(VenvUtilsError, match="ppip installation timed out"):
        VenvUtils.install_with_ppip(packages, venv_path)


def test_install_with_ppip_with_multiple_packages(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test installing multiple packages with ppip."""
    # ARRANGE
    from basefunctions.runtime.venv_utils import VenvUtils

    packages: List[str] = ["package1", "package2", "package3"]
    venv_path: Path = tmp_path / ".venv"

    # Mock shutil.which to return ppip path
    mock_ppip_path = "/usr/local/bin/ppip"
    monkeypatch.setattr("shutil.which", lambda cmd: mock_ppip_path if cmd == "ppip" else None)

    # Mock subprocess.run
    mock_run: Mock = Mock()
    mock_run.return_value = Mock(returncode=0)
    monkeypatch.setattr("subprocess.run", mock_run)

    # ACT
    VenvUtils.install_with_ppip(packages, venv_path)

    # ASSERT
    assert mock_run.called
    call_args = mock_run.call_args[0][0]
    assert "package1" in call_args
    assert "package2" in call_args
    assert "package3" in call_args


# -------------------------------------------------------------
# TESTS FOR edge cases and error conditions
# -------------------------------------------------------------


def test_parse_dependencies_invalid_toml(mock_ppip_instance) -> None:
    """Test handling invalid TOML gracefully."""
    # ARRANGE
    package_name = "invalid_toml_package"

    package_dir = mock_ppip_instance.packages_dir / package_name
    package_dir.mkdir(parents=True)

    # Write invalid TOML
    (package_dir / "pyproject.toml").write_text("invalid toml content [[[")

    # ACT
    result: List[str] = mock_ppip_instance._parse_local_package_dependencies(package_name)

    # ASSERT
    assert result == []  # Should return empty list on parse error


def test_install_with_dependencies_mixed_local_and_pypi(mock_ppip_instance, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test installing package with both local and PyPI dependencies."""
    # ARRANGE
    # Create local dependency
    local_dep_dir = mock_ppip_instance.packages_dir / "local_dep"
    local_dep_dir.mkdir(parents=True)
    (local_dep_dir / "pyproject.toml").write_text("""
[project]
name = "local_dep"
version = "1.0.0"
""")

    # Create main package with mixed dependencies
    main_dir = mock_ppip_instance.packages_dir / "mixed_pkg"
    main_dir.mkdir(parents=True)
    (main_dir / "pyproject.toml").write_text("""
[project]
name = "mixed_pkg"
version = "1.0.0"
dependencies = [
    "local_dep>=1.0.0",
    "requests>=2.28.0",
    "pytest>=7.0.0",
]
""")

    # Mock virtual environment check
    monkeypatch.setattr(mock_ppip_instance, "is_in_virtual_env", lambda: True)

    # Mock install_package
    install_calls = []

    def mock_install(pkg_name):
        install_calls.append(pkg_name)
        return True

    monkeypatch.setattr(mock_ppip_instance, "install_package", mock_install)

    # ACT
    result: Dict[str, bool] = mock_ppip_instance.install_packages_with_dependencies(["mixed_pkg"])

    # ASSERT
    # Only local_dep should be in dependency install phase
    assert "local_dep" in install_calls
    assert "mixed_pkg" in install_calls
    # requests and pytest are PyPI-only, handled by pip during main package install
    assert "requests" not in install_calls
    assert "pytest" not in install_calls


def test_install_with_dependencies_circular_dependencies(mock_ppip_instance, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test handling circular dependencies gracefully."""
    # ARRANGE
    # Create pkg1 depending on pkg2
    pkg1_dir = mock_ppip_instance.packages_dir / "circular_pkg1"
    pkg1_dir.mkdir(parents=True)
    (pkg1_dir / "pyproject.toml").write_text("""
[project]
name = "circular_pkg1"
version = "1.0.0"
dependencies = ["circular_pkg2>=1.0.0"]
""")

    # Create pkg2 depending on pkg1 (circular)
    pkg2_dir = mock_ppip_instance.packages_dir / "circular_pkg2"
    pkg2_dir.mkdir(parents=True)
    (pkg2_dir / "pyproject.toml").write_text("""
[project]
name = "circular_pkg2"
version = "1.0.0"
dependencies = ["circular_pkg1>=1.0.0"]
""")

    # Mock virtual environment check
    monkeypatch.setattr(mock_ppip_instance, "is_in_virtual_env", lambda: True)

    # Mock install_package
    install_calls = []

    def mock_install(pkg_name):
        install_calls.append(pkg_name)
        return True

    monkeypatch.setattr(mock_ppip_instance, "install_package", mock_install)

    # ACT
    result: Dict[str, bool] = mock_ppip_instance.install_packages_with_dependencies(["circular_pkg1"])

    # ASSERT
    # Should handle gracefully - circular_pkg2 will be installed as dependency
    # Then circular_pkg1 installed (which may trigger re-install of circular_pkg2)
    # At minimum, both should appear in results
    assert "circular_pkg1" in install_calls or "circular_pkg1" in result
    assert "circular_pkg2" in install_calls or "circular_pkg2" in result


def test_install_with_dependencies_empty_package_list(mock_ppip_instance, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test installing with empty package list."""
    # ARRANGE
    monkeypatch.setattr(mock_ppip_instance, "is_in_virtual_env", lambda: True)

    # ACT
    result: Dict[str, bool] = mock_ppip_instance.install_packages_with_dependencies([])

    # ASSERT
    assert result == {}


def test_install_with_ppip_none_venv_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test install_with_ppip with None venv_path (uses current environment)."""
    # ARRANGE
    from basefunctions.runtime.venv_utils import VenvUtils

    packages: List[str] = ["testpackage"]

    # Mock shutil.which to return ppip path
    mock_ppip_path = "/usr/local/bin/ppip"
    monkeypatch.setattr("shutil.which", lambda cmd: mock_ppip_path if cmd == "ppip" else None)

    # Mock subprocess.run
    mock_run: Mock = Mock()
    mock_run.return_value = Mock(returncode=0)
    monkeypatch.setattr("subprocess.run", mock_run)

    # ACT
    VenvUtils.install_with_ppip(packages, venv_path=None)

    # ASSERT
    assert mock_run.called
    call_args = mock_run.call_args[0][0]
    assert mock_ppip_path in call_args
