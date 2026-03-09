# Runtime - User Documentation

**Package:** basefunctions
**Subpackage:** runtime
**Purpose:** Runtime environment detection and path management for development/deployment environments

---

## Overview

The `basefunctions.runtime` subpackage provides intelligent environment detection and path resolution
for packages that exist in both a local development directory and a deployed installation. It reads a
bootstrap configuration file to understand where development and deployment directories live, then
uses the current working directory to determine which environment is active at runtime. This removes
the need for hardcoded paths or environment variables in every package that builds on basefunctions.

**Key Features:**

- CWD-based automatic detection of development vs. deployment context
- Bootstrap configuration with sensible defaults — works without any manual setup
- Complete package structure initialization for both development and deployed packages
- Hash-based change detection in `DeploymentManager` to skip redundant deployments
- All-static `VenvUtils` class for virtual environment inspection and management

**Common Use Cases:**

- Load the config directory of any package without knowing where it is installed
- Detect whether code is running from source or from a deployed copy
- Initialize the standard directory structure for a new package
- Deploy a development module to the deployment directory
- Inspect installed packages and manage dependencies in a virtual environment

---

## Architecture: Development vs. Deployment

Every package managed by basefunctions lives in exactly two places:

| Environment | Base path (default) | Example for `mypkg` |
|-------------|--------------------|--------------------|
| Development | `~/Code` (configurable) | `~/Code/neuraldev/mypkg` |
| Deployment  | `~/.neuraldevelopment` | `~/.neuraldevelopment/packages/mypkg` |

The runtime subpackage detects the active environment by comparing the current working directory
against all known development directories. If the CWD is located inside a known development
directory, the development path is returned. Otherwise the deployment path is used as a fallback.
All path-returning functions return `str`, not `pathlib.Path`.

---

## Bootstrap Configuration

The bootstrap configuration file controls where basefunctions looks for development and deployment
directories. It is the single source of truth for all path resolution.

**Location:** `~/.config/basefunctions/bootstrap.json`

**Default content (auto-created if missing):**

```json
{
  "bootstrap": {
    "paths": {
      "deployment_directory": "~/.neuraldevelopment",
      "development_directories": ["~/Code", "~/Development"]
    }
  }
}
```

If the file does not exist, basefunctions creates it automatically with the defaults shown above the
first time any runtime function is called. You do not need to create it manually.

**Common customization — restrict to a single development root:**

```json
{
  "bootstrap": {
    "paths": {
      "deployment_directory": "~/.neuraldevelopment",
      "development_directories": ["~/Code/neuraldev", "~/Code/neuraldev-utils"]
    }
  }
}
```

**Programmatic access:**

```python
from basefunctions.runtime import (
    get_bootstrap_config_path,
    get_bootstrap_deployment_directory,
    get_bootstrap_development_directories,
)

print(get_bootstrap_config_path())
# "~/.config/basefunctions/bootstrap.json"

print(get_bootstrap_deployment_directory())
# "/Users/me/.neuraldevelopment"

print(get_bootstrap_development_directories())
# ["/Users/me/Code", "/Users/me/Development"]
```

---

## Path Resolution Functions

### get_runtime_path()

```python
def get_runtime_path(package_name: str) -> str
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `package_name` | `str` | Name of the package to locate |

Returns the root directory of `package_name` — either the development checkout or the deployed
copy — based entirely on the current working directory at the time of the call.

**Algorithm (step by step):**

1. Load the bootstrap config to get `dev_dirs` (list) and `deploy_dir`.
2. Normalize and expand all `dev_dirs`, then sort them by string length in descending order so that
   more specific (longer) paths are checked before shorter parent paths.
3. Resolve `Path.cwd()`.
4. For each `dev_dir` in the sorted list, attempt `cwd.relative_to(dev_dir)`:
   - If the CWD is not under this `dev_dir`, a `ValueError` is raised internally and the next
     entry is tried.
   - If the CWD is under this `dev_dir`, extract the path components (e.g. `["neuraldev",
     "basefunctions", "src"]`).
   - Search those components for `package_name`. If found at index `idx`, return
     `str(dev_dir / Path(*parts[:idx+1]))` — the package root inside the development tree.
5. If no `dev_dir` matched, return the deployment fallback:
   `str(normalize(deploy_dir) / "packages" / package_name)`.

**Scenarios with examples:**

```python
from basefunctions.runtime import get_runtime_path

# Scenario 1: CWD is ~/Code/neuraldev/mypkg/src
# Returns development path
path = get_runtime_path("mypkg")
# "/Users/me/Code/neuraldev/mypkg"

# Scenario 2: CWD is ~/Code/neuraldev/mypkg/tests/unit
# Still finds "mypkg" in the path components — development path returned
path = get_runtime_path("mypkg")
# "/Users/me/Code/neuraldev/mypkg"

