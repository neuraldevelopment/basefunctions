# Utils - User Documentation

**Package:** basefunctions
**Subpackage:** utils
**Version:** 0.5.75
**Purpose:** Utility functions including decorators, logging, caching, time operations, and more

---

## Overview

The utils subpackage provides essential utility functions and classes for common programming tasks.

**Key Features:**
- Function decorators (timing, caching, retry, thread-safety)
- Logging configuration and management
- Multi-backend caching system
- Time/datetime utilities with timezone support
- Observer pattern implementation
- Progress tracking
- Table rendering
- Demo/test runner

**Common Use Cases:**
- Performance profiling
- Application logging setup
- Data caching strategies
- Timezone-aware datetime handling
- Event notification systems
- Progress visualization
- Data table formatting

---

## Decorators

### @function_timer

**Purpose:** Measure and log function execution time

```python
from basefunctions.utils import function_timer

@function_timer
def slow_function():
    time.sleep(1)
    return "done"

result = slow_function()  # Logs: runtime of slow_function: 1.00012345 seconds
```

**Best For:**
- Performance profiling
- Identifying bottlenecks
- Optimization validation

---

### @singleton

**Purpose:** Ensure only one instance of class exists

```python
from basefunctions.utils import singleton

@singleton
class Database:
    def __init__(self):
        self.connection = self.connect()

    def connect(self):
        return "connected"

db1 = Database()
db2 = Database()
print(db1 is db2)  # True - same instance
```

**Best For:**
- Database connections
- Configuration managers
- Resource pools
- Global state

---

### @cache_results

**Purpose:** Cache function return values

```python
from basefunctions.utils import cache_results

@cache_results(ttl=300)  # Cache for 5 minutes
def expensive_calculation(n):
    time.sleep(2)
    return n ** 2

result = expensive_calculation(10)  # Takes 2 seconds
result = expensive_calculation(10)  # Instant - cached
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ttl` | int | 3600 | Time-to-live in seconds |

**Best For:**
- API call results
- Database queries
- Expensive computations
- Repetitive operations

---

### @retry_on_exception

**Purpose:** Retry function on exception with exponential backoff

```python
from basefunctions.utils import retry_on_exception

@retry_on_exception(max_retries=3, delay=1, backoff=2)
def unstable_api_call():
    response = requests.get("https://api.example.com/data")
    return response.json()

data = unstable_api_call()  # Retries up to 3 times on failure
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_retries` | int | 3 | Maximum retry attempts |
| `delay` | float | 1.0 | Initial delay in seconds |
| `backoff` | float | 2.0 | Backoff multiplier |

**Best For:**
- Network requests
- Database connections
- External service calls
- Flaky operations

---

### @catch_exceptions

**Purpose:** Catch and log exceptions without crashing

```python
from basefunctions.utils import catch_exceptions

@catch_exceptions
def risky_function():
    return 1 / 0  # Would normally crash

risky_function()  # Logs error, returns None
```

**Best For:**
- Background tasks
- Event handlers
- Optional operations
- Graceful degradation

---

### @thread_safe

**Purpose:** Make function thread-safe with lock

```python
from basefunctions.utils import thread_safe

class Counter:
    def __init__(self):
        self.count = 0

    @thread_safe
    def increment(self):
        self.count += 1

counter = Counter()
# Safe for concurrent access
```

**Best For:**
- Shared resources
- Global state modifications
- Critical sections
- Race condition prevention

---

### @warn_if_slow

**Purpose:** Log warning if function exceeds time threshold

```python
from basefunctions.utils import warn_if_slow

@warn_if_slow(threshold=1.0)  # Warn if >1 second
def sometimes_slow():
    time.sleep(1.5)
    return "done"

sometimes_slow()  # Logs warning: Function took 1.5s (threshold: 1.0s)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `threshold` | float | 1.0 | Time threshold in seconds |

---

### @profile_memory

**Purpose:** Track memory usage of function

```python
from basefunctions.utils import profile_memory

@profile_memory
def memory_intensive():
    data = [i for i in range(1000000)]
    return len(data)

result = memory_intensive()  # Logs memory usage
```

---

## Logging

### setup_logger()

**Purpose:** Configure logger for module

```python
from basefunctions.utils import setup_logger

setup_logger(__name__)
```

**Best Practice:**
```python
# At top of every module
from basefunctions.utils import setup_logger

setup_logger(__name__)
```

---

### get_logger()

**Purpose:** Get configured logger instance

```python
from basefunctions.utils import get_logger

