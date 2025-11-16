"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.

 Description:
 Pytest test suite for VenvUtils.
 Tests platform-aware virtual environment operations and pip management.

 Log:
 v1.0.0 : Initial test implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
# External imports
import subprocess
import sys
from pathlib import Path
from typing import List, Optional
from unittest.mock import Mock, patch

import pytest

# Project imports
from basefunctions.runtime.venv_utils import VenvUtils, VenvUtilsError, PROTECTED_PACKAGES

# -------------------------------------------------------------
# FIXTURES
# -------------------------------------------------------------


@pytest.fixture
def mock_venv(tmp_path: Path) -> Path:
    """
    Create mock virtual environment structure.

    Parameters
    ----------
    tmp_path : Path
        Pytest builtin fixture for temporary directory

    Returns
    -------
    Path
        Path to mock virtual environment

    Notes
    -----
    Creates platform-appropriate bin/Scripts directory with pip and python executables
    """
    # ARRANGE
    venv_path: Path = tmp_path / ".venv"

    if sys.platform == "win32":
        scripts_dir: Path = venv_path / "Scripts"
        scripts_dir.mkdir(parents=True)
        (scripts_dir / "pip.exe").write_text("mock pip")
        (scripts_dir / "python.exe").write_text("mock python")
        (scripts_dir / "activate.bat").write_text("mock activate")
    else:
        bin_dir: Path = venv_path / "bin"
        bin_dir.mkdir(parents=True)
        (bin_dir / "pip").write_text("#!/bin/bash\necho pip")
        (bin_dir / "python").write_text("#!/bin/bash\necho python")
        (bin_dir / "activate").write_text("#!/bin/bash\necho activate")

    # RETURN
    return venv_path


@pytest.fixture
def platform_mock(monkeypatch: pytest.MonkeyPatch):
    """
    Factory fixture to mock sys.platform.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture

    Returns
    -------
    callable
        Function to set platform (accepts "win32" or "linux")

    Notes
    -----
    Use this to test platform-specific behavior
    """
    # RETURN
    def _set_platform(platform: str) -> None:
        monkeypatch.setattr("sys.platform", platform)

    return _set_platform


# -------------------------------------------------------------
# TESTS FOR get_pip_executable
# -------------------------------------------------------------


def test_get_pip_executable_returns_windows_path_on_win32(tmp_path: Path, platform_mock) -> None:
    """Test get_pip_executable returns Scripts/pip.exe on Windows."""
    # ARRANGE
    platform_mock("win32")
    venv_path: Path = tmp_path / "venv"

    # ACT
    result: Path = VenvUtils.get_pip_executable(venv_path)

    # ASSERT
    assert result == venv_path / "Scripts" / "pip.exe"


def test_get_pip_executable_returns_unix_path_on_posix(tmp_path: Path, platform_mock) -> None:
    """Test get_pip_executable returns bin/pip on Unix-like systems."""
    # ARRANGE
    platform_mock("linux")
    venv_path: Path = tmp_path / "venv"

    # ACT
    result: Path = VenvUtils.get_pip_executable(venv_path)

    # ASSERT
    assert result == venv_path / "bin" / "pip"


# -------------------------------------------------------------
# TESTS FOR get_python_executable
# -------------------------------------------------------------


def test_get_python_executable_returns_windows_path_on_win32(tmp_path: Path, platform_mock) -> None:
    """Test get_python_executable returns Scripts/python.exe on Windows."""
    # ARRANGE
    platform_mock("win32")
    venv_path: Path = tmp_path / "venv"

    # ACT
    result: Path = VenvUtils.get_python_executable(venv_path)

    # ASSERT
    assert result == venv_path / "Scripts" / "python.exe"


