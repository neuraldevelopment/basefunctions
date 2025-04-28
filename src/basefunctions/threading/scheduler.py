"""
=============================================================================

  Licensed Materials, Property of Ralph Vogl, Munich

  Project : unified_task_pool

  Copyright (c) by Ralph Vogl

  All rights reserved.

  Description:

  Scheduler class for delayed and recurring task execution within
  the unified task execution system.

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import threading
import heapq
import time


# -------------------------------------------------------------
# CLASS DEFINITIONS
# -------------------------------------------------------------


class Scheduler:
    """
    A scheduler for delayed and recurring task execution.
    """

    def __init__(self, unified_pool):
        self.unified_pool = unified_pool
        self.scheduled_tasks = []
        self.lock = threading.Lock()
        self.running = True
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()

    def schedule(self, msg_type, content, delay=0, every=None, priority=100, **kwargs):
        """
        Schedules a new task for execution.

        Parameters:
            msg_type (str): The message type to submit.
            content (Any): The task payload.
            delay (int): Delay before first execution in seconds.
            every (int, optional): Recurrence interval in seconds.
            priority (int): Task priority.
            kwargs: Additional parameters for the task.
        """
        run_at = time.time() + delay
        task = (run_at, msg_type, content, every, priority, kwargs)
        with self.lock:
            heapq.heappush(self.scheduled_tasks, task)

    def _worker(self):
        """
        Internal scheduler worker thread for executing scheduled tasks.
        """
        while self.running:
            now = time.time()
            with self.lock:
                while self.scheduled_tasks and self.scheduled_tasks[0][0] <= now:
                    run_at, msg_type, content, every, priority, kwargs = heapq.heappop(
                        self.scheduled_tasks
                    )
                    self.unified_pool.submit_message(
                        msg_type, content, priority=priority, **kwargs
                    )
                    if every:
                        next_run = run_at + every
                        heapq.heappush(
                            self.scheduled_tasks,
                            (next_run, msg_type, content, every, priority, kwargs),
                        )
            time.sleep(0.5)

    def stop(self):
        """
        Stops the scheduler thread gracefully.
        """
        self.running = False
        self.thread.join()
