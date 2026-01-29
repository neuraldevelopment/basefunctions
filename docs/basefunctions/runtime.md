# Runtime - User Documentation

**Package:** basefunctions
**Subpackage:** runtime
**Version:** 0.5.75
**Purpose:** Runtime environment detection and package structure management

---

## Overview

The runtime subpackage provides automatic detection of development and deployment environments, plus utilities for managing package structures, virtual environments, and deployment operations.

**Key Features:**
- Automatic environment detection (development vs deployment)
- Path resolution for package components (config, logs, templates)
- Package structure creation and validation
- Virtual environment management
- Version information utilities

**Common Use Cases:**
- Finding package configuration files
- Detecting development vs deployment environment
- Creating standard package directory structures
- Managing virtual environments
- Resolving package-specific paths

---

## Public APIs

### Environment Detection Functions

**Purpose:** Detect runtime environment and resolve paths automatically

```python
from basefunctions.runtime import (
    get_runtime_path,
    get_deployment_path,
    find_development_path
)
```

**Key Functions:**

| Function | Parameters | Returns | Description |
|----------|-----------|---------|-------------|
| `get_runtime_path()` | `package_name: str` | `Path` | Get package root path (dev or deploy) |
| `get_deployment_path()` | `package_name: str` | `Path` | Get deployment path |
| `find_development_path()` | `package_name: str` | `Path | None` | Find development path if exists |

**Examples:**

```python
from basefunctions.runtime import get_runtime_path

# Automatically detects environment and returns correct path
package_path = get_runtime_path("myapp")
# Development: /Users/user/Code/neuraldev/myapp
# Deployment: ~/.neuraldevelopment/packages/myapp

# Check which environment
if "neuraldev" in str(package_path):
    print("Running in development")
else:
    print("Running in deployment")
```

---

### Component Path Functions

**Purpose:** Resolve paths to specific package components (config, logs, templates)

```python
from basefunctions.runtime import (
    get_runtime_component_path,
    get_runtime_config_path,
    get_runtime_log_path,
    get_runtime_template_path
)
```

**Key Functions:**

| Function | Parameters | Returns | Description |
|----------|-----------|---------|-------------|
| `get_runtime_component_path()` | `package_name: str, component: str` | `Path` | Get path to any component |
| `get_runtime_config_path()` | `package_name: str` | `Path` | Get config directory path |
| `get_runtime_log_path()` | `package_name: str` | `Path` | Get log directory path |
| `get_runtime_template_path()` | `package_name: str` | `Path` | Get template directory path |

**Examples:**

```python
from basefunctions.runtime import (
    get_runtime_config_path,
    get_runtime_log_path,
    get_runtime_template_path
)

# Get component paths
config_dir = get_runtime_config_path("myapp")
log_dir = get_runtime_log_path("myapp")
template_dir = get_runtime_template_path("myapp")

# Use paths
config_file = config_dir / "myapp.yaml"
log_file = log_dir / "app.log"
template = template_dir / "email.html"

print(f"Config: {config_file}")
print(f"Log: {log_file}")
print(f"Template: {template}")
```

---

### Package Structure Functions

**Purpose:** Create and manage standard package directory structures

```python
from basefunctions.runtime import (
    create_bootstrap_package_structure,
    create_full_package_structure,
    ensure_bootstrap_package_structure
)
```

**Key Functions:**

| Function | Parameters | Returns | Description |
|----------|-----------|---------|-------------|
| `create_bootstrap_package_structure()` | `package_name: str` | `None` | Create minimal deployment structure |
| `create_full_package_structure()` | `package_path: Path` | `None` | Create complete package structure |
| `ensure_bootstrap_package_structure()` | `package_name: str` | `None` | Create structure if not exists |

**Examples:**

```python
from basefunctions.runtime import (
    create_bootstrap_package_structure,
    ensure_bootstrap_package_structure
)

# Create minimal structure for deployment
create_bootstrap_package_structure("myapp")
# Creates: ~/.neuraldevelopment/packages/myapp/{config,log,temp}

# Ensure structure exists (safe to call multiple times)
ensure_bootstrap_package_structure("myapp")
# Creates only if missing
```

---

### DeploymentManager

**Purpose:** Manage package deployment operations

```python
from basefunctions.runtime import DeploymentManager

manager = DeploymentManager()
```

