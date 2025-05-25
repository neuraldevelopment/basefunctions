"""
=============================================================================

 Licensed Materials, Property of neuraldevelopment , Munich

 Project : basefunctions

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 Unit tests for event filter mechanisms

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import pytest
from unittest.mock import Mock
import basefunctions

# -------------------------------------------------------------
# DEFINITIONS REGISTRY
# -------------------------------------------------------------

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------


# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------
class ConcreteFilter(basefunctions.EventFilter):
    """Concrete implementation of the EventFilter interface for testing."""

    def __init__(self, return_value=True):
        """Initialize with a return value for matches."""
        self.return_value = return_value
        self.match_calls = []

    def matches(self, event):
        """Record calls and return the configured value."""
        self.match_calls.append(event)
        return self.return_value


class TestEventFilter:
    """Tests for the EventFilter abstract base class."""

    def test_abstract_interface(self):
        """Test that EventFilter is an abstract interface."""
        # Should not be able to instantiate directly
        with pytest.raises(TypeError):
            basefunctions.EventFilter()

    def test_callable_interface(self):
        """Test that filters are callable objects."""
        filter_inst = ConcreteFilter(True)
        event = basefunctions.Event("test_event")

        # Call as a function
        result = filter_inst(event)

        # Verify it calls matches
        assert result is True
        assert len(filter_inst.match_calls) == 1
        assert filter_inst.match_calls[0] is event

    def test_and_filter_creation(self):
        """Test creating an AND filter from two filters."""
        filter1 = ConcreteFilter(True)
        filter2 = ConcreteFilter(True)

        # Create AND filter
        and_filter = filter1.and_filter(filter2)

        # Verify type and structure
        assert isinstance(and_filter, basefunctions.AndFilter)
        assert and_filter._filters[0] is filter1
        assert and_filter._filters[1] is filter2

    def test_or_filter_creation(self):
        """Test creating an OR filter from two filters."""
        filter1 = ConcreteFilter(True)
        filter2 = ConcreteFilter(True)

        # Create OR filter
        or_filter = filter1.or_filter(filter2)

        # Verify type and structure
        assert isinstance(or_filter, basefunctions.OrFilter)
        assert or_filter._filters[0] is filter1
        assert or_filter._filters[1] is filter2

    def test_not_filter_creation(self):
        """Test creating a NOT filter from a filter."""
        filter_inst = ConcreteFilter(True)

        # Create NOT filter
        not_filter = filter_inst.not_filter()

        # Verify type and structure
        assert isinstance(not_filter, basefunctions.NotFilter)
        assert not_filter._filter is filter_inst


class TestFunctionFilter:
    """Tests for the FunctionFilter class."""

    def test_initialization(self):
        """Test initialization with a function."""
        # Create mock function
        filter_func = Mock(return_value=True)

        # Create filter
        filter_inst = basefunctions.FunctionFilter(filter_func)

        # Verify internal state
        assert hasattr(filter_inst, "_filter_func")
        assert filter_inst._filter_func is filter_func

    def test_matches_delegation(self):
        """Test that matches delegates to the function."""
        # Create mock function
        filter_func = Mock(return_value=True)

        # Create filter and test
        filter_inst = basefunctions.FunctionFilter(filter_func)
        event = basefunctions.Event("test_event")
        result = filter_inst.matches(event)

        # Verify delegation
        filter_func.assert_called_once_with(event)
        assert result is True

        # Test with different return value
        filter_func.return_value = False
        result = filter_inst.matches(event)
        assert result is False


class TestAndFilter:
    """Tests for the AndFilter class."""

    def test_initialization(self):
        """Test initialization with multiple filters."""
        filter1 = ConcreteFilter(True)
        filter2 = ConcreteFilter(True)
        filter3 = ConcreteFilter(True)

        # Create filter
        and_filter = basefunctions.AndFilter(filter1, filter2, filter3)

        # Verify internal state
        assert hasattr(and_filter, "_filters")
        assert len(and_filter._filters) == 3
        assert and_filter._filters[0] is filter1
        assert and_filter._filters[1] is filter2
        assert and_filter._filters[2] is filter3

    def test_matches_all_true(self):
        """Test matching when all filters match."""
        filter1 = ConcreteFilter(True)
        filter2 = ConcreteFilter(True)

        and_filter = basefunctions.AndFilter(filter1, filter2)
        event = basefunctions.Event("test_event")

        # Test
        result = and_filter.matches(event)

        # Verify
        assert result is True
        assert len(filter1.match_calls) == 1
        assert len(filter2.match_calls) == 1

    def test_matches_one_false(self):
        """Test matching when one filter doesn't match."""
        filter1 = ConcreteFilter(True)
        filter2 = ConcreteFilter(False)

        and_filter = basefunctions.AndFilter(filter1, filter2)
        event = basefunctions.Event("test_event")

        # Test
        result = and_filter.matches(event)

        # Verify
        assert result is False
        assert len(filter1.match_calls) == 1
        assert len(filter2.match_calls) == 1

    def test_short_circuit_evaluation(self):
        """Test that evaluation short-circuits on first failure."""
        filter1 = ConcreteFilter(False)
        filter2 = ConcreteFilter(True)

        and_filter = basefunctions.AndFilter(filter1, filter2)
        event = basefunctions.Event("test_event")

        # Test
        result = and_filter.matches(event)

        # Verify
        assert result is False
        assert len(filter1.match_calls) == 1
        # filter2 should not be called due to short-circuit
        assert len(filter2.match_calls) == 0


