"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Export functions for KPI history to various formats (DataFrame, etc)
 Log:
 v1.7 : Added currency override parameter (default EUR) - replaces all currency codes with specified currency
 v1.6 : MAJOR REFACTOR - print_kpi_table() 2-level grouping (package-only) with subgroup sections
        Breaking changes: Removed include_units parameter, Units integrated into Value column,
        Changed output format to single table per package with UPPERCASE subgroup headers
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


# =============================================================================
# CONSTANTS
# =============================================================================
# Known currency codes that will be replaced by currency parameter
CURRENCY_CODES = {
    "USD", "EUR", "GBP", "CHF", "JPY", "CNY", "CAD", "AUD",
    "SEK", "NOK", "DKK", "PLN", "CZK", "HUF", "RUB", "INR",
    "BRL", "MXN", "ZAR", "KRW", "SGD", "HKD", "NZD", "TRY"
}

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


def _extract_metric_name(kpi_key: str) -> str:
    """
    Extract only the metric name (last segment) from full KPI key.

    Parameters
    ----------
    kpi_key : str
        Full KPI key, e.g. "business.portfoliofunctions.activity.win_rate"

    Returns
    -------
    str
        Metric name only, e.g. "win_rate"

    Examples
    --------
    >>> _extract_metric_name("business.portfoliofunctions.activity.win_rate")
    'win_rate'
    >>> _extract_metric_name("win_rate")
    'win_rate'
    """
    parts = kpi_key.split(".")
    return parts[-1] if parts else ""


def _extract_subgroup_name(kpi_key: str) -> str:
    """
    Extract subgroup name (3rd segment) from full KPI key.

    Parameters
    ----------
    kpi_key : str
        Full KPI key, e.g. "business.portfoliofunctions.activity.win_rate"

    Returns
    -------
    str
        Subgroup name (normalized to UPPERCASE), e.g. "ACTIVITY"

    Examples
    --------
    >>> _extract_subgroup_name("business.portfoliofunctions.activity.win_rate")
    'ACTIVITY'
    >>> _extract_subgroup_name("business.portfoliofunctions.win_rate")
    'OTHER'
    """
    parts = kpi_key.split(".")
    if len(parts) >= 3:
        # Normalize: replace hyphens with underscores, uppercase
        subgroup = parts[2].replace("-", "_").upper()
        return subgroup
    return "OTHER"


def _format_value_with_unit(
    value: float,
    unit: Optional[str],
    decimals: int = 2,
    currency: str = "EUR"
) -> str:
    """
    Format value with integrated unit (e.g., "0.75 %", "1000 EUR").

    Replaces any known currency code with the specified currency parameter.

    Parameters
    ----------
    value : float
        Numeric value
    unit : Optional[str]
        Unit string (e.g., "%", "USD", "-", "days")
    decimals : int, default 2
        Decimal places for formatting
    currency : str, default "EUR"
        Currency to use when replacing known currency codes

    Returns
    -------
    str
        Formatted string, e.g. "0.75 %" or "1000.00 EUR"

    Examples
    --------
    >>> _format_value_with_unit(0.75, "%", 2)
    '0.75 %'
    >>> _format_value_with_unit(1000.0, "USD", 2, "EUR")
    '1000.00 EUR'
    >>> _format_value_with_unit(1000.0, "GBP", 2, "EUR")
    '1000.00 EUR'
    >>> _format_value_with_unit(42.0, None, 2)
    '42'
    """
    if value == int(value):
        formatted = str(int(value))
    else:
        formatted = f"{value:.{decimals}f}"

    if unit:
        # Replace known currency codes with specified currency
        if unit in CURRENCY_CODES:
            unit = currency
        return f"{formatted} {unit}"
    return formatted


