# Utils Module Guide

**basefunctions Framework - Utility Components**

---

## Table of Contents

1. [Overview](#overview)
2. [Module Structure](#module-structure)
3. [Table Renderer](#table-renderer)
4. [Decorators](#decorators)
5. [Cache Manager](#cache-manager)
6. [Time Utilities](#time-utilities)
7. [Logging System](#logging-system)
8. [Observer Pattern](#observer-pattern)
9. [Progress Tracking](#progress-tracking)
10. [Demo Runner](#demo-runner)
11. [Best Practices](#best-practices)
12. [API Reference](#api-reference)

---

## Overview

The `utils` module provides essential utility components for the basefunctions framework:

- **Table Renderer**: Complete table rendering with column formatting and themes
- **Decorators**: Function and class decorators for common patterns
- **Cache Manager**: Multi-backend caching system with TTL support
- **Time Utilities**: Timezone-aware datetime handling
- **Logging**: Thread-safe, module-specific logging framework
- **Observer Pattern**: Event-driven component communication
- **Progress Tracking**: Unified progress tracking interface
- **Demo Runner**: Class-based test suite execution

### Design Principles

- **KISSS**: Keep It Simple, Stupid, Straightforward
- **Thread-Safe**: All components support concurrent access
- **Minimal Dependencies**: Uses Python stdlib where possible
- **Flexible Backends**: Support for multiple storage backends
- **Type-Safe**: Full type hints for better IDE support

---

## Module Structure

```
src/basefunctions/utils/
├── table_renderer.py      # Complete table rendering solution
├── decorators.py          # Function/class decorators
├── cache_manager.py       # Multi-backend caching system
├── time_utils.py          # Timezone-aware datetime utilities
├── logging.py             # Module-specific logging framework
├── observer.py            # Observer pattern implementation
├── progress_tracker.py    # Progress tracking interface
├── demo_runner.py         # Test suite execution framework
└── ohlcv_generator.py     # Financial data generation (specialized)
```

---

## Table Renderer

### Overview

Complete table rendering solution with column-level formatting and theme support. Replaces external dependencies (like tabulate) with built-in implementation while providing backward compatibility, ANSI color support, and enhanced formatting capabilities.

**Key Features:**
- Column-level formatting (alignment, width, decimal places, unit suffixes)
- Multiple themes (grid, fancy_grid, minimal, psql)
- ANSI color code support
- pandas DataFrame integration
- Backward compatibility with tabulate() interface
- ConfigHandler integration

### Quick Start

```python
from basefunctions.utils.table_renderer import render_table

data = [["Alice", 24], ["Bob", 19]]
headers = ["Name", "Age"]

print(render_table(data, headers=headers))
```

**Output:**
```
┌──────┬─────┐
│ Name │ Age │
├──────┼─────┤
│ Alice│  24 │
│ Bob  │  19 │
└──────┴─────┘
```

### Column Spec Format

Format: `"alignment:width[:decimals[:unit]]"`

**Alignment options:** `left`, `right`, `center`, `decimal`

**Examples:**
```python
specs = [
    "left:15",              # Left-aligned, 15 chars
    "decimal:10:2:EUR",     # Decimal-aligned, 10 chars, 2 decimals, EUR suffix
    "right:8",              # Right-aligned, 8 chars
    "center:12"             # Center-aligned, 12 chars
]
```

### Functions

#### `render_table(data, headers, column_specs, theme, max_width)`

**Purpose:** Render list-based table data with formatting and theme styling.

**Parameters:**
- `data` - List of rows (each row is list of values)
- `headers` - Column headers (optional)
- `column_specs` - Column format specs as list of strings
- `theme` - Theme name: "grid", "fancy_grid", "minimal", "psql"
- `max_width` - Maximum table width (distributes evenly)

**Returns:** Formatted table string

**Example:**
```python
from basefunctions.utils.table_renderer import render_table

data = [["Widget", 29.99], ["Gadget", 49.50]]
headers = ["Product", "Price"]
specs = ["left:15", "decimal:10:2:EUR"]

print(render_table(data, headers=headers, column_specs=specs))
```

---

#### `render_dataframe(df, column_specs, theme, max_width, showindex)`

**Purpose:** Render pandas DataFrame as formatted table.

**Parameters:**
- `df` - pandas DataFrame
- `column_specs` - Column format specifications
- `theme` - Table theme
- `max_width` - Maximum width
- `showindex` - Include DataFrame index (default: False)

**Example:**
```python
import pandas as pd
from basefunctions.utils.table_renderer import render_dataframe

df = pd.DataFrame({
    "Symbol": ["AAPL", "GOOGL"],
    "Price": [150.25, 2850.75]
})

print(render_dataframe(df))
```

---

#### `tabulate_compat(data, headers, tablefmt, colalign, disable_numparse, showindex)`

**Purpose:** Backward compatibility wrapper for tabulate() function.

**Example:**
```python
from basefunctions.utils.table_renderer import tabulate_compat

data = [["Alice", 1250.50], ["Bob", 980.25]]
result = tabulate_compat(
    data,
    headers=["Name", "Score"],
    tablefmt="grid",
    colalign=("left", "right")
)
print(result)
```

---

#### `get_table_format()`

**Purpose:** Read configured table format from ConfigHandler.

**Returns:** Default theme string (e.g., "grid")

```python
from basefunctions.utils.table_renderer import get_table_format

fmt = get_table_format()  # Returns configured format or "grid" default
```

---

### Themes

**grid** (default) - Unicode box-drawing with borders
```
┌──────┬─────┐
│ Name │ Age │
├──────┼─────┤
│ Alice│  24 │
└──────┴─────┘
```

**fancy_grid** - Thick Unicode with row separators
```
╒══════╤═════╕
│ Name │ Age │
╞══════╪═════╡
│ Alice│  24 │
╘══════╧═════╛
```

**minimal** - Minimal borders, header underline only
```
 Name   Age
 ──────────
 Alice   24
```

**psql** - PostgreSQL-style
```
 Name | Age
------+----
 Alice|  24
```

---

### Common Patterns

**Financial KPI Table:**
```python
from basefunctions.utils.table_renderer import render_table

kpis = [
    ["Revenue", 1250000.50],
    ["Expenses", 850000.25]
]
specs = ["left:15", "decimal:12:2:EUR"]

print(render_table(kpis, headers=["KPI", "Amount"], column_specs=specs))
```

**Status Table with Minimal Theme:**
```python
data = [
    ["Web Server", "Running"],
    ["Database", "Running"],
    ["Cache", "Stopped"]
]
specs = ["left:15", "left:12"]

print(render_table(data, headers=["Service", "Status"], column_specs=specs, theme="minimal"))
```

---

### Performance Notes

- O(n) width calculation with ANSI-aware handling
- Efficient border rendering
- 170+ tests in <1s
- No external dependencies

### Use Cases

- CLI table output with financial data
- Status dashboards
- Data analysis results
- DataFrame display with custom formatting
- Legacy code migration from tabulate

For detailed documentation: See [User Dokumentation](#)

---

## Decorators

### Overview

The `decorators` module provides a clean collection of useful decorators without bloat.

### Available Decorators

#### `@singleton`

Ensures only one instance of a class exists (pickle-safe, thread-safe).

```python
from basefunctions import singleton

@singleton
class ConfigManager:
    def __init__(self):
        self.config = {}

# Always returns the same instance
manager1 = ConfigManager()
manager2 = ConfigManager()
assert manager1 is manager2  # True
```

**Features:**
- Thread-safe using locks
- Pickle-safe implementation
- Returns same instance on repeated calls
- Preserves class name and docstring

**Use Cases:**
- Configuration managers
- Database connection pools
- Event buses
- Resource managers

---

#### `@function_timer`

Measures and logs execution time of a function.

```python
from basefunctions import function_timer

@function_timer
def expensive_operation():
    # Do something time-consuming
    return result

# Logs: "runtime of expensive_operation: 0.12345678 seconds"
```

**Features:**
- Uses `time.perf_counter()` for high precision
- Logs to basefunctions logger
- Minimal overhead
- Returns function result unchanged

**Use Cases:**
- Performance monitoring
- Identifying bottlenecks
- Debugging slow operations
- Profiling production code

---

#### `@retry_on_exception`

Retries a function if specified exceptions are raised.

```python
from basefunctions import retry_on_exception
import requests

@retry_on_exception(retries=3, delay=1, exceptions=(requests.RequestException,))
def fetch_data(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

# Retries up to 3 times with 1 second delay on RequestException
data = fetch_data("https://api.example.com/data")
```

**Parameters:**
- `retries` (int): Number of retry attempts (default: 3)
- `delay` (int/float): Delay in seconds between retries (default: 1)
- `exceptions` (tuple): Exception types to catch (default: `(Exception,)`)

**Features:**
- Logs each retry attempt
- Raises exception after exhausting retries
- Configurable delay between attempts
- Selective exception handling

**Use Cases:**
- Network requests
- Database operations
- File I/O operations
- External API calls

---

#### `@cache_results`

Caches function results to avoid redundant computations (uses `lru_cache`).

```python
from basefunctions import cache_results

@cache_results
def fibonacci(n):
    if n < 2:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# First call computes, subsequent calls return cached result
result = fibonacci(100)  # Fast!
```

**Features:**
- Unlimited cache size (`maxsize=None`)
- Based on Python's `functools.lru_cache`
- Arguments must be hashable
- Thread-safe

**Use Cases:**
- Expensive computations
- Recursive functions
- Data transformations
- API responses

**Note:** For more advanced caching, use `CacheManager` (see [Cache Manager](#cache-manager)).

---

#### `@thread_safe`

Makes a function thread-safe using a lock.

```python
from basefunctions import thread_safe

@thread_safe
def update_counter():
    global counter
    counter += 1
    return counter

# Safe to call from multiple threads
```

**Features:**
- Uses `threading.Lock`
- Ensures exclusive access
- Minimal overhead
- Each decorated function gets its own lock

**Use Cases:**
- Updating shared state
- File writes
- Resource allocation
- Counter increments

---

#### `@catch_exceptions`

Catches and logs exceptions without crashing.

```python
from basefunctions import catch_exceptions

@catch_exceptions
def risky_operation():
    # Might raise exception
    result = 10 / 0
    return result

# Returns None instead of crashing, logs error
result = risky_operation()
```

**Features:**
- Logs exception with function name
- Returns None on exception
- Prevents crashes
- Uses basefunctions logger

**Use Cases:**
- Background tasks
- Event handlers
- Callbacks
- Non-critical operations

**Warning:** Use sparingly - don't hide important errors!

---

#### `@suppress`

Suppresses specified exceptions (no logging).

```python
from basefunctions import suppress

@suppress(FileNotFoundError, PermissionError)
def try_delete_file(path):
    os.remove(path)

# Silently ignores FileNotFoundError and PermissionError
try_delete_file("/path/to/file")
```

**Parameters:**
- `*exceptions`: Exception types to suppress

**Features:**
- Selective exception suppression
- Logs suppression to DEBUG level
- Returns None on suppressed exception

**Use Cases:**
- Cleanup operations
- Optional operations
- Best-effort operations

**Warning:** Use very carefully - silent failures can be dangerous!

---

#### `@profile_memory`

Profiles and logs memory usage of a function.

```python
from basefunctions import profile_memory

@profile_memory
def memory_intensive_operation():
    data = [i for i in range(1000000)]
    return data

# Logs: "memory_intensive_operation used 12345.6KB, peaked at 23456.7KB"
```

**Features:**
- Uses `tracemalloc` module
- Logs current and peak memory usage
- Minimal overhead
- Automatic cleanup

**Use Cases:**
- Memory profiling
- Leak detection
- Optimization
- Resource monitoring

---

#### `@warn_if_slow`

Logs a warning if function execution exceeds threshold.

```python
from basefunctions import warn_if_slow

@warn_if_slow(threshold=0.5)  # 500ms
def api_call():
    # Should be fast
    return requests.get(url).json()

# Warns: "api_call took 0.75s (limit: 0.50s)" if too slow
```

**Parameters:**
- `threshold` (float): Time limit in seconds

**Features:**
- Non-intrusive monitoring
- Configurable threshold
- Only warns on slow execution
- Returns result unchanged

**Use Cases:**
- SLA monitoring
- Performance alerts
- Response time tracking
- Production monitoring

---

#### `@assert_non_null_args`

Asserts that no arguments are None.

```python
from basefunctions import assert_non_null_args

@assert_non_null_args
def process_data(data, config):
    # Guaranteed data and config are not None
    return data.process(config)

# Raises ValueError if any argument is None
process_data(data, None)  # ValueError: None value detected
```

**Features:**
- Checks both positional and keyword arguments
- Raises `ValueError` with clear message
- Early validation
- Zero overhead for valid calls

**Use Cases:**
- Input validation
- API boundaries
- Critical functions
- Type safety

---

#### `@log_to_file`

Redirects function logging to specific file.

```python
from basefunctions import log_to_file, get_logger

@log_to_file("debug_functions.log", level="DEBUG")
def debug_function():
    logger = get_logger(__name__)
    logger.debug("This goes to debug_functions.log")
    logger.info("This too")
    return result

# All logs from this function go to separate file
```

**Parameters:**
- `file` (str): Log file path
- `level` (str): Log level for this function (default: "DEBUG")

**Features:**
- Function-specific log files
- Separate log levels
- Automatic logger setup
- Logs function entry/exit

**Use Cases:**
- Debugging specific functions
- Audit trails
- Compliance logging
- Performance analysis

---

#### `@auto_property`

Creates property with automatic getter/setter.

```python
from basefunctions import auto_property

class Person:
    @auto_property
    def name(self):
        pass  # Implementation not needed

    @auto_property
    def age(self):
        pass

# Automatic getter/setter using _name and _age
person = Person()
person.name = "Alice"  # Sets _name
print(person.name)     # Gets _name
```

**Features:**
- Automatic private attribute creation
- No boilerplate code
- Property-based access
- Type-safe

**Use Cases:**
- Data classes
- Configuration objects
- DTO/VO patterns
- Reducing boilerplate

---

### Decorator Combinations

Decorators can be combined for powerful effects:

```python
from basefunctions import (
    singleton,
    function_timer,
    retry_on_exception,
    catch_exceptions
)

@singleton
class APIClient:

    @function_timer
    @retry_on_exception(retries=3, delay=1)
    def fetch_data(self, endpoint):
        response = requests.get(endpoint)
        response.raise_for_status()
        return response.json()

    @catch_exceptions
    def optional_operation(self):
        # Won't crash on failure
        return self._risky_operation()
```

**Best Practice Order:**
1. Class decorators (`@singleton`) first
2. Error handling (`@catch_exceptions`, `@retry_on_exception`)
3. Monitoring (`@function_timer`, `@profile_memory`)
4. Optimization (`@cache_results`)

---

## Cache Manager

### Overview

Unified caching framework with multiple backend support, TTL management, and statistics tracking.

### Architecture

```
CacheManager (High-level API)
    ↓
CacheBackend (Abstract interface)
    ↓
├── MemoryBackend (In-memory cache with LRU)
├── DatabaseBackend (Persistent DB cache)
├── FileBackend (File-system cache)
└── MultiLevelBackend (L1 → L2 → L3 cache hierarchy)
```

### Quick Start

```python
from basefunctions import get_cache

# Memory cache (default)
cache = get_cache()

# Set value with 1 hour TTL
cache.set("user:123", {"name": "Alice", "age": 30}, ttl=3600)

# Get value
user = cache.get("user:123")

# Get or compute
user = cache.get_or_set("user:456", lambda: fetch_user_from_db(456))

# Check existence
if cache.exists("user:123"):
    print("User cached")

# Delete key
cache.delete("user:123")

# Clear all
cache.clear()

# Get statistics
stats = cache.stats()
print(f"Hit rate: {stats['hit_rate_percent']}%")
```

### Backend Types

#### Memory Backend

Fast in-memory cache with LRU eviction.

```python
cache = get_cache("memory", max_size=1000)
```

**Features:**
- Lightning fast (no I/O)
- Automatic LRU eviction
- TTL support
- Thread-safe
- Expired entry cleanup

**Configuration:**
- `max_size` (int): Maximum entries (default: 1000)

**Use Cases:**
- Session storage
- API response caching
- Temporary data
- High-frequency reads

**Limitations:**
- Lost on process restart
- Not shared across processes
- Memory consumption

---

#### Database Backend

Persistent cache using basefunctions.Db.

```python
cache = get_cache("database", instance_name="local", database_name="cache_db")
```

**Features:**
- Persistent across restarts
- Supports PostgreSQL, MySQL, SQLite
- Automatic table creation
- TTL with database timestamps
- Transaction support

**Configuration:**
- `instance_name` (str): Database instance name
- `database_name` (str): Database name

**Use Cases:**
- Long-term caching
- Shared cache across processes
- Audit trails
- Persistent sessions

**Requirements:**
- basefunctions.Db configured
- Database access

---

#### File Backend

File-system based cache.

```python
cache = get_cache("file", cache_dir="/tmp/my_cache")
```

**Features:**
- Persistent across restarts
- No database required
- Automatic directory creation
- MD5 key hashing
- Pickle serialization

**Configuration:**
- `cache_dir` (str): Cache directory path (default: "/tmp/basefunctions_cache")

**Use Cases:**
- Simple persistence
- No database available
- File-based workflows
- Development/testing

**Limitations:**
- Slower than memory
- File system overhead
- Limited pattern matching

---

#### Multi-Level Backend

Hierarchical cache (L1 → L2 → L3).

```python
cache = get_cache("multi", backends=[
    ("memory", {"max_size": 100}),           # L1: Fast memory
    ("file", {"cache_dir": "/tmp/cache"}),   # L2: File persistence
    ("database", {"instance_name": "local", "database_name": "cache"})  # L3: Database
])
```

**Features:**
- Cache promotion (L2 → L1)
- Automatic fallback
- Best of all backends
- Configurable levels

**How It Works:**
1. Check L1 (memory) - fastest
2. If miss, check L2 (file)
3. If miss, check L3 (database)
4. On hit, promote to higher levels
5. On set, write to all levels

**Use Cases:**
- Production systems
- High-performance requirements
- Balanced speed/persistence
- Large datasets

---

### Advanced Features

#### TTL Management

```python
# Set with 1 hour TTL
cache.set("key", "value", ttl=3600)

# Set with no expiration (permanent)
cache.set("permanent_key", "value", ttl=0)

# Update TTL for existing key
cache.expire("key", ttl=7200)  # Extend to 2 hours

# Get remaining TTL
remaining = cache.ttl("key")
print(f"Expires in {remaining} seconds")
```

#### Pattern-Based Operations

```python
# Store multiple related keys
cache.set("user:123:profile", profile_data)
cache.set("user:123:settings", settings_data)
cache.set("user:456:profile", profile_data_2)

# Get all user keys
user_keys = cache.keys("user:*")

# Get specific user keys
user_123_keys = cache.keys("user:123:*")

# Clear pattern
cache.clear("user:123:*")  # Remove all user 123 data
```

#### Statistics and Monitoring

```python
# Get detailed statistics
stats = cache.stats()
print(f"Total requests: {stats['total_requests']}")
print(f"Hits: {stats['hits']}")
print(f"Misses: {stats['misses']}")
print(f"Hit rate: {stats['hit_rate_percent']}%")
print(f"Cache size: {stats['size']} entries")
print(f"Sets: {stats['sets']}")
print(f"Deletes: {stats['deletes']}")
print(f"Clears: {stats['clears']}")
```

#### Get-or-Set Pattern

```python
# Compute expensive value only if not cached
def compute_expensive_value():
    # Heavy computation or DB query
    return expensive_operation()

# Cached for 1 hour
value = cache.get_or_set("expensive_key", compute_expensive_value, ttl=3600)

# Lambda version
user = cache.get_or_set(
    f"user:{user_id}",
    lambda: db.query_one("SELECT * FROM users WHERE id = ?", (user_id,)),
    ttl=3600
)
```

#### Cache Invalidation

```python
# Delete specific key
cache.delete("user:123")

# Invalidate pattern
cache.invalidate_pattern("user:123:*")

# Clear all
cache.clear()

# Clear specific pattern
cache.clear("session:*")
```

---

### Custom Backend

Create your own cache backend:

```python
from basefunctions.utils.cache_manager import CacheBackend, CacheEntry, CacheFactory

class RedisBackend(CacheBackend):
    def __init__(self, host="localhost", port=6379):
        super().__init__()
        import redis
        self.redis = redis.Redis(host=host, port=port)

    def _get_raw(self, key: str) -> Optional[CacheEntry]:
        data = self.redis.get(key)
        if data is None:
            return None
        return pickle.loads(data)

    def _set_raw(self, key: str, entry: CacheEntry) -> None:
        data = pickle.dumps(entry)
        if entry.expires_at:
            ttl = int(entry.expires_at - time.time())
            self.redis.setex(key, ttl, data)
        else:
            self.redis.set(key, data)

    def _delete_raw(self, key: str) -> bool:
        return bool(self.redis.delete(key))

    def _clear_raw(self) -> int:
        return self.redis.flushdb()

    def _keys_raw(self) -> List[str]:
        return [k.decode() for k in self.redis.keys()]

# Register custom backend
factory = CacheFactory()
factory.register_backend("redis", RedisBackend)

# Use custom backend
cache = get_cache("redis", host="localhost", port=6379)
```

---

### Performance Considerations

**Memory Backend:**
- Fastest: ~0.001ms per operation
- Best for: High-frequency access, small datasets (<100K entries)

**File Backend:**
- Medium: ~1-10ms per operation
- Best for: Persistence without DB, moderate frequency

**Database Backend:**
- Slower: ~10-50ms per operation
- Best for: Large datasets, shared cache, ACID requirements

**Multi-Level Backend:**
- Adaptive: Fast for L1 hits, slower for misses
- Best for: Production, balanced requirements

**Optimization Tips:**
1. Use memory backend for hot data
2. Set appropriate TTL to prevent bloat
3. Monitor hit rates and adjust strategy
4. Use multi-level for best of both worlds
5. Clear expired entries periodically

---

## Time Utilities

### Overview

Timezone-aware datetime handling utilities built on Python 3.9+ `zoneinfo`.

### Core Functions

#### Current Time

```python
from basefunctions import now_utc, now_local, utc_timestamp

# Current UTC datetime
utc_now = now_utc()
print(utc_now)  # 2025-01-15 14:30:00+00:00

# Current local datetime (system timezone)
local_now = now_local()
print(local_now)  # 2025-01-15 15:30:00+01:00

# Current local datetime in specific timezone
berlin_now = now_local("Europe/Berlin")
tokyo_now = now_local("Asia/Tokyo")

# POSIX timestamp
ts = utc_timestamp()
print(ts)  # 1705327800.123456
```

#### Timezone Conversion

```python
from basefunctions import to_timezone

# Convert datetime to different timezone
utc_time = now_utc()
berlin_time = to_timezone(utc_time, "Europe/Berlin")
ny_time = to_timezone(utc_time, "America/New_York")

print(f"UTC:    {utc_time}")
print(f"Berlin: {berlin_time}")
print(f"NY:     {ny_time}")
```

#### ISO 8601 Formatting

```python
from basefunctions import format_iso, parse_iso

# Format datetime to ISO 8601
dt = now_utc()
iso_str = format_iso(dt)
print(iso_str)  # "2025-01-15T14:30:00+00:00"

# Parse ISO 8601 string
dt = parse_iso("2025-01-15T14:30:00+00:00")

# Parse and convert to specific timezone
berlin_dt = parse_iso("2025-01-15T14:30:00+00:00", tz_str="Europe/Berlin")
```

#### Custom Formatting

```python
from basefunctions import datetime_to_str, str_to_datetime

# Format datetime with custom format
dt = now_utc()
formatted = datetime_to_str(dt, "%Y-%m-%d %H:%M:%S")
print(formatted)  # "2025-01-15 14:30:00"

# Parse datetime from custom format
dt = str_to_datetime("2025-01-15 14:30:00", "%Y-%m-%d %H:%M:%S")
```

#### Timestamp Conversion

```python
from basefunctions import timestamp_to_datetime, datetime_to_timestamp

# POSIX timestamp to UTC datetime
ts = 1705327800.0
dt = timestamp_to_datetime(ts)
print(dt)  # 2025-01-15 14:30:00+00:00

# Datetime to POSIX timestamp
dt = now_utc()
ts = datetime_to_timestamp(dt)
print(ts)  # 1705327800.123456
```

### Common Patterns

#### API Response Timestamps

```python
from basefunctions import format_iso, now_utc

def create_api_response(data):
    return {
        "data": data,
        "timestamp": format_iso(now_utc()),
        "server_time": datetime_to_timestamp(now_utc())
    }

response = create_api_response({"user_id": 123})
# {
#     "data": {"user_id": 123},
#     "timestamp": "2025-01-15T14:30:00+00:00",
#     "server_time": 1705327800.123456
# }
```

#### Multi-Timezone Support

```python
from basefunctions import now_utc, to_timezone

def get_current_times():
    utc = now_utc()
    return {
        "utc": format_iso(utc),
        "berlin": format_iso(to_timezone(utc, "Europe/Berlin")),
        "new_york": format_iso(to_timezone(utc, "America/New_York")),
        "tokyo": format_iso(to_timezone(utc, "Asia/Tokyo")),
        "sydney": format_iso(to_timezone(utc, "Australia/Sydney"))
    }
```

#### Log Timestamps

```python
from basefunctions import now_utc, datetime_to_str

def log_with_timestamp(message):
    timestamp = datetime_to_str(now_utc(), "%Y-%m-%d %H:%M:%S UTC")
    print(f"[{timestamp}] {message}")

log_with_timestamp("Application started")
# [2025-01-15 14:30:00 UTC] Application started
```

#### Duration Calculations

```python
from basefunctions import now_utc
from datetime import timedelta

start_time = now_utc()
# ... do work ...
end_time = now_utc()

duration = end_time - start_time
print(f"Elapsed: {duration.total_seconds():.2f} seconds")

# Schedule future task
future_time = now_utc() + timedelta(hours=1)
print(f"Task scheduled for: {format_iso(future_time)}")
```

### Requirements

- Python 3.9+ (for `zoneinfo`)
- Standard library only

**Note:** On Python < 3.9, timezone functions will raise `ImportError`.

---

## Logging System

### Overview

Thread-safe, module-specific logging framework with console/file control.

**Key Features:**
- Silent by default (no spam)
- Module-specific control
- Thread-safe
- File logging support
- Runtime reconfiguration
- Global and per-module console control

For detailed documentation, see: **[LOGGING_USAGE_GUIDE.md](./LOGGING_USAGE_GUIDE.md)**

### Quick Reference

```python
from basefunctions import setup_logger, get_logger

# Enable logging for module
setup_logger(__name__, level="DEBUG", file="debug.log")

# Get logger instance
logger = get_logger(__name__)

# Log messages
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical message")

# Enable console output globally
from basefunctions import enable_console, disable_console

enable_console(level="INFO")  # Show INFO+ on console
disable_console()             # Turn off console

# Module-specific console control
from basefunctions import configure_module_logging

configure_module_logging(
    "basefunctions.http",
    level="DEBUG",
    console=True,           # Force console ON
    console_level="WARNING" # Only show WARNING+ on console
)
```

---

## Observer Pattern

### Overview

Classic Observer pattern for component communication without tight coupling.

### Components

#### Observer Interface

```python
from basefunctions.utils.observer import Observer

class MyObserver(Observer):
    def notify(self, message, *args, **kwargs):
        print(f"Received: {message}")
        # Handle event
```

#### Observable Base Class

```python
from basefunctions.utils.observer import Observable

class DataSource(Observable):
    def __init__(self):
        super().__init__()
        self.data = []

    def add_data(self, item):
        self.data.append(item)
        # Notify observers of "data_added" event
        self.notify_observers("data_added", item)

    def clear_data(self):
        self.data.clear()
        # Notify observers of "data_cleared" event
        self.notify_observers("data_cleared", len(self.data))
```

### Usage Example

```python
from basefunctions.utils.observer import Observer, Observable

# Create observer
class DataLogger(Observer):
    def notify(self, message, *args, **kwargs):
        print(f"[LOG] {message}: {args}")

class DataValidator(Observer):
    def notify(self, message, *args, **kwargs):
        if message == "data_added":
            item = args[0]
            if item < 0:
                print(f"Warning: Negative value {item}")

# Create observable
source = DataSource()

# Attach observers
logger = DataLogger()
validator = DataValidator()

source.attach_observer_for_event("data_added", logger)
source.attach_observer_for_event("data_added", validator)
source.attach_observer_for_event("data_cleared", logger)

# Trigger events
source.add_data(42)    # Both observers notified
source.add_data(-5)    # Both observers notified (validator warns)
source.clear_data()    # Logger notified

# Detach observer
source.detach_observer_for_event("data_added", logger)
```

### API Reference

#### `Observable.attach_observer_for_event(event_type, observer)`

Attach observer for specific event type.

**Parameters:**
- `event_type` (str): Event identifier
- `observer` (Observer): Observer instance

**Raises:**
- `TypeError`: If observer is not an Observer instance

#### `Observable.detach_observer_for_event(event_type, observer)`

Detach observer from specific event type.

**Parameters:**
- `event_type` (str): Event identifier
- `observer` (Observer): Observer instance

#### `Observable.notify_observers(event_type, message, *args, **kwargs)`

Notify all observers for specific event type.

**Parameters:**
- `event_type` (str): Event identifier
- `message` (Any): Message to send
- `*args`: Additional positional arguments
- `**kwargs`: Additional keyword arguments

### Use Cases

- **Model-View separation**: Update UI when data changes
- **Plugin systems**: Notify plugins of application events
- **Logging**: Centralized event logging
- **Validation**: Validate data on changes
- **Metrics**: Track application events
- **Notifications**: Send alerts on specific events

### Observer vs EventBus

**Use Observer when:**
- Simple 1-to-many communication
- Direct object relationships
- Synchronous notifications
- Lightweight requirements

**Use EventBus when:**
- Complex event routing
- Async/threaded processing
- Priority/retry/timeout needed
- System-wide events

---

## Progress Tracking

### Overview

Unified interface for progress tracking with pluggable backends.

### Interface

```python
from basefunctions.utils.progress_tracker import ProgressTracker

class ProgressTracker(ABC):
    def progress(self, n: int = 1) -> None:
        """Advance progress by n steps."""
        pass

    def close(self) -> None:
        """Close progress tracker and cleanup."""
        pass

    def __enter__(self):
        """Context manager support."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup."""
        self.close()
```

### AliveProgressTracker

```python
from basefunctions.utils.progress_tracker import AliveProgressTracker

# Known total
with AliveProgressTracker(total=100, desc="Processing") as progress:
    for i in range(100):
        # Do work
        process_item(i)
        # Update progress
        progress.progress(1)

# Unknown total (shows counter)
with AliveProgressTracker(desc="Downloading") as progress:
    while data := download_chunk():
        process_chunk(data)
        progress.progress(1)

# Batch progress
with AliveProgressTracker(total=1000) as progress:
    for batch in batches:
        process_batch(batch)
        progress.progress(len(batch))  # Advance by batch size
```

**Features:**
- Thread-safe
- Auto-cleanup with context manager
- Unknown total support
- Batch updates
- Console progress bar

**Requirements:**
- `pip install alive-progress`

**Use Cases:**
- Long-running operations
- Batch processing
- File downloads
- Data migration
- Import/export

### Custom Tracker

```python
from basefunctions.utils.progress_tracker import ProgressTracker

class LogProgressTracker(ProgressTracker):
    def __init__(self, total=None, desc="Processing"):
        self.total = total
        self.desc = desc
        self.current = 0

    def progress(self, n=1):
        self.current += n
        if self.total:
            pct = (self.current / self.total) * 100
            print(f"{self.desc}: {self.current}/{self.total} ({pct:.1f}%)")
        else:
            print(f"{self.desc}: {self.current}")

    def close(self):
        print(f"{self.desc}: Complete!")

# Use custom tracker
with LogProgressTracker(total=100, desc="Migration") as progress:
    for item in items:
        migrate_item(item)
        progress.progress()
```

---

## Demo Runner

### Overview

Class-based test suite execution framework with automatic running and structured output.

### Quick Start

```python
from basefunctions.utils.demo_runner import run, test

@run("MathTests")
class TestMath:
    def setup(self):
        """Run before tests (optional)."""
        self.calculator = Calculator()

    @test("addition")
    def test_add(self):
        result = self.calculator.add(2, 3)
        assert result == 5, f"Expected 5, got {result}"

    @test("division")
    def test_divide(self):
        result = self.calculator.divide(10, 2)
        assert result == 5.0

    @test("division_by_zero")
    def test_divide_by_zero(self):
        try:
            self.calculator.divide(10, 0)
            assert False, "Should have raised ZeroDivisionError"
        except ZeroDivisionError:
            pass  # Expected

    def teardown(self):
        """Run after tests (optional)."""
        self.calculator = None

# Tests run automatically on script exit
# Output:
# +---------------------------+----------+-----------+
# | Test Name                 | Status   | Duration  |
# +===========================+==========+===========+
# | MathTests.setup           | PASSED   | 0.001s    |
# | MathTests.addition        | PASSED   | 0.002s    |
# | MathTests.division        | PASSED   | 0.001s    |
# | MathTests.division_by_zero| PASSED   | 0.001s    |
# | MathTests.teardown        | PASSED   | 0.000s    |
# +---------------------------+----------+-----------+
#
# Summary: 5/5 passed • 0.005s total
```

### Decorators

#### `@run(suite_name)`

Register test class for automatic execution.

```python
@run("DatabaseTests")
class TestDatabase:
    @test("connection")
    def test_connect(self):
        db = Database()
        assert db.connect()
```

#### `@test(test_name)`

Mark method as test case.

```python
@test("user_creation")
def test_create_user(self):
    user = create_user("alice")
    assert user.name == "alice"
```

### Lifecycle Methods

#### `setup(self)`

Runs before all tests (optional).

```python
def setup(self):
    self.db = Database()
    self.db.connect()
    self.db.create_tables()
```

#### `teardown(self)`

Runs after all tests (optional).

```python
def teardown(self):
    self.db.drop_tables()
    self.db.disconnect()
```

### Multiple Test Suites

```python
@run("Unit Tests")
class UnitTests:
    @test("fast_operation")
    def test_fast(self):
        assert quick_function() == 42

@run("Integration Tests")
class IntegrationTests:
    @test("database_integration")
    def test_db(self):
        # Database integration test
        pass

@run("API Tests")
class APITests:
    @test("api_endpoint")
    def test_api(self):
        # API test
        pass

# All suites run automatically
```

### Output Format

```
+---------------------------+----------+-----------+
| Test Name                 | Status   | Duration  |
+===========================+==========+===========+
| UnitTests.setup           | PASSED   | 0.001s    |
| UnitTests.fast_operation  | PASSED   | 0.002s    |
| UnitTests.teardown        | PASSED   | 0.001s    |
| IntegrationTests.setup    | PASSED   | 0.050s    |
| IntegrationTests.database | PASSED   | 0.123s    |
| IntegrationTests.teardown | PASSED   | 0.045s    |
| APITests.api_endpoint     | PASSED   | 0.234s    |
+---------------------------+----------+-----------+

Summary: 7/7 passed • 0.456s total
```

### Features

- **Automatic Execution**: Tests run on script exit via `atexit`
- **Structured Output**: Tabular results with `tabulate`
- **Setup/Teardown**: Lifecycle methods for test preparation/cleanup
- **Multiple Suites**: Organize tests into logical groups
- **Timing**: Automatic execution time tracking
- **Error Handling**: Failed tests show error messages

### Use Cases

- **Demo Scripts**: Showcase library features
- **Smoke Tests**: Quick validation tests
- **Examples**: Executable documentation
- **Prototyping**: Rapid test development
- **Learning**: Simple test framework for beginners

**Note:** For production testing, use `pytest` or `unittest`.

---

## Best Practices

### Decorator Usage

**DO:**
- Use `@singleton` for stateful managers
- Use `@function_timer` during optimization
- Use `@retry_on_exception` for network operations
- Use `@cache_results` for pure functions
- Use `@thread_safe` for shared state

**DON'T:**
- Don't overuse decorators (readability)
- Don't suppress important exceptions
- Don't cache functions with side effects
- Don't use `@thread_safe` unnecessarily (performance)

### Cache Strategy

**DO:**
- Set appropriate TTL for data freshness
- Monitor cache hit rates
- Use memory cache for hot data
- Use multi-level for production
- Invalidate on data changes

**DON'T:**
- Don't cache indefinitely (memory leaks)
- Don't cache large objects in memory
- Don't ignore cache statistics
- Don't use cache for configuration

### Time Handling

**DO:**
- Always use UTC internally
- Convert to local timezone only for display
- Use ISO 8601 for serialization
- Store timestamps as UTC
- Use timezone-aware datetimes

**DON'T:**
- Don't use naive datetimes
- Don't assume server timezone
- Don't hardcode timezone offsets
- Don't compare datetimes across timezones

### Logging

**DO:**
- Enable logging only where needed
- Use appropriate log levels
- Log to files for production
- Use module-specific loggers
- Monitor log file sizes

**DON'T:**
- Don't leave DEBUG logging in production
- Don't log sensitive data
- Don't spam logs with redundant messages
- Don't forget to rotate log files

### Observer Pattern

**DO:**
- Use for loose coupling
- Keep observers lightweight
- Handle observer exceptions
- Document event types
- Detach when done

**DON'T:**
- Don't create observer loops
- Don't perform heavy work in notify
- Don't assume observer order
- Don't leak observer references

---

## API Reference

### Table Renderer Module

```python
from basefunctions.utils.table_renderer import (
    render_table,           # Render list-based table
    render_dataframe,       # Render DataFrame
    tabulate_compat,        # Backward compatibility wrapper
    get_table_format,       # Get configured theme
    THEMES                  # Available themes dict
)

# Main functions
render_table(
    data: List[List[Any]],
    headers: Optional[List[str]] = None,
    column_specs: Optional[List[str]] = None,
    theme: Optional[str] = None,
    max_width: Optional[int] = None
) -> str

render_dataframe(
    df: Any,
    column_specs: Optional[List[str]] = None,
    theme: Optional[str] = None,
    max_width: Optional[int] = None,
    showindex: bool = False
) -> str

tabulate_compat(
    data: Any,
    headers: Optional[List[str]] = None,
    tablefmt: Optional[str] = None,
    colalign: Optional[Tuple[str, ...]] = None,
    disable_numparse: bool = False,
    showindex: bool = False
) -> str

get_table_format() -> str
```

**Column Spec Format:**
```
"alignment:width[:decimals[:unit]]"
- alignment: "left" | "right" | "center" | "decimal"
- width: integer (characters)
- decimals: integer (optional, numeric values only)
- unit: string (optional, suffix like "EUR", "%", "ms")
```

**Available Themes:** "grid" | "fancy_grid" | "minimal" | "psql"

### Decorators Module

```python
from basefunctions import (
    singleton,              # Singleton pattern
    function_timer,         # Execution timing
    retry_on_exception,     # Retry on failure
    cache_results,          # Result caching
    thread_safe,            # Thread safety
    catch_exceptions,       # Exception handling
    suppress,               # Exception suppression
    profile_memory,         # Memory profiling
    warn_if_slow,           # Performance warning
    assert_non_null_args,   # Argument validation
    log_to_file,            # Function-specific logging
    auto_property           # Automatic properties
)
```

### Cache Manager

```python
from basefunctions import get_cache
from basefunctions.utils.cache_manager import (
    CacheManager,          # High-level cache interface
    CacheBackend,          # Abstract backend
    MemoryBackend,         # In-memory cache
    DatabaseBackend,       # Database cache
    FileBackend,           # File-system cache
    MultiLevelBackend,     # Multi-level cache
    CacheFactory,          # Cache factory
    CacheEntry,            # Cache entry with TTL
    CacheError,            # Cache exceptions
    CacheBackendError
)

# Get cache manager
cache = get_cache(backend="memory", max_size=1000)

# Cache operations
cache.get(key: str) -> Optional[Any]
cache.set(key: str, value: Any, ttl: int = 3600) -> None
cache.get_or_set(key: str, callable_func: Callable, ttl: int) -> Any
cache.delete(key: str) -> bool
cache.exists(key: str) -> bool
cache.clear(pattern: str = "*") -> int
cache.keys(pattern: str = "*") -> List[str]
cache.size() -> int
cache.stats() -> Dict[str, Any]
cache.expire(key: str, ttl: int) -> bool
cache.ttl(key: str) -> Optional[int]
cache.invalidate_pattern(pattern: str) -> int
```

### Time Utilities

```python
from basefunctions import (
    now_utc,                  # Current UTC time
    now_local,                # Current local time
    utc_timestamp,            # POSIX timestamp
    format_iso,               # Format to ISO 8601
    parse_iso,                # Parse ISO 8601
    to_timezone,              # Convert timezone
    datetime_to_str,          # Custom formatting
    str_to_datetime,          # Custom parsing
    timestamp_to_datetime,    # Timestamp to datetime
    datetime_to_timestamp     # Datetime to timestamp
)

now_utc() -> datetime.datetime
now_local(tz_str: Optional[str] = None) -> datetime.datetime
utc_timestamp() -> float
format_iso(dt: datetime.datetime) -> str
parse_iso(s: str, tz_str: Optional[str] = None) -> datetime.datetime
to_timezone(dt: datetime.datetime, tz_str: str) -> datetime.datetime
datetime_to_str(dt: datetime.datetime, fmt: str) -> str
str_to_datetime(s: str, fmt: str) -> datetime.datetime
timestamp_to_datetime(ts: float) -> datetime.datetime
datetime_to_timestamp(dt: datetime.datetime) -> float
```

### Logging

```python
from basefunctions import (
    setup_logger,              # Setup module logger
    get_logger,                # Get logger instance
    enable_console,            # Enable console output
    disable_console,           # Disable console output
    redirect_all_to_file,      # Redirect all to file
    configure_module_logging,  # Configure specific module
    get_module_logging_config  # Get module config
)

setup_logger(name: str, level: str = "ERROR", file: Optional[str] = None) -> None
get_logger(name: str) -> logging.Logger
enable_console(level: str = "CRITICAL") -> None
disable_console() -> None
redirect_all_to_file(file: str, level: str = "DEBUG") -> None
configure_module_logging(
    name: str,
    level: Optional[str] = None,
    console: Optional[bool] = None,
    console_level: Optional[str] = None,
    file: Optional[str] = None
) -> None
get_module_logging_config(name: str) -> Optional[Dict]
```

### Observer Pattern

```python
from basefunctions.utils.observer import Observer, Observable

class Observer(ABC):
    @abstractmethod
    def notify(self, message: Any, *args, **kwargs) -> None:
        pass

class Observable:
    def attach_observer_for_event(self, event_type: str, observer: Observer) -> None
    def detach_observer_for_event(self, event_type: str, observer: Observer) -> None
    def notify_observers(self, event_type: str, message: Any, *args, **kwargs) -> None
```

### Progress Tracking

```python
from basefunctions.utils.progress_tracker import (
    ProgressTracker,
    AliveProgressTracker
)

class ProgressTracker(ABC):
    @abstractmethod
    def progress(self, n: int = 1) -> None:
        pass

    @abstractmethod
    def close(self) -> None:
        pass

class AliveProgressTracker(ProgressTracker):
    def __init__(self, total: Optional[int] = None, desc: str = "Processing")
    def progress(self, n: int = 1) -> None
    def close(self) -> None
```

### Demo Runner

```python
from basefunctions.utils.demo_runner import run, test

@run(suite_name: str) -> Callable
@test(test_name: str) -> Callable

# Test class structure
class TestSuite:
    def setup(self):        # Optional
        pass

    @test("test_name")
    def test_method(self):
        pass

    def teardown(self):     # Optional
        pass
```

---

## Examples

### Complete Cache Example

```python
from basefunctions import get_cache, get_logger, setup_logger

# Setup logging
setup_logger(__name__, level="INFO")
logger = get_logger(__name__)

# Create multi-level cache
cache = get_cache("multi", backends=[
    ("memory", {"max_size": 100}),
    ("file", {"cache_dir": "/tmp/app_cache"})
])

def get_user(user_id: int):
    """Get user with caching."""
    cache_key = f"user:{user_id}"

    # Try cache first
    user = cache.get(cache_key)
    if user:
        logger.info(f"Cache hit for user {user_id}")
        return user

    # Cache miss - fetch from database
    logger.info(f"Cache miss for user {user_id}")
    user = db.query_one("SELECT * FROM users WHERE id = ?", (user_id,))

    # Cache for 1 hour
    cache.set(cache_key, user, ttl=3600)

    return user

# Use it
user = get_user(123)

# Monitor cache performance
stats = cache.stats()
logger.info(f"Cache hit rate: {stats['hit_rate_percent']}%")
```

### Complete Observer Example

```python
from basefunctions.utils.observer import Observer, Observable
from basefunctions import get_logger, setup_logger

setup_logger(__name__, level="INFO")
logger = get_logger(__name__)

class EventLogger(Observer):
    """Log all events."""
    def notify(self, message, *args, **kwargs):
        logger.info(f"Event: {message}, Args: {args}")

class EventValidator(Observer):
    """Validate events."""
    def notify(self, message, *args, **kwargs):
        if message == "data_added":
            value = args[0]
            if value < 0:
                logger.warning(f"Negative value: {value}")

class DataStore(Observable):
    """Observable data store."""
    def __init__(self):
        super().__init__()
        self.data = []

    def add(self, value):
        self.data.append(value)
        self.notify_observers("data_added", value)

    def clear(self):
        count = len(self.data)
        self.data.clear()
        self.notify_observers("data_cleared", count)

# Setup
store = DataStore()
store.attach_observer_for_event("data_added", EventLogger())
store.attach_observer_for_event("data_added", EventValidator())
store.attach_observer_for_event("data_cleared", EventLogger())

# Use
store.add(42)    # Logged and validated
store.add(-5)    # Logged and warning
store.clear()    # Logged
```

### Complete Demo Runner Example

```python
from basefunctions.utils.demo_runner import run, test

@run("API Tests")
class TestAPI:
    def setup(self):
        """Setup test environment."""
        self.base_url = "https://api.example.com"
        self.client = APIClient(self.base_url)

    @test("authentication")
    def test_auth(self):
        """Test API authentication."""
        token = self.client.authenticate("user", "pass")
        assert token is not None, "Failed to get auth token"

    @test("user_list")
    def test_get_users(self):
        """Test user list endpoint."""
        users = self.client.get("/users")
        assert len(users) > 0, "No users returned"

    @test("error_handling")
    def test_404(self):
        """Test 404 error handling."""
        try:
            self.client.get("/nonexistent")
            assert False, "Should have raised 404 error"
        except APIError as e:
            assert e.status_code == 404

    def teardown(self):
        """Cleanup."""
        self.client.close()

# Tests run automatically on exit
```

---

## Conclusion

The `utils` module provides essential utilities for building robust Python applications:

- **Decorators** reduce boilerplate and add cross-cutting concerns
- **Cache Manager** improves performance with flexible caching
- **Time Utilities** handle timezones correctly
- **Logging** provides thread-safe, configurable logging
- **Observer Pattern** enables loose coupling
- **Progress Tracking** provides feedback for long operations
- **Demo Runner** simplifies test creation

All components follow KISSS principles and integrate seamlessly with the basefunctions framework.

For more information:
- [Logging Guide](./LOGGING_USAGE_GUIDE.md)
- [EventBus Guide](./EVENTBUS_USAGE_GUIDE.md)
- [CLI Guide](./CLI_USAGE_GUIDE.md)

---

**Version:** 1.2
**Last Updated:** 2026-01-26
**Framework:** basefunctions v0.5.72
**Added:** Table Renderer Module
