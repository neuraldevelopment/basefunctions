"""
=============================================================================

  Licensed Materials, Property of Ralph Vogl, Munich

  Project : basefunctions

  Copyright (c) 2025

  All rights reserved.

  Description:

  Implements a pure thread-based task pool with priority handling.

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import threading
import queue
import time


# -------------------------------------------------------------
# CLASS DEFINITIONS
# -------------------------------------------------------------


class ThreadTaskPool:
    """
    A thread-based task pool that processes prioritized tasks.
    """

    def __init__(self, num_threads=4):
        self.input_queue = queue.PriorityQueue()
        self.result_handlers = {}
        self.handler_map = {}
        self.threads = []
        self.running = True
        self.paused = threading.Event()
        self.paused.set()

        for _ in range(num_threads):
            t = threading.Thread(target=self._worker, daemon=True)
            t.start()
            self.threads.append(t)

    def register_handler(self, handler):
        """
        Registers a task handler.
        """
        self.handler_map[handler._msg_type] = handler

    def submit_message(self, message, result_handler=None):
        """
        Submits a message for execution.
        """
        self.result_handlers.setdefault(message.task_id, []).append(result_handler)
        self.input_queue.put(message)

    def _worker(self):
        """
        Internal worker method.
        """
        while self.running:
            self.paused.wait()
            message = self.input_queue.get()
            if message == "##STOP##":
                break

            if message.delay_until and time.time() < message.delay_until:
                time.sleep(message.delay_until - time.time())

            handler = self.handler_map.get(message.msg_type)
            try:
                result = handler(message)
                result.msg_type = message.msg_type
                result.task_id = message.task_id
                result.original_message = message
            except Exception as e:
                result = type(
                    "TaskResult",
                    (object,),
                    {
                        "success": False,
                        "error": str(e),
                        "msg_type": message.msg_type,
                        "task_id": message.task_id,
                        "original_message": message,
                    },
                )()

            handlers = self.result_handlers.get(message.task_id, [])
            for handler_cb in handlers:
                if handler_cb:
                    try:
                        handler_cb(result)
                    except Exception:
                        pass

            self.input_queue.task_done()

    def pause(self):
        """
        Pauses the pool.
        """
        self.paused.clear()

    def resume(self):
        """
        Resumes the pool.
        """
        self.paused.set()

    def stop(self):
        """
        Stops the pool.
        """
        self.running = False
        for _ in self.threads:
            self.input_queue.put("##STOP##")
        for t in self.threads:
            t.join()
