"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Protocol definition for KPI providers enabling recursive collection
 Log:
 v1.0.0 : Initial implementation
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
# Standard Library
from typing import Dict, Optional, Protocol


# =============================================================================
# PROTOCOL DEFINITIONS
# =============================================================================
class KPIProvider(Protocol):
    """
    Protocol for objects that provide Key Performance Indicators.

    Any class implementing this protocol can be used with KPICollector
    to recursively collect metrics from hierarchical structures.
    """

    def get_kpis(self) -> Dict[str, float]:
        """
        Return current KPI values for this provider.

        Returns
        -------
        Dict[str, float]
            Dictionary mapping KPI names to their current numeric values.
            Example: {"balance": 1000.0, "profit": 50.0}
        """
        ...

    def get_subproviders(self) -> Optional[Dict[str, "KPIProvider"]]:
        """
        Return nested KPI providers for hierarchical collection.

        Returns
        -------
        Optional[Dict[str, KPIProvider]]
            Dictionary mapping subprovider names to KPIProvider instances,
            or None if this provider has no subproviders.
            Example: {"portfolio": PortfolioKPIs(), "risk": RiskKPIs()}
        """
        ...
