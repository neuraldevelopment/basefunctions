"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Utility functions including decorators, logging, time utilities,
 caching, observer pattern, and data generation
 Log:
 v1.0 : Initial implementation
=============================================================================
"""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Decorators
from basefunctions.utils.decorators import (
    function_timer,
    singleton,
    auto_property,
    assert_non_null_args,
    cache_results,
    catch_exceptions,
    profile_memory,
    retry_on_exception,
    suppress,
    thread_safe,
    warn_if_slow,
)

# Logging
from basefunctions.utils.logging import (
    setup_logger,
    get_logger,
    enable_console,
    disable_console,
    redirect_all_to_file,
)

# Time Utilities
from basefunctions.utils.time_utils import (
    now_utc,
    now_local,
    utc_timestamp,
    format_iso,
    parse_iso,
    to_timezone,
    datetime_to_str,
    str_to_datetime,
    timestamp_to_datetime,
    datetime_to_timestamp,
)

# Cache Manager
from basefunctions.utils.cache_manager import (
    CacheManager,
    CacheFactory,
    CacheBackend,
    MemoryBackend,
    DatabaseBackend,
    FileBackend,
    MultiLevelBackend,
    CacheError,
    CacheBackendError,
    get_cache,
)

# Observer Pattern
from basefunctions.utils.observer import Observer, Observable

# Protocols (re-exported from centralized protocols module for backward compatibility)
from basefunctions.protocols import MetricsSource

# Data Generation
from basefunctions.utils.ohlcv_generator import OHLCVGenerator

# Demo Runner
from basefunctions.utils.demo_runner import DemoRunner, run, test

# Progress Tracking
from basefunctions.utils.progress_tracker import ProgressTracker, AliveProgressTracker

# =============================================================================
# EXPORT DEFINITIONS
# =============================================================================
__all__ = [
    # Decorators
    "function_timer",
    "singleton",
    "auto_property",
    "assert_non_null_args",
    "cache_results",
    "catch_exceptions",
    "profile_memory",
    "retry_on_exception",
    "suppress",
    "thread_safe",
    "warn_if_slow",
    # Logging
    "setup_logger",
    "get_logger",
    "enable_console",
    "disable_console",
    "redirect_all_to_file",
    # Time Utilities
    "now_utc",
    "now_local",
    "utc_timestamp",
    "format_iso",
    "parse_iso",
    "to_timezone",
    "datetime_to_str",
    "str_to_datetime",
    "timestamp_to_datetime",
    "datetime_to_timestamp",
    # Cache Manager
    "CacheManager",
    "CacheFactory",
    "CacheBackend",
    "MemoryBackend",
    "DatabaseBackend",
    "FileBackend",
    "MultiLevelBackend",
    "CacheError",
    "CacheBackendError",
    "get_cache",
    # Observer Pattern
    "Observer",
    "Observable",
    # Protocols
    "MetricsSource",
    # Data Generation
    "OHLCVGenerator",
    # Demo Runner
    "DemoRunner",
    "run",
    "test",
    # Progress Tracking
    "ProgressTracker",
    "AliveProgressTracker",
]
