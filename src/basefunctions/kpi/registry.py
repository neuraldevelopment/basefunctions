"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Central registry for KPI provider discovery - module-level dict
 Log:
 v1.0 : Initial implementation
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
# Standard Library
from typing import Dict

# Project modules
from basefunctions.kpi.protocol import KPIProvider


# =============================================================================
# MODULE-LEVEL REGISTRY
# =============================================================================
_PROVIDERS: Dict[str, KPIProvider] = {}


# =============================================================================
# FUNCTION DEFINITIONS
# =============================================================================
def register(name: str, provider: KPIProvider) -> None:
    """
    Register KPI provider under name.

    Parameters
    ----------
    name : str
        Unique name to register provider under
    provider : KPIProvider
        Provider instance implementing KPIProvider protocol

    Raises
    ------
    ValueError
        If name already registered
    """
    if name in _PROVIDERS:
        raise ValueError(f"KPI provider '{name}' bereits registriert")
    _PROVIDERS[name] = provider


def get_all_providers() -> Dict[str, KPIProvider]:
    """
    Get all registered providers.

    Returns
    -------
    Dict[str, KPIProvider]
        Dictionary mapping provider names to provider instances
    """
    return _PROVIDERS.copy()


def clear() -> None:
    """
    Clear registry (for testing).

    Removes all registered providers from the registry.
    """
    _PROVIDERS.clear()
