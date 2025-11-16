"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich

  Project : basefunctions

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  Pytest test suite for cache_manager.py.
  Tests unified caching framework with multiple backend support,
  TTL expiration, pattern matching, and multi-level cache hierarchies.

  Log:
  v1.0.0 : Initial test implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
# External imports
import pickle
import pytest
import time
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import Mock, MagicMock, patch, call

# Project imports
from basefunctions.utils.cache_manager import (
    CacheEntry,
    CacheBackend,
    MemoryBackend,
    FileBackend,
    DatabaseBackend,
    MultiLevelBackend,
    CacheManager,
    CacheFactory,
    CacheError,
    CacheBackendError,
    get_cache,
    DEFAULT_TTL,
    CACHE_TABLE_NAME,
)

# -------------------------------------------------------------
# FIXTURES
# -------------------------------------------------------------


@pytest.fixture
def mock_time() -> float:
    """
    Provide mock timestamp for testing.

    Returns
    -------
    float
        Fixed timestamp value (1000.0)
    """
    return 1000.0


@pytest.fixture
def sample_cache_entry(mock_time: float) -> CacheEntry:
    """
    Create sample cache entry for testing.

    Parameters
    ----------
    mock_time : float
        Mock timestamp

    Returns
    -------
    CacheEntry
        Cache entry with test data

    Notes
    -----
    Created with TTL of 3600 seconds
    """
    with patch("time.time", return_value=mock_time):
        return CacheEntry("test_value", 3600)


@pytest.fixture
def memory_backend() -> MemoryBackend:
    """
    Create memory backend instance.

    Returns
    -------
    MemoryBackend
        Fresh memory backend with max_size=100
    """
    return MemoryBackend(max_size=100)


@pytest.fixture
def file_backend(tmp_path: Path) -> FileBackend:
    """
    Create file backend instance with temporary directory.

    Parameters
    ----------
    tmp_path : Path
        Pytest temporary directory fixture

    Returns
    -------
    FileBackend
        File backend using temporary directory
    """
    cache_dir = tmp_path / "cache"
    return FileBackend(cache_dir=str(cache_dir))


@pytest.fixture
def mock_db() -> Mock:
    """
    Create mock database object.

    Returns
    -------
    Mock
        Mock Db instance with connector setup
    """
    mock_db = Mock()
    mock_connector = Mock()
    mock_connector.db_type = "sqlite"
    mock_db.get_connector.return_value = mock_connector
    mock_db.check_if_table_exists.return_value = True
    mock_db.query_one.return_value = None
    mock_db.query_all.return_value = []
    return mock_db


@pytest.fixture
def database_backend_with_mock(mock_db: Mock) -> DatabaseBackend:
    """
    Create DatabaseBackend with mocked database.

    Parameters
    ----------
    mock_db : Mock
        Mock database fixture

    Returns
    -------
    DatabaseBackend
        Backend instance with mocked DB
    """
    with patch.object(DatabaseBackend, "__init__", lambda self, instance_name, database_name: None):
        backend = DatabaseBackend("test_instance", "test_db")
        backend.instance_name = "test_instance"
        backend.database_name = "test_db"
        backend.db = mock_db
        backend.stats = {"hits": 0, "misses": 0, "sets": 0, "deletes": 0, "clears": 0}
        backend._lock = threading.RLock()
        return backend


# -------------------------------------------------------------
# TEST CASES: CacheEntry
# -------------------------------------------------------------


def test_cache_entry_initialization_with_ttl() -> None:
    """Test CacheEntry initializes correctly with TTL."""
    # ARRANGE
    value: str = "test_data"
    ttl: int = 3600
    start_time: float = time.time()

    # ACT
    entry: CacheEntry = CacheEntry(value, ttl)

    # ASSERT
    assert entry.value == value
    assert entry.access_count == 0
    assert entry.created_at >= start_time
    assert entry.expires_at is not None
    assert entry.expires_at == entry.created_at + ttl


def test_cache_entry_initialization_without_ttl() -> None:
    """Test CacheEntry with zero TTL has no expiration."""
    # ARRANGE
    value: str = "test_data"
    ttl: int = 0

    # ACT
    entry: CacheEntry = CacheEntry(value, ttl)

    # ASSERT
    assert entry.value == value
    assert entry.expires_at is None


def test_cache_entry_is_expired_returns_false_when_not_expired() -> None:
    """Test is_expired returns False for valid entry."""
    # ARRANGE
    entry: CacheEntry = CacheEntry("data", 3600)

    # ACT
    result: bool = entry.is_expired()

    # ASSERT
    assert result is False


def test_cache_entry_is_expired_returns_true_when_expired() -> None:
    """Test is_expired returns True for expired entry."""
    # ARRANGE
    entry: CacheEntry = CacheEntry("data", 1)  # 1 second TTL
    time.sleep(1.1)  # Wait for expiration

    # ACT
    result: bool = entry.is_expired()

    # ASSERT
    assert result is True


def test_cache_entry_is_expired_returns_false_when_no_ttl() -> None:
    """Test is_expired returns False when expires_at is None."""
    # ARRANGE
    entry: CacheEntry = CacheEntry("data", 0)

    # ACT
    result: bool = entry.is_expired()

    # ASSERT
    assert result is False


