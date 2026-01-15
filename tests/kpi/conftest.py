"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Shared test fixtures for KPI tests
 Log:
 v1.0 : Initial implementation
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
# Standard Library
from typing import Dict, Optional

# Third-party
import pytest

# Project modules
from basefunctions.kpi.protocol import KPIProvider


# =============================================================================
# FIXTURE DEFINITIONS
# =============================================================================
@pytest.fixture
def flat_provider():
    """Provide flat KPI provider (no subproviders)."""

    class FlatProvider:
        def get_kpis(self) -> Dict[str, float]:
            return {"balance": 100.0, "profit": 50.0}

        def get_subproviders(self) -> Optional[Dict[str, KPIProvider]]:
            return None

    return FlatProvider()


@pytest.fixture
def nested_provider():
    """Provide nested KPI provider (one level of subproviders)."""

    class SubProvider:
        def get_kpis(self) -> Dict[str, float]:
            return {"sub_balance": 25.0}

        def get_subproviders(self) -> Optional[Dict[str, KPIProvider]]:
            return None

    class RootProvider:
        def get_kpis(self) -> Dict[str, float]:
            return {"balance": 100.0}

        def get_subproviders(self) -> Optional[Dict[str, KPIProvider]]:
            return {"portfolio": SubProvider()}

    return RootProvider()


@pytest.fixture
def deeply_nested_provider():
    """Provide deeply nested KPI provider (3 levels)."""

    class Level3Provider:
        def get_kpis(self) -> Dict[str, float]:
            return {"level3_value": 10.0}

        def get_subproviders(self) -> Optional[Dict[str, KPIProvider]]:
            return None

    class Level2Provider:
        def get_kpis(self) -> Dict[str, float]:
            return {"level2_value": 50.0}

        def get_subproviders(self) -> Optional[Dict[str, KPIProvider]]:
            return {"level3": Level3Provider()}

    class Level1Provider:
        def get_kpis(self) -> Dict[str, float]:
            return {"level1_value": 100.0}

        def get_subproviders(self) -> Optional[Dict[str, KPIProvider]]:
            return {"level2": Level2Provider()}

    return Level1Provider()


@pytest.fixture
def multi_subprovider():
    """Provide provider with multiple subproviders."""

    class PortfolioProvider:
        def get_kpis(self) -> Dict[str, float]:
            return {"portfolio_value": 1000.0}

        def get_subproviders(self) -> Optional[Dict[str, KPIProvider]]:
            return None

    class RiskProvider:
        def get_kpis(self) -> Dict[str, float]:
            return {"var": 50.0, "sharpe": 1.5}

        def get_subproviders(self) -> Optional[Dict[str, KPIProvider]]:
            return None

    class RootProvider:
        def get_kpis(self) -> Dict[str, float]:
            return {"balance": 5000.0}

        def get_subproviders(self) -> Optional[Dict[str, KPIProvider]]:
            return {
                "portfolio": PortfolioProvider(),
                "risk": RiskProvider(),
            }

    return RootProvider()


@pytest.fixture
def empty_provider():
    """Provide provider with empty KPI dict."""

    class EmptyProvider:
        def get_kpis(self) -> Dict[str, float]:
            return {}

        def get_subproviders(self) -> Optional[Dict[str, KPIProvider]]:
            return None

    return EmptyProvider()


@pytest.fixture
def empty_subprovider():
    """Provide provider with empty subproviders dict."""

    class EmptySubProvider:
        def get_kpis(self) -> Dict[str, float]:
            return {"balance": 100.0}

        def get_subproviders(self) -> Optional[Dict[str, KPIProvider]]:
            return {}

    return EmptySubProvider()


@pytest.fixture
def numeric_provider():
    """Provide provider with various numeric types."""

    class NumericProvider:
        def get_kpis(self) -> Dict[str, float]:
            return {
                "int_value": 100.0,
                "float_value": 123.456,
                "zero": 0.0,
                "negative": -50.5,
            }

        def get_subproviders(self) -> Optional[Dict[str, KPIProvider]]:
            return None

    return NumericProvider()


@pytest.fixture
def categorized_provider():
    """Provide provider with business and technical KPIs."""

    class CategorizedProvider:
        def get_kpis(self) -> Dict[str, float]:
            return {
                "business.revenue": 10000.0,
                "business.orders": 50.0,
                "technical.cpu_usage": 75.0,
                "technical.memory_mb": 512.0,
            }

        def get_subproviders(self) -> Optional[Dict[str, KPIProvider]]:
            return None

    return CategorizedProvider()


@pytest.fixture
def mixed_categorized_provider():
    """Provide provider with mixed business, technical, and uncategorized KPIs."""

    class MixedProvider:
        def get_kpis(self) -> Dict[str, float]:
            return {
                "business.revenue": 10000.0,
                "technical.cpu": 50.0,
                "balance": 1000.0,  # No category prefix
            }

        def get_subproviders(self) -> Optional[Dict[str, KPIProvider]]:
            return None

    return MixedProvider()


@pytest.fixture
def nested_categorized_provider():
    """Provide nested provider with categorized KPIs in subproviders."""

    class SubProvider:
        def get_kpis(self) -> Dict[str, float]:
            return {
                "business.profit": 100.0,
                "technical.latency_ms": 45.0,
            }

        def get_subproviders(self) -> Optional[Dict[str, KPIProvider]]:
            return None

    class RootProvider:
        def get_kpis(self) -> Dict[str, float]:
            return {
                "business.balance": 1000.0,
                "technical.cpu": 50.0,
            }

        def get_subproviders(self) -> Optional[Dict[str, KPIProvider]]:
            return {"portfolio": SubProvider()}

    return RootProvider()


@pytest.fixture
def only_business_provider():
    """Provide provider with only business KPIs."""

    class OnlyBusinessProvider:
        def get_kpis(self) -> Dict[str, float]:
            return {
                "business.revenue": 5000.0,
                "business.profit": 500.0,
            }

        def get_subproviders(self) -> Optional[Dict[str, KPIProvider]]:
            return None

    return OnlyBusinessProvider()


@pytest.fixture
def only_technical_provider():
    """Provide provider with only technical KPIs."""

    class OnlyTechnicalProvider:
        def get_kpis(self) -> Dict[str, float]:
            return {
                "technical.uptime": 99.9,
                "technical.errors": 2.0,
            }

        def get_subproviders(self) -> Optional[Dict[str, KPIProvider]]:
            return None

    return OnlyTechnicalProvider()
