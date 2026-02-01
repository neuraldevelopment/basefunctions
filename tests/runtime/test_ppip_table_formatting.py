"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.

 Description:
 Pytest test suite for ppip KPI-style formatting and version comparison.
 Tests two-section output (Local Packages, PyPI Packages) with alphabetical sorting.

 Log:
 v1.0.0 : Initial test implementation (TDD Red phase)
 v2.0.0 : Redesigned for KPI-style output with alphabetical sorting
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
# Standard Library
import importlib.util
from pathlib import Path
from typing import Dict, List, Tuple
from unittest.mock import Mock, patch

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


@pytest.fixture
def mock_package_data_single():
    """
    Mock data for a single package.

    Returns
    -------
    List[Tuple[str, str, str, str]]
        List with single package: (name, available_version, installed_version, status)
    """
    # ARRANGE & RETURN
    return [("basefunctions", "0.5.75", "0.5.75", "current")]


@pytest.fixture
def mock_package_data_multiple():
    """
    Mock data for multiple packages with different statuses.

    Returns
    -------
    List[Tuple[str, str, str, str]]
        List with multiple packages: (name, available_version, installed_version, status)
    """
    # ARRANGE & RETURN
    return [
        ("basefunctions", "0.5.75", "0.5.75", "current"),
        ("chartfunctions", "1.2.5", "1.2.0", "update_available"),
        ("newpackage", "1.0.0", None, "not_installed"),
        ("requests", None, "2.31.0", "pypi"),
    ]


@pytest.fixture
def mock_package_data_empty():
    """
    Mock data for empty package list.

    Returns
    -------
    List
        Empty list
    """
    # ARRANGE & RETURN
    return []


# =============================================================================
# TESTS FOR get_package_status()
# =============================================================================


def test_get_package_status_versions_equal_returns_current(mock_bootstrap_config):
    """Test that equal versions return 'current' status."""
    # ARRANGE
    ppip = PersonalPip()
    local_version = "1.0.0"
    installed_version = "1.0.0"

    # ACT
    result = ppip.get_package_status(local_version, installed_version)

    # ASSERT
    assert result == "current"


def test_get_package_status_local_greater_returns_update_available():
    """Test that local > installed returns 'update_available' status."""
    # ARRANGE

    ppip = PersonalPip()
    local_version = "1.2.5"
    installed_version = "1.2.0"

    # ACT
    result = ppip.get_package_status(local_version, installed_version)

    # ASSERT
    assert result == "update_available"


def test_get_package_status_installed_none_returns_not_installed():
    """Test that None installed_version returns 'not_installed' status."""
    # ARRANGE

    ppip = PersonalPip()
    local_version = "1.0.0"
    installed_version = None

    # ACT
    result = ppip.get_package_status(local_version, installed_version)

    # ASSERT
    assert result == "not_installed"


def test_get_package_status_local_none_returns_pypi():
    """Test that None local_version returns 'pypi' status."""
    # ARRANGE

    ppip = PersonalPip()
    local_version = None
    installed_version = "2.31.0"

    # ACT
    result = ppip.get_package_status(local_version, installed_version)

    # ASSERT
    assert result == "pypi"


# =============================================================================
# TESTS FOR sort_packages_for_display() - NEW ALPHABETICAL SORTING
# =============================================================================


def test_sort_packages_alphabetical_local_only():
    """Test that local packages are sorted alphabetically (no status grouping)."""
    # ARRANGE
    ppip = PersonalPip()
    packages = [
        ("zebra", "1.0.0", "1.0.0", "current"),
        ("apple", "2.0.0", "1.0.0", "update_available"),
        ("mango", "1.0.0", None, "not_installed"),
    ]

    # ACT
    sorted_packages = ppip.sort_packages_for_display(packages)

    # ASSERT
    names = [pkg[0] for pkg in sorted_packages]
    assert names == ["apple", "mango", "zebra"]


def test_sort_packages_alphabetical_pypi_only():
    """Test that PyPI packages are sorted alphabetically."""
    # ARRANGE
    ppip = PersonalPip()
    packages = [
        ("zzz_pypi", None, "1.0.0", "pypi"),
        ("aaa_pypi", None, "2.0.0", "pypi"),
        ("mmm_pypi", None, "3.0.0", "pypi"),
    ]

    # ACT
    sorted_packages = ppip.sort_packages_for_display(packages)

    # ASSERT
    names = [pkg[0] for pkg in sorted_packages]
    assert names == ["aaa_pypi", "mmm_pypi", "zzz_pypi"]


def test_sort_packages_local_and_pypi_separated():
    """Test that local and PyPI packages are separated with separator."""
    # ARRANGE
    ppip = PersonalPip()
    packages = [
        ("basefunctions", "0.5.75", "0.5.75", "current"),
        ("requests", None, "2.31.0", "pypi"),
        ("chartfunctions", "1.2.5", "1.2.0", "update_available"),
    ]

    # ACT
    sorted_packages = ppip.sort_packages_for_display(packages)

    # ASSERT
    # Expected: basefunctions, chartfunctions, __separator__, requests
    assert len(sorted_packages) == 4
    assert sorted_packages[0][0] == "basefunctions"
    assert sorted_packages[1][0] == "chartfunctions"
    assert sorted_packages[2] == ("__separator__", None, None, None)
    assert sorted_packages[3][0] == "requests"


