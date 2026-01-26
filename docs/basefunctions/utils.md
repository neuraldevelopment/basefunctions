# basefunctions.utils

Utility functions for table rendering, logging, progress tracking, decorators, and time utilities

**Version:** 0.5.73
**Updated:** 2026-01-26
**Python:** >= 3.10

---

## Overview

**Purpose:** Provides utility functions for professional CLI applications including config-based table rendering, structured logging, progress tracking, decorators, and time utilities.

**Key Features:**
- Professional table rendering with themes (grid, fancy_grid, minimal, psql)
- Config-based theme resolution (reads from ConfigHandler)
- ANSI color support in tables
- Column-level formatting (alignment, width, decimals, units)
- Logging with file/console routing
- Progress tracking (text & alive-progress)
- Decorators (singleton, timer, cache, retry)

**Use Cases:**
- CLI tools with professional table output
- Consistent theme across application via config
- Color-coded CLI output (warnings, errors, sections)
- Performance measurement (function_timer)
- Progress tracking for long-running operations

---

## Public API

### Table Rendering

#### `render_table(data, headers=None, column_specs=None, theme=None, max_width=None)`

**Purpose:** Render table with flexible column formatting and theme support

**Params:**
- `data` - List[List[Any]] - table data as list of rows
- `headers` - List[str], optional - column headers
- `column_specs` - List[str], optional - column format specs: "alignment:width[:decimals[:unit]]"
  - alignment: "left", "right", "center", "decimal"
  - width: integer column width
  - decimals: decimal places for numeric values
  - unit: suffix to append (e.g., "%", "ms")
- `theme` - str, optional - "grid", "fancy_grid", "minimal", "psql" (None = reads from config via get_default_theme())
- `max_width` - int, optional - max table width (distributes evenly across columns)

**Returns:** str - formatted table string

**Raises:**
- `ValueError` - invalid theme or column_specs format

**Example:**
```python
from basefunctions.utils import render_table

data = [["Alice", 24], ["Bob", 19]]
print(render_table(data, headers=["Name", "Age"], theme="grid"))

# With column specs
specs = ["left:10", "decimal:8:2"]
print(render_table(data, headers=["Name", "Score"], column_specs=specs))
```

#### `render_dataframe(df, column_specs=None, theme=None, max_width=None, showindex=False)`

**Purpose:** Render pandas DataFrame as formatted table

**Params:**
- `df` - pandas.DataFrame - DataFrame to render
- `column_specs` - List[str], optional - column format specs (see render_table())
- `theme` - str, optional - table theme
- `max_width` - int, optional - max table width
- `showindex` - bool - include DataFrame index as first column (default: False)

**Returns:** str - formatted table string

**Example:**
```python
from basefunctions.utils import render_dataframe
import pandas as pd

df = pd.DataFrame({"Name": ["Alice", "Bob"], "Age": [24, 19]})
print(render_dataframe(df, theme="fancy_grid"))
```

#### `get_default_theme()`

**Purpose:** Get default table theme from configuration (Single Source of Truth for theme resolution)

**Returns:** str - theme name from config (default: "grid")

**Config Key:** `basefunctions/table_format`

**Theme Resolution Logic:**
1. **Config Loaded:** Reads from ConfigHandler under `basefunctions/table_format`
2. **Config Missing:** Returns default "grid"
3. **Used by:** `render_table()` when `theme=None`, `tabulate_compat()` when `tablefmt=None`, `print_kpi_table()` when `table_format=None`

**Example:**
```python
from basefunctions.utils import get_default_theme, render_table
from basefunctions import ConfigHandler

# Setup - load config with custom theme
config = ConfigHandler()
config.load_config_for_package("basefunctions")
# Config file contains: {"basefunctions": {"table_format": "fancy_grid"}}

# Get theme
theme = get_default_theme()  # Returns "fancy_grid"
print(render_table(data, theme=theme))

# Equivalent - theme=None triggers get_default_theme()
print(render_table(data, theme=None))  # Uses "fancy_grid"
```

