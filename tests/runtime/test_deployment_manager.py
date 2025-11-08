"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.

 Description:
 Pytest test suite for DeploymentManager.
 Tests module deployment logic, change detection, and deployment operations.

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
from typing import Any, Dict, List
from unittest.mock import Mock, MagicMock, patch, call

import pytest

# Project imports
from basefunctions.runtime.deployment_manager import DeploymentManager, DeploymentError
from basefunctions.runtime.venv_utils import VenvUtilsError

# -------------------------------------------------------------
# FIXTURES
# -------------------------------------------------------------


@pytest.fixture
def mock_module_structure(tmp_path: Path) -> Dict[str, Any]:
    """
    Create complete mock module structure for testing.

    Parameters
    ----------
    tmp_path : Path
        Pytest builtin fixture for temporary directory

    Returns
    -------
    Dict[str, Any]
        Dictionary containing paths and structure information

    Notes
    -----
    Creates src/, bin/, templates/, .venv/ directories with sample files
    """
    # ARRANGE
    module_name: str = "testmodule"
    module_path: Path = tmp_path / module_name

    # Create directory structure
    src_dir: Path = module_path / "src" / module_name
    bin_dir: Path = module_path / "bin"
    templates_dir: Path = module_path / "templates" / "config"
    venv_dir: Path = module_path / ".venv" / "bin"

    src_dir.mkdir(parents=True)
    bin_dir.mkdir(parents=True)
    templates_dir.mkdir(parents=True)
    venv_dir.mkdir(parents=True)

    # Create sample files
    (src_dir / "__init__.py").write_text("# test module")
    (bin_dir / "test_tool.py").write_text("#!/usr/bin/env python\nprint('test')")
    (templates_dir / "config.json").write_text('{"test": true}')
    (venv_dir / "pip").write_text("#!/bin/bash\necho pip")
    (venv_dir / "python").write_text("#!/bin/bash\necho python")
    (module_path / "pyproject.toml").write_text('[project]\nname = "testmodule"\ndependencies = []')

    # RETURN
    return {
        "module_name": module_name,
        "module_path": module_path,
        "src_dir": src_dir,
        "bin_dir": bin_dir,
        "templates_dir": templates_dir,
        "venv_dir": venv_dir.parent,
    }


@pytest.fixture
def mock_deployment_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """
    Mock deployment directory with bootstrap config.

    Parameters
    ----------
    tmp_path : Path
        Pytest builtin fixture for temporary directory
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture

    Returns
    -------
    Path
        Deployment directory path

    Notes
    -----
    Patches basefunctions.runtime functions to use temporary directory
    """
    # ARRANGE
    deploy_dir: Path = tmp_path / "deployment"
    deploy_dir.mkdir(parents=True)

    packages_dir: Path = deploy_dir / "packages"
    packages_dir.mkdir()

    bin_dir: Path = deploy_dir / "bin"
    bin_dir.mkdir()

    hashes_dir: Path = deploy_dir / "deployment" / "hashes"
    hashes_dir.mkdir(parents=True)

    # Mock bootstrap functions
    monkeypatch.setattr(
        "basefunctions.runtime.deployment_manager.basefunctions.runtime.get_bootstrap_deployment_directory",
        lambda: str(deploy_dir),
    )
    monkeypatch.setattr(
        "basefunctions.runtime.deployment_manager.basefunctions.runtime.get_deployment_path",
        lambda name: str(packages_dir / name),
    )

    # RETURN
    return deploy_dir


@pytest.fixture
def deployment_manager() -> DeploymentManager:
    """
    Create fresh DeploymentManager instance.

    Returns
    -------
    DeploymentManager
        Fresh DeploymentManager instance

    Notes
    -----
    Due to singleton pattern, this returns the same instance but ensures it's initialized
    """
    # RETURN
    return DeploymentManager()


# -------------------------------------------------------------
# TESTS FOR deploy_module
# -------------------------------------------------------------


def test_deploy_module_raises_error_when_module_name_empty(deployment_manager: DeploymentManager) -> None:  # CRITICAL TEST
    """Test deploy_module raises DeploymentError when module name is empty string."""
    # ARRANGE
    empty_name: str = ""

    # ACT & ASSERT
    with pytest.raises(DeploymentError, match="Module name must be provided"):
        deployment_manager.deploy_module(empty_name)


def test_deploy_module_raises_error_when_module_name_none(deployment_manager: DeploymentManager) -> None:  # CRITICAL TEST
    """Test deploy_module raises DeploymentError when module name is None."""
    # ARRANGE
    none_name: None = None

    # ACT & ASSERT
    with pytest.raises(DeploymentError, match="Module name must be provided"):
        deployment_manager.deploy_module(none_name)


