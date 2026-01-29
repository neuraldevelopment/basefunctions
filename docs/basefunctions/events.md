# Events - User Documentation

**Package:** basefunctions
**Subpackage:** events
**Version:** 0.5.75
**Purpose:** Event-driven messaging framework with multiple execution modes

---

## Overview

The events subpackage provides a complete event-driven messaging framework that enables decoupled, asynchronous communication between components. It supports synchronous, threaded, and corelet-based execution modes.

**Key Features:**
- Multiple execution modes: synchronous, threaded, and corelet-based (isolated processes)
- Type-safe event system with automatic handler registration
- Built-in retry and timeout mechanisms
- Timer-based scheduled events
- Context propagation across event boundaries

**Common Use Cases:**
- Decoupling application components
- Implementing asynchronous task execution
- Building plugin-based architectures
- Creating background job systems
- Scheduled task execution

---

## Public APIs

### EventBus

**Purpose:** Central message broker for event distribution and handler coordination

```python
from basefunctions.events import EventBus

bus = EventBus()
```

**Parameters:**
None - EventBus is initialized without parameters

**Key Methods:**

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `publish()` | `event: Event` | `EventResult` | Publish an event for processing |
| `subscribe()` | `event_type: str, handler: EventHandler` | `None` | Register a handler for an event type |
| `shutdown()` | - | `None` | Gracefully shutdown the event bus |

**Examples:**

```python
from basefunctions.events import EventBus, Event, EXECUTION_MODE_SYNC

# Create event bus
bus = EventBus()

# Publish a simple event
event = Event(
    event_type="user.created",
    data={"user_id": 123, "username": "john_doe"}
)
result = bus.publish(event)
print(f"Event processed: {result.success}")
```

**Best For:**
- Central event coordination
- Decoupled component communication
- Plugin architecture implementation

---

### Event

**Purpose:** Represents an event with data and execution configuration

```python
from basefunctions.events import Event

event = Event(
    event_type: str,
    data: dict | None = None,
    mode: str = EXECUTION_MODE_SYNC,
    priority: int = DEFAULT_PRIORITY,
    timeout: float = DEFAULT_TIMEOUT,
    retry_count: int = DEFAULT_RETRY_COUNT
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `event_type` | str | - | Type identifier for the event |
| `data` | dict | None | Event payload data |
| `mode` | str | SYNC | Execution mode (SYNC, THREAD, CORELET, CMD) |
| `priority` | int | 5 | Execution priority (higher = first) |
| `timeout` | float | 30.0 | Max execution time in seconds |
| `retry_count` | int | 0 | Number of retries on failure |

**Execution Modes:**
- `EXECUTION_MODE_SYNC`: Execute in current thread (blocking)
- `EXECUTION_MODE_THREAD`: Execute in background thread (non-blocking)
- `EXECUTION_MODE_CORELET`: Execute in isolated process (maximum isolation)
- `EXECUTION_MODE_CMD`: Execute command-line process

**Examples:**

```python
from basefunctions.events import Event, EXECUTION_MODE_THREAD

# Simple synchronous event
event = Event(event_type="data.process", data={"values": [1, 2, 3]})

# Background thread execution
event = Event(
    event_type="file.upload",
    data={"path": "/tmp/file.txt"},
    mode=EXECUTION_MODE_THREAD
)

# High priority with retry
event = Event(
    event_type="critical.task",
    data={"task_id": 456},
    priority=10,
    retry_count=3,
    timeout=60.0
)
```

---

### EventHandler

**Purpose:** Base class for implementing custom event handlers

```python
from basefunctions.events import EventHandler, EventContext, EventResult

class MyHandler(EventHandler):
    def execute(self, context: EventContext) -> EventResult:
        """Process the event"""
        # Access event data
        data = context.event.data

        # Process logic here
        result = process_data(data)

        # Return result
        return EventResult(
            success=True,
            data={"result": result}
        )
