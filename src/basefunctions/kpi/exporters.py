"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Export functions for KPI history to various formats (DataFrame, etc)
 Log:
 v1.3 : Added print_kpi_table for formatted console output with grouping/filtering
 v1.2 : Add KPIValue format support with optional unit suffixes in column names
 v1.1 : Added category filtering functions (export_by_category, export_business_technical_split)
 v1.0 : Initial implementation
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
# Standard Library
import fnmatch
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Tuple

# Third-party
from tabulate import tabulate


# =============================================================================
# FUNCTION DEFINITIONS
# =============================================================================
def _flatten_dict(
    d: Dict[str, Any],
    prefix: str = "",
    include_units_in_columns: bool = False
) -> Dict[str, float]:
    """
    Flatten nested dictionary using dot notation with KPIValue support.

    Handles KPIValue format {"value": float, "unit": Optional[str]} by
    extracting the numeric value and optionally appending unit to column name.

    Parameters
    ----------
    d : Dict[str, Any]
        Nested dictionary to flatten (may contain KPIValue dicts)
    prefix : str, default ""
        Prefix for keys (used in recursion)
    include_units_in_columns : bool, default False
        If True, append unit suffix to column names (e.g., "balance_USD").
        If False, use plain column names (e.g., "balance").

    Returns
    -------
    Dict[str, float]
        Flattened dictionary with dot-notation keys and numeric values.
        Example: {"portfolio.balance": 100.0, "portfolio.balance_USD": 100.0}

    Examples
    --------
    >>> kpis = {"portfolio": {"balance": {"value": 100.0, "unit": "USD"}}}
    >>> _flatten_dict(kpis)
    {'portfolio.balance': 100.0}

    >>> _flatten_dict(kpis, include_units_in_columns=True)
    {'portfolio.balance_USD': 100.0}
    """
    result: Dict[str, float] = {}

    for key, value in d.items():
        full_key = f"{prefix}.{key}" if prefix else key

        if isinstance(value, dict):
            # Check if it's KPIValue format
            if "value" in value and "unit" in value:
                # Extract numeric value only
                numeric_value = float(value["value"])

                # Optional: Add unit to column name
                if include_units_in_columns and value.get("unit"):
                    unit_suffix = _format_unit_suffix(value["unit"])
                    full_key = f"{full_key}{unit_suffix}"

                result[full_key] = numeric_value
            else:
                # Regular nested dict - recurse
                result.update(
                    _flatten_dict(value, full_key, include_units_in_columns)
                )
        else:
            # Plain value (backward compatibility)
            result[full_key] = float(value)

    return result


def _format_unit_suffix(unit: str) -> str:
    """
    Format unit as column name suffix.

    Parameters
    ----------
    unit : str
        Unit string (e.g., "USD", "%", "s")

    Returns
    -------
    str
        Formatted suffix for column name

    Examples
    --------
    >>> _format_unit_suffix("USD")
    '_USD'
    >>> _format_unit_suffix("%")
    '_pct'
    >>> _format_unit_suffix("s")
    '_s'
    """
    if unit == "%":
        return "_pct"
    return f"_{unit}"


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
    history: List[Tuple[datetime, Dict[str, Any]]],
    include_units_in_columns: bool = False
):
    """
    Export KPI history to pandas DataFrame with flattened columns.

    Supports KPIValue format {"value": float, "unit": Optional[str]}.
    Units can optionally be included in column names as suffixes.

    Parameters
    ----------
    history : List[Tuple[datetime, Dict[str, Any]]]
        KPI history from KPICollector.get_history()
    include_units_in_columns : bool, default False
        If True, append unit suffix to column names (e.g., "balance_USD").
        If False, use plain column names (e.g., "balance").

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

    Examples
    --------
    >>> history = [(datetime.now(), {
    ...     "portfolio": {"balance": {"value": 100.0, "unit": "USD"}}
    ... })]
    >>> df = export_to_dataframe(history)
    >>> list(df.columns)
    ['portfolio.balance']

    >>> df = export_to_dataframe(history, include_units_in_columns=True)
    >>> list(df.columns)
    ['portfolio.balance_USD']
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
    flattened_rows = [
        _flatten_dict(kpis, include_units_in_columns=include_units_in_columns)
        for _, kpis in history
    ]

    df = pd.DataFrame(flattened_rows, index=timestamps)
    df.index.name = "timestamp"

    return df


def export_by_category(
    history: List[Tuple[datetime, Dict[str, Any]]],
    category: Literal["business", "technical"],
    include_units_in_columns: bool = False
):
    """
    Export KPI history filtered by category prefix.

    Parameters
    ----------
    history : List[Tuple[datetime, Dict[str, Any]]]
        KPI history from KPICollector.get_history()
    category : Literal["business", "technical"]
        Category to filter by (business/technical prefix)
    include_units_in_columns : bool, default False
        If True, append unit suffix to column names (e.g., "balance_USD")

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
    ...     "business.revenue": {"value": 1000.0, "unit": "USD"},
    ...     "technical.cpu_usage": {"value": 50.0, "unit": "%"}
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

    return export_to_dataframe(filtered_history, include_units_in_columns)