**Key Methods:**

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `deploy_package()` | `package_name: str, source_path: Path` | `None` | Deploy package to deployment directory |
| `get_deployed_version()` | `package_name: str` | `str | None` | Get deployed package version |
| `list_deployed_packages()` | - | `list[str]` | List all deployed packages |

**Examples:**

```python
from basefunctions.runtime import DeploymentManager
from pathlib import Path

manager = DeploymentManager()

# Deploy package
source = Path("/Users/user/Code/neuraldev/myapp")
manager.deploy_package("myapp", source)

# Check deployed version
version = manager.get_deployed_version("myapp")
print(f"Deployed version: {version}")

# List all deployed packages
packages = manager.list_deployed_packages()
for pkg in packages:
    print(f"- {pkg}")
```

---

### VenvUtils

**Purpose:** Virtual environment management utilities

```python
from basefunctions.runtime import VenvUtils

utils = VenvUtils()
```

**Key Methods:**

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `create_venv()` | `venv_path: Path` | `None` | Create virtual environment |
| `get_venv_python()` | `venv_path: Path` | `Path` | Get Python executable path |
| `is_venv()` | `path: Path` | `bool` | Check if path is venv |

**Examples:**

```python
from basefunctions.runtime import VenvUtils
from pathlib import Path

utils = VenvUtils()

# Create virtual environment
venv_path = Path("/path/to/myproject/.venv")
utils.create_venv(venv_path)

# Get Python executable
python_exe = utils.get_venv_python(venv_path)
print(f"Python: {python_exe}")

# Check if directory is venv
if utils.is_venv(venv_path):
    print("Valid virtual environment")
```

---

### Version Functions

**Purpose:** Get version information for packages

```python
from basefunctions.runtime import version, versions
```

**Key Functions:**

| Function | Parameters | Returns | Description |
|----------|-----------|---------|-------------|
| `version()` | `package_name: str` | `str` | Get package version |
| `versions()` | - | `dict[str, str]` | Get all package versions |

**Examples:**

```python
from basefunctions.runtime import version, versions

# Get specific package version
bf_version = version("basefunctions")
print(f"basefunctions: {bf_version}")

# Get all installed package versions
all_versions = versions()
for pkg, ver in all_versions.items():
    print(f"{pkg}: {ver}")
```

---

## Usage Examples

### Basic Usage (Most Common)

**Scenario:** Load configuration from environment-aware path

```python
from basefunctions.runtime import get_runtime_config_path
from pathlib import Path
import yaml

# Step 1: Get config directory
config_dir = get_runtime_config_path("myapp")

# Step 2: Build config file path
config_file = config_dir / "myapp.yaml"

# Step 3: Load configuration
if config_file.exists():
    with open(config_file, "r") as f:
        config = yaml.safe_load(f)
    print(f"Loaded config from: {config_file}")
else:
    print(f"Config not found: {config_file}")
```

**Expected Output:**
```
# Development:
Loaded config from: /Users/user/Code/neuraldev/myapp/config/myapp.yaml

# Deployment:
Loaded config from: /Users/user/.neuraldevelopment/packages/myapp/config/myapp.yaml
```

---

### Advanced Usage - Environment Detection

**Scenario:** Execute different logic based on environment

```python
from basefunctions.runtime import get_runtime_path, find_development_path

# Detect environment
package_path = get_runtime_path("myapp")
dev_path = find_development_path("myapp")

if dev_path:
    print("Development environment detected")
    debug_mode = True
    use_test_db = True
else:
    print("Deployment environment detected")
    debug_mode = False
    use_test_db = False

# Use environment-specific settings
if debug_mode:
    print("Debug logging enabled")
    print(f"Package path: {package_path}")
```

---

### Advanced Usage - Package Structure Setup

**Scenario:** Initialize new package with standard structure

```python
from basefunctions.runtime import (
    create_full_package_structure,
    ensure_bootstrap_package_structure
)
from pathlib import Path

# Create full development structure
dev_path = Path("/Users/user/Code/neuraldev/mynewapp")
dev_path.mkdir(parents=True, exist_ok=True)
create_full_package_structure(dev_path)
# Creates: bin/, config/, demos/, log/, report/, src/, tests/, temp/

# Ensure deployment structure exists
ensure_bootstrap_package_structure("mynewapp")
# Creates: ~/.neuraldevelopment/packages/mynewapp/{config,log,temp}

print("Package structure initialized")
```

---

### Integration with ConfigHandler

