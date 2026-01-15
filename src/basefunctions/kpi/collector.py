"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 KPI collector for recursive collection and history management
 Log:
 v1.0 : Initial implementation
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
# Standard Library
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

# Project modules
from basefunctions.kpi.protocol import KPIProvider


# =============================================================================
# CLASS DEFINITIONS
# =============================================================================
class KPICollector:
    """
    Collector for recursive KPI gathering with history tracking.

    Supports hierarchical KPI structures through recursive collection
    from providers and their subproviders.
    """

    def __init__(self) -> None:
        """
        Initialize empty KPI collector.

        The collector starts with an empty history list.
        """
        self._history: List[Tuple[datetime, Dict[str, Any]]] = []

    def collect(self, provider: KPIProvider) -> Dict[str, Any]:
        """
        Recursively collect KPIs from provider and all subproviders.

        Parameters
        ----------
        provider : KPIProvider
            Root provider to collect KPIs from

        Returns
        -------
        Dict[str, Any]
            Nested dictionary with KPI values. Direct KPIs at root level,
            subprovider KPIs in nested dictionaries.
            Example: {"balance": 100.0, "portfolio": {"balance": 50.0}}
        """
        result: Dict[str, Any] = dict(provider.get_kpis())

        subproviders = provider.get_subproviders()
        if subproviders:
            for name, subprovider in subproviders.items():
                result[name] = self.collect(subprovider)

        return result

    def collect_and_store(self, provider: KPIProvider) -> Dict[str, Any]:
        """
        Collect KPIs and add to history with timestamp.

        Parameters
        ----------
        provider : KPIProvider
            Root provider to collect KPIs from

        Returns
        -------
        Dict[str, Any]
            The collected KPI dictionary (same as collect() output)
        """
        kpis = self.collect(provider)
        self._history.append((datetime.now(), kpis))
        return kpis

    def get_history(
        self, since: Optional[datetime] = None
    ) -> List[Tuple[datetime, Dict[str, Any]]]:
        """
        Get KPI history, optionally filtered by time.

        Parameters
        ----------
        since : Optional[datetime], default None
            If provided, only return entries with timestamp >= since.
            If None, return complete history.

        Returns
        -------
        List[Tuple[datetime, Dict[str, Any]]]
            List of (timestamp, kpis) tuples, chronologically ordered
        """
        if since is None:
            return list(self._history)

        return [(ts, kpis) for ts, kpis in self._history if ts >= since]

    def clear_history(self) -> None:
        """
        Clear all stored KPI history.

        After calling this method, the history list will be empty.
        """
        self._history.clear()
