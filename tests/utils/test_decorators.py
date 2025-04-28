"""
=============================================================================

  Licensed Materials, Property of Ralph Vogl, Munich

  Project : basefunctions

  Copyright (c) by Ralph Vogl

  All rights reserved.

  Description:

  pytest testcases for decorators.py

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------

import pytest
import time
import threading
import logging
import basefunctions as bf

# -------------------------------------------------------------
# FUNCTION DEFINITIONS
# -------------------------------------------------------------


def test_function_timer(capsys):
    @bf.function_timer
    def sample():
        time.sleep(0.01)

    sample()
    out = capsys.readouterr().out
    assert "Runtime of sample:" in out


def test_singleton():
    @bf.singleton
    class Sample:
        pass

    a = Sample()
    b = Sample()
    assert a is b


def test_auto_property():
    @bf.auto_property
    class Sample:
        _value = 42

    s = Sample()
    assert s.value == 42
    s.value = 100
    assert s.value == 100


def test_assert_non_null_args_pass():
    @bf.assert_non_null_args
    def sample(x, y):
        return x + y

    assert sample(1, 2) == 3


def test_log_instances_global():
    @bf.log_instances(global_log=False)
    class Sample:
        def __init__(self, x):
            self.x = x

    s1 = Sample(1)
    s2 = Sample(2)

    assert hasattr(Sample, "_instance_log")
    assert len(Sample._instance_log) == 2


def test_enable_logging(tmp_path):
    @bf.enable_logging()
    def sample():
        logging.getLogger().debug("test log")

    sample()
    # Logfileprüfung müsste spezifisch angepasst werden


def test_trace(capsys):
    @bf.trace
    def sample(x):
        return x * 2

    assert sample(3) == 6
    out = capsys.readouterr().out
    assert "[TRACE]" in out


def test_log(capsys):
    @bf.log
    def sample(x):
        return x + 1

    assert sample(1) == 2


def test_catch_exceptions(capsys):
    @bf.catch_exceptions
    def sample(x):
        return 1 / x

    assert sample(1) == 1
    sample(0)
    out = capsys.readouterr().out
    assert "Exception in sample" in out


def test_count_calls(capsys):
    @bf.count_calls
    def sample():
        return 1

    sample()
    sample()
    assert sample.call_count == 2


def test_log_stack(capsys):
    @bf.log_stack
    def sample():
        return 42

    sample()
    out = capsys.readouterr().out
    assert "[STACK]" in out


def test_freeze_args():
    @bf.freeze_args
    def sample(lst):
        lst.append(1)
        return lst

    arg = []
    result = sample(arg)
    assert arg == []
    assert result == [1]


def test_assert_output():
    @bf.assert_output(3)
    def sample():
        return 3

    assert sample() == 3


def test_log_types(capsys):
    @bf.log_types
    def sample(x):
        return str(x)

    assert sample(5) == "5"
    out = capsys.readouterr().out
    assert "arg types" in out


def test_sanitize_args():
    @bf.sanitize_args
    def sample(x):
        return x

    import math

    assert sample(math.nan) == 0


def test_thread_safe():
    counter = {"val": 0}

    @bf.thread_safe
    def inc():
        val = counter["val"]
        time.sleep(0.01)
        counter["val"] = val + 1

    threads = [threading.Thread(target=inc) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert counter["val"] == 10


def test_profile_memory(capsys):
    @bf.profile_memory
    def sample():
        return [i for i in range(1000)]

    sample()
    out = capsys.readouterr().out
    assert "used" in out


def test_recursion_limit():
    @bf.recursion_limit(3000)
    def sample(n):
        if n == 0:
            return 0
        return sample(n - 1)

    assert sample(50) == 0


def test_inspect_signature(capsys):
    @bf.inspect_signature
    def sample(x, y):
        return x + y

    assert sample(1, 2) == 3


def test_warn_if_slow(capsys):
    @bf.warn_if_slow(0.001)
    def sample():
        time.sleep(0.002)

    sample()
    out = capsys.readouterr().out
    assert "⚠️ Warning" in out


def test_retry_on_exception():
    call_counter = {"count": 0}

    @bf.retry_on_exception(retries=2, delay=0.01)
    def sample():
        call_counter["count"] += 1
        if call_counter["count"] < 2:
            raise ValueError("fail")
        return "ok"

    assert sample() == "ok"


def test_cache_results():
    call_counter = {"count": 0}

    @bf.cache_results
    def sample(x):
        call_counter["count"] += 1
        return x * 2

    assert sample(2) == 4
    assert sample(2) == 4
    assert call_counter["count"] == 1


def test_suppress():
    @bf.suppress(ZeroDivisionError)
    def sample(x):
        return 1 / x

    assert sample(0) is None


def test_log_class_methods(capsys):
    @bf.log_class_methods
    class Sample:
        def foo(self):
            return "bar"

    s = Sample()
    assert s.foo() == "bar"


def test_track_variable_changes(capsys):
    @bf.track_variable_changes
    def sample():
        x = 1
        x += 1
        y = 3

    sample()
    out = capsys.readouterr().out
    assert "Changes in sample" in out
