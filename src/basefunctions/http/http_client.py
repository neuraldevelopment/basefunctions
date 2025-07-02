"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich

  Project : basefunctions

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  Simple HTTP client

  Log:
  v1.0 : Initial implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
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

    def get_sync(self, url: str, **kwargs) -> any:
        """Send HTTP GET synchronously and wait for result."""
        event = basefunctions.Event(type="http_request", data={"method": "GET", "url": url, **kwargs})
        self.event_bus.publish(event)
        self.event_bus.join()
        response_event = self.event_bus.get_response(event.event_id)
        if not response_event:
            raise RuntimeError("No response received for event")
        if response_event.type == "error":
            raise RuntimeError(response_event.data.get("error"))
        return response_event.data["result_data"]

    def get_async(self, url: str, **kwargs) -> str:
        """Send HTTP GET asynchronously and return event_id."""
        event = basefunctions.Event(type="http_request", data={"method": "GET", "url": url, **kwargs})
        self.event_bus.publish(event)
        return event.event_id

    def get(self, url: str, **kwargs) -> any:
        """Synchronous alias for backward compatibility."""
        return self.get_sync(url, **kwargs)