**Working with Configuration:**

```python
from basefunctions.runtime import get_runtime_config_path
from basefunctions.config import ConfigHandler
from pathlib import Path

# Get config path for current environment
config_dir = get_runtime_config_path("myapp")
config_file = config_dir / "myapp.yaml"

# Verify config exists
if not config_file.exists():
    print(f"Config not found at: {config_file}")
    # Create default config or exit
    exit(1)

# Load configuration
config = ConfigHandler()
config.load_config_for_package("myapp")

# Use configuration
db_host = config.get("database.host")
print(f"Connecting to database at: {db_host}")
```

---

### Custom Implementation Example

**Scenario:** Build environment-aware logger

```python
from basefunctions.runtime import get_runtime_log_path, find_development_path
import logging
from pathlib import Path

class EnvironmentLogger:
    """Logger with environment-aware configuration"""

    def __init__(self, package_name: str):
        self.package_name = package_name
        self.is_dev = find_development_path(package_name) is not None
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """Setup logger based on environment"""
        logger = logging.getLogger(self.package_name)

        if self.is_dev:
            # Development: console + debug level
            handler = logging.StreamHandler()
            level = logging.DEBUG
        else:
            # Deployment: file + info level
            log_dir = get_runtime_log_path(self.package_name)
            log_file = log_dir / f"{self.package_name}.log"
            handler = logging.FileHandler(log_file)
            level = logging.INFO

        handler.setLevel(level)
        logger.setLevel(level)
        logger.addHandler(handler)

        return logger

    def info(self, message: str) -> None:
        """Log info message"""
        self.logger.info(message)

    def debug(self, message: str) -> None:
        """Log debug message"""
        self.logger.debug(message)

# Usage
logger = EnvironmentLogger("myapp")
logger.info("Application started")
logger.debug("Debug information")
```

---

## Choosing the Right Approach

### When to Use get_runtime_path()

Use for getting package root path:
- Need main package directory
- Environment-agnostic path resolution
- Building paths to package subdirectories

```python
from basefunctions.runtime import get_runtime_path

package_root = get_runtime_path("myapp")
data_dir = package_root / "data"
```

**Pros:**
- Automatic environment detection
- Single source of truth
- Consistent path resolution

**Cons:**
- Requires package to exist
- Can't distinguish dev vs deploy explicitly

---

### When to Use Component-Specific Functions

Use for standard component directories:
- Accessing config files
- Writing logs
- Loading templates

```python
from basefunctions.runtime import get_runtime_config_path, get_runtime_log_path

config_path = get_runtime_config_path("myapp")
log_path = get_runtime_log_path("myapp")
```

**Pros:**
- Standard directory structure
- Clear intent
- Built-in path construction

**Cons:**
- Limited to predefined components
- Less flexible for custom directories

---

### When to Use find_development_path()

Use for explicit environment detection:
- Need to know if in development
- Different behavior per environment
- Development-only features

```python
from basefunctions.runtime import find_development_path

dev_path = find_development_path("myapp")
if dev_path:
    enable_debug_mode()
else:
    enable_production_mode()
```

**Pros:**
- Explicit environment check
- Returns None if not development
- Clear conditional logic

**Cons:**
- Deployment path separate function
- Two calls for both environments

---

## Best Practices

### Best Practice 1: Use Runtime Functions Instead of Hardcoded Paths

**Why:** Portability and environment independence

```python
# GOOD
from basefunctions.runtime import get_runtime_config_path

config_dir = get_runtime_config_path("myapp")
config_file = config_dir / "myapp.yaml"
```

```python
# AVOID
config_file = "/Users/username/Code/myapp/config/myapp.yaml"  # Breaks on other systems
```

---

### Best Practice 2: Ensure Structure Before Use

**Why:** Prevent file operation errors

```python
# GOOD
from basefunctions.runtime import ensure_bootstrap_package_structure, get_runtime_log_path

ensure_bootstrap_package_structure("myapp")
log_dir = get_runtime_log_path("myapp")
log_file = log_dir / "app.log"

with open(log_file, "w") as f:
    f.write("Log entry")
```

```python
# AVOID
from basefunctions.runtime import get_runtime_log_path

log_dir = get_runtime_log_path("myapp")
log_file = log_dir / "app.log"
# May fail if directory doesn't exist
with open(log_file, "w") as f:
    f.write("Log entry")
```

---