# Scenario 3: CWD is ~/Desktop (not under any dev_dir)
# Falls back to deployment path
path = get_runtime_path("mypkg")
# "/Users/me/.neuraldevelopment/packages/mypkg"
```

---

### get_deployment_path()

```python
def get_deployment_path(package_name: str) -> str
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `package_name` | `str` | Name of the package to locate |

Always returns the deployment path for `package_name`, regardless of the current working directory.
Use this when you explicitly need the deployed copy, for example when reading installed configs.

```python
from basefunctions.runtime import get_deployment_path

path = get_deployment_path("mypkg")
# "/Users/me/.neuraldevelopment/packages/mypkg"
# — same result no matter where you call it from
```

---

### get_runtime_component_path()

```python
def get_runtime_component_path(package_name: str, component: str) -> str
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `package_name` | `str` | Name of the package |
| `component` | `str` | Subdirectory name (e.g. `"config"`, `"logs"`, `"templates/config"`) |

Returns `get_runtime_path(package_name) + "/" + component`. Use the specific shortcut functions
below when you need `config`, `logs`, or `templates/config`.

```python
from basefunctions.runtime import get_runtime_component_path

path = get_runtime_component_path("mypkg", "data")
# "/Users/me/Code/neuraldev/mypkg/data"
```

---

### get_runtime_config_path()

```python
def get_runtime_config_path(package_name: str) -> str
```

Shortcut for `get_runtime_component_path(package_name, "config")`.

```python
from basefunctions.runtime import get_runtime_config_path

config_dir = get_runtime_config_path("mypkg")
# "/Users/me/Code/neuraldev/mypkg/config"
```

---

### get_runtime_log_path()

```python
def get_runtime_log_path(package_name: str) -> str
```

Shortcut for `get_runtime_component_path(package_name, "logs")`.

```python
from basefunctions.runtime import get_runtime_log_path

log_dir = get_runtime_log_path("mypkg")
# "/Users/me/Code/neuraldev/mypkg/logs"
```

---

### get_runtime_template_path()

```python
def get_runtime_template_path(package_name: str) -> str
```

Shortcut for `get_runtime_component_path(package_name, "templates/config")`.

```python
from basefunctions.runtime import get_runtime_template_path

tmpl_dir = get_runtime_template_path("mypkg")
# "/Users/me/Code/neuraldev/mypkg/templates/config"
```

---

### get_runtime_completion_path()

```python
def get_runtime_completion_path(package_name: str, tool_name: str | None = None) -> str
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `package_name` | `str` | — | Name of the package |
| `tool_name` | `str \| None` | `None` | Name of the CLI tool (used in the filename) |

Returns the path for a shell completion file. The detection logic and the filename format differ
between development and deployment contexts.

**CWD detection algorithm:**

1. Load `dev_dirs` (sorted longest-first) and `deploy_dir` from the bootstrap config.
2. Resolve `Path.cwd()`.
3. For each `dev_dir`, compute `package_dir = dev_dir / package_name`. If the CWD equals
   `package_dir` or `package_dir` is one of the CWD's parents, this is the development context.
4. In development: create `<package_dir>/.cli/` and return
   `str(<package_dir>/.cli/<package_name>_<tool_name>.completion)` (uses a dot extension).
5. Fallback (deployment): create `~/.neuraldevelopment/completion/` and return
   `str(~/.neuraldevelopment/completion/<package_name>_<tool_name>_completion)` (no dot extension,
   underscore separator).

**Filename format comparison:**

| Context     | Format                              | Example                          |
|-------------|-------------------------------------|----------------------------------|
| Development | `{package}_{tool}.completion`       | `mypkg_cli.completion`           |
| Deployment  | `{package}_{tool}_completion`       | `mypkg_cli_completion`           |

```python
from basefunctions.runtime import get_runtime_completion_path

# Development context (CWD inside ~/Code/neuraldev/mypkg)
path = get_runtime_completion_path("mypkg", "cli")
# "/Users/me/Code/neuraldev/mypkg/.cli/mypkg_cli.completion"

# Deployment context (CWD outside any dev_dir)
path = get_runtime_completion_path("mypkg", "cli")
# "/Users/me/.neuraldevelopment/completion/mypkg_cli_completion"
```

---

## Development Path Search

### find_development_path()