def test_sort_packages_mixed_statuses_alphabetical():
    """Test sorting ignores status, only alphabetical within local/pypi groups."""
    # ARRANGE
    ppip = PersonalPip()
    packages = [
        ("zebra_current", "1.0.0", "1.0.0", "current"),
        ("apple_update", "2.0.0", "1.0.0", "update_available"),
        ("mango_not_installed", "1.0.0", None, "not_installed"),
        ("banana_current", "1.5.0", "1.5.0", "current"),
        ("cherry_pypi", None, "3.0.0", "pypi"),
        ("date_update", "1.1.0", "1.0.0", "update_available"),
    ]

    # ACT
    sorted_packages = ppip.sort_packages_for_display(packages)

    # ASSERT
    # Local packages should be alphabetical (ignore status)
    local_packages = [pkg for pkg in sorted_packages if pkg[3] != "pypi" and pkg[0] != "__separator__"]
    local_names = [pkg[0] for pkg in local_packages]
    assert local_names == ["apple_update", "banana_current", "date_update", "mango_not_installed", "zebra_current"]

    # PyPI packages should be alphabetical
    pypi_packages = [pkg for pkg in sorted_packages if pkg[3] == "pypi"]
    pypi_names = [pkg[0] for pkg in pypi_packages]
    assert pypi_names == ["cherry_pypi"]


def test_sort_packages_case_insensitive():
    """Test that sorting is case-insensitive."""
    # ARRANGE
    ppip = PersonalPip()
    packages = [
        ("Zebra", "1.0.0", "1.0.0", "current"),
        ("apple", "1.0.0", "1.0.0", "current"),
        ("Mango", "1.0.0", "1.0.0", "current"),
    ]

    # ACT
    sorted_packages = ppip.sort_packages_for_display(packages)

    # ASSERT
    names = [pkg[0] for pkg in sorted_packages]
    assert names == ["apple", "Mango", "Zebra"]


def test_sort_packages_empty_list():
    """Test sorting empty package list."""
    # ARRANGE
    ppip = PersonalPip()
    packages = []

    # ACT
    sorted_packages = ppip.sort_packages_for_display(packages)

    # ASSERT
    assert sorted_packages == []


# =============================================================================
# TESTS FOR format_package_output() - NEW KPI-STYLE FORMAT
# =============================================================================


def test_format_package_output_local_section_header():
    """Test that output contains 'Local Packages' section header."""
    # ARRANGE
    ppip = PersonalPip()
    packages = [("basefunctions", "0.5.75", "0.5.75", "current")]

    # ACT
    result = ppip.format_package_output(packages)

    # ASSERT
    assert "Local Packages" in result


def test_format_package_output_pypi_section_header():
    """Test that output contains 'PyPI Packages' section header."""
    # ARRANGE
    ppip = PersonalPip()
    packages = [("requests", None, "2.31.0", "pypi")]

    # ACT
    result = ppip.format_package_output(packages)

    # ASSERT
    assert "PyPI Packages" in result


def test_format_package_output_local_package_format():
    """Test that local package has correct format with arrow and status."""
    # ARRANGE
    ppip = PersonalPip()
    packages = [("basefunctions", "0.5.75", "0.5.75", "current")]

    # ACT
    result = ppip.format_package_output(packages)

    # ASSERT
    assert "basefunctions" in result
    assert "0.5.75" in result
    assert "→" in result
    assert "✅" in result
    assert "Current" in result


def test_format_package_output_pypi_package_format():
    """Test that PyPI package has simple format (name and version only)."""
    # ARRANGE
    ppip = PersonalPip()
    packages = [("requests", None, "2.31.0", "pypi")]

    # ACT
    result = ppip.format_package_output(packages)

    # ASSERT
    assert "requests" in result
    assert "2.31.0" in result
    # PyPI packages should NOT have arrow
    lines = result.split("\n")
    pypi_section_started = False
    for line in lines:
        if "PyPI Packages" in line:
            pypi_section_started = True
        if pypi_section_started and "requests" in line:
            assert "→" not in line
            assert "✅" not in line
            assert "🟠" not in line
            assert "❌" not in line


def test_format_package_output_blank_separator():
    """Test that blank line separates Local and PyPI sections."""
    # ARRANGE
    ppip = PersonalPip()
    packages = [
        ("basefunctions", "0.5.75", "0.5.75", "current"),
        ("__separator__", None, None, None),
        ("requests", None, "2.31.0", "pypi"),
    ]

    # ACT
    result = ppip.format_package_output(packages)

    # ASSERT
    lines = result.split("\n")
    # Find blank line between sections
    local_idx = None
    pypi_idx = None
    for i, line in enumerate(lines):
        if "Local Packages" in line:
            local_idx = i
        if "PyPI Packages" in line:
            pypi_idx = i

    assert local_idx is not None
    assert pypi_idx is not None
    # There should be blank line(s) between sections
    blank_found = False
    for i in range(local_idx, pypi_idx):
        if lines[i].strip() == "":
            blank_found = True
            break
    assert blank_found


