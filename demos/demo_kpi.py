"""
Demo script for basefunctions.kpi system.

Shows how to:
1. Implement KPIProvider protocol with KPIValue format (value + unit)
2. Create nested provider hierarchies
3. Collect KPIs with KPICollector
4. Use group_kpis_by_name() for nested structures
5. Sort KPIs alphabetically with sort_keys parameter
6. Track history over time
7. Export to DataFrame
"""

import time
from datetime import datetime, timedelta

import basefunctions
from basefunctions.kpi.utils import group_kpis_by_name


# =============================================================================
# Simple Flat Provider
# =============================================================================
class Portfolio(basefunctions.KPIProvider):
    """Simple portfolio with flat KPIs."""

    def __init__(self):
        self.balance = 10000.0
        self.positions = 5
        self.profit = 0.0

    def get_kpis(self):
        return {
            "balance": {"value": self.balance, "unit": "USD"},
            "positions": {"value": float(self.positions), "unit": None},
            "profit": {"value": self.profit, "unit": "USD"}
        }

    def get_subproviders(self):
        return None  # Flat provider

    def update(self, profit_change: float):
        """Simulate trading activity."""
        self.profit += profit_change
        self.balance += profit_change


# =============================================================================
# Risk Management Provider
# =============================================================================
class RiskManager(basefunctions.KPIProvider):
    """Risk management KPIs."""

    def __init__(self):
        self.max_drawdown = -500.0
        self.volatility = 0.15
        self.sharpe_ratio = 1.2

    def get_kpis(self):
        return {
            "max_drawdown": {"value": self.max_drawdown, "unit": "USD"},
            "volatility": {"value": self.volatility, "unit": "%"},
            "sharpe_ratio": {"value": self.sharpe_ratio, "unit": None}
        }

    def get_subproviders(self):
        return None


# =============================================================================
# Signal Engine Provider
# =============================================================================
class SignalEngine(basefunctions.KPIProvider):
    """Signal generation KPIs."""

    def __init__(self):
        self.signals_generated = 0
        self.signals_executed = 0
        self.win_rate = 0.0

    def get_kpis(self):
        return {
            "signals_generated": {"value": float(self.signals_generated), "unit": None},
            "signals_executed": {"value": float(self.signals_executed), "unit": None},
            "win_rate": {"value": self.win_rate, "unit": "%"}
        }

    def get_subproviders(self):
        return None

    def generate_signal(self, executed: bool, won: bool):
        """Simulate signal generation."""
        self.signals_generated += 1
        if executed:
            self.signals_executed += 1
            if won:
                total_wins = int(self.win_rate * (self.signals_executed - 1))
                self.win_rate = (total_wins + 1) / self.signals_executed


# =============================================================================
# Backtester with Nested Providers
# =============================================================================
class Backtester(basefunctions.KPIProvider):
    """Main backtester with nested subproviders."""

    def __init__(self):
        self.total_trades = 0
        self.runtime_seconds = 0.0

        # Nested subproviders
        self.portfolio = Portfolio()
        self.risk_manager = RiskManager()
        self.signal_engine = SignalEngine()

    def get_kpis(self):
        return {
            "total_trades": {"value": float(self.total_trades), "unit": None},
            "runtime_seconds": {"value": self.runtime_seconds, "unit": "s"}
        }

    def get_subproviders(self):
        return {
            "portfolio": self.portfolio,
            "risk": self.risk_manager,
            "signals": self.signal_engine
        }

    def execute_trade(self, profit: float):
        """Simulate trade execution."""
        self.total_trades += 1
        self.portfolio.update(profit)
        self.signal_engine.generate_signal(executed=True, won=profit > 0)


# =============================================================================
# Demo Functions
# =============================================================================
def print_nested_dict(d: dict, indent: int = 0) -> None:
    """
    Pretty print nested dictionary with KPIValue format support.

    Handles both KPIValue dicts {"value": x, "unit": y} and nested structures.
    """
    for key, value in d.items():
        if isinstance(value, dict):
            # Check if it's a KPIValue dict
            if "value" in value and "unit" in value:
                # KPIValue format
                unit_str = f" {value['unit']}" if value.get('unit') else ""
                print("  " * indent + f"{key}: {value['value']:.2f}{unit_str}")
            else:
                # Nested dict
                print("  " * indent + f"{key}:")
                print_nested_dict(value, indent + 1)
        else:
            # Plain value (shouldn't happen with KPIValue format)
            print("  " * indent + f"{key}: {value:.2f}")


def demo_basic_collection() -> None:
    """Demo 1: Basic KPI collection."""
    print("\n" + "="*70)
    print("DEMO 1: Basic KPI Collection")
    print("="*70)

    # Create backtester
    backtester = Backtester()

    # Execute some trades
    backtester.execute_trade(100.0)  # Win
    backtester.execute_trade(-50.0)  # Loss
    backtester.execute_trade(200.0)  # Win

    # Collect KPIs
    collector = basefunctions.KPICollector()
    kpis = collector.collect(backtester)

    print("\nCollected KPIs (Nested Structure):")
    print_nested_dict(kpis)


def demo_kpi_with_units() -> None:
    """Demo 2: KPIValue format with units."""
    print("\n" + "="*70)
    print("DEMO 2: KPIValue Format with Units")
    print("="*70)

    # Create backtester
    backtester = Backtester()
    backtester.execute_trade(500.0)
    backtester.execute_trade(-100.0)

    # Collect KPIs
    collector = basefunctions.KPICollector()
    kpis = collector.collect(backtester)

    print("\nKPIValue Format Examples:")
    print(f"  Balance: {kpis['portfolio']['balance']}")
    print(f"  Volatility: {kpis['risk']['volatility']}")
    print(f"  Win Rate: {kpis['signals']['win_rate']}")

    print("\nAll KPIs with Units:")
    print_nested_dict(kpis)


