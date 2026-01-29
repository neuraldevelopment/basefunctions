# IO - User Documentation

**Package:** basefunctions
**Subpackage:** io
**Version:** 0.5.75
**Purpose:** File operations, output redirection, and serialization utilities

---

## Overview

The io subpackage provides comprehensive input/output utilities for file handling, output redirection, and data serialization.

**Key Features:**
- Cross-platform file and directory operations
- Output redirection to files, memory, or databases
- Multi-format serialization (JSON, Pickle, YAML, MessagePack)
- Automatic format detection from file extensions
- Thread-safe output handling

**Common Use Cases:**
- File and directory management
- Capturing program output
- Saving/loading data in multiple formats
- Cross-platform path handling
- Log redirection

---

## Public APIs

## File Functions

### check_if_exists()

**Purpose:** Check if file or directory exists

```python
from basefunctions.io import check_if_exists

exists = check_if_exists(file_name, file_type="FILE")
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `file_name` | str | - | Path to check |
| `file_type` | str | "FILE" | "FILE" or "DIRECTORY" |

**Returns:**
- **Type:** bool
- **Description:** True if exists, False otherwise

**Examples:**

```python
# Check file
if check_if_exists("/path/to/file.txt", "FILE"):
    print("File exists")

# Check directory
if check_if_exists("/path/to/dir", "DIRECTORY"):
    print("Directory exists")
```

---

### get_file_name()

**Purpose:** Extract filename from path

```python
from basefunctions.io import get_file_name

name = get_file_name("/path/to/file.txt")  # Returns: "file.txt"
```

---

### get_extension()

**Purpose:** Get file extension

```python
from basefunctions.io import get_extension

ext = get_extension("/path/to/file.txt")  # Returns: ".txt"
```

---

### create_directory()

**Purpose:** Create directory recursively

```python
from basefunctions.io import create_directory

create_directory("/path/to/new/directory")
```

---

### create_file_list()

**Purpose:** Get list of files matching pattern

```python
from basefunctions.io import create_file_list

files = create_file_list("/path/to/dir", "*.py")
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `directory` | str | - | Directory to search |
| `pattern` | str | "*" | Glob pattern for matching |

**Returns:**
- **Type:** list[str]
- **Description:** List of matching file paths

---

## Serialization

### serialize()

**Purpose:** Serialize data to string/bytes

```python
from basefunctions.io import serialize

data = {"key": "value"}
serialized = serialize(data, "json")
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `data` | Any | - | Data to serialize |
| `format_type` | str | - | "json", "pickle", "yaml", "msgpack" |

**Returns:**
- **Type:** str or bytes
- **Description:** Serialized data

**Raises:**
- `UnsupportedFormatError`: If format not supported
- `SerializationError`: If serialization fails

---

### deserialize()

**Purpose:** Deserialize data from string/bytes

```python
from basefunctions.io import deserialize

data = deserialize(serialized, "json")
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `data` | str or bytes | - | Serialized data |
| `format_type` | str | - | Format type |

**Returns:**
- **Type:** Any
- **Description:** Deserialized object

---

### to_file()

**Purpose:** Serialize and save to file with auto-format detection

```python
from basefunctions.io import to_file

data = {"users": [{"name": "Alice"}, {"name": "Bob"}]}
to_file(data, "/path/to/data.json")  # Format auto-detected
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `data` | Any | - | Data to save |
| `filepath` | str | - | Target file path |
| `format_type` | str or None | None | Explicit format (auto-detected if None) |
| `**kwargs` | Any | - | Serializer configuration |

**Supported Extensions:**
- `.json` - JSON format
- `.pkl`, `.pickle` - Pickle format
- `.yaml`, `.yml` - YAML format (requires PyYAML)
- `.mp`, `.msgpack` - MessagePack format (requires msgpack)
- `.gz` - Compressed files (e.g., `data.json.gz`)

**Examples:**

```python
# JSON (auto-detected)
to_file(data, "config.json")

