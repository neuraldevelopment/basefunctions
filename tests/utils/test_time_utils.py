"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich

  Project : basefunctions

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  Pytest test suite for time_utils module.
  Tests unified time handling utilities with timezone support.

  Log:
  v1.0.0 : Initial test implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
# External imports (alphabetical)
import datetime
import time
from typing import Any, Dict, Optional
from unittest.mock import MagicMock, patch

import pytest

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None

# Project imports (relative to project root)
from basefunctions.utils import time_utils

# -------------------------------------------------------------
# FIXTURES
# -------------------------------------------------------------


@pytest.fixture
def fixed_utc_time() -> datetime.datetime:
    """
    Provide fixed UTC datetime for deterministic testing.

    Returns
    -------
    datetime.datetime
        Fixed UTC datetime (2025-01-15 12:30:45 UTC)

    Notes
    -----
    Use this fixture to ensure tests are not time-dependent
    """
    # RETURN
    return datetime.datetime(2025, 1, 15, 12, 30, 45, tzinfo=datetime.timezone.utc)


@pytest.fixture
def fixed_timestamp() -> float:
    """
    Provide fixed POSIX timestamp for testing.

    Returns
    -------
    float
        Fixed timestamp corresponding to 2025-01-15 12:30:45 UTC

    Notes
    -----
    Corresponds to fixed_utc_time fixture
    """
    # RETURN
    return datetime.datetime(2025, 1, 15, 12, 30, 45, tzinfo=datetime.timezone.utc).timestamp()


@pytest.fixture
def sample_iso_strings() -> Dict[str, Any]:
    """
    Provide sample ISO format strings for testing.

    Returns
    -------
    Dict[str, Any]
        Dictionary with 'valid' and 'invalid' ISO string lists

    Notes
    -----
    Includes edge cases and malformed strings
    """
    # RETURN
    return {
        "valid": [
            "2025-01-15T12:30:45+00:00",
            "2025-01-15T12:30:45Z",
            "2025-01-15T12:30:45.123456+00:00",
            "2025-01-15T12:30:45",
        ],
        "invalid": [
            "",
            "not-a-date",
            "2025-13-45",
            "2025-01-15 12:30:45",  # Space instead of T
            None,
        ],
    }


