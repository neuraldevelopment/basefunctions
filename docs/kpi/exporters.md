# User Dokumentation: basefunctions.kpi.exporters

**Module:** `basefunctions.kpi.exporters`
**Purpose:** Export KPI metrics to DataFrames and render formatted tables for console output

---

## Quick Summary

The `exporters` module provides functions to visualize and export KPI metrics collected via `KPICollector`. Key capabilities:

- **Console Display:** Professional formatted tables with 2-level grouping (package + subgroup)
- **DataFrame Export:** Convert KPI history to pandas DataFrames for analysis
- **Filtering:** Wildcard patterns and category filtering (business vs technical)
- **Customization:** Currency override, decimal precision, table width control

---

## Quick Start

### 1. Basic Table Display
```python
from basefunctions.kpi.exporters import print_kpi_table

# Get current KPIs from your collector
kpis = collector.get_current_kpis()

# Display formatted table
print_kpi_table(kpis)
```

**Output:**
```
Portfolio KPIs - 4 Metrics
╒═══════════════════╤════════════╤══════╕
│ KPI               │      Value │ Unit │
╞═══════════════════╪════════════╪══════╡
│ ACTIVITY          │            │      │
│   win_rate        │       0.75 │ %    │
│   total_trades    │        150 │      │
│                   │            │      │
│ RETURNS           │            │      │
│   total_pnl       │    1000.00 │ EUR  │
│   win_loss_ratio  │       2.50 │      │
╘═══════════════════╧════════════╧══════╛
```

---

### 2. Export to DataFrame
```python
from basefunctions.kpi.exporters import export_to_dataframe

# Get historical KPI data
history = collector.get_history()

# Convert to pandas DataFrame
df = export_to_dataframe(history)

print(df.head())
```

**Output:**
```
                          business.portfolio.activity.win_rate  business.portfolio.returns.total_pnl
timestamp
2025-01-26 10:00:00                                      0.75                                1000.0
2025-01-26 10:05:00                                      0.78                                1050.0
2025-01-26 10:10:00                                      0.72                                 980.0
```

---

### 3. Filter Business KPIs Only
```python
from basefunctions.kpi.exporters import export_by_category

# Export only business metrics
business_df = export_by_category(history, category="business")

print(f"Business KPIs: {list(business_df.columns)}")
```

---

### 4. Wildcard Filtering
```python
# Show only portfolio metrics
print_kpi_table(
    kpis,
    filter_patterns=["business.portfolio.*"]
)

# Multiple patterns
print_kpi_table(
    kpis,
    filter_patterns=[
        "business.portfolio.activity.*",
        "business.portfolio.returns.*"
    ]
)
```

---

## Common Use Cases

### Use Case 1: Monitoring Dashboard Display
Display all current KPIs in a clean, formatted table for terminal monitoring.

```python
from basefunctions.kpi.exporters import print_kpi_table

# Collect KPIs during application run
collector.record("business.portfolio.activity.win_rate", 0.75, unit="%")
collector.record("business.portfolio.returns.total_pnl", 1000.0, unit="USD")
collector.record("technical.performance.cpu_usage", 45.0, unit="%")

# Display formatted table with custom currency
kpis = collector.get_current_kpis()
print_kpi_table(
    kpis,
    currency="EUR",  # Replace all currency codes with EUR
    decimals=2,
    max_table_width=60
)
```

**When to Use:**
- Real-time monitoring dashboards
- CLI tools with status output
- Debug output during development

---

### Use Case 2: Export Historical Data for Analysis
Convert time-series KPI data to pandas DataFrame for statistical analysis.

```python
from basefunctions.kpi.exporters import export_to_dataframe

# Collect KPIs over time
# ... application runs, KPIs recorded ...

# Export to DataFrame
history = collector.get_history()
df = export_to_dataframe(history)

# Perform analysis
print("\nDescriptive Statistics:")
print(df.describe())

# Plot trends
import matplotlib.pyplot as plt
df.plot(y="business.portfolio.returns.total_pnl", figsize=(10, 5))
plt.title("P&L Trend")
plt.show()
```

**When to Use:**
- Post-run analysis
- Performance trend visualization
- Statistical reporting

---

### Use Case 3: Split Business vs Technical Metrics
Separate business KPIs (revenue, trades) from technical KPIs (CPU, memory) for focused analysis.

```python
from basefunctions.kpi.exporters import export_business_technical_split

# Split into two DataFrames
history = collector.get_history()
business_df, technical_df = export_business_technical_split(history)

# Analyze business metrics
print(f"\nBusiness KPIs ({len(business_df.columns)} columns):")
print(business_df.tail())

# Analyze technical metrics
print(f"\nTechnical KPIs ({len(technical_df.columns)} columns):")
print(technical_df.tail())

# Compare correlation
print("\nBusiness KPI Correlation:")
print(business_df.corr())
```

**When to Use:**
- Separate stakeholder reports (business vs ops teams)
- Different analysis workflows
- Focused optimization (business metrics vs system metrics)

---

