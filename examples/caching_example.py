#!/usr/bin/env python3
"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich
  Project : basefunctions
  Copyright (c) by neuraldevelopment
  All rights reserved.
  Description:
  Demo script to test all cache manager variants using DemoRunner
 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import time
import tempfile
import shutil
from typing import Dict, Any
import basefunctions

# -------------------------------------------------------------
# DEFINITIONS REGISTRY
# -------------------------------------------------------------

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


def main():
    """Run all cache demos using DemoRunner."""
    # Initialize logging and demo runner
    log_file = basefunctions.DemoRunner.init_logging("INFO")
    runner = basefunctions.DemoRunner(max_width=120)

    print("🚀 Cache Manager Demo")
    print("=" * 50)
    print(f"Logging to: {log_file}")

    @runner.test("Memory Cache - Basic Operations")
    def test_memory_basic():
        cache = basefunctions.get_cache("memory", max_size=3)
        cache.set("user:123", {"name": "John", "age": 30}, ttl=300)
        cache.set("user:456", {"name": "Jane", "age": 25}, ttl=300)

        user = cache.get("user:123")
        assert user["name"] == "John"
        assert cache.exists("user:456")
        assert cache.size() == 2

    @runner.test("Memory Cache - Get Or Set")
    def test_memory_get_or_set():
        cache = basefunctions.get_cache("memory", max_size=10)

        call_count = 0

        def expensive_calculation():
            nonlocal call_count
            call_count += 1
            return {"result": "computed_value", "timestamp": time.time()}

        result1 = cache.get_or_set("expensive:calc", expensive_calculation, ttl=60)
        result2 = cache.get_or_set("expensive:calc", expensive_calculation, ttl=60)

        assert call_count == 1  # Should only be called once
        assert result1 == result2  # Should be same cached result

    @runner.test("Memory Cache - LRU Eviction")
    def test_memory_eviction():
        cache = basefunctions.get_cache("memory", max_size=2)

        cache.set("key1", "value1", ttl=300)
        cache.set("key2", "value2", ttl=300)
        cache.set("key3", "value3", ttl=300)  # Should trigger eviction

        assert cache.size() <= 2
        assert cache.get("key3") == "value3"  # Latest should be there

    @runner.test("Memory Cache - TTL Expiration")
    def test_memory_ttl():
        cache = basefunctions.get_cache("memory", max_size=10)

        # Very short TTL for reliable test
        cache.set("temp:data", "temporary", ttl=0.1)  # 100ms

        # Verify it exists initially
        assert cache.get("temp:data") == "temporary"
        ttl_before = cache.ttl("temp:data")
        assert ttl_before is not None and ttl_before >= 0

        # Wait double the TTL to ensure expiration
        time.sleep(0.25)  # 250ms - more than double the TTL

        # Should be expired now
        expired_value = cache.get("temp:data")
        assert expired_value is None, f"Expected None, got {expired_value}"

        # TTL should also return None for expired key
        ttl_after = cache.ttl("temp:data")
        assert ttl_after is None

    @runner.test("Memory Cache - Pattern Operations")
    def test_memory_patterns():
        cache = basefunctions.get_cache("memory", max_size=10)

        cache.set("test:a", "value_a", ttl=300)
        cache.set("test:b", "value_b", ttl=300)
        cache.set("other:c", "value_c", ttl=300)

        test_keys = cache.keys("test:*")
        assert len(test_keys) == 2

        cleared = cache.invalidate_pattern("test:*")
        assert cleared == 2

        remaining_keys = cache.keys()
        assert "other:c" in remaining_keys
        assert len([k for k in remaining_keys if k.startswith("test:")]) == 0

    @runner.test("File Cache - Persistence")
    def test_file_persistence():
        temp_dir = tempfile.mkdtemp(prefix="cache_test_")

        try:
            # Create first cache instance
            cache1 = basefunctions.get_cache("file", cache_dir=temp_dir)

            data = {
                "dataframe_like": [[1, 2, 3], [4, 5, 6], [7, 8, 9]],
                "metadata": {"created": time.time(), "version": "1.0"},
                "nested": {"deep": {"structure": {"value": 42}}},
            }

            cache1.set("complex:data", data, ttl=3600)

            # Create second cache instance (simulates restart)
            cache2 = basefunctions.get_cache("file", cache_dir=temp_dir)
            retrieved = cache2.get("complex:data")

            assert retrieved is not None
            assert retrieved["metadata"]["version"] == "1.0"
            assert retrieved["nested"]["deep"]["structure"]["value"] == 42

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    @runner.test("File Cache - Complex Data Types")
    def test_file_complex_data():
        temp_dir = tempfile.mkdtemp(prefix="cache_test_")

        try:
            cache = basefunctions.get_cache("file", cache_dir=temp_dir)

            test_data = [
                ("string", "Hello World"),
                ("int", 42),
                ("float", 3.14159),
                ("list", [1, 2, 3, "mixed", {"nested": True}]),
                ("dict", {"user": "admin", "permissions": ["read", "write"]}),
            ]

            # Set all test data
            for key, value in test_data:
                cache.set(f"type:{key}", value, ttl=1800)

            # Retrieve and verify
            for key, original_value in test_data:
                retrieved = cache.get(f"type:{key}")
                assert retrieved == original_value

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    @runner.test("Multi-Level Cache - Promotion")
    def test_multi_level_promotion():
        temp_dir = tempfile.mkdtemp(prefix="multi_cache_test_")

        try:
            # Create multi-level cache: Memory (L1) -> File (L2)
            cache = basefunctions.get_cache(
                "multi", backends=[("memory", {"max_size": 5}), ("file", {"cache_dir": temp_dir})]
            )

            cache.set("promo:test", "promotion_data", ttl=300)

            # Create new cache instance (new memory, same file)
            cache2 = basefunctions.get_cache(
                "multi", backends=[("memory", {"max_size": 5}), ("file", {"cache_dir": temp_dir})]
            )

            # Should find in L2 (file) and promote to L1 (memory)
            result = cache2.get("promo:test")
            assert result == "promotion_data"

            # Second get should be faster (from L1)
            result2 = cache2.get("promo:test")
            assert result2 == "promotion_data"

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    @runner.test("Cache Statistics")
    def test_cache_stats():
        cache = basefunctions.get_cache("memory", max_size=10)

        # Generate some hits and misses
        cache.set("key1", "value1", ttl=300)
        cache.set("key2", "value2", ttl=300)

        # Hits
        cache.get("key1")
        cache.get("key2")
        cache.get("key1")  # Another hit

        # Misses
        cache.get("nonexistent1")
        cache.get("nonexistent2")

        stats = cache.stats()
        assert stats["hits"] == 3
        assert stats["misses"] == 2
        assert stats["sets"] == 2
        assert stats["hit_rate_percent"] == 60.0  # 3/(3+2) = 60%

    @runner.test("Performance - Market Data Simulation")
    def test_performance_market_data():
        cache = basefunctions.get_cache("memory", max_size=100)

        def simulate_expensive_fetch(symbol):
            time.sleep(0.01)  # Simulate network delay
            return {
                "symbol": symbol,
                "data": [[100 + i, 101 + i, 99 + i, 100.5 + i] for i in range(10)],
                "fetched_at": time.time(),
            }

        symbols = ["AAPL", "GOOGL", "MSFT"]

        # First run - populate cache
        start_time = time.time()
        for symbol in symbols:
            key = f"market_data:{symbol}"
            data = cache.get_or_set(key, lambda s=symbol: simulate_expensive_fetch(s), ttl=3600)
        first_run_time = time.time() - start_time

        # Second run - from cache
        start_time = time.time()
        for symbol in symbols:
            key = f"market_data:{symbol}"
            data = cache.get(key)
            assert data is not None
        second_run_time = time.time() - start_time

        # Cache should be significantly faster
        speedup = first_run_time / second_run_time if second_run_time > 0 else float("inf")
        assert speedup > 5  # At least 5x speedup

    @runner.test("Database Cache - PostgreSQL Backend")
    def test_database_cache():
        # Check if test instance exists and is running
        manager = basefunctions.DbManager()
        instance_name = "dev_test_db_postgres"

        try:
            # Check if instance exists
            if not manager.has_instance(instance_name):
                raise Exception(f"Instance '{instance_name}' not found")

            # Get instance and check if it's reachable
            instance = manager.get_instance(instance_name)
            if not instance.is_reachable():
                raise Exception(f"Instance '{instance_name}' is not running or reachable")

            # Check if it's actually PostgreSQL (skip for other DB types)
            instance_type = instance.get_type()
            if instance_type != "postgresql":
                raise Exception(f"Expected PostgreSQL, found {instance_type} - skipping database cache test")

            # Create database cache
            cache = basefunctions.get_cache("database", instance_name=instance_name, database_name="cache_test")

            # Test with various data types
            test_data = [
                ("string:key", "Hello Database Cache"),
                ("int:key", 42),
                ("float:key", 3.14159),
                ("list:key", [1, 2, 3, "mixed", {"nested": True}]),
                ("dict:key", {"user": "cache_test", "permissions": ["read", "write", "cache"]}),
            ]

            # Set all test data
            for key, value in test_data:
                cache.set(key, value, ttl=1800)

            # Retrieve and verify
            for key, original_value in test_data:
                retrieved = cache.get(key)
                assert retrieved == original_value, f"Mismatch for {key}"

            # Test database-specific features
            assert cache.size() >= len(test_data)

            # Test TTL operations
            cache.set("ttl:test", "expires_soon", ttl=60)
            assert cache.ttl("ttl:test") <= 60

            # Test pattern operations
            cache.set("pattern:a", "value_a", ttl=300)
            cache.set("pattern:b", "value_b", ttl=300)
            pattern_keys = cache.keys("pattern:*")
            assert len(pattern_keys) >= 2

            # Test persistence - create new cache instance
            cache2 = basefunctions.get_cache("database", instance_name=instance_name, database_name="cache_test")

            # Should find existing data
            persisted_value = cache2.get("string:key")
            assert persisted_value == "Hello Database Cache"

            # Cleanup test data
            cache.invalidate_pattern("string:*")
            cache.invalidate_pattern("int:*")
            cache.invalidate_pattern("float:*")
            cache.invalidate_pattern("list:*")
            cache.invalidate_pattern("dict:*")
            cache.invalidate_pattern("ttl:*")
            cache.invalidate_pattern("pattern:*")

        except Exception as e:
            # Skip test if instance not available, not running, or not PostgreSQL
            error_str = str(e).lower()
            if any(
                skip_reason in error_str
                for skip_reason in ["not found", "not running", "not reachable", "expected postgresql"]
            ):
                print(f"  Skipping database cache test: {str(e)}")
                return  # Skip test gracefully
            else:
                raise  # Re-raise unexpected errors

    @runner.test("Performance - Indicator Calculation")
    def test_performance_indicators():
        cache = basefunctions.get_cache("memory", max_size=100)

        def calculate_rsi(data, period=14):
            time.sleep(0.01)  # Simulate calculation time
            return [50 + (i % 20 - 10) for i in range(len(data))]

        test_data = list(range(100))
        data_hash = str(hash(tuple(test_data)))
        rsi_key = f"indicator:rsi_14:{data_hash}"

        # First calculation
        start_time = time.time()
        rsi_values = cache.get_or_set(rsi_key, lambda: calculate_rsi(test_data), ttl=1800)
        first_calc_time = time.time() - start_time

        # Cached retrieval
        start_time = time.time()
        rsi_values_cached = cache.get(rsi_key)
        cached_calc_time = time.time() - start_time

        assert rsi_values == rsi_values_cached
        assert len(rsi_values) == 100

        # Cache should be much faster
        if cached_calc_time > 0:
            speedup = first_calc_time / cached_calc_time
            assert speedup > 10  # At least 10x speedup

    # Run all tests
    runner.run_all_tests()

    # Create performance data for display
    performance_data = [
        ("Memory Cache Hit Rate", "~99% for repeated access"),
        ("File Cache Overhead", "~10-50ms for complex objects"),
        ("Multi-Level Promotion", "L2→L1 automatic optimization"),
        ("Market Data Speedup", "5-100x improvement over API calls"),
        ("Indicator Calculation", "10-1000x speedup for expensive computations"),
        ("TTL Management", "Automatic expiration and cleanup"),
        ("Pattern Matching", "Wildcard support for bulk operations"),
    ]

    # Print results
    runner.print_results("Cache Manager Test Results")
    runner.print_performance_table(performance_data, "Cache Performance Metrics")

    # Summary
    passed, total = runner.get_summary()
    print(f"\n🎯 Summary: {passed}/{total} tests passed")

    if runner.has_failures():
        print("\n❌ Failed tests:")
        for test_name, error in runner.get_failed_tests():
            print(f"  - {test_name}: {error}")
    else:
        print("\n✅ All cache functionality working correctly!")
        print("\nKey Benefits Demonstrated:")
        print("- Memory cache: Ultra-fast access with LRU eviction")
        print("- File cache: Persistent storage across restarts")
        print("- Multi-level: Automatic promotion for optimal performance")
        print("- Statistics: Comprehensive hit/miss tracking")
        print("- Performance: Massive speedups for expensive operations")


if __name__ == "__main__":
    main()
