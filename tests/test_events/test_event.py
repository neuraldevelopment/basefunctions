"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Test suite for Event class
 Log:
 v1.0.0 : Initial implementation
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
import pytest
from basefunctions.events.event import Event, EXECUTION_MODE_SYNC

# =============================================================================
# TEST CLASS - EVENT REQUEUE COUNT
# =============================================================================


class TestEventRequeueCount:
    """Test _requeue_count attribute in Event class."""

    def test_event_has_requeue_count_attribute(self):
        """Test that Event has _requeue_count in __slots__."""
        # Arrange & Act
        event = Event(event_type="test", event_exec_mode=EXECUTION_MODE_SYNC)

        # Assert
        assert hasattr(event, "_requeue_count")

    def test_event_requeue_count_initializes_to_zero(self):
        """Test that _requeue_count is initialized to 0."""
        # Arrange & Act
        event = Event(event_type="test", event_exec_mode=EXECUTION_MODE_SYNC)

        # Assert
        assert event._requeue_count == 0

    def test_event_requeue_count_can_be_incremented(self):
        """Test that _requeue_count can be incremented."""
        # Arrange
        event = Event(event_type="test", event_exec_mode=EXECUTION_MODE_SYNC)

        # Act
        event._requeue_count += 1

        # Assert
        assert event._requeue_count == 1