### Use Case 4: Custom Filtered Reports
Create focused reports by filtering specific packages or subgroups.

```python
from basefunctions.kpi.exporters import print_kpi_table

# Full KPI set
kpis = collector.get_current_kpis()

# Report 1: Only portfolio activity metrics
print("\n=== PORTFOLIO ACTIVITY REPORT ===")
print_kpi_table(
    kpis,
    filter_patterns=["business.portfolio.activity.*"],
    max_table_width=50
)

# Report 2: All returns metrics across packages
print("\n=== RETURNS REPORT ===")
print_kpi_table(
    kpis,
    filter_patterns=["*.returns.*"],  # Any package, returns subgroup
    max_table_width=50
)

# Report 3: System performance only
print("\n=== SYSTEM PERFORMANCE ===")
print_kpi_table(
    kpis,
    filter_patterns=["technical.*"],
    unit_column=False,  # Compact format
    max_table_width=40
)
```

**When to Use:**
- Multi-audience reporting
- Focused debugging
- Executive summaries

---

## Parameter Guide

### `print_kpi_table()` Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `kpis` | Dict | *required* | Nested KPI dictionary (e.g., from `get_current_kpis()`) |
| `filter_patterns` | List[str] | None | Wildcard patterns to filter KPIs (e.g., `["business.portfolio.*"]`) |
| `decimals` | int | 2 | Decimal places for float values (integers always show without decimals) |
| `sort_keys` | bool | False | If True, sort packages/subgroups alphabetically. If False, preserve insertion order |
| `table_format` | str | None | Tabulate format (`"grid"`, `"fancy_grid"`, `"simple"`). If None, uses config default |
| `currency` | str | "EUR" | Replace all currency codes (USD, GBP, etc.) with this value |
| `max_table_width` | int | 50 | Maximum total table width in characters |
| `unit_column` | bool | True | If True, use 3-column layout (KPI/Value/Unit). If False, use 2-column (KPI/Value with unit) |

---

### `export_to_dataframe()` Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `history` | List[Tuple] | *required* | KPI history from `KPICollector.get_history()` |
| `include_units_in_columns` | bool | False | If True, append unit suffix to column names (e.g., `"balance_USD"`) |

---

### `export_by_category()` Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `history` | List[Tuple] | *required* | KPI history from `KPICollector.get_history()` |
| `category` | Literal | *required* | `"business"` or `"technical"` - prefix filter |
| `include_units_in_columns` | bool | False | If True, append unit suffix to column names |

---

### `export_business_technical_split()` Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `history` | List[Tuple] | *required* | KPI history from `KPICollector.get_history()` |
| `include_units_in_columns` | bool | False | If True, append unit suffix to column names |

---

## Common Patterns

### Pattern 1: Compact vs Wide Tables
```python
# Compact format (narrow terminal)
print_kpi_table(
    kpis,
    max_table_width=40,
    unit_column=False,  # 2-column mode
    decimals=1
)

# Wide format (detailed report)
print_kpi_table(
    kpis,
    max_table_width=80,
    unit_column=True,  # 3-column mode
    decimals=3
)
```

**Use Case:**
- Compact: Terminal output, logs, narrow screens
- Wide: Reports, dashboards, detailed analysis

---

### Pattern 2: Currency Override
```python
# Default (EUR)
print_kpi_table(kpis)  # Shows "1000 EUR"

# Override to USD
print_kpi_table(kpis, currency="USD")  # Shows "1000 USD"

# Override to CHF
print_kpi_table(kpis, currency="CHF")  # Shows "1000 CHF"
```

**Important:** ALL currency codes (USD, GBP, CHF, etc.) are replaced with the specified currency. This is intentional for consistent reporting.

---

### Pattern 3: Unit Suffixes in DataFrames
```python
# Standard column names (cleaner)
df = export_to_dataframe(history)
# Columns: ["business.portfolio.balance", "business.portfolio.orders"]

# Include unit suffixes (explicit)
df = export_to_dataframe(history, include_units_in_columns=True)
# Columns: ["business.portfolio.balance_USD", "business.portfolio.orders"]
```

**Use Case:**
- Without units: Cleaner for single-unit datasets
- With units: Explicit when mixing currencies/units in analysis

---

### Pattern 4: Sorted vs Insertion Order
```python
# Preserve insertion order (default, recommended)
print_kpi_table(kpis, sort_keys=False)
# Shows: portfolio → backtester → signals (as added)

# Alphabetical sorting
print_kpi_table(kpis, sort_keys=True)
# Shows: backtester → portfolio → signals (A-Z)
```

**Recommendation:** Use `sort_keys=False` (default) to preserve logical grouping. Use `sort_keys=True` only for comparison across runs.

---

## Error Handling

### Empty History
```python
from basefunctions.kpi.exporters import export_to_dataframe

history = []
try:
    df = export_to_dataframe(history)
except ValueError as e:
    print(f"Error: {e}")
    # Output: "Error: History ist leer - keine Daten zum Exportieren"
```

**Resolution:** Ensure KPIs are recorded before exporting. Check `collector.get_history()` is not empty.

---

