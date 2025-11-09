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
 v1.3 : Robust error handling with metadata structure
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Any, List, Dict, Optional
from datetime import datetime
from basefunctions.utils.logging import setup_logger
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
setup_logger(__name__)


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
            Dictionary with structure:
            {
                'data': {event_id: response_data, ...},
                'metadata': {
                    'total_requested': int,
                    'successful': int,
                    'failed': int,
                    'event_ids': {event_id: 'success'|'failed', ...},
                    'timestamp': str
                },
                'errors': {event_id: error_message, ...}
            }
        """
        # Use pending list if no specific IDs provided
        ids_to_fetch = event_ids if event_ids is not None else self._pending_event_ids.copy()

        if not ids_to_fetch:
            return {
                "data": {},
                "metadata": {
                    "total_requested": 0,
                    "successful": 0,
                    "failed": 0,
                    "event_ids": {},
                    "timestamp": datetime.now().isoformat(),
                },
                "errors": {},
            }

        results = self.event_bus.get_results(event_ids=ids_to_fetch, join_before=join_before)

        # Remove fetched IDs from pending list
        self._pending_event_ids = [eid for eid in self._pending_event_ids if eid not in ids_to_fetch]

        # Build result structure
        data = {}
        errors = {}
        event_status = {}
        successful = 0
        failed = 0

        for event_id in ids_to_fetch:
            result = results.get(event_id)

            if result and result.success:
                data[event_id] = result.data
                event_status[event_id] = "success"
                successful += 1
            else:
                # Extract error message
                if result and result.exception:
                    error_msg = str(result.exception)
                elif result and hasattr(result, "data") and result.data:
                    error_msg = str(result.data)
                elif result:
                    error_msg = f"HTTP request failed for event: {event_id}"
                else:
                    error_msg = "No result received"

                errors[event_id] = error_msg
                event_status[event_id] = "failed"
                failed += 1

        return {
            "data": data,
            "metadata": {
                "total_requested": len(ids_to_fetch),
                "successful": successful,
                "failed": failed,
                "event_ids": event_status,
                "timestamp": datetime.now().isoformat(),
            },
            "errors": errors,
        }
