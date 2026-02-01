"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Complete table rendering solution - replaces tabulate dependency with custom
 implementation. Supports column-level formatting (alignment, width, decimals,
 units), multiple themes, and backward compatibility via tabulate_compat().
 Multi-table width synchronization via return_widths/enforce_widths.
 Log:
 v1.4.0 : Add row_separators parameter to control separator lines between data rows
 v1.3.0 : Add return_widths and enforce_widths for multi-table synchronization
 v1.2.0 : Add get_default_theme() for render_table() theme resolution
 v1.1.0 : Implement alignment handling (right/center/decimal)
 v1.0.0 : Initial implementation
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
# Standard Library
import re
from typing import Any, Dict, List, Optional, Tuple

# Project modules
from basefunctions.config.config_handler import ConfigHandler


# =============================================================================
# CONSTANTS
# =============================================================================
THEMES: Dict[str, Dict[str, Any]] = {
    "grid": {
        "top": ("┌", "─", "┬", "┐"),
        "header_sep": ("├", "─", "┼", "┤"),
        "row_sep": None,
        "bottom": ("└", "─", "┴", "┘"),
        "vertical": "│",
        "padding": 1,
    },
    "fancy_grid": {
        "top": ("╒", "═", "╤", "╕"),
        "header_sep": ("╞", "═", "╪", "╡"),
        "row_sep": ("├", "─", "┼", "┤"),
        "bottom": ("╘", "═", "╧", "╛"),
        "vertical": "│",
        "padding": 1,
    },
    "minimal": {
        "top": None,
        "header_sep": ("", "─", " ", ""),
        "row_sep": None,
        "bottom": None,
        "vertical": " ",
        "padding": 2,
    },
    "psql": {
        "top": None,
        "header_sep": ("|", "-", "+", "|"),
        "row_sep": None,
        "bottom": None,
        "vertical": "|",
        "padding": 1,
    },
}


# =============================================================================
# FUNCTION DEFINITIONS
# =============================================================================
def get_default_theme() -> str:
    """
    Get default table theme from configuration.

    Used by render_table() when theme parameter is None.
    Reads from ConfigHandler key "basefunctions/table_format" with fallback "grid".

    Returns
    -------
    str
        Default theme name (e.g., "grid", "fancy_grid", "minimal", "psql").

    Examples
    --------
    >>> theme = get_default_theme()
    >>> theme in ["grid", "fancy_grid", "minimal", "psql"]
    True
    """
    config_handler = ConfigHandler()
    return config_handler.get_config_parameter(
        "basefunctions/table_format",
        default_value="grid"
    )


def get_table_format() -> str:
    """
    Get configured table format from configuration.

    Reads from ConfigHandler key "basefunctions/table_format" with fallback "grid".

    Returns
    -------
    str
        Table format name (e.g., "grid", "fancy_grid", "minimal", "psql").

    Examples
    --------
    >>> fmt = get_table_format()
    >>> fmt in ["grid", "fancy_grid", "minimal", "psql"]
    True
    """
    config_handler = ConfigHandler()
    return config_handler.get_config_parameter(
        "basefunctions/table_format",
        default_value="grid"
    )


