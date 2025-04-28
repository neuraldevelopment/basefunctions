"""
=============================================================================

  Licensed Materials, Property of Ralph Vogl, Munich

  Project : unified_task_pool

  Copyright (c) by Ralph Vogl

  All rights reserved.

  Description:

  Chainer class for sequential task execution where each task receives
  the result of the previous one.

=============================================================================
"""

# -------------------------------------------------------------
# CLASS DEFINITIONS
# -------------------------------------------------------------


class Chainer:
    """
    Executes a chain of tasks where each task receives the previous result.
    """

    def __init__(self, unified_pool):
        self.unified_pool = unified_pool

    def chain(self, task_list):
        """
        Starts a chained execution of multiple tasks.

        Parameters:
            task_list (List[Tuple[str, dict]]): List of (msg_type, content_dict).
        """
        if not task_list:
            return

        def build_chain(index, previous_result=None):
            if index >= len(task_list):
                return

            msg_type, content = task_list[index]
            if previous_result is not None:
                content["previous_result"] = previous_result

            def result_handler(result):
                if result.success:
                    build_chain(index + 1, previous_result=result.result)
                else:
                    print(f"[Chain] Task {msg_type} failed, breaking chain.")

            self.unified_pool.submit_message(
                msg_type,
                content,
                priority=50,
                result_handler=result_handler,
            )

        build_chain(0)