**Config Setup:**
```json
{
  "basefunctions": {
    "table_format": "fancy_grid"
  }
}
```
Config location: `~/.neuraldevelopment/packages/<package>/config/config.json` or `~/Code/neuraldev*/<package>/config/config.json`

#### `tabulate_compat(data, headers=None, tablefmt=None, colalign=None, disable_numparse=False, showindex=False)`

**Purpose:** Backward compatibility wrapper for tabulate() function

**Params:**
- `data` - table data or pandas DataFrame
- `headers` - List[str], optional - column headers
- `tablefmt` - str, optional - table format/theme (None = uses config via get_default_theme())
- `colalign` - Tuple[str, ...], optional - column alignments ("left", "right", "center")
- `disable_numparse` - bool - skip numeric formatting (default: False)
- `showindex` - bool - include DataFrame index (default: False)

**Returns:** str - formatted table string

**Example:**
```python
from basefunctions.utils.table_renderer import tabulate_compat as tabulate

data = [["Alice", 24], ["Bob", 19]]
print(tabulate(data, headers=["Name", "Age"], tablefmt="grid"))
```

---

### Logging

**Module:** `basefunctions.utils.logging`

#### `setup_logger(name: str)`

**Purpose:** Setup logger for module
**Params:** `name` - module name (usually __name__)
**Returns:** logging.Logger instance

#### `get_logger(name: str)`

**Purpose:** Get logger instance for module
**Params:** `name` - module name
**Returns:** logging.Logger instance

#### `enable_console()`

**Purpose:** Enable console output for all loggers

#### `disable_console()`

**Purpose:** Disable console output for all loggers

#### `redirect_all_to_file(filepath: str)`

**Purpose:** Redirect all log output to file
**Params:** `filepath` - absolute path to log file

#### `get_standard_log_directory()`

**Purpose:** Get standard log directory path
**Returns:** str - path to log directory

#### `enable_logging()`

**Purpose:** Enable logging globally

**Example:**
```python
from basefunctions.utils.logging import setup_logger, enable_logging

enable_logging()
logger = setup_logger(__name__)
logger.info("Application started")
```

---

### Progress Tracking

**Module:** `basefunctions.utils.progress_tracker`

#### `ProgressTracker`

**Purpose:** Simple text-based progress tracking

**Init:**
```python
ProgressTracker(
    total: int,                   # Total items
    description: str = "Progress" # Description
)
```

**Methods:**
- `update(increment: int = 1)` - Increment progress
- `set_description(desc: str)` - Update description
- `finish()` - Complete progress

**Example:**
```python
from basefunctions.utils import ProgressTracker

tracker = ProgressTracker(total=100, description="Processing")
for i in range(100):
    # Work
    tracker.update(1)
tracker.finish()
```

#### `AliveProgressTracker`

**Purpose:** Advanced progress tracking with alive-progress library

**Init:**
```python
AliveProgressTracker(
    total: int,                   # Total items
    description: str = "Progress" # Description
)
```

**Methods:**
- `update(increment: int = 1)` - Increment progress
- `set_description(desc: str)` - Update description
- `finish()` - Complete progress

**Example:**
```python
from basefunctions.utils import AliveProgressTracker

tracker = AliveProgressTracker(total=1000, description="Downloading")
for chunk in chunks:
    process(chunk)
    tracker.update(len(chunk))
tracker.finish()
```

---

### Decorators

**Module:** `basefunctions.utils.decorators`

#### `@singleton`

**Purpose:** Singleton pattern - ensures only one instance
**Example:**
```python
from basefunctions.utils import singleton

@singleton
class Config:
    def __init__(self):
        self.data = {}
```

#### `@function_timer`

**Purpose:** Measure and log function execution time
**Example:**
```python
from basefunctions.utils import function_timer

@function_timer
def slow_function():
    time.sleep(2)
```

#### `@cache_results`