def demo_grouped_kpis() -> None:
    """Demo 3: KPI grouping with group_kpis_by_name()."""
    print("\n" + "="*70)
    print("DEMO 3: KPI Grouping and Sorting")
    print("="*70)

    # Create flat KPIs (simulating flattened collection)
    flat_kpis = {
        "portfolio.balance": {"value": 10500.0, "unit": "USD"},
        "portfolio.profit": {"value": 500.0, "unit": "USD"},
        "risk.volatility": {"value": 0.15, "unit": "%"},
        "risk.sharpe_ratio": {"value": 1.2, "unit": None},
        "signals.win_rate": {"value": 0.65, "unit": "%"},
    }

    print("\nFlat KPIs (dot-separated names):")
    for key, value in flat_kpis.items():
        unit_str = f" {value['unit']}" if value.get('unit') else ""
        print(f"  {key}: {value['value']:.2f}{unit_str}")

    # Group without sorting (insertion order)
    grouped_unsorted = group_kpis_by_name(flat_kpis, sort_keys=False)
    print("\nGrouped KPIs (Insertion Order - Default):")
    print_nested_dict(grouped_unsorted)

    # Group with sorting
    grouped_sorted = group_kpis_by_name(flat_kpis, sort_keys=True)
    print("\nGrouped KPIs (Alphabetically Sorted):")
    print_nested_dict(grouped_sorted)


def demo_history_tracking() -> None:
    """Demo 4: History tracking over time."""
    print("\n" + "="*70)
    print("DEMO 4: History Tracking Over Time")
    print("="*70)

    # Create backtester and collector
    backtester = Backtester()
    collector = basefunctions.KPICollector()

    # Simulate 5 time periods
    print("\nSimulating 5 trading periods...")
    for i in range(5):
        # Execute some trades
        profit = 100.0 if i % 2 == 0 else -30.0
        backtester.execute_trade(profit)
        backtester.runtime_seconds += 10.0

        # Collect and store
        collector.collect_and_store(backtester)
        print(f"Period {i+1}: Balance = {backtester.portfolio.balance:.2f}")

        time.sleep(0.1)  # Small delay to show time progression

    # Get history
    history = collector.get_history()
    print(f"\nHistory entries collected: {len(history)}")
    print(f"First timestamp: {history[0][0].strftime('%H:%M:%S')}")
    print(f"Last timestamp: {history[-1][0].strftime('%H:%M:%S')}")


def demo_dataframe_export() -> None:
    """Demo 6: Export to pandas DataFrame."""
    print("\n" + "="*70)
    print("DEMO 6: DataFrame Export")
    print("="*70)

    # Create backtester and collector
    backtester = Backtester()
    collector = basefunctions.KPICollector()

    # Collect multiple snapshots
    print("\nCollecting 10 snapshots...")
    for i in range(10):
        profit = 50.0 if i % 3 == 0 else -20.0
        backtester.execute_trade(profit)
        collector.collect_and_store(backtester)
        time.sleep(0.05)

    # Export to DataFrame
    try:
        df = basefunctions.export_to_dataframe(collector.get_history())
        print("\nDataFrame created successfully!")
        print(f"Shape: {df.shape}")
        print("\nColumns (flattened with dot notation):")
        for col in sorted(df.columns):
            print(f"  - {col}")

        print("\nFirst 3 rows:")
        print(df.head(3))

        print("\nBasic statistics:")
        print(df[['portfolio.balance', 'portfolio.profit']].describe())

    except ImportError:
        print("\n⚠️  pandas not installed - skipping DataFrame export")
        print("Install with: pip install pandas")


def demo_filtered_history() -> None:
    """Demo 5: Filtered history access."""
    print("\n" + "="*70)
    print("DEMO 5: Filtered History Access")
    print("="*70)

    # Create backtester and collector
    backtester = Backtester()
    collector = basefunctions.KPICollector()

    # Collect snapshots
    print("\nCollecting snapshots over 5 seconds...")
    for _ in range(10):
        backtester.execute_trade(100.0)
        collector.collect_and_store(backtester)
        time.sleep(0.5)

    # Get recent history only
    now = datetime.now()
    since = now - timedelta(seconds=3)

    all_history = collector.get_history()
    recent_history = collector.get_history(since=since)

    print(f"\nTotal history entries: {len(all_history)}")
    print(f"Recent entries (last 3 seconds): {len(recent_history)}")

    if recent_history:
        print(f"\nRecent balance progression:")
        for ts, kpis in recent_history:
            balance = kpis['portfolio']['balance']['value']
            print(f"  {ts.strftime('%H:%M:%S')}: {balance:.2f}")


# =============================================================================
# Main
# =============================================================================
def main() -> None:
    """Run all demos."""
    print("\n" + "="*70)
    print("basefunctions.kpi - Demo Script")
    print("="*70)
    print("\nNew Features:")
    print("  ✓ KPIValue format with units (USD, %, etc.)")
    print("  ✓ group_kpis_by_name() for nested structures")
    print("  ✓ sort_keys parameter for alphabetical sorting")

    # Run demos
    demo_basic_collection()
    demo_kpi_with_units()
    demo_grouped_kpis()
    demo_history_tracking()
    demo_filtered_history()
    demo_dataframe_export()

    print("\n" + "="*70)
    print("All demos completed!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
