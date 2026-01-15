"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Export functions for KPI history to various formats (DataFrame, etc)
 Log:
 v1.1 : Added category filtering functions (export_by_category, export_business_technical_split)
 v1.0 : Initial implementation
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
# Standard Library
from datetime import datetime
from typing import Any, Dict, List, Literal, Tuple


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


def _filter_history_by_prefix(
    history: List[Tuple[datetime, Dict[str, Any]]], prefix: str
) -> List[Tuple[datetime, Dict[str, Any]]]:
    """
    Filter KPI history entries by key prefix.

    Parameters
    ----------
    history : List[Tuple[datetime, Dict[str, Any]]]
        KPI history from KPICollector.get_history()
    prefix : str
        Prefix to filter by (e.g., "business", "technical")

    Returns
    -------
    List[Tuple[datetime, Dict[str, Any]]]
        Filtered history with only KPIs matching the prefix
    """
    filtered_history: List[Tuple[datetime, Dict[str, Any]]] = []

    for timestamp, kpis in history:
        filtered_kpis = {
            key: value for key, value in kpis.items() if key.startswith(prefix)
        }
        if filtered_kpis:
            filtered_history.append((timestamp, filtered_kpis))

    return filtered_history


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


def export_by_category(
    history: List[Tuple[datetime, Dict[str, Any]]],
    category: Literal["business", "technical"]
):
    """
    Export KPI history filtered by category prefix.

    Parameters
    ----------
    history : List[Tuple[datetime, Dict[str, Any]]]
        KPI history from KPICollector.get_history()
    category : Literal["business", "technical"]
        Category to filter by (business/technical prefix)

    Returns
    -------
    pd.DataFrame
        DataFrame with timestamp index and filtered KPI columns.
        Only KPIs matching the category prefix are included.

    Raises
    ------
    ImportError
        If pandas is not installed
    ValueError
        If history is empty or no KPIs match the category

    Examples
    --------
    >>> history = [(datetime.now(), {
    ...     "business.revenue": 1000.0,
    ...     "technical.cpu_usage": 50.0
    ... })]
    >>> df = export_by_category(history, "business")
    >>> list(df.columns)
    ['business.revenue']
    """
    filtered_history = _filter_history_by_prefix(history, category)

    if not filtered_history:
        raise ValueError(
            f"Keine KPIs mit Präfix '{category}' in History gefunden"
        )

    return export_to_dataframe(filtered_history)


def export_business_technical_split(
    history: List[Tuple[datetime, Dict[str, Any]]]
) -> Tuple[Any, Any]:
    """
    Export KPI history split into business and technical DataFrames.

    Parameters
    ----------
    history : List[Tuple[datetime, Dict[str, Any]]]
        KPI history from KPICollector.get_history()

    Returns
    -------
    Tuple[pd.DataFrame, pd.DataFrame]
        Tuple of (business_df, technical_df) with filtered KPIs.
        Each DataFrame has timestamp index and category-specific columns.

    Raises
    ------
    ImportError
        If pandas is not installed
    ValueError
        If history is empty or either category has no KPIs

    Examples
    --------
    >>> history = [(datetime.now(), {
    ...     "business.revenue": 1000.0,
    ...     "business.orders": 50.0,
    ...     "technical.cpu_usage": 50.0,
    ...     "technical.memory_mb": 512.0
    ... })]
    >>> business_df, technical_df = export_business_technical_split(history)
    >>> list(business_df.columns)
    ['business.revenue', 'business.orders']
    >>> list(technical_df.columns)
    ['technical.cpu_usage', 'technical.memory_mb']
    """
    business_df = export_by_category(history, "business")
    technical_df = export_by_category(history, "technical")

    return business_df, technical_df
