"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Comprehensive demo of table_renderer module showing all features and themes
 Log:
 v1.0.0 : Initial implementation
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
# Standard Library
# (no typing imports needed)

# Third-party
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

# Project modules
from basefunctions.utils.table_renderer import (
    render_table,
    render_dataframe,
    tabulate_compat
)


# =============================================================================
# CONSTANTS
# =============================================================================
SEPARATOR_MAJOR = "=" * 80
SEPARATOR_MINOR = "-" * 80


# =============================================================================
# FUNCTION DEFINITIONS
# =============================================================================
def demo_basic_table() -> None:
    """
    Demonstrate basic table rendering with default grid theme.

    Shows simple 2D list with headers rendered in grid theme.
    """
    print(f"\n{SEPARATOR_MINOR}")
    print("1. BASIC TABLE RENDERING")
    print(SEPARATOR_MINOR)

    data = [
        ["Alice", 24, "Berlin"],
        ["Bob", 19, "Munich"],
        ["Charlie", 31, "Hamburg"]
    ]
    headers = ["Name", "Age", "City"]

    print("\nSimple 2D list with headers (default grid theme):\n")
    print(render_table(data, headers=headers))


def demo_all_themes() -> None:
    """
    Demonstrate all 4 available themes with identical data.

    Shows grid, fancy_grid, minimal, and psql themes side-by-side
    with same data to compare styling.
    """
    print(f"\n{SEPARATOR_MINOR}")
    print("2. ALL FOUR THEMES")
    print(SEPARATOR_MINOR)

    data = [
        ["Alice", 24, "Berlin"],
        ["Bob", 19, "Munich"],
        ["Charlie", 31, "Hamburg"]
    ]
    headers = ["Name", "Age", "City"]

    for theme_name in ["grid", "fancy_grid", "minimal", "psql"]:
        print(f"\nTheme: {theme_name.upper()}")
        print(render_table(data, headers=headers, theme=theme_name))


def demo_column_alignment() -> None:
    """
    Demonstrate all column alignment types.

    Shows left, right, center, and decimal alignments with
    appropriate sample data for each type.
    """
    print(f"\n{SEPARATOR_MINOR}")
    print("3. COLUMN ALIGNMENT EXAMPLES")
    print(SEPARATOR_MINOR)

    data = [
        ["Product A", 1234, "Center Text", 98.567],
        ["Product B", 567, "More Text", 42.123],
        ["Product C", 89012, "Centered", 156.890]
    ]
    headers = ["Name (left)", "Amount (right)", "Description (center)", "Score (decimal)"]
    specs = ["left:15", "right:12", "center:16", "decimal:12"]

    print("\nColumn alignment with specified widths:\n")
    print(render_table(data, headers=headers, column_specs=specs, theme="grid"))


def demo_column_specs() -> None:
    """
    Demonstrate column specification format.

    Shows the "alignment:width[:decimals[:unit]]" format with
    various examples including decimals and unit suffixes.
    """
    print(f"\n{SEPARATOR_MINOR}")
    print("4. COLUMN SPECIFICATION FORMAT")
    print(SEPARATOR_MINOR)

    print("\nFormat: 'alignment:width[:decimals[:unit]]'")
    print("  - alignment: left, right, center, decimal")
    print("  - width: column width in characters")
    print("  - decimals: (optional) decimal places for numeric values")
    print("  - unit: (optional) suffix to append (e.g., %, EUR, ms)")

    data = [
        ["Feature 1", 1234567, 24.5, 145],
        ["Feature 2", 567890, 18.3, 89],
        ["Feature 3", 2345678, 31.7, 203]
    ]
    headers = ["Feature", "Revenue", "Margin", "Time"]
    specs = [
        "left:15",           # Left-aligned, 15 chars
        "right:12",          # Right-aligned, 12 chars
        "decimal:10:1:%",    # Decimal, 10 chars, 1 decimal, % suffix
        "decimal:10:0:ms"    # Decimal, 10 chars, 0 decimals, ms suffix
    ]

    print("\nExample with mixed alignments and decimals:\n")
    print(render_table(data, headers=headers, column_specs=specs, theme="grid"))


