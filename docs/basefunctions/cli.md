# CLI Framework Module Guide

**basefunctions.cli** - Professional Command-Line Interface Framework

Version: 1.1
Last Updated: 2025-01-24
Framework: basefunctions v0.5.32

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Quick Start](#quick-start)
4. [Core Components](#core-components)
5. [Building Commands](#building-commands)
6. [Command Groups](#command-groups)
7. [Argument Parsing](#argument-parsing)
8. [Context Management](#context-management)
9. [Tab Completion](#tab-completion)
10. [Output Formatting](#output-formatting)
11. [Progress Tracking](#progress-tracking)
12. [Best Practices](#best-practices)
13. [Complete Examples](#complete-examples)
14. [API Reference](#api-reference)

---

## Overview

The `basefunctions.cli` module provides a comprehensive framework for building professional command-line interface applications with:

**Key Features:**
- **Command Groups** - Organize commands hierarchically (e.g., `git commit`, `docker ps`)
- **Smart Argument Parsing** - Handle quoted strings, compound arguments, context resolution
- **Tab Completion** - Intelligent shell-like tab completion with custom completion functions
- **Context Management** - Maintain state across commands (e.g., current database, instance)
- **Help System** - Automatic help generation from command metadata
- **Output Formatting** - Consistent, professional output with tables and boxes
- **Progress Tracking** - Built-in progress bars for long operations
- **Alias Support** - Create shortcuts for frequently used commands
- **Multi-Handler Support** - Multiple command handlers per group

**Philosophy:**
- **Convention over Configuration** - Sensible defaults, minimal boilerplate
- **Developer Experience** - Easy to extend, clear patterns
- **User Experience** - Professional CLI with tab completion and helpful errors
- **Type Safety** - Strong typing with metadata-driven validation

---

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     CLIApplication                          │
│  - Main orchestrator                                        │
│  - Event loop, command routing                              │
│  - Lifecycle management                                     │
└─────────────────────────────────────────────────────────────┘
           │           │                    │
           ▼           ▼                    ▼
    ┌────────────┐ ┌────────────┐   ┌────────────────┐
    │  Command   │ │  Context   │   │  Completion    │
    │  Registry  │ │  Manager   │   │  Handler       │
    └────────────┘ └────────────┘   └────────────────┘
           │
           ▼
    ┌─────────────────────┐
    │   BaseCommand       │
    │   (Abstract Base)   │
    └─────────────────────┘
           │
           ▼
    ┌─────────────────────┐
    │  Your Commands      │
    │  (Implementations)  │
    └─────────────────────┘
```

### Data Flow

```
User Input
    │
    ▼
ArgumentParser ──> (command, subcommand, args)
    │
    ▼
CommandRegistry ──> Resolve aliases, find handler
    │
    ▼
BaseCommand ──> Validate, execute
    │
    ▼
OutputFormatter ──> Display results
```

### Core Classes

| Class | Purpose | Key Responsibilities |
|-------|---------|---------------------|
| `CLIApplication` | Main orchestrator | Event loop, routing, lifecycle |
| `BaseCommand` | Command base class | Command registration, execution |
| `CommandRegistry` | Command catalog | Registration, lookup, dispatch |
| `ContextManager` | State management | Context storage, prompt generation |
| `ArgumentParser` | Input processing | Parsing, validation |
| `CompletionHandler` | Tab completion | Intelligent suggestions |
| `OutputFormatter` | Display formatting | Tables, boxes, results |
| `HelpFormatter` | Help generation | Auto-generated help text |

---

## Quick Start

### 5-Minute CLI Application

**Step 1: Create Command Handler**

```python
from basefunctions.cli import BaseCommand, CommandMetadata, ArgumentSpec

class MyCommands(BaseCommand):
    def register_commands(self):
        return {
            "hello": CommandMetadata(
                name="hello",
                description="Greet user",
                usage="hello [name]",
                args=[
                    ArgumentSpec(
                        name="name",
                        arg_type="string",
                        required=False,
                        description="Name to greet"
                    )
                ],
                examples=["hello", "hello Alice"]
            ),
            "status": CommandMetadata(
                name="status",
                description="Show application status",
                usage="status"
            )
        }

    def execute(self, command, args):
        if command == "hello":
            name = args[0] if args else "World"
            print(f"Hello, {name}!")

        elif command == "status":
            print("Application is running")
```

**Step 2: Create Application**

```python
from basefunctions.cli import CLIApplication

def main():
    app = CLIApplication("myapp", version="1.0")

    # Register commands at root level (empty string)
    app.register_command_group("", MyCommands(app.context))

    # Run interactive loop
    app.run()

if __name__ == "__main__":
    main()
```

**Step 3: Run**

```bash
$ python myapp.py
myapp v1.0
Type 'help' for commands or 'quit' to exit

myapp> hello
Hello, World!

myapp> hello Alice
Hello, Alice!

myapp> status
Application is running

myapp> help
Available commands:

ROOT COMMANDS:
  hello [name]                             - Greet user
  status                                   - Show application status

GENERAL:
  help [command]      - Show help
  quit/exit           - Exit CLI

myapp> quit
Goodbye!
```

**That's it!** You now have a fully functional CLI with:
- Tab completion (try pressing Tab)
- Automatic help generation
- Command validation
- Professional output

---

## Core Components

### CLIApplication

The main application orchestrator that manages the command lifecycle.

#### Basic Usage

```python
from basefunctions.cli import CLIApplication

# Create application
app = CLIApplication(
    app_name="mytool",
    version="1.0.0",
    enable_completion=True  # Enable tab completion (default)
)

# Register command groups
app.register_command_group("", RootCommands(app.context))
app.register_command_group("db", DatabaseCommands(app.context))
app.register_command_group("user", UserCommands(app.context))

# Register aliases
app.register_alias("ls", "list")
app.register_alias("st", "status")

# Run interactive loop
app.run()
```

#### Properties

- `app_name` - Application name (shown in prompt)
- `version` - Application version
- `context` - Shared context manager
- `registry` - Command registry
- `parser` - Argument parser
- `completion` - Completion handler (if enabled)

#### Built-in Commands

These commands are always available:

- `help` - Show help for all commands
- `help [group]` - Show help for command group
- `help [group] [command]` - Show help for specific command
- `help aliases` - Show all aliases
- `quit` / `exit` - Exit application

#### Command Routing

The application uses intelligent command routing:

```
Input: "db connect mydb"
    ↓
1. Parse: group="db", command="connect", args=["mydb"]
2. Resolve alias (if any)
3. Lookup handlers for group "db"
4. Find handler that validates "connect"
5. Execute handler.execute("connect", ["mydb"])
```

**Root vs. Group Commands:**

```python
# Root-level command (no group)
app.register_command_group("", RootCommands(app.context))
# Usage: "status", "version", etc.

# Grouped command
app.register_command_group("db", DatabaseCommands(app.context))
# Usage: "db connect", "db list", etc.
```

---

### BaseCommand

Abstract base class for implementing command handlers.

#### Implementation Pattern

```python
from basefunctions.cli import BaseCommand, CommandMetadata, ArgumentSpec
from typing import Dict, List

class MyCommands(BaseCommand):
    def __init__(self, context_manager):
        super().__init__(context_manager)
        # Custom initialization here

    def register_commands(self) -> Dict[str, CommandMetadata]:
        """Register available commands with metadata."""
        return {
            "command1": CommandMetadata(...),
            "command2": CommandMetadata(...),
        }

    def execute(self, command: str, args: List[str]) -> None:
        """Execute specific command."""
        if command == "command1":
            self._handle_command1(args)
        elif command == "command2":
            self._handle_command2(args)

    def _handle_command1(self, args):
        """Implementation for command1."""
        pass
```

#### Helper Methods

BaseCommand provides useful helper methods:

```python
class MyCommands(BaseCommand):
    def execute(self, command, args):
        if command == "delete":
            # Get user confirmation
            if not self._confirm_action("Delete all data?"):
                print("Cancelled")
                return

            try:
                # ... perform delete ...
                print("Deleted successfully")
            except Exception as e:
                # Handle error with logging
                self._handle_error(command, e)
```

**Available Helpers:**

- `self.context` - Access shared context
- `self.logger` - Logger instance
- `self._confirm_action(message)` - Get user confirmation (y/N)
- `self._handle_error(command, error)` - Log and display error
- `self.get_available_commands()` - List of registered commands
- `self.get_command_metadata(cmd)` - Get metadata for command
- `self.validate_command(cmd)` - Check if command exists
- `self.get_help(cmd)` - Generate help text

---

### CommandMetadata

Defines command structure, arguments, and documentation.

#### Complete Example

```python
from basefunctions.cli import CommandMetadata, ArgumentSpec

metadata = CommandMetadata(
    # Basic information
    name="connect",
    description="Connect to a database instance",
    usage="db connect <instance> [database]",

    # Arguments
    args=[
        ArgumentSpec(
            name="instance",
            arg_type="string",
            required=True,
            context_key="instance",  # Can fallback to context
            description="Database instance name",
            completion_func=lambda text, ctx: get_instances(text)  # Custom completion
        ),
        ArgumentSpec(
            name="database",
            arg_type="string",
            required=False,
            context_key="database",
            choices=["main", "test", "dev"],  # Predefined choices
            description="Database name (default: main)"
        )
    ],

    # Documentation
    examples=[
        "db connect prod",
        "db connect prod.main",
        "db connect test main"
    ],

    # Context requirements
    requires_context=False,
    context_keys=None,  # Or ["instance"] if context required

    # Aliases
    aliases=["conn"]
)
```

#### Argument Types

Common `arg_type` values:

- `"string"` - Generic string argument
- `"int"` - Integer value
- `"file"` - File path
- `"instance"` - Instance name (domain-specific)
- `"database"` - Database name (domain-specific)

**Note:** These are semantic hints for completion and validation, not enforced types.

#### Context Integration

Commands can use context for default values:

```python
ArgumentSpec(
    name="instance",
    arg_type="string",
    required=False,  # Not required if in context
    context_key="instance",  # Fallback to context["instance"]
    description="Instance name"
)
```

**Usage:**

```python
# Without context
myapp> db connect prod
# context["instance"] = "prod"

# Now "instance" is in context
myapp[prod]> db list
# Uses context["instance"] automatically

# Override context
myapp[prod]> db list test
# Uses "test" instead of context
```

---

## Building Commands

### Simple Command

```python
class SimpleCommands(BaseCommand):
    def register_commands(self):
        return {
            "ping": CommandMetadata(
                name="ping",
                description="Test connectivity",
                usage="ping"
            )
        }

    def execute(self, command, args):
        if command == "ping":
            print("Pong!")
```

### Command with Arguments

```python
class FileCommands(BaseCommand):
    def register_commands(self):
        return {
            "read": CommandMetadata(
                name="read",
                description="Read file contents",
                usage="read <filename>",
                args=[
                    ArgumentSpec(
                        name="filename",
                        arg_type="file",
                        required=True,
                        description="File to read"
                    )
                ],
                examples=["read config.json", "read data.csv"]
            )
        }

    def execute(self, command, args):
        if command == "read":
            if not args:
                print("Error: filename required")
                return

            filename = args[0]
            try:
                with open(filename, 'r') as f:
                    print(f.read())
            except FileNotFoundError:
                print(f"Error: File '{filename}' not found")
```

### Command with Optional Arguments

```python
class GreetCommands(BaseCommand):
    def register_commands(self):
        return {
            "greet": CommandMetadata(
                name="greet",
                description="Greet user",
                usage="greet [name] [--formal]",
                args=[
                    ArgumentSpec(
                        name="name",
                        arg_type="string",
                        required=False,
                        description="Name to greet (default: User)"
                    ),
                    ArgumentSpec(
                        name="formal",
                        arg_type="string",
                        required=False,
                        choices=["--formal"],
                        description="Use formal greeting"
                    )
                ]
            )
        }

    def execute(self, command, args):
        if command == "greet":
            name = args[0] if args else "User"
            formal = "--formal" in args

            if formal:
                print(f"Good day, {name}")
            else:
                print(f"Hi {name}!")
```

### Command with Validation

```python
class MathCommands(BaseCommand):
    def register_commands(self):
        return {
            "add": CommandMetadata(
                name="add",
                description="Add two numbers",
                usage="add <num1> <num2>",
                args=[
                    ArgumentSpec(name="num1", arg_type="int", required=True),
                    ArgumentSpec(name="num2", arg_type="int", required=True)
                ],
                examples=["add 5 3", "add 100 -50"]
            )
        }

    def execute(self, command, args):
        if command == "add":
            if len(args) < 2:
                print("Error: Two numbers required")
                return

            try:
                num1 = int(args[0])
                num2 = int(args[1])
                result = num1 + num2
                print(f"{num1} + {num2} = {result}")
            except ValueError:
                print("Error: Arguments must be integers")
```

---

## Command Groups

Command groups organize related commands hierarchically.

### Multi-Group Application

```python
from basefunctions.cli import CLIApplication, BaseCommand, CommandMetadata

# Root-level commands
class RootCommands(BaseCommand):
    def register_commands(self):
        return {
            "status": CommandMetadata(
                name="status",
                description="Show application status",
                usage="status"
            ),
            "version": CommandMetadata(
                name="version",
                description="Show version information",
                usage="version"
            )
        }

    def execute(self, command, args):
        if command == "status":
            print("Application: Running")
        elif command == "version":
            print("Version: 1.0.0")

# Database commands
class DatabaseCommands(BaseCommand):
    def register_commands(self):
        return {
            "list": CommandMetadata(
                name="list",
                description="List all databases",
                usage="db list"
            ),
            "create": CommandMetadata(
                name="create",
                description="Create new database",
                usage="db create <name>",
                args=[
                    ArgumentSpec(name="name", arg_type="string", required=True)
                ]
            )
        }

    def execute(self, command, args):
        if command == "list":
            print("Databases: main, test, dev")
        elif command == "create":
            db_name = args[0] if args else None
            if db_name:
                print(f"Created database: {db_name}")
            else:
                print("Error: database name required")

# User commands
class UserCommands(BaseCommand):
    def register_commands(self):
        return {
            "list": CommandMetadata(
                name="list",
                description="List all users",
                usage="user list"
            ),
            "add": CommandMetadata(
                name="add",
                description="Add new user",
                usage="user add <username>",
                args=[
                    ArgumentSpec(name="username", arg_type="string", required=True)
                ]
            )
        }

    def execute(self, command, args):
        if command == "list":
            print("Users: admin, guest")
        elif command == "add":
            username = args[0] if args else None
            if username:
                print(f"Added user: {username}")

# Create application
app = CLIApplication("myapp", version="1.0")

# Register all command groups
app.register_command_group("", RootCommands(app.context))
app.register_command_group("db", DatabaseCommands(app.context))
app.register_command_group("user", UserCommands(app.context))

# Run
app.run()
```

**Usage:**

```
myapp> status
Application: Running

myapp> db list
Databases: main, test, dev

myapp> user list
Users: admin, guest

myapp> help

Available commands:

ROOT COMMANDS:
  status                                   - Show application status
  version                                  - Show version information

DB COMMANDS:
  db list                                  - List all databases
  db create <name>                         - Create new database

USER COMMANDS:
  user list                                - List all users
  user add <username>                      - Add new user
```

### Multi-Handler Groups

Multiple handlers can be registered for the same group:

```python
# Database connection commands
class DbConnectionCommands(BaseCommand):
    def register_commands(self):
        return {
            "connect": CommandMetadata(...),
            "disconnect": CommandMetadata(...)
        }

    def execute(self, command, args):
        # Handle connection commands
        pass

# Database query commands
class DbQueryCommands(BaseCommand):
    def register_commands(self):
        return {
            "select": CommandMetadata(...),
            "insert": CommandMetadata(...)
        }

    def execute(self, command, args):
        # Handle query commands
        pass

# Register both to "db" group
app.register_command_group("db", DbConnectionCommands(app.context))
app.register_command_group("db", DbQueryCommands(app.context))

# Now "db" group has: connect, disconnect, select, insert
```

---

## Argument Parsing

The `ArgumentParser` handles complex input parsing.

### Quoted Arguments

```python
myapp> greet "John Doe"
# args = ["John Doe"]

myapp> open "/path/with spaces/file.txt"
# args = ["/path/with spaces/file.txt"]

myapp> process "item 1" "item 2"
# args = ["item 1", "item 2"]
```

### Compound Arguments

Arguments can use dot notation for hierarchical values:

```python
# Parsing compound arguments
from basefunctions.cli import ArgumentParser

arg = "instance.database"
primary, secondary = ArgumentParser.split_compound_argument(arg)
# primary = "instance"
# secondary = "database"
```

**Example Usage:**

```python
class DbCommands(BaseCommand):
    def execute(self, command, args):
        if command == "connect":
            arg = args[0] if args else None

            # Parse "instance.database" or use context
            instance, database = self.context.resolve_target(
                arg,
                primary_key="instance",
                secondary_key="database"
            )

            print(f"Connecting to {instance}.{database}")
```

```
# Usage variations
myapp> db connect prod.main
Connecting to prod.main

myapp> db connect prod
# Uses context["database"] if set
Connecting to prod.dev

myapp[prod.main]> db connect
# Uses both from context
Connecting to prod.main
```

### Context Resolution

Arguments can fallback to context values:

```python
from basefunctions.cli import ArgumentParser

value = ArgumentParser.resolve_argument_with_context(
    arg=args[0] if args else None,
    arg_spec=argument_spec,
    context_manager=self.context
)
```

**Resolution Order:**
1. Use provided argument if present
2. Check context_key in ContextManager
3. Raise ValueError if required and not found

---

## Context Management

`ContextManager` maintains state across commands.

### Basic Usage

```python
# Access context
context = app.context

# Set values
context.set("instance", "production")
context.set("database", "main")

# Get values
instance = context.get("instance")
database = context.get("database", default="default")

# Check existence
if context.has("instance"):
    print(f"Connected to {context.get('instance')}")

# Clear values
context.clear("instance")  # Clear specific key
context.clear()  # Clear all

# Get all context
all_values = context.get_all()
# Returns: {"instance": "production", "database": "main"}
```

### Context-Aware Prompts

The prompt automatically shows current context:

```python
# No context
myapp>

# With context
myapp[production]>

# Multiple context values
myapp[production.main]>
```

**Custom Prompt Generation:**

The prompt shows context values in sorted order, joined by dots.

```python
context.set("env", "prod")
context.set("region", "us-east")
# Prompt: myapp[prod.us-east]>
```

### Context in Commands

```python
class ContextAwareCommands(BaseCommand):
    def register_commands(self):
        return {
            "connect": CommandMetadata(
                name="connect",
                description="Connect to instance",
                usage="connect [instance]",
                args=[
                    ArgumentSpec(
                        name="instance",
                        arg_type="string",
                        required=False,
                        context_key="instance"  # Fallback to context
                    )
                ]
            ),
            "show": CommandMetadata(
                name="show",
                description="Show current context",
                usage="show"
            ),
            "clear": CommandMetadata(
                name="clear",
                description="Clear context",
                usage="clear [key]"
            )
        }

    def execute(self, command, args):
        if command == "connect":
            # Resolve from args or context
            instance = self.context.resolve_argument(
                args[0] if args else None,
                "instance"
            )
            self.context.set("instance", instance)
            print(f"Connected to {instance}")

        elif command == "show":
            ctx = self.context.get_all()
            if ctx:
                for key, value in ctx.items():
                    print(f"{key}: {value}")
            else:
                print("No context set")

        elif command == "clear":
            if args:
                self.context.clear(args[0])
                print(f"Cleared: {args[0]}")
            else:
                self.context.clear()
                print("Cleared all context")
```

**Usage:**

```
myapp> connect production
Connected to production

myapp[production]> show
instance: production

myapp[production]> connect test
Connected to test

myapp[test]> clear instance
Cleared: instance

myapp> clear
Cleared all context
```

---

## Tab Completion

Intelligent tab completion for commands and arguments.

### How It Works

The `CompletionHandler` provides context-aware completion:

1. **Command Groups** - Complete group names, aliases, built-in commands
2. **Subcommands** - Complete subcommands within groups
3. **Arguments** - Complete based on ArgumentSpec (choices, custom functions)

### Built-in Completion

**Command completion** is automatic:

```
myapp> d<TAB>
db    docker    deploy

myapp> db <TAB>
list    create    delete    connect

myapp> help <TAB>
db    docker    deploy    aliases
```

### Custom Completion Functions

Define custom completion logic for arguments:

```python
# Completion function signature
def complete_instances(text: str, context: ContextManager) -> List[str]:
    """
    Custom completion function.

    Parameters
    ----------
    text : str
        Current text being completed
    context : ContextManager
        Access to current context

    Returns
    -------
    List[str]
        List of matching completions
    """
    instances = ["prod", "test", "dev", "staging"]
    return [i for i in instances if i.startswith(text)]

# Use in ArgumentSpec
ArgumentSpec(
    name="instance",
    arg_type="string",
    required=True,
    completion_func=complete_instances  # Custom completion
)
```

**Advanced Example:**

```python
class DatabaseCommands(BaseCommand):
    def __init__(self, context_manager):
        super().__init__(context_manager)
        self.db_client = DatabaseClient()

    def _complete_databases(self, text, context):
        """Complete database names from current instance."""
        instance = context.get("instance")
        if not instance:
            return []

        # Fetch real database names
        databases = self.db_client.list_databases(instance)
        return [db for db in databases if db.startswith(text)]

    def _complete_tables(self, text, context):
        """Complete table names from current database."""
        instance = context.get("instance")
        database = context.get("database")
        if not instance or not database:
            return []

        tables = self.db_client.list_tables(instance, database)
        return [t for t in tables if t.startswith(text)]

    def register_commands(self):
        return {
            "use": CommandMetadata(
                name="use",
                description="Switch database",
                usage="use <database>",
                args=[
                    ArgumentSpec(
                        name="database",
                        arg_type="database",
                        required=True,
                        completion_func=self._complete_databases
                    )
                ]
            ),
            "describe": CommandMetadata(
                name="describe",
                description="Describe table schema",
                usage="describe <table>",
                args=[
                    ArgumentSpec(
                        name="table",
                        arg_type="string",
                        required=True,
                        completion_func=self._complete_tables
                    )
                ]
            )
        }
```

**Usage:**

```
myapp[prod]> db use <TAB>
main    test    analytics    logs

myapp[prod.main]> db describe <TAB>
users    orders    products    invoices
```

### Choices-Based Completion

For fixed choices, use the `choices` parameter:

```python
ArgumentSpec(
    name="format",
    arg_type="string",
    required=False,
    choices=["json", "yaml", "csv", "xml"],  # Fixed choices
    description="Output format"
)
```

```
myapp> export --format <TAB>
json    yaml    csv    xml
```

### Disabling Completion

```python
# Disable globally
app = CLIApplication("myapp", version="1.0", enable_completion=False)
```

---

## Output Formatting

Professional output formatting with `OutputFormatter`.

### Basic Formatting

```python
from basefunctions.cli import show_header, show_progress, show_result

# Show operation header
show_header("Database Migration Tool")

# Show progress steps
show_progress("Connecting to database...")
show_progress("Running migration scripts...")
show_progress("Updating schema version...")

# Show final result
show_result("Migration completed successfully", success=True, details={
    "Scripts executed": 5,
    "Duration": "2.3s",
    "Version": "1.5.0"
})
```

**Output:**

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ Database Migration Tool                                                      │
└──────────────────────────────────────────────────────────────────────────────┘
  → Connecting to database...
  → Running migration scripts...
  → Updating schema version...
┌──────────────────────────────────────────────────────────────────────────────┐
│ ✓ SUCCESS: Migration completed successfully (2.3s)                           │
│   Scripts executed: 5                                                        │
│   Duration: 2.3s                                                             │
│   Version: 1.5.0                                                             │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Error Formatting

```python
try:
    # ... operation ...
    show_result("Operation completed", success=True)
except Exception as e:
    show_result(f"Operation failed: {str(e)}", success=False, details={
        "Error type": type(e).__name__,
        "Suggestion": "Check logs for details"
    })
```

**Output:**

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ ✗ ERROR: Operation failed: Connection timeout (5.1s)                         │
│   Error type: TimeoutError                                                   │
│   Suggestion: Check logs for details                                         │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Using OutputFormatter Class

```python
from basefunctions.cli import OutputFormatter

formatter = OutputFormatter()

formatter.show_header("Data Export Tool")
formatter.show_progress("Loading data...")
formatter.show_progress("Processing records...")
formatter.show_result("Export completed", success=True, details={
    "Records": 1000,
    "File": "export.csv"
})
```

### In Commands

```python
from basefunctions.cli import show_header, show_progress, show_result

class ExportCommands(BaseCommand):
    def execute(self, command, args):
        if command == "export":
            show_header("Data Export")

            show_progress("Connecting to database...")
            # ... connect ...

            show_progress("Fetching records...")
            # ... fetch ...

            show_progress("Writing to file...")
            # ... write ...

            show_result("Export completed", success=True, details={
                "Records": 1500,
                "Output": "data.csv",
                "Size": "2.5 MB"
            })
```

---

## Progress Tracking

Long-running operations can show progress bars.

### Using AliveProgressTracker

```python
from basefunctions.cli import AliveProgressTracker

# With context manager (recommended)
with AliveProgressTracker(total=100, desc="Processing") as progress:
    for i in range(100):
        # ... do work ...
        progress.progress(1)  # Advance by 1 step

# Manual usage
progress = AliveProgressTracker(total=100, desc="Processing")
for i in range(100):
    # ... do work ...
    progress.progress(1)
progress.close()
```

**Output:**

```
Processing |███████████████████████████| 100/100
```

### Unknown Total

```python
# For unknown total, omit 'total' parameter
with AliveProgressTracker(desc="Downloading") as progress:
    while has_more_data():
        chunk = fetch_chunk()
        process(chunk)
        progress.progress(1)  # Just count iterations
```

### Multi-Step Progress

```python
with AliveProgressTracker(total=1000, desc="Migrating records") as progress:
    for record in records:
        migrate(record)
        progress.progress(1)

    # Can advance by multiple steps
    progress.progress(10)  # Advance by 10
```

### In Commands

```python
from basefunctions.cli import AliveProgressTracker

class DataCommands(BaseCommand):
    def execute(self, command, args):
        if command == "migrate":
            records = fetch_records()

            with AliveProgressTracker(total=len(records), desc="Migrating") as progress:
                for record in records:
                    migrate_record(record)
                    progress.progress(1)

            print("Migration completed!")
```

### Custom Progress Tracker

Implement your own progress tracker:

```python
from basefunctions.cli import ProgressTracker

class CustomProgressTracker(ProgressTracker):
    def __init__(self, total=None, desc=""):
        self.total = total
        self.desc = desc
        self.current = 0

    def progress(self, n=1):
        self.current += n
        percent = (self.current / self.total * 100) if self.total else 0
        print(f"{self.desc}: {percent:.1f}% ({self.current}/{self.total})")

    def close(self):
        print(f"{self.desc}: Complete!")

# Use custom tracker
with CustomProgressTracker(total=100, desc="Processing") as progress:
    for i in range(100):
        # ... work ...
        progress.progress(1)
```

---

## Best Practices

### 1. Command Design

**DO:**
- Use clear, descriptive command names (`connect`, not `conn`)
- Group related commands (`db connect`, `db list`)
- Provide helpful descriptions and examples
- Make common operations easy (root-level or aliases)

**DON'T:**
- Use cryptic abbreviations
- Create deep hierarchies (max 2 levels recommended)
- Duplicate command names across groups
- Require too many arguments

### 2. Error Handling

```python
class SafeCommands(BaseCommand):
    def execute(self, command, args):
        try:
            # Validate arguments
            if command == "process" and len(args) < 1:
                print("Error: filename required")
                print("Usage: process <filename>")
                return

            # Perform operation
            result = self.process_file(args[0])

            # Show success
            print(f"Processed: {result}")

        except FileNotFoundError:
            # Specific error with helpful message
            print(f"Error: File '{args[0]}' not found")
            print("Hint: Check the file path")

        except PermissionError:
            print(f"Error: Permission denied for '{args[0]}'")
            print("Hint: Check file permissions")

        except Exception as e:
            # Generic error handler
            self._handle_error(command, e)
```

### 3. User Confirmation

```python
def execute(self, command, args):
    if command == "delete-all":
        # Dangerous operations should require confirmation
        if not self._confirm_action("Delete all data? This cannot be undone!"):
            print("Cancelled")
            return

        # ... perform deletion ...
        print("All data deleted")
```

### 4. Context Usage

```python
# Set context when it makes sense
def execute(self, command, args):
    if command == "connect":
        instance = args[0]
        self.context.set("instance", instance)
        print(f"Connected to {instance}")

    elif command == "disconnect":
        self.context.clear("instance")
        print("Disconnected")

    elif command == "query":
        # Use context if available
        instance = self.context.get("instance")
        if not instance:
            print("Error: Not connected to any instance")
            print("Hint: Use 'connect <instance>' first")
            return

        # ... perform query ...
```

### 5. Help Documentation

```python
# Always provide comprehensive metadata
CommandMetadata(
    name="export",
    description="Export data to file",  # Clear description
    usage="export <format> [filename]",  # Show syntax
    args=[
        ArgumentSpec(
            name="format",
            arg_type="string",
            required=True,
            choices=["json", "csv", "xml"],
            description="Output format"  # Explain each arg
        ),
        ArgumentSpec(
            name="filename",
            arg_type="file",
            required=False,
            description="Output filename (default: export.<format>)"
        )
    ],
    examples=[  # Provide realistic examples
        "export json",
        "export csv data.csv",
        "export xml output.xml"
    ]
)
```

### 6. Logging

```python
class LoggingCommands(BaseCommand):
    def execute(self, command, args):
        # Log important operations
        self.logger.info(f"executing command: {command} with args: {args}")

        try:
            # ... perform operation ...
            self.logger.info(f"command '{command}' completed successfully")

        except Exception as e:
            # Log errors
            self.logger.error(f"command '{command}' failed: {str(e)}")
            raise
```

### 7. Aliases

```python
# Create aliases for frequently used commands
app.register_alias("ls", "list")
app.register_alias("st", "status")
app.register_alias("conn", "db connect")
app.register_alias("q", "quit")

# User can now use:
# myapp> ls         (instead of "list")
# myapp> conn prod  (instead of "db connect prod")
```

### 8. Testing Commands

```python
# Commands should be testable
class TestableCommands(BaseCommand):
    def __init__(self, context_manager, client=None):
        super().__init__(context_manager)
        self.client = client or RealClient()  # Dependency injection

    def execute(self, command, args):
        # Business logic separated for testing
        if command == "fetch":
            result = self._fetch_data(args[0])
            print(result)

    def _fetch_data(self, id):
        # Testable business logic
        return self.client.fetch(id)

# In tests:
mock_client = MockClient()
commands = TestableCommands(context, client=mock_client)
commands.execute("fetch", ["123"])
```

---

## Complete Examples

### Example 1: File Manager CLI

```python
from basefunctions.cli import (
    CLIApplication, BaseCommand, CommandMetadata, ArgumentSpec,
    show_header, show_progress, show_result
)
import os
import shutil

class FileCommands(BaseCommand):
    def register_commands(self):
        return {
            "list": CommandMetadata(
                name="list",
                description="List files in directory",
                usage="list [directory]",
                args=[
                    ArgumentSpec(
                        name="directory",
                        arg_type="file",
                        required=False,
                        description="Directory to list (default: current)"
                    )
                ],
                examples=["list", "list /path/to/dir"]
            ),
            "copy": CommandMetadata(
                name="copy",
                description="Copy file or directory",
                usage="copy <source> <destination>",
                args=[
                    ArgumentSpec(name="source", arg_type="file", required=True),
                    ArgumentSpec(name="destination", arg_type="file", required=True)
                ],
                examples=["copy file.txt backup.txt", "copy dir1 dir2"]
            ),
            "delete": CommandMetadata(
                name="delete",
                description="Delete file or directory",
                usage="delete <path>",
                args=[
                    ArgumentSpec(name="path", arg_type="file", required=True)
                ],
                examples=["delete old_file.txt", "delete temp_dir"]
            ),
            "info": CommandMetadata(
                name="info",
                description="Show file information",
                usage="info <path>",
                args=[
                    ArgumentSpec(name="path", arg_type="file", required=True)
                ]
            )
        }

    def execute(self, command, args):
        try:
            if command == "list":
                self._list_files(args)
            elif command == "copy":
                self._copy_file(args)
            elif command == "delete":
                self._delete_file(args)
            elif command == "info":
                self._show_info(args)
        except Exception as e:
            self._handle_error(command, e)

    def _list_files(self, args):
        directory = args[0] if args else "."

        if not os.path.exists(directory):
            print(f"Error: Directory '{directory}' not found")
            return

        files = os.listdir(directory)
        if files:
            print(f"Files in {directory}:")
            for f in sorted(files):
                path = os.path.join(directory, f)
                type_str = "DIR " if os.path.isdir(path) else "FILE"
                print(f"  [{type_str}] {f}")
        else:
            print(f"Directory '{directory}' is empty")

    def _copy_file(self, args):
        if len(args) < 2:
            print("Error: source and destination required")
            return

        source, dest = args[0], args[1]

        if not os.path.exists(source):
            print(f"Error: Source '{source}' not found")
            return

        show_header(f"Copy: {source} → {dest}")
        show_progress("Copying...")

        try:
            if os.path.isdir(source):
                shutil.copytree(source, dest)
            else:
                shutil.copy2(source, dest)

            show_result("Copy completed", success=True, details={
                "Source": source,
                "Destination": dest,
                "Size": f"{os.path.getsize(dest)} bytes"
            })
        except Exception as e:
            show_result(f"Copy failed: {str(e)}", success=False)

    def _delete_file(self, args):
        if not args:
            print("Error: path required")
            return

        path = args[0]

        if not os.path.exists(path):
            print(f"Error: '{path}' not found")
            return

        # Require confirmation
        if not self._confirm_action(f"Delete '{path}'?"):
            print("Cancelled")
            return

        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
            print(f"Deleted: {path}")
        except Exception as e:
            print(f"Error: {str(e)}")

    def _show_info(self, args):
        if not args:
            print("Error: path required")
            return

        path = args[0]

        if not os.path.exists(path):
            print(f"Error: '{path}' not found")
            return

        stat = os.stat(path)
        file_type = "Directory" if os.path.isdir(path) else "File"

        print(f"Path: {path}")
        print(f"Type: {file_type}")
        print(f"Size: {stat.st_size} bytes")
        print(f"Modified: {stat.st_mtime}")

def main():
    app = CLIApplication("filemgr", version="1.0")
    app.register_command_group("", FileCommands(app.context))
    app.run()

if __name__ == "__main__":
    main()
```

### Example 2: Database Manager CLI

```python
from basefunctions.cli import (
    CLIApplication, BaseCommand, CommandMetadata, ArgumentSpec,
    show_header, show_progress, show_result
)

class ConnectionCommands(BaseCommand):
    def __init__(self, context_manager):
        super().__init__(context_manager)
        self.connections = {}  # Store active connections

    def register_commands(self):
        return {
            "connect": CommandMetadata(
                name="connect",
                description="Connect to database instance",
                usage="connect <instance> [database]",
                args=[
                    ArgumentSpec(
                        name="instance",
                        arg_type="string",
                        required=True,
                        context_key="instance",
                        choices=["prod", "test", "dev"],
                        description="Instance name"
                    ),
                    ArgumentSpec(
                        name="database",
                        arg_type="string",
                        required=False,
                        context_key="database",
                        description="Database name"
                    )
                ],
                examples=["connect prod", "connect test main"]
            ),
            "disconnect": CommandMetadata(
                name="disconnect",
                description="Disconnect from current instance",
                usage="disconnect"
            ),
            "status": CommandMetadata(
                name="status",
                description="Show connection status",
                usage="status"
            )
        }

    def execute(self, command, args):
        if command == "connect":
            self._connect(args)
        elif command == "disconnect":
            self._disconnect()
        elif command == "status":
            self._status()

    def _connect(self, args):
        if not args:
            print("Error: instance required")
            return

        instance = args[0]
        database = args[1] if len(args) > 1 else "default"

        show_header(f"Connecting to {instance}.{database}")
        show_progress("Establishing connection...")

        # Simulate connection
        import time
        time.sleep(1)

        self.connections[instance] = database
        self.context.set("instance", instance)
        self.context.set("database", database)

        show_result("Connected successfully", success=True, details={
            "Instance": instance,
            "Database": database
        })

    def _disconnect(self):
        instance = self.context.get("instance")
        if not instance:
            print("Not connected to any instance")
            return

        del self.connections[instance]
        self.context.clear()
        print(f"Disconnected from {instance}")

    def _status(self):
        if self.connections:
            print("Active connections:")
            for inst, db in self.connections.items():
                print(f"  {inst}.{db}")
        else:
            print("No active connections")

class QueryCommands(BaseCommand):
    def register_commands(self):
        return {
            "select": CommandMetadata(
                name="select",
                description="Execute SELECT query",
                usage="select <table> [where]",
                args=[
                    ArgumentSpec(name="table", arg_type="string", required=True),
                    ArgumentSpec(name="where", arg_type="string", required=False)
                ],
                examples=["select users", "select users 'id=1'"]
            ),
            "tables": CommandMetadata(
                name="tables",
                description="List all tables",
                usage="tables"
            )
        }

    def execute(self, command, args):
        # Check connection
        if not self.context.get("instance"):
            print("Error: Not connected to any instance")
            print("Hint: Use 'connect <instance>' first")
            return

        if command == "select":
            self._select(args)
        elif command == "tables":
            self._tables()

    def _select(self, args):
        if not args:
            print("Error: table name required")
            return

        table = args[0]
        where = args[1] if len(args) > 1 else None

        instance = self.context.get("instance")
        database = self.context.get("database")

        query = f"SELECT * FROM {table}"
        if where:
            query += f" WHERE {where}"

        print(f"Executing: {query}")
        print(f"On: {instance}.{database}")
        print("\nResults:")
        print("  id | name        | email")
        print("  ---+-------------+------------------")
        print("   1 | John Doe    | john@example.com")
        print("   2 | Jane Smith  | jane@example.com")

    def _tables(self):
        instance = self.context.get("instance")
        database = self.context.get("database")

        print(f"Tables in {instance}.{database}:")
        for table in ["users", "orders", "products", "invoices"]:
            print(f"  - {table}")

def main():
    app = CLIApplication("dbmgr", version="1.0")

    # Register command groups
    app.register_command_group("", ConnectionCommands(app.context))
    app.register_command_group("query", QueryCommands(app.context))

    # Register aliases
    app.register_alias("conn", "connect")
    app.register_alias("disco", "disconnect")
    app.register_alias("st", "status")

    app.run()

if __name__ == "__main__":
    main()
```

**Usage:**

```
dbmgr v1.0
Type 'help' for commands or 'quit' to exit

dbmgr> conn prod
┌──────────────────────────────────────────────────────────────────────────────┐
│ Connecting to prod.default                                                   │
└──────────────────────────────────────────────────────────────────────────────┘
  → Establishing connection...
┌──────────────────────────────────────────────────────────────────────────────┐
│ ✓ SUCCESS: Connected successfully (1.0s)                                     │
│   Instance: prod                                                             │
│   Database: default                                                          │
└──────────────────────────────────────────────────────────────────────────────┘

dbmgr[prod.default]> query tables
Tables in prod.default:
  - users
  - orders
  - products
  - invoices

dbmgr[prod.default]> query select users
Executing: SELECT * FROM users
On: prod.default

Results:
  id | name        | email
  ---+-------------+------------------
   1 | John Doe    | john@example.com
   2 | Jane Smith  | jane@example.com

dbmgr[prod.default]> disco
Disconnected from prod

dbmgr> quit
Goodbye!
```

---

## API Reference

### CLIApplication

```python
class CLIApplication:
    """Main CLI application orchestrator."""

    def __init__(self, app_name: str, version: str = "1.0", enable_completion: bool = True):
        """
        Initialize CLI application.

        Parameters
        ----------
        app_name : str
            Application name
        version : str
            Application version
        enable_completion : bool
            Enable tab completion (default: True)
        """

    def register_command_group(self, group_name: str, handler: BaseCommand) -> None:
        """
        Register command group.

        Parameters
        ----------
        group_name : str
            Group name (empty string for root-level)
        handler : BaseCommand
            Command handler instance
        """

    def register_alias(self, alias: str, target: str) -> None:
        """
        Register command alias.

        Parameters
        ----------
        alias : str
            Alias name
        target : str
            Target command (format: "group command" or "command")
        """

    def run(self) -> None:
        """Run interactive CLI main loop."""
```

### BaseCommand

```python
class BaseCommand(ABC):
    """Abstract base class for CLI command groups."""

    def __init__(self, context_manager: ContextManager):
        """
        Initialize base command.

        Parameters
        ----------
        context_manager : ContextManager
            Shared context manager instance
        """

    @abstractmethod
    def register_commands(self) -> Dict[str, CommandMetadata]:
        """
        Register available commands with metadata.

        Returns
        -------
        Dict[str, CommandMetadata]
            Command name to metadata mapping
        """

    @abstractmethod
    def execute(self, command: str, args: List[str]) -> None:
        """
        Execute specific command.

        Parameters
        ----------
        command : str
            Command name
        args : List[str]
            Command arguments
        """

    def get_available_commands(self) -> List[str]:
        """Get list of available commands."""

    def get_command_metadata(self, command: str) -> CommandMetadata:
        """Get metadata for specific command."""

    def validate_command(self, command: str) -> bool:
        """Validate if command exists."""

    def get_help(self, command: str = None) -> str:
        """Generate help text."""

    def _confirm_action(self, message: str) -> bool:
        """Get user confirmation (y/N)."""

    def _handle_error(self, command: str, error: Exception) -> None:
        """Handle command execution error."""
```

### CommandMetadata

```python
@dataclass
class CommandMetadata:
    """Command metadata for registration and execution."""

    name: str                           # Command name
    description: str                    # Command description
    usage: str                          # Usage string
    args: List[ArgumentSpec] = []       # Command arguments
    examples: List[str] = []            # Usage examples
    requires_context: bool = False      # Whether command requires context
    context_keys: Optional[List[str]] = None  # Required context keys
    aliases: List[str] = []             # Command aliases

    def get_required_args(self) -> List[ArgumentSpec]:
        """Get required arguments."""

    def get_optional_args(self) -> List[ArgumentSpec]:
        """Get optional arguments."""

    def validate_args_count(self, provided_count: int) -> bool:
        """Validate argument count."""
```

### ArgumentSpec

```python
@dataclass
class ArgumentSpec:
    """Argument specification for commands."""

    name: str                               # Argument name
    arg_type: str                           # Type of argument
    required: bool = True                   # Whether argument is required
    context_key: Optional[str] = None       # Context key for fallback
    choices: Optional[List[str]] = None     # Valid choices
    completion_func: Optional[Callable] = None  # Custom completion
    description: str = ""                   # Argument description
```

### ContextManager

```python
class ContextManager:
    """Generic context manager for CLI applications."""

    def __init__(self, app_name: str = "cli"):
        """Initialize context manager."""

    def set(self, key: str, value: Any) -> None:
        """Set context value."""

    def get(self, key: str, default: Any = None) -> Any:
        """Get context value."""

    def clear(self, key: Optional[str] = None) -> None:
        """Clear context (specific key or all)."""

    def has(self, key: str) -> bool:
        """Check if context key exists."""

    def get_all(self) -> Dict[str, Any]:
        """Get all context values."""

    def get_prompt(self) -> str:
        """Generate context-aware prompt."""

    def resolve_argument(self, arg: Optional[str], context_key: str) -> str:
        """Resolve argument with context fallback."""

    def resolve_target(self, arg: Optional[str], primary_key: str, secondary_key: str) -> Tuple[str, str]:
        """Resolve compound target (e.g., instance.database)."""
```

### ArgumentParser

```python
class ArgumentParser:
    """Command line argument parser."""

    @staticmethod
    def parse_command(command_line: str) -> Tuple[Optional[str], Optional[str], List[str]]:
        """
        Parse command line into components.

        Returns
        -------
        Tuple[Optional[str], Optional[str], List[str]]
            (command_group, subcommand, args)
        """

    @staticmethod
    def validate_args(metadata: CommandMetadata, args: List[str]) -> bool:
        """Validate arguments against metadata."""

    @staticmethod
    def resolve_argument_with_context(
        arg: Optional[str],
        arg_spec: ArgumentSpec,
        context_manager: ContextManager
    ) -> Optional[str]:
        """Resolve argument with context fallback."""

    @staticmethod
    def split_compound_argument(arg: str) -> Tuple[str, Optional[str]]:
        """Split compound argument (e.g., 'instance.database')."""
```

### OutputFormatter

```python
class OutputFormatter:
    """Thread-safe formatter for CLI tool output."""

    def show_header(self, title: str) -> None:
        """Show formatted header."""

    def show_progress(self, message: str) -> None:
        """Show formatted progress message."""

    def show_result(self, message: str, success: bool = True, details: Optional[dict] = None) -> None:
        """Show formatted result summary."""

# Convenience functions
def show_header(title: str) -> None:
    """Show formatted header."""

def show_progress(message: str) -> None:
    """Show formatted progress message."""

def show_result(message: str, success: bool = True, details: Optional[dict] = None) -> None:
    """Show formatted result summary."""
```

### CompletionHandler

```python
class CompletionHandler:
    """Tab completion handler for CLI commands."""

    def __init__(self, registry: CommandRegistry, context: ContextManager):
        """Initialize completion handler."""

    def complete(self, text: str, state: int) -> Optional[str]:
        """Main completion handler for readline."""

    def setup(self) -> None:
        """Setup readline with tab completion."""

    def cleanup(self) -> None:
        """Save readline history on exit."""
```

### ProgressTracker

```python
class ProgressTracker(ABC):
    """Abstract base class for progress tracking."""

    @abstractmethod
    def progress(self, n: int = 1) -> None:
        """Advance progress by n steps."""

    @abstractmethod
    def close(self) -> None:
        """Close progress tracker and cleanup resources."""

class AliveProgressTracker(ProgressTracker):
    """Progress tracker using alive-progress."""

    def __init__(self, total: Optional[int] = None, desc: str = "Processing"):
        """
        Initialize alive-progress progress tracker.

        Parameters
        ----------
        total : Optional[int]
            Expected total number of steps
        desc : str
            Description shown in progress bar
        """
```

---

## Summary

The `basefunctions.cli` framework provides everything you need to build professional command-line applications:

**Core Features:**
- Command groups and hierarchies
- Intelligent argument parsing
- Tab completion
- Context management
- Help system
- Output formatting
- Progress tracking

**Design Principles:**
- Easy to learn and use
- Minimal boilerplate
- Professional UX
- Extensible and testable

**Getting Started:**
1. Create `BaseCommand` subclasses
2. Register commands with `CommandMetadata`
3. Implement `execute()` method
4. Register with `CLIApplication`
5. Run with `app.run()`

**Next Steps:**
- Study the complete examples
- Review the API reference
- Build your own CLI application
- Contribute improvements

**Resources:**
- Source code: `/Users/neutro2/Code/neuraldev/basefunctions/src/basefunctions/cli/`
- Project docs: `CLAUDE.md`
- Package info: `pyproject.toml`

---

**Questions or Issues?**

For support, check the basefunctions documentation or contact the development team.

**Happy CLI building!**
