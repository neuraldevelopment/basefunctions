"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Tests for demos/demo_table_variants.py - Table rendering variants demo.

 Coverage:
 - demo_render_table_all_themes() - all 4 themes (grid, fancy_grid, minimal, psql)
 - demo_render_dataframe() - pandas DataFrame rendering (with/without pandas)
 - demo_print_kpi_table() - KPI table rendering with filtering
 - demo_tabulate_compat() - backward compatibility wrapper
 - main() - complete demo execution

 Log:
 v1.0.0 : Initial implementation
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
# Standard Library
import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch

# Third-party
import pytest

# Load demo_table_variants module from file path
demo_path = Path(__file__).parent.parent.parent / "demos" / "demo_table_variants.py"
spec = importlib.util.spec_from_file_location("demo_table_variants", demo_path)
if spec is None or spec.loader is None:
    raise ImportError(f"Failed to load demo_table_variants from {demo_path}")
demo_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(demo_module)

# Register in sys.modules for potential mocking
sys.modules["demo_table_variants"] = demo_module


# =============================================================================
# TEST: demo_render_table_all_themes
# =============================================================================
def test_demo_render_table_all_themes_executes_successfully(capsys):
    """Test demo_render_table_all_themes runs without errors and shows all 4 themes."""
    # Arrange & Act
    demo_module.demo_render_table_all_themes()
    captured = capsys.readouterr()

    # Assert - header and all 4 themes present
    assert "1. RENDER_TABLE() - ALL 4 THEMES" in captured.out
    assert "Theme: GRID" in captured.out
    assert "Theme: FANCY_GRID" in captured.out
    assert "Theme: MINIMAL" in captured.out
    assert "Theme: PSQL" in captured.out

    # Assert - financial data present
    assert "Q1 2024" in captured.out
    assert "Revenue" in captured.out
    assert "Margin %" in captured.out


def test_demo_render_table_all_themes_shows_correct_data(capsys):
    """Test demo_render_table_all_themes displays financial performance data."""
    # Arrange & Act
    demo_module.demo_render_table_all_themes()
    captured = capsys.readouterr()

    # Assert - quarterly data and metrics
    assert "Q2 2024" in captured.out
    assert "Q3 2024" in captured.out
    assert "Q4 2024" in captured.out
    assert "Profit" in captured.out


# =============================================================================
# TEST: demo_render_dataframe
# =============================================================================
def test_demo_render_dataframe_with_pandas_installed(capsys):
    """Test demo_render_dataframe executes successfully when pandas is available."""
    # Arrange - check if pandas is available
    try:
        import pandas  # noqa: F401,F841

        has_pandas = True
    except ImportError:
        has_pandas = False

    if not has_pandas:
        pytest.skip("pandas not installed")

    # Act
    demo_module.demo_render_dataframe()
    captured = capsys.readouterr()

    # Assert - headers and data present
    assert "2. RENDER_DATAFRAME() - PANDAS SUPPORT" in captured.out
    assert "Without Index" in captured.out
    assert "With Index" in captured.out
    assert "Product" in captured.out
    assert "Laptop Pro" in captured.out
    assert "Desktop Elite" in captured.out


def test_demo_render_dataframe_without_pandas_skips_gracefully(capsys):
    """Test demo_render_dataframe skips gracefully when pandas not installed."""
    # Arrange - mock HAS_PANDAS as False using patch
    with patch.object(demo_module, 'HAS_PANDAS', False):  # type: ignore
        # Act
        demo_module.demo_render_dataframe()
        captured = capsys.readouterr()

        # Assert - skipped message
        assert "2. RENDER_DATAFRAME() - SKIPPED (pandas not installed)" in captured.out


# =============================================================================
# TEST: demo_print_kpi_table
# =============================================================================
def test_demo_print_kpi_table_executes_successfully(capsys):
    """Test demo_print_kpi_table runs without errors and displays KPI data."""
    # Arrange & Act
    demo_module.demo_print_kpi_table()
    captured = capsys.readouterr()

    # Assert - header and sections present
    assert "3. PRINT_KPI_TABLE() - KPI RENDERING" in captured.out
    assert "All KPIs (sorted by package/subgroup)" in captured.out
    assert "Filtered KPIs (portfoliofunctions only)" in captured.out