### Empty Filter Results
```python
from basefunctions.kpi.exporters import print_kpi_table

kpis = collector.get_current_kpis()
print_kpi_table(kpis, filter_patterns=["nonexistent.pattern.*"])
# Output: "No KPIs match filter patterns"
```

**Resolution:** Verify filter patterns match actual KPI keys. Use `print_kpi_table(kpis)` without filters to see all available KPIs.

---

### Missing Pandas
```python
from basefunctions.kpi.exporters import export_to_dataframe

try:
    df = export_to_dataframe(history)
except ImportError as e:
    print(f"Error: {e}")
    # Output: "pandas ist nicht installiert. Installiere mit: pip install pandas"
```

**Resolution:** Install pandas: `pip install pandas`

---

### No KPIs After Filtering
```python
from basefunctions.kpi.exporters import export_by_category

history = collector.get_history()
try:
    df = export_by_category(history, "business")
except ValueError as e:
    print(f"Error: {e}")
    # Output: "Keine KPIs mit Präfix 'business' in History gefunden"
```

**Resolution:** Verify KPIs are recorded with correct category prefix (e.g., `"business.portfolio.*"`).

---

## Advanced Tips

### Tip 1: Custom Table Formats
```python
from basefunctions.kpi.exporters import print_kpi_table

# Professional report (fancy grid)
print_kpi_table(kpis, table_format="fancy_grid")

# Simple ASCII (log files)
print_kpi_table(kpis, table_format="simple")

# Plain text (minimal)
print_kpi_table(kpis, table_format="plain")
```

**Available Formats:** `"grid"`, `"fancy_grid"`, `"simple"`, `"plain"`, `"pipe"`, `"rst"`, `"mediawiki"`, `"html"`, `"latex"`

---

### Tip 2: DataFrame Post-Processing
```python
from basefunctions.kpi.exporters import export_to_dataframe

# Export to DataFrame
df = export_to_dataframe(history)

# Add derived columns
df["pnl_per_trade"] = df["business.portfolio.returns.total_pnl"] / df["business.portfolio.activity.total_trades"]

# Resample to hourly averages
df_hourly = df.resample("H").mean()

# Filter time range
df_today = df[df.index.date == pd.Timestamp.now().date()]

# Export to CSV
df.to_csv("kpi_history.csv")
```

---

### Tip 3: Combining Filters
```python
# Multiple wildcard patterns (OR logic)
print_kpi_table(
    kpis,
    filter_patterns=[
        "business.portfolio.activity.*",  # All portfolio activity
        "business.signals.quality.*",     # All signal quality
        "technical.cpu*"                  # CPU-related metrics
    ]
)
```

---

### Tip 4: Dynamic Currency from Config
```python
from basefunctions.config import ConfigManager

# Get currency from config
config = ConfigManager()
reporting_currency = config.get("reporting/currency", "EUR")

# Use in table rendering
print_kpi_table(kpis, currency=reporting_currency)
```

---

### Tip 5: Conditional Formatting in DataFrames
```python
from basefunctions.kpi.exporters import export_to_dataframe

df = export_to_dataframe(history)

# Highlight negative P&L
def highlight_negative(val):
    return "color: red" if val < 0 else ""

styled = df.style.applymap(
    highlight_negative,
    subset=["business.portfolio.returns.total_pnl"]
)

# Display in Jupyter
styled
```

---

## Integration Example

Complete workflow from KPI collection to export:

```python
from basefunctions.kpi import KPICollector
from basefunctions.kpi.exporters import (
    print_kpi_table,
    export_to_dataframe,
    export_business_technical_split
)

# Initialize collector
collector = KPICollector()

# Simulate application recording KPIs
collector.record("business.portfolio.activity.win_rate", 0.75, unit="%")
collector.record("business.portfolio.activity.total_trades", 150)
collector.record("business.portfolio.returns.total_pnl", 1000.0, unit="USD")
collector.record("business.portfolio.returns.win_loss_ratio", 2.5)
collector.record("technical.performance.cpu_usage", 45.0, unit="%")
collector.record("technical.performance.memory_mb", 512.0, unit="MB")

# Display current state
print("\n=== CURRENT KPI STATUS ===")
kpis = collector.get_current_kpis()
print_kpi_table(kpis, currency="EUR", max_table_width=60)

# Filter specific package
print("\n=== PORTFOLIO METRICS ONLY ===")
print_kpi_table(
    kpis,
    filter_patterns=["business.portfolio.*"],
    max_table_width=60
)

# Export historical data (if tracked over time)
history = collector.get_history()
if history:
    # Full DataFrame
    df_all = export_to_dataframe(history)
    print(f"\nTotal KPI columns: {len(df_all.columns)}")

    # Split business vs technical
    business_df, technical_df = export_business_technical_split(history)
    print(f"Business columns: {len(business_df.columns)}")
    print(f"Technical columns: {len(technical_df.columns)}")

    # Save to CSV
    df_all.to_csv("kpi_history.csv")
    print("\nExported to kpi_history.csv")
```

---

**End of User Dokumentation**
