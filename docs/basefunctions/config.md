# Config - User Documentation

**Package:** basefunctions
**Subpackage:** config
**Version:** 0.5.75
**Purpose:** Configuration and secret management with environment-aware loading

---

## Overview

The config subpackage provides secure configuration and secret management for Python applications. It supports YAML-based configuration files with automatic environment detection and secure secret storage.

**Key Features:**
- YAML-based configuration management
- Secure secret storage using platform keyring
- Environment-aware configuration (development/deployment)
- Automatic path resolution for config files
- Type-safe configuration access

**Common Use Cases:**
- Application configuration management
- Secure API key and credential storage
- Environment-specific settings
- Database connection configuration
- Feature flag management

---

## Public APIs

### ConfigHandler

**Purpose:** Load and manage application configuration from YAML files

```python
from basefunctions.config import ConfigHandler

config = ConfigHandler()
```

**Parameters:**
None - ConfigHandler is initialized without parameters

**Key Methods:**

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `load_config_for_package()` | `package_name: str` | `None` | Load configuration for a package |
| `get()` | `key: str, default: Any = None` | `Any` | Get configuration value by key |
| `set()` | `key: str, value: Any` | `None` | Set configuration value |
| `has()` | `key: str` | `bool` | Check if key exists |
| `get_all()` | - | `dict` | Get all configuration |

**Examples:**

```python
from basefunctions.config import ConfigHandler

# Create handler
config = ConfigHandler()

# Load package configuration
config.load_config_for_package("myapp")

# Access configuration values
db_host = config.get("database.host", default="localhost")
db_port = config.get("database.port", default=5432)
debug_mode = config.get("debug", default=False)

# Check if key exists
if config.has("feature.new_ui"):
    enabled = config.get("feature.new_ui")

# Get all configuration
all_config = config.get_all()
print(all_config)
```

**Best For:**
- Application configuration management
- Environment-specific settings
- Feature flags
- Service configuration

**Configuration File Location:**

The handler searches for configuration in these locations (in order):
1. `./config/<package_name>.yaml` (development)
2. `~/.neuraldevelopment/packages/<package_name>/config/<package_name>.yaml` (deployment)

---

### SecretHandler

**Purpose:** Securely store and retrieve sensitive credentials using system keyring

```python
from basefunctions.config import SecretHandler

secrets = SecretHandler(service_name: str)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `service_name` | str | - | Service identifier for keyring storage |

**Key Methods:**

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `set_secret()` | `key: str, value: str` | `None` | Store a secret securely |
| `get_secret()` | `key: str` | `str | None` | Retrieve a stored secret |
| `delete_secret()` | `key: str` | `None` | Remove a stored secret |
| `has_secret()` | `key: str` | `bool` | Check if secret exists |

**Examples:**

```python
from basefunctions.config import SecretHandler

# Create handler for your service
secrets = SecretHandler(service_name="myapp")

# Store API credentials securely
secrets.set_secret("api_key", "sk_live_1234567890abcdef")
secrets.set_secret("api_secret", "supersecret")

# Retrieve secrets
api_key = secrets.get_secret("api_key")
if api_key:
    # Use the API key
    connect_to_api(api_key)

# Check if secret exists
if secrets.has_secret("database_password"):
    db_pass = secrets.get_secret("database_password")

# Remove secret when no longer needed
secrets.delete_secret("old_api_key")
```

**Security Notes:**
- Secrets are stored in the system keyring (Keychain on macOS, Credential Manager on Windows, Secret Service on Linux)
- Secrets are never stored in plain text files
- Secrets are user-specific and protected by OS-level security
- Always use SecretHandler for passwords, API keys, tokens, and credentials

**Best For:**
- API keys and tokens
- Database passwords
- OAuth client secrets
- Encryption keys
- Any sensitive credentials

---

## Usage Examples

### Basic Usage (Most Common)

**Scenario:** Load application configuration and access settings

```python
from basefunctions.config import ConfigHandler

