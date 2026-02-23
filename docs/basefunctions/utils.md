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

**BREAKING CHANGE (v0.5.94):** Complete API redesign for simpler, more consistent logging configuration.

The logging API has been completely redesigned to provide a simpler, more consistent interface. The old API with `setup_logger()`, `enable_console()`, `disable_console()`, etc. has been removed.

### Migration Guide

Migrating from old API to new API:

| Old API | New API |
|---------|---------|
| `setup_logger(__name__, "DEBUG", "/tmp/app.log")` | `logger = get_logger(__name__); set_log_level("DEBUG"); set_log_file("/tmp/app.log")` |
| `enable_console("INFO")` | `set_log_console(True, "INFO")` |
| `disable_console()` | `set_log_console(False)` |
| `redirect_all_to_file("/tmp/app.log")` | `set_log_file("/tmp/app.log")` |
| `configure_module_logging()` | No direct replacement - use `set_log_level()` per module |

**Key Differences:**
- Configuration is now centralized (affects ALL loggers, not just named ones)
- File rotation is now built-in and configurable
- Console and file logging can coexist
- All loggers (even direct `logging.getLogger()` calls) are automatically captured

---

### Configuration-Based Logging

**Purpose:** Zero-setup logging through config.json

Logging can now be configured entirely through `config.json` with no setup code required in your applications. On the first call to `get_logger()`, the logging system automatically reads configuration and sets up logging accordingly.

**Config Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `basefunctions/log_enabled` | bool | false | Master switch - logging disabled if false |
| `basefunctions/log_level` | str | "INFO" | Global log level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `basefunctions/log_file` | str or null | null | Log file path. If null, auto-generates log file from script name |

**Behavior:**

- `log_enabled=false`: No logging setup (silent)
- `log_enabled=true` + `log_file=null`: **Auto-generates log file** (NEW in v4.1)
- `log_enabled=true` + `log_file="/path"`: File logging with explicit path (console disabled)
- Silent operation: No exceptions if config unavailable
- Manual setup (via `set_log_*` functions) overrides auto-init

**Auto-Log-File Feature (v4.1):**

When `log_file=null`, the logging system automatically generates a log file based on:
- **Script name:** Extracted from `sys.argv[0]` (e.g., `my_script.py` → `my_script.log`)
- **Package directory:** Auto-detected from path (e.g., `neuraldev/tickerhub` → tickerhub package)
- **Log directory:** Uses standard log directory for package

**Auto-Generated Log File Path:**
```
<package_log_dir>/<script_name>.log
```

**Examples:**
- Direct call: `python ~/Code/neuraldev/tickerhub/ticker.py` → `~/Code/neuraldev/tickerhub/log/ticker.log`
- Deployment: `python ~/.neuraldevelopment/packages/tickerhub/bin/ticker` → `~/.neuraldevelopment/logs/tickerhub/ticker.log`
- Import case: Stack inspection finds caller filename → `<package_log_dir>/caller.log`
- Fallback: If auto-generation fails → Console logging (stderr)

**Example 1: Auto-Generated Log File (NEW in v4.1)**

```json
{
  "basefunctions": {
    "log_enabled": true,
    "log_level": "DEBUG",
    "log_file": null
  }
}
```

```python
# tickerhub/ticker.py - ZERO setup code
from basefunctions.utils.logging import get_logger

logger = get_logger(__name__)
logger.debug("Ticker started")  # → ~/Code/neuraldev/tickerhub/log/ticker.log
```

**What happens:**
- Script name: `ticker.py` → Log file: `ticker.log`
- Package: `tickerhub` → Log directory: `~/Code/neuraldev/tickerhub/log/`
- Full path: `~/Code/neuraldev/tickerhub/log/ticker.log`

**Example 2: Production Mode (File)**

```json
{
  "basefunctions": {
    "log_enabled": true,
    "log_level": "INFO",
    "log_file": "/var/log/myapp/app.log"
  }
}
```

```python
# tickerhub/ticker.py - ZERO setup code
from basefunctions.utils.logging import get_logger

logger = get_logger(__name__)
logger.info("Ticker started")  # → /var/log/myapp/app.log

# portfoliofunctions/portfolio.py - ZERO setup code
from basefunctions.utils.logging import get_logger

logger = get_logger(__name__)
logger.info("Portfolio loaded")  # → /var/log/myapp/app.log (same file!)

# signalengine/engine.py - ZERO setup code
from basefunctions.utils.logging import get_logger

logger = get_logger(__name__)
logger.info("Engine running")  # → /var/log/myapp/app.log (same file!)
```

**All three apps log to ONE file with ZERO setup code.**

