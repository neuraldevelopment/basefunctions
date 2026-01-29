# Pandas - User Documentation

**Package:** basefunctions
**Subpackage:** pandas
**Version:** 0.5.75
**Purpose:** Extended DataFrame and Series accessors for metadata management

---

## Overview

The pandas subpackage provides custom accessors that extend pandas DataFrame and Series objects with convenient attribute management functionality.

**Key Features:**
- Access DataFrame/Series attributes via `.pf` accessor
- Get, set, check, list, and delete custom attributes
- Validation and error handling
- Seamless integration with pandas API
- No modification to pandas core behavior

**Common Use Cases:**
- Storing metadata with DataFrames
- Tracking data source information
- Preserving processing history
- Custom application-specific flags
- Configuration attached to data

---

## Public APIs

### PandasDataFrame Accessor

**Purpose:** Extended functionality for pandas DataFrames via `.pf` accessor

```python
import pandas as pd
from basefunctions.pandas import PandasDataFrame

# Accessor is automatically registered
df = pd.DataFrame({"A": [1, 2, 3]})

# Use .pf accessor
df.pf.set_attrs("source", "database")
source = df.pf.get_attrs("source")
```

**Available Methods:**
- `get_attrs(name)` - Retrieve attribute value
- `set_attrs(name, value)` - Set attribute value
- `has_attrs(names, abort)` - Check attribute existence
- `list_attrs()` - List all attribute names
- `del_attrs(name)` - Delete attribute

---

### PandasSeries Accessor

**Purpose:** Extended functionality for pandas Series via `.pf` accessor

```python
import pandas as pd
from basefunctions.pandas import PandasSeries

# Accessor is automatically registered
s = pd.Series([1, 2, 3])

# Use .pf accessor
s.pf.set_attrs("unit", "meters")
unit = s.pf.get_attrs("unit")
```

**Available Methods:**
Same as PandasDataFrame accessor

---

### get_attrs()

**Purpose:** Retrieve attribute value by name

```python
value = df.pf.get_attrs("attribute_name")
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | str | - | Attribute name to retrieve |

**Returns:**
- **Type:** Any
- **Description:** Attribute value or None if not found

**Examples:**

```python
import pandas as pd

df = pd.DataFrame({"A": [1, 2, 3]})
df.pf.set_attrs("source", "database")

# Retrieve attribute
source = df.pf.get_attrs("source")
print(source)  # "database"

# Non-existent attribute
missing = df.pf.get_attrs("nonexistent")
print(missing)  # None
```

---

### set_attrs()

**Purpose:** Set attribute to specified value

```python
df.pf.set_attrs("name", value)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | str | - | Attribute name |
| `value` | Any | - | Value to assign |

**Returns:**
- **Type:** Any
- **Description:** The value that was set

**Examples:**

```python
import pandas as pd

df = pd.DataFrame({"A": [1, 2, 3]})

# Set string attribute
df.pf.set_attrs("source", "api")

# Set dict attribute
df.pf.set_attrs("metadata", {"version": 1, "author": "Alice"})

# Set list attribute
df.pf.set_attrs("columns_original", ["A", "B", "C"])
```

---

### has_attrs()

**Purpose:** Check if attributes exist

```python
exists = df.pf.has_attrs(names, abort=True)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `names` | str or list[str] | - | Attribute name(s) to check |
| `abort` | bool | True | Raise error if missing |

**Returns:**
- **Type:** bool
- **Description:** True if all attributes exist

**Raises:**
- `ValueError`: If abort=True and any attribute missing

**Examples:**

```python
import pandas as pd

df = pd.DataFrame({"A": [1, 2, 3]})
df.pf.set_attrs("source", "database")

# Check single attribute
if df.pf.has_attrs("source", abort=False):
    print("Has source attribute")

# Check multiple attributes
df.pf.set_attrs("version", 1)
has_both = df.pf.has_attrs(["source", "version"], abort=False)
print(has_both)  # True

# With abort (raises ValueError if missing)
try:
    df.pf.has_attrs(["source", "missing"], abort=True)
except ValueError as e:
    print(f"Error: {e}")
```

---

### list_attrs()

**Purpose:** List all attribute names

```python
names = df.pf.list_attrs()
```

**Returns:**
- **Type:** list[str]
- **Description:** List of all attribute names

**Examples:**

```python
import pandas as pd

df = pd.DataFrame({"A": [1, 2, 3]})
df.pf.set_attrs("source", "database")
df.pf.set_attrs("version", 1)
df.pf.set_attrs("validated", True)

# List all attributes
attrs = df.pf.list_attrs()
print(attrs)  # ['source', 'version', 'validated']

# Iterate over attributes
for name in df.pf.list_attrs():
    value = df.pf.get_attrs(name)
    print(f"{name}: {value}")