```python
def find_development_path(package_name: str, max_depth: int = 3) -> list[str]
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `package_name` | `str` | — | Directory name to search for |
| `max_depth` | `int` | `3` | Maximum recursion depth from each dev root |

Recursively searches all configured development directories for a directory whose name matches
`package_name`. Returns a list of all matching paths found. The list may be empty (not found),
contain one element (normal case), or contain multiple elements (same package cloned in several
development roots).

**Full recursive algorithm:**

1. Initialize `found_paths = []` and `visited_paths = set()` (symlink loop guard).
2. For each `dev_dir` in `get_bootstrap_development_directories()`: normalize and verify it exists.
3. Call `_search_recursive(dev_path, depth=0)`:
   - Resolve the real path of `base_path`. If already in `visited_paths`, return immediately
     (prevents infinite loops through symlinks).
   - If `current_depth > max_depth`, return (depth guard).
   - Iterate `base_path.iterdir()`:
     - If `item.name == package_name` and `item.is_dir()`: append `str(item)` to `found_paths`.
     - Else if `item.is_dir()`: recurse with `current_depth + 1`.
     - `OSError` and `PermissionError` are silently skipped.
4. Return `found_paths`.

```python
from basefunctions.runtime import find_development_path

# Normal case — one result
paths = find_development_path("mypkg")
# ["/Users/me/Code/neuraldev/mypkg"]

# Not found — empty list
paths = find_development_path("nonexistent")
# []

# Package exists in two dev roots — multiple results
paths = find_development_path("sharedlib")
# ["/Users/me/Code/neuraldev/sharedlib",
#  "/Users/me/Code/neuraldev-utils/sharedlib"]

# Branch on result
if paths:
    print(f"Found at: {paths[0]}")
else:
    print("Not in development — using deployed copy")
```

---

### get_bootstrap_development_directories()

```python
def get_bootstrap_development_directories() -> list
```

Returns the list of expanded development directory paths from the bootstrap config.

```python
from basefunctions.runtime import get_bootstrap_development_directories

dirs = get_bootstrap_development_directories()
# ["/Users/me/Code", "/Users/me/Development"]
```

---

### get_bootstrap_deployment_directory()

```python
def get_bootstrap_deployment_directory() -> str
```

Returns the expanded deployment base directory from the bootstrap config.

```python
from basefunctions.runtime import get_bootstrap_deployment_directory

deploy = get_bootstrap_deployment_directory()
# "/Users/me/.neuraldevelopment"
```

---

### get_bootstrap_config_path()

```python
def get_bootstrap_config_path() -> str
```

Returns the constant path to the bootstrap configuration file. This function always returns the
same string: `"~/.config/basefunctions/bootstrap.json"` (unexpanded).

```python
from basefunctions.runtime import get_bootstrap_config_path

path = get_bootstrap_config_path()
# "~/.config/basefunctions/bootstrap.json"
```

---

## Package Structure Management

These functions create the standard directory structure for a package under the deployment root.
Call them once during initial setup or at startup to ensure required directories exist.

### create_root_structure()

```python
def create_root_structure() -> None
```

Creates the top-level deployment root structure:

```
~/.neuraldevelopment/
├── bin/
└── packages/
```

Call this once before deploying any package for the first time.

```python
from basefunctions.runtime import create_root_structure

create_root_structure()
```

---

### create_bootstrap_package_structure()

```python
def create_bootstrap_package_structure(package_name: str) -> None
```

**Raises:** `ValueError` if `package_name` is empty.

Creates the minimal bootstrap directory structure for `package_name` under the deployment path:

```
~/.neuraldevelopment/packages/<package_name>/
├── config/
└── templates/
    └── config/
```

These are the directories defined in `BOOTSTRAP_DIRECTORIES = ["config", "templates/config"]`.

```python
from basefunctions.runtime import create_bootstrap_package_structure

create_bootstrap_package_structure("mypkg")
```

---

### create_full_package_structure()

```python
def create_full_package_structure(package_name: str, custom_directories: list = None) -> None
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `package_name` | `str` | — | Target package name |
| `custom_directories` | `list \| None` | `None` | Additional subdirectories to create |

**Raises:** `ValueError` if `package_name` is empty.

Creates the full standard directory structure under the deployment path. The default directories
are defined by `DEFAULT_PACKAGE_DIRECTORIES = ["config", "logs", "templates/config"]`. If
`custom_directories` is provided, those directories are created in addition to the defaults.

```python
from basefunctions.runtime import create_full_package_structure

# Default structure only
create_full_package_structure("mypkg")
# Creates: config/, logs/, templates/config/

# With extra directories
create_full_package_structure("mypkg", custom_directories=["cache", "exports"])
# Creates: config/, logs/, templates/config/, cache/, exports/
```

---

### ensure_bootstrap_package_structure()

```python
def ensure_bootstrap_package_structure(package_name: str) -> None
```

Safe to call any number of times. Creates the bootstrap structure only if the directories do not
already exist. Use this at package startup to guarantee that required directories are available
without raising errors on repeated calls.

```python
from basefunctions.runtime import ensure_bootstrap_package_structure

# Safe to call at every startup
ensure_bootstrap_package_structure("mypkg")
```

---

## Version Utilities

### version()

