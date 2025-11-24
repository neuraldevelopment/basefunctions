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
 v1.0.1 : Added tests for path validation before destructive operations
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
# External imports
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import Mock

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
        "basefunctions.runtime.deployment_manager.basefunctions.runtime" ".get_bootstrap_deployment_directory",
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


def test_deploy_module_raises_error_when_module_name_empty(
    deployment_manager: DeploymentManager,
) -> None:  # CRITICAL TEST
    """Test deploy_module raises DeploymentError when module name is empty string."""
    # ARRANGE
    empty_name: str = ""

    # ACT & ASSERT
    with pytest.raises(DeploymentError, match="Module name must be provided"):
        deployment_manager.deploy_module(empty_name)


def test_deploy_module_raises_error_when_module_name_none(
    deployment_manager: DeploymentManager,
) -> None:  # CRITICAL TEST
    """Test deploy_module raises DeploymentError when module name is None."""
    # ARRANGE
    none_name: None = None

    # ACT & ASSERT
    with pytest.raises(DeploymentError, match="Module name must be provided"):
        deployment_manager.deploy_module(none_name)


def test_deploy_module_raises_error_when_module_not_found(
    deployment_manager: DeploymentManager, monkeypatch: pytest.MonkeyPatch
) -> None:  # CRITICAL TEST
    """
    Test deploy_module raises DeploymentError when module not found in
    development directories.
    """
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


def test_clean_deployment_raises_error_when_module_name_empty(
    deployment_manager: DeploymentManager,
) -> None:  # CRITICAL TEST
    """Test clean_deployment raises DeploymentError when module name is empty."""
    # ARRANGE
    empty_name: str = ""

    # ACT & ASSERT
    with pytest.raises(DeploymentError, match="Module name must be provided"):
        deployment_manager.clean_deployment(empty_name)


