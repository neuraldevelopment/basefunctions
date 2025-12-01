# basefunctions

[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.5.36-green.svg)](pyproject.toml)

A comprehensive Python framework providing production-ready base functionalities for rapid application development.

## Overview

**basefunctions** accelerates Python development with battle-tested implementations:

- **Event-Driven Architecture**: EventBus with SYNC/THREAD/CORELET/CMD execution modes
- **CLI Framework**: Professional command-line applications with tab completion
- **Runtime Management**: Deployment, virtual environment utilities, version control
- **I/O Utilities**: Multi-format serialization (JSON/YAML/Pickle/MessagePack), file operations
- **Configuration**: Secure config and secrets handling
- **Decorators**: Caching, timing, retry, thread-safety, memory profiling
- **HTTP Client**: Event-based HTTP requests
- **Pandas Extensions**: Custom DataFrame/Series accessors

## Installation

### From PyPI

```bash
pip install basefunctions
```

### From Source

```bash
git clone https://github.com/neuraldevelopment/basefunctions.git
cd basefunctions
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev,test,docs]"
```

### Installation Options

```bash
pip install basefunctions              # Core dependencies
pip install basefunctions[dev]         # + Development tools
pip install basefunctions[test]        # + Testing tools
pip install basefunctions[docs]        # + Documentation tools
pip install basefunctions[dev,test,docs]  # All dependencies
```

## Quick Start

### Event-Driven Messaging

```python
from basefunctions import EventBus, Event, EventHandler

class MyHandler(EventHandler):
    def handle(self, event: Event):
        return {"status": "processed", "data": event.data}

bus = EventBus()
bus.register_handler("my_event", MyHandler())
event = Event("my_event", data={"message": "Hello"})
result = bus.publish_event(event)
```

### CLI Application

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

### Configuration

```python
from basefunctions import ConfigHandler, SecretHandler

config = ConfigHandler()
config.load_config_for_package("myapp")
api_url = config.get("api.url", "https://api.example.com")

secrets = SecretHandler()
secrets.set("api_key", "secret123")
api_key = secrets.get("api_key")
```

### Serialization

```python
from basefunctions.io import to_file, from_file

data = {"name": "John", "age": 30}
to_file(data, "data.json")   # Auto-detects format
to_file(data, "data.yaml")
to_file(data, "data.pkl")

loaded = from_file("data.json")
```

### Decorators

```python
from basefunctions.utils import cache, timeit, retry, singleton

@cache(ttl=3600)
def expensive_computation(x):
    return x ** 2

@timeit
def slow_function():
    time.sleep(1)

@retry(max_attempts=3, delay=1.0)
def unstable_api_call():
    return requests.get("https://api.example.com").json()

@singleton
class DatabaseConnection:
    pass
```

### HTTP Client

```python
from basefunctions.http import HttpClient, HttpClientHandler
from basefunctions import EventBus, Event

bus = EventBus()
bus.register_handler("_http_request", HttpClientHandler())

event = Event("_http_request", data={
    "url": "https://api.github.com",
    "method": "GET",
    "headers": {"Accept": "application/json"}
})
result = bus.publish_event(event)
```

### Deployment

```python
from basefunctions.runtime import DeploymentManager, get_runtime_path

manager = DeploymentManager()
changed, version = manager.deploy_module("myapp", force=False)

config_path = get_runtime_path("config")
data_path = get_runtime_path("data")
```

## Key Features

- **Event System**: Multiple execution modes (SYNC/THREAD/CORELET/CMD), priority scheduling, retry logic
- **CLI Framework**: Command groups, tab completion, progress tracking, help system
- **Runtime Management**: Cross-platform venv, hash-based deployment, version control
- **I/O**: JSON/YAML/Pickle/MessagePack serialization, file operations, output redirection
- **Configuration**: Hierarchical config, encrypted secrets, auto-loading
- **Utilities**: `@cache`, `@timeit`, `@retry`, `@singleton`, `@threadsafe`, `@profile_memory`

## Documentation

Comprehensive guides in `docs/` directory:
- [Framework Overview](docs/basefunctions_overview.md)
- [CLI Module](docs/cli/cli_module_guide.md)
- [Configuration](docs/config/config_module_guide.md)
- [EventBus](docs/events/eventbus_usage_guide.md)
- [HTTP Client](docs/http/http_module_guide.md)
- [I/O Utilities](docs/io/io_module_guide.md)
- [Pandas Extensions](docs/pandas/pandas_module_guide.md)
- [Runtime & Deployment](docs/runtime/runtime_module_guide.md)
- [Utilities](docs/utils/utils_module_guide.md)

## Development

### Setup

```bash
git clone https://github.com/neuraldevelopment/basefunctions.git
cd basefunctions
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,test]"
```

### Testing

```bash
pytest tests/                            # All tests
pytest --cov=basefunctions tests/        # With coverage
pytest tests/cli/test_cli_application.py # Specific file
```

### Code Quality

```bash
black --line-length 119 src/             # Format
flake8 --max-line-length=99 src/         # Lint
pylint src/basefunctions                 # Lint
mypy src/basefunctions                   # Type check
```

### Building

```bash
python -m build                          # Build package
./bin/deploy.py --version x.y.z          # Deploy
./bin/deploy.py --force                  # Force deploy
```

### Utility Scripts (bin/)

- `create_python_project.py` - Create Python package from templates
- `deploy.py` - Deploy with version management
- `ppip.py` - Personal pip wrapper
- `create_virtual_environment.py` - Create venv
- `clean_virtual_environment.py` - Clean venv
- `update_packages.py` - Update packages
- `patch_zshrc.py` - Patch shell config

## Architecture

### Module Structure

```
src/basefunctions/
├── cli/              # CLI framework
├── config/           # Configuration management
├── events/           # Event-driven messaging
├── http/             # HTTP client
├── io/               # File operations, serialization
├── pandas/           # Pandas extensions
├── runtime/          # Deployment, venv utilities
└── utils/            # Decorators, logging, caching
```

### Design Patterns

- **Singleton**: EventBus, ConfigHandler, SecretHandler, DeploymentManager
- **Strategy**: SerializerFactory, EventHandler plugins
- **Factory**: EventFactory, SerializerFactory
- **Observer**: Observable/Observer implementations
- **Command**: CLI command pattern
- **Decorator**: Utility decorators for cross-cutting concerns

### Bootstrap vs Deployment

Three contexts:
- **Bootstrap**: Minimal setup for self-deployment
- **Deployment**: Full package deployment
- **Development**: Source-based development

Use: `get_bootstrap_config_path()`, `get_deployment_path()`, `find_development_path()`, `get_runtime_path()`

## Requirements

- **Python**: >= 3.12
- **Core**: load_dotenv, msgpack, pandas, psutil, pyyaml, requests, tabulate, tqdm
- **Dev**: pytest, black, flake8, pylint, mypy
- **Build**: build

See `pyproject.toml` for versions.

## License

MIT License - see [LICENSE](LICENSE) file.

## Author

**neuraldevelopment**
Email: neutro2@outlook.de

## Version

**Current**: 0.5.36
**Updated**: 2025-12-01
**Python**: >= 3.12

See git tags for version history.
