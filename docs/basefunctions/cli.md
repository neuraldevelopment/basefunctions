# CLI - User Documentation

**Package:** basefunctions
**Subpackage:** cli
**Version:** 0.5.75
**Purpose:** Complete framework for building professional command-line applications

---

## Overview

The cli subpackage provides a complete framework for building command-line applications with automatic help generation, shell completion, progress tracking, and formatted output.

**Key Features:**
- Command-based architecture with automatic registration
- Built-in argument parsing and validation
- Shell completion support (bash, zsh, fish)
- Rich output formatting and progress tracking
- Context management for shared state
- Extensible command system

**Common Use Cases:**
- Building CLI tools and utilities
- Creating multi-command applications
- Interactive command-line interfaces
- Development tools and scripts
- Administration utilities

---

## Public APIs

### CLIApplication

**Purpose:** Main application class that coordinates commands and execution

```python
from basefunctions.cli import CLIApplication

app = CLIApplication(
    name: str,
    version: str,
    description: str = ""
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | str | - | Application name |
| `version` | str | - | Application version |
| `description` | str | "" | Application description |

**Key Methods:**

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `register_command()` | `command: BaseCommand` | `None` | Register a command |
| `run()` | `args: list[str] | None = None` | `int` | Execute application (returns exit code) |

**Examples:**

```python
from basefunctions.cli import CLIApplication, BaseCommand

# Create application
app = CLIApplication(
    name="mytool",
    version="1.0.0",
    description="My command-line tool"
)

# Register commands (see BaseCommand below)
app.register_command(MyCommand())

# Run application
exit_code = app.run()
```

**Best For:**
- Main entry point for CLI apps
- Command coordination
- Automatic help and version handling

---

### BaseCommand

**Purpose:** Base class for implementing custom commands

```python
from basefunctions.cli import BaseCommand, CommandMetadata, ArgumentSpec

class MyCommand(BaseCommand):
    def get_metadata(self) -> CommandMetadata:
        """Define command metadata"""
        return CommandMetadata(
            name="mycommand",
            description="Description of command",
            arguments=[
                ArgumentSpec(
                    name="arg1",
                    type="str",
                    required=True,
                    help="Argument help text"
                )
            ]
        )

    def execute(self, context) -> int:
        """Execute command logic"""
        # Access arguments
        arg1 = context.get_arg("arg1")

        # Command logic here
        print(f"Processing: {arg1}")

        return 0  # Return exit code
```

**When to Extend:**
- Implementing each CLI command
- Creating reusable command components
- Building command hierarchies

**Implementation Example:**

```python
from basefunctions.cli import BaseCommand, CommandMetadata, ArgumentSpec, ContextManager

class ProcessCommand(BaseCommand):
    def get_metadata(self) -> CommandMetadata:
        """Define command interface"""
        return CommandMetadata(
            name="process",
            description="Process data files",
            arguments=[
                ArgumentSpec(
                    name="input",
                    type="str",
                    required=True,
                    help="Input file path"
                ),
                ArgumentSpec(
                    name="output",
                    type="str",
                    required=False,
                    default="output.txt",
                    help="Output file path"
                ),
                ArgumentSpec(
                    name="verbose",
                    type="flag",
                    short_name="v",
                    help="Enable verbose output"
                )
            ]
        )

    def execute(self, context: ContextManager) -> int:
        """Execute processing"""
        # Get arguments
        input_file = context.get_arg("input")
        output_file = context.get_arg("output")
        verbose = context.get_arg("verbose", default=False)

        # Process
        if verbose:
            print(f"Processing {input_file} -> {output_file}")

        try:
            # Processing logic
            result = process_file(input_file, output_file)

            print(f"Success: {result}")
            return 0
        except Exception as e:
            print(f"Error: {e}")
            return 1
