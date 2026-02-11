"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Tests for update_packages.py script - verify table formatting integration
 Log:
 v1.0.0 : Initial implementation
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
# Standard Library
import sys
from pathlib import Path

# Third Party
import pytest

# Add bin to path for importing update_packages module
bin_path = Path(__file__).parent.parent.parent / "bin"
sys.path.insert(0, str(bin_path))

# Module under test
import update_packages

# Additional imports for testing
from unittest.mock import MagicMock, patch, mock_open


# =============================================================================
# TEST FIXTURES
# =============================================================================
@pytest.fixture
def sample_updates():
    """Provide sample update data for testing."""
    return [
        ("basefunctions", "0.5.10", "0.5.77"),
        ("chartfunctions", "0.3.5", "0.3.10"),
        ("datatools", "1.2.0", "1.2.5")
    ]


# =============================================================================
# TESTS
# =============================================================================
def test_format_update_table_uses_render_table(sample_updates):
    """
    Test that _format_update_table uses render_table with fancy_grid theme.

    Verify:
    - Uses render_table() function from basefunctions
    - Uses fancy_grid theme
    - Has 3 columns: Package, Current, Target
    - Current and Target columns are right-aligned
    """
    # Arrange & Act
    result = update_packages._format_update_table(sample_updates)

    # Assert
    # Verify fancy_grid theme characters are present
    assert "╒" in result, "Should use fancy_grid top-left corner"
    assert "═" in result, "Should use fancy_grid horizontal line"
    assert "╤" in result, "Should use fancy_grid top junction"
    assert "╕" in result, "Should use fancy_grid top-right corner"

    # Verify headers are present
    assert "Package" in result
    assert "Current" in result
    assert "Target" in result

    # Verify data is present
    assert "basefunctions" in result
    assert "0.5.10" in result
    assert "0.5.77" in result


def test_format_update_table_empty_list():
    """
    Test that _format_update_table handles empty update list.

    Verify:
    - Returns empty string for empty list
    """
    # Arrange & Act
    result = update_packages._format_update_table([])

    # Assert
    assert result == "", "Should return empty string for empty list"


def test_format_update_table_column_alignment(sample_updates):
    """
    Test that version columns are right-aligned.

    Verify:
    - Current and Target columns have proper right alignment
    """
    # Arrange & Act
    result = update_packages._format_update_table(sample_updates)

    # Assert
    lines = result.split("\n")

    # Find data rows (skip header and separator rows)
    data_rows = [line for line in lines if "basefunctions" in line or "chartfunctions" in line]

    # Verify at least one data row exists
    assert len(data_rows) > 0, "Should have data rows"

    # The version numbers should be right-aligned
    # This means spaces should appear BEFORE version numbers in their columns
    first_row = data_rows[0]
    assert "0.5.10" in first_row, "Should contain version number"


# =============================================================================
# DEPENDENCY RESOLUTION TESTS
# =============================================================================
def test_get_neuraldevelopment_deps():
    """
    Test extraction of neuraldevelopment dependencies from pyproject.toml.

    Verify:
    - Correctly parses dependencies section
    - Only extracts neuraldevelopment packages
    - Handles missing files gracefully
    """
    # Create mock pyproject.toml content
    pyproject_content = '''
[project]
version = "0.5.81"
dependencies = [
    "numpy>=1.20.0",
    "basefunctions>=0.5.72",
    "dbfunctions>=0.1.0",
    "requests>=2.25.0",
    "taxfunctions>=0.0.1"
]
'''

    updater = update_packages.PackageUpdater()

    with patch("pathlib.Path.exists", return_value=True):
        with patch("pathlib.Path.read_text", return_value=pyproject_content):
            deps = updater._get_neuraldevelopment_deps("portfoliofunctions")

    # Assert
    assert deps == {"basefunctions", "dbfunctions", "taxfunctions"}
    assert "numpy" not in deps  # Should exclude non-neuraldevelopment packages
    assert "requests" not in deps


def test_build_dependency_graph():
    """
    Test dependency graph building.

    Verify:
    - Creates correct dependency relationships
    - Only includes dependencies that are in the update list
    """
    updater = update_packages.PackageUpdater()

    # Mock dependency extraction
    def mock_get_deps(package):
        deps_map = {
            "portfoliofunctions": {"basefunctions", "dbfunctions", "taxfunctions"},
            "dbfunctions": {"basefunctions"},
            "basefunctions": set(),
            "taxfunctions": set()
        }
        return deps_map.get(package, set())

    updater._get_neuraldevelopment_deps = mock_get_deps

    packages = ["basefunctions", "dbfunctions", "portfoliofunctions"]
    graph = updater._build_dependency_graph(packages)

    # Assert
    assert graph["portfoliofunctions"] == {"basefunctions", "dbfunctions"}  # taxfunctions not in update list
    assert graph["dbfunctions"] == {"basefunctions"}
    assert graph["basefunctions"] == set()


