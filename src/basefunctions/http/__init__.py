"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 HTTP client with event-based request handling
 Log:
 v1.1 : Added RateLimitedHttpHandler for rate-limited requests
 v1.0 : Initial implementation
=============================================================================
"""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
from basefunctions.http.http_client import HttpClient
from basefunctions.http.http_client_handler import (
    HttpClientHandler,
    register_http_handlers,
)
from basefunctions.http.rate_limited_http_handler import RateLimitedHttpHandler

# =============================================================================
# EXPORT DEFINITIONS
# =============================================================================
__all__ = [
    "HttpClient",
    "HttpClientHandler",
    "RateLimitedHttpHandler",
    "register_http_handlers",
]
