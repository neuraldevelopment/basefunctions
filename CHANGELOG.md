# Changelog

All notable changes to basefunctions will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### =4 BREAKING CHANGES

#### Logging API Complete Rewrite

The logging API has been completely redesigned for simplicity and consistency. The old API has been removed.

**Removed Functions:**
- `setup_logger(name, level, file)` � Use `get_logger()` + `set_log_level()` + `set_log_file()`
- `enable_console(level)` � Use `set_log_console(True, level)`
- `disable_console()` � Use `set_log_console(False)`
- `redirect_all_to_file(file, level)` � Use `set_log_file(file, level)`
- `configure_module_logging()` � Use `set_log_level(level, module=...)`
- `get_module_logging_config()` � No replacement (not needed in new design)
- `enable_logging(enabled)` � No replacement (not needed in new design)

**New Functions:**
- `get_logger(name=None)` - Get logger with auto-detection
- `set_log_level(level, module=None)` - Set global or module-specific level
- `set_log_console(enabled, level=None)` - Enable/disable console output
- `set_log_file(filepath, level=None, rotation=False, rotation_count=3, rotation_size_kb=1024)` - Configure file logging with rotation
- `set_log_file_rotation(enabled, count=3, size_kb=1024)` - Toggle rotation on existing file handler

**Migration Guide:**

```python
# OLD API
from basefunctions.utils.logging import setup_logger, get_logger, enable_console

setup_logger(__name__, level="DEBUG", file="/tmp/app.log")
logger = get_logger(__name__)
enable_console("INFO")

# NEW API
from basefunctions.utils.logging import get_logger, set_log_level, set_log_file, set_log_console

logger = get_logger(__name__)
set_log_level("DEBUG")
set_log_file("/tmp/app.log")
set_log_console(True, "INFO")
```

**Key Improvements:**
-  Simpler API (5 functions instead of 8)
-  Built-in log file rotation support
-  Captures ALL logs (including third-party libraries using `logging.getLogger()`)
-  Explicit control over console and file output
-  Thread-safe operations
-  Better error messages

**See:** `docs/basefunctions/utils.md` for complete documentation and examples.

### Added

- **Config-based Logging Auto-Initialization**: Logging now auto-configures from `config.json` on first `get_logger()` call
  - Zero setup code required in applications
  - Configure once in `config.json`, use everywhere
  - Three config parameters:
    - `basefunctions/log_enabled` (bool, default: false) - Master switch for logging
    - `basefunctions/log_level` (str, default: "INFO") - Global log level
    - `basefunctions/log_file` (str|null, default: null) - Log file path (null = console)
  - Silent operation: No exceptions if config unavailable
  - Manual setup still works and overrides auto-init
  - Example config:
    ```json
    {
      "basefunctions": {
        "log_enabled": true,
        "log_level": "DEBUG",
        "log_file": "/var/log/myapp/app.log"
      }
    }
    ```
  - All apps using basefunctions automatically log to same file with zero code changes
- File rotation support via `set_log_file()` with `rotation=True`
- Auto-detection of module name in `get_logger()` when called without arguments
- Module-specific log level configuration via `set_log_level(level, module="...")`

### Changed

- Logging system now captures all logs by default, including direct `logging.getLogger()` usage
- `get_standard_log_directory()` remains unchanged and compatible
- **Migrated 30 internal modules from deprecated `setup_logger()` to `get_logger()`**
  - All CLI, Config, Events, HTTP, IO, Pandas, Runtime, and Utils modules updated
  - Eliminates DeprecationWarnings in test output
  - Uses new logging API throughout codebase

### Fixed

- Fixed inconsistent logger initialization across codebase (6 modules updated)
- Improved thread-safety for all logging operations
- **Runtime path detection now supports nested directory structures**
  - Packages in subdirectories (e.g., `~/Code/neuraldev/basefunctions`) are now correctly detected as development environment
  - Previously only direct paths (e.g., `~/Code/basefunctions`) were recognized
  - Affects: `get_runtime_path()`, `get_runtime_log_path()`, `get_standard_log_directory()`
  - Users with nested project structures no longer fall back to deployment paths incorrectly

---

## [0.5.94] - 2026-02-22

- (Previous changes - if any)
