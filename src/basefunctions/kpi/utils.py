"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Utility functions for KPI data transformation
 Log:
 v1.0 : Initial implementation
 v1.1 : Add KPIValue TypedDict for unit support
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
from typing import Any, Optional, TypedDict


# =============================================================================
# TYPE DEFINITIONS
# =============================================================================
class KPIValue(TypedDict):
    """
    KPI value with optional unit for display formatting.

    Attributes
    ----------
    value : float
        Numeric KPI value
    unit : Optional[str]
        Unit for display formatting (e.g., "USD", "%", "MB/s")
    """

    value: float
    unit: Optional[str]


# =============================================================================
# FUNCTION DEFINITIONS
# =============================================================================
def _sort_dict_recursive(d: dict[str, Any]) -> dict[str, Any]:
    """
    Recursively sort dictionary keys alphabetically.

    Parameters
    ----------
    d : dict[str, Any]
        Dictionary to sort (may contain nested dicts)

    Returns
    -------
    dict[str, Any]
        New dictionary with sorted keys at all levels
    """
    result: dict[str, Any] = {}
    for key in sorted(d.keys()):
        value = d[key]
        if isinstance(value, dict):
            result[key] = _sort_dict_recursive(value)
        else:
            result[key] = value
    return result


def group_kpis_by_name(kpis: dict[str, Any], sort_keys: bool = False) -> dict[str, Any]:
    """
    Transform flat KPI dictionary with dot-separated names into nested structure.

    Preserves insertion order of keys (Python 3.7+ dict behavior) unless sort_keys=True.

    Parameters
    ----------
    kpis : dict[str, Any]
        Flat dictionary with dot-separated keys (e.g., {"a.b.c": 1.0}).
        Values should be KPIValue format: {"value": float, "unit": Optional[str]}
    sort_keys : bool, default False
        If True, sort keys alphabetically at all nesting levels.
        If False, preserve insertion order.

    Returns
    -------
    dict[str, Any]
        Nested dictionary structure (e.g., {"a": {"b": {"c": 1.0}}}).
        Leaf values are KPIValue dicts with value and optional unit.

    Examples
    --------
    >>> group_kpis_by_name({"a.b.c": 1.0})
    {'a': {'b': {'c': 1.0}}}

    >>> group_kpis_by_name({"x": 5, "y.z": 10})
    {'x': 5, 'y': {'z': 10}}

    >>> group_kpis_by_name({})
    {}

    >>> group_kpis_by_name({"z.a": 1, "a.z": 2}, sort_keys=True)
    {'a': {'z': 2}, 'z': {'a': 1}}

    >>> kpis = {
    ...     "returns.total": {"value": 0.15, "unit": "USD"},
    ...     "risk.volatility": {"value": 0.08, "unit": "%"}
    ... }
    >>> group_kpis_by_name(kpis)
    {'returns': {'total': {'value': 0.15, 'unit': 'USD'}}, 'risk': {'volatility': {'value': 0.08, 'unit': '%'}}}
    """
    result: dict[str, Any] = {}

    for name, value in kpis.items():
        parts = name.split(".")

        if len(parts) == 1:
            # Single-level key stays flat
            result[name] = value
        else:
            # Multi-level key: build nested structure
            current = result
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            current[parts[-1]] = value

    if sort_keys:
        result = _sort_dict_recursive(result)

    return result