**Example 3: Manual Override**

Config-based auto-init can be overridden at runtime:

```python
from basefunctions.utils.logging import get_logger, set_log_file

# Auto-init happens on first call (reads config.json)
logger = get_logger(__name__)

# Manual override - switch to different file
set_log_file("/tmp/debug.log", level="DEBUG")

logger.debug("Now logging to debug file")  # → /tmp/debug.log
```

**Migration: Manual Setup → Config-Based**

**Before (Manual Setup):**
```python
# Every app needs this boilerplate
from basefunctions.utils.logging import get_logger, set_log_level, set_log_file

set_log_level("INFO")
set_log_file("/var/log/myapp/app.log")

logger = get_logger(__name__)
logger.info("Started")
```

**After (Config-Based):**
```json
// config.json (once, in parent app)
{
  "basefunctions": {
    "log_enabled": true,
    "log_level": "INFO",
    "log_file": "/var/log/myapp/app.log"
  }
}
```

```python
# All apps just use logger - ZERO setup
from basefunctions.utils.logging import get_logger

logger = get_logger(__name__)
logger.info("Started")  # → /var/log/myapp/app.log
```

---

### get_logger()

**Purpose:** Get logger instance for module

```python
from basefunctions.utils.logging import get_logger

logger = get_logger(__name__)
logger.info("Application started")
logger.error("Error occurred: %s", error_msg)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | str or None | None | Logger name (use `__name__` for module-level logging) |

**Returns:**
- **Type:** `logging.Logger`
- **Description:** Configured logger instance

**Best Practice:**
```python
# At top of every module
from basefunctions.utils.logging import get_logger

logger = get_logger(__name__)
```

**Note:** This is the ONLY way to get a logger. All configuration is done via `set_log_*` functions.

---

### set_log_level()

**Purpose:** Set global or module-specific log level

```python
from basefunctions.utils.logging import set_log_level

# Set global level
set_log_level("INFO")

# Set module-specific level
set_log_level("DEBUG", module="myapp.database")
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `level` | str | - | Log level: "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL" |
| `module` | str or None | None | Module name (None = global level) |

**Best For:**
- Application startup configuration
- Module-specific debugging
- Runtime log level changes

---

### set_log_console()

**Purpose:** Enable/disable console output

```python
from basefunctions.utils.logging import set_log_console

# Enable console logging
set_log_console(True, level="INFO")

# Disable console logging
set_log_console(False)

# Enable with custom level
set_log_console(True, level="WARNING")  # Only warnings and above
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enabled` | bool | - | Enable (True) or disable (False) console output |
| `level` | str or None | None | Console-specific log level (None = use global level) |

**Best For:**
- Development mode (console ON)
- Production mode (console OFF)
- Different levels for console vs file

---

### set_log_file()

**Purpose:** Configure file-based logging with optional rotation

```python
from basefunctions.utils.logging import set_log_file

# Simple file logging
set_log_file("/tmp/app.log")

# File logging with rotation
set_log_file(
    "/tmp/app.log",
    level="DEBUG",
    rotation=True,
    rotation_count=3,
    rotation_size_kb=1000
)

# Different level than console
set_log_file("/tmp/app.log", level="DEBUG")  # Console might be INFO
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `filepath` | str | - | Path to log file |
| `level` | str | "INFO" | File-specific log level |
| `rotation` | bool | False | Enable log file rotation |
| `rotation_count` | int | 3 | Number of backup files to keep |
| `rotation_size_kb` | int | 1024 | Max file size in KB before rotation |

**Best For:**
- Production logging
- Debug file with higher verbosity than console
- Long-running applications (with rotation)

**Rotation Behavior:**
- When file reaches `rotation_size_kb`, it's renamed to `app.log.1`
- Previous backups are shifted: `app.log.1` → `app.log.2`, etc.
- Oldest backup (beyond `rotation_count`) is deleted

---

### set_log_file_rotation()

**Purpose:** Update rotation settings for existing file handler

```python
from basefunctions.utils.logging import set_log_file_rotation

# Enable rotation
set_log_file_rotation(True, count=5, size_kb=2000)

# Disable rotation
set_log_file_rotation(False)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enabled` | bool | - | Enable/disable rotation |
| `count` | int | 3 | Number of backup files |
| `size_kb` | int | 1024 | Max size in KB |

**Best For:**
- Changing rotation settings at runtime
- Disabling rotation temporarily

---

### get_standard_log_directory()

**Purpose:** Get standard log directory for package (unchanged from old API)

```python
from basefunctions.utils.logging import get_standard_log_directory

