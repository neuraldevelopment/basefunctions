# KPI - User Documentation

**Package:** basefunctions
**Subpackage:** kpi
**Version:** 0.5.75
**Purpose:** Protocol-based Key Performance Indicator collection and export

---

## Overview

The kpi subpackage provides a flexible system for collecting, managing, and exporting Key Performance Indicators from any object implementing the KPIProvider protocol.

**Key Features:**
- Protocol-based design for duck-typing compatibility
- Recursive collection from hierarchical structures
- Category-based filtering (business/technical)
- Multiple export formats (DataFrame, JSON, formatted tables)
- History tracking with timestamps
- No inheritance required

**Common Use Cases:**
- Collecting metrics from trading systems
- Application performance monitoring
- Business KPI dashboards
- Hierarchical metric aggregation
- Time-series KPI tracking

---

## Public APIs

### KPIProvider Protocol

**Purpose:** Define interface for KPI-providing objects

```python
from basefunctions.protocols import KPIProvider

class MyComponent:
    def get_kpis(self) -> dict[str, float]:
        return {"balance": 1000.0, "profit": 50.0}

    def get_subproviders(self) -> dict[str, KPIProvider] | None:
        return None  # Or return nested providers
```

**When to Implement:**
- Any class that wants to expose metrics
- Components in hierarchical systems
- Application monitoring
- Custom metric sources

**Implementation Example:**

```python
class Portfolio:
    def __init__(self):
        self.balance = 1000.0
        self.positions = []

    def get_kpis(self) -> dict[str, float]:
        """Return current KPI values"""
        return {
            "business.balance": self.balance,
            "business.position_count": len(self.positions),
            "technical.memory_mb": 45.2
        }

    def get_subproviders(self) -> dict[str, "KPIProvider"] | None:
        """Return nested KPI providers"""
        if not self.positions:
            return None

        return {
            f"position_{i}": pos
            for i, pos in enumerate(self.positions)
        }
```

**Important Rules:**
1. `get_kpis()` must return `dict[str, float]`
2. `get_subproviders()` returns `dict[str, KPIProvider]` or `None`
3. Use "business." or "technical." prefixes for category filtering
4. KPI names should be unique within provider

---

### KPICollector

**Purpose:** Collect KPIs from providers recursively

```python
from basefunctions.kpi import KPICollector

collector = KPICollector()
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| None | - | - | No initialization parameters |

**Examples:**

```python
from basefunctions.kpi import KPICollector

# Create collector
collector = KPICollector()

# Collect from provider
kpis = collector.collect(my_provider)

# Collect and store with timestamp
kpis = collector.collect_and_store(my_provider)

# Get history
history = collector.get_history()
```

---

### KPICollector.collect()

**Purpose:** Recursively collect all KPIs from provider

```python
kpis = collector.collect(provider)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `provider` | KPIProvider | - | Root provider to collect from |

**Returns:**
- **Type:** dict[str, Any]
- **Description:** Nested dictionary with KPI values

**Result Structure:**
```python
{
    "balance": 1000.0,                    # Direct KPIs
    "profit": 50.0,
    "portfolio": {                        # Nested subprovider
        "balance": 500.0,
        "position_count": 5
    }
}
```

**Examples:**

```python
# Simple collection
kpis = collector.collect(portfolio)
print(f"Balance: {kpis['balance']}")

# Access nested KPIs
portfolio_balance = kpis['portfolio']['balance']
```

---

### KPICollector.collect_by_category()

**Purpose:** Collect only KPIs matching category prefix

```python
kpis = collector.collect_by_category(provider, "business")
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `provider` | KPIProvider | - | Root provider |
| `category` | Literal["business", "technical"] | - | Category to filter |

**Returns:**
- **Type:** dict[str, Any]
- **Description:** Filtered dictionary with matching KPIs only

**Examples:**

```python
# Get only business KPIs
business_kpis = collector.collect_by_category(provider, "business")
# Returns: {"business.balance": 1000.0, "business.profit": 50.0}

