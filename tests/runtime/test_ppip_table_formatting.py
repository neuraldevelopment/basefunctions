"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.

 Description:
 Pytest test suite for ppip table formatting and version comparison.
 Tests colored table output with version comparison and emoji status indicators.

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
def mock_package_data_long_names():
    """
    Mock data with long package names to test column width.

    Returns
    -------
    List[Tuple[str, str, str, str]]
        List with packages with very long names
    """
    # ARRANGE & RETURN
    return [
        ("very_long_package_name_that_exceeds_normal_width", "1.0.0", "1.0.0", "current"),
        ("another_extremely_long_package_name", "2.0.0", "1.5.0", "update_available"),
        ("short", "1.0.0", None, "not_installed"),
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


def test_get_package_status_major_version_difference():
    """Test version comparison with major version difference."""
    # ARRANGE

    ppip = PersonalPip()
    local_version = "2.0.0"
    installed_version = "1.9.9"

    # ACT
    result = ppip.get_package_status(local_version, installed_version)

    # ASSERT
    assert result == "update_available"


def test_get_package_status_minor_version_difference():
    """Test version comparison with minor version difference."""
    # ARRANGE

    ppip = PersonalPip()
    local_version = "1.5.0"
    installed_version = "1.4.9"

    # ACT
    result = ppip.get_package_status(local_version, installed_version)

    # ASSERT
    assert result == "update_available"


def test_get_package_status_patch_version_difference():
    """Test version comparison with patch version difference."""
    # ARRANGE

    ppip = PersonalPip()
    local_version = "1.0.5"
    installed_version = "1.0.3"

    # ACT
    result = ppip.get_package_status(local_version, installed_version)

    # ASSERT
    assert result == "update_available"


def test_get_package_status_installed_greater_returns_current():
    """Test that installed > local returns 'current' (no downgrade)."""
    # ARRANGE

    ppip = PersonalPip()
    local_version = "1.0.0"
    installed_version = "1.5.0"

    # ACT
    result = ppip.get_package_status(local_version, installed_version)

    # ASSERT
    # When installed > local, we consider it current (no forced downgrade)
    assert result == "current"


def test_get_package_status_both_none_returns_not_installed():
    """Test that both None versions returns 'not_installed' status."""
    # ARRANGE

    ppip = PersonalPip()
    local_version = None
    installed_version = None

    # ACT
    result = ppip.get_package_status(local_version, installed_version)

    # ASSERT
    assert result == "not_installed"


# =============================================================================
# TESTS FOR format_package_table()
# =============================================================================


def test_format_package_table_empty_list_returns_header_only(mock_package_data_empty):
    """Test that empty package list returns only table header."""
    # ARRANGE

    ppip = PersonalPip()
    packages = mock_package_data_empty

    # ACT
    result = ppip.format_package_table(packages)

    # ASSERT
    # Should contain header row with column names
    assert "Package" in result
    assert "Available" in result
    assert "Installed" in result
    assert "Status" in result
    # Should contain box drawing characters
    assert "─" in result or "━" in result
    assert "│" in result or "┃" in result


def test_format_package_table_single_package(mock_package_data_single):
    """Test formatting single package entry."""
    # ARRANGE

    ppip = PersonalPip()
    packages = mock_package_data_single

    # ACT
    result = ppip.format_package_table(packages)

    # ASSERT
    # Should contain package name
    assert "basefunctions" in result
    # Should contain version
    assert "0.5.75" in result
    # Should contain status emoji
    assert "✅" in result  # current status emoji
    # Should contain box drawing characters
    assert "─" in result or "━" in result
    assert "│" in result or "┃" in result


def test_format_package_table_multiple_packages(mock_package_data_multiple):
    """Test formatting multiple packages with different statuses."""
    # ARRANGE

    ppip = PersonalPip()
    packages = mock_package_data_multiple

    # ACT
    result = ppip.format_package_table(packages)

    # ASSERT
    # Should contain all package names
    assert "basefunctions" in result
    assert "chartfunctions" in result
    assert "newpackage" in result
    assert "requests" in result
    # Should contain all status emojis
    assert "✅" in result  # current
    assert "🟠" in result  # update_available
    assert "❌" in result  # not_installed
    assert "📦" in result  # pypi


def test_format_package_table_contains_ansi_color_codes(mock_package_data_multiple):
    """Test that output contains ANSI color codes."""
    # ARRANGE

    ppip = PersonalPip()
    packages = mock_package_data_multiple

    # ACT
    result = ppip.format_package_table(packages)

    # ASSERT
    # Should contain ANSI escape codes for colors
    assert "\033[" in result or "\x1b[" in result
    # Green (32), Orange/Yellow (33), Red (31), Blue (34)
    assert "32m" in result or "33m" in result or "31m" in result or "34m" in result


def test_format_package_table_long_names_auto_width(mock_package_data_long_names):
    """Test that long package names adjust column width automatically."""
    # ARRANGE

    ppip = PersonalPip()
    packages = mock_package_data_long_names

    # ACT
    result = ppip.format_package_table(packages)

    # ASSERT
    # Should contain full package names (not truncated)
    assert "very_long_package_name_that_exceeds_normal_width" in result
    assert "another_extremely_long_package_name" in result
    # Should still have proper alignment (check for consistent separators)
    lines = result.split("\n")
    # All separator lines should be same length
    separator_lines = [line for line in lines if "─" in line or "━" in line]
    if len(separator_lines) > 1:
        assert len(separator_lines[0]) == len(separator_lines[-1])


def test_format_package_table_unicode_box_drawing():
    """Test that output uses Unicode box drawing characters."""
    # ARRANGE

    ppip = PersonalPip()
    packages = [("test", "1.0.0", "1.0.0", "current")]

    # ACT
    result = ppip.format_package_table(packages)

    # ASSERT
    # Should contain box drawing characters (various styles possible)
    box_chars = ["─", "━", "│", "┃", "┌", "┐", "└", "┘", "├", "┤", "┬", "┴", "┼"]
    assert any(char in result for char in box_chars)


def test_format_package_table_proper_alignment():
    """Test that columns are properly aligned."""
    # ARRANGE

    ppip = PersonalPip()
    packages = [
        ("short", "1.0.0", "1.0.0", "current"),
        ("very_long_package_name", "2.5.10", "2.5.9", "update_available"),
    ]

    # ACT
    result = ppip.format_package_table(packages)

    # ASSERT
    lines = result.split("\n")
    # Filter out empty lines and ANSI codes for alignment check
    import re

    clean_lines = [re.sub(r"\033\[[0-9;]+m", "", line) for line in lines if line.strip()]

    # Each data row should have same number of separators (│ or ┃)
    data_rows = [line for line in clean_lines if "─" not in line and "━" not in line and line.strip()]
    if len(data_rows) > 1:
        separator_counts = [line.count("│") + line.count("┃") for line in data_rows]
        assert len(set(separator_counts)) == 1  # All rows should have same separator count


def test_format_package_table_status_emoji_current():
    """Test that 'current' status shows green checkmark emoji."""
    # ARRANGE

    ppip = PersonalPip()
    packages = [("test", "1.0.0", "1.0.0", "current")]

    # ACT
    result = ppip.format_package_table(packages)

    # ASSERT
    assert "✅" in result


def test_format_package_table_status_emoji_update_available():
    """Test that 'update_available' status shows orange circle emoji."""
    # ARRANGE

    ppip = PersonalPip()
    packages = [("test", "1.5.0", "1.0.0", "update_available")]

    # ACT
    result = ppip.format_package_table(packages)

    # ASSERT
    assert "🟠" in result


def test_format_package_table_status_emoji_not_installed():
    """Test that 'not_installed' status shows red X emoji."""
    # ARRANGE

    ppip = PersonalPip()
    packages = [("test", "1.0.0", None, "not_installed")]

    # ACT
    result = ppip.format_package_table(packages)

    # ASSERT
    assert "❌" in result


def test_format_package_table_status_emoji_pypi():
    """Test that 'pypi' status shows package emoji."""
    # ARRANGE

    ppip = PersonalPip()
    packages = [("requests", None, "2.31.0", "pypi")]

    # ACT
    result = ppip.format_package_table(packages)

    # ASSERT
    assert "📦" in result


def test_format_package_table_none_installed_version_display():
    """Test that None installed_version displays as dash or empty."""
    # ARRANGE

    ppip = PersonalPip()
    packages = [("newpkg", "1.0.0", None, "not_installed")]

    # ACT
    result = ppip.format_package_table(packages)

    # ASSERT
    # Should show some placeholder for None (like "-" or "N/A")
    assert "newpkg" in result
    # The exact placeholder depends on implementation, but should not show "None"
    assert "None" not in result


def test_format_package_table_none_available_version_display():
    """Test that None available_version displays as dash or empty."""
    # ARRANGE

    ppip = PersonalPip()
    packages = [("requests", None, "2.31.0", "pypi")]

    # ACT
    result = ppip.format_package_table(packages)

    # ASSERT
    # Should show some placeholder for None (like "-" or "N/A")
    assert "requests" in result
    # Should not show literal "None"
    assert result.count("None") == 0 or "-" in result


def test_format_package_table_renders_separator():
    """Test that separator is rendered as blank line in table."""
    # ARRANGE

    ppip = PersonalPip()
    packages = [
        ("basefunctions", "0.5.75", "0.5.75", "current"),
        ("__separator__", None, None, None),
        ("requests", None, "2.31.0", "pypi"),
    ]

    # ACT
    result = ppip.format_package_table(packages)

    # ASSERT
    # Should contain a blank/separator line between packages
    lines = result.split("\n")
    # Should have more lines than just header + 2 data rows
    # Expected: header, separator, data1, separator/blank, data2, separator
    assert len(lines) >= 5
    # Find the blank line or separator line between data rows
    has_blank_line = any(line.strip() == "" for line in lines)
    has_separator_line = any("─" in line and all(c in "─│┌┐└┘├┤┬┴┼ " for c in line.strip()) for line in lines)
    assert has_blank_line or has_separator_line


def test_format_package_table_separator_has_full_width():
    """Test that separator line spans full table width."""
    # ARRANGE

    ppip = PersonalPip()
    packages = [
        ("basefunctions", "0.5.75", "0.5.75", "current"),
        ("__separator__", None, None, None),
        ("requests", None, "2.31.0", "pypi"),
    ]

    # ACT
    result = ppip.format_package_table(packages)

    # ASSERT
    import re

    lines = result.split("\n")
    # Remove ANSI codes for width comparison
    clean_lines = [re.sub(r"\033\[[0-9;]+m", "", line) for line in lines]
    # Get widths of all non-empty lines
    widths = [len(line) for line in clean_lines if line.strip()]
    # All lines should have similar widths (within reasonable tolerance)
    if len(widths) > 1:
        max_width = max(widths)
        min_width = min(widths)
        # Allow small variance for box characters
        assert max_width - min_width <= 2


# =============================================================================
# TESTS FOR version sorting and display ordering
# =============================================================================


def test_sort_packages_by_status_priority():
    """Test that packages are sorted by status priority."""
    # ARRANGE

    ppip = PersonalPip()
    packages = [
        ("pkg_current", "1.0.0", "1.0.0", "current"),
        ("pkg_update", "2.0.0", "1.0.0", "update_available"),
        ("pkg_not_installed", "1.0.0", None, "not_installed"),
        ("pkg_pypi", None, "2.0.0", "pypi"),
    ]

    # ACT
    sorted_packages = ppip.sort_packages_for_display(packages)

    # ASSERT
    # Expected order: update_available (orange), not_installed (red), current (green), pypi (blue) at end
    statuses = [pkg[3] for pkg in sorted_packages]
    # Update available should come before not_installed
    assert statuses.index("update_available") < statuses.index("not_installed")
    # Not installed should come before current
    assert statuses.index("not_installed") < statuses.index("current")
    # PyPI should be last
    assert statuses[-1] == "pypi"


def test_sort_packages_alphabetically_within_status():
    """Test that packages are sorted alphabetically within same status."""
    # ARRANGE

    ppip = PersonalPip()
    packages = [
        ("zebra", "1.0.0", "0.5.0", "update_available"),
        ("apple", "1.0.0", "0.5.0", "update_available"),
        ("mango", "1.0.0", "0.5.0", "update_available"),
    ]

    # ACT
    sorted_packages = ppip.sort_packages_for_display(packages)

    # ASSERT
    names = [pkg[0] for pkg in sorted_packages]
    assert names == ["apple", "mango", "zebra"]


def test_sort_packages_pypi_at_bottom_alphabetically():
    """Test that PyPI packages are at bottom, sorted alphabetically."""
    # ARRANGE

    ppip = PersonalPip()
    packages = [
        ("local_pkg", "1.0.0", "1.0.0", "current"),
        ("zzz_pypi", None, "1.0.0", "pypi"),
        ("aaa_pypi", None, "2.0.0", "pypi"),
        ("mmm_pypi", None, "3.0.0", "pypi"),
    ]

    # ACT
    sorted_packages = ppip.sort_packages_for_display(packages)

    # ASSERT
    # Last three should be PyPI packages in alphabetical order
    pypi_packages = [pkg for pkg in sorted_packages if pkg[3] == "pypi"]
    pypi_names = [pkg[0] for pkg in pypi_packages]
    assert pypi_names == ["aaa_pypi", "mmm_pypi", "zzz_pypi"]
    # PyPI packages should be at end
    assert all(pkg[3] == "pypi" for pkg in sorted_packages[-3:])


def test_sort_packages_mixed_statuses_complex():
    """Test sorting with all status types mixed."""
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
    # Expected order:
    # 1. update_available (alphabetically): apple_update, date_update
    # 2. not_installed: mango_not_installed
    # 3. current (alphabetically): banana_current, zebra_current
    # 4. [SEPARATOR]
    # 5. pypi: cherry_pypi
    names = [pkg[0] for pkg in sorted_packages]
    expected = [
        "apple_update",
        "date_update",
        "mango_not_installed",
        "banana_current",
        "zebra_current",
        "__separator__",
        "cherry_pypi",
    ]
    assert names == expected


def test_sort_packages_empty_list():
    """Test sorting empty package list."""
    # ARRANGE

    ppip = PersonalPip()
    packages = []

    # ACT
    sorted_packages = ppip.sort_packages_for_display(packages)

    # ASSERT
    assert sorted_packages == []


def test_sort_packages_case_insensitive_alphabetical():
    """Test that alphabetical sorting is case-insensitive."""
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
    # Should be sorted case-insensitively
    assert names == ["apple", "Mango", "Zebra"]


def test_sort_packages_includes_separator_between_local_and_pypi():
    """Test that separator is included between local and PyPI packages."""
    # ARRANGE

    ppip = PersonalPip()
    packages = [
        ("basefunctions", "0.5.75", "0.5.75", "current"),
        ("requests", None, "2.31.0", "pypi"),
    ]

    # ACT
    sorted_packages = ppip.sort_packages_for_display(packages)

    # ASSERT
    # Should have 3 entries: local package, separator, pypi package
    assert len(sorted_packages) == 3
    # Separator should be between local and pypi
    assert sorted_packages[1] == ("__separator__", None, None, None)
    # First should be local package
    assert sorted_packages[0][3] != "pypi"
    # Last should be pypi package
    assert sorted_packages[2][3] == "pypi"


def test_sort_packages_local_sorted_alphabetically_within_status():
    """Test that local packages are alphabetically sorted within same status."""
    # ARRANGE

    ppip = PersonalPip()
    packages = [
        ("dbfunctions", "0.1.24", "0.1.23", "update_available"),
        ("basefunctions", "0.5.75", "0.5.75", "current"),
        ("newpkg", "1.0.0", None, "not_installed"),
        ("requests", None, "2.31.0", "pypi"),
    ]

    # ACT
    sorted_packages = ppip.sort_packages_for_display(packages)

    # ASSERT
    # Expected order:
    # 1. dbfunctions (update_available) - first status priority
    # 2. newpkg (not_installed) - second status priority
    # 3. basefunctions (current) - third status priority
    # 4. [SEPARATOR]
    # 5. requests (pypi)
    assert len(sorted_packages) == 5
    assert sorted_packages[0][0] == "dbfunctions"
    assert sorted_packages[0][3] == "update_available"
    assert sorted_packages[1][0] == "newpkg"
    assert sorted_packages[1][3] == "not_installed"
    assert sorted_packages[2][0] == "basefunctions"
    assert sorted_packages[2][3] == "current"
    assert sorted_packages[3] == ("__separator__", None, None, None)
    assert sorted_packages[4][0] == "requests"
    assert sorted_packages[4][3] == "pypi"


# =============================================================================
# INTEGRATION TEST - Full list_packages with formatting
# =============================================================================


def test_list_packages_integration_with_table_format(tmp_path, monkeypatch):
    """Test list_packages() method using new table format."""
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
        ppip, "get_installed_versions", lambda: {"basefunctions": "0.5.75", "chartfunctions": "1.2.0"}
    )

    # ACT
    # Capture output by redirecting stdout
    import io
    import sys

    captured_output = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = captured_output

    try:
        ppip.list_packages()
    finally:
        sys.stdout = old_stdout

    result = captured_output.getvalue()

    # ASSERT
    # Should contain table with box drawing characters
    assert "─" in result or "━" in result
    assert "│" in result or "┃" in result
    # Should contain package names
    assert "basefunctions" in result
    assert "chartfunctions" in result
    # Should contain emojis
    assert "✅" in result  # basefunctions is current
    assert "🟠" in result  # chartfunctions has update available
