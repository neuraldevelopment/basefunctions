"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Tests for create_python_project.py - verify exception handling in
 _setup_virtual_environment: editable install must propagate errors,
 dev extras must tolerate errors.
 Log:
 v1.0.0 : Initial implementation
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
# Standard Library
import logging
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Third Party
import pytest

# Add bin to path for importing create_python_project module
bin_path = Path(__file__).parent.parent.parent / "bin"
sys.path.insert(0, str(bin_path))

# Module under test
from create_python_project import CreatePythonPackage, CreatePythonPackageError  # noqa: E402

# =============================================================================
# LOGGING
# =============================================================================
logger = logging.getLogger(__name__)

# =============================================================================
# MODULE-LEVEL MARKS
# =============================================================================
# Suppress DeprecationWarning from basefunctions.setup_logger() called at
# module level in create_python_project.py — legacy code outside our scope
pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def creator():
    """
    Provide a CreatePythonPackage instance with mocked dependencies.

    Returns
    -------
    CreatePythonPackage
        Instance with config loading mocked out.
    """
    with patch("create_python_project.basefunctions.ConfigHandler") as mock_config_class:
        mock_config = MagicMock()
        mock_config_class.return_value = mock_config
        with patch("create_python_project.basefunctions.OutputFormatter"):
            instance = CreatePythonPackage.__new__(CreatePythonPackage)
            instance.logger = logging.getLogger("test")
            instance.formatter = MagicMock()
            instance.config_handler = mock_config
            yield instance


# =============================================================================
# TESTS
# =============================================================================


class TestSetupVirtualEnvironmentEditableInstall:
    """Tests for _setup_virtual_environment editable install error propagation."""

    def test_setup_virtual_environment_editable_install_fails_raises_error(
        self, creator: CreatePythonPackage, tmp_path: Path
    ) -> None:
        """
        Editable install failure must raise CreatePythonPackageError.

        When pip install -e . raises CalledProcessError, the error must
        propagate as CreatePythonPackageError — not be swallowed.
        """
        # Arrange
        mock_pip = Path("/mock/pip")
        with (
            patch("create_python_project.subprocess.run") as mock_run,
            patch("create_python_project.basefunctions.VenvUtils") as mock_venv_utils,
        ):
            mock_venv_utils.upgrade_pip.return_value = None
            mock_venv_utils.get_pip_executable.return_value = mock_pip
            # venv creation succeeds, editable install fails
            mock_run.side_effect = [
                MagicMock(),  # venv creation
                subprocess.CalledProcessError(1, "pip install -e ."),  # editable install fails
            ]

            # Act & Assert
            with pytest.raises(CreatePythonPackageError):
                creator._setup_virtual_environment(tmp_path)

    def test_setup_virtual_environment_dev_extras_fail_no_exception(
        self, creator: CreatePythonPackage, tmp_path: Path
    ) -> None:
        """
        Dev extras failure must NOT raise — only log a warning.

        When pip install -e .[dev,test] fails after a successful editable
        install, the function must return normally without raising.
        """
        # Arrange
        mock_pip = Path("/mock/pip")
        with (
            patch("create_python_project.subprocess.run") as mock_run,
            patch("create_python_project.basefunctions.VenvUtils") as mock_venv_utils,
        ):
            mock_venv_utils.upgrade_pip.return_value = None
            mock_venv_utils.get_pip_executable.return_value = mock_pip
            mock_run.side_effect = [
                MagicMock(),  # venv creation
                MagicMock(),  # editable install succeeds
                subprocess.CalledProcessError(1, "pip install -e .[dev,test]"),  # dev extras fail
            ]

            # Act & Assert — no exception expected
            creator._setup_virtual_environment(tmp_path)

    def test_setup_virtual_environment_both_succeed_no_exception(
        self, creator: CreatePythonPackage, tmp_path: Path
    ) -> None:
        """
        When both installs succeed, function returns None without exception.
        """
        # Arrange
        mock_pip = Path("/mock/pip")
        with (
            patch("create_python_project.subprocess.run") as mock_run,
            patch("create_python_project.basefunctions.VenvUtils") as mock_venv_utils,
        ):
            mock_venv_utils.upgrade_pip.return_value = None
            mock_venv_utils.get_pip_executable.return_value = mock_pip
            mock_run.side_effect = [
                MagicMock(),  # venv creation
                MagicMock(),  # editable install
                MagicMock(),  # dev extras
            ]

            # Act
            result = creator._setup_virtual_environment(tmp_path)

            # Assert
            assert result is None
