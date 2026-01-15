"""
Demo script for basefunctions.kpi system.

Shows how to:
1. Implement KPIProvider protocol
2. Create nested provider hierarchies
3. Collect KPIs with KPICollector
4. Track history over time
5. Export to DataFrame
"""

import basefunctions
import time
from datetime import datetime


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
            "balance": self.balance,
            "positions": float(self.positions),
            "profit": self.profit
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
            "max_drawdown": self.max_drawdown,
            "volatility": self.volatility,
            "sharpe_ratio": self.sharpe_ratio
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
            "signals_generated": float(self.signals_generated),
            "signals_executed": float(self.signals_executed),
            "win_rate": self.win_rate
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
            "total_trades": float(self.total_trades),
            "runtime_seconds": self.runtime_seconds
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
def print_nested_dict(d, indent=0):
    """Pretty print nested dictionary."""
    for key, value in d.items():
        if isinstance(value, dict):
            print("  " * indent + f"{key}:")
            print_nested_dict(value, indent + 1)
        else:
            print("  " * indent + f"{key}: {value:.2f}")


def demo_basic_collection():
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


def demo_history_tracking():
    """Demo 2: History tracking over time."""
    print("\n" + "="*70)
    print("DEMO 2: History Tracking Over Time")
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


def demo_dataframe_export():
    """Demo 3: Export to pandas DataFrame."""
    print("\n" + "="*70)
    print("DEMO 3: DataFrame Export")
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


def demo_filtered_history():
    """Demo 4: Filtered history access."""
    print("\n" + "="*70)
    print("DEMO 4: Filtered History Access")
    print("="*70)

    # Create backtester and collector
    backtester = Backtester()
    collector = basefunctions.KPICollector()

    # Collect snapshots
    print("\nCollecting snapshots over 5 seconds...")
    for i in range(10):
        backtester.execute_trade(100.0)
        collector.collect_and_store(backtester)
        time.sleep(0.5)

    # Get recent history only
    from datetime import timedelta
    now = datetime.now()
    since = now - timedelta(seconds=3)

    all_history = collector.get_history()
    recent_history = collector.get_history(since=since)

    print(f"\nTotal history entries: {len(all_history)}")
    print(f"Recent entries (last 3 seconds): {len(recent_history)}")

    if recent_history:
        print(f"\nRecent balance progression:")
        for ts, kpis in recent_history:
            balance = kpis['portfolio']['balance']
            print(f"  {ts.strftime('%H:%M:%S')}: {balance:.2f}")


# =============================================================================
# Main
# =============================================================================
def main():
    """Run all demos."""
    print("\n" + "="*70)
    print("basefunctions.kpi - Demo Script")
    print("="*70)

    # Run demos
    demo_basic_collection()
    demo_history_tracking()
    demo_filtered_history()
    demo_dataframe_export()

    print("\n" + "="*70)
    print("All demos completed!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
