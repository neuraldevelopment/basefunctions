# Basefunctions - Overview Documentation

**Package:** basefunctions
**Version:** 0.5.75
**Python:** >= 3.12
**Purpose:** Comprehensive Python framework for building robust applications

---

## What is Basefunctions?

Basefunctions is a comprehensive toolkit that provides commonly needed functionality across Python projects. It eliminates the need to reimplement common patterns and provides a consistent, well-tested foundation for application development.

**Core Philosophy:**
- Simple over clever (KISSS principle)
- Explicit over implicit
- Zero abstractions without concrete use cases
- Production-ready, high-quality code

---

## Key Features

### Event-Driven Messaging
Complete event system with multiple execution modes (synchronous, threaded, process-based). Build decoupled, scalable applications with automatic handler registration and retry mechanisms.

**Use Cases:**
- Microservices communication
- Plugin architectures
- Background job processing
- Scheduled tasks

### CLI Framework
Professional command-line applications with automatic help generation, shell completion, progress tracking, and formatted output.

**Use Cases:**
- Development tools
- System administration utilities
- Data processing pipelines
- Interactive CLI applications

### Configuration & Secrets
Environment-aware configuration with secure credential storage using system keyring.

**Use Cases:**
- Application settings management
- API key storage
- Database credentials
- Environment-specific configuration

### Runtime Detection
Automatic detection of development vs deployment environments with standardized path resolution.

**Use Cases:**
- Environment-agnostic code
- Config file location
- Log file management
- Package structure creation

### File I/O & Serialization
Comprehensive file operations with multi-format serialization (JSON, YAML, Pickle, MessagePack).

**Use Cases:**
- Data persistence
- Configuration files
- API responses
- Inter-process communication

### Utilities
Rich set of utilities including decorators, logging, caching, time handling, progress tracking, and more.

**Use Cases:**
- Performance monitoring
- Retry logic
- Thread safety
- Progress visualization

---

## Quick Start

### Installation

```bash
ppip install basefunctions
```

For development:
```bash
ppip install basefunctions[dev]
```

---

### Basic Usage

```python
import basefunctions as bf

# Logging
logger = bf.get_logger(__name__)
logger.info("Application started")

# Time utilities
current_time = bf.now_utc()
timestamp = bf.utc_timestamp()

# File operations
if bf.check_if_file_exists("data.json"):
    data = bf.from_file("data.json")

# Decorators
@bf.function_timer
@bf.retry_on_exception(max_retries=3)
def process_data():
    pass
```

---

## Architecture Overview

### Package Structure

```
basefunctions/
├── cli/          # CLI framework
├── config/       # Configuration & secrets
├── events/       # Event messaging system
├── http/         # HTTP client
├── io/           # File I/O & serialization
├── kpi/          # Metrics tracking
├── pandas/       # Pandas extensions
├── protocols/    # Type protocols
├── runtime/      # Environment detection
└── utils/        # Utilities & decorators
```

---

## Core Subpackages

### Events - Messaging Framework

Event-driven messaging with multiple execution modes.

**Key Components:**
- `EventBus` - Central message broker
- `Event` - Event definition with data and config
- `EventHandler` - Base handler class
- `EventFactory` - Handler registration

**Quick Example:**
```python
from basefunctions.events import EventBus, Event, EventHandler, EventContext, EventResult

class MyHandler(EventHandler):
    def execute(self, context: EventContext) -> EventResult:
        data = context.event.data
        return EventResult(success=True, data={"processed": True})

factory = EventFactory()
factory.register_event_type("process", MyHandler)

bus = EventBus()
event = Event(event_type="process", data={"value": 123})
result = bus.publish(event)
```

**Documentation:** `docs/basefunctions/events.md`

---

### Config - Configuration Management

Secure configuration and secret management.

**Key Components:**
- `ConfigHandler` - YAML-based configuration
- `SecretHandler` - Secure keyring storage

**Quick Example:**
```python
from basefunctions.config import ConfigHandler, SecretHandler

# Load configuration
config = ConfigHandler()
config.load_config_for_package("myapp")
db_host = config.get("database.host", default="localhost")

# Store secrets securely
secrets = SecretHandler(service_name="myapp")
secrets.set_secret("api_key", "secret_value")
api_key = secrets.get_secret("api_key")
```

