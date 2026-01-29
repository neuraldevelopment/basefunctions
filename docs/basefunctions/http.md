# HTTP - User Documentation

**Package:** basefunctions
**Subpackage:** http
**Version:** 0.5.75
**Purpose:** Event-based HTTP client with async/sync request handling

---

## Overview

The http subpackage provides an event-driven HTTP client that integrates seamlessly with basefunctions' event system.

**Key Features:**
- Synchronous and asynchronous HTTP GET requests
- Automatic event ID tracking for async requests
- Built-in error handling with detailed metadata
- Integration with EventBus for scalable request handling

**Common Use Cases:**
- Fetching data from REST APIs
- Batch HTTP requests with async processing
- Event-driven HTTP workflows
- Automated request/response tracking

---

## Public APIs

### HttpClient

**Purpose:** Main HTTP client with async/sync request capabilities

```python
from basefunctions import HttpClient

client = HttpClient()
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| None | - | - | No initialization parameters required |

**Returns:**
- **Type:** HttpClient
- **Description:** Initialized HTTP client with internal EventBus

**Examples:**

```python
from basefunctions import HttpClient

# Create client instance
client = HttpClient()

# Synchronous request
response = client.get_sync("https://api.example.com/data")
print(response)

# Asynchronous request
event_id = client.get_async("https://api.example.com/data")
```

---

### HttpClient.get_sync()

**Purpose:** Send HTTP GET request and wait for response synchronously

```python
response = client.get_sync(url, **kwargs)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | str | - | Target URL for GET request |
| `**kwargs` | Any | - | Additional parameters passed to event |

**Returns:**
- **Type:** Any
- **Description:** HTTP response content

**Raises:**
- `RuntimeError`: If request failed or no response received

**Examples:**

```python
# Basic GET request
data = client.get_sync("https://api.example.com/users")

# With query parameters
data = client.get_sync(
    "https://api.example.com/users",
    params={"page": 1, "limit": 10}
)

# Error handling
try:
    data = client.get_sync("https://api.example.com/data")
except RuntimeError as e:
    print(f"Request failed: {e}")
```

**Best For:**
- Simple request-response workflows
- Sequential API calls
- Scripts requiring immediate results

---

### HttpClient.get_async()

**Purpose:** Send HTTP GET request asynchronously and return event ID for tracking

```python
event_id = client.get_async(url, **kwargs)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | str | - | Target URL for GET request |
| `**kwargs` | Any | - | Additional parameters passed to event |

**Returns:**
- **Type:** str
- **Description:** Event ID for tracking request

**Examples:**

```python
# Single async request
event_id = client.get_async("https://api.example.com/data")

# Multiple async requests
urls = [
    "https://api.example.com/users/1",
    "https://api.example.com/users/2",
    "https://api.example.com/users/3"
]

event_ids = []
for url in urls:
    event_id = client.get_async(url)
    event_ids.append(event_id)

# Retrieve results later
results = client.get_results()
```

**Best For:**
- Batch HTTP requests
- Non-blocking operations
- Parallel API calls
- Background data fetching

---

### HttpClient.get_results()

**Purpose:** Retrieve results from async requests with automatic tracking

```python
results = client.get_results(event_ids=None, join_before=True)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `event_ids` | list[str] or None | None | Specific event IDs to retrieve |
| `join_before` | bool | True | Wait for all events before retrieving |

**Returns:**
- **Type:** dict[str, Any]
- **Description:** Dictionary with data, metadata, and errors

**Result Structure:**
```python
{
    'data': {event_id: response_data, ...},
    'metadata': {
        'total_requested': int,
        'successful': int,
        'failed': int,
        'event_ids': {event_id: 'success'|'failed', ...},
        'timestamp': str
    },
    'errors': {event_id: error_message, ...}
}
```

**Examples:**