```

---

### del_attrs()

**Purpose:** Delete attribute from object

```python
df.pf.del_attrs("name")
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | str | - | Attribute name to delete |

**Examples:**

```python
import pandas as pd

df = pd.DataFrame({"A": [1, 2, 3]})
df.pf.set_attrs("temp", "value")

# Delete attribute
df.pf.del_attrs("temp")

# Verify deletion
print(df.pf.get_attrs("temp"))  # None
```

---

## Usage Examples

### Store Data Source Information

**Scenario:** Track where data came from

```python
import pandas as pd

# Load data
df = pd.read_csv("data.csv")

# Store source metadata
df.pf.set_attrs("source", "data.csv")
df.pf.set_attrs("load_time", "2026-01-29 10:30:00")
df.pf.set_attrs("loader", "ETL Pipeline v2")

# Later: Check source
print(f"Data from: {df.pf.get_attrs('source')}")
print(f"Loaded at: {df.pf.get_attrs('load_time')}")
```

---

### Track Processing History

**Scenario:** Record transformations applied to data

```python
import pandas as pd

df = pd.DataFrame({
    "name": ["Alice", "Bob", "Charlie"],
    "age": [25, 30, 35]
})

# Initialize processing history
df.pf.set_attrs("history", [])

# Track each transformation
def add_history(df, operation):
    history = df.pf.get_attrs("history")
    history.append(operation)
    df.pf.set_attrs("history", history)

# Apply transformations
df = df[df["age"] > 25]
add_history(df, "filtered: age > 25")

df["age"] = df["age"] + 1
add_history(df, "incremented: age + 1")

# View history
print("Processing history:")
for step in df.pf.get_attrs("history"):
    print(f"  - {step}")
```

---

### Validate Required Attributes

**Scenario:** Ensure DataFrame has required metadata before processing

```python
import pandas as pd

def process_dataframe(df):
    """Process DataFrame requiring specific attributes"""
    # Validate required attributes
    try:
        df.pf.has_attrs(["source", "version", "validated"], abort=True)
    except ValueError as e:
        print(f"Missing attributes: {e}")
        return None

    # Process data
    print(f"Processing data from {df.pf.get_attrs('source')}")
    print(f"Version: {df.pf.get_attrs('version')}")
    return df

# Valid DataFrame
df1 = pd.DataFrame({"A": [1, 2, 3]})
df1.pf.set_attrs("source", "api")
df1.pf.set_attrs("version", 2)
df1.pf.set_attrs("validated", True)
process_dataframe(df1)  # Works

# Invalid DataFrame
df2 = pd.DataFrame({"B": [4, 5, 6]})
df2.pf.set_attrs("source", "file")
process_dataframe(df2)  # Fails - missing attributes
```

---

### Configuration with DataFrame

**Scenario:** Attach configuration to data

```python
import pandas as pd

# Create DataFrame
df = pd.DataFrame({
    "value": [100, 200, 300],
    "category": ["A", "B", "C"]
})

# Attach configuration
config = {
    "currency": "EUR",
    "decimal_places": 2,
    "display_format": "currency",
    "filters": {"min_value": 0, "max_value": 1000}
}
df.pf.set_attrs("config", config)

# Use configuration later
def format_value(df, col):
    cfg = df.pf.get_attrs("config")
    if cfg and cfg.get("display_format") == "currency":
        currency = cfg.get("currency", "USD")
        decimals = cfg.get("decimal_places", 2)
        return df[col].apply(lambda x: f"{x:.{decimals}f} {currency}")
    return df[col]

# Apply formatting
formatted = format_value(df, "value")
print(formatted)
```

---

### Series Unit Tracking

**Scenario:** Store units with Series data

```python
import pandas as pd

# Create Series
temperature = pd.Series([20.5, 21.0, 19.8], name="temperature")

# Set unit
temperature.pf.set_attrs("unit", "°C")
temperature.pf.set_attrs("sensor_id", "TEMP_01")

# Display with unit
unit = temperature.pf.get_attrs("unit")
print(f"Temperature ({unit}): {temperature.values}")

# Convert to Fahrenheit
def celsius_to_fahrenheit(series):
    if series.pf.get_attrs("unit") == "°C":
        converted = series * 9/5 + 32
        converted.pf.set_attrs("unit", "°F")
        converted.pf.set_attrs("converted_from", "°C")
        return converted
    return series

temp_f = celsius_to_fahrenheit(temperature)
print(f"Temperature ({temp_f.pf.get_attrs('unit')}): {temp_f.values}")
```

---

## Best Practices

### Best Practice 1: Use Descriptive Attribute Names

**Why:** Makes code self-documenting

