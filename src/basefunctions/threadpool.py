"""
=============================================================================

  Licensed Materials, Property of Ralph Vogl, Munich

  Project : basefunctions

  Copyright (c) by Ralph Vogl

  All rights reserved.

  Description:

  a simple framework for base functionalities in python

=============================================================================
"""

# pylint: disable=W0718
# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Any, List
from dataclasses import dataclass
import atexit
import ctypes
import queue
import threading
import types
import basefunctions


# -------------------------------------------------------------
# DEFINITIONS REGISTRY
# -------------------------------------------------------------

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------


# -------------------------------------------------------------
# VARIABLE DEFINTIONS
# -------------------------------------------------------------


# -------------------------------------------------------------
#  CLASS DEFINITIONS
# -------------------------------------------------------------


class ThreadPoolHookObjectInterface:
    """
    This class defines the interface for a hook object that gets called after
    the message was processed by the thread pool.
    """

    def hook_function(
        self,
        thread_local_data: Any,
        input_queue: queue.Queue,
        ouput_queue: queue.Queue,
        message: Any,
        *args,
        **kwargs,
    ):
        """
        This function will be called after the message was processed by the
        thread pool.

        Parameters:
        -----------
            thread_local_data (Any): The thread local data.
            input_queue (queue.Queue): The input queue for receiving tasks.
            output_queue (queue.Queue): The output queue for storing results.
            message (Any): The message that was processed by the thread pool.

        """
        raise NotImplementedError


@dataclass
class ThreadPoolMessage:
    """
    This class represents a message that can be sent to the thread pool.
    """

    type: str
    retry: int = 3
    abort_on_error: bool = False
    timeout: int = 5
    content: Any = None
    hook: ThreadPoolHookObjectInterface = None


# pylint too-few-public-methods
class ThreadPoolUserObjectInterface:
    """
    This class represents a user object which contains the callable_function
    that can be executed by a thread pool.

    Methods
    -------
    callableFunction(outputQueue, item)
        This function will be called from the thread pool in order to execute
        a specific command. The command is provided in the item parameter
        and is application specific. After processing the command, the result
        of the command can be put into the outputQueue.

    Attributes
    ----------
    None
    """

    def callable_function(
        self,
        thread_local_data: Any,
        input_queue: queue.Queue,
        output_queue: queue.Queue,
        message: ThreadPoolMessage,
        *args,
        **kwargs,
    ) -> int:
        """
        This function will be called from the thread pool in order to execute
        a specific command. The command is provided in the message parameter
        and is application specific. After processing the command, the result
        of the command can be put into the output_queue. If there are any
        other commands that needs to be executed, they can be put into the
        input_queue.

        Parameters
        ----------
        thread_local_data : Any
            The thread local data.
        input_queue : queue.LifoQueue
            The input queue for receiving tasks.
        output_queue : queue.Queue
            The queue to put the result of the task.
        message : object
            The message containing the command to execute.

        Returns
        -------
        int
            The return code of the task.
            Return 0 if successful, otherwise any other value.
        """
        raise NotImplementedError


def create_threadpool_message(
    _type: str,
    content: Any,
    retry: int = 3,
    abort_on_error: bool = False,
    timeout: int = 5,
    hook: ThreadPoolHookObjectInterface = None,
) -> ThreadPoolMessage:
    """
    Creates a ThreadPoolMessage object with the specified type and content.

    Args:
        _type (str): The type of the message.
        content (Any): The content of the message.
        retry (int): The number of retries for the message.
        abort_on_error (bool): Whether to abort on error.
        timeout (int): The timeout value for the message.
        hook(ThreadPoolHookObjectInterface): The hook function to call after message was processed.

    Returns:
        ThreadPoolMessage: The created ThreadPoolMessage object.
    """
    return ThreadPoolMessage(_type, retry, abort_on_error, timeout, content, hook)


