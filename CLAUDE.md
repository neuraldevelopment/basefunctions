# CLAUDE.md

This file provides guidance to Claude Code when working with the basefunctions repository.

## Project Context

**basefunctions** is a comprehensive Python framework (v0.5.36) providing production-ready base functionalities for rapid application development. It includes event-driven messaging, CLI framework, runtime management, I/O utilities, configuration handling, and utility decorators.

## Critical Rules

### Git Repository Access
**ABSOLUTE PROHIBITION**: Writing to git repository is COMPLETELY FORBIDDEN.
- No git commits, pushes, or repository modifications
- Read-only access to git information (status, log, diff, etc.)

### Python Code Development
All Python code modifications MUST use Python agents via slash commands:
- `/pychain` - Standard code generation with tests and review
- `/pynew` - New features (>100 LOC or complex architecture)
- `/pyfix` - Safe refactoring with test validation
- `/pyvsc` - Fix VS Code diagnostics/errors
- Direct Python file edits are FORBIDDEN

## Module Documentation

Global module documentation is available at:
- `~/.claude/agents/_docs/basefunctions.md` (56KB comprehensive reference)

This documentation includes complete API reference, architecture, design patterns, and usage examples for all agents working with basefunctions.

## Project Structure

```
basefunctions/
├── src/basefunctions/       # Source code
│   ├── cli/                 # CLI framework
│   ├── config/              # Configuration management
│   ├── events/              # Event-driven messaging system
│   ├── http/                # HTTP client
│   ├── io/                  # File operations, serialization
│   ├── pandas/              # Pandas extensions
│   ├── runtime/             # Deployment, venv utilities
│   └── utils/               # Decorators, logging, caching
├── tests/                   # Test suite (pytest)
├── docs/                    # Comprehensive documentation
├── bin/                     # Utility scripts
├── templates/               # Project scaffolding templates
└── config/                  # Configuration files
```

## Development Workflow

### Environment Setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # macOS/Linux

# Install in development mode with all dependencies
pip install -e ".[dev,test,docs]"
```

### Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=basefunctions tests/

# Run specific test file
pytest tests/cli/test_cli_application.py
```

### Code Quality

```bash
# Format code (Black, 119 char line length)
black --line-length 119 src/

# Lint with flake8 (99 char guideline)
flake8 --max-line-length=99 src/

# Lint with pylint
pylint src/basefunctions

# Type checking
mypy src/basefunctions
```

### Build and Deployment

```bash
# Build package
python -m build

# Deploy using custom DeploymentManager
./bin/deploy.py --version x.y.z
./bin/deploy.py --force  # Skip change detection
```

## Code Standards

### Style Guidelines
- **Line Length**: 119 chars max (Black), 99 char guideline (flake8)
- **Formatter**: Black (required)
- **Python Version**: >= 3.12
- **Docstring Style**: NumPy-style with sections (Parameters, Returns, Raises, Examples)
- **Import Organization**: Organized blocks with comment headers
- **Type Hints**: Required for all public APIs

### Quality Requirements
- **Test Coverage**: >80% (target: 100%)
- **Review Score**: >8.0/10.0 (using scoring_system.txt)
- **Diagnostics**: Zero VS Code errors/warnings
- **KISSS Principle**: Keep It Simple, Stupid, Safe

## Architecture Patterns

### Singleton Components
Core services using `@singleton` decorator:
- `EventBus` - Central event distribution
- `ConfigHandler` - Configuration management
- `SecretHandler` - Secure secrets storage
- `DeploymentManager` - Module deployment

### Event-Driven System
- **EventBus**: Central pub-sub system with SYNC/THREAD/CORELET/CMD modes
- **Event**: Priority, timeout, retry, data payload
- **EventHandler**: Subclass for custom event processing
- **EventContext**: Hierarchical context for event chains
- **CoreletWorker**: Process-based parallelism

### CLI Framework
- **CLIApplication**: Main application orchestrator
- **BaseCommand**: Base class for command handlers
- **CommandRegistry**: Command group management
- **CompletionHandler**: Tab completion generation
- Commands organized in groups (empty string "" for root)

### Runtime Management
- **DeploymentManager**: Hash-based change detection, version control
- **VenvUtils**: Cross-platform virtual environment operations
- **Runtime Paths**: `get_runtime_path()`, `get_runtime_config_path()`
- Bootstrap vs. Deployment vs. Development contexts

### Serialization
- **SerializerFactory**: JSON, YAML, Pickle, MessagePack backends
- **Convenience Functions**: `to_file()`, `from_file()`, `serialize()`, `deserialize()`
- Auto-detection from file extension

## Common Development Tasks

