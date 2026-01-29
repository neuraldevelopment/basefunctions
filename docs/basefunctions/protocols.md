# Protocols - User Documentation

**Package:** basefunctions
**Subpackage:** protocols
**Version:** 0.5.75
**Purpose:** Type protocol definitions for structural typing and duck-typing with type safety

---

## Overview

The protocols subpackage provides Protocol definitions that enable duck-typing with full IDE autocomplete and static type-checker support.

**Key Features:**
- Structural typing without inheritance
- IDE autocomplete support
- Static type checking with mypy/pyright
- Flexible interface contracts
- No runtime overhead

**Common Use Cases:**
- Defining interfaces without base classes
- Framework integration points
- Plugin systems
- Type-safe duck-typing
- Decoupled component design

---

## Public APIs

### KPIProvider Protocol

**Purpose:** Interface for objects providing Key Performance Indicators with hierarchical structure

```python
from basefunctions.protocols import KPIProvider

class MyComponent:
    """No inheritance required - just implement the methods"""

    def get_kpis(self) -> dict[str, float]:
        return {"metric": 100.0}

    def get_subproviders(self) -> dict[str, "KPIProvider"] | None:
        return None
```

**Required Methods:**

| Method | Return Type | Description |
|--------|-------------|-------------|
| `get_kpis()` | dict[str, float] | Return current KPI values |
| `get_subproviders()` | dict[str, KPIProvider] or None | Return nested providers |

**When to Implement:**
- Components that expose metrics
- Hierarchical monitoring systems
- Business/technical KPI sources
- Performance tracking objects

**Implementation Example:**

```python
from basefunctions.protocols import KPIProvider

class TradingBot:
    """Trading bot implementing KPIProvider protocol"""

    def __init__(self):
        self.balance = 10000.0
        self.trades = 42
        self.positions = []

    def get_kpis(self) -> dict[str, float]:
        """Return current KPI values"""
        return {
            "business.balance": self.balance,
            "business.trade_count": float(self.trades),
            "business.position_count": float(len(self.positions)),
            "technical.cpu_percent": 25.5,
            "technical.memory_mb": 128.0
        }

    def get_subproviders(self) -> dict[str, KPIProvider] | None:
        """Return nested providers (positions)"""
        if not self.positions:
            return None

        return {
            f"position_{i}": position
            for i, position in enumerate(self.positions)
        }
```

**Important Rules:**
1. `get_kpis()` MUST return `dict[str, float]`
2. All values must be numeric (float)
3. `get_subproviders()` returns dict or None (not empty dict)
4. Use "business." or "technical." prefixes for filtering
5. No inheritance required - just implement the methods

---

### MetricsSource Protocol

**Purpose:** Simplified interface for objects providing flat KPI metrics

```python
from basefunctions.protocols import MetricsSource

class Portfolio:
    """Portfolio implementing MetricsSource protocol"""

    def __init__(self):
        self.total_return = 0.15
        self.sharpe_ratio = 1.8

    def get_kpis(self) -> dict[str, float]:
        """Return KPI metrics"""
        return {
            "total_return": self.total_return,
            "sharpe_ratio": self.sharpe_ratio,
            "max_drawdown": -0.12
        }
```

**Required Methods:**

| Method | Return Type | Description |
|--------|-------------|-------------|
| `get_kpis()` | dict[str, float] | Return metric dictionary |

**When to Implement:**
- Simple metric sources
- Single-level metrics (no hierarchy)
- Backward compatibility with older code
- Flat reporting structures

**Difference from KPIProvider:**
- MetricsSource: Only `get_kpis()` method (simpler)
- KPIProvider: Both `get_kpis()` and `get_subproviders()` (hierarchical)

---

## Usage Examples

### Basic Protocol Implementation

**Scenario:** Create simple metrics provider

```python
from basefunctions.protocols import MetricsSource

class SystemMonitor:
    """System monitor implementing MetricsSource"""

    def __init__(self):
        self.cpu = 45.5
        self.memory = 2048.0
        self.disk = 512.0

    def get_kpis(self) -> dict[str, float]:
        return {
            "cpu_percent": self.cpu,
            "memory_mb": self.memory,
            "disk_mb": self.disk,
            "uptime_hours": 24.5
        }

# Use with type checking
def display_metrics(source: MetricsSource):
    """Type-safe function accepting any MetricsSource"""
    kpis = source.get_kpis()
    for name, value in kpis.items():
        print(f"{name}: {value:.2f}")

# Works with our implementation
monitor = SystemMonitor()
display_metrics(monitor)  # Type checker approves!
```

---

### Hierarchical KPI Provider

**Scenario:** Implement nested KPI structure