class ThreadPool:
    """
    A thread pool implementation for executing tasks concurrently.

    This class manages a pool of threads that can execute tasks in parallel.
    It provides a convenient way to distribute work across multiple threads
    and process the results asynchronously.

    Attributes:
        thread_pool (list): A list of threads in the thread pool.
        input_queue (Queue): The input queue for receiving tasks.
        output_queue (Queue): The output queue for storing results.
        thread_pool_user_objects (dict): A dictionary of thread pool user

    Methods:
        add_thread(target)
            Adds a thread to the thread pool.
        stop_threads()
            Stops all the threads in the thread pool by putting a stop signal
            in the input queue.
        register_message_handler(msg_type, msg_handler)
            Registers a message handler for a specific message type.
        get_message_handler(msg_type)
            Get message handler for a specific message type.
        callback(thread_num, thread_local_data, input_queue, output_queue,
                thread_pool_user_objects)
            Executes the callback function for each item in the input queue.
        get_input_queue()
            Returns the input queue of the thread pool.
        get_output_queue()
            Returns the output queue of the thread pool.
        get_dataframes_from_output_queue()
            Receive a list of DataFrames from the output queue.
    """

    # -------------------------------------------------------------
    # VARIABLE DEFINTIONS
    # -------------------------------------------------------------
    thread_list: List[threading.Thread] = []
    input_queue: queue.Queue = queue.Queue()
    output_queue: queue.Queue = queue.Queue()
    thread_pool_user_objects: dict = {}
    thread_local_data = threading.local()

    # -------------------------------------------------------------
    # INIT METHOD DEFINITION
    # -------------------------------------------------------------
    def __init__(
        self,
        default_thread_pool_user_object: ThreadPoolUserObjectInterface,
        num_of_threads: int = 5,
    ) -> None:
        # save the default thread pool user object
        self.thread_pool_user_objects["default"] = (
            default_thread_pool_user_object
            if default_thread_pool_user_object is not None
            else ThreadPoolUserObjectInterface()
        )
        self.num_of_threads = basefunctions.ConfigHandler().get_config_value(
            "basefunctions/threadpool/num_of_threads", num_of_threads
        )
        # create worker threads
        for _ in range(num_of_threads):
            self.add_thread(target=self.callback)
        # register atexit function
        atexit.register(self.stop_threads)

    # -------------------------------------------------------------
    # STOP THREADS METHOD DEFINITION
    # -------------------------------------------------------------
    def add_thread(self, target: types.FunctionType) -> None:
        """
        Adds a thread to the thread pool.
        """
        thread = threading.Thread(
            target=target,
            args=(
                len(self.thread_list),
                self.thread_local_data,
                self.input_queue,
                self.output_queue,
                self.thread_pool_user_objects,
            ),
            daemon=True,
        )
        # start the thread
        thread.start()
        # add the thread to the thread list
        self.thread_list.append(thread)

    # -------------------------------------------------------------
    # STOP THREADS METHOD DEFINITION
    # -------------------------------------------------------------
    def stop_threads(self) -> None:
        """
        Stops all the threads in the thread pool by putting a stop signal
        in the input queue.
        """
        for _ in range(len(self.thread_list)):
            self.input_queue.put("##STOP##")

    # -------------------------------------------------------------
    # REGISTER MESSAGE HANDLER METHOD DEFINITION
    # -------------------------------------------------------------
    def register_message_handler(
        self, msg_type: str, msg_handler: ThreadPoolUserObjectInterface
    ) -> None:
        """
        Registers a message handler for a specific message type.
        """
        self.thread_pool_user_objects[msg_type] = msg_handler

    # -------------------------------------------------------------
    # GET MESSAGE HANDLER METHOD DEFINITION
    # -------------------------------------------------------------
    def get_message_handler(self, msg_type: str) -> ThreadPoolUserObjectInterface:
        """
        Get message handler for a specific message type.
        """
        if msg_type in self.thread_pool_user_objects:
            return self.thread_pool_user_objects[msg_type]
        else:
            return self.thread_pool_user_objects["default"]

    # -------------------------------------------------------------
    # CALLBACK METHOD DEFINITION
    # -------------------------------------------------------------
    def callback(
        self,
        _,
        thread_local_data,
        input_queue,
        output_queue,
        thread_pool_user_objects,
    ) -> None:
        """
        Executes the callback function for each item in the input queue.

        Args:
            thread_num (int): The number of the thread.
            thread_local_data (Any): The thread local data.
            input_queue (Queue): The input queue containing the items to
                process.
            output_queue (Queue): The output queue to store the results.
            thread_pool_function (ThreadPoolFunction): The thread pool
                function object.

        Returns:
            None
        """
        for message in iter(input_queue.get, "##STOP##"):
            # if item from queue is no ThreadPoolMessage, raise an exception
            if not isinstance(message, ThreadPoolMessage):
                raise ValueError("Message is not a ThreadPoolMessage")
            # retry until successful or max retries reached
            result = 1
            for try_counter in range(message.retry):
                with TimerThread(message.timeout, threading.get_ident()):
                    # init variables
                    result = 1
                    try:
                        thread_pool_user_object = (
                            thread_pool_user_objects[message.type]
                            if message.type in thread_pool_user_objects
                            else thread_pool_user_objects["default"]
                        )
                        # call the callable function
                        result = thread_pool_user_object.callable_function(
                            thread_local_data,
                            input_queue,
                            output_queue,
                            message,
                        )
                    except TimeoutError as e:
                        # Log the timeout message instead of printing
                        print(f"##TIMEOUT## - try: ({try_counter+1} of {message.retry}) - {e}")
                    except Exception as e:
                        print(f"##EXCEPTION## - try: ({try_counter+1} of {message.retry}) - {e}")
                # check if the task was successful
                if result in (None, 0):
                    break

            # if not successful, put an item into the output queue
            if result not in (None, 0):
                # check message.abort_on_error
                if message.abort_on_error:
                    input_queue.task_done()
                    raise ValueError("##ABORT ON ERROR##")
                output_queue.put(None)
            else:
                # check to call the hook function
                if message.hook is not None:
                    message.hook.hook_function(
                        thread_local_data, input_queue, output_queue, message.content
                    )

            # signal that the task is done
            input_queue.task_done()

    # -------------------------------------------------------------
    # GET INPUT QUEUE METHOD DEFINITION
    # -------------------------------------------------------------
    def get_input_queue(self) -> queue.Queue | None:
        """
        Returns the input queue of the thread pool.

        Returns:
            The input queue of the thread pool.
        """
        return self.input_queue

    # -------------------------------------------------------------
    # GET OUTPUT QUEUE METHOD DEFINITION
    # -------------------------------------------------------------
    def get_output_queue(self) -> queue.Queue | None:
        """
        Returns the output queue of the thread pool.

        Returns:
            The output queue of the thread pool.
        """
        return self.output_queue

    # -------------------------------------------------------------
    # GET DATAFRAMES FROM OUTPUT QUEUE AND JOIN THEM INTO DICTIONARY
    # -------------------------------------------------------------
    def get_dataframes_from_output_queue(self) -> dict:
        """
        Receive a list of DataFrames from the output queue.

        Returns
        -------
        dict
            A dictionary of DataFrames.
        """
        result = {}
        while not self.get_output_queue().empty():
            result = result | self.get_output_queue().get()
        return result


class TimerThread:
    """
    A class representing a timer thread that raises a RuntimeError in the
    thread with the specified thread_id to terminate it after a specified
    timeout.
    """

    timeout: int | None = None
    thread_id: int | None = None
    timer: threading.Thread | None = None

    def __init__(self, timeout: int, thread_id: int) -> None:
        """
        Initializes a TimerThread object with the specified timeout and
        thread_id.

        Args:
            timeout (float): The timeout value in seconds.
            thread_id (int): The ID of the thread to terminate.
        """
        self.timeout = timeout
        self.thread_id = thread_id
        self.timer = threading.Timer(
            interval=self.timeout,
            function=self.timeout_thread,
            args=[],
        )

    def __enter__(self):
        """
        Starts the timer thread.
        """
        self.timer.start()

    def __exit__(self, _type, _value, _traceback):
        """
        Cancels the timer thread.
        """
        self.timer.cancel()

    def timeout_thread(self):
        """
        Raises a TimeoutError in the thread with the specified thread_id to
        terminate it.
        """
        ctypes.pythonapi.PyThreadState_SetAsyncExc(
            ctypes.c_long(self.thread_id),
            ctypes.py_object(TimeoutError),
        )