# Step 1: Create handler
config = ConfigHandler()

# Step 2: Load configuration
config.load_config_for_package("myapp")

# Step 3: Access configuration values
app_name = config.get("app.name", default="MyApp")
port = config.get("server.port", default=8000)
log_level = config.get("logging.level", default="INFO")

# Step 4: Use configuration
print(f"Starting {app_name} on port {port} with log level {log_level}")
```

**Configuration File (./config/myapp.yaml):**
```yaml
app:
  name: "MyApp"
  version: "1.0.0"

server:
  port: 8080
  host: "0.0.0.0"

logging:
  level: "DEBUG"
  file: "logs/app.log"
```

**Expected Output:**
```
Starting MyApp on port 8080 with log level DEBUG
```

---

### Advanced Usage - Secure Credentials

**Scenario:** Store and retrieve database credentials securely

```python
from basefunctions.config import ConfigHandler, SecretHandler

# Step 1: Setup configuration
config = ConfigHandler()
config.load_config_for_package("myapp")

# Step 2: Setup secrets handler
secrets = SecretHandler(service_name="myapp")

# First run: Store credentials (do this once, manually or via setup script)
secrets.set_secret("db_username", "admin")
secrets.set_secret("db_password", "super_secure_password_123")

# Step 3: Retrieve configuration and secrets
db_host = config.get("database.host", default="localhost")
db_port = config.get("database.port", default=5432)
db_name = config.get("database.name", default="myapp_db")

# Retrieve secure credentials
db_user = secrets.get_secret("db_username")
db_pass = secrets.get_secret("db_password")

# Step 4: Connect to database
connection_string = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
db_connect(connection_string)
```

---

### Advanced Usage - Environment-Specific Configuration

**Scenario:** Different settings for development and deployment

```python
from basefunctions.config import ConfigHandler
from basefunctions.runtime import get_runtime_path

config = ConfigHandler()
config.load_config_for_package("myapp")

# Configuration automatically loads from correct location:
# Development: ./config/myapp.yaml
# Deployment: ~/.neuraldevelopment/packages/myapp/config/myapp.yaml

# Access environment-specific settings
api_url = config.get("api.url")  # Different URL per environment
debug = config.get("debug", default=False)

if debug:
    print(f"Running in debug mode with API: {api_url}")
else:
    print(f"Production mode with API: {api_url}")
```

**Development Config (./config/myapp.yaml):**
```yaml
api:
  url: "http://localhost:5000"
debug: true
```

**Deployment Config (~/.neuraldevelopment/packages/myapp/config/myapp.yaml):**
```yaml
api:
  url: "https://api.production.com"
debug: false
```

---

### Integration with Other Components

**Working with Events:**

```python
from basefunctions.config import ConfigHandler
from basefunctions.events import EventBus, Event, EXECUTION_MODE_THREAD

# Load configuration
config = ConfigHandler()
config.load_config_for_package("myapp")

# Create event bus
bus = EventBus()

# Use configuration to control event behavior
max_retries = config.get("events.max_retries", default=3)
timeout = config.get("events.timeout", default=30.0)
async_mode = config.get("events.async", default=True)

# Create event with config-driven settings
event = Event(
    event_type="process.data",
    data={"value": 123},
    mode=EXECUTION_MODE_THREAD if async_mode else EXECUTION_MODE_SYNC,
    retry_count=max_retries,
    timeout=timeout
)

result = bus.publish(event)
```

---

### Custom Implementation Example

**Scenario:** Build a configuration manager with validation

```python
from basefunctions.config import ConfigHandler
from typing import Any