def demo_financial_data() -> None:
    """
    Demonstrate real financial/KPI data rendering.

    Shows practical example with financial metrics including
    values with units (EUR, %, ms) appended to numbers.
    """
    print(f"\n{SEPARATOR_MINOR}")
    print("5. FINANCIAL DATA EXAMPLE (Real KPI Data)")
    print(SEPARATOR_MINOR)

    data = [
        ["Revenue", 1234567.89],
        ["Operating Cost", 456789.23],
        ["Profit Margin", 24.5],
        ["EBITDA", 789012.45],
        ["Response Time", 145],
        ["Error Rate", 0.25]
    ]
    headers = ["KPI", "Value"]
    specs = [
        "left:25",           # KPI names left-aligned
        "decimal:15:2:EUR"   # Values with EUR suffix, 2 decimals
    ]

    print("\nKPI Report with Units:\n")
    print(render_table(data, headers=headers, column_specs=specs, theme="grid"))


def demo_dataframe() -> None:
    """
    Demonstrate pandas DataFrame support.

    Shows rendering DataFrame with and without index using
    render_dataframe() function.
    """
    if not HAS_PANDAS:
        print(f"\n{SEPARATOR_MINOR}")
        print("6. DATAFRAME SUPPORT - SKIPPED (pandas not installed)")
        print(SEPARATOR_MINOR)
        return

    print(f"\n{SEPARATOR_MINOR}")
    print("6. PANDAS DATAFRAME SUPPORT")
    print(SEPARATOR_MINOR)

    df = pd.DataFrame({
        "Name": ["Alice", "Bob", "Charlie"],
        "Score": [95.5, 87.3, 92.1],
        "Grade": ["A", "B", "A"]
    })

    print("\nDataFrame without index:\n")
    print(render_dataframe(df, theme="grid"))

    print("\n\nDataFrame with index:\n")
    print(render_dataframe(df, showindex=True, theme="grid"))


def demo_ansi_colors() -> None:
    """
    Demonstrate ANSI color code preservation in tables.

    Shows that ANSI escape codes (color, formatting) don't break
    alignment or column width calculations.
    """
    print(f"\n{SEPARATOR_MINOR}")
    print("7. ANSI COLOR SUPPORT")
    print(SEPARATOR_MINOR)

    # ANSI color codes
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RESET = "\033[0m"

    data = [
        [f"{RED}Error{RESET}", 15],
        [f"{GREEN}Success{RESET}", 92],
        [f"{YELLOW}Warning{RESET}", 8]
    ]
    headers = ["Status", "Count"]
    specs = ["left:15", "right:8"]

    print("\nTable with color-coded status cells:\n")
    print(render_table(data, headers=headers, column_specs=specs, theme="grid"))


def demo_stock_splits() -> None:
    """
    Demonstrate stock split tracking example.

    Real-world example from design specification showing stock
    split data with multiple alignment types and decimal places.
    """
    print(f"\n{SEPARATOR_MINOR}")
    print("8. STOCK SPLITS EXAMPLE (Real-World Use Case)")
    print(SEPARATOR_MINOR)

    data = [
        ["AAPL", "2024-05-14", 2.0000, 192.53, 192.53, 192.53, "Regular", "Planned"],
        ["TSLA", "2024-06-10", 3.0000, 243.50, 245.00, 242.75, "Special", "Executed"],
        ["NVDA", "2024-03-20", 10.0000, 875.04, 873.00, 879.50, "Regular", "Pending"]
    ]
    headers = ["Symbol", "Date", "Factor", "Close[-1]", "Expected", "Close[0]", "Type", "Status"]
    specs = [
        "right:12",       # Symbol
        "left:10",        # Date
        "decimal:10:4",   # Factor (4 decimals)
        "decimal:10:2",   # Close[-1] (2 decimals)
        "decimal:10:2",   # Expected (2 decimals)
        "decimal:10:2",   # Close[0] (2 decimals)
        "left:16",        # Type
        "right:10"        # Status
    ]

    print("\nStock Split Tracking Table:\n")
    print(render_table(data, headers=headers, column_specs=specs, theme="fancy_grid"))


