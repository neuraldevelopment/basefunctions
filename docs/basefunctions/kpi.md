# basefunctions.kpi

Protocol-based KPI collection with recursive provider support and history tracking.

**Version:** 1.0
**Updated:** 2026-01-15
**Python:** >= 3.9

---

## Overview

**Purpose:** Collect Key Performance Indicators from hierarchical structures using protocol-based duck typing.

**Key Features:**
- Protocol-based architecture (no inheritance required)
- Recursive collection from nested providers
- Time-series history tracking
- Pandas DataFrame export with lazy import

**Use Cases:**
- Trading strategy metrics collection
- Portfolio performance tracking
- System health monitoring
- Multi-level analytics

---

## Public API

### Protocol

#### `KPIProvider`

**Purpose:** Protocol defining the interface for KPI-providing objects.

**Required Methods:**

**`get_kpis() -> Dict[str, float]`**
- **Purpose:** Return current KPI values
- **Returns:** Dict mapping KPI names to numeric values
- **Example:** `{"balance": 1000.0, "profit": 50.0}`

**`get_subproviders() -> Optional[Dict[str, KPIProvider]]`**
- **Purpose:** Return nested providers for hierarchical collection
- **Returns:** Dict of subprovider names to instances, or `None`
- **Example:** `{"portfolio": PortfolioKPIs(), "risk": RiskKPIs()}`

**Implementation Example:**
```python
class MyStrategy:
    def get_kpis(self) -> Dict[str, float]:
        return {"balance": self.balance, "profit": self.profit}

    def get_subproviders(self) -> Optional[Dict[str, KPIProvider]]:
        return {"portfolio": self.portfolio, "risk": self.risk_manager}
```

---

### Classes

#### `KPICollector`

**Purpose:** Recursive KPI collection with history management.

**Init:**
```python
KPICollector()  # No parameters - starts with empty history
```

**Methods:**

**`collect(provider: KPIProvider) -> Dict[str, Any]`**
- **Purpose:** Recursively collect KPIs from provider and all subproviders
- **Params:** `provider` - Root provider implementing KPIProvider protocol
- **Returns:** Nested dict with KPIs (flat at root, nested for subproviders)
- **Example Output:** `{"balance": 100.0, "portfolio": {"balance": 50.0, "profit": 10.0}}`

**`collect_and_store(provider: KPIProvider) -> Dict[str, Any]`**
- **Purpose:** Collect KPIs and add to history with timestamp
- **Params:** `provider` - Root provider
- **Returns:** The collected KPI dict (same as `collect()`)

**`get_history(since: Optional[datetime] = None) -> List[Tuple[datetime, Dict[str, Any]]]`**
- **Purpose:** Retrieve KPI history, optionally filtered by time
- **Params:** `since` - Only return entries after this timestamp (default: all)
- **Returns:** List of `(timestamp, kpis)` tuples

**`clear_history() -> None`**
- **Purpose:** Clear all stored history

---

### Functions

#### `export_to_dataframe(history: List[Tuple[datetime, Dict[str, Any]]]) -> pd.DataFrame`

**Purpose:** Export KPI history to pandas DataFrame with flattened columns.

**Params:**
- `history` - KPI history from `KPICollector.get_history()`

**Returns:** DataFrame with timestamp index and flattened KPI columns using dot notation.

**Raises:**
- `ImportError` - If pandas not installed
- `ValueError` - If history is empty

**Example Output:**
```
                     balance  portfolio.balance  portfolio.profit
timestamp
2026-01-15 10:00:00   1000.0               50.0              10.0
2026-01-15 11:00:00   1050.0               60.0              15.0
```

#### `register(name: str, provider: KPIProvider) -> None`

**Purpose:** Register KPI provider in global registry for discovery.

**Params:**
- `name` - Unique identifier for provider
- `provider` - Provider instance implementing KPIProvider protocol

**Raises:**
- `ValueError` - If name already registered

#### `get_all_providers() -> Dict[str, KPIProvider]`

**Purpose:** Retrieve all registered KPI providers.

**Returns:** Dict mapping provider names to instances (defensive copy).

#### `clear() -> None`

**Purpose:** Clear registry (testing only).

---

## Usage Patterns

### Basic Usage (90% Case)

```python
from basefunctions.kpi import KPICollector

# Create collector
collector = KPICollector()

# Collect KPIs from provider (must implement KPIProvider protocol)
kpis = collector.collect_and_store(my_strategy)

# Get history
history = collector.get_history()
```

### Advanced Usage: Registry for Multi-Package Collection

```python
from basefunctions.kpi import register, get_all_providers, KPICollector

# Register providers from different packages (e.g., backtester, strategy, portfolio)
register("strategy", my_strategy)
register("portfolio", my_portfolio)
register("backtester", my_backtester)

# Collect KPIs from all registered providers
collector = KPICollector()
all_kpis = {}

for name, provider in get_all_providers().items():
    all_kpis[name] = collector.collect(provider)

# Result: {"strategy": {...}, "portfolio": {...}, "backtester": {...}}
```

### Advanced Usage: History & Export

```python
from basefunctions.kpi import KPICollector, export_to_dataframe
from datetime import datetime, timedelta

# Create collector
collector = KPICollector()

# Collect over time
for i in range(10):
    kpis = collector.collect_and_store(my_strategy)
    time.sleep(60)  # Wait 1 minute

# Get recent history
since = datetime.now() - timedelta(hours=1)
recent = collector.get_history(since=since)

# Export to DataFrame
df = export_to_dataframe(recent)
print(df)

# Clear old data
collector.clear_history()
```

### Protocol Implementation

```python
from typing import Dict, Optional

class TradingStrategy:
    """Example strategy implementing KPIProvider protocol."""

    def __init__(self):
        self.balance = 1000.0
        self.profit = 0.0
        self.portfolio = Portfolio()

    def get_kpis(self) -> Dict[str, float]:
        """Direct KPIs at strategy level."""
        return {
            "balance": self.balance,
            "profit": self.profit,
            "total_trades": float(self.trade_count)
        }

    def get_subproviders(self) -> Optional[Dict[str, "KPIProvider"]]:
        """Nested providers for hierarchical collection."""
        return {
            "portfolio": self.portfolio,
            "risk": self.risk_manager
        }

# Usage - no inheritance required!
collector = KPICollector()
kpis = collector.collect(TradingStrategy())
```

---

## Error Handling

### Custom Exceptions

**None** - Uses standard Python exceptions only.

### Common Errors

**Scenario: Pandas not installed**
- **Exception:** `ImportError`
- **Cause:** `export_to_dataframe()` requires pandas
- **Prevention:** Install pandas: `pip install pandas`

**Scenario: Empty history export**
- **Exception:** `ValueError`
- **Cause:** Called `export_to_dataframe()` with empty history
- **Prevention:** Check history before export: `if history: df = export_to_dataframe(history)`

**Scenario: Non-numeric KPI values**
- **Exception:** `ValueError` (from float() conversion)
- **Cause:** `get_kpis()` returned non-numeric values
- **Prevention:** Ensure all KPI values are convertible to float

---

## Testing

**Location:** `tests/kpi/`

**Run:**
```bash
pytest tests/kpi/
pytest --cov=src/basefunctions/kpi tests/kpi/
```

---

## Related

- [basefunctions System Docs](~/.claude/_docs/python/basefunctions.md) - Technical reference
- [basefunctions.events](events.md) - Event-driven patterns

---

**Generated by:** python_doc_agent v5.0.0
**Updated:** 2026-01-15 10:30