```

**When to Extend:**
- Implementing custom event processing logic
- Creating reusable event handlers
- Building domain-specific event processors

**Implementation Example:**

```python
from basefunctions.events import EventHandler, EventContext, EventResult

class UserNotificationHandler(EventHandler):
    def __init__(self, notification_service):
        super().__init__()
        self.service = notification_service

    def execute(self, context: EventContext) -> EventResult:
        """Send user notification"""
        try:
            user_id = context.event.data.get("user_id")
            message = context.event.data.get("message")

            # Send notification
            self.service.send(user_id, message)

            return EventResult(
                success=True,
                data={"sent_at": datetime.now().isoformat()}
            )
        except Exception as e:
            return EventResult(
                success=False,
                error_message=str(e)
            )
```

**Important Rules:**
1. Always call `super().__init__()` in your constructor
2. Return `EventResult` with success status
3. Handle exceptions and return failure results
4. Keep handlers focused on single responsibility

---

### EventFactory

**Purpose:** Register and manage event type to handler mappings

```python
from basefunctions.events import EventFactory

factory = EventFactory()
factory.register_event_type("user.created", UserCreatedHandler)
```

**Key Methods:**

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `register_event_type()` | `event_type: str, handler_class: type[EventHandler]` | `None` | Register handler for event type |
| `create_handler()` | `event_type: str` | `EventHandler` | Create handler instance for event type |

**Examples:**

```python
from basefunctions.events import EventFactory, EventHandler

# Create factory
factory = EventFactory()

# Register multiple handlers
factory.register_event_type("order.created", OrderCreatedHandler)
factory.register_event_type("order.cancelled", OrderCancelledHandler)
factory.register_event_type("order.shipped", OrderShippedHandler)

# Factory automatically creates handlers when events arrive
```

---

### TimerThread

**Purpose:** Schedule periodic or delayed event execution

```python
from basefunctions.events import TimerThread, EventBus, Event

timer = TimerThread(
    event_bus: EventBus,
    interval_seconds: float,
    event: Event,
    run_once: bool = False
)
timer.start()
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `event_bus` | EventBus | - | Event bus to publish to |
| `interval_seconds` | float | - | Delay or interval in seconds |
| `event` | Event | - | Event to publish |
| `run_once` | bool | False | Execute once (True) or repeat (False) |

**Examples:**

```python
from basefunctions.events import TimerThread, EventBus, Event

bus = EventBus()

# One-time delayed execution (5 seconds)
delayed_event = Event(event_type="cleanup.start", data={})
timer = TimerThread(bus, 5.0, delayed_event, run_once=True)
timer.start()

# Periodic execution (every 60 seconds)
health_check = Event(event_type="system.health_check", data={})
periodic = TimerThread(bus, 60.0, health_check, run_once=False)
periodic.start()

# Stop periodic timer later
periodic.stop()
```

---

## Usage Examples

### Basic Usage (Most Common)

**Scenario:** Simple synchronous event processing

```python
from basefunctions.events import EventBus, EventFactory, Event, EventHandler, EventContext, EventResult

# Step 1: Create handler
class WelcomeEmailHandler(EventHandler):
    def execute(self, context: EventContext) -> EventResult:
        email = context.event.data.get("email")
        print(f"Sending welcome email to {email}")
        return EventResult(success=True)

# Step 2: Register handler with factory
factory = EventFactory()
factory.register_event_type("user.registered", WelcomeEmailHandler)

# Step 3: Create event bus
bus = EventBus()

# Step 4: Publish event
event = Event(
    event_type="user.registered",
    data={"email": "user@example.com", "user_id": 123}
)
result = bus.publish(event)

print(f"Success: {result.success}")
```

**Expected Output:**
```
Sending welcome email to user@example.com
Success: True
```

---

### Advanced Usage - Background Processing

**Scenario:** Process events in background threads for non-blocking execution