log_dir = get_standard_log_directory("myapp")
# Returns: "~/Code/neuraldev/myapp/log" (development)
# or "~/.neuraldevelopment/packages/myapp/log" (deployment)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `package_name` | str | - | Name of package |
| `ensure_exists` | bool | True | Create directory if missing |

**Returns:**
- **Type:** `str`
- **Description:** Absolute path to log directory

---

## Usage Examples

### Simple Console Logging

**Scenario:** Quick development/debugging

```python
from basefunctions.utils.logging import get_logger, set_log_level, set_log_console

# Configure
set_log_level("INFO")
set_log_console(True)

# Use
logger = get_logger(__name__)
logger.info("App started")
logger.debug("This won't show (level=INFO)")
logger.warning("This will show")
```

---

### File Logging with Rotation

**Scenario:** Production application with log rotation

```python
from basefunctions.utils.logging import get_logger, set_log_file, set_log_level

# Configure
set_log_level("INFO")
set_log_file(
    "/var/log/myapp/app.log",
    level="DEBUG",  # More verbose in file
    rotation=True,
    rotation_count=5,
    rotation_size_kb=5000  # 5 MB
)

# Use
logger = get_logger(__name__)
logger.info("Application started")
logger.debug("Detailed debug info (only in file)")
```

---

### Capture ALL Logs (Even Third-Party)

**Scenario:** Capture logs from libraries that use `logging.getLogger()` directly

```python
from basefunctions.utils.logging import set_log_file, set_log_level

# Configure BEFORE any imports
set_log_level("INFO")
set_log_file("/tmp/all.log")

# Now import and use libraries
import requests  # Uses logging internally
import pandas as pd  # Uses logging internally

# ALL logs (yours + libraries) go to /tmp/all.log
response = requests.get("https://api.example.com")  # Requests logs captured
```

**Why This Works:** The new API configures the root logger, so ALL loggers inherit the configuration.

---

### Console + File Simultaneously

**Scenario:** Console for INFO+, file for DEBUG+

```python
from basefunctions.utils.logging import get_logger, set_log_console, set_log_file, set_log_level

# Global level (affects both)
set_log_level("DEBUG")

# Console: INFO and above
set_log_console(True, level="INFO")

# File: DEBUG and above
set_log_file("/tmp/app.log", level="DEBUG")

# Use
logger = get_logger(__name__)
logger.debug("Detailed info (file only)")
logger.info("Important event (console + file)")
logger.error("Error occurred (console + file)")
```

---

### Module-Specific Log Levels

**Scenario:** Debug one module, silence another

```python
from basefunctions.utils.logging import get_logger, set_log_level, set_log_console

# Global level
set_log_level("INFO")
set_log_console(True)

# Module-specific levels
set_log_level("DEBUG", module="myapp.database")  # Verbose DB logs
set_log_level("ERROR", module="myapp.external")  # Silence noisy library

# Use
db_logger = get_logger("myapp.database")
db_logger.debug("SQL: SELECT * FROM users")  # Shows

ext_logger = get_logger("myapp.external")
ext_logger.info("External call")  # Doesn't show (ERROR+ only)
```

---

### Standard Log Directory

**Scenario:** Use package-standard log directory

```python
from basefunctions.utils.logging import get_standard_log_directory, set_log_file, get_logger
from pathlib import Path

# Get standard log directory
log_dir = get_standard_log_directory("myapp", ensure_exists=True)
log_file = str(Path(log_dir) / "app.log")

# Configure
set_log_file(log_file, rotation=True)

# Use
logger = get_logger(__name__)
logger.info("Logging to standard directory")
```

---

## Best Practices

### Best Practice 1: Configure Early

**Why:** Ensure all logs are captured from app start

```python
# GOOD - Configure at module top level or main() entry
from basefunctions.utils.logging import set_log_level, set_log_console

set_log_level("INFO")
set_log_console(True)

# Now import other modules
from myapp import database, api
```

```python
# AVOID - Configure after imports
from myapp import database, api  # These might log before config

from basefunctions.utils.logging import set_log_level
set_log_level("INFO")  # Too late for some logs
```

---

### Best Practice 2: Use Rotation in Production

**Why:** Prevent unbounded log file growth

```python
# GOOD - Production setup
set_log_file(
    "/var/log/myapp/app.log",
    rotation=True,
    rotation_count=7,  # 7 days of backups
    rotation_size_kb=10000  # 10 MB per file
)
```

```python
# AVOID - No rotation in long-running apps
set_log_file("/var/log/myapp/app.log")  # File grows forever
```

---

### Best Practice 3: Different Levels for Console vs File