def test_get_python_executable_returns_unix_path_on_posix(tmp_path: Path, platform_mock) -> None:
    """Test get_python_executable returns bin/python on Unix-like systems."""
    # ARRANGE
    platform_mock("linux")
    venv_path: Path = tmp_path / "venv"

    # ACT
    result: Path = VenvUtils.get_python_executable(venv_path)

    # ASSERT
    assert result == venv_path / "bin" / "python"


# -------------------------------------------------------------
# TESTS FOR get_activate_script
# -------------------------------------------------------------


def test_get_activate_script_returns_windows_path_on_win32(tmp_path: Path, platform_mock) -> None:
    """Test get_activate_script returns Scripts/activate.bat on Windows."""
    # ARRANGE
    platform_mock("win32")
    venv_path: Path = tmp_path / "venv"

    # ACT
    result: Path = VenvUtils.get_activate_script(venv_path)

    # ASSERT
    assert result == venv_path / "Scripts" / "activate.bat"


def test_get_activate_script_returns_unix_path_on_posix(tmp_path: Path, platform_mock) -> None:
    """Test get_activate_script returns bin/activate on Unix-like systems."""
    # ARRANGE
    platform_mock("linux")
    venv_path: Path = tmp_path / "venv"

    # ACT
    result: Path = VenvUtils.get_activate_script(venv_path)

    # ASSERT
    assert result == venv_path / "bin" / "activate"


# -------------------------------------------------------------
# TESTS FOR is_virtual_environment
# -------------------------------------------------------------


