"""
=============================================================================

  Licensed Materials, Property of [Dein Name] - UnifiedTaskPool

  Project : UnifiedTaskPool

  Copyright (c) 2025

  All rights reserved.

  Description:

  Implements process-based task pool with priority handling.

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import multiprocessing
import threading
import queue
import time


# -------------------------------------------------------------
# CLASS DEFINITIONS
# -------------------------------------------------------------


class ProcessTaskPool:
    """
    A process-based task pool that processes prioritized messages.
    """

    def __init__(self, num_processes=2):
        self.input_queue = multiprocessing.Queue()
        self.output_queue = multiprocessing.Queue()
        self.handler_map = {}
        self.result_handlers = {}
        self.processes = []
        self.running = True
        self.paused = threading.Event()
        self.paused.set()

        for _ in range(num_processes):
            p = multiprocessing.Process(target=self._worker)
            p.start()
            self.processes.append(p)

        self.listener_thread = threading.Thread(target=self._result_listener, daemon=True)
        self.listener_thread.start()

    def register_handler(self, handler):
        """
        Registers a handler for a specific message type.
        """
        self.handler_map[handler.msg_type] = handler

    def submit_message(self, message, result_handler=None):
        """
        Submits a message to the process pool.
        """
        self.result_handlers.setdefault(message.task_id, []).append(result_handler)
        self.input_queue.put((message.priority, message.msg_type, message))

    def _worker(self):
        """
        Worker method to process tasks from the input queue.
        """
        tasks = []
        while self.running:
            try:
                priority, msg_type, message = self.input_queue.get(timeout=0.5)
                if msg_type == "##STOP##":
                    break
                tasks.append((priority, msg_type, message))
                tasks.sort()
            except queue.Empty:
                pass

            while tasks:
                self.paused.wait()
                priority, msg_type, message = tasks.pop(0)

                if message.delay_until and time.time() < message.delay_until:
                    time.sleep(message.delay_until - time.time())

                handler = self.handler_map.get(msg_type)
                try:
                    result = handler.callable_function(message)
                    result.msg_type = msg_type
                    result.task_id = message.task_id
                    result.original_message = message
                except Exception as e:
                    result = type(
                        "TaskResult",
                        (object,),
                        {
                            "success": False,
                            "error": str(e),
                            "msg_type": msg_type,
                            "task_id": message.task_id,
                            "original_message": message,
                        },
                    )()

                self.output_queue.put(result)

    def _result_listener(self):
        """
        Listens for results and dispatches to result handlers.
        """
        while self.running:
            try:
                result = self.output_queue.get(timeout=0.5)
                handlers = self.result_handlers.get(result.task_id, [])
                for handler_cb in handlers:
                    if handler_cb:
                        try:
                            handler_cb(result)
                        except Exception as e:
                            print(f"[ProcessPool] Result handler exception: {e}")
            except queue.Empty:
                pass

    def pause(self):
        """
        Pauses the process pool.
        """
        self.paused.clear()

    def resume(self):
        """
        Resumes the process pool.
        """
        self.paused.set()

    def stop(self):
        """
        Stops the process pool and waits for all processes to terminate.
        """
        self.running = False
        for _ in self.processes:
            self.input_queue.put((9999, "##STOP##", None))
        for p in self.processes:
            p.join()