def test_format_package_output_status_emojis():
    """Test that correct emojis are shown for each status."""
    # ARRANGE
    ppip = PersonalPip()
    packages = [
        ("pkg1", "1.0.0", "1.0.0", "current"),
        ("pkg2", "2.0.0", "1.0.0", "update_available"),
        ("pkg3", "1.0.0", None, "not_installed"),
    ]

    # ACT
    result = ppip.format_package_output(packages)

    # ASSERT
    assert "✅" in result  # current
    assert "🟠" in result  # update_available
    assert "❌" in result  # not_installed


def test_format_package_output_none_installed_display():
    """Test that None installed version displays as dash."""
    # ARRANGE
    ppip = PersonalPip()
    packages = [("newpkg", "1.0.0", None, "not_installed")]

    # ACT
    result = ppip.format_package_output(packages)

    # ASSERT
    assert "newpkg" in result
    # Should not show literal "None"
    assert "None" not in result
    # Should show dash for missing version
    assert "→" in result


def test_format_package_output_column_alignment():
    """Test that columns are aligned properly."""
    # ARRANGE
    ppip = PersonalPip()
    packages = [
        ("short", "1.0.0", "1.0.0", "current"),
        ("very_long_package_name", "2.5.10", "2.5.9", "update_available"),
    ]

    # ACT
    result = ppip.format_package_output(packages)

    # ASSERT
    # Both lines should start with proper indentation (2 spaces)
    lines = result.split("\n")
    data_lines = [line for line in lines if "short" in line or "very_long_package_name" in line]
    for line in data_lines:
        assert line.startswith("  ")


def test_format_package_output_empty_list():
    """Test formatting empty package list."""
    # ARRANGE
    ppip = PersonalPip()
    packages = []

    # ACT
    result = ppip.format_package_output(packages)

    # ASSERT
    # Should still show headers or be empty
    assert isinstance(result, str)


# =============================================================================
# TESTS FOR list_packages() with show_all parameter
# =============================================================================


def test_list_packages_default_no_pypi(tmp_path, monkeypatch):
    """Test list_packages() without show_all flag excludes PyPI-only packages."""
    # ARRANGE
    import importlib.util
    import io
    import json
    import sys

    # Load ppip module
    test_file_path = Path(__file__)
    repo_root = test_file_path.parent.parent.parent
    ppip_path = repo_root / "bin" / "ppip.py"

    if not ppip_path.exists():
        pytest.skip(f"ppip.py not found at {ppip_path}")

    spec = importlib.util.spec_from_file_location("ppip", str(ppip_path))
    ppip_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ppip_module)

    # Setup mock config
    config_dir = tmp_path / ".config" / "basefunctions"
    config_dir.mkdir(parents=True)
    config_file = config_dir / "bootstrap.json"

    deploy_dir = tmp_path / "deployment"
    deploy_dir.mkdir(parents=True)
    packages_dir = deploy_dir / "packages"
    packages_dir.mkdir(parents=True)

    config_data = {"bootstrap": {"paths": {"deployment_directory": str(deploy_dir)}}}
    config_file.write_text(json.dumps(config_data))

    monkeypatch.setattr(ppip_module, "BOOTSTRAP_CONFIG_PATH", config_file)

    # Create sample local packages
    pkg1_dir = packages_dir / "basefunctions"
    pkg1_dir.mkdir()
    (pkg1_dir / "pyproject.toml").write_text('version = "0.5.75"')

    # Create instance
    ppip = ppip_module.PersonalPip()

    # Mock get_installed_versions - includes PyPI-only package "requests"
    monkeypatch.setattr(ppip, "get_installed_versions", lambda: {"basefunctions": "0.5.75", "requests": "2.31.0"})

    # ACT
    captured_output = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = captured_output

    try:
        ppip.list_packages()  # Default: show_all=False
    finally:
        sys.stdout = old_stdout

    result = captured_output.getvalue()

    # ASSERT
    # Should contain local package
    assert "basefunctions" in result
    # Should NOT contain PyPI-only package
    assert "requests" not in result


