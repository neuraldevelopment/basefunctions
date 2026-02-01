"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.

 Description:
 Test suite for ppip table width synchronization (TDD).
 Tests that local and PyPI tables render with identical total width.

 Log:
 v1.0.0 : Initial test implementation (TDD Red phase)
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
# Standard Library
import importlib.util
from pathlib import Path

import pytest

# =============================================================================
# MODULE LOADING
# =============================================================================

# Load ppip.py dynamically from bin directory
_test_file_path = Path(__file__)
_repo_root = _test_file_path.parent.parent.parent  # tests/runtime/ -> tests/ -> basefunctions/
_ppip_path = _repo_root / "bin" / "ppip.py"

if not _ppip_path.exists():
    raise FileNotFoundError(f"ppip.py not found at {_ppip_path}")

_spec = importlib.util.spec_from_file_location("ppip", str(_ppip_path))
_ppip_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_ppip_module)
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
# TEST 1: Local Packages Table Structure
# =============================================================================


def test_local_packages_table_structure(mock_bootstrap_config):
    """
    Test that _format_local_packages_table() returns widths dict when requested.

    RED PHASE: Test must fail initially.
    - Rendere Local Packages mit return_widths=True
    - Assert: Rückgabe ist (str, dict)
    - Assert: dict hat Keys 'column_widths' und 'total_width'
    - Assert: 4 Spalten in der Tabelle
    """
    # ARRANGE
    ppip = PersonalPip()
    packages = [
        ("basefunctions", "0.5.75", "0.5.75", "current"),
        ("chartfunctions", "1.2.5", "1.2.0", "update_available"),
    ]

    # ACT
    result = ppip._format_local_packages_table(packages, return_widths=True)

    # ASSERT
    # Should return tuple (str, dict)
    assert isinstance(result, tuple)
    assert len(result) == 2

    table_str, widths = result
    assert isinstance(table_str, str)
    assert isinstance(widths, dict)

    # dict must have 'column_widths' and 'total_width' keys
    assert "column_widths" in widths
    assert "total_width" in widths
    assert isinstance(widths["column_widths"], list)
    assert isinstance(widths["total_width"], int)

    # Should have 4 columns (Package, Available, Installed, Status)
    assert len(widths["column_widths"]) == 4

    # Headers must be present in table
    assert "Package" in table_str
    assert "Available" in table_str
    assert "Installed" in table_str
    assert "Status" in table_str


# =============================================================================
# TEST 2: PyPI Packages Table with enforce_widths
# =============================================================================


def test_pypi_packages_table_with_enforce_widths(mock_bootstrap_config):
    """
    Test that PyPI table uses enforce_widths for width synchronization.

    RED PHASE: Test must fail initially.
    - Rendere Local Packages (extract widths)
    - Rendere PyPI Packages mit den gleichen Breiten
    - Assert: Beide Tabellen haben die gleiche Breite
    - Assert: PyPI "Available" Spalte ist leer
    """
    # ARRANGE
    ppip = PersonalPip()
    local_packages = [
        ("basefunctions", "0.5.75", "0.5.75", "current"),
        ("chartfunctions", "1.2.5", "1.2.0", "update_available"),
    ]
    pypi_packages = [
        ("numpy", None, "1.24.0", "pypi"),
        ("requests", None, "2.31.0", "pypi"),
    ]

    # ACT
    # Render local table and extract widths
    local_output, widths = ppip._format_local_packages_table(local_packages, return_widths=True)

    # Render PyPI table with enforce_widths
    pypi_output = ppip._format_pypi_packages_table(pypi_packages, enforce_widths=widths)

    # ASSERT
    # Both tables should be strings
    assert isinstance(local_output, str)
    assert isinstance(pypi_output, str)

    # Calculate total width of both tables (first line)
    local_lines = local_output.split("\n")
    pypi_lines = pypi_output.split("\n")

    # First line should have identical width
    assert len(local_lines) > 0
    assert len(pypi_lines) > 0
    local_width = len(local_lines[0])
    pypi_width = len(pypi_lines[0])

    # CRITICAL: Both tables must have identical total width
    assert local_width == pypi_width, f"Width mismatch: Local={local_width}, PyPI={pypi_width}"

    # PyPI table should have "Available" column (empty)
    assert "Available" in pypi_output

    # PyPI table should contain package names and versions
    assert "numpy" in pypi_output
    assert "1.24.0" in pypi_output


# =============================================================================
# TEST 3: Full integration - Equal width sync
# =============================================================================


def test_format_packages_as_tables_equal_width_sync(mock_bootstrap_config):
    """
    Test that _format_packages_as_tables() renders both tables with identical width.

    RED PHASE: Test must fail initially.
    - Beiden Tabellen rendern mit width synchronization
    - Assert: output enthält beide Tabellen
    - Assert: Visuelle Breite identisch (count characters pro Zeile)
    """
    # ARRANGE
    ppip = PersonalPip()
    packages = [
        ("basefunctions", "0.5.75", "0.5.75", "current"),
        ("chartfunctions", "1.2.5", "1.2.0", "update_available"),
        ("numpy", None, "1.24.0", "pypi"),
        ("requests", None, "2.31.0", "pypi"),
    ]

    # ACT
    output = ppip._format_packages_as_tables(packages)

    # ASSERT
    assert isinstance(output, str)

    # Output must contain all packages
    assert "basefunctions" in output
    assert "chartfunctions" in output
    assert "numpy" in output
    assert "requests" in output

    # Split into lines and find table top borders
    lines = output.split("\n")

    # Find all lines starting with table top border (┌ or ╒)
    table_starts = [i for i, line in enumerate(lines) if line.startswith("┌") or line.startswith("╒")]

    # Must have exactly 2 tables
    assert len(table_starts) == 2, f"Expected 2 tables, found {len(table_starts)}"

    # Extract first line from each table
    local_top_border = lines[table_starts[0]]
    pypi_top_border = lines[table_starts[1]]

    # CRITICAL: Both borders must have identical width
    assert len(local_top_border) == len(
        pypi_top_border
    ), f"Width mismatch: Local={len(local_top_border)}, PyPI={len(pypi_top_border)}"


# =============================================================================
# TEST 4: Empty cases
# =============================================================================


def test_empty_cases_only_local(mock_bootstrap_config):
    """Test rendering with only local packages."""
    # ARRANGE
    ppip = PersonalPip()
    packages = [
        ("basefunctions", "0.5.75", "0.5.75", "current"),
    ]

    # ACT
    output = ppip._format_packages_as_tables(packages)

    # ASSERT
    assert isinstance(output, str)
    assert "basefunctions" in output


def test_empty_cases_only_pypi(mock_bootstrap_config):
    """Test rendering with only PyPI packages."""
    # ARRANGE
    ppip = PersonalPip()
    packages = [
        ("requests", None, "2.31.0", "pypi"),
    ]

    # ACT
    output = ppip._format_packages_as_tables(packages)

    # ASSERT
    assert isinstance(output, str)
    assert "requests" in output


def test_empty_cases_no_packages(mock_bootstrap_config):
    """Test rendering with no packages."""
    # ARRANGE
    ppip = PersonalPip()
    packages = []

    # ACT
    output = ppip._format_packages_as_tables(packages)

    # ASSERT
    assert isinstance(output, str)
    # Should be empty or minimal output
    assert len(output) == 0
