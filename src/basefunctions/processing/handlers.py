"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment , Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Handler implementations for the unified task pool system
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Any, Tuple

from .interfaces import TaskContext, TaskletRequestInterface
from .message_types import UnifiedTaskPoolMessage


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
class DefaultTaskHandler(TaskletRequestInterface):
    """
    Default implementation of TaskletRequestInterface.
    Used when no specific handler is registered for a message type.
    """

    def process_request(
        self, context: TaskContext, message: UnifiedTaskPoolMessage
    ) -> Tuple[bool, Any]:
        """
        Default implementation that returns an error.

        Parameters
        ----------
        context : TaskContext
            Context containing thread-local storage and queues.
        message : UnifiedTaskPoolMessage
            Message to process.

        Returns
        -------
        Tuple[bool, Any]
            Always returns (False, RuntimeError)
        """
        return False, RuntimeError(
            f"No handler implemented for message type: {message.message_type}"
        )