```python
from basefunctions.events import EventBus, EventFactory, Event, EventHandler
from basefunctions.events import EXECUTION_MODE_THREAD, EventContext, EventResult
import time

# Heavy processing handler
class ImageProcessingHandler(EventHandler):
    def execute(self, context: EventContext) -> EventResult:
        image_path = context.event.data.get("path")
        print(f"Processing image: {image_path}")
        time.sleep(2)  # Simulate heavy processing
        return EventResult(success=True, data={"processed": True})

# Setup
factory = EventFactory()
factory.register_event_type("image.process", ImageProcessingHandler)
bus = EventBus()

# Publish multiple events (non-blocking)
for i in range(5):
    event = Event(
        event_type="image.process",
        data={"path": f"/images/photo_{i}.jpg"},
        mode=EXECUTION_MODE_THREAD  # Background execution
    )
    result = bus.publish(event)
    print(f"Submitted image {i}")

print("All images submitted, continuing with other work...")
```

---

### Advanced Usage - Corelet Isolation

**Scenario:** Execute events in isolated processes for maximum reliability

```python
from basefunctions.events import EventBus, EventFactory, Event, EventHandler
from basefunctions.events import EXECUTION_MODE_CORELET, EventContext, EventResult

# Critical handler that needs isolation
class PaymentProcessingHandler(EventHandler):
    def execute(self, context: EventContext) -> EventResult:
        amount = context.event.data.get("amount")
        account = context.event.data.get("account")

        # Process payment in isolated environment
        # If this crashes, main process is unaffected
        success = process_payment(amount, account)

        return EventResult(success=success, data={"transaction_id": 789})

# Setup
factory = EventFactory()
factory.register_event_type("payment.process", PaymentProcessingHandler)
bus = EventBus()

# Publish with corelet mode
event = Event(
    event_type="payment.process",
    data={"amount": 99.99, "account": "ACC123"},
    mode=EXECUTION_MODE_CORELET,  # Isolated process
    timeout=30.0,
    retry_count=2
)
result = bus.publish(event)

if result.success:
    print(f"Payment processed: {result.data.get('transaction_id')}")
```

---

### Integration with Other Components

**Working with ConfigHandler:**

```python
from basefunctions.events import EventBus, EventFactory, Event
from basefunctions.config import ConfigHandler

# Load configuration
config = ConfigHandler()
config.load_config_for_package("myapp")

# Create event bus with config-driven settings
bus = EventBus()

# Create events based on configuration
notify_email = config.get("notifications.email.enabled", default=True)
if notify_email:
    event = Event(
        event_type="notification.email",
        data={"recipient": "admin@example.com"}
    )
    bus.publish(event)
```

---

### Custom Implementation Example

**Scenario:** Build a multi-step workflow using events

```python
from basefunctions.events import EventBus, EventFactory, Event, EventHandler
from basefunctions.events import EventContext, EventResult

# Step 1: Data validation
class ValidateDataHandler(EventHandler):
    def execute(self, context: EventContext) -> EventResult:
        data = context.event.data
        if not data.get("required_field"):
            return EventResult(success=False, error_message="Missing required field")

        # Trigger next step
        next_event = Event(event_type="data.transform", data=data)
        context.event_bus.publish(next_event)
        return EventResult(success=True)

# Step 2: Data transformation
class TransformDataHandler(EventHandler):
    def execute(self, context: EventContext) -> EventResult:
        data = context.event.data
        transformed = transform(data)

        # Trigger final step
        next_event = Event(event_type="data.save", data=transformed)
        context.event_bus.publish(next_event)
        return EventResult(success=True)

# Step 3: Save data
class SaveDataHandler(EventHandler):
    def execute(self, context: EventContext) -> EventResult:
        data = context.event.data
        save_to_database(data)
        return EventResult(success=True, data={"saved_id": 123})

# Setup workflow
factory = EventFactory()
factory.register_event_type("data.validate", ValidateDataHandler)
factory.register_event_type("data.transform", TransformDataHandler)
factory.register_event_type("data.save", SaveDataHandler)

bus = EventBus()

# Start workflow
initial_event = Event(
    event_type="data.validate",
    data={"required_field": "value", "other_data": 123}
)
bus.publish(initial_event)
```

