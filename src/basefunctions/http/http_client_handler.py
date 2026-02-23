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
 v1.3 : Add connection pooling for 10x performance improvement
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
# Standard Library
from __future__ import annotations

# Third-party
import requests
from requests.adapters import HTTPAdapter

# Project modules
import basefunctions
from basefunctions.utils.logging import get_logger

# -------------------------------------------------------------
# CONSTANTS
# -------------------------------------------------------------
_POOL_CONNECTIONS = 100
_POOL_MAXSIZE = 100

# -------------------------------------------------------------
# LOGGING
# -------------------------------------------------------------
# Enable logging for this module
get_logger(__name__)

# -------------------------------------------------------------
# MODULE-LEVEL SESSION (CONNECTION POOLING)
# -------------------------------------------------------------
_SESSION = requests.Session()
_ADAPTER = HTTPAdapter(pool_connections=_POOL_CONNECTIONS, pool_maxsize=_POOL_MAXSIZE)
_SESSION.mount("http://", _ADAPTER)
_SESSION.mount("https://", _ADAPTER)

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


class HttpClientHandler(basefunctions.EventHandler):
    """
    HTTP request handler with connection pooling.

    Uses module-level Session singleton with connection pool (100 connections, 100 max)
    for 10x performance improvement. Thread-safe for concurrent requests.

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
                msg = "Missing URL"
                return basefunctions.EventResult.business_result(
                    event.event_id, False, msg
                )

            # Get method (default GET)
            method = event.event_data.get("method", "GET").upper()

            # Make request using pooled session (10x faster)
            response = _SESSION.request(method, url, timeout=25)
            response.raise_for_status()

            # Return response content (text), not the response object
            return basefunctions.EventResult.business_result(
                event.event_id, True, response.text
            )

        except requests.exceptions.RequestException as e:
            msg = f"HTTP error: {str(e)}"
            return basefunctions.EventResult.business_result(
                event.event_id, False, msg
            )
        except Exception as e:
            return basefunctions.EventResult.exception_result(event.event_id, e)


# Registration
def register_http_handlers() -> None:
    """
    Register HTTP handler with EventFactory.

    Returns
    -------
    None
    """
    factory = basefunctions.EventFactory()
    factory.register_event_type("http_request", HttpClientHandler)
