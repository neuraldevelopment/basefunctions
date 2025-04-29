"""
=============================================================================

  Licensed Materials, Property of neuraldevelopment , Munich

  Project : basefunctions

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  a simple time utility module for unified time handling with timezone support

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import datetime
import time
from typing import Optional

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None

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
def _get_timezone(tz_str: Optional[str]) -> datetime.tzinfo:
    """
    Internal helper to resolve timezone string to tzinfo object.

    Parameters
    ----------
    tz_str : Optional[str]
        The timezone string (e.g., 'Europe/Berlin').

    Returns
    -------
    datetime.tzinfo
        The corresponding timezone object.

    Raises
    ------
    ImportError
        If ZoneInfo is not available (Python < 3.9).
    """
    if tz_str is None:
        return datetime.timezone.utc
    if ZoneInfo is None:
        basefunctions.get_logger(__name__).error("zoneinfo not available, python 3.9+ required")
        raise ImportError("zoneinfo is not available. Python 3.9+ is required.")
    return ZoneInfo(tz_str)


def now_utc() -> datetime.datetime:
    """
    Returns the current UTC datetime.

    Returns
    -------
    datetime.datetime
        The current UTC datetime.
    """
    return datetime.datetime.now(datetime.timezone.utc)


def now_local(tz_str: Optional[str] = None) -> datetime.datetime:
    """
    Returns the current local datetime, optionally in a specified timezone.

    Parameters
    ----------
    tz_str : Optional[str]
        Timezone string (e.g., 'Europe/Berlin'). If None, local system timezone is used.

    Returns
    -------
    datetime.datetime
        The current local datetime.
    """
    dt = datetime.datetime.now()
    if tz_str:
        dt = dt.replace(tzinfo=datetime.timezone.utc).astimezone(_get_timezone(tz_str))
    return dt


def utc_timestamp() -> float:
    """
    Returns the current UTC timestamp.

    Returns
    -------
    float
        POSIX timestamp.
    """
    return time.time()


def format_iso(dt: datetime.datetime) -> str:
    """
    Formats a datetime object to ISO 8601 string.

    Parameters
    ----------
    dt : datetime.datetime
        The datetime object to format.

    Returns
    -------
    str
        ISO formatted datetime string.
    """
    return dt.astimezone(datetime.timezone.utc).isoformat()


def parse_iso(s: str, tz_str: Optional[str] = None) -> datetime.datetime:
    """
    Parses an ISO 8601 string to a datetime object.

    Parameters
    ----------
    s : str
        ISO formatted datetime string.
    tz_str : Optional[str]
        Optional timezone string.

    Returns
    -------
    datetime.datetime
        The parsed datetime object.
    """
    dt = datetime.datetime.fromisoformat(s)
    if tz_str:
        dt = dt.astimezone(_get_timezone(tz_str))
    return dt


def to_timezone(dt: datetime.datetime, tz_str: str) -> datetime.datetime:
    """
    Converts a datetime object to another timezone.

    Parameters
    ----------
    dt : datetime.datetime
        The datetime object to convert.
    tz_str : str
        Target timezone string (e.g., 'Europe/Berlin').

    Returns
    -------
    datetime.datetime
        The datetime object in the new timezone.
    """
    return dt.astimezone(_get_timezone(tz_str))


def datetime_to_str(dt: datetime.datetime, fmt: str) -> str:
    """
    Formats a datetime object according to a given format string.

    Parameters
    ----------
    dt : datetime.datetime
        The datetime object to format.
    fmt : str
        The format string (e.g., '%Y-%m-%d %H:%M:%S').

    Returns
    -------
    str
        Formatted datetime string.
    """
    return dt.strftime(fmt)


def str_to_datetime(s: str, fmt: str) -> datetime.datetime:
    """
    Parses a datetime object from a string and format.

    Parameters
    ----------
    s : str
        Datetime string.
    fmt : str
        Format string.

    Returns
    -------
    datetime.datetime
        The parsed datetime object.
    """
    return datetime.datetime.strptime(s, fmt)


def timestamp_to_datetime(ts: float) -> datetime.datetime:
    """
    Converts a POSIX timestamp to a UTC datetime object.

    Parameters
    ----------
    ts : float
        POSIX timestamp.

    Returns
    -------
    datetime.datetime
        UTC datetime.
    """
    return datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc)


def datetime_to_timestamp(dt: datetime.datetime) -> float:
    """
    Converts a datetime object to a POSIX timestamp.

    Parameters
    ----------
    dt : datetime.datetime
        The datetime object.

    Returns
    -------
    float
        POSIX timestamp.
    """
    return dt.timestamp()
