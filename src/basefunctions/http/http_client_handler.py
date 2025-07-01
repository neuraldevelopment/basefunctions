"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich
  Project : basefunctions
  Copyright (c) by neuraldevelopment
  All rights reserved.
  Description:
  Simple HTTP event handler - one job: make HTTP requests
 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Tuple, Any, Optional
import requests
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
# LOGGING INITIALIZE
# -------------------------------------------------------------
# Enable logging for this module
basefunctions.setup_logger(__name__)

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


class HttpClientHandler(basefunctions.EventHandler):
    """
    Simple HTTP request handler.

    Event data: {"url": "https://api.com", "method": "GET"}  # method optional
    Returns: HTTP response data or error message
    """

    execution_mode = basefunctions.EXECUTION_MODE_THREAD

    def handle(
        self,
        event: basefunctions.Event,
        context: Optional[basefunctions.EventContext] = None,
    ) -> Tuple[bool, Any]:
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
        Tuple[bool, Any]
            (success, response_data_or_error)
        """
        try:
            # Get URL
            url = event.data.get("url")
            if not url:
                return (False, "Missing URL")

            # Get method (default GET)
            method = event.data.get("method", "GET").upper()

            # Make request
            response = requests.request(method, url)
            response.raise_for_status()

            # Return response data
            return (
                True,
                {
                    "status_code": response.status_code,
                    "json": response.json() if "json" in response.headers.get("content-type", "") else None,
                    "text": response.text,
                },
            )

        except requests.exceptions.RequestException as e:
            return (False, f"HTTP error: {str(e)}")
        except Exception as e:
            return (False, f"Error: {str(e)}")


# Registration
def register_http_handlers() -> None:
    """Register HTTP handler with EventFactory."""
    factory = basefunctions.EventFactory()
    factory.register_event_type("http_request", HttpClientHandler)
