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
from typing import Any
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

    def get_sync(self, url: str, **kwargs) -> Any:
        """Send HTTP GET synchronously and wait for result."""
        event = basefunctions.Event(event_type="http_request", event_data={"method": "GET", "url": url, **kwargs})
        self.event_bus.publish(event)
        self.event_bus.join()
        results = self.event_bus.get_results([event.event_id])
        
        if not results:
            raise RuntimeError("No response received for event")
        
        result = results[event.event_id]
        if not result.success:
            # Debug: Print all result attributes
            print(f"DEBUG - EventResult attributes: {dir(result)}")
            print(f"DEBUG - Success: {result.success}")
            print(f"DEBUG - Exception: {result.exception}")
            print(f"DEBUG - Data: {result.data}")
            for attr in dir(result):
                if not attr.startswith('_'):
                    print(f"DEBUG - {attr}: {getattr(result, attr, 'N/A')}")
            
            if result.exception:
                error_msg = str(result.exception)
            elif hasattr(result, 'message') and result.message:
                error_msg = result.message
            elif hasattr(result, 'data') and result.data:
                error_msg = str(result.data)
            else:
                error_msg = f"HTTP request failed for URL: {url}"
            raise RuntimeError(error_msg)
        return result.data

    def get_async(self, url: str, **kwargs) -> str:
        """Send HTTP GET asynchronously and return event_id."""
        event = basefunctions.Event(event_type="http_request", event_data={"method": "GET", "url": url, **kwargs})
        self.event_bus.publish(event)
        return event.event_id

    def get(self, url: str, **kwargs) -> Any:
        """Synchronous alias for backward compatibility."""
        return self.get_sync(url, **kwargs)