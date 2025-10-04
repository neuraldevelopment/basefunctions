"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich

 Project : basefunctions

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 Simple HTTP client with automatic event ID management

 Log:
 v1.0 : Initial implementation
 v1.1 : Added get_results for symmetric async/sync API
 v1.2 : Automatic event ID tracking, removed get() alias
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Any, List, Dict, Optional
import basefunctions

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# LOGGING INITIALIZE
# -------------------------------------------------------------
# Enable logging for this module
basefunctions.setup_logger(__name__)


# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------
class HttpClient:

    def __init__(self):
        self.event_bus = basefunctions.EventBus()
        self._pending_event_ids = []

    def get_sync(self, url: str, **kwargs) -> Any:
        """
        Send HTTP GET synchronously and wait for result.

        Parameters
        ----------
        url : str
            Target URL for GET request
        **kwargs
            Additional parameters passed to event_data

        Returns
        -------
        Any
            HTTP response content

        Raises
        ------
        RuntimeError
            If request failed or no response received
        """
        event = basefunctions.Event(event_type="http_request", event_data={"method": "GET", "url": url, **kwargs})
        self.event_bus.publish(event)
        self.event_bus.join()
        results = self.event_bus.get_results([event.event_id])

        if not results:
            raise RuntimeError("No response received for event")

        result = results[event.event_id]
        if not result.success:
            if result.exception:
                error_msg = str(result.exception)
            elif hasattr(result, "data") and result.data:
                error_msg = str(result.data)
            else:
                error_msg = f"HTTP request failed for URL: {url}"
            raise RuntimeError(error_msg)
        return result.data

    def get_async(self, url: str, **kwargs) -> str:
        """
        Send HTTP GET asynchronously and return event_id.

        Parameters
        ----------
        url : str
            Target URL for GET request
        **kwargs
            Additional parameters passed to event_data

        Returns
        -------
        str
            Event ID for result tracking
        """
        event = basefunctions.Event(event_type="http_request", event_data={"method": "GET", "url": url, **kwargs})
        self.event_bus.publish(event)
        self._pending_event_ids.append(event.event_id)
        return event.event_id

    def get_pending_ids(self) -> List[str]:
        """
        Get list of pending event IDs.

        Returns
        -------
        List[str]
            Copy of pending event IDs list
        """
        return self._pending_event_ids.copy()

    def set_pending_ids(self, event_ids: List[str]) -> None:
        """
        Set pending event IDs list.

        Parameters
        ----------
        event_ids : List[str]
            New list of event IDs to track
        """
        self._pending_event_ids = event_ids.copy()

    def get_results(self, event_ids: Optional[List[str]] = None, join_before: bool = True) -> Dict[str, Any]:
        """
        Get results from async requests with automatic ID management.

        Parameters
        ----------
        event_ids : Optional[List[str]], optional
            List of specific event_ids to retrieve. If None, retrieves all pending events.
        join_before : bool, optional
            Wait for all pending events before retrieving results. Default is True.

        Returns
        -------
        Dict[str, Any]
            Dictionary mapping event_ids to response data.

        Raises
        ------
        RuntimeError
            If request failed or response is invalid.
        """
        # Use pending list if no specific IDs provided
        ids_to_fetch = event_ids if event_ids is not None else self._pending_event_ids.copy()

        if not ids_to_fetch:
            return {}

        results = self.event_bus.get_results(event_ids=ids_to_fetch, join_before=join_before)

        # Remove fetched IDs from pending list
        for event_id in ids_to_fetch:
            if event_id in self._pending_event_ids:
                self._pending_event_ids.remove(event_id)

        # Transform EventResult to response data
        response_data = {}
        for event_id, result in results.items():
            if not result.success:
                if result.exception:
                    error_msg = str(result.exception)
                elif hasattr(result, "data") and result.data:
                    error_msg = str(result.data)
                else:
                    error_msg = f"HTTP request failed for event: {event_id}"
                raise RuntimeError(error_msg)
            response_data[event_id] = result.data

        return response_data