```python
# Get all pending results
results = client.get_results()
print(f"Successful: {results['metadata']['successful']}")
print(f"Failed: {results['metadata']['failed']}")

# Access successful responses
for event_id, data in results['data'].items():
    print(f"{event_id}: {data}")

# Handle errors
for event_id, error in results['errors'].items():
    print(f"Error for {event_id}: {error}")

# Get specific results
event_ids = ["abc123", "def456"]
results = client.get_results(event_ids=event_ids)

# Get results without waiting
results = client.get_results(join_before=False)
```

---

### HttpClient.get_pending_ids()

**Purpose:** Get list of pending event IDs

```python
pending_ids = client.get_pending_ids()
```

**Returns:**
- **Type:** list[str]
- **Description:** Copy of pending event IDs list

**Examples:**

```python
# Check pending requests
pending = client.get_pending_ids()
print(f"Pending requests: {len(pending)}")

# Store for later retrieval
my_ids = client.get_pending_ids()
```

---

### HttpClient.set_pending_ids()

**Purpose:** Set pending event IDs list manually

```python
client.set_pending_ids(event_ids)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `event_ids` | list[str] | - | New list of event IDs to track |

**Examples:**

```python
# Replace pending list
client.set_pending_ids(["id1", "id2", "id3"])

# Clear pending list
client.set_pending_ids([])
```

---

## Usage Examples

### Basic Synchronous Request

**Scenario:** Fetch data from API and process immediately

```python
from basefunctions import HttpClient

# Create client
client = HttpClient()

# Fetch data
data = client.get_sync("https://api.example.com/weather?city=Munich")
print(f"Temperature: {data['temp']}")
```

**Expected Output:**
```
Temperature: 18.5
```

---

### Batch Asynchronous Requests

**Scenario:** Fetch multiple API endpoints in parallel

```python
from basefunctions import HttpClient

# Create client
client = HttpClient()

# Define URLs
base_url = "https://api.example.com/users/"
user_ids = [1, 2, 3, 4, 5]

# Send async requests
for user_id in user_ids:
    client.get_async(f"{base_url}{user_id}")

# Wait and retrieve all results
results = client.get_results()

# Process successful responses
print(f"Fetched {results['metadata']['successful']} users")
for event_id, user_data in results['data'].items():
    print(f"- {user_data['name']}")

# Handle errors
if results['errors']:
    print(f"\nFailed requests: {len(results['errors'])}")
    for event_id, error in results['errors'].items():
        print(f"- {error}")
```

---

### Selective Result Retrieval

**Scenario:** Process results in batches

```python
from basefunctions import HttpClient

client = HttpClient()

# Send 100 async requests
event_ids = []
for i in range(100):
    event_id = client.get_async(f"https://api.example.com/data/{i}")
    event_ids.append(event_id)

# Process first 10 results
batch_1 = event_ids[:10]
results = client.get_results(event_ids=batch_1)
print(f"Batch 1: {results['metadata']['successful']} successful")

# Process next 10 results
batch_2 = event_ids[10:20]
results = client.get_results(event_ids=batch_2)
print(f"Batch 2: {results['metadata']['successful']} successful")

# Remaining requests still pending
pending = client.get_pending_ids()
print(f"Still pending: {len(pending)}")
```

---

### Error Handling Pattern

**Scenario:** Robust error handling with retry logic

```python
from basefunctions import HttpClient
import time

client = HttpClient()

def fetch_with_retry(url, max_retries=3):
    """Fetch URL with retry logic"""
    for attempt in range(max_retries):
        try:
            return client.get_sync(url)
        except RuntimeError as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                raise

# Use retry function
try:
    data = fetch_with_retry("https://api.example.com/data")
    print("Success:", data)
except RuntimeError:
    print("All retries failed")
```

---

## Choosing the Right Approach

### When to Use get_sync()

Use synchronous requests when:
- You need immediate results
- Request order matters
- Sequential processing is required
- Simple scripts or one-off requests

```python
# Sequential processing
user = client.get_sync("https://api.example.com/user/1")
orders = client.get_sync(f"https://api.example.com/user/{user['id']}/orders")
```

**Pros:**
- Simple to use
- Immediate results
- Easy error handling

**Cons:**
- Slower for multiple requests
- Blocks execution

---

### When to Use get_async()

Use asynchronous requests when:
- Fetching multiple endpoints
- Performance matters
- Non-blocking operation needed
- Background data collection

```python
# Parallel fetching
for url in urls:
    client.get_async(url)