class AppConfig:
    """Application configuration manager with validation"""

    def __init__(self, package_name: str):
        self.config = ConfigHandler()
        self.config.load_config_for_package(package_name)
        self._validate()

    def _validate(self) -> None:
        """Validate required configuration keys"""
        required_keys = [
            "app.name",
            "app.version",
            "database.host",
            "database.name"
        ]

        for key in required_keys:
            if not self.config.has(key):
                raise ValueError(f"Missing required configuration: {key}")

    def get_database_config(self) -> dict[str, Any]:
        """Get database configuration"""
        return {
            "host": self.config.get("database.host"),
            "port": self.config.get("database.port", default=5432),
            "name": self.config.get("database.name"),
            "pool_size": self.config.get("database.pool_size", default=10)
        }

    def get_feature_flags(self) -> dict[str, bool]:
        """Get all feature flags"""
        all_config = self.config.get_all()
        features = all_config.get("features", {})
        return {k: bool(v) for k, v in features.items()}

# Usage
app_config = AppConfig("myapp")
db_config = app_config.get_database_config()
features = app_config.get_feature_flags()

if features.get("new_ui"):
    print("New UI enabled")
```

---

## Configuration File Structure

### Basic Configuration

```yaml
# myapp.yaml
app:
  name: "MyApplication"
  version: "1.0.0"
  debug: false

server:
  host: "0.0.0.0"
  port: 8080
  workers: 4

database:
  host: "localhost"
  port: 5432
  name: "myapp_db"
  pool_size: 10

logging:
  level: "INFO"
  file: "logs/app.log"
  max_size_mb: 100

features:
  new_ui: true
  experimental_api: false
```

### Accessing Nested Configuration

```python
config = ConfigHandler()
config.load_config_for_package("myapp")

# Dot notation for nested keys
app_name = config.get("app.name")
db_host = config.get("database.host")
log_level = config.get("logging.level")
feature_enabled = config.get("features.new_ui")
```

---

## Best Practices

### Best Practice 1: Never Hardcode Secrets

**Why:** Security and flexibility

```python
# GOOD - Use SecretHandler
secrets = SecretHandler("myapp")
api_key = secrets.get_secret("api_key")
```

```python
# AVOID - Hardcoded secrets
api_key = "sk_live_1234567890"  # NEVER DO THIS
```

---

### Best Practice 2: Provide Defaults

**Why:** Robustness and backward compatibility

```python
# GOOD - Defaults ensure code works even if key missing
port = config.get("server.port", default=8080)
timeout = config.get("timeout", default=30.0)
```

```python
# AVOID - No defaults, crashes if key missing
port = config.get("server.port")  # KeyError if not in config
```

---

### Best Practice 3: Validate Configuration Early

**Why:** Fail fast with clear errors

```python
# GOOD - Validate at startup
config = ConfigHandler()
config.load_config_for_package("myapp")

required = ["database.host", "database.name", "api.key"]
for key in required:
    if not config.has(key):
        raise ValueError(f"Missing required config: {key}")

# Now safe to use
db_host = config.get("database.host")
```

```python
# AVOID - No validation, fails later
config = ConfigHandler()
config.load_config_for_package("myapp")
# ... later in code, cryptic error when key missing
```

---

### Best Practice 4: Separate Secrets from Configuration

**Why:** Security and version control safety

```python
# GOOD - Configuration in YAML, secrets in keyring
config = ConfigHandler()
config.load_config_for_package("myapp")
secrets = SecretHandler("myapp")

db_host = config.get("database.host")  # From config file
db_pass = secrets.get_secret("db_password")  # From secure keyring
```

```python
# AVOID - Secrets in configuration file
# config.yaml:
# database:
#   password: "secret123"  # NEVER DO THIS
```

---

## Error Handling

### Common Errors

**Error 1: Configuration File Not Found**

```python
# WRONG - Package config doesn't exist
config = ConfigHandler()
config.load_config_for_package("nonexistent_package")
# FileNotFoundError or silent failure
```

**Solution:**
```python
# CORRECT - Ensure config file exists first
from pathlib import Path

config_file = Path("./config/myapp.yaml")
if not config_file.exists():
    print("Configuration file not found, using defaults")
    # Create default config or use fallback