def _organize_kpis_by_package_subgroup(
    kpis_dict: Dict[str, Any]
) -> Dict[str, Dict[str, List[Tuple[str, Dict[str, Any]]]]]:
    """
    Organize KPIs by package, then subgroup.

    Parameters
    ----------
    kpis_dict : Dict[str, Any]
        Flat KPI dictionary: {"business.package.subgroup.metric": KPIValue}

    Returns
    -------
    Dict[str, Dict[str, List[Tuple[str, Dict[str, Any]]]]]
        Nested structure: {
            "portfoliofunctions": {
                "ACTIVITY": [("win_rate", kpi_value_dict), ...],
                "RETURNS": [("total_pnl", kpi_value_dict), ...],
            },
            "backtesterfunctions": {...}
        }
        Each tuple contains (metric_name, kpi_value_dict).

    Examples
    --------
    >>> kpis = {
    ...     "business.portfolio.activity.win_rate": {"value": 0.75, "unit": "%"},
    ...     "business.portfolio.returns.total_pnl": {"value": 1000.0, "unit": "USD"},
    ... }
    >>> grouped = _organize_kpis_by_package_subgroup(kpis)
    >>> grouped["portfolio"]["ACTIVITY"]
    [('win_rate', {'value': 0.75, 'unit': '%'})]
    >>> grouped["portfolio"]["RETURNS"]
    [('total_pnl', {'value': 1000.0, 'unit': 'USD'})]
    """
    grouped: Dict[str, Dict[str, List[Tuple[str, Dict[str, Any]]]]] = {}

    for kpi_key, kpi_value in kpis_dict.items():
        parts = kpi_key.split(".")

        if len(parts) < 3:
            # Skip invalid KPI keys
            continue

        package = parts[1]
        subgroup = _extract_subgroup_name(kpi_key)
        metric = _extract_metric_name(kpi_key)

        if package not in grouped:
            grouped[package] = {}

        if subgroup not in grouped[package]:
            grouped[package][subgroup] = []

        grouped[package][subgroup].append((metric, kpi_value))

    return grouped


def _build_table_rows_with_sections(
    grouped_subgroups: Dict[str, List[Tuple[str, Any]]],
    decimals: int = 2,
    currency: str = "EUR"
) -> List[List[str]]:
    """
    Build table rows with section headers and indentation.

    Parameters
    ----------
    grouped_subgroups : Dict[str, List[Tuple[str, Any]]]
        Subgroups and metrics: {"ACTIVITY": [("win_rate", kpi_dict), ...]}
    decimals : int, default 2
        Decimal places for value formatting
    currency : str, default "EUR"
        Currency to use when replacing known currency codes

    Returns
    -------
    List[List[str]]
        Table rows: [["KPI_NAME", "VALUE"], ...]
        - Section headers: ["ACTIVITY", ""]
        - Metrics: ["  win_rate", "0.75 %"] (2-space indented)
        - Separators: ["", ""] (empty rows between sections)

    Examples
    --------
    >>> grouped_subgroups = {
    ...     "ACTIVITY": [("win_rate", {"value": 0.75, "unit": "%"})],
    ...     "RETURNS": [("total_pnl", {"value": 1000.0, "unit": "USD"})]
    ... }
    >>> rows = _build_table_rows_with_sections(grouped_subgroups, decimals=2, currency="EUR")
    >>> rows
    [['ACTIVITY', ''], ['  win_rate', '0.75 %'], ['', ''], ['RETURNS', ''], ['  total_pnl', '1000.00 EUR']]
    """
    rows: List[List[str]] = []
    subgroup_names = sorted(grouped_subgroups.keys())

    for i, subgroup in enumerate(subgroup_names):
        # Add section header
        rows.append([subgroup, ""])

        # Add metrics
        for metric, kpi_value in grouped_subgroups[subgroup]:
            value_str = ""
            unit_str = ""

            # Extract value and unit from KPIValue dict
            if isinstance(kpi_value, dict):
                value_str = str(kpi_value.get("value", ""))
                unit_str = kpi_value.get("unit", "")
            else:
                value_str = str(kpi_value)

            # Format with unit
            try:
                value_float = float(value_str)
                formatted = _format_value_with_unit(value_float, unit_str, decimals, currency)
            except (ValueError, TypeError):
                formatted = str(kpi_value)

            # Add indented metric row
            rows.append([f"  {metric}", formatted])

        # Add separator row (except after last section)
        if i < len(subgroup_names) - 1:
            rows.append(["", ""])

    return rows


def _format_package_name(package: str) -> str:
    """
    Format package name for display (capitalize first letter).

    Parameters
    ----------
    package : str
        Package name, e.g. "portfoliofunctions"

    Returns
    -------
    str
        Formatted name, e.g. "Portfoliofunctions"

    Examples
    --------
    >>> _format_package_name("portfoliofunctions")
    'Portfoliofunctions'
    >>> _format_package_name("")
    ''
    """
    return package[0].upper() + package[1:] if package else ""