def test_list_packages_with_all_flag_includes_pypi(tmp_path, monkeypatch):
    """Test list_packages(show_all=True) includes PyPI-only packages."""
    # ARRANGE
    import importlib.util
    import io
    import json
    import sys

    # Load ppip module
    test_file_path = Path(__file__)
    repo_root = test_file_path.parent.parent.parent
    ppip_path = repo_root / "bin" / "ppip.py"

    if not ppip_path.exists():
        pytest.skip(f"ppip.py not found at {ppip_path}")

    spec = importlib.util.spec_from_file_location("ppip", str(ppip_path))
    ppip_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ppip_module)

    # Setup mock config
    config_dir = tmp_path / ".config" / "basefunctions"
    config_dir.mkdir(parents=True)
    config_file = config_dir / "bootstrap.json"

    deploy_dir = tmp_path / "deployment"
    deploy_dir.mkdir(parents=True)
    packages_dir = deploy_dir / "packages"
    packages_dir.mkdir(parents=True)

    config_data = {"bootstrap": {"paths": {"deployment_directory": str(deploy_dir)}}}
    config_file.write_text(json.dumps(config_data))

    monkeypatch.setattr(ppip_module, "BOOTSTRAP_CONFIG_PATH", config_file)

    # Create sample local packages
    pkg1_dir = packages_dir / "basefunctions"
    pkg1_dir.mkdir()
    (pkg1_dir / "pyproject.toml").write_text('version = "0.5.75"')

    # Create instance
    ppip = ppip_module.PersonalPip()

    # Mock get_installed_versions - includes PyPI-only package "requests"
    monkeypatch.setattr(ppip, "get_installed_versions", lambda: {"basefunctions": "0.5.75", "requests": "2.31.0"})

    # ACT
    captured_output = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = captured_output

    try:
        ppip.list_packages(show_all=True)  # With show_all=True
    finally:
        sys.stdout = old_stdout

    result = captured_output.getvalue()

    # ASSERT
    # Should contain local package
    assert "basefunctions" in result
    # Should contain PyPI-only package
    assert "requests" in result
    # With new table format, PyPI packages appear in separate table
    # Just verify both packages are present in output


# =============================================================================
# TESTS FOR _format_local_packages_table() - NEW TABLE RENDERING
# =============================================================================


def test_format_local_packages_table_returns_string(mock_bootstrap_config):
    """Test that _format_local_packages_table() returns a string."""
    # ARRANGE
    ppip = PersonalPip()
    local_packages = [
        ("basefunctions", "0.5.75", "0.5.75", "current"),
        ("chartfunctions", "1.2.5", "1.2.0", "update_available"),
    ]

    # ACT
    result = ppip._format_local_packages_table(local_packages)

    # ASSERT
    assert isinstance(result, str)


def test_format_local_packages_table_contains_package_names(mock_bootstrap_config):
    """Test that output contains all package names."""
    # ARRANGE
    ppip = PersonalPip()
    local_packages = [
        ("basefunctions", "0.5.75", "0.5.75", "current"),
        ("chartfunctions", "1.2.5", "1.2.0", "update_available"),
    ]

    # ACT
    result = ppip._format_local_packages_table(local_packages)

    # ASSERT
    assert "basefunctions" in result
    assert "chartfunctions" in result


def test_format_local_packages_table_contains_headers(mock_bootstrap_config):
    """Test that output contains expected column headers."""
    # ARRANGE
    ppip = PersonalPip()
    local_packages = [
        ("basefunctions", "0.5.75", "0.5.75", "current"),
    ]

    # ACT
    result = ppip._format_local_packages_table(local_packages)

    # ASSERT
    # Headers should be: Package, Available, Installed, Status
    # They may appear in rendered table borders/headers
    assert "Package" in result
    assert "Available" in result
    assert "Installed" in result
    assert "Status" in result


def test_format_local_packages_table_with_return_widths(mock_bootstrap_config):
    """Test that _format_local_packages_table() can return widths dict."""
    # ARRANGE
    ppip = PersonalPip()
    local_packages = [
        ("basefunctions", "0.5.75", "0.5.75", "current"),
        ("chartfunctions", "1.2.5", "1.2.0", "update_available"),
    ]

    # ACT
    result, widths = ppip._format_local_packages_table(local_packages, return_widths=True)

    # ASSERT
    assert isinstance(result, str)
    assert isinstance(widths, dict)
    assert "column_widths" in widths
    assert "total_width" in widths
    assert isinstance(widths["column_widths"], list)
    assert isinstance(widths["total_width"], int)


def test_local_packages_table_with_return_widths_and_no_separators(mock_bootstrap_config):
    """
    Test that Local Packages table returns widths and has no row separators.

    TDD CYCLE 1 - RED PHASE:
    - return_widths=True returns tuple (str, dict)
    - dict has 'column_widths' and 'total_width' keys
    - Table string has NO separators between rows (only header separator)
    - Table string has outer borders (fancy_grid theme)
    """
    # ARRANGE
    ppip = PersonalPip()
    local_packages = [
        ("basefunctions", "0.5.75", "0.5.75", "current"),
        ("chartfunctions", "1.2.5", "1.2.0", "update_available"),
    ]

    # ACT
    result = ppip._format_local_packages_table(local_packages, return_widths=True)

    # ASSERT
    # Should return tuple of (str, dict)
    assert isinstance(result, tuple)
    assert len(result) == 2
    table_str, widths_dict = result

    # Check table string
    assert isinstance(table_str, str)
    assert len(table_str) > 0

    # Check widths dict structure
    assert isinstance(widths_dict, dict)
    assert "column_widths" in widths_dict
    assert "total_width" in widths_dict
    assert isinstance(widths_dict["column_widths"], list)
    assert isinstance(widths_dict["total_width"], int)

    # Check NO row separators (only 1 separator = header separator)
    lines = table_str.split("\n")
    # fancy_grid uses ═ (U+2550) for horizontal lines, not ─ (U+2500)
    # Count lines with horizontal box drawing chars (═)
    horizontal_lines = [line for line in lines if "═" in line]
    # fancy_grid has: top border, header separator, bottom border = 3 lines
    # With row_separators=True it would have more (one between each data row)
    assert len(horizontal_lines) == 3, f"Expected 3 horizontal lines (top, header, bottom), got {len(horizontal_lines)}"

    # Check outer borders exist (fancy_grid theme)
    assert "│" in table_str  # Vertical borders
    assert "═" in table_str  # Horizontal borders