logger = get_logger(__name__)
logger.info("Application started")
logger.error("Error occurred: %s", error_msg)
```

---

### enable_console() / disable_console()

**Purpose:** Control console output

```python
from basefunctions.utils import enable_console, disable_console

# Disable console logging
disable_console()
print("This won't show")

# Re-enable
enable_console()
print("This shows")
```

---

### redirect_all_to_file()

**Purpose:** Redirect all logging to file

```python
from basefunctions.utils import redirect_all_to_file

redirect_all_to_file("app.log")
logger.info("This goes to file")
```

---

## Time Utilities

### now_utc() / now_local()

**Purpose:** Get current datetime in UTC or local timezone

```python
from basefunctions.utils import now_utc, now_local

utc_time = now_utc()  # datetime in UTC
local_time = now_local()  # datetime in local timezone
```

---

### utc_timestamp()

**Purpose:** Get current UTC timestamp

```python
from basefunctions.utils import utc_timestamp

timestamp = utc_timestamp()  # Unix timestamp (float)
```

---

### format_iso() / parse_iso()

**Purpose:** Format/parse ISO 8601 datetime strings

```python
from basefunctions.utils import format_iso, parse_iso
from datetime import datetime

dt = datetime.now()
iso_string = format_iso(dt)  # "2026-01-29T10:30:00+00:00"

parsed = parse_iso(iso_string)  # datetime object
```

---

### to_timezone()

**Purpose:** Convert datetime to different timezone

```python
from basefunctions.utils import to_timezone, now_utc

utc_time = now_utc()
tokyo_time = to_timezone(utc_time, "Asia/Tokyo")
ny_time = to_timezone(utc_time, "America/New_York")
```

---

### datetime_to_str() / str_to_datetime()

**Purpose:** Convert between datetime and string with custom format

```python
from basefunctions.utils import datetime_to_str, str_to_datetime
from datetime import datetime

dt = datetime.now()
string = datetime_to_str(dt, "%Y-%m-%d %H:%M:%S")
parsed = str_to_datetime(string, "%Y-%m-%d %H:%M:%S")
```

---

### timestamp_to_datetime() / datetime_to_timestamp()

**Purpose:** Convert between Unix timestamp and datetime

```python
from basefunctions.utils import timestamp_to_datetime, datetime_to_timestamp
from datetime import datetime

# Timestamp to datetime
dt = timestamp_to_datetime(1706518200.0)

# Datetime to timestamp
timestamp = datetime_to_timestamp(dt)
```

---

## Cache Manager

### get_cache()

**Purpose:** Get cache manager with specified backend

```python
from basefunctions.utils import get_cache

# Memory cache (default)
cache = get_cache("memory")

# File cache
cache = get_cache("file", cache_dir="/tmp/mycache")

# Database cache
cache = get_cache("database", instance_name="mydb", database_name="cache")
```

**Backend Options:**

| Backend | Description | Use Case |
|---------|-------------|----------|
| `memory` | In-memory dict | Fast, temporary data |
| `file` | File-based | Persistent, simple |
| `database` | Database-backed | Persistent, shared |
| `multi` | Multi-level | L1→L2→L3 caching |

---

### CacheManager

**Purpose:** High-level cache interface

```python
from basefunctions.utils import get_cache

cache = get_cache("memory", max_size=1000)

# Set value
cache.set("user:123", {"name": "Alice"}, ttl=300)

# Get value
user = cache.get("user:123")

# Check exists
if cache.exists("user:123"):
    print("User cached")

# Get or compute
def expensive_query():
    return {"name": "Bob"}

user = cache.get_or_set("user:456", expensive_query, ttl=60)

# Delete
cache.delete("user:123")

# Clear all
cache.clear()

# Pattern clearing
cache.clear("user:*")

# Get statistics
stats = cache.stats()
print(f"Hit rate: {stats['hit_rate_percent']}%")
```

**Methods:**

| Method | Description |
|--------|-------------|
| `set(key, value, ttl)` | Store value with TTL |
| `get(key)` | Retrieve value |
| `get_or_set(key, callable, ttl)` | Get or compute and cache |
| `delete(key)` | Remove key |
| `exists(key)` | Check if key exists |
| `clear(pattern)` | Clear matching keys |
| `keys(pattern)` | List matching keys |
| `size()` | Get entry count |
| `stats()` | Get cache statistics |
| `expire(key, ttl)` | Set TTL for key |
| `ttl(key)` | Get remaining TTL |

---

## Observer Pattern

### Observer / Observable

**Purpose:** Implement observer pattern for event notifications

```python
from basefunctions.utils import Observer, Observable