@pytest.fixture
def mock_zoneinfo_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Simulate Python < 3.9 environment where ZoneInfo is unavailable.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture

    Returns
    -------
    None

    Notes
    -----
    Sets time_utils.ZoneInfo to None to simulate ImportError condition
    """
    # ARRANGE
    monkeypatch.setattr(time_utils, "ZoneInfo", None)


# -------------------------------------------------------------
# TEST CASES - CRITICAL FUNCTIONS
# -------------------------------------------------------------


def test_get_timezone_returns_utc_when_none() -> None:  # CRITICAL TEST
    """
    Test _get_timezone returns UTC when tz_str is None.

    Tests that _get_timezone correctly defaults to UTC timezone
    when given None as input.

    Returns
    -------
    None
        Test passes if timezone is UTC
    """
    # ARRANGE
    tz_str: Optional[str] = None

    # ACT
    result: datetime.tzinfo = time_utils._get_timezone(tz_str)

    # ASSERT
    assert result == datetime.timezone.utc


@pytest.mark.skipif(ZoneInfo is None, reason="ZoneInfo not available (Python < 3.9)")
def test_get_timezone_returns_zoneinfo_when_valid_string() -> None:  # CRITICAL TEST
    """
    Test _get_timezone returns ZoneInfo for valid timezone string.

    Tests that _get_timezone correctly creates ZoneInfo object
    when given valid timezone string like 'Europe/Berlin'.

    Returns
    -------
    None
        Test passes if ZoneInfo object created correctly
    """
    # ARRANGE
    tz_str: str = "Europe/Berlin"

    # ACT
    result: datetime.tzinfo = time_utils._get_timezone(tz_str)

    # ASSERT
    assert isinstance(result, ZoneInfo)
    assert str(result) == "Europe/Berlin"


def test_get_timezone_raises_importerror_when_zoneinfo_unavailable(
    mock_zoneinfo_unavailable: None,
) -> None:  # CRITICAL TEST
    """
    Test _get_timezone raises ImportError when ZoneInfo unavailable.

    Tests that _get_timezone correctly raises ImportError
    when ZoneInfo is None (Python < 3.9 environment).

    Parameters
    ----------
    mock_zoneinfo_unavailable : None
        Fixture that sets ZoneInfo to None

    Returns
    -------
    None
        Test passes if ImportError raised with correct message
    """
    # ARRANGE
    tz_str: str = "Europe/Berlin"

    # ACT & ASSERT
    with pytest.raises(ImportError, match="zoneinfo is not available"):
        time_utils._get_timezone(tz_str)


@pytest.mark.skipif(ZoneInfo is None, reason="ZoneInfo not available (Python < 3.9)")
@pytest.mark.parametrize(
    "invalid_tz",
    [
        "Invalid/Timezone",
        "../../etc/passwd",  # CRITICAL: path traversal attempt
        "Europe/Invalid",
        "America/NotACity",
        "../Berlin",
        "Europe/../America/New_York",
    ],
)
def test_get_timezone_raises_exception_when_invalid_timezone(invalid_tz: str) -> None:  # CRITICAL TEST
    """
    Test _get_timezone raises exception for invalid timezone strings.

    Tests that _get_timezone correctly rejects invalid timezone names
    including path traversal attempts.

    Parameters
    ----------
    invalid_tz : str
        Invalid timezone string to test

    Returns
    -------
    None
        Test passes if exception raised
    """
    # ACT & ASSERT
    with pytest.raises(Exception):  # ZoneInfo raises various exceptions for invalid timezones
        time_utils._get_timezone(invalid_tz)


@pytest.mark.skipif(ZoneInfo is None, reason="ZoneInfo not available (Python < 3.9)")
@pytest.mark.parametrize(
    "valid_tz",
    [
        "Europe/Berlin",
        "America/New_York",
        "Asia/Tokyo",
        "UTC",
        "Europe/London",
        "Australia/Sydney",
    ],
)
def test_get_timezone_handles_various_timezone_names(valid_tz: str) -> None:  # CRITICAL TEST
    """
    Test _get_timezone handles various valid timezone names.

    Tests that _get_timezone correctly creates ZoneInfo objects
    for common timezone strings.

    Parameters
    ----------
    valid_tz : str
        Valid timezone string to test

    Returns
    -------
    None
        Test passes if ZoneInfo created successfully
    """
    # ACT
    result: datetime.tzinfo = time_utils._get_timezone(valid_tz)

    # ASSERT
    assert isinstance(result, ZoneInfo)
    assert str(result) == valid_tz


def test_parse_iso_valid_iso_string_returns_datetime(sample_iso_strings: Dict[str, Any]) -> None:  # CRITICAL TEST
    """
    Test parse_iso parses valid ISO string to datetime.

    Tests that parse_iso correctly parses standard ISO 8601
    formatted datetime strings.

    Parameters
    ----------
    sample_iso_strings : Dict[str, Any]
        Fixture providing sample ISO strings

    Returns
    -------
    None
        Test passes if datetime parsed correctly
    """
    # ARRANGE
    iso_string: str = sample_iso_strings["valid"][0]

    # ACT
    result: datetime.datetime = time_utils.parse_iso(iso_string)

    # ASSERT
    assert isinstance(result, datetime.datetime)
    assert result.year == 2025
    assert result.month == 1
    assert result.day == 15


@pytest.mark.skipif(ZoneInfo is None, reason="ZoneInfo not available (Python < 3.9)")
def test_parse_iso_with_timezone_converts_correctly(sample_iso_strings: Dict[str, Any]) -> None:  # CRITICAL TEST
    """
    Test parse_iso converts to specified timezone correctly.

    Tests that parse_iso correctly converts parsed datetime
    to the specified target timezone.

    Parameters
    ----------
    sample_iso_strings : Dict[str, Any]
        Fixture providing sample ISO strings

    Returns
    -------
    None
        Test passes if timezone conversion correct
    """
    # ARRANGE
    iso_string: str = sample_iso_strings["valid"][0]
    target_tz: str = "Europe/Berlin"

    # ACT
    result: datetime.datetime = time_utils.parse_iso(iso_string, tz_str=target_tz)

    # ASSERT
    assert isinstance(result, datetime.datetime)
    assert isinstance(result.tzinfo, ZoneInfo)
    assert str(result.tzinfo) == target_tz


@pytest.mark.parametrize(
    "invalid_input",
    [
        "not-a-date",
        "2025-13-45",
        "2025-01-32T12:30:45",
        "invalid",
        "2025/01/15",
        "15-01-2025",
    ],
)
def test_parse_iso_raises_valueerror_when_invalid_format(invalid_input: str) -> None:  # CRITICAL TEST
    """
    Test parse_iso raises ValueError for invalid ISO format.

    Tests that parse_iso correctly rejects malformed
    datetime strings.

    Parameters
    ----------
    invalid_input : str
        Invalid datetime string

    Returns
    -------
    None
        Test passes if ValueError raised
    """
    # ACT & ASSERT
    with pytest.raises(ValueError):
        time_utils.parse_iso(invalid_input)


def test_parse_iso_raises_exception_when_empty_string() -> None:  # CRITICAL TEST
    """
    Test parse_iso raises exception when given empty string.

    Tests that parse_iso correctly rejects empty string input.

    Returns
    -------
    None
        Test passes if exception raised
    """
    # ARRANGE
    empty_string: str = ""

    # ACT & ASSERT
    with pytest.raises(ValueError):
        time_utils.parse_iso(empty_string)


@pytest.mark.skipif(ZoneInfo is None, reason="ZoneInfo not available (Python < 3.9)")
def test_parse_iso_raises_exception_when_invalid_timezone() -> None:  # CRITICAL TEST
    """
    Test parse_iso raises exception for invalid timezone.

    Tests that parse_iso correctly rejects invalid timezone
    strings when converting parsed datetime.

    Returns
    -------
    None
        Test passes if exception raised
    """
    # ARRANGE
    valid_iso: str = "2025-01-15T12:30:45+00:00"
    invalid_tz: str = "Invalid/Timezone"

    # ACT & ASSERT
    with pytest.raises(Exception):
        time_utils.parse_iso(valid_iso, tz_str=invalid_tz)


@pytest.mark.parametrize(
    "iso_string",
    [
        "2025-01-15T12:30:45+00:00",
        "2025-01-15T12:30:45Z",
        "2025-01-15T12:30:45.123456+00:00",
        "2025-01-15T12:30:45",
        "2025-01-15T12:30:45+01:00",
    ],
)
def test_parse_iso_handles_various_iso_formats(iso_string: str) -> None:  # CRITICAL TEST
    """
    Test parse_iso handles various valid ISO formats.

    Tests that parse_iso correctly parses different variations
    of ISO 8601 datetime formats.

    Parameters
    ----------
    iso_string : str
        ISO formatted datetime string

    Returns
    -------
    None
        Test passes if datetime parsed successfully
    """
    # ACT
    result: datetime.datetime = time_utils.parse_iso(iso_string)

    # ASSERT
    assert isinstance(result, datetime.datetime)
    assert result.year == 2025
    assert result.month == 1
    assert result.day == 15


def test_str_to_datetime_parses_valid_format_correctly() -> None:  # CRITICAL TEST
    """
    Test str_to_datetime parses datetime with valid format string.

    Tests that str_to_datetime correctly parses datetime string
    when given matching format string.

    Returns
    -------
    None
        Test passes if datetime parsed correctly
    """
    # ARRANGE
    date_string: str = "2025-01-15 12:30:45"
    format_string: str = "%Y-%m-%d %H:%M:%S"

    # ACT
    result: datetime.datetime = time_utils.str_to_datetime(date_string, format_string)

    # ASSERT
    assert isinstance(result, datetime.datetime)
    assert result.year == 2025
    assert result.month == 1
    assert result.day == 15
    assert result.hour == 12
    assert result.minute == 30
    assert result.second == 45


@pytest.mark.parametrize(
    "date_string,format_string",
    [
        ("2025-01-15", "%Y-%m-%d %H:%M:%S"),  # Missing time
        ("12:30:45", "%Y-%m-%d"),  # Missing date
        ("2025/01/15", "%Y-%m-%d"),  # Wrong separator
        ("Jan 15 2025", "%Y-%m-%d"),  # Completely different format
    ],
)
def test_str_to_datetime_raises_valueerror_when_format_mismatch(
    date_string: str, format_string: str
) -> None:  # CRITICAL TEST
    """
    Test str_to_datetime raises ValueError when format doesn't match.

    Tests that str_to_datetime correctly rejects datetime strings
    that don't match the provided format string.

    Parameters
    ----------
    date_string : str
        Datetime string to parse
    format_string : str
        Format string that doesn't match

    Returns
    -------
    None
        Test passes if ValueError raised
    """
    # ACT & ASSERT
    with pytest.raises(ValueError):
        time_utils.str_to_datetime(date_string, format_string)


@pytest.mark.parametrize(
    "invalid_format",
    [
        "%Q",  # Invalid directive
        "%Y-%m-%d %Z %Z",  # Duplicate timezone
        "",  # Empty format
    ],
)
def test_str_to_datetime_raises_valueerror_when_invalid_format(invalid_format: str) -> None:  # CRITICAL TEST
    """
    Test str_to_datetime raises ValueError for invalid format strings.

    Tests that str_to_datetime correctly rejects invalid
    strptime format strings.

    Parameters
    ----------
    invalid_format : str
        Invalid format string

    Returns
    -------
    None
        Test passes if ValueError raised
    """
    # ARRANGE
    date_string: str = "2025-01-15"

    # ACT & ASSERT
    with pytest.raises(ValueError):
        time_utils.str_to_datetime(date_string, invalid_format)


@pytest.mark.parametrize(
    "date_string,format_string",
    [
        ("2025-01-15", "%Y-%m-%d"),
        ("15/01/2025", "%d/%m/%Y"),
        ("Jan 15, 2025", "%b %d, %Y"),
        ("2025-01-15 12:30:45", "%Y-%m-%d %H:%M:%S"),
        ("20250115", "%Y%m%d"),
    ],
)
def test_str_to_datetime_handles_various_formats(date_string: str, format_string: str) -> None:  # CRITICAL TEST
    """
    Test str_to_datetime handles various datetime formats.

    Tests that str_to_datetime correctly parses different
    datetime format combinations.

    Parameters
    ----------
    date_string : str
        Datetime string to parse
    format_string : str
        Matching format string

    Returns
    -------
    None
        Test passes if datetime parsed successfully
    """
    # ACT
    result: datetime.datetime = time_utils.str_to_datetime(date_string, format_string)

    # ASSERT
    assert isinstance(result, datetime.datetime)
    assert result.year == 2025
    assert result.month == 1
    assert result.day == 15


# -------------------------------------------------------------
# TEST CASES - IMPORTANT FUNCTIONS
# -------------------------------------------------------------


def test_now_local_returns_aware_datetime() -> None:  # IMPORTANT TEST
    """
    Test now_local returns timezone-aware datetime.

    Tests that now_local correctly returns datetime with
    timezone information when called without arguments.

    Returns
    -------
    None
        Test passes if datetime is timezone-aware
    """
    # ACT
    result: datetime.datetime = time_utils.now_local()

    # ASSERT
    assert isinstance(result, datetime.datetime)
    assert result.tzinfo is not None


@pytest.mark.skipif(ZoneInfo is None, reason="ZoneInfo not available (Python < 3.9)")
def test_now_local_with_timezone_returns_correct_tz() -> None:  # IMPORTANT TEST
    """
    Test now_local returns datetime in specified timezone.

    Tests that now_local correctly returns datetime in
    the specified timezone when tz_str provided.

    Returns
    -------
    None
        Test passes if timezone matches requested
    """
    # ARRANGE
    tz_str: str = "Europe/Berlin"

    # ACT
    result: datetime.datetime = time_utils.now_local(tz_str=tz_str)

    # ASSERT
    assert isinstance(result, datetime.datetime)
    assert isinstance(result.tzinfo, ZoneInfo)
    assert str(result.tzinfo) == tz_str


@pytest.mark.skipif(ZoneInfo is None, reason="ZoneInfo not available (Python < 3.9)")
def test_now_local_raises_error_when_invalid_timezone() -> None:  # IMPORTANT TEST
    """
    Test now_local raises error for invalid timezone string.

    Tests that now_local correctly propagates exception
    when given invalid timezone string.

    Returns
    -------
    None
        Test passes if exception raised
    """
    # ARRANGE
    invalid_tz: str = "Invalid/Timezone"

    # ACT & ASSERT
    with pytest.raises(Exception):
        time_utils.now_local(tz_str=invalid_tz)


@pytest.mark.skipif(ZoneInfo is None, reason="ZoneInfo not available (Python < 3.9)")
def test_to_timezone_converts_datetime_correctly(fixed_utc_time: datetime.datetime) -> None:  # IMPORTANT TEST
    """
    Test to_timezone converts datetime to target timezone.

    Tests that to_timezone correctly converts datetime
    from one timezone to another.

    Parameters
    ----------
    fixed_utc_time : datetime.datetime
        Fixture providing fixed UTC datetime

    Returns
    -------
    None
        Test passes if conversion correct
    """
    # ARRANGE
    target_tz: str = "Europe/Berlin"

    # ACT
    result: datetime.datetime = time_utils.to_timezone(fixed_utc_time, target_tz)

    # ASSERT
    assert isinstance(result, datetime.datetime)
    assert isinstance(result.tzinfo, ZoneInfo)
    assert str(result.tzinfo) == target_tz
    # UTC 12:30 should be 13:30 or 14:30 in Berlin (depending on DST)
    assert result.year == fixed_utc_time.year
    assert result.month == fixed_utc_time.month
    assert result.day == fixed_utc_time.day


@pytest.mark.skipif(ZoneInfo is None, reason="ZoneInfo not available (Python < 3.9)")
def test_to_timezone_raises_error_when_invalid_timezone(
    fixed_utc_time: datetime.datetime,
) -> None:  # IMPORTANT TEST
    """
    Test to_timezone raises error for invalid timezone.

    Tests that to_timezone correctly raises exception
    when given invalid timezone string.

    Parameters
    ----------
    fixed_utc_time : datetime.datetime
        Fixture providing fixed UTC datetime

    Returns
    -------
    None
        Test passes if exception raised
    """
    # ARRANGE
    invalid_tz: str = "Invalid/Timezone"

    # ACT & ASSERT
    with pytest.raises(Exception):
        time_utils.to_timezone(fixed_utc_time, invalid_tz)


@pytest.mark.skipif(ZoneInfo is None, reason="ZoneInfo not available (Python < 3.9)")
def test_to_timezone_handles_naive_datetime() -> None:  # IMPORTANT TEST
    """
    Test to_timezone handles naive datetime correctly.

    Tests that to_timezone can convert naive datetime
    (without timezone info) to target timezone.

    Returns
    -------
    None
        Test passes if conversion succeeds or raises appropriate error
    """
    # ARRANGE
    naive_dt: datetime.datetime = datetime.datetime(2025, 1, 15, 12, 30, 45)
    target_tz: str = "Europe/Berlin"

    # ACT & ASSERT
    # Naive datetime may raise ValueError or convert with assumption
    try:
        result: datetime.datetime = time_utils.to_timezone(naive_dt, target_tz)
        assert isinstance(result, datetime.datetime)
    except ValueError:
        # Expected behavior for naive datetime
        pass


def test_format_iso_formats_aware_datetime_correctly(fixed_utc_time: datetime.datetime) -> None:  # IMPORTANT TEST
    """
    Test format_iso formats aware datetime to ISO string.

    Tests that format_iso correctly formats timezone-aware
    datetime to ISO 8601 string.

    Parameters
    ----------
    fixed_utc_time : datetime.datetime
        Fixture providing fixed UTC datetime

    Returns
    -------
    None
        Test passes if ISO string formatted correctly
    """
    # ACT
    result: str = time_utils.format_iso(fixed_utc_time)

    # ASSERT
    assert isinstance(result, str)
    assert "2025-01-15" in result
    assert "12:30:45" in result
    assert "+" in result or "Z" in result  # Timezone indicator


def test_format_iso_handles_datetime_with_different_timezone() -> None:  # IMPORTANT TEST
    """
    Test format_iso converts to UTC before formatting.

    Tests that format_iso correctly converts non-UTC timezone
    datetime to UTC before formatting to ISO string.

    Returns
    -------
    None
        Test passes if conversion to UTC occurs
    """
    # ARRANGE - Create datetime in specific timezone offset
    dt_with_offset: datetime.datetime = datetime.datetime(
        2025, 1, 15, 13, 30, 45, tzinfo=datetime.timezone(datetime.timedelta(hours=1))
    )

    # ACT
    result: str = time_utils.format_iso(dt_with_offset)

    # ASSERT
    assert isinstance(result, str)
    # Should be converted to UTC (12:30:45)
    assert "12:30:45" in result


def test_datetime_to_str_formats_correctly() -> None:  # IMPORTANT TEST
    """
    Test datetime_to_str formats datetime with custom format.

    Tests that datetime_to_str correctly formats datetime
    using provided strftime format string.

    Returns
    -------
    None
        Test passes if formatting correct
    """
    # ARRANGE
    dt: datetime.datetime = datetime.datetime(2025, 1, 15, 12, 30, 45)
    fmt: str = "%Y-%m-%d %H:%M:%S"

    # ACT
    result: str = time_utils.datetime_to_str(dt, fmt)

    # ASSERT
    assert isinstance(result, str)
    assert result == "2025-01-15 12:30:45"


@pytest.mark.parametrize(
    "dt,fmt,expected",
    [
        (datetime.datetime(2025, 1, 15, 12, 30, 45), "%Y-%m-%d", "2025-01-15"),
        (datetime.datetime(2025, 1, 15, 12, 30, 45), "%H:%M:%S", "12:30:45"),
        (datetime.datetime(2025, 1, 15, 12, 30, 45), "%d/%m/%Y", "15/01/2025"),
        (datetime.datetime(2025, 1, 15, 12, 30, 45), "%Y%m%d", "20250115"),
    ],
)
def test_datetime_to_str_handles_various_formats(
    dt: datetime.datetime, fmt: str, expected: str
) -> None:  # IMPORTANT TEST
    """
    Test datetime_to_str handles various format strings.

    Tests that datetime_to_str correctly formats datetime
    with different strftime format patterns.

    Parameters
    ----------
    dt : datetime.datetime
        Datetime to format
    fmt : str
        Format string
    expected : str
        Expected output

    Returns
    -------
    None
        Test passes if output matches expected
    """
    # ACT
    result: str = time_utils.datetime_to_str(dt, fmt)

    # ASSERT
    assert result == expected


def test_timestamp_to_datetime_converts_correctly(fixed_timestamp: float) -> None:  # IMPORTANT TEST
    """
    Test timestamp_to_datetime converts POSIX timestamp to datetime.

    Tests that timestamp_to_datetime correctly converts
    POSIX timestamp to UTC datetime object.

    Parameters
    ----------
    fixed_timestamp : float
        Fixture providing fixed timestamp

    Returns
    -------
    None
        Test passes if conversion correct
    """
    # ACT
    result: datetime.datetime = time_utils.timestamp_to_datetime(fixed_timestamp)

    # ASSERT
    assert isinstance(result, datetime.datetime)
    assert result.tzinfo == datetime.timezone.utc
    assert result.year == 2025
    assert result.month == 1
    assert result.day == 15


def test_timestamp_to_datetime_handles_zero_timestamp() -> None:  # IMPORTANT TEST
    """
    Test timestamp_to_datetime handles zero timestamp (epoch).

    Tests that timestamp_to_datetime correctly converts
    zero timestamp to Unix epoch datetime.

    Returns
    -------
    None
        Test passes if epoch datetime returned
    """
    # ARRANGE
    zero_timestamp: float = 0.0

    # ACT
    result: datetime.datetime = time_utils.timestamp_to_datetime(zero_timestamp)

    # ASSERT
    assert isinstance(result, datetime.datetime)
    assert result.year == 1970
    assert result.month == 1
    assert result.day == 1


def test_timestamp_to_datetime_handles_negative_timestamp() -> None:  # IMPORTANT TEST
    """
    Test timestamp_to_datetime handles negative timestamp.

    Tests that timestamp_to_datetime correctly handles
    negative POSIX timestamps (before 1970).

    Returns
    -------
    None
        Test passes if datetime before epoch returned
    """
    # ARRANGE
    negative_timestamp: float = -86400.0  # One day before epoch

    # ACT
    result: datetime.datetime = time_utils.timestamp_to_datetime(negative_timestamp)

    # ASSERT
    assert isinstance(result, datetime.datetime)
    assert result.year == 1969


def test_datetime_to_timestamp_converts_correctly(fixed_utc_time: datetime.datetime) -> None:  # IMPORTANT TEST
    """
    Test datetime_to_timestamp converts datetime to POSIX timestamp.

    Tests that datetime_to_timestamp correctly converts
    datetime object to POSIX timestamp.

    Parameters
    ----------
    fixed_utc_time : datetime.datetime
        Fixture providing fixed UTC datetime

    Returns
    -------
    None
        Test passes if conversion correct
    """
    # ACT
    result: float = time_utils.datetime_to_timestamp(fixed_utc_time)

    # ASSERT
    assert isinstance(result, float)
    assert result > 0
    # Verify round-trip conversion
    reconstructed: datetime.datetime = time_utils.timestamp_to_datetime(result)
    assert reconstructed == fixed_utc_time


def test_datetime_to_timestamp_handles_epoch() -> None:  # IMPORTANT TEST
    """
    Test datetime_to_timestamp handles Unix epoch datetime.

    Tests that datetime_to_timestamp correctly converts
    Unix epoch datetime to zero timestamp.

    Returns
    -------
    None
        Test passes if timestamp is zero
    """
    # ARRANGE
    epoch: datetime.datetime = datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)

    # ACT
    result: float = time_utils.datetime_to_timestamp(epoch)

    # ASSERT
    assert result == 0.0


# -------------------------------------------------------------
# TEST CASES - SIMPLE WRAPPER FUNCTIONS
# -------------------------------------------------------------


def test_now_utc_returns_aware_utc_datetime() -> None:
    """
    Test now_utc returns timezone-aware UTC datetime.

    Tests that now_utc correctly returns current datetime
    in UTC timezone with timezone info.

    Returns
    -------
    None
        Test passes if datetime is UTC-aware
    """
    # ACT
    result: datetime.datetime = time_utils.now_utc()

    # ASSERT
    assert isinstance(result, datetime.datetime)
    assert result.tzinfo == datetime.timezone.utc
    # Verify it's recent (within last minute)
    now: datetime.datetime = datetime.datetime.now(datetime.timezone.utc)
    time_diff: datetime.timedelta = abs(now - result)
    assert time_diff.total_seconds() < 60


def test_utc_timestamp_returns_float() -> None:
    """
    Test utc_timestamp returns float POSIX timestamp.

    Tests that utc_timestamp correctly returns current
    POSIX timestamp as float.

    Returns
    -------
    None
        Test passes if timestamp is valid float
    """
    # ACT
    result: float = time_utils.utc_timestamp()

    # ASSERT
    assert isinstance(result, float)
    assert result > 0
    # Verify it's recent (within last minute)
    now_ts: float = time.time()
    assert abs(now_ts - result) < 60


def test_utc_timestamp_matches_time_time() -> None:
    """
    Test utc_timestamp returns same value as time.time().

    Tests that utc_timestamp is equivalent to calling
    time.time() directly.

    Returns
    -------
    None
        Test passes if timestamps are nearly identical
    """
    # ACT
    result1: float = time_utils.utc_timestamp()
    result2: float = time.time()

    # ASSERT
    # Should be within microseconds of each other
    assert abs(result1 - result2) < 0.01


# -------------------------------------------------------------
# TEST CASES - EDGE CASES AND INTEGRATION
# -------------------------------------------------------------


def test_round_trip_iso_conversion(fixed_utc_time: datetime.datetime) -> None:
    """
    Test round-trip conversion: datetime -> ISO -> datetime.

    Tests that formatting to ISO and parsing back
    preserves datetime value (integration test).

    Parameters
    ----------
    fixed_utc_time : datetime.datetime
        Fixture providing fixed UTC datetime

    Returns
    -------
    None
        Test passes if round-trip preserves value
    """
    # ACT
    iso_string: str = time_utils.format_iso(fixed_utc_time)
    reconstructed: datetime.datetime = time_utils.parse_iso(iso_string)

    # ASSERT
    # Compare timestamps to avoid microsecond precision issues
    assert abs(reconstructed.timestamp() - fixed_utc_time.timestamp()) < 0.001


def test_round_trip_timestamp_conversion(fixed_utc_time: datetime.datetime) -> None:
    """
    Test round-trip conversion: datetime -> timestamp -> datetime.

    Tests that converting to timestamp and back
    preserves datetime value (integration test).

    Parameters
    ----------
    fixed_utc_time : datetime.datetime
        Fixture providing fixed UTC datetime

    Returns
    -------
    None
        Test passes if round-trip preserves value
    """
    # ACT
    timestamp: float = time_utils.datetime_to_timestamp(fixed_utc_time)
    reconstructed: datetime.datetime = time_utils.timestamp_to_datetime(timestamp)

    # ASSERT
    assert reconstructed == fixed_utc_time


def test_round_trip_string_conversion() -> None:
    """
    Test round-trip conversion: datetime -> str -> datetime.

    Tests that formatting with custom format and parsing back
    preserves datetime value (integration test).

    Returns
    -------
    None
        Test passes if round-trip preserves value
    """
    # ARRANGE
    original: datetime.datetime = datetime.datetime(2025, 1, 15, 12, 30, 45)
    fmt: str = "%Y-%m-%d %H:%M:%S"

    # ACT
    string_repr: str = time_utils.datetime_to_str(original, fmt)
    reconstructed: datetime.datetime = time_utils.str_to_datetime(string_repr, fmt)

    # ASSERT
    assert reconstructed == original


@pytest.mark.skipif(ZoneInfo is None, reason="ZoneInfo not available (Python < 3.9)")
def test_timezone_conversion_preserves_instant() -> None:
    """
    Test timezone conversion preserves same instant in time.

    Tests that converting datetime between timezones
    preserves the actual moment in time (timestamp).

    Returns
    -------
    None
        Test passes if timestamps match
    """
    # ARRANGE
    utc_time: datetime.datetime = datetime.datetime(2025, 1, 15, 12, 0, 0, tzinfo=datetime.timezone.utc)

    # ACT
    berlin_time: datetime.datetime = time_utils.to_timezone(utc_time, "Europe/Berlin")
    tokyo_time: datetime.datetime = time_utils.to_timezone(utc_time, "Asia/Tokyo")

    # ASSERT
    # All should represent the same instant
    assert utc_time.timestamp() == berlin_time.timestamp()
    assert utc_time.timestamp() == tokyo_time.timestamp()
    # But have different wall clock times
    assert utc_time.hour != berlin_time.hour or utc_time.hour != tokyo_time.hour