def export_business_technical_split(
    history: List[Tuple[datetime, Dict[str, Any]]],
    include_units_in_columns: bool = False
) -> Tuple[Any, Any]:
    """
    Export KPI history split into business and technical DataFrames.

    Parameters
    ----------
    history : List[Tuple[datetime, Dict[str, Any]]]
        KPI history from KPICollector.get_history()
    include_units_in_columns : bool, default False
        If True, append unit suffix to column names (e.g., "balance_USD")

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
    ...     "business.revenue": {"value": 1000.0, "unit": "USD"},
    ...     "business.orders": {"value": 50.0, "unit": None},
    ...     "technical.cpu_usage": {"value": 50.0, "unit": "%"},
    ...     "technical.memory_mb": {"value": 512.0, "unit": "MB"}
    ... })]
    >>> business_df, technical_df = export_business_technical_split(history)
    >>> list(business_df.columns)
    ['business.revenue', 'business.orders']
    >>> list(technical_df.columns)
    ['technical.cpu_usage', 'technical.memory_mb']
    """
    business_df = export_by_category(history, "business", include_units_in_columns)
    technical_df = export_by_category(history, "technical", include_units_in_columns)

    return business_df, technical_df


def print_kpi_table(
    kpis: Dict[str, Any],
    filter_patterns: Optional[List[str]] = None,
    sort_keys: bool = True,
    include_units: bool = True,
    tablefmt: str = "grid",
    decimals: int = 2
) -> None:
    """
    Print KPI dictionary as formatted table grouped by category.package.

    Groups KPIs by first two path segments (category.package) and prints
    separate table per group. Supports wildcard filtering with fnmatch.

    Parameters
    ----------
    kpis : Dict[str, Any]
        Nested KPI dictionary with KPIValue format
        {"value": float, "unit": Optional[str]}
    filter_patterns : Optional[List[str]], default None
        Wildcard patterns for filtering (OR-logic: match if ANY pattern matches).
        Examples: ["business.*"], ["*.returns.*"], ["business.portfolio.*"]
    sort_keys : bool, default True
        Sort KPI keys alphabetically within each group
    include_units : bool, default True
        Include Unit column in output table
    tablefmt : str, default "grid"
        Table format (grid, simple, plain, etc.) - passed to tabulate
    decimals : int, default 2
        Number of decimal places for float values

    Raises
    ------
    ValueError
        If decimals is negative

    Examples
    --------
    >>> kpis = {
    ...     "business": {
    ...         "portfolio": {
    ...             "returns": {"total_pnl": {"value": 1000.0, "unit": "USD"}},
    ...             "positions": {"count": {"value": 5, "unit": None}}
    ...         }
    ...     },
    ...     "technical": {
    ...         "performance": {
    ...             "cpu_usage": {"value": 45.5, "unit": "%"}
    ...         }
    ...     }
    ... }
    >>> print_kpi_table(kpis)
    ## Business KPIs - Portfolio
    ╔═══════════════════════╦═════════╦══════╗
    ║ Portfolio             ║   Value ║ Unit ║
    ╠═══════════════════════╬═════════╬══════╣
    ║ positions.count       ║       5 ║ -    ║
    ║ returns.total_pnl     ║ 1000.00 ║ USD  ║
    ╚═══════════════════════╩═════════╩══════╝
    <BLANKLINE>
    ## Technical KPIs - Performance
    ╔════════════════╦═══════╦══════╗
    ║ Performance    ║ Value ║ Unit ║
    ╠════════════════╬═══════╬══════╣
    ║ cpu_usage      ║ 45.50 ║ %    ║
    ╚════════════════╩═══════╩══════╝
    """
    # Validate input
    if decimals < 0:
        raise ValueError("decimals muss >= 0 sein")

    if not kpis:
        print("Keine KPIs vorhanden")
        return

    # Flatten nested dict to dot-notation (preserve KPIValue structure)
    def _flatten_with_kpi_value(
        d: Dict[str, Any], prefix: str = ""
    ) -> Dict[str, Dict[str, Any]]:
        """Flatten dict but preserve KPIValue dicts at leaf level."""
        result: Dict[str, Dict[str, Any]] = {}

        for key, value in d.items():
            full_key = f"{prefix}.{key}" if prefix else key

            if isinstance(value, dict):
                # Check if it's KPIValue format
                if "value" in value and "unit" in value:
                    result[full_key] = value
                else:
                    # Regular nested dict - recurse
                    result.update(_flatten_with_kpi_value(value, full_key))
            else:
                # Plain value (backward compatibility)
                result[full_key] = {"value": value, "unit": None}

        return result

    flattened = _flatten_with_kpi_value(kpis)

    # Apply wildcard filtering (OR-logic)
    if filter_patterns:
        filtered = {
            key: value
            for key, value in flattened.items()
            if any(fnmatch.fnmatch(key, pattern) for pattern in filter_patterns)
        }
    else:
        filtered = flattened

    if not filtered:
        print("Keine KPIs nach Filterung gefunden")
        return

    # Group by category.package (first two path segments)
    grouped: Dict[str, List[tuple[str, Dict[str, Any]]]] = {}
    for key, value_dict in filtered.items():
        parts = key.split(".")
        if len(parts) >= 2:
            group_key = f"{parts[0]}.{parts[1]}"
            # Store remaining path segments + value
            remaining_key = ".".join(parts[2:]) if len(parts) > 2 else parts[1]
        else:
            group_key = parts[0]
            remaining_key = parts[0]

        if group_key not in grouped:
            grouped[group_key] = []
        grouped[group_key].append((remaining_key, value_dict))

    # Sort groups if requested
    group_keys = sorted(grouped.keys()) if sort_keys else list(grouped.keys())

    # Print each group as separate table
    for group_key in group_keys:
        items = grouped[group_key]

        # Sort items within group if requested
        if sort_keys:
            items = sorted(items, key=lambda x: x[0])

        # Prepare table data
        rows = []
        for kpi_name, value_dict in items:
            # Extract value and unit from KPIValue format
            numeric_value = value_dict["value"]
            unit = value_dict.get("unit", None)

            # Format value: int detection
            if numeric_value == int(numeric_value):
                formatted_value = str(int(numeric_value))
            else:
                formatted_value = f"{numeric_value:.{decimals}f}"

            # Format unit
            unit_str = unit if unit else "-"

            if include_units:
                rows.append([kpi_name, formatted_value, unit_str])
            else:
                rows.append([kpi_name, formatted_value])

        # Generate table header from group name
        parts = group_key.split(".")
        category = parts[0].capitalize()
        package = parts[1].capitalize() if len(parts) > 1 else ""
        section_header = f"## {category} KPIs - {package}" if package else f"## {category} KPIs"

        # Table headers
        headers = [package if package else category, "Value"]
        if include_units:
            headers.append("Unit")

        # Print section header + table
        print(section_header)
        print(tabulate(rows, headers=headers, tablefmt=tablefmt, numalign="right"))
        print()  # Blank line between groups