def test_clean_deployment_removes_target_directory(
    deployment_manager: DeploymentManager,
    mock_deployment_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
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
    deployment_manager: DeploymentManager,
    mock_deployment_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
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


def test_hash_pip_freeze_returns_no_venv_when_venv_missing(
    deployment_manager: DeploymentManager, tmp_path: Path
) -> None:
    """Test _hash_pip_freeze returns 'no-venv' when venv doesn't exist."""
    # ARRANGE
    nonexistent_venv: str = str(tmp_path / "nonexistent_venv")

    # ACT
    result: str = deployment_manager._hash_pip_freeze(nonexistent_venv)

    # ASSERT
    assert result == "no-venv"


def test_hash_pip_freeze_returns_no_pip_when_pip_missing(
    deployment_manager: DeploymentManager, tmp_path: Path
) -> None:
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
    deployment_manager: DeploymentManager,
    mock_module_structure: Dict[str, Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:  # CRITICAL TEST
    """Test _deploy_venv raises DeploymentError when VenvUtils operations fail."""
    # ARRANGE
    source_path: str = str(mock_module_structure["module_path"])
    target_path: str = str(tmp_path / "deployment")

    # Mock VenvUtils to raise error
    def mock_upgrade_pip(*args, **kwargs):
        raise VenvUtilsError("Mock pip upgrade failed")

    monkeypatch.setattr(
        "basefunctions.runtime.deployment_manager.basefunctions.VenvUtils.upgrade_pip",
        mock_upgrade_pip,
    )

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
    deployment_manager: DeploymentManager,
    mock_module_structure: Dict[str, Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
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


# -------------------------------------------------------------
# TESTS FOR _calculate_combined_hash
# -------------------------------------------------------------


def test_calculate_combined_hash_handles_no_src_directory(
    deployment_manager: DeploymentManager, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test _calculate_combined_hash handles module without src directory."""
    # ARRANGE
    module_path: Path = tmp_path / "module"
    module_path.mkdir()

    # Mock _hash_pip_freeze to avoid subprocess
    monkeypatch.setattr(deployment_manager, "_hash_pip_freeze", lambda path: "no-venv")
    monkeypatch.setattr(deployment_manager, "_hash_bin_files", lambda path: "no-bin")
    monkeypatch.setattr(deployment_manager, "_hash_template_files", lambda path: "no-templates")
    monkeypatch.setattr(deployment_manager, "_get_dependency_timestamps", lambda path: "no-local-deps")

    # ACT
    result: str = deployment_manager._calculate_combined_hash(str(module_path))

    # ASSERT
    assert result is not None
    assert isinstance(result, str)
    assert len(result) == 64  # SHA256 hex digest length


def test_calculate_combined_hash_includes_all_components(
    deployment_manager: DeploymentManager,
    mock_module_structure: Dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Test _calculate_combined_hash includes src, pip, bin, templates, and
    dependencies.
    """
    # ARRANGE
    module_path: str = str(mock_module_structure["module_path"])

    # Mock components to return known values
    monkeypatch.setattr(deployment_manager, "_hash_src_files", lambda path: "src-hash")
    monkeypatch.setattr(deployment_manager, "_hash_pip_freeze", lambda path: "pip-hash")
    monkeypatch.setattr(deployment_manager, "_hash_bin_files", lambda path: "bin-hash")
    monkeypatch.setattr(deployment_manager, "_hash_template_files", lambda path: "templates-hash")
    monkeypatch.setattr(deployment_manager, "_get_dependency_timestamps", lambda path: "deps-hash")

    # ACT
    result: str = deployment_manager._calculate_combined_hash(module_path)

    # ASSERT
    assert result is not None
    assert isinstance(result, str)
    assert len(result) == 64


def test_calculate_combined_hash_produces_different_hashes_for_different_content(
    deployment_manager: DeploymentManager,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Test _calculate_combined_hash produces different hashes for different
    module states.
    """
    # ARRANGE
    module_path: Path = tmp_path / "module"
    module_path.mkdir()

    # Mock components - first state
    monkeypatch.setattr(deployment_manager, "_hash_pip_freeze", lambda path: "no-venv")
    monkeypatch.setattr(deployment_manager, "_hash_bin_files", lambda path: "no-bin")
    monkeypatch.setattr(deployment_manager, "_hash_template_files", lambda path: "no-templates")
    monkeypatch.setattr(deployment_manager, "_get_dependency_timestamps", lambda path: "no-local-deps")

    # ACT
    hash1: str = deployment_manager._calculate_combined_hash(str(module_path))

    # Change component
    monkeypatch.setattr(deployment_manager, "_hash_bin_files", lambda path: "bin-changed")
    hash2: str = deployment_manager._calculate_combined_hash(str(module_path))

    # ASSERT
    assert hash1 != hash2


# -------------------------------------------------------------
# TESTS FOR _hash_src_files
# -------------------------------------------------------------


def test_hash_src_files_returns_no_src_when_directory_missing(
    deployment_manager: DeploymentManager, tmp_path: Path
) -> None:
    """Test _hash_src_files returns 'no-src' when src directory doesn't exist."""
    # ARRANGE
    module_path: Path = tmp_path / "module"
    module_path.mkdir()

    # ACT
    result: str = deployment_manager._hash_src_files(str(module_path))

    # ASSERT
    assert result == "no-src"


def test_hash_src_files_calculates_hash_from_python_files(
    deployment_manager: DeploymentManager, tmp_path: Path
) -> None:
    """Test _hash_src_files calculates hash from Python files in src directory."""
    # ARRANGE
    module_path: Path = tmp_path / "module"
    src_dir: Path = module_path / "src" / "mypackage"
    src_dir.mkdir(parents=True)

    (src_dir / "__init__.py").write_text("# init")
    (src_dir / "module.py").write_text("def func(): pass")
    (src_dir / "test.txt").write_text("should be ignored")

    # ACT
    result: str = deployment_manager._hash_src_files(str(module_path))

    # ASSERT
    assert result != "no-src"
    assert isinstance(result, str)
    assert len(result) == 64


def test_hash_src_files_produces_consistent_hash(deployment_manager: DeploymentManager, tmp_path: Path) -> None:
    """Test _hash_src_files produces consistent hash for same file set."""
    # ARRANGE
    module_path: Path = tmp_path / "module"
    src_dir: Path = module_path / "src"
    src_dir.mkdir(parents=True)

    (src_dir / "test.py").write_text("test")

    # ACT
    hash1: str = deployment_manager._hash_src_files(str(module_path))
    hash2: str = deployment_manager._hash_src_files(str(module_path))

    # ASSERT
    assert hash1 == hash2


# -------------------------------------------------------------
# TESTS FOR _hash_bin_files
# -------------------------------------------------------------


def test_hash_bin_files_returns_no_bin_when_directory_missing(
    deployment_manager: DeploymentManager, tmp_path: Path
) -> None:
    """Test _hash_bin_files returns 'no-bin' when bin directory doesn't exist."""
    # ARRANGE
    module_path: Path = tmp_path / "module"
    module_path.mkdir()

    # ACT
    result: str = deployment_manager._hash_bin_files(str(module_path))

    # ASSERT
    assert result == "no-bin"


def test_hash_bin_files_calculates_hash_from_all_files(deployment_manager: DeploymentManager, tmp_path: Path) -> None:
    """Test _hash_bin_files calculates hash from all files in bin directory."""
    # ARRANGE
    module_path: Path = tmp_path / "module"
    bin_dir: Path = module_path / "bin"
    bin_dir.mkdir(parents=True)

    (bin_dir / "tool1.py").write_text("#!/usr/bin/env python\nprint('tool1')")
    (bin_dir / "tool2.py").write_text("#!/usr/bin/env python\nprint('tool2')")

    # ACT
    result: str = deployment_manager._hash_bin_files(str(module_path))

    # ASSERT
    assert result != "no-bin"
    assert isinstance(result, str)
    assert len(result) == 64


def test_hash_bin_files_changes_when_file_modified(deployment_manager: DeploymentManager, tmp_path: Path) -> None:
    """Test _hash_bin_files produces different hash when file is modified."""
    # ARRANGE
    module_path: Path = tmp_path / "module"
    bin_dir: Path = module_path / "bin"
    bin_dir.mkdir(parents=True)

    tool_file: Path = bin_dir / "tool.py"
    tool_file.write_text("v1")

    # ACT
    hash1: str = deployment_manager._hash_bin_files(str(module_path))

    import time

    time.sleep(0.01)  # Ensure mtime changes
    tool_file.write_text("v2")

    hash2: str = deployment_manager._hash_bin_files(str(module_path))

    # ASSERT
    assert hash1 != hash2


# -------------------------------------------------------------
# TESTS FOR _hash_template_files
# -------------------------------------------------------------


def test_hash_template_files_returns_no_templates_when_directory_missing(
    deployment_manager: DeploymentManager, tmp_path: Path
) -> None:
    """Test _hash_template_files returns 'no-templates' when templates directory doesn't exist."""
    # ARRANGE
    module_path: Path = tmp_path / "module"
    module_path.mkdir()

    # ACT
    result: str = deployment_manager._hash_template_files(str(module_path))

    # ASSERT
    assert result == "no-templates"


def test_hash_template_files_calculates_hash_from_all_templates(
    deployment_manager: DeploymentManager, tmp_path: Path
) -> None:
    """Test _hash_template_files calculates hash from all template files."""
    # ARRANGE
    module_path: Path = tmp_path / "module"
    templates_dir: Path = module_path / "templates"
    config_dir: Path = templates_dir / "config"
    config_dir.mkdir(parents=True)

    (config_dir / "config.json").write_text('{"key": "value"}')
    (templates_dir / "template.txt").write_text("template content")

    # ACT
    result: str = deployment_manager._hash_template_files(str(module_path))

    # ASSERT
    assert result != "no-templates"
    assert isinstance(result, str)
    assert len(result) == 64


# -------------------------------------------------------------
# TESTS FOR _get_stored_hash and _update_hash
# -------------------------------------------------------------


def test_get_stored_hash_returns_none_when_file_missing(
    deployment_manager: DeploymentManager, mock_deployment_dir: Path
) -> None:
    """Test _get_stored_hash returns None when hash file doesn't exist."""
    # ARRANGE
    module_name: str = "nonexistent"

    # ACT
    result: Optional[str] = deployment_manager._get_stored_hash(module_name)

    # ASSERT
    assert result is None


def test_update_hash_creates_hash_file(
    deployment_manager: DeploymentManager,
    mock_deployment_dir: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test _update_hash creates hash file with calculated hash."""
    # ARRANGE
    module_name: str = "testmodule"
    source_path: Path = tmp_path / "source"
    source_path.mkdir()

    expected_hash: str = "test_hash_value"
    monkeypatch.setattr(deployment_manager, "_calculate_combined_hash", lambda path: expected_hash)

    # ACT
    deployment_manager._update_hash(module_name, str(source_path))

    # ASSERT
    stored_hash: Optional[str] = deployment_manager._get_stored_hash(module_name)
    assert stored_hash == expected_hash


def test_update_hash_overwrites_existing_hash(
    deployment_manager: DeploymentManager,
    mock_deployment_dir: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test _update_hash overwrites existing hash file."""
    # ARRANGE
    module_name: str = "testmodule"
    source_path: Path = tmp_path / "source"
    source_path.mkdir()

    # Create initial hash
    old_hash: str = "old_hash"
    monkeypatch.setattr(deployment_manager, "_calculate_combined_hash", lambda path: old_hash)
    deployment_manager._update_hash(module_name, str(source_path))

    # Update with new hash
    new_hash: str = "new_hash"
    monkeypatch.setattr(deployment_manager, "_calculate_combined_hash", lambda path: new_hash)

    # ACT
    deployment_manager._update_hash(module_name, str(source_path))

    # ASSERT
    stored_hash: Optional[str] = deployment_manager._get_stored_hash(module_name)
    assert stored_hash == new_hash


def test_update_hash_handles_write_errors_gracefully(
    deployment_manager: DeploymentManager,
    mock_deployment_dir: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test _update_hash handles file write errors gracefully."""
    # ARRANGE
    module_name: str = "testmodule"
    source_path: Path = tmp_path / "source"
    source_path.mkdir()

    monkeypatch.setattr(deployment_manager, "_calculate_combined_hash", lambda path: "hash")

    # Mock open to raise exception
    def mock_open(*args, **kwargs):
        raise PermissionError("Mock permission denied")

    monkeypatch.setattr("builtins.open", mock_open)

    # ACT (should not raise)
    deployment_manager._update_hash(module_name, str(source_path))

    # ASSERT (no exception raised)


# -------------------------------------------------------------
# TESTS FOR _remove_stored_hash
# -------------------------------------------------------------


def test_remove_stored_hash_removes_existing_hash_file(
    deployment_manager: DeploymentManager,
    mock_deployment_dir: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test _remove_stored_hash removes existing hash file."""
    # ARRANGE
    module_name: str = "testmodule"
    source_path: Path = tmp_path / "source"
    source_path.mkdir()

    # Create hash file
    monkeypatch.setattr(deployment_manager, "_calculate_combined_hash", lambda path: "test_hash")
    deployment_manager._update_hash(module_name, str(source_path))

    assert deployment_manager._get_stored_hash(module_name) is not None

    # ACT
    deployment_manager._remove_stored_hash(module_name)

    # ASSERT
    assert deployment_manager._get_stored_hash(module_name) is None


def test_remove_stored_hash_handles_nonexistent_file_gracefully(
    deployment_manager: DeploymentManager, mock_deployment_dir: Path
) -> None:
    """Test _remove_stored_hash handles nonexistent hash file gracefully."""
    # ARRANGE
    module_name: str = "nonexistent"

    # ACT (should not raise)
    deployment_manager._remove_stored_hash(module_name)

    # ASSERT (no exception raised)


# -------------------------------------------------------------
# TESTS FOR _get_available_local_packages
# -------------------------------------------------------------


def test_get_available_local_packages_returns_empty_when_directory_missing(
    deployment_manager: DeploymentManager,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Test _get_available_local_packages returns empty list when packages
    directory doesn't exist.
    """
    # ARRANGE
    deploy_dir: Path = tmp_path / "deployment"
    deploy_dir.mkdir()

    monkeypatch.setattr(
        "basefunctions.runtime.deployment_manager.basefunctions.runtime" ".get_bootstrap_deployment_directory",
        lambda: str(deploy_dir),
    )

    # ACT
    result: List[str] = deployment_manager._get_available_local_packages()

    # ASSERT
    assert result == []


def test_get_available_local_packages_returns_package_list(
    deployment_manager: DeploymentManager, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test _get_available_local_packages returns list of available packages."""
    # ARRANGE
    deploy_dir: Path = tmp_path / "deployment"
    packages_dir: Path = deploy_dir / "packages"
    packages_dir.mkdir(parents=True)

    (packages_dir / "package1").mkdir()
    (packages_dir / "package2").mkdir()
    (packages_dir / "file.txt").write_text("not a directory")

    monkeypatch.setattr(
        "basefunctions.runtime.deployment_manager.basefunctions.runtime" ".get_bootstrap_deployment_directory",
        lambda: str(deploy_dir),
    )

    # ACT
    result: List[str] = deployment_manager._get_available_local_packages()

    # ASSERT
    assert set(result) == {"package1", "package2"}


def test_get_available_local_packages_handles_listdir_errors_gracefully(
    deployment_manager: DeploymentManager,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test _get_available_local_packages handles os.listdir errors gracefully."""
    # ARRANGE
    deploy_dir: Path = tmp_path / "deployment"
    packages_dir: Path = deploy_dir / "packages"
    packages_dir.mkdir(parents=True)

    monkeypatch.setattr(
        "basefunctions.runtime.deployment_manager.basefunctions.runtime" ".get_bootstrap_deployment_directory",
        lambda: str(deploy_dir),
    )

    # Mock listdir to raise exception
    monkeypatch.setattr("os.listdir", Mock(side_effect=PermissionError("Mock error")))

    # ACT
    result: List[str] = deployment_manager._get_available_local_packages()

    # ASSERT
    assert result == []


# -------------------------------------------------------------
# TESTS FOR _get_dependency_timestamps
# -------------------------------------------------------------


def test_get_dependency_timestamps_returns_no_local_deps_when_none_found(
    deployment_manager: DeploymentManager, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test _get_dependency_timestamps returns 'no-local-deps' when no local dependencies."""
    # ARRANGE
    module_path: str = str(tmp_path / "module")

    monkeypatch.setattr(deployment_manager, "_parse_project_dependencies", lambda path: [])
    monkeypatch.setattr(deployment_manager, "_get_available_local_packages", lambda: [])

    # ACT
    result: str = deployment_manager._get_dependency_timestamps(module_path)

    # ASSERT
    assert result == "no-local-deps"


def test_get_dependency_timestamps_calculates_hash_from_timestamps(
    deployment_manager: DeploymentManager,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Test _get_dependency_timestamps calculates hash from dependency
    timestamps.
    """
    # ARRANGE
    module_path: str = str(tmp_path / "module")

    monkeypatch.setattr(deployment_manager, "_parse_project_dependencies", lambda path: ["dep1", "dep2"])
    monkeypatch.setattr(deployment_manager, "_get_available_local_packages", lambda: ["dep1", "dep2"])
    monkeypatch.setattr(deployment_manager, "_get_deployment_timestamp", lambda pkg: "123456")

    # ACT
    result: str = deployment_manager._get_dependency_timestamps(module_path)

    # ASSERT
    assert result != "no-local-deps"
    assert isinstance(result, str)
    assert len(result) == 64  # SHA256 hash


def test_get_dependency_timestamps_filters_unavailable_packages(
    deployment_manager: DeploymentManager,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test _get_dependency_timestamps filters out unavailable packages."""
    # ARRANGE
    module_path: str = str(tmp_path / "module")

    monkeypatch.setattr(
        deployment_manager,
        "_parse_project_dependencies",
        lambda path: ["dep1", "dep2", "dep3"],
    )
    monkeypatch.setattr(deployment_manager, "_get_available_local_packages", lambda: ["dep1", "dep2"])

    timestamps_called = []

    def mock_get_timestamp(pkg):
        timestamps_called.append(pkg)
        return "123456"

    monkeypatch.setattr(deployment_manager, "_get_deployment_timestamp", mock_get_timestamp)

    # ACT
    deployment_manager._get_dependency_timestamps(module_path)

    # ASSERT
    assert set(timestamps_called) == {"dep1", "dep2"}
    assert "dep3" not in timestamps_called


# -------------------------------------------------------------
# TESTS FOR _get_deployment_timestamp
# -------------------------------------------------------------


def test_get_deployment_timestamp_returns_not_deployed_when_missing(
    deployment_manager: DeploymentManager, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test _get_deployment_timestamp returns 'not-deployed' when package not deployed."""
    # ARRANGE
    package_name: str = "nonexistent"

    monkeypatch.setattr(
        "basefunctions.runtime.deployment_manager.basefunctions.runtime.get_deployment_path",
        lambda name: str(tmp_path / "nonexistent"),
    )

    # ACT
    result: str = deployment_manager._get_deployment_timestamp(package_name)

    # ASSERT
    assert result == "not-deployed"


def test_get_deployment_timestamp_returns_latest_mtime(
    deployment_manager: DeploymentManager, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test _get_deployment_timestamp returns latest modification time."""
    # ARRANGE
    package_name: str = "testpkg"
    deploy_path: Path = tmp_path / "deployment" / package_name
    deploy_path.mkdir(parents=True)

    file1: Path = deploy_path / "file1.txt"
    file2: Path = deploy_path / "file2.txt"

    file1.write_text("content1")
    import time

    time.sleep(0.01)
    file2.write_text("content2")

    monkeypatch.setattr(
        "basefunctions.runtime.deployment_manager.basefunctions.runtime.get_deployment_path",
        lambda name: str(deploy_path),
    )

    # ACT
    result: str = deployment_manager._get_deployment_timestamp(package_name)

    # ASSERT
    assert result != "not-deployed"
    assert result != "timestamp-error"
    assert float(result) > 0


def test_get_deployment_timestamp_returns_error_on_exception(
    deployment_manager: DeploymentManager, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test _get_deployment_timestamp returns 'timestamp-error' on exception."""
    # ARRANGE
    package_name: str = "testpkg"
    deploy_path: Path = tmp_path / "deployment" / package_name
    deploy_path.mkdir(parents=True)

    monkeypatch.setattr(
        "basefunctions.runtime.deployment_manager.basefunctions.runtime.get_deployment_path",
        lambda name: str(deploy_path),
    )

    # Mock os.walk to raise exception
    monkeypatch.setattr("os.walk", Mock(side_effect=PermissionError("Mock error")))

    # ACT
    result: str = deployment_manager._get_deployment_timestamp(package_name)

    # ASSERT
    assert result == "timestamp-error"


# -------------------------------------------------------------
# TESTS FOR _has_src_directory
# -------------------------------------------------------------


def test_has_src_directory_returns_true_when_src_exists(deployment_manager: DeploymentManager, tmp_path: Path) -> None:
    """Test _has_src_directory returns True when src directory exists."""
    # ARRANGE
    module_path: Path = tmp_path / "module"
    src_dir: Path = module_path / "src"
    src_dir.mkdir(parents=True)

    # ACT
    result: bool = deployment_manager._has_src_directory(str(module_path))

    # ASSERT
    assert result is True


def test_has_src_directory_returns_false_when_src_missing(
    deployment_manager: DeploymentManager, tmp_path: Path
) -> None:
    """Test _has_src_directory returns False when src directory doesn't exist."""
    # ARRANGE
    module_path: Path = tmp_path / "module"
    module_path.mkdir()

    # ACT
    result: bool = deployment_manager._has_src_directory(str(module_path))

    # ASSERT
    assert result is False


# -------------------------------------------------------------
# TESTS FOR _get_local_dependencies_intersection
# -------------------------------------------------------------


def test_get_local_dependencies_intersection_returns_matching_packages(
    deployment_manager: DeploymentManager,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Test _get_local_dependencies_intersection returns intersection of deps
    and available packages.
    """
    # ARRANGE
    source_path: str = str(tmp_path / "module")

    monkeypatch.setattr(
        deployment_manager,
        "_parse_project_dependencies",
        lambda path: ["dep1", "dep2", "dep3"],
    )
    monkeypatch.setattr(
        deployment_manager,
        "_get_available_local_packages",
        lambda: ["dep1", "dep3", "dep4"],
    )

    # ACT
    result: List[str] = deployment_manager._get_local_dependencies_intersection(source_path)

    # ASSERT
    assert set(result) == {"dep1", "dep3"}


def test_get_local_dependencies_intersection_returns_empty_when_no_match(
    deployment_manager: DeploymentManager,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Test _get_local_dependencies_intersection returns empty list when no
    matches.
    """
    # ARRANGE
    source_path: str = str(tmp_path / "module")

    monkeypatch.setattr(deployment_manager, "_parse_project_dependencies", lambda path: ["dep1", "dep2"])
    monkeypatch.setattr(deployment_manager, "_get_available_local_packages", lambda: ["dep3", "dep4"])

    # ACT
    result: List[str] = deployment_manager._get_local_dependencies_intersection(source_path)

    # ASSERT
    assert result == []


# -------------------------------------------------------------
# TESTS FOR _install_local_package_with_venvutils
# -------------------------------------------------------------


def test_install_local_package_raises_error_when_package_not_found(
    deployment_manager: DeploymentManager,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:  # CRITICAL TEST
    """
    Test _install_local_package_with_venvutils raises error when package
    path doesn't exist.
    """
    # ARRANGE
    venv_path: Path = tmp_path / "venv"
    venv_path.mkdir()
    package_name: str = "nonexistent"

    deploy_dir: Path = tmp_path / "deployment"
    deploy_dir.mkdir()

    monkeypatch.setattr(
        "basefunctions.runtime.deployment_manager.basefunctions.runtime" ".get_bootstrap_deployment_directory",
        lambda: str(deploy_dir),
    )

    # ACT & ASSERT
    with pytest.raises(DeploymentError, match="Local package .* not found"):
        deployment_manager._install_local_package_with_venvutils(venv_path, package_name)


def test_install_local_package_raises_error_when_venvutils_fails(
    deployment_manager: DeploymentManager,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:  # CRITICAL TEST
    """Test _install_local_package_with_venvutils raises error when VenvUtils fails."""
    # ARRANGE
    venv_path: Path = tmp_path / "venv"
    venv_path.mkdir()
    package_name: str = "testpkg"

    deploy_dir: Path = tmp_path / "deployment"
    packages_dir: Path = deploy_dir / "packages" / package_name
    packages_dir.mkdir(parents=True)

    monkeypatch.setattr(
        "basefunctions.runtime.deployment_manager.basefunctions.runtime" ".get_bootstrap_deployment_directory",
        lambda: str(deploy_dir),
    )

    # Mock VenvUtils to raise error on both ppip and pip fallback
    def mock_install_with_ppip(*args, **kwargs):
        raise VenvUtilsError("Mock ppip install failed")

    def mock_run_pip(*args, **kwargs):
        raise VenvUtilsError("Mock pip install failed")

    monkeypatch.setattr(
        "basefunctions.runtime.deployment_manager.basefunctions.VenvUtils.install_with_ppip",
        mock_install_with_ppip,
    )
    monkeypatch.setattr(
        "basefunctions.runtime.deployment_manager.basefunctions.VenvUtils.run_pip_command", mock_run_pip
    )

    # ACT & ASSERT
    with pytest.raises(DeploymentError, match="Failed to install local package"):
        deployment_manager._install_local_package_with_venvutils(venv_path, package_name)


# -------------------------------------------------------------
# TESTS FOR _copy_package_structure
# -------------------------------------------------------------


def test_copy_package_structure_copies_all_relevant_files(
    deployment_manager: DeploymentManager, tmp_path: Path
) -> None:
    """Test _copy_package_structure copies all relevant package files."""
    # ARRANGE
    source_path: Path = tmp_path / "source"
    source_path.mkdir()
    target_path: Path = tmp_path / "target"
    target_path.mkdir()

    # Create files to copy
    (source_path / "pyproject.toml").write_text('[project]\nname = "test"')
    (source_path / "setup.py").write_text("# setup")
    (source_path / "README.md").write_text("# README")
    (source_path / "LICENSE").write_text("MIT")

    # Create directories to copy
    src_dir: Path = source_path / "src"
    src_dir.mkdir()
    (src_dir / "__init__.py").write_text("# init")

    config_dir: Path = source_path / "config"
    config_dir.mkdir()
    (config_dir / "config.json").write_text("{}")

    # ACT
    deployment_manager._copy_package_structure(str(source_path), str(target_path))

    # ASSERT
    assert (target_path / "pyproject.toml").exists()
    assert (target_path / "setup.py").exists()
    assert (target_path / "README.md").exists()
    assert (target_path / "LICENSE").exists()
    assert (target_path / "src" / "__init__.py").exists()
    assert (target_path / "config" / "config.json").exists()


def test_copy_package_structure_handles_missing_files_gracefully(
    deployment_manager: DeploymentManager, tmp_path: Path
) -> None:
    """Test _copy_package_structure handles missing optional files gracefully."""
    # ARRANGE
    source_path: Path = tmp_path / "source"
    source_path.mkdir()
    target_path: Path = tmp_path / "target"
    target_path.mkdir()

    # Only create pyproject.toml (minimal)
    (source_path / "pyproject.toml").write_text('[project]\nname = "test"')

    # ACT (should not raise)
    deployment_manager._copy_package_structure(str(source_path), str(target_path))

    # ASSERT
    assert (target_path / "pyproject.toml").exists()
    assert not (target_path / "LICENSE").exists()


def test_copy_package_structure_overwrites_existing_directories(
    deployment_manager: DeploymentManager, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test _copy_package_structure overwrites existing directories."""
    # ARRANGE
    source_path: Path = tmp_path / "source"
    source_path.mkdir()
    target_path: Path = tmp_path / "target"
    target_path.mkdir()

    # Mock deployment directory for path validation
    monkeypatch.setattr(
        "basefunctions.runtime.deployment_manager.basefunctions.runtime" ".get_bootstrap_deployment_directory",
        lambda: str(tmp_path),
    )

    # Create source dir with new content
    src_dir: Path = source_path / "src"
    src_dir.mkdir()
    (src_dir / "new_file.py").write_text("new content")

    # Create target dir with old content
    target_src: Path = target_path / "src"
    target_src.mkdir()
    (target_src / "old_file.py").write_text("old content")

    # ACT
    deployment_manager._copy_package_structure(str(source_path), str(target_path))

    # ASSERT
    assert (target_path / "src" / "new_file.py").exists()
    assert not (target_path / "src" / "old_file.py").exists()


# -------------------------------------------------------------
# TESTS FOR _deploy_templates
# -------------------------------------------------------------


def test_deploy_templates_copies_templates_directory(deployment_manager: DeploymentManager, tmp_path: Path) -> None:
    """Test _deploy_templates copies templates directory to target."""
    # ARRANGE
    source_path: Path = tmp_path / "source"
    templates_dir: Path = source_path / "templates"
    templates_dir.mkdir(parents=True)
    (templates_dir / "template.txt").write_text("template content")

    target_path: Path = tmp_path / "target"
    target_path.mkdir()

    # ACT
    deployment_manager._deploy_templates(str(source_path), str(target_path))

    # ASSERT
    assert (target_path / "templates" / "template.txt").exists()


def test_deploy_templates_skips_when_no_templates_directory(
    deployment_manager: DeploymentManager, tmp_path: Path
) -> None:
    """Test _deploy_templates skips when templates directory doesn't exist."""
    # ARRANGE
    source_path: Path = tmp_path / "source"
    source_path.mkdir()
    target_path: Path = tmp_path / "target"
    target_path.mkdir()

    # ACT (should not raise)
    deployment_manager._deploy_templates(str(source_path), str(target_path))

    # ASSERT
    assert not (target_path / "templates").exists()


def test_deploy_templates_overwrites_existing_templates(
    deployment_manager: DeploymentManager, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test _deploy_templates overwrites existing templates directory."""
    # ARRANGE
    source_path: Path = tmp_path / "source"
    templates_dir: Path = source_path / "templates"
    templates_dir.mkdir(parents=True)
    (templates_dir / "new.txt").write_text("new")

    target_path: Path = tmp_path / "target"
    target_templates: Path = target_path / "templates"
    target_templates.mkdir(parents=True)
    (target_templates / "old.txt").write_text("old")

    # Mock deployment directory for path validation
    monkeypatch.setattr(
        "basefunctions.runtime.deployment_manager.basefunctions.runtime" ".get_bootstrap_deployment_directory",
        lambda: str(tmp_path),
    )

    # ACT
    deployment_manager._deploy_templates(str(source_path), str(target_path))

    # ASSERT
    assert (target_path / "templates" / "new.txt").exists()
    assert not (target_path / "templates" / "old.txt").exists()


def test_deploy_templates_raises_error_on_copy_failure(
    deployment_manager: DeploymentManager, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:  # CRITICAL TEST
    """Test _deploy_templates raises DeploymentError on copy failure."""
    # ARRANGE
    source_path: Path = tmp_path / "source"
    templates_dir: Path = source_path / "templates"
    templates_dir.mkdir(parents=True)

    target_path: Path = tmp_path / "target"
    target_path.mkdir()

    # Mock copytree to fail
    monkeypatch.setattr("shutil.copytree", Mock(side_effect=PermissionError("Mock error")))

    # ACT & ASSERT
    with pytest.raises(DeploymentError, match="Failed to deploy templates"):
        deployment_manager._deploy_templates(str(source_path), str(target_path))


# -------------------------------------------------------------
# TESTS FOR _deploy_configs
# -------------------------------------------------------------


def test_deploy_configs_creates_configs_from_templates(deployment_manager: DeploymentManager, tmp_path: Path) -> None:
    """Test _deploy_configs creates config files from templates."""
    # ARRANGE
    target_path: Path = tmp_path / "target"
    template_dir: Path = target_path / "templates" / "config"
    template_dir.mkdir(parents=True)
    (template_dir / "config.json").write_text('{"key": "value"}')

    # ACT
    deployment_manager._deploy_configs(str(target_path))

    # ASSERT
    assert (target_path / "config" / "config.json").exists()
    assert (target_path / "config" / "config.json").read_text() == '{"key": "value"}'


def test_deploy_configs_preserves_existing_user_configs(deployment_manager: DeploymentManager, tmp_path: Path) -> None:
    """Test _deploy_configs preserves existing user config files."""
    # ARRANGE
    target_path: Path = tmp_path / "target"
    template_dir: Path = target_path / "templates" / "config"
    template_dir.mkdir(parents=True)
    (template_dir / "config.json").write_text('{"new": "template"}')

    config_dir: Path = target_path / "config"
    config_dir.mkdir()
    (config_dir / "config.json").write_text('{"user": "custom"}')

    # ACT
    deployment_manager._deploy_configs(str(target_path))

    # ASSERT
    # User config should be preserved
    assert (config_dir / "config.json").read_text() == '{"user": "custom"}'


def test_deploy_configs_skips_when_no_template_directory(
    deployment_manager: DeploymentManager, tmp_path: Path
) -> None:
    """Test _deploy_configs skips when templates/config directory doesn't exist."""
    # ARRANGE
    target_path: Path = tmp_path / "target"
    target_path.mkdir()

    # ACT (should not raise)
    deployment_manager._deploy_configs(str(target_path))

    # ASSERT (no exception raised)


def test_deploy_configs_raises_error_on_copy_failure(
    deployment_manager: DeploymentManager, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:  # CRITICAL TEST
    """Test _deploy_configs raises DeploymentError on copy failure."""
    # ARRANGE
    target_path: Path = tmp_path / "target"
    template_dir: Path = target_path / "templates" / "config"
    template_dir.mkdir(parents=True)
    (template_dir / "config.json").write_text("{}")

    # Mock copy2 to fail
    monkeypatch.setattr("shutil.copy2", Mock(side_effect=PermissionError("Mock error")))

    # ACT & ASSERT
    with pytest.raises(DeploymentError, match="Failed to deploy configs"):
        deployment_manager._deploy_configs(str(target_path))


# -------------------------------------------------------------
# TESTS FOR _deploy_bin_tools
# -------------------------------------------------------------


def test_deploy_bin_tools_copies_bin_directory_and_creates_wrappers(
    deployment_manager: DeploymentManager, tmp_path: Path, mock_deployment_dir: Path
) -> None:
    """Test _deploy_bin_tools copies bin directory and creates global wrappers."""
    # ARRANGE
    source_path: Path = tmp_path / "source"
    bin_dir: Path = source_path / "bin"
    bin_dir.mkdir(parents=True)
    (bin_dir / "tool.py").write_text("#!/usr/bin/env python\nprint('tool')")

    target_path: Path = tmp_path / "target"
    target_path.mkdir()

    module_name: str = "testmodule"

    # ACT
    deployment_manager._deploy_bin_tools(str(source_path), str(target_path), module_name)

    # ASSERT
    assert (target_path / "bin" / "tool.py").exists()
    assert os.access(str(target_path / "bin" / "tool.py"), os.X_OK)

    # Check wrapper created
    global_bin: Path = mock_deployment_dir / "bin"
    assert (global_bin / "tool").exists()


def test_deploy_bin_tools_skips_when_no_bin_directory(deployment_manager: DeploymentManager, tmp_path: Path) -> None:
    """Test _deploy_bin_tools skips when bin directory doesn't exist."""
    # ARRANGE
    source_path: Path = tmp_path / "source"
    source_path.mkdir()
    target_path: Path = tmp_path / "target"
    target_path.mkdir()

    # ACT (should not raise)
    deployment_manager._deploy_bin_tools(str(source_path), str(target_path), "testmodule")

    # ASSERT (no exception raised)


def test_deploy_bin_tools_raises_error_on_failure(
    deployment_manager: DeploymentManager, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:  # CRITICAL TEST
    """Test _deploy_bin_tools raises DeploymentError on copy failure."""
    # ARRANGE
    source_path: Path = tmp_path / "source"
    bin_dir: Path = source_path / "bin"
    bin_dir.mkdir(parents=True)
    (bin_dir / "tool.py").write_text("#!/usr/bin/env python")

    target_path: Path = tmp_path / "target"
    target_path.mkdir()

    # Mock copytree to fail
    monkeypatch.setattr("shutil.copytree", Mock(side_effect=PermissionError("Mock error")))

    # ACT & ASSERT
    with pytest.raises(DeploymentError, match="Failed to deploy bin tools"):
        deployment_manager._deploy_bin_tools(str(source_path), str(target_path), "testmodule")


# -------------------------------------------------------------
# TESTS FOR _remove_module_wrappers
# -------------------------------------------------------------


def test_remove_module_wrappers_removes_matching_wrappers(
    deployment_manager: DeploymentManager, tmp_path: Path
) -> None:
    """Test _remove_module_wrappers removes wrappers that match module name."""
    # ARRANGE
    global_bin: Path = tmp_path / "bin"
    global_bin.mkdir()

    module_name: str = "testmodule"

    # Create wrapper for testmodule
    wrapper1: Path = global_bin / "tool1"
    wrapper1.write_text(f'#!/bin/bash\nexec /path/packages/{module_name}/bin/tool1 "$@"')

    # Create wrapper for different module
    wrapper2: Path = global_bin / "tool2"
    wrapper2.write_text('#!/bin/bash\nexec /path/packages/othermodule/bin/tool2 "$@"')

    # ACT
    deployment_manager._remove_module_wrappers(str(global_bin), module_name)

    # ASSERT
    assert not wrapper1.exists()
    assert wrapper2.exists()


def test_remove_module_wrappers_handles_nonexistent_directory_gracefully(
    deployment_manager: DeploymentManager, tmp_path: Path
) -> None:
    """Test _remove_module_wrappers handles nonexistent bin directory gracefully."""
    # ARRANGE
    global_bin: str = str(tmp_path / "nonexistent_bin")

    # ACT (should not raise)
    deployment_manager._remove_module_wrappers(global_bin, "testmodule")

    # ASSERT (no exception raised)


def test_remove_module_wrappers_handles_read_errors_gracefully(
    deployment_manager: DeploymentManager, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test _remove_module_wrappers handles file read errors gracefully."""
    # ARRANGE
    global_bin: Path = tmp_path / "bin"
    global_bin.mkdir()

    wrapper: Path = global_bin / "tool"
    wrapper.write_text("content")

    # Mock open to raise exception
    original_open = open

    def mock_open(path, *args, **kwargs):
        if str(path) == str(wrapper):
            raise PermissionError("Mock error")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr("builtins.open", mock_open)

    # ACT (should not raise)
    deployment_manager._remove_module_wrappers(str(global_bin), "testmodule")

    # ASSERT (no exception raised, file still exists)
    assert wrapper.exists()


def test_remove_module_wrappers_skips_non_file_entries(deployment_manager: DeploymentManager, tmp_path: Path) -> None:
    """Test _remove_module_wrappers skips directories and non-files."""
    # ARRANGE
    global_bin: Path = tmp_path / "bin"
    global_bin.mkdir()

    # Create a subdirectory (should be skipped)
    subdir: Path = global_bin / "subdir"
    subdir.mkdir()

    # Create wrapper
    wrapper: Path = global_bin / "tool"
    wrapper.write_text('#!/bin/bash\nexec /path/packages/testmodule/bin/tool "$@"')

    # ACT
    deployment_manager._remove_module_wrappers(str(global_bin), "testmodule")

    # ASSERT
    assert subdir.exists()
    assert not wrapper.exists()


# -------------------------------------------------------------
# TESTS FOR _hash_pip_freeze with timeout
# -------------------------------------------------------------


def test_hash_pip_freeze_returns_pip_timeout_on_timeout(
    deployment_manager: DeploymentManager, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test _hash_pip_freeze returns 'pip-timeout' on timeout."""
    # ARRANGE
    venv_path: Path = tmp_path / "venv" / "bin"
    venv_path.mkdir(parents=True)
    pip_path: Path = venv_path / "pip"
    pip_path.write_text("#!/bin/bash\nsleep 100")
    pip_path.chmod(0o755)

    # Mock subprocess to raise TimeoutExpired
    monkeypatch.setattr("subprocess.run", Mock(side_effect=subprocess.TimeoutExpired("pip", 30)))

    # ACT
    result: str = deployment_manager._hash_pip_freeze(str(venv_path.parent))

    # ASSERT
    assert result == "pip-timeout"


def test_hash_pip_freeze_returns_hash_on_success(
    deployment_manager: DeploymentManager, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test _hash_pip_freeze returns hash on successful pip list."""
    # ARRANGE
    venv_path: Path = tmp_path / "venv" / "bin"
    venv_path.mkdir(parents=True)
    pip_path: Path = venv_path / "pip"
    pip_path.write_text("#!/bin/bash")
    pip_path.chmod(0o755)

    # Mock subprocess
    mock_result: Mock = Mock()
    mock_result.returncode = 0
    mock_result.stdout = "package1==1.0.0\npackage2==2.0.0"
    monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: mock_result)

    # ACT
    result: str = deployment_manager._hash_pip_freeze(str(venv_path.parent))

    # ASSERT
    assert result != "no-venv"
    assert result != "pip-error"
    assert isinstance(result, str)
    assert len(result) == 64


# -------------------------------------------------------------
# TESTS FOR _get_hash_file_path
# -------------------------------------------------------------


def test_get_hash_file_path_returns_correct_path(
    deployment_manager: DeploymentManager, mock_deployment_dir: Path
) -> None:
    """Test _get_hash_file_path returns correct hash file path."""
    # ARRANGE
    module_name: str = "testmodule"

    # ACT
    result: str = deployment_manager._get_hash_file_path(module_name)

    # ASSERT
    assert result.endswith(f"deployment/hashes/{module_name}.hash")
    assert "testmodule.hash" in result


# -------------------------------------------------------------
# TESTS FOR _parse_project_dependencies with various formats
# -------------------------------------------------------------


def test_parse_project_dependencies_handles_version_specifiers(
    deployment_manager: DeploymentManager, tmp_path: Path
) -> None:
    """Test _parse_project_dependencies extracts package names from various version formats."""
    # ARRANGE
    source_path: Path = tmp_path
    pyproject_file: Path = source_path / "pyproject.toml"
    pyproject_content: str = """
[project]
dependencies = [
    "pkg1>=1.0.0",
    "pkg2==2.0.0",
    "pkg3~=3.0",
    "pkg4<4.0",
    "pkg5>5.0",
    "pkg6[extra]>=6.0"
]
"""
    pyproject_file.write_text(pyproject_content)

    # ACT
    result: List[str] = deployment_manager._parse_project_dependencies(str(source_path))

    # ASSERT
    assert "pkg1" in result
    assert "pkg2" in result
    assert "pkg3" in result
    assert "pkg4" in result
    assert "pkg5" in result
    assert "pkg6" in result
    assert len(result) == 6


def test_parse_project_dependencies_handles_missing_project_section(
    deployment_manager: DeploymentManager, tmp_path: Path
) -> None:
    """Test _parse_project_dependencies handles TOML without [project] section."""
    # ARRANGE
    source_path: Path = tmp_path
    pyproject_file: Path = source_path / "pyproject.toml"
    pyproject_content: str = """
[build-system]
requires = ["setuptools"]
"""
    pyproject_file.write_text(pyproject_content)

    # ACT
    result: List[str] = deployment_manager._parse_project_dependencies(str(source_path))

    # ASSERT
    assert result == []


def test_parse_project_dependencies_handles_tomli_import_error(
    deployment_manager: DeploymentManager, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test _parse_project_dependencies handles missing tomllib/tomli gracefully."""
    # ARRANGE
    source_path: Path = tmp_path
    pyproject_file: Path = source_path / "pyproject.toml"
    pyproject_file.write_text('[project]\ndependencies = ["pkg1"]')

    # Mock module-level tomllib to None (simulating unavailable TOML parser)
    import basefunctions.runtime.deployment_manager

    monkeypatch.setattr(basefunctions.runtime.deployment_manager, "tomllib", None)

    # ACT
    result: List[str] = deployment_manager._parse_project_dependencies(str(source_path))

    # ASSERT
    assert result == []


# -------------------------------------------------------------
# TESTS FOR edge cases to increase coverage to >80%
# -------------------------------------------------------------


def test_deploy_module_removes_existing_target_directory(
    deployment_manager: DeploymentManager,
    mock_module_structure: Dict[str, Any],
    mock_deployment_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test deploy_module removes existing target directory before deployment."""
    # ARRANGE
    module_name: str = mock_module_structure["module_name"]
    module_path: Path = mock_module_structure["module_path"]

    monkeypatch.setattr("os.getcwd", lambda: str(module_path))
    monkeypatch.setattr(
        "basefunctions.runtime.deployment_manager.basefunctions.runtime.find_development_path",
        lambda name: [str(module_path)],
    )

    # Create existing deployment with files
    target_path: Path = mock_deployment_dir / "packages" / module_name
    target_path.mkdir(parents=True)
    (target_path / "old_file.txt").write_text("old content")

    # Mock deployment methods
    monkeypatch.setattr(deployment_manager, "_detect_changes", lambda name, path: True)
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
    # Old file should be gone
    assert not (target_path / "old_file.txt").exists()


def test_get_stored_hash_handles_read_exception(
    deployment_manager: DeploymentManager,
    mock_deployment_dir: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test _get_stored_hash returns None on read exception."""
    # ARRANGE
    module_name: str = "testmodule"

    # Create hash file
    monkeypatch.setattr(deployment_manager, "_calculate_combined_hash", lambda path: "test_hash")
    source_path: Path = tmp_path / "source"
    source_path.mkdir()
    deployment_manager._update_hash(module_name, str(source_path))

    # Mock open to raise exception on read
    original_open = open

    def mock_open(path, *args, **kwargs):
        if "hash" in str(path):
            raise IOError("Mock read error")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr("builtins.open", mock_open)

    # ACT
    result: Optional[str] = deployment_manager._get_stored_hash(module_name)

    # ASSERT
    assert result is None


def test_remove_stored_hash_handles_remove_exception(
    deployment_manager: DeploymentManager,
    mock_deployment_dir: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test _remove_stored_hash handles os.remove exception gracefully."""
    # ARRANGE
    module_name: str = "testmodule"
    source_path: Path = tmp_path / "source"
    source_path.mkdir()

    # Create hash file
    monkeypatch.setattr(deployment_manager, "_calculate_combined_hash", lambda path: "test_hash")
    deployment_manager._update_hash(module_name, str(source_path))

    # Mock os.remove to raise exception
    monkeypatch.setattr("os.remove", Mock(side_effect=PermissionError("Mock error")))

    # ACT (should not raise)
    deployment_manager._remove_stored_hash(module_name)

    # ASSERT (no exception raised)


def test_install_local_package_with_venvutils_succeeds(
    deployment_manager: DeploymentManager,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Test _install_local_package_with_venvutils succeeds when all conditions
    met.
    """
    # ARRANGE
    venv_path: Path = tmp_path / "venv"
    venv_path.mkdir()
    package_name: str = "testpkg"

    deploy_dir: Path = tmp_path / "deployment"
    packages_dir: Path = deploy_dir / "packages" / package_name
    packages_dir.mkdir(parents=True)
    (packages_dir / "pyproject.toml").write_text('[project]\nname = "testpkg"')

    monkeypatch.setattr(
        "basefunctions.runtime.deployment_manager.basefunctions.runtime" ".get_bootstrap_deployment_directory",
        lambda: str(deploy_dir),
    )

    # Mock VenvUtils to succeed
    mock_install_with_ppip = Mock()
    mock_run_pip = Mock()
    monkeypatch.setattr(
        "basefunctions.runtime.deployment_manager.basefunctions.VenvUtils.install_with_ppip",
        mock_install_with_ppip,
    )
    monkeypatch.setattr(
        "basefunctions.runtime.deployment_manager.basefunctions.VenvUtils" ".run_pip_command",
        mock_run_pip,
    )

    # ACT
    deployment_manager._install_local_package_with_venvutils(venv_path, package_name)

    # ASSERT - ppip should be called, run_pip should not (ppip succeeded)
    mock_install_with_ppip.assert_called_once()
    mock_run_pip.assert_not_called()


def test_deploy_venv_skips_when_no_source_venv(deployment_manager: DeploymentManager, tmp_path: Path) -> None:
    """Test _deploy_venv returns early when source .venv doesn't exist."""
    # ARRANGE
    source_path: Path = tmp_path / "source"
    source_path.mkdir()
    target_path: Path = tmp_path / "target"
    target_path.mkdir()

    # ACT (should return early without creating target venv)
    deployment_manager._deploy_venv(str(source_path), str(target_path))

    # ASSERT
    assert not (target_path / "venv").exists()


def test_deploy_venv_raises_error_on_generic_exception(
    deployment_manager: DeploymentManager,
    mock_module_structure: Dict[str, Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:  # CRITICAL TEST
    """Test _deploy_venv raises DeploymentError on generic exception."""
    # ARRANGE
    source_path: str = str(mock_module_structure["module_path"])
    target_path: str = str(tmp_path / "deployment")

    # Mock subprocess to succeed (venv creation)
    mock_subprocess: Mock = Mock()
    mock_subprocess.returncode = 0
    monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: mock_subprocess)

    # Mock _copy_package_structure to raise generic exception
    monkeypatch.setattr(
        deployment_manager, "_copy_package_structure", Mock(side_effect=RuntimeError("Mock generic error"))
    )

    # ACT & ASSERT
    with pytest.raises(DeploymentError, match="Failed to deploy virtual environment"):
        deployment_manager._deploy_venv(source_path, target_path)


def test_create_wrapper_raises_exception_on_write_failure(
    deployment_manager: DeploymentManager,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:  # CRITICAL TEST
    """Test _create_wrapper raises exception when writing wrapper fails."""
    # ARRANGE
    global_bin: str = str(tmp_path / "bin")
    os.makedirs(global_bin, exist_ok=True)

    tool_name: str = "test_tool.py"
    module_name: str = "testmodule"
    target_path: str = str(tmp_path / "deployment")

    # Mock open to raise exception
    original_open = open

    def mock_open(path, *args, **kwargs):
        if "test_tool" in str(path) and "w" in args:
            raise PermissionError("Mock write error")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr("builtins.open", mock_open)

    # ACT & ASSERT
    with pytest.raises(PermissionError):
        deployment_manager._create_wrapper(global_bin, tool_name, module_name, target_path)


# -------------------------------------------------------------
# TESTS FOR _validate_deployment_path
# -------------------------------------------------------------


def test_validate_deployment_path_raises_error_on_empty_path(
    deployment_manager: DeploymentManager,
) -> None:  # CRITICAL TEST
    """Test _validate_deployment_path raises DeploymentError when path is empty."""
    # ARRANGE
    empty_path: str = ""

    # ACT & ASSERT
    with pytest.raises(DeploymentError, match="Path cannot be empty"):
        deployment_manager._validate_deployment_path(empty_path)


def test_validate_deployment_path_raises_error_on_system_directory(
    deployment_manager: DeploymentManager,
) -> None:  # CRITICAL TEST
    """Test _validate_deployment_path rejects system directories."""
    # ARRANGE
    system_paths: List[str] = ["/", "/usr", "/bin", "/etc", "/var", "/tmp"]

    # ACT & ASSERT
    for path in system_paths:
        with pytest.raises(DeploymentError, match="CRITICAL.*system directory"):
            deployment_manager._validate_deployment_path(path)


def test_validate_deployment_path_raises_error_on_system_subdirectory(
    deployment_manager: DeploymentManager,
) -> None:  # CRITICAL TEST
    """Test _validate_deployment_path rejects subdirectories of system directories."""
    # ARRANGE
    system_subpaths: List[str] = ["/usr/local", "/etc/config", "/var/log"]

    # ACT & ASSERT
    for path in system_subpaths:
        with pytest.raises(DeploymentError, match="CRITICAL.*system directory"):
            deployment_manager._validate_deployment_path(path)


def test_validate_deployment_path_raises_error_on_home_directory(
    deployment_manager: DeploymentManager,
) -> None:  # CRITICAL TEST
    """Test _validate_deployment_path rejects home directory."""
    # ARRANGE
    home_path: str = "~"

    # ACT & ASSERT
    with pytest.raises(DeploymentError, match="CRITICAL.*home directory"):
        deployment_manager._validate_deployment_path(home_path)


def test_validate_deployment_path_raises_error_on_path_outside_deployment_dir(
    deployment_manager: DeploymentManager, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:  # CRITICAL TEST
    """Test _validate_deployment_path rejects paths outside deployment directory."""
    # ARRANGE
    deploy_dir: Path = tmp_path / "deployment"
    deploy_dir.mkdir()

    outside_path: Path = tmp_path / "other_directory"
    outside_path.mkdir()

    monkeypatch.setattr(
        "basefunctions.runtime.deployment_manager.basefunctions.runtime" ".get_bootstrap_deployment_directory",
        lambda: str(deploy_dir),
    )

    # ACT & ASSERT
    with pytest.raises(DeploymentError, match="Path must be within deployment directory"):
        deployment_manager._validate_deployment_path(str(outside_path))


def test_validate_deployment_path_raises_error_on_shallow_path(
    deployment_manager: DeploymentManager, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:  # CRITICAL TEST
    """Test _validate_deployment_path rejects paths too shallow from deployment root."""
    # ARRANGE
    deploy_dir: Path = tmp_path / "deployment"
    deploy_dir.mkdir()

    monkeypatch.setattr(
        "basefunctions.runtime.deployment_manager.basefunctions.runtime" ".get_bootstrap_deployment_directory",
        lambda: str(deploy_dir),
    )

    # ACT & ASSERT - deployment directory itself is too shallow
    with pytest.raises(DeploymentError, match="Path too shallow for destructive operation"):
        deployment_manager._validate_deployment_path(str(deploy_dir))


def test_validate_deployment_path_accepts_valid_path(
    deployment_manager: DeploymentManager, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test _validate_deployment_path accepts valid paths within deployment directory."""
    # ARRANGE
    deploy_dir: Path = tmp_path / "deployment"
    deploy_dir.mkdir()

    valid_path: Path = deploy_dir / "packages" / "mymodule"
    valid_path.mkdir(parents=True)

    monkeypatch.setattr(
        "basefunctions.runtime.deployment_manager.basefunctions.runtime" ".get_bootstrap_deployment_directory",
        lambda: str(deploy_dir),
    )

    # ACT (should not raise)
    deployment_manager._validate_deployment_path(str(valid_path))

    # ASSERT (no exception raised)


def test_validate_deployment_path_accepts_one_level_deep(
    deployment_manager: DeploymentManager, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test _validate_deployment_path accepts paths one level deep from deployment root."""
    # ARRANGE
    deploy_dir: Path = tmp_path / "deployment"
    deploy_dir.mkdir()

    one_level_path: Path = deploy_dir / "packages"
    one_level_path.mkdir()

    monkeypatch.setattr(
        "basefunctions.runtime.deployment_manager.basefunctions.runtime" ".get_bootstrap_deployment_directory",
        lambda: str(deploy_dir),
    )

    # ACT (should not raise)
    deployment_manager._validate_deployment_path(str(one_level_path))

    # ASSERT (no exception raised)


def test_validate_deployment_path_normalizes_tilde(
    deployment_manager: DeploymentManager, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test _validate_deployment_path correctly expands tilde in paths."""
    # ARRANGE
    deploy_dir: Path = Path.home() / ".test_deployment"

    # Use a path like ~/.test_deployment/packages/module
    test_path: str = "~/.test_deployment/packages/module"

    monkeypatch.setattr(
        "basefunctions.runtime.deployment_manager.basefunctions.runtime" ".get_bootstrap_deployment_directory",
        lambda: str(deploy_dir),
    )

    # ACT (should not raise if path is valid)
    # Note: This will validate the path structure even if it doesn't exist
    try:
        deployment_manager._validate_deployment_path(test_path)
    except DeploymentError as e:
        # Should not be a system directory or home directory error
        assert "system directory" not in str(e)
        assert "home directory" not in str(e)


def test_deploy_module_validates_path_before_removal(
    deployment_manager: DeploymentManager,
    mock_module_structure: Dict[str, Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:  # CRITICAL TEST
    """Test deploy_module validates path before performing shutil.rmtree."""
    # ARRANGE
    module_name: str = mock_module_structure["module_name"]
    module_path: Path = mock_module_structure["module_path"]

    monkeypatch.setattr("os.getcwd", lambda: str(module_path))
    monkeypatch.setattr(
        "basefunctions.runtime.deployment_manager.basefunctions.runtime.find_development_path",
        lambda name: [str(module_path)],
    )

    # Create deployment dir structure
    deploy_dir: Path = tmp_path / "deployment"
    deploy_dir.mkdir()

    # Mock deployment path to return a system directory (should be blocked)
    monkeypatch.setattr(
        "basefunctions.runtime.deployment_manager.basefunctions.runtime.get_deployment_path",
        lambda name: "/usr/local/test",  # System directory - should be rejected
    )
    monkeypatch.setattr(
        "basefunctions.runtime.deployment_manager.basefunctions.runtime" ".get_bootstrap_deployment_directory",
        lambda: str(deploy_dir),
    )

    # Mock _detect_changes to return True (force deployment)
    monkeypatch.setattr(deployment_manager, "_detect_changes", lambda name, path: True)

    # Create the target directory
    os.makedirs("/tmp/test_usr_local_test", exist_ok=True)
    monkeypatch.setattr("os.path.exists", lambda path: path == "/usr/local/test")

    # ACT & ASSERT
    with pytest.raises(DeploymentError, match="CRITICAL.*system directory"):
        deployment_manager.deploy_module(module_name, force=True)


def test_clean_deployment_validates_path_before_removal(
    deployment_manager: DeploymentManager, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:  # CRITICAL TEST
    """Test clean_deployment validates path before performing shutil.rmtree."""
    # ARRANGE
    module_name: str = "testmodule"

    # Mock deployment path to return a system directory (should be blocked)
    monkeypatch.setattr(
        "basefunctions.runtime.deployment_manager.basefunctions.runtime.get_deployment_path",
        lambda name: "/etc/test",  # System directory - should be rejected
    )

    deploy_dir: Path = tmp_path / "deployment"
    deploy_dir.mkdir()

    monkeypatch.setattr(
        "basefunctions.runtime.deployment_manager.basefunctions.runtime" ".get_bootstrap_deployment_directory",
        lambda: str(deploy_dir),
    )

    # Mock path exists
    monkeypatch.setattr("os.path.exists", lambda path: path == "/etc/test")

    # ACT & ASSERT
    with pytest.raises(DeploymentError, match="CRITICAL.*system directory"):
        deployment_manager.clean_deployment(module_name)
