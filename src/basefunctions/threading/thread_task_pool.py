"""
=============================================================================

  Licensed Materials, Property of [Dein Name] - UnifiedTaskPool

  Project : UnifiedTaskPool

  Copyright (c) 2025

  All rights reserved.

  Description:

  Implements thread-based task pool with priority handling.

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
    A thread-based task pool that processes prioritized messages.
    """

    def __init__(self, num_threads=4):
        self.input_queue = queue.PriorityQueue()
        self.result_handlers = {}
        self.handler_map = {}
        self.threads = []
        self.running = True
        self.paused = threading.Event()
        self.paused.set()  # Start unpaused

        for _ in range(num_threads):
            t = threading.Thread(target=self._worker, daemon=True)
            t.start()
            self.threads.append(t)

    def register_handler(self, handler):
        """
        Registers a handler for a specific message type.
        """
        self.handler_map[handler.msg_type] = handler

    def submit_message(self, message, result_handler=None):
        """
        Submits a message to the thread pool.
        """
        self.result_handlers.setdefault(message.task_id, []).append(result_handler)
        self.input_queue.put(message)

    def _worker(self):
        """
        Worker method to process tasks from the input queue.
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
                result = handler.callable_function(message)
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

            if result.success and message.on_success:
                self.submit_message(
                    type(
                        "TaskMessage",
                        (object,),
                        {
                            "priority": 50,
                            "msg_type": message.on_success,
                            "content": {"previous_result": result.result},
                            "retry": 3,
                            "timeout": 5,
                            "abort_on_error": False,
                            "task_id": "auto-" + str(time.time()),
                        },
                    )()
                )
            elif not result.success and message.on_failure:
                self.submit_message(
                    type(
                        "TaskMessage",
                        (object,),
                        {
                            "priority": 50,
                            "msg_type": message.on_failure,
                            "content": {"error": result.error},
                            "retry": 3,
                            "timeout": 5,
                            "abort_on_error": False,
                            "task_id": "auto-" + str(time.time()),
                        },
                    )()
                )

            handlers = self.result_handlers.get(message.task_id, [])
            for handler_cb in handlers:
                if handler_cb:
                    try:
                        handler_cb(result)
                    except Exception as e:
                        print(f"[ThreadPool] Result handler exception: {e}")

            self.input_queue.task_done()

    def pause(self):
        """
        Pauses the thread pool.
        """
        self.paused.clear()

    def resume(self):
        """
        Resumes the thread pool.
        """
        self.paused.set()

    def stop(self):
        """
        Stops the thread pool and waits for all threads to terminate.
        """
        self.running = False
        for _ in self.threads:
            self.input_queue.put("##STOP##")
        for t in self.threads:
            t.join()