class DataSource(Observable):
    def __init__(self):
        super().__init__()
        self.data = 0

    def update_data(self, value):
        self.data = value
        self.notify_observers("data_changed", value)

class Display(Observer):
    def update(self, event, data):
        print(f"Display received: {event} = {data}")

# Setup
source = DataSource()
display = Display()
source.attach(display)

# Trigger notification
source.update_data(42)  # Display prints: Display received: data_changed = 42
```

**Observable Methods:**
- `attach(observer)` - Add observer
- `detach(observer)` - Remove observer
- `notify_observers(event, data)` - Notify all observers

**Observer Methods:**
- `update(event, data)` - Handle notification

---

## Progress Tracking

### ProgressTracker

**Purpose:** Abstract base for progress tracking

```python
from basefunctions.utils import AliveProgressTracker

# Create tracker
with AliveProgressTracker(total=100, desc="Processing") as tracker:
    for i in range(100):
        # Do work
        process_item(i)
        tracker.progress()  # Advance by 1
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `total` | int or None | None | Expected total steps |
| `desc` | str | "Processing" | Progress bar description |

**Methods:**
- `progress(n=1)` - Advance by n steps
- `close()` - Close tracker

---

## Table Rendering

### render_table()

**Purpose:** Render data as formatted table

```python
from basefunctions.utils import render_table

data = [
    ["Alice", 25, "Engineer"],
    ["Bob", 30, "Designer"],
    ["Charlie", 35, "Manager"]
]

headers = ["Name", "Age", "Role"]

table = render_table(data, headers=headers)
print(table)
```

**Output:**
```
┌─────────┬─────┬──────────┐
│ Name    │ Age │ Role     │
├─────────┼─────┼──────────┤
│ Alice   │  25 │ Engineer │
│ Bob     │  30 │ Designer │
│ Charlie │  35 │ Manager  │
└─────────┴─────┴──────────┘
```

---

### render_dataframe()

**Purpose:** Render pandas DataFrame as table

```python
from basefunctions.utils import render_dataframe
import pandas as pd

df = pd.DataFrame({
    "Name": ["Alice", "Bob"],
    "Age": [25, 30]
})

table = render_dataframe(df)
print(table)
```

---

## Usage Examples

### Performance Profiling

**Scenario:** Measure function execution times

```python
from basefunctions.utils import function_timer

@function_timer
def load_data():
    return pd.read_csv("large_file.csv")

@function_timer
def process_data(df):
    return df.groupby("category").sum()

@function_timer
def save_results(df):
    df.to_csv("output.csv")

# All timing logged automatically
df = load_data()
result = process_data(df)
save_results(result)
```

---

### Smart Caching Strategy

**Scenario:** Multi-level cache for optimal performance

```python
from basefunctions.utils import get_cache

# L1: Memory (fast, small)
# L2: File (persistent, medium)
# L3: Database (shared, large)
cache = get_cache("multi", backends=[
    ("memory", {"max_size": 100}),
    ("file", {"cache_dir": "/tmp/cache"}),
    ("database", {"instance_name": "db", "database_name": "cache"})
])

# Get data (checks L1 → L2 → L3)
def expensive_query(user_id):
    return database.query(f"SELECT * FROM users WHERE id={user_id}")

user = cache.get_or_set(f"user:{user_id}", lambda: expensive_query(user_id))

# Data automatically promoted to higher cache levels
```

---

### Timezone-Aware Timestamps

**Scenario:** Handle timestamps across timezones

```python
from basefunctions.utils import (
    now_utc,
    to_timezone,
    format_iso,
    parse_iso
)

# Store in UTC
created_at = now_utc()
print(f"Created (UTC): {format_iso(created_at)}")

# Display in user's timezone
tokyo_time = to_timezone(created_at, "Asia/Tokyo")
print(f"Created (Tokyo): {format_iso(tokyo_time)}")

ny_time = to_timezone(created_at, "America/New_York")
print(f"Created (NY): {format_iso(ny_time)}")

# Parse ISO string
iso_str = "2026-01-29T10:30:00+09:00"
dt = parse_iso(iso_str)
print(f"Parsed: {dt}")
```

---

### Observer Pattern for Events

**Scenario:** Notify multiple components of data changes

