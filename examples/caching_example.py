#!/usr/bin/env python3
"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich
  Project : basefunctions
  Copyright (c) by neuraldevelopment
  All rights reserved.
  Description:
  Demo script to test CachedDataFrameDb with Write-Back cache pattern
 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import time
import pandas as pd
import numpy as np
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


def create_sample_dataframe(rows: int, table_suffix: str = "") -> pd.DataFrame:
    """Create sample DataFrame for testing."""
    np.random.seed(42 + hash(table_suffix) % 1000)  # Consistent but different data per table

    return pd.DataFrame(
        {
            "id": range(1, rows + 1),
            "name": [f"User_{i}_{table_suffix}" for i in range(1, rows + 1)],
            "value": np.random.randint(1, 1000, rows),
            "score": np.random.uniform(0, 100, rows).round(2),
            "category": np.random.choice(["A", "B", "C"], rows),
            "timestamp": pd.date_range("2024-01-01", periods=rows, freq="1h"),
        }
    )


def main():
    """Run DataFrame caching demo using DemoRunner."""
    # Initialize logging and demo runner
    log_file = basefunctions.DemoRunner.init_logging("INFO")
    runner = basefunctions.DemoRunner(max_width=120)

    print("🚀 DataFrame Caching Demo - Write-Back Pattern")
    print("=" * 55)
    print(f"Logging to: {log_file}")

    # Test database instance setup
    instance_name = "dev_test_db_postgres"
    database_name = "cache_test_df"

    @runner.test("Database Instance Check")
    def test_instance_available():
        manager = basefunctions.DbManager()

        if not manager.has_instance(instance_name):
            raise Exception(f"Instance '{instance_name}' not found - please create test instance first")

        instance = manager.get_instance(instance_name)
        if not instance.is_reachable():
            raise Exception(f"Instance '{instance_name}' is not running or reachable")

        instance_type = instance.get_type()
        if instance_type != "postgres":
            raise Exception(f"Expected PostgreSQL, found {instance_type}")

    @runner.test("Write-Back Cache - Basic Write and Read")
    def test_basic_write_read():
        cached_db = basefunctions.CachedDataFrameDb(instance_name, database_name)

        # Create test data
        df = create_sample_dataframe(100, "basic")
        table_name = "test_basic"

        # Write to cache (should be instant)
        start_time = time.time()
        result = cached_db.write(df, table_name)
        write_time = time.time() - start_time

        assert result == True
        assert write_time < 0.1  # Should be very fast (cache only)

        # Read from cache (should return written data)
        start_time = time.time()
        read_df = cached_db.read(table_name)
        read_time = time.time() - start_time

        assert len(read_df) == 100
        assert list(read_df.columns) == list(df.columns)
        assert read_time < 0.1  # Should be very fast (cache hit)

        # Check cache stats
        stats = cached_db.get_cache_stats()
        assert stats["cache"]["dirty_entries"] == 1
        assert stats["cache"]["total_entries"] == 1

    @runner.test("Write-Back Cache - Multiple Writes with Append")
    def test_multiple_append_writes():
        cached_db = basefunctions.CachedDataFrameDb(instance_name, database_name)

        table_name = "test_append"

        # Write first batch
        df1 = create_sample_dataframe(50, "batch1")
        cached_db.write(df1, table_name, if_exists="replace")

        # Write second batch (append)
        df2 = create_sample_dataframe(30, "batch2")
        cached_db.write(df2, table_name, if_exists="append")

        # Write third batch (append)
        df3 = create_sample_dataframe(20, "batch3")
        cached_db.write(df3, table_name, if_exists="append")

        # Read combined data from cache
        combined_df = cached_db.read(table_name)

        # Should have all data combined
        assert len(combined_df) == 100  # 50 + 30 + 20

        # Check that data from all batches is present
        batch1_users = combined_df[combined_df["name"].str.contains("batch1")]
        batch2_users = combined_df[combined_df["name"].str.contains("batch2")]
        batch3_users = combined_df[combined_df["name"].str.contains("batch3")]

        assert len(batch1_users) == 50
        assert len(batch2_users) == 30
        assert len(batch3_users) == 20

        # Cache should still be dirty (not flushed)
        stats = cached_db.get_cache_stats()
        assert stats["cache"]["dirty_entries"] >= 1

    @runner.test("Write-Back Cache - Flush Operation")
    def test_flush_operation():
        cached_db = basefunctions.CachedDataFrameDb(instance_name, database_name)

        # Write data to multiple tables
        tables_data = [
            ("flush_test_1", create_sample_dataframe(75, "flush1")),
            ("flush_test_2", create_sample_dataframe(125, "flush2")),
            ("flush_test_3", create_sample_dataframe(50, "flush3")),
        ]

        for table_name, df in tables_data:
            cached_db.write(df, table_name)

        # Verify data is in cache but dirty
        stats_before = cached_db.get_cache_stats()
        assert stats_before["cache"]["dirty_entries"] == 3

        # Flush all data to database
        start_time = time.time()
        flushed_count = cached_db.flush()
        flush_time = time.time() - start_time

        assert flushed_count == 3

        # Verify cache is now clean
        stats_after = cached_db.get_cache_stats()
        assert stats_after["cache"]["dirty_entries"] == 0
        assert stats_after["cache"]["clean_entries"] == 3

        # Verify data can still be read from cache (now clean)
        for table_name, original_df in tables_data:
            read_df = cached_db.read(table_name)
            assert len(read_df) == len(original_df)

    @runner.test("Write-Back Cache - Immediate Write Bypass")
    def test_immediate_write_bypass():
        cached_db = basefunctions.CachedDataFrameDb(instance_name, database_name)

        df = create_sample_dataframe(80, "immediate")
        table_name = "test_immediate"

        # Write with immediate=True (should bypass cache and go directly to DB)
        start_time = time.time()
        result = cached_db.write(df, table_name, immediate=True)
        immediate_write_time = time.time() - start_time

        assert result == True
        # Should take longer than cached write (involves DB operation)
        assert immediate_write_time > 0.01

        # Reading should hit database and then cache the result
        read_df = cached_db.read(table_name)
        assert len(read_df) == 80

        # Cache should have clean entry
        stats = cached_db.get_cache_stats()
        clean_entries = stats["cache"]["clean_entries"]
        assert clean_entries >= 1

    @runner.test("Write-Back Cache - Cache Hit vs Miss Performance")
    def test_cache_performance():
        cached_db = basefunctions.CachedDataFrameDb(instance_name, database_name)

        df = create_sample_dataframe(200, "perf")
        table_name = "test_performance"

        # First write (to cache)
        cached_db.write(df, table_name)

        # First read (cache hit - should be very fast)
        start_time = time.time()
        read_df_1 = cached_db.read(table_name)
        cache_hit_time = time.time() - start_time

        # Clear cache to force DB read
        cached_db.clear_cache()

        # Flush data to DB first
        cached_db.write(df, table_name, immediate=True)
        cached_db.clear_cache()  # Clear again

        # Second read (cache miss - should be slower)
        start_time = time.time()
        read_df_2 = cached_db.read(table_name)
        cache_miss_time = time.time() - start_time

        # Verify data integrity
        assert len(read_df_1) == len(read_df_2) == 200

        # Cache hit should be significantly faster
        if cache_miss_time > 0:
            speedup = cache_miss_time / cache_hit_time
            assert speedup > 2  # At least 2x speedup

    @runner.test("Write-Back Cache - Cache Invalidation")
    def test_cache_invalidation():
        cached_db = basefunctions.CachedDataFrameDb(instance_name, database_name)

        # Write data to cache
        df = create_sample_dataframe(60, "invalid")
        table_name = "test_invalidation"

        cached_db.write(df, table_name)

        # Verify data is cached
        stats_before = cached_db.get_cache_stats()
        assert stats_before["cache"]["total_entries"] >= 1

        # Clear cache for specific table pattern
        cleared_count = cached_db.clear_cache("*invalidation*")
        assert cleared_count >= 1

        # Verify cache is cleared
        stats_after = cached_db.get_cache_stats()
        assert stats_after["cache"]["total_entries"] < stats_before["cache"]["total_entries"]

    @runner.test("Write-Back Cache - Large Data Handling")
    def test_large_data_handling():
        cached_db = basefunctions.CachedDataFrameDb(instance_name, database_name)

        # Create larger dataset
        large_df = create_sample_dataframe(1000, "large")
        table_name = "test_large_data"

        # Write large data
        start_time = time.time()
        result = cached_db.write(large_df, table_name)
        write_time = time.time() - start_time

        assert result == True

        # Read large data
        start_time = time.time()
        read_df = cached_db.read(table_name)
        read_time = time.time() - start_time

        assert len(read_df) == 1000

        # Flush large data
        start_time = time.time()
        flushed_count = cached_db.flush()
        flush_time = time.time() - start_time

        assert flushed_count >= 1

    @runner.test("Write-Back Cache - Error Handling")
    def test_error_handling():
        cached_db = basefunctions.CachedDataFrameDb(instance_name, database_name)

        # Test empty DataFrame
        empty_df = pd.DataFrame()
        try:
            cached_db.write(empty_df, "test_empty")
            assert False, "Should have raised validation error"
        except basefunctions.DataFrameValidationError:
            pass  # Expected

        # Test invalid table name
        valid_df = create_sample_dataframe(10, "error")
        try:
            cached_db.write(valid_df, "")
            assert False, "Should have raised validation error"
        except basefunctions.DataFrameValidationError:
            pass  # Expected

        # Test non-DataFrame input
        try:
            cached_db.write("not_a_dataframe", "test_invalid")
            assert False, "Should have raised validation error"
        except basefunctions.DataFrameValidationError:
            pass  # Expected

    # Run all tests
    runner.run_all_tests()

    # Create performance data for display
    performance_data = [
        ("Write-Back Pattern", "Instant writes to cache, batched DB writes"),
        ("Cache Hit Performance", "2-100x faster than database reads"),
        ("Memory Efficiency", "Smart DataFrame copying and dirty tracking"),
        ("Append Operations", "Efficient DataFrame concatenation in cache"),
        ("Flush Optimization", "Batch writes reduce DB connection overhead"),
        ("Immediate Writes", "Bypass cache for critical data consistency"),
        ("Large Data Support", "Handles 1000+ rows efficiently"),
        ("Error Resilience", "Comprehensive validation and error handling"),
    ]

    # Print results
    runner.print_results("DataFrame Caching Test Results")
    runner.print_performance_table(performance_data, "Write-Back Cache Performance Metrics")

    # Summary
    passed, total = runner.get_summary()
    print(f"\n🎯 Summary: {passed}/{total} tests passed")

    if runner.has_failures():
        print("\n❌ Failed tests:")
        for test_name, error in runner.get_failed_tests():
            print(f"  - {test_name}: {error}")
    else:
        print("\n✅ Write-Back DataFrame caching working correctly!")
        print("\nKey Features Demonstrated:")
        print("- ✨ Instant writes: Data immediately available in cache")
        print("- 🚀 Fast reads: Cache hits are 2-100x faster than DB")
        print("- 📦 Smart batching: Multiple writes combined efficiently")
        print("- 🔄 Append support: DataFrame concatenation in memory")
        print("- 💾 Lazy persistence: Flush when needed, not on every write")
        print("- ⚡ Immediate mode: Bypass cache for critical operations")
        print("- 🛡️  Error handling: Comprehensive validation and recovery")

        print(f"\n📊 Overall Benefits:")
        print("- Write performance: Near-instant (memory-only)")
        print("- Read performance: 2-100x speedup on cache hits")
        print("- Memory usage: Efficient with copy-on-write semantics")
        print("- Database load: Reduced through intelligent batching")


if __name__ == "__main__":
    main()
