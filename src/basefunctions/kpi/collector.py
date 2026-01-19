"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 KPI collector for recursive collection and history management
 Log:
 v1.2 : Improve _filter_by_prefix docstring with examples and clarify logic
 v1.1 : Add category filtering (business/technical prefix)
 v1.0 : Initial implementation
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
# Standard Library
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Tuple

# Project modules
from basefunctions.protocols import KPIProvider


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

    def collect_by_category(
        self, provider: KPIProvider, category: Literal["business", "technical"]
    ) -> Dict[str, Any]:
        """
        Recursively collect KPIs filtered by category prefix.

        Only KPIs with keys starting with "business." or "technical." prefix
        are included. Filters recursively through all nested subproviders.

        Parameters
        ----------
        provider : KPIProvider
            Root provider to collect KPIs from
        category : Literal["business", "technical"]
            Category prefix to filter KPIs by

        Returns
        -------
        Dict[str, Any]
            Filtered nested dictionary containing only KPIs matching the
            category prefix. Structure mirrors collect() output but filtered.

        Examples
        --------
        >>> collector = KPICollector()
        >>> # Provider has: {"business.revenue": 1000, "technical.uptime": 99.9}
        >>> collector.collect_by_category(provider, "business")
        {"business.revenue": 1000}
        >>> collector.collect_by_category(provider, "technical")
        {"technical.uptime": 99.9}
        """
        # Collect all KPIs first
        all_kpis = self.collect(provider)

        # Filter by category prefix
        prefix = f"{category}."
        return self._filter_by_prefix(all_kpis, prefix)

    def _filter_by_prefix(self, data: Dict[str, Any], prefix: str) -> Dict[str, Any]:
        """
        Recursively filter dictionary by key prefix.

        Filters through entire hierarchy including nested dictionaries.
        Only includes keys matching the prefix and nested dicts containing
        matching keys.

        Parameters
        ----------
        data : Dict[str, Any]
            Dictionary to filter (can contain nested dictionaries)
        prefix : str
            Prefix to match keys against (e.g., "business.", "technical.")

        Returns
        -------
        Dict[str, Any]
            Filtered dictionary containing only matching keys and nested
            structures with matching keys

        Examples
        --------
        >>> data = {
        ...     "business.balance": 1000.0,
        ...     "technical.cpu": 50.0,
        ...     "portfolio": {
        ...         "business.profit": 100.0,
        ...         "technical.latency": 45.0
        ...     }
        ... }
        >>> collector._filter_by_prefix(data, "business.")
        {
            "business.balance": 1000.0,
            "portfolio": {"business.profit": 100.0}
        }
        """
        result: Dict[str, Any] = {}

        for key, value in data.items():
            # Direct match: key has the prefix
            if key.startswith(prefix):
                result[key] = value
            # Nested dict: recurse to find matches inside
            # Note: We use 'elif' here because if key matches prefix,
            # we include the entire value (even if it's a dict)
            elif isinstance(value, dict):
                filtered_nested = self._filter_by_prefix(value, prefix)
                if filtered_nested:  # Only include if nested dict has matches
                    result[key] = filtered_nested

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