# Pickle
to_file(data, "data.pkl")

# YAML
to_file(data, "settings.yaml")

# Compressed JSON
to_file(data, "data.json.gz", compression=True)

# Explicit format
to_file(data, "data.txt", format_type="json")
```

---

### from_file()

**Purpose:** Load and deserialize from file with auto-format detection

```python
from basefunctions.io import from_file

data = from_file("/path/to/data.json")
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `filepath` | str | - | Source file path |
| `format_type` | str or None | None | Explicit format (auto-detected if None) |
| `**kwargs` | Any | - | Serializer configuration |

**Returns:**
- **Type:** Any
- **Description:** Deserialized object

**Examples:**

```python
# Auto-detect format from extension
data = from_file("config.json")

# Explicit format
data = from_file("data.txt", format_type="json")

# Compressed file
data = from_file("data.json.gz")
```

---

### SerializerFactory

**Purpose:** Factory for creating custom serializers

```python
from basefunctions.io import SerializerFactory

factory = SerializerFactory()
serializer = factory.get_serializer("json")

# Configure serializer
serializer.configure(compression=True)

# Use serializer
serialized = serializer.serialize(data)
deserialized = serializer.deserialize(serialized)

# Save/load files
serializer.to_file(data, "output.json")
loaded = serializer.from_file("output.json")
```

**Methods:**
- `get_serializer(format_type)` - Get serializer instance
- `register_serializer(format, class)` - Register custom serializer
- `list_available_formats()` - List supported formats

---

## Output Redirection

### redirect_output()

**Purpose:** Context manager for output redirection

```python
from basefunctions.io import redirect_output

with redirect_output("output.log"):
    print("This goes to file")
    print("And this too")
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `target` | str or OutputTarget | - | File path or target object |
| `mode` | str | "w" | File mode ("w" or "a") |

**Examples:**

```python
# Redirect to file
with redirect_output("log.txt"):
    print("Logged message")

# Append mode
with redirect_output("log.txt", mode="a"):
    print("Appended message")
```

---

### OutputRedirector

**Purpose:** Manual output redirection control

```python
from basefunctions.io import OutputRedirector, FileTarget

# Create target
target = FileTarget("output.log")

# Create redirector
redirector = OutputRedirector(target)

# Start redirection
redirector.start()
print("This goes to file")

# Stop redirection
redirector.stop()
print("This goes to console")
```

**Targets:**
- `FileTarget(filepath, mode)` - Redirect to file
- `MemoryTarget()` - Redirect to memory buffer
- `DatabaseTarget(db, table)` - Redirect to database

---

### MemoryTarget

**Purpose:** Capture output in memory

```python
from basefunctions.io import MemoryTarget, OutputRedirector

# Create memory target
target = MemoryTarget()

# Redirect output
with OutputRedirector(target):
    print("Line 1")
    print("Line 2")

# Get captured output
output = target.get_output()
print(f"Captured: {output}")
```

---

## Usage Examples

### Basic File Operations

**Scenario:** Cross-platform file handling

```python
from basefunctions.io import (
    check_if_file_exists,
    create_directory,
    get_file_name,
    get_extension,
    create_file_list
)

# Check if file exists
if not check_if_file_exists("/data/config.json"):
    print("Config file not found")

# Create directory
create_directory("/data/output")

# List all Python files
py_files = create_file_list("/src", "*.py")
for file in py_files:
    name = get_file_name(file)
    ext = get_extension(file)
    print(f"{name} -> {ext}")
```

---

### Save and Load Data

**Scenario:** Persist application data in multiple formats

```python
from basefunctions.io import to_file, from_file

# Application data
config = {
    "database": {
        "host": "localhost",
        "port": 5432
    },
    "features": ["auth", "api", "admin"]
}

# Save as JSON
to_file(config, "config.json")

# Save as YAML
to_file(config, "config.yaml")

