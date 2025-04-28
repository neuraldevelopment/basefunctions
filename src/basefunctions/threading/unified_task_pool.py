"""
=============================================================================

  Licensed Materials, Property of [Dein Name] - UnifiedTaskPool

  Project : UnifiedTaskPool

  Copyright (c) 2025

  All rights reserved.

  Description:

  Combines thread, process pools and management modules into a unified interface.

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import time
import basefunctions


# -------------------------------------------------------------
# CLASS DEFINITIONS
# -------------------------------------------------------------


class UnifiedTaskPool:
    """
    A unified task pool managing both threads and processes with advanced features.
    """

    def __init__(self, num_threads=4, num_processes=2):
        self.thread_pool = basefunctions.ThreadTaskPool(num_threads)
        self.process_pool = basefunctions.ProcessTaskPool(num_processes)
        self.scheduler = basefunctions.Scheduler(self)
        self.chainer = basefunctions.Chainer(self)
        self.retry_handler = basefunctions.RetryHandler(self)
        self.recorder = basefunctions.Recorder()
        self.inspector = basefunctions.Inspector(self)
        self.inspector.start()

        self.handler_registry = {}
        self.result_handler_registry = {}

        # Auto-register decorated handlers if they exist
        for msg_type, func in basefunctions.TASK_HANDLER_REGISTRY.items():
            self.register_handler(func)
        for msg_type, funcs in basefunctions.RESULT_HANDLER_REGISTRY.items():
            for func in funcs:
                self.register_result_handler(msg_type, func)

    def register_handler(self, handler):
        """
        Registers a task handler.
        """
        run_on_own_core = getattr(handler, "_run_on_own_core", False)
        msg_type = getattr(handler, "_msg_type", None)
        if not msg_type:
            raise ValueError("Handler must define a msg_type.")

        wrapped_handler = self._wrap_callable(handler)

        self.handler_registry[msg_type] = (wrapped_handler, run_on_own_core)
        if run_on_own_core:
            self.process_pool.register_handler(wrapped_handler)
        else:
            self.thread_pool.register_handler(wrapped_handler)

    def register_result_handler(self, msg_type, handler):
        """
        Registers a result handler for a given message type.
        """
        self.result_handler_registry.setdefault(msg_type, []).append(handler)

    def submit_message(
        self,
        msg_type,
        content,
        priority=100,
        result_handler=None,
        retry_strategy=None,
        max_retries=3,
        delay=0,
        on_success=None,
        on_failure=None,
        **kwargs,
    ):
        """
        Submits a message for processing.
        """
        if msg_type not in self.handler_registry:
            raise ValueError(f"No handler registered for msg_type: {msg_type}")

        handler, run_on_own_core = self.handler_registry[msg_type]

        delay_until = time.time() + delay if delay else None

        message = basefunctions.TaskMessage(
            msg_type=msg_type,
            content=content,
            priority=priority,
            retry=max_retries,
            delay_until=delay_until,
            on_success=on_success,
            on_failure=on_failure,
            **kwargs,
        )

        final_result_handler = self._build_final_result_handler(msg_type, result_handler)

        if retry_strategy == "backoff":
            final_result_handler = self.retry_handler.submit_with_retry(
                message, final_result_handler
            )

        if run_on_own_core:
            self.process_pool.submit_message(message, result_handler=final_result_handler)
        else:
            self.thread_pool.submit_message(message, result_handler=final_result_handler)

    def _wrap_callable(self, func):
        """
        Wraps the handler function with middlewares if any.
        """
        return apply_middlewares(func)

    def _build_final_result_handler(self, msg_type, custom_handler):
        """
        Combines the built-in and user-provided result handlers.
        """
        built_in_handlers = self.result_handler_registry.get(msg_type, [])

        def handler_wrapper(result):
            if custom_handler:
                custom_handler(result)
            for h in built_in_handlers:
                try:
                    h(result)
                except Exception as e:
                    print(f"[UnifiedTaskPool] Result handler error: {e}")

            self.recorder.save_snapshot(result.original_message, result)

        return handler_wrapper

    def stop_all(self):
        """
        Stops all internal components.
        """
        self.scheduler.stop()
        self.thread_pool.stop()
        self.process_pool.stop()
        self.inspector.stop()

    def pause(self):
        """
        Pauses both thread and process pools.
        """
        self.thread_pool.pause()
        self.process_pool.pause()

    def resume(self):
        """
        Resumes both thread and process pools.
        """
        self.thread_pool.resume()
        self.process_pool.resume()

    def inspect(self):
        """
        Prints the current status manually.
        """
        self.inspector._worker()