**Documentation:** `docs/basefunctions/config.md`

---

### Runtime - Environment Detection

Automatic environment detection and path resolution.

**Key Components:**
- `get_runtime_path()` - Package root path
- `get_runtime_config_path()` - Config directory
- `get_runtime_log_path()` - Log directory
- `DeploymentManager` - Deployment operations

**Quick Example:**
```python
from basefunctions.runtime import (
    get_runtime_path,
    get_runtime_config_path,
    find_development_path
)

# Get paths (automatically detects environment)
package_path = get_runtime_path("myapp")
config_path = get_runtime_config_path("myapp")

# Check environment
if find_development_path("myapp"):
    print("Running in development")
else:
    print("Running in deployment")
```

**Documentation:** `docs/basefunctions/runtime.md`

---

### CLI - Command-Line Framework

Complete framework for building professional CLI applications.

**Key Components:**
- `CLIApplication` - Main application
- `BaseCommand` - Command base class
- `CommandMetadata` - Command definition
- `ArgumentSpec` - Argument specification

**Quick Example:**
```python
from basefunctions.cli import (
    CLIApplication,
    BaseCommand,
    CommandMetadata,
    ArgumentSpec,
    ContextManager
)

class GreetCommand(BaseCommand):
    def get_metadata(self) -> CommandMetadata:
        return CommandMetadata(
            name="greet",
            description="Greet a user",
            arguments=[
                ArgumentSpec(name="name", type="str", required=True)
            ]
        )

    def execute(self, context: ContextManager) -> int:
        name = context.get_arg("name")
        print(f"Hello, {name}!")
        return 0

app = CLIApplication(name="greeter", version="1.0.0")
app.register_command(GreetCommand())
exit(app.run())
```

**Documentation:** `docs/basefunctions/cli.md`

---

## Common Patterns

### Application Initialization

```python
import basefunctions as bf

def initialize_app(package_name: str):
    """Initialize application with standard components"""
    # Setup logging
    log_path = bf.get_runtime_log_path(package_name)
    logger = bf.setup_logger(package_name, log_dir=log_path)
    logger.info(f"Starting {package_name}")

    # Load configuration
    config = bf.ConfigHandler()
    config.load_config_for_package(package_name)

    # Initialize event bus
    bus = bf.EventBus()
    bf.register_internal_handlers()

    return logger, config, bus
```

---

### Event-Based Processing

```python
from basefunctions.events import (
    EventBus,
    EventFactory,
    Event,
    EventHandler,
    EventContext,
    EventResult,
    EXECUTION_MODE_THREAD
)

# Define handlers
class DataProcessor(EventHandler):
    def execute(self, context: EventContext) -> EventResult:
        data = context.event.data
        # Process data
        return EventResult(success=True)

# Setup
factory = EventFactory()
factory.register_event_type("data.process", DataProcessor)

bus = EventBus()

# Publish events (non-blocking)
for item in data_items:
    event = Event(
        event_type="data.process",
        data=item,
        mode=EXECUTION_MODE_THREAD
    )
    bus.publish(event)

# Cleanup
bus.shutdown()
```

---

### Configuration-Driven Application

```python
from basefunctions.config import ConfigHandler, SecretHandler
from basefunctions.runtime import get_runtime_config_path

def setup_database_connection(package_name: str):
    """Setup database using config and secrets"""
    # Load configuration
    config = ConfigHandler()
    config.load_config_for_package(package_name)

    # Get connection settings
    db_host = config.get("database.host")
    db_port = config.get("database.port", default=5432)
    db_name = config.get("database.name")

    # Get secure credentials
    secrets = SecretHandler(service_name=package_name)
    db_user = secrets.get_secret("db_username")
    db_pass = secrets.get_secret("db_password")

    # Connect
    connection = connect_database(
        host=db_host,
        port=db_port,
        database=db_name,
        user=db_user,
        password=db_pass
    )

    return connection
```

---

### CLI Tool with Multiple Commands