```

**Important Rules:**
1. Always implement `get_metadata()` and `execute()`
2. Return exit code from `execute()` (0 = success, non-zero = error)
3. Use `ContextManager` for argument access
4. Handle exceptions and return appropriate exit codes

---

### CommandMetadata

**Purpose:** Define command interface with arguments and help text

```python
from basefunctions.cli import CommandMetadata, ArgumentSpec

metadata = CommandMetadata(
    name: str,
    description: str,
    arguments: list[ArgumentSpec] = [],
    examples: list[str] = []
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | str | - | Command name |
| `description` | str | - | Command description |
| `arguments` | list | [] | List of ArgumentSpec |
| `examples` | list | [] | Usage examples |

**Examples:**

```python
from basefunctions.cli import CommandMetadata, ArgumentSpec

metadata = CommandMetadata(
    name="deploy",
    description="Deploy application to server",
    arguments=[
        ArgumentSpec(name="environment", type="str", required=True),
        ArgumentSpec(name="dry-run", type="flag", help="Simulate deployment")
    ],
    examples=[
        "mytool deploy production",
        "mytool deploy staging --dry-run"
    ]
)
```

---

### ArgumentSpec

**Purpose:** Define individual command arguments

```python
from basefunctions.cli import ArgumentSpec

arg = ArgumentSpec(
    name: str,
    type: str = "str",
    required: bool = False,
    default: Any = None,
    short_name: str | None = None,
    help: str = "",
    choices: list | None = None
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | str | - | Argument name |
| `type` | str | "str" | Type: "str", "int", "float", "flag" |
| `required` | bool | False | Is argument required |
| `default` | Any | None | Default value |
| `short_name` | str | None | Short flag (e.g., "v" for -v) |
| `help` | str | "" | Help text |
| `choices` | list | None | Valid choices |

**Examples:**

```python
from basefunctions.cli import ArgumentSpec

# Required string argument
arg1 = ArgumentSpec(
    name="file",
    type="str",
    required=True,
    help="Path to input file"
)

# Optional with default
arg2 = ArgumentSpec(
    name="timeout",
    type="int",
    default=30,
    help="Timeout in seconds"
)

# Flag (boolean)
arg3 = ArgumentSpec(
    name="verbose",
    type="flag",
    short_name="v",
    help="Enable verbose output"
)

# Choices
arg4 = ArgumentSpec(
    name="level",
    type="str",
    choices=["debug", "info", "warning", "error"],
    default="info",
    help="Log level"
)
```

---

### OutputFormatter

**Purpose:** Format and display output in consistent style

```python
from basefunctions.cli import OutputFormatter, show_header, show_result

# Direct functions
show_header("Section Title")
show_result("Success", success=True)
show_result("Failed", success=False)
```

**Helper Functions:**

| Function | Parameters | Description |
|----------|-----------|-------------|
| `show_header()` | `text: str` | Display section header |
| `show_progress()` | `message: str, percent: float` | Show progress |
| `show_result()` | `message: str, success: bool` | Display result |

**Examples:**

```python
from basefunctions.cli import show_header, show_progress, show_result

# Display header
show_header("Processing Data")

# Show progress
for i in range(100):
    show_progress("Processing", i / 100)

# Show result
show_result("Processing complete", success=True)
```

---

### ProgressTracker

**Purpose:** Track and display progress for long-running operations

```python
from basefunctions.cli import ProgressTracker

tracker = ProgressTracker(
    total: int,
    title: str = "Progress"
)
```

**Key Methods:**

| Method | Parameters | Description |
|--------|-----------|-------------|
| `update()` | `count: int = 1` | Increment progress |
| `set_progress()` | `current: int` | Set absolute progress |
| `finish()` | - | Complete progress |

**Examples:**

```python
from basefunctions.cli import ProgressTracker

# Create tracker
tracker = ProgressTracker(total=100, title="Processing files")

# Update progress
for i in range(100):
    process_file(i)
    tracker.update(1)

# Finish
tracker.finish()
```

---

### ContextManager

**Purpose:** Manage shared state and arguments across commands

```python
from basefunctions.cli import ContextManager

context = ContextManager()
```

**Key Methods:**

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `get_arg()` | `name: str, default: Any = None` | `Any` | Get argument value |
| `set_value()` | `key: str, value: Any` | `None` | Store shared value |
| `get_value()` | `key: str, default: Any = None` | `Any` | Retrieve shared value |

**Examples:**

```python
# Access in command
def execute(self, context: ContextManager) -> int:
    # Get arguments
    file_path = context.get_arg("file")
    verbose = context.get_arg("verbose", default=False)

    # Store shared state
    context.set_value("processed_count", 42)

    # Access later
    count = context.get_value("processed_count")
```

---

## Usage Examples

### Basic Usage (Most Common)

**Scenario:** Simple CLI tool with single command

```python
from basefunctions.cli import (
    CLIApplication,
    BaseCommand,
    CommandMetadata,
    ArgumentSpec,
    ContextManager
)

# Step 1: Define command
class GreetCommand(BaseCommand):
    def get_metadata(self) -> CommandMetadata:
        return CommandMetadata(
            name="greet",
            description="Greet a user",
            arguments=[
                ArgumentSpec(
                    name="name",
                    type="str",
                    required=True,
                    help="Name to greet"
                ),
                ArgumentSpec(
                    name="loud",
                    type="flag",
                    short_name="l",
                    help="Greet loudly"
                )
            ]
        )

    def execute(self, context: ContextManager) -> int:
        name = context.get_arg("name")
        loud = context.get_arg("loud", default=False)

        greeting = f"Hello, {name}!"
        if loud:
            greeting = greeting.upper()

        print(greeting)
        return 0

# Step 2: Create application
app = CLIApplication(
    name="greeter",
    version="1.0.0",
    description="A simple greeting tool"
)

# Step 3: Register command
app.register_command(GreetCommand())

# Step 4: Run
if __name__ == "__main__":
    exit_code = app.run()
    exit(exit_code)
```

**Usage:**
```bash
python greeter.py greet John
# Output: Hello, John!

python greeter.py greet John --loud
# Output: HELLO, JOHN!

python greeter.py --help
# Shows help
```

---

### Advanced Usage - Multiple Commands

**Scenario:** CLI tool with multiple commands

```python
from basefunctions.cli import (
    CLIApplication,
    BaseCommand,
    CommandMetadata,
    ArgumentSpec,
    ContextManager,
    show_header,
    show_result
)

# Command 1: Create
class CreateCommand(BaseCommand):
    def get_metadata(self) -> CommandMetadata:
        return CommandMetadata(
            name="create",
            description="Create a new project",
            arguments=[
                ArgumentSpec(name="name", type="str", required=True, help="Project name"),
                ArgumentSpec(name="template", type="str", default="basic", help="Template type")
            ]
        )

    def execute(self, context: ContextManager) -> int:
        name = context.get_arg("name")
        template = context.get_arg("template")

        show_header(f"Creating project: {name}")
        create_project(name, template)
        show_result("Project created successfully", success=True)
        return 0

# Command 2: Build
class BuildCommand(BaseCommand):
    def get_metadata(self) -> CommandMetadata:
        return CommandMetadata(
            name="build",
            description="Build the project",
            arguments=[
                ArgumentSpec(name="release", type="flag", short_name="r", help="Release build")
            ]
        )

    def execute(self, context: ContextManager) -> int:
        release = context.get_arg("release", default=False)

        show_header("Building project")
        build_project(release=release)
        show_result("Build complete", success=True)
        return 0

# Setup application
app = CLIApplication(
    name="projecttool",
    version="1.0.0",
    description="Project management tool"
)

app.register_command(CreateCommand())
app.register_command(BuildCommand())

if __name__ == "__main__":
    exit(app.run())
```

**Usage:**
```bash
projecttool create myapp --template advanced
projecttool build --release
```

---

### Advanced Usage - Progress Tracking

**Scenario:** Show progress for long operations

```python
from basefunctions.cli import (
    BaseCommand,
    CommandMetadata,
    ArgumentSpec,
    ContextManager,
    ProgressTracker
)
import time

class ProcessCommand(BaseCommand):
    def get_metadata(self) -> CommandMetadata:
        return CommandMetadata(
            name="process",
            description="Process files",
            arguments=[
                ArgumentSpec(name="count", type="int", default=10)
            ]
        )

    def execute(self, context: ContextManager) -> int:
        count = context.get_arg("count")

        # Create progress tracker
        tracker = ProgressTracker(total=count, title="Processing files")

        # Process with progress updates
        for i in range(count):
            time.sleep(0.1)  # Simulate work
            tracker.update(1)

        tracker.finish()
        print("All files processed!")
        return 0
```

---

### Integration with Other Components

**Working with ConfigHandler:**

```python
from basefunctions.cli import BaseCommand, CommandMetadata, ContextManager
from basefunctions.config import ConfigHandler

class ConfigCommand(BaseCommand):
    def __init__(self):
        super().__init__()
        self.config = ConfigHandler()

    def get_metadata(self) -> CommandMetadata:
        return CommandMetadata(
            name="config",
            description="Show configuration"
        )

    def execute(self, context: ContextManager) -> int:
        # Load config
        self.config.load_config_for_package("myapp")

        # Display config
        all_config = self.config.get_all()
        for key, value in all_config.items():
            print(f"{key}: {value}")

        return 0
```

---

### Custom Implementation Example

**Scenario:** Build command with validation and error handling

```python
from basefunctions.cli import (
    BaseCommand,
    CommandMetadata,
    ArgumentSpec,
    ContextManager,
    show_header,
    show_result
)
from pathlib import Path

class ValidatedCommand(BaseCommand):
    def get_metadata(self) -> CommandMetadata:
        return CommandMetadata(
            name="import",
            description="Import data from file",
            arguments=[
                ArgumentSpec(
                    name="file",
                    type="str",
                    required=True,
                    help="File to import"
                ),
                ArgumentSpec(
                    name="format",
                    type="str",
                    choices=["json", "yaml", "csv"],
                    default="json",
                    help="File format"
                )
            ]
        )

    def execute(self, context: ContextManager) -> int:
        file_path = context.get_arg("file")
        file_format = context.get_arg("format")

        show_header("Importing Data")

        # Validate file exists
        path = Path(file_path)
        if not path.exists():
            show_result(f"File not found: {file_path}", success=False)
            return 1

        # Validate format matches extension
        expected_ext = f".{file_format}"
        if path.suffix != expected_ext:
            show_result(
                f"Format mismatch: file has {path.suffix}, expected {expected_ext}",
                success=False
            )
            return 1

        # Import data
        try:
            data = self._import_file(path, file_format)
            show_result(f"Imported {len(data)} records", success=True)
            return 0
        except Exception as e:
            show_result(f"Import failed: {e}", success=False)
            return 1

    def _import_file(self, path: Path, format: str) -> list:
        """Import file based on format"""
        # Implementation here
        return []
```

---

## Best Practices

### Best Practice 1: Clear Command Names and Help

**Why:** Usability and discoverability

```python
# GOOD
CommandMetadata(
    name="deploy",
    description="Deploy application to target environment",
    arguments=[
        ArgumentSpec(
            name="environment",
            type="str",
            required=True,
            help="Target environment (staging, production)"
        )
    ],
    examples=[
        "mytool deploy staging",
        "mytool deploy production --dry-run"
    ]
)
```

```python
# AVOID
CommandMetadata(
    name="d",
    description="Deploy",
    arguments=[
        ArgumentSpec(name="env", type="str", required=True)
    ]
)
```

---

### Best Practice 2: Return Meaningful Exit Codes

**Why:** Integration with scripts and automation

```python
# GOOD
def execute(self, context: ContextManager) -> int:
    try:
        result = perform_operation()
        if result.success:
            return 0  # Success
        else:
            print(f"Operation failed: {result.error}")
            return 1  # Generic error
    except FileNotFoundError:
        print("Required file not found")
        return 2  # Specific error code
    except PermissionError:
        print("Permission denied")
        return 3  # Specific error code
```

```python
# AVOID
def execute(self, context: ContextManager) -> int:
    perform_operation()
    return 0  # Always success, even on error
```

---

### Best Practice 3: Validate Arguments

**Why:** Better error messages and user experience

```python
# GOOD
def execute(self, context: ContextManager) -> int:
    timeout = context.get_arg("timeout")

    # Validate range
    if timeout < 1 or timeout > 300:
        print("Error: timeout must be between 1 and 300 seconds")
        return 1

    # Proceed with valid value
    perform_operation(timeout=timeout)
    return 0
```

```python
# AVOID
def execute(self, context: ContextManager) -> int:
    timeout = context.get_arg("timeout")
    perform_operation(timeout=timeout)  # May fail with cryptic error
    return 0
```

---

## Error Handling

### Common Errors

**Error 1: Missing Required Argument**

```python
# User runs: mytool process
# Without required 'file' argument

# Framework automatically shows:
# Error: Missing required argument: file
# Try: mytool process --help
```

**Solution:** Framework handles this automatically with clear error messages

---

**Error 2: Invalid Argument Type**

```python
# User runs: mytool process --timeout abc

# Framework validates type:
# Error: Invalid value for --timeout: expected int, got 'abc'
```

**Solution:** Framework handles type validation automatically

---

### Error Recovery

```python
def execute(self, context: ContextManager) -> int:
    try:
        file_path = context.get_arg("file")
        data = load_file(file_path)
        process_data(data)
        return 0
    except FileNotFoundError as e:
        print(f"Error: File not found: {e}")
        return 1
    except ValueError as e:
        print(f"Error: Invalid data format: {e}")
        return 2
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 99
```

---

## See Also

**Related Subpackages:**
- `config` (`docs/basefunctions/config.md`) - Configuration for CLI apps
- `utils` - Progress tracking and formatting utilities

**System Documentation:**
- `~/.claude/_docs/python/basefunctions.md` - Internal architecture details

---

## Quick Reference

### Imports

```python
# Core classes
from basefunctions.cli import (
    CLIApplication,
    BaseCommand,
    CommandMetadata,
    ArgumentSpec,
    ContextManager
)

# Output formatting
from basefunctions.cli import (
    OutputFormatter,
    show_header,
    show_progress,
    show_result
)

# Progress tracking
from basefunctions.cli import ProgressTracker, AliveProgressTracker
```

### Quick Start

```python
# Step 1: Define command
class MyCommand(BaseCommand):
    def get_metadata(self) -> CommandMetadata:
        return CommandMetadata(
            name="mycommand",
            description="Description",
            arguments=[
                ArgumentSpec(name="arg", type="str", required=True)
            ]
        )

    def execute(self, context: ContextManager) -> int:
        arg = context.get_arg("arg")
        print(f"Processing: {arg}")
        return 0

# Step 2: Create app
app = CLIApplication(name="mytool", version="1.0.0")
app.register_command(MyCommand())

# Step 3: Run
exit(app.run())
```

### Cheat Sheet

| Task | Code |
|------|------|
| Create app | `CLIApplication(name, version)` |
| Register command | `app.register_command(cmd)` |
| Run app | `app.run()` |
| Get argument | `context.get_arg("name")` |
| Show header | `show_header("Title")` |
| Show result | `show_result("msg", success=True)` |
| Track progress | `ProgressTracker(total=100)` |

---

**Document Version:** 0.5.75
**Last Updated:** 2026-01-29
**Subpackage Version:** 0.5.75
