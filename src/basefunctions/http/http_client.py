"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich
  Project : basefunctions
  Copyright (c) by neuraldevelopment
  All rights reserved.
  Description:
  Context-aware HTTP client with EventBus integration and standalone resilience
 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import threading
import time
import requests
from typing import Dict, Any, Optional, Union
import basefunctions

# -------------------------------------------------------------
# DEFINITIONS REGISTRY
# -------------------------------------------------------------

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------
DEFAULT_TIMEOUT = 30
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_FACTOR = 2
DEFAULT_CONNECT_TIMEOUT = 5
DEFAULT_READ_TIMEOUT = 30

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


class HttpClientError(Exception):
    """Base exception for HTTP client operations."""

    pass


class HttpTimeoutError(HttpClientError):
    """HTTP request timeout error."""

    pass


class HttpRetryExhaustedError(HttpClientError):
    """HTTP retries exhausted error."""

    pass


class HttpClient:
    """
    Context-aware HTTP client with automatic EventBus integration.

    When used within EventBus threads, leverages EventBus timeout and retry mechanisms.
    When used standalone, provides own resilience features.
    """

    def __init__(
        self,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
        connect_timeout: int = DEFAULT_CONNECT_TIMEOUT,
        read_timeout: int = DEFAULT_READ_TIMEOUT,
    ):
        """
        Initialize HTTP client with standalone resilience configuration.

        Parameters
        ----------
        timeout : int, optional
            Total request timeout in seconds, by default 30
        max_retries : int, optional
            Maximum retry attempts for failed requests, by default 3
        backoff_factor : float, optional
            Exponential backoff factor for retries, by default 2
        connect_timeout : int, optional
            Connection timeout in seconds, by default 5
        read_timeout : int, optional
            Read timeout in seconds, by default 30
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout
        self.logger = basefunctions.get_logger(__name__)

        # Session for connection pooling
        self.session = requests.Session()

    def get(self, url: str, **kwargs) -> requests.Response:
        """
        Perform HTTP GET request with context-aware resilience.

        Parameters
        ----------
        url : str
            URL to request
        **kwargs
            Additional arguments passed to requests

        Returns
        -------
        requests.Response
            HTTP response object

        Raises
        ------
        HttpClientError
            If request fails after all retries
        """
        return self._request("GET", url, **kwargs)

    def post(self, url: str, **kwargs) -> requests.Response:
        """
        Perform HTTP POST request with context-aware resilience.

        Parameters
        ----------
        url : str
            URL to request
        **kwargs
            Additional arguments passed to requests

        Returns
        -------
        requests.Response
            HTTP response object

        Raises
        ------
        HttpClientError
            If request fails after all retries
        """
        return self._request("POST", url, **kwargs)

    def put(self, url: str, **kwargs) -> requests.Response:
        """
        Perform HTTP PUT request with context-aware resilience.

        Parameters
        ----------
        url : str
            URL to request
        **kwargs
            Additional arguments passed to requests

        Returns
        -------
        requests.Response
            HTTP response object

        Raises
        ------
        HttpClientError
            If request fails after all retries
        """
        return self._request("PUT", url, **kwargs)

    def delete(self, url: str, **kwargs) -> requests.Response:
        """
        Perform HTTP DELETE request with context-aware resilience.

        Parameters
        ----------
        url : str
            URL to request
        **kwargs
            Additional arguments passed to requests

        Returns
        -------
        requests.Response
            HTTP response object

        Raises
        ------
        HttpClientError
            If request fails after all retries
        """
        return self._request("DELETE", url, **kwargs)

    def request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Perform HTTP request with specified method and context-aware resilience.

        Parameters
        ----------
        method : str
            HTTP method (GET, POST, PUT, DELETE, etc.)
        url : str
            URL to request
        **kwargs
            Additional arguments passed to requests

        Returns
        -------
        requests.Response
            HTTP response object

        Raises
        ------
        HttpClientError
            If request fails after all retries
        """
        return self._request(method, url, **kwargs)

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Internal request method with context detection and resilience.

        Parameters
        ----------
        method : str
            HTTP method
        url : str
            URL to request
        **kwargs
            Additional arguments passed to requests

        Returns
        -------
        requests.Response
            HTTP response object

        Raises
        ------
        HttpClientError
            If request fails
        """
        if self._is_in_eventbus_context():
            # EventBus handles timeout and retry - use lean implementation
            return self._lean_request(method, url, **kwargs)
        else:
            # Standalone usage - use robust implementation with own resilience
            return self._robust_request(method, url, **kwargs)

    def _is_in_eventbus_context(self) -> bool:
        """
        Check if running within EventBus worker thread context.

        Returns
        -------
        bool
            True if in EventBus context, False otherwise
        """
        try:
            thread_local = threading.local()
            return getattr(thread_local, "eventbus_context", False)
        except Exception:
            return False

    def _lean_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Lean HTTP request for EventBus context (no own timeout/retry).

        Parameters
        ----------
        method : str
            HTTP method
        url : str
            URL to request
        **kwargs
            Additional arguments passed to requests

        Returns
        -------
        requests.Response
            HTTP response object

        Raises
        ------
        HttpClientError
            If request fails
        """
        try:
            # Set reasonable timeouts for EventBus context
            if "timeout" not in kwargs:
                kwargs["timeout"] = (self.connect_timeout, self.read_timeout)

            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response

        except requests.exceptions.Timeout as e:
            raise HttpTimeoutError(f"HTTP {method} timeout for {url}: {str(e)}") from e
        except requests.exceptions.RequestException as e:
            raise HttpClientError(f"HTTP {method} failed for {url}: {str(e)}") from e

    def _robust_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Robust HTTP request for standalone usage (with own timeout/retry).

        Parameters
        ----------
        method : str
            HTTP method
        url : str
            URL to request
        **kwargs
            Additional arguments passed to requests

        Returns
        -------
        requests.Response
            HTTP response object

        Raises
        ------
        HttpClientError
            If request fails after all retries
        """
        last_exception = None

        for attempt in range(self.max_retries + 1):  # +1 for initial attempt
            try:
                # Set timeout if not provided
                if "timeout" not in kwargs:
                    kwargs["timeout"] = (self.connect_timeout, self.read_timeout)

                # Make request
                response = self.session.request(method, url, **kwargs)
                response.raise_for_status()

                if attempt > 0:
                    self.logger.info(f"HTTP {method} {url} succeeded on attempt {attempt + 1}")

                return response

            except (
                requests.exceptions.Timeout,
                requests.exceptions.ConnectionError,
                requests.exceptions.HTTPError,
            ) as e:
                last_exception = e

                # Check if we should retry
                if not self._should_retry(e, attempt):
                    break

                # Calculate backoff delay
                if attempt < self.max_retries:
                    delay = self.backoff_factor**attempt
                    self.logger.warning(
                        f"HTTP {method} {url} failed on attempt {attempt + 1}, " f"retrying in {delay}s: {str(e)}"
                    )
                    time.sleep(delay)

            except requests.exceptions.RequestException as e:
                # Non-retryable error
                raise HttpClientError(f"HTTP {method} failed for {url}: {str(e)}") from e

        # All retries exhausted
        raise HttpRetryExhaustedError(
            f"HTTP {method} {url} failed after {self.max_retries + 1} attempts: {str(last_exception)}"
        ) from last_exception

    def _should_retry(self, exception: Exception, attempt: int) -> bool:
        """
        Determine if request should be retried based on exception type and attempt count.

        Parameters
        ----------
        exception : Exception
            Exception that occurred
        attempt : int
            Current attempt number (0-based)

        Returns
        -------
        bool
            True if should retry, False otherwise
        """
        if attempt >= self.max_retries:
            return False

        # Retry on timeout and connection errors
        if isinstance(exception, (requests.exceptions.Timeout, requests.exceptions.ConnectionError)):
            return True

        # Retry on specific HTTP status codes
        if isinstance(exception, requests.exceptions.HTTPError):
            if hasattr(exception, "response") and exception.response is not None:
                status_code = exception.response.status_code
                # Retry on server errors (500-599) but not client errors (400-499)
                return 500 <= status_code < 600

        return False

    def close(self) -> None:
        """Close the underlying session and cleanup resources."""
        if self.session:
            self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def get_stats(self) -> Dict[str, Any]:
        """
        Get HTTP client statistics and configuration.

        Returns
        -------
        Dict[str, Any]
            Client statistics and configuration
        """
        return {
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "backoff_factor": self.backoff_factor,
            "connect_timeout": self.connect_timeout,
            "read_timeout": self.read_timeout,
            "in_eventbus_context": self._is_in_eventbus_context(),
        }