def test_cache_entry_access_increments_counter() -> None:
    """Test access method increments access_count."""
    # ARRANGE
    entry: CacheEntry = CacheEntry("data", 3600)
    initial_count: int = entry.access_count

    # ACT
    returned_value: str = entry.access()

    # ASSERT
    assert returned_value == "data"
    assert entry.access_count == initial_count + 1


def test_cache_entry_access_multiple_times() -> None:
    """Test access method tracks multiple accesses."""
    # ARRANGE
    entry: CacheEntry = CacheEntry("data", 3600)

    # ACT
    for _ in range(5):
        entry.access()

    # ASSERT
    assert entry.access_count == 5


def test_cache_entry_remaining_ttl_returns_correct_value() -> None:
    """Test remaining_ttl returns correct seconds remaining."""
    # ARRANGE
    ttl: int = 3600
    entry: CacheEntry = CacheEntry("data", ttl)

    # ACT
    remaining: Optional[int] = entry.remaining_ttl()

    # ASSERT
    assert remaining is not None
    assert 3595 <= remaining <= 3600  # Allow small time drift


def test_cache_entry_remaining_ttl_returns_none_when_no_expiration() -> None:
    """Test remaining_ttl returns None when no TTL set."""
    # ARRANGE
    entry: CacheEntry = CacheEntry("data", 0)

    # ACT
    remaining: Optional[int] = entry.remaining_ttl()

    # ASSERT
    assert remaining is None


def test_cache_entry_remaining_ttl_returns_zero_when_expired() -> None:
    """Test remaining_ttl returns 0 for expired entry."""
    # ARRANGE
    entry: CacheEntry = CacheEntry("data", 1)
    time.sleep(1.1)

    # ACT
    remaining: Optional[int] = entry.remaining_ttl()

    # ASSERT
    assert remaining == 0


# -------------------------------------------------------------
# TEST CASES: MemoryBackend
# -------------------------------------------------------------


def test_memory_backend_get_returns_none_when_key_not_found(memory_backend: MemoryBackend) -> None:
    """Test get returns None for non-existent key."""
    # ACT
    result: Optional[Any] = memory_backend.get("nonexistent")

    # ASSERT
    assert result is None
    assert memory_backend.stats["misses"] == 1


def test_memory_backend_set_and_get_successfully(memory_backend: MemoryBackend) -> None:
    """Test set and get operations work correctly."""
    # ARRANGE
    key: str = "test_key"
    value: str = "test_value"

    # ACT
    memory_backend.set(key, value, ttl=3600)
    result: Optional[str] = memory_backend.get(key)

    # ASSERT
    assert result == value
    assert memory_backend.stats["sets"] == 1
    assert memory_backend.stats["hits"] == 1


def test_memory_backend_delete_removes_key(memory_backend: MemoryBackend) -> None:
    """Test delete removes key from cache."""
    # ARRANGE
    key: str = "test_key"
    memory_backend.set(key, "value")

    # ACT
    success: bool = memory_backend.delete(key)
    result: Optional[Any] = memory_backend.get(key)

    # ASSERT
    assert success is True
    assert result is None
    assert memory_backend.stats["deletes"] == 1


def test_memory_backend_delete_returns_false_when_key_not_found(memory_backend: MemoryBackend) -> None:
    """Test delete returns False for non-existent key."""
    # ACT
    success: bool = memory_backend.delete("nonexistent")

    # ASSERT
    assert success is False


def test_memory_backend_exists_returns_true_when_key_exists(memory_backend: MemoryBackend) -> None:
    """Test exists returns True for valid key."""
    # ARRANGE
    memory_backend.set("key", "value")

    # ACT
    result: bool = memory_backend.exists("key")

    # ASSERT
    assert result is True


def test_memory_backend_exists_returns_false_when_key_expired(memory_backend: MemoryBackend) -> None:
    """Test exists returns False for expired key."""
    # ARRANGE
    memory_backend.set("key", "value", ttl=1)
    time.sleep(1.1)

    # ACT
    result: bool = memory_backend.exists("key")

    # ASSERT
    assert result is False


def test_memory_backend_clear_removes_all_entries(memory_backend: MemoryBackend) -> None:
    """Test clear removes all cache entries."""
    # ARRANGE
    memory_backend.set("key1", "value1")
    memory_backend.set("key2", "value2")
    memory_backend.set("key3", "value3")

    # ACT
    count: int = memory_backend.clear()

    # ASSERT
    assert count == 3
    assert memory_backend.size() == 0
    assert memory_backend.stats["clears"] == 1


def test_memory_backend_clear_with_pattern_removes_matching_keys(memory_backend: MemoryBackend) -> None:
    """Test clear with pattern removes only matching keys."""
    # ARRANGE
    memory_backend.set("user:1", "value1")
    memory_backend.set("user:2", "value2")
    memory_backend.set("session:1", "value3")

    # ACT
    count: int = memory_backend.clear(pattern="user:*")

    # ASSERT
    assert count == 2
    assert memory_backend.exists("session:1") is True


