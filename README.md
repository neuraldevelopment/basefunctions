# basefunctions

A comprehensive Python framework providing essential base functionalities for Python development, including event-driven messaging, CLI applications, runtime management, I/O utilities, and more.

[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

`basefunctions` is designed to accelerate Python application development by providing robust, production-ready implementations of common patterns and utilities. Whether you're building CLI tools, event-driven systems, or data processing pipelines, basefunctions offers the building blocks you need.

## Key Features

- **Event-Driven Messaging**: Powerful EventBus with sync, threaded, and process-based execution modes
- **CLI Framework**: Full-featured command-line application framework with tab completion
- **Runtime Management**: Deployment management with version control and virtual environment utilities
- **I/O Utilities**: Comprehensive file operations, serialization (JSON, YAML, Pickle, MessagePack), and output redirection
- **Configuration Management**: Secure configuration and secrets handling
- **Decorators**: Collection of useful decorators (caching, timing, retry, thread-safety, etc.)
- **Observer Pattern**: Observable and Observer implementations
- **HTTP Client**: Event-based HTTP client with handler system
- **Pandas Extensions**: Custom accessors for DataFrame and Series
- **Time Utilities**: Comprehensive datetime handling with timezone support
- **Logging**: Advanced logging setup with console/file redirection

## Installation

### From PyPI (when published)

```bash
pip install basefunctions
```

### From Source

```bash
# Clone the repository
git clone https://github.com/neuraldevelopment/basefunctions.git
cd basefunctions

# Install in development mode with all dependencies
pip install -e ".[dev,test]"
```

## Quick Start

### Event-Driven Messaging

The EventBus provides a powerful pub-sub system with multiple execution modes:

```python
from basefunctions import EventBus, Event, EventHandler, EventResult

# Define a custom event handler
class MyHandler(EventHandler):
    def handle(self, event):
        data = event.data
        print(f"Processing: {data}")
        return EventResult(success=True, data={"processed": True})

# Get EventBus singleton and register handler
bus = EventBus()
bus.register_handler("my_event", MyHandler())

# Publish an event
event = Event("my_event", data={"message": "Hello World"})
result = bus.publish_event(event)

print(f"Success: {result.success}, Data: {result.data}")
```

**Execution Modes:**
- `EXECUTION_MODE_SYNC`: Synchronous execution in the same thread
- `EXECUTION_MODE_THREAD`: Asynchronous execution in thread pool
- `EXECUTION_MODE_CORELET`: Process-based execution for CPU-intensive tasks

```python
from basefunctions import Event, EXECUTION_MODE_THREAD

# Create event with thread-based execution
event = Event("my_event", execution_mode=EXECUTION_MODE_THREAD, data={"key": "value"})
```

### CLI Application Framework

Build professional command-line applications with minimal boilerplate:

```python
from basefunctions import CLIApplication, BaseCommand, ArgumentSpec, CommandMetadata

# Define commands
class MyCommands(BaseCommand):
    def get_metadata(self):
        return {
            "greet": CommandMetadata(
                name="greet",
                description="Greet a user",
                arguments=[
                    ArgumentSpec(name="name", help="Name to greet", required=True),
                    ArgumentSpec(name="--formal", help="Use formal greeting", is_flag=True)
                ]
            )
        }

    def cmd_greet(self, args):
        """Greet command implementation"""
        greeting = "Good day" if args.formal else "Hi"
        return f"{greeting}, {args.name}!"

# Create and run application
app = CLIApplication("myapp", version="1.0", enable_completion=True)
app.register_command_group("", MyCommands())  # Root-level commands

# Run the application
app.run()
```

**Features:**
- Automatic help generation
- Tab completion support
- Command grouping
- Argument parsing with type hints
- Progress tracking
- Context management

### File and Serialization Utilities

Comprehensive I/O operations with multiple serialization formats:

```python
from basefunctions import serialize, deserialize, to_file, from_file

# Serialize data
data = {"users": ["Alice", "Bob"], "count": 2}

# JSON
json_str = serialize(data, format="json")

# Save to file (format auto-detected from extension)
to_file(data, "data.json")  # JSON
to_file(data, "data.yaml")  # YAML
to_file(data, "data.pkl")   # Pickle

# Load from file
loaded = from_file("data.json")
print(loaded)  # {'users': ['Alice', 'Bob'], 'count': 2}
```

**Supported formats:** JSON, YAML, Pickle, MessagePack

### Configuration and Secrets Management

Secure configuration handling with environment variable support:

```python
from basefunctions import ConfigHandler, SecretHandler

# Configuration management
config = ConfigHandler()
config.load_config_for_package("myapp")
api_url = config.get("api.url", default="https://api.example.com")

# Secrets management (encrypted storage)
secrets = SecretHandler()
secrets.set("api_key", "secret-key-here")
api_key = secrets.get("api_key")
```

### Decorators

Powerful decorators for common tasks:

```python
from basefunctions import (
    function_timer,
    cache_results,
    retry_on_exception,
    singleton,
    thread_safe
)

@function_timer
@cache_results(max_size=100, ttl=300)
def expensive_computation(x, y):
    """This function's execution time is logged and results are cached"""
    return x ** y

@retry_on_exception(max_attempts=3, delay=1.0)
def unstable_network_call():
    """Automatically retries on failure"""
    # Make network request
    pass

@singleton
class DatabaseConnection:
    """Only one instance will ever exist"""
    pass

@thread_safe
def update_shared_resource(value):
    """Thread-safe access with automatic locking"""
    pass
```

**Available decorators:**
- `function_timer` - Log execution time
- `cache_results` - LRU caching with TTL
- `retry_on_exception` - Automatic retry logic
- `singleton` - Singleton pattern
- `thread_safe` - Thread synchronization
- `catch_exceptions` - Exception handling
- `profile_memory` - Memory profiling
- `warn_if_slow` - Performance warnings
- `assert_non_null_args` - Input validation
- `suppress` - Suppress specific exceptions

### Observer Pattern

Implement the observer pattern with built-in support:

```python
from basefunctions import Observable, Observer

class DataProcessor(Observable):
    def process(self, data):
        # Do processing
        result = {"processed": data}
        # Notify observers
        self.notify_observers("data_processed", result)

class Logger(Observer):
    def update(self, observable, event_type, data):
        print(f"Event: {event_type}, Data: {data}")

# Setup
processor = DataProcessor()
logger = Logger()
processor.add_observer(logger)

# Process data - logger will be notified
processor.process("test data")
```

### Time Utilities

Comprehensive datetime handling with timezone support:

```python
from basefunctions import (
    now_utc,
    now_local,
    format_iso,
    parse_iso,
    to_timezone,
    datetime_to_timestamp
)

# Get current time
utc_time = now_utc()
local_time = now_local()

# Format datetime
iso_string = format_iso(utc_time)  # "2025-01-15T10:30:00Z"

# Parse ISO string
dt = parse_iso("2025-01-15T10:30:00Z")

# Convert timezone
tokyo_time = to_timezone(utc_time, "Asia/Tokyo")

# Unix timestamp
timestamp = datetime_to_timestamp(utc_time)
```

### Cache Management

Flexible caching with multiple backends:

```python
from basefunctions import get_cache, CacheFactory

# Get default memory cache
cache = get_cache()
cache.set("key", "value", ttl=3600)
value = cache.get("key")

# Create custom cache with different backend
file_cache = CacheFactory.create("file", cache_dir="/tmp/cache")
file_cache.set("data", {"important": "info"})

# Multi-level cache (memory + file)
multi_cache = CacheFactory.create("multi", backends=["memory", "file"])
```

**Supported backends:** Memory, File, Database, Multi-level

### Output Redirection

Redirect stdout/stderr to files, memory, or databases:

```python
from basefunctions import redirect_output, FileTarget, MemoryTarget

# Redirect to file
with redirect_output(FileTarget("/tmp/output.log")):
    print("This goes to the file")

# Capture in memory
memory = MemoryTarget()
with redirect_output(memory):
    print("This is captured")

captured = memory.get_content()
print(f"Captured: {captured}")
```

### HTTP Client

Event-based HTTP client with handler system:

```python
from basefunctions import HttpClient, EventBus

# HTTP client uses EventBus for requests
client = HttpClient(base_url="https://api.example.com")

# Make requests
response = client.get("/users")
response = client.post("/users", json={"name": "Alice"})
```

### Runtime and Deployment Management

Manage application deployment and virtual environments:

```python
from basefunctions import (
    DeploymentManager,
    VenvUtils,
    get_runtime_path,
    get_runtime_config_path
)

# Deployment management
manager = DeploymentManager()
changed, version = manager.deploy_module("mymodule", force=False)

# Virtual environment utilities
venv = VenvUtils()
venv.create("/path/to/venv")
venv.install_package("requests")

# Runtime paths
runtime_path = get_runtime_path("myapp")
config_path = get_runtime_config_path("myapp")
```

### Pandas Extensions

Custom DataFrame and Series accessors:

```python
from basefunctions import PandasDataFrame, PandasSeries
import pandas as pd

# Extended DataFrame functionality
df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
# Custom accessors available through df.bf.*
```

### Logging

Advanced logging setup:

```python
from basefunctions import setup_logger, get_logger

# Setup logger for module
setup_logger(__name__)
logger = get_logger(__name__)

logger.info("Application started")
logger.error("Something went wrong", exc_info=True)

# Redirect all output to file
from basefunctions import redirect_all_to_file
redirect_all_to_file("/var/log/myapp.log")
```

## Architecture

### Module Structure

```
basefunctions/
   cli/              # CLI framework (commands, parsers, completion)
   config/           # ConfigHandler, SecretHandler
   events/           # EventBus, Event, EventHandler, Corelet workers
   http/             # HttpClient, HttpClientHandler
   io/               # File operations, serialization, output redirection
   pandas/           # Pandas accessor extensions
   runtime/          # DeploymentManager, VenvUtils, version management
   utils/            # Decorators, logging, caching, observers, time utils
```

### Design Patterns

- **Singleton Pattern**: EventBus, ConfigHandler, SecretHandler, DeploymentManager
- **Observer Pattern**: Observable/Observer for event propagation
- **Factory Pattern**: SerializerFactory, CacheFactory
- **Decorator Pattern**: Extensive decorator collection for cross-cutting concerns
- **Strategy Pattern**: Multiple cache backends, serialization formats

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/neuraldevelopment/basefunctions.git
cd basefunctions

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate  # On Windows

# Install development dependencies
pip install -e ".[dev,test]"
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=basefunctions tests/

# Run specific test file
pytest tests/test_event_bus.py
```

### Code Quality

```bash
# Format code (Black with 119 char line length)
black --line-length 119 src/

# Lint with flake8
flake8 --max-line-length=99 src/

# Lint with pylint
pylint src/basefunctions
```

### Building

```bash
# Build package
python -m build

# This creates distribution files in dist/
```

## Requirements

- Python >= 3.12
- Dependencies:
  - `pandas >= 2.0`
  - `psutil >= 7.0`
  - `pyyaml >= 6.0`
  - `requests >= 2.32`
  - `tabulate >= 0.9`
  - `tqdm >= 4.67`
  - `load_dotenv >= 0.1`

## Contributing

Contributions are welcome! Please ensure:

1. Code follows Black formatting (119 char line length)
2. Tests pass (`pytest tests/`)
3. Type hints are included
4. Docstrings follow NumPy style
5. New features include tests and documentation

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Authors

**neuraldevelopment**
Email: neutro2@outlook.de

## Acknowledgments

- Built with Python 3.12+
- Uses industry-standard libraries (pandas, pyyaml, requests, tqdm)
- Inspired by best practices from the Python community

## Support

For issues, questions, or contributions:
- GitHub Issues: [https://github.com/neuraldevelopment/basefunctions/issues](https://github.com/neuraldevelopment/basefunctions/issues)
- Email: neutro2@outlook.de

## Documentation

For detailed documentation on specific modules, see the `docs/` directory:

| Module | Documentation |
|--------|---------------|
| **Overview** | [docs/basefunctions_overview.md](docs/basefunctions_overview.md) |
| **CLI** | [docs/cli/cli_module_guide.md](docs/cli/cli_module_guide.md) |
| **Config** | [docs/config/config_module_guide.md](docs/config/config_module_guide.md) |
| **Events** | [docs/events/eventbus_usage_guide.md](docs/events/eventbus_usage_guide.md) |
| **HTTP** | [docs/http/http_module_guide.md](docs/http/http_module_guide.md) |
| **I/O** | [docs/io/io_module_guide.md](docs/io/io_module_guide.md) |
| **Pandas** | [docs/pandas/pandas_module_guide.md](docs/pandas/pandas_module_guide.md) |
| **Runtime** | [docs/runtime/runtime_module_guide.md](docs/runtime/runtime_module_guide.md) |
| **Utils** | [docs/utils/utils_module_guide.md](docs/utils/utils_module_guide.md) |

Each module guide contains:
- Detailed API reference
- Usage examples
- Best practices
- Common patterns
- Integration guides

---

**Version**: 0.5.32
**Last Updated**: 2025-01-24
**Copyright** (c) 2023-2025 neuraldevelopment, Munich