```python
# GOOD
df.pf.set_attrs("data_source_url", "https://api.example.com/data")
df.pf.set_attrs("fetch_timestamp", datetime.now())
df.pf.set_attrs("row_count_original", len(df))
```

```python
# AVOID
df.pf.set_attrs("src", "url")  # Too cryptic
df.pf.set_attrs("time", datetime.now())  # Ambiguous
df.pf.set_attrs("n", 100)  # Unclear meaning
```

---

### Best Practice 2: Check Existence Before Getting

**Why:** Avoid None surprises

```python
# GOOD
if df.pf.has_attrs("source", abort=False):
    source = df.pf.get_attrs("source")
    print(f"Source: {source}")
```

```python
# AVOID
source = df.pf.get_attrs("source")  # Might be None
print(f"Source: {source}")  # Could print "None"
```

---

### Best Practice 3: Document Expected Attributes

**Why:** Clear API contracts

```python
# GOOD
def process_dataframe(df):
    """
    Process DataFrame with required attributes.

    Required attributes:
        - source: str - Data source identifier
        - version: int - Data schema version
        - validated: bool - Data validation flag
    """
    df.pf.has_attrs(["source", "version", "validated"], abort=True)
    # ... process
```

---

## Integration Examples

### Integration with Serialization

```python
import pandas as pd
from basefunctions.io import to_file, from_file

# Create DataFrame with attributes
df = pd.DataFrame({"A": [1, 2, 3]})
df.pf.set_attrs("source", "database")
df.pf.set_attrs("version", 1)

# Save with pickle (preserves attributes)
to_file(df, "data.pkl")

# Load
loaded_df = from_file("data.pkl")
print(loaded_df.pf.get_attrs("source"))  # "database"

# Note: JSON export loses attributes
to_file(df.to_dict(), "data.json")  # Attributes not saved
```

---

### Integration with KPI System

```python
import pandas as pd
from basefunctions.kpi import KPICollector

# DataFrame as KPI provider
class DataFrameKPIProvider:
    def __init__(self, df):
        self.df = df

    def get_kpis(self):
        kpis = {
            "technical.row_count": len(self.df),
            "technical.column_count": len(self.df.columns),
            "technical.memory_mb": self.df.memory_usage(deep=True).sum() / 1024 / 1024
        }

        # Add custom KPIs from attributes
        if self.df.pf.has_attrs("source", abort=False):
            kpis["business.source"] = 1.0  # Indicator

        return kpis

    def get_subproviders(self):
        return None

# Collect KPIs
df = pd.DataFrame({"A": range(1000)})
df.pf.set_attrs("source", "api")

provider = DataFrameKPIProvider(df)
collector = KPICollector()
kpis = collector.collect(provider)
print(kpis)
```

---

## FAQ

**Q: Are attributes preserved when copying DataFrames?**

A: No. Use `df.copy()` and manually copy attributes with `df2.attrs = df1.attrs.copy()`.

**Q: What types of values can be stored?**

A: Any Python object. Pandas uses a dict internally for attrs.

**Q: Can I use this with Dask or other DataFrame libraries?**

A: No. This is specific to pandas DataFrame/Series objects.

**Q: Are attributes preserved when saving to CSV?**

A: No. Only Pickle format preserves attributes. Consider separate metadata file for CSV exports.

---

## See Also

**Related Subpackages:**
- `io` (`docs/basefunctions/io.md`) - Serialization for saving DataFrames
- `kpi` (`docs/basefunctions/kpi.md`) - KPI collection from DataFrames

**System Documentation:**
- `~/.claude/_docs/python/basefunctions.md` - Internal architecture details

**External Resources:**
- [Pandas attrs documentation](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.attrs.html)

---

## Quick Reference

### Imports

```python
import pandas as pd
from basefunctions.pandas import PandasDataFrame, PandasSeries

# Accessor is automatically registered on import
```

### Quick Start

```python
# Step 1: Create DataFrame/Series
import pandas as pd
df = pd.DataFrame({"A": [1, 2, 3]})

# Step 2: Set attribute
df.pf.set_attrs("source", "database")

# Step 3: Get attribute
source = df.pf.get_attrs("source")

# Step 4: Check existence
if df.pf.has_attrs("source", abort=False):
    print("Has source")
```

### Cheat Sheet

| Task | Code |
|------|------|
| Set attribute | `df.pf.set_attrs("name", value)` |
| Get attribute | `df.pf.get_attrs("name")` |
| Check exists | `df.pf.has_attrs("name", abort=False)` |
| List all | `df.pf.list_attrs()` |
| Delete | `df.pf.del_attrs("name")` |
| Same for Series | `series.pf.method()` |

---

**Document Version:** 1.0.0
**Last Updated:** 2026-01-29
**Subpackage Version:** 0.5.75