# Save as Pickle
to_file(config, "config.pkl")

# Load data
loaded_config = from_file("config.json")
print(f"Database host: {loaded_config['database']['host']}")
```

---

### Compressed Data Storage

**Scenario:** Save large datasets with compression

```python
from basefunctions.io import to_file, from_file

# Large dataset
data = {
    "records": [{"id": i, "value": i * 100} for i in range(10000)]
}

# Save with compression
to_file(data, "data.json.gz", compression=True)

# Load compressed data
loaded = from_file("data.json.gz")
print(f"Records: {len(loaded['records'])}")
```

---

### Capture Program Output

**Scenario:** Capture and analyze program output

```python
from basefunctions.io import MemoryTarget, OutputRedirector

def run_analysis():
    """Function that prints analysis results"""
    print("Starting analysis...")
    print("Result: 42")
    print("Analysis complete")

# Capture output
target = MemoryTarget()
redirector = OutputRedirector(target)

redirector.start()
run_analysis()
redirector.stop()

# Analyze output
output = target.get_output()
lines = output.strip().split('\n')
print(f"Generated {len(lines)} lines of output")

if "Result: 42" in output:
    print("Analysis successful")
```

---

### Log to File

**Scenario:** Redirect output to log file

```python
from basefunctions.io import redirect_output
from datetime import datetime

def process_data(items):
    """Process items with logging"""
    for i, item in enumerate(items):
        print(f"[{datetime.now()}] Processing item {i}: {item}")

# Redirect to log file
with redirect_output("processing.log"):
    items = ["apple", "banana", "cherry"]
    process_data(items)

print("Processing complete (this goes to console)")
```

---

### Custom Serializer

**Scenario:** Create custom serialization format

```python
from basefunctions.io import Serializer, SerializerFactory

class CSVSerializer(Serializer):
    """Custom CSV serializer"""

    def serialize(self, data):
        """Convert list of dicts to CSV"""
        if not data:
            return ""

        # Get headers from first item
        headers = list(data[0].keys())
        lines = [",".join(headers)]

        # Add rows
        for row in data:
            values = [str(row.get(h, "")) for h in headers]
            lines.append(",".join(values))

        return "\n".join(lines)

    def deserialize(self, data):
        """Convert CSV to list of dicts"""
        lines = data.strip().split("\n")
        if not lines:
            return []

        headers = lines[0].split(",")
        result = []

        for line in lines[1:]:
            values = line.split(",")
            row = dict(zip(headers, values))
            result.append(row)

        return result

# Register custom serializer
factory = SerializerFactory()
factory.register_serializer("csv", CSVSerializer)

# Use custom serializer
data = [
    {"name": "Alice", "age": "30"},
    {"name": "Bob", "age": "25"}
]

serializer = factory.get_serializer("csv")
csv_data = serializer.serialize(data)
print(csv_data)
```

---

## Choosing the Right Approach

### When to Use JSON

Use JSON when:
- Human-readable format needed
- Web API integration
- Configuration files
- Cross-language compatibility required

```python
to_file(config, "config.json")
```

**Pros:**
- Human-readable
- Widely supported
- Small file size

**Cons:**
- Limited type support
- Slower than binary formats

---

### When to Use Pickle

Use Pickle when:
- Python-only application
- Complex Python objects
- Performance matters
- Binary format acceptable

```python
to_file(complex_object, "data.pkl")
```

**Pros:**
- Supports complex Python objects
- Fast serialization
- Preserves object types

**Cons:**
- Python-only
- Security risks (don't unpickle untrusted data)
- Not human-readable

---

### When to Use YAML

Use YAML when:
- Configuration files
- Human-readable format with comments
- Hierarchical data

```python
to_file(config, "config.yaml")
```

**Pros:**
- Very human-readable
- Supports comments
- Clean syntax

**Cons:**
- Slower than JSON
- Requires PyYAML dependency

---

### When to Use MessagePack

Use MessagePack when:
- High performance needed
- Network transmission
- Binary format acceptable

```python
to_file(data, "data.mp")
```

**Pros:**
- Very fast
- Compact binary format
- Cross-language support

**Cons:**
- Not human-readable
- Requires msgpack dependency

---

## Best Practices

### Best Practice 1: Use Pathlib-Compatible Functions

**Why:** Cross-platform compatibility

```python
# GOOD
from pathlib import Path
from basefunctions.io import check_if_file_exists

