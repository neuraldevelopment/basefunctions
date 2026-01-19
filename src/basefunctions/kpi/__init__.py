"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 KPI subpackage - Protocol-based KPI collection and export
 Log:
 v1.2 : Add print_kpi_table to exports
 v1.1 : Add KPIValue to exports
 v1.0 : Initial implementation
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
from basefunctions.kpi.collector import KPICollector
from basefunctions.kpi.exporters import (
    export_business_technical_split,
    export_by_category,
    export_to_dataframe,
    print_kpi_table,
)
from basefunctions.kpi.registry import clear, get_all_providers, register
from basefunctions.kpi.utils import KPIValue, group_kpis_by_name
# Re-export KPIProvider from centralized protocols module for backward compatibility
from basefunctions.protocols import KPIProvider

# =============================================================================
# PUBLIC API
# =============================================================================
__all__ = [
    "KPIProvider",
    "KPICollector",
    "KPIValue",
    "export_to_dataframe",
    "export_by_category",
    "export_business_technical_split",
    "print_kpi_table",
    "register",
    "get_all_providers",
    "clear",
    "group_kpis_by_name",
]