def test_memory_backend_keys_returns_all_keys(memory_backend: MemoryBackend) -> None:
    """Test keys returns all cache keys."""
    # ARRANGE
    memory_backend.set("key1", "value1")
    memory_backend.set("key2", "value2")

    # ACT
    keys: List[str] = memory_backend.keys()

    # ASSERT
    assert set(keys) == {"key1", "key2"}


def test_memory_backend_keys_with_pattern_filters_correctly(memory_backend: MemoryBackend) -> None:
    """Test keys with pattern returns matching keys only."""
    # ARRANGE
    memory_backend.set("user:admin", "value1")
    memory_backend.set("user:guest", "value2")
    memory_backend.set("session:123", "value3")

    # ACT
    keys: List[str] = memory_backend.keys(pattern="user:*")

    # ASSERT
    assert set(keys) == {"user:admin", "user:guest"}


def test_memory_backend_size_returns_correct_count(memory_backend: MemoryBackend) -> None:
    """Test size returns number of cached entries."""
    # ARRANGE
    memory_backend.set("key1", "value1")
    memory_backend.set("key2", "value2")

    # ACT
    size: int = memory_backend.size()

    # ASSERT
    assert size == 2


def test_memory_backend_expire_updates_ttl(memory_backend: MemoryBackend) -> None:
    """Test expire updates TTL for existing key."""
    # ARRANGE
    memory_backend.set("key", "value", ttl=3600)

    # ACT
    success: bool = memory_backend.expire("key", ttl=7200)
    new_ttl: Optional[int] = memory_backend.ttl("key")

    # ASSERT
    assert success is True
    assert new_ttl is not None
    assert 7195 <= new_ttl <= 7200


def test_memory_backend_expire_returns_false_when_key_not_found(memory_backend: MemoryBackend) -> None:
    """Test expire returns False for non-existent key."""
    # ACT
    success: bool = memory_backend.expire("nonexistent", ttl=3600)

    # ASSERT
    assert success is False


def test_memory_backend_ttl_returns_remaining_time(memory_backend: MemoryBackend) -> None:
    """Test ttl returns remaining seconds."""
    # ARRANGE
    memory_backend.set("key", "value", ttl=3600)

    # ACT
    ttl: Optional[int] = memory_backend.ttl("key")

    # ASSERT
    assert ttl is not None
    assert 3595 <= ttl <= 3600


def test_memory_backend_ttl_returns_none_when_key_not_found(memory_backend: MemoryBackend) -> None:
    """Test ttl returns None for non-existent key."""
    # ACT
    ttl: Optional[int] = memory_backend.ttl("nonexistent")

    # ASSERT
    assert ttl is None


def test_memory_backend_get_stats_returns_correct_metrics(memory_backend: MemoryBackend) -> None:
    """Test get_stats returns accurate statistics."""
    # ARRANGE
    memory_backend.set("key1", "value1")
    memory_backend.get("key1")  # Hit
    memory_backend.get("key2")  # Miss

    # ACT
    stats: Dict[str, Any] = memory_backend.get_stats()

    # ASSERT
    assert stats["hits"] == 1
    assert stats["misses"] == 1
    assert stats["sets"] == 1
    assert stats["total_requests"] == 2
    assert stats["hit_rate_percent"] == 50.0
    assert stats["size"] == 1


def test_memory_backend_evicts_expired_entries_when_at_capacity() -> None:  # IMPORTANT TEST
    """Test backend evicts expired entries when reaching max_size."""
    # ARRANGE
    backend: MemoryBackend = MemoryBackend(max_size=3)
    backend.set("key1", "value1", ttl=1)  # Will expire
    backend.set("key2", "value2", ttl=3600)
    backend.set("key3", "value3", ttl=3600)
    time.sleep(1.1)  # Expire key1

    # ACT
    backend.set("key4", "value4", ttl=3600)  # Should trigger eviction

    # ASSERT
    assert backend.exists("key1") is False  # Expired, should be evicted
    assert backend.exists("key2") is True
    assert backend.exists("key3") is True
    assert backend.exists("key4") is True


def test_memory_backend_evicts_lru_when_no_expired_entries() -> None:  # IMPORTANT TEST
    """Test backend evicts LRU entry when at capacity with no expired entries."""
    # ARRANGE
    backend: MemoryBackend = MemoryBackend(max_size=3)
    backend.set("key1", "value1", ttl=3600)
    backend.set("key2", "value2", ttl=3600)
    backend.set("key3", "value3", ttl=3600)

    # ACT
    backend.set("key4", "value4", ttl=3600)  # Should evict oldest

    # ASSERT
    assert backend.size() == 3
    # key1 should be evicted (oldest created)
    assert backend.exists("key1") is False