else:
    config = ConfigHandler()
    config.load_config_for_package("myapp")
```

---

**Error 2: Secret Not Found**

```python
# WRONG - Assuming secret exists
secrets = SecretHandler("myapp")
api_key = secrets.get_secret("api_key")
# Returns None if not found, may cause AttributeError later
```

**Solution:**
```python
# CORRECT - Check if secret exists
secrets = SecretHandler("myapp")
api_key = secrets.get_secret("api_key")

if api_key is None:
    raise ValueError("API key not configured. Run setup first.")

# Or provide fallback
api_key = secrets.get_secret("api_key") or "default_key"
```

---

## Performance Tips

**Tip 1:** Load configuration once at startup
```python
# FAST - Load once, reuse
config = ConfigHandler()
config.load_config_for_package("myapp")

# Use multiple times
value1 = config.get("key1")
value2 = config.get("key2")

# SLOW - Loading multiple times
for i in range(100):
    config = ConfigHandler()  # Don't do this
    config.load_config_for_package("myapp")
```

**Tip 2:** Cache frequently accessed values
```python
# FAST - Cache in variable
db_host = config.get("database.host")
for query in queries:
    connect(db_host)  # Use cached value

# SLOW - Repeated lookups
for query in queries:
    connect(config.get("database.host"))  # Redundant lookups
```

---

## Security Guidelines

### Storing Secrets

**What to Store in SecretHandler:**
- Database passwords
- API keys and tokens
- OAuth client secrets
- Encryption keys
- Private certificates

**What to Store in ConfigHandler:**
- Hostnames and URLs (non-sensitive)
- Port numbers
- Feature flags
- Timeouts and limits
- Application settings

### Example: Secure vs Insecure

```python
# SECURE
config = ConfigHandler()
secrets = SecretHandler("myapp")

config.load_config_for_package("myapp")
secrets.set_secret("stripe_api_key", "sk_live_...")

# Later
api_endpoint = config.get("payment.api_url")  # OK in config
api_key = secrets.get_secret("stripe_api_key")  # Secure

# INSECURE
config = ConfigHandler()
config.set("stripe_api_key", "sk_live_...")  # NEVER DO THIS
```

---

## See Also

**Related Subpackages:**
- `runtime` (`docs/basefunctions/runtime.md`) - Environment detection for config paths
- `events` (`docs/basefunctions/events.md`) - Configuration for event handlers

**System Documentation:**
- `~/.claude/_docs/python/basefunctions.md` - Internal architecture details

---

## Quick Reference

### Imports

```python
from basefunctions.config import ConfigHandler, SecretHandler
```

### Quick Start - Configuration

```python
# Step 1: Create handler
config = ConfigHandler()

# Step 2: Load package config
config.load_config_for_package("myapp")

# Step 3: Access values
value = config.get("key.subkey", default="default_value")

# Step 4: Check existence
if config.has("feature.enabled"):
    enabled = config.get("feature.enabled")
```

### Quick Start - Secrets

```python
# Step 1: Create handler
secrets = SecretHandler(service_name="myapp")

# Step 2: Store secret (once)
secrets.set_secret("api_key", "secret_value")

# Step 3: Retrieve secret
api_key = secrets.get_secret("api_key")

# Step 4: Use secret
if api_key:
    connect_to_service(api_key)
```

### Cheat Sheet

| Task | Code |
|------|------|
| Load config | `config.load_config_for_package("name")` |
| Get value | `config.get("key", default=value)` |
| Set value | `config.set("key", value)` |
| Check key | `config.has("key")` |
| Store secret | `secrets.set_secret("key", "value")` |
| Get secret | `secrets.get_secret("key")` |
| Delete secret | `secrets.delete_secret("key")` |
| Check secret | `secrets.has_secret("key")` |

---

**Document Version:** 0.5.75
**Last Updated:** 2026-01-29
**Subpackage Version:** 0.5.75
