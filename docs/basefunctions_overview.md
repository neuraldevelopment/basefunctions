# Basefunctions Framework - Complete Overview

**Version:** 0.5.24
**Python:** >= 3.12
**License:** MIT

---

## Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Architecture](#architecture)
4. [Module Overview](#module-overview)
5. [Quick Start](#quick-start)
6. [Key Concepts](#key-concepts)
7. [Common Patterns](#common-patterns)
8. [Development](#development)
9. [API Overview](#api-overview)
10. [Documentation Links](#documentation-links)

---

## Overview

### What is basefunctions?

**basefunctions** is a comprehensive Python framework providing essential base functionalities for professional Python development. It accelerates application development by offering robust, production-ready implementations of common patterns and utilities.

### Vision and Goals

**Vision**: Provide a unified, reliable foundation for Python applications with emphasis on:
- **Event-driven architecture** for decoupled, scalable systems
- **CLI framework** for professional command-line applications
- **Production-ready utilities** for I/O, configuration, deployment, and more
- **Clean abstractions** following SOLID principles
- **Zero-surprise behavior** with explicit configuration

**Goals**:
- Reduce boilerplate code in Python projects
- Provide thread-safe, concurrent-ready components
- Offer flexible execution modes (sync, async, process-based)
- Enable rapid development without sacrificing code quality
- Maintain backward compatibility and stability

### Key Features

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
- **Cache Management**: Flexible caching with multiple backends (memory, file, database, multi-level)

---

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

### Development Setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate  # On Windows

# Install development dependencies
pip install -e ".[dev,test,docs]"
```

### Dependencies

**Core Dependencies:**
- `pandas >= 2.0` - Data manipulation
- `psutil >= 7.0` - Process and system utilities
- `pyyaml >= 6.0` - YAML serialization
- `requests >= 2.32` - HTTP client
- `tabulate >= 0.9` - Table formatting
- `tqdm >= 4.67` - Progress bars
- `load_dotenv >= 0.1` - Environment variables

**Development Dependencies:**
- `pytest >= 7.0` - Testing framework
- `autopep8 >= 2.0` - Code formatting
- `black >= 24.0` - Code formatter
- `flake8 >= 7.0` - Linting
- `pylint >= 3.0` - Static analysis

---

## Architecture

### Design Philosophy

**basefunctions** follows these core principles:

1. **KISSS (Keep It Simple, Stupid, Safe)**: Simplicity and safety over complexity
2. **Explicit over Implicit**: Configuration must be explicit (e.g., logging silent by default)
3. **Singleton Pattern**: Core services are singletons (EventBus, ConfigHandler, etc.)
4. **Thread-Safe by Design**: All components are thread-safe for concurrent use
5. **Layered Architecture**: Clear separation between framework layers
6. **Plugin-Based**: Extensible through handlers, commands, and backends

### Module Structure

```
basefunctions/
├── cli/              # CLI framework (commands, parsers, completion)
│   ├── argument_parser.py       # Argument parsing
│   ├── base_command.py          # Command base class
│   ├── cli_application.py       # CLI app orchestrator
│   ├── command_metadata.py      # Command definitions
│   ├── command_registry.py      # Command registry
│   ├── completion_handler.py    # Tab completion
│   ├── context_manager.py       # Execution context
│   ├── help_formatter.py        # Help text generation
│   ├── output_formatter.py      # Output formatting
│   └── progress_tracker.py      # Progress tracking
│
├── config/           # Configuration and secrets management
│   ├── config_handler.py        # Config loading/access
│   └── secret_handler.py        # Secure credential storage
│
├── events/           # Event-driven messaging system
│   ├── event.py                 # Event data class
│   ├── event_bus.py             # Central event dispatcher
│   ├── event_context.py         # Execution context
│   ├── event_exceptions.py      # Event-specific exceptions
│   ├── event_factory.py         # Handler registry
│   ├── event_handler.py         # Handler base classes
│   ├── corelet_worker.py        # Process-based workers
│   └── timer_thread.py          # Timeout handling
│
├── http/             # HTTP client system
│   ├── http_client.py           # HTTP client
│   └── http_client_handler.py   # Event handlers for HTTP
│
├── io/               # I/O utilities
│   ├── filefunctions.py         # File operations
│   ├── output_redirector.py     # stdout/stderr redirection
│   └── serializer.py            # Multi-format serialization
│
├── pandas/           # Pandas extensions
│   ├── accessors.py             # Custom DataFrame/Series accessors
│   └── __init__.py
│
├── runtime/          # Runtime and deployment management
│   ├── deployment_manager.py    # Module deployment
│   ├── venv_utils.py            # Virtual environment utilities
│   ├── runtime_paths.py         # Path resolution
│   ├── version.py               # Version management
│   └── bootstrap.py             # Bootstrap structure
│
└── utils/            # Utility functions and helpers
    ├── cache_manager.py         # Caching system
    ├── decorators.py            # Decorator collection
    ├── demo_runner.py           # Demo/test runner
    ├── logging.py               # Logging framework
    ├── observer.py              # Observer pattern
    ├── ohlcv_generator.py       # OHLCV data generation
    ├── progress_tracker.py      # Progress tracking
    └── time_utils.py            # Datetime utilities
```

### Design Patterns

**1. Singleton Pattern**

Core services maintain single instances per process:
- `EventBus` - Central event dispatcher
- `EventFactory` - Handler registry
- `ConfigHandler` - Configuration manager
- `SecretHandler` - Secrets manager
- `DeploymentManager` - Deployment controller

**2. Observer Pattern**

Event propagation and state notifications:
- `Observable` / `Observer` classes
- EventBus pub-sub model
- Progress tracking

**3. Factory Pattern**

Object creation and registration:
- `SerializerFactory` - Multi-format serializers
- `CacheFactory` - Cache backend creation
- `EventFactory` - Handler instantiation

**4. Decorator Pattern**

Cross-cutting concerns via decorators:
- `@function_timer` - Execution time logging
- `@cache_results` - LRU caching with TTL
- `@retry_on_exception` - Automatic retry
- `@singleton` - Singleton enforcement
- `@thread_safe` - Thread synchronization

**5. Strategy Pattern**

Pluggable implementations:
- Multiple cache backends (memory, file, database)
- Multiple serialization formats (JSON, YAML, Pickle, MessagePack)
- Multiple execution modes (SYNC, THREAD, CORELET, CMD)

**6. Command Pattern**

CLI framework command execution:
- `BaseCommand` subclasses
- `CommandRegistry` management
- Undo/redo support via context

---

## Module Overview

### CLI Framework

**Purpose**: Build professional command-line applications with minimal boilerplate.

**Key Components**:
- `CLIApplication` - Main application orchestrator
- `BaseCommand` - Base class for command handlers
- `CommandRegistry` - Command group management
- `CompletionHandler` - Tab completion support
- `ArgumentParser` - Advanced argument parsing
- `ProgressTracker` - Progress visualization

**Use Cases**:
- Building CLI tools and utilities
- Interactive command-line interfaces
- Deployment scripts with progress tracking
- Developer tools with tab completion

**Example**:
```python
from basefunctions import CLIApplication, BaseCommand, CommandMetadata, ArgumentSpec

class MyCommands(BaseCommand):
    def get_metadata(self):
        return {
            "hello": CommandMetadata(
                name="hello",
                description="Greet the user",
                arguments=[
                    ArgumentSpec(name="name", help="Name to greet", required=True)
                ]
            )
        }

    def cmd_hello(self, args):
        return f"Hello, {args.name}!"

app = CLIApplication("myapp", version="1.0")
app.register_command_group("", MyCommands())
app.run()
```

**Learn More**: See `/docs/cli/CLI_FRAMEWORK_GUIDE.md` (coming soon)

---

### Config & Secrets

**Purpose**: Manage application configuration and secure credentials.

**Key Components**:
- `ConfigHandler` - Load and access configuration from JSON files
- `SecretHandler` - Encrypted storage for sensitive data

**Use Cases**:
- Loading application settings from config files
- Environment-specific configuration
- Secure API key storage
- Database credential management

**Example**:
```python
from basefunctions import ConfigHandler, SecretHandler

# Configuration
config = ConfigHandler()
config.load_config_for_package("myapp")
api_url = config.get("api.base_url", default="https://api.example.com")

# Secrets
secrets = SecretHandler()
secrets.set("api_key", "secret-key-12345")
api_key = secrets.get("api_key")
```

**Learn More**: See `/docs/config/CONFIG_GUIDE.md` (coming soon)

---

### Events (EventBus)

**Purpose**: Event-driven messaging system with multiple execution modes for decoupled architecture.

**Key Components**:
- `EventBus` - Central event dispatcher (singleton)
- `Event` - Event data container
- `EventHandler` - Handler base class
- `EventFactory` - Handler registry
- `CoreletWorker` - Process-based worker
- `EventContext` - Execution context with thread-local storage

**Execution Modes**:
- **SYNC**: Synchronous execution in calling thread (< 100ms operations)
- **THREAD**: Asynchronous thread-based execution (I/O-bound tasks)
- **CORELET**: Process-based isolation (CPU-bound, fault isolation)
- **CMD**: Subprocess execution (external commands)

**Use Cases**:
- Decoupled component communication
- Background task processing
- Parallel data processing
- CPU-intensive computations
- External tool execution

**Example**:
```python
from basefunctions import EventBus, Event, EventHandler, EventResult, EXECUTION_MODE_THREAD

class DataProcessor(EventHandler):
    def handle(self, event, context):
        data = event.event_data
        result = process_data(data)
        return EventResult.business_result(event.event_id, True, result)

# Register handler
from basefunctions import EventFactory
factory = EventFactory()
factory.register_event_type("process_data", DataProcessor)

# Publish event
bus = EventBus()
event = Event("process_data", EXECUTION_MODE_THREAD, event_data={"file": "data.csv"})
event_id = bus.publish(event)

# Get results
bus.join()
results = bus.get_results([event_id])
```

**Learn More**: [EventBus Usage Guide](/docs/events/eventbus_usage_guide.md)

---

### HTTP Client

**Purpose**: Event-based HTTP client with handler system.

**Key Components**:
- `HttpClient` - HTTP client using EventBus
- `HttpClientHandler` - Event handlers for HTTP requests

**Use Cases**:
- API integration
- Web scraping
- Webhook handling
- Event-driven HTTP requests

**Example**:
```python
from basefunctions import HttpClient

client = HttpClient(base_url="https://api.example.com")
response = client.get("/users/123")
response = client.post("/users", json={"name": "Alice"})
```

**Learn More**: See `/docs/http/HTTP_CLIENT_GUIDE.md` (coming soon)

---

### I/O & Serialization

**Purpose**: File operations and multi-format serialization.

**Key Components**:
- **File Operations**: Path manipulation, directory management
- **Serialization**: JSON, YAML, Pickle, MessagePack support
- **Output Redirection**: Redirect stdout/stderr to files, memory, or database

**Use Cases**:
- Reading/writing configuration files
- Data persistence
- Log file management
- Capturing subprocess output

**Example**:
```python
from basefunctions import to_file, from_file, serialize, deserialize

# Serialization
data = {"users": ["Alice", "Bob"], "count": 2}

# Auto-detect format from extension
to_file(data, "data.json")  # JSON
to_file(data, "data.yaml")  # YAML
to_file(data, "data.pkl")   # Pickle

# Load from file
loaded = from_file("data.json")

# Output redirection
from basefunctions import redirect_output, FileTarget

with redirect_output(FileTarget("/tmp/output.log")):
    print("This goes to file")
```

**Learn More**: See `/docs/io/IO_GUIDE.md` (coming soon)

---

### Pandas Extensions

**Purpose**: Custom DataFrame and Series accessors.

**Key Components**:
- `PandasDataFrame` - DataFrame accessor extensions
- `PandasSeries` - Series accessor extensions

**Use Cases**:
- Custom DataFrame operations
- Domain-specific data transformations
- Reusable data processing functions

**Example**:
```python
import pandas as pd
from basefunctions import PandasDataFrame

df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
# Custom accessors available through df.bf.*
```

**Learn More**: See `/docs/pandas/PANDAS_GUIDE.md` (coming soon)

---

### Runtime & Deployment

**Purpose**: Manage application deployment, virtual environments, and runtime paths.

**Key Components**:
- `DeploymentManager` - Module deployment with hash-based change detection
- `VenvUtils` - Virtual environment operations
- Runtime path functions - Path resolution for runtime, config, logs, templates

**Use Cases**:
- Module deployment to production
- Virtual environment management
- Application bootstrapping
- Version management

**Example**:
```python
from basefunctions import (
    DeploymentManager,
    VenvUtils,
    get_runtime_path,
    get_runtime_config_path
)

# Deployment
manager = DeploymentManager()
changed, version = manager.deploy_module("mymodule", force=False)

# Virtual environment
venv = VenvUtils()
venv.create("/path/to/venv")
venv.install_package("requests")

# Runtime paths
runtime_path = get_runtime_path("myapp")
config_path = get_runtime_config_path("myapp")
```

**Learn More**: See `/docs/runtime/DEPLOYMENT_GUIDE.md` (coming soon)

---

### Utils & Logging

**Purpose**: Utility functions, decorators, caching, and logging framework.

**Key Components**:

**Decorators**:
- `@function_timer` - Log execution time
- `@cache_results` - LRU caching with TTL
- `@retry_on_exception` - Automatic retry logic
- `@singleton` - Singleton pattern enforcement
- `@thread_safe` - Thread synchronization
- `@catch_exceptions` - Exception handling
- `@profile_memory` - Memory profiling
- `@warn_if_slow` - Performance warnings

**Logging**:
- Silent by default (explicit configuration required)
- Module-specific log levels
- Global console enable/disable
- Thread-safe operation
- File and console output

**Caching**:
- Multiple backends (memory, file, database, multi-level)
- LRU eviction
- TTL support
- Thread-safe

**Time Utilities**:
- Timezone-aware datetime handling
- ISO 8601 formatting/parsing
- Timestamp conversion

**Example**:
```python
from basefunctions import (
    function_timer, cache_results, retry_on_exception,
    setup_logger, get_logger, enable_console
)

# Decorators
@function_timer
@cache_results(max_size=100, ttl=300)
def expensive_computation(x, y):
    return x ** y

# Logging
setup_logger(__name__, level="INFO")
enable_console(level="INFO")
logger = get_logger(__name__)
logger.info("Application started")
```

**Learn More**: [Logging Usage Guide](/docs/utils/logging/logging_usage_guide.md)

---

## Quick Start

### First Program in 5 Minutes

**Step 1: Install basefunctions**

```bash
pip install -e ".[dev,test]"
```

**Step 2: Create a simple EventBus application**

```python
# myapp.py
import basefunctions

# Setup logging
basefunctions.setup_logger(__name__, level="INFO")
basefunctions.enable_console(level="INFO")
logger = basefunctions.get_logger(__name__)

# Define event handler
class GreetingHandler(basefunctions.EventHandler):
    def handle(self, event, context):
        name = event.event_data.get("name", "World")
        greeting = f"Hello, {name}!"
        logger.info(greeting)
        return basefunctions.EventResult.business_result(
            event.event_id, True, greeting
        )

# Register handler
factory = basefunctions.EventFactory()
factory.register_event_type("greet", GreetingHandler)

# Create event bus
bus = basefunctions.EventBus()

# Publish events
event1 = basefunctions.Event("greet", basefunctions.EXECUTION_MODE_SYNC,
                              event_data={"name": "Alice"})
event2 = basefunctions.Event("greet", basefunctions.EXECUTION_MODE_SYNC,
                              event_data={"name": "Bob"})

bus.publish(event1)
bus.publish(event2)

# Get results
results = bus.get_results()
for event_id, result in results.items():
    print(f"Result: {result.data}")
```

**Step 3: Run the application**

```bash
python myapp.py
```

**Output**:
```
__main__ - INFO - Hello, Alice!
__main__ - INFO - Hello, Bob!
Result: Hello, Alice!
Result: Hello, Bob!
```

---

## Key Concepts

### 1. Singleton Pattern

Core framework components are singletons:

```python
from basefunctions import EventBus, ConfigHandler

# Multiple calls return the same instance
bus1 = EventBus()
bus2 = EventBus()
assert bus1 is bus2  # True

config1 = ConfigHandler()
config2 = ConfigHandler()
assert config1 is config2  # True
```

**Implication**: Configuration changes affect all code using the singleton.

---

### 2. Event-Driven Architecture

Decouple components through events:

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│  Publisher  │ publish │   EventBus   │ route   │   Handler   │
│             ├────────>│  (Singleton) ├────────>│             │
│  (Producer) │         │              │         │  (Consumer) │
└─────────────┘         └──────────────┘         └─────────────┘
```

**Benefits**:
- Components don't know about each other
- Easy to add/remove handlers
- Testable in isolation
- Scalable (thread/process-based execution)

---

### 3. Execution Modes

Choose the right mode for your task:

| Mode | Use For | Example |
|------|---------|---------|
| **SYNC** | Fast operations (< 100ms) | Input validation, database queries |
| **THREAD** | I/O-bound operations | API requests, file I/O |
| **CORELET** | CPU-bound operations | Image processing, ML inference |
| **CMD** | External commands | Running `ffmpeg`, `git` |

---

### 4. Explicit Configuration

**Silent by default** - you must explicitly enable features:

```python
# Logging: Silent by default
import basefunctions

# Setup logger (still silent)
basefunctions.setup_logger("myapp")

# Enable console output (now visible)
basefunctions.enable_console(level="INFO")

# Get logger and use
logger = basefunctions.get_logger("myapp")
logger.info("Now you see me!")
```

---

### 5. Thread Safety

All components are thread-safe:

```python
import basefunctions
import threading

basefunctions.setup_logger("myapp")
logger = basefunctions.get_logger("myapp")

def worker_task(worker_id):
    logger.info(f"Worker {worker_id} started")
    # Safe to use in multiple threads

threads = [threading.Thread(target=worker_task, args=(i,)) for i in range(10)]
for thread in threads:
    thread.start()
for thread in threads:
    thread.join()
```

---

### 6. Factory Pattern

Register and create handlers dynamically:

```python
from basefunctions import EventFactory, EventHandler

# Register handler
factory = EventFactory()
factory.register_event_type("my_event", MyHandler)

# Check registration
if factory.is_handler_available("my_event"):
    handler = factory.create_handler("my_event")
```

---

## Common Patterns

### Pattern 1: CLI Application with EventBus

```python
from basefunctions import CLIApplication, BaseCommand, EventBus, Event, EXECUTION_MODE_THREAD

class DataCommands(BaseCommand):
    def get_metadata(self):
        return {
            "process": CommandMetadata(
                name="process",
                description="Process data files",
                arguments=[ArgumentSpec(name="file", help="File to process", required=True)]
            )
        }

    def cmd_process(self, args):
        # Use EventBus for background processing
        bus = EventBus()
        event = Event("process_file", EXECUTION_MODE_THREAD,
                      event_data={"file": args.file})
        event_id = bus.publish(event)
        bus.join()
        result = bus.get_results([event_id])[event_id]
        return f"Processed: {result.data}"

app = CLIApplication("datatools", version="1.0")
app.register_command_group("", DataCommands())
app.run()
```

---

### Pattern 2: Configuration-Driven Application

```python
from basefunctions import ConfigHandler, setup_logger, enable_console
import os

def setup_application():
    # Load configuration
    config = ConfigHandler()
    config.load_config_for_package("myapp")

    # Setup logging based on environment
    env = os.getenv("ENV", "production")

    if env == "development":
        setup_logger("myapp", level="DEBUG")
        enable_console(level="DEBUG")
    else:
        setup_logger("myapp", level="WARNING")
        # Production: file only, no console

    # Get settings
    api_url = config.get("api.base_url")
    timeout = config.get("api.timeout", default=30)

    return api_url, timeout
```

---

### Pattern 3: Parallel Data Processing

```python
from basefunctions import EventBus, Event, EventHandler, EventResult, EXECUTION_MODE_CORELET
import pandas as pd

class DataChunkProcessor(EventHandler):
    def handle(self, event, context):
        chunk = event.event_data["chunk"]
        # CPU-intensive processing
        result = expensive_transformation(chunk)
        return EventResult.business_result(event.event_id, True, result)

# Register handler
factory = EventFactory()
factory.register_event_type("process_chunk", DataChunkProcessor)

# Split data into chunks
df = pd.read_csv("large_dataset.csv")
chunk_size = len(df) // 8
chunks = [df[i:i+chunk_size] for i in range(0, len(df), chunk_size)]

# Process chunks in parallel
bus = EventBus()
event_ids = []
for i, chunk in enumerate(chunks):
    event = Event("process_chunk", EXECUTION_MODE_CORELET,
                  event_data={"chunk": chunk})
    event_ids.append(bus.publish(event))

bus.join()
results = bus.get_results(event_ids)

# Combine results
processed_chunks = [r.data for r in results.values() if r.success]
final_df = pd.concat(processed_chunks)
```

---

### Pattern 4: Retry with Decorators

```python
from basefunctions import retry_on_exception, function_timer
import requests

@function_timer
@retry_on_exception(max_attempts=3, delay=1.0)
def fetch_api_data(url):
    """Automatically retries on failure, logs execution time"""
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()

# Will retry up to 3 times, wait 1 second between attempts
data = fetch_api_data("https://api.example.com/data")
```

---

### Pattern 5: Cached Results with TTL

```python
from basefunctions import cache_results

@cache_results(max_size=100, ttl=300)  # Cache for 5 minutes
def get_user_profile(user_id):
    """Expensive database query cached for 5 minutes"""
    return database.query(f"SELECT * FROM users WHERE id = {user_id}")

# First call: hits database
profile1 = get_user_profile(123)

# Second call within 5 minutes: returns cached result
profile2 = get_user_profile(123)  # Fast!
```

---

### Pattern 6: Observer Pattern

```python
from basefunctions import Observable, Observer

class DataProcessor(Observable):
    def process(self, data):
        result = transform(data)
        # Notify all observers
        self.notify_observers("data_processed", result)
        return result

class Logger(Observer):
    def update(self, observable, event_type, data):
        print(f"Event: {event_type}, Data: {data}")

class MetricsCollector(Observer):
    def update(self, observable, event_type, data):
        # Collect metrics
        pass

# Setup
processor = DataProcessor()
processor.add_observer(Logger())
processor.add_observer(MetricsCollector())

# Process - both observers notified
processor.process("test data")
```

---

## Development

### Environment Setup

```bash
# Clone repository
git clone https://github.com/neuraldevelopment/basefunctions.git
cd basefunctions

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate  # Windows

# Install development dependencies
pip install -e ".[dev,test,docs]"
```

---

### Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=basefunctions tests/

# Run specific test file
pytest tests/test_event_bus.py

# Run with verbose output
pytest -v tests/
```

---

### Code Quality

**Formatting:**
```bash
# Format code with Black (119 char line length)
black --line-length 119 src/

# Check formatting without changes
black --check --line-length 119 src/
```

**Linting:**
```bash
# Lint with flake8 (99 char guideline)
flake8 --max-line-length=99 src/

# Lint with pylint
pylint src/basefunctions
```

---

### Building

```bash
# Build package
python -m build

# This creates:
# - dist/basefunctions-0.5.24.tar.gz
# - dist/basefunctions-0.5.24-py3-none-any.whl
```

---

### Deployment

```bash
# Deploy using DeploymentManager
./bin/deploy.py --version 0.5.24

# Force deployment (ignore hashes)
./bin/deploy.py --force
```

---

### Contributing

**Code Style Guidelines:**
- **Line length**: 119 chars max (Black), 99 char guideline (flake8)
- **Formatter**: Black
- **Docstring style**: NumPy-style with sections (Parameters, Returns, Raises, Examples)
- **Import organization**: Organized in blocks with comment headers
- **Type hints**: Use type hints for all public functions

**Example Docstring:**
```python
def process_data(data: List[float], threshold: float = 0.5) -> Dict[str, Any]:
    """
    Process data with threshold filtering.

    Parameters
    ----------
    data : List[float]
        List of numerical values to process.
    threshold : float, optional
        Minimum value threshold (default: 0.5).

    Returns
    -------
    Dict[str, Any]
        Processing results with keys 'filtered', 'count', 'mean'.

    Raises
    ------
    ValueError
        If data is empty.

    Examples
    --------
    >>> process_data([0.3, 0.7, 0.9], threshold=0.5)
    {'filtered': [0.7, 0.9], 'count': 2, 'mean': 0.8}
    """
    if not data:
        raise ValueError("data cannot be empty")

    filtered = [x for x in data if x >= threshold]
    return {
        "filtered": filtered,
        "count": len(filtered),
        "mean": sum(filtered) / len(filtered) if filtered else 0
    }
```

---

## API Overview

### High-Level API

**Core Functions:**
```python
# Logging
basefunctions.setup_logger(name, level="ERROR", file=None)
basefunctions.get_logger(name)
basefunctions.enable_console(level="CRITICAL")
basefunctions.disable_console()

# Events
basefunctions.EventBus()
basefunctions.Event(event_type, event_exec_mode, event_data)
basefunctions.EventFactory()

# CLI
basefunctions.CLIApplication(name, version)
basefunctions.BaseCommand()

# Configuration
basefunctions.ConfigHandler()
basefunctions.SecretHandler()

# I/O
basefunctions.serialize(data, format="json")
basefunctions.deserialize(data_str, format="json")
basefunctions.to_file(data, filepath)
basefunctions.from_file(filepath)

# Decorators
@basefunctions.function_timer
@basefunctions.cache_results(max_size=100, ttl=300)
@basefunctions.retry_on_exception(max_attempts=3, delay=1.0)
@basefunctions.singleton
@basefunctions.thread_safe

# Cache
basefunctions.get_cache()
basefunctions.CacheFactory.create(backend_type)

# Time
basefunctions.now_utc()
basefunctions.now_local()
basefunctions.format_iso(dt)
basefunctions.parse_iso(iso_string)

# Runtime
basefunctions.get_runtime_path(package)
basefunctions.DeploymentManager()
basefunctions.VenvUtils()
```

---

## Documentation Links

### Module-Specific Guides

- **[EventBus Usage Guide](docs/events/eventbus_usage_guide.md)** - Comprehensive guide to event-driven architecture
- **[Logging Usage Guide](docs/utils/logging/logging_usage_guide.md)** - Logging framework documentation
- **CLI Framework Guide** - _(coming soon)_
- **HTTP Client Guide** - _(coming soon)_
- **Configuration Guide** - _(coming soon)_
- **Deployment Guide** - _(coming soon)_
- **I/O and Serialization Guide** - _(coming soon)_
- **Pandas Extensions Guide** - _(coming soon)_

### Additional Resources

- **[CLAUDE.md](CLAUDE.md)** - Development guide for Claude Code
- **[README.md](README.md)** - Quick reference
- **[pyproject.toml](pyproject.toml)** - Package configuration
- **Source Code**: [GitHub Repository](https://github.com/neuraldevelopment/basefunctions)

---

## Support

**Issues and Questions**:
- GitHub Issues: [https://github.com/neuraldevelopment/basefunctions/issues](https://github.com/neuraldevelopment/basefunctions/issues)
- Email: neutro2@outlook.de

**License**: MIT
**Copyright**: (c) 2023 neuraldevelopment, Munich

---

**Document Version**: 1.0
**Last Updated**: 2025-11-08
**Framework Version**: basefunctions 0.5.24+