def render_table(
    data: List[List[Any]],
    headers: Optional[List[str]] = None,
    column_specs: Optional[List[str]] = None,
    theme: Optional[str] = None,
    max_width: Optional[int] = None,
    return_widths: bool = False,
    enforce_widths: Optional[Dict[str, Any]] = None,
    row_separators: bool = True
) -> Any:
    """
    Render table with flexible column formatting and theme support.

    Converts data to formatted string with optional headers, column-level
    formatting (alignment, width, decimals, units), and theme styling.

    Parameters
    ----------
    data : List[List[Any]]
        Table data as list of rows (each row is list of cell values).
    headers : List[str], optional
        Column headers. If None, table renders without header row.
    column_specs : List[str], optional
        Column format specifications as strings. Format: "alignment:width[:decimals[:unit]]"
        - alignment: "left", "right", "center", "decimal"
        - width: integer column width in characters
        - decimals: number of decimal places (numeric values only)
        - unit: suffix to append (e.g., "%", "ms")
        Example: ["left:15", "decimal:10:2:%", "right:8"]
    theme : str, optional
        Table theme name. If None, reads from config via get_default_theme().
        Valid values: "grid", "fancy_grid", "minimal", "psql"
    max_width : int, optional
        Maximum table width. If specified, columns are resized to fit within
        this width constraint. Width is distributed evenly across columns.
    return_widths : bool, default False
        If True, returns tuple (table_str, widths_dict) instead of just table_str.
        widths_dict contains 'column_widths' (list) and 'total_width' (int).
    enforce_widths : Dict[str, Any], optional
        Force specific column widths instead of auto-calculating. Dict must contain
        'column_widths' key with list of integers. Used for multi-table synchronization.
        Example: {'column_widths': [12, 8], 'total_width': 25}
    row_separators : bool, default True
        If True, render separator lines between data rows (current behavior).
        If False, only render header separator and outer borders, no separators between data rows.

    Returns
    -------
    str or Tuple[str, Dict[str, Any]]
        If return_widths=False: Formatted table as multi-line string.
        If return_widths=True: Tuple of (table_str, widths_dict) where widths_dict
        contains 'column_widths' (List[int]) and 'total_width' (int).

    Raises
    ------
    ValueError
        If theme not found in THEMES or invalid column_specs format.

    Examples
    --------
    >>> data = [["Alice", 24], ["Bob", 19]]
    >>> print(render_table(data, headers=["Name", "Age"]))
    ┌──────┬─────┐
    │ Name │ Age │
    ├──────┼─────┤
    │ Alice│  24 │
    │ Bob  │  19 │
    └──────┴─────┘

    >>> specs = ["left:10", "decimal:8:2"]
    >>> print(render_table(data, headers=["Name", "Score"], column_specs=specs))
    ┌────────────┬──────────┐
    │ Name       │    Score │
    ├────────────┼──────────┤
    │ Alice      │    24.00 │
    │ Bob        │    19.00 │
    └────────────┴──────────┘
    """
    # Handle empty data
    if not data:
        return ""

    if theme is None:
        theme = get_default_theme()

    if theme not in THEMES:
        valid = ", ".join(THEMES.keys())
        raise ValueError(f"Invalid theme '{theme}'. Valid themes: {valid}")

    # Parse column specifications
    parsed_specs = None
    if column_specs:
        parsed_specs = []
        for spec in column_specs:
            # Allow None for auto-width columns
            if spec is None:
                parsed_specs.append(None)
            else:
                parsed_specs.append(_parse_column_spec(spec))

    # Format cells
    formatted_data = []
    for row in data:
        formatted_row = []
        for cell_idx, cell in enumerate(row):
            spec = None
            if parsed_specs is not None and cell_idx < len(parsed_specs):
                spec = parsed_specs[cell_idx]
            formatted_row.append(_format_cell(cell, spec))
        formatted_data.append(formatted_row)

    # Calculate column widths
    if return_widths:
        column_widths, total_width = _calculate_column_widths(
            formatted_data,
            headers,
            parsed_specs,
            max_width,
            return_total=True,
            enforce_widths=enforce_widths
        )
    else:
        column_widths = _calculate_column_widths(
            formatted_data,
            headers,
            parsed_specs,
            max_width,
            enforce_widths=enforce_widths
        )

    # Render with theme
    table_str = _render_with_theme(
        formatted_data,
        headers,
        column_widths,
        theme,
        parsed_specs,
        row_separators
    )

    if return_widths:
        widths_dict = {
            "column_widths": column_widths,
            "total_width": total_width
        }
        return table_str, widths_dict

    return table_str