def demo_backward_compatibility() -> None:
    """
    Demonstrate backward compatibility wrapper.

    Shows how tabulate_compat() function provides drop-in
    replacement for original tabulate() library.
    """
    print(f"\n{SEPARATOR_MINOR}")
    print("9. BACKWARD COMPATIBILITY (tabulate_compat wrapper)")
    print(SEPARATOR_MINOR)

    data = [
        ["Alice", 24, 92.5],
        ["Bob", 19, 87.3],
        ["Charlie", 31, 95.1]
    ]
    headers = ["Name", "Age", "Score"]
    colalign = ("left", "right", "decimal")

    print("\nUsing tabulate_compat() with colalign parameter:\n")
    print(tabulate_compat(data, headers=headers, tablefmt="grid", colalign=colalign))

    print("\n\nUsing tabulate_compat() with psql format:\n")
    print(tabulate_compat(data, headers=headers, tablefmt="psql", colalign=colalign))


def demo_complex_example() -> None:
    """
    Demonstrate complex table combining multiple features.

    Shows combined use of different alignments, decimal places,
    units, and the psql theme in a real-world financial data example.
    Features stock split tracking with price validation mismatch detection.
    """
    print(f"\n{SEPARATOR_MINOR}")
    print("10. COMPLEX MIXED EXAMPLE (Price Validation Problems)")
    print(SEPARATOR_MINOR)

    data = [
        ["1NBA.XETRA", "2008-11-25", 1.5996, 17.60, 11.00, 12.25, "Price Mismatch", 6.90],
        ["1U1.XETRA", "1999-07-20", 12.0000, 147.99, 12.33, 13.70, "Price Mismatch", 6.20],
        ["2BTC.XETRA", "2021-04-12", 14.0000, 244.22, 17.44, 18.00, "Price Mismatch", 8.60],
        ["2INV.XETRA", "2021-01-28", 0.1111, 1.82, 16.38, 1.82, "Price Mismatch", 89.00],
        ["7V0.XETRA", "2025-09-18", 4.0000, 23.40, 5.85, 8.00, "Price Mismatch", 35.00],
        ["AAQ1.XETRA", "2020-10-29", 0.1000, 0.28, 2.76, 2.62, "Price Mismatch", 9.70]
    ]
    headers = ["Symbol", "Date", "Factor", "Close[-1]", "Expected", "Close[0]", "Type", "Details"]
    specs = [
        "right:12",       # Symbol
        "left:10",        # Date
        "decimal:8:4",    # Factor (4 decimals)
        "decimal:8:2",    # Close[-1] (2 decimals)
        "decimal:8:2",    # Expected (2 decimals)
        "decimal:8:2",    # Close[0] (2 decimals)
        "left:16",        # Type
        "decimal:8:2:%"   # Details error percentage
    ]

    print("\nPrice validation problems with mixed alignments and precision:\n")
    print(render_table(data, headers=headers, column_specs=specs, theme="psql"))


def main() -> None:
    """
    Run all demo sections in sequence.

    Demonstrates all features of table_renderer module with
    practical examples and clear section labels.
    """
    print(SEPARATOR_MAJOR)
    print("TABLE_RENDERER COMPREHENSIVE DEMO")
    print(SEPARATOR_MAJOR)

    demo_basic_table()
    demo_all_themes()
    demo_column_alignment()
    demo_column_specs()
    demo_financial_data()
    demo_dataframe()
    demo_ansi_colors()
    demo_stock_splits()
    demo_backward_compatibility()
    demo_complex_example()

    print(f"\n{SEPARATOR_MAJOR}")
    print("DEMO COMPLETE")
    print(SEPARATOR_MAJOR)
    print()


# =============================================================================
# MAIN EXECUTION
# =============================================================================
if __name__ == "__main__":
    main()