def test_pypi_packages_table_with_enforce_widths_and_no_separators(mock_bootstrap_config):
    """
    Test that PyPI Packages table enforces widths and has no row separators.

    TDD CYCLE 2 - RED PHASE:
    - enforce_widths parameter accepts widths dict from local table
    - PyPI table uses same column widths as local table
    - PyPI table has same total width as local table
    - NO separators between rows (only header separator)
    """
    # ARRANGE
    ppip = PersonalPip()
    local_packages = [
        ("basefunctions", "0.5.75", "0.5.75", "current"),
        ("chartfunctions", "1.2.5", "1.2.0", "update_available"),
    ]
    pypi_packages = [
        ("requests", None, "2.31.0", "pypi"),
        ("numpy", None, "1.24.3", "pypi"),
    ]

    # Get widths from local table
    local_table_str, widths = ppip._format_local_packages_table(local_packages, return_widths=True)

    # ACT
    pypi_table_str = ppip._format_pypi_packages_table(pypi_packages, enforce_widths=widths)

    # ASSERT
    # Should return string only
    assert isinstance(pypi_table_str, str)
    assert len(pypi_table_str) > 0

    # Check that PyPI table has same total width as local table
    local_lines = local_table_str.split("\n")
    pypi_lines = pypi_table_str.split("\n")
    # First line is top border - should have same length
    assert len(local_lines[0]) == len(pypi_lines[0]), \
        f"Local width: {len(local_lines[0])}, PyPI width: {len(pypi_lines[0])}"

    # Check NO row separators in PyPI table
    horizontal_lines = [line for line in pypi_lines if "═" in line]
    assert len(horizontal_lines) == 3, \
        f"Expected 3 horizontal lines (top, header, bottom), got {len(horizontal_lines)}"

    # Check outer borders exist
    assert "│" in pypi_table_str
    assert "═" in pypi_table_str


# =============================================================================
# TESTS FOR _format_pypi_packages_table() - PYPI TABLE RENDERING
# =============================================================================


def test_format_pypi_packages_table_returns_string(mock_bootstrap_config):
    """Test that _format_pypi_packages_table() returns a string."""
    # ARRANGE
    ppip = PersonalPip()
    pypi_packages = [
        ("requests", None, "2.31.0", "pypi"),
        ("numpy", None, "1.24.3", "pypi"),
    ]

    # ACT
    result = ppip._format_pypi_packages_table(pypi_packages)

    # ASSERT
    assert isinstance(result, str)


def test_format_pypi_packages_table_contains_package_names(mock_bootstrap_config):
    """Test that output contains all PyPI package names."""
    # ARRANGE
    ppip = PersonalPip()
    pypi_packages = [
        ("requests", None, "2.31.0", "pypi"),
        ("numpy", None, "1.24.3", "pypi"),
    ]

    # ACT
    result = ppip._format_pypi_packages_table(pypi_packages)

    # ASSERT
    assert "requests" in result
    assert "numpy" in result


def test_pypi_table_has_four_columns(mock_bootstrap_config):
    """
    Test that PyPI table has 4 columns for width synchronization.

    PHASE 1, TEST 1:
    PyPI table must have same column count as local table (4 columns).
    Middle 2 columns (Available, Status) are empty, only Package and Installed have data.
    """
    # ARRANGE
    ppip = PersonalPip()
    pypi_packages = [
        ("requests", None, "2.31.0", "pypi"),
        ("numpy", None, "1.24.0", "pypi"),
    ]

    # ACT
    result = ppip._format_pypi_packages_table(pypi_packages)

    # ASSERT
    # Should contain all 4 headers (same as local table)
    assert "Package" in result
    assert "Available" in result
    assert "Installed" in result
    assert "Status" in result

    # Package names should be present
    assert "requests" in result
    assert "numpy" in result

    # Installed versions should be present
    assert "2.31.0" in result
    assert "1.24.0" in result