```python
from basefunctions.protocols import KPIProvider

class Position:
    """Individual position with KPIs"""

    def __init__(self, symbol, quantity, price):
        self.symbol = symbol
        self.quantity = quantity
        self.price = price

    def get_kpis(self) -> dict[str, float]:
        return {
            "business.quantity": float(self.quantity),
            "business.value": self.quantity * self.price,
            "business.avg_price": self.price
        }

    def get_subproviders(self) -> None:
        return None


class Portfolio:
    """Portfolio with nested positions"""

    def __init__(self):
        self.cash = 10000.0
        self.positions = [
            Position("AAPL", 10, 150.0),
            Position("GOOGL", 5, 2800.0)
        ]

    def get_kpis(self) -> dict[str, float]:
        total_value = sum(p.quantity * p.price for p in self.positions)
        return {
            "business.cash": self.cash,
            "business.total_value": total_value + self.cash,
            "business.position_count": float(len(self.positions)),
            "technical.memory_mb": 64.0
        }

    def get_subproviders(self) -> dict[str, KPIProvider]:
        return {
            position.symbol: position
            for position in self.positions
        }

# Collect recursively
from basefunctions.kpi import KPICollector

portfolio = Portfolio()
collector = KPICollector()
kpis = collector.collect(portfolio)

print(f"Total value: {kpis['business.total_value']}")
print(f"AAPL value: {kpis['AAPL']['business.value']}")
```

---

### Type-Safe Function Parameters

**Scenario:** Use protocols for type hints in functions

```python
from basefunctions.protocols import KPIProvider, MetricsSource
from typing import Union

def collect_and_log(source: MetricsSource) -> None:
    """Accept any object implementing MetricsSource"""
    kpis = source.get_kpis()
    for name, value in kpis.items():
        print(f"[METRIC] {name}: {value}")

def collect_hierarchical(provider: KPIProvider) -> dict:
    """Accept any object implementing KPIProvider"""
    from basefunctions.kpi import KPICollector
    collector = KPICollector()
    return collector.collect(provider)

# Both accept implementations without inheritance
class MyClass:
    def get_kpis(self):
        return {"metric": 1.0}

    def get_subproviders(self):
        return None

obj = MyClass()
collect_and_log(obj)  # Works!
collect_hierarchical(obj)  # Works!
```

---

### Plugin System

**Scenario:** Create extensible plugin architecture

```python
from basefunctions.protocols import MetricsSource
from typing import Dict

class PluginRegistry:
    """Registry for metric plugins"""

    def __init__(self):
        self.plugins: Dict[str, MetricsSource] = {}

    def register(self, name: str, plugin: MetricsSource) -> None:
        """Register plugin - any MetricsSource implementation"""
        self.plugins[name] = plugin

    def collect_all(self) -> dict[str, dict[str, float]]:
        """Collect metrics from all plugins"""
        result = {}
        for name, plugin in self.plugins.items():
            result[name] = plugin.get_kpis()
        return result

# Create plugins (no inheritance required!)
class DatabasePlugin:
    def get_kpis(self):
        return {"query_time_ms": 45.2, "connections": 5.0}

class CachePlugin:
    def get_kpis(self):
        return {"hit_rate": 0.85, "size_mb": 128.0}

# Register and collect
registry = PluginRegistry()
registry.register("database", DatabasePlugin())
registry.register("cache", CachePlugin())

all_metrics = registry.collect_all()
print(all_metrics)
# Output: {'database': {'query_time_ms': 45.2, ...}, 'cache': {...}}
```

---

### Integration with Existing Classes

**Scenario:** Add protocol support to existing classes

```python
from basefunctions.protocols import MetricsSource

class ExistingClass:
    """Existing class without modifications"""

    def __init__(self):
        self.value = 100

    def process(self):
        self.value += 10

# Add protocol support via adapter
class ExistingClassAdapter:
    """Adapter making ExistingClass a MetricsSource"""

    def __init__(self, obj: ExistingClass):
        self.obj = obj

    def get_kpis(self) -> dict[str, float]:
        return {
            "value": float(self.obj.value),
            "status": 1.0  # 1.0 = active
        }

# Use adapted class
existing = ExistingClass()
existing.process()

adapter = ExistingClassAdapter(existing)
print(adapter.get_kpis())  # {'value': 110.0, 'status': 1.0}
```

---

## Choosing the Right Protocol

### When to Use MetricsSource

Use MetricsSource when:
- Simple flat metrics
- No nested structure needed
- Backward compatibility required
- Single-level reporting

```python
from basefunctions.protocols import MetricsSource

class SimpleMonitor:  # MetricsSource
    def get_kpis(self):
        return {"cpu": 50.0}
```