```python
def version(package_name: str = "basefunctions") -> str
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `package_name` | `str` | `"basefunctions"` | Package whose version to retrieve |

Returns the version string for `package_name`. The function uses a 3-step resolution strategy to
return the most informative version string available for the current context.

**3-step resolution algorithm:**

1. **Find package root with pyproject.toml:**
   - Call `find_development_path(package_name)`. For each result, check whether the CWD starts
     with that path AND the directory contains `pyproject.toml`. If yes, use that as the root.
   - If not found in development, call `get_deployment_path(package_name)`. Check whether the CWD
     starts with that path AND `pyproject.toml` exists there.
   - Returns `None` if neither location qualifies.

2. **If a package root was found:**
   - Read `pyproject.toml` using `tomllib` (Python 3.11+), `tomli`, or a regex fallback.
   - Extract `project.version` as `base_version`.
   - Run `git describe --tags --abbrev=0` to get the latest tag, then
     `git rev-list {tag}..HEAD --count` to count commits since that tag.
   - Return the version string according to `commits_ahead`:
     - `> 0` → `f"{base_version}-dev+{commits_ahead}"`
     - `== 0` → `f"{base_version}-dev"`
   - Any git error returns 0 commits ahead (treated as "at tag").

3. **Fallback:** `importlib.metadata.version(package_name)` — the version from the installed
   package metadata. Any exception at any point returns `"unknown"`.

**Version string format:**

| Scenario | Example | Meaning |
|----------|---------|---------|
| Deployed (pip/ppip) | `"0.5.98"` | Installed version from `importlib.metadata` |
| Development, at tag | `"0.5.98-dev"` | `pyproject.toml` version, 0 commits ahead of latest tag |
| Development, ahead | `"0.5.98-dev+3"` | `pyproject.toml` version, 3 commits ahead of latest tag |

```python
from basefunctions.runtime import version

# Query basefunctions itself (default)
v = version()
# "0.5.98-dev+2"

# Query another package
v = version("mypkg")
# "1.2.0-dev"

# Unknown package
v = version("doesnotexist")
# "unknown"
```

---

### versions()

```python
def versions() -> dict[str, str]
```

Returns a dictionary mapping every package name found under
`~/.neuraldevelopment/packages/` to its version string as reported by `version()`.

```python
from basefunctions.runtime import versions

all_versions = versions()
# {
#   "basefunctions": "0.5.98",
#   "mypkg": "1.2.0",
#   "anotherpkg": "0.3.1",
# }

for pkg, ver in all_versions.items():
    print(f"{pkg}: {ver}")
```

---

## DeploymentManager

`DeploymentManager` is decorated with `@basefunctions.singleton`, meaning only one instance exists
per Python process. Every call to `DeploymentManager()` returns the same object. Import and
instantiate it directly — no factory function is needed.

```python
from basefunctions.runtime import DeploymentManager

dm = DeploymentManager()   # creates instance on first call
dm2 = DeploymentManager()  # returns the same instance
assert dm is dm2            # True
```

---

### deploy_module()

```python
def deploy_module(self, module_name: str, force: bool = False, version: str | None = None) -> tuple[bool, str]
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `module_name` | `str` | — | Name of the module/package to deploy |
| `force` | `bool` | `False` | Skip change detection and always redeploy |
| `version` | `str \| None` | `None` | Override version string (uses detected version if `None`) |

**Returns:** `tuple[bool, str]` — `(was_deployed, version_string)`

- `was_deployed` is `False` when no changes were detected and deployment was skipped.
- `version_string` is the version of the module after the operation.

**5-step deployment pipeline:**

1. **Validate:** `module_name` must not be empty (`DeploymentError` otherwise).

2. **Context check:** Call `find_development_path(module_name)`. At least one development path must
   be found, and the CWD must start with one of them. You must run `deploy_module` from inside
   the package's development directory, otherwise `DeploymentError` is raised.

3. **Change detection** (skipped when `force=True`):
   - Compute a combined SHA256 hash covering: `.py` file modification times in `src/`, the output
     of `pip freeze`, `bin/` script modification times, `templates/` modification times, and
     deployment timestamps of declared dependencies.
   - Compare with the stored hash in `~/.neuraldevelopment/deployment/hashes/{module_name}.hash`.
   - If hashes match: print "No changes detected", return `(False, version)`.

4. **Deploy:**
   - Validate that the target path is safe (not a system directory, not the home directory, must
     be within the configured `deploy_dir`).
   - Remove the existing target directory with `shutil.rmtree`.
   - Create the target directory and a `logs/` subdirectory.
   - Copy `.venv` to the target.
   - Copy `templates/config/` to the target.
   - Initialize `config/` structure.
   - Copy `bin/` scripts and create venv-activating shell wrappers for each tool. Tools in
     `NO_VENV_TOOLS` are deployed as-is without a wrapper:
     `clean_virtual_environment`, `ppip`, `update_packages`, `deploy_manager`
     (and their `.py` variants).