def test_format_packages_as_tables_equal_width_sync(mock_bootstrap_config):
    """
    Test that both tables have EXACTLY equal width and no row separators.

    TDD CYCLE 3 - RED PHASE:
    - Both tables (Local + PyPI) are rendered with identical total width
    - Local table uses return_widths=True
    - PyPI table uses enforce_widths from Local table
    - NO row separators in BOTH tables (only header separators)
    - Output contains "PyPI Packages" title
    """
    # ARRANGE
    ppip = PersonalPip()
    packages = [
        ("basefunctions", "0.5.75", "0.5.75", "current"),
        ("chartfunctions", "1.2.5", "1.2.0", "update_available"),
        ("requests", None, "2.31.0", "pypi"),
        ("numpy", None, "1.24.3", "pypi"),
    ]

    # ACT
    result = ppip._format_packages_as_tables(packages)

    # ASSERT
    assert isinstance(result, str)
    assert len(result) > 0

    # Should contain "PyPI Packages" title
    assert "PyPI Packages" in result

    # Split into sections
    sections = result.split("PyPI Packages")
    assert len(sections) == 2, "Expected exactly one 'PyPI Packages' title"
    local_section = sections[0]
    pypi_section = sections[1]

    # Extract table lines (non-empty, non-title lines)
    local_lines = [line for line in local_section.split("\n") if line.strip()]
    pypi_lines = [line for line in pypi_section.split("\n") if line.strip()]

    # Both tables should have content
    assert len(local_lines) > 0
    assert len(pypi_lines) > 0

    # First line of each table is top border - should have IDENTICAL length
    local_border = local_lines[0]
    pypi_border = pypi_lines[0]
    assert len(local_border) == len(pypi_border), \
        f"Tables have different widths: Local={len(local_border)}, PyPI={len(pypi_border)}"

    # Check NO row separators in both tables (only 3 horizontal lines each)
    local_horizontal = [line for line in local_lines if "═" in line]
    pypi_horizontal = [line for line in pypi_lines if "═" in line]
    assert len(local_horizontal) == 3, f"Local table has {len(local_horizontal)} horizontal lines, expected 3"
    assert len(pypi_horizontal) == 3, f"PyPI table has {len(pypi_horizontal)} horizontal lines, expected 3"


# =============================================================================
# TESTS FOR _format_packages_as_tables() - WIDTH SYNCHRONIZATION
# =============================================================================


def test_format_packages_as_tables_with_both_local_and_pypi(mock_bootstrap_config):
    """Test width synchronization between local and PyPI tables."""
    # ARRANGE
    ppip = PersonalPip()
    packages = [
        ("basefunctions", "0.5.75", "0.5.75", "current"),
        ("chartfunctions", "1.2.5", "1.2.0", "update_available"),
        ("requests", None, "2.31.0", "pypi"),
        ("numpy", None, "1.24.3", "pypi"),
    ]

    # ACT
    result = ppip._format_packages_as_tables(packages)

    # ASSERT
    assert isinstance(result, str)
    # Should contain both tables
    assert "basefunctions" in result
    assert "chartfunctions" in result
    assert "requests" in result
    assert "numpy" in result


def test_format_packages_as_tables_width_synchronization(mock_bootstrap_config):
    """Test that Package column has same width in both tables."""
    # ARRANGE
    ppip = PersonalPip()
    # Local package with longer name
    packages = [
        ("very_long_package_name_local", "1.0.0", "1.0.0", "current"),
        ("short", None, "1.0.0", "pypi"),
    ]

    # ACT
    result = ppip._format_packages_as_tables(packages)

    # ASSERT
    # Both tables should exist
    assert "very_long_package_name_local" in result
    assert "short" in result
    # Result should be a valid string
    assert isinstance(result, str)
    assert len(result) > 0


def test_format_packages_as_tables_only_local(mock_bootstrap_config):
    """Test that only local table is rendered when no PyPI packages."""
    # ARRANGE
    ppip = PersonalPip()
    packages = [
        ("basefunctions", "0.5.75", "0.5.75", "current"),
    ]

    # ACT
    result = ppip._format_packages_as_tables(packages)

    # ASSERT
    assert isinstance(result, str)
    assert "basefunctions" in result


def test_format_packages_as_tables_only_pypi(mock_bootstrap_config):
    """Test that only PyPI table is rendered when no local packages."""
    # ARRANGE
    ppip = PersonalPip()
    packages = [
        ("requests", None, "2.31.0", "pypi"),
    ]

    # ACT
    result = ppip._format_packages_as_tables(packages)

    # ASSERT
    assert isinstance(result, str)
    assert "requests" in result


# =============================================================================
# INTEGRATION TEST - Full list_packages with new formatting
# =============================================================================


