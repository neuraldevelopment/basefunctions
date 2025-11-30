# Runtime Module Guide

**basefunctions Runtime Module - Comprehensive Documentation**

Version: 1.1
Last Updated: 2025-01-24
Framework: basefunctions v0.5.32

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Core Components](#core-components)
4. [DeploymentManager](#deploymentmanager)
5. [VenvUtils](#venvutils)
6. [Version Management](#version-management)
7. [Runtime Path System](#runtime-path-system)
8. [Bootstrap vs Deployment](#bootstrap-vs-deployment)
9. [Use Cases](#use-cases)
10. [Best Practices](#best-practices)
11. [API Reference](#api-reference)

---

## Overview

The Runtime Module provides comprehensive infrastructure for managing Python package deployment, virtual environments, version tracking, and runtime path resolution. It enables seamless transitions between development and deployment environments with intelligent change detection and automated dependency management.

### Key Features

- **Hash-Based Change Detection**: Combined hash strategy tracking source code, dependencies, bin tools, and templates
- **Intelligent Deployment**: Automatic deployment only when changes are detected
- **Virtual Environment Management**: Platform-aware venv operations with pip command wrappers
- **Version Tracking**: Git-based version management with development status indicators
- **Runtime Path Resolution**: Automatic detection of development vs deployment environments
- **Bootstrap Support**: Self-deployment capability for basefunctions framework
- **Local Dependency Management**: Automatic installation of locally deployed dependencies

### Module Structure

```
src/basefunctions/runtime/
├── __init__.py                 # Public API exports
├── deployment_manager.py       # DeploymentManager singleton
├── runtime_functions.py        # Runtime path utilities
├── venv_utils.py              # Virtual environment operations
└── version.py                 # Version management utilities
```

---

## Architecture

### Design Principles

1. **KISSS Philosophy**: Keep It Simple, Straightforward, and Smart
2. **Singleton Pattern**: Core managers use @singleton decorator for global state
3. **Platform Awareness**: Cross-platform compatibility (macOS, Linux, Windows)
4. **Context Detection**: Automatic environment detection (dev vs deployment)
5. **Change Detection**: Hash-based tracking to prevent unnecessary deployments
6. **Bootstrap Support**: Self-deployment capability for framework itself

### Component Interaction

```
┌─────────────────────────────────────────────────────────────┐
│                     User Application                         │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        v
┌─────────────────────────────────────────────────────────────┐
│                  Runtime Module API                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Deployment   │  │  VenvUtils   │  │   Version    │      │
│  │  Manager     │  │              │  │  Management  │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                 │                  │              │
│         v                 v                  v              │
│  ┌──────────────────────────────────────────────────┐      │
│  │          Runtime Path Functions                   │      │
│  │  - Development Path Detection                     │      │
│  │  - Deployment Path Resolution                     │      │
│  │  - Bootstrap Configuration                        │      │
│  └──────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
                        │
                        v
┌─────────────────────────────────────────────────────────────┐
│                  Filesystem Layer                            │
│  ┌────────────────────┐      ┌────────────────────┐        │
│  │ Development Dirs   │      │ Deployment Dir     │        │
│  │ ~/Code/neuraldev/  │      │ ~/.neuraldevelopment/       │
│  │   basefunctions/   │      │   packages/        │        │
│  │   dbfunctions/     │      │   bin/             │        │
│  └────────────────────┘      └────────────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. DeploymentManager

**Purpose**: Singleton manager for module deployment with intelligent change detection.

**Key Responsibilities**:
- Deploy modules from development to deployment directory
- Detect changes using combined hash strategy
- Manage virtual environments during deployment
- Handle bin tool wrapper generation
- Track deployment state via hash storage

**Singleton Pattern**:
```python
@basefunctions.singleton
class DeploymentManager:
    """Singleton for handling module deployment with change detection."""
```

### 2. VenvUtils

**Purpose**: Platform-aware virtual environment utility functions.

**Key Responsibilities**:
- Get platform-specific paths (pip, python, activate)
- Run pip commands in virtual environments
- List and manage installed packages
- Validate virtual environment structure
- Calculate venv sizes

**Static Methods**: All methods are static for easy import and use.

### 3. Version Management

**Purpose**: Git-based version tracking with development indicators.

**Key Responsibilities**:
- Get package versions from metadata
- Detect development status via git commits
- Count commits ahead of latest tag
- Show development indicators (e.g., "0.5.2-dev+3")

**Functions**:
- `version(package_name)`: Get version with dev indicator
- `versions()`: Get all local package versions

### 4. Runtime Path Functions

**Purpose**: Intelligent path resolution for development and deployment.

**Key Responsibilities**:
- Detect current environment context
- Resolve runtime paths based on context
- Manage bootstrap configuration
- Create directory structures

---

## DeploymentManager

### Overview

The `DeploymentManager` is the central component for deploying Python packages from development directories to the deployment directory. It uses a sophisticated change detection system to avoid unnecessary deployments.

### Change Detection Strategy

The change detection uses a **combined hash** approach:

```python
combined_hash = SHA256(
    src_hash +          # Source file timestamps
    pip_hash +          # Pip freeze output
    bin_hash +          # Bin tool timestamps
    templates_hash +    # Template file timestamps
    dependency_timestamps  # Local dependency deployment times
)
```

#### Hash Components

1. **Source Hash** (`_hash_src_files`)
   - All `.py` files in `src/` directory
   - Uses file modification times
   - Returns `"no-src"` if no src directory

2. **Pip Hash** (`_hash_pip_freeze`)
   - Output of `pip list --format=freeze`
   - Sorted package list
   - Detects dependency changes

3. **Bin Hash** (`_hash_bin_files`)
   - All files in `bin/` directory
   - Uses file modification times
   - Returns `"no-bin"` if no bin directory

4. **Templates Hash** (`_hash_template_files`)
   - All files in `templates/` directory
   - Uses file modification times
   - Returns `"no-templates"` if no templates directory

5. **Dependency Timestamps** (`_get_dependency_timestamps`)
   - Timestamps of all local dependencies
   - Triggers redeployment when dependencies change
   - Only tracks dependencies that are available locally

### Deployment Workflow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Context Validation                                        │
│    - Verify user is in development directory                │
│    - Check module exists                                     │
└────────────────┬─────────────────────────────────────────────┘
                 │
                 v
┌─────────────────────────────────────────────────────────────┐
│ 2. Change Detection (unless --force)                        │
│    - Calculate combined hash                                │
│    - Compare with stored hash                               │
│    - Skip if no changes detected                            │
└────────────────┬─────────────────────────────────────────────┘
                 │
                 v
┌─────────────────────────────────────────────────────────────┐
│ 3. Clean Target Directory                                   │
│    - Remove existing deployment                             │
│    - Create fresh directory structure                       │
└────────────────┬─────────────────────────────────────────────┘
                 │
                 v
┌─────────────────────────────────────────────────────────────┐
│ 4. Deploy Components                                        │
│    ├─ Virtual Environment (fresh venv)                      │
│    ├─ Templates (fresh copy)                                │
│    ├─ Configs (protect existing user configs)               │
│    └─ Bin Tools (with global wrappers)                      │
└────────────────┬─────────────────────────────────────────────┘
                 │
                 v
┌─────────────────────────────────────────────────────────────┐
│ 5. Update Hash                                              │
│    - Store new combined hash                                │
│    - Enable future change detection                         │
└─────────────────────────────────────────────────────────────┘
```

### Virtual Environment Deployment

The `_deploy_venv` method creates a fresh virtual environment in deployment:

**Steps**:
1. Create fresh venv using `python -m venv`
2. Copy package structure (pyproject.toml, src/, etc.)
3. Upgrade pip (silently)
4. Install local dependencies first (visible output)
5. Install current module (visible output)

**Local Dependency Management**:
- Parses `pyproject.toml` for dependencies
- Checks which dependencies are available locally
- Installs local versions before installing current module
- Ensures dependency consistency

**Example**:
```python
# If package A depends on basefunctions (local):
# 1. Install basefunctions from ~/.neuraldevelopment/packages/basefunctions
# 2. Then install package A from development directory
```

### Bin Tool Deployment

The `_deploy_bin_tools` method handles executable tool deployment:

**Features**:
1. **Tool Copying**: Copy all bin/ files to deployment
2. **Make Executable**: Set 755 permissions on all tools
3. **Global Wrappers**: Create wrapper scripts in global bin/

**Wrapper Types**:

1. **Standard Wrapper** (activates venv):
```bash
#!/bin/bash
# Auto-generated wrapper for tool.py from module mymodule
source /path/to/deployment/venv/bin/activate
exec /path/to/deployment/bin/tool.py "$@"
```

2. **NO_VENV Wrapper** (no venv activation):
```bash
#!/bin/bash
# Auto-generated wrapper for ppip.py from module basefunctions (no venv)
exec /path/to/deployment/bin/ppip.py "$@"
```

**NO_VENV Tools**:
Tools that manage virtual environments themselves should not activate venv:
- `clean_virtual_environment.py`
- `ppip.py`
- `update_packages.py`
- `deploy_manager.py`

### Template and Config Deployment

**Templates** (`_deploy_templates`):
- Always fresh copy from source
- Overwrites existing templates
- Used as source for config generation

**Configs** (`_deploy_configs`):
- Protect existing user configs (never overwrite)
- Only generate from templates if config missing
- Preserves user customizations

### Usage Examples

#### Basic Deployment
```python
from basefunctions import DeploymentManager

manager = DeploymentManager()
deployed, version = manager.deploy_module("mypackage")

if deployed:
    print(f"Deployed {version}")
else:
    print("No changes detected")
```

#### Force Deployment
```python
# Deploy even without changes
deployed, version = manager.deploy_module("mypackage", force=True)
```

#### With Version Tagging
```python
# Deploy with version information
deployed, version = manager.deploy_module("mypackage", version="v0.5.2")
```

#### Clean Deployment
```python
# Remove deployment and start fresh
manager.clean_deployment("mypackage")
```

### Hash Storage

Hashes are stored in:
```
~/.neuraldevelopment/deployment/hashes/
├── basefunctions.hash
├── dbfunctions.hash
└── mypackage.hash
```

Each `.hash` file contains the SHA256 hash for change detection.

---

## VenvUtils

### Overview

`VenvUtils` provides platform-aware virtual environment operations. All methods are static for easy import and use.

### Platform Awareness

Different platforms have different venv structures:

**Unix/macOS**:
```
.venv/
├── bin/
│   ├── pip
│   ├── python
│   └── activate
└── lib/
```

**Windows**:
```
.venv/
├── Scripts/
│   ├── pip.exe
│   ├── python.exe
│   └── activate.bat
└── Lib/
```

### Core Methods

#### Path Resolution

**Get Pip Executable**:
```python
from pathlib import Path
from basefunctions import VenvUtils

venv_path = Path(".venv")
pip = VenvUtils.get_pip_executable(venv_path)
# macOS: .venv/bin/pip
# Windows: .venv\Scripts\pip.exe
```

**Get Python Executable**:
```python
python = VenvUtils.get_python_executable(venv_path)
# macOS: .venv/bin/python
# Windows: .venv\Scripts\python.exe
```

**Get Activate Script**:
```python
activate = VenvUtils.get_activate_script(venv_path)
# macOS: .venv/bin/activate
# Windows: .venv\Scripts\activate.bat
```

#### Environment Detection

**Check if in Virtual Environment**:
```python
if VenvUtils.is_virtual_environment():
    print("Running in venv")
else:
    print("Running in system Python")
```

**Validate Virtual Environment**:
```python
venv_path = Path(".venv")
if VenvUtils.is_valid_venv(venv_path):
    print("Valid venv")
else:
    print("Invalid or missing venv")
```

**Find Virtual Environment**:
```python
directory = Path.cwd()
venv = VenvUtils.find_venv_in_directory(directory)

if venv:
    print(f"Found venv at: {venv}")
else:
    print("No venv found")
```

#### Package Management

**List Installed Packages**:
```python
# In current environment
packages = VenvUtils.get_installed_packages()

# In specific venv
venv_path = Path(".venv")
packages = VenvUtils.get_installed_packages(venv_path)

# Include protected packages (pip, setuptools, wheel)
packages = VenvUtils.get_installed_packages(venv_path, include_protected=True)

# Show live output instead of capturing
VenvUtils.get_installed_packages(venv_path, capture_output=False)
```

**Get Package Info**:
```python
info = VenvUtils.get_package_info("basefunctions", venv_path)

if info:
    print(f"Name: {info['Name']}")
    print(f"Version: {info['Version']}")
    print(f"Location: {info['Location']}")
```

**Run Pip Command**:
```python
# Install package
VenvUtils.run_pip_command(
    ["install", "requests"],
    venv_path,
    capture_output=False  # Show live output
)

# Install with timeout
VenvUtils.run_pip_command(
    ["install", "large-package"],
    venv_path,
    timeout=600,  # 10 minutes
    capture_output=False
)
```

**Upgrade Pip**:
```python
# Upgrade pip silently
VenvUtils.upgrade_pip(venv_path, capture_output=True)

# Upgrade pip with visible output
VenvUtils.upgrade_pip(venv_path, capture_output=False)
```

**Install Requirements File**:
```python
requirements = Path("requirements.txt")
VenvUtils.install_requirements(venv_path, requirements, capture_output=False)
```

**Uninstall Packages**:
```python
packages_to_remove = ["old-package", "deprecated-lib"]
VenvUtils.uninstall_packages(packages_to_remove, venv_path, capture_output=False)
```

#### Virtual Environment Utilities

**Get Venv Size**:
```python
size_bytes = VenvUtils.get_venv_size(venv_path)
print(f"Venv size: {size_bytes} bytes")

# Format size
formatted = VenvUtils.format_size(size_bytes)
print(f"Venv size: {formatted}")  # e.g., "234.5 MB"
```

### Output Control

Many methods support `capture_output` parameter:

- `capture_output=True` (default): Capture output, return as string
- `capture_output=False`: Show live output to user

**When to use each**:

**Capture Output** (silent):
- Internal operations
- Error checking
- Automated scripts
- When output not needed

**Live Output** (visible):
- Package installation (user feedback)
- Long-running operations
- Interactive mode
- Debugging

### Error Handling

All pip operations raise `VenvUtilsError` on failure:

```python
from basefunctions import VenvUtils, VenvUtilsError

try:
    VenvUtils.install_requirements(venv_path, requirements)
except VenvUtilsError as e:
    print(f"Installation failed: {e}")
```

### Protected Packages

Certain packages are protected from uninstallation:
- `pip`
- `setuptools`
- `wheel`

These are excluded by default when listing packages (unless `include_protected=True`).

---

## Version Management

### Overview

The version management system tracks package versions using Python package metadata and Git commit information to provide accurate version strings with development status indicators.

### Version String Format

**Production** (installed from deployment):
```
0.5.2
```

**Development** (in dev directory, at tag):
```
0.5.2-dev
```

**Development** (in dev directory, ahead of tag):
```
0.5.2-dev+3
```

Where `+3` indicates 3 commits ahead of latest tag.

### Core Functions

#### `version(package_name)`

Get version for a specific package with development indicator.

**Logic**:
1. Get base version from `importlib.metadata`
2. Check if current directory is in package development path
3. If in development, count commits ahead of latest tag
4. Add `-dev` suffix, plus `+N` if commits ahead

**Examples**:
```python
from basefunctions import version

# In production (deployment directory)
v = version("basefunctions")
# Returns: "0.5.2"

# In development at tag
v = version("basefunctions")
# Returns: "0.5.2-dev"

# In development with 3 commits ahead
v = version("basefunctions")
# Returns: "0.5.2-dev+3"
```

#### `versions()`

Get versions of all installed neuraldevelopment packages.

**Logic**:
1. Find all packages in deployment directory
2. Get versions for installed packages
3. Only add `-dev` suffix for package where CWD is located
4. Return dictionary of package -> version

**Example**:
```python
from basefunctions import versions

# In basefunctions development directory
v = versions()
# Returns: {
#     "basefunctions": "0.5.2-dev+3",
#     "dbfunctions": "0.1.5",
#     "utilfunctions": "0.2.1"
# }
```

**Important**: Only the package you're currently working in shows `-dev` status. Other packages show their installed versions honestly.

### Git Integration

#### Commit Counting

The system counts commits ahead of the latest tag:

```bash
# Get latest tag
git describe --tags --abbrev=0
# Returns: v0.5.2

# Count commits since tag
git rev-list v0.5.2..HEAD --count
# Returns: 3
```

This provides accurate tracking of development progress.

#### Development Path Detection

The system detects if CWD is within a package's development directory:

**Check Process**:
1. Get development directories from bootstrap config
2. Check if `os.getcwd()` starts with any dev directory
3. If yes, determine which package by matching path

**Example**:
```
CWD: /Users/user/Code/neuraldev/basefunctions/src
Dev Paths:
  - /Users/user/Code/neuraldev
Match: basefunctions (in development)
```

### Version Display Best Practices

**CLI Tools**:
```python
from basefunctions import version, versions

# Show current package version
print(f"basefunctions {version('basefunctions')}")
# Output: basefunctions 0.5.2-dev+3

# Show all package versions
for pkg, ver in versions().items():
    print(f"{pkg:20} {ver}")
# Output:
# basefunctions        0.5.2-dev+3
# dbfunctions          0.1.5
# utilfunctions        0.2.1
```

**Deployment Scripts**:
```python
from basefunctions import version

current_version = version("mypackage")
print(f"Deploying {current_version}")
```

---

## Runtime Path System

### Overview

The runtime path system automatically detects whether code is running in a development or deployment context and returns appropriate paths.

### Bootstrap Configuration

The bootstrap configuration file stores paths for development and deployment:

**Location**: `~/.config/basefunctions/bootstrap.json`

**Default Structure**:
```json
{
  "bootstrap": {
    "paths": {
      "deployment_directory": "~/.neuraldevelopment",
      "development_directories": [
        "~/Code/neuraldev",
        "~/Code/neuraldev-utils"
      ]
    }
  }
}
```

**Functions**:
```python
from basefunctions.runtime import (
    get_bootstrap_config_path,
    get_bootstrap_deployment_directory,
    get_bootstrap_development_directories
)

# Get config path
config_path = get_bootstrap_config_path()
# Returns: "~/.config/basefunctions/bootstrap.json"

# Get deployment directory
deploy_dir = get_bootstrap_deployment_directory()
# Returns: "~/.neuraldevelopment"

# Get development directories
dev_dirs = get_bootstrap_development_directories()
# Returns: ["~/Code/neuraldev", "~/Code/neuraldev-utils"]
```

### Path Resolution Logic

#### `get_runtime_path(package_name)`

Automatically resolves base runtime path based on context.

**Logic**:
1. Load bootstrap config (dev dirs and deploy dir)
2. Get current working directory
3. Check if CWD is within any dev directory for this package
4. If yes: return development path
5. If no: return deployment path

**Example**:
```python
from basefunctions.runtime import get_runtime_path

# Case 1: In development directory
# CWD: /Users/user/Code/neuraldev/basefunctions/src
path = get_runtime_path("basefunctions")
# Returns: /Users/user/Code/neuraldev/basefunctions

# Case 2: In deployment or elsewhere
# CWD: /Users/user/Documents
path = get_runtime_path("basefunctions")
# Returns: /Users/user/.neuraldevelopment/packages/basefunctions
```

#### `get_deployment_path(package_name)`

Always returns deployment path (never development).

**Usage**:
```python
from basefunctions.runtime import get_deployment_path

# Always returns deployment path
path = get_deployment_path("basefunctions")
# Returns: /Users/user/.neuraldevelopment/packages/basefunctions
```

#### `find_development_path(package_name)`

Find all development paths where package exists.

**Returns**: List of paths (can be multiple if package exists in multiple dev directories)

**Example**:
```python
from basefunctions.runtime import find_development_path

paths = find_development_path("basefunctions")
# Returns: [
#   "/Users/user/Code/neuraldev/basefunctions",
#   "/Users/user/Code/neuraldev-backup/basefunctions"
# ]
```

### Component Paths

After getting base runtime path, you can get specific component paths:

**Get Config Path**:
```python
from basefunctions.runtime import get_runtime_config_path

config_path = get_runtime_config_path("basefunctions")
# Dev: /Users/user/Code/neuraldev/basefunctions/config
# Deploy: /Users/user/.neuraldevelopment/packages/basefunctions/config
```

**Get Log Path**:
```python
from basefunctions.runtime import get_runtime_log_path

log_path = get_runtime_log_path("basefunctions")
# Dev: /Users/user/Code/neuraldev/basefunctions/logs
# Deploy: /Users/user/.neuraldevelopment/packages/basefunctions/logs
```

**Get Template Path**:
```python
from basefunctions.runtime import get_runtime_template_path

template_path = get_runtime_template_path("basefunctions")
# Dev: /Users/user/Code/neuraldev/basefunctions/templates/config
# Deploy: /Users/user/.neuraldevelopment/packages/basefunctions/templates/config
```

**Get Custom Component Path**:
```python
from basefunctions.runtime import get_runtime_component_path

data_path = get_runtime_component_path("basefunctions", "data")
# Dev: /Users/user/Code/neuraldev/basefunctions/data
# Deploy: /Users/user/.neuraldevelopment/packages/basefunctions/data
```

### Directory Structure Creation

**Bootstrap Package Structure**:
Creates minimal structure for bootstrap phase:
```python
from basefunctions.runtime import create_bootstrap_package_structure

create_bootstrap_package_structure("basefunctions")
# Creates:
# - config/
# - templates/config/
```

**Full Package Structure**:
Creates complete structure:
```python
from basefunctions.runtime import create_full_package_structure

create_full_package_structure("basefunctions")
# Creates (default):
# - config/
# - logs/
# - templates/config/

# Custom directories
create_full_package_structure("mypackage", ["data", "cache", "output"])
# Creates:
# - data/
# - cache/
# - output/
```

**Root Deployment Structure**:
Creates deployment root directories:
```python
from basefunctions.runtime import create_root_structure

create_root_structure()
# Creates:
# ~/.neuraldevelopment/
# ├── bin/
# └── packages/
```

---

## Bootstrap vs Deployment

### Context Definitions

**Bootstrap Context**:
- Deploying basefunctions framework itself
- No existing basefunctions installation available
- Must use local development environment
- Self-deployment scenario

**Deployment Context**:
- Deploying other packages using basefunctions
- basefunctions is already installed
- Can import and use DeploymentManager
- Standard deployment scenario

**Development Context**:
- Working in source code (src/ directory)
- Using local `.venv` for development
- Changes not yet deployed

### Bootstrap Detection

The `deploy.py` script detects bootstrap scenario:

```python
def is_bootstrap_deployment() -> bool:
    """Check if we are deploying basefunctions itself."""
    module_name = os.path.basename(os.getcwd())
    return module_name == "basefunctions"
```

### Bootstrap Deployment Workflow

When deploying basefunctions itself:

```
┌─────────────────────────────────────────────────────────────┐
│ 1. detect_bootstrap()                                        │
│    CWD: ~/Code/neuraldev/basefunctions/                     │
│    → Bootstrap mode: YES                                     │
└────────────────┬─────────────────────────────────────────────┘
                 │
                 v
┌─────────────────────────────────────────────────────────────┐
│ 2. bootstrap_deploy()                                        │
│    - Find local .venv/bin/python                            │
│    - Re-execute deploy.py with venv python                  │
│    - Pass --bootstrap-internal flag                         │
└────────────────┬─────────────────────────────────────────────┘
                 │
                 v
┌─────────────────────────────────────────────────────────────┐
│ 3. bootstrap_deploy_internal()                              │
│    - Add src/ to sys.path                                   │
│    - Import basefunctions from local src/                   │
│    - Use DeploymentManager normally                         │
└─────────────────────────────────────────────────────────────┘
```

### Standard Deployment Workflow

When deploying other packages:

```
┌─────────────────────────────────────────────────────────────┐
│ 1. detect_bootstrap()                                        │
│    CWD: ~/Code/neuraldev/mypackage/                         │
│    → Bootstrap mode: NO                                      │
└────────────────┬─────────────────────────────────────────────┘
                 │
                 v
┌─────────────────────────────────────────────────────────────┐
│ 2. normal_deploy()                                           │
│    - Import basefunctions (installed)                       │
│    - Get DeploymentManager                                  │
│    - Deploy module                                          │
└─────────────────────────────────────────────────────────────┘
```

### Path Resolution in Different Contexts

**Bootstrap (basefunctions deployment)**:
```python
# During bootstrap deployment (in basefunctions dev dir)
get_runtime_path("basefunctions")
# Returns: ~/Code/neuraldev/basefunctions (development)

get_deployment_path("basefunctions")
# Returns: ~/.neuraldevelopment/packages/basefunctions (target)
```

**Development (working on code)**:
```python
# In development directory
os.chdir("~/Code/neuraldev/mypackage")
get_runtime_path("mypackage")
# Returns: ~/Code/neuraldev/mypackage

# In other directory
os.chdir("~/Documents")
get_runtime_path("mypackage")
# Returns: ~/.neuraldevelopment/packages/mypackage
```

**Deployment (using deployed package)**:
```python
# Anywhere outside dev directory
get_runtime_path("mypackage")
# Returns: ~/.neuraldevelopment/packages/mypackage
```

### Directory Structure Differences

**Development Structure**:
```
~/Code/neuraldev/basefunctions/
├── .venv/              # Development venv
├── bin/                # Development bin tools
├── src/                # Source code
│   └── basefunctions/
├── templates/          # Templates
├── config/            # Dev config (optional)
├── tests/             # Test files
├── pyproject.toml     # Package metadata
└── README.md
```

**Deployment Structure**:
```
~/.neuraldevelopment/packages/basefunctions/
├── venv/              # Deployment venv (fresh)
├── bin/               # Deployed bin tools
├── src/               # Source code (copied)
│   └── basefunctions/
├── templates/         # Templates (copied)
├── config/           # User configs (protected)
├── logs/             # Runtime logs
├── pyproject.toml    # Package metadata (copied)
└── README.md         # Readme (copied)
```

**Global Bin Directory**:
```
~/.neuraldevelopment/bin/
├── deploy             # Wrapper → basefunctions/bin/deploy.py
├── ppip               # Wrapper → basefunctions/bin/ppip.py
└── mytool             # Wrapper → mypackage/bin/mytool.py
```

---

## Use Cases

### Use Case 1: Deploy Module After Changes

**Scenario**: You've made changes to your package and want to deploy them.

**Steps**:
```bash
# 1. Navigate to development directory
cd ~/Code/neuraldev/mypackage

# 2. Make changes to code
vim src/mypackage/core.py

# 3. Commit changes (required before deployment)
git add .
git commit -m "Add new feature"

# 4. Deploy
deploy
# Or with force flag:
deploy --force
```

**What Happens**:
1. Context validation (checks you're in dev directory)
2. Change detection (calculates combined hash)
3. If changes detected → deploy
4. If no changes → skip deployment
5. Version management (creates git tag)

### Use Case 2: Force Deployment Without Changes

**Scenario**: You want to redeploy even without code changes (e.g., to test deployment process).

**Code**:
```python
from basefunctions import DeploymentManager

manager = DeploymentManager()
deployed, version = manager.deploy_module("mypackage", force=True)
print(f"Forced deployment: {deployed}")
```

**CLI**:
```bash
deploy --force
```

### Use Case 3: Check Package Versions

**Scenario**: You want to see which versions of packages are installed.

**Code**:
```python
from basefunctions import versions

for package, ver in versions().items():
    print(f"{package:20} {ver}")
```

**Output**:
```
basefunctions        0.5.2-dev+3
dbfunctions          0.1.5
utilfunctions        0.2.1
```

### Use Case 4: Get Runtime Config Path

**Scenario**: Your package needs to load config, and path depends on context.

**Code**:
```python
from basefunctions.runtime import get_runtime_config_path
from pathlib import Path
import json

# Get config path (auto-detects dev vs deployment)
config_dir = get_runtime_config_path("mypackage")
config_file = Path(config_dir) / "config.json"

# Load config
with open(config_file) as f:
    config = json.load(f)
```

**Result**:
- In dev: Uses `~/Code/neuraldev/mypackage/config/config.json`
- In deploy: Uses `~/.neuraldevelopment/packages/mypackage/config/config.json`

### Use Case 5: Create Virtual Environment Tools

**Scenario**: You're building a tool that manages virtual environments.

**Code**:
```python
from pathlib import Path
from basefunctions import VenvUtils

# Find venv in current directory
venv = VenvUtils.find_venv_in_directory(Path.cwd())

if not venv:
    print("No virtual environment found")
    exit(1)

# Get installed packages
packages = VenvUtils.get_installed_packages(venv)

print(f"Found {len(packages)} packages:")
for pkg in packages:
    info = VenvUtils.get_package_info(pkg, venv)
    if info:
        print(f"  {pkg:20} {info['Version']}")
```

### Use Case 6: Install Local Dependencies

**Scenario**: Your package depends on other local packages.

**pyproject.toml**:
```toml
[project]
name = "mypackage"
version = "1.0.0"
dependencies = [
    "basefunctions>=0.5.0",
    "dbfunctions>=0.1.0",
    "requests>=2.28.0"
]
```

**Deployment Process**:
1. DeploymentManager parses dependencies
2. Checks which are available locally:
   - `basefunctions` → in `~/.neuraldevelopment/packages/basefunctions` ✓
   - `dbfunctions` → in `~/.neuraldevelopment/packages/dbfunctions` ✓
   - `requests` → not local, will install from PyPI
3. Installs local dependencies first from deployment directory
4. Then installs current package (which pulls `requests` from PyPI)

**Result**: Local dependencies use deployed versions, external dependencies use PyPI.

### Use Case 7: Clean and Redeploy

**Scenario**: Deployment is corrupted, want to start fresh.

**Code**:
```python
from basefunctions import DeploymentManager

manager = DeploymentManager()

# Clean existing deployment
manager.clean_deployment("mypackage")

# Redeploy from scratch
deployed, version = manager.deploy_module("mypackage", force=True)
```

**CLI**:
```bash
# Clean deployment
rm -rf ~/.neuraldevelopment/packages/mypackage
rm ~/.neuraldevelopment/deployment/hashes/mypackage.hash

# Redeploy
deploy --force
```

### Use Case 8: Bootstrap basefunctions Itself

**Scenario**: Fresh installation of basefunctions framework.

**Steps**:
```bash
# 1. Clone repository
git clone https://github.com/neuraldevelopment/basefunctions.git
cd basefunctions

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate

# 3. Install package in development mode
pip install -e ".[dev]"

# 4. Deploy basefunctions (bootstrap)
bin/deploy.py
```

**What Happens**:
1. Script detects CWD is "basefunctions" → bootstrap mode
2. Finds local `.venv/bin/python`
3. Re-executes with venv python
4. Adds `src/` to sys.path
5. Imports basefunctions from local src
6. Deploys to `~/.neuraldevelopment/packages/basefunctions`
7. Creates global wrappers in `~/.neuraldevelopment/bin/`

### Use Case 9: Development Version Tracking

**Scenario**: You want to see if you're working on development version.

**Code**:
```python
from basefunctions import version

# In development directory
print(version("basefunctions"))
# Output: 0.5.2-dev+3

# In deployment directory or elsewhere
print(version("basefunctions"))
# Output: 0.5.2
```

**Usage in CLI Tools**:
```python
import argparse
from basefunctions import version

parser = argparse.ArgumentParser(
    prog="mytool",
    description="My Tool"
)
parser.add_argument("--version", action="version",
                   version=f"%(prog)s {version('mypackage')}")
```

### Use Case 10: Platform-Aware Venv Operations

**Scenario**: Building cross-platform tool that works with venvs.

**Code**:
```python
import sys
from pathlib import Path
from basefunctions import VenvUtils

def activate_venv(venv_path: Path):
    """Get activation command based on platform."""
    activate = VenvUtils.get_activate_script(venv_path)

    if sys.platform == "win32":
        return f"call {activate}"
    else:
        return f"source {activate}"

def install_package(venv_path: Path, package: str):
    """Install package in platform-aware manner."""
    try:
        VenvUtils.run_pip_command(
            ["install", package],
            venv_path,
            capture_output=False
        )
        print(f"✓ Installed {package}")
    except Exception as e:
        print(f"✗ Failed to install {package}: {e}")

# Usage
venv = Path(".venv")
if not VenvUtils.is_valid_venv(venv):
    print("Invalid venv")
    exit(1)

print(f"Activation command: {activate_venv(venv)}")
install_package(venv, "requests")
```

---

## Best Practices

### 1. Deployment Workflow

**Recommended Workflow**:
```bash
# 1. Make changes
vim src/mypackage/core.py

# 2. Test changes locally
pytest tests/

# 3. Commit changes (REQUIRED before deployment)
git add .
git commit -m "Add feature X"

# 4. Deploy
deploy

# 5. Test deployed version
mytool --version  # Uses deployment

# 6. If problems, fix and redeploy
vim src/mypackage/core.py
git add .
git commit -m "Fix issue Y"
deploy
```

**Best Practices**:
- ✓ Always commit before deploying
- ✓ Test locally before deploying
- ✓ Use meaningful commit messages
- ✓ Deploy after significant changes
- ✗ Don't deploy with uncommitted changes
- ✗ Don't deploy without testing

### 2. Version Management

**Semantic Versioning**:
- `MAJOR.MINOR.PATCH` (e.g., `0.5.2`)
- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes

**Git Tag Strategy**:
```bash
# Patch version (default)
deploy

# Minor version
deploy --set-minor

# Major version
deploy --set-major

# Specific version
deploy --set-version 2.0.0
```

**Best Practices**:
- ✓ Use git tags for version tracking
- ✓ Follow semantic versioning
- ✓ Tag releases consistently
- ✓ Push tags to remote (`deploy` does this automatically)
- ✗ Don't manually edit version files
- ✗ Don't skip version numbers

### 3. Virtual Environment Management

**Development Venv**:
```bash
# Create development venv
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,test]"
```

**Deployment Venv**:
- Created automatically during deployment
- Fresh venv for each deployment
- Contains only production dependencies
- Isolated from development venv

**Best Practices**:
- ✓ Keep development venv up-to-date
- ✓ Use `pip list` to check installed packages
- ✓ Document dependencies in `pyproject.toml`
- ✓ Let DeploymentManager handle deployment venv
- ✗ Don't manually modify deployment venv
- ✗ Don't share venvs between packages

### 4. Dependency Management

**Local Dependencies**:
When your package depends on other local packages:

**pyproject.toml**:
```toml
dependencies = [
    "basefunctions>=0.5.0",  # Local
    "dbfunctions>=0.1.0",    # Local
    "requests>=2.28.0"       # PyPI
]
```

**Deployment Order**:
1. Deploy base dependencies first: `basefunctions`
2. Deploy intermediate dependencies: `dbfunctions`
3. Deploy your package: `mypackage`

**Best Practices**:
- ✓ Deploy dependencies before dependents
- ✓ Use version constraints (`>=0.5.0`)
- ✓ Document local dependencies clearly
- ✓ Keep dependencies up-to-date
- ✗ Don't create circular dependencies
- ✗ Don't mix dev and prod dependencies

### 5. Configuration Management

**Config Strategy**:

**Template Config** (`templates/config/config.json`):
```json
{
  "setting1": "default_value",
  "setting2": 123
}
```

**User Config** (`config/config.json`):
```json
{
  "setting1": "custom_value",
  "setting2": 456
}
```

**Deployment Behavior**:
- First deployment: Copy template → user config
- Subsequent deployments: Preserve user config (never overwrite)
- Template always updated (for reference)

**Best Practices**:
- ✓ Provide sensible defaults in templates
- ✓ Document all config options
- ✓ Use `get_runtime_config_path()` for loading
- ✓ Protect user customizations
- ✗ Don't hardcode paths
- ✗ Don't overwrite user configs

### 6. Path Resolution

**Always Use Runtime Functions**:
```python
from basefunctions.runtime import get_runtime_config_path

# ✓ Good: Context-aware
config_dir = get_runtime_config_path("mypackage")

# ✗ Bad: Hardcoded
config_dir = "/Users/user/.neuraldevelopment/packages/mypackage/config"

# ✗ Bad: Relative path assumptions
config_dir = "../config"
```

**Best Practices**:
- ✓ Use `get_runtime_path()` for base paths
- ✓ Use `get_runtime_config_path()` for configs
- ✓ Use `get_runtime_log_path()` for logs
- ✓ Let system detect context (dev vs deploy)
- ✗ Don't hardcode paths
- ✗ Don't assume directory structure

### 7. Error Handling

**Deployment Errors**:
```python
from basefunctions import DeploymentManager, DeploymentError

manager = DeploymentManager()

try:
    deployed, version = manager.deploy_module("mypackage")
except DeploymentError as e:
    print(f"Deployment failed: {e}")
    # Handle error appropriately
```

**Venv Errors**:
```python
from basefunctions import VenvUtils, VenvUtilsError

try:
    VenvUtils.install_requirements(venv_path, requirements)
except VenvUtilsError as e:
    print(f"Installation failed: {e}")
    # Handle error appropriately
```

**Best Practices**:
- ✓ Catch specific exceptions (`DeploymentError`, `VenvUtilsError`)
- ✓ Provide helpful error messages
- ✓ Log errors for debugging
- ✓ Clean up on failure (if needed)
- ✗ Don't catch and ignore errors silently
- ✗ Don't use bare `except:` clauses

### 8. Logging

**Use basefunctions Logging**:
```python
import basefunctions

# Setup logger
basefunctions.setup_logger(__name__)
logger = basefunctions.get_logger(__name__)

# Log at appropriate levels
logger.debug("Detailed debugging information")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error occurred")
logger.critical("Critical deployment step")
```

**DeploymentManager Logging**:
The DeploymentManager uses `logger.critical()` for important deployment steps:
- Module deployment started
- Component deployment (venv, templates, bin tools)
- Module deployment completed

**Best Practices**:
- ✓ Use appropriate log levels
- ✓ Log important state changes
- ✓ Include context in log messages
- ✓ Use `get_runtime_log_path()` for log files
- ✗ Don't spam logs with noise
- ✗ Don't log sensitive information

### 9. Change Detection Optimization

**When to Use Force Flag**:
```bash
# Regular deployment (use change detection)
deploy

# Force deployment when:
# - Testing deployment process
# - Deployment corrupted
# - Hash file deleted
# - Manual changes to deployment
deploy --force
```

**What Triggers Redeployment**:
- Source code changes (any `.py` file in `src/`)
- Dependency changes (pip packages)
- Bin tool changes (any file in `bin/`)
- Template changes (any file in `templates/`)
- Local dependency redeployments

**Best Practices**:
- ✓ Trust change detection (default behavior)
- ✓ Use `--force` sparingly
- ✓ Commit before deploying (for accurate detection)
- ✗ Don't use `--force` routinely
- ✗ Don't manually modify deployment directory

### 10. Testing Strategy

**Test in Development First**:
```bash
# 1. Development testing
source .venv/bin/activate
pytest tests/
python src/mypackage/cli.py --test

# 2. Deploy
deploy

# 3. Test deployed version
mytool --test  # Uses deployment

# 4. Compare results
```

**Test Deployment Process**:
```python
# test_deployment.py
import pytest
from basefunctions import DeploymentManager

def test_deployment():
    """Test deployment process."""
    manager = DeploymentManager()

    # Deploy with force
    deployed, version = manager.deploy_module("mypackage", force=True)

    assert deployed == True
    assert version is not None
```

**Best Practices**:
- ✓ Test locally before deploying
- ✓ Test deployed version after deployment
- ✓ Automate deployment tests
- ✓ Test with both dev and deployed versions
- ✗ Don't skip testing
- ✗ Don't assume deployment works

---

## API Reference

### DeploymentManager

#### `DeploymentManager()`

**Description**: Singleton manager for module deployment with change detection.

**Methods**:

##### `deploy_module(module_name, force=False, version=None)`

Deploy specific module with context validation and change detection.

**Parameters**:
- `module_name` (str): Name of the module to deploy
- `force` (bool, optional): Force deployment even if no changes detected (default: False)
- `version` (str, optional): Version string for logging (e.g., 'v0.5.2')

**Returns**:
- `Tuple[bool, str]`: (deployed, version) - True if deployment was performed with version string

**Raises**:
- `DeploymentError`: If user not in development directory or deployment fails

**Example**:
```python
from basefunctions import DeploymentManager

manager = DeploymentManager()
deployed, version = manager.deploy_module("mypackage")

if deployed:
    print(f"Deployed version {version}")
else:
    print("No changes detected")
```

##### `clean_deployment(module_name)`

Delete complete deployment for fresh start.

**Parameters**:
- `module_name` (str): Name of the module to clean

**Raises**:
- `DeploymentError`: If module_name is invalid

**Example**:
```python
manager.clean_deployment("mypackage")
```

---

### VenvUtils

All methods are static.

#### Path Resolution Methods

##### `get_pip_executable(venv_path)`

Get platform-aware pip executable path for virtual environment.

**Parameters**:
- `venv_path` (Path): Path to virtual environment directory

**Returns**:
- `Path`: Path to pip executable

**Example**:
```python
from pathlib import Path
from basefunctions import VenvUtils

venv = Path(".venv")
pip = VenvUtils.get_pip_executable(venv)
# macOS: .venv/bin/pip
# Windows: .venv\Scripts\pip.exe
```

##### `get_python_executable(venv_path)`

Get platform-aware python executable path for virtual environment.

**Parameters**:
- `venv_path` (Path): Path to virtual environment directory

**Returns**:
- `Path`: Path to python executable

##### `get_activate_script(venv_path)`

Get platform-aware activate script path for virtual environment.

**Parameters**:
- `venv_path` (Path): Path to virtual environment directory

**Returns**:
- `Path`: Path to activate script

#### Environment Detection Methods

##### `is_virtual_environment()`

Check if currently running in a virtual environment.

**Returns**:
- `bool`: True if in virtual environment

**Example**:
```python
if VenvUtils.is_virtual_environment():
    print("Running in venv")
```

##### `is_valid_venv(venv_path)`

Check if path contains a valid virtual environment.

**Parameters**:
- `venv_path` (Path): Path to check

**Returns**:
- `bool`: True if valid virtual environment

##### `find_venv_in_directory(directory, venv_name='.venv')`

Find virtual environment in directory.

**Parameters**:
- `directory` (Path): Directory to search in
- `venv_name` (str, optional): Virtual environment directory name (default: '.venv')

**Returns**:
- `Optional[Path]`: Path to virtual environment if found, None otherwise

#### Package Management Methods

##### `get_installed_packages(venv_path=None, include_protected=False, capture_output=True)`

Get list of installed packages in environment.

**Parameters**:
- `venv_path` (Optional[Path], optional): Path to virtual environment, uses current if None
- `include_protected` (bool, optional): Include protected packages like pip, setuptools (default: False)
- `capture_output` (bool): Whether to capture command output or show live (default: True)

**Returns**:
- `List[str]`: List of installed package names

**Raises**:
- `VenvUtilsError`: If listing packages fails

##### `get_package_info(package_name, venv_path=None, capture_output=True)`

Get information about installed package.

**Parameters**:
- `package_name` (str): Name of the package
- `venv_path` (Optional[Path], optional): Path to virtual environment, uses current if None
- `capture_output` (bool): Whether to capture command output or show live (default: True)

**Returns**:
- `Optional[dict]`: Package information dictionary or None if not found

##### `run_pip_command(command, venv_path=None, timeout=300, capture_output=True)`

Run pip command in virtual environment.

**Parameters**:
- `command` (List[str]): Pip command arguments (without 'pip')
- `venv_path` (Optional[Path], optional): Path to virtual environment, uses current if None
- `timeout` (int, optional): Command timeout in seconds (default: 300)
- `capture_output` (bool): Whether to capture command output or show live (default: True)

**Returns**:
- `subprocess.CompletedProcess`: Command result

**Raises**:
- `VenvUtilsError`: If command fails

**Example**:
```python
VenvUtils.run_pip_command(
    ["install", "requests"],
    venv_path,
    capture_output=False
)
```

##### `upgrade_pip(venv_path, capture_output=True)`

Upgrade pip in virtual environment.

**Parameters**:
- `venv_path` (Path): Path to virtual environment
- `capture_output` (bool): Whether to capture command output or show live (default: True)

**Raises**:
- `VenvUtilsError`: If pip upgrade fails

##### `install_requirements(venv_path, requirements_file, capture_output=True)`

Install requirements file in virtual environment.

**Parameters**:
- `venv_path` (Path): Path to virtual environment
- `requirements_file` (Path): Path to requirements file
- `capture_output` (bool): Whether to capture command output or show live (default: True)

**Raises**:
- `VenvUtilsError`: If requirements installation fails

##### `uninstall_packages(packages, venv_path=None, capture_output=True)`

Uninstall packages from virtual environment.

**Parameters**:
- `packages` (List[str]): List of package names to uninstall
- `venv_path` (Optional[Path], optional): Path to virtual environment, uses current if None
- `capture_output` (bool): Whether to capture command output or show live (default: True)

**Raises**:
- `VenvUtilsError`: If uninstallation fails

#### Utility Methods

##### `get_venv_size(venv_path)`

Get virtual environment size in bytes.

**Parameters**:
- `venv_path` (Path): Path to virtual environment

**Returns**:
- `int`: Size in bytes

##### `format_size(size_bytes)`

Format size in human-readable format.

**Parameters**:
- `size_bytes` (int): Size in bytes

**Returns**:
- `str`: Formatted size string (e.g., "234.5 MB")

---

### Version Management

#### `version(package_name='basefunctions')`

Get version of installed package from metadata with development indicator.

**Parameters**:
- `package_name` (str, optional): Name of the package to get version for (default: 'basefunctions')

**Returns**:
- `str`: Version string (e.g., "0.5.2" or "0.5.2-dev+3") or "unknown" if not found

**Example**:
```python
from basefunctions import version

v = version("basefunctions")
print(f"Version: {v}")
```

#### `versions()`

Get versions of all installed neuraldevelopment packages.

**Returns**:
- `Dict[str, str]`: Dictionary mapping package names to version strings

**Notes**:
- Only shows packages in deployment/packages directory
- Only shows packages that are actually installed
- Adds `-dev` suffix only for package where CWD is located

**Example**:
```python
from basefunctions import versions

for pkg, ver in versions().items():
    print(f"{pkg}: {ver}")
```

---

### Runtime Path Functions

#### `get_bootstrap_config_path()`

Get bootstrap configuration file path.

**Returns**:
- `str`: Bootstrap configuration file path ("~/.config/basefunctions/bootstrap.json")

#### `get_bootstrap_deployment_directory()`

Get deployment directory from bootstrap config.

**Returns**:
- `str`: Deployment directory path (default: "~/.neuraldevelopment")

#### `get_bootstrap_development_directories()`

Get development directories from bootstrap config.

**Returns**:
- `list`: List of development directory paths

#### `get_deployment_path(package_name)`

Get deployment path for package - ALWAYS returns deployment directory.

**Parameters**:
- `package_name` (str): Package name to get deployment path for

**Returns**:
- `str`: Deployment path for package (always ~/.neuraldevelopment/packages/PACKAGE_NAME)

**Example**:
```python
from basefunctions.runtime import get_deployment_path

path = get_deployment_path("basefunctions")
# Returns: /Users/user/.neuraldevelopment/packages/basefunctions
```

#### `find_development_path(package_name)`

Find all development paths for package by searching all development directories.

**Parameters**:
- `package_name` (str): Package name to find

**Returns**:
- `List[str]`: List of development paths where package exists (can be multiple!), empty list if not found

**Example**:
```python
from basefunctions.runtime import find_development_path

paths = find_development_path("basefunctions")
# Returns: ["/Users/user/Code/neuraldev/basefunctions"]
```

#### `get_runtime_path(package_name)`

Get runtime base path for package based on environment detection.

**Parameters**:
- `package_name` (str): Package name to get path for

**Returns**:
- `str`: Base runtime path for package (development or deployment)

**Logic**:
1. Check if CWD is within any development directory for this package
2. If yes: return development path
3. If no: return deployment path

**Example**:
```python
from basefunctions.runtime import get_runtime_path

# In development directory
path = get_runtime_path("basefunctions")
# Returns: /Users/user/Code/neuraldev/basefunctions

# In deployment or elsewhere
path = get_runtime_path("basefunctions")
# Returns: /Users/user/.neuraldevelopment/packages/basefunctions
```

#### `get_runtime_component_path(package_name, component)`

Get runtime path for a specific package component.

**Parameters**:
- `package_name` (str): Package name to get path for
- `component` (str): Component name (config, logs, data, etc.)

**Returns**:
- `str`: Complete path to package component

#### `get_runtime_config_path(package_name)`

Get runtime config path for a package.

**Parameters**:
- `package_name` (str): Package name to get config path for

**Returns**:
- `str`: Complete path to package config directory

**Example**:
```python
from basefunctions.runtime import get_runtime_config_path

config_path = get_runtime_config_path("basefunctions")
# Dev: /Users/user/Code/neuraldev/basefunctions/config
# Deploy: /Users/user/.neuraldevelopment/packages/basefunctions/config
```

#### `get_runtime_log_path(package_name)`

Get runtime log path for a package.

**Parameters**:
- `package_name` (str): Package name to get log path for

**Returns**:
- `str`: Complete path to package log directory

#### `get_runtime_template_path(package_name)`

Get runtime template config path for a package.

**Parameters**:
- `package_name` (str): Package name to get template path for

**Returns**:
- `str`: Complete path to package template config directory

#### `create_root_structure()`

Create initial deployment root directory structure.

**Raises**:
- `Exception`: If directory creation fails

**Creates**:
- `~/.neuraldevelopment/`
- `~/.neuraldevelopment/bin/`
- `~/.neuraldevelopment/packages/`

#### `create_bootstrap_package_structure(package_name)`

Create minimal package directory structure (bootstrap phase).

**Parameters**:
- `package_name` (str): Package name for which to create structure

**Raises**:
- `ValueError`: If package_name is None or empty
- `Exception`: If directory creation fails

**Creates**:
- `config/`
- `templates/config/`

#### `create_full_package_structure(package_name, custom_directories=None)`

Create full package directory structure with custom or default directories.

**Parameters**:
- `package_name` (str): Package name for which to create structure
- `custom_directories` (list, optional): Custom directories list, uses DEFAULT_PACKAGE_DIRECTORIES if None

**Raises**:
- `ValueError`: If package_name is None or empty
- `Exception`: If directory creation fails

**Default Creates**:
- `config/`
- `logs/`
- `templates/config/`

---

### Exceptions

#### `DeploymentError`

Exception raised during deployment operations.

**Inherits**: `Exception`

**Example**:
```python
from basefunctions import DeploymentError

try:
    manager.deploy_module("mypackage")
except DeploymentError as e:
    print(f"Deployment failed: {e}")
```

#### `VenvUtilsError`

Virtual environment utility operation failed.

**Inherits**: `Exception`

**Example**:
```python
from basefunctions import VenvUtilsError

try:
    VenvUtils.install_requirements(venv_path, requirements)
except VenvUtilsError as e:
    print(f"Installation failed: {e}")
```

---

## Summary

The Runtime Module provides a comprehensive infrastructure for:

1. **Deployment Management**: Hash-based change detection, intelligent deployment
2. **Virtual Environment Operations**: Platform-aware venv utilities
3. **Version Tracking**: Git-based version management with dev indicators
4. **Path Resolution**: Context-aware runtime paths (dev vs deployment)
5. **Bootstrap Support**: Self-deployment capability for framework

**Key Principles**:
- KISSS: Keep It Simple, Straightforward, and Smart
- Platform awareness: Cross-platform compatibility
- Context detection: Automatic environment detection
- Change detection: Deploy only when needed
- Isolation: Separate development and deployment environments

**Best Practices**:
- Always commit before deploying
- Use semantic versioning
- Trust change detection (avoid `--force`)
- Use runtime path functions (never hardcode)
- Test locally before deploying
- Handle errors appropriately

For more information, see the [basefunctions documentation](https://github.com/neuraldevelopment/basefunctions).

---

**End of Runtime Module Guide**