class TestOrFilter:
    """Tests for the OrFilter class."""

    def test_initialization(self):
        """Test initialization with multiple filters."""
        filter1 = ConcreteFilter(True)
        filter2 = ConcreteFilter(True)

        # Create filter
        or_filter = basefunctions.OrFilter(filter1, filter2)

        # Verify internal state
        assert hasattr(or_filter, "_filters")
        assert len(or_filter._filters) == 2
        assert or_filter._filters[0] is filter1
        assert or_filter._filters[1] is filter2

    def test_matches_one_true(self):
        """Test matching when one filter matches."""
        filter1 = ConcreteFilter(True)
        filter2 = ConcreteFilter(False)

        or_filter = basefunctions.OrFilter(filter1, filter2)
        event = basefunctions.Event("test_event")

        # Test
        result = or_filter.matches(event)

        # Verify
        assert result is True
        assert len(filter1.match_calls) == 1
        assert len(filter2.match_calls) == 0  # Short-circuit

    def test_matches_all_false(self):
        """Test matching when all filters don't match."""
        filter1 = ConcreteFilter(False)
        filter2 = ConcreteFilter(False)

        or_filter = basefunctions.OrFilter(filter1, filter2)
        event = basefunctions.Event("test_event")

        # Test
        result = or_filter.matches(event)

        # Verify
        assert result is False
        assert len(filter1.match_calls) == 1
        assert len(filter2.match_calls) == 1

    def test_short_circuit_evaluation(self):
        """Test that evaluation short-circuits on first success."""
        filter1 = ConcreteFilter(True)
        filter2 = ConcreteFilter(True)

        or_filter = basefunctions.OrFilter(filter1, filter2)
        event = basefunctions.Event("test_event")

        # Test
        result = or_filter.matches(event)

        # Verify
        assert result is True
        assert len(filter1.match_calls) == 1
        # filter2 should not be called due to short-circuit
        assert len(filter2.match_calls) == 0


class TestNotFilter:
    """Tests for the NotFilter class."""

    def test_initialization(self):
        """Test initialization with a filter."""
        inner_filter = ConcreteFilter(True)

        # Create filter
        not_filter = basefunctions.NotFilter(inner_filter)

        # Verify internal state
        assert hasattr(not_filter, "_filter")
        assert not_filter._filter is inner_filter

    def test_matches_negation(self):
        """Test that matches negates the inner filter's result."""
        # Test with inner filter returning True
        inner_filter = ConcreteFilter(True)
        not_filter = basefunctions.NotFilter(inner_filter)
        event = basefunctions.Event("test_event")

        result = not_filter.matches(event)

        # Verify
        assert result is False
        assert len(inner_filter.match_calls) == 1

        # Test with inner filter returning False
        inner_filter = ConcreteFilter(False)
        not_filter = basefunctions.NotFilter(inner_filter)

        result = not_filter.matches(event)

        # Verify
        assert result is True
        assert len(inner_filter.match_calls) == 1


class TestTypeFilter:
    """Tests for the TypeFilter class."""

    def test_initialization_with_string(self):
        """Test initialization with a string event type."""
        # Create filter
        filter_inst = basefunctions.TypeFilter("test.event")

        # Verify internal state
        assert hasattr(filter_inst, "_event_types")
        assert isinstance(filter_inst._event_types, set)
        assert "test.event" in filter_inst._event_types

    def test_initialization_with_list(self):
        """Test initialization with a list of event types."""
        # Create filter
        filter_inst = basefunctions.TypeFilter(["event1", "event2", "event3"])

        # Verify internal state
        assert len(filter_inst._event_types) == 3
        assert "event1" in filter_inst._event_types
        assert "event2" in filter_inst._event_types
        assert "event3" in filter_inst._event_types

    def test_matches_matching_type(self):
        """Test matching an event with a matching type."""
        filter_inst = basefunctions.TypeFilter(["event1", "event2"])
        event = basefunctions.Event("event1")

        # Test
        result = filter_inst.matches(event)

        # Verify
        assert result is True

    def test_matches_non_matching_type(self):
        """Test matching an event with a non-matching type."""
        filter_inst = basefunctions.TypeFilter(["event1", "event2"])
        event = basefunctions.Event("event3")

        # Test
        result = filter_inst.matches(event)

        # Verify
        assert result is False