# Get only technical KPIs
tech_kpis = collector.collect_by_category(provider, "technical")
# Returns: {"technical.cpu": 45.2, "technical.memory_mb": 128.5}
```

---

### KPICollector.collect_and_store()

**Purpose:** Collect KPIs and add to history with timestamp

```python
kpis = collector.collect_and_store(provider)
```

**Returns:**
- **Type:** dict[str, Any]
- **Description:** Collected KPI dictionary

**Examples:**

```python
# Collect and store multiple times
for i in range(5):
    collector.collect_and_store(provider)
    time.sleep(1)

# Get history
history = collector.get_history()
print(f"Collected {len(history)} snapshots")
```

---

### KPICollector.get_history()

**Purpose:** Get KPI history, optionally filtered by time

```python
history = collector.get_history(since=None)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `since` | datetime or None | None | Filter entries >= since |

**Returns:**
- **Type:** list[tuple[datetime, dict[str, Any]]]
- **Description:** List of (timestamp, kpis) tuples

**Examples:**

```python
# Get all history
history = collector.get_history()
for timestamp, kpis in history:
    print(f"{timestamp}: {kpis['balance']}")

# Get history since specific time
from datetime import datetime, timedelta
since = datetime.now() - timedelta(hours=1)
recent = collector.get_history(since=since)
```

---

### export_to_dataframe()

**Purpose:** Convert KPI history to pandas DataFrame

```python
from basefunctions.kpi import export_to_dataframe

df = export_to_dataframe(history)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `history` | list[tuple[datetime, dict]] | - | KPI history from collector |
| `include_units_in_columns` | bool | False | Append units to column names |

**Returns:**
- **Type:** pandas.DataFrame
- **Description:** DataFrame with timestamp index and KPI columns

**Examples:**

```python
import pandas as pd
from basefunctions.kpi import export_to_dataframe

# Collect history
for i in range(10):
    collector.collect_and_store(provider)

# Export to DataFrame
df = export_to_dataframe(collector.get_history())

# Analyze
print(df.describe())
print(df['business.balance'].mean())

# Plot
df['business.profit'].plot()
```

---

### print_kpi_table()

**Purpose:** Print formatted KPI table to console

```python
from basefunctions.kpi import print_kpi_table