def test_is_virtual_environment_returns_true_when_in_venv(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test is_virtual_environment returns True when running in virtual environment."""
    # ARRANGE
    monkeypatch.setattr(sys, "base_prefix", "/usr")
    monkeypatch.setattr(sys, "prefix", "/home/user/venv")

    # ACT
    result: bool = VenvUtils.is_virtual_environment()

    # ASSERT
    assert result is True


def test_is_virtual_environment_returns_false_when_not_in_venv(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test is_virtual_environment returns False when not in virtual environment."""
    # ARRANGE
    monkeypatch.setattr(sys, "base_prefix", "/usr")
    monkeypatch.setattr(sys, "prefix", "/usr")
    monkeypatch.delattr(sys, "real_prefix", raising=False)

    # ACT
    result: bool = VenvUtils.is_virtual_environment()

    # ASSERT
    assert result is False


# -------------------------------------------------------------
# TESTS FOR is_valid_venv
# -------------------------------------------------------------


def test_is_valid_venv_returns_true_for_valid_venv(mock_venv: Path) -> None:
    """Test is_valid_venv returns True for properly structured virtual environment."""
    # ACT
    result: bool = VenvUtils.is_valid_venv(mock_venv)

    # ASSERT
    assert result is True


def test_is_valid_venv_returns_false_for_missing_directory(tmp_path: Path) -> None:
    """Test is_valid_venv returns False when directory doesn't exist."""
    # ARRANGE
    nonexistent_path: Path = tmp_path / "nonexistent"

    # ACT
    result: bool = VenvUtils.is_valid_venv(nonexistent_path)

    # ASSERT
    assert result is False


def test_is_valid_venv_returns_false_for_missing_pip(tmp_path: Path) -> None:
    """Test is_valid_venv returns False when pip executable is missing."""
    # ARRANGE
    venv_path: Path = tmp_path / "venv"
    bin_dir: Path = venv_path / "bin"
    bin_dir.mkdir(parents=True)
    (bin_dir / "python").write_text("#!/bin/bash\necho python")

    # ACT
    result: bool = VenvUtils.is_valid_venv(venv_path)

    # ASSERT
    assert result is False


def test_is_valid_venv_returns_false_for_missing_python(tmp_path: Path) -> None:
    """Test is_valid_venv returns False when python executable is missing."""
    # ARRANGE
    venv_path: Path = tmp_path / "venv"
    bin_dir: Path = venv_path / "bin"
    bin_dir.mkdir(parents=True)
    (bin_dir / "pip").write_text("#!/bin/bash\necho pip")

    # ACT
    result: bool = VenvUtils.is_valid_venv(venv_path)

    # ASSERT
    assert result is False


# -------------------------------------------------------------
# TESTS FOR find_venv_in_directory
# -------------------------------------------------------------


def test_find_venv_in_directory_returns_venv_when_found(mock_venv: Path) -> None:
    """Test find_venv_in_directory returns venv path when found."""
    # ARRANGE
    directory: Path = mock_venv.parent

    # ACT
    result: Optional[Path] = VenvUtils.find_venv_in_directory(directory, venv_name=".venv")

    # ASSERT
    assert result == mock_venv


def test_find_venv_in_directory_returns_none_when_not_found(tmp_path: Path) -> None:
    """Test find_venv_in_directory returns None when venv not found."""
    # ARRANGE
    directory: Path = tmp_path

    # ACT
    result: Optional[Path] = VenvUtils.find_venv_in_directory(directory)

    # ASSERT
    assert result is None


def test_find_venv_in_directory_uses_custom_venv_name(tmp_path: Path) -> None:
    """Test find_venv_in_directory searches for custom venv directory name."""
    # ARRANGE
    directory: Path = tmp_path
    custom_venv: Path = directory / "custom_env"
    bin_dir: Path = custom_venv / "bin"
    bin_dir.mkdir(parents=True)
    (bin_dir / "pip").write_text("#!/bin/bash")
    (bin_dir / "python").write_text("#!/bin/bash")

    # ACT
    result: Optional[Path] = VenvUtils.find_venv_in_directory(directory, venv_name="custom_env")

    # ASSERT
    assert result == custom_venv


# -------------------------------------------------------------
# TESTS FOR run_pip_command
# -------------------------------------------------------------


def test_run_pip_command_executes_successfully(mock_venv: Path, monkeypatch: pytest.MonkeyPatch) -> None:  # CRITICAL TEST
    """Test run_pip_command executes pip command successfully."""
    # ARRANGE
    command: List[str] = ["install", "pytest"]

    mock_result: Mock = Mock()
    mock_result.returncode = 0
    mock_run: Mock = Mock(return_value=mock_result)
    monkeypatch.setattr("subprocess.run", mock_run)

    # ACT
    result = VenvUtils.run_pip_command(command, mock_venv, capture_output=True)

    # ASSERT
    assert mock_run.called
    call_args = mock_run.call_args
    assert "install" in call_args[0][0]
    assert "pytest" in call_args[0][0]


def test_run_pip_command_raises_error_on_failure(mock_venv: Path, monkeypatch: pytest.MonkeyPatch) -> None:  # CRITICAL TEST
    """Test run_pip_command raises VenvUtilsError when pip command fails."""
    # ARRANGE
    command: List[str] = ["install", "nonexistent-package"]

    monkeypatch.setattr(
        "subprocess.run",
        Mock(side_effect=subprocess.CalledProcessError(1, "pip")),
    )

    # ACT & ASSERT
    with pytest.raises(VenvUtilsError, match="Pip command failed"):
        VenvUtils.run_pip_command(command, mock_venv, capture_output=True)


def test_run_pip_command_raises_error_on_timeout(mock_venv: Path, monkeypatch: pytest.MonkeyPatch) -> None:  # CRITICAL TEST
    """Test run_pip_command raises VenvUtilsError when command times out."""
    # ARRANGE
    command: List[str] = ["install", "package"]

    monkeypatch.setattr(
        "subprocess.run",
        Mock(side_effect=subprocess.TimeoutExpired("pip", 10)),
    )

    # ACT & ASSERT
    with pytest.raises(VenvUtilsError, match="Pip command timed out"):
        VenvUtils.run_pip_command(command, mock_venv, timeout=10, capture_output=True)


def test_run_pip_command_handles_empty_command_list(mock_venv: Path, monkeypatch: pytest.MonkeyPatch) -> None:  # CRITICAL TEST
    """Test run_pip_command handles empty command list correctly."""
    # ARRANGE
    command: List[str] = []

    mock_result: Mock = Mock()
    mock_result.returncode = 0
    mock_run: Mock = Mock(return_value=mock_result)
    monkeypatch.setattr("subprocess.run", mock_run)

    # ACT
    VenvUtils.run_pip_command(command, mock_venv, capture_output=True)

    # ASSERT
    assert mock_run.called


def test_run_pip_command_respects_capture_output_flag(mock_venv: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test run_pip_command respects capture_output parameter."""
    # ARRANGE
    command: List[str] = ["list"]

    mock_result: Mock = Mock()
    mock_result.returncode = 0
    mock_run: Mock = Mock(return_value=mock_result)
    monkeypatch.setattr("subprocess.run", mock_run)

    # ACT
    VenvUtils.run_pip_command(command, mock_venv, capture_output=False)

    # ASSERT
    call_kwargs = mock_run.call_args[1]
    assert call_kwargs["capture_output"] is False


def test_run_pip_command_with_cwd_parameter_passes_to_subprocess(mock_venv: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test run_pip_command passes cwd parameter to subprocess.run()."""
    # ARRANGE
    command: List[str] = ["install", "pytest"]
    work_dir: Path = tmp_path / "work"
    work_dir.mkdir()

    mock_result: Mock = Mock()
    mock_result.returncode = 0
    mock_run: Mock = Mock(return_value=mock_result)
    monkeypatch.setattr("subprocess.run", mock_run)

    # ACT
    VenvUtils.run_pip_command(command, mock_venv, cwd=work_dir, capture_output=True)

    # ASSERT
    call_kwargs = mock_run.call_args[1]
    assert call_kwargs["cwd"] == work_dir


def test_run_pip_command_with_none_cwd_uses_default(mock_venv: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test run_pip_command with cwd=None uses subprocess default."""
    # ARRANGE
    command: List[str] = ["list"]

    mock_result: Mock = Mock()
    mock_result.returncode = 0
    mock_run: Mock = Mock(return_value=mock_result)
    monkeypatch.setattr("subprocess.run", mock_run)

    # ACT
    VenvUtils.run_pip_command(command, mock_venv, cwd=None, capture_output=True)

    # ASSERT
    call_kwargs = mock_run.call_args[1]
    assert call_kwargs["cwd"] is None


def test_run_pip_command_without_cwd_parameter_defaults_to_none(mock_venv: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test run_pip_command without cwd parameter defaults to None."""
    # ARRANGE
    command: List[str] = ["list"]

    mock_result: Mock = Mock()
    mock_result.returncode = 0
    mock_run: Mock = Mock(return_value=mock_result)
    monkeypatch.setattr("subprocess.run", mock_run)

    # ACT
    VenvUtils.run_pip_command(command, mock_venv, capture_output=True)

    # ASSERT
    call_kwargs = mock_run.call_args[1]
    assert call_kwargs["cwd"] is None


def test_run_pip_command_with_cwd_as_string_path(mock_venv: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test run_pip_command with cwd as Path object (edge case for type compatibility)."""
    # ARRANGE
    command: List[str] = ["list"]
    work_dir: Path = tmp_path / "workdir"
    work_dir.mkdir()

    mock_result: Mock = Mock()
    mock_result.returncode = 0
    mock_run: Mock = Mock(return_value=mock_result)
    monkeypatch.setattr("subprocess.run", mock_run)

    # ACT
    VenvUtils.run_pip_command(command, mock_venv, cwd=work_dir, capture_output=True)

    # ASSERT
    call_kwargs = mock_run.call_args[1]
    # Verify cwd is passed correctly (Path objects are accepted by subprocess.run)
    assert call_kwargs["cwd"] == work_dir


# -------------------------------------------------------------
# TESTS FOR get_installed_packages
# -------------------------------------------------------------


def test_get_installed_packages_returns_package_list(mock_venv: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_installed_packages returns list of installed packages."""
    # ARRANGE
    mock_output: str = "pytest==7.0.0\nrequests==2.28.0\npip==22.0.0"

    mock_result: Mock = Mock()
    mock_result.returncode = 0
    mock_result.stdout = mock_output
    monkeypatch.setattr("subprocess.run", Mock(return_value=mock_result))

    # ACT
    result: List[str] = VenvUtils.get_installed_packages(mock_venv, include_protected=False, capture_output=True)

    # ASSERT
    assert "pytest" in result
    assert "requests" in result
    assert "pip" not in result  # Protected package excluded


def test_get_installed_packages_includes_protected_when_requested(mock_venv: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_installed_packages includes protected packages when include_protected is True."""
    # ARRANGE
    mock_output: str = "pytest==7.0.0\npip==22.0.0\nsetuptools==60.0.0"

    mock_result: Mock = Mock()
    mock_result.returncode = 0
    mock_result.stdout = mock_output
    monkeypatch.setattr("subprocess.run", Mock(return_value=mock_result))

    # ACT
    result: List[str] = VenvUtils.get_installed_packages(mock_venv, include_protected=True, capture_output=True)

    # ASSERT
    assert "pip" in result
    assert "setuptools" in result


def test_get_installed_packages_raises_error_on_failure(mock_venv: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_installed_packages raises VenvUtilsError when pip list fails."""
    # ARRANGE
    monkeypatch.setattr(
        "subprocess.run",
        Mock(side_effect=subprocess.CalledProcessError(1, "pip")),
    )

    # ACT & ASSERT
    with pytest.raises(VenvUtilsError, match="Failed to list packages"):
        VenvUtils.get_installed_packages(mock_venv, capture_output=True)


def test_get_installed_packages_raises_error_on_timeout(mock_venv: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_installed_packages raises VenvUtilsError when command times out."""
    # ARRANGE
    monkeypatch.setattr(
        "subprocess.run",
        Mock(side_effect=subprocess.TimeoutExpired("pip", 30)),
    )

    # ACT & ASSERT
    with pytest.raises(VenvUtilsError, match="Package listing timed out"):
        VenvUtils.get_installed_packages(mock_venv, capture_output=True)


# -------------------------------------------------------------
# TESTS FOR get_package_info
# -------------------------------------------------------------


def test_get_package_info_returns_package_information(mock_venv: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_package_info returns dictionary with package information."""
    # ARRANGE
    package_name: str = "pytest"
    mock_output: str = "Name: pytest\nVersion: 7.0.0\nSummary: Testing framework"

    mock_result: Mock = Mock()
    mock_result.returncode = 0
    mock_result.stdout = mock_output
    monkeypatch.setattr("subprocess.run", Mock(return_value=mock_result))

    # ACT
    result: Optional[dict] = VenvUtils.get_package_info(package_name, mock_venv, capture_output=True)

    # ASSERT
    assert result is not None
    assert result["Name"] == "pytest"
    assert result["Version"] == "7.0.0"


def test_get_package_info_returns_none_when_package_not_found(mock_venv: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_package_info returns None when package not found."""
    # ARRANGE
    package_name: str = "nonexistent-package"

    monkeypatch.setattr(
        "subprocess.run",
        Mock(side_effect=subprocess.CalledProcessError(1, "pip")),
    )

    # ACT
    result: Optional[dict] = VenvUtils.get_package_info(package_name, mock_venv, capture_output=True)

    # ASSERT
    assert result is None


def test_get_package_info_returns_none_when_capture_output_false(mock_venv: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_package_info returns None when capture_output is False."""
    # ARRANGE
    package_name: str = "pytest"

    mock_result: Mock = Mock()
    mock_result.returncode = 0
    monkeypatch.setattr("subprocess.run", Mock(return_value=mock_result))

    # ACT
    result: Optional[dict] = VenvUtils.get_package_info(package_name, mock_venv, capture_output=False)

    # ASSERT
    assert result is None


# -------------------------------------------------------------
# TESTS FOR uninstall_packages
# -------------------------------------------------------------


def test_uninstall_packages_executes_correctly(mock_venv: Path, monkeypatch: pytest.MonkeyPatch) -> None:  # CRITICAL TEST
    """Test uninstall_packages executes uninstall command correctly."""
    # ARRANGE
    packages: List[str] = ["pytest", "requests"]

    mock_result: Mock = Mock()
    mock_result.returncode = 0
    mock_run: Mock = Mock(return_value=mock_result)
    monkeypatch.setattr("subprocess.run", mock_run)

    # ACT
    VenvUtils.uninstall_packages(packages, mock_venv, capture_output=True)

    # ASSERT
    assert mock_run.called
    call_args = mock_run.call_args[0][0]
    assert "uninstall" in call_args
    assert "-y" in call_args
    assert "pytest" in call_args
    assert "requests" in call_args


def test_uninstall_packages_handles_empty_list_gracefully(mock_venv: Path) -> None:  # CRITICAL TEST
    """Test uninstall_packages handles empty package list gracefully."""
    # ARRANGE
    packages: List[str] = []

    # ACT (should not raise)
    VenvUtils.uninstall_packages(packages, mock_venv, capture_output=True)

    # ASSERT
    # No exception raised


def test_uninstall_packages_raises_error_on_failure(mock_venv: Path, monkeypatch: pytest.MonkeyPatch) -> None:  # CRITICAL TEST
    """Test uninstall_packages raises VenvUtilsError when uninstall fails."""
    # ARRANGE
    packages: List[str] = ["nonexistent-package"]

    monkeypatch.setattr(
        "subprocess.run",
        Mock(side_effect=subprocess.CalledProcessError(1, "pip")),
    )

    # ACT & ASSERT
    with pytest.raises(VenvUtilsError, match="Pip command failed"):
        VenvUtils.uninstall_packages(packages, mock_venv, capture_output=True)


# -------------------------------------------------------------
# TESTS FOR upgrade_pip
# -------------------------------------------------------------


def test_upgrade_pip_executes_successfully(mock_venv: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test upgrade_pip executes pip upgrade command successfully."""
    # ARRANGE
    mock_result: Mock = Mock()
    mock_result.returncode = 0
    mock_run: Mock = Mock(return_value=mock_result)
    monkeypatch.setattr("subprocess.run", mock_run)

    # ACT
    VenvUtils.upgrade_pip(mock_venv, capture_output=True)

    # ASSERT
    assert mock_run.called
    call_args = mock_run.call_args[0][0]
    assert "install" in call_args
    assert "--upgrade" in call_args
    assert "pip" in call_args


def test_upgrade_pip_raises_error_on_failure(mock_venv: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test upgrade_pip raises VenvUtilsError when upgrade fails."""
    # ARRANGE
    monkeypatch.setattr(
        "subprocess.run",
        Mock(side_effect=subprocess.CalledProcessError(1, "pip")),
    )

    # ACT & ASSERT
    with pytest.raises(VenvUtilsError, match="Pip command failed"):
        VenvUtils.upgrade_pip(mock_venv, capture_output=True)


# -------------------------------------------------------------
# TESTS FOR install_requirements
# -------------------------------------------------------------


def test_install_requirements_executes_successfully(mock_venv: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:  # CRITICAL TEST
    """Test install_requirements installs from requirements file successfully."""
    # ARRANGE
    requirements_file: Path = tmp_path / "requirements.txt"
    requirements_file.write_text("pytest>=7.0.0\nrequests>=2.28.0")

    mock_result: Mock = Mock()
    mock_result.returncode = 0
    mock_run: Mock = Mock(return_value=mock_result)
    monkeypatch.setattr("subprocess.run", mock_run)

    # ACT
    VenvUtils.install_requirements(mock_venv, requirements_file, capture_output=True)

    # ASSERT
    assert mock_run.called
    call_args = mock_run.call_args[0][0]
    assert "install" in call_args
    assert "-r" in call_args


def test_install_requirements_raises_error_when_file_missing(mock_venv: Path, tmp_path: Path) -> None:  # CRITICAL TEST
    """Test install_requirements raises VenvUtilsError when requirements file doesn't exist."""
    # ARRANGE
    nonexistent_file: Path = tmp_path / "nonexistent.txt"

    # ACT & ASSERT
    with pytest.raises(VenvUtilsError, match="Requirements file not found"):
        VenvUtils.install_requirements(mock_venv, nonexistent_file, capture_output=True)


def test_install_requirements_raises_error_on_install_failure(
    mock_venv: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test install_requirements raises VenvUtilsError when pip install fails."""
    # ARRANGE
    requirements_file: Path = tmp_path / "requirements.txt"
    requirements_file.write_text("invalid-package>=999.0.0")

    monkeypatch.setattr(
        "subprocess.run",
        Mock(side_effect=subprocess.CalledProcessError(1, "pip")),
    )

    # ACT & ASSERT
    with pytest.raises(VenvUtilsError, match="Pip command failed"):
        VenvUtils.install_requirements(mock_venv, requirements_file, capture_output=True)


# -------------------------------------------------------------
# TESTS FOR get_venv_size
# -------------------------------------------------------------


def test_get_venv_size_returns_size_in_bytes(mock_venv: Path) -> None:
    """Test get_venv_size returns virtual environment size in bytes."""
    # ACT
    result: int = VenvUtils.get_venv_size(mock_venv)

    # ASSERT
    assert isinstance(result, int)
    assert result > 0


def test_get_venv_size_returns_zero_for_nonexistent_venv(tmp_path: Path) -> None:
    """Test get_venv_size returns 0 for nonexistent virtual environment."""
    # ARRANGE
    nonexistent_venv: Path = tmp_path / "nonexistent"

    # ACT
    result: int = VenvUtils.get_venv_size(nonexistent_venv)

    # ASSERT
    assert result == 0


def test_get_venv_size_handles_permission_errors_gracefully(mock_venv: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_venv_size handles file permission errors gracefully."""
    # ARRANGE
    # Create a file that will raise OSError when stat() is called
    test_file: Path = mock_venv / "bin" / "protected_file"
    test_file.write_text("test")

    original_stat = Path.stat
    call_count = {"count": 0}

    def mock_stat(self, *, follow_symlinks=True):
        # Only raise error on subsequent calls (not the first call from is_file check)
        if self.name == "protected_file":
            call_count["count"] += 1
            if call_count["count"] > 1:
                raise OSError("Permission denied")
        return original_stat(self, follow_symlinks=follow_symlinks)

    monkeypatch.setattr(Path, "stat", mock_stat)

    # ACT
    result: int = VenvUtils.get_venv_size(mock_venv)

    # ASSERT
    assert isinstance(result, int)
    # Should still return size, just excluding the protected file


# -------------------------------------------------------------
# TESTS FOR format_size
# -------------------------------------------------------------


@pytest.mark.parametrize(
    "size_bytes,expected_output",
    [
        (0, "0.0 B"),
        (512, "512.0 B"),
        (1024, "1.0 KB"),
        (1536, "1.5 KB"),
        (1048576, "1.0 MB"),
        (1073741824, "1.0 GB"),
        (1099511627776, "1.0 TB"),
    ],
)
def test_format_size_formats_correctly(size_bytes: int, expected_output: str) -> None:
    """Test format_size formats various byte sizes correctly."""
    # ACT
    result: str = VenvUtils.format_size(size_bytes)

    # ASSERT
    assert result == expected_output
