"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Central table format configuration for consistent formatting across package
 Log:
 v1.0 : Initial implementation
=============================================================================
"""

# =============================================================================
# FUNCTION DEFINITIONS
# =============================================================================
def get_table_format() -> str:
    """
    Get configured table format for tabulate library.

    Reads table format from configuration file under key
    "basefunctions/table_format" with fallback default "grid".

    Returns
    -------
    str
        Table format string (e.g., "grid", "simple", "plain")
        Valid formats defined by tabulate library.

    Examples
    --------
    >>> fmt = get_table_format()
    >>> fmt
    'grid'

    >>> # Use in tabulate call
    >>> from tabulate import tabulate
    >>> data = [["Alice", 24], ["Bob", 19]]
    >>> print(tabulate(data, headers=["Name", "Age"], tablefmt=get_table_format()))
    """
    # Lazy import to avoid circular dependency
    from basefunctions.config.config_handler import ConfigHandler

    config_handler = ConfigHandler()
    return config_handler.get_config_parameter(
        "basefunctions/table_format",
        default_value="grid"
    )
