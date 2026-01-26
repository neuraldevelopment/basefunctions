# basefunctions.kpi

KPI collection, DataFrame export, and formatted table printing with currency/unit support

**Version:** 0.5.73
**Updated:** 2026-01-26
**Python:** >= 3.10

---

## Overview

**Purpose:** Provides hierarchical KPI collection from providers, DataFrame export for analysis, and professional table printing with themes, filtering, and currency formatting.

**Key Features:**
- Recursive KPI collection with history tracking
- Export to pandas DataFrame with flattened columns
- Professional table printing with subgroup sections
- Wildcard filtering for selective KPI display
- Currency code replacement for consistent reporting

**Use Cases:**
- Application performance metrics collection
- Business KPI reporting (revenue, orders, profit)
- Technical KPI tracking (CPU, memory, latency)
- Time-series KPI analysis via DataFrame export
- CLI-friendly KPI tables with themes

---

## Public API

### Classes

#### `KPICollector`

**Purpose:** Recursive KPI collection with history tracking

**Init:**
```python
KPICollector()  # No parameters - starts with empty history
```

**Methods:**

**`collect(provider: KPIProvider) -> Dict[str, Any]`**
- **Purpose:** Recursively collect KPIs from provider and all subproviders
- **Params:** `provider` - Root KPIProvider instance
- **Returns:** Nested dictionary with KPIs ({"balance": 100.0, "portfolio": {"profit": 50.0}})

**`collect_and_store(provider: KPIProvider) -> Dict[str, Any]`**
- **Purpose:** Collect KPIs and add to history with timestamp
- **Params:** `provider` - Root KPIProvider instance
- **Returns:** Collected KPI dictionary
- **Side Effect:** Appends (datetime.now(), kpis) to internal history

**`get_history(since: Optional[datetime] = None) -> List[Tuple[datetime, Dict[str, Any]]]`**
- **Purpose:** Get KPI history, optionally filtered by time
- **Params:** `since` - If provided, only return entries with timestamp >= since
- **Returns:** List of (timestamp, kpis) tuples, chronologically ordered

**`clear_history() -> None`**
- **Purpose:** Clear all stored KPI history

**Example:**
```python
from basefunctions.kpi import KPICollector

collector = KPICollector()
kpis = collector.collect_and_store(my_provider)
history = collector.get_history()
print(f"Collected {len(history)} snapshots")
```

---

### Functions

#### `export_to_dataframe(history, include_units_in_columns=False)`

**Purpose:** Export KPI history to pandas DataFrame with flattened columns

**Params:**
- `history` - List[Tuple[datetime, Dict[str, Any]]] from KPICollector.get_history()
- `include_units_in_columns` - If True, append unit suffix to column names (default: False)

**Returns:** pd.DataFrame with timestamp index and flattened KPI columns

**Raises:**
- `ImportError` - pandas is not installed
- `ValueError` - history is empty

**Example:**
```python
from basefunctions.kpi import export_to_dataframe

# Without units in column names
df = export_to_dataframe(history)
# Columns: "portfolio.balance", "portfolio.total_pnl"

# With units in column names
df = export_to_dataframe(history, include_units_in_columns=True)
# Columns: "portfolio.balance_USD", "portfolio.total_pnl_USD"
```

#### `export_by_category(history, category, include_units_in_columns=False)`

**Purpose:** Export KPI history filtered by category prefix ("business" or "technical")

**Params:**
- `history` - List[Tuple[datetime, Dict[str, Any]]]
- `category` - Literal["business", "technical"] - category to filter by
- `include_units_in_columns` - If True, append unit suffix to column names

**Returns:** pd.DataFrame with filtered KPIs only

**Raises:**
- `ImportError` - pandas not installed
- `ValueError` - no KPIs match category

**Example:**
```python
from basefunctions.kpi import export_by_category

# Only business KPIs
business_df = export_by_category(history, "business")
# Columns: "business.revenue", "business.orders"

# Only technical KPIs
technical_df = export_by_category(history, "technical")
# Columns: "technical.cpu_usage", "technical.memory_mb"
```

#### `export_business_technical_split(history, include_units_in_columns=False)`

**Purpose:** Export KPI history split into business and technical DataFrames

**Params:**
- `history` - List[Tuple[datetime, Dict[str, Any]]]
- `include_units_in_columns` - If True, append unit suffix to column names

**Returns:** Tuple[pd.DataFrame, pd.DataFrame] - (business_df, technical_df)

**Raises:**
- `ImportError` - pandas not installed
- `ValueError` - either category has no KPIs

**Example:**
```python
from basefunctions.kpi import export_business_technical_split

business_df, technical_df = export_business_technical_split(history)
print(f"Business: {list(business_df.columns)}")
print(f"Technical: {list(technical_df.columns)}")
```

#### `print_kpi_table(kpis, filter_patterns=None, decimals=2, sort_keys=False, table_format=None, currency="EUR", max_table_width=50, unit_column=True)`