### Best Practice 3: Use Path Objects

**Why:** Cross-platform compatibility

```python
# GOOD
from basefunctions.runtime import get_runtime_path
from pathlib import Path

package_path = get_runtime_path("myapp")  # Returns Path
data_file = package_path / "data" / "file.txt"  # Path operations
```

```python
# AVOID
package_path = str(get_runtime_path("myapp"))  # Converts to string
data_file = package_path + "/data/file.txt"  # String concatenation (fragile)
```

---

## Error Handling

### Common Errors

**Error 1: Package Not Found**

```python
# WRONG - Package doesn't exist
from basefunctions.runtime import get_runtime_path

path = get_runtime_path("nonexistent_package")
# May raise error or return unexpected path
```

**Solution:**
```python
# CORRECT - Check if package exists first
from basefunctions.runtime import get_runtime_path, find_development_path, get_deployment_path
from pathlib import Path

dev_path = find_development_path("mypackage")
deploy_path = get_deployment_path("mypackage")

if dev_path and dev_path.exists():
    package_path = dev_path
elif deploy_path.exists():
    package_path = deploy_path
else:
    raise ValueError("Package 'mypackage' not found")
```

---

**Error 2: Directory Creation Failure**

```python
# WRONG - No permission to create directory
from basefunctions.runtime import create_bootstrap_package_structure

create_bootstrap_package_structure("myapp")
# May fail due to permissions
```

**Solution:**
```python
# CORRECT - Handle errors
from basefunctions.runtime import create_bootstrap_package_structure, DeploymentError

try:
    create_bootstrap_package_structure("myapp")
    print("Structure created successfully")
except DeploymentError as e:
    print(f"Failed to create structure: {e}")
    # Handle error or fall back to alternative
except PermissionError as e:
    print(f"Permission denied: {e}")
```

---

## Performance Tips

**Tip 1:** Cache resolved paths
```python
# FAST - Resolve once, use multiple times
from basefunctions.runtime import get_runtime_path

package_path = get_runtime_path("myapp")  # Cache this
file1 = package_path / "data" / "file1.txt"
file2 = package_path / "data" / "file2.txt"

# SLOW - Repeated path resolution
for file_name in file_names:
    path = get_runtime_path("myapp") / "data" / file_name  # Redundant calls
```

**Tip 2:** Use specific component functions
```python
# FAST - Direct component path
from basefunctions.runtime import get_runtime_config_path

config_dir = get_runtime_config_path("myapp")

# SLOWER - Manual path construction
from basefunctions.runtime import get_runtime_path

package_path = get_runtime_path("myapp")
config_dir = package_path / "config"
```

---

## See Also

**Related Subpackages:**
- `config` (`docs/basefunctions/config.md`) - Configuration management using runtime paths
- `io` - File operations with resolved paths

**System Documentation:**
- `~/.claude/_docs/python/basefunctions.md` - Internal architecture details

---

## Quick Reference

### Imports

```python
# Path resolution
from basefunctions.runtime import (
    get_runtime_path,
    get_runtime_config_path,
    get_runtime_log_path,
    get_runtime_template_path
)

# Environment detection
from basefunctions.runtime import (
    find_development_path,
    get_deployment_path
)

# Structure management
from basefunctions.runtime import (
    create_bootstrap_package_structure,
    ensure_bootstrap_package_structure
)

# Utilities
from basefunctions.runtime import (
    DeploymentManager,
    VenvUtils,
    version,
    versions
)
```

### Quick Start

```python
from basefunctions.runtime import get_runtime_path, get_runtime_config_path

# Step 1: Get package path
package_path = get_runtime_path("myapp")

# Step 2: Get component paths
config_dir = get_runtime_config_path("myapp")

# Step 3: Build file paths
config_file = config_dir / "myapp.yaml"

# Step 4: Use paths
if config_file.exists():
    # Load config
    pass
```

### Cheat Sheet

| Task | Code |
|------|------|
| Get package path | `get_runtime_path("pkg")` |
| Get config dir | `get_runtime_config_path("pkg")` |
| Get log dir | `get_runtime_log_path("pkg")` |
| Check if dev | `find_development_path("pkg") is not None` |
| Create structure | `ensure_bootstrap_package_structure("pkg")` |
| Get version | `version("pkg")` |

---

**Document Version:** 0.5.75
**Last Updated:** 2026-01-29
**Subpackage Version:** 0.5.75
