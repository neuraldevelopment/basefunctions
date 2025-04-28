"""
=============================================================================

  Licensed Materials, Property of [Dein Name] - UnifiedTaskPool

  Project : UnifiedTaskPool

  Copyright (c) 2025

  All rights reserved.

  Description:

  Implements core task messaging and result structures.

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional


# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------


@dataclass(order=True)
class TaskMessage:
    """
    Represents a message to be processed by the task pool.
    """

    priority: int
    msg_type: str = field(compare=False)
    content: Any = field(compare=False)
    retry: int = field(default=3, compare=False)
    timeout: int = field(default=5, compare=False)
    abort_on_error: bool = field(default=False, compare=False)
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()), compare=False)
    delay_until: Optional[float] = field(default=None, compare=False)
    on_success: Optional[str] = field(default=None, compare=False)
    on_failure: Optional[str] = field(default=None, compare=False)


@dataclass
class TaskResult:
    """
    Represents the result after processing a task message.
    """

    success: bool
    result: Any = None
    error: Optional[str] = None
    msg_type: Optional[str] = None
    task_id: Optional[str] = None
    original_message: Optional[TaskMessage] = None


# -------------------------------------------------------------
# CLASS DEFINITIONS
# -------------------------------------------------------------


class TaskHandlerInterface:
    """
    Interface class for task handlers.
    """

    msg_type: str = "default"
    run_on_own_core: bool = False

    def callable_function(self, message: TaskMessage) -> TaskResult:
        """
        Method to be implemented by concrete task handlers.
        """
        raise NotImplementedError