def _flatten_kpis(kpis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Flatten nested KPI dictionary to dot notation, preserving KPIValue dicts.

    Parameters
    ----------
    kpis : Dict[str, Any]
        Nested KPI dictionary

    Returns
    -------
    Dict[str, Any]
        Flattened dictionary with dot notation keys

    Examples
    --------
    >>> nested = {"business": {"portfolio": {"win_rate": {"value": 0.75, "unit": "%"}}}}
    >>> _flatten_kpis(nested)
    {'business.portfolio.win_rate': {'value': 0.75, 'unit': '%'}}
    """
    return _flatten_with_kpi_value(kpis)


def _apply_filters(
    kpis: Dict[str, Any],
    filter_patterns: Optional[List[str]]
) -> Dict[str, Any]:
    """
    Apply wildcard filter patterns to KPI keys.

    Parameters
    ----------
    kpis : Dict[str, Any]
        Flattened KPI dictionary
    filter_patterns : Optional[List[str]]
        Wildcard patterns (e.g., ["business.portfolio.*"])

    Returns
    -------
    Dict[str, Any]
        Filtered KPI dictionary

    Examples
    --------
    >>> kpis = {"business.portfolio.win_rate": {"value": 0.75, "unit": "%"}}
    >>> _apply_filters(kpis, ["business.portfolio.*"])
    {'business.portfolio.win_rate': {'value': 0.75, 'unit': '%'}}
    """
    if not filter_patterns:
        return kpis

    return {
        k: v for k, v in kpis.items()
        if any(fnmatch.fnmatch(k, p) for p in filter_patterns)
    }


def print_kpi_table(
    kpis: Dict[str, Any],
    filter_patterns: Optional[List[str]] = None,
    decimals: int = 2,
    sort_keys: bool = True,
    table_format: str = "fancy_grid",
    currency: str = "EUR"
) -> None:
    """
    Print KPIs as formatted table with subgroup sections (2-level grouping).

    Groups by package only. Subgroups shown as UPPERCASE section headers
    within table with 2-space indented items. Units integrated into Value column.
    One professional table per package. All currency codes are replaced with
    the specified currency.

    Parameters
    ----------
    kpis : Dict[str, Any]
        KPI dictionary: {"business.package.subgroup.metric": {"value": X, "unit": "Y"}}
    filter_patterns : Optional[List[str]], default None
        Wildcard patterns for filtering (e.g., ["business.portfolio.*"])
    decimals : int, default 2
        Decimal places for numeric values
    sort_keys : bool, default True
        Sort packages and subgroups alphabetically
    table_format : str, default "fancy_grid"
        Tabulate format (fancy_grid, heavy_grid, grid, etc.)
    currency : str, default "EUR"
        Currency to use for display. Replaces all known currency codes
        (USD, GBP, CHF, etc.) with this value.

    Returns
    -------
    None
        Prints to console

    Examples
    --------
    >>> kpis = {
    ...     "business": {
    ...         "portfolio": {
    ...             "activity": {"win_rate": {"value": 0.75, "unit": "%"}},
    ...             "returns": {"total_pnl": {"value": 1000.0, "unit": "USD"}}
    ...         }
    ...     }
    ... }
    >>> print_kpi_table(kpis)

    Portfoliofunctions KPIs - 2 Metrics
    ╒═══════════════════════════╤═══════════════════╕
    │ KPI                       │            Value  │
    ╞═══════════════════════════╪═══════════════════╡
    │ ACTIVITY                  │                   │
    │   win_rate                │          0.75 %   │
    │                           │                   │
    │ RETURNS                   │                   │
    │   total_pnl               │       1000.00 USD │
    ╘═══════════════════════════╧═══════════════════╛
    """
    # Validate input
    if not kpis:
        print("No KPIs to display")
        return

    # Flatten and filter
    flat_kpis = _flatten_kpis(dict(kpis))
    if not flat_kpis:
        print("No KPIs found after flattening")
        return

    filtered_kpis = _apply_filters(flat_kpis, filter_patterns)
    if not filtered_kpis:
        print("No KPIs match filter patterns")
        return

    # Group by package and subgroup
    grouped_by_pkg = _organize_kpis_by_package_subgroup(filtered_kpis)
    if not grouped_by_pkg:
        print("No valid KPIs after grouping")
        return

    # Sort if requested
    if sort_keys:
        grouped_by_pkg = {
            k: {sk: grouped_by_pkg[k][sk] for sk in sorted(grouped_by_pkg[k].keys())}
            for k in sorted(grouped_by_pkg.keys())
        }

    # Print one table per package
    for package, subgroups in grouped_by_pkg.items():
        total_metrics = sum(len(items) for items in subgroups.values())
        pkg_name = _format_package_name(package)
        header = f"{pkg_name} KPIs - {total_metrics} Metrics"

        # Build rows with section headers and indentation
        rows = _build_table_rows_with_sections(subgroups, decimals, currency)

        # Print header
        print(f"\n{header}")

        # Print table with fancy_grid format
        table_output = tabulate(
            rows,
            headers=["KPI", "Value"],
            tablefmt=table_format,
            numalign="right",
            maxcolwidths=[60, None]
        )
        print(table_output)