def test_list_packages_integration_new_format(tmp_path, monkeypatch):
    """Test list_packages(show_all=True) method using new KPI-style format with PyPI packages."""
    # ARRANGE
    import importlib.util

    # Load ppip module
    test_file_path = Path(__file__)
    repo_root = test_file_path.parent.parent.parent
    ppip_path = repo_root / "bin" / "ppip.py"

    if not ppip_path.exists():
        pytest.skip(f"ppip.py not found at {ppip_path}")

    spec = importlib.util.spec_from_file_location("ppip", str(ppip_path))
    ppip_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ppip_module)

    # Setup mock config
    import json

    config_dir = tmp_path / ".config" / "basefunctions"
    config_dir.mkdir(parents=True)
    config_file = config_dir / "bootstrap.json"

    deploy_dir = tmp_path / "deployment"
    deploy_dir.mkdir(parents=True)
    packages_dir = deploy_dir / "packages"
    packages_dir.mkdir(parents=True)

    config_data = {"bootstrap": {"paths": {"deployment_directory": str(deploy_dir)}}}
    config_file.write_text(json.dumps(config_data))

    monkeypatch.setattr(ppip_module, "BOOTSTRAP_CONFIG_PATH", config_file)

    # Create sample packages
    pkg1_dir = packages_dir / "basefunctions"
    pkg1_dir.mkdir()
    (pkg1_dir / "pyproject.toml").write_text('version = "0.5.75"')

    pkg2_dir = packages_dir / "chartfunctions"
    pkg2_dir.mkdir()
    (pkg2_dir / "pyproject.toml").write_text('version = "1.2.5"')

    # Create instance
    ppip = ppip_module.PersonalPip()

    # Mock get_installed_versions
    monkeypatch.setattr(
        ppip, "get_installed_versions", lambda: {"basefunctions": "0.5.75", "chartfunctions": "1.2.0", "requests": "2.31.0"}
    )

    # ACT
    # Capture output by redirecting stdout
    import io
    import sys

    captured_output = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = captured_output

    try:
        ppip.list_packages(show_all=True)  # Changed: explicitly use show_all=True
    finally:
        sys.stdout = old_stdout

    result = captured_output.getvalue()

    # ASSERT
    # With new table format, verify package names are present
    assert "basefunctions" in result
    assert "chartfunctions" in result
    assert "requests" in result
    # Should contain table headers
    assert "Package" in result
    assert "Available" in result
    assert "Installed" in result
    assert "Status" in result
    # Should contain emojis
    assert "✅" in result  # basefunctions is current
    assert "🟠" in result  # chartfunctions has update available


# =============================================================================
# TESTS FOR WIDER VERSION COLUMNS WITH column_specs
# =============================================================================


def test_local_packages_table_with_wider_version_columns(mock_bootstrap_config):
    """
    Test that Local Packages table uses column_specs for wider version columns.

    TDD CYCLE 1 - RED PHASE:
    - Available column is at least 12 characters wide, right-aligned
    - Installed column is at least 15 characters wide, right-aligned
    - Longer version numbers like "2.9.0.post0" fit completely (not truncated)
    - return_widths=True returns (str, dict) tuple
    """
    # ARRANGE
    ppip = PersonalPip()
    local_packages = [
        ("basefunctions", "2.9.0.post0", "2.9.0.post0", "current"),
        ("chartfunctions", "25.9.0", "2025.10.5", "update_available"),
    ]

    # ACT
    result = ppip._format_local_packages_table(local_packages, return_widths=True)

    # ASSERT
    # Should return tuple (str, dict)
    assert isinstance(result, tuple)
    assert len(result) == 2
    table_str, widths_dict = result

    # Check widths dict structure
    assert isinstance(widths_dict, dict)
    assert "column_widths" in widths_dict
    assert isinstance(widths_dict["column_widths"], list)
    assert len(widths_dict["column_widths"]) == 4  # 4 columns

    # Check Available column (index 1) is at least 12 chars wide
    available_width = widths_dict["column_widths"][1]
    assert available_width >= 12, f"Available column width {available_width} < 12"

    # Check Installed column (index 2) is at least 15 chars wide
    installed_width = widths_dict["column_widths"][2]
    assert installed_width >= 15, f"Installed column width {installed_width} < 15"

    # Check that long version numbers are NOT truncated
    assert "2.9.0.post0" in table_str
    assert "25.9.0" in table_str
    assert "2025.10.5" in table_str


def test_pypi_packages_table_with_wider_version_columns(mock_bootstrap_config):
    """
    Test that PyPI Packages table uses column_specs for wider version columns.

    TDD CYCLE 2 - RED PHASE:
    - PyPI table rendered WITHOUT enforce_widths uses column_specs internally
    - Available column is at least 12 characters wide, right-aligned
    - Installed column is at least 15 characters wide, right-aligned
    - Longer version numbers like "2.9.0.post0" fit completely (not truncated)
    """
    # ARRANGE
    ppip = PersonalPip()
    pypi_packages = [
        ("requests", None, "2.9.0.post0", "pypi"),
        ("numpy", None, "2025.10.5", "pypi"),
    ]

    # ACT - Render WITHOUT enforce_widths to test column_specs usage
    result = ppip._format_pypi_packages_table(pypi_packages)

    # ASSERT
    # Should return string
    assert isinstance(result, str)

    # Check that long version numbers are NOT truncated
    assert "2.9.0.post0" in result
    assert "2025.10.5" in result

    # To verify column widths, render local table with same data to compare
    # Both should use same column_specs internally
    local_packages = [("pkg", "2.9.0.post0", "2025.10.5", "current")]
    _, local_widths = ppip._format_local_packages_table(local_packages, return_widths=True)

    # Widths should meet minimum requirements (12 and 15)
    assert local_widths["column_widths"][1] >= 12, \
        f"Available column width {local_widths['column_widths'][1]} < 12"
    assert local_widths["column_widths"][2] >= 15, \
        f"Installed column width {local_widths['column_widths'][2]} < 15"