5. **Finalize:** Write the new hash to disk, return `(True, version)`.

**Raises `DeploymentError` when:**
- `module_name` is empty
- No development path found for `module_name`
- CWD is not inside the development directory of `module_name`
- Target path fails safety validation

```python
from basefunctions.runtime import DeploymentManager, DeploymentError

dm = DeploymentManager()

# Standard deploy (change detection active)
deployed, ver = dm.deploy_module("mypkg")
if deployed:
    print(f"Deployed version {ver}")
else:
    print(f"No changes — still at {ver}")

# Force redeploy regardless of changes
deployed, ver = dm.deploy_module("mypkg", force=True)

# Handle errors
try:
    dm.deploy_module("mypkg")
except DeploymentError as e:
    print(f"Deployment failed: {e}")
```

---

### clean_deployment()

```python
def clean_deployment(self, module_name: str) -> None
```

Completely removes the deployment of `module_name`. Specifically:

1. Resolves the deployment path via `get_deployment_path(module_name)`.
2. Validates path safety (same rules as `deploy_module`).
3. Removes the entire deployment directory with `shutil.rmtree`.
4. Removes all global bin wrappers for this module from `~/.neuraldevelopment/bin/`.
5. Removes the stored change-detection hash from
   `~/.neuraldevelopment/deployment/hashes/{module_name}.hash`.

```python
from basefunctions.runtime import DeploymentManager

dm = DeploymentManager()
dm.clean_deployment("mypkg")
# mypkg is fully removed from the deployment location
```

---

### DeploymentError

```python
class DeploymentError(Exception)
```

Raised by `DeploymentManager` when a deployment operation cannot proceed. See the error message
for the specific reason (empty name, wrong CWD, unsafe target path).

---

## VenvUtils

`VenvUtils` is a utility class with exclusively static methods — you never instantiate it. Import
the class and call methods directly on it.

```python
from basefunctions.runtime import VenvUtils, VenvUtilsError
from pathlib import Path

venv = Path("/Users/me/Code/neuraldev/mypkg/.venv")
```

**Constants:**

- `PROTECTED_PACKAGES = ["pip", "setuptools", "wheel"]` — excluded from `get_installed_packages`
  by default
- `DEFAULT_VENV_NAME = ".venv"` — default venv directory name for `find_venv_in_directory`

---

### Platform Utilities

#### get_pip_executable()

```python
@staticmethod def get_pip_executable(venv_path: Path) -> Path
```

Returns the platform-correct path to `pip` inside the given venv.
- Unix/macOS: `<venv_path>/bin/pip`
- Windows: `<venv_path>/Scripts/pip.exe`

```python
pip = VenvUtils.get_pip_executable(venv)
# Path("/Users/me/Code/neuraldev/mypkg/.venv/bin/pip")
```

---

#### get_python_executable()

```python
@staticmethod def get_python_executable(venv_path: Path) -> Path
```

Returns the platform-correct path to `python` inside the given venv.
- Unix/macOS: `<venv_path>/bin/python`
- Windows: `<venv_path>/Scripts/python.exe`

```python
python = VenvUtils.get_python_executable(venv)
# Path("/Users/me/Code/neuraldev/mypkg/.venv/bin/python")
```

---

#### get_activate_script()

```python
@staticmethod def get_activate_script(venv_path: Path) -> Path
```

Returns the platform-correct path to the activation script.
- Unix/macOS: `<venv_path>/bin/activate`
- Windows: `<venv_path>/Scripts/activate.bat`

```python
activate = VenvUtils.get_activate_script(venv)
# Path("/Users/me/Code/neuraldev/mypkg/.venv/bin/activate")
```

---

### Environment Detection

#### is_virtual_environment()

```python
@staticmethod def is_virtual_environment() -> bool
```

Returns `True` if the current Python process is running inside a virtual environment. Checks for
the presence of `sys.real_prefix` (set by virtualenv) or compares `sys.base_prefix` with
`sys.prefix` (set by venv).

```python
if VenvUtils.is_virtual_environment():
    print("Running inside a venv")
```

---

#### is_valid_venv()

```python
@staticmethod def is_valid_venv(venv_path: Path) -> bool
```

Returns `True` if `venv_path` exists, is a directory, and contains both a pip executable and a
python executable. All four conditions must hold.

```python
if VenvUtils.is_valid_venv(venv):
    print("Venv is healthy")
```

---

#### find_venv_in_directory()

```python
@staticmethod def find_venv_in_directory(
    directory: Path,
    venv_name: str = ".venv"
) -> Path | None
```

Looks for `directory / venv_name` and validates it with `is_valid_venv`. Returns the `Path` if
valid, `None` otherwise.

```python
pkg_dir = Path("/Users/me/Code/neuraldev/mypkg")
venv = VenvUtils.find_venv_in_directory(pkg_dir)
if venv:
    print(f"Found venv at {venv}")
```

