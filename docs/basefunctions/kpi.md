# basefunctions.kpi

Protocol-based KPI collection with recursive provider support and history tracking.

**Version:** 1.2
**Updated:** 2026-01-17
**Python:** >= 3.9

---

## Overview

**Purpose:** Collect Key Performance Indicators from hierarchical structures using protocol-based duck typing.

**Key Features:**
- Protocol-based architecture (no inheritance required)
- Recursive collection from nested providers
- Time-series history tracking
- Category-based filtering (business vs technical KPIs)
- Pandas DataFrame export with lazy import

**Use Cases:**
- Trading strategy metrics collection
- Portfolio performance tracking
- System health monitoring
- Multi-level analytics

---

## KPI Naming Convention

**4-Level Structure:**
```
{category}.{package}.{subpackage}.{kpi_name}
```

**Components:**
- **Category:** `business` | `technical`
  - `business` - Business-relevant metrics (trading performance, P&L, ROI)
  - `technical` - Technical/system metrics (execution time, memory usage, API calls)
- **Package:** Package name (e.g., `portfoliofunctions`, `backtester`)
- **Subpackage:** Subpackage name (minus allowed, e.g., `business-metrics`, `returns`)
- **KPI Name:** ONLY underscores, NO minus! (e.g., `win_rate`, `total_realized_pnl`)

**Naming Rules:**
- Category prefix required for filtering
- Package and subpackage match code structure
- **CRITICAL:** KPI name MUST use underscores (_), NEVER minus (-)
- Subpackage names CAN use minus (-)

**Examples:**
```python
# Correct ✅
kpis['business.portfoliofunctions.business-metrics.win_rate']
kpis['business.portfoliofunctions.returns.total_realized_pnl']
kpis['technical.portfoliofunctions.execution.avg_time_ms']
kpis['technical.backtester.performance.memory_usage_mb']

# Wrong ❌
kpis['business.portfoliofunctions.returns.total-realized-pnl']  # Minus in KPI name!
kpis['portfoliofunctions.returns.total_realized_pnl']  # Missing category!
kpis['business.total_realized_pnl']  # Missing package/subpackage!
```

**When to Use:**
- Use 4-level structure for all KPI names in provider implementations
- Category prefix enables `collect_by_category()` filtering
- Package/subpackage provides clear organization and traceability

**Future:**
- Optional validation for underscore rule may be implemented
- Would be a breaking change if enforced
- Currently documentation-based convention

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

**`collect_by_category(provider: KPIProvider, category: str) -> Dict[str, Any]`**
- **Purpose:** Collect only KPIs matching the specified category prefix
- **Params:** `provider` - Root provider | `category` - Category prefix ("business" or "technical")
- **Returns:** Filtered dict with only matching KPIs
- **Example:** `collect_by_category(provider, "business")` → `{"business.profit": 100.0, "business.balance": 1000.0}`

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

#### `export_by_category(history: List[Tuple[datetime, Dict[str, Any]]], category: str) -> pd.DataFrame`

**Purpose:** Export KPI history filtered by category prefix.

**Params:**
- `history` - KPI history from `KPICollector.get_history()`
- `category` - Category prefix to filter ("business" or "technical")

**Returns:** DataFrame with only KPIs matching the category prefix.

**Raises:**
- `ImportError` - If pandas not installed
- `ValueError` - If history is empty or no matching KPIs

**Example:**
```python
# Only business KPIs
df = export_by_category(history, "business")
# Columns: business.profit, business.balance, business.roi
```

#### `export_business_technical_split(history: List[Tuple[datetime, Dict[str, Any]]]) -> Tuple[pd.DataFrame, pd.DataFrame]`

**Purpose:** Export KPI history split into separate business and technical DataFrames.

**Params:**
- `history` - KPI history from `KPICollector.get_history()`

**Returns:** Tuple of `(business_df, technical_df)` with separated KPIs.

**Raises:**
- `ImportError` - If pandas not installed
- `ValueError` - If history is empty