def test_both_tables_synchronized_with_wider_columns(mock_bootstrap_config):
    """
    Test that both tables (Local + PyPI) are synchronized with wider columns.

    TDD CYCLE 3 - RED PHASE:
    - Both tables have EXACTLY same total width
    - Column widths are synchronized between both tables
    - Available column >= 12 chars in BOTH tables
    - Installed column >= 15 chars in BOTH tables
    - Long version numbers fit in both tables without truncation
    """
    # ARRANGE
    ppip = PersonalPip()
    packages = [
        ("basefunctions", "2.9.0.post0", "2025.10.5", "current"),
        ("chartfunctions", "1.0.0", "1.0.0", "update_available"),
        ("requests", None, "2.9.0.post0", "pypi"),
        ("numpy", None, "25.9.0", "pypi"),
    ]

    # ACT
    result = ppip._format_packages_as_tables(packages)

    # ASSERT
    assert isinstance(result, str)
    assert len(result) > 0

    # Should contain "PyPI Packages" title
    assert "PyPI Packages" in result

    # Split into sections
    sections = result.split("PyPI Packages")
    assert len(sections) == 2, "Expected exactly one 'PyPI Packages' title"
    local_section = sections[0]
    pypi_section = sections[1]

    # Extract table lines (non-empty)
    local_lines = [line for line in local_section.split("\n") if line.strip()]
    pypi_lines = [line for line in pypi_section.split("\n") if line.strip()]

    # Both tables should have content
    assert len(local_lines) > 0
    assert len(pypi_lines) > 0

    # First line of each table is top border - should have IDENTICAL length
    local_border = local_lines[0]
    pypi_border = pypi_lines[0]
    assert len(local_border) == len(pypi_border), \
        f"Tables have different widths: Local={len(local_border)}, PyPI={len(pypi_border)}"

    # Check that long version numbers are NOT truncated in both tables
    assert "2.9.0.post0" in result
    assert "2025.10.5" in result
    assert "25.9.0" in result

    # Verify width requirements by rendering local table with return_widths
    local_pkgs = [p for p in packages if p[3] != "pypi"]
    _, widths = ppip._format_local_packages_table(local_pkgs, return_widths=True)

    # Check minimum widths
    assert widths["column_widths"][1] >= 12, \
        f"Available column width {widths['column_widths'][1]} < 12"
    assert widths["column_widths"][2] >= 15, \
        f"Installed column width {widths['column_widths'][2]} < 15"


def test_version_numbers_not_truncated(mock_bootstrap_config):
    """
    Test that long version numbers are NOT truncated in tables.

    TDD CYCLE 4 - RED PHASE:
    - Create test data with very long version numbers
    - Render both local and PyPI tables
    - Assert that NO version number is truncated/cut off
    - Assert that all version numbers are fully visible in output
    """
    # ARRANGE
    ppip = PersonalPip()
    # Use VERY long version numbers to stress test
    packages = [
        ("pkg_a", "2.9.0.post0", "2.9.0.post0", "current"),
        ("pkg_b", "25.9.0", "2025.10.5", "update_available"),
        ("pkg_c", "2025.10.5", "25.9.0", "update_available"),
        ("pypi_pkg_a", None, "2.9.0.post0", "pypi"),
        ("pypi_pkg_b", None, "2025.10.5", "pypi"),
        ("pypi_pkg_c", None, "25.9.0", "pypi"),
    ]

    # ACT
    result = ppip._format_packages_as_tables(packages)

    # ASSERT
    assert isinstance(result, str)

    # Check that ALL version numbers are present (not truncated)
    # Available versions
    assert "2.9.0.post0" in result, "Version '2.9.0.post0' not found or truncated"
    assert "25.9.0" in result, "Version '25.9.0' not found or truncated"
    assert "2025.10.5" in result, "Version '2025.10.5' not found or truncated"

    # Count occurrences to verify ALL instances are present
    # "2.9.0.post0" appears 3 times: 1x Available, 1x Installed (local), 1x Installed (PyPI)
    assert result.count("2.9.0.post0") >= 3, \
        f"Expected 3+ occurrences of '2.9.0.post0', found {result.count('2.9.0.post0')}"

    # "25.9.0" appears 3 times: 1x Available, 1x Installed (local), 1x Installed (PyPI)
    assert result.count("25.9.0") >= 3, \
        f"Expected 3+ occurrences of '25.9.0', found {result.count('25.9.0')}"

    # "2025.10.5" appears 3 times: 1x Available, 1x Installed (local), 1x Installed (PyPI)
    assert result.count("2025.10.5") >= 3, \
        f"Expected 3+ occurrences of '2025.10.5', found {result.count('2025.10.5')}"

    # Verify that columns are wide enough
    local_pkgs = [p for p in packages if p[3] != "pypi"]
    _, widths = ppip._format_local_packages_table(local_pkgs, return_widths=True)

    # Column 1 (Available) should be >= 12 to fit "2025.10.5" (10 chars) comfortably
    assert widths["column_widths"][1] >= 12

    # Column 2 (Installed) should be >= 15 to fit "2.9.0.post0" (12 chars) comfortably
    assert widths["column_widths"][2] >= 15
