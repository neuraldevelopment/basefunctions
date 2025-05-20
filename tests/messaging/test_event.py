"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment , Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Unit tests for Event and TypedEvent classes
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import pytest
from datetime import datetime
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
class TestEvent:
    """Tests for the base Event class."""

    def test_initialization(self):
        """Test that Event initializes with the correct attributes."""
        event_type = "test_event"
        source = "test_source"

        event = basefunctions.Event(event_type, source)

        assert event.type == event_type
        assert event.source == source
        assert isinstance(event.timestamp, datetime)
        assert event.processed is False

    def test_mark_processed(self):
        """Test that an event can be marked as processed."""
        event = basefunctions.Event("test_event")
        assert event.processed is False

        event.mark_processed()
        assert event.processed is True

    def test_data_storage(self):
        """Test storing and retrieving data in the event."""
        event = basefunctions.Event("test_event")

        # Test setting and getting data
        event.set_data("key1", "value1")
        assert event.get_data("key1") == "value1"

        # Test default value for non-existent key
        assert event.get_data("non_existent") is None
        assert event.get_data("non_existent", "default") == "default"

        # Test get_all_data returns a copy
        data_dict = event.get_all_data()
        assert isinstance(data_dict, dict)
        assert data_dict.get("key1") == "value1"

        # Modify the returned dict and verify original is unchanged
        data_dict["key1"] = "modified"
        assert event.get_data("key1") == "value1"

    def test_string_representation(self):
        """Test the string representation of an event."""
        event = basefunctions.Event("test_event", "test_source")
        str_repr = str(event)

        assert "Event" in str_repr
        assert "test_event" in str_repr
        assert "test_source" in str_repr


class CustomTypedEvent(basefunctions.TypedEvent):
    """Custom TypedEvent for testing."""

    event_type = "custom.typed.event"


class TestTypedEvent:
    """Tests for the TypedEvent class."""

    def test_initialization(self):
        """Test that TypedEvent initializes with the class-defined event type."""
        event = CustomTypedEvent()

        assert event.type == "custom.typed.event"
        assert isinstance(event.timestamp, datetime)
        assert event.processed is False

    def test_inheritance(self):
        """Test that TypedEvent inherits properly from Event."""
        event = CustomTypedEvent()

        assert isinstance(event, basefunctions.Event)
        assert isinstance(event, basefunctions.TypedEvent)

    def test_with_source_and_data(self):
        """Test TypedEvent with source and data parameters."""
        source = "test_source"
        data = {"key": "value"}

        event = CustomTypedEvent(source, data)

        assert event.source == source
        assert event.get_data("key") == "value"

    def test_multiple_typed_events(self):
        """Test multiple TypedEvent subclasses with different types."""

        class Event1(basefunctions.TypedEvent):
            event_type = "event.type.1"

        class Event2(basefunctions.TypedEvent):
            event_type = "event.type.2"

        event1 = Event1()
        event2 = Event2()

        assert event1.type == "event.type.1"
        assert event2.type == "event.type.2"