class TestPropertyFilter:
    """Tests for the PropertyFilter class."""

    def test_initialization(self):
        """Test initialization with property path and expected value."""
        # Create filter
        filter_inst = basefunctions.PropertyFilter("source.name", "test")

        # Verify internal state
        assert hasattr(filter_inst, "_property_path")
        assert hasattr(filter_inst, "_expected_value")
        assert filter_inst._property_path == "source.name"
        assert filter_inst._expected_value == "test"

    def test_matches_simple_property(self):
        """Test matching a simple property."""
        filter_inst = basefunctions.PropertyFilter("type", "test.event")
        event = basefunctions.Event("test.event")

        # Test
        result = filter_inst.matches(event)

        # Verify
        assert result is True

    def test_matches_nested_property(self):
        """Test matching a nested property."""
        # Create an event with a nested property
        event = basefunctions.Event("test.event")

        # Create a mock source with a name property
        class Source:
            def __init__(self, name):
                self.name = name

        event._source = Source("test_source")

        # Create filter and test
        filter_inst = basefunctions.PropertyFilter("source.name", "test_source")
        result = filter_inst.matches(event)

        # Verify
        assert result is True

    def test_matches_data_property(self):
        """Test matching a property in the event's data dictionary."""
        event = basefunctions.Event("test.event")
        event.set_data("user", "test_user")

        # Create filter and test
        filter_inst = basefunctions.PropertyFilter("user", "test_user")
        result = filter_inst.matches(event)

        # Verify
        assert result is True

    def test_matches_non_existent_property(self):
        """Test matching a non-existent property."""
        event = basefunctions.Event("test.event")

        # Create filter and test
        filter_inst = basefunctions.PropertyFilter("non_existent", "value")
        result = filter_inst.matches(event)

        # Verify
        assert result is False


class TestDataFilter:
    """Tests for the DataFilter class."""

    def test_initialization(self):
        """Test initialization with key and expected value."""
        # Create filter
        filter_inst = basefunctions.DataFilter("user", "test_user")

        # Verify internal state
        assert hasattr(filter_inst, "_key")
        assert hasattr(filter_inst, "_expected_value")
        assert filter_inst._key == "user"
        assert filter_inst._expected_value == "test_user"

    def test_matches_existing_key(self):
        """Test matching an existing key in the event's data."""
        event = basefunctions.Event("test.event")
        event.set_data("user", "test_user")

        # Create filter and test
        filter_inst = basefunctions.DataFilter("user", "test_user")
        result = filter_inst.matches(event)

        # Verify
        assert result is True

    def test_matches_non_existing_key(self):
        """Test matching a non-existing key."""
        event = basefunctions.Event("test.event")

        # Create filter and test
        filter_inst = basefunctions.DataFilter("user", "test_user")
        result = filter_inst.matches(event)

        # Verify
        assert result is False

    def test_matches_different_value(self):
        """Test matching with a different value."""
        event = basefunctions.Event("test.event")
        event.set_data("user", "other_user")

        # Create filter and test
        filter_inst = basefunctions.DataFilter("user", "test_user")
        result = filter_inst.matches(event)

        # Verify
        assert result is False


class TestFilterFactoryFunctions:
    """Tests for the filter factory functions."""

    def test_type_filter_factory(self):
        """Test the type_filter factory function."""
        # Create filter
        filter_inst = basefunctions.type_filter("test.event")

        # Verify
        assert isinstance(filter_inst, basefunctions.TypeFilter)
        assert "test.event" in filter_inst._event_types

    def test_property_filter_factory(self):
        """Test the property_filter factory function."""
        # Create filter
        filter_inst = basefunctions.property_filter("source.name", "test")

        # Verify
        assert isinstance(filter_inst, basefunctions.PropertyFilter)
        assert filter_inst._property_path == "source.name"
        assert filter_inst._expected_value == "test"

    def test_data_filter_factory(self):
        """Test the data_filter factory function."""
        # Create filter
        filter_inst = basefunctions.data_filter("user", "test_user")

        # Verify
        assert isinstance(filter_inst, basefunctions.DataFilter)
        assert filter_inst._key == "user"
        assert filter_inst._expected_value == "test_user"

    def test_function_filter_factory(self):
        """Test the function_filter factory function."""
        # Create mock function
        filter_func = Mock()

        # Create filter
        filter_inst = basefunctions.function_filter(filter_func)

        # Verify
        assert isinstance(filter_inst, basefunctions.FunctionFilter)
        assert filter_inst._filter_func is filter_func