### Creating CLI Application
```python
from basefunctions import CLIApplication, BaseCommand, CommandRegistry

class HelloCommand(BaseCommand):
    def execute(self, args):
        print(f"Hello, {args.name}!")
        return 0

    def configure_parser(self, parser):
        parser.add_argument("name", help="Name to greet")

app = CLIApplication("myapp", version="1.0.0")
registry = CommandRegistry()
registry.register("hello", HelloCommand(), "Greet someone")
app.register_command_group("", registry)
app.run()
```

### Using EventBus
```python
from basefunctions import EventBus, Event, EventHandler

class MyHandler(EventHandler):
    def handle(self, event: Event):
        return {"status": "processed", "data": event.data}

bus = EventBus()
bus.register_handler("my_event", MyHandler())
event = Event("my_event", data={"key": "value"})
result = bus.publish_event(event)
```

### Deployment
```python
from basefunctions import DeploymentManager

manager = DeploymentManager()
changed, version = manager.deploy_module("mymodule", force=False)
```

## Testing Strategy

### Test Organization
- Tests in `tests/` directory mirror `src/basefunctions/` structure
- Use pytest with fixtures for common setup
- Test coverage required for all new features

### Test Patterns
- **Unit Tests**: Individual component testing
- **Integration Tests**: Component interaction testing
- **Singleton Testing**: Use reset methods for test isolation
- **Event System Testing**: Mock handlers for EventBus testing

### Running Tests
```bash
# All tests
pytest tests/

# Specific module
pytest tests/events/

# With coverage report
pytest --cov=basefunctions --cov-report=html tests/
```

## Utility Scripts (bin/)

- `create_python_project.py` - Create new Python package from templates
- `deploy.py` - Deploy module with version management
- `ppip.py` - Personal pip wrapper (local packages first)
- `create_virtual_environment.py` - Create venv
- `clean_virtual_environment.py` - Clean venv
- `update_packages.py` - Update packages
- `patch_zshrc.py` - Patch shell config

## Bootstrap vs Deployment

The codebase distinguishes three contexts:
1. **Bootstrap**: Minimal setup for basefunctions self-deployment
2. **Deployment**: Full package deployment to deployment directory
3. **Development**: Source-based development with local paths

Use appropriate path functions:
- `get_bootstrap_config_path()` - Bootstrap config path
- `get_deployment_path()` - Deployment directory
- `find_development_path()` - Development source path
- `get_runtime_path()` - Runtime data path
- `get_runtime_config_path()` - Runtime config path

## Initialization Sequence

On `import basefunctions`:
1. Auto-load package configuration via `ConfigHandler().load_config_for_package("basefunctions")`
2. Register HTTP handlers via `register_http_handlers()`
3. Initialize singleton instances on first access

## Important Files

- `pyproject.toml` - Package metadata, dependencies, build configuration
- `config/config.json` - Runtime configuration structure
- `bin/deploy.py` - Main deployment script with git tag versioning
- `src/basefunctions/__init__.py` - Public API exports
- `templates/` - Project scaffolding templates

## Documentation

Comprehensive documentation in `docs/` directory:
- `basefunctions_overview.md` - Complete framework overview
- `cli/cli_module_guide.md` - CLI framework
- `config/config_module_guide.md` - Configuration system
- `events/eventbus_usage_guide.md` - Event system
- `http/http_module_guide.md` - HTTP client
- `io/io_module_guide.md` - I/O utilities
- `pandas/pandas_module_guide.md` - Pandas extensions
- `runtime/runtime_module_guide.md` - Runtime and deployment
- `utils/utils_module_guide.md` - Utilities and decorators

## Agent Workflow

When modifying Python code:
1. Use appropriate `/py*` command (pychain, pynew, pyfix, pyvsc)
2. Agent loads global documentation from `~/.claude/agents/_docs/basefunctions.md`
3. Agent generates code following KISSS principles
4. Tests are generated automatically (>80% coverage)
5. Code review validates quality (score >8.0/10.0)
6. VS Code diagnostics checked (zero errors required)

## Dependencies

**Core Dependencies** (see pyproject.toml):
- load_dotenv >= 0.1
- msgpack >= 1.0
- pandas >= 2.0
- psutil >= 7.0
- pyyaml >= 6.0
- requests >= 2.32
- tabulate >= 0.9
- tqdm >= 4.67

**Development Dependencies**:
- pytest, pytest-cov (testing)
- black, flake8, pylint, mypy (code quality)
- build (packaging)

## Version

**Current Version**: 0.5.36
**Last Updated**: 2025-12-01
**Python**: >= 3.12
**License**: MIT

See `pyproject.toml` for current version and git tags for version history.
