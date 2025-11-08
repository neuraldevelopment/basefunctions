# Basefunctions Logging System - Usage Guide

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Core Concepts](#core-concepts)
4. [Basic Usage](#basic-usage)
5. [Use Cases](#use-cases)
6. [Module-Specific Logging](#module-specific-logging)
7. [Logging Control](#logging-control)
8. [Configuration](#configuration)
9. [Advanced Features](#advanced-features)
10. [Best Practices](#best-practices)
11. [API Reference](#api-reference)

---

## Overview

The **basefunctions** logging system is a thread-safe, stdlib-based logging framework designed around the **KISSS principle** (Keep It Simple, Stupid, Safe). It provides fine-grained control over logging output at both global and module levels.

### Key Features

- **Silent by Default**: No output unless explicitly enabled
- **Thread-Safe**: Built with `threading.Lock` for concurrent environments
- **Module-Specific Control**: Configure logging per module independently
- **Hierarchical Logger Names**: Support for dotted module names (e.g., `basefunctions.http.client`)
- **Multiple Output Targets**: Console (stderr), file, or both
- **Global Control**: Enable/disable console output for all modules at once
- **Granular Overrides**: Modules can override global console settings
- **Zero Dependencies**: Pure Python stdlib implementation

### Design Philosophy

1. **Silent by Default**: Logging is OFF by default (`CRITICAL + 1` level). No unexpected output.
2. **Explicit Configuration**: You must explicitly enable logging for modules you care about.
3. **Global + Local Control**: Global switches (console on/off) combined with module-specific overrides.
4. **Thread-Safe**: All operations are protected by locks for use in EventBus, CLI, and multi-threaded contexts.

---

## Quick Start

### 1. Basic Module Logging Setup

```python
import basefunctions

# Enable logging for your module
basefunctions.setup_logger(__name__)

# Get logger instance
logger = basefunctions.get_logger(__name__)

# Use the logger
logger.info("Application started")
logger.warning("Resource usage high")
logger.error("Failed to connect to database")
```

### 2. Enable Console Output

```python
import basefunctions

# Setup logging for modules
basefunctions.setup_logger("myapp.core")
basefunctions.setup_logger("myapp.database")

# Enable console output globally
basefunctions.enable_console(level="INFO")

# Now all configured modules will log to console
logger = basefunctions.get_logger("myapp.core")
logger.info("This will appear on console")
```

### 3. Module-Specific Configuration

```python
import basefunctions

# Configure specific module with DEBUG level and force console ON
basefunctions.configure_module_logging(
    "myapp.http",
    level="DEBUG",
    console=True,
    console_level="INFO"
)

logger = basefunctions.get_logger("myapp.http")
logger.debug("Detailed HTTP request info")  # Logged to file (if configured)
logger.info("HTTP request completed")        # Logged to console AND file
```

---

## Core Concepts

### Logging Hierarchy

The logging system uses **hierarchical logger names** based on Python's module structure:

```
myapp
├── myapp.core
├── myapp.database
│   ├── myapp.database.connection
│   └── myapp.database.query
└── myapp.http
    ├── myapp.http.client
    └── myapp.http.server
```

**Best Practice**: Always use `__name__` when setting up loggers to maintain this hierarchy automatically.

```python
# In myapp/database/connection.py
basefunctions.setup_logger(__name__)  # Creates logger named "myapp.database.connection"
```

### Log Levels

The system supports standard Python log levels:

| Level      | Numeric Value | Use Case                                      |
|------------|---------------|-----------------------------------------------|
| `DEBUG`    | 10            | Detailed diagnostic information               |
| `INFO`     | 20            | General informational messages                |
| `WARNING`  | 30            | Warning messages (something unexpected)       |
| `ERROR`    | 40            | Error messages (functionality affected)       |
| `CRITICAL` | 50            | Critical errors (system may fail)             |

**Default**: `ERROR` (only errors and critical messages are logged)

### Silent by Default

```python
# WITHOUT setup_logger() - completely silent
import logging
logger = logging.getLogger("mymodule")
logger.error("This will NOT appear")  # Silenced

# WITH setup_logger() - enabled
import basefunctions
basefunctions.setup_logger("mymodule")
logger = basefunctions.get_logger("mymodule")
logger.error("This WILL be logged")  # Appears based on configuration
```

### Console vs File Output

- **Console Output**: Logs to `stderr` (visible in terminal)
- **File Output**: Logs to specified file path
- **Both**: You can have both console and file output simultaneously

**Control**:
- **Global Console Control**: `enable_console()` / `disable_console()`
- **Module-Specific Console Control**: `configure_module_logging(name, console=True/False)`
- **File Output**: Set via `setup_logger(name, file="path.log")` or `configure_module_logging(name, file="path.log")`

---

## Basic Usage

### Setting Up a Logger

**Pattern 1: Simple Setup (File Only)**

```python
import basefunctions

# Setup logger for this module, log to file
basefunctions.setup_logger(__name__, level="INFO", file="/tmp/myapp.log")

logger = basefunctions.get_logger(__name__)
logger.info("Application initialized")
```

**Pattern 2: Setup with Console**

```python
import basefunctions

# Setup logger
basefunctions.setup_logger(__name__, level="DEBUG")

# Enable console globally
basefunctions.enable_console(level="INFO")

logger = basefunctions.get_logger(__name__)
logger.debug("Debug info")  # Not shown on console (< INFO)
logger.info("Info message")  # Shown on console
```

**Pattern 3: Module-Specific Console**

```python
import basefunctions

# Setup logger with forced console output
basefunctions.configure_module_logging(
    __name__,
    level="DEBUG",
    console=True,        # Force console ON (ignores global disable_console)
    console_level="WARNING"  # Only show WARNING+ on console
)

logger = basefunctions.get_logger(__name__)
logger.debug("Debug message")    # Logged to file only
logger.warning("Warning message") # Logged to file AND console
```

### Logging Messages

```python
logger = basefunctions.get_logger(__name__)

# Standard logging calls
logger.debug("Detailed diagnostic information")
logger.info("Informational message")
logger.warning("Warning: something unexpected")
logger.error("Error: operation failed")
logger.critical("Critical: system failure imminent")

# With formatting
user_id = 12345
logger.info(f"User {user_id} logged in")
logger.error(f"Failed to process order {order_id}: {error_msg}")

# With exception info
try:
    risky_operation()
except Exception as e:
    logger.error(f"Operation failed: {e}", exc_info=True)
```

### Checking Logger Configuration

```python
# Get current configuration for a module
config = basefunctions.get_module_logging_config("myapp.http")

if config:
    print(f"Level: {config['level']}")                    # e.g., "DEBUG"
    print(f"Console override: {config['console']}")       # True/False/None
    print(f"Console level: {config['console_level']}")    # e.g., "INFO"
    print(f"File: {config['file']}")                      # e.g., "/tmp/myapp.log"
    print(f"Console enabled: {config['effective_console']}")  # True/False
else:
    print("Module not configured")
```

---

## Use Cases

### Use Case 1: Logging in CLI Applications

```python
import basefunctions

class MyCLIApp(basefunctions.CLIApplication):
    def __init__(self):
        super().__init__("myapp", version="1.0.0")

        # Setup logging for CLI components
        basefunctions.setup_logger("myapp.cli", level="INFO")
        basefunctions.setup_logger("myapp.commands", level="DEBUG")

        # Enable console for user feedback
        basefunctions.enable_console(level="INFO")

        self.logger = basefunctions.get_logger("myapp.cli")

    def run(self):
        self.logger.info("Starting CLI application")
        # ... application logic
```

**Output**:
```
myapp.cli - INFO - Starting CLI application
```

### Use Case 2: EventBus Integration

```python
import basefunctions

# Setup logging for EventBus and handlers
basefunctions.setup_logger("basefunctions.events.event_bus", level="DEBUG")
basefunctions.setup_logger("myapp.handlers", level="INFO")

# Enable console only for WARNING+ messages
basefunctions.enable_console(level="WARNING")

# EventBus will now log its operations
bus = basefunctions.EventBus()
event = basefunctions.Event("process_data", data={"key": "value"})
bus.publish_event(event)
```

### Use Case 3: HTTP Client Debugging

```python
import basefunctions

# Enable DEBUG logging for HTTP client
basefunctions.configure_module_logging(
    "basefunctions.http.http_client",
    level="DEBUG",
    console=True,
    console_level="DEBUG"
)

# Use HTTP client with detailed logging
client = basefunctions.HttpClient()
response = client.get("https://api.example.com/data")

# You'll see detailed request/response logs on console
```

### Use Case 4: Structured Logging with Context

```python
import basefunctions

basefunctions.setup_logger(__name__, level="INFO")
logger = basefunctions.get_logger(__name__)

def process_order(order_id, customer_id):
    # Log with structured context
    logger.info(
        f"Processing order | order_id={order_id} | customer_id={customer_id}"
    )

    try:
        # Business logic
        result = perform_payment(order_id)
        logger.info(
            f"Payment successful | order_id={order_id} | amount={result['amount']}"
        )
    except Exception as e:
        logger.error(
            f"Payment failed | order_id={order_id} | error={str(e)}",
            exc_info=True
        )
```

### Use Case 5: Performance Logging

```python
import basefunctions
import time

basefunctions.setup_logger(__name__, level="INFO")
logger = basefunctions.get_logger(__name__)

@basefunctions.function_timer  # Decorator logs execution time
def expensive_operation(data):
    logger.info(f"Starting expensive operation | data_size={len(data)}")

    start_time = time.time()
    # ... processing
    duration = time.time() - start_time

    logger.info(f"Operation completed | duration={duration:.2f}s")
    return result

# Logs:
# - Function timer decorator output
# - Custom performance metrics
```

### Use Case 6: Debug vs Production Logging

**Development Environment**:
```python
import basefunctions
import os

# In development: verbose logging
if os.getenv("ENV") == "development":
    basefunctions.setup_logger("myapp", level="DEBUG")
    basefunctions.enable_console(level="DEBUG")
else:
    # In production: minimal logging
    basefunctions.setup_logger("myapp", level="ERROR")
    basefunctions.redirect_all_to_file("/var/log/myapp/app.log", level="ERROR")
```

### Use Case 7: Component-Specific Logging

```python
import basefunctions

# Different log levels for different components
basefunctions.setup_logger("myapp.database", level="INFO")
basefunctions.setup_logger("myapp.cache", level="WARNING")
basefunctions.setup_logger("myapp.api", level="DEBUG")

# Enable console for all
basefunctions.enable_console(level="INFO")

# But override console level for API (too verbose)
basefunctions.configure_module_logging(
    "myapp.api",
    console_level="WARNING"  # Only show warnings on console
)

# Usage
db_logger = basefunctions.get_logger("myapp.database")
cache_logger = basefunctions.get_logger("myapp.cache")
api_logger = basefunctions.get_logger("myapp.api")

db_logger.info("Database query executed")      # Console + file
cache_logger.info("Cache hit")                  # Not logged (< WARNING)
api_logger.debug("API request details")         # File only
api_logger.warning("API rate limit approaching") # Console + file
```

---

## Module-Specific Logging

### Logger Naming Convention

Use `__name__` to automatically create hierarchical logger names:

```python
# In myapp/database/connection.py
basefunctions.setup_logger(__name__)  # Logger: "myapp.database.connection"

# In myapp/database/query.py
basefunctions.setup_logger(__name__)  # Logger: "myapp.database.query"

# In myapp/http/client.py
basefunctions.setup_logger(__name__)  # Logger: "myapp.http.client"
```

**Benefits**:
- Organized hierarchy matching your code structure
- Easy to filter logs by subsystem
- Clear identification of log source

### Per-Module Configuration

Configure each module independently:

```python
import basefunctions

# Core module: INFO level, console enabled
basefunctions.configure_module_logging(
    "myapp.core",
    level="INFO",
    console=True
)

# Database module: DEBUG level, file output
basefunctions.configure_module_logging(
    "myapp.database",
    level="DEBUG",
    file="/var/log/myapp/database.log"
)

# HTTP module: DEBUG level, separate console level
basefunctions.configure_module_logging(
    "myapp.http",
    level="DEBUG",
    console=True,
    console_level="WARNING"  # Only warnings on console
)

# Cache module: WARNING level, console disabled
basefunctions.configure_module_logging(
    "myapp.cache",
    level="WARNING",
    console=False  # Never show on console
)
```

### Module Override Behavior

**Console Override Rules**:

1. `console=True` → **Always show on console** (ignores global `disable_console()`)
2. `console=False` → **Never show on console** (ignores global `enable_console()`)
3. `console=None` → **Follow global setting** (default behavior)

**Example**:

```python
import basefunctions

# Setup modules
basefunctions.setup_logger("myapp.core")
basefunctions.setup_logger("myapp.http")
basefunctions.setup_logger("myapp.cache")

# Configure module-specific overrides
basefunctions.configure_module_logging("myapp.http", console=True)   # Force ON
basefunctions.configure_module_logging("myapp.cache", console=False) # Force OFF

# Disable console globally
basefunctions.disable_console()

# Results:
# - myapp.core: No console output (follows global disable)
# - myapp.http: Console output ENABLED (override to True)
# - myapp.cache: No console output (override to False)

# Enable console globally
basefunctions.enable_console()

# Results:
# - myapp.core: Console output enabled (follows global enable)
# - myapp.http: Console output ENABLED (override to True)
# - myapp.cache: No console output (override to False)
```

### Console Level Overrides

Control console verbosity separately from logger level:

```python
import basefunctions

# Setup: DEBUG to file, INFO to console
basefunctions.configure_module_logging(
    "myapp.api",
    level="DEBUG",           # Log everything at DEBUG+
    console=True,
    console_level="INFO"     # But only show INFO+ on console
)

logger = basefunctions.get_logger("myapp.api")

logger.debug("Detailed request parsing")   # File only
logger.info("Request processed")            # File + Console
logger.warning("Rate limit warning")        # File + Console
```

---

## Logging Control

### Global Console Control

#### Enable Console Output

```python
import basefunctions

# Enable console for all configured modules
basefunctions.enable_console(level="INFO")
```

**Parameters**:
- `level`: Minimum log level for console (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`)

**Behavior**:
- Adds console handler to all modules (unless module has `console=False` override)
- Existing file handlers remain active
- Safe to call multiple times (removes old console handler before adding new one)

#### Disable Console Output

```python
import basefunctions

# Disable console for all modules
basefunctions.disable_console()
```

**Behavior**:
- Removes console handlers from all modules (unless module has `console=True` override)
- File handlers remain active
- Useful for production environments where logs go only to files

### File Output Control

#### Module-Specific File Output

```python
import basefunctions

# Setup logger with file output
basefunctions.setup_logger(
    "myapp.database",
    level="DEBUG",
    file="/var/log/myapp/database.log"
)
```

#### Global File Output

Redirect all configured modules to a single file:

```python
import basefunctions

# Setup multiple modules
basefunctions.setup_logger("myapp.core")
basefunctions.setup_logger("myapp.database")
basefunctions.setup_logger("myapp.http")

# Redirect all to single file
basefunctions.redirect_all_to_file(
    file="/var/log/myapp/all.log",
    level="DEBUG"
)
```

**Note**: Individual module file handlers remain active. The global file handler is **added** to all modules.

### Runtime Configuration Changes

Change logging configuration while application is running:

```python
import basefunctions

# Initial setup
basefunctions.setup_logger("myapp.http", level="ERROR")

# Later: enable debug logging for troubleshooting
basefunctions.configure_module_logging("myapp.http", level="DEBUG", console=True)

# Even later: reduce verbosity
basefunctions.configure_module_logging("myapp.http", level="WARNING")

# Disable console for this module
basefunctions.configure_module_logging("myapp.http", console=False)
```

### Checking Current Configuration

```python
import basefunctions

# Get configuration for a module
config = basefunctions.get_module_logging_config("myapp.http")

if config:
    print(f"Logger level: {config['level']}")              # "DEBUG"
    print(f"Console override: {config['console']}")        # True/False/None
    print(f"Console level: {config['console_level']}")     # "INFO" or None
    print(f"File path: {config['file']}")                  # "/path/to/file.log" or None
    print(f"Console active: {config['effective_console']}") # True/False (final result)
```

---

## Configuration

### Programmatic Configuration

**Example 1: Simple Application**

```python
import basefunctions

def setup_logging():
    # Setup logging for all app modules
    basefunctions.setup_logger("myapp.core", level="INFO")
    basefunctions.setup_logger("myapp.database", level="DEBUG")
    basefunctions.setup_logger("myapp.api", level="INFO")

    # Enable console for interactive use
    basefunctions.enable_console(level="INFO")

# Call at app startup
setup_logging()
```

**Example 2: Environment-Based Configuration**

```python
import basefunctions
import os

def setup_logging():
    env = os.getenv("APP_ENV", "production")

    if env == "development":
        # Development: verbose logging
        basefunctions.setup_logger("myapp", level="DEBUG")
        basefunctions.enable_console(level="DEBUG")

    elif env == "staging":
        # Staging: moderate logging
        basefunctions.setup_logger("myapp", level="INFO")
        basefunctions.enable_console(level="INFO")
        basefunctions.redirect_all_to_file("/var/log/myapp/staging.log")

    else:  # production
        # Production: minimal logging, file only
        basefunctions.setup_logger("myapp", level="ERROR")
        basefunctions.redirect_all_to_file("/var/log/myapp/production.log")
        basefunctions.disable_console()

setup_logging()
```

**Example 3: Configuration from Dictionary**

```python
import basefunctions

LOGGING_CONFIG = {
    "myapp.core": {
        "level": "INFO",
        "console": True,
        "file": None
    },
    "myapp.database": {
        "level": "DEBUG",
        "console": False,
        "file": "/var/log/myapp/db.log"
    },
    "myapp.api": {
        "level": "DEBUG",
        "console": True,
        "console_level": "WARNING",
        "file": "/var/log/myapp/api.log"
    }
}

def setup_logging_from_config(config):
    for module_name, module_config in config.items():
        basefunctions.configure_module_logging(
            module_name,
            level=module_config.get("level"),
            console=module_config.get("console"),
            console_level=module_config.get("console_level"),
            file=module_config.get("file")
        )

setup_logging_from_config(LOGGING_CONFIG)
```

### ConfigHandler Integration

The logging system integrates with `basefunctions.ConfigHandler`:

```python
import basefunctions

# config.json structure:
# {
#   "myapp": {
#     "logging": {
#       "enabled": true,
#       "level": "INFO",
#       "modules": {
#         "myapp.core": {
#           "level": "INFO",
#           "console": true
#         },
#         "myapp.database": {
#           "level": "DEBUG",
#           "file": "/var/log/myapp/db.log"
#         }
#       }
#     }
#   }
# }

def setup_logging_from_config_handler():
    config = basefunctions.ConfigHandler()
    logging_config = config.get("myapp.logging")

    if not logging_config.get("enabled"):
        return

    # Configure modules
    for module_name, module_cfg in logging_config.get("modules", {}).items():
        basefunctions.configure_module_logging(
            module_name,
            level=module_cfg.get("level"),
            console=module_cfg.get("console"),
            console_level=module_cfg.get("console_level"),
            file=module_cfg.get("file")
        )

    # Enable console if configured
    if logging_config.get("console_enabled"):
        basefunctions.enable_console(level=logging_config.get("level", "INFO"))

setup_logging_from_config_handler()
```

### Handler and Formatter Configuration

The logging system uses standard Python `logging` formatters:

**Default Formatters**:

- **Console**: `"%(name)s - %(levelname)s - %(message)s"`
  ```
  myapp.core - INFO - Application started
  ```

- **File**: `"%(asctime)s - %(name)s - %(levelname)s - %(message)s"`
  ```
  2025-01-15 14:30:22,123 - myapp.core - INFO - Application started
  ```

**Custom Formatter** (advanced):

```python
import basefunctions
import logging

# Setup basic logger
basefunctions.setup_logger("myapp.custom", level="INFO")

# Get logger and customize formatter
logger_config = basefunctions._logger_configs["myapp.custom"]
logger = logger_config["logger"]

# Create custom formatter
custom_formatter = logging.Formatter(
    fmt="[%(asctime)s] %(name)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Apply to all handlers
for handler in logger.handlers:
    handler.setFormatter(custom_formatter)

# Now logs will use custom format
logger.info("Custom formatted message")
```

---

## Advanced Features

### Thread-Safe Operation

The logging system is fully thread-safe using `threading.Lock`:

```python
import basefunctions
import threading

basefunctions.setup_logger("myapp.worker", level="INFO")
basefunctions.enable_console()

def worker_task(worker_id):
    logger = basefunctions.get_logger("myapp.worker")
    logger.info(f"Worker {worker_id} started")
    # ... work
    logger.info(f"Worker {worker_id} completed")

# Safe to use in multiple threads
threads = [
    threading.Thread(target=worker_task, args=(i,))
    for i in range(10)
]

for thread in threads:
    thread.start()

for thread in threads:
    thread.join()
```

### EventBus Integration

The logging system works seamlessly with the EventBus:

```python
import basefunctions

# Enable logging for EventBus components
basefunctions.configure_module_logging(
    "basefunctions.events.event_bus",
    level="DEBUG",
    console=True,
    console_level="INFO"
)

basefunctions.configure_module_logging(
    "basefunctions.events.corelet_worker",
    level="DEBUG",
    console=True
)

# EventBus operations will now be logged
bus = basefunctions.EventBus()

class MyHandler(basefunctions.EventHandler):
    def __init__(self):
        basefunctions.setup_logger(__name__)
        self.logger = basefunctions.get_logger(__name__)

    def handle(self, event):
        self.logger.info(f"Handling event: {event.name}")
        return basefunctions.EventResult(success=True)

bus.register_handler("my_event", MyHandler())
event = basefunctions.Event("my_event", data={"key": "value"})
result = bus.publish_event(event)
```

### Output Redirection

Combine logging with output redirection:

```python
import basefunctions

# Setup logging
basefunctions.setup_logger("myapp.core", level="INFO")
logger = basefunctions.get_logger("myapp.core")

# Redirect stdout/stderr to file while keeping logs
with basefunctions.redirect_output(file="/tmp/output.txt"):
    # Regular print statements go to file
    print("This goes to file")

    # Logs go to configured handlers (console/file)
    logger.info("This goes to log handlers")
```

### Conditional Logging

Conditionally enable logging based on conditions:

```python
import basefunctions
import os

# Check environment variable or command-line flag
DEBUG_ENABLED = os.getenv("DEBUG", "false").lower() == "true"

if DEBUG_ENABLED:
    basefunctions.configure_module_logging(
        "myapp",
        level="DEBUG",
        console=True
    )
else:
    basefunctions.configure_module_logging(
        "myapp",
        level="WARNING",
        file="/var/log/myapp/errors.log"
    )
```

### Context-Aware Logging

Use structured logging with context:

```python
import basefunctions

basefunctions.setup_logger(__name__, level="INFO")
logger = basefunctions.get_logger(__name__)

class RequestContext:
    def __init__(self, request_id, user_id):
        self.request_id = request_id
        self.user_id = user_id
        self.logger = basefunctions.get_logger(__name__)

    def log_info(self, message):
        self.logger.info(
            f"[req={self.request_id}] [user={self.user_id}] {message}"
        )

    def log_error(self, message, exc=None):
        self.logger.error(
            f"[req={self.request_id}] [user={self.user_id}] {message}",
            exc_info=exc
        )

# Usage
ctx = RequestContext(request_id="abc123", user_id=456)
ctx.log_info("Processing payment")
ctx.log_error("Payment failed", exc=payment_exception)
```

---

## Best Practices

### 1. When to Use Which Log Level

| Level      | Use For                                                                 | Example                                          |
|------------|-------------------------------------------------------------------------|--------------------------------------------------|
| `DEBUG`    | Detailed diagnostic info for troubleshooting                            | "Parsed config: {config_dict}"                   |
| `INFO`     | General informational messages about app state                          | "Server started on port 8000"                    |
| `WARNING`  | Unexpected situations that don't prevent operation                      | "Cache miss for key 'user:123'"                  |
| `ERROR`    | Errors that prevent a specific operation                                | "Failed to save to database: {error}"            |
| `CRITICAL` | Severe errors that may cause application failure                        | "Out of memory, shutting down"                   |

### 2. Logger Setup Pattern

**Always use this pattern in modules**:

```python
import basefunctions

# At module level (top of file)
basefunctions.setup_logger(__name__)

# In class or function
logger = basefunctions.get_logger(__name__)
logger.info("Module loaded")
```

**Benefits**:
- Logger name matches module hierarchy
- Consistent setup across codebase
- Easy to configure entire subsystems

### 3. Avoid Logging in Tight Loops

**Bad**:
```python
for item in large_list:  # 1 million items
    logger.debug(f"Processing item {item}")  # Too verbose!
```

**Good**:
```python
logger.info(f"Processing {len(large_list)} items")
for i, item in enumerate(large_list):
    if i % 10000 == 0:  # Log every 10,000 items
        logger.debug(f"Processed {i}/{len(large_list)} items")
logger.info("Processing complete")
```

### 4. Use String Formatting Correctly

**Prefer f-strings** for readability:

```python
# Good
logger.info(f"User {user_id} performed action {action}")

# Also acceptable (lazy evaluation)
logger.debug("Processing data: %s", data)
```

**Avoid**:
```python
# Bad: concatenation
logger.info("User " + str(user_id) + " logged in")
```

### 5. Log Exceptions Properly

**Good**:
```python
try:
    risky_operation()
except Exception as e:
    logger.error(f"Operation failed: {e}", exc_info=True)  # Includes stack trace
```

**Better** (with context):
```python
try:
    risky_operation(param1, param2)
except Exception as e:
    logger.error(
        f"Operation failed | param1={param1} | param2={param2} | error={e}",
        exc_info=True
    )
```

### 6. Security: Never Log Secrets

**Bad**:
```python
logger.info(f"User logged in with password: {password}")  # NEVER!
logger.debug(f"API key: {api_key}")  # NEVER!
```

**Good**:
```python
logger.info(f"User {username} logged in")
logger.debug(f"API key: {api_key[:8]}***")  # Masked
```

### 7. Production vs Development Logging

**Development**:
```python
basefunctions.setup_logger("myapp", level="DEBUG")
basefunctions.enable_console(level="DEBUG")
```

**Production**:
```python
basefunctions.setup_logger("myapp", level="WARNING")
basefunctions.redirect_all_to_file("/var/log/myapp/app.log", level="INFO")
basefunctions.disable_console()
```

### 8. Module-Specific Verbosity

Configure different verbosity for different components:

```python
# Critical components: detailed logging
basefunctions.configure_module_logging("myapp.payment", level="DEBUG")
basefunctions.configure_module_logging("myapp.security", level="DEBUG")

# Less critical: errors only
basefunctions.configure_module_logging("myapp.cache", level="WARNING")
basefunctions.configure_module_logging("myapp.ui", level="WARNING")
```

### 9. Structured Log Messages

Use consistent formatting for machine parsing:

```python
# Good: structured, parseable
logger.info(f"event=user_login | user_id={user_id} | ip={ip_address} | timestamp={timestamp}")

# Also good: JSON-style
logger.info(f"{{ event: 'user_login', user_id: {user_id}, ip: '{ip_address}' }}")
```

### 10. Don't Log Personal Data (GDPR)

**Bad**:
```python
logger.info(f"User email: {email}")  # PII!
logger.info(f"User address: {address}")  # PII!
```

**Good**:
```python
# Hash or mask PII
import hashlib
user_hash = hashlib.sha256(email.encode()).hexdigest()[:16]
logger.info(f"User hash: {user_hash}")
```

---

## API Reference

### `setup_logger(name, level="ERROR", file=None)`

Enable logging for a specific module.

**Parameters**:
- `name` (str): Module name (use `__name__`)
- `level` (str, optional): Log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`). Default: `"ERROR"`
- `file` (str, optional): File path for logging output. Default: `None`

**Returns**: None

**Example**:
```python
basefunctions.setup_logger(__name__, level="INFO", file="/tmp/app.log")
```

---

### `get_logger(name)`

Get logger instance for a module.

**Parameters**:
- `name` (str): Module name (use `__name__`)

**Returns**: `logging.Logger` instance

**Example**:
```python
logger = basefunctions.get_logger(__name__)
logger.info("Message")
```

**Note**: If module not configured with `setup_logger()`, returns a silent logger.

---

### `enable_console(level="CRITICAL")`

Enable console output for all configured modules.

**Parameters**:
- `level` (str, optional): Minimum log level for console. Default: `"CRITICAL"`

**Returns**: None

**Example**:
```python
basefunctions.enable_console(level="INFO")
```

**Behavior**:
- Adds console handler to all modules (unless module has `console=False` override)
- Safe to call multiple times

---

### `disable_console()`

Disable console output for all modules.

**Parameters**: None

**Returns**: None

**Example**:
```python
basefunctions.disable_console()
```

**Behavior**:
- Removes console handlers from all modules (unless module has `console=True` override)

---

### `redirect_all_to_file(file, level="DEBUG")`

Redirect all configured modules to a single file.

**Parameters**:
- `file` (str): File path for all logging output
- `level` (str, optional): Minimum log level. Default: `"DEBUG"`

**Returns**: None

**Example**:
```python
basefunctions.redirect_all_to_file("/var/log/myapp/all.log", level="INFO")
```

**Behavior**:
- Adds global file handler to all configured loggers
- Individual module file handlers remain active

---

### `configure_module_logging(name, level=None, console=None, console_level=None, file=None)`

Configure or update logging for a specific module at runtime.

**Parameters**:
- `name` (str): Module name
- `level` (str, optional): Logger level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`)
- `console` (bool, optional): Enable/disable console for this module
  - `True`: Force console ON
  - `False`: Force console OFF
  - `None`: Follow global setting
- `console_level` (str, optional): Console-specific log level
- `file` (str, optional): File path for module output

**Returns**: None

**Raises**: `ValueError` if invalid log level provided

**Examples**:
```python
# Enable DEBUG logging with console
basefunctions.configure_module_logging("myapp.http", level="DEBUG", console=True)

# Different console level than logger level
basefunctions.configure_module_logging(
    "myapp.api",
    level="DEBUG",
    console=True,
    console_level="WARNING"
)

# Disable console for specific module
basefunctions.configure_module_logging("myapp.cache", console=False)
```

---

### `get_module_logging_config(name)`

Get current logging configuration for a module.

**Parameters**:
- `name` (str): Module name

**Returns**: `dict` or `None`

**Return Dictionary Keys**:
- `level` (str): Logger level
- `console` (bool or None): Console override setting
- `console_level` (str or None): Console-specific level
- `file` (str or None): File path
- `effective_console` (bool): Whether console is actually enabled for this module

**Example**:
```python
config = basefunctions.get_module_logging_config("myapp.http")
if config:
    print(f"Level: {config['level']}")
    print(f"Console enabled: {config['effective_console']}")
```

---

## Summary

The **basefunctions** logging system provides:

1. **Silent by Default**: No surprise output
2. **Explicit Configuration**: You control what gets logged
3. **Fine-Grained Control**: Per-module level, console, and file settings
4. **Global Switches**: Enable/disable console for all modules at once
5. **Module Overrides**: Modules can override global console settings
6. **Thread-Safe**: Safe for EventBus, CLI, and multi-threaded applications
7. **Zero Dependencies**: Pure Python stdlib

**Typical Workflow**:

```python
import basefunctions

# 1. Setup loggers for your modules
basefunctions.setup_logger("myapp.core", level="INFO")
basefunctions.setup_logger("myapp.database", level="DEBUG")

# 2. Enable console output
basefunctions.enable_console(level="INFO")

# 3. Get logger and use
logger = basefunctions.get_logger("myapp.core")
logger.info("Application started")

# 4. Configure modules at runtime
basefunctions.configure_module_logging("myapp.http", level="DEBUG", console=True)

# 5. Check configuration
config = basefunctions.get_module_logging_config("myapp.http")
print(config)
```

**Best Practices Recap**:

- ✅ Always use `__name__` for logger names
- ✅ Use appropriate log levels (`DEBUG` < `INFO` < `WARNING` < `ERROR` < `CRITICAL`)
- ✅ Never log secrets, passwords, or PII
- ✅ Use f-strings for readable formatting
- ✅ Include context in error messages
- ✅ Configure different verbosity for dev vs production
- ✅ Avoid logging in tight loops
- ✅ Use `exc_info=True` when logging exceptions

**KISSS**: Keep It Simple, Stupid, Safe.
