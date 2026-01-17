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
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
from typing import Any


# =============================================================================
# FUNCTION DEFINITIONS
# =============================================================================
def group_kpis_by_name(kpis: dict[str, Any]) -> dict[str, Any]:
    """
    Transform flat KPI dictionary with dot-separated names into nested structure.

    Preserves insertion order of keys (Python 3.7+ dict behavior).

    Parameters
    ----------
    kpis : dict[str, Any]
        Flat dictionary with dot-separated keys (e.g., {"a.b.c": 1.0})

    Returns
    -------
    dict[str, Any]
        Nested dictionary structure (e.g., {"a": {"b": {"c": 1.0}}})

    Examples
    --------
    >>> group_kpis_by_name({"a.b.c": 1.0})
    {'a': {'b': {'c': 1.0}}}

    >>> group_kpis_by_name({"x": 5, "y.z": 10})
    {'x': 5, 'y': {'z': 10}}

    >>> group_kpis_by_name({})
    {}
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

    return result