---

## Choosing the Right Approach

### When to Use SYNC Mode

Use synchronous execution when:
- Result is needed immediately
- Order of execution matters
- Simple, fast operations
- Testing and debugging

```python
event = Event(event_type="validate.input", mode=EXECUTION_MODE_SYNC)
result = bus.publish(event)
if result.success:
    proceed_with_data()
```

**Pros:**
- Simple and predictable
- Immediate results
- Easy to debug

**Cons:**
- Blocks caller
- No parallelism

---

### When to Use THREAD Mode

Use threaded execution when:
- Operations can run in background
- Non-blocking execution needed
- Multiple tasks can run in parallel
- Results are not immediately needed

```python
event = Event(event_type="send.notification", mode=EXECUTION_MODE_THREAD)
bus.publish(event)
# Continue immediately
```

**Pros:**
- Non-blocking
- Parallel execution
- Better resource utilization

**Cons:**
- No immediate result
- Shared memory (thread safety needed)

---

### When to Use CORELET Mode

Use corelet (isolated process) execution when:
- Maximum isolation required
- Handler might crash or hang
- Working with untrusted code
- Need independent resource limits

```python
event = Event(event_type="process.untrusted", mode=EXECUTION_MODE_CORELET, timeout=10.0)
result = bus.publish(event)
```

**Pros:**
- Process isolation
- Crash protection
- Independent resources

**Cons:**
- Higher overhead
- Serialization required
- More resource intensive

---

## Error Handling

### Common Errors

**Error 1: NoHandlerAvailableError**

```python
# WRONG - No handler registered
event = Event(event_type="unknown.event", data={})
result = bus.publish(event)
# NoHandlerAvailableError: No handler for 'unknown.event'
```

**Solution:**
```python
# CORRECT - Register handler first
factory = EventFactory()
factory.register_event_type("unknown.event", MyHandler)

event = Event(event_type="unknown.event", data={})
result = bus.publish(event)
```

**What Went Wrong:** Attempted to publish event without registered handler

---

**Error 2: EventExecutionError**

```python
# WRONG - Handler raises unhandled exception
class BrokenHandler(EventHandler):
    def execute(self, context: EventContext) -> EventResult:
        raise ValueError("Something broke")
```

**Solution:**
```python
# CORRECT - Handle exceptions properly
class SafeHandler(EventHandler):
    def execute(self, context: EventContext) -> EventResult:
        try:
            # Process logic
            result = risky_operation()
            return EventResult(success=True, data=result)
        except ValueError as e:
            return EventResult(success=False, error_message=str(e))
```

**What Went Wrong:** Handler raised exception instead of returning failure result

---

### Error Recovery

```python
from basefunctions.events import EventBus, Event, EventExecutionError

bus = EventBus()

try:
    event = Event(
        event_type="risky.operation",
        data={"value": 123},
        retry_count=3,  # Automatic retry on failure
        timeout=30.0
    )
    result = bus.publish(event)

    if not result.success:
        print(f"Operation failed: {result.error_message}")
        # Implement fallback logic

except EventExecutionError as e:
    print(f"Event execution error: {e}")
    # Log and handle
except Exception as e:
    print(f"Unexpected error: {e}")
```

---

## Best Practices

### Best Practice 1: Always Return EventResult

**Why:** Consistent result handling and error propagation

```python
# GOOD
class GoodHandler(EventHandler):
    def execute(self, context: EventContext) -> EventResult:
        try:
            result = process()
            return EventResult(success=True, data=result)
        except Exception as e:
            return EventResult(success=False, error_message=str(e))
```

