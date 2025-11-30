# Config Module Guide

**Comprehensive Documentation for basefunctions Configuration & Secrets Management**

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [ConfigHandler](#confighandler)
4. [SecretHandler](#secrethandler)
5. [Configuration Structure](#configuration-structure)
6. [Package-Specific Configs](#package-specific-configs)
7. [Environment Variables](#environment-variables)
8. [Use Cases](#use-cases)
9. [Best Practices](#best-practices)
10. [API Reference](#api-reference)

---

## Overview

The `basefunctions.config` module provides a unified, thread-safe system for managing application configurations and secrets. It consists of two main components:

### **ConfigHandler**
- **Purpose**: Centralized JSON-based configuration management
- **Pattern**: Thread-safe singleton
- **Scope**: Multi-package support with single config file
- **Features**:
  - Path-based parameter access
  - Auto-loading for packages
  - Template-based initialization
  - Bootstrap and deployment support

### **SecretHandler**
- **Purpose**: Secure credentials and sensitive data management
- **Pattern**: Thread-safe singleton
- **Scope**: Environment variable integration
- **Features**:
  - .env file loading
  - Dict-style access
  - Default value support
  - Home directory standard

### **Key Design Principles**

1. **Single Config File**: One `config.json` contains all package configurations
2. **Separation of Concerns**: Public config vs. sensitive secrets
3. **Thread Safety**: RLock-based synchronization for EventBus compatibility
4. **Bootstrap First**: Self-contained initialization to break circular dependencies
5. **Package Isolation**: Each package has its own section in config

---

## Architecture

### **Module Structure**

```
basefunctions/
├── config/
│   ├── __init__.py           # Public API exports
│   ├── config_handler.py     # ConfigHandler class
│   └── secret_handler.py     # SecretHandler class
├── runtime/
│   └── runtime_functions.py  # Path resolution functions
└── templates/
    └── config/
        └── config.json       # Default template
```

### **Runtime Directory Structure**

When a package is initialized, the following structure is created:

```
~/.neuraldevelopment/          # Default deployment directory
└── basefunctions/             # Package-specific directory
    ├── config/
    │   └── config.json        # Active configuration
    ├── logs/                  # Log files
    └── templates/
        └── config/
            └── config.json    # Configuration template
```

### **Configuration Lifecycle**

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Package Import                                           │
│    import basefunctions                                     │
└────────────────┬────────────────────────────────────────────┘
                 │
                 v
┌─────────────────────────────────────────────────────────────┐
│ 2. ConfigHandler Initialization (Singleton)                 │
│    - Create RLock for thread safety                         │
│    - Initialize empty config dict                           │
│    - Create root structure                                  │
└────────────────┬────────────────────────────────────────────┘
                 │
                 v
┌─────────────────────────────────────────────────────────────┐
│ 3. Bootstrap Package Structure                              │
│    ensure_bootstrap_package_structure("basefunctions")      │
│    - Creates: config/, templates/config/                    │
└────────────────┬────────────────────────────────────────────┘
                 │
                 v
┌─────────────────────────────────────────────────────────────┐
│ 4. Config File Loading                                      │
│    ConfigHandler().load_config_for_package("basefunctions") │
│    - Checks for config.json                                 │
│    - Creates from template if missing                       │
│    - Loads JSON into memory                                 │
└────────────────┬────────────────────────────────────────────┘
                 │
                 v
┌─────────────────────────────────────────────────────────────┐
│ 5. Full Package Structure                                   │
│    _create_full_package_structure("basefunctions")          │
│    - Reads custom directories from config                   │
│    - Creates additional directories (logs, etc.)            │
└────────────────┬────────────────────────────────────────────┘
                 │
                 v
┌─────────────────────────────────────────────────────────────┐
│ 6. Ready for Use                                            │
│    ConfigHandler().get_config_parameter("basefunctions/...") │
└─────────────────────────────────────────────────────────────┘
```

### **Thread Safety Model**

The `ConfigHandler` uses `threading.RLock()` for thread safety, allowing:
- **Reentrant locking**: Same thread can acquire lock multiple times
- **EventBus compatibility**: Works with THREAD and CORELET execution modes
- **Atomic operations**: All config reads/writes are synchronized

```python
class ConfigHandler:
    def __init__(self):
        self._lock = threading.RLock()  # Reentrant lock

    def get_config_parameter(self, path: str, default_value: Any = None) -> Any:
        with self._lock:  # Thread-safe access
            # ... parameter retrieval logic
```

---

## ConfigHandler

### **Purpose**

`ConfigHandler` is a thread-safe singleton that manages JSON-based configurations for multiple packages in a single centralized file.

### **Initialization**

```python
from basefunctions import ConfigHandler

# Get singleton instance
config = ConfigHandler()

# Auto-loaded on basefunctions import:
# ConfigHandler().load_config_for_package("basefunctions")
```

### **Core Concepts**

#### **1. Single Config File, Multiple Packages**

The `config.json` file contains sections for different packages:

```json
{
  "package_structure": {
    "directories": ["config", "logs", "templates/config"]
  },
  "basefunctions": {
    "feature_a": { "enabled": true },
    "feature_b": { "timeout": 30 }
  },
  "myapp": {
    "database": { "host": "localhost", "port": 5432 }
  }
}
```

#### **2. Path-Based Navigation**

Access nested configuration using slash-separated paths:

```python
# Get entire package config
basefunctions_config = config.get_config_for_package("basefunctions")

# Get specific parameter
timeout = config.get_config_parameter("basefunctions/feature_b/timeout")
# Returns: 30

# Get nested parameter with default
host = config.get_config_parameter("myapp/database/host", default_value="127.0.0.1")
# Returns: "localhost"

# Non-existent path returns default
missing = config.get_config_parameter("myapp/missing/value", default_value=None)
# Returns: None
```

#### **3. Bootstrap vs. Full Structure**

**Bootstrap Phase** (minimal, breaks circular dependencies):
- Creates: `config/`, `templates/config/`
- Purpose: Allow ConfigHandler to initialize without dependencies

**Full Phase** (after config loaded):
- Creates: Additional directories from config
- Purpose: Complete package structure with custom directories

```python
# Bootstrap (automatic, minimal)
ensure_bootstrap_package_structure("mypackage")
# Creates: ~/.neuraldevelopment/mypackage/config/
#          ~/.neuraldevelopment/mypackage/templates/config/

# Full structure (automatic after config load)
# Reads: package_structure/directories from config
# Creates: All specified directories
```

### **Key Methods**

#### **load_config_for_package(package_name: str)**

Load configuration for a specific package context. This is the primary entry point.

```python
config = ConfigHandler()
config.load_config_for_package("myapp")
```

**Process:**
1. Ensures bootstrap package structure exists
2. Locates config file using `get_runtime_config_path()`
3. Creates config from template if missing
4. Loads JSON into memory
5. Creates full package structure based on config

**When to use:**
- Package initialization (typically in `__init__.py`)
- First-time setup
- After deployment

#### **get_config_for_package(package: Optional[str] = None)**

Retrieve configuration for a specific package or all packages.

```python
# Get specific package config
basefunctions_cfg = config.get_config_for_package("basefunctions")
# Returns: {"feature_a": {...}, "feature_b": {...}}

# Get all configurations
all_configs = config.get_config_for_package()
# Returns: {"package_structure": {...}, "basefunctions": {...}, "myapp": {...}}
```

**Returns:** Copy of configuration (not reference) for safety.

#### **get_config_parameter(path: str, default_value: Any = None)**

Get specific parameter using path notation.

```python
# Simple path
level = config.get_config_parameter("basefunctions/logging/level", default_value="INFO")

# Nested path
dirs = config.get_config_parameter("basefunctions/prodtools/create_project/project_types/generic/directories")
# Returns: ["00-Planning", "20-Documents", ...]

# Non-existent path returns default
value = config.get_config_parameter("nonexistent/path", default_value=42)
# Returns: 42
```

**Path Syntax:**
- Use `/` to separate levels
- Case-sensitive
- Returns default if any part of path is missing

#### **create_config_from_template(package_name: str)**

Create central config.json from template or empty structure.

```python
config = ConfigHandler()
config.create_config_from_template("myapp")
```

**Process:**
1. Locates template: `~/.neuraldevelopment/myapp/templates/config/config.json`
2. Creates template if missing (empty package section)
3. Copies template to: `~/.neuraldevelopment/myapp/config/config.json`

**Template Creation:**
If template doesn't exist, creates:
```json
{
  "myapp": {}
}
```

#### **load_config_file(file_path: str)**

Load a JSON configuration file from arbitrary path.

```python
config = ConfigHandler()
config.load_config_file("/path/to/custom/config.json")
```

**Use cases:**
- Loading additional configuration files
- Testing with custom configs
- Merging multiple config sources

**Validation:**
- Must be `.json` file
- Must contain valid JSON
- Must be a dictionary at root level
- Updates existing config (merge, not replace)

### **Thread Safety**

All methods are protected with `RLock`:

```python
def get_config_parameter(self, path: str, default_value: Any = None) -> Any:
    with self._lock:  # Acquire lock
        # ... safe access to self.config
    # Lock automatically released
```

**Why RLock (Reentrant Lock)?**
- Allows same thread to acquire lock multiple times
- Needed for methods that call other locked methods
- Example: `load_config_for_package` → `_create_full_package_structure` → `get_config_parameter`

### **Integration with Runtime System**

ConfigHandler relies on runtime path functions:

```python
# Get config directory for package
config_path = basefunctions.get_runtime_config_path("myapp")
# Returns: ~/.neuraldevelopment/myapp/config

# Get template directory
template_path = basefunctions.get_runtime_template_path("myapp")
# Returns: ~/.neuraldevelopment/myapp/templates/config

# Full config file path
config_file = os.path.join(config_path, "config.json")
```

**Path Resolution Order:**
1. Check deployment directory: `~/.neuraldevelopment/`
2. Check development directories: `~/Code/`, `~/Development/`
3. Use bootstrap config for customization

---

## SecretHandler

### **Purpose**

`SecretHandler` provides secure storage and retrieval of sensitive credentials using `.env` files and environment variables.

### **Initialization**

```python
from basefunctions import SecretHandler

# Default: loads ~/.env
secrets = SecretHandler()

# Custom .env file
secrets = SecretHandler(env_file="/path/to/.env")
```

### **Core Concepts**

#### **1. .env File Format**

Standard `.env` file with KEY=VALUE pairs:

```bash
# ~/.env
DATABASE_URL=postgresql://user:pass@localhost/db
API_KEY=sk-1234567890abcdef
SECRET_TOKEN=mysecrettoken123
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

# Comments are supported
DEBUG_MODE=true

# Multi-line values (use quotes)
PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA...
-----END RSA PRIVATE KEY-----"
```

#### **2. Environment Variable Integration**

`SecretHandler` uses `python-dotenv` which:
- Loads `.env` file into environment variables
- Does NOT override existing environment variables
- Provides dict-style access via `dotenv_values()`

```python
import os

secrets = SecretHandler()

# Both return same value:
api_key_1 = secrets.get_secret_value("API_KEY")
api_key_2 = os.getenv("API_KEY")
```

#### **3. Security Best Practices**

- **Never commit .env files**: Add to `.gitignore`
- **User-specific secrets**: Store in `~/.env` (home directory)
- **Project-specific secrets**: Use `.env` in project root (gitignored)
- **Production secrets**: Use environment variables directly
- **Rotation**: Easy to update by editing `.env` file

### **Key Methods**

#### **get_secret_value(key: str, default_value: Any = None)**

Retrieve secret by key with optional default.

```python
secrets = SecretHandler()

# Get secret
api_key = secrets.get_secret_value("API_KEY")
# Returns: "sk-1234567890abcdef"

# Get with default (if missing)
debug = secrets.get_secret_value("DEBUG_MODE", default_value="false")
# Returns: "true" if exists, "false" if missing

# Missing secret returns None
missing = secrets.get_secret_value("NONEXISTENT")
# Returns: None

# Missing secret with default
port = secrets.get_secret_value("PORT", default_value="8080")
# Returns: "8080"
```

**Note:** All values from `.env` are **strings**. Convert as needed:

```python
# Boolean conversion
debug = secrets.get_secret_value("DEBUG_MODE", "false").lower() == "true"

# Integer conversion
port = int(secrets.get_secret_value("PORT", "8080"))

# JSON conversion
import json
config = json.loads(secrets.get_secret_value("JSON_CONFIG", "{}"))
```

#### **__getitem__(key: str)**

Dict-style access to secrets.

```python
secrets = SecretHandler()

# Dict-style access
api_key = secrets["API_KEY"]
# Equivalent to: secrets.get_secret_value("API_KEY")

# Returns None if missing (no KeyError)
missing = secrets["NONEXISTENT"]
# Returns: None
```

**Use case:** Clean syntax when secret is required:

```python
# Traditional
db_url = secrets.get_secret_value("DATABASE_URL")

# Dict-style
db_url = secrets["DATABASE_URL"]
```

#### **get_all_secrets()**

Retrieve all secrets as dictionary.

```python
secrets = SecretHandler()

all_secrets = secrets.get_all_secrets()
# Returns: {
#   "DATABASE_URL": "postgresql://...",
#   "API_KEY": "sk-...",
#   "SECRET_TOKEN": "...",
#   ...
# }
```

**Use cases:**
- Debugging (check what's loaded)
- Passing secrets to subprocesses
- Logging secret keys (NOT values!)

**Security Warning:**

```python
# SAFE: Log secret keys
logger.info(f"Loaded {len(secrets.get_all_secrets())} secrets")
logger.debug(f"Secret keys: {list(secrets.get_all_secrets().keys())}")

# UNSAFE: Never log secret values!
logger.debug(f"Secrets: {secrets.get_all_secrets()}")  # DON'T DO THIS!
```

### **File Location Strategy**

#### **Default Location: ~/.env**

```python
# Loads ~/.env automatically
secrets = SecretHandler()
```

**Benefits:**
- User-specific credentials
- Shared across all projects
- Easy to manage

**Typical use:** Personal API keys, shared credentials

#### **Custom Location**

```python
# Project-specific secrets
secrets = SecretHandler(env_file=".env")

# Absolute path
secrets = SecretHandler(env_file="/etc/myapp/secrets.env")

# Relative path
import os
project_root = os.path.dirname(__file__)
secrets = SecretHandler(env_file=os.path.join(project_root, ".env"))
```

**Typical use:** Project-specific config, different environments

### **Integration with ConfigHandler**

**Clear separation of concerns:**

```python
from basefunctions import ConfigHandler, SecretHandler

config = ConfigHandler()
secrets = SecretHandler()

# Public configuration (not sensitive)
db_host = config.get_config_parameter("myapp/database/host")
db_port = config.get_config_parameter("myapp/database/port", default_value=5432)

# Sensitive credentials (private)
db_user = secrets.get_secret_value("DB_USER")
db_password = secrets.get_secret_value("DB_PASSWORD")

# Combine for database connection
db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/mydb"
```

**What goes where?**

| Type | Storage | Example |
|------|---------|---------|
| Public settings | `config.json` | Timeouts, feature flags, URLs (without credentials) |
| Sensitive data | `.env` | Passwords, API keys, tokens, private keys |
| Infrastructure | `.env` or config | Depends on sensitivity (DB host → config, DB password → .env) |

---

## Configuration Structure

### **config.json Format**

The central configuration file uses a hierarchical JSON structure:

```json
{
  "package_structure": {
    "directories": ["config", "logs", "templates/config"]
  },
  "basefunctions": {
    "prodtools": {
      "create_project": {
        "project_types": {
          "generic": {
            "directories": [
              "00-Planning",
              "20-Documents",
              "30-Assets",
              "40-Work",
              "50-Deliverables",
              "90-Archive"
            ]
          },
          "code": {
            "directories": [
              "00-Planning",
              "10-Code",
              "20-Documents",
              "30-Assets",
              "40-Work",
              "50-Deliverables",
              "90-Archive"
            ]
          }
        }
      },
      "create_python_package": {
        "default_license": "MIT",
        "template_path": "templates/licenses",
        "default_structure": {
          "use_src_layout": true,
          "create_tests": true,
          "include_vscode": true,
          "github_integration": true
        }
      }
    },
    "devonthink_sync": {
      "source": "~/Library/Application Support/DEVONthink/Inbox.dtBase2/Files.noindex",
      "target": "~/Files/00_DevonThink_Inbox"
    }
  }
}
```

### **Reserved Sections**

#### **package_structure**

Defines directory structure for package runtime environment.

```json
{
  "package_structure": {
    "directories": [
      "config",           // Configuration files
      "logs",             // Log files
      "templates/config", // Configuration templates
      "custom_dir_1",     // Custom directories
      "custom_dir_2"
    ]
  }
}
```

**Purpose:**
- Customize package directory structure
- Created automatically on package initialization
- Used by `create_full_package_structure()`

**Default directories** (if not specified):
```python
DEFAULT_PACKAGE_DIRECTORIES = ["config", "logs", "templates/config"]
```

### **Package Sections**

Each package gets its own top-level section:

```json
{
  "myapp": {
    "feature_a": { "enabled": true },
    "feature_b": { "timeout": 30 },
    "database": {
      "host": "localhost",
      "port": 5432,
      "pool_size": 10
    }
  }
}
```

**Naming conventions:**
- Use package name as section key
- Lowercase with underscores: `my_app`
- Avoid reserved names: `package_structure`

### **Hierarchical Organization**

Organize related settings in nested structures:

```json
{
  "myapp": {
    "services": {
      "api": {
        "url": "https://api.example.com",
        "timeout": 30,
        "retry_count": 3
      },
      "database": {
        "host": "localhost",
        "port": 5432
      }
    },
    "features": {
      "feature_x": { "enabled": true },
      "feature_y": { "enabled": false, "beta": true }
    }
  }
}
```

**Access:**
```python
api_url = config.get_config_parameter("myapp/services/api/url")
# Returns: "https://api.example.com"

api_config = config.get_config_parameter("myapp/services/api")
# Returns: {"url": "...", "timeout": 30, "retry_count": 3}
```

### **Data Types**

Supported JSON data types:

```json
{
  "myapp": {
    "string_value": "hello",
    "number_int": 42,
    "number_float": 3.14,
    "boolean": true,
    "null_value": null,
    "array": [1, 2, 3],
    "object": {
      "nested": "value"
    }
  }
}
```

**Type preservation:**
```python
# Returns Python equivalents
string_val = config.get_config_parameter("myapp/string_value")  # str
int_val = config.get_config_parameter("myapp/number_int")      # int
float_val = config.get_config_parameter("myapp/number_float")  # float
bool_val = config.get_config_parameter("myapp/boolean")        # bool
none_val = config.get_config_parameter("myapp/null_value")     # None
list_val = config.get_config_parameter("myapp/array")          # list
dict_val = config.get_config_parameter("myapp/object")         # dict
```

### **Comments in JSON**

**Standard JSON doesn't support comments**, but you can use:

**Option 1: Convention key (ignored)**
```json
{
  "myapp": {
    "_comment": "This is a configuration section for myapp",
    "timeout": 30
  }
}
```

**Option 2: Remove before deployment**
```json5
// config.json5 (development)
{
  "myapp": {
    // This timeout is critical for API stability
    "timeout": 30
  }
}
```
Convert to standard JSON for deployment.

**Option 3: External documentation**
Create `CONFIG.md` explaining configuration structure.

---

## Package-Specific Configs

### **Auto-Loading on Import**

When basefunctions is imported, it automatically loads its own configuration:

```python
# In basefunctions/__init__.py
ConfigHandler().load_config_for_package("basefunctions")
```

**Process:**
1. Check for `~/.neuraldevelopment/basefunctions/config/config.json`
2. If missing, create from template
3. Load into ConfigHandler singleton
4. Create full package structure

### **Loading Config for Your Package**

In your package's `__init__.py`:

```python
# myapp/__init__.py
from basefunctions import ConfigHandler

# Load package configuration
ConfigHandler().load_config_for_package("myapp")

# Now accessible throughout package
config = ConfigHandler()
setting = config.get_config_parameter("myapp/some_setting")
```

### **Package Template Creation**

#### **Step 1: Create Template**

Create template in development environment:

```python
# myapp/setup.py or myapp/__init__.py
from basefunctions import ConfigHandler
import os
import json

config = ConfigHandler()

# Define default configuration
default_config = {
    "myapp": {
        "api": {
            "url": "https://api.example.com",
            "timeout": 30
        },
        "database": {
            "host": "localhost",
            "port": 5432
        },
        "features": {
            "feature_x": True,
            "feature_y": False
        }
    }
}

# Save as template
import basefunctions
template_path = basefunctions.get_runtime_template_path("myapp")
os.makedirs(template_path, exist_ok=True)
template_file = os.path.join(template_path, "config.json")

with open(template_file, "w", encoding="utf-8") as f:
    json.dump(default_config, f, indent=2)
```

#### **Step 2: Load Config**

On first run, config is created from template:

```python
# myapp/__init__.py
from basefunctions import ConfigHandler

# First run: Creates config from template
# Subsequent runs: Loads existing config
ConfigHandler().load_config_for_package("myapp")
```

#### **Step 3: Access Config**

Throughout your package:

```python
# myapp/services/api_client.py
from basefunctions import ConfigHandler

config = ConfigHandler()

api_url = config.get_config_parameter("myapp/api/url")
timeout = config.get_config_parameter("myapp/api/timeout", default_value=30)
```

### **Multi-Package Scenarios**

**Single config.json, multiple packages:**

```json
{
  "package_structure": {
    "directories": ["config", "logs", "templates/config"]
  },
  "basefunctions": {
    "feature_a": {}
  },
  "myapp": {
    "api": {}
  },
  "another_app": {
    "settings": {}
  }
}
```

**Loading multiple packages:**

```python
from basefunctions import ConfigHandler

config = ConfigHandler()

# Load configs for different packages
config.load_config_for_package("myapp")
config.load_config_for_package("another_app")

# Access configs
myapp_cfg = config.get_config_for_package("myapp")
another_cfg = config.get_config_for_package("another_app")
```

**Shared configuration:**

```json
{
  "shared": {
    "logging": {
      "level": "INFO",
      "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    }
  },
  "myapp": {
    "logging": {
      "level": "DEBUG"  // Override for myapp
    }
  }
}
```

```python
# Get with fallback
log_level = (
    config.get_config_parameter("myapp/logging/level") or
    config.get_config_parameter("shared/logging/level", default_value="INFO")
)
```

### **Custom Directory Structures**

Define custom directories in config:

```json
{
  "package_structure": {
    "directories": [
      "config",
      "logs",
      "templates/config",
      "data",           // Custom: data files
      "cache",          // Custom: cache
      "exports",        // Custom: exported files
      "imports"         // Custom: imported files
    ]
  },
  "myapp": {}
}
```

**Result:**
```
~/.neuraldevelopment/myapp/
├── config/
├── logs/
├── templates/config/
├── data/          # Custom
├── cache/         # Custom
├── exports/       # Custom
└── imports/       # Custom
```

**Access custom directories:**

```python
import basefunctions
import os

# Get package runtime path
package_path = basefunctions.get_runtime_path("myapp")

# Access custom directories
data_dir = os.path.join(package_path, "data")
cache_dir = os.path.join(package_path, "cache")
```

---

## Environment Variables

### **Integration with .env Files**

SecretHandler uses `python-dotenv` for `.env` file support:

```python
from basefunctions import SecretHandler

# Loads ~/.env and sets environment variables
secrets = SecretHandler()

# Access via SecretHandler
api_key = secrets.get_secret_value("API_KEY")

# Or via os.getenv (same result)
import os
api_key = os.getenv("API_KEY")
```

### **Precedence Rules**

Environment variable resolution order (highest to lowest precedence):

1. **System environment variables** (shell exports)
2. **Existing environment variables** (not overridden by .env)
3. **.env file values**
4. **Default values in code**

```bash
# Shell
export API_KEY=from_shell

# ~/.env
API_KEY=from_dotenv
```

```python
from basefunctions import SecretHandler
import os

# System environment takes precedence
secrets = SecretHandler()
api_key = secrets.get_secret_value("API_KEY")
# Returns: "from_shell" (NOT "from_dotenv")

# Same with os.getenv
api_key = os.getenv("API_KEY")
# Returns: "from_shell"
```

### **Use Cases**

#### **Development vs. Production**

**Development (.env file):**
```bash
# ~/.env
DATABASE_URL=postgresql://localhost/dev_db
API_URL=http://localhost:8000
DEBUG=true
```

**Production (environment variables):**
```bash
# Set by deployment system
export DATABASE_URL=postgresql://prod-host/prod_db
export API_URL=https://api.production.com
export DEBUG=false
```

**Code (works in both):**
```python
from basefunctions import SecretHandler

secrets = SecretHandler()
db_url = secrets.get_secret_value("DATABASE_URL")
debug = secrets.get_secret_value("DEBUG", "false") == "true"
```

#### **CI/CD Integration**

**GitHub Actions:**
```yaml
# .github/workflows/test.yml
jobs:
  test:
    runs-on: ubuntu-latest
    env:
      DATABASE_URL: ${{ secrets.DATABASE_URL }}
      API_KEY: ${{ secrets.API_KEY }}
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: pytest tests/
```

**Code:**
```python
# tests/conftest.py
from basefunctions import SecretHandler

# No .env file in CI, uses environment variables
secrets = SecretHandler()
db_url = secrets.get_secret_value("DATABASE_URL", "sqlite:///:memory:")
```

#### **Docker Integration**

**Dockerfile:**
```dockerfile
FROM python:3.12
WORKDIR /app
COPY . .
RUN pip install -e .
CMD ["python", "app.py"]
```

**docker-compose.yml:**
```yaml
services:
  app:
    build: .
    env_file:
      - .env
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - API_KEY=${API_KEY}
```

**Code:**
```python
# app.py
from basefunctions import SecretHandler

secrets = SecretHandler()
db_url = secrets.get_secret_value("DATABASE_URL")
# Works with both .env file and Docker environment
```

### **Security Considerations**

#### **Never Commit Secrets**

**.gitignore:**
```gitignore
# Environment files
.env
.env.local
.env.*.local

# But DO commit example/template
!.env.example
```

**.env.example (commit this):**
```bash
# Copy to .env and fill in your values
DATABASE_URL=postgresql://user:password@host/database
API_KEY=your_api_key_here
SECRET_TOKEN=your_secret_token
```

#### **Secrets in Logs**

```python
import logging
from basefunctions import SecretHandler

logger = logging.getLogger(__name__)
secrets = SecretHandler()

# SAFE: Log that secret exists
api_key = secrets.get_secret_value("API_KEY")
if api_key:
    logger.info("API_KEY loaded successfully")
else:
    logger.error("API_KEY not found")

# UNSAFE: Never log secret values!
logger.debug(f"API_KEY: {api_key}")  # DON'T DO THIS!

# SAFE: Log masked value
logger.debug(f"API_KEY: {api_key[:4]}..." if api_key else "None")
```

#### **Secrets in Error Messages**

```python
from basefunctions import SecretHandler

secrets = SecretHandler()
db_url = secrets.get_secret_value("DATABASE_URL")

try:
    # Connect to database
    conn = connect(db_url)
except Exception as e:
    # UNSAFE: Exception might contain connection string with password
    logger.error(f"Database connection failed: {e}")

    # SAFE: Generic error message
    logger.error("Database connection failed - check DATABASE_URL")
    logger.debug(f"Error type: {type(e).__name__}")
```

---

## Use Cases

### **1. Application Configuration**

**Scenario:** Web application with multiple services

**config.json:**
```json
{
  "mywebapp": {
    "server": {
      "host": "0.0.0.0",
      "port": 8000,
      "workers": 4
    },
    "database": {
      "pool_size": 10,
      "pool_timeout": 30,
      "echo_sql": false
    },
    "cache": {
      "backend": "redis",
      "ttl": 3600
    },
    "features": {
      "enable_registration": true,
      "enable_api": true,
      "require_email_verification": true
    }
  }
}
```

**~/.env:**
```bash
DATABASE_URL=postgresql://user:pass@localhost/mywebapp
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key-here
```

**Code:**
```python
# mywebapp/__init__.py
from basefunctions import ConfigHandler, SecretHandler

# Load configuration
ConfigHandler().load_config_for_package("mywebapp")
config = ConfigHandler()
secrets = SecretHandler()

# Server config
SERVER_HOST = config.get_config_parameter("mywebapp/server/host", "0.0.0.0")
SERVER_PORT = config.get_config_parameter("mywebapp/server/port", 8000)
WORKERS = config.get_config_parameter("mywebapp/server/workers", 4)

# Database config (public + secret)
DB_URL = secrets.get_secret_value("DATABASE_URL")
DB_POOL_SIZE = config.get_config_parameter("mywebapp/database/pool_size", 10)
DB_ECHO = config.get_config_parameter("mywebapp/database/echo_sql", False)

# Cache config
CACHE_BACKEND = config.get_config_parameter("mywebapp/cache/backend", "redis")
REDIS_URL = secrets.get_secret_value("REDIS_URL")
CACHE_TTL = config.get_config_parameter("mywebapp/cache/ttl", 3600)

# Feature flags
ENABLE_REGISTRATION = config.get_config_parameter("mywebapp/features/enable_registration", True)
ENABLE_API = config.get_config_parameter("mywebapp/features/enable_api", True)
```

### **2. CLI Tool Configuration**

**Scenario:** Command-line tool with user preferences

**config.json:**
```json
{
  "mycli": {
    "defaults": {
      "output_format": "json",
      "verbosity": "info",
      "color": true
    },
    "aliases": {
      "ll": "list --long",
      "st": "status --verbose"
    },
    "api": {
      "base_url": "https://api.example.com",
      "timeout": 30,
      "retry_count": 3
    }
  }
}
```

**~/.env:**
```bash
MYCLI_API_KEY=your_api_key
MYCLI_USER_TOKEN=your_user_token
```

**Code:**
```python
# mycli/config.py
from basefunctions import ConfigHandler, SecretHandler

class CLIConfig:
    def __init__(self):
        ConfigHandler().load_config_for_package("mycli")
        self.config = ConfigHandler()
        self.secrets = SecretHandler()

    @property
    def output_format(self):
        return self.config.get_config_parameter("mycli/defaults/output_format", "json")

    @property
    def verbosity(self):
        return self.config.get_config_parameter("mycli/defaults/verbosity", "info")

    @property
    def api_key(self):
        return self.secrets.get_secret_value("MYCLI_API_KEY")

    def get_alias(self, alias_name):
        aliases = self.config.get_config_parameter("mycli/aliases", {})
        return aliases.get(alias_name)

# Usage
cli_config = CLIConfig()
print(f"Output format: {cli_config.output_format}")
print(f"API Key loaded: {bool(cli_config.api_key)}")
```

### **3. Data Processing Pipeline**

**Scenario:** ETL pipeline with multiple data sources

**config.json:**
```json
{
  "etl_pipeline": {
    "sources": {
      "database": {
        "enabled": true,
        "query_batch_size": 1000
      },
      "api": {
        "enabled": true,
        "rate_limit": 100,
        "rate_period": 60
      },
      "files": {
        "enabled": false,
        "input_dir": "~/data/input"
      }
    },
    "processing": {
      "parallel_workers": 4,
      "chunk_size": 100,
      "timeout": 300
    },
    "output": {
      "format": "parquet",
      "compression": "snappy",
      "output_dir": "~/data/output"
    }
  }
}
```

**~/.env:**
```bash
# Data sources
DB_CONNECTION_STRING=postgresql://etl_user:password@db.example.com/warehouse
API_KEY=your_api_key
API_SECRET=your_api_secret

# Output credentials
S3_BUCKET=my-etl-bucket
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

**Code:**
```python
# etl_pipeline/pipeline.py
from basefunctions import ConfigHandler, SecretHandler
import os

class ETLPipeline:
    def __init__(self):
        ConfigHandler().load_config_for_package("etl_pipeline")
        self.config = ConfigHandler()
        self.secrets = SecretHandler()

    def setup_sources(self):
        sources = {}

        # Database source
        if self.config.get_config_parameter("etl_pipeline/sources/database/enabled"):
            sources["database"] = {
                "connection": self.secrets.get_secret_value("DB_CONNECTION_STRING"),
                "batch_size": self.config.get_config_parameter(
                    "etl_pipeline/sources/database/query_batch_size", 1000
                )
            }

        # API source
        if self.config.get_config_parameter("etl_pipeline/sources/api/enabled"):
            sources["api"] = {
                "key": self.secrets.get_secret_value("API_KEY"),
                "secret": self.secrets.get_secret_value("API_SECRET"),
                "rate_limit": self.config.get_config_parameter(
                    "etl_pipeline/sources/api/rate_limit", 100
                )
            }

        return sources

    def get_processing_config(self):
        return {
            "workers": self.config.get_config_parameter(
                "etl_pipeline/processing/parallel_workers", 4
            ),
            "chunk_size": self.config.get_config_parameter(
                "etl_pipeline/processing/chunk_size", 100
            ),
            "timeout": self.config.get_config_parameter(
                "etl_pipeline/processing/timeout", 300
            )
        }

    def get_output_config(self):
        output_dir = self.config.get_config_parameter(
            "etl_pipeline/output/output_dir", "~/data/output"
        )
        return {
            "format": self.config.get_config_parameter(
                "etl_pipeline/output/format", "parquet"
            ),
            "compression": self.config.get_config_parameter(
                "etl_pipeline/output/compression", "snappy"
            ),
            "directory": os.path.expanduser(output_dir),
            "s3_bucket": self.secrets.get_secret_value("S3_BUCKET")
        }
```

### **4. Microservices Configuration**

**Scenario:** Multiple microservices sharing config

**config.json:**
```json
{
  "shared": {
    "logging": {
      "level": "INFO",
      "format": "json"
    },
    "tracing": {
      "enabled": true,
      "sample_rate": 0.1
    }
  },
  "auth_service": {
    "port": 8001,
    "token_ttl": 3600,
    "refresh_ttl": 86400
  },
  "user_service": {
    "port": 8002,
    "cache_ttl": 300
  },
  "api_gateway": {
    "port": 8000,
    "upstream_services": {
      "auth": "http://localhost:8001",
      "user": "http://localhost:8002"
    }
  }
}
```

**~/.env:**
```bash
# Shared secrets
JWT_SECRET=your-jwt-secret
DATABASE_URL=postgresql://user:pass@localhost/myapp

# Service-specific
AUTH_SERVICE_KEY=auth-key
USER_SERVICE_KEY=user-key
```

**Code:**
```python
# shared/config.py
from basefunctions import ConfigHandler, SecretHandler

class ServiceConfig:
    def __init__(self, service_name):
        self.service_name = service_name
        ConfigHandler().load_config_for_package(service_name)
        self.config = ConfigHandler()
        self.secrets = SecretHandler()

    def get_shared_config(self, key):
        return self.config.get_config_parameter(f"shared/{key}")

    def get_service_config(self, key):
        return self.config.get_config_parameter(f"{self.service_name}/{key}")

# auth_service/main.py
from shared.config import ServiceConfig

config = ServiceConfig("auth_service")

# Shared logging config
log_level = config.get_shared_config("logging/level")

# Service-specific config
port = config.get_service_config("port")
token_ttl = config.get_service_config("token_ttl")

# Secrets
jwt_secret = config.secrets.get_secret_value("JWT_SECRET")
db_url = config.secrets.get_secret_value("DATABASE_URL")
```

### **5. Testing with Custom Configs**

**Scenario:** Different configs for testing

**Code:**
```python
# tests/conftest.py
import pytest
from basefunctions import ConfigHandler
import os
import json
import tempfile

@pytest.fixture
def test_config():
    """Provide test configuration."""
    config_data = {
        "myapp": {
            "database": {
                "host": "localhost",
                "port": 5432
            },
            "api": {
                "timeout": 10,
                "retry_count": 1
            }
        }
    }

    # Create temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        config_file = f.name

    # Load config
    config = ConfigHandler()
    config.load_config_file(config_file)

    yield config

    # Cleanup
    os.unlink(config_file)

# tests/test_api.py
def test_api_timeout(test_config):
    timeout = test_config.get_config_parameter("myapp/api/timeout")
    assert timeout == 10  # Test value, not production
```

---

## Best Practices

### **Configuration Management**

#### **1. Separation of Concerns**

**Do:**
```json
// config.json - Public configuration
{
  "myapp": {
    "api": {
      "url": "https://api.example.com",
      "timeout": 30,
      "retry_count": 3
    }
  }
}
```

```bash
# .env - Sensitive credentials
API_KEY=your_api_key
API_SECRET=your_api_secret
```

**Don't:**
```json
// DON'T put secrets in config.json
{
  "myapp": {
    "api": {
      "url": "https://api.example.com",
      "api_key": "your_api_key"  // ❌ NEVER DO THIS
    }
  }
}
```

#### **2. Use Hierarchical Organization**

**Good:**
```json
{
  "myapp": {
    "services": {
      "database": {
        "pool_size": 10,
        "timeout": 30
      },
      "cache": {
        "ttl": 3600,
        "max_size": 1000
      }
    },
    "features": {
      "feature_x": {"enabled": true},
      "feature_y": {"enabled": false}
    }
  }
}
```

**Avoid:**
```json
{
  "myapp": {
    "database_pool_size": 10,
    "database_timeout": 30,
    "cache_ttl": 3600,
    "cache_max_size": 1000,
    "feature_x_enabled": true,
    "feature_y_enabled": false
  }
}
```

#### **3. Provide Defaults**

**Always use defaults in code:**

```python
# Good - with defaults
timeout = config.get_config_parameter("myapp/api/timeout", default_value=30)
workers = config.get_config_parameter("myapp/workers", default_value=4)

# Risky - no defaults
timeout = config.get_config_parameter("myapp/api/timeout")  # Could be None!
```

#### **4. Document Configuration**

**Create CONFIG.md:**

```markdown
# MyApp Configuration Guide

## config.json

### myapp/api/timeout
- Type: integer
- Default: 30
- Description: API request timeout in seconds
- Range: 1-300

### myapp/database/pool_size
- Type: integer
- Default: 10
- Description: Database connection pool size
- Range: 1-100
```

### **Security Best Practices**

#### **1. Never Commit Secrets**

**.gitignore:**
```gitignore
# Environment files with secrets
.env
.env.local
.env.*.local

# Config files (if they contain secrets)
config.json

# But DO commit templates
!.env.example
!config.json.example
```

#### **2. Use Environment-Specific .env Files**

```bash
# .env.development
DATABASE_URL=postgresql://localhost/dev_db
DEBUG=true

# .env.staging
DATABASE_URL=postgresql://staging-host/staging_db
DEBUG=false

# .env.production
DATABASE_URL=postgresql://prod-host/prod_db
DEBUG=false
```

**Load based on environment:**

```python
import os
from basefunctions import SecretHandler

env = os.getenv("ENV", "development")
env_file = f".env.{env}"

secrets = SecretHandler(env_file=env_file)
```

#### **3. Rotate Secrets Regularly**

```python
# Old approach (hardcoded)
API_KEY = "sk-1234567890"  # ❌ Hard to rotate

# Good approach (env variable)
from basefunctions import SecretHandler
secrets = SecretHandler()
API_KEY = secrets.get_secret_value("API_KEY")  # ✅ Easy to rotate

# Just update ~/.env:
# API_KEY=sk-new-key-here
```

#### **4. Validate Secrets on Startup**

```python
from basefunctions import SecretHandler
import sys

secrets = SecretHandler()

# Required secrets
required_secrets = ["DATABASE_URL", "API_KEY", "SECRET_TOKEN"]

missing = []
for secret in required_secrets:
    if not secrets.get_secret_value(secret):
        missing.append(secret)

if missing:
    print(f"ERROR: Missing required secrets: {', '.join(missing)}")
    print(f"Please set them in ~/.env")
    sys.exit(1)
```

### **Deployment Best Practices**

#### **1. Use Templates for Distribution**

**Ship template, not actual config:**

```bash
# project/
├── config.json.example    # ✅ Commit this
├── .env.example           # ✅ Commit this
├── config.json            # ❌ DON'T commit
└── .env                   # ❌ DON'T commit
```

**Installation instructions:**

```bash
# Setup instructions in README.md
cp config.json.example config.json
cp .env.example .env
# Edit config.json and .env with your values
```

#### **2. Environment Variable Override**

**Allow environment variables to override config:**

```python
from basefunctions import ConfigHandler
import os

config = ConfigHandler()

# Try environment variable first, then config, then default
db_host = (
    os.getenv("DATABASE_HOST") or
    config.get_config_parameter("myapp/database/host") or
    "localhost"
)
```

#### **3. Validation on Load**

```python
from basefunctions import ConfigHandler

class AppConfig:
    def __init__(self):
        ConfigHandler().load_config_for_package("myapp")
        self.config = ConfigHandler()
        self._validate()

    def _validate(self):
        """Validate configuration on load."""
        # Check required sections exist
        if not self.config.get_config_parameter("myapp"):
            raise ValueError("Missing 'myapp' section in config")

        # Validate ranges
        timeout = self.config.get_config_parameter("myapp/api/timeout", 30)
        if not (1 <= timeout <= 300):
            raise ValueError(f"Invalid timeout: {timeout} (must be 1-300)")

        # Validate types
        workers = self.config.get_config_parameter("myapp/workers", 4)
        if not isinstance(workers, int):
            raise TypeError(f"workers must be int, got {type(workers)}")
```

### **Performance Best Practices**

#### **1. Cache Config Values**

**Don't:**
```python
# Reads from ConfigHandler every time
def process_data(data):
    timeout = ConfigHandler().get_config_parameter("myapp/timeout", 30)
    # ... process with timeout
```

**Do:**
```python
# Cache at module/class level
class DataProcessor:
    def __init__(self):
        config = ConfigHandler()
        self.timeout = config.get_config_parameter("myapp/timeout", 30)

    def process_data(self, data):
        # Use cached value
        # ... process with self.timeout
```

#### **2. Batch Config Reads**

**Don't:**
```python
# Multiple individual reads
host = config.get_config_parameter("myapp/database/host")
port = config.get_config_parameter("myapp/database/port")
user = config.get_config_parameter("myapp/database/user")
```

**Do:**
```python
# Single read of parent object
db_config = config.get_config_parameter("myapp/database", {})
host = db_config.get("host", "localhost")
port = db_config.get("port", 5432)
user = db_config.get("user", "admin")
```

#### **3. Use Property Decorators**

```python
from basefunctions import ConfigHandler

class AppConfig:
    def __init__(self):
        self._config = ConfigHandler()

    @property
    def api_timeout(self):
        """Lazy-loaded, cached on first access."""
        if not hasattr(self, "_api_timeout"):
            self._api_timeout = self._config.get_config_parameter(
                "myapp/api/timeout", 30
            )
        return self._api_timeout
```

### **Testing Best Practices**

#### **1. Use Fixtures for Test Configs**

```python
# tests/conftest.py
import pytest
from basefunctions import ConfigHandler
import json
import tempfile
import os

@pytest.fixture(scope="session")
def test_config_file():
    """Create temporary test config file."""
    config_data = {
        "myapp": {
            "api": {"timeout": 10},
            "database": {"host": "localhost"}
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        config_file = f.name

    yield config_file

    os.unlink(config_file)

@pytest.fixture
def config(test_config_file):
    """Provide ConfigHandler with test config."""
    handler = ConfigHandler()
    handler.load_config_file(test_config_file)
    return handler
```

#### **2. Mock Secrets in Tests**

```python
# tests/test_api.py
import pytest
from unittest.mock import patch, MagicMock

@patch('basefunctions.config.secret_handler.os.getenv')
def test_api_with_mocked_secrets(mock_getenv):
    """Test with mocked secrets."""
    # Mock secret values
    mock_getenv.side_effect = lambda key, default=None: {
        "API_KEY": "test_api_key",
        "API_SECRET": "test_api_secret"
    }.get(key, default)

    from basefunctions import SecretHandler
    secrets = SecretHandler()

    # Test with mocked values
    api_key = secrets.get_secret_value("API_KEY")
    assert api_key == "test_api_key"
```

#### **3. Test Different Configurations**

```python
# tests/test_config_variations.py
import pytest

@pytest.mark.parametrize("timeout,expected", [
    (10, 10),
    (None, 30),  # Default
    (300, 300),
])
def test_timeout_variations(config, timeout, expected):
    """Test different timeout configurations."""
    if timeout is not None:
        config.config["myapp"]["api"]["timeout"] = timeout

    result = config.get_config_parameter("myapp/api/timeout", default_value=30)
    assert result == expected
```

---

## API Reference

### **ConfigHandler**

#### **Class Definition**

```python
@basefunctions.singleton
class ConfigHandler:
    """Thread-safe singleton for JSON-based configuration management."""
```

**Singleton:** Only one instance exists application-wide.

**Thread-safe:** All methods use `RLock` for synchronization.

#### **Methods**

---

##### **__init__()**

```python
def __init__(self):
    """Initialize ConfigHandler singleton."""
```

**Automatically called on first access. Do not call directly.**

**Initializes:**
- Empty config dictionary
- Thread lock (RLock)
- Logger
- Root structure

---

##### **load_config_file(file_path: str) -> None**

```python
def load_config_file(self, file_path: str) -> None:
    """
    Load JSON configuration file from specified path.

    Parameters
    ----------
    file_path : str
        Path to JSON configuration file

    Raises
    ------
    ValueError
        If file is not .json extension or invalid format
    FileNotFoundError
        If file does not exist
    json.JSONDecodeError
        If JSON parsing fails
    RuntimeError
        For other unexpected errors
    """
```

**Example:**
```python
config = ConfigHandler()
config.load_config_file("/path/to/config.json")
```

---

##### **load_config_for_package(package_name: str) -> None**

```python
def load_config_for_package(self, package_name: str) -> None:
    """
    Load configuration for a package context.

    Parameters
    ----------
    package_name : str
        Name of package (used for path detection)

    Notes
    -----
    - Ensures bootstrap package structure exists
    - Creates config from template if missing
    - Loads config into memory
    - Creates full package structure
    """
```

**Example:**
```python
config = ConfigHandler()
config.load_config_for_package("myapp")
```

---

##### **create_config_from_template(package_name: str) -> None**

```python
def create_config_from_template(self, package_name: str) -> None:
    """
    Create config.json from template or empty structure.

    Parameters
    ----------
    package_name : str
        Name of package

    Raises
    ------
    ValueError
        If package_name is empty
    RuntimeError
        If config creation fails
    """
```

**Example:**
```python
config = ConfigHandler()
config.create_config_from_template("myapp")
```

---

##### **get_config_for_package(package: Optional[str] = None) -> dict**

```python
def get_config_for_package(self, package: Optional[str] = None) -> dict:
    """
    Get configuration for package section or all configurations.

    Parameters
    ----------
    package : Optional[str], optional
        Package name, if None returns all configurations

    Returns
    -------
    dict
        Configuration dictionary (copy, not reference)
    """
```

**Example:**
```python
config = ConfigHandler()

# Get specific package config
myapp_cfg = config.get_config_for_package("myapp")

# Get all configs
all_cfg = config.get_config_for_package()
```

---

##### **get_config_parameter(path: str, default_value: Any = None) -> Any**

```python
def get_config_parameter(self, path: str, default_value: Any = None) -> Any:
    """
    Get configuration parameter by slash-separated path.

    Parameters
    ----------
    path : str
        Configuration path separated by '/' (e.g., 'package/section/key')
    default_value : Any, optional
        Default value if path not found (default: None)

    Returns
    -------
    Any
        Configuration parameter value or default_value
    """
```

**Example:**
```python
config = ConfigHandler()

timeout = config.get_config_parameter("myapp/api/timeout", default_value=30)
db_cfg = config.get_config_parameter("myapp/database")
```

---

### **SecretHandler**

#### **Class Definition**

```python
@basefunctions.singleton
class SecretHandler:
    """Singleton for .env file and environment variable management."""
```

**Singleton:** Only one instance exists application-wide.

#### **Methods**

---

##### **__init__(env_file: Optional[str] = None)**

```python
def __init__(self, env_file: Optional[str] = None):
    """
    Initialize SecretHandler with .env file.

    Parameters
    ----------
    env_file : Optional[str], optional
        Path to .env file. If None, uses ~/.env (default: None)

    Notes
    -----
    - Loads .env file into environment variables
    - Does not override existing environment variables
    - Creates internal dict of secrets
    """
```

**Example:**
```python
# Default: ~/.env
secrets = SecretHandler()

# Custom path
secrets = SecretHandler(env_file="/path/to/.env")
```

---

##### **get_secret_value(key: str, default_value: Any = None) -> Any**

```python
def get_secret_value(self, key: str, default_value: Any = None) -> Any:
    """
    Get secret value from environment variables.

    Parameters
    ----------
    key : str
        Secret key name
    default_value : Any, optional
        Default value if key not found (default: None)

    Returns
    -------
    Any
        Secret value (as string) or default_value

    Notes
    -----
    All values from .env are strings. Convert as needed.
    """
```

**Example:**
```python
secrets = SecretHandler()

api_key = secrets.get_secret_value("API_KEY")
db_url = secrets.get_secret_value("DATABASE_URL", default_value="sqlite:///:memory:")

# Type conversion
port = int(secrets.get_secret_value("PORT", "8000"))
debug = secrets.get_secret_value("DEBUG", "false").lower() == "true"
```

---

##### **__getitem__(key: str) -> Any**

```python
def __getitem__(self, key: str) -> Any:
    """
    Dict-style access to secrets.

    Parameters
    ----------
    key : str
        Secret key name

    Returns
    -------
    Any
        Secret value or None
    """
```

**Example:**
```python
secrets = SecretHandler()

# Dict-style access
api_key = secrets["API_KEY"]

# Equivalent to
api_key = secrets.get_secret_value("API_KEY")
```

---

##### **get_all_secrets() -> dict[str, str]**

```python
def get_all_secrets(self) -> dict[str, str]:
    """
    Get all secrets loaded from .env file.

    Returns
    -------
    dict[str, str]
        Dictionary of all secret key-value pairs

    Warning
    -------
    Use carefully - contains sensitive data
    """
```

**Example:**
```python
secrets = SecretHandler()

all_secrets = secrets.get_all_secrets()

# Safe usage
print(f"Loaded {len(all_secrets)} secrets")
print(f"Keys: {list(all_secrets.keys())}")

# Unsafe usage - DON'T DO THIS
print(f"Secrets: {all_secrets}")  # Exposes all values!
```

---

### **Runtime Path Functions**

These functions are used by ConfigHandler to determine file paths.

#### **get_runtime_config_path(package_name: str) -> str**

```python
def get_runtime_config_path(package_name: str) -> str:
    """
    Get config directory path for package.

    Parameters
    ----------
    package_name : str
        Package name

    Returns
    -------
    str
        Path to config directory

    Example
    -------
    ~/.neuraldevelopment/myapp/config
    """
```

#### **get_runtime_template_path(package_name: str) -> str**

```python
def get_runtime_template_path(package_name: str) -> str:
    """
    Get template directory path for package.

    Parameters
    ----------
    package_name : str
        Package name

    Returns
    -------
    str
        Path to template directory

    Example
    -------
    ~/.neuraldevelopment/myapp/templates/config
    """
```

#### **get_runtime_path(package_name: str) -> str**

```python
def get_runtime_path(package_name: str) -> str:
    """
    Get runtime root directory for package.

    Parameters
    ----------
    package_name : str
        Package name

    Returns
    -------
    str
        Path to package runtime directory

    Example
    -------
    ~/.neuraldevelopment/myapp
    """
```

---

## Appendix

### **Example .env File**

```bash
# ~/.env
# Application Secrets - DO NOT COMMIT

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/mydb
DB_USER=myapp_user
DB_PASSWORD=secure_password_here

# APIs
API_KEY=sk-1234567890abcdefghijklmnopqrstuvwxyz
API_SECRET=secret_key_here
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx

# Authentication
SECRET_KEY=your-secret-key-for-jwt
JWT_SECRET=another-secret-key

# AWS
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_REGION=us-east-1

# Email
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=myapp@example.com
SMTP_PASSWORD=email_password_here

# Third-party services
STRIPE_API_KEY=sk_test_xxxxxxxxxxxxxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxx

# Feature flags (can also go in config.json)
ENABLE_BETA_FEATURES=true
DEBUG=false
```

### **Example config.json**

```json
{
  "package_structure": {
    "directories": [
      "config",
      "logs",
      "templates/config",
      "data",
      "cache"
    ]
  },
  "myapp": {
    "server": {
      "host": "0.0.0.0",
      "port": 8000,
      "workers": 4,
      "timeout": 30
    },
    "database": {
      "pool_size": 10,
      "pool_timeout": 30,
      "pool_recycle": 3600,
      "echo_sql": false
    },
    "cache": {
      "backend": "redis",
      "ttl": 3600,
      "max_size": 10000
    },
    "logging": {
      "level": "INFO",
      "format": "json",
      "output": "file"
    },
    "features": {
      "enable_registration": true,
      "enable_api": true,
      "require_email_verification": true,
      "max_upload_size": 10485760
    },
    "api": {
      "rate_limit": {
        "enabled": true,
        "requests_per_minute": 60,
        "burst": 10
      },
      "cors": {
        "enabled": true,
        "origins": ["http://localhost:3000", "https://myapp.com"],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "max_age": 3600
      }
    }
  }
}
```

### **Example Project Structure**

```
myapp/
├── .env                        # Secrets (gitignored)
├── .env.example                # Template (committed)
├── config.json                 # Runtime config (gitignored)
├── config.json.example         # Template (committed)
├── .gitignore
├── README.md
├── pyproject.toml
├── src/
│   └── myapp/
│       ├── __init__.py         # Load config here
│       ├── config.py           # Config wrapper class
│       ├── services/
│       │   ├── api.py
│       │   └── database.py
│       └── utils/
│           └── helpers.py
└── tests/
    ├── conftest.py             # Test config fixtures
    └── test_config.py
```

**.gitignore:**
```gitignore
# Secrets and config
.env
.env.local
.env.*.local
config.json

# But commit templates
!.env.example
!config.json.example

# Virtual environments
.venv/
venv/
env/

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
```

---

## Quick Reference

### **ConfigHandler Quick Commands**

```python
from basefunctions import ConfigHandler

# Get singleton
config = ConfigHandler()

# Load package config (first time setup)
config.load_config_for_package("myapp")

# Get entire package config
myapp_cfg = config.get_config_for_package("myapp")

# Get specific parameter
value = config.get_config_parameter("myapp/section/key", default_value=42)

# Get nested object
db_cfg = config.get_config_parameter("myapp/database")
```

### **SecretHandler Quick Commands**

```python
from basefunctions import SecretHandler

# Get singleton (loads ~/.env)
secrets = SecretHandler()

# Get secret
api_key = secrets.get_secret_value("API_KEY")

# Get secret with default
port = secrets.get_secret_value("PORT", default_value="8000")

# Dict-style access
db_url = secrets["DATABASE_URL"]

# Get all secrets (careful!)
all_secrets = secrets.get_all_secrets()
```

### **Common Patterns**

**Initialize in package __init__.py:**
```python
from basefunctions import ConfigHandler
ConfigHandler().load_config_for_package("myapp")
```

**Config wrapper class:**
```python
from basefunctions import ConfigHandler, SecretHandler

class AppConfig:
    def __init__(self):
        self.config = ConfigHandler()
        self.secrets = SecretHandler()

    @property
    def db_url(self):
        return self.secrets.get_secret_value("DATABASE_URL")

    @property
    def api_timeout(self):
        return self.config.get_config_parameter("myapp/api/timeout", 30)
```

**Combine config and secrets:**
```python
from basefunctions import ConfigHandler, SecretHandler

config = ConfigHandler()
secrets = SecretHandler()

# Public config
db_host = config.get_config_parameter("myapp/database/host", "localhost")
db_port = config.get_config_parameter("myapp/database/port", 5432)

# Sensitive credentials
db_user = secrets.get_secret_value("DB_USER")
db_pass = secrets.get_secret_value("DB_PASSWORD")

# Combined connection string
db_url = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/mydb"
```

---

## Conclusion

The basefunctions config module provides a robust, thread-safe system for managing application configurations and secrets:

**Key Takeaways:**

1. **ConfigHandler**: Centralized JSON-based configuration with path navigation
2. **SecretHandler**: Secure .env-based secrets management
3. **Separation**: Keep public config and sensitive secrets separate
4. **Thread-safe**: RLock-based synchronization for concurrent access
5. **Bootstrap**: Self-contained initialization breaks circular dependencies
6. **Multi-package**: Single config file supports multiple packages

**Best Practices Summary:**

- Use `config.json` for public settings
- Use `.env` for sensitive credentials
- Always provide default values
- Never commit secrets
- Validate configuration on startup
- Cache frequently accessed values
- Document configuration structure

For more information, see:
- [basefunctions README](../README.md)
- [CLAUDE.md](../CLAUDE.md)
- Source code: `src/basefunctions/config/`


---

**Document Version**: 1.1
**Last Updated**: 2025-01-24
**Framework Version**: basefunctions 0.5.32
