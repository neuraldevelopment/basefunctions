# EventBus Usage Guide

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Execution Modes](#execution-modes)
4. [Basic Usage](#basic-usage)
5. [Use Cases](#use-cases)
6. [Handler Development](#handler-development)
7. [Important Concepts](#important-concepts)
8. [Critical Warnings](#critical-warnings)
9. [Best Practices](#best-practices)
10. [Common Errors & Troubleshooting](#common-errors--troubleshooting)
11. [API Reference](#api-reference)

---

## 1. Overview

### What is the EventBus System?

The **EventBus** is a central event distribution system that implements a **producer-consumer pattern** with support for three execution modes: synchronous (SYNC), thread-based asynchronous (THREAD), and process-based isolated execution (CORELET).

It provides:
- **Unified messaging infrastructure** for decoupled component communication
- **Multiple execution modes** for different performance and isolation needs
- **Priority-based event scheduling** with automatic retry and timeout handling
- **LRU-based result caching** with smart cleanup strategies
- **Thread-safe** concurrent event processing
- **Process isolation** for fault-tolerant parallel execution

### Event-Driven Architecture

The EventBus implements a **publish-subscribe model**:

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│  Publisher  │ publish │   EventBus   │ route   │   Handler   │
│             ├────────>│  (Singleton) ├────────>│  (Subclass) │
│  (Producer) │         │              │         │  (Consumer) │
└─────────────┘         └──────┬───────┘         └─────────────┘
                               │
                               │ get_results()
                               v
                        ┌──────────────┐
                        │  EventResult │
                        │   (Cache)    │
                        └──────────────┘
```

**Key Benefits:**
- **Decoupling**: Publishers don't need to know about consumers
- **Scalability**: Handlers can run in threads or separate processes
- **Fault Tolerance**: Process isolation prevents crashes from affecting main app
- **Testability**: Events and handlers can be tested independently

---

## 2. Architecture

### Core Components

#### 2.1 EventBus (Singleton)

The central dispatcher that manages event routing, handler execution, and result caching.

**Key Responsibilities:**
- Validate and route events based on execution mode
- Manage worker thread pool (auto-sized to CPU cores)
- Handle priority queue for async events
- Cache results with LRU eviction
- Coordinate timeouts and retries

```python
from basefunctions import EventBus

# EventBus is a singleton - only one instance per process
bus = EventBus()  # Auto-detects CPU cores
# or
bus = EventBus(num_threads=8)  # Custom thread count
```

#### 2.2 Event

Data container representing something that happened in the system.

**Key Attributes:**
- `event_id` (str): Unique UUID for tracking
- `event_type` (str): Identifier for routing to handlers
- `event_exec_mode` (str): SYNC, THREAD, CORELET, or CMD
- `event_data` (Any): Payload data
- `priority` (int): 0-10, higher = more important
- `timeout` (int): Processing timeout in seconds
- `max_retries` (int): Number of retry attempts

```python
from basefunctions import Event, EXECUTION_MODE_THREAD

event = Event(
    event_type="data_process",
    event_exec_mode=EXECUTION_MODE_THREAD,
    event_data={"input_file": "data.csv"},
    priority=7,
    timeout=30,
    max_retries=3
)
```

#### 2.3 EventHandler (Abstract Base Class)

Base class for all event processors. Handlers implement the `handle()` method to define event processing logic.

```python
from basefunctions import EventHandler, EventResult

class DataProcessor(EventHandler):
    def handle(self, event, context):
        # Process event
        data = event.event_data
        result = process_data(data)

        # Return result
        return EventResult.business_result(
            event.event_id,
            success=True,
            data=result
        )
```

#### 2.4 EventResult

Unified result container for both successful and failed processing outcomes.

**Two result types:**
- **Business Result**: Expected outcomes (success or failure)
- **Exception Result**: Technical errors (timeouts, crashes)

```python
# Success
result = EventResult.business_result(
    event_id="abc-123",
    success=True,
    data={"processed": 100}
)

# Business failure (e.g., validation error)
result = EventResult.business_result(
    event_id="abc-123",
    success=False,
    data="Invalid input: missing field 'name'"
)

# Technical exception
result = EventResult.exception_result(
    event_id="abc-123",
    exception=TimeoutError("Processing timeout")
)
```

#### 2.5 EventFactory (Singleton)

Registry for handler classes. Manages handler registration and creation.

```python
from basefunctions import EventFactory

factory = EventFactory()
factory.register_event_type("data_process", DataProcessHandler)

# Check registration
if factory.is_handler_available("data_process"):
    handler = factory.create_handler("data_process")
```

#### 2.6 EventContext

Context data passed to every handler, providing thread-local storage and execution metadata.

**Key Attributes:**
- `thread_local_data`: Thread-specific storage for caching
- `thread_id`: Worker thread identifier (THREAD mode)
- `process_id`: Worker process PID (CORELET mode)
- `worker`: Reference to CoreletWorker (CORELET mode only)

```python
def handle(self, event, context):
    # Use thread-local cache
    if not hasattr(context.thread_local_data, 'db_conn'):
        context.thread_local_data.db_conn = create_connection()

    conn = context.thread_local_data.db_conn
    # ... use connection ...
```

#### 2.7 CoreletWorker

Isolated worker process for CORELET mode. Runs handlers in separate process space with dedicated event loop.

**Features:**
- Process isolation (no GIL, no shared memory)
- Signal handling (SIGTERM, SIGINT)
- Dynamic handler loading via `corelet_meta`
- Idle timeout (10 minutes default)
- Low process priority to avoid CPU contention

---

## 3. Execution Modes

This is the **core feature** of the EventBus. Understanding when to use each mode is critical.

### 3.1 SYNC - Synchronous Execution

**How it works:**
- Events processed **immediately** in the calling thread
- No queuing, no async workers
- Results available **instantly**

**When to use:**
- Simple, fast operations (< 100ms)
- Database queries with connection pooling
- Configuration lookups
- Input validation
- When you need results **immediately**

**Pros:**
- ✅ No threading overhead
- ✅ Immediate results
- ✅ Simplest debugging (stack traces work normally)
- ✅ Predictable execution order

**Cons:**
- ❌ Blocks calling thread
- ❌ No parallelism
- ❌ Slow operations freeze the app

**Example:**

```python
from basefunctions import EventBus, Event, EXECUTION_MODE_SYNC

bus = EventBus()

# Publish sync event
event = Event(
    event_type="validate_input",
    event_exec_mode=EXECUTION_MODE_SYNC,
    event_data={"user_id": 123}
)

event_id = bus.publish(event)

# Results available immediately (no need to join)
results = bus.get_results([event_id])
print(results[event_id].success)  # True or False
```

### 3.2 THREAD - Thread-Based Asynchronous

**How it works:**
- Events queued in **priority queue**
- Worker thread pool picks up events
- Handlers run in **separate threads**
- Results cached and retrieved later

**When to use:**
- I/O-bound operations (file reads, HTTP requests, database queries)
- Medium-duration tasks (100ms - 10s)
- Background processing
- When you need **concurrent execution** of multiple tasks
- When you want to **free up the calling thread**

**Pros:**
- ✅ Non-blocking (caller continues immediately)
- ✅ Parallel execution (limited by GIL for CPU-bound tasks)
- ✅ Shared memory (handlers can access shared state)
- ✅ Lower overhead than processes

**Cons:**
- ❌ Subject to Python GIL (no true parallelism for CPU-bound tasks)
- ❌ Crash in handler can affect thread pool
- ❌ Thread-safety required for shared state

**Example:**

```python
from basefunctions import EventBus, Event, EXECUTION_MODE_THREAD

bus = EventBus()

# Publish multiple async events
event_ids = []
for i in range(100):
    event = Event(
        event_type="fetch_data",
        event_exec_mode=EXECUTION_MODE_THREAD,
        event_data={"url": f"https://api.example.com/data/{i}"},
        priority=5,
        timeout=10
    )
    event_ids.append(bus.publish(event))

# Continue with other work...
print("Events submitted, continuing...")

# Later: wait for all events to complete
bus.join()

# Retrieve results
results = bus.get_results(event_ids)
for event_id in event_ids:
    result = results[event_id]
    if result.success:
        print(f"Success: {result.data}")
    else:
        print(f"Failed: {result.exception}")
```

### 3.3 CORELET - Process-Based Isolation

**How it works:**
- Events forwarded to **separate worker processes**
- Handler runs in **isolated process space**
- Communication via **pickle serialization** over pipes
- One corelet per worker thread (lazy creation)

**When to use:**
- **CPU-bound tasks** (computation-heavy operations)
- **Fault isolation** (handler crashes shouldn't affect main app)
- **Memory isolation** (large data processing)
- **True parallelism** (no GIL contention)
- **Untrusted code** (sandbox execution)

**Pros:**
- ✅ True parallelism (no GIL)
- ✅ Crash isolation (process crash doesn't kill main app)
- ✅ Memory isolation (separate address space)
- ✅ Resource limits (per-process limits possible)

**Cons:**
- ❌ Higher overhead (process creation, IPC)
- ❌ No shared memory (all data must be pickled)
- ❌ Pickle serialization required (limits data types)
- ❌ ⚠️ **CRITICAL**: Currently no automatic cleanup (see warnings)

**Example:**

```python
from basefunctions import EventBus, Event, EXECUTION_MODE_CORELET

bus = EventBus()

# CPU-intensive task in isolated process
event = Event(
    event_type="heavy_computation",
    event_exec_mode=EXECUTION_MODE_CORELET,
    event_data={
        "matrix_size": 10000,
        "iterations": 100
    },
    timeout=60
)

event_id = bus.publish(event)
bus.join()

result = bus.get_results([event_id])[event_id]
print(result.data)
```

**IMPORTANT: Pickle Serialization**

Only pickle-compatible data can be sent to corelets:

```python
# ✅ GOOD: Pickle-friendly data
event_data = {
    "numbers": [1, 2, 3],
    "config": {"key": "value"},
    "dataframe": df  # Pandas DataFrames are pickle-compatible
}

# ❌ BAD: Cannot pickle these
event_data = {
    "file_handle": open("file.txt"),  # File handles
    "thread_lock": threading.Lock(),  # Locks
    "lambda": lambda x: x + 1,        # Lambdas
    "generator": (x for x in range(10))  # Generators
}
```

### 3.4 CMD - Subprocess Execution

**How it works:**
- Special mode for **executing external commands**
- Uses `DefaultCmdHandler` internally
- Runs via `subprocess.Popen`
- Supports stdout/stderr redirection to files

**When to use:**
- Running external CLI tools
- System commands
- Scripts in other languages
- Build processes

**Example:**

```python
from basefunctions import EventBus, Event, EXECUTION_MODE_CMD

bus = EventBus()

event = Event(
    event_type="run_command",  # Any name, uses DefaultCmdHandler
    event_exec_mode=EXECUTION_MODE_CMD,
    event_data={
        "executable": "python",
        "args": ["script.py", "--input", "data.csv"],
        "cwd": "/path/to/workdir",
        "stdout_file": "/tmp/output.log",  # Optional
        "stderr_file": "/tmp/error.log"    # Optional
    },
    timeout=300
)

event_id = bus.publish(event)
bus.join()

result = bus.get_results([event_id])[event_id]
if result.success:
    print(f"Return code: {result.data['returncode']}")
    print(f"Stdout: {result.data['stdout']}")
else:
    print(f"Command failed: {result.exception}")
```

### Execution Mode Comparison

| Feature | SYNC | THREAD | CORELET | CMD |
|---------|------|--------|---------|-----|
| **Parallelism** | No | Yes (GIL-limited) | Yes (true) | Yes |
| **Isolation** | No | Thread-only | Process | Process |
| **Overhead** | Minimal | Low | High | High |
| **Shared Memory** | Yes | Yes | No | No |
| **Use Case** | Fast I/O | Async I/O | CPU-bound | External tools |
| **Best For** | <100ms | 100ms-10s | >10s, CPU | CLI commands |

---

## 4. Basic Usage

### 4.1 Initialize EventBus

```python
from basefunctions import EventBus

# Auto-detect CPU cores (recommended)
bus = EventBus()

# Custom thread count
bus = EventBus(num_threads=16)
```

**Note**: EventBus is a **singleton** - only one instance per process. Multiple calls to `EventBus()` return the same instance.

### 4.2 Register Handler

Handlers must be registered **before** publishing events.

```python
from basefunctions import EventFactory, EventHandler, EventResult

# Define handler
class MyHandler(EventHandler):
    def handle(self, event, context):
        data = event.event_data
        result = process(data)
        return EventResult.business_result(
            event.event_id, True, result
        )

# Register handler
factory = EventFactory()
factory.register_event_type("my_event", MyHandler)
```

### 4.3 Create and Publish Events

```python
from basefunctions import Event, EXECUTION_MODE_THREAD

# Create event
event = Event(
    event_type="my_event",
    event_exec_mode=EXECUTION_MODE_THREAD,
    event_data={"key": "value"},
    priority=5,
    timeout=30
)

# Publish and get event ID
event_id = bus.publish(event)
```

### 4.4 Retrieve Results

```python
# Wait for all events to complete
bus.join()

# Get specific results (consumed from cache)
results = bus.get_results([event_id])
result = results[event_id]

if result.success:
    print(f"Data: {result.data}")
else:
    print(f"Error: {result.exception}")

# Or get all results (preserved in cache)
all_results = bus.get_results()  # Returns all cached results
```

### 4.5 Complete Example

```python
from basefunctions import (
    EventBus, Event, EventFactory, EventHandler, EventResult,
    EXECUTION_MODE_THREAD
)

# 1. Define Handler
class DataProcessor(EventHandler):
    def handle(self, event, context):
        try:
            data = event.event_data
            result = process_data(data)
            return EventResult.business_result(
                event.event_id, True, result
            )
        except Exception as e:
            return EventResult.exception_result(
                event.event_id, e
            )

# 2. Register Handler
factory = EventFactory()
factory.register_event_type("data_process", DataProcessor)

# 3. Initialize EventBus
bus = EventBus()

# 4. Publish Events
event_ids = []
for i in range(10):
    event = Event(
        event_type="data_process",
        event_exec_mode=EXECUTION_MODE_THREAD,
        event_data={"id": i}
    )
    event_ids.append(bus.publish(event))

# 5. Wait and Retrieve Results
bus.join()
results = bus.get_results(event_ids)

for event_id in event_ids:
    result = results[event_id]
    print(f"Event {event_id}: {result.success}")
```

---

## 5. Use Cases

### 5.1 Synchronous Event Processing

**Scenario**: Input validation that must complete before continuing.

```python
from basefunctions import EventBus, Event, EXECUTION_MODE_SYNC

bus = EventBus()

event = Event(
    event_type="validate_user_input",
    event_exec_mode=EXECUTION_MODE_SYNC,
    event_data={"email": "user@example.com", "age": 25}
)

event_id = bus.publish(event)

# Results immediately available
result = bus.get_results([event_id])[event_id]
if not result.success:
    raise ValueError(f"Validation failed: {result.data}")
```

### 5.2 Asynchronous Task Execution

**Scenario**: Fetch data from 100 APIs concurrently.

```python
from basefunctions import EventBus, Event, EXECUTION_MODE_THREAD

bus = EventBus()

urls = [f"https://api.example.com/data/{i}" for i in range(100)]

event_ids = []
for url in urls:
    event = Event(
        event_type="fetch_url",
        event_exec_mode=EXECUTION_MODE_THREAD,
        event_data={"url": url},
        timeout=10
    )
    event_ids.append(bus.publish(event))

# Wait for all fetches
bus.join()

# Process results
results = bus.get_results(event_ids)
successful = [r.data for r in results.values() if r.success]
print(f"Fetched {len(successful)}/{len(urls)} URLs")
```

### 5.3 Parallel Processing with Corelets

**Scenario**: Process large dataset chunks in parallel using all CPU cores.

```python
from basefunctions import EventBus, Event, EXECUTION_MODE_CORELET
import pandas as pd

bus = EventBus()

# Split DataFrame into chunks
df = pd.read_csv("large_dataset.csv")
chunk_size = len(df) // bus._num_threads
chunks = [df[i:i+chunk_size] for i in range(0, len(df), chunk_size)]

event_ids = []
for i, chunk in enumerate(chunks):
    event = Event(
        event_type="process_dataframe_chunk",
        event_exec_mode=EXECUTION_MODE_CORELET,
        event_data={"chunk": chunk, "chunk_id": i},
        timeout=120
    )
    event_ids.append(bus.publish(event))

bus.join()

# Combine results
results = bus.get_results(event_ids)
processed_chunks = [r.data for r in results.values() if r.success]
final_df = pd.concat(processed_chunks)
```

### 5.4 Priority-Based Scheduling

**Scenario**: Critical events should be processed before low-priority events.

```python
from basefunctions import EventBus, Event, EXECUTION_MODE_THREAD

bus = EventBus()

# Low priority: background cleanup
cleanup_event = Event(
    event_type="cleanup_temp_files",
    event_exec_mode=EXECUTION_MODE_THREAD,
    priority=2  # Low priority
)

# High priority: user request
user_event = Event(
    event_type="process_user_request",
    event_exec_mode=EXECUTION_MODE_THREAD,
    priority=9  # High priority - processed first!
)

bus.publish(cleanup_event)
bus.publish(user_event)  # Will be processed before cleanup

bus.join()
```

### 5.5 Timeout & Retry Logic

**Scenario**: Network requests that may fail and need retries.

```python
from basefunctions import EventBus, Event, EXECUTION_MODE_THREAD

bus = EventBus()

event = Event(
    event_type="api_request",
    event_exec_mode=EXECUTION_MODE_THREAD,
    event_data={"endpoint": "/users/123"},
    timeout=5,      # 5 second timeout per attempt
    max_retries=3   # Retry up to 3 times
)

event_id = bus.publish(event)
bus.join()

result = bus.get_results([event_id])[event_id]
if result.success:
    print(f"Success after {result.data.get('attempts', 1)} attempts")
else:
    print(f"Failed after 3 retries: {result.exception}")
```

### 5.6 Progress Tracking Integration

**Scenario**: Track progress of batch event processing.

```python
from basefunctions import EventBus, Event, EXECUTION_MODE_THREAD
from basefunctions import ProgressTracker

bus = EventBus()
tracker = ProgressTracker(total=100, desc="Processing items")

# Set progress tracker for current thread
bus.set_progress_tracker(tracker, progress_steps=1)

# Publish 100 events - each completion advances progress by 1
event_ids = []
for i in range(100):
    event = Event(
        event_type="process_item",
        event_exec_mode=EXECUTION_MODE_THREAD,
        event_data={"item_id": i}
    )
    event_ids.append(bus.publish(event))

bus.join()

# Clean up progress tracker
bus.clear_progress_tracker()

print(f"Completed {tracker.current}/{tracker.total}")
```

---

## 6. Handler Development

### 6.1 Basic Handler Structure

```python
from basefunctions import EventHandler, EventResult

class MyHandler(EventHandler):
    def handle(self, event, context):
        """
        Process event and return result.

        Parameters
        ----------
        event : Event
            Event to process
        context : EventContext
            Execution context with thread_local_data

        Returns
        -------
        EventResult
            Processing result
        """
        try:
            # Extract data
            data = event.event_data

            # Process
            result = self._process(data)

            # Return success
            return EventResult.business_result(
                event.event_id, True, result
            )

        except ValueError as e:
            # Business error (expected)
            return EventResult.business_result(
                event.event_id, False, str(e)
            )

        except Exception as e:
            # Technical error (unexpected)
            return EventResult.exception_result(
                event.event_id, e
            )

    def _process(self, data):
        # Implementation
        return {"processed": True}
```

### 6.2 EventResult Usage

**Business Result (Expected Outcomes):**

```python
# Success
return EventResult.business_result(
    event.event_id,
    success=True,
    data={"records_processed": 100}
)

# Business failure (validation error, not found, etc.)
return EventResult.business_result(
    event.event_id,
    success=False,
    data="User not found: ID 123"
)
```

**Exception Result (Technical Errors):**

```python
# Timeout, crash, network error, etc.
try:
    result = risky_operation()
except Exception as e:
    return EventResult.exception_result(event.event_id, e)
```

### 6.3 Thread-Local Storage via EventContext

Use `context.thread_local_data` for caching expensive resources:

```python
class DatabaseHandler(EventHandler):
    def handle(self, event, context):
        # Initialize DB connection once per thread
        if not hasattr(context.thread_local_data, 'db_connection'):
            context.thread_local_data.db_connection = create_db_connection()

        # Reuse connection
        conn = context.thread_local_data.db_connection
        result = conn.execute(event.event_data['query'])

        return EventResult.business_result(
            event.event_id, True, result
        )
```

**Benefits:**
- Connection pooling per thread
- Expensive initialization happens once
- Thread-safe by design (threading.local())
- Automatic cleanup on thread shutdown

### 6.4 Caching in Handlers

```python
class CachedAPIHandler(EventHandler):
    def handle(self, event, context):
        # Initialize cache
        if not hasattr(context.thread_local_data, 'api_cache'):
            context.thread_local_data.api_cache = {}

        cache = context.thread_local_data.api_cache
        key = event.event_data['resource_id']

        # Check cache
        if key in cache:
            return EventResult.business_result(
                event.event_id, True, cache[key]
            )

        # Fetch and cache
        data = fetch_from_api(key)
        cache[key] = data

        return EventResult.business_result(
            event.event_id, True, data
        )
```

### 6.5 Subprocess Cleanup with terminate()

If your handler spawns subprocesses, override `terminate()` for timeout cleanup:

```python
class SubprocessHandler(EventHandler):
    def handle(self, event, context):
        import subprocess

        # Start subprocess
        cmd = event.event_data['command']
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)

        # Store reference for cleanup
        context.thread_local_data.subprocess = proc

        # Wait for completion
        stdout, stderr = proc.communicate(timeout=event.timeout)

        # Clean up reference
        if hasattr(context.thread_local_data, 'subprocess'):
            delattr(context.thread_local_data, 'subprocess')

        return EventResult.business_result(
            event.event_id, True, {"stdout": stdout, "returncode": proc.returncode}
        )

    def terminate(self, context):
        """Called by EventBus on timeout to clean up subprocess."""
        if hasattr(context.thread_local_data, 'subprocess'):
            proc = context.thread_local_data.subprocess
            if proc.poll() is None:  # Still running
                proc.terminate()
                try:
                    proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    proc.kill()
            delattr(context.thread_local_data, 'subprocess')
```

### 6.6 Corelet-Compatible Handler

For CORELET mode, ensure handler and data are pickle-compatible:

```python
# ✅ GOOD: Stateless handler with pickle-compatible data
class CoreletHandler(EventHandler):
    def handle(self, event, context):
        import numpy as np  # Import inside handler (for corelet isolation)

        # Extract pickle-compatible data
        matrix = event.event_data['matrix']  # NumPy arrays are pickle-compatible

        # CPU-intensive operation
        result = np.linalg.inv(matrix)

        return EventResult.business_result(
            event.event_id, True, {"result": result.tolist()}
        )

# ❌ BAD: Handler with non-pickle-compatible state
class BadCoreletHandler(EventHandler):
    def __init__(self):
        self.lock = threading.Lock()  # ❌ Locks cannot be pickled!

    def handle(self, event, context):
        with self.lock:  # Will fail in corelet!
            pass
```

---

## 7. Important Concepts

### 7.1 Priority Queue (0-10)

Events are processed in priority order (higher = more important):

```python
# Priority 10: Critical user-facing requests
critical_event = Event(
    event_type="user_login",
    event_exec_mode=EXECUTION_MODE_THREAD,
    priority=10
)

# Priority 5: Normal background tasks
normal_event = Event(
    event_type="sync_data",
    event_exec_mode=EXECUTION_MODE_THREAD,
    priority=5
)

# Priority 1: Low-priority cleanup
cleanup_event = Event(
    event_type="cleanup",
    event_exec_mode=EXECUTION_MODE_THREAD,
    priority=1
)
```

**Default priority**: 5

### 7.2 Timeout Handling

Each event has a configurable timeout (default: 30 seconds):

```python
event = Event(
    event_type="long_task",
    event_exec_mode=EXECUTION_MODE_THREAD,
    timeout=120  # 2 minutes
)
```

**On timeout:**
1. Handler execution interrupted via `TimerThread`
2. Handler's `terminate()` method called (if overridden)
3. Retry logic triggered (if `max_retries > 0`)
4. After all retries: `EventResult.exception_result(event_id, TimeoutError)`

**For CORELET mode**, timeout has 1-second safety buffer to allow graceful shutdown.

### 7.3 Retry Logic

Events are retried automatically on failure:

```python
event = Event(
    event_type="api_call",
    event_exec_mode=EXECUTION_MODE_THREAD,
    max_retries=5,  # Retry up to 5 times
    timeout=10      # 10 seconds per attempt
)
```

**Retry behavior:**
- Retries triggered on: TimeoutError, Exception from handler
- **Not** retried on: Business failures (`success=False` in `business_result`)
- Total time: `timeout * max_retries` (e.g., 50 seconds for above)

### 7.4 LRU Result Caching

Results are cached with **LRU eviction** to prevent memory growth:

**Cache size**: `num_threads * 1000` (default)

**Two retrieval patterns:**

1. **Consumer Pattern** (specific event IDs):
   ```python
   # Results removed from cache after retrieval
   results = bus.get_results([event_id])
   ```

2. **Observer Pattern** (all results):
   ```python
   # Results preserved in cache (LRU handles eviction)
   all_results = bus.get_results()
   ```

**Why this matters:**
- Prevents unbounded memory growth
- Supports both one-time consumers and multiple observers
- LRU evicts oldest results when limit reached

### 7.5 Thread Safety

**Thread-safe components:**
- EventBus (uses RLock)
- EventFactory (uses RLock)
- Priority queue (thread-safe)
- Result cache (lock-protected)

**Thread-local storage:**
- `context.thread_local_data` is inherently thread-safe
- Each thread has isolated storage
- No locking required for accessing `thread_local_data`

**Handler thread safety:**
- SYNC/THREAD mode: Handlers must be thread-safe
- CORELET mode: Process isolation, no shared state

### 7.6 Progress Tracking

Automatically update progress trackers for batch operations:

```python
from basefunctions import ProgressTracker

tracker = ProgressTracker(total=1000)

# Set tracker for current thread
bus.set_progress_tracker(tracker, progress_steps=1)

# Each event completion advances progress by 1
for i in range(1000):
    event = Event("process_item", EXECUTION_MODE_THREAD, event_data={"id": i})
    bus.publish(event)

bus.join()
bus.clear_progress_tracker()

print(f"Progress: {tracker.current}/{tracker.total}")
```

**Alternative: Per-event progress tracking:**

```python
tracker = ProgressTracker(total=100)

event = Event(
    event_type="process_batch",
    event_exec_mode=EXECUTION_MODE_THREAD,
    event_data={"items": items},
    progress_tracker=tracker,
    progress_steps=10  # Advance by 10 on completion
)
```

---

## 8. Critical Warnings

### 8.1 EventBus is Singleton

**IMPORTANT**: Only one EventBus instance per process!

```python
# Both variables reference the SAME instance
bus1 = EventBus()
bus2 = EventBus()

assert bus1 is bus2  # True
```

**Implication**: Configuration changes affect all code using EventBus.

### 8.2 Handlers Must Be Thread-Safe (THREAD mode)

Handlers in THREAD mode are cached per-thread but can be called concurrently:

```python
# ❌ BAD: Shared mutable state
class BadHandler(EventHandler):
    def __init__(self):
        self.counter = 0  # Shared across events!

    def handle(self, event, context):
        self.counter += 1  # Race condition!
        return EventResult.business_result(event.event_id, True, self.counter)

# ✅ GOOD: Stateless handler
class GoodHandler(EventHandler):
    def handle(self, event, context):
        # Use context.thread_local_data for state
        if not hasattr(context.thread_local_data, 'counter'):
            context.thread_local_data.counter = 0

        context.thread_local_data.counter += 1
        return EventResult.business_result(
            event.event_id, True, context.thread_local_data.counter
        )
```

### 8.3 Corelet Data Must Be Pickle-Compatible

**CORELET mode serializes events via pickle**:

```python
# ✅ GOOD: Pickle-compatible
event_data = {
    "numbers": [1, 2, 3],
    "dataframe": pd.DataFrame(...),  # Pandas supports pickle
    "config": {"key": "value"}
}

# ❌ BAD: Cannot pickle
event_data = {
    "file": open("file.txt"),         # File handles
    "lock": threading.Lock(),         # Locks
    "lambda": lambda x: x + 1,        # Lambdas
    "generator": (x for x in range(10))  # Generators
}
```

**Error you'll see:**
```
TypeError: cannot pickle '_io.TextIOWrapper' object
```

### 8.4 Result Caching: Specific IDs Are Consumed

**Important**: Retrieving specific event IDs **removes** them from cache!

```python
event_id = bus.publish(event)
bus.join()

# First retrieval: Returns result (and removes from cache)
result1 = bus.get_results([event_id])
print(result1[event_id].data)  # Works

# Second retrieval: Result not found!
result2 = bus.get_results([event_id])
print(result2)  # {} - empty dict!
```

**Solution**: Store results if you need them multiple times:

```python
results = bus.get_results([event_id])
result = results[event_id]
# Use 'result' as many times as needed
```

### 8.5 join() Blocks Until Queue Empty

`join()` waits for **all** queued events, not just yours:

```python
# Thread A:
for i in range(1000):
    bus.publish(Event("slow_task", EXECUTION_MODE_THREAD))

# Thread B (concurrent):
event_id = bus.publish(Event("my_task", EXECUTION_MODE_THREAD))
bus.join()  # ⚠️ Waits for all 1001 events!
```

**Solution**: Track your own event IDs and use non-blocking retrieval:

```python
event_id = bus.publish(Event("my_task", EXECUTION_MODE_THREAD))

# Non-blocking check
while True:
    results = bus.get_results([event_id], join_before=False)
    if event_id in results:
        break
    time.sleep(0.1)
```

### 8.6 Corelet Lifecycle Management (CRITICAL!)

**⚠️ KNOWN ISSUE**: Corelet processes are **not automatically cleaned up** during runtime!

**Current behavior:**
- Corelets created on first use per thread
- Kept alive for session duration (until shutdown event)
- **No automatic cleanup** if threads keep running

**Implications:**
- Under load: Hundreds/thousands of corelet processes may accumulate
- Memory leak potential
- Process table pollution

**Temporary mitigations:**
1. Monitor process count: `ps aux | grep corelet | wc -l`
2. Set OS process limits
3. Periodic manual cleanup (restart workers)
4. Use explicit shutdown: `bus.shutdown()`

**TODO**: Implement proper lifecycle management (HIGH PRIORITY)

Options being considered:
- SESSION-BASED: Cleanup on thread shutdown (current approach)
- IDLE TIMEOUT: Terminate after inactivity (10 min default in code)
- POOL-BASED: Maintain reusable corelet pool

### 8.7 Signal Handling in CoreletWorker

Corelets handle signals for graceful shutdown:

- **SIGTERM**: Graceful shutdown (finish current event)
- **SIGINT**: Immediate shutdown

**Don't send signals manually** - use EventBus shutdown:

```python
# ✅ GOOD:
bus.shutdown()

# ❌ BAD:
os.kill(corelet_pid, signal.SIGTERM)  # Don't do this!
```

---

## 9. Best Practices

### 9.1 When to Use Which Mode?

**Decision Tree:**

```
Is it < 100ms fast?
├─ Yes → SYNC
└─ No → Is it CPU-bound?
    ├─ Yes → CORELET
    └─ No (I/O-bound) → THREAD
```

**Examples:**

| Task | Mode | Reason |
|------|------|--------|
| Input validation | SYNC | Fast, need immediate result |
| Database query | THREAD | I/O-bound, benefits from async |
| API request (100x) | THREAD | I/O-bound, parallelizable |
| Image processing | CORELET | CPU-bound, needs true parallelism |
| Matrix multiplication | CORELET | CPU-bound, no GIL interference |
| File read (small) | SYNC | Fast enough |
| File read (large) | THREAD | I/O-bound |
| Running `ffmpeg` | CMD | External tool |

### 9.2 Keep Handlers Stateless

**Why**: Enables caching, thread-safety, and predictability.

```python
# ✅ GOOD: Stateless
class StatelessHandler(EventHandler):
    def handle(self, event, context):
        data = event.event_data
        result = self._process(data)
        return EventResult.business_result(event.event_id, True, result)

    def _process(self, data):
        # Pure function - no side effects
        return data['value'] * 2

# ❌ BAD: Stateful
class StatefulHandler(EventHandler):
    def __init__(self):
        self.results = []  # Shared state!

    def handle(self, event, context):
        result = self._process(event.event_data)
        self.results.append(result)  # Race condition!
        return EventResult.business_result(event.event_id, True, result)
```

### 9.3 Use EventContext for State

**Pattern**: Expensive initialization once per thread, reuse across events.

```python
class DatabaseHandler(EventHandler):
    def handle(self, event, context):
        # Initialize connection once
        if not hasattr(context.thread_local_data, 'db'):
            context.thread_local_data.db = connect_to_database()

        db = context.thread_local_data.db

        # Use connection
        result = db.query(event.event_data['sql'])

        return EventResult.business_result(event.event_id, True, result)
```

**Benefits:**
- Connection pooling per thread
- Automatic cleanup on thread exit
- Thread-safe by design

### 9.4 Implement Idempotent Handlers

**Idempotent**: Same input → same output, no side effects.

```python
# ✅ GOOD: Idempotent
class IdempotentHandler(EventHandler):
    def handle(self, event, context):
        user_id = event.event_data['user_id']

        # Check if already processed
        if is_already_processed(user_id):
            return EventResult.business_result(
                event.event_id, True, "Already processed"
            )

        # Process
        result = process_user(user_id)
        mark_as_processed(user_id)

        return EventResult.business_result(event.event_id, True, result)
```

**Why**: Safe retries, no duplicate operations.

### 9.5 Use business_result vs exception_result Correctly

**Rule of thumb:**
- **Expected failures** → `business_result(success=False)`
- **Unexpected errors** → `exception_result(exception=...)`

```python
def handle(self, event, context):
    try:
        user_id = event.event_data['user_id']

        # Validation: Expected failure
        if user_id < 0:
            return EventResult.business_result(
                event.event_id, False, "Invalid user_id: must be positive"
            )

        # Process
        user = db.get_user(user_id)

        # Not found: Expected failure
        if not user:
            return EventResult.business_result(
                event.event_id, False, f"User {user_id} not found"
            )

        # Success
        return EventResult.business_result(
            event.event_id, True, user
        )

    except DatabaseConnectionError as e:
        # Unexpected error: Network, DB down, etc.
        return EventResult.exception_result(event.event_id, e)
```

### 9.6 Set Priorities Wisely

**Priority Guidelines:**

- **10**: Critical user-facing operations (login, checkout)
- **8-9**: High-priority background tasks (payment processing)
- **5**: Normal operations (default)
- **2-3**: Low-priority background tasks (analytics, cleanup)
- **1**: Lowest priority (archival, cold storage)

```python
# User login: Critical
login_event = Event("user_login", EXECUTION_MODE_THREAD, priority=10)

# Data sync: Normal
sync_event = Event("sync_data", EXECUTION_MODE_THREAD, priority=5)

# Cleanup: Low
cleanup_event = Event("cleanup", EXECUTION_MODE_THREAD, priority=2)
```

### 9.7 Choose Timeouts Appropriately

**Guidelines:**

| Task Type | Timeout |
|-----------|---------|
| Database query | 5-10s |
| API request | 10-30s |
| File I/O | 30-60s |
| Image processing | 60-300s |
| ML training | 3600s+ |

**Add buffer for retries:**

```python
# Timeout per attempt: 10s
# Max retries: 3
# Total time: 10s * 3 = 30s
event = Event(
    event_type="api_call",
    event_exec_mode=EXECUTION_MODE_THREAD,
    timeout=10,
    max_retries=3
)
```

### 9.8 Use Progress Tracking for Long Tasks

```python
from basefunctions import ProgressTracker

tracker = ProgressTracker(total=1000, desc="Processing items")

bus.set_progress_tracker(tracker, progress_steps=1)

for i in range(1000):
    event = Event("process_item", EXECUTION_MODE_THREAD, event_data={"id": i})
    bus.publish(event)

bus.join()
bus.clear_progress_tracker()
```

**Or**: Per-event tracking for batch operations:

```python
tracker = ProgressTracker(total=100)

event = Event(
    event_type="process_batch",
    event_exec_mode=EXECUTION_MODE_THREAD,
    event_data={"items": items},
    progress_tracker=tracker,
    progress_steps=10  # Each batch = 10 items
)
```

---

## 10. Common Errors & Troubleshooting

### 10.1 NoHandlerAvailableError

**Error:**
```python
NoHandlerAvailableError: No handler available for event type: 'my_event'
```

**Cause**: Handler not registered before publishing event.

**Solution**:
```python
# Register handler BEFORE publishing
factory = EventFactory()
factory.register_event_type("my_event", MyHandler)

# Then publish
event = Event("my_event", EXECUTION_MODE_THREAD)
bus.publish(event)
```

### 10.2 Pickle Errors in CORELET Mode

**Error:**
```python
TypeError: cannot pickle '_io.TextIOWrapper' object
```

**Cause**: Event data contains non-pickle-compatible objects.

**Solution**: Convert to pickle-compatible types:

```python
# ❌ BAD:
event_data = {"file": open("data.txt")}

# ✅ GOOD:
with open("data.txt") as f:
    content = f.read()
event_data = {"content": content}  # String is pickle-compatible
```

**Common culprits:**
- File handles → Read content first
- Locks → Use process-safe alternatives (multiprocessing.Lock)
- Lambdas → Use named functions
- Generators → Convert to list
- Database connections → Recreate in corelet

### 10.3 Timeout Too Short

**Symptom**: Events fail with `TimeoutError` even though handler works.

**Cause**: Timeout too aggressive for operation.

**Solution**: Increase timeout:

```python
# Before (too short)
event = Event("heavy_task", EXECUTION_MODE_THREAD, timeout=5)

# After (realistic)
event = Event("heavy_task", EXECUTION_MODE_THREAD, timeout=60)
```

**Debug tip**: Log execution time:

```python
class DebugHandler(EventHandler):
    def handle(self, event, context):
        import time
        start = time.time()

        result = self._process(event.event_data)

        elapsed = time.time() - start
        print(f"Execution time: {elapsed:.2f}s")

        return EventResult.business_result(event.event_id, True, result)
```

### 10.4 Memory Leaks (Results Not Retrieved)

**Symptom**: Memory usage grows over time.

**Cause**: Results cached but never retrieved.

**Solution**: Retrieve results regularly:

```python
# ❌ BAD: Publish without retrieving
for i in range(10000):
    bus.publish(Event("task", EXECUTION_MODE_THREAD))
# Results accumulate in cache!

# ✅ GOOD: Retrieve in batches
batch_size = 100
for batch_start in range(0, 10000, batch_size):
    event_ids = []
    for i in range(batch_start, batch_start + batch_size):
        event_ids.append(bus.publish(Event("task", EXECUTION_MODE_THREAD)))

    bus.join()
    results = bus.get_results(event_ids)  # Consume results
```

### 10.5 Deadlock with join()

**Symptom**: `join()` hangs indefinitely.

**Cause**: Handler waiting for another event to complete.

```python
# ❌ BAD: Deadlock
class DeadlockHandler(EventHandler):
    def handle(self, event, context):
        # Publish another event
        new_event = Event("other_task", EXECUTION_MODE_THREAD)
        event_id = bus.publish(new_event)

        # Wait for it (blocks worker thread!)
        bus.join()  # ⚠️ DEADLOCK!

        return EventResult.business_result(event.event_id, True, "done")
```

**Solution**: Use SYNC mode for dependent events or publish without waiting:

```python
# ✅ GOOD: Use SYNC for dependent events
class NoDeadlockHandler(EventHandler):
    def handle(self, event, context):
        # Use SYNC mode (immediate execution)
        new_event = Event("other_task", EXECUTION_MODE_SYNC)
        event_id = bus.publish(new_event)

        # Results available immediately
        results = bus.get_results([event_id])

        return EventResult.business_result(event.event_id, True, "done")
```

### 10.6 Corelet Processes Accumulating

**Symptom**: `ps aux | grep python` shows many corelet processes.

**Cause**: No automatic cleanup (known issue).

**Mitigation**:

```python
# Graceful shutdown when done
bus.shutdown()

# Or: Monitor and alert
import psutil
corelet_count = len([p for p in psutil.process_iter() if 'corelet' in p.name()])
if corelet_count > 100:
    print("WARNING: Too many corelet processes!")
```

### 10.7 Handler Not Thread-Safe

**Symptom**: Intermittent failures, race conditions, wrong results.

**Cause**: Shared mutable state in handler.

**Solution**: Use thread-local storage:

```python
# ❌ BAD: Shared counter
class UnsafeHandler(EventHandler):
    def __init__(self):
        self.counter = 0

    def handle(self, event, context):
        self.counter += 1  # Race condition!
        return EventResult.business_result(event.event_id, True, self.counter)

# ✅ GOOD: Thread-local counter
class SafeHandler(EventHandler):
    def handle(self, event, context):
        if not hasattr(context.thread_local_data, 'counter'):
            context.thread_local_data.counter = 0

        context.thread_local_data.counter += 1
        return EventResult.business_result(
            event.event_id, True, context.thread_local_data.counter
        )
```

---

## 11. API Reference

### 11.1 EventBus

**Constructor:**
```python
EventBus(num_threads: Optional[int] = None)
```

**Parameters:**
- `num_threads`: Number of worker threads. If None, auto-detects CPU cores.

**Methods:**

#### `publish(event: Event) -> str`

Publish event to handlers.

**Parameters:**
- `event`: Event to publish

**Returns:**
- Event ID (str) for result tracking

**Raises:**
- `InvalidEventError`: Invalid event
- `NoHandlerAvailableError`: No handler registered

**Example:**
```python
event_id = bus.publish(Event("my_event", EXECUTION_MODE_THREAD))
```

#### `join() -> None`

Wait for all queued events to complete.

**Example:**
```python
bus.join()
```

#### `get_results(event_ids: List[str] = None, join_before: bool = True) -> Dict[str, EventResult]`

Retrieve event results.

**Parameters:**
- `event_ids`: List of event IDs (or single ID). If None, returns all results.
- `join_before`: Wait for queue to empty before retrieving (default: True)

**Returns:**
- Dict mapping event IDs to EventResult objects

**Example:**
```python
# Specific results (consumed)
results = bus.get_results([event_id])

# All results (preserved)
all_results = bus.get_results()

# Non-blocking
results = bus.get_results([event_id], join_before=False)
```

#### `shutdown(immediately: bool = False) -> None`

Shutdown EventBus and worker threads/processes.

**Parameters:**
- `immediately`: If True, shutdown with high priority

**Example:**
```python
bus.shutdown()
```

#### `set_progress_tracker(progress_tracker: ProgressTracker, progress_steps: int = 1) -> None`

Set progress tracker for current thread.

**Parameters:**
- `progress_tracker`: ProgressTracker instance
- `progress_steps`: Steps to advance per event completion

**Example:**
```python
tracker = ProgressTracker(total=100)
bus.set_progress_tracker(tracker, progress_steps=1)
```

#### `clear_progress_tracker() -> None`

Clear progress tracker for current thread.

**Example:**
```python
bus.clear_progress_tracker()
```

### 11.2 Event

**Constructor:**
```python
Event(
    event_type: str,
    event_exec_mode: str = EXECUTION_MODE_THREAD,
    event_name: Optional[str] = None,
    event_source: Optional[Any] = None,
    event_target: Any = None,
    event_data: Any = None,
    max_retries: int = 3,
    timeout: int = 30,
    priority: int = 5,
    corelet_meta: Optional[dict] = None,
    progress_tracker: Optional[ProgressTracker] = None,
    progress_steps: int = 0
)
```

**Key Parameters:**
- `event_type`: Event type identifier (for handler routing)
- `event_exec_mode`: SYNC, THREAD, CORELET, or CMD
- `event_data`: Payload data
- `priority`: 0-10, higher = more important
- `timeout`: Processing timeout in seconds
- `max_retries`: Number of retry attempts

**Example:**
```python
event = Event(
    event_type="data_process",
    event_exec_mode=EXECUTION_MODE_THREAD,
    event_data={"file": "data.csv"},
    priority=7,
    timeout=60,
    max_retries=3
)
```

### 11.3 EventHandler

**Abstract Methods:**

#### `handle(event: Event, context: EventContext) -> EventResult`

Process event.

**Parameters:**
- `event`: Event to process
- `context`: Execution context

**Returns:**
- EventResult

**Example:**
```python
class MyHandler(EventHandler):
    def handle(self, event, context):
        data = event.event_data
        result = process(data)
        return EventResult.business_result(event.event_id, True, result)
```

#### `terminate(context: EventContext) -> None`

Terminate running processes (optional override).

**Example:**
```python
def terminate(self, context):
    if hasattr(context.thread_local_data, 'subprocess'):
        context.thread_local_data.subprocess.terminate()
```

### 11.4 EventResult

**Class Methods:**

#### `business_result(event_id: str, success: bool, data: Any = None) -> EventResult`

Create business result (expected outcome).

**Example:**
```python
# Success
result = EventResult.business_result(event_id, True, {"count": 100})

# Failure
result = EventResult.business_result(event_id, False, "Validation error")
```

#### `exception_result(event_id: str, exception: Exception) -> EventResult`

Create exception result (technical error).

**Example:**
```python
try:
    risky_operation()
except Exception as e:
    result = EventResult.exception_result(event_id, e)
```

**Attributes:**
- `event_id` (str): Event ID
- `success` (bool): Success flag
- `data` (Any): Result data or error message
- `exception` (Exception): Exception object (if technical error)

### 11.5 EventFactory

**Methods:**

#### `register_event_type(event_type: str, event_handler_class: Type[EventHandler]) -> None`

Register handler for event type.

**Example:**
```python
factory = EventFactory()
factory.register_event_type("my_event", MyHandler)
```

#### `create_handler(event_type: str) -> EventHandler`

Create handler instance.

**Example:**
```python
handler = factory.create_handler("my_event")
```

#### `is_handler_available(event_type: str) -> bool`

Check if handler is registered.

**Example:**
```python
if factory.is_handler_available("my_event"):
    print("Handler registered")
```

#### `get_handler_meta(event_type: str) -> dict`

Get handler metadata for corelet.

**Returns:**
```python
{
    "module_path": "myapp.handlers",
    "class_name": "MyHandler",
    "event_type": "my_event"
}
```

#### `get_supported_event_types() -> List[str]`

Get all registered event types.

**Example:**
```python
event_types = factory.get_supported_event_types()
```

### 11.6 EventContext

**Attributes:**
- `thread_local_data`: Thread-local storage (threading.local())
- `thread_id`: Thread identifier
- `process_id`: Process PID (corelet mode)
- `worker`: CoreletWorker reference (corelet mode)
- `timestamp`: Creation timestamp

**Example:**
```python
def handle(self, event, context):
    # Access thread-local storage
    if not hasattr(context.thread_local_data, 'cache'):
        context.thread_local_data.cache = {}

    # Use cache
    cache = context.thread_local_data.cache
```

### 11.7 Execution Mode Constants

```python
from basefunctions import (
    EXECUTION_MODE_SYNC,    # "sync"
    EXECUTION_MODE_THREAD,  # "thread"
    EXECUTION_MODE_CORELET, # "corelet"
    EXECUTION_MODE_CMD      # "cmd"
)
```

### 11.8 Internal Events

```python
from basefunctions import (
    INTERNAL_SHUTDOWN_EVENT,           # "_shutdown"
    INTERNAL_CMD_EXECUTION_EVENT,      # "_cmd_execution"
    INTERNAL_CORELET_FORWARDING_EVENT  # "_corelet_forwarding"
)
```

**Note**: These are registered automatically. Don't register handlers for them manually.

---

## Conclusion

The EventBus system provides a powerful, flexible event-driven architecture for Python applications. By understanding the **three execution modes** (SYNC, THREAD, CORELET), properly implementing handlers, and following best practices, you can build scalable, fault-tolerant systems with clean separation of concerns.

**Key Takeaways:**

1. **Choose the right mode**: SYNC for fast ops, THREAD for I/O, CORELET for CPU-bound
2. **Keep handlers stateless**: Use `context.thread_local_data` for caching
3. **Use business_result vs exception_result correctly**: Expected vs unexpected failures
4. **Be aware of pickle limitations**: Only for CORELET mode
5. **Retrieve results regularly**: Prevent memory leaks
6. **Set realistic timeouts and priorities**: Match your workload
7. **⚠️ Watch for corelet process leaks**: Known issue, mitigate with shutdown

For questions or issues, refer to the source code or file a bug report.

---

**Document Version**: 1.1
**Last Updated**: 2025-01-24
**EventBus Version**: basefunctions 0.5.32
