"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Export functions for KPI history to various formats (DataFrame, etc)
 Log:
 v1.5 : Added 3-level KPI grouping (category.package.subgroup) with backward compatibility
 v1.4 : Refactored to use central table format configuration
        (breaking change: removed tablefmt parameter)
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

# Project modules
from basefunctions.utils.table_formatter import get_table_format


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
        import pandas as pd  # pylint: disable=import-outside-toplevel
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


def _parse_kpi_parts(kpi_key: str) -> Tuple[str, str, str]:
    """
    Parse KPI key into category, package, subgroup parts.

    Parameters
    ----------
    kpi_key : str
        Full KPI key in dot notation (e.g., "business.portfolio.returns")

    Returns
    -------
    Tuple[str, str, str]
        Tuple of (category, package, subgroup) where empty strings
        represent missing parts

    Examples
    --------
    >>> _parse_kpi_parts("business.portfolio.returns")
    ('business', 'portfolio', 'returns')
    >>> _parse_kpi_parts("business.portfolio")
    ('business', 'portfolio', '')
    >>> _parse_kpi_parts("business")
    ('business', '', '')
    """
    parts = kpi_key.split(".")
    category = parts[0] if len(parts) > 0 else ""
    package = parts[1] if len(parts) > 1 else ""
    subgroup = parts[2] if len(parts) > 2 else ""
    return category, package, subgroup


def _build_section_header(category: str, package: str, subgroup: str) -> str:
    """
    Build section header from KPI parts.

    Parameters
    ----------
    category : str
        Category name (e.g., "business")
    package : str
        Package name (e.g., "portfolio")
    subgroup : str
        Subgroup name (e.g., "returns")

    Returns
    -------
    str
        Formatted section header (e.g., "## Business KPIs - Portfolio - Returns")

    Examples
    --------
    >>> _build_section_header("business", "portfolio", "returns")
    '## Business KPIs - Portfolio - Returns'
    >>> _build_section_header("business", "portfolio", "")
    '## Business KPIs - Portfolio'
    >>> _build_section_header("business", "", "")
    '## Business KPIs'
    """
    cap_category = category.capitalize()
    cap_package = package.capitalize()
    cap_subgroup = subgroup.capitalize()

    if cap_subgroup:
        return f"## {cap_category} KPIs - {cap_package} - {cap_subgroup}"
    if cap_package:
        return f"## {cap_category} KPIs - {cap_package}"
    return f"## {cap_category} KPIs"


def _format_kpi_value(value: float, decimals: int) -> str:
    """
    Format KPI value as string with appropriate decimal places.

    Parameters
    ----------
    value : float
        Numeric value to format
    decimals : int
        Number of decimal places for float values

    Returns
    -------
    str
        Formatted value string (int if whole number, else decimal)

    Examples
    --------
    >>> _format_kpi_value(100.0, 2)
    '100'
    >>> _format_kpi_value(100.45, 2)
    '100.45'
    >>> _format_kpi_value(100.456, 2)
    '100.46'
    """
    if value == int(value):
        return str(int(value))
    return f"{value:.{decimals}f}"


def _flatten_with_kpi_value(
    d: Dict[str, Any], prefix: str = ""
) -> Dict[str, Dict[str, Any]]:
    """
    Flatten dict to dot-notation but preserve KPIValue dicts at leaf level.

    Parameters
    ----------
    d : Dict[str, Any]
        Nested dictionary to flatten
    prefix : str, default ""
        Prefix for keys (used in recursion)

    Returns
    -------
    Dict[str, Dict[str, Any]]
        Flattened dictionary preserving KPIValue structure at leaves

    Examples
    --------
    >>> nested = {"portfolio": {"balance": {"value": 100.0, "unit": "USD"}}}
    >>> _flatten_with_kpi_value(nested)
    {'portfolio.balance': {'value': 100.0, 'unit': 'USD'}}
    """
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


def _organize_kpis_by_group(
    flattened: Dict[str, Dict[str, Any]]
) -> Dict[str, List[Tuple[str, Dict[str, Any]]]]:
    """
    Organize flattened KPIs into groups by category.package.subgroup.

    Parameters
    ----------
    flattened : Dict[str, Dict[str, Any]]
        Flattened KPI dictionary with full keys

    Returns
    -------
    Dict[str, List[Tuple[str, Dict[str, Any]]]]
        Dictionary mapping group key to list of (remaining_key, value_dict) tuples

    Examples
    --------
    >>> kpis = {"business.portfolio.returns.total": {"value": 100.0, "unit": "USD"}}
    >>> _organize_kpis_by_group(kpis)
    {'business.portfolio.returns': [('total', {'value': 100.0, 'unit': 'USD'})]}
    """
    grouped: Dict[str, List[Tuple[str, Dict[str, Any]]]] = {}

    for key, value_dict in flattened.items():
        parts = key.split(".")

        # Determine group key and remaining key based on path depth
        if len(parts) >= 3:
            # 3-level grouping: category.package.subgroup
            group_key = f"{parts[0]}.{parts[1]}.{parts[2]}"
            remaining_key = ".".join(parts[3:]) if len(parts) > 3 else parts[2]
        elif len(parts) >= 2:
            # Backward compatibility: 2-level fallback
            group_key = f"{parts[0]}.{parts[1]}"
            remaining_key = ".".join(parts[2:]) if len(parts) > 2 else parts[1]
        else:
            # Edge case: single segment
            group_key = parts[0]
            remaining_key = parts[0]

        if group_key not in grouped:
            grouped[group_key] = []
        grouped[group_key].append((remaining_key, value_dict))

    return grouped


def print_kpi_table(
    kpis: Dict[str, Any],
    filter_patterns: Optional[List[str]] = None,
    sort_keys: bool = True,
    include_units: bool = True,
    decimals: int = 2
) -> None:
    """
    Print KPI dictionary as formatted table grouped by category.package.subgroup.

    Groups KPIs by first three path segments (category.package.subgroup) and prints
    separate table per group. Backward compatible with 2-segment KPIs (legacy support).
    Supports wildcard filtering with fnmatch. Table format is configured centrally
    via config.json.

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

    # Flatten and filter KPIs
    flat_kpis = _flatten_with_kpi_value(kpis)
    if filter_patterns:
        flat_kpis = {
            k: v for k, v in flat_kpis.items()
            if any(fnmatch.fnmatch(k, p) for p in filter_patterns)
        }

    if not flat_kpis:
        print("Keine KPIs nach Filterung gefunden")
        return

    # Group and sort KPIs
    grouped = _organize_kpis_by_group(flat_kpis)
    group_keys = sorted(grouped.keys()) if sort_keys else list(grouped.keys())

    # Print each group as separate table
    for group_key in group_keys:
        items = grouped[group_key]

        # Sort items within group if requested
        if sort_keys:
            items = sorted(items, key=lambda x: x[0])

        # Build table rows
        rows = [
            [
                name,
                _format_kpi_value(vdict["value"], decimals),
                vdict.get("unit") or "-"
            ] if include_units else [
                name,
                _format_kpi_value(vdict["value"], decimals)
            ]
            for name, vdict in items
        ]

        # Parse and print
        cat, pkg, subg = _parse_kpi_parts(group_key)
        print(_build_section_header(cat, pkg, subg))

        # Build and print table
        cols = [
            (subg.capitalize() if subg else pkg.capitalize() if pkg else cat.capitalize()),
            "Value"
        ] + (["Unit"] if include_units else [])
        print(tabulate(rows, headers=cols, tablefmt=get_table_format(), numalign="right"))
        print()  # Blank line between groups
