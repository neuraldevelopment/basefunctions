"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment , Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Example usage of the UnifiedTaskPool for both thread and corelet execution
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import time
from typing import Any, Tuple
import basefunctions

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
class ExampleThreadHandler(basefunctions.TaskletRequestInterface):
    """
    Example implementation of a thread-based task handler.
    """

    def process_request(
        self, context: basefunctions.TaskContext, message: basefunctions.UnifiedTaskPoolMessage
    ) -> Tuple[bool, Any]:
        """
        Process a request in a thread.

        Parameters
        ----------
        context : TaskContext
            Context with thread information
        message : UnifiedTaskPoolMessage
            Message to process

        Returns
        -------
        Tuple[bool, Any]
            Success status and result data
        """
        basefunctions.get_logger(__name__).info(
            "processing thread request: %s", message.message_type
        )

        # Simulate some processing
        time.sleep(1)

        # Return success and processed data
        return True, {"processed_by": "thread", "original_data": message.content}


class ExampleObserver(basefunctions.Observer):
    """
    Example observer for start and stop events.
    """

    def __init__(self, event_type: str):
        """
        Initialize observer.

        Parameters
        ----------
        event_type : str
            Type of event this observer is for
        """
        self.event_type = event_type

    def notify(self, message: Any, *args, **kwargs) -> None:
        """
        Handle notification from subject.

        Parameters
        ----------
        message : Any
            Message from the subject
        args : Any
            Additional arguments
        kwargs : Any
            Additional keyword arguments
        """
        basefunctions.get_logger(__name__).info(
            "observer for %s received: %s",
            self.event_type,
            message.id if hasattr(message, "id") else str(message),
        )

        # Example of processing the result for a stop notification
        if self.event_type.startswith("stop-") and hasattr(message, "data"):
            basefunctions.get_logger(__name__).info(
                "processing result data for message %s", message.id
            )
            # Here you could write to a database, send notifications, etc.


def main():
    """
    Example application using the UnifiedTaskPool.
    """
    # Create task pool instance
    pool = basefunctions.UnifiedTaskPool(num_of_threads=3)

    # Register message handler for thread execution
    pool.register_message_handler("example_thread", ExampleThreadHandler())

    # Register observers for start and stop events
    thread_start_observer = ExampleObserver("start-example_thread")
    thread_stop_observer = ExampleObserver("stop-example_thread")
    core_start_observer = ExampleObserver("start-example_core")
    core_stop_observer = ExampleObserver("stop-example_core")

    # Attach observers
    pool.register_observer_for_message_type("example_thread", True, thread_start_observer)
    pool.register_observer_for_message_type("example_thread", False, thread_stop_observer)
    pool.register_observer_for_message_type("example_core", True, core_start_observer)
    pool.register_observer_for_message_type("example_core", False, core_stop_observer)

    # Create and submit thread-based task
    thread_message = basefunctions.UnifiedTaskPoolMessage(
        message_type="example_thread",
        execution_type="thread",
        content={"task_id": 1, "data": "Sample thread task"},
    )

    # Add message to queue
    pool.get_input_queue().put(thread_message)

    basefunctions.get_logger(__name__).info("submitted thread task")

    # Create and submit core-based task with specific module path
    core_message = basefunctions.UnifiedTaskPoolMessage(
        message_type="example_core",
        execution_type="core",
        corelet_path="./example_corelet.py",  # Spezifischer Corelet-Path
        content={"task_id": 2, "data": "Sample core task"},
    )

    # Add message to queue
    pool.get_input_queue().put(core_message)

    basefunctions.get_logger(__name__).info(
        "submitted core task with module path %s", core_message.corelet_path
    )

    # Wait for all tasks to complete
    pool.wait_for_all()

    # Retrieve results
    results = pool.get_results_from_output_queue()

    # Process results
    for result in results:
        basefunctions.get_logger(__name__).info(
            "result for message %s (type: %s): success=%s",
            result.id,
            result.message_type,
            result.success,
        )

        if result.success:
            basefunctions.get_logger(__name__).info("data: %s", result.data)
        else:
            basefunctions.get_logger(__name__).error(
                "error: %s (%s)", result.error, result.exception_type
            )

    basefunctions.get_logger(__name__).info("all tasks completed")


if __name__ == "__main__":
    main()