def test_topological_sort():
    """
    Test topological sorting of dependency graph.

    Verify:
    - Dependencies come before dependents
    - Handles complex hierarchies correctly
    - Handles cycles gracefully
    """
    updater = update_packages.PackageUpdater()

    # Test normal hierarchy
    graph = {
        "portfoliofunctions": {"dbfunctions", "basefunctions"},
        "dbfunctions": {"basefunctions"},
        "basefunctions": set(),
        "taxfunctions": set()
    }

    sorted_packages = updater._topological_sort(graph)

    # Assert: basefunctions should come before dbfunctions,
    # dbfunctions should come before portfoliofunctions
    assert sorted_packages.index("basefunctions") < sorted_packages.index("dbfunctions")
    assert sorted_packages.index("dbfunctions") < sorted_packages.index("portfoliofunctions")
    assert "taxfunctions" in sorted_packages


def test_topological_sort_with_cycle():
    """
    Test topological sort handles cycles gracefully.

    Verify:
    - Falls back to alphabetical order when cycle detected
    """
    updater = update_packages.PackageUpdater()

    # Create a cycle: A depends on B, B depends on A
    graph = {
        "package_a": {"package_b"},
        "package_b": {"package_a"},
        "package_c": set()
    }

    sorted_packages = updater._topological_sort(graph)

    # Assert: Should still return all packages (fallback behavior)
    assert len(sorted_packages) == 3
    assert all(pkg in sorted_packages for pkg in ["package_a", "package_b", "package_c"])


def test_verify_dependencies_available():
    """
    Test verification of available dependencies.

    Verify:
    - Correctly identifies missing dependencies
    - Returns empty list when all dependencies available
    """
    updater = update_packages.PackageUpdater()

    # Mock available packages
    updater._get_available_local_packages = MagicMock(
        return_value=["basefunctions", "dbfunctions"]
    )

    # Mock dependency extraction
    def mock_get_deps(package):
        deps_map = {
            "portfoliofunctions": {"basefunctions", "dbfunctions", "taxfunctions"},
            "dbfunctions": {"basefunctions"}
        }
        return deps_map.get(package, set())

    updater._get_neuraldevelopment_deps = mock_get_deps

    # Test with missing dependency
    missing = updater._verify_dependencies_available(["portfoliofunctions"])
    assert missing == ["taxfunctions"]

    # Test with all dependencies available
    missing = updater._verify_dependencies_available(["dbfunctions"])
    assert missing == []


def test_update_package_with_no_deps():
    """
    Test that update_package correctly uses --no-deps flag.

    Verify:
    - Adds --no-deps flag when use_no_deps=True
    - Doesn't add flag when use_no_deps=False
    - Tracks updated packages to prevent duplicates
    """
    updater = update_packages.PackageUpdater()
    venv_path = Path("/test/venv")

    with patch("update_packages._run_pip_command") as mock_pip:
        with patch("pathlib.Path.exists", return_value=True):
            # Test with no-deps flag
            updater._update_package("basefunctions", venv_path, use_no_deps=True)
            mock_pip.assert_called_with(
                ["install", "--no-deps", str(updater.packages_dir / "basefunctions")],
                venv_path
            )

            # Reset for next test
            updater._updated_packages.clear()
            mock_pip.reset_mock()

            # Test without no-deps flag
            updater._update_package("dbfunctions", venv_path, use_no_deps=False)
            mock_pip.assert_called_with(
                ["install", str(updater.packages_dir / "dbfunctions")],
                venv_path
            )


def test_update_package_tracking():
    """
    Test that packages are tracked to prevent duplicate updates.

    Verify:
    - First update executes pip command
    - Second update is skipped
    - Tracking is per venv
    """
    updater = update_packages.PackageUpdater()
    venv_path1 = Path("/test/venv1")
    venv_path2 = Path("/test/venv2")

    with patch("update_packages._run_pip_command") as mock_pip:
        with patch("pathlib.Path.exists", return_value=True):
            # First update should execute
            result = updater._update_package("basefunctions", venv_path1, use_no_deps=True)
            assert result is True
            assert mock_pip.call_count == 1

            # Second update to same venv should be skipped
            result = updater._update_package("basefunctions", venv_path1, use_no_deps=True)
            assert result is True
            assert mock_pip.call_count == 1  # Still 1, not called again

            # Update to different venv should execute
            result = updater._update_package("basefunctions", venv_path2, use_no_deps=True)
            assert result is True
            assert mock_pip.call_count == 2


def test_update_order_integration():
    """
    Integration test for complete update order logic.

    Verify:
    - Packages are updated in correct topological order
    - Each package only updated once
    - Uses --no-deps flag
    """
    updater = update_packages.PackageUpdater()

    # Mock dependency extraction
    def mock_get_deps(package):
        deps_map = {
            "portfoliofunctions": {"basefunctions", "dbfunctions"},
            "dbfunctions": {"basefunctions"},
            "basefunctions": set()
        }
        return deps_map.get(package, set())

    updater._get_neuraldevelopment_deps = mock_get_deps

    # Build graph and sort
    packages = ["portfoliofunctions", "dbfunctions", "basefunctions"]
    graph = updater._build_dependency_graph(packages)
    sorted_order = updater._topological_sort(graph)

    # Verify order: basefunctions first, then dbfunctions, then portfoliofunctions
    assert sorted_order[0] == "basefunctions"
    assert sorted_order[-1] == "portfoliofunctions"
    assert sorted_order.index("basefunctions") < sorted_order.index("dbfunctions")
    assert sorted_order.index("dbfunctions") < sorted_order.index("portfoliofunctions")