**Purpose:** Memoization - cache function results
**Example:**
```python
from basefunctions.utils import cache_results

@cache_results
def expensive_computation(x):
    return x ** 2
```

#### `@retry_on_exception`

**Purpose:** Retry function on exception with exponential backoff
**Example:**
```python
from basefunctions.utils import retry_on_exception

@retry_on_exception(max_retries=3, delay=1.0)
def flaky_api_call():
    return requests.get("https://api.example.com")
```

#### `@thread_safe`

**Purpose:** Thread-safe decorator with RLock
**Example:**
```python
from basefunctions.utils import thread_safe

@thread_safe
def update_shared_state():
    global counter
    counter += 1
```

#### `@catch_exceptions`

**Purpose:** Catch and log exceptions, return default value
**Example:**
```python
from basefunctions.utils import catch_exceptions

@catch_exceptions(default=None)
def risky_operation():
    return 1 / 0  # Returns None instead of raising
```

---

### Time Utilities

**Module:** `basefunctions.utils.time_utils`

**Available Functions:**
- `now_utc()` - Current UTC datetime
- `now_local()` - Current local datetime
- `utc_timestamp()` - Current UTC timestamp
- `format_iso(dt)` - Format datetime to ISO 8601
- `parse_iso(s)` - Parse ISO 8601 string
- `to_timezone(dt, tz)` - Convert to timezone
- `datetime_to_str(dt, fmt)` - Format datetime
- `str_to_datetime(s, fmt)` - Parse datetime string
- `timestamp_to_datetime(ts)` - Convert timestamp to datetime
- `datetime_to_timestamp(dt)` - Convert datetime to timestamp

**Example:**
```python
from basefunctions.utils.time_utils import now_utc, format_iso

now = now_utc()
iso_string = format_iso(now)
print(iso_string)  # "2026-01-26T15:30:00Z"
```

---

## Usage Patterns

### Basic Table Rendering (90% Case)

```python
from basefunctions.utils import render_table, get_default_theme

data = [["Alice", 100], ["Bob", 85], ["Charlie", 92]]
headers = ["Name", "Score"]

# Use config theme
print(render_table(data, headers=headers, theme=None))

# Explicit theme
print(render_table(data, headers=headers, theme="fancy_grid"))
```

### Config-Based Theme Resolution

```python
from basefunctions import ConfigHandler
from basefunctions.utils import render_table, get_default_theme

# Setup - load config
config = ConfigHandler()
config.load_config_for_package("myapp")

# Theme automatically reads from config
theme = get_default_theme()  # Reads basefunctions/table_format
print(f"Using theme: {theme}")

# render_table with theme=None uses config
print(render_table(data, headers=headers, theme=None))
```

### Column-Level Formatting

```python
from basefunctions.utils import render_table

data = [["Alice", 95.5, 150], ["Bob", 88.2, 120]]
headers = ["Name", "Score", "Time"]

# Column specs: name (left, 10 chars), score (right, 8 chars, 2 decimals, %), time (right, 6 chars, 0 decimals, ms)
specs = ["left:10", "decimal:8:2:%", "right:6:0:ms"]

print(render_table(data, headers=headers, column_specs=specs))
```

### ANSI Color Support

```python
from basefunctions.utils import render_table

# ANSI codes preserved in render_table
data = [
    ["\033[32mSuccess\033[0m", 100],
    ["\033[31mError\033[0m", 0],
    ["\033[33mWarning\033[0m", 50]
]

print(render_table(data, headers=["Status", "Count"]))
```

---

## Common Patterns

### Pattern 1: Professional CLI Output

```python
from basefunctions.utils import render_table, get_default_theme
from basefunctions import ConfigHandler

# Load config
config = ConfigHandler()
config.load_config_for_package("myapp")

# Consistent theme throughout app
theme = get_default_theme()

# Tables use same theme
print("\n=== Results ===")
print(render_table(results, headers=["ID", "Value"], theme=theme))

print("\n=== Summary ===")
print(render_table(summary, headers=["Metric", "Count"], theme=theme))
```

