"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich

  Project : basefunctions

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  Simple HTTP event handler - one job: make HTTP requests

  Log:
  v1.0 : Initial implementation
  v1.1 : Updated to return EventResult instead of tuple
  v1.2 : Return response content instead of response object
=============================================================================
"""

from __future__ import annotations

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import requests
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


class HttpClientHandler(basefunctions.EventHandler):
    """
    Simple HTTP request handler.

    Event data: {"url": "https://api.com", "method": "GET"}  # method optional
    Returns: EventResult with HTTP response content or error message
    """

    execution_mode = basefunctions.EXECUTION_MODE_THREAD

    def handle(
        self,
        event: basefunctions.Event,
        context: basefunctions.EventContext | None = None,
    ) -> basefunctions.EventResult:
        """
        Make HTTP request from event data.

        Parameters
        ----------
        event : basefunctions.Event
            Event with URL and optional method
        context : Optional[basefunctions.EventContext], optional
            Event context (unused)

        Returns
        -------
        basefunctions.EventResult
            EventResult with success flag and response content or error
        """
        try:
            # Get URL
            url = event.event_data.get("url")
            if not url:
                return basefunctions.EventResult.business_result(event.event_id, False, "Missing URL")

            # Get method (default GET)
            method = event.event_data.get("method", "GET").upper()

            # Make request
            response = requests.request(method, url, timeout=25)
            response.raise_for_status()

            # Return response content (text), not the response object
            return basefunctions.EventResult.business_result(event.event_id, True, response.text)

        except requests.exceptions.RequestException as e:
            return basefunctions.EventResult.business_result(event.event_id, False, f"HTTP error: {str(e)}")
        except Exception as e:
            return basefunctions.EventResult.exception_result(event.event_id, e)


# Registration
def register_http_handlers() -> None:
    """Register HTTP handler with EventFactory."""
    factory = basefunctions.EventFactory()
    factory.register_event_type("http_request", HttpClientHandler)