**Pros:**
- Simpler interface
- Less code
- Faster implementation

**Cons:**
- No hierarchical support
- Cannot nest providers

---

### When to Use KPIProvider

Use KPIProvider when:
- Hierarchical structure needed
- Nested components with metrics
- Complex system monitoring
- Recursive collection required

```python
from basefunctions.protocols import KPIProvider

class HierarchicalSystem:  # KPIProvider
    def get_kpis(self):
        return {"total": 100.0}

    def get_subproviders(self):
        return {"component": child}
```

**Pros:**
- Hierarchical support
- Recursive collection
- Scalable architecture

**Cons:**
- More complex
- Two methods required

---

## Best Practices

### Best Practice 1: Always Return dict[str, float]

**Why:** Protocol contract and type safety

```python
# GOOD
def get_kpis(self) -> dict[str, float]:
    return {
        "count": float(self.count),  # Convert int to float
        "value": self.value
    }
```

```python
# AVOID
def get_kpis(self):  # Missing type hint
    return {
        "count": self.count,  # int instead of float
        "name": "value"  # str instead of float
    }
```

---

### Best Practice 2: Return None for No Subproviders

**Why:** Clear intent, protocol compliance

```python
# GOOD
def get_subproviders(self) -> dict[str, KPIProvider] | None:
    if not self.children:
        return None
    return {"child": self.child}
```

```python
# AVOID
def get_subproviders(self):
    return {}  # Return None instead
```

---

### Best Practice 3: Use Type Hints in Function Signatures

**Why:** IDE support and type checking

```python
# GOOD
from basefunctions.protocols import KPIProvider

def process(provider: KPIProvider) -> dict:
    return provider.get_kpis()
```

```python
# AVOID
def process(provider):  # No type hint
    return provider.get_kpis()
```

---

## Integration Examples

### Integration with KPI Collection

```python
from basefunctions.protocols import KPIProvider
from basefunctions.kpi import KPICollector

# Any KPIProvider works automatically
collector = KPICollector()
kpis = collector.collect(my_provider)  # Type-safe!
```

---

### Integration with Type Checkers

```python
from basefunctions.protocols import MetricsSource

def analyze(source: MetricsSource) -> float:
    """Type checker validates source has get_kpis()"""
    kpis = source.get_kpis()
    return sum(kpis.values())

# mypy/pyright will catch errors
class BadClass:
    pass

analyze(BadClass())  # Type error: Missing get_kpis()
```

---

## FAQ

**Q: Do I need to inherit from the Protocol?**

A: No. Protocols use structural typing - just implement the methods.

**Q: What's the difference between Protocol and ABC?**

A: Protocol = structural typing (duck-typing with types). ABC = nominal typing (explicit inheritance).

**Q: Can I add extra methods to my implementation?**

A: Yes. Protocol only defines minimum required methods.

**Q: Will this work with older Python versions?**

A: Protocol requires Python 3.8+. Use `typing_extensions` for older versions.

**Q: Is there runtime overhead?**

A: No. Protocols are purely for type checking - no runtime cost.

---

## See Also

**Related Subpackages:**
- `kpi` (`docs/basefunctions/kpi.md`) - KPI collection using protocols
- `utils` (`docs/basefunctions/utils.md`) - Utility functions

**System Documentation:**
- `~/.claude/_docs/python/basefunctions.md` - Internal architecture details

**External Resources:**
- [PEP 544 - Protocols](https://www.python.org/dev/peps/pep-0544/)
- [Python typing.Protocol documentation](https://docs.python.org/3/library/typing.html#typing.Protocol)

---

## Quick Reference

### Imports

```python
from basefunctions.protocols import KPIProvider, MetricsSource
```

### Quick Start

```python
# Step 1: Implement protocol (no inheritance!)
class MyClass:
    def get_kpis(self) -> dict[str, float]:
        return {"metric": 100.0}

    def get_subproviders(self):
        return None

# Step 2: Use with type hints
def process(provider: KPIProvider):
    return provider.get_kpis()

# Step 3: Call function
obj = MyClass()
kpis = process(obj)  # Type-safe!
```

### Cheat Sheet

| Task | Code |
|------|------|
| Import protocol | `from basefunctions.protocols import KPIProvider` |
| Implement (no inheritance) | `class X:` (just add methods) |
| Type hint parameter | `def f(p: KPIProvider):` |
| Type hint return | `def f() -> KPIProvider:` |
| Check with mypy | `mypy script.py` |
| Runtime check | Not applicable (compile-time only) |

---

**Document Version:** 1.0.0
**Last Updated:** 2026-01-29
**Subpackage Version:** 0.5.75
