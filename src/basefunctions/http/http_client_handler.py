"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich
  Project : basefunctions
  Copyright (c) by neuraldevelopment
  All rights reserved.
  Description:
  EventHandler for HTTP requests with automatic EventBus integration
 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Tuple, Any, Optional, Dict
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


class HttpClientHandler(basefunctions.EventHandler):
    """
    EventHandler for HTTP requests using HttpClient with EventBus integration.

    Handles events with HTTP request data and returns response data or errors.
    Leverages EventBus timeout and retry mechanisms automatically.
    """

    execution_mode = basefunctions.EXECUTION_MODE_THREAD

    def __init__(self):
        """Initialize HTTP client handler with shared HttpClient instance."""
        self.http_client = basefunctions.HttpClient()
        self.logger = basefunctions.get_logger(__name__)

    def handle(
        self,
        event: basefunctions.Event,
        context: Optional[basefunctions.EventContext] = None,
    ) -> Tuple[bool, Any]:
        """
        Handle HTTP request event.

        Expected event.data format:
        {
            "url": "https://api.example.com/data",
            "method": "GET",  # Optional, defaults to GET
            "headers": {...},  # Optional
            "params": {...},   # Optional query parameters
            "json": {...},     # Optional JSON body for POST/PUT
            "data": {...},     # Optional form data
            "timeout": 30,     # Optional, overrides client default
            "follow_redirects": True,  # Optional, defaults to True
        }

        Parameters
        ----------
        event : basefunctions.Event
            Event containing HTTP request data
        context : Optional[basefunctions.EventContext], optional
            Event execution context

        Returns
        -------
        Tuple[bool, Any]
            (success, response_data) where response_data contains:
            - On success: {"status_code": int, "headers": dict, "json": dict/list, "text": str}
            - On failure: error message string
        """
        try:
            # Validate event data
            if not event.data or not isinstance(event.data, dict):
                return (False, "Invalid event data: expected dictionary with HTTP request parameters")

            url = event.data.get("url")
            if not url:
                return (False, "Missing required parameter: url")

            # Extract HTTP parameters
            method = event.data.get("method", "GET").upper()
            headers = event.data.get("headers", {})
            params = event.data.get("params", {})
            json_data = event.data.get("json")
            form_data = event.data.get("data")
            timeout = event.data.get("timeout")
            follow_redirects = event.data.get("follow_redirects", True)

            # Build request kwargs
            request_kwargs = {}

            if headers:
                request_kwargs["headers"] = headers

            if params:
                request_kwargs["params"] = params

            if json_data is not None:
                request_kwargs["json"] = json_data

            if form_data is not None:
                request_kwargs["data"] = form_data

            if timeout is not None:
                request_kwargs["timeout"] = timeout

            request_kwargs["allow_redirects"] = follow_redirects

            # Log request
            self.logger.debug(f"Making HTTP {method} request to {url}")

            # Make HTTP request (EventBus handles timeout/retry)
            response = self.http_client.request(method, url, **request_kwargs)

            # Prepare response data
            response_data = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "url": response.url,
                "elapsed_ms": int(response.elapsed.total_seconds() * 1000),
            }

            # Add response body based on content type
            content_type = response.headers.get("content-type", "").lower()

            if "application/json" in content_type:
                try:
                    response_data["json"] = response.json()
                    response_data["text"] = response.text
                except ValueError:
                    # Invalid JSON, fall back to text
                    response_data["text"] = response.text
            else:
                response_data["text"] = response.text

            self.logger.debug(
                f"HTTP {method} {url} completed: {response.status_code} " f"({response_data['elapsed_ms']}ms)"
            )

            return (True, response_data)

        except basefunctions.HttpTimeoutError as e:
            error_msg = f"HTTP request timeout: {str(e)}"
            self.logger.warning(error_msg)
            return (False, error_msg)

        except basefunctions.HttpRetryExhaustedError as e:
            error_msg = f"HTTP request failed after retries: {str(e)}"
            self.logger.warning(error_msg)
            return (False, error_msg)

        except basefunctions.HttpClientError as e:
            error_msg = f"HTTP request failed: {str(e)}"
            self.logger.warning(error_msg)
            return (False, error_msg)

        except Exception as e:
            error_msg = f"Unexpected error in HTTP request: {str(e)}"
            self.logger.error(error_msg)
            return (False, error_msg)


class HttpGetHandler(HttpClientHandler):
    """Specialized handler for HTTP GET requests."""

    def handle(
        self,
        event: basefunctions.Event,
        context: Optional[basefunctions.EventContext] = None,
    ) -> Tuple[bool, Any]:
        """
        Handle HTTP GET request event.

        Automatically sets method to GET and delegates to parent handler.
        """
        # Ensure method is GET
        if event.data is None:
            event.data = {}
        event.data["method"] = "GET"

        return super().handle(event, context)


class HttpPostHandler(HttpClientHandler):
    """Specialized handler for HTTP POST requests."""

    def handle(
        self,
        event: basefunctions.Event,
        context: Optional[basefunctions.EventContext] = None,
    ) -> Tuple[bool, Any]:
        """
        Handle HTTP POST request event.

        Automatically sets method to POST and delegates to parent handler.
        """
        # Ensure method is POST
        if event.data is None:
            event.data = {}
        event.data["method"] = "POST"

        return super().handle(event, context)


class HttpJsonApiHandler(HttpClientHandler):
    """Specialized handler for JSON API requests with common defaults."""

    def handle(
        self,
        event: basefunctions.Event,
        context: Optional[basefunctions.EventContext] = None,
    ) -> Tuple[bool, Any]:
        """
        Handle JSON API request event with sensible defaults.

        Automatically sets Content-Type and Accept headers for JSON APIs.
        """
        if event.data is None:
            event.data = {}

        # Set JSON API defaults
        headers = event.data.get("headers", {})
        headers.setdefault("Content-Type", "application/json")
        headers.setdefault("Accept", "application/json")
        event.data["headers"] = headers

        return super().handle(event, context)


# Registration helper function
def register_http_handlers() -> None:
    """
    Register all HTTP handlers with the EventFactory.

    Call this function to register HTTP event handlers:
    - "http_request": General HTTP requests
    - "http_get": HTTP GET requests
    - "http_post": HTTP POST requests
    - "http_json_api": JSON API requests
    """
    factory = basefunctions.EventFactory()

    factory.register_event_type("http_request", HttpClientHandler)
    factory.register_event_type("http_get", HttpGetHandler)
    factory.register_event_type("http_post", HttpPostHandler)
    factory.register_event_type("http_json_api", HttpJsonApiHandler)
