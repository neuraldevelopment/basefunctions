# config - User Documentation

**Package:** basefunctions
**Subpackage:** config
**Purpose:** App-controlled JSON configuration with automatic package defaults

---

## Overview

The `config` subpackage provides JSON-based configuration management following a clear
separation of roles:

- **Apps** load their config file explicitly via `load_config_file`
- **Packages** register their default config at import time via `register_package_defaults`
- **All code** reads parameters via `get_config_parameter` or `get_config_for_package`

**Key Features:**
- Single `ConfigHandler` singleton shared across the entire process
- Deep-merge: App config overrides package defaults without destroying nested keys
- Self-Registration Pattern: package defaults are available immediately after import
- Thread-safe: safe to use from concurrent threads (event system, timers)

**Common Use Cases:**
- App startup: load a single JSON config that overrides package defaults
- Library authoring: register default config values that apps can override
- Runtime reads: access any config parameter by slash-separated path

---

## Quickstart: App Developer

```python
from basefunctions import ConfigHandler

# Step 1: Import packages — defaults registered automatically
import tickerhub   # registers tickerhub defaults at import time

# Step 2: Load your app config (overrides specific values)
ConfigHandler().load_config_file("/path/to/app-config.json")

# Step 3: Read parameters anywhere in your code
host = ConfigHandler().get_config_parameter("tickerhub/database/host")
port = ConfigHandler().get_config_parameter("tickerhub/database/port", default_value=5432)

# Or read a full section
db_config = ConfigHandler().get_config_for_package("tickerhub")
```

---

## Quickstart: Package Author

Register your defaults in `__init__.py` so they are available as soon as your package
is imported:

```python
# mypackage/__init__.py
from basefunctions import ConfigHandler
from basefunctions.runtime import get_runtime_config_path

ConfigHandler().register_package_defaults(
    "mypackage",
    get_runtime_config_path("mypackage")
)
```

Then place your defaults at `config/config.json` in your package directory:

```json
{
  "mypackage": {
    "database": {
      "host": "localhost",
      "port": 5432
    },
    "logging": {
      "level": "INFO"
    }
  }
}
```

If `config/config.json` does not exist, `register_package_defaults` does nothing silently.
Your package works even in environments where no config file is deployed.

---

## Config File Format

All config files are JSON. Top-level keys are package names. Nesting is unrestricted.

```json
{
  "mypackage": {
    "database": {
      "host": "localhost",
      "port": 5432,
      "name": "mydb"
    },
    "logging": {
      "level": "DEBUG"
    }
  },
  "otherapackage": {
    "timeout": 30
  }
}
```

The config file must:
- Have a `.json` extension
- Parse as a JSON object (dict) at root level

---

## Public API

### `ConfigHandler().load_config_file`

```python
def load_config_file(file_path: str) -> None
```

Load a JSON config file and deep-merge it into the current config.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `file_path` | `str` | Absolute path to a `.json` config file |

**Returns:** `None`

**Raises:**

| Exception | When |
|-----------|------|
| `ValueError` | Path does not end with `.json` |
| `ValueError` | JSON root is not a dict |
| `FileNotFoundError` | File does not exist |
| `json.JSONDecodeError` | File contains invalid JSON |

**Example:**
```python
from basefunctions import ConfigHandler

ConfigHandler().load_config_file("/etc/myapp/config.json")
```

---

### `ConfigHandler().register_package_defaults`

```python
def register_package_defaults(package_name: str, config_path: str | Path) -> None
```

Register package default configuration by loading `config/config.json` from the given
directory. Silent when missing.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `package_name` | `str` | Package name (logging identifier only) |
| `config_path` | `str | Path` | Directory containing `config.json` |

**Returns:** `None`

**Raises:** Never raises. Logs DEBUG if file missing, WARNING on parse error.

**Example:**
```python
from basefunctions import ConfigHandler
from basefunctions.runtime import get_runtime_config_path

ConfigHandler().register_package_defaults(
    "mypackage",
    get_runtime_config_path("mypackage")
)
```

---

### `ConfigHandler().get_config_for_package`

```python
def get_config_for_package(package: str | None = None) -> dict[str, Any]
```

Get the config section for a package, or the entire config if `package=None`.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `package` | `str | None` | `None` | Package name key; `None` returns full config |

**Returns:** `dict[str, Any]` — copy of the config section. Empty dict if not found.

**Example:**
```python
from basefunctions import ConfigHandler

# Get one package section
db_config = ConfigHandler().get_config_for_package("mypackage")
print(db_config)  # {"database": {"host": "localhost", "port": 5432}, ...}

# Get everything
all_config = ConfigHandler().get_config_for_package()
```

---

### `ConfigHandler().get_config_parameter`

```python
def get_config_parameter(path: str, default_value: Any = None) -> Any
```

Read a single config value by slash-separated path.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `path` | `str` | — | Slash-separated path, e.g. `"mypackage/database/host"` |
| `default_value` | `Any` | `None` | Returned if path not found |

**Returns:** The value at the path, or `default_value` if any key is missing.

**Example:**
```python
from basefunctions import ConfigHandler

host = ConfigHandler().get_config_parameter("mypackage/database/host", "localhost")
level = ConfigHandler().get_config_parameter("mypackage/logging/level", "INFO")
timeout = ConfigHandler().get_config_parameter("mypackage/timeout", 30)
```

---

## Error Handling

```python
from basefunctions import ConfigHandler
import json

try:
    ConfigHandler().load_config_file("/path/to/config.json")
except FileNotFoundError as e:
    print(f"Config file not found: {e}")
    # Use defaults or exit
except json.JSONDecodeError as e:
    print(f"Invalid JSON in config: {e}")
    # Fix the config file
except ValueError as e:
    print(f"Invalid config: {e}")
    # Wrong file type or format
```

**Note:** `register_package_defaults` never raises — errors are logged only.

---

## Best Practices

**Call `load_config_file` once at startup, before your app logic runs.**
All singleton reads will see the merged result from that point on.

```python
# GOOD: Load early
from basefunctions import ConfigHandler
import mypackage  # registers defaults

ConfigHandler().load_config_file("/etc/myapp/config.json")
# Now start your app
```

**Use `get_config_parameter` for scalar values, `get_config_for_package` for sections.**

---

## See Also

**Related Subpackages:**
- `secret` (`docs/basefunctions/secret.md`) - Credential management via SecretHandler

**System Documentation:**
- `~/.claude/_docs/python/basefunctions/config.md` - Internal architecture, merge algorithm, thread safety

---

**Document Version:** 1.0.0
**Last Updated:** 2026-03-23
