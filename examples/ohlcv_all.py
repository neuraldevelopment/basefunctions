"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Complete OHLCV implementation - Events and all Handlers
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Optional, Any
from datetime import datetime
import time
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


class OHLCVDataEvent(basefunctions.Event):
    """Event containing OHLCV data for a specific ticker and date."""

    __slots__ = ("dataframe", "ticker_id", "current_date")

    def __init__(self, dataframe, ticker_id, current_date):
        """
        Initialize OHLCV event with business data.

        Parameters
        ----------
        dataframe : pd.DataFrame
            The OHLCV dataframe for a single ticker
        ticker_id : int
            The ID of the ticker
        current_date : datetime
            The current date in the simulation
        """
        # Set event type and system data
        self.type = "ohlcv_data"
        self.source = None
        self.timestamp = datetime.now()

        # Set business data
        self.dataframe = dataframe
        self.ticker_id = ticker_id
        self.current_date = current_date


class OHLCVSyncHandler(basefunctions.EventHandler):
    """Synchronous handler for OHLCV data events."""

    execution_mode = 0  # sync

    def __init__(self):
        """Initialize the handler."""
        self.processed_count = 0
        self.total_rows_processed = 0

    def handle(
        self, event: basefunctions.Event, context: Optional[basefunctions.EventContext] = None
    ) -> Any:
        """
        Handle OHLCV data event synchronously.

        Parameters
        ----------
        event : Event
            The event containing OHLCV data
        context : EventContext, optional
            Context (unused for sync)

        Returns
        -------
        Any
            Row count on success, raise Exception on error
        """
        if isinstance(event, OHLCVDataEvent):
            # Direct access to business data
            date_slice = event.dataframe.loc[: event.current_date]
            rows_processed = len(date_slice)
            self.total_rows_processed += rows_processed
            self.processed_count += 1
            return rows_processed
        else:
            raise ValueError("Invalid event type - expected OHLCVDataEvent")


class OHLCVThreadHandler(basefunctions.EventHandler):
    """Thread-based handler for OHLCV data events."""

    execution_mode = 1  # thread

    def handle(
        self, event: basefunctions.Event, context: Optional[basefunctions.EventContext] = None
    ) -> Any:
        """
        Handle OHLCV data event in thread.

        Parameters
        ----------
        event : Event
            The event containing OHLCV data
        context : EventContext
            Thread context with thread_local_data

        Returns
        -------
        Any
            Row count on success, raise Exception on error
        """
        if isinstance(event, OHLCVDataEvent):
            # Access thread local data for stats
            if context and context.thread_local_data:
                if not hasattr(context.thread_local_data, "processed_count"):
                    context.thread_local_data.processed_count = 0
                    context.thread_local_data.total_rows_processed = 0

                # Process the data
                date_slice = event.dataframe.loc[: event.current_date]
                rows_processed = len(date_slice)

                # Update thread local stats
                context.thread_local_data.processed_count += 1
                context.thread_local_data.total_rows_processed += rows_processed

                return rows_processed
            else:
                # Fallback if no context
                date_slice = event.dataframe.loc[: event.current_date]
                return len(date_slice)
        else:
            raise ValueError("Invalid event type - expected OHLCVDataEvent")


class OHLCVCoreletHandler(basefunctions.EventHandler):
    """Corelet-based handler for OHLCV data events."""

    execution_mode = 2  # corelet

    def handle(
        self, event: basefunctions.Event, context: Optional[basefunctions.EventContext] = None
    ) -> Any:
        """
        Handle OHLCV data event in corelet process.

        Parameters
        ----------
        event : Event
            The event containing OHLCV data
        context : EventContext
            Corelet context with process info

        Returns
        -------
        Any
            Row count on success, raise Exception on error
        """
        # Note: Check event attributes since we're in subprocess and may not have exact type
        if hasattr(event, "dataframe") and hasattr(event, "current_date"):
            # Process the data in separate process
            date_slice = event.dataframe.loc[: event.current_date]
            rows_processed = len(date_slice)
            return rows_processed
        else:
            raise ValueError("Invalid event - missing dataframe or current_date attributes")