---

### Package Management

#### get_installed_packages()

```python
@staticmethod def get_installed_packages(
    venv_path: Path | None = None,
    include_protected: bool = False,
    capture_output: bool = True,
) -> list[str]
```

Returns a list of installed package names by running `pip list --format=freeze` inside the venv.
When `venv_path` is `None`, uses the currently active Python environment. Protected packages
(`pip`, `setuptools`, `wheel`) are excluded by default unless `include_protected=True`.

**Raises:** `VenvUtilsError` if pip execution fails.

```python
packages = VenvUtils.get_installed_packages(venv)
# ["requests", "numpy", "pandas", ...]

# Include pip/setuptools/wheel
all_pkgs = VenvUtils.get_installed_packages(venv, include_protected=True)
```

---

#### get_package_info()

```python
@staticmethod def get_package_info(
    package_name: str,
    venv_path: Path | None = None,
    capture_output: bool = True,
) -> dict | None
```

Runs `pip show <package_name>` and parses the output into a dictionary. Returns `None` if the
package is not installed. When `venv_path` is `None`, uses the active environment.

```python
info = VenvUtils.get_package_info("requests", venv)
if info:
    print(info["Version"])
# None if not installed
```

---

#### run_pip_command()

```python
@staticmethod def run_pip_command(
    command: list[str],
    venv_path: Path | None = None,
    timeout: int = 300,
    capture_output: bool = True,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `command` | `list[str]` | — | pip subcommand and arguments (e.g. `["install", "requests"]`) |
| `venv_path` | `Path \| None` | `None` | Venv to use; `None` = active environment |
| `timeout` | `int` | `300` | Seconds before the subprocess is killed |
| `capture_output` | `bool` | `True` | Capture stdout/stderr |
| `cwd` | `Path \| None` | `None` | Working directory for the subprocess |

Builds `full_command = [pip_executable] + command` and runs it. Returns the
`subprocess.CompletedProcess` result.

**Raises:** `VenvUtilsError` if the command exits with a non-zero return code.

```python
result = VenvUtils.run_pip_command(["install", "requests"], venv)
```

---

#### upgrade_pip()

```python
@staticmethod def upgrade_pip(venv_path: Path, capture_output: bool = True) -> None
```

Upgrades pip inside the given venv by calling
`run_pip_command(["install", "--upgrade", "pip"])`.

**Raises:** `VenvUtilsError` if the upgrade fails.

```python
VenvUtils.upgrade_pip(venv)
```

---

#### install_requirements()

```python
@staticmethod def install_requirements(
    venv_path: Path,
    requirements_file: Path,
    capture_output: bool = True,
) -> None
```

Installs packages from a `requirements.txt` file. Validates that `requirements_file` exists before
running the install command.

**Raises:** `VenvUtilsError` if the file does not exist or if installation fails.

```python
from pathlib import Path

reqs = Path("/Users/me/Code/neuraldev/mypkg/requirements.txt")
VenvUtils.install_requirements(venv, reqs)
```

---

#### uninstall_packages()

```python
@staticmethod def uninstall_packages(
    packages: list[str],
    venv_path: Path | None = None,
    capture_output: bool = True,
) -> None
```

Uninstalls the given list of packages from the venv by running
`pip uninstall -y <packages...>`. No-op if `packages` is empty. When `venv_path` is `None`,
uses the active environment.

```python
VenvUtils.uninstall_packages(["requests", "urllib3"], venv)
```

---

#### install_with_ppip()

```python
@staticmethod def install_with_ppip(
    packages: list[str],
    venv_path: Path | None = None,
    fallback_to_pip: bool = True,
) -> None
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `packages` | `list[str]` | — | Package names to install |
| `venv_path` | `Path \| None` | `None` | Target venv; `None` = active environment |
| `fallback_to_pip` | `bool` | `True` | Fall back to standard pip if ppip not found |

Installs packages using `ppip` (the local-first package manager for neuraldevelopment), with an
optional fallback to standard `pip`. This is the preferred installation method because `ppip`
resolves packages from the local deployment directory before falling back to PyPI.

**3-branch logic:**

1. **ppip found** (`shutil.which("ppip")` returns a path):
   - Sets `VIRTUAL_ENV` environment variable to `str(venv_path)` (so ppip activates the correct
     venv).
   - Prepends the venv's `bin/` to `PATH`.
   - Runs `ppip install <packages...>`.

2. **ppip not found + `fallback_to_pip=True`:**
   - Falls back to `run_pip_command(["install"] + packages, venv_path)`.
   - Logs a warning that ppip was not available.

3. **ppip not found + `fallback_to_pip=False`:**
   - Raises `VenvUtilsError` immediately — ppip is required and not available.

**Raises:** `VenvUtilsError` in branch 3, or if the chosen installer returns a non-zero exit code.

