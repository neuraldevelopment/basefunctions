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
import time
import logging
from typing import Optional, Any, Tuple
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


class OHLCVDataEvent(basefunctions.Event):
    """Event containing OHLCV data for a specific ticker and date."""

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
        # Use standard Event constructor with data dictionary
        super().__init__(
            type="ohlcv_data",
            data={"dataframe": dataframe, "ticker_id": ticker_id, "current_date": current_date},
        )


class OHLCVSyncHandler(basefunctions.EventHandler):
    """Synchronous handler for OHLCV data events."""

    execution_mode = basefunctions.EXECUTION_MODE_SYNC

    def __init__(self):
        """Initialize the handler."""
        self.processed_count = 0
        self.total_rows_processed = 0

    def handle(
        self, event: basefunctions.Event, context: Optional[basefunctions.EventContext] = None
    ) -> Tuple[bool, Any]:
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
        Tuple[bool, Any]
            Success flag and row count
        """
        try:
            if event.type == "ohlcv_data":
                # Access data from event.data dictionary
                dataframe = event.data.get("dataframe")
                current_date = event.data.get("current_date")

                if dataframe is None or current_date is None:
                    return False, "Missing dataframe or current_date in event data"

                date_slice = dataframe.loc[:current_date]
                rows_processed = len(date_slice)
                self.total_rows_processed += rows_processed
                self.processed_count += 1
                return True, rows_processed
            else:
                return False, f"Invalid event type - expected ohlcv_data, got {event.type}"
        except Exception as e:
            return False, str(e)


class OHLCVThreadHandler(basefunctions.EventHandler):
    """Thread-based handler for OHLCV data events."""

    execution_mode = basefunctions.EXECUTION_MODE_THREAD

    def handle(
        self, event: basefunctions.Event, context: Optional[basefunctions.EventContext] = None
    ) -> Tuple[bool, Any]:
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
        Tuple[bool, Any]
            Success flag and row count
        """
        try:
            if event.type == "ohlcv_data":
                # Access thread local data for stats
                if context and context.thread_local_data:
                    if not hasattr(context.thread_local_data, "processed_count"):
                        context.thread_local_data.processed_count = 0
                        context.thread_local_data.total_rows_processed = 0

                    # Access data from event.data dictionary
                    dataframe = event.data.get("dataframe")
                    current_date = event.data.get("current_date")

                    if dataframe is None or current_date is None:
                        return False, "Missing dataframe or current_date in event data"

                    # Process the data
                    date_slice = dataframe.loc[:current_date]
                    rows_processed = len(date_slice)

                    # Update thread local stats
                    context.thread_local_data.processed_count += 1
                    context.thread_local_data.total_rows_processed += rows_processed

                    return True, rows_processed
                else:
                    # Fallback if no context
                    dataframe = event.data.get("dataframe")
                    current_date = event.data.get("current_date")

                    if dataframe is None or current_date is None:
                        return False, "Missing dataframe or current_date in event data"

                    date_slice = dataframe.loc[:current_date]
                    return True, len(date_slice)
            else:
                return False, f"Invalid event type - expected ohlcv_data, got {event.type}"
        except Exception as e:
            return False, str(e)


class OHLCVCoreletHandler(basefunctions.EventHandler):
    """Corelet-based handler for OHLCV data events."""

    execution_mode = basefunctions.EXECUTION_MODE_CORELET

    def handle(self, event, context=None) -> Tuple[bool, Any]:
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
        Tuple[bool, Any]
            Success flag and row count
        """
        try:
            if event.type == "ohlcv_data":
                dataframe = event.data.get("dataframe")
                current_date = event.data.get("current_date")

                if dataframe is None or current_date is None:
                    return False, "Missing dataframe or current_date in event data"

                date_slice = dataframe.loc[:current_date]
                rows_processed = len(date_slice)
                return True, rows_processed
            else:
                return False, f"Invalid event type - expected ohlcv_data, got {event.type}"
        except Exception as e:
            return False, str(e)