**Why:** Keep console clean, file verbose

```python
# GOOD - Console for important events, file for debugging
set_log_console(True, level="WARNING")  # Only warnings/errors on console
set_log_file("/tmp/app.log", level="DEBUG")  # Everything in file
```

---

### Best Practice 4: Always Use `__name__` for Loggers

**Why:** Enables module-specific log levels and clear log sources

```python
# GOOD
logger = get_logger(__name__)
logger.info("User logged in")  # Log shows: myapp.auth: User logged in

# AVOID
logger = get_logger("app")  # Loses module context
```

---

## Common Patterns

### Pattern: Development Mode

**When to use:** Local development with console output

```python
from basefunctions.utils.logging import set_log_level, set_log_console, get_logger

# Development configuration
set_log_level("DEBUG")
set_log_console(True)

# Your code
logger = get_logger(__name__)
logger.debug("Entering function")
logger.info("Processing complete")
```

---

### Pattern: Production Mode

**When to use:** Production deployment with file logging

```python
from basefunctions.utils.logging import (
    set_log_level,
    set_log_console,
    set_log_file,
    get_standard_log_directory,
    get_logger
)
from pathlib import Path

# Production configuration
log_dir = get_standard_log_directory("myapp")
log_file = str(Path(log_dir) / "app.log")

set_log_level("INFO")
set_log_console(False)  # No console in production
set_log_file(
    log_file,
    level="INFO",
    rotation=True,
    rotation_count=7,
    rotation_size_kb=10000
)

# Your code
logger = get_logger(__name__)
logger.info("Application started")
```

---

### Pattern: Hybrid Mode

**When to use:** Production with console for critical errors

```python
from basefunctions.utils.logging import set_log_level, set_log_console, set_log_file, get_logger

# Hybrid configuration
set_log_level("INFO")
set_log_console(True, level="ERROR")  # Only errors on console
set_log_file("/var/log/myapp/app.log", level="INFO", rotation=True)

# Your code
logger = get_logger(__name__)
logger.info("User action")  # File only
logger.error("Critical error")  # Console + file
```

---

## Error Handling

### Common Errors

**Error 1: File Permission Denied**

```python
# WRONG
set_log_file("/root/app.log")  # Permission denied if not root
# PermissionError: [Errno 13] Permission denied: '/root/app.log'
```

**Solution:**
```python
# CORRECT - Use accessible directory
from basefunctions.utils.logging import get_standard_log_directory
from pathlib import Path

log_dir = get_standard_log_directory("myapp")
log_file = str(Path(log_dir) / "app.log")
set_log_file(log_file)
```

---

**Error 2: Directory Doesn't Exist**

```python
# WRONG
set_log_file("/tmp/logs/app.log")  # /tmp/logs doesn't exist
# FileNotFoundError: [Errno 2] No such file or directory: '/tmp/logs/app.log'
```

**Solution:**
```python
# CORRECT - Create directory first
from pathlib import Path

log_file = Path("/tmp/logs/app.log")
log_file.parent.mkdir(parents=True, exist_ok=True)
set_log_file(str(log_file))
```

---

## FAQ

**Q: Can I use console and file logging together?**

A: Yes! Call both `set_log_console(True)` and `set_log_file("/path")`. Each can have different log levels.

**Q: Do I still need to call `setup_logger()` or `configure_module_logging()`?**

A: No! These functions were removed in v0.5.94. Use `get_logger(__name__)` + `set_log_*` functions instead.

**Q: How do I capture logs from third-party libraries?**

A: The new API automatically captures ALL loggers. Just configure once with `set_log_level()` and `set_log_file()`.

**Q: What happens if I don't configure logging?**

A: Python's default logging behavior applies (WARNING+ to console). It's recommended to always configure explicitly.

**Q: Can I change log levels at runtime?**

A: Yes! Call `set_log_level()` anytime. Changes affect all future log calls.

**Q: How does rotation work?**

A: When log file reaches `rotation_size_kb`, it's renamed to `app.log.1`, previous backups shift up, oldest is deleted.

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
from basefunctions.utils.logging import (
    get_logger,
    set_log_level,
    set_log_console,
    set_log_file,
    set_log_file_rotation,
    get_standard_log_directory
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
| Get logger | `get_logger(__name__)` |
| Set log level | `set_log_level("INFO")` |
| Enable console | `set_log_console(True)` |
| Log to file | `set_log_file("/tmp/app.log")` |
| Progress bar | `AliveProgressTracker(total=100)` |

---

**Document Version:** 1.0.0
**Last Updated:** 2026-01-29
**Subpackage Version:** 0.5.75