```python
from basefunctions.cli import CLIApplication, BaseCommand, CommandMetadata, ArgumentSpec

class InitCommand(BaseCommand):
    def get_metadata(self) -> CommandMetadata:
        return CommandMetadata(
            name="init",
            description="Initialize project"
        )

    def execute(self, context) -> int:
        print("Initializing project...")
        return 0

class BuildCommand(BaseCommand):
    def get_metadata(self) -> CommandMetadata:
        return CommandMetadata(
            name="build",
            description="Build project",
            arguments=[
                ArgumentSpec(name="release", type="flag", help="Release build")
            ]
        )

    def execute(self, context) -> int:
        release = context.get_arg("release", default=False)
        print(f"Building ({'release' if release else 'debug'})...")
        return 0

# Setup application
app = CLIApplication(name="builder", version="1.0.0")
app.register_command(InitCommand())
app.register_command(BuildCommand())

if __name__ == "__main__":
    exit(app.run())
```

---

## Best Practices

### 1. Use Runtime Functions for Paths

**Good:**
```python
from basefunctions.runtime import get_runtime_config_path

config_dir = get_runtime_config_path("myapp")
config_file = config_dir / "myapp.yaml"
```

**Avoid:**
```python
# Hardcoded paths break portability
config_file = "/Users/username/myapp/config/myapp.yaml"
```

---

### 2. Never Hardcode Secrets

**Good:**
```python
from basefunctions.config import SecretHandler

secrets = SecretHandler("myapp")
api_key = secrets.get_secret("api_key")
```

**Avoid:**
```python
# NEVER do this
api_key = "sk_live_1234567890"
```

---

### 3. Use Event System for Decoupling

**Good:**
```python
# Components communicate via events
bus.publish(Event(event_type="user.created", data={"user_id": 123}))
```

**Avoid:**
```python
# Direct coupling
email_service.send_welcome_email(user)
notification_service.notify_admins(user)
audit_service.log_creation(user)
```

---

### 4. Choose Appropriate Execution Mode

**Fast operations:** Synchronous mode
```python
Event(event_type="validate", mode=EXECUTION_MODE_SYNC)
```

**I/O operations:** Thread mode
```python
Event(event_type="upload", mode=EXECUTION_MODE_THREAD)
```

**Critical operations:** Corelet mode (process isolation)
```python
Event(event_type="payment", mode=EXECUTION_MODE_CORELET)
```

---

### 5. Provide Meaningful Exit Codes

```python
def execute(self, context: ContextManager) -> int:
    try:
        result = perform_operation()
        return 0  # Success
    except FileNotFoundError:
        print("File not found")
        return 1  # File error
    except PermissionError:
        print("Permission denied")
        return 2  # Permission error
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 99  # Unknown error
```

---

## Integration Examples

### Events + Config

```python
from basefunctions.events import EventBus, Event, EXECUTION_MODE_THREAD
from basefunctions.config import ConfigHandler

config = ConfigHandler()
config.load_config_for_package("myapp")

bus = EventBus()

# Use config to control event behavior
async_enabled = config.get("events.async", default=True)
max_retries = config.get("events.retries", default=3)

event = Event(
    event_type="process",
    data={},
    mode=EXECUTION_MODE_THREAD if async_enabled else EXECUTION_MODE_SYNC,
    retry_count=max_retries
)
bus.publish(event)
```

---

### CLI + Events

```python
from basefunctions.cli import BaseCommand, CommandMetadata, ContextManager
from basefunctions.events import EventBus, Event

class ProcessCommand(BaseCommand):
    def __init__(self):
        super().__init__()
        self.bus = EventBus()

    def get_metadata(self) -> CommandMetadata:
        return CommandMetadata(
            name="process",
            description="Process data via events"
        )

    def execute(self, context: ContextManager) -> int:
        event = Event(event_type="process.data", data={})
        result = self.bus.publish(event)
        return 0 if result.success else 1
```

---

### Runtime + Config

```python
from basefunctions.runtime import get_runtime_config_path, find_development_path
from basefunctions.config import ConfigHandler
from pathlib import Path

# Get config path for current environment
config_path = get_runtime_config_path("myapp")
config_file = config_path / "myapp.yaml"

# Load if exists
if config_file.exists():
    config = ConfigHandler()
    config.load_config_for_package("myapp")

    # Adjust behavior based on environment
    is_dev = find_development_path("myapp") is not None
    debug_mode = config.get("debug", default=is_dev)
```

---

## Error Handling

Basefunctions uses specific exception types:

```python
from basefunctions import (
    EventValidationError,
    EventExecutionError,
    SerializationError,
    CacheError,
    DeploymentError,
    VenvUtilsError
)

try:
    # Event operations
    bus.publish(event)
except EventValidationError as e:
    print(f"Invalid event: {e}")
except EventExecutionError as e:
    print(f"Execution failed: {e}")

try:
    # Serialization
    data = from_file("config.json")
except SerializationError as e:
    print(f"Failed to load: {e}")

try:
    # Deployment operations
    manager.deploy_package("myapp", source_path)
except DeploymentError as e:
    print(f"Deployment failed: {e}")
```

---

## Performance Tips

### 1. Cache Resolved Paths
```python
# FAST - Resolve once
package_path = get_runtime_path("myapp")
file1 = package_path / "data" / "file1.txt"
file2 = package_path / "data" / "file2.txt"

# SLOW - Repeated resolution
for filename in filenames:
    path = get_runtime_path("myapp") / "data" / filename
```

### 2. Use Appropriate Event Mode
```python
# FAST - Non-blocking for I/O
event = Event(event_type="upload", mode=EXECUTION_MODE_THREAD)

# SLOW - Blocks for I/O
event = Event(event_type="upload", mode=EXECUTION_MODE_SYNC)
```

### 3. Load Config Once
```python
# FAST - Load once at startup
config = ConfigHandler()
config.load_config_for_package("myapp")
db_host = config.get("database.host")

# SLOW - Loading repeatedly
for i in range(100):
    config = ConfigHandler()
    config.load_config_for_package("myapp")
```

---

## Testing with Basefunctions

### Unit Tests

```python
import pytest
from basefunctions import serialize, deserialize

def test_serialization():
    data = {"key": "value", "number": 42}
    json_str = serialize(data, format="json")
    loaded = deserialize(json_str, format="json")
    assert loaded == data

def test_event_handler():
    from basefunctions.events import Event, EventContext

    handler = MyHandler()
    event = Event(event_type="test", data={"value": 123})
    context = EventContext(event)
    result = handler.execute(context)

    assert result.success
    assert result.data["processed"] == True
```

### Integration Tests

```python
import pytest
from basefunctions import EventBus, EventFactory, Event

def test_event_flow():
    # Setup
    factory = EventFactory()
    factory.register_event_type("test", TestHandler)
    bus = EventBus()

    # Execute
    event = Event(event_type="test", data={"value": 42})
    result = bus.publish(event)

    # Assert
    assert result.success
    assert result.data["value"] == 42

    # Cleanup
    bus.shutdown()
```

---

## Subpackage Documentation

**Detailed documentation for each subpackage:**

- **Events:** `docs/basefunctions/events.md` - Event-driven messaging framework
- **Config:** `docs/basefunctions/config.md` - Configuration and secret management
- **Runtime:** `docs/basefunctions/runtime.md` - Environment detection and path resolution
- **CLI:** `docs/basefunctions/cli.md` - Command-line application framework

**Additional subpackages:**
- **HTTP:** HTTP client with event integration
- **IO:** File operations and serialization
- **KPI:** Metrics collection and tracking
- **Pandas:** Pandas extensions
- **Utils:** Decorators, logging, caching, and more

---

## System Documentation

For internal architecture details and implementation specifics:
- `~/.claude/_docs/python/basefunctions.md` - System documentation

---

## Quick Reference

### Common Imports

```python
# Events
from basefunctions.events import EventBus, Event, EventHandler

# Config
from basefunctions.config import ConfigHandler, SecretHandler

# Runtime
from basefunctions.runtime import (
    get_runtime_path,
    get_runtime_config_path,
    get_runtime_log_path
)

# CLI
from basefunctions.cli import CLIApplication, BaseCommand

# Utilities
from basefunctions import (
    get_logger,
    now_utc,
    serialize,
    deserialize,
    from_file,
    to_file
)

# Decorators
from basefunctions import (
    function_timer,
    retry_on_exception,
    cache_results,
    thread_safe
)
```

---

## Getting Help

### Documentation
- Overview: `docs/basefunctions/overview.md` (this file)
- Events: `docs/basefunctions/events.md`
- Config: `docs/basefunctions/config.md`
- Runtime: `docs/basefunctions/runtime.md`
- CLI: `docs/basefunctions/cli.md`

### Support
Contact: neutro2@outlook.de

---

**Document Version:** 0.5.75
**Last Updated:** 2026-01-29
**Package Version:** 0.5.75
