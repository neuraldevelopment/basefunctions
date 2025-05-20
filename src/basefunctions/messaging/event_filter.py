"""
=============================================================================

 Licensed Materials, Property of neuraldevelopment, Munich

 Project : basefunctions

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 Event filtering mechanisms for the messaging system

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from abc import ABC, abstractmethod
from typing import Any, Callable, List, Union, TYPE_CHECKING

# Import for type hints only, not at runtime
if TYPE_CHECKING:
    from basefunctions.messaging.event import Event

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


class EventFilter(ABC):
    """
    Abstract base class for event filters.

    Event filters decide whether an event should be passed to a handler.
    """

    @abstractmethod
    def matches(self, event: "Event") -> bool:
        """
        Check if an event matches this filter.

        Parameters
        ----------
        event : Event
            The event to check.

        Returns
        -------
        bool
            True if the event matches the filter, False otherwise.
        """
        pass

    def __call__(self, event: "Event") -> bool:
        """
        Make the filter callable.

        This allows using filter instances directly as filter functions.

        Parameters
        ----------
        event : Event
            The event to check.

        Returns
        -------
        bool
            True if the event matches the filter, False otherwise.
        """
        return self.matches(event)

    def and_filter(self, other: "EventFilter") -> "AndFilter":
        """
        Combine this filter with another using logical AND.

        Parameters
        ----------
        other : EventFilter
            The other filter to combine with.

        Returns
        -------
        AndFilter
            A new filter that matches only if both this filter and
            the other filter match.
        """
        return AndFilter(self, other)

    def or_filter(self, other: "EventFilter") -> "OrFilter":
        """
        Combine this filter with another using logical OR.

        Parameters
        ----------
        other : EventFilter
            The other filter to combine with.

        Returns
        -------
        OrFilter
            A new filter that matches if either this filter or
            the other filter matches.
        """
        return OrFilter(self, other)

    def not_filter(self) -> "NotFilter":
        """
        Negate this filter.

        Returns
        -------
        NotFilter
            A new filter that matches if this filter does not match.
        """
        return NotFilter(self)


class FunctionFilter(EventFilter):
    """
    Filter that uses a function to determine matches.

    This is the most flexible filter, as it can use any callable
    that takes an event and returns a boolean.
    """

    __slots__ = ("_filter_func",)

    def __init__(self, filter_func: Callable[["Event"], bool]):
        """
        Initialize a function filter.

        Parameters
        ----------
        filter_func : Callable[[Event], bool]
            The function to use for filtering.
        """
        self._filter_func = filter_func

    def matches(self, event: "Event") -> bool:
        """
        Check if an event matches this filter.

        Parameters
        ----------
        event : Event
            The event to check.

        Returns
        -------
        bool
            True if the filter function returns True for the event,
            False otherwise.
        """
        return self._filter_func(event)


class AndFilter(EventFilter):
    """
    Filter that matches if all of its constituent filters match.
    """

    __slots__ = ("_filters",)

    def __init__(self, *filters: EventFilter):
        """
        Initialize an AND filter.

        Parameters
        ----------
        *filters : EventFilter
            The filters to combine with logical AND.
        """
        self._filters = filters

    def matches(self, event: "Event") -> bool:
        """
        Check if an event matches all constituent filters.

        Parameters
        ----------
        event : Event
            The event to check.

        Returns
        -------
        bool
            True if all constituent filters match, False otherwise.
        """
        return all(f.matches(event) for f in self._filters)


class OrFilter(EventFilter):
    """
    Filter that matches if any of its constituent filters match.
    """

    __slots__ = ("_filters",)

    def __init__(self, *filters: EventFilter):
        """
        Initialize an OR filter.

        Parameters
        ----------
        *filters : EventFilter
            The filters to combine with logical OR.
        """
        self._filters = filters

    def matches(self, event: "Event") -> bool:
        """
        Check if an event matches any constituent filter.

        Parameters
        ----------
        event : Event
            The event to check.

        Returns
        -------
        bool
            True if any constituent filter matches, False otherwise.
        """
        return any(f.matches(event) for f in self._filters)


class NotFilter(EventFilter):
    """
    Filter that negates the result of another filter.
    """

    __slots__ = ("_filter",)

    def __init__(self, filter_: EventFilter):
        """
        Initialize a NOT filter.

        Parameters
        ----------
        filter_ : EventFilter
            The filter to negate.
        """
        self._filter = filter_

    def matches(self, event: "Event") -> bool:
        """
        Check if an event does not match the underlying filter.

        Parameters
        ----------
        event : Event
            The event to check.

        Returns
        -------
        bool
            True if the underlying filter does not match, False otherwise.
        """
        return not self._filter.matches(event)


class TypeFilter(EventFilter):
    """
    Filter that matches events of a specific type.
    """

    __slots__ = ("_event_types",)

    def __init__(self, event_types: Union[str, List[str]]):
        """
        Initialize a type filter.

        Parameters
        ----------
        event_types : Union[str, List[str]]
            The event type(s) to match.
        """
        if isinstance(event_types, str):
            event_types = [event_types]
        self._event_types = set(event_types)

    def matches(self, event: "Event") -> bool:
        """
        Check if an event is of one of the specified types.

        Parameters
        ----------
        event : Event
            The event to check.

        Returns
        -------
        bool
            True if the event's type is in the set of types to match,
            False otherwise.
        """
        return event.type in self._event_types


class PropertyFilter(EventFilter):
    """
    Filter that matches events based on property values.
    """

    __slots__ = ("_property_path", "_expected_value")

    def __init__(self, property_path: str, expected_value: Any):
        """
        Initialize a property filter.

        Parameters
        ----------
        property_path : str
            The path to the property to check, using dot notation
            (e.g., 'source.name').
        expected_value : Any
            The expected value of the property.
        """
        self._property_path = property_path
        self._expected_value = expected_value

    def matches(self, event: "Event") -> bool:
        """
        Check if an event has a property with the expected value.

        Parameters
        ----------
        event : Event
            The event to check.

        Returns
        -------
        bool
            True if the specified property has the expected value,
            False otherwise.
        """
        # Get the property value by following the path
        current = event
        parts = self._property_path.split(".")

        # Handle the first part - could be an attribute or a data key
        if not parts:
            return False

        # Navigate through the property path
        for i, part in enumerate(parts):
            if hasattr(current, part):
                # It's an attribute, access it directly
                current = getattr(current, part)
            elif hasattr(current, "get_data") and callable(current.get_data):
                # It's an Event with a data dictionary
                # If this is the last part of the path, use get_data
                if i == len(parts) - 1:
                    current = current.get_data(part)
                else:
                    # For intermediate parts, get the value and continue if possible
                    temp = current.get_data(part)
                    if temp is None:
                        return False
                    current = temp
            else:
                # Can't navigate further
                return False

        # Compare with expected value
        return current == self._expected_value


class DataFilter(EventFilter):
    """
    Filter that matches events based on data dictionary values.

    This is specifically for the Event class's data dictionary.
    """

    __slots__ = ("_key", "_expected_value")

    def __init__(self, key: str, expected_value: Any):
        """
        Initialize a data filter.

        Parameters
        ----------
        key : str
            The key in the event's data dictionary.
        expected_value : Any
            The expected value for the key.
        """
        self._key = key
        self._expected_value = expected_value

    def matches(self, event: "Event") -> bool:
        """
        Check if an event has the expected value for the specified key.

        Parameters
        ----------
        event : Event
            The event to check.

        Returns
        -------
        bool
            True if the event's data contains the key with the expected value,
            False otherwise.
        """
        return event.get_data(self._key) == self._expected_value


# Factory functions for creating filters


def type_filter(event_types: Union[str, List[str]]) -> TypeFilter:
    """
    Create a filter that matches events of the specified type(s).

    Parameters
    ----------
    event_types : Union[str, List[str]]
        The event type(s) to match.

    Returns
    -------
    TypeFilter
        A filter that matches events of the specified type(s).
    """
    return TypeFilter(event_types)


def property_filter(property_path: str, expected_value: Any) -> PropertyFilter:
    """
    Create a filter that matches events with the specified property value.

    Parameters
    ----------
    property_path : str
        The path to the property to check, using dot notation.
    expected_value : Any
        The expected value of the property.

    Returns
    -------
    PropertyFilter
        A filter that matches events with the specified property value.
    """
    return PropertyFilter(property_path, expected_value)


def data_filter(key: str, expected_value: Any) -> DataFilter:
    """
    Create a filter that matches events with the specified data value.

    Parameters
    ----------
    key : str
        The key in the event's data dictionary.
    expected_value : Any
        The expected value for the key.

    Returns
    -------
    DataFilter
        A filter that matches events with the specified data value.
    """
    return DataFilter(key, expected_value)


def function_filter(
    filter_func: Callable[["Event"], bool],
) -> FunctionFilter:
    """
    Create a filter that uses a function to determine matches.

    Parameters
    ----------
    filter_func : Callable[[Event], bool]
        The function to use for filtering.

    Returns
    -------
    FunctionFilter
        A filter that uses the specified function.
    """
    return FunctionFilter(filter_func)