```python
# AVOID
class BadHandler(EventHandler):
    def execute(self, context: EventContext) -> EventResult:
        process()  # Might raise exception
        return EventResult(success=True)
```

---

### Best Practice 2: Use Appropriate Execution Mode

**Why:** Performance and reliability depend on correct mode selection

```python
# GOOD - Fast validation in sync mode
validation_event = Event(event_type="validate", mode=EXECUTION_MODE_SYNC)

# GOOD - Slow I/O in thread mode
io_event = Event(event_type="file.upload", mode=EXECUTION_MODE_THREAD)

# GOOD - Critical operations in corelet mode
critical_event = Event(event_type="payment", mode=EXECUTION_MODE_CORELET)
```

```python
# AVOID - Slow I/O blocking caller
slow_event = Event(event_type="file.upload", mode=EXECUTION_MODE_SYNC)
```

---

### Best Practice 3: Cleanup Resources

**Why:** Prevent resource leaks and ensure graceful shutdown

```python
# GOOD
bus = EventBus()
try:
    # Use event bus
    bus.publish(event)
finally:
    bus.shutdown()  # Always cleanup
```

```python
# AVOID
bus = EventBus()
bus.publish(event)
# Bus not shut down - resources leaked
```

---

## Performance Tips

**Tip 1:** Use thread mode for I/O-bound operations
```python
# FAST - Non-blocking I/O
event = Event(event_type="api.call", mode=EXECUTION_MODE_THREAD)

# SLOW - Blocks until complete
event = Event(event_type="api.call", mode=EXECUTION_MODE_SYNC)
```

**Tip 2:** Batch events when possible
```python
# FAST - Single handler with batch data
event = Event(event_type="process.batch", data={"items": items})

# SLOW - Multiple events
for item in items:
    event = Event(event_type="process.item", data=item)
```

---

## See Also

**Related Subpackages:**
- `config` (`docs/basefunctions/config.md`) - Configuration for event handlers
- `runtime` (`docs/basefunctions/runtime.md`) - Runtime environment detection

**System Documentation:**
- `~/.claude/_docs/python/basefunctions.md` - Internal architecture details

---

## Quick Reference

### Imports

```python
# Core classes
from basefunctions.events import EventBus, Event, EventHandler

# Execution modes
from basefunctions.events import (
    EXECUTION_MODE_SYNC,
    EXECUTION_MODE_THREAD,
    EXECUTION_MODE_CORELET
)

# Results and context
from basefunctions.events import EventResult, EventContext

# Factory and timer
from basefunctions.events import EventFactory, TimerThread

# Exceptions
from basefunctions.events import (
    EventExecutionError,
    NoHandlerAvailableError
)
```

### Quick Start

```python
# Step 1: Create handler
class MyHandler(EventHandler):
    def execute(self, context: EventContext) -> EventResult:
        return EventResult(success=True)

# Step 2: Register handler
factory = EventFactory()
factory.register_event_type("my.event", MyHandler)

# Step 3: Create bus and publish
bus = EventBus()
event = Event(event_type="my.event", data={"key": "value"})
result = bus.publish(event)

# Step 4: Cleanup
bus.shutdown()
```

### Cheat Sheet

| Task | Code |
|------|------|
| Create event | `Event(event_type="type", data={})` |
| Publish sync | `bus.publish(Event(event_type="type"))` |
| Publish async | `bus.publish(Event(event_type="type", mode=EXECUTION_MODE_THREAD))` |
| Register handler | `factory.register_event_type("type", HandlerClass)` |
| Schedule timer | `TimerThread(bus, 60.0, event).start()` |
| Shutdown bus | `bus.shutdown()` |

---

**Document Version:** 0.5.75
**Last Updated:** 2026-01-29
**Subpackage Version:** 0.5.75