def test_demo_print_kpi_table_shows_portfolio_kpis(capsys):
    """Test demo_print_kpi_table displays portfoliofunctions KPIs."""
    # Arrange & Act
    demo_module.demo_print_kpi_table()
    captured = capsys.readouterr()

    # Assert - portfolio metrics present
    assert "total_return" in captured.out
    assert "win_rate" in captured.out
    assert "sharpe_ratio" in captured.out


def test_demo_print_kpi_table_shows_backtester_kpis(capsys):
    """Test demo_print_kpi_table displays backtesterfunctions KPIs."""
    # Arrange & Act
    demo_module.demo_print_kpi_table()
    captured = capsys.readouterr()

    # Assert - backtester metrics present
    assert "total_backtest_runs" in captured.out
    assert "avg_runtime" in captured.out


# =============================================================================
# TEST: demo_tabulate_compat
# =============================================================================
def test_demo_tabulate_compat_executes_successfully(capsys):
    """Test demo_tabulate_compat runs without errors and shows backward compatibility."""
    # Arrange & Act
    demo_module.demo_tabulate_compat()
    captured = capsys.readouterr()

    # Assert - header and all 3 format variants
    assert "4. TABULATE_COMPAT() - BACKWARD COMPATIBILITY" in captured.out
    assert "Legacy tabulate() call with grid format" in captured.out
    assert "Legacy tabulate() call with fancy_grid format" in captured.out
    assert "Legacy tabulate() call with psql format" in captured.out


def test_demo_tabulate_compat_shows_server_data(capsys):
    """Test demo_tabulate_compat displays server performance metrics."""
    # Arrange & Act
    demo_module.demo_tabulate_compat()
    captured = capsys.readouterr()

    # Assert - server metrics present
    assert "Server" in captured.out
    assert "CPU %" in captured.out
    assert "Memory MB" in captured.out
    assert "web-server-01" in captured.out
    assert "db-server-01" in captured.out


# =============================================================================
# TEST: main
# =============================================================================
def test_main_executes_all_demos_successfully(capsys):
    """Test main runs all demo functions and completes successfully."""
    # Arrange & Act
    demo_module.main()
    captured = capsys.readouterr()

    # Assert - main header and completion message
    assert "BASEFUNCTIONS TABLE RENDERING - ALL VARIANTS" in captured.out
    assert "DEMO COMPLETE" in captured.out

    # Assert - all 4 demo sections executed
    assert "1. RENDER_TABLE() - ALL 4 THEMES" in captured.out
    assert "2. RENDER_DATAFRAME()" in captured.out
    assert "3. PRINT_KPI_TABLE()" in captured.out
    assert "4. TABULATE_COMPAT()" in captured.out


def test_main_shows_all_table_themes(capsys):
    """Test main displays all 4 table themes through render_table demo."""
    # Arrange & Act
    demo_module.main()
    captured = capsys.readouterr()

    # Assert - all themes visible in output
    assert "Theme: GRID" in captured.out
    assert "Theme: FANCY_GRID" in captured.out
    assert "Theme: MINIMAL" in captured.out
    assert "Theme: PSQL" in captured.out


def test_main_handles_missing_pandas_gracefully(capsys):
    """Test main handles missing pandas gracefully in render_dataframe demo."""
    # Arrange - mock HAS_PANDAS as False using patch
    with patch.object(demo_module, 'HAS_PANDAS', False):  # type: ignore
        # Act
        demo_module.main()
        captured = capsys.readouterr()

        # Assert - completes successfully with skip message
        assert "DEMO COMPLETE" in captured.out
        assert "SKIPPED" in captured.out


# =============================================================================
# TEST: Script Execution
# =============================================================================
def test_script_is_executable():
    """Test demo_table_variants.py is executable as script."""
    # Arrange
    demo_file = Path(__file__).parent.parent.parent / "demos" / "demo_table_variants.py"

    # Act & Assert - file exists and is readable
    assert demo_file.exists()
    assert demo_file.is_file()

    # Assert - file has __main__ execution block
    content = demo_file.read_text(encoding="utf-8")
    assert 'if __name__ == "__main__":' in content
    assert "main()" in content