def render_dataframe(
    df: Any,
    column_specs: Optional[List[str]] = None,
    theme: Optional[str] = None,
    max_width: Optional[int] = None,
    showindex: bool = False
) -> str:
    """
    Render pandas DataFrame as formatted table.

    Extracts data and headers from DataFrame and renders using render_table().

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame to render.
    column_specs : List[str], optional
        Column format specifications (see render_table() for format).
    theme : str, optional
        Table theme name (see render_table() for valid values).
    max_width : int, optional
        Maximum table width (reserved for future).
    showindex : bool, default False
        If True, include DataFrame index as first column.

    Returns
    -------
    str
        Formatted table as multi-line string.

    Examples
    --------
    >>> import pandas as pd
    >>> df = pd.DataFrame({"Name": ["Alice", "Bob"], "Age": [24, 19]})
    >>> print(render_dataframe(df))
    """
    headers = []
    if showindex:
        headers.append(df.index.name or "index")

    headers.extend(df.columns.tolist())

    data = []
    if showindex:
        for idx, row in df.iterrows():
            data.append([idx] + row.tolist())
    else:
        data = df.values.tolist()

    return render_table(
        data,
        headers=headers,
        column_specs=column_specs,
        theme=theme,
        max_width=max_width
    )


def tabulate_compat(
    data: Any,
    headers: Optional[List[str]] = None,
    tablefmt: Optional[str] = None,
    colalign: Optional[Tuple[str, ...]] = None,
    disable_numparse: bool = False,
    showindex: bool = False
) -> str:
    """
    Backward compatibility wrapper for tabulate() function.

    Accepts standard tabulate() arguments and maps to render_table() or
    render_dataframe() depending on input type.

    Parameters
    ----------
    data : Any
        Table data as list of rows or pandas DataFrame.
    headers : List[str], optional
        Column headers.
    tablefmt : str, optional
        Table format/theme. Defaults to configured format via get_default_theme().
    colalign : Tuple[str, ...], optional
        Column alignments as tuple of alignment strings.
        Example: ("left", "right", "center")
    disable_numparse : bool, default False
        If True, skip numeric formatting (treat all values as strings).
        Disables decimal place formatting and numeric-specific alignment.
    showindex : bool, default False
        If True and data is DataFrame, include index as first column.

    Returns
    -------
    str
        Formatted table as multi-line string.

    Raises
    ------
    ValueError
        If invalid theme specified.

    Examples
    --------
    >>> data = [["Alice", 24], ["Bob", 19]]
    >>> print(tabulate_compat(data, headers=["Name", "Age"], tablefmt="grid"))
    """
    # Detect DataFrame
    if hasattr(data, "values") and hasattr(data, "columns"):
        return render_dataframe(
            data,
            column_specs=None,
            theme=tablefmt,
            showindex=showindex
        )

    # Convert colalign to column_specs format
    column_specs = None
    if colalign:
        column_specs = [align for align in colalign]

    # Remove decimals from specs if disable_numparse is True
    if disable_numparse and column_specs:
        # Parse specs and strip decimals
        parsed = []
        for spec_str in column_specs:
            parts = spec_str.split(":")
            # Keep only alignment and width (first 2 parts)
            new_spec = ":".join(parts[:2]) if len(parts) >= 2 else parts[0]
            parsed.append(new_spec)
        column_specs = parsed

    if tablefmt is None:
        tablefmt = get_default_theme()

    return render_table(
        data,
        headers=headers,
        column_specs=column_specs,
        theme=tablefmt
    )