```python
from basefunctions.runtime import VenvUtils, VenvUtilsError
from pathlib import Path

venv = Path("/Users/me/Code/neuraldev/mypkg/.venv")

# Preferred: ppip with pip fallback (default)
VenvUtils.install_with_ppip(["requests", "numpy"], venv)

# Require ppip — fail if not available
try:
    VenvUtils.install_with_ppip(["mylocalpkg"], venv, fallback_to_pip=False)
except VenvUtilsError as e:
    print(f"ppip required but not found: {e}")

# Install into the currently active environment
VenvUtils.install_with_ppip(["requests"])
```

---

### Utility Methods

#### get_venv_size()

```python
@staticmethod def get_venv_size(venv_path: Path) -> int
```

Returns the total size of the virtual environment in bytes by recursively globbing all files under
`venv_path` and summing their `st_size` values.

```python
size_bytes = VenvUtils.get_venv_size(venv)
# 45678901
```

---

#### format_size()

```python
@staticmethod def format_size(size_bytes: int | float) -> str
```

Converts a raw byte count to a human-readable string with one decimal place. Thresholds:
`< 1 KB` -> bytes, `< 1 MB` -> KB, `< 1 GB` -> MB, `< 1 TB` -> GB, else TB.

```python
size = VenvUtils.format_size(VenvUtils.get_venv_size(venv))
# "43.5 MB"

VenvUtils.format_size(512)
# "512 bytes"

VenvUtils.format_size(1536)
# "1.5 KB"
```

---

### VenvUtilsError

```python
class VenvUtilsError(Exception)
```

Raised by `VenvUtils` methods when a venv operation fails. This includes failed pip/ppip commands,
missing requirements files, and situations where ppip is required but absent.

---

## Usage Examples

### Example 1: Load package configuration (most common)

```python
from basefunctions.runtime import get_runtime_config_path
from pathlib import Path

config_dir = Path(get_runtime_config_path("mypkg"))
config_file = config_dir / "settings.yaml"

if config_file.exists():
    with config_file.open() as f:
        # load config
        pass
```

---

### Example 2: Detect environment and branch logic

```python
from basefunctions.runtime import find_development_path, get_deployment_path

dev_paths = find_development_path("mypkg")

if dev_paths:
    print(f"Running from development: {dev_paths[0]}")
    data_dir = dev_paths[0] + "/testdata"
else:
    print(f"Running from deployment: {get_deployment_path('mypkg')}")
    data_dir = get_deployment_path("mypkg") + "/data"
```

---

### Example 3: Initialize package structure before first use

```python
from basefunctions.runtime import (
    ensure_bootstrap_package_structure,
    get_runtime_config_path,
)
from pathlib import Path

# Idempotent — safe to call every time the package starts
ensure_bootstrap_package_structure("mypkg")

config_dir = Path(get_runtime_config_path("mypkg"))
# config_dir is now guaranteed to exist
```

---

### Example 4: Get version info for all local packages

```python
from basefunctions.runtime import versions

for pkg_name, pkg_version in versions().items():
    print(f"{pkg_name:30s} {pkg_version}")
```

---

### Example 5: Deploy a module

```python
from basefunctions.runtime import DeploymentManager, DeploymentError

dm = DeploymentManager()

try:
    deployed, ver = dm.deploy_module("mypkg")
    if deployed:
        print(f"Successfully deployed mypkg {ver}")
    else:
        print(f"No changes — mypkg {ver} is up to date")
except DeploymentError as e:
    print(f"Deployment failed: {e}")
```

---

### Example 6: Inspect and manage a virtual environment

```python
from basefunctions.runtime import VenvUtils
from pathlib import Path

venv = Path("/Users/me/Code/neuraldev/mypkg/.venv")

if not VenvUtils.is_valid_venv(venv):
    print("Venv is missing or broken")
else:
    packages = VenvUtils.get_installed_packages(venv)
    size = VenvUtils.format_size(VenvUtils.get_venv_size(venv))
    print(f"{len(packages)} packages, venv size: {size}")

    info = VenvUtils.get_package_info("requests", venv)
    if info:
        print(f"requests {info['Version']}")
```

---

### Example 7: Install with ppip (local-first)

```python
from basefunctions.runtime import VenvUtils, VenvUtilsError
from pathlib import Path

venv = Path("/Users/me/Code/neuraldev/mypkg/.venv")

# Preferred: try ppip, fall back to pip
VenvUtils.install_with_ppip(["basefunctions", "requests"], venv)

# Require ppip — local packages that cannot be found on PyPI
try:
    VenvUtils.install_with_ppip(
        ["mylocalpkg"],
        venv,
        fallback_to_pip=False,
    )
except VenvUtilsError as e:
    print(f"Install failed: {e}")
```

---

## Error Handling

### Common Errors and Solutions

