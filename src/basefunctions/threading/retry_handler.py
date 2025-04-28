"""
=============================================================================

  Licensed Materials, Property of Ralph Vogl, Munich

  Project : unified_task_pool

  Copyright (c) by Ralph Vogl

  All rights reserved.

  Description:

  Retry handler class providing retry logic with exponential backoff
  for failed task executions within the unified task execution system.

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import time
import random


# -------------------------------------------------------------
# CLASS DEFINITIONS
# -------------------------------------------------------------


class RetryHandler:
    """
    Handles task retries with exponential backoff on failure.
    """

    def __init__(self, unified_pool):
        self.unified_pool = unified_pool

    def submit_with_retry(self, message, result_handler=None):
        """
        Wraps a result handler with retry logic for a given message.

        Parameters:
            message (TaskMessage): The task message to manage retries for.
            result_handler (Callable, optional): Final result callback.

        Returns:
            Callable: The wrapped result handler.
        """
        retries_left = message.retry
        backoff = 1

        def inner_handler(result):
            nonlocal retries_left, backoff

            if result.success:
                if result_handler:
                    result_handler(result)
            else:
                if retries_left > 0:
                    retries_left -= 1
                    sleep_time = backoff * (2 ** (message.retry - retries_left))
                    sleep_time = min(sleep_time, 30)
                    print(
                        f"[Retry] Task {message.msg_type} failed, retrying in {sleep_time:.1f}s..."
                    )
                    time.sleep(sleep_time + random.uniform(0, 0.5))
                    self.unified_pool.submit_message(
                        message.msg_type,
                        message.content,
                        priority=message.priority,
                        retry=retries_left,
                        timeout=message.timeout,
                        abort_on_error=message.abort_on_error,
                        on_success=message.on_success,
                        on_failure=message.on_failure,
                    )
                else:
                    if result_handler:
                        result_handler(result)

        return inner_handler
