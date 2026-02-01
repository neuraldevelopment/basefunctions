#!/usr/bin/env python3
"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Demo script showing ALL table rendering variants in basefunctions.
 Demonstrates the 4 main rendering functions with realistic data.
 Log:
 v1.0.0 : Initial implementation
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
# Standard Library
# (none required)

# Third-party
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

# Project modules
from basefunctions.kpi.exporters import print_kpi_table
from basefunctions.utils.table_renderer import (
    render_dataframe,
    render_table,
    tabulate_compat,
)


# =============================================================================
# CONSTANTS
# =============================================================================
SEPARATOR_MAJOR = "=" * 80
SEPARATOR_MINOR = "-" * 80


# =============================================================================
# FUNCTION DEFINITIONS
# =============================================================================
def demo_render_table_all_themes() -> None:
    """
    Demonstrate render_table() with all 4 themes.

    Shows identical financial data rendered in grid, fancy_grid,
    minimal, and psql themes for direct comparison.
    """
    print(f"\n{SEPARATOR_MAJOR}")
    print("1. RENDER_TABLE() - ALL 4 THEMES")
    print(SEPARATOR_MAJOR)

    # Financial performance data
    data = [
        ["Q1 2024", 1250000.50, 875000.25, 375000.25, 30.0],
        ["Q2 2024", 1450000.75, 950000.50, 500000.25, 34.5],
        ["Q3 2024", 1680000.00, 1100000.00, 580000.00, 34.5],
        ["Q4 2024", 1920000.25, 1250000.75, 669250.50, 34.9],
    ]
    headers = ["Period", "Revenue", "Costs", "Profit", "Margin %"]
    column_specs = [
        "left:12",
        "decimal:15:2",
        "decimal:15:2",
        "decimal:15:2",
        "decimal:10:1:%",
    ]

    themes = ["grid", "fancy_grid", "minimal", "psql"]

    for theme in themes:
        print(f"\n{SEPARATOR_MINOR}")
        print(f"Theme: {theme.upper()}")
        print(SEPARATOR_MINOR)
        print(
            render_table(
                data, headers=headers, column_specs=column_specs, theme=theme
            )
        )


def demo_render_dataframe() -> None:
    """
    Demonstrate render_dataframe() with pandas DataFrame.

    Shows product sales data with themed rendering and optional
    index display.
    """
    if not HAS_PANDAS:
        print(f"\n{SEPARATOR_MAJOR}")
        print("2. RENDER_DATAFRAME() - SKIPPED (pandas not installed)")
        print(SEPARATOR_MAJOR)
        return

    print(f"\n{SEPARATOR_MAJOR}")
    print("2. RENDER_DATAFRAME() - PANDAS SUPPORT")
    print(SEPARATOR_MAJOR)

    # Product sales data
    df = pd.DataFrame(
        {
            "Product": ["Laptop Pro", "Desktop Elite", "Monitor 4K"],
            "Units Sold": [1250, 850, 2100],
            "Revenue": [1875000.00, 1445000.00, 525000.00],
            "Avg Price": [1500.00, 1700.00, 250.00],
        }
    )

    print(f"\n{SEPARATOR_MINOR}")
    print("Without Index (fancy_grid theme)")
    print(SEPARATOR_MINOR)
    print(render_dataframe(df, theme="fancy_grid", showindex=False))

    print(f"\n{SEPARATOR_MINOR}")
    print("With Index (grid theme)")
    print(SEPARATOR_MINOR)
    print(render_dataframe(df, theme="grid", showindex=True))