file_path = Path("/data") / "config.json"
if check_if_file_exists(str(file_path)):
    pass
```

---

### Best Practice 2: Always Use Context Managers

**Why:** Ensures proper cleanup

```python
# GOOD
with redirect_output("log.txt"):
    process_data()

# AVOID
redirector = OutputRedirector(FileTarget("log.txt"))
redirector.start()
process_data()
redirector.stop()  # Might not run if error occurs
```

---

### Best Practice 3: Handle Serialization Errors

**Why:** File operations can fail

```python
# GOOD
from basefunctions.io import to_file, SerializationError

try:
    to_file(data, "output.json")
except SerializationError as e:
    logger.error(f"Failed to save: {e}")
```

---

## Performance Tips

**Tip 1:** Use Pickle for large Python objects
```python
# FAST - Pickle
to_file(large_object, "data.pkl")

# SLOW - JSON
to_file(large_object, "data.json")
```

**Tip 2:** Enable compression for large files
```python
# FAST - Compressed
to_file(data, "data.json.gz", compression=True)

# SLOW - Uncompressed large file
to_file(data, "data.json")
```

**Tip 3:** Use MessagePack for network data
```python
# FAST
data = serialize(obj, "msgpack")
send_over_network(data)

# SLOW
data = serialize(obj, "json")
send_over_network(data)
```

---

## FAQ

**Q: Which file functions are cross-platform?**

A: All functions in filefunctions module use pathlib internally for cross-platform support.

**Q: Can I serialize custom classes?**

A: Yes with Pickle. JSON/YAML require custom serialization logic. See Custom Serializer example.

**Q: Is output redirection thread-safe?**

A: Yes, use `ThreadSafeOutputRedirector` for multi-threaded applications.

**Q: How do I list available serialization formats?**

A: `SerializerFactory().list_available_formats()`

---

## See Also

**Related Subpackages:**
- `utils` (`docs/basefunctions/utils.md`) - Utility functions including logging
- `config` (`docs/basefunctions/config.md`) - Configuration management

**System Documentation:**
- `~/.claude/_docs/python/basefunctions.md` - Internal architecture details

---

## Quick Reference

### Imports

```python
# File functions
from basefunctions.io import (
    check_if_file_exists,
    create_directory,
    get_file_name,
    create_file_list
)

# Serialization
from basefunctions.io import (
    to_file,
    from_file,
    serialize,
    deserialize
)

# Output redirection
from basefunctions.io import (
    redirect_output,
    OutputRedirector,
    MemoryTarget
)
```

### Quick Start

```python
# Save data
from basefunctions.io import to_file
to_file({"key": "value"}, "data.json")

# Load data
from basefunctions.io import from_file
data = from_file("data.json")

# Redirect output
from basefunctions.io import redirect_output
with redirect_output("log.txt"):
    print("Logged")
```

### Cheat Sheet

| Task | Code |
|------|------|
| Check file exists | `check_if_file_exists(path)` |
| Create directory | `create_directory(path)` |
| List files | `create_file_list(dir, "*.py")` |
| Save JSON | `to_file(data, "file.json")` |
| Load JSON | `from_file("file.json")` |
| Redirect output | `with redirect_output("log.txt"):` |
| Capture output | `MemoryTarget()` |

---

**Document Version:** 1.0.0
**Last Updated:** 2026-01-29
**Subpackage Version:** 0.5.75
