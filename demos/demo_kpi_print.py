"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Demo for print_kpi_table with KPIValue protocol - creates 5 sample KPIs
 and displays them using formatted table output
 Log:
 v1.0 : Initial implementation
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
from basefunctions.kpi.exporters import print_kpi_table


# =============================================================================
# FUNCTION DEFINITIONS
# =============================================================================
def main():
    """
    Demo: Create sample KPIs and display with print_kpi_table.

    Creates 5 KPIs across different packages and subgroups:
    - Portfolio activity metrics (win_rate, total_trades)
    - Portfolio returns metrics (total_pnl, avg_return)
    - System performance metric (cpu_usage)

    All KPIs use the KPIValue protocol: {"value": float, "unit": str}
    """
    # Create sample KPI dictionary with 5 metrics
    kpis = {
        "business": {
            "portfolio": {
                "activity": {"win_rate": {"value": 0.75, "unit": "%"}, "total_trades": {"value": 150.0, "unit": "-"}},
                "returns": {
                    "total_pnl": {"value": 25000.0, "unit": "USD"},
                    "avg_return": {"value": 0.0325, "unit": "%"},
                },
            }
        },
        "technical": {"system": {"performance": {"cpu_usage": {"value": 42.5, "unit": "%"}}}},
    }

    # ========================================================================
    # VERSION 1: KPI Table with 3 Columns (unit_column=True, DEFAULT)
    # ========================================================================
    print("=" * 80)
    print("VERSION 1: print_kpi_table(unit_column=True) - 3 Columns (DEFAULT)")
    print("=" * 80)

    # Print KPI table with default settings (EUR currency, 50 char width, 3 columns)
    print("\n=== Demo: KPI Table Output (3 Columns) ===")
    print_kpi_table(kpis, decimals=2, currency="EUR")

    # Print filtered view - only portfolio metrics
    print("\n=== Demo: Filtered View (Portfolio only, 3 Columns) ===")
    print_kpi_table(kpis, filter_patterns=["business.portfolio.*"], decimals=2, unit_column=True)

    # ========================================================================
    # VERSION 2: KPI Table with 2 Columns (unit_column=False)
    # ========================================================================
    print("\n\n")
    print("=" * 80)
    print("VERSION 2: print_kpi_table(unit_column=False) - 2 Columns")
    print("=" * 80)

    # Print KPI table with 2 columns (EUR currency, 50 char width)
    print("\n=== Demo: KPI Table Output (2 Columns) ===")
    print_kpi_table(kpis, decimals=2, currency="EUR", unit_column=False)

    # Print filtered view - only portfolio metrics
    print("\n=== Demo: Filtered View (Portfolio only, 2 Columns) ===")
    print_kpi_table(kpis, filter_patterns=["business.portfolio.*"], decimals=2, unit_column=False)

    # Print with custom currency and decimal precision
    print("\n=== Demo: Custom Currency (USD) + High Precision (2 Columns) ===")
    print_kpi_table(kpis, filter_patterns=["business.*"], decimals=4, currency="USD", unit_column=True)


if __name__ == "__main__":
    main()