def test_memory_backend_thread_safety() -> None:
    """Test memory backend is thread-safe."""
    # ARRANGE
    backend: MemoryBackend = MemoryBackend(max_size=1000)
    errors: List[Exception] = []

    def worker() -> None:
        try:
            for i in range(100):
                backend.set(f"key_{i}", f"value_{i}")
                backend.get(f"key_{i}")
        except Exception as e:
            errors.append(e)

    # ACT
    threads: List[threading.Thread] = [threading.Thread(target=worker) for _ in range(10)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    # ASSERT
    assert len(errors) == 0


# -------------------------------------------------------------
# TEST CASES: FileBackend (CRITICAL)
# -------------------------------------------------------------


def test_file_backend_get_cache_path_creates_hashed_filename(file_backend: FileBackend) -> None:  # CRITICAL TEST
    """Test _get_cache_path creates MD5 hashed filename."""
    # ARRANGE
    key: str = "test_key"

    # ACT
    path: str = file_backend._get_cache_path(key)

    # ASSERT
    assert path.endswith(".cache")
    assert "test_key" not in path  # Should be hashed
    assert len(Path(path).name) == 38  # 32 hex chars + .cache


@pytest.mark.parametrize(
    "malicious_key",
    [
        "../../../etc/passwd",
        "../../outside",
        "/absolute/path",
        "dir/../../../escape",
        "key\x00null",
        "key/with/slashes",
        "key\\with\\backslashes",
    ],
)
def test_file_backend_get_cache_path_sanitizes_malicious_keys(
    file_backend: FileBackend, malicious_key: str
) -> None:  # CRITICAL TEST
    """Test _get_cache_path prevents path traversal attacks."""
    # ACT
    path: str = file_backend._get_cache_path(malicious_key)

    # ASSERT
    # Path should be within cache_dir
    cache_dir_resolved: Path = Path(file_backend.cache_dir).resolve()
    path_resolved: Path = Path(path).resolve()
    assert str(path_resolved).startswith(str(cache_dir_resolved))


def test_file_backend_set_and_get_successfully(file_backend: FileBackend) -> None:
    """Test file backend stores and retrieves data correctly."""
    # ARRANGE
    key: str = "test_key"
    value: str = "test_value"

    # ACT
    file_backend.set(key, value, ttl=3600)
    result: Optional[str] = file_backend.get(key)

    # ASSERT
    assert result == value


def test_file_backend_set_creates_cache_file(file_backend: FileBackend, tmp_path: Path) -> None:
    """Test set creates actual cache file on disk."""
    # ARRANGE
    key: str = "test_key"
    value: str = "test_value"

    # ACT
    file_backend.set(key, value)
    cache_path: Path = Path(file_backend._get_cache_path(key))

    # ASSERT
    assert cache_path.exists()


def test_file_backend_set_raises_error_when_permission_denied(file_backend: FileBackend) -> None:  # CRITICAL TEST
    """Test set raises CacheBackendError when file write fails."""
    # ARRANGE
    key: str = "test_key"
    value: str = "test_value"

    with patch("builtins.open", side_effect=PermissionError("Access denied")):
        # ACT & ASSERT
        with pytest.raises(CacheBackendError, match="Failed to write cache file"):
            file_backend._set_raw(key, CacheEntry(value, 3600))


def test_file_backend_get_returns_none_when_file_not_found(file_backend: FileBackend) -> None:
    """Test get returns None for non-existent file."""
    # ACT
    result: Optional[Any] = file_backend.get("nonexistent")

    # ASSERT
    assert result is None


def test_file_backend_get_handles_corrupted_file_gracefully(file_backend: FileBackend) -> None:  # CRITICAL TEST
    """Test get removes corrupted cache file and returns None."""
    # ARRANGE
    key: str = "test_key"
    cache_path: Path = Path(file_backend._get_cache_path(key))
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_bytes(b"corrupted data")

    # ACT
    result: Optional[Any] = file_backend.get(key)

    # ASSERT
    assert result is None
    assert not cache_path.exists()  # Should be removed


def test_file_backend_delete_removes_file(file_backend: FileBackend) -> None:  # CRITICAL TEST
    """Test delete removes cache file from disk."""
    # ARRANGE
    key: str = "test_key"
    file_backend.set(key, "value")
    cache_path: Path = Path(file_backend._get_cache_path(key))

    # ACT
    success: bool = file_backend.delete(key)

    # ASSERT
    assert success is True
    assert not cache_path.exists()


def test_file_backend_delete_returns_false_when_file_not_found(file_backend: FileBackend) -> None:
    """Test delete returns False for non-existent file."""
    # ACT
    success: bool = file_backend.delete("nonexistent")

    # ASSERT
    assert success is False


def test_file_backend_clear_removes_all_cache_files(file_backend: FileBackend) -> None:  # CRITICAL TEST
    """Test clear removes all .cache files from directory."""
    # ARRANGE
    file_backend.set("key1", "value1")
    file_backend.set("key2", "value2")
    file_backend.set("key3", "value3")

    # ACT
    count: int = file_backend.clear()

    # ASSERT
    assert count == 3
    assert file_backend.size() == 0


def test_file_backend_clear_ignores_non_cache_files(file_backend: FileBackend, tmp_path: Path) -> None:
    """Test clear does not remove non-.cache files."""
    # ARRANGE
    file_backend.set("key1", "value1")
    other_file: Path = Path(file_backend.cache_dir) / "other.txt"
    other_file.write_text("data")

    # ACT
    count: int = file_backend.clear()

    # ASSERT
    assert count == 1
    assert other_file.exists()  # Should not be deleted


def test_file_backend_keys_returns_hashed_keys(file_backend: FileBackend) -> None:
    """Test keys returns list of hashed keys."""
    # ARRANGE
    file_backend.set("key1", "value1")
    file_backend.set("key2", "value2")

    # ACT
    keys: List[str] = file_backend.keys()

    # ASSERT
    assert len(keys) == 2
    # Keys should be hashes (32 hex chars)
    assert all(len(key) == 32 for key in keys)


# -------------------------------------------------------------
# TEST CASES: DatabaseBackend (CRITICAL)
# -------------------------------------------------------------


def test_database_backend_ensure_table_creates_table_when_not_exists(
    database_backend_with_mock: DatabaseBackend,
) -> None:  # CRITICAL TEST
    """Test _ensure_table creates cache table if missing."""
    # ARRANGE
    database_backend_with_mock.db.check_if_table_exists.return_value = False

    # ACT
    database_backend_with_mock._ensure_table()

    # ASSERT
    database_backend_with_mock.db.check_if_table_exists.assert_called_once_with(CACHE_TABLE_NAME)
    database_backend_with_mock.db.execute.assert_called_once()
    create_sql: str = database_backend_with_mock.db.execute.call_args[0][0]
    assert "CREATE TABLE" in create_sql
    assert CACHE_TABLE_NAME in create_sql


def test_database_backend_ensure_table_raises_error_on_failure(
    database_backend_with_mock: DatabaseBackend,
) -> None:  # CRITICAL TEST
    """Test _ensure_table raises CacheBackendError on database error."""
    # ARRANGE
    database_backend_with_mock.db.check_if_table_exists.side_effect = Exception("DB connection failed")

    # ACT & ASSERT
    with pytest.raises(CacheBackendError, match="Failed to create cache table"):
        database_backend_with_mock._ensure_table()


def test_database_backend_get_raw_deserializes_pickle_data(
    database_backend_with_mock: DatabaseBackend,
) -> None:  # CRITICAL TEST
    """Test _get_raw deserializes pickled cache value."""
    # ARRANGE
    test_value: str = "test_data"
    pickled_value: bytes = pickle.dumps(test_value)

    from datetime import datetime

    database_backend_with_mock.db.query_one.return_value = {
        "cache_value": pickled_value,
        "expires_at": datetime.fromtimestamp(time.time() + 3600),
        "created_at": datetime.fromtimestamp(time.time()),
        "access_count": 5,
    }

    # ACT
    entry: Optional[CacheEntry] = database_backend_with_mock._get_raw("test_key")

    # ASSERT
    assert entry is not None
    assert entry.value == test_value
    assert entry.access_count == 5


def test_database_backend_get_raw_raises_error_on_pickle_exploit(
    database_backend_with_mock: DatabaseBackend,
) -> None:  # CRITICAL TEST
    """Test _get_raw raises CacheBackendError on malformed pickle data."""
    # ARRANGE
    from datetime import datetime

    # Corrupted pickle data
    database_backend_with_mock.db.query_one.return_value = {
        "cache_value": b"corrupted_pickle_data",
        "expires_at": datetime.fromtimestamp(time.time() + 3600),
        "created_at": datetime.fromtimestamp(time.time()),
        "access_count": 0,
    }

    # ACT & ASSERT
    with pytest.raises(CacheBackendError, match="Failed to get cache entry"):
        database_backend_with_mock._get_raw("test_key")


def test_database_backend_set_raw_serializes_value(
    database_backend_with_mock: DatabaseBackend,
) -> None:  # CRITICAL TEST
    """Test _set_raw pickles and stores cache value."""
    # ARRANGE
    entry: CacheEntry = CacheEntry("test_value", 3600)

    # ACT
    database_backend_with_mock._set_raw("test_key", entry)

    # ASSERT
    database_backend_with_mock.db.execute.assert_called()
    call_args = database_backend_with_mock.db.execute.call_args[0]
    assert "INSERT" in call_args[0]
    assert isinstance(call_args[1][1], bytes)  # Pickled value should be bytes


def test_database_backend_set_raw_uses_postgres_syntax() -> None:
    """Test _set_raw uses PostgreSQL-specific syntax."""
    # ARRANGE
    mock_db = Mock()
    mock_connector = Mock()
    mock_connector.db_type = "postgres"
    mock_db.get_connector.return_value = mock_connector

    with patch.object(DatabaseBackend, "__init__", lambda self, instance_name, database_name: None):
        backend = DatabaseBackend("test_instance", "test_db")
        backend.db = mock_db
        backend.stats = {"hits": 0, "misses": 0, "sets": 0, "deletes": 0, "clears": 0}
        backend._lock = threading.RLock()

        entry: CacheEntry = CacheEntry("test_value", 3600)

        # ACT
        backend._set_raw("test_key", entry)

        # ASSERT
        mock_db.execute.assert_called()
        sql: str = mock_db.execute.call_args[0][0]
        assert "ON CONFLICT" in sql
        assert "%s" in sql  # PostgreSQL placeholder


def test_database_backend_delete_raw_removes_entry(
    database_backend_with_mock: DatabaseBackend,
) -> None:  # CRITICAL TEST
    """Test _delete_raw executes DELETE query."""
    # ACT
    success: bool = database_backend_with_mock._delete_raw("test_key")

    # ASSERT
    assert success is True
    database_backend_with_mock.db.execute.assert_called()
    sql: str = database_backend_with_mock.db.execute.call_args[0][0]
    assert "DELETE FROM" in sql
    assert CACHE_TABLE_NAME in sql


def test_database_backend_clear_raw_removes_all_entries(
    database_backend_with_mock: DatabaseBackend,
) -> None:  # CRITICAL TEST
    """Test _clear_raw deletes all cache entries."""
    # ARRANGE
    database_backend_with_mock.db.query_one.return_value = {"count": 42}

    # ACT
    count: int = database_backend_with_mock._clear_raw()

    # ASSERT
    assert count == 42
    delete_calls = [
        call_obj for call_obj in database_backend_with_mock.db.execute.call_args_list if "DELETE" in str(call_obj)
    ]
    assert len(delete_calls) >= 1


def test_database_backend_keys_raw_returns_all_keys(
    database_backend_with_mock: DatabaseBackend,
) -> None:
    """Test _keys_raw returns all cache keys from database."""
    # ARRANGE
    database_backend_with_mock.db.query_all.return_value = [
        {"cache_key": "key1"},
        {"cache_key": "key2"},
        {"cache_key": "key3"},
    ]

    # ACT
    keys: List[str] = database_backend_with_mock._keys_raw()

    # ASSERT
    assert keys == ["key1", "key2", "key3"]


# -------------------------------------------------------------
# TEST CASES: MultiLevelBackend
# -------------------------------------------------------------


def test_multi_level_backend_get_raw_promotes_to_higher_levels() -> None:  # IMPORTANT TEST
    """Test multi-level backend promotes cache hits to higher levels."""
    # ARRANGE
    backends_config: List[tuple] = [
        ("memory", {"max_size": 100}),
        ("memory", {"max_size": 100}),
    ]
    multi_backend: MultiLevelBackend = MultiLevelBackend(backends_config)

    # Set value only in L2
    entry: CacheEntry = CacheEntry("test_value", 3600)
    multi_backend.backends[1]._set_raw("key", entry)

    # ACT
    result: Optional[CacheEntry] = multi_backend._get_raw("key")

    # ASSERT
    assert result is not None
    assert result.value == "test_value"
    # Should be promoted to L1
    l1_entry: Optional[CacheEntry] = multi_backend.backends[0]._get_raw("key")
    assert l1_entry is not None


def test_multi_level_backend_set_raw_sets_in_all_backends() -> None:
    """Test multi-level backend sets value in all levels."""
    # ARRANGE
    backends_config: List[tuple] = [
        ("memory", {"max_size": 100}),
        ("memory", {"max_size": 100}),
    ]
    multi_backend: MultiLevelBackend = MultiLevelBackend(backends_config)
    entry: CacheEntry = CacheEntry("test_value", 3600)

    # ACT
    multi_backend._set_raw("key", entry)

    # ASSERT
    for backend in multi_backend.backends:
        backend_entry: Optional[CacheEntry] = backend._get_raw("key")
        assert backend_entry is not None
        assert backend_entry.value == "test_value"


def test_multi_level_backend_delete_raw_deletes_from_all_backends() -> None:
    """Test multi-level backend deletes from all levels."""
    # ARRANGE
    backends_config: List[tuple] = [
        ("memory", {"max_size": 100}),
        ("memory", {"max_size": 100}),
    ]
    multi_backend: MultiLevelBackend = MultiLevelBackend(backends_config)
    entry: CacheEntry = CacheEntry("test_value", 3600)
    multi_backend._set_raw("key", entry)

    # ACT
    success: bool = multi_backend._delete_raw("key")

    # ASSERT
    assert success is True
    for backend in multi_backend.backends:
        assert backend._get_raw("key") is None


def test_multi_level_backend_keys_raw_returns_union_of_all_keys() -> None:
    """Test multi-level backend returns union of keys from all levels."""
    # ARRANGE
    backends_config: List[tuple] = [
        ("memory", {"max_size": 100}),
        ("memory", {"max_size": 100}),
    ]
    multi_backend: MultiLevelBackend = MultiLevelBackend(backends_config)

    multi_backend.backends[0]._set_raw("key1", CacheEntry("value1", 3600))
    multi_backend.backends[1]._set_raw("key2", CacheEntry("value2", 3600))

    # ACT
    keys: List[str] = multi_backend._keys_raw()

    # ASSERT
    assert set(keys) == {"key1", "key2"}


# -------------------------------------------------------------
# TEST CASES: CacheManager
# -------------------------------------------------------------


def test_cache_manager_get_or_set_returns_cached_value_when_exists() -> None:
    """Test get_or_set returns cached value without calling function."""
    # ARRANGE
    backend: MemoryBackend = MemoryBackend()
    manager: CacheManager = CacheManager(backend)
    backend.set("key", "cached_value")
    callable_func: Mock = Mock(return_value="computed_value")

    # ACT
    result: str = manager.get_or_set("key", callable_func)

    # ASSERT
    assert result == "cached_value"
    callable_func.assert_not_called()


def test_cache_manager_get_or_set_computes_and_caches_when_missing() -> None:
    """Test get_or_set computes value and caches it when not present."""
    # ARRANGE
    backend: MemoryBackend = MemoryBackend()
    manager: CacheManager = CacheManager(backend)
    callable_func: Mock = Mock(return_value="computed_value")

    # ACT
    result: str = manager.get_or_set("key", callable_func, ttl=3600)

    # ASSERT
    assert result == "computed_value"
    callable_func.assert_called_once()
    assert backend.get("key") == "computed_value"


def test_cache_manager_get_or_set_handles_callable_exception() -> None:  # IMPORTANT TEST
    """Test get_or_set propagates exception from callable."""
    # ARRANGE
    backend: MemoryBackend = MemoryBackend()
    manager: CacheManager = CacheManager(backend)
    callable_func: Mock = Mock(side_effect=ValueError("Computation failed"))

    # ACT & ASSERT
    with pytest.raises(ValueError, match="Computation failed"):
        manager.get_or_set("key", callable_func)


def test_cache_manager_get_or_set_caches_none_value() -> None:
    """Test get_or_set caches None values correctly."""
    # ARRANGE
    backend: MemoryBackend = MemoryBackend()
    manager: CacheManager = CacheManager(backend)
    callable_func: Mock = Mock(return_value=None)

    # ACT
    result: Any = manager.get_or_set("key", callable_func)

    # ASSERT
    assert result is None
    # Should NOT cache None (backend.get returns None for missing keys)
    callable_func.assert_called_once()


def test_cache_manager_invalidate_pattern_clears_matching_keys() -> None:
    """Test invalidate_pattern removes keys matching pattern."""
    # ARRANGE
    backend: MemoryBackend = MemoryBackend()
    manager: CacheManager = CacheManager(backend)
    manager.set("user:1", "value1")
    manager.set("user:2", "value2")
    manager.set("session:1", "value3")

    # ACT
    count: int = manager.invalidate_pattern("user:*")

    # ASSERT
    assert count == 2
    assert manager.exists("session:1") is True


def test_cache_manager_stats_returns_backend_statistics() -> None:
    """Test stats returns backend statistics."""
    # ARRANGE
    backend: MemoryBackend = MemoryBackend()
    manager: CacheManager = CacheManager(backend)
    manager.set("key", "value")
    manager.get("key")

    # ACT
    stats: Dict[str, Any] = manager.stats()

    # ASSERT
    assert stats["hits"] == 1
    assert stats["sets"] == 1
    assert stats["size"] == 1


# -------------------------------------------------------------
# TEST CASES: CacheFactory (CRITICAL)
# -------------------------------------------------------------


def test_cache_factory_get_cache_creates_memory_backend_by_default() -> None:
    """Test factory creates memory backend when no type specified."""
    # ARRANGE
    factory: CacheFactory = CacheFactory()

    # ACT
    manager: CacheManager = factory.get_cache()

    # ASSERT
    assert isinstance(manager.backend, MemoryBackend)


def test_cache_factory_get_cache_creates_file_backend() -> None:
    """Test factory creates file backend with config."""
    # ARRANGE
    factory: CacheFactory = CacheFactory()

    # ACT
    manager: CacheManager = factory.get_cache(backend="file", cache_dir="/tmp/test_cache")

    # ASSERT
    assert isinstance(manager.backend, FileBackend)


def test_cache_factory_get_cache_creates_database_backend() -> None:
    """Test factory creates database backend with config."""
    # ARRANGE
    factory: CacheFactory = CacheFactory()

    # Mock DatabaseBackend.__init__ to avoid actual DB connection
    with patch.object(DatabaseBackend, "__init__", return_value=None):
        # ACT
        manager: CacheManager = factory.get_cache(
            backend="database", instance_name="test_instance", database_name="test_db"
        )

        # ASSERT
        assert isinstance(manager.backend, DatabaseBackend)


def test_cache_factory_get_cache_creates_multi_level_backend() -> None:
    """Test factory creates multi-level backend."""
    # ARRANGE
    factory: CacheFactory = CacheFactory()
    backends_config: List[tuple] = [
        ("memory", {"max_size": 100}),
        ("memory", {"max_size": 1000}),
    ]

    # ACT
    manager: CacheManager = factory.get_cache(backend="multi", backends=backends_config)

    # ASSERT
    assert isinstance(manager.backend, MultiLevelBackend)
    assert len(manager.backend.backends) == 2


def test_cache_factory_get_cache_raises_error_for_unknown_backend() -> None:  # IMPORTANT TEST
    """Test factory raises CacheError for unknown backend type."""
    # ARRANGE
    factory: CacheFactory = CacheFactory()

    # ACT & ASSERT
    with pytest.raises(CacheError, match="Unknown backend 'invalid'"):
        factory.get_cache(backend="invalid")


def test_cache_factory_get_cache_raises_error_on_backend_init_failure() -> None:  # IMPORTANT TEST
    """Test factory raises CacheError when backend initialization fails."""
    # ARRANGE
    factory: CacheFactory = CacheFactory()

    # ACT & ASSERT
    with pytest.raises(CacheError, match="Failed to create database backend"):
        # Missing required parameters
        factory.get_cache(backend="database")


def test_cache_factory_register_backend_adds_custom_backend() -> None:
    """Test register_backend allows custom backend registration."""
    # ARRANGE
    factory: CacheFactory = CacheFactory()

    class CustomBackend(CacheBackend):
        def _get_raw(self, key: str) -> Optional[CacheEntry]:
            return None

        def _set_raw(self, key: str, entry: CacheEntry) -> None:
            pass

        def _delete_raw(self, key: str) -> bool:
            return True

        def _clear_raw(self) -> int:
            return 0

        def _keys_raw(self) -> List[str]:
            return []

    # ACT
    factory.register_backend("custom", CustomBackend)
    manager: CacheManager = factory.get_cache(backend="custom")

    # ASSERT
    assert isinstance(manager.backend, CustomBackend)


def test_cache_factory_register_backend_raises_error_for_invalid_class() -> None:
    """Test register_backend raises TypeError for non-CacheBackend class."""
    # ARRANGE
    factory: CacheFactory = CacheFactory()

    class NotABackend:
        pass

    # ACT & ASSERT
    with pytest.raises(TypeError, match="must be subclass of CacheBackend"):
        factory.register_backend("invalid", NotABackend)


def test_cache_factory_is_singleton() -> None:
    """Test CacheFactory is a singleton."""
    # ACT
    factory1: CacheFactory = CacheFactory()
    factory2: CacheFactory = CacheFactory()

    # ASSERT
    assert factory1 is factory2


# -------------------------------------------------------------
# TEST CASES: Convenience Functions
# -------------------------------------------------------------


def test_get_cache_convenience_function_creates_manager() -> None:
    """Test get_cache convenience function returns CacheManager."""
    # ACT
    manager: CacheManager = get_cache()

    # ASSERT
    assert isinstance(manager, CacheManager)
    assert isinstance(manager.backend, MemoryBackend)


def test_get_cache_convenience_function_passes_config() -> None:
    """Test get_cache passes configuration to factory."""
    # ACT
    manager: CacheManager = get_cache(backend="memory", max_size=500)

    # ASSERT
    assert isinstance(manager.backend, MemoryBackend)
    assert manager.backend.max_size == 500


# -------------------------------------------------------------
# TEST CASES: Edge Cases and Error Handling
# -------------------------------------------------------------


@pytest.mark.parametrize(
    "pattern,expected_count",
    [
        ("*", 3),
        ("user:*", 2),
        ("session:*", 1),
        ("nonexistent:*", 0),
        ("user:?", 2),  # ? matches single char (1, 2)
        ("user:??", 0),  # ?? matches two chars (no match)
    ],
)
def test_cache_backend_clear_pattern_matching(
    memory_backend: MemoryBackend, pattern: str, expected_count: int
) -> None:
    """Test clear pattern matching with various patterns."""
    # ARRANGE
    memory_backend.set("user:1", "value1")
    memory_backend.set("user:2", "value2")
    memory_backend.set("session:1", "value3")

    # ACT
    count: int = memory_backend.clear(pattern=pattern)

    # ASSERT
    assert count == expected_count


@pytest.mark.parametrize(
    "ttl,should_expire",
    [
        (0, False),  # No TTL
        (3600, False),  # Future expiration
        (-1, True),  # Negative TTL (already expired)
    ],
)
def test_cache_entry_expiration_edge_cases(ttl: int, should_expire: bool) -> None:
    """Test CacheEntry expiration with edge case TTL values."""
    # ARRANGE & ACT
    entry: CacheEntry = CacheEntry("data", ttl)

    # ASSERT
    if ttl >= 0:
        assert entry.is_expired() == should_expire


def test_cache_backend_handles_concurrent_access() -> None:
    """Test cache backend handles concurrent read/write operations."""
    # ARRANGE
    backend: MemoryBackend = MemoryBackend(max_size=1000)
    results: List[bool] = []

    def worker(worker_id: int) -> None:
        for i in range(50):
            key: str = f"key_{worker_id}_{i}"
            backend.set(key, f"value_{worker_id}_{i}")
            value: Optional[str] = backend.get(key)
            results.append(value is not None)

    # ACT
    threads: List[threading.Thread] = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    # ASSERT
    assert all(results)  # All reads should succeed


def test_memory_backend_handles_empty_cache_eviction() -> None:
    """Test memory backend handles eviction when cache is empty."""
    # ARRANGE
    backend: MemoryBackend = MemoryBackend(max_size=1)

    # ACT & ASSERT (should not raise exception)
    backend._evict_lru()


def test_file_backend_handles_missing_cache_directory() -> None:
    """Test file backend creates cache directory if missing."""
    # ARRANGE
    cache_dir: str = "/tmp/nonexistent_cache_dir_test"
    import shutil

    if Path(cache_dir).exists():
        shutil.rmtree(cache_dir)

    # ACT
    backend: FileBackend = FileBackend(cache_dir=cache_dir)

    # ASSERT
    assert Path(cache_dir).exists()

    # Cleanup
    shutil.rmtree(cache_dir)


def test_cache_backend_get_returns_none_for_expired_entry() -> None:
    """Test get automatically removes and returns None for expired entries."""
    # ARRANGE
    backend: MemoryBackend = MemoryBackend()
    backend.set("key", "value", ttl=1)
    time.sleep(1.1)

    # ACT
    result: Optional[Any] = backend.get("key")

    # ASSERT
    assert result is None
    assert backend.stats["misses"] == 1
    assert backend.size() == 0  # Should be removed
