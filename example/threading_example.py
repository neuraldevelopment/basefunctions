import time
import basefunctions


@basefunctions.task_handler("task_A")
@basefunctions.debug_task
def task_A(message):
    print(f"[Task A] Received: {message.content}")
    time.sleep(2)
    return type("TaskResult", (object,), {"success": False, "result": None})()


@basefunctions.task_handler("task_B")
@basefunctions.debug_task
def task_B(message):
    print(f"[Task B] Received: {message.content}")
    time.sleep(5)
    return type("TaskResult", (object,), {"success": False, "result": None})()


@basefunctions.task_handler("task_C")
@basefunctions.debug_task
def task_C(message):
    print(f"[Task C] Received: {message.content}")
    time.sleep(5)
    return type("TaskResult", (object,), {"success": False, "result": None})()


if __name__ == "__main__":
    pool = basefunctions.get_default_thread_task_pool()

    pool.register_handler(task_A)
    pool.register_handler(task_B)
    pool.register_handler(task_C)

    msg1 = basefunctions.TaskMessage(
        priority=10, msg_type="task_A", content="Payload A", retry=3, timeout=5
    )
    msg2 = basefunctions.TaskMessage(
        priority=20, msg_type="task_B", content="Payload B", retry=3, timeout=5
    )
    msg3 = basefunctions.TaskMessage(
        priority=30, msg_type="task_C", content="Payload C", retry=2, timeout=5
    )

    pool.submit_message(msg1)
    pool.submit_message(msg2)
    pool.submit_message(msg3)

    print("Waiting for tasks to complete...")

    pool.input_queue.join()  # <------ WICHTIG

    print("All tasks finished. Stopping...")
    pool.stop()
