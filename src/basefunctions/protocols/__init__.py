"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Protocol definitions for structural typing contracts. Enables duck-typing
 with full IDE and type-checker support for framework integrations.
 Log:
 v1.0.0 : Initial implementation
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
from basefunctions.protocols.kpi_provider import KPIProvider
from basefunctions.protocols.metrics_source import MetricsSource

# =============================================================================
# EXPORTS
# =============================================================================
__all__ = [
    "KPIProvider",
    "MetricsSource",
]