def _parse_column_spec(spec: str) -> Dict[str, Any]:
    """
    Parse column specification string into format dictionary.

    Parses "alignment:width[:decimals[:unit]]" into component parts.

    Parameters
    ----------
    spec : str
        Specification string. Format: "alignment:width[:decimals[:unit]]"

    Returns
    -------
    Dict[str, Any]
        Dictionary with keys: "align", "width", "decimals", "unit"
        - align: str or None
        - width: int or None
        - decimals: int or None
        - unit: str or None

    Raises
    ------
    ValueError
        If alignment is invalid or width cannot be converted to int.

    Examples
    --------
    >>> spec = _parse_column_spec("left:15")
    >>> spec["align"]
    'left'
    >>> spec["width"]
    15

    >>> spec = _parse_column_spec("decimal:10:2:%")
    >>> spec["decimals"]
    2
    >>> spec["unit"]
    '%'
    """
    parts = spec.split(":")
    valid_aligns = {"left", "right", "center", "decimal"}

    result: Dict[str, Any] = {
        "align": None,
        "width": None,
        "decimals": None,
        "unit": None
    }

    if len(parts) >= 1 and parts[0]:
        alignment = parts[0].strip()
        if alignment not in valid_aligns:
            raise ValueError(
                f"Invalid alignment '{alignment}'. "
                f"Valid: {', '.join(sorted(valid_aligns))}"
            )
        result["align"] = alignment

    if len(parts) >= 2 and parts[1]:
        try:
            result["width"] = int(parts[1].strip())
        except ValueError as e:
            raise ValueError(f"Width must be integer: {parts[1]}") from e

    if len(parts) >= 3 and parts[2]:
        try:
            result["decimals"] = int(parts[2].strip())
        except ValueError as e:
            raise ValueError(f"Decimals must be integer: {parts[2]}") from e

    if len(parts) >= 4 and parts[3]:
        result["unit"] = parts[3].strip()

    return result


def _format_cell(value: Any, spec: Optional[Dict[str, Any]]) -> str:
    """
    Format single table cell according to specification.

    Converts value to string and applies numeric formatting (decimals).
    Alignment is handled by _render_row(). Preserves ANSI escape codes.

    Parameters
    ----------
    value : Any
        Cell value to format (any type).
    spec : Dict[str, Any], optional
        Format specification from _parse_column_spec(). If None, simple str().

    Returns
    -------
    str
        Formatted cell string.

    Examples
    --------
    >>> spec = {"align": "right", "width": 8, "decimals": 2, "unit": "%"}
    >>> result = _format_cell(42.5, spec)
    >>> "42.50%" in result
    True
    """
    if spec is None:
        return str(value)

    # Convert to string
    str_value = str(value)

    # Apply numeric formatting if decimals specified and value numeric
    if spec.get("decimals") is not None:
        try:
            numeric = float(value)
            decimals = spec["decimals"]
            str_value = f"{numeric:.{decimals}f}"
        except (ValueError, TypeError):
            pass

    # Append unit if specified
    if spec.get("unit"):
        str_value = f"{str_value}{spec['unit']}"

    return str_value


