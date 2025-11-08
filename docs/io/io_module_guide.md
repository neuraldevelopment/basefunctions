# IO Module Guide

**basefunctions I/O Utilities and Serialization Framework**

Version: 1.2
Last Updated: 2025-11-08

---

## Table of Contents

1. [Overview](#overview)
2. [Module Architecture](#module-architecture)
3. [File Functions](#file-functions)
4. [Serialization Framework](#serialization-framework)
5. [Output Redirection](#output-redirection)
6. [Use Cases & Examples](#use-cases--examples)
7. [Best Practices](#best-practices)
8. [API Reference](#api-reference)

---

## Overview

The `basefunctions.io` module provides a comprehensive suite of I/O utilities for Python applications, including:

- **File Operations**: Cross-platform file and directory manipulation
- **Path Utilities**: Path parsing, validation, and transformation
- **Serialization**: Unified interface for JSON, YAML, Pickle, and MessagePack formats
- **Output Redirection**: Flexible stdout/stderr capture and redirection to files, databases, or memory

### Key Features

- Cross-platform file operations with consistent API
- Auto-detection of serialization formats from file extensions
- Optional gzip compression for all serialization formats
- Thread-safe output redirection
- Context manager support for clean resource management
- Extensible serializer architecture
- Comprehensive error handling

### Installation

The IO module is part of basefunctions and requires Python 3.12+:

```bash
pip install basefunctions
```

Optional dependencies for full serialization support:

```bash
pip install basefunctions[yaml]      # YAML support
pip install basefunctions[msgpack]   # MessagePack support
```

---

## Module Architecture

```
basefunctions/io/
├── filefunctions.py       # File and directory operations
├── serializer.py          # Unified serialization framework
└── output_redirector.py   # stdout/stderr redirection
```

### Component Overview

| Component | Purpose | Key Classes/Functions |
|-----------|---------|----------------------|
| **filefunctions** | File/directory operations | `check_if_exists()`, `create_file_list()`, path utilities |
| **serializer** | Data serialization | `SerializerFactory`, `serialize()`, `to_file()` |
| **output_redirector** | Output capture | `OutputRedirector`, `FileTarget`, `MemoryTarget` |

### Import Patterns

```python
# Import all I/O utilities from main package
from basefunctions import (
    # File operations
    check_if_file_exists, create_directory, remove_file,
    get_file_name, get_path_name, create_file_list,

    # Serialization
    serialize, deserialize, to_file, from_file,
    SerializerFactory,

    # Output redirection
    OutputRedirector, FileTarget, MemoryTarget,
    redirect_output
)
```

---

## File Functions

The `filefunctions` module provides cross-platform file and directory operations.

### File Existence Checks

```python
from basefunctions import check_if_file_exists, check_if_dir_exists

# Check if file exists
if check_if_file_exists("/path/to/file.txt"):
    print("File exists")

# Check if directory exists
if check_if_dir_exists("/path/to/directory"):
    print("Directory exists")

# Generic check with type specification
from basefunctions.io.filefunctions import check_if_exists
check_if_exists("/path/to/item", file_type="FILE")      # File check
check_if_exists("/path/to/item", file_type="DIRECTORY")  # Directory check
```

### Path Parsing and Manipulation

```python
from basefunctions import (
    get_file_name, get_path_name, get_file_extension,
    get_base_name_prefix, get_path_without_extension
)

filepath = "/home/user/documents/report_2024.pdf"

# Extract components
filename = get_file_name(filepath)              # "report_2024.pdf"
path = get_path_name(filepath)                  # "/home/user/documents/"
extension = get_file_extension(filepath)        # ".pdf"
basename = get_base_name_prefix(filepath)       # "report_2024"
path_no_ext = get_path_without_extension(filepath)  # "/home/user/documents/report_2024"

# Parent paths
from basefunctions.io.filefunctions import get_parent_path_name
parent = get_parent_path_name(filepath)         # "/home/user/"

# Home directory
from basefunctions.io.filefunctions import get_home_path
home = get_home_path()                          # "/home/user" (platform-dependent)
```

### Directory Operations

```python
from basefunctions import create_directory, remove_directory
from basefunctions.io.filefunctions import (
    get_current_directory, set_current_directory
)

# Create directory (recursive)
create_directory("/path/to/new/nested/directory")

# Get/set current working directory
cwd = get_current_directory()
set_current_directory("/path/to/workdir")

# Remove directory and all contents (use with caution!)
remove_directory("/path/to/old/directory")
```

### File Operations

```python
from basefunctions import remove_file
from basefunctions.io.filefunctions import rename_file

# Remove file
remove_file("/path/to/file.txt")

# Rename/move file
rename_file(
    src="/path/to/old_name.txt",
    target="/path/to/new_name.txt",
    overwrite=False  # Raise error if target exists
)

# Overwrite existing file
rename_file(
    src="/path/to/source.txt",
    target="/path/to/existing.txt",
    overwrite=True
)
```

### File Listing and Pattern Matching

```python
from basefunctions.io.filefunctions import create_file_list

# List all files in directory
files = create_file_list(dir_name="/path/to/directory")

# Pattern matching (glob-style)
python_files = create_file_list(
    pattern_list=["*.py"],
    dir_name="/path/to/project"
)

# Multiple patterns
source_files = create_file_list(
    pattern_list=["*.py", "*.yaml", "*.json"],
    dir_name="/path/to/config"
)

# Recursive search
all_python = create_file_list(
    pattern_list=["*.py"],
    dir_name="/path/to/project",
    recursive=True
)

# Include directories
items = create_file_list(
    pattern_list=["*"],
    dir_name="/path/to/data",
    append_dirs=True  # Include directories in result
)

# Include hidden files
all_files = create_file_list(
    pattern_list=["*"],
    dir_name="/path/to/directory",
    add_hidden_files=True,  # Include .hidden files
    reverse_sort=True       # Sort in reverse order
)
```

### Path Normalization

```python
from basefunctions.io.filefunctions import norm_path

# Normalize paths (handles backslashes, relative paths)
normalized = norm_path("path\\to\\file.txt")  # "path/to/file.txt"
normalized = norm_path("./path/../other/file.txt")  # "other/file.txt"
```

---

## Serialization Framework

The serialization framework provides a unified interface for multiple data formats with automatic format detection.

### Supported Formats

| Format | Extension | Binary | Requires Package | Compression Support |
|--------|-----------|--------|-----------------|---------------------|
| JSON | `.json` | No | Built-in | Yes (gzip) |
| Pickle | `.pkl`, `.pickle` | Yes | Built-in | Yes (gzip) |
| YAML | `.yaml`, `.yml` | No | PyYAML | Yes (gzip) |
| MessagePack | `.msgpack`, `.mp` | Yes | msgpack | Yes (gzip) |

### Quick Start: Convenience Functions

```python
from basefunctions import to_file, from_file

# Automatic format detection from file extension
data = {"name": "Alice", "age": 30, "tags": ["python", "data"]}

# Save as JSON
to_file(data, "/path/to/data.json")

# Save as YAML
to_file(data, "/path/to/data.yaml")

# Save as Pickle
to_file(data, "/path/to/data.pkl")

# Save as MessagePack
to_file(data, "/path/to/data.msgpack")

# Load from file (auto-detects format)
loaded = from_file("/path/to/data.json")
```

### Compression Support

```python
from basefunctions import to_file, from_file

data = {"large": "dataset" * 10000}

# Enable gzip compression
to_file(data, "/path/to/data.json.gz", compression=True)

# Load compressed file (auto-detects compression)
loaded = from_file("/path/to/data.json.gz")

# Compression works with all formats
to_file(data, "/path/to/data.yaml.gz", compression=True)
to_file(data, "/path/to/data.pkl.gz", compression=True)
```

### Explicit Format Specification

```python
from basefunctions import to_file, from_file

# Override auto-detection
to_file(data, "/path/to/file.dat", format_type="json")
loaded = from_file("/path/to/file.dat", format_type="yaml")
```

### In-Memory Serialization

```python
from basefunctions import serialize, deserialize

data = {"key": "value", "numbers": [1, 2, 3]}

# Serialize to string/bytes
json_str = serialize(data, "json")      # Returns JSON string
pickle_bytes = serialize(data, "pickle")  # Returns bytes
yaml_str = serialize(data, "yaml")      # Returns YAML string

# Deserialize from string/bytes
restored = deserialize(json_str, "json")
restored = deserialize(pickle_bytes, "pickle")
```

### Using SerializerFactory

```python
from basefunctions import SerializerFactory

factory = SerializerFactory()  # Singleton instance

# List available formats
formats = factory.list_available_formats()
print(formats)  # ['json', 'msgpack', 'mp', 'pickle', 'yaml', 'yml']

# Get serializer for specific format
json_serializer = factory.get_serializer("json")

# Configure serializer
json_serializer.configure(compression=True, encoding="utf-8")

# Use serializer
serialized = json_serializer.serialize(data)
deserialized = json_serializer.deserialize(serialized)

# File operations with serializer
json_serializer.to_file(data, "/path/to/output.json")
loaded = json_serializer.from_file("/path/to/output.json")
```

### Custom Serializers

```python
from basefunctions import SerializerFactory
from basefunctions.io.serializer import Serializer
from typing import Any, Union

class CustomSerializer(Serializer):
    """Custom XML serializer example."""

    def serialize(self, data: Any) -> str:
        # Custom serialization logic
        return f"<data>{data}</data>"

    def deserialize(self, data: Union[str, bytes]) -> Any:
        # Custom deserialization logic
        if isinstance(data, bytes):
            data = data.decode(self.encoding)
        # Parse XML and return object
        return data.replace("<data>", "").replace("</data>", "")

# Register custom serializer
factory = SerializerFactory()
factory.register_serializer("xml", CustomSerializer)

# Use custom serializer
from basefunctions import serialize, deserialize
xml_data = serialize({"test": "data"}, "xml")
restored = deserialize(xml_data, "xml")
```

### Error Handling

```python
from basefunctions import to_file, from_file
from basefunctions.io.serializer import (
    SerializationError,
    UnsupportedFormatError
)

try:
    to_file(data, "/path/to/file.unknown")
except UnsupportedFormatError as e:
    print(f"Format not supported: {e}")

try:
    to_file(data, "/invalid/path/file.json")
except SerializationError as e:
    print(f"Serialization failed: {e}")

try:
    loaded = from_file("/nonexistent/file.json")
except FileNotFoundError as e:
    print(f"File not found: {e}")
except SerializationError as e:
    print(f"Deserialization failed: {e}")
```

---

## Output Redirection

The output redirection system provides flexible capture and routing of stdout/stderr streams.

### Basic Output Redirection

```python
from basefunctions import OutputRedirector, MemoryTarget

# Capture stdout to memory
target = MemoryTarget()
redirector = OutputRedirector(target, redirect_stdout=True)

redirector.start()
print("This goes to memory buffer")
print("So does this")
redirector.stop()

# Retrieve captured output
output = target.get_buffer()
print(f"Captured: {output}")
```

### File Output Target

```python
from basefunctions import OutputRedirector, FileTarget

# Redirect to file
file_target = FileTarget(
    filename="/path/to/output.log",
    mode="a",      # "a" for append, "w" for overwrite
    encoding="utf-8"
)

redirector = OutputRedirector(file_target, redirect_stdout=True)

with redirector:  # Context manager handles start/stop
    print("This line goes to file")
    print("This line too")
```

### Context Manager Usage

```python
from basefunctions import OutputRedirector, FileTarget

# Cleaner syntax with context manager
with OutputRedirector(FileTarget("/path/to/log.txt")):
    print("Automatically redirected")
    print("Automatically restored on exit")

# Original stdout restored here
print("This goes to console")
```

### Redirect Both stdout and stderr

```python
from basefunctions import OutputRedirector, FileTarget

target = FileTarget("/path/to/combined.log")

with OutputRedirector(
    target,
    redirect_stdout=True,
    redirect_stderr=True
):
    print("Normal output")
    import sys
    print("Error output", file=sys.stderr)
    # Both go to same file
```

### Database Output Target

```python
from basefunctions import OutputRedirector, DatabaseTarget
# Note: Requires basefunctions.db module

# Example structure (requires DbManager setup)
from basefunctions import DbManager

db_manager = DbManager()
# ... configure database instance ...

db_target = DatabaseTarget(
    db_manager=db_manager,
    instance_name="my_db_instance",
    db_name="logs",
    table="output_log",
    fields={
        "timestamp": "TIMESTAMP",
        "message": "TEXT"
    }
)

with OutputRedirector(db_target):
    print("This message goes to database")
    print("With automatic timestamp")
```

### Decorator-based Redirection

```python
from basefunctions import redirect_output

# Redirect function output to file
@redirect_output("/path/to/function_output.log")
def my_function():
    print("Function output goes to file")
    return 42

result = my_function()  # Output redirected automatically

# Redirect to custom target
from basefunctions import MemoryTarget

target = MemoryTarget()

@redirect_output(target=target, stdout=True, stderr=False)
def another_function():
    print("Captured in memory")
    return "result"

result = another_function()
output = target.get_buffer()
```

### Thread-Safe Redirection

```python
from basefunctions.io.output_redirector import ThreadSafeOutputRedirector, MemoryTarget
import threading

# Create thread-safe redirector with target factory
def target_factory():
    return MemoryTarget()

redirector = ThreadSafeOutputRedirector(
    target_factory,
    redirect_stdout=True
)

def worker(name):
    redirector.start()
    print(f"Worker {name} output")
    redirector.stop()

# Each thread gets its own target
threads = [
    threading.Thread(target=worker, args=(i,))
    for i in range(5)
]

for t in threads:
    t.start()
for t in threads:
    t.join()
```

### Custom Output Targets

```python
from basefunctions.io.output_redirector import OutputTarget, OutputRedirector

class WebhookTarget(OutputTarget):
    """Send output to webhook."""

    def __init__(self, webhook_url):
        self.webhook_url = webhook_url
        self.buffer = []

    def write(self, text: str) -> None:
        self.buffer.append(text)

    def flush(self) -> None:
        if self.buffer:
            # Send to webhook
            import requests
            requests.post(
                self.webhook_url,
                json={"message": "".join(self.buffer)}
            )
            self.buffer.clear()

    def close(self) -> None:
        self.flush()

# Use custom target
webhook_target = WebhookTarget("https://example.com/webhook")

with OutputRedirector(webhook_target):
    print("This goes to webhook")
```

---

## Use Cases & Examples

### Use Case 1: Configuration File Management

```python
from basefunctions import to_file, from_file, check_if_file_exists

# Save application config
config = {
    "database": {
        "host": "localhost",
        "port": 5432
    },
    "features": {
        "enable_cache": True,
        "max_connections": 100
    }
}

# Save as YAML for readability
to_file(config, "/etc/myapp/config.yaml")

# Load config
if check_if_file_exists("/etc/myapp/config.yaml"):
    config = from_file("/etc/myapp/config.yaml")
else:
    # Use defaults
    config = default_config
```

### Use Case 2: Data Pipeline Serialization

```python
from basefunctions import to_file, from_file
import pandas as pd

# Process data and cache intermediate results
data = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})

# Cache as Pickle for fast serialization
to_file(data.to_dict(), "/tmp/cache/step1.pkl")

# Later: restore from cache
cached_data = from_file("/tmp/cache/step1.pkl")
df = pd.DataFrame(cached_data)

# Export final results as JSON
results = {"summary": df.describe().to_dict()}
to_file(results, "/output/results.json")
```

### Use Case 3: Compressed Log Archival

```python
from basefunctions import to_file, create_file_list
from basefunctions.io.filefunctions import get_file_name
from datetime import datetime

# Collect log data
logs = []
log_files = create_file_list(
    pattern_list=["*.log"],
    dir_name="/var/log/myapp"
)

for logfile in log_files:
    with open(logfile) as f:
        logs.append({
            "file": get_file_name(logfile),
            "content": f.read()
        })

# Archive as compressed JSON
archive_name = f"/archive/logs_{datetime.now():%Y%m%d}.json.gz"
to_file(logs, archive_name, compression=True)
```

### Use Case 4: Test Output Capture

```python
from basefunctions import OutputRedirector, MemoryTarget

def test_function_output():
    """Test that function prints expected output."""

    target = MemoryTarget()

    with OutputRedirector(target):
        # Function under test
        print("Expected output")
        print("Line 2")

    output = target.get_buffer()

    assert "Expected output" in output
    assert "Line 2" in output
```

### Use Case 5: Batch File Processing

```python
from basefunctions import (
    create_file_list, create_directory,
    get_base_name_prefix, get_path_name
)

# Find all text files
text_files = create_file_list(
    pattern_list=["*.txt"],
    dir_name="/input",
    recursive=True
)

# Process each file
output_dir = "/output/processed"
create_directory(output_dir)

for filepath in text_files:
    basename = get_base_name_prefix(filepath)

    with open(filepath) as f:
        content = f.read()

    # Process content
    processed = content.upper()

    # Save with new extension
    output_path = f"{output_dir}/{basename}_processed.txt"
    with open(output_path, "w") as f:
        f.write(processed)
```

### Use Case 6: Multi-format Export

```python
from basefunctions import to_file

data = {
    "report": "Q4 2024",
    "metrics": {
        "revenue": 1000000,
        "users": 50000
    }
}

# Export in multiple formats for different consumers
base_path = "/exports/q4_2024"

# JSON for web API
to_file(data, f"{base_path}.json")

# YAML for configuration
to_file(data, f"{base_path}.yaml")

# Pickle for Python processing
to_file(data, f"{base_path}.pkl")

# Compressed MessagePack for efficient storage
to_file(data, f"{base_path}.msgpack.gz", compression=True)
```

---

## Best Practices

### File Operations

**1. Always Check for Existence Before Operations**

```python
from basefunctions import check_if_file_exists, remove_file

# GOOD: Check before removing
if check_if_file_exists("/path/to/file.txt"):
    remove_file("/path/to/file.txt")

# BAD: Direct removal may raise errors
remove_file("/path/to/file.txt")  # FileNotFoundError if missing
```

**2. Use Absolute Paths for Clarity**

```python
import os
from basefunctions import create_directory

# GOOD: Explicit absolute path
abs_path = os.path.abspath("/data/output")
create_directory(abs_path)

# ACCEPTABLE: Relative paths when context is clear
create_directory("./temp")
```

**3. Handle Cross-Platform Paths**

```python
from basefunctions.io.filefunctions import norm_path
import os

# GOOD: Use os.path.join for cross-platform compatibility
filepath = os.path.join("data", "output", "file.txt")

# GOOD: Normalize paths from external sources
user_path = norm_path(r"data\output\file.txt")  # Works on all platforms
```

**4. Protect Against Accidental Deletions**

```python
from basefunctions import remove_directory
import os

# GOOD: Verify path before deletion
target_dir = "/tmp/myapp/cache"
if os.path.abspath(target_dir) != os.path.sep:  # Not root
    if "myapp" in target_dir:  # Safety check
        remove_directory(target_dir)

# BAD: Direct deletion without checks
remove_directory(user_input)  # Dangerous!
```

### Serialization

**5. Choose Appropriate Format for Use Case**

```python
# JSON: Human-readable, web APIs, configuration
to_file(config, "config.json")

# YAML: Configuration files, human-friendly
to_file(config, "config.yaml")

# Pickle: Python-only, complex objects, fast
to_file(ml_model, "model.pkl")

# MessagePack: Compact binary, cross-language
to_file(large_dataset, "data.msgpack")
```

**6. Use Compression for Large Data**

```python
from basefunctions import to_file

large_data = {"records": [{"id": i} for i in range(100000)]}

# Enable compression for large datasets
to_file(large_data, "data.json.gz", compression=True)

# Typical compression ratios:
# JSON: 5-10x smaller
# YAML: 5-8x smaller
# Pickle: 3-5x smaller
```

**7. Handle Serialization Errors Gracefully**

```python
from basefunctions import to_file, from_file
from basefunctions.io.serializer import SerializationError

def save_safely(data, filepath):
    """Save with error handling and rollback."""
    backup_path = f"{filepath}.backup"

    try:
        # Create backup if file exists
        if check_if_file_exists(filepath):
            import shutil
            shutil.copy(filepath, backup_path)

        # Save new data
        to_file(data, filepath)

        # Remove backup on success
        if check_if_file_exists(backup_path):
            remove_file(backup_path)

    except SerializationError as e:
        # Restore backup on failure
        if check_if_file_exists(backup_path):
            import shutil
            shutil.copy(backup_path, filepath)
        raise
```

**8. Avoid Pickle for Untrusted Data**

```python
# GOOD: Use JSON/YAML for external data
user_data = from_file("user_upload.json")

# BAD: Pickle can execute arbitrary code during deserialization
untrusted_data = from_file("untrusted.pkl")  # SECURITY RISK!

# Use Pickle only for:
# - Internal application data
# - Trusted sources
# - Python-specific objects (classes, functions)
```

### Output Redirection

**9. Always Use Context Managers**

```python
from basefunctions import OutputRedirector, FileTarget

# GOOD: Automatic cleanup with context manager
with OutputRedirector(FileTarget("output.log")):
    print("Logged safely")
# Stream automatically restored here

# BAD: Manual start/stop (error-prone)
redirector = OutputRedirector(FileTarget("output.log"))
redirector.start()
print("Logged")
redirector.stop()  # May not execute if exception occurs
```

**10. Flush Regularly for Real-time Logging**

```python
from basefunctions import OutputRedirector, FileTarget

target = FileTarget("app.log")
redirector = OutputRedirector(target)

redirector.start()
print("Important message")
redirector.flush()  # Ensure written immediately

# For time-sensitive operations
for i in range(100):
    print(f"Processing item {i}")
    if i % 10 == 0:
        redirector.flush()  # Periodic flush
```

**11. Use Appropriate Targets for Use Case**

```python
# MEMORY: Fast, for testing, small outputs
target = MemoryTarget()

# FILE: Persistent storage, logs, auditing
target = FileTarget("/var/log/app.log", mode="a")

# DATABASE: Structured storage, querying, analysis
target = DatabaseTarget(db_manager, "instance", "db", "logs")
```

### Performance

**12. Use MessagePack for Speed**

```python
import time
from basefunctions import to_file, from_file

large_data = {"items": [i for i in range(100000)]}

# MessagePack: Fastest serialization
start = time.time()
to_file(large_data, "data.msgpack")
msgpack_time = time.time() - start

# JSON: Slower but human-readable
start = time.time()
to_file(large_data, "data.json")
json_time = time.time() - start

# Typical speedup: 3-5x faster with MessagePack
```

**13. Batch File Operations**

```python
from basefunctions import create_file_list

# GOOD: Single traversal with pattern matching
files = create_file_list(
    pattern_list=["*.txt", "*.log", "*.md"],
    dir_name="/data",
    recursive=True
)

# BAD: Multiple traversals
txt_files = create_file_list(["*.txt"], "/data", recursive=True)
log_files = create_file_list(["*.log"], "/data", recursive=True)
md_files = create_file_list(["*.md"], "/data", recursive=True)
```

### Error Handling

**14. Provide Meaningful Error Messages**

```python
from basefunctions import remove_file, check_if_file_exists

def delete_user_file(filepath):
    """Delete file with comprehensive error handling."""

    if not filepath:
        raise ValueError("filepath cannot be empty")

    if not check_if_file_exists(filepath):
        raise FileNotFoundError(
            f"Cannot delete '{filepath}': file does not exist"
        )

    if not filepath.startswith("/tmp/myapp/"):
        raise PermissionError(
            f"Cannot delete '{filepath}': not in allowed directory"
        )

    try:
        remove_file(filepath)
    except Exception as e:
        raise RuntimeError(
            f"Failed to delete '{filepath}': {e}"
        ) from e
```

**15. Use Specific Exception Types**

```python
from basefunctions import to_file
from basefunctions.io.serializer import (
    SerializationError,
    UnsupportedFormatError
)

try:
    to_file(data, "output.xyz")

except UnsupportedFormatError:
    # Handle unknown format specifically
    print("Format not supported, using JSON fallback")
    to_file(data, "output.json")

except FileNotFoundError:
    # Handle missing directory
    create_directory(get_path_name("output.xyz"))
    to_file(data, "output.xyz")

except SerializationError as e:
    # Handle other serialization errors
    logging.error(f"Serialization failed: {e}")
    raise
```

---

## API Reference

### File Functions (filefunctions.py)

#### Existence Checks

##### `check_if_exists(file_name: str, file_type: str = "FILE") -> bool`

Check if a specific file or directory exists.

**Parameters:**
- `file_name` (str): Name of the file or directory to be checked
- `file_type` (str): Type to check - "FILE" or "DIRECTORY" (default: "FILE")

**Returns:** `bool` - True if exists, False otherwise

**Raises:** `ValueError` - If unknown file_type is passed

---

##### `check_if_file_exists(file_name: str) -> bool`

Check if a file exists.

**Parameters:**
- `file_name` (str): The name of the file to be checked

**Returns:** `bool` - True if the file exists, False otherwise

---

##### `check_if_dir_exists(dir_name: str) -> bool`

Check if directory exists.

**Parameters:**
- `dir_name` (str): Directory name to be checked

**Returns:** `bool` - True if directory exists, False otherwise

---

##### `is_file(file_name: str) -> bool`

Check if file_name is a regular file. Alias for `check_if_file_exists()`.

---

##### `is_directory(dir_name: str) -> bool`

Check if dir_name is a regular directory. Alias for `check_if_dir_exists()`.

---

#### Path Parsing

##### `get_file_name(path_file_name: str) -> str`

Get the file name part from a complete file path.

**Parameters:**
- `path_file_name` (str): The complete file path

**Returns:** `str` - The file name (basename) of the path

**Example:**
```python
get_file_name("/home/user/document.txt")  # "document.txt"
```

---

##### `get_file_extension(path_file_name: str) -> str`

Get the file extension from a complete file name.

**Parameters:**
- `path_file_name` (str): The path file name

**Returns:** `str` - The file extension including the dot (e.g., ".txt")

**Example:**
```python
get_file_extension("/path/to/file.txt")  # ".txt"
```

---

##### `get_extension(path_file_name: str) -> str`

Alias for `get_file_extension()`.

---

##### `get_base_name(path_file_name: str) -> str`

Get the base name from a complete file name. Alias for `get_file_name()`.

---

##### `get_base_name_prefix(path_file_name: str) -> str`

Get the basename without extension.

**Parameters:**
- `path_file_name` (str): The path file name

**Returns:** `str` - The basename without extension

**Example:**
```python
get_base_name_prefix("/path/to/file.tar.gz")  # "file.tar"
```

---

##### `get_path_name(path_file_name: str) -> str`

Get the directory path from a complete file name.

**Parameters:**
- `path_file_name` (str): The path file name

**Returns:** `str` - The directory path with trailing separator

**Example:**
```python
get_path_name("/home/user/document.txt")  # "/home/user/"
```

---

##### `get_parent_path_name(path_file_name: str) -> str`

Get the parent directory path.

**Parameters:**
- `path_file_name` (str): The path file name

**Returns:** `str` - The parent directory path with trailing separator

**Example:**
```python
get_parent_path_name("/home/user/docs/file.txt")  # "/home/user/"
```

---

##### `get_home_path() -> str`

Get the home directory of the current user.

**Returns:** `str` - The home directory path

**Example:**
```python
get_home_path()  # "/home/username" on Linux, "C:\\Users\\username" on Windows
```

---

##### `get_path_without_extension(path_file_name: str) -> str`

Get the full path without the file extension.

**Parameters:**
- `path_file_name` (str): The path file name

**Returns:** `str` - The path without extension

**Example:**
```python
get_path_without_extension("/path/to/file.txt")  # "/path/to/file"
```

---

##### `norm_path(file_name: str) -> str`

Normalize a path (convert backslashes, resolve relative paths).

**Parameters:**
- `file_name` (str): File path to normalize

**Returns:** `str` - Normalized path

**Example:**
```python
norm_path("path\\to\\file.txt")  # "path/to/file.txt"
```

---

#### Directory Operations

##### `get_current_directory() -> str`

Get the current working directory.

**Returns:** `str` - Current directory path

---

##### `set_current_directory(directory_name: str) -> None`

Set the current working directory.

**Parameters:**
- `directory_name` (str): Directory to change to

**Raises:** `RuntimeError` - If directory does not exist

---

##### `create_directory(dir_name: str) -> None`

Create a directory recursively (creates parent directories if needed).

**Parameters:**
- `dir_name` (str): Directory path to create

**Raises:** `OSError` - If there is an error creating the directory

---

##### `remove_directory(dir_name: str) -> None`

Remove a directory and all its contents.

**Parameters:**
- `dir_name` (str): Directory to remove

**Raises:** `RuntimeError` - If attempting to remove root directory ('/')

**Warning:** This operation is irreversible. Use with caution.

---

#### File Operations

##### `rename_file(src: str, target: str, overwrite: bool = False) -> None`

Rename or move a file.

**Parameters:**
- `src` (str): Source file path
- `target` (str): Target file path
- `overwrite` (bool): Whether to overwrite target if exists (default: False)

**Raises:**
- `FileNotFoundError` - If source file or target directory doesn't exist
- `FileExistsError` - If target exists and overwrite is False

---

##### `remove_file(file_name: str) -> None`

Remove a file.

**Parameters:**
- `file_name` (str): File to remove

**Raises:** `FileNotFoundError` - If file does not exist

---

#### File Listing

##### `create_file_list(pattern_list: List[str] | None = None, dir_name: str = "", recursive: bool = False, append_dirs: bool = False, add_hidden_files: bool = False, reverse_sort: bool = False) -> List[str]`

Create a list of files matching patterns in a directory.

**Parameters:**
- `pattern_list` (List[str], optional): Glob patterns to match (default: ["*"])
- `dir_name` (str, optional): Directory to search (default: current directory)
- `recursive` (bool, optional): Recursively search subdirectories (default: False)
- `append_dirs` (bool, optional): Include directories in results (default: False)
- `add_hidden_files` (bool, optional): Include hidden files (default: False)
- `reverse_sort` (bool, optional): Sort results in reverse (default: False)

**Returns:** `List[str]` - List of file paths matching criteria

**Example:**
```python
# Find all Python files recursively
files = create_file_list(
    pattern_list=["*.py"],
    dir_name="/project",
    recursive=True
)
```

---

### Serialization (serializer.py)

#### Convenience Functions

##### `serialize(data: Any, format_type: str) -> Union[str, bytes]`

Serialize data to string or bytes.

**Parameters:**
- `data` (Any): Data to serialize
- `format_type` (str): Format - "json", "yaml", "pickle", "msgpack"

**Returns:** `Union[str, bytes]` - Serialized data (string for text formats, bytes for binary)

**Raises:** `UnsupportedFormatError` - If format not supported

---

##### `deserialize(data: Union[str, bytes], format_type: str) -> Any`

Deserialize data from string or bytes.

**Parameters:**
- `data` (Union[str, bytes]): Serialized data
- `format_type` (str): Format - "json", "yaml", "pickle", "msgpack"

**Returns:** `Any` - Deserialized object

**Raises:** `SerializationError` - If deserialization fails

---

##### `to_file(data: Any, filepath: str, format_type: Optional[str] = None, **kwargs) -> None`

Serialize data to file with auto-format detection.

**Parameters:**
- `data` (Any): Data to serialize
- `filepath` (str): Target file path
- `format_type` (Optional[str]): Explicit format (auto-detected from extension if None)
- `**kwargs`: Additional options:
  - `compression` (bool): Enable gzip compression (default: False)
  - `encoding` (str): Text encoding (default: "utf-8")

**Raises:**
- `UnsupportedFormatError` - If format cannot be detected or is unsupported
- `SerializationError` - If serialization fails

**Example:**
```python
to_file(data, "output.json")  # Auto-detects JSON
to_file(data, "output.yaml.gz", compression=True)  # Compressed YAML
```

---

##### `from_file(filepath: str, format_type: Optional[str] = None, **kwargs) -> Any`

Deserialize data from file with auto-format detection.

**Parameters:**
- `filepath` (str): Source file path
- `format_type` (Optional[str]): Explicit format (auto-detected from extension if None)
- `**kwargs`: Additional options:
  - `compression` (bool): Enable gzip decompression (auto-detected)
  - `encoding` (str): Text encoding (default: "utf-8")

**Returns:** `Any` - Deserialized object

**Raises:**
- `FileNotFoundError` - If file does not exist
- `UnsupportedFormatError` - If format cannot be detected
- `SerializationError` - If deserialization fails

---

#### SerializerFactory Class

##### `SerializerFactory()`

Singleton factory for creating serializer instances.

**Methods:**

##### `get_serializer(format_type: str) -> Serializer`

Get a serializer instance for the specified format.

**Parameters:**
- `format_type` (str): Format name - "json", "yaml", "pickle", "msgpack"

**Returns:** `Serializer` - Serializer instance

**Raises:** `UnsupportedFormatError` - If format not supported

---

##### `list_available_formats() -> List[str]`

Get list of available serialization formats.

**Returns:** `List[str]` - Available format names

**Example:**
```python
factory = SerializerFactory()
formats = factory.list_available_formats()
# ['json', 'msgpack', 'mp', 'pickle', 'yaml', 'yml']
```

---

##### `register_serializer(format_type: str, serializer_class: Type[Serializer]) -> None`

Register a custom serializer.

**Parameters:**
- `format_type` (str): Format identifier
- `serializer_class` (Type[Serializer]): Serializer class (must inherit from Serializer)

**Raises:** `TypeError` - If serializer_class is not a Serializer subclass

---

#### Serializer Base Class

##### `Serializer`

Abstract base class for all serializers.

**Methods:**

##### `configure(compression: bool = False, encoding: str = "utf-8") -> None`

Configure serializer options.

**Parameters:**
- `compression` (bool): Enable gzip compression (default: False)
- `encoding` (str): Text encoding (default: "utf-8")

---

##### `serialize(data: Any) -> Union[str, bytes]`

Abstract method - serialize data to string or bytes.

---

##### `deserialize(data: Union[str, bytes]) -> Any`

Abstract method - deserialize data from string or bytes.

---

##### `to_file(data: Any, filepath: str) -> None`

Serialize data to file.

---

##### `from_file(filepath: str) -> Any`

Deserialize data from file.

---

#### Exception Classes

##### `SerializationError(Exception)`

Base exception for serialization errors.

---

##### `UnsupportedFormatError(SerializationError)`

Raised when unsupported format is requested.

---

### Output Redirection (output_redirector.py)

#### OutputRedirector Class

##### `OutputRedirector(target: Optional[OutputTarget] = None, **kwargs)`

Main class for redirecting stdout/stderr to different targets.

**Parameters:**
- `target` (OutputTarget, optional): Output target (default: MemoryTarget)
- `**kwargs`: Additional options:
  - `redirect_stdout` (bool): Redirect stdout (default: True)
  - `redirect_stderr` (bool): Redirect stderr (default: False)

**Methods:**

##### `start() -> None`

Start redirecting output streams.

---

##### `stop() -> None`

Stop redirecting and restore original streams.

---

##### `write(text: str) -> None`

Write text directly to the target.

---

##### `flush() -> None`

Flush the output buffer.

---

**Context Manager Support:**

```python
with OutputRedirector(target) as redirector:
    # Output redirected here
    pass
# Automatically restored
```

---

#### Output Targets

##### `FileTarget(filename: str, mode: str = "a", encoding: str = "utf-8")`

Target for writing output to a file.

**Parameters:**
- `filename` (str): Path to output file
- `mode` (str): File mode - "a" (append) or "w" (overwrite) (default: "a")
- `encoding` (str): File encoding (default: "utf-8")

---

##### `MemoryTarget()`

Target for storing output in memory.

**Methods:**

##### `get_buffer() -> str`

Get the captured output as a string.

**Returns:** `str` - All captured output

**Example:**
```python
target = MemoryTarget()
with OutputRedirector(target):
    print("Test")
output = target.get_buffer()  # "Test\n"
```

---

##### `DatabaseTarget(db_manager, instance_name: str, db_name: str, table: str, fields: Optional[Dict[str, str]] = None)`

Target for writing output to a database.

**Parameters:**
- `db_manager`: DbManager instance
- `instance_name` (str): Database instance name
- `db_name` (str): Database name
- `table` (str): Target table name
- `fields` (Dict[str, str], optional): Field definitions (default: {"timestamp": "TIMESTAMP", "message": "TEXT"})

**Note:** Requires basefunctions.db module.

---

#### Decorator

##### `redirect_output(target: Optional[Union[OutputTarget, str]] = None, stdout: bool = True, stderr: bool = False)`

Decorator for redirecting function output.

**Parameters:**
- `target` (OutputTarget | str, optional): Target or filename (default: MemoryTarget)
- `stdout` (bool): Redirect stdout (default: True)
- `stderr` (bool): Redirect stderr (default: False)

**Example:**
```python
@redirect_output("/path/to/output.log")
def my_function():
    print("This goes to file")
```

---

#### Thread-Safe Redirection

##### `ThreadSafeOutputRedirector(target_factory, **kwargs)`

Thread-safe version of OutputRedirector.

**Parameters:**
- `target_factory` (Callable): Function that creates a new target for each thread
- `**kwargs`: Same as OutputRedirector

**Example:**
```python
def target_factory():
    return MemoryTarget()

redirector = ThreadSafeOutputRedirector(target_factory)
```

---

## Appendix

### Format Comparison

| Feature | JSON | YAML | Pickle | MessagePack |
|---------|------|------|--------|-------------|
| Human-readable | Yes | Yes | No | No |
| Cross-language | Yes | Yes | No | Yes |
| Python objects | Limited | Limited | Yes | Limited |
| Speed | Medium | Slow | Fast | Very Fast |
| Size | Large | Large | Medium | Small |
| Security | Safe | Safe | **Unsafe** | Safe |

### Encoding Reference

Supported encodings (via Python standard library):
- `utf-8` (default, recommended)
- `utf-16`, `utf-32`
- `ascii`
- `latin-1`, `iso-8859-1`
- `cp1252` (Windows)

### Version History

- **v1.2**: Removed basefunctions special handling, uses bootstrap config
- **v1.1**: Added deployment/development path detection
- **v1.0**: Initial implementation

---

**End of IO Module Guide**

For more information, visit the [basefunctions documentation](https://github.com/neuraldevelopment/basefunctions) or contact the development team.
