"""
# =============================================================================
#
#  Licensed Materials, Property of neuraldevelopment, Munich
#
#  Project : basefunctions
#
#  Copyright (c) by neuraldevelopment
#
#  All rights reserved.
#
#  Description:
#
#  Example usage of the threadpool with decorators and auto-injected arguments.
#
# =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import time
import uuid
import basefunctions

# -------------------------------------------------------------
# FUNCTION DEFINITIONS
# -------------------------------------------------------------


class MultiplyByTwoResultHandler(basefunctions.ThreadPoolResultInterface):
    def process_result(self, raw_data, original_message):
        return raw_data * 2


@basefunctions.task_handler("task_A")
def task_A(message):
    """
    Task A: simulate short processing.

    Parameters
    ----------
    message : ThreadPoolMessage
        Incoming message.

    Returns
    -------
    Tuple[bool, Any]
        Task success and result payload.
    """
    print(f"[Task A] Received: {message.content}")
    time.sleep(2)
    return True, {"done": "A"}


@basefunctions.task_handler("task_B")
def task_B(message):
    """
    Task B: returns numeric value 2.

    Parameters
    ----------
    message : ThreadPoolMessage

    Returns
    -------
    Tuple[bool, Any]
    """
    print(f"[Task B] Received: {message.content}")
    time.sleep(1)
    return True, 2


@basefunctions.task_handler("task_C")
@basefunctions.debug_task
def task_C(message):
    """
    Task C: simulate failure.

    Parameters
    ----------
    message : ThreadPoolMessage

    Returns
    -------
    Tuple[bool, Any]
    """
    print(f"[Task C] Received: {message.content}")
    raise RuntimeError("invalid data received")


if __name__ == "__main__":
    pool = basefunctions.ThreadPool(num_of_threads=3)

    pool.register_message_handler("task_A", task_A)
    pool.register_message_handler("task_B", task_B)
    pool.register_message_handler("task_C", task_C)

    pool.get_input_queue().put(
        basefunctions.ThreadPoolMessage(
            id=str(uuid.uuid4()), message_type="task_A", content="Payload A"
        )
    )
    pool.get_input_queue().put(
        basefunctions.ThreadPoolMessage(
            id=str(uuid.uuid4()),
            message_type="task_B",
            content="Payload B",
            result_handler=MultiplyByTwoResultHandler(),
        )
    )
    pool.get_input_queue().put(
        basefunctions.ThreadPoolMessage(
            id=str(uuid.uuid4()), message_type="task_C", content="Payload C"
        )
    )

    print("Waiting for tasks to complete...")
    pool.get_input_queue().join()
    print("All tasks finished. Collecting results...")
    for result in pool.get_results_from_output_queue():
        print(
            f"Result for {result.message_type} "
            f"(id={result.id}): success={result.success}, data={result.data}, "
            f"retry_counter={result.retry_counter}"
        )

    print("Stopping...")
    pool.stop_threads()