def _calculate_column_widths(
    data: List[List[str]],
    headers: Optional[List[str]],
    specs: Optional[List[Dict[str, Any]]],
    max_width: Optional[int] = None,
    return_total: bool = False,
    enforce_widths: Optional[Dict[str, Any]] = None
) -> Any:
    """
    Calculate optimal column widths from data and specifications.

    Determines width for each column as maximum of data widths, header widths,
    and specified widths. Accounts for ANSI escape codes in width calculation.
    If max_width constraint is provided, distributes available width evenly.
    If enforce_widths provided, uses those widths directly instead of calculating.

    Parameters
    ----------
    data : List[List[str]]
        Formatted table data.
    headers : List[str], optional
        Column headers.
    specs : List[Dict], optional
        Column specifications with width hints.
    max_width : int, optional
        Maximum table width constraint. If specified, columns are resized
        to fit within this constraint with width distributed evenly.
    return_total : bool, default False
        If True, return tuple (widths, total_width). If False, return widths only.
    enforce_widths : Dict[str, Any], optional
        Force specific column widths. Must contain 'column_widths' key with list.
        If provided, auto-calculation is skipped and these widths are used directly.

    Returns
    -------
    List[int] or Tuple[List[int], int]
        If return_total=False: Column widths in characters (excluding ANSI codes).
        If return_total=True: Tuple of (column_widths, total_width).
    """
    if not data and not headers:
        return []

    # If enforce_widths provided, use those directly
    if enforce_widths is not None:
        if "column_widths" not in enforce_widths:
            raise ValueError("enforce_widths must contain 'column_widths' key")

        widths = enforce_widths["column_widths"]
        num_cols = len(widths)

        if return_total:
            if "total_width" in enforce_widths:
                return widths, enforce_widths["total_width"]

            # Calculate total_width if not provided
            padding = 1
            total = sum(widths) + (num_cols * 2 * padding) + (num_cols + 1)
            return widths, total
        return widths

    # Determine number of columns
    num_cols = len(data[0]) if data else (len(headers) if headers else 0)

    widths = [0] * num_cols

    # Check header widths
    if headers:
        for col_idx, header in enumerate(headers):
            widths[col_idx] = max(widths[col_idx], _visible_width(header))

    # Check data widths
    for row in data:
        for col_idx, cell in enumerate(row):
            if col_idx < len(widths):
                widths[col_idx] = max(widths[col_idx], _visible_width(cell))

    # Apply specified widths
    if specs:
        for col_idx, spec in enumerate(specs):
            if col_idx < len(widths) and spec and spec.get("width"):
                widths[col_idx] = max(widths[col_idx], spec["width"])

    # Apply max_width constraint if specified
    if max_width is not None and num_cols > 0:
        total_width = sum(widths)
        if total_width > max_width:
            # Distribute available width evenly across columns
            width_per_col = max_width // num_cols
            widths = [width_per_col] * num_cols

    if return_total:
        # Calculate total width: sum of column widths + borders + padding
        # Format: |<pad>col1<pad>|<pad>col2<pad>|...
        # = (num_cols + 1) * "|" + num_cols * 2 * padding + sum(widths)
        # Simplified: Get total from theme - for now use default padding=1
        padding = 1  # Default from most themes
        total = sum(widths) + (num_cols * 2 * padding) + (num_cols + 1)
        return widths, total

    return widths


def _visible_width(text: str) -> int:
    """
    Calculate visible width of text, excluding ANSI escape codes.

    ANSI escape sequences (color codes, formatting) are not counted
    in the visible width calculation. Emojis are counted as 2 characters.

    Parameters
    ----------
    text : str
        Text string potentially containing ANSI codes.

    Returns
    -------
    int
        Visible character width.

    Examples
    --------
    >>> _visible_width("\\033[31mRed\\033[0m")
    3
    >>> _visible_width("✅ Current")
    11
    """
    # Strip ANSI escape sequences: \033[...m or \x1b[...m
    ansi_pattern = r"\x1b\[[0-9;]*m|\033\[[0-9;]*m"
    clean_text = re.sub(ansi_pattern, "", text)

    # Count emojis as 2 characters (specific status emojis)
    width = 0
    emoji_chars = {"✅", "❌", "🟠", "📦"}

    for char in clean_text:
        if char in emoji_chars:
            width += 2  # Emojis take 2 display columns
        else:
            width += 1

    return width


