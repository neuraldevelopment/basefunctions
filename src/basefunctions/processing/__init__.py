"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment , Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Unified task pool package for handling both thread-based and process-based execution
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from .message_types import UnifiedTaskPoolMessage, UnifiedTaskPoolResult
from .interfaces import TaskContext, TaskletRequestInterface
from .handlers import DefaultTaskHandler
from .timer import TimerThread
from .task_pool import UnifiedTaskPool

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
__all__ = [
    "UnifiedTaskPoolMessage",
    "UnifiedTaskPoolResult",
    "TaskContext",
    "TaskletRequestInterface",
    "DefaultTaskHandler",
    "TimerThread",
    "UnifiedTaskPool",
]
