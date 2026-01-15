"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Tests for KPI registry - central provider registration
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
from basefunctions.kpi import clear, get_all_providers, register
from basefunctions.kpi.protocol import KPIProvider


# =============================================================================
# FIXTURE DEFINITIONS
# =============================================================================
@pytest.fixture(autouse=True)
def clear_registry():
    """Clear registry before and after each test."""
    clear()
    yield
    clear()


@pytest.fixture
def mock_provider():
    """Provide mock KPI provider."""

    class MockProvider:
        def get_kpis(self) -> Dict[str, float]:
            return {"balance": 100.0}

        def get_subproviders(self) -> Optional[Dict[str, KPIProvider]]:
            return None

    return MockProvider()


@pytest.fixture
def second_mock_provider():
    """Provide second mock KPI provider."""

    class SecondMockProvider:
        def get_kpis(self) -> Dict[str, float]:
            return {"profit": 50.0}

        def get_subproviders(self) -> Optional[Dict[str, KPIProvider]]:
            return None

    return SecondMockProvider()


# =============================================================================
# TEST DEFINITIONS - register()
# =============================================================================
def test_register_single_provider_is_retrievable(mock_provider):
    """Test single provider registration and retrieval."""
    # Arrange
    name = "test_provider"

    # Act
    register(name, mock_provider)
    providers = get_all_providers()

    # Assert
    assert name in providers
    assert providers[name] is mock_provider


def test_register_multiple_providers_are_all_retrievable(
    mock_provider, second_mock_provider
):
    """Test multiple providers registration and retrieval."""
    # Arrange
    name1 = "provider1"
    name2 = "provider2"

    # Act
    register(name1, mock_provider)
    register(name2, second_mock_provider)
    providers = get_all_providers()

    # Assert
    assert len(providers) == 2
    assert providers[name1] is mock_provider
    assert providers[name2] is second_mock_provider


def test_register_with_duplicate_name_raises_value_error(mock_provider):
    """Test duplicate registration raises ValueError."""
    # Arrange
    name = "duplicate"
    register(name, mock_provider)

    # Act & Assert
    with pytest.raises(ValueError, match="bereits registriert"):
        register(name, mock_provider)


def test_register_with_empty_string_name_registers_successfully(mock_provider):
    """Test empty string as name registers successfully."""
    # Arrange
    name = ""

    # Act
    register(name, mock_provider)
    providers = get_all_providers()

    # Assert
    assert name in providers
    assert providers[name] is mock_provider


def test_register_with_none_name_registers_successfully(mock_provider):
    """Test None as name registers successfully (dicts allow None keys)."""
    # Arrange
    name = None

    # Act
    register(name, mock_provider)  # type: ignore[arg-type]
    providers = get_all_providers()

    # Assert
    assert name in providers
    assert providers[name] is mock_provider


def test_register_with_none_provider_registers_successfully():
    """Test None as provider registers successfully."""
    # Arrange
    name = "none_provider"
    provider = None

    # Act
    register(name, provider)  # type: ignore[arg-type]
    providers = get_all_providers()

    # Assert
    assert name in providers
    assert providers[name] is None


# =============================================================================
# TEST DEFINITIONS - get_all_providers()
# =============================================================================
def test_get_all_providers_with_empty_registry_returns_empty_dict():
    """Test get_all_providers on empty registry returns empty dict."""
    # Arrange
    # Registry cleared by fixture

    # Act
    providers = get_all_providers()

    # Assert
    assert providers == {}
    assert isinstance(providers, dict)


def test_get_all_providers_with_single_provider_returns_one_entry(mock_provider):
    """Test get_all_providers with single provider returns dict with one entry."""
    # Arrange
    name = "single_provider"
    register(name, mock_provider)

    # Act
    providers = get_all_providers()

    # Assert
    assert len(providers) == 1
    assert name in providers
    assert providers[name] is mock_provider


def test_get_all_providers_with_multiple_providers_returns_all_entries(
    mock_provider, second_mock_provider
):
    """Test get_all_providers with multiple providers returns all entries."""
    # Arrange
    name1 = "provider1"
    name2 = "provider2"
    register(name1, mock_provider)
    register(name2, second_mock_provider)

    # Act
    providers = get_all_providers()

    # Assert
    assert len(providers) == 2
    assert name1 in providers
    assert name2 in providers
    assert providers[name1] is mock_provider
    assert providers[name2] is second_mock_provider


def test_get_all_providers_returns_defensive_copy(mock_provider):
    """Test get_all_providers returns defensive copy."""
    # Arrange
    name = "copy_test"
    register(name, mock_provider)

    # Act
    providers1 = get_all_providers()
    providers1["new_key"] = mock_provider
    providers2 = get_all_providers()

    # Assert
    assert "new_key" not in providers2
    assert len(providers2) == 1


# =============================================================================
# TEST DEFINITIONS - clear()
# =============================================================================
def test_clear_empty_registry_does_not_raise_error():
    """Test clear on empty registry does not raise error."""
    # Arrange
    # Registry cleared by fixture

    # Act & Assert (no exception expected)
    clear()


def test_clear_after_registrations_empties_registry(mock_provider):
    """Test clear after registrations empties registry."""
    # Arrange
    register("provider1", mock_provider)
    register("provider2", mock_provider)
    assert len(get_all_providers()) == 2

    # Act
    clear()

    # Assert
    providers = get_all_providers()
    assert len(providers) == 0
    assert providers == {}


def test_clear_allows_re_registration_after_clear(mock_provider):
    """Test re-registration works after clear."""
    # Arrange
    name = "reregister_test"
    register(name, mock_provider)
    clear()

    # Act
    register(name, mock_provider)
    providers = get_all_providers()

    # Assert
    assert name in providers
    assert providers[name] is mock_provider


# =============================================================================
# TEST DEFINITIONS - Integration
# =============================================================================
def test_registry_complete_lifecycle(mock_provider, second_mock_provider):
    """Test complete registry lifecycle: register → get → clear → get."""
    # Arrange
    name1 = "provider1"
    name2 = "provider2"

    # Act & Assert - Register
    register(name1, mock_provider)
    register(name2, second_mock_provider)
    providers = get_all_providers()
    assert len(providers) == 2

    # Act & Assert - Clear
    clear()
    providers = get_all_providers()
    assert len(providers) == 0

    # Act & Assert - Re-register
    register(name1, mock_provider)
    providers = get_all_providers()
    assert len(providers) == 1
    assert name1 in providers


def test_registry_multiple_register_calls_different_names(
    mock_provider, second_mock_provider
):
    """Test multiple register calls with different names."""
    # Arrange
    names = ["provider1", "provider2", "provider3"]

    # Act
    register(names[0], mock_provider)
    register(names[1], second_mock_provider)
    register(names[2], mock_provider)
    providers = get_all_providers()

    # Assert
    assert len(providers) == 3
    for name in names:
        assert name in providers


def test_registry_isolation_between_tests():
    """Test registry isolation between tests via autouse fixture."""
    # Arrange
    # This test verifies that the autouse fixture properly clears
    # the registry, ensuring test isolation

    # Act
    providers = get_all_providers()

    # Assert
    assert len(providers) == 0
    assert providers == {}
