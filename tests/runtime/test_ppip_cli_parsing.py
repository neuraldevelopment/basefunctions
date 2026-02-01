"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.

 Description:
 Test CLI argument parsing for ppip --all flag.

 Log:
 v1.0.0 : Initial test implementation (TDD)
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
# Standard Library
import importlib.util
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

# =============================================================================
# MODULE LOADING
# =============================================================================

# Load ppip.py dynamically from bin directory
_test_file_path = Path(__file__)
_repo_root = _test_file_path.parent.parent.parent
_ppip_path = _repo_root / "bin" / "ppip.py"

if not _ppip_path.exists():
    raise FileNotFoundError(f"ppip.py not found at {_ppip_path}")

_spec = importlib.util.spec_from_file_location("ppip", str(_ppip_path))
assert _spec is not None, f"Failed to create spec for {_ppip_path}"
_ppip_module = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None, f"Failed to get loader for {_ppip_path}"
_spec.loader.exec_module(_ppip_module)
main_func = _ppip_module.main
PersonalPip = _ppip_module.PersonalPip

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def mock_bootstrap_config(tmp_path, monkeypatch):
    """
    Create mock bootstrap config for tests.

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
    """
    import json

    # Create config directory and file
    config_dir = tmp_path / ".config" / "basefunctions"
    config_dir.mkdir(parents=True)
    config_file = config_dir / "bootstrap.json"

    # Create deployment directory
    deploy_dir = tmp_path / "deployment"
    deploy_dir.mkdir(parents=True, exist_ok=True)
    (deploy_dir / "packages").mkdir(parents=True)

    # Write bootstrap config
    config_data = {"bootstrap": {"paths": {"deployment_directory": str(deploy_dir)}}}
    config_file.write_text(json.dumps(config_data), encoding="utf-8")

    # Mock the bootstrap config path
    monkeypatch.setattr(_ppip_module, "BOOTSTRAP_CONFIG_PATH", config_file)

    return deploy_dir


# =============================================================================
# TESTS FOR main() CLI Parsing
# =============================================================================


def test_main_list_without_all_flag_calls_list_packages_default(mock_bootstrap_config, monkeypatch):
    """Test 'ppip list' calls list_packages() with show_all=False."""
    # ARRANGE
    monkeypatch.setattr(sys, "argv", ["ppip", "list"])

    mock_list_packages = Mock()
    monkeypatch.setattr(PersonalPip, "list_packages", mock_list_packages)

    # ACT
    main_func()

    # ASSERT
    # Should call list_packages() with default show_all=False
    mock_list_packages.assert_called_once()
    call_args = mock_list_packages.call_args
    # Check if show_all parameter was NOT provided or is False
    if call_args.kwargs:
        assert call_args.kwargs.get("show_all", False) is False
    else:
        # Called without any kwargs (default behavior)
        assert len(call_args.args) == 0 or call_args.args[0] is False


def test_main_list_with_all_flag_calls_list_packages_show_all(mock_bootstrap_config, monkeypatch):
    """Test 'ppip list --all' calls list_packages(show_all=True)."""
    # ARRANGE
    monkeypatch.setattr(sys, "argv", ["ppip", "list", "--all"])

    mock_list_packages = Mock()
    monkeypatch.setattr(PersonalPip, "list_packages", mock_list_packages)

    # ACT
    main_func()

    # ASSERT
    # Should call list_packages(show_all=True)
    mock_list_packages.assert_called_once_with(show_all=True)