**Example:**
```python
business_df, technical_df = export_business_technical_split(history)
# business_df: business.profit, business.balance, etc.
# technical_df: technical.execution_time_ms, technical.memory_mb, etc.
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

### KPI Grouping Utilities

#### `group_kpis_by_name(kpis: dict[str, Any]) -> dict[str, Any]`

**Purpose:** Transform flat KPI dictionary with dot-separated names into nested hierarchical structure.

**Key Feature:** Preserves insertion order of keys (Python 3.7+ dict behavior) - critical for consistent output in exports and reports.

**Params:**
- `kpis` - Flat dictionary with dot-separated keys (e.g., `{"package.subpackage.kpi": 1.0}`)

**Returns:** Nested dictionary structure (e.g., `{"package": {"subpackage": {"kpi": 1.0}}}`)

**Use Cases:**
- Hierarchical visualization of KPIs
- Category-based grouping for exports
- JSON/YAML export with nested structure
- Dashboard rendering with grouped metrics

**Simple Example:**
```python
from basefunctions.kpi import group_kpis_by_name

# Flat KPI structure from collector
kpis = {
    "business.portfoliofunctions.returns.total_pnl": 319.00,
    "business.portfoliofunctions.returns.win_rate": 0.65,
    "technical.backtester.execution.avg_time_ms": 45.2,
}

# Group into nested structure
grouped = group_kpis_by_name(kpis)
# Result:
# {
#     "business": {
#         "portfoliofunctions": {
#             "returns": {
#                 "total_pnl": 319.00,
#                 "win_rate": 0.65
#             }
#         }
#     },
#     "technical": {
#         "backtester": {
#             "execution": {
#                 "avg_time_ms": 45.2
#             }
#         }
#     }
# }
```

**Integration with KPICollector:**
```python
from basefunctions.kpi import KPICollector, group_kpis_by_name
import json

# Collect KPIs
collector = KPICollector()
kpis = collector.collect(my_strategy)

# Example flat KPIs:
# {
#     "business.portfoliofunctions.activity.avg_trade_size": 2660.91,
#     "business.portfoliofunctions.activity.open_trades": 1.00,
#     "business.portfoliofunctions.returns.total_pnl": 319.00,
# }

# Group for hierarchical export
grouped = group_kpis_by_name(kpis)

# Export to JSON with nested structure
with open("kpis.json", "w") as f:
    json.dump(grouped, f, indent=2)

# Result structure:
# {
#   "business": {
#     "portfoliofunctions": {
#       "activity": {
#         "avg_trade_size": 2660.91,
#         "open_trades": 1.00
#       },
#       "returns": {
#         "total_pnl": 319.00
#       }
#     }
#   }
# }
```

**Single-Level Keys:**
```python
# Mixed flat and nested keys
kpis = {
    "total": 100.0,  # Single-level key
    "portfolio.balance": 50.0,  # Multi-level key
}

grouped = group_kpis_by_name(kpis)
# Result: {"total": 100.0, "portfolio": {"balance": 50.0}}
```

**Order Preservation (Critical Feature):**
```python
# Input order preserved in output
kpis = {
    "z.value": 1.0,
    "a.value": 2.0,
    "m.value": 3.0,
}

grouped = group_kpis_by_name(kpis)
# Iterating over grouped preserves z → a → m order
# Important for: consistent exports, reproducible reports, diff-friendly outputs
```

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

### Category-Based Filtering & Export

```python
from basefunctions.kpi import (
    KPICollector,
    export_by_category,
    export_business_technical_split
)

# Create collector
collector = KPICollector()

# Collect KPIs with business/technical categories
kpis = collector.collect_and_store(my_strategy)
# Example: {"business.profit": 100.0, "technical.execution_time_ms": 45.0}

# Collect only business KPIs
business_kpis = collector.collect_by_category(my_strategy, "business")
# Result: {"business.profit": 100.0, "business.balance": 1000.0}

# Export only business KPIs to DataFrame
history = collector.get_history()
business_df = export_by_category(history, "business")
print(business_df)
# Columns: business.profit, business.balance, business.roi

# Export split DataFrames (business vs technical)
business_df, technical_df = export_business_technical_split(history)
print("Business Metrics:", business_df.columns.tolist())
print("Technical Metrics:", technical_df.columns.tolist())
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

## Open Items

### KPI Name Validation (Future Enhancement)

**Status:** Not implemented (documentation-based convention)

**Description:**
Currently, KPI naming convention (4-level structure with underscore-only kpi_name) is enforced via documentation only. Optional validation could be added to ensure:
- Correct 4-level structure
- Valid category (business/technical)
- No minus (-) in kpi_name component

**Impact:** Would be a breaking change if enforced retroactively

**Decision:** KISSS principle - document clearly, implement validation only if naming violations become a problem in production

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
**Updated:** 2026-01-17 14:20