print_kpi_table(
    kpis,
    filter_pattern=None,
    decimals=2,
    sort_keys=False,
    currency="EUR"
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `kpis` | dict | - | KPI dictionary to display |
| `filter_pattern` | str or None | None | Glob pattern for filtering |
| `decimals` | int | 2 | Decimal places for numbers |
| `sort_keys` | bool | False | Sort KPI names alphabetically |
| `max_table_width` | int | 80 | Maximum table width in characters |
| `currency` | str | "EUR" | Currency symbol to use |

**Examples:**

```python
from basefunctions.kpi import print_kpi_table

# Simple table
print_kpi_table(kpis)

# Filter business KPIs only
print_kpi_table(kpis, filter_pattern="business.*")

# Custom formatting
print_kpi_table(
    kpis,
    decimals=4,
    sort_keys=True,
    currency="USD"
)
```

**Output Example:**
```
┌─────────────────────────────────────────────────────────────────┐
│ PORTFOLIO                                                       │
├────────────────────────────────────┬────────────────────────────┤
│ KPI                                │ Value                      │
├────────────────────────────────────┼────────────────────────────┤
│ balance                            │            1,000.00 EUR    │
│ profit                             │               50.00 EUR    │
│ position_count                     │                   5        │
└────────────────────────────────────┴────────────────────────────┘
```

---

### KPIValue

**Purpose:** Structured KPI value with optional unit

```python
from basefunctions.kpi import KPIValue

# Create KPI value
kpi = KPIValue(value=1000.0, unit="EUR")

# Use in get_kpis()
def get_kpis(self):
    return {
        "balance": KPIValue(1000.0, "EUR"),
        "cpu": KPIValue(45.2, "%")
    }
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `value` | float | - | Numeric value |
| `unit` | str or None | None | Unit symbol (e.g., "EUR", "%") |

---

### Registry Functions

**Purpose:** Manage global KPI provider registry

```python
from basefunctions.kpi import register, get_all_providers, clear

# Register provider
register("portfolio", my_portfolio)

# Get all providers
providers = get_all_providers()

# Clear registry
clear()
```

---

## Usage Examples

### Basic KPI Collection

**Scenario:** Collect metrics from single object

```python
from basefunctions.kpi import KPICollector

class TradingBot:
    def __init__(self):
        self.balance = 10000.0
        self.trades = 42

    def get_kpis(self):
        return {
            "business.balance": self.balance,
            "business.trade_count": self.trades,
            "technical.uptime": 99.9
        }

    def get_subproviders(self):
        return None

# Collect KPIs
bot = TradingBot()
collector = KPICollector()
kpis = collector.collect(bot)

print(f"Balance: {kpis['business.balance']}")
print(f"Trades: {kpis['business.trade_count']}")
```

---

### Hierarchical KPI Collection

**Scenario:** Collect from nested component structure

```python
from basefunctions.kpi import KPICollector

class Position:
    def __init__(self, symbol, quantity):
        self.symbol = symbol
        self.quantity = quantity

    def get_kpis(self):
        return {
            "business.quantity": self.quantity,
            "business.value": self.quantity * 100.0
        }

    def get_subproviders(self):
        return None

class Portfolio:
    def __init__(self):
        self.positions = [
            Position("AAPL", 10),
            Position("GOOGL", 5)
        ]

    def get_kpis(self):
        total_value = sum(p.quantity * 100 for p in self.positions)
        return {
            "business.total_value": total_value,
            "business.position_count": len(self.positions)
        }

    def get_subproviders(self):
        return {
            pos.symbol: pos
            for pos in self.positions
        }

# Collect recursively
portfolio = Portfolio()
collector = KPICollector()
kpis = collector.collect(portfolio)

# Access nested KPIs
print(f"Total value: {kpis['business.total_value']}")
print(f"AAPL quantity: {kpis['AAPL']['business.quantity']}")
print(f"GOOGL value: {kpis['GOOGL']['business.value']}")
```

---

### Category Filtering

**Scenario:** Separate business and technical metrics

```python
from basefunctions.kpi import KPICollector

# Collect by category
collector = KPICollector()

business = collector.collect_by_category(provider, "business")
technical = collector.collect_by_category(provider, "technical")

# Export to separate reports
print("=== Business KPIs ===")
for name, value in business.items():
    print(f"{name}: {value}")

print("\n=== Technical KPIs ===")
for name, value in technical.items():
    print(f"{name}: {value}")
```

---

### Time-Series Analysis

**Scenario:** Track KPIs over time and analyze

```python
from basefunctions.kpi import KPICollector, export_to_dataframe
import time

collector = KPICollector()

# Collect every second for 10 seconds
for i in range(10):
    collector.collect_and_store(provider)
    time.sleep(1)

# Export to DataFrame
df = export_to_dataframe(collector.get_history())

# Analyze trends
print("Balance statistics:")
print(df['business.balance'].describe())

# Calculate changes
df['balance_change'] = df['business.balance'].diff()
print(f"Max increase: {df['balance_change'].max()}")

# Plot
df['business.balance'].plot(title='Balance Over Time')
```

---

### Formatted Console Output

**Scenario:** Display KPIs in readable table format

```python
from basefunctions.kpi import KPICollector, print_kpi_table

collector = KPICollector()
kpis = collector.collect(portfolio)

# Display all KPIs
print("=== All KPIs ===")
print_kpi_table(kpis)

# Display only business KPIs
print("\n=== Business KPIs ===")
print_kpi_table(kpis, filter_pattern="business.*")

# Custom formatting
print("\n=== Detailed View ===")
print_kpi_table(
    kpis,
    decimals=4,
    sort_keys=True,
    currency="USD"
)
```

---

## Best Practices

### Best Practice 1: Use Category Prefixes

**Why:** Enables filtering and organization

```python
# GOOD
def get_kpis(self):
    return {
        "business.revenue": 1000.0,
        "business.profit": 50.0,
        "technical.cpu": 45.2,
        "technical.memory_mb": 128.5
    }
```

```python
# AVOID
def get_kpis(self):
    return {
        "revenue": 1000.0,  # No category prefix
        "cpu": 45.2
    }
```

---

### Best Practice 2: Return None for No Subproviders

**Why:** Clear intent, avoids empty dict overhead

```python
# GOOD
def get_subproviders(self):
    if not self.children:
        return None
    return {"child": self.child}
```

```python
# AVOID
def get_subproviders(self):
    return {}  # Return None instead
```

---

### Best Practice 3: Use KPIValue for Units

**Why:** Preserves unit information

```python
# GOOD
from basefunctions.kpi import KPIValue

def get_kpis(self):
    return {
        "balance": KPIValue(1000.0, "EUR"),
        "cpu": KPIValue(45.2, "%")
    }
```

---

## Integration Examples

### Integration with ConfigHandler

```python
from basefunctions import ConfigHandler, KPICollector

config = ConfigHandler()
config.load_config_for_package("myapp")

# Get KPI collection settings
interval = config.get("kpi.collection_interval", 60)
enabled = config.get("kpi.enabled", True)

if enabled:
    collector = KPICollector()
    kpis = collector.collect(provider)
```

---

### Integration with Pandas

```python
from basefunctions.kpi import export_to_dataframe
import pandas as pd

# Export to DataFrame
df = export_to_dataframe(collector.get_history())

# Pandas operations
df_resampled = df.resample('1H').mean()
df_rolling = df.rolling(window=10).mean()

# Save to CSV
df.to_csv("kpi_history.csv")
```

---

## FAQ

**Q: Do I need to inherit from a base class?**

A: No. Just implement `get_kpis()` and `get_subproviders()` methods. Protocol-based design.

**Q: Can I use non-numeric values?**

A: No. `get_kpis()` must return `dict[str, float]`. Use KPIValue for unit metadata.

**Q: How deep can the hierarchy go?**

A: Unlimited. Collection is fully recursive.

**Q: Can I filter by custom patterns?**

A: Yes. Use `print_kpi_table(kpis, filter_pattern="my_pattern*")` with glob patterns.

---

## See Also

**Related Subpackages:**
- `protocols` (`docs/basefunctions/protocols.md`) - Protocol definitions
- `utils` (`docs/basefunctions/utils.md`) - Utility functions including table rendering

**System Documentation:**
- `~/.claude/_docs/python/basefunctions.md` - Internal architecture details

---

## Quick Reference

### Imports

```python
# Main classes
from basefunctions.kpi import KPICollector, KPIValue

# Protocol
from basefunctions.protocols import KPIProvider

# Export functions
from basefunctions.kpi import (
    export_to_dataframe,
    print_kpi_table,
    export_by_category
)

# Registry
from basefunctions.kpi import register, get_all_providers, clear
```

### Quick Start

```python
# Step 1: Implement protocol
class MyClass:
    def get_kpis(self):
        return {"metric": 100.0}

    def get_subproviders(self):
        return None

# Step 2: Collect
from basefunctions.kpi import KPICollector
collector = KPICollector()
kpis = collector.collect(MyClass())

# Step 3: Display
from basefunctions.kpi import print_kpi_table
print_kpi_table(kpis)
```

### Cheat Sheet

| Task | Code |
|------|------|
| Implement provider | `def get_kpis(self): return {}` |
| Collect KPIs | `collector.collect(provider)` |
| Filter by category | `collector.collect_by_category(p, "business")` |
| Store with timestamp | `collector.collect_and_store(provider)` |
| Export to DataFrame | `export_to_dataframe(history)` |
| Print table | `print_kpi_table(kpis)` |

---

**Document Version:** 1.0.0
**Last Updated:** 2026-01-29
**Subpackage Version:** 0.5.75