### Pattern 2: DataFrame Rendering

```python
from basefunctions.utils import render_dataframe
import pandas as pd

df = pd.DataFrame({
    "Symbol": ["AAPL", "GOOGL", "MSFT"],
    "Price": [150.0, 2800.0, 300.0],
    "Change": [2.5, -15.0, 5.0]
})

# With column specs for formatting
specs = ["left:8", "decimal:10:2", "decimal:10:2:%"]
print(render_dataframe(df, column_specs=specs, theme="fancy_grid"))
```

### Pattern 3: Progress Tracking

```python
from basefunctions.utils import AliveProgressTracker

items = range(1000)
tracker = AliveProgressTracker(total=len(items), description="Processing items")

for item in items:
    process(item)
    tracker.update(1)

tracker.finish()
print("Done!")
```

### Pattern 4: Logging Setup

```python
from basefunctions.utils.logging import (
    setup_logger,
    enable_logging,
    redirect_all_to_file
)

# Enable logging
enable_logging()

# Setup logger
logger = setup_logger(__name__)

# Optionally redirect to file
redirect_all_to_file("/path/to/app.log")

# Use logger
logger.info("Application started")
logger.error("Something went wrong")
```

---

## Error Handling

### Custom Exceptions

**`ValueError`**
- **When:** Invalid theme or column_specs format in render_table()
- **Handling:**
```python
try:
    print(render_table(data, theme="invalid"))
except ValueError as e:
    print(f"Invalid theme: {e}")
    print(render_table(data, theme="grid"))  # Fallback
```

### Common Errors

**Scenario: Theme not found**
- **Exception:** `ValueError: Invalid theme 'xyz'. Valid themes: grid, fancy_grid, minimal, psql`
- **Cause:** Invalid theme parameter in render_table()
- **Prevention:** Use get_default_theme() or explicit valid theme

**Scenario: Config not loaded before get_default_theme()**
- **Exception:** None - returns default "grid"
- **Cause:** ConfigHandler not initialized or config file missing
- **Prevention:** Always call ConfigHandler().load_config_for_package() before get_default_theme()

**Scenario: Invalid column_specs format**
- **Exception:** `ValueError: Invalid alignment 'xyz'. Valid: left, right, center, decimal`
- **Cause:** Malformed column_specs string
- **Prevention:** Use format "alignment:width[:decimals[:unit]]"

---

## Testing

**Location:** `tests/utils/test_*.py`

**Run:**
```bash
pytest tests/utils/
pytest --cov=src/basefunctions/utils tests/utils/
```

**Example:**
```python
def test_render_table():
    data = [["Alice", 24], ["Bob", 19]]
    result = render_table(data, headers=["Name", "Age"], theme="grid")
    assert "Alice" in result
    assert "24" in result
    assert "┌" in result  # Grid border
```

---

## Integration Example

```python
from basefunctions import ConfigHandler
from basefunctions.utils import (
    render_table,
    get_default_theme,
    setup_logger,
    enable_logging,
    AliveProgressTracker
)

# Setup
config = ConfigHandler()
config.load_config_for_package("myapp")
enable_logging()
logger = setup_logger(__name__)

# Get theme from config
theme = get_default_theme()
logger.info(f"Using table theme: {theme}")

# Process data
items = range(1000)
tracker = AliveProgressTracker(total=len(items), description="Processing")

results = []
for item in items:
    result = process(item)
    results.append(result)
    tracker.update(1)

tracker.finish()

# Display results
print("\n=== Results ===")
data = [[r["id"], r["value"], r["status"]] for r in results[:10]]
headers = ["ID", "Value", "Status"]
print(render_table(data, headers=headers, theme=theme))

logger.info(f"Processed {len(results)} items")
```

---

## Related

- [basefunctions.kpi](kpi.md) - KPI collection and table printing
- [basefunctions.config](../config/) - ConfigHandler for theme resolution

---

**Generated by:** python_doc_agent v5.0.0
**Updated:** 2026-01-26 15:30