| Error | Raised By | Cause | Solution |
|-------|-----------|-------|----------|
| `DeploymentError` | `deploy_module` | `module_name` is empty | Pass a non-empty module name |
| `DeploymentError` | `deploy_module` | No development path found | Ensure the package is checked out in a configured dev directory |
| `DeploymentError` | `deploy_module` | CWD not inside dev directory | `cd` into the package's development directory before deploying |
| `DeploymentError` | `deploy_module` / `clean_deployment` | Target path fails safety check | Verify the bootstrap config's `deployment_directory` is set correctly |
| `VenvUtilsError` | `get_installed_packages` | pip execution failed | Check that the venv is valid with `is_valid_venv` first |
| `VenvUtilsError` | `install_requirements` | Requirements file missing | Verify the file path before calling |
| `VenvUtilsError` | `install_with_ppip` | ppip not found, `fallback_to_pip=False` | Install ppip or set `fallback_to_pip=True` |
| `ValueError` | `create_bootstrap_package_structure` | Empty `package_name` | Pass a non-empty string |
| `ValueError` | `create_full_package_structure` | Empty `package_name` | Pass a non-empty string |

---

## Best Practices

**Use `get_runtime_config_path` instead of hardcoding paths.**

```python
# GOOD
config_dir = Path(get_runtime_config_path("mypkg"))

# AVOID
config_dir = Path.home() / ".neuraldevelopment" / "packages" / "mypkg" / "config"
```

---

**Use `ensure_bootstrap_package_structure` at package startup.**

```python
# GOOD — idempotent, safe every run
ensure_bootstrap_package_structure("mypkg")

# AVOID — will fail on second run
create_bootstrap_package_structure("mypkg")
```

---

**Check `find_development_path` before assuming development context.**

```python
# GOOD
paths = find_development_path("mypkg")
is_dev = bool(paths)

# AVOID — get_runtime_path may still return deployment path
path = get_runtime_path("mypkg")
is_dev = "Code" in path  # brittle and wrong
```

---

**Always handle `DeploymentError` when calling `deploy_module`.**

```python
# GOOD
try:
    deployed, ver = dm.deploy_module("mypkg")
except DeploymentError as e:
    logger.error("Deploy failed: %s", e)
    raise

# AVOID — silent failure masks real problems
deployed, ver = dm.deploy_module("mypkg")
```

---

**Prefer `install_with_ppip` over `run_pip_command` for package installation.**

```python
# GOOD — respects local-first resolution
VenvUtils.install_with_ppip(["basefunctions"], venv)

# AVOID for local packages — bypasses local-first resolution
VenvUtils.run_pip_command(["install", "basefunctions"], venv)
```

---

## Quick Reference

### Imports

```python
# Path resolution
from basefunctions.runtime import (
    get_runtime_path,
    get_runtime_config_path,
    get_runtime_log_path,
    get_runtime_template_path,
    get_runtime_component_path,
    get_runtime_completion_path,
    get_deployment_path,
    find_development_path,
)

# Bootstrap config
from basefunctions.runtime import (
    get_bootstrap_config_path,
    get_bootstrap_deployment_directory,
    get_bootstrap_development_directories,
)

# Package structure
from basefunctions.runtime import (
    create_root_structure,
    create_bootstrap_package_structure,
    create_full_package_structure,
    ensure_bootstrap_package_structure,
)

# Versioning
from basefunctions.runtime import version, versions

# Deployment
from basefunctions.runtime import DeploymentManager, DeploymentError

# Venv management
from basefunctions.runtime import VenvUtils, VenvUtilsError
```

### Cheat Sheet

| Task | Code |
|------|------|
| Get config directory | `get_runtime_config_path("pkg")` |
| Get log directory | `get_runtime_log_path("pkg")` |
| Get template directory | `get_runtime_template_path("pkg")` |
| Get package root | `get_runtime_path("pkg")` |
| Get deployment root (always) | `get_deployment_path("pkg")` |
| Find development checkout | `find_development_path("pkg")` |
| Check if in development | `bool(find_development_path("pkg"))` |
| Get current version | `version("pkg")` |
| Get all deployed versions | `versions()` |
| Initialize package dirs | `ensure_bootstrap_package_structure("pkg")` |
| Deploy a module | `DeploymentManager().deploy_module("pkg")` |
| Remove a deployment | `DeploymentManager().clean_deployment("pkg")` |
| Check venv valid | `VenvUtils.is_valid_venv(venv_path)` |
| List installed packages | `VenvUtils.get_installed_packages(venv_path)` |
| Install packages (local-first) | `VenvUtils.install_with_ppip(["pkg"], venv_path)` |
| Get venv size | `VenvUtils.format_size(VenvUtils.get_venv_size(venv_path))` |

---

**Document Version:** 1.0.0
**Last Updated:** 2026-03-09
**Subpackage Version:** 0.5.98+
