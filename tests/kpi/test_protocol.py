"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Tests for KPIProvider Protocol - Protocol compliance and duck typing
 Log:
 v1.0 : Initial implementation
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
# Standard Library
from typing import Dict, Optional

# Project modules
from basefunctions.kpi.protocol import KPIProvider


# =============================================================================
# TEST CLASSES
# =============================================================================
def test_flat_provider_implements_protocol():
    """Test flat provider implements KPIProvider Protocol."""
    # Arrange
    class FlatProvider:
        def get_kpis(self) -> Dict[str, float]:
            return {"balance": 100.0, "profit": 50.0}

        def get_subproviders(self) -> Optional[Dict[str, KPIProvider]]:
            return None

    # Act
    provider = FlatProvider()
    kpis = provider.get_kpis()
    subproviders = provider.get_subproviders()

    # Assert
    assert kpis == {"balance": 100.0, "profit": 50.0}
    assert subproviders is None


def test_nested_provider_implements_protocol():
    """Test nested provider implements KPIProvider Protocol."""
    # Arrange
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

    # Act
    provider = RootProvider()
    kpis = provider.get_kpis()
    subproviders = provider.get_subproviders()

    # Assert
    assert kpis == {"balance": 100.0}
    assert subproviders is not None
    assert "portfolio" in subproviders
    assert subproviders["portfolio"].get_kpis() == {"sub_balance": 25.0}


def test_provider_with_empty_kpis():
    """Test provider with empty KPI dict."""
    # Arrange
    class EmptyProvider:
        def get_kpis(self) -> Dict[str, float]:
            return {}

        def get_subproviders(self) -> Optional[Dict[str, KPIProvider]]:
            return None

    # Act
    provider = EmptyProvider()
    kpis = provider.get_kpis()

    # Assert
    assert kpis == {}


def test_provider_with_empty_subproviders_dict():
    """Test provider with empty subproviders dict."""
    # Arrange
    class EmptySubProvider:
        def get_kpis(self) -> Dict[str, float]:
            return {"balance": 100.0}

        def get_subproviders(self) -> Optional[Dict[str, KPIProvider]]:
            return {}

    # Act
    provider = EmptySubProvider()
    subproviders = provider.get_subproviders()

    # Assert
    assert subproviders == {}


def test_provider_with_multiple_subproviders():
    """Test provider with multiple nested subproviders."""
    # Arrange
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

    # Act
    provider = RootProvider()
    subproviders = provider.get_subproviders()

    # Assert
    assert subproviders is not None
    assert len(subproviders) == 2
    assert "portfolio" in subproviders
    assert "risk" in subproviders
    assert subproviders["portfolio"].get_kpis() == {"portfolio_value": 1000.0}
    assert subproviders["risk"].get_kpis() == {"var": 50.0, "sharpe": 1.5}


def test_deeply_nested_provider_structure():
    """Test provider with deep nesting (3 levels)."""
    # Arrange
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

    # Act
    provider = Level1Provider()
    level2_providers = provider.get_subproviders()

    # Assert
    assert level2_providers is not None
    level2 = level2_providers["level2"]
    assert level2.get_kpis() == {"level2_value": 50.0}

    level3_providers = level2.get_subproviders()
    assert level3_providers is not None
    level3 = level3_providers["level3"]
    assert level3.get_kpis() == {"level3_value": 10.0}


def test_provider_with_numeric_variations():
    """Test provider with various numeric types in KPIs."""
    # Arrange
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

    # Act
    provider = NumericProvider()
    kpis = provider.get_kpis()

    # Assert
    assert kpis["int_value"] == 100.0
    assert kpis["float_value"] == 123.456
    assert kpis["zero"] == 0.0
    assert kpis["negative"] == -50.5
