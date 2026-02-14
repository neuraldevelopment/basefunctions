"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Event-driven messaging framework with support for synchronous,
 threaded, and corelet-based execution modes
 Log:
 v1.0 : Initial implementation
=============================================================================
"""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Event Core
from basefunctions.events.event import (
    Event,
    EXECUTION_MODE_SYNC,
    EXECUTION_MODE_THREAD,
    EXECUTION_MODE_CORELET,
    EXECUTION_MODE_CMD,
)
from basefunctions.events.event_context import EventContext
from basefunctions.events.event_handler import (
    EventHandler,
    EventResult,
    DefaultCmdHandler,
    CoreletHandle,
    CoreletForwardingHandler,
    register_internal_handlers,
)

# Event Management
from basefunctions.events.event_bus import (
    EventBus,
    DEFAULT_TIMEOUT,
    DEFAULT_RETRY_COUNT,
    DEFAULT_PRIORITY,
    INTERNAL_CMD_EXECUTION_EVENT,
    INTERNAL_CORELET_FORWARDING_EVENT,
    INTERNAL_SHUTDOWN_EVENT,
)
from basefunctions.events.event_factory import EventFactory

# Worker System
from basefunctions.events.corelet_worker import CoreletWorker, worker_main

# Timer Support
from basefunctions.events.timer_thread import TimerThread

# Rate Limiting
from basefunctions.events.rate_limiter import RateLimiter

# Event Exceptions
from basefunctions.events.event_exceptions import (
    EventValidationError,
    EventConnectionError,
    EventExecutionError,
    EventShutdownError,
    InvalidEventError,
    NoHandlerAvailableError,
)

# =============================================================================
# EXPORT DEFINITIONS
# =============================================================================
__all__ = [
    # Event Core
    "Event",
    "EventContext",
    "EventHandler",
    "EventResult",
    "DefaultCmdHandler",
    "CoreletHandle",
    "CoreletForwardingHandler",
    "register_internal_handlers",
    # Event Management
    "EventBus",
    "EventFactory",
    "DEFAULT_TIMEOUT",
    "DEFAULT_RETRY_COUNT",
    "DEFAULT_PRIORITY",
    "INTERNAL_CMD_EXECUTION_EVENT",
    "INTERNAL_CORELET_FORWARDING_EVENT",
    "INTERNAL_SHUTDOWN_EVENT",
    # Worker System
    "CoreletWorker",
    "worker_main",
    # Timer Support
    "TimerThread",
    # Rate Limiting
    "RateLimiter",
    # Event Exceptions
    "EventValidationError",
    "EventConnectionError",
    "EventExecutionError",
    "EventShutdownError",
    "InvalidEventError",
    "NoHandlerAvailableError",
    # Execution Modes
    "EXECUTION_MODE_SYNC",
    "EXECUTION_MODE_THREAD",
    "EXECUTION_MODE_CORELET",
    "EXECUTION_MODE_CMD",
]