def demo_print_kpi_table() -> None:
    """
    Demonstrate print_kpi_table() for KPI display.

    Shows business KPIs grouped by package and subgroup with
    automatic formatting, units, and color-coded headers.
    """
    print(f"\n{SEPARATOR_MAJOR}")
    print("3. PRINT_KPI_TABLE() - KPI RENDERING")
    print(SEPARATOR_MAJOR)

    # Nested KPI structure: business.package.subgroup.metric
    kpis = {
        "business": {
            "portfoliofunctions": {
                "performance": {
                    "total_return": {"value": 15.75, "unit": "%"},
                    "sharpe_ratio": {"value": 1.85, "unit": "-"},
                    "max_drawdown": {"value": -8.50, "unit": "%"},
                },
                "activity": {
                    "total_trades": {"value": 1250, "unit": "-"},
                    "win_rate": {"value": 62.5, "unit": "%"},
                    "avg_holding_days": {"value": 14.5, "unit": "days"},
                },
                "risk": {
                    "volatility": {"value": 12.3, "unit": "%"},
                    "value_at_risk": {"value": 25000.00, "unit": "USD"},
                    "beta": {"value": 0.95, "unit": "-"},
                },
            },
            "backtesterfunctions": {
                "metrics": {
                    "total_backtest_runs": {"value": 45, "unit": "-"},
                    "avg_runtime": {"value": 125.5, "unit": "s"},
                    "success_rate": {"value": 95.5, "unit": "%"},
                },
                "data": {
                    "instruments_tested": {"value": 150, "unit": "-"},
                    "data_points": {"value": 2500000, "unit": "-"},
                },
            },
        }
    }

    print(f"\n{SEPARATOR_MINOR}")
    print("All KPIs (sorted by package/subgroup)")
    print(SEPARATOR_MINOR)
    print_kpi_table(
        kpis,
        decimals=2,
        sort_keys=True,
        currency="EUR",
        max_table_width=80,
        unit_column=False,
    )

    print(f"\n{SEPARATOR_MINOR}")
    print("Filtered KPIs (portfoliofunctions only)")
    print(SEPARATOR_MINOR)
    print_kpi_table(
        kpis,
        filter_patterns=["business.portfoliofunctions.*"],
        decimals=2,
        sort_keys=False,
        currency="EUR",
        max_table_width=80,
        unit_column=False,
    )


def demo_tabulate_compat() -> None:
    """
    Demonstrate tabulate_compat() for backward compatibility.

    Shows legacy tabulate() API support with colalign parameter
    and multiple format strings.
    """
    print(f"\n{SEPARATOR_MAJOR}")
    print("4. TABULATE_COMPAT() - BACKWARD COMPATIBILITY")
    print(SEPARATOR_MAJOR)

    # Server performance metrics
    data = [
        ["web-server-01", 45.5, 8192, 99.95],
        ["web-server-02", 52.3, 7850, 99.87],
        ["web-server-03", 38.9, 8500, 99.99],
        ["db-server-01", 78.2, 16384, 99.92],
    ]
    headers = ["Server", "CPU %", "Memory MB", "Uptime %"]
    colalign = ("left", "decimal", "right", "decimal")

    print(f"\n{SEPARATOR_MINOR}")
    print("Legacy tabulate() call with grid format")
    print(SEPARATOR_MINOR)
    print(tabulate_compat(data, headers=headers, tablefmt="grid", colalign=colalign))

    print(f"\n{SEPARATOR_MINOR}")
    print("Legacy tabulate() call with fancy_grid format")
    print(SEPARATOR_MINOR)
    print(
        tabulate_compat(data, headers=headers, tablefmt="fancy_grid", colalign=colalign)
    )

    print(f"\n{SEPARATOR_MINOR}")
    print("Legacy tabulate() call with psql format")
    print(SEPARATOR_MINOR)
    print(tabulate_compat(data, headers=headers, tablefmt="psql", colalign=colalign))


def main() -> None:
    """
    Run all table rendering variant demos.

    Demonstrates the 4 main table rendering functions in basefunctions
    with realistic, production-like data examples.
    """
    print(SEPARATOR_MAJOR)
    print("BASEFUNCTIONS TABLE RENDERING - ALL VARIANTS")
    print(SEPARATOR_MAJOR)

    demo_render_table_all_themes()
    demo_render_dataframe()
    demo_print_kpi_table()
    demo_tabulate_compat()

    print(f"\n{SEPARATOR_MAJOR}")
    print("DEMO COMPLETE")
    print(SEPARATOR_MAJOR)
    print()


# =============================================================================
# MAIN EXECUTION
# =============================================================================
if __name__ == "__main__":
    main()