results = client.get_results()
```

**Pros:**
- Much faster for multiple requests
- Non-blocking
- Scalable

**Cons:**
- Slightly more complex
- Need to manage event IDs

---

## Best Practices

### Best Practice 1: Reuse Client Instance

**Why:** Avoids creating multiple EventBus instances

```python
# GOOD
client = HttpClient()
for url in urls:
    client.get_async(url)
results = client.get_results()
```

```python
# AVOID
for url in urls:
    client = HttpClient()  # Creates new EventBus each time
    client.get_sync(url)
```

---

### Best Practice 2: Always Handle Errors

**Why:** Network requests can fail

```python
# GOOD
try:
    data = client.get_sync(url)
except RuntimeError as e:
    logger.error(f"Request failed: {e}")
    data = None
```

```python
# AVOID
data = client.get_sync(url)  # No error handling
```

---

### Best Practice 3: Check Results Metadata

**Why:** Know which requests succeeded/failed

```python
# GOOD
results = client.get_results()
if results['metadata']['failed'] > 0:
    logger.warning(f"Failed requests: {results['metadata']['failed']}")
for event_id, error in results['errors'].items():
    handle_error(event_id, error)
```

---

## Integration Examples

### Integration with ConfigHandler

```python
from basefunctions import HttpClient, ConfigHandler

# Load API configuration
config = ConfigHandler()
config.load_config_for_package("myapp")
api_url = config.get("api.base_url")

# Use configured URL
client = HttpClient()
data = client.get_sync(f"{api_url}/data")
```

---

### Integration with Event System

```python
from basefunctions import HttpClient, EventBus

# Use shared EventBus
bus = EventBus()
client = HttpClient()

# HttpClient has its own internal EventBus,
# but you can access results through client methods
event_id = client.get_async("https://api.example.com/data")
results = client.get_results([event_id])
```

---

## FAQ

**Q: Can I use POST, PUT, DELETE methods?**

A: Currently only GET is supported. For other methods, register custom event handlers with the EventBus.

**Q: How many concurrent requests can I make?**

A: Limited by the underlying EventBus thread pool. Default is suitable for most use cases.

**Q: Are results cached?**

A: No. Each request creates a new HTTP call. Use CacheManager if caching is needed.

**Q: Can I set timeouts or headers?**

A: Pass them via kwargs to get_sync() or get_async(). These are forwarded to the event handler.

---

## See Also

**Related Subpackages:**
- `events` (`docs/basefunctions/events.md`) - Event system documentation
- `utils` (`docs/basefunctions/utils.md`) - Utility functions including caching

**System Documentation:**
- `~/.claude/_docs/python/basefunctions.md` - Internal architecture details

---

## Quick Reference

### Imports

```python
# Main class
from basefunctions import HttpClient

# With handler registration
from basefunctions.http import (
    HttpClient,
    HttpClientHandler,
    register_http_handlers
)
```

### Quick Start

```python
# Step 1: Import
from basefunctions import HttpClient

# Step 2: Create client
client = HttpClient()

# Step 3: Sync request
data = client.get_sync("https://api.example.com/data")

# OR: Async request
event_id = client.get_async("https://api.example.com/data")
results = client.get_results()
```

### Cheat Sheet

| Task | Code |
|------|------|
| Create client | `HttpClient()` |
| Sync GET | `client.get_sync(url)` |
| Async GET | `client.get_async(url)` |
| Get results | `client.get_results()` |
| Check pending | `client.get_pending_ids()` |
| Error handling | `try/except RuntimeError` |

---

**Document Version:** 1.0.0
**Last Updated:** 2026-01-29
**Subpackage Version:** 0.5.75
