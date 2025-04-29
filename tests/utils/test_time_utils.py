"""
=============================================================================

  Licensed Materials, Property of neuraldevelopment , Munich

  Project : basefunctions - tests

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  unit tests for timeutils module

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import pytest
import datetime
import basefunctions

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------


# -------------------------------------------------------------
# FUNCTION DEFINITIONS
# -------------------------------------------------------------
def test_now_utc():
    now = basefunctions.now_utc()
    assert isinstance(now, datetime.datetime)
    assert now.tzinfo is not None
    assert now.tzinfo.utcoffset(now) == datetime.timedelta(0)


def test_now_local():
    now = basefunctions.now_local()
    assert isinstance(now, datetime.datetime)

    berlin_now = basefunctions.now_local(tz_str="Europe/Berlin")
    assert isinstance(berlin_now, datetime.datetime)
    assert berlin_now.tzinfo is not None


def test_utc_timestamp():
    ts = basefunctions.utc_timestamp()
    assert isinstance(ts, float)
    assert ts > 0


def test_format_iso_and_parse_iso():
    now = basefunctions.now_utc()
    iso_str = basefunctions.format_iso(now)
    parsed = basefunctions.parse_iso(iso_str)
    assert isinstance(iso_str, str)
    assert isinstance(parsed, datetime.datetime)
    assert abs((parsed - now).total_seconds()) < 1


def test_to_timezone():
    now = basefunctions.now_utc()
    berlin_time = basefunctions.to_timezone(now, "Europe/Berlin")
    assert berlin_time.tzinfo is not None
    assert berlin_time.tzname() in ["CET", "CEST"]


def test_datetime_to_str_and_str_to_datetime():
    now = basefunctions.now_utc()
    fmt = "%Y-%m-%d %H:%M:%S"
    s = basefunctions.datetime_to_str(now, fmt)
    dt = basefunctions.str_to_datetime(s, fmt)
    assert isinstance(s, str)
    assert isinstance(dt, datetime.datetime)
    assert dt.strftime(fmt) == now.strftime(fmt)


def test_timestamp_conversion():
    ts = basefunctions.utc_timestamp()
    dt = basefunctions.timestamp_to_datetime(ts)
    ts_converted = basefunctions.datetime_to_timestamp(dt)
    assert isinstance(dt, datetime.datetime)
    assert abs(ts - ts_converted) < 1
