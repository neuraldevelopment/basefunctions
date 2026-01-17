"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Demo showcasing group_kpis_by_name() functionality - transforming flat
 KPI dictionaries with dot-separated names into nested structures while
 preserving insertion order.
 Log:
 v1.0 : Initial implementation
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
# Standard Library
import json
from typing import Any

# Project modules
from basefunctions.kpi.utils import group_kpis_by_name


# =============================================================================
# FUNCTION DEFINITIONS
# =============================================================================
def print_scenario(
    title: str,
    flat_kpis: dict[str, Any],
    grouped_kpis: dict[str, Any],
) -> None:
    """
    Print a demo scenario with before/after comparison.

    Parameters
    ----------
    title : str
        Scenario title
    flat_kpis : dict[str, Any]
        Original flat KPI dictionary
    grouped_kpis : dict[str, Any]
        Grouped nested KPI dictionary
    """
    print(f"\n{'=' * 80}")
    print(f"SCENARIO: {title}")
    print(f"{'=' * 80}")
    print("\n--- BEFORE (Flat) ---")
    print(json.dumps(flat_kpis, indent=2))
    print("\n--- AFTER (Grouped/Nested) ---")
    print(json.dumps(grouped_kpis, indent=2))


def demo_kpi_grouping() -> None:
    """
    Demonstrate group_kpis_by_name() with various scenarios.

    Scenarios
    ---------
    1. Real-world portfolio KPIs (activity, business_metrics, returns, etc.)
    2. Order preservation (non-alphabetical insertion order)
    3. Mixed single-level and nested KPIs
    4. Deep nesting (3+ levels)
    5. Edge cases (empty dict, single key, no dots)
    """
    print("\n" + "=" * 80)
    print("KPI GROUPING DEMO - group_kpis_by_name()")
    print("=" * 80)
    print("\nPurpose: Transform flat KPI dicts into nested structures")
    print("Key Feature: PRESERVES insertion order (Python 3.7+ dict behavior)")

    # =========================================================================
    # SCENARIO 1: Real-World Portfolio KPIs
    # =========================================================================
    scenario1_flat = {
        "portfoliofunctions.activity.avg_trade_size": 2660.91,
        "portfoliofunctions.activity.open_trades": 1.00,
        "portfoliofunctions.activity.total_trades": 25.00,
        "portfoliofunctions.business_metrics.win_rate": 0.60,
        "portfoliofunctions.business_metrics.profit_factor": 1.85,
        "portfoliofunctions.returns.total_pnl": 319.00,
        "portfoliofunctions.returns.max_drawdown": -156.00,
        "portfoliofunctions.returns.sharpe_ratio": 1.42,
        "portfoliofunctions.risk.volatility": 0.023,
        "portfoliofunctions.risk.var_95": -89.50,
    }
    scenario1_grouped = group_kpis_by_name(scenario1_flat)
    print_scenario(
        "Real-World Portfolio KPIs",
        scenario1_flat,
        scenario1_grouped,
    )

    # =========================================================================
    # SCENARIO 2: Order Preservation (Non-Alphabetical)
    # =========================================================================
    print(
        "\n\n" + "!" * 80 + "\n"
        "CRITICAL: Order preservation demo - keys inserted Z, Y, X (NOT alphabetical)\n"
        "Expected output: performance.z_metric, performance.y_metric, performance.x_metric\n"
        + "!" * 80
    )
    scenario2_flat = {
        "performance.z_metric": 3.0,
        "performance.y_metric": 2.0,
        "performance.x_metric": 1.0,
    }
    scenario2_grouped = group_kpis_by_name(scenario2_flat)
    print_scenario(
        "Order Preservation (Non-Alphabetical Insertion Order)",
        scenario2_flat,
        scenario2_grouped,
    )

    # =========================================================================
    # SCENARIO 3: Mixed Single-Level and Nested KPIs
    # =========================================================================
    scenario3_flat = {
        "total_count": 100,
        "metrics.accuracy": 0.95,
        "metrics.precision": 0.92,
        "status": "active",
        "config.timeout": 30,
    }
    scenario3_grouped = group_kpis_by_name(scenario3_flat)
    print_scenario(
        "Mixed Single-Level and Nested KPIs",
        scenario3_flat,
        scenario3_grouped,
    )

    # =========================================================================
    # SCENARIO 4: Deep Nesting (3+ Levels)
    # =========================================================================
    scenario4_flat = {
        "system.api.rest.get_requests": 1500,
        "system.api.rest.post_requests": 350,
        "system.api.graphql.queries": 890,
        "system.db.postgres.connections": 45,
        "system.db.postgres.queries_per_sec": 230,
        "system.cache.redis.hit_rate": 0.87,
    }
    scenario4_grouped = group_kpis_by_name(scenario4_flat)
    print_scenario(
        "Deep Nesting (3+ Levels)",
        scenario4_flat,
        scenario4_grouped,
    )

    # =========================================================================
    # SCENARIO 5: Edge Cases
    # =========================================================================
    print("\n\n" + "=" * 80)
    print("SCENARIO: Edge Cases")
    print("=" * 80)

    # Empty dict
    edge_empty = {}
    edge_empty_grouped = group_kpis_by_name(edge_empty)
    print("\n--- Edge Case: Empty Dict ---")
    print(f"Input:  {edge_empty}")
    print(f"Output: {edge_empty_grouped}")

    # Single key, no dots
    edge_single = {"total": 42}
    edge_single_grouped = group_kpis_by_name(edge_single)
    print("\n--- Edge Case: Single Key (No Dots) ---")
    print(f"Input:  {edge_single}")
    print(f"Output: {edge_single_grouped}")

    # Multiple single-level keys
    edge_flat = {"a": 1, "b": 2, "c": 3}
    edge_flat_grouped = group_kpis_by_name(edge_flat)
    print("\n--- Edge Case: All Single-Level Keys ---")
    print(f"Input:  {edge_flat}")
    print(f"Output: {edge_flat_grouped}")

    # =========================================================================
    # SUMMARY
    # =========================================================================
    print("\n\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("\nKey Takeaways:")
    print("  1. Flat KPIs with dot-separated names → Nested structures")
    print("  2. Insertion order PRESERVED (Python 3.7+ dict guarantee)")
    print("  3. Single-level keys stay flat (no unnecessary nesting)")
    print("  4. Handles deep nesting (3+ levels) seamlessly")
    print("  5. Edge cases (empty, single key, no dots) handled correctly")
    print("\nUse Case:")
    print("  - KPI collectors produce flat dicts for simplicity")
    print("  - group_kpis_by_name() transforms for JSON export/display")
    print("  - Result: Clean, hierarchical structure for APIs/reports")
    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    demo_kpi_grouping()