def _render_with_theme(
    rows: List[List[str]],
    headers: Optional[List[str]],
    widths: List[int],
    theme_name: str,
    specs: Optional[List[Dict[str, Any]]] = None,
    row_separators: bool = True
) -> str:
    """
    Render table rows and headers with theme borders and separators.

    Builds complete table string with theme styling applied.

    Parameters
    ----------
    rows : List[List[str]]
        Formatted data rows.
    headers : List[str], optional
        Header row (if any).
    widths : List[int]
        Column widths.
    theme_name : str
        Theme name (must exist in THEMES).
    specs : List[Dict[str, Any]], optional
        Column specifications with alignment info.
    row_separators : bool, default True
        If True, render separator lines between data rows.
        If False, only render header separator and outer borders.

    Returns
    -------
    str
        Complete formatted table as multi-line string.
    """
    theme = THEMES[theme_name]
    lines: List[str] = []

    vertical = theme["vertical"]
    padding = theme["padding"]

    # Top border
    if theme["top"]:
        lines.append(_render_border(widths, theme["top"], padding))

    # Headers
    if headers:
        lines.append(_render_row(headers, widths, vertical, padding, specs))
        if theme["header_sep"]:
            lines.append(_render_border(widths, theme["header_sep"], padding))

    # Data rows
    for row_idx, row in enumerate(rows):
        lines.append(_render_row(row, widths, vertical, padding, specs))
        if (
            row_separators
            and theme["row_sep"]
            and row_idx < len(rows) - 1
        ):
            lines.append(_render_border(widths, theme["row_sep"], padding))

    # Bottom border
    if theme["bottom"]:
        lines.append(_render_border(widths, theme["bottom"], padding))

    return "\n".join(lines)


def _render_row(
    cells: List[str],
    widths: List[int],
    vertical_char: str,
    padding: int,
    specs: Optional[List[Dict[str, Any]]] = None
) -> str:
    """
    Render single table row with theme formatting and alignment.

    Pads cells to column widths based on alignment specifications,
    applies theme vertical separator and padding. Supports ANSI codes.

    Parameters
    ----------
    cells : List[str]
        Formatted cell values.
    widths : List[int]
        Column widths.
    vertical_char : str
        Theme vertical separator character.
    padding : int
        Number of spaces around cell content.
    specs : List[Dict[str, Any]], optional
        Column specifications with alignment info. If None, defaults to left.

    Returns
    -------
    str
        Formatted row string.
    """
    padded_cells = []
    for cell_idx, cell in enumerate(cells):
        width = widths[cell_idx] if cell_idx < len(widths) else 0
        visible = _visible_width(cell)
        ansi_length = len(cell) - visible
        target_len = width + ansi_length

        if len(cell) >= target_len:
            padded = cell
        else:
            # Get alignment from specs
            align = "left"  # Default
            if specs and cell_idx < len(specs) and specs[cell_idx]:
                spec_align = specs[cell_idx].get("align")
                if spec_align in {"left", "right", "center", "decimal"}:
                    align = spec_align

            # Apply alignment-based padding
            spaces_needed = target_len - len(cell)

            if align == "right" or align == "decimal":
                # Spaces on LEFT
                padded = " " * spaces_needed + cell
            elif align == "center":
                # Spaces on BOTH sides
                left_spaces = spaces_needed // 2
                right_spaces = spaces_needed - left_spaces
                padded = " " * left_spaces + cell + " " * right_spaces
            else:
                # left or None: Spaces on RIGHT (default)
                padded = cell + " " * spaces_needed

        padded_cells.append(padded)

    pad_str = " " * padding
    row_str = vertical_char + pad_str + (pad_str + vertical_char + pad_str).join(padded_cells) + pad_str + vertical_char

    return row_str


def _render_border(
    widths: List[int],
    border_chars: Tuple[str, str, str, str],
    padding: int
) -> str:
    """
    Render border or separator line for table.

    Parameters
    ----------
    widths : List[int]
        Column widths.
    border_chars : Tuple[str, str, str, str]
        (left, horizontal, junction, right) characters for border.
    padding : int
        Number of padding spaces per column.

    Returns
    -------
    str
        Border line string.

    Examples
    --------
    >>> border_chars = ("┌", "─", "┬", "┐")
    >>> _render_border([5, 8], border_chars, 1)
    '┌───────┬──────────┐'
    """
    left, horizontal, junction, right = border_chars

    # Calculate total width including padding
    segments = []
    for width in widths:
        total = width + (padding * 2)
        segments.append(horizontal * total)

    line = left + junction.join(segments) + right

    return line
