# Introduction

basefunction is a simple library to have some commonly used functions for everyday purpose.  The functions include some
convenience functions for file handling as well as a threadpool class with automatic retry and timeout functionality.  

## Getting Started

There are the following functionalities in this lib:

- `database` - some convienience functions for sql handling
- `filefunctions` - some convienience functions for file handling
- `threadpool` - a threadpool class with message system

## Installing

```
pip install basefunctions
```

## Usage

### Using convenience file functions

```python
import basefunctions as bf

bf.get_current_directory()
/Users/neutro2/
```

## Using threadpool class

The code below is a small example of the threadpool usage. If you want to see more complex examples 
on how to use the threadpool, please see package <https://pypi.org/project/eod2pd/> where I've used 
the framework in order to speed up the downloads.

You can play a little bit with adding UserObjects A, B and C, setting timeout and sleep values 
towards desired values and see how the framework reacts. For simplicity I recommend to remove 
classes B and C first and just use class A and understand what the parameters does. Then adding 
class B and see how the parameters work and how everything fits together. The problem with 
threading is that you never know which thread will execute your code but from a global perspective
this is not relevant as long as the desired behaviour is visible.  

```python
"""
    Summary:
    This script demonstrates the usage of the basefunctions module to create a
    ThreadPool and execute tasks concurrently.

    It defines two classes A & B of ThreadPoolUserObjects which contains the working functions
    callable_function where the user can add the own functionality. Each working function prints
    the message content and then sleeps for 3 seconds. After awakeing we return 1 to signal that
    he command has failed. This is because we want to see that the threadpool automatically
    restarts the command for a defined number of retires.

    The threadpool operates by sending messages of what todo into the input queues of the
    threadpool. This allows to have multiple user functions all running with the same thread pool.
    In order to let the threadpool know which user object to call we register message handlers
    for a specific string which takes the message and process it.

    As the function always return 1 in the end, finally we receive an error message that none of
    the commands have executed sucessfully.

    With the retry and timeout parameter you can play around a little bit and see that the
    framework also interrupts the user functions after a specified number of seconds and reports a
    timeout.

    Returns:
    -------
    int
        The return value of the callable function.
"""

import time

import basefunctions

# pylint: disable=too-few-public-methods


class A(basefunctions.ThreadPoolUserObjectInterface):
    """
    class A
    """

    def callable_function(self, thread_local_data, input_queue, output_queue, message) -> int:
        """
        Summary:
        This method represents the task that will be executed by the
        ThreadPool.

        Parameters:
        ----------
        inputQueue : LifoQueue
            The input queue to add additional tasks to the ThreadPool.
        outputQueue : Queue
            The output queue to store the result of the task.
        message : ThreadPoolMessage
            The message to be processed by the task.

        Returns:
        -------
        int
            The return value of the task.
        """
        print(f"A: callable called with item: {message.content}")
        time.sleep(2)
        return 1


class B(basefunctions.ThreadPoolUserObjectInterface):
    """
    class B
    """

    def callable_function(self, thread_local_data, input_queue, output_queue, message) -> int:
        """
        Summary:
        This method represents the task that will be executed by the
        ThreadPool.

        Parameters:
        ----------
        inputQueue : Queue
            The input queue to add additional tasks to the ThreadPool.
        outputQueue : Queue
            The output queue to store the result of the task.
        message : ThreadPoolMessage
            The message to be processed by the task.

        Returns:
        -------
        int
            The return value of the task.
        """
        print(f"B: callable called with item: {message.content}")
        time.sleep(5)
        return 1


class C(basefunctions.ThreadPoolUserObjectInterface):
    """
    class B
    """

    def callable_function(self, thread_local_data, input_queue, output_queue, message) -> int:
        """
        Summary:
        This method represents the task that will be executed by the
        ThreadPool.

        Parameters:
        ----------
        inputQueue : Queue
            The input queue to add additional tasks to the ThreadPool.
        outputQueue : Queue
            The output queue to store the result of the task.
        message : ThreadPoolMessage
            The message to be processed by the task.

        Returns:
        -------
        int
            The return value of the task.
        """
        print(f"C: callable called with item: {message.content}")
        time.sleep(5)
        return 1


# register the message handlers in the default threadpool
basefunctions.default_threadpool.register_message_handler("1", A())
basefunctions.default_threadpool.register_message_handler("2", B())
basefunctions.default_threadpool.register_message_handler("3", C())

# create the messages for sending towards the threadpool
msg1 = basefunctions.threadpool.ThreadPoolMessage(type="1", retry=3, timeout=3, content="1")
msg2 = basefunctions.threadpool.ThreadPoolMessage(type="2", retry=3, timeout=2, content="2")
msg3 = basefunctions.threadpool.ThreadPoolMessage(
    type="3", retry=2, timeout=2, abort_on_error=False, content="3"
)

# run the code
print("starting")
basefunctions.default_threadpool.get_input_queue().put(msg1)
basefunctions.default_threadpool.get_input_queue().put(msg2)
basefunctions.default_threadpool.get_input_queue().put(msg3)
basefunctions.default_threadpool.get_input_queue().join()
print("finished")
```

## Project Homepage

<https://dev.azure.com/neuraldevelopment/basefunctions>

## Contribute

If you find a defect or suggest a new function, please send an eMail to <neutro2@outlook.de>
