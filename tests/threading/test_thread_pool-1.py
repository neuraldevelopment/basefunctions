"""
=============================================================================

 Licensed Materials, Property of neuraldevelopment , Munich

 Project : basefunctions

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 Tests CoreletBase and ThreadPool via real subprocess and thread handler

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import os
import pickle
import subprocess
import sys
import basefunctions
import pytest

# -------------------------------------------------------------
# DEFINITIONS REGISTRY
# -------------------------------------------------------------


# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------
class DummyThreadHandler(basefunctions.ThreadPoolRequestInterface):
    def process_request(self, context, message):
        return True, f"thread-ok: {message.content}"


# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------


# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------
def test_thread_handler():
    """test the thread handler functionality"""
    pool = basefunctions.ThreadPool(num_of_threads=1)
    pool.register_handler("testmsg", DummyThreadHandler, "thread")
    mid = pool.submit_task("testmsg", content="hi")
    pool.wait_for_all()
    result = pool.get_results_from_output_queue()[0]
    assert result.id == mid
    assert result.success
    assert result.data == "thread-ok: hi"


def test_corelet_process(tmp_path):
    """test direct corelet execution via subprocess"""
    script_path = tmp_path / "corelet.py"
    script_path.write_text(
        f"""
import sys
import pickle
sys.path.insert(0, {repr(str(os.getcwd()))})
import basefunctions

class Corelet(basefunctions.CoreletBase):
    def process_request(self, context, message):
        return True, f"core-ok: {{message.content}}"

if __name__ == "__main__":
    Corelet().main()
"""
    )
    message = basefunctions.ThreadPoolMessage(message_type="coretest", content="42")
    message_data = pickle.dumps(message)

    # Use with context to ensure proper cleanup of resources
    with subprocess.Popen(
        [sys.executable, str(script_path)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ) as proc:
        output, error = proc.communicate(input=message_data, timeout=3)

        assert proc.returncode == 0, error.decode()
        result = pickle.loads(output)
        assert result.success
        assert result.data == "core-ok: 42"


def test_corelet_via_threadpool(tmp_path, monkeypatch):
    """test corelet execution through threadpool"""
    # Patch the _process_request_core method to ensure proper cleanup
    original_process_request_core = basefunctions.ThreadPool._process_request_core

    def patched_process_request_core(self, context, message):
        # get corelet path from registration
        corelet_path = self._get_corelet_path(message.message_type)

        # create subprocess with pipes for communication
        process = None
        try:
            # prepare message data
            message_data = pickle.dumps(message)

            # start subprocess
            process = subprocess.Popen(
                ["python", corelet_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # store process in context for timeout handling
            if context:
                context.process_info = {"process": process, "type": "corelet"}

            # send message data to subprocess
            process.stdin.write(message_data)
            process.stdin.flush()
            process.stdin.close()

            # read result from stdout
            result_data = process.stdout.read()

            # make sure to read stderr too to avoid resource leaks
            error_output = process.stderr.read()

            # check process exit code
            return_code = process.wait()
            if return_code != 0:
                basefunctions.get_logger(__name__).error(
                    "corelet process exited with code %d: %s", return_code, error_output
                )
                return False, f"corelet process failed with exit code {return_code}"

            # check if we got a result
            if result_data:
                result = pickle.loads(result_data)
                return result.success, result.data
            else:
                return False, "no result received from corelet process"

        except Exception as e:
            return False, str(e)
        finally:
            # Make sure to clean up process resources
            if process:
                try:
                    # Close any remaining open file descriptors
                    if process.stdin and not process.stdin.closed:
                        process.stdin.close()
                    if process.stdout and not process.stdout.closed:
                        process.stdout.close()
                    if process.stderr and not process.stderr.closed:
                        process.stderr.close()
                except:
                    pass

    # Apply the patch
    monkeypatch.setattr(
        basefunctions.ThreadPool, "_process_request_core", patched_process_request_core
    )

    corelet_file = tmp_path / "corelet_main.py"
    corelet_file.write_text(
        f"""
import sys
import pickle
import os
sys.path.insert(0, {repr(str(os.getcwd()))})
import basefunctions

class Corelet(basefunctions.CoreletBase):
    def process_request(self, context, message):
        return True, f"corelet says: {{message.content}}"

if __name__ == "__main__":
    try:
        corelet = Corelet()
        corelet.main()
    finally:
        # Ensure all file handles are closed
        if not sys.stdin.closed:
            sys.stdin.close()
        if not sys.stdout.closed:
            sys.stdout.close()
        if not sys.stderr.closed:
            sys.stderr.close()
"""
    )
    pool = basefunctions.ThreadPool(num_of_threads=1)
    pool.register_handler("hello", str(corelet_file), "core")
    mid = pool.submit_task("hello", content="neutro2", timeout=5)

    try:
        pool.wait_for_all()
        result = pool.get_results_from_output_queue()[0]
        assert result.id == mid
        assert result.success
        assert result.data == "corelet says: neutro2"
    finally:
        # Ensure clean termination
        pool.stop_threads()