```python
from basefunctions.utils import Observer, Observable

class DataModel(Observable):
    def __init__(self):
        super().__init__()
        self.value = 0

    def set_value(self, value):
        old_value = self.value
        self.value = value
        self.notify_observers("value_changed", {
            "old": old_value,
            "new": value
        })

class Logger(Observer):
    def update(self, event, data):
        print(f"[LOG] {event}: {data['old']} -> {data['new']}")

class Display(Observer):
    def update(self, event, data):
        print(f"[DISPLAY] Current value: {data['new']}")

class Database(Observer):
    def update(self, event, data):
        print(f"[DB] Saving value: {data['new']}")

# Setup
model = DataModel()
model.attach(Logger())
model.attach(Display())
model.attach(Database())

# Single update notifies all
model.set_value(42)
# Output:
# [LOG] value_changed: 0 -> 42
# [DISPLAY] Current value: 42
# [DB] Saving value: 42
```

---

### Progress Bar for Long Operations

**Scenario:** Visual feedback for batch processing

```python
from basefunctions.utils import AliveProgressTracker

items = range(1000)

with AliveProgressTracker(total=len(items), desc="Processing items") as tracker:
    for item in items:
        # Process item
        result = process_item(item)
        save_result(result)

        # Update progress
        tracker.progress()

# Output: [████████████████████] 100% Processing items
```

---

## Best Practices

### Best Practice 1: Use Decorators for Cross-Cutting Concerns

**Why:** Clean separation of concerns

```python
# GOOD
@function_timer
@retry_on_exception(max_retries=3)
@cache_results(ttl=300)
def fetch_data(url):
    return requests.get(url).json()
```

---

### Best Practice 2: Always Use UTC for Storage

**Why:** Avoid timezone confusion

```python
# GOOD - Store UTC
from basefunctions.utils import now_utc, format_iso

timestamp = now_utc()
db.save({"created_at": format_iso(timestamp)})

# Display in user timezone
user_time = to_timezone(timestamp, user.timezone)
```

---

### Best Practice 3: Cache Expensive Operations

**Why:** Improve performance

```python
# GOOD
from basefunctions.utils import get_cache

cache = get_cache()

def get_user(user_id):
    return cache.get_or_set(
        f"user:{user_id}",
        lambda: db.query_user(user_id),
        ttl=300
    )
```

---

## FAQ

**Q: Which cache backend should I use?**

A: Memory for speed, File for persistence, Database for sharing across processes, Multi for best of all.

**Q: Are decorators compatible with async functions?**

A: Most decorators work with sync functions only. Check specific decorator documentation.

**Q: Can I nest decorators?**

A: Yes. Order matters - decorators are applied bottom-to-top.

**Q: How do I clear the singleton cache?**

A: Singletons persist for application lifetime. Restart app to reset.

---

## See Also

**Related Subpackages:**
- `io` (`docs/basefunctions/io.md`) - File operations and serialization
- `config` (`docs/basefunctions/config.md`) - Configuration management

**System Documentation:**
- `~/.claude/_docs/python/basefunctions.md` - Internal architecture details

---

## Quick Reference

### Imports

```python
# Decorators
from basefunctions.utils import (
    function_timer,
    singleton,
    cache_results,
    retry_on_exception,
    catch_exceptions,
    thread_safe
)

# Logging
from basefunctions.utils import (
    setup_logger,
    get_logger,
    enable_console,
    disable_console
)

# Time
from basefunctions.utils import (
    now_utc,
    now_local,
    format_iso,
    parse_iso,
    to_timezone
)

# Cache
from basefunctions.utils import get_cache, CacheManager

# Observer
from basefunctions.utils import Observer, Observable

# Progress
from basefunctions.utils import AliveProgressTracker
```

### Cheat Sheet

| Task | Code |
|------|------|
| Time function | `@function_timer` |
| Make singleton | `@singleton` |
| Cache results | `@cache_results(ttl=300)` |
| Retry on error | `@retry_on_exception(max_retries=3)` |
| Thread-safe | `@thread_safe` |
| Get cache | `get_cache("memory")` |
| Cache value | `cache.set(key, value, ttl=60)` |
| Get UTC time | `now_utc()` |
| Format ISO | `format_iso(dt)` |
| Parse ISO | `parse_iso(string)` |
| Convert timezone | `to_timezone(dt, "Asia/Tokyo")` |
| Setup logger | `setup_logger(__name__)` |
| Progress bar | `AliveProgressTracker(total=100)` |

---

**Document Version:** 1.0.0
**Last Updated:** 2026-01-29
**Subpackage Version:** 0.5.75
