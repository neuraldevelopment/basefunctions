# HTTP Module Guide

**Version:** basefunctions v0.5.32
**Last Updated:** 2025-01-24

---

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [HttpClient Class](#httpclient-class)
  - [Synchronous Requests](#synchronous-requests)
  - [Asynchronous Requests](#asynchronous-requests)
  - [Result Management](#result-management)
- [HttpClientHandler](#httpclienthandler)
- [Architecture](#architecture)
- [Error Handling](#error-handling)
- [Use Cases](#use-cases)
- [API Reference](#api-reference)

---

## Overview

The `http` module provides a simple, event-driven HTTP client built on top of the basefunctions EventBus system. It enables both synchronous and asynchronous HTTP requests with automatic event ID management and comprehensive error handling.

**Key Features:**
- **Event-driven architecture** - HTTP requests as events
- **Sync and async modes** - Choose blocking or non-blocking requests
- **Automatic ID tracking** - Manages pending async request IDs
- **Structured results** - Rich metadata and error information
- **Thread-based execution** - HTTP requests run in threads
- **Simple API** - Minimal boilerplate for common use cases

**Components:**
- `HttpClient` - High-level client for making HTTP requests
- `HttpClientHandler` - EventHandler that processes HTTP requests
- `register_http_handlers()` - Registers handler with EventBus

---

## Quick Start

### Initialization

The HTTP module is automatically initialized when you import basefunctions:

```python
import basefunctions

# Initialize framework (registers HTTP handlers)
basefunctions.initialize()
```

### Basic Synchronous Request

```python
from basefunctions import HttpClient

client = HttpClient()

# Synchronous GET request
response = client.get_sync("https://api.github.com/users/octocat")
print(response)  # Response text content
```

### Basic Asynchronous Requests

```python
from basefunctions import HttpClient

client = HttpClient()

# Send multiple async requests
event_id1 = client.get_async("https://api.github.com/users/octocat")
event_id2 = client.get_async("https://api.github.com/users/torvalds")
event_id3 = client.get_async("https://api.github.com/users/gvanrossum")

# Get all results
results = client.get_results()

# Access response data
for event_id, data in results['data'].items():
    print(f"{event_id}: {data[:50]}...")

# Check metadata
print(f"Total: {results['metadata']['total_requested']}")
print(f"Successful: {results['metadata']['successful']}")
print(f"Failed: {results['metadata']['failed']}")

# Handle errors
if results['errors']:
    for event_id, error in results['errors'].items():
        print(f"Error for {event_id}: {error}")
```

---

## HttpClient Class

The `HttpClient` class provides a high-level interface for HTTP requests with automatic event management.

### Synchronous Requests

**Method:** `get_sync(url: str, **kwargs) -> Any`

Send an HTTP GET request and wait for the result.

**Parameters:**
- `url` (str): Target URL for GET request
- `**kwargs`: Additional parameters passed to event_data

**Returns:**
- `Any`: HTTP response content (text)

**Raises:**
- `RuntimeError`: If request failed or no response received

**Example:**

```python
client = HttpClient()

try:
    response = client.get_sync("https://api.example.com/data")
    print(f"Response: {response}")
except RuntimeError as e:
    print(f"Request failed: {e}")
```

**How it works:**
1. Creates an Event with type `"http_request"`
2. Publishes event to EventBus
3. Waits for event to complete (`join()`)
4. Retrieves result and returns data or raises error

---

### Asynchronous Requests

**Method:** `get_async(url: str, **kwargs) -> str`

Send an HTTP GET request asynchronously and return event ID immediately.

**Parameters:**
- `url` (str): Target URL for GET request
- `**kwargs`: Additional parameters passed to event_data

**Returns:**
- `str`: Event ID for result tracking

**Example:**

```python
client = HttpClient()

# Send multiple requests without waiting
id1 = client.get_async("https://api.example.com/user/1")
id2 = client.get_async("https://api.example.com/user/2")
id3 = client.get_async("https://api.example.com/user/3")

# Do other work here...

# Get results later
results = client.get_results()
```

**Automatic ID Tracking:**
- Event IDs are automatically tracked in internal `_pending_event_ids` list
- IDs are removed from pending list when results are retrieved
- No manual ID management required for typical use cases

---

### Result Management

**Method:** `get_results(event_ids: list[str] | None = None, join_before: bool = True) -> dict[str, Any]`

Retrieve results from async requests with automatic ID management.

**Parameters:**
- `event_ids` (Optional[List[str]]): Specific event IDs to retrieve. If None, retrieves all pending events.
- `join_before` (bool): Wait for all pending events before retrieving results. Default is True.

**Returns:**
- `dict[str, Any]`: Dictionary with structure:
  ```python
  {
      'data': {event_id: response_data, ...},
      'metadata': {
          'total_requested': int,
          'successful': int,
          'failed': int,
          'event_ids': {event_id: 'success'|'failed', ...},
          'timestamp': str  # ISO format
      },
      'errors': {event_id: error_message, ...}
  }
  ```

**Examples:**

**1. Get all pending results:**

```python
client = HttpClient()

# Send async requests
client.get_async("https://api.example.com/user/1")
client.get_async("https://api.example.com/user/2")

# Get all results
results = client.get_results()

# Access successful responses
for event_id, data in results['data'].items():
    print(f"Success: {data}")

# Check for errors
if results['errors']:
    for event_id, error in results['errors'].items():
        print(f"Failed: {error}")
```

**2. Get specific event results:**

```python
client = HttpClient()

id1 = client.get_async("https://api.example.com/fast")
id2 = client.get_async("https://api.example.com/slow")

# Get only first result
results = client.get_results([id1])
print(results['data'][id1])

# Get second result later
results = client.get_results([id2])
print(results['data'][id2])
```

**3. Get results without waiting:**

```python
client = HttpClient()

client.get_async("https://api.example.com/data")

# Get results immediately (may be incomplete)
results = client.get_results(join_before=False)

if results['data']:
    print("Some results available")
else:
    print("No results yet")
```

---

### Pending ID Management

**Method:** `get_pending_ids() -> list[str]`

Get list of pending event IDs.

**Returns:**
- `List[str]`: Copy of pending event IDs list

**Example:**

```python
client = HttpClient()

client.get_async("https://api.example.com/user/1")
client.get_async("https://api.example.com/user/2")

pending = client.get_pending_ids()
print(f"Pending requests: {len(pending)}")
```

---

**Method:** `set_pending_ids(event_ids: list[str]) -> None`

Set pending event IDs list.

**Parameters:**
- `event_ids` (List[str]): New list of event IDs to track

**Example:**

```python
client = HttpClient()

# Manually set pending IDs (advanced use case)
client.set_pending_ids(['event-123', 'event-456'])
```

---

## HttpClientHandler

The `HttpClientHandler` is an `EventHandler` subclass that processes HTTP requests.

**Event Type:** `"http_request"`

**Execution Mode:** `EXECUTION_MODE_THREAD` (runs in thread pool)

**Event Data Structure:**

```python
{
    "url": "https://api.example.com/endpoint",
    "method": "GET"  # Optional, defaults to GET
}
```

**Returns:** `EventResult` with:
- `success=True`: Response content (text)
- `success=False`: Error message

**Example - Using Handler Directly:**

```python
from basefunctions import EventBus, Event

bus = EventBus()

# Create HTTP request event
event = Event(
    event_type="http_request",
    event_data={"url": "https://api.github.com", "method": "GET"}
)

# Publish and wait
bus.publish(event)
bus.join()

# Get result
results = bus.get_results([event.event_id])
result = results[event.event_id]

if result.success:
    print(f"Response: {result.data}")
else:
    print(f"Error: {result.data}")
```

**Implementation Details:**

```python
class HttpClientHandler(basefunctions.EventHandler):
    """Simple HTTP request handler."""

    execution_mode = basefunctions.EXECUTION_MODE_THREAD

    def handle(self, event, context=None):
        # Extract URL and method
        url = event.event_data.get("url")
        method = event.event_data.get("method", "GET").upper()

        # Make request with 30s timeout
        response = requests.request(method, url, timeout=30)
        response.raise_for_status()

        # Return response text
        return EventResult.business_result(event.event_id, True, response.text)
```

---

## Architecture

### Event-Driven Design

The HTTP module integrates with the basefunctions event system:

```
HttpClient
    ↓
  Event (type="http_request")
    ↓
  EventBus.publish()
    ↓
  EventFactory → HttpClientHandler
    ↓
  ThreadPoolExecutor (EXECUTION_MODE_THREAD)
    ↓
  requests.request()
    ↓
  EventResult (success + data/error)
    ↓
  EventBus.get_results()
    ↓
  HttpClient.get_results()
```

### Benefits of Event-Driven Approach

1. **Decoupling**: HTTP logic separate from business logic
2. **Async by default**: Non-blocking requests with minimal code
3. **Centralized management**: All HTTP requests flow through EventBus
4. **Consistent error handling**: EventResult structure for all requests
5. **Monitoring**: Easy to add logging/metrics at EventBus level
6. **Testing**: Mock EventBus instead of HTTP layer

---

## Error Handling

### Synchronous Request Errors

`get_sync()` raises `RuntimeError` on failure:

```python
client = HttpClient()

try:
    response = client.get_sync("https://invalid-url.example.com")
except RuntimeError as e:
    print(f"Request failed: {e}")
    # e.g., "HTTP error: Connection timeout"
```

### Asynchronous Request Errors

`get_async()` returns event ID immediately. Errors are available in `get_results()`:

```python
client = HttpClient()

id1 = client.get_async("https://api.example.com/valid")
id2 = client.get_async("https://invalid-url.example.com")

results = client.get_results()

# Check individual event status
status = results['metadata']['event_ids']
print(f"Event {id1}: {status[id1]}")  # "success"
print(f"Event {id2}: {status[id2]}")  # "failed"

# Access error details
if id2 in results['errors']:
    print(f"Error: {results['errors'][id2]}")
```

### Error Categories

1. **Missing URL**: Event data missing `"url"` key
2. **HTTP Errors**: Status code errors (404, 500, etc.)
3. **Network Errors**: Connection timeout, DNS failure, etc.
4. **Request Exceptions**: Any `requests.exceptions.RequestException`
5. **Unexpected Errors**: Caught as generic exceptions

**Error Structure in Results:**

```python
{
    'errors': {
        'event-abc': 'HTTP error: 404 Client Error: Not Found',
        'event-def': 'HTTP error: Connection timeout',
        'event-ghi': 'Missing URL'
    }
}
```

---

## Use Cases

### 1. Batch Data Fetching

Fetch data from multiple endpoints efficiently:

```python
client = HttpClient()

# Define endpoints
user_ids = [1, 2, 3, 4, 5]
base_url = "https://api.example.com/users"

# Send all requests asynchronously
for user_id in user_ids:
    client.get_async(f"{base_url}/{user_id}")

# Get all results
results = client.get_results()

# Process successful responses
for event_id, data in results['data'].items():
    process_user_data(data)

# Log failures
if results['errors']:
    logger.warning(f"Failed requests: {len(results['errors'])}")
```

### 2. API Health Monitoring

Check multiple service endpoints:

```python
client = HttpClient()

endpoints = [
    "https://api1.example.com/health",
    "https://api2.example.com/health",
    "https://api3.example.com/health"
]

# Check all endpoints
for endpoint in endpoints:
    client.get_async(endpoint)

# Get results
results = client.get_results()

# Generate health report
report = {
    'timestamp': results['metadata']['timestamp'],
    'total': results['metadata']['total_requested'],
    'healthy': results['metadata']['successful'],
    'unhealthy': results['metadata']['failed'],
    'failures': list(results['errors'].keys())
}

print(f"Health Status: {report['healthy']}/{report['total']} services healthy")
```

### 3. Mixed Sync/Async Operations

Combine synchronous and asynchronous requests:

```python
client = HttpClient()

# Get config synchronously (blocking, must succeed)
try:
    config = client.get_sync("https://api.example.com/config")
except RuntimeError as e:
    print(f"Cannot proceed without config: {e}")
    sys.exit(1)

# Parse config
endpoints = parse_config(config)

# Fetch data from all endpoints asynchronously
for endpoint in endpoints:
    client.get_async(endpoint)

# Process results
results = client.get_results()
for event_id, data in results['data'].items():
    process_data(data)
```

### 4. Progressive Result Retrieval

Process results as they become available:

```python
client = HttpClient()

# Send requests
for i in range(100):
    client.get_async(f"https://api.example.com/item/{i}")

# Process results in batches
while client.get_pending_ids():
    # Get results without waiting for all
    results = client.get_results(join_before=False)

    # Process available results
    for event_id, data in results['data'].items():
        process_data(data)

    # Small delay before next check
    time.sleep(0.1)
```

---

## API Reference

### HttpClient

```python
class HttpClient:
    """Simple HTTP client with event-driven architecture."""

    def __init__(self) -> None:
        """Initialize HttpClient with EventBus."""

    def get_sync(self, url: str, **kwargs: Any) -> Any:
        """Send HTTP GET synchronously."""

    def get_async(self, url: str, **kwargs: Any) -> str:
        """Send HTTP GET asynchronously, return event_id."""

    def get_pending_ids(self) -> list[str]:
        """Get list of pending event IDs."""

    def set_pending_ids(self, event_ids: list[str]) -> None:
        """Set pending event IDs list."""

    def get_results(
        self,
        event_ids: list[str] | None = None,
        join_before: bool = True
    ) -> dict[str, Any]:
        """Get results from async requests."""
```

### HttpClientHandler

```python
class HttpClientHandler(basefunctions.EventHandler):
    """
    Simple HTTP request handler.

    Event data: {"url": "https://api.com", "method": "GET"}
    Returns: EventResult with HTTP response content or error
    """

    execution_mode = EXECUTION_MODE_THREAD

    def handle(
        self,
        event: Event,
        context: EventContext | None = None
    ) -> EventResult:
        """Make HTTP request from event data."""
```

### Registration Function

```python
def register_http_handlers() -> None:
    """Register HTTP handler with EventFactory."""
```

**Usage:**

```python
from basefunctions import register_http_handlers

# Register handlers (done automatically by initialize())
register_http_handlers()
```

---

## Notes

### Thread Safety

- `HttpClient` uses EventBus which is thread-safe
- Multiple `HttpClient` instances can coexist safely
- `get_pending_ids()` returns a copy (safe for concurrent access)

### Performance Considerations

- HTTP requests execute in thread pool (default pool size from EventBus)
- Network I/O is the bottleneck (threading is appropriate)
- For extreme parallelism (>1000s requests), consider process-based workers
- Default timeout: 30 seconds per request

### Limitations

- Only GET method currently exposed via `get_sync`/`get_async`
- For POST/PUT/DELETE, use EventBus directly with custom event_data
- No built-in retry logic (use EventBus retry features)
- No request/response interceptors (add at EventHandler level)

### Future Enhancements

Potential additions:
- `post_sync()`, `post_async()` methods
- Custom timeout per request
- Request headers and authentication
- Response caching
- Retry configuration
- Connection pooling

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| v1.3 | 2025-01-24 | Robust error handling with metadata structure |
| v1.2 | 2025-01-20 | Automatic event ID tracking, removed get() alias |
| v1.1 | 2025-01-15 | Added get_results for symmetric async/sync API |
| v1.0 | 2025-01-10 | Initial implementation |

---

## See Also

- [EventBus Usage Guide](../events/eventbus_usage_guide.md) - Event system documentation
- [IO Module Guide](../io/io_module_guide.md) - Serialization for API responses
- [Utils Module Guide](../utils/utils_module_guide.md) - Decorators and utilities
