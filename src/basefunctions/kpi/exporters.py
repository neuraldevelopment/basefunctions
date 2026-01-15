"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Export functions for KPI history to various formats (DataFrame, etc)
 Log:
 v1.0 : Initial implementation
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
# Standard Library
from datetime import datetime
from typing import Any, Dict, List, Tuple


# =============================================================================
# FUNCTION DEFINITIONS
# =============================================================================
def _flatten_dict(d: Dict[str, Any], prefix: str = "") -> Dict[str, float]:
    """
    Flatten nested dictionary using dot notation.

    Parameters
    ----------
    d : Dict[str, Any]
        Nested dictionary to flatten
    prefix : str, default ""
        Prefix for keys (used in recursion)

    Returns
    -------
    Dict[str, float]
        Flattened dictionary with dot-notation keys.
        Example: {"portfolio.balance": 100.0, "balance": 50.0}
    """
    result: Dict[str, float] = {}

    for key, value in d.items():
        full_key = f"{prefix}.{key}" if prefix else key

        if isinstance(value, dict):
            result.update(_flatten_dict(value, full_key))
        else:
            result[full_key] = float(value)

    return result


def export_to_dataframe(
    history: List[Tuple[datetime, Dict[str, Any]]]
):
    """
    Export KPI history to pandas DataFrame with flattened columns.

    Parameters
    ----------
    history : List[Tuple[datetime, Dict[str, Any]]]
        KPI history from KPICollector.get_history()

    Returns
    -------
    pd.DataFrame
        DataFrame with timestamp index and flattened KPI columns.
        Nested KPIs use dot notation (e.g., "portfolio.balance").

    Raises
    ------
    ImportError
        If pandas is not installed
    ValueError
        If history is empty
    """
    try:
        import pandas as pd
    except ImportError as exc:
        raise ImportError(
            "pandas ist nicht installiert. Installiere mit: pip install pandas"
        ) from exc

    if not history:
        raise ValueError("History ist leer - keine Daten zum Exportieren")

    timestamps = [ts for ts, _ in history]
    flattened_rows = [_flatten_dict(kpis) for _, kpis in history]

    df = pd.DataFrame(flattened_rows, index=timestamps)
    df.index.name = "timestamp"

    return df