def test_deploy_module_raises_error_when_module_not_found(
    deployment_manager: DeploymentManager, monkeypatch: pytest.MonkeyPatch
) -> None:  # CRITICAL TEST
    """Test deploy_module raises DeploymentError when module not found in development directories."""
    # ARRANGE
    module_name: str = "nonexistent_module"
    monkeypatch.setattr(
        "basefunctions.runtime.deployment_manager.basefunctions.runtime.find_development_path",
        lambda name: [],
    )

    # ACT & ASSERT
    with pytest.raises(DeploymentError, match="Module .* not found in any development directory"):
        deployment_manager.deploy_module(module_name)


def test_deploy_module_raises_error_when_not_in_dev_directory(
    deployment_manager: DeploymentManager, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:  # CRITICAL TEST
    """Test deploy_module raises DeploymentError when user not in development directory."""
    # ARRANGE
    module_name: str = "testmodule"
    dev_path: Path = tmp_path / module_name
    dev_path.mkdir()

    wrong_cwd: Path = tmp_path / "other_directory"
    wrong_cwd.mkdir()

    monkeypatch.setattr("os.getcwd", lambda: str(wrong_cwd))
    monkeypatch.setattr(
        "basefunctions.runtime.deployment_manager.basefunctions.runtime.find_development_path",
        lambda name: [str(dev_path)],
    )

    # ACT & ASSERT
    with pytest.raises(DeploymentError, match="You must be inside the development directory"):
        deployment_manager.deploy_module(module_name)


def test_deploy_module_skips_when_no_changes_and_force_false(
    deployment_manager: DeploymentManager,
    mock_module_structure: Dict[str, Any],
    mock_deployment_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test deploy_module skips deployment when no changes detected and force is False."""
    # ARRANGE
    module_name: str = mock_module_structure["module_name"]
    module_path: Path = mock_module_structure["module_path"]

    # Mock CWD to be inside module
    monkeypatch.setattr("os.getcwd", lambda: str(module_path))
    monkeypatch.setattr(
        "basefunctions.runtime.deployment_manager.basefunctions.runtime.find_development_path",
        lambda name: [str(module_path)],
    )

    # Create existing deployment
    deploy_path: Path = mock_deployment_dir / "packages" / module_name
    deploy_path.mkdir(parents=True)

    # Mock _detect_changes to return False
    monkeypatch.setattr(deployment_manager, "_detect_changes", lambda name, path: False)

    # ACT
    deployed: bool
    version: str
    deployed, version = deployment_manager.deploy_module(module_name, force=False)

    # ASSERT
    assert deployed is False
    assert version == "unknown"


def test_deploy_module_deploys_when_force_true(
    deployment_manager: DeploymentManager,
    mock_module_structure: Dict[str, Any],
    mock_deployment_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test deploy_module deploys even without changes when force is True."""
    # ARRANGE
    module_name: str = mock_module_structure["module_name"]
    module_path: Path = mock_module_structure["module_path"]

    monkeypatch.setattr("os.getcwd", lambda: str(module_path))
    monkeypatch.setattr(
        "basefunctions.runtime.deployment_manager.basefunctions.runtime.find_development_path",
        lambda name: [str(module_path)],
    )

    # Mock deployment methods to prevent actual operations
    monkeypatch.setattr(deployment_manager, "_detect_changes", lambda name, path: False)
    monkeypatch.setattr(deployment_manager, "_deploy_venv", lambda src, tgt: None)
    monkeypatch.setattr(deployment_manager, "_deploy_templates", lambda src, tgt: None)
    monkeypatch.setattr(deployment_manager, "_deploy_configs", lambda tgt: None)
    monkeypatch.setattr(deployment_manager, "_deploy_bin_tools", lambda src, tgt, name: None)
    monkeypatch.setattr(deployment_manager, "_update_hash", lambda name, path: None)

    # ACT
    deployed: bool
    version: str
    deployed, version = deployment_manager.deploy_module(module_name, force=True)

    # ASSERT
    assert deployed is True


def test_deploy_module_returns_correct_tuple_format(
    deployment_manager: DeploymentManager,
    mock_module_structure: Dict[str, Any],
    mock_deployment_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test deploy_module returns tuple (bool, str) with version information."""
    # ARRANGE
    module_name: str = mock_module_structure["module_name"]
    module_path: Path = mock_module_structure["module_path"]
    version_string: str = "v1.2.3"

    monkeypatch.setattr("os.getcwd", lambda: str(module_path))
    monkeypatch.setattr(
        "basefunctions.runtime.deployment_manager.basefunctions.runtime.find_development_path",
        lambda name: [str(module_path)],
    )

    # Mock all deployment operations
    monkeypatch.setattr(deployment_manager, "_detect_changes", lambda name, path: True)
    monkeypatch.setattr(deployment_manager, "_deploy_venv", lambda src, tgt: None)
    monkeypatch.setattr(deployment_manager, "_deploy_templates", lambda src, tgt: None)
    monkeypatch.setattr(deployment_manager, "_deploy_configs", lambda tgt: None)
    monkeypatch.setattr(deployment_manager, "_deploy_bin_tools", lambda src, tgt, name: None)
    monkeypatch.setattr(deployment_manager, "_update_hash", lambda name, path: None)

    # ACT
    deployed: bool
    version: str
    deployed, version = deployment_manager.deploy_module(module_name, force=True, version=version_string)

    # ASSERT
    assert isinstance(deployed, bool)
    assert isinstance(version, str)
    assert deployed is True
    assert version == version_string


# -------------------------------------------------------------
# TESTS FOR clean_deployment
# -------------------------------------------------------------


def test_clean_deployment_raises_error_when_module_name_empty(deployment_manager: DeploymentManager) -> None:  # CRITICAL TEST
    """Test clean_deployment raises DeploymentError when module name is empty."""
    # ARRANGE
    empty_name: str = ""

    # ACT & ASSERT
    with pytest.raises(DeploymentError, match="Module name must be provided"):
        deployment_manager.clean_deployment(empty_name)


def test_clean_deployment_removes_target_directory(
    deployment_manager: DeploymentManager, mock_deployment_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:  # CRITICAL TEST
    """Test clean_deployment removes target deployment directory."""
    # ARRANGE
    module_name: str = "testmodule"
    target_path: Path = mock_deployment_dir / "packages" / module_name
    target_path.mkdir(parents=True)
    (target_path / "test.txt").write_text("test")

    # Mock methods that aren't being tested
    monkeypatch.setattr(deployment_manager, "_remove_module_wrappers", lambda bin_dir, name: None)
    monkeypatch.setattr(deployment_manager, "_remove_stored_hash", lambda name: None)

    # ACT
    deployment_manager.clean_deployment(module_name)

    # ASSERT
    assert not target_path.exists()


def test_clean_deployment_handles_nonexistent_target_gracefully(
    deployment_manager: DeploymentManager, mock_deployment_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test clean_deployment handles nonexistent target directory gracefully."""
    # ARRANGE
    module_name: str = "nonexistent"

    monkeypatch.setattr(deployment_manager, "_remove_module_wrappers", lambda bin_dir, name: None)
    monkeypatch.setattr(deployment_manager, "_remove_stored_hash", lambda name: None)

    # ACT (should not raise)
    deployment_manager.clean_deployment(module_name)

    # ASSERT
    # No exception raised


# -------------------------------------------------------------
# TESTS FOR _detect_changes
# -------------------------------------------------------------


def test_detect_changes_returns_true_when_deployment_missing(
    deployment_manager: DeploymentManager, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test _detect_changes returns True when deployment directory doesn't exist."""
    # ARRANGE
    module_name: str = "testmodule"
    source_path: str = str(tmp_path / module_name)

    monkeypatch.setattr(
        "basefunctions.runtime.deployment_manager.basefunctions.runtime.get_deployment_path",
        lambda name: str(tmp_path / "deployment" / name),
    )

    # ACT
    result: bool = deployment_manager._detect_changes(module_name, source_path)

    # ASSERT
    assert result is True


def test_detect_changes_returns_true_when_hash_differs(
    deployment_manager: DeploymentManager, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test _detect_changes returns True when stored hash differs from current hash."""
    # ARRANGE
    module_name: str = "testmodule"
    source_path: str = str(tmp_path / module_name)
    deploy_path: Path = tmp_path / "deployment" / module_name
    deploy_path.mkdir(parents=True)

    monkeypatch.setattr(
        "basefunctions.runtime.deployment_manager.basefunctions.runtime.get_deployment_path",
        lambda name: str(deploy_path),
    )
    monkeypatch.setattr(deployment_manager, "_calculate_combined_hash", lambda path: "new_hash")
    monkeypatch.setattr(deployment_manager, "_get_stored_hash", lambda name: "old_hash")

    # ACT
    result: bool = deployment_manager._detect_changes(module_name, source_path)

    # ASSERT
    assert result is True


def test_detect_changes_returns_false_when_hash_matches(
    deployment_manager: DeploymentManager, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test _detect_changes returns False when stored hash matches current hash."""
    # ARRANGE
    module_name: str = "testmodule"
    source_path: str = str(tmp_path / module_name)
    deploy_path: Path = tmp_path / "deployment" / module_name
    deploy_path.mkdir(parents=True)

    same_hash: str = "identical_hash"

    monkeypatch.setattr(
        "basefunctions.runtime.deployment_manager.basefunctions.runtime.get_deployment_path",
        lambda name: str(deploy_path),
    )
    monkeypatch.setattr(deployment_manager, "_calculate_combined_hash", lambda path: same_hash)
    monkeypatch.setattr(deployment_manager, "_get_stored_hash", lambda name: same_hash)

    # ACT
    result: bool = deployment_manager._detect_changes(module_name, source_path)

    # ASSERT
    assert result is False


# -------------------------------------------------------------
# TESTS FOR _hash_pip_freeze
# -------------------------------------------------------------


def test_hash_pip_freeze_returns_no_venv_when_venv_missing(deployment_manager: DeploymentManager, tmp_path: Path) -> None:
    """Test _hash_pip_freeze returns 'no-venv' when venv doesn't exist."""
    # ARRANGE
    nonexistent_venv: str = str(tmp_path / "nonexistent_venv")

    # ACT
    result: str = deployment_manager._hash_pip_freeze(nonexistent_venv)

    # ASSERT
    assert result == "no-venv"


def test_hash_pip_freeze_returns_no_pip_when_pip_missing(deployment_manager: DeploymentManager, tmp_path: Path) -> None:
    """Test _hash_pip_freeze returns 'no-pip' when pip executable doesn't exist."""
    # ARRANGE
    venv_path: Path = tmp_path / "venv"
    venv_path.mkdir()

    # ACT
    result: str = deployment_manager._hash_pip_freeze(str(venv_path))

    # ASSERT
    assert result == "no-pip"


def test_hash_pip_freeze_returns_pip_error_when_subprocess_fails(
    deployment_manager: DeploymentManager, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test _hash_pip_freeze returns 'pip-error' when subprocess fails."""
    # ARRANGE
    venv_path: Path = tmp_path / "venv" / "bin"
    venv_path.mkdir(parents=True)
    pip_path: Path = venv_path / "pip"
    pip_path.write_text("#!/bin/bash\nexit 1")
    pip_path.chmod(0o755)

    # Mock subprocess to fail
    mock_result: Mock = Mock()
    mock_result.returncode = 1
    monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: mock_result)

    # ACT
    result: str = deployment_manager._hash_pip_freeze(str(venv_path.parent))

    # ASSERT
    assert result == "pip-error"


# -------------------------------------------------------------
# TESTS FOR _parse_project_dependencies
# -------------------------------------------------------------


def test_parse_project_dependencies_returns_empty_when_file_missing(
    deployment_manager: DeploymentManager, tmp_path: Path
) -> None:
    """Test _parse_project_dependencies returns empty list when pyproject.toml missing."""
    # ARRANGE
    source_path: str = str(tmp_path)

    # ACT
    result: List[str] = deployment_manager._parse_project_dependencies(source_path)

    # ASSERT
    assert result == []


def test_parse_project_dependencies_extracts_package_names(
    deployment_manager: DeploymentManager, tmp_path: Path
) -> None:
    """Test _parse_project_dependencies correctly extracts package names from pyproject.toml."""
    # ARRANGE
    source_path: Path = tmp_path
    pyproject_file: Path = source_path / "pyproject.toml"
    pyproject_content: str = """
[project]
name = "testproject"
dependencies = [
    "basefunctions>=0.5.0",
    "requests>=2.28.0",
    "pytest>=7.0.0"
]
"""
    pyproject_file.write_text(pyproject_content)

    # ACT
    result: List[str] = deployment_manager._parse_project_dependencies(str(source_path))

    # ASSERT
    assert "basefunctions" in result
    assert "requests" in result
    assert "pytest" in result


def test_parse_project_dependencies_handles_malformed_toml_gracefully(
    deployment_manager: DeploymentManager, tmp_path: Path
) -> None:
    """Test _parse_project_dependencies handles malformed TOML gracefully."""
    # ARRANGE
    source_path: Path = tmp_path
    pyproject_file: Path = source_path / "pyproject.toml"
    pyproject_file.write_text("invalid toml content {{{")

    # ACT
    result: List[str] = deployment_manager._parse_project_dependencies(str(source_path))

    # ASSERT
    assert result == []


# -------------------------------------------------------------
# TESTS FOR _create_wrapper
# -------------------------------------------------------------


def test_create_wrapper_creates_executable_file(
    deployment_manager: DeploymentManager, tmp_path: Path
) -> None:  # CRITICAL TEST
    """Test _create_wrapper creates wrapper file with correct permissions."""
    # ARRANGE
    global_bin: str = str(tmp_path / "bin")
    os.makedirs(global_bin, exist_ok=True)

    tool_name: str = "test_tool.py"
    module_name: str = "testmodule"
    target_path: str = str(tmp_path / "deployment")

    # ACT
    deployment_manager._create_wrapper(global_bin, tool_name, module_name, target_path)

    # ASSERT
    wrapper_path: Path = Path(global_bin) / "test_tool"
    assert wrapper_path.exists()
    assert wrapper_path.is_file()
    assert os.access(wrapper_path, os.X_OK)


def test_create_wrapper_creates_no_venv_wrapper_for_protected_tools(
    deployment_manager: DeploymentManager, tmp_path: Path
) -> None:  # CRITICAL TEST
    """Test _create_wrapper creates no-venv wrapper for tools in NO_VENV_TOOLS list."""
    # ARRANGE
    global_bin: str = str(tmp_path / "bin")
    os.makedirs(global_bin, exist_ok=True)

    tool_name: str = "ppip.py"  # This is in NO_VENV_TOOLS
    module_name: str = "testmodule"
    target_path: str = str(tmp_path / "deployment")

    # ACT
    deployment_manager._create_wrapper(global_bin, tool_name, module_name, target_path)

    # ASSERT
    wrapper_path: Path = Path(global_bin) / "ppip"
    wrapper_content: str = wrapper_path.read_text()
    assert "source" not in wrapper_content  # No venv activation
    assert "exec" in wrapper_content


def test_create_wrapper_creates_venv_wrapper_for_normal_tools(
    deployment_manager: DeploymentManager, tmp_path: Path
) -> None:  # CRITICAL TEST
    """Test _create_wrapper creates venv-activating wrapper for normal tools."""
    # ARRANGE
    global_bin: str = str(tmp_path / "bin")
    os.makedirs(global_bin, exist_ok=True)

    tool_name: str = "normal_tool.py"
    module_name: str = "testmodule"
    target_path: str = str(tmp_path / "deployment")

    # ACT
    deployment_manager._create_wrapper(global_bin, tool_name, module_name, target_path)

    # ASSERT
    wrapper_path: Path = Path(global_bin) / "normal_tool"
    wrapper_content: str = wrapper_path.read_text()
    assert "source" in wrapper_content  # Venv activation present
    assert "activate" in wrapper_content


# -------------------------------------------------------------
# TESTS FOR _deploy_venv
# -------------------------------------------------------------


def test_deploy_venv_raises_error_when_venvutils_fails(
    deployment_manager: DeploymentManager, mock_module_structure: Dict[str, Any], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:  # CRITICAL TEST
    """Test _deploy_venv raises DeploymentError when VenvUtils operations fail."""
    # ARRANGE
    source_path: str = str(mock_module_structure["module_path"])
    target_path: str = str(tmp_path / "deployment")

    # Mock VenvUtils to raise error
    def mock_upgrade_pip(*args, **kwargs):
        raise VenvUtilsError("Mock pip upgrade failed")

    monkeypatch.setattr("basefunctions.runtime.deployment_manager.basefunctions.VenvUtils.upgrade_pip", mock_upgrade_pip)

    # Mock subprocess for venv creation
    mock_subprocess: Mock = Mock()
    mock_subprocess.returncode = 0
    monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: mock_subprocess)

    # Mock _copy_package_structure
    monkeypatch.setattr(deployment_manager, "_copy_package_structure", lambda src, tgt: None)

    # ACT & ASSERT
    with pytest.raises(DeploymentError, match="Failed to create virtual environment"):
        deployment_manager._deploy_venv(source_path, target_path)


def test_deploy_venv_raises_error_when_subprocess_fails(
    deployment_manager: DeploymentManager, mock_module_structure: Dict[str, Any], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:  # CRITICAL TEST
    """Test _deploy_venv raises DeploymentError when subprocess venv creation fails."""
    # ARRANGE
    source_path: str = str(mock_module_structure["module_path"])
    target_path: str = str(tmp_path / "deployment")

    # Mock subprocess to fail
    monkeypatch.setattr("subprocess.run", Mock(side_effect=subprocess.CalledProcessError(1, "venv")))

    # ACT & ASSERT
    with pytest.raises(DeploymentError, match="Failed to create virtual environment"):
        deployment_manager._deploy_venv(source_path, target_path)