**Purpose:** Print KPIs as formatted table with subgroup sections (2-level grouping by package)

**Params:**
- `kpis` - Dict[str, Any] - KPI dictionary: {"business.package.subgroup.metric": {"value": X, "unit": "Y"}}
- `filter_patterns` - Optional[List[str]] - Wildcard patterns (e.g., ["business.portfolio.*"])
- `decimals` - int - Decimal places for numeric values (default: 2)
- `sort_keys` - bool - Sort packages and subgroups alphabetically (default: False)
- `table_format` - Optional[str] - Tabulate format ("fancy_grid", "grid", "simple"). If None, uses config (default: None)
- `currency` - str - Currency to use for display, replaces all currency codes (default: "EUR")
- `max_table_width` - int - Maximum table width in characters (default: 50)
- `unit_column` - bool - If True, display units in separate column (3 cols: KPI/Value/Unit). If False, integrate units into Value column (2 cols: KPI/Value) (default: True)

**Returns:** None (prints to console)

**Example:**
```python
from basefunctions.kpi import print_kpi_table

kpis = {
    "business": {
        "portfolio": {
            "activity": {"win_rate": {"value": 0.75, "unit": "%"}},
            "returns": {"total_pnl": {"value": 1000.0, "unit": "USD"}}
        }
    }
}

# Basic usage
print_kpi_table(kpis)

# With filtering
print_kpi_table(kpis, filter_patterns=["business.portfolio.activity.*"])

# Custom currency and width
print_kpi_table(kpis, currency="USD", max_table_width=80)

# 2-column layout (integrated units)
print_kpi_table(kpis, unit_column=False)
```

---

## Usage Patterns

### Basic (90% Case)

```python
from basefunctions.kpi import KPICollector, export_to_dataframe

# Collect and store
collector = KPICollector()
kpis = collector.collect_and_store(my_provider)

# Get history
history = collector.get_history()

# Export to DataFrame for analysis
df = export_to_dataframe(history)
print(df.describe())
```

### Advanced - Filtered Export & Table Printing

```python
from basefunctions.kpi import (
    KPICollector,
    export_by_category,
    print_kpi_table
)

# Collect
collector = KPICollector()
kpis = collector.collect_and_store(provider)

# Export business KPIs only
history = collector.get_history()
business_df = export_by_category(history, "business")

# Print technical KPIs with filtering
print_kpi_table(
    kpis,
    filter_patterns=["technical.*.cpu*"],
    currency="USD",
    max_table_width=80
)
```

### Time-Series Analysis

```python
from datetime import datetime, timedelta
from basefunctions.kpi import KPICollector, export_to_dataframe

collector = KPICollector()

# Collect multiple snapshots
for _ in range(10):
    collector.collect_and_store(provider)
    time.sleep(60)

# Get last hour
since = datetime.now() - timedelta(hours=1)
recent_history = collector.get_history(since=since)

# Export and analyze
df = export_to_dataframe(recent_history)
print(df.rolling(window=3).mean())
```

### Wildcard Filtering

```python
from basefunctions.kpi import print_kpi_table

kpis = collector.collect(provider)

# Show only portfolio activity metrics
print_kpi_table(kpis, filter_patterns=["business.portfolio.activity.*"])

# Show all returns across packages
print_kpi_table(kpis, filter_patterns=["*.*.returns.*"])

# Multiple patterns (OR logic)
print_kpi_table(kpis, filter_patterns=[
    "business.portfolio.*",
    "technical.cpu*"
])
```

---

## Parameter Guide

### KPIValue Format

KPIs must use KPIValue format for units:
```python
# Correct
{"value": 1000.0, "unit": "USD"}

# Wrong - unit ignored
1000.0
```

### Table Format Options

**`table_format` Parameter:**
- `"grid"` - Professional grid with box drawing (default)
- `"fancy_grid"` - Double-line grid (best for reports)
- `"minimal"` - No borders, header separator only
- `"psql"` - PostgreSQL-style table

**Config-Based Format:**
```python
from basefunctions import ConfigHandler
config = ConfigHandler()
config.load_config_for_package("basefunctions")
# Now print_kpi_table() uses config theme when table_format=None
print_kpi_table(kpis)  # Uses config theme
```

### Currency Replacement

**CURRENCY_CODES Set:**
- USD, EUR, GBP, CHF, JPY, CNY, CAD, AUD, SEK, NOK, DKK, PLN, CZK, HUF, RUB, INR, BRL, MXN, ZAR, KRW, SGD, HKD, NZD, TRY

**Behavior:**
- Any unit matching CURRENCY_CODES is replaced by `currency` parameter
- Non-currency units (%, ms, MB) are preserved

**Example:**
```python
kpis = {
    "balance": {"value": 1000.0, "unit": "USD"},
    "rate": {"value": 0.75, "unit": "%"}
}

print_kpi_table(kpis, currency="EUR")
# Displays: "1000.00 EUR" and "0.75 %"
```

### Column Layout

