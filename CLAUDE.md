# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## GIT MODIFICATIONS
ES IST KOMPLETT VERBOTEN, SCHREIBEND AUF DIE GIT REPOS ZUZUGREIFEN

## Project Overview

`basefunctions` is a Python framework providing base functionalities for Python development, including:
- Event-driven messaging system (EventBus with sync/thread/corelet modes)
- CLI application framework with tab completion
- Runtime/deployment management
- I/O utilities (serialization, file operations, output redirection)
- Configuration and secret handling
- Utility decorators and helpers
- Pandas accessor extensions
- HTTP client with handler system

## Development Commands

### Environment Setup
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On macOS/Linux

# Install package in development mode with dev dependencies
pip install -e ".[dev,test]"
```

### Testing
```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_specific.py

# Run with coverage
pytest --cov=basefunctions tests/
```

### Code Quality
```bash
# Format code (Black with 119 char line length)
black --line-length 119 src/

# Lint with flake8 (99 char guideline)
flake8 --max-line-length=99 src/

# Lint with pylint
pylint src/basefunctions
```

### Build and Deployment
```bash
# Build package
python -m build

# Deploy using DeploymentManager (custom deployment system)
./bin/deploy.py [--force] [--version x.y.z]
```

### Utility Scripts in bin/
- `create_python_project.py` - Creates new Python package from templates
- `deploy.py` - Deploys module using DeploymentManager with version management
- `ppip.py` - Personal pip wrapper (local packages first, then PyPI)
- `create_virtual_environment.py` - Creates venv for projects
- `clean_virtual_environment.py` - Cleans venv
- `update_packages.py` - Updates packages
- `patch_zshrc.py` - Patches shell config

## Architecture

### Module Structure
```
src/basefunctions/
├── cli/              # CLI framework (commands, parsers, completion)
├── config/           # ConfigHandler, SecretHandler
├── events/           # EventBus, Event, EventHandler, Corelet workers
├── http/             # HttpClient, HttpClientHandler
├── io/               # File operations, serialization, output redirection
├── pandas/           # Pandas accessor extensions
├── runtime/          # DeploymentManager, VenvUtils, version mgmt, runtime paths
└── utils/            # Decorators, logging, caching, observers, time utils
```

### Key Architectural Patterns

**Event-Driven Messaging (events/)**
- `EventBus` is a singleton central event distribution system
- Supports 3 execution modes: SYNC, THREAD, CORELET (process-based)
- `Event` objects with priority, timeout, retry support
- `EventHandler` subclasses define event processing logic
- `CoreletWorker` provides process-based parallelism
- Internal events: `_shutdown`, `_cmd_execution`, `_corelet_forwarding`

**CLI Framework (cli/)**
- `CLIApplication` orchestrates command execution
- `BaseCommand` base class for command handlers
- `CommandRegistry` manages command groups and metadata
- `CompletionHandler` provides tab completion
- `ArgumentParser`, `HelpFormatter`, `OutputFormatter` for UI
- Commands can be grouped (empty string "" for root-level)

**Runtime & Deployment (runtime/)**
- `DeploymentManager` handles module deployment with change detection
- Uses hash-based tracking in `deployment/hashes/`
- `VenvUtils` provides platform-aware virtual environment operations
- Bootstrap vs. full package structure distinction
- Runtime paths: `get_runtime_path()`, `get_runtime_config_path()`, etc.
- Version management via `version.py` and `versions()` function

**Configuration System (config/)**
- `ConfigHandler` loads package configs from `config/config.json`
- Auto-loads basefunctions config on import
- `SecretHandler` for secure credential storage

**Serialization (io/serializer.py)**
- `SerializerFactory` with JSON, YAML, Pickle, MessagePack backends
- Convenience functions: `serialize()`, `deserialize()`, `to_file()`, `from_file()`

### Singleton Pattern
Many core components use `@singleton` decorator:
- `EventBus`
- `DeploymentManager`
- `ConfigHandler`
- `SecretHandler`

### Initialization Sequence
On `import basefunctions`:
1. `ConfigHandler().load_config_for_package("basefunctions")`
2. `register_http_handlers()` registers HTTP event handlers

## Code Style

- **Line length**: 119 chars max (Black), 99 char guideline (flake8)
- **Formatter**: Black
- **Python version**: >=3.12
- **Docstring style**: NumPy-style with sections (Parameters, Returns, Raises)
- **Import organization**: Organized in blocks with comment headers
- **Logging**: Use `basefunctions.setup_logger(__name__)` and `basefunctions.get_logger(__name__)`

## Templates

The `templates/` directory contains project scaffolding:
- `python_package/` - Package structure templates
  - `project/` - pyproject.toml, README.md, .gitignore
  - `package/` - __init__.py template
  - `test/` - test template
  - `licenses/` - License templates
  - `vscode/` - VS Code settings
- `config/` - Config and alias templates

## Testing Strategy

Tests should go in `tests/` directory. The project uses pytest with optional coverage reporting.

## Common Patterns

**Creating a CLI Application:**
```python
from basefunctions import CLIApplication, BaseCommand

app = CLIApplication("myapp", version="1.0")
app.register_command_group("", MyRootCommands())
app.run()
```

**Using EventBus:**
```python
from basefunctions import EventBus, Event, EventHandler

bus = EventBus()
bus.register_handler("my_event", MyHandler())
event = Event("my_event", data={"key": "value"})
result = bus.publish_event(event)
```

**Deployment:**
```python
from basefunctions import DeploymentManager

manager = DeploymentManager()
changed, version = manager.deploy_module("mymodule", force=False)
```

## Bootstrap vs Deployment Contexts

The codebase distinguishes between:
- **Bootstrap**: Minimal setup for basefunctions self-deployment
- **Deployment**: Full package deployment to deployment directory
- **Development**: Source-based development with local paths

Use `get_bootstrap_config_path()`, `get_deployment_path()`, `find_development_path()` accordingly.

## Important Files

- `pyproject.toml` - Package metadata, dependencies, build config
- `config/config.json` - Runtime config structure
- `bin/deploy.py` - Main deployment script with git tag versioning
- `src/basefunctions/__init__.py` - Public API exports

## Documentation

Comprehensive documentation is available in the `docs/` directory:
- `docs/basefunctions_overview.md` - Complete framework overview
- `docs/cli/cli_module_guide.md` - CLI framework documentation
- `docs/config/config_module_guide.md` - Configuration system
- `docs/events/eventbus_usage_guide.md` - EventBus and event system
- `docs/http/http_module_guide.md` - HTTP client documentation
- `docs/io/io_module_guide.md` - I/O utilities and serialization
- `docs/pandas/pandas_module_guide.md` - Pandas extensions
- `docs/runtime/runtime_module_guide.md` - Runtime and deployment
- `docs/utils/utils_module_guide.md` - Utilities and decorators

## Current Version

**Version**: 0.5.32
**Last Updated**: 2025-01-24

See `pyproject.toml` for the current version and `docs/` for version-specific documentation.