**`unit_column=True` (3 columns):**
- KPI | Value | Unit
- Width ratio: 60% / 28% / 12%
- Integers: WITH decimals (consistent)

**`unit_column=False` (2 columns):**
- KPI | Value (with unit)
- Width ratio: 57% / 43%
- Integers: WITHOUT decimals (compact)

---

## Common Patterns

### Pattern 1: Periodic KPI Collection

```python
import time
from basefunctions.kpi import KPICollector

collector = KPICollector()

# Collect every minute
while running:
    collector.collect_and_store(provider)
    time.sleep(60)

# Export at end
df = export_to_dataframe(collector.get_history())
df.to_csv("kpi_history.csv")
```

### Pattern 2: Category-Based Reporting

```python
from basefunctions.kpi import (
    KPICollector,
    export_business_technical_split,
    print_kpi_table
)

collector = KPICollector()
kpis = collector.collect_and_store(provider)

# Print business KPIs
print("\n=== Business KPIs ===")
print_kpi_table(kpis, filter_patterns=["business.*"])

# Print technical KPIs
print("\n=== Technical KPIs ===")
print_kpi_table(kpis, filter_patterns=["technical.*"])
```

### Pattern 3: Package-Specific Tables

```python
from basefunctions.kpi import print_kpi_table

# Show only portfoliofunctions package
print_kpi_table(kpis, filter_patterns=["*.portfoliofunctions.*"])

# Show only backtesterfunctions package
print_kpi_table(kpis, filter_patterns=["*.backtesterfunctions.*"])
```

### Pattern 4: DataFrame Analysis

```python
from basefunctions.kpi import export_to_dataframe
import pandas as pd

df = export_to_dataframe(history)

# Statistics
print(df.describe())

# Correlation
print(df.corr())

# Rolling average
print(df.rolling(window=5).mean())

# Plot
df.plot(figsize=(12, 6))
```

---

## Error Handling

### Custom Exceptions

**`ImportError`**
- **When:** pandas not installed and export_to_dataframe() called
- **Handling:**
```python
try:
    df = export_to_dataframe(history)
except ImportError:
    print("Install pandas: pip install pandas")
    # Fallback to table printing
    print_kpi_table(kpis)
```

**`ValueError`**
- **When:** Empty history or no KPIs match filter
- **Handling:**
```python
try:
    df = export_to_dataframe(history)
except ValueError as e:
    print(f"No data: {e}")
```

### Common Errors

**Scenario: Empty History**
- **Exception:** `ValueError: "History ist leer - keine Daten zum Exportieren"`
- **Cause:** export_to_dataframe() called before any KPIs collected
- **Prevention:** Check history length: `if history: df = export_to_dataframe(history)`

**Scenario: No KPIs Match Filter**
- **Exception:** Prints "No KPIs match filter patterns"
- **Cause:** filter_patterns too restrictive
- **Prevention:** Test patterns: `[k for k in kpis.keys() if fnmatch(k, pattern)]`

**Scenario: Invalid KPIValue Format**
- **Exception:** None (falls back to str(value))
- **Cause:** KPI not in {"value": X, "unit": Y} format
- **Prevention:** Always use KPIValue format for metrics

---

## Testing

**Location:** `tests/kpi/test_*.py`

**Run:**
```bash
pytest tests/kpi/
pytest --cov=src/basefunctions/kpi tests/kpi/
```

**Example:**
```python
def test_export_to_dataframe():
    history = [(datetime.now(), {"balance": {"value": 100.0, "unit": "USD"}})]
    df = export_to_dataframe(history)
    assert "balance" in df.columns
    assert df.iloc[0]["balance"] == 100.0
```

---

## Integration Example

```python
from basefunctions.kpi import KPICollector, export_to_dataframe, print_kpi_table
from basefunctions import ConfigHandler
from datetime import datetime, timedelta
import time

# Setup
config = ConfigHandler()
config.load_config_for_package("myapp")
collector = KPICollector()

# Collect KPIs every minute for 10 minutes
print("Collecting KPIs...")
for i in range(10):
    kpis = collector.collect_and_store(my_provider)
    print(f"Snapshot {i+1}/10 - {len(kpis)} KPIs")
    time.sleep(60)

# Display current KPIs
print("\n=== Current KPIs ===")
print_kpi_table(
    kpis,
    filter_patterns=["business.portfolio.*"],
    currency="USD",
    max_table_width=80
)

# Export to DataFrame for analysis
history = collector.get_history()
df = export_to_dataframe(history)

# Statistics
print("\n=== Statistics ===")
print(df.describe())

# Save to CSV
df.to_csv("kpi_report.csv")
print(f"\nExported {len(df)} snapshots to kpi_report.csv")
```

---

## Related

- [basefunctions.utils](utils.md) - Table rendering functions
- [basefunctions.protocols](../protocols/) - KPIProvider protocol

---

**Generated by:** python_doc_agent v5.0.0
**Updated:** 2026-01-26 15:30
