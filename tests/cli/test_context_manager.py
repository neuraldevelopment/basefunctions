"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.

 Description:
 Pytest test suite for ContextManager.
 Tests CLI context state management with security-critical path validation.

 Log:
 v1.0.0 : Initial test implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
# External imports
import pytest
from typing import Any, Dict, Tuple

# Project imports
from basefunctions.cli import ContextManager

# -------------------------------------------------------------
# FIXTURES
# -------------------------------------------------------------


@pytest.fixture
def context_manager() -> ContextManager:
    """
    Provide ContextManager instance for testing.

    Returns
    -------
    ContextManager
        Fresh context manager with test app name

    Notes
    -----
    Starts with empty context dictionary
    """
    return ContextManager(app_name="test_app")


@pytest.fixture
def populated_context_manager() -> ContextManager:
    """
    Provide ContextManager with preset values for testing.

    Returns
    -------
    ContextManager
        Context manager with instance and database set

    Notes
    -----
    Used for testing prompt generation and resolution
    """
    ctx = ContextManager(app_name="test_app")
    ctx.set("instance", "prod_instance")
    ctx.set("database", "main_db")
    return ctx


# -------------------------------------------------------------
# TESTS: Basic Context Operations
# -------------------------------------------------------------


def test_init_creates_empty_context(context_manager: ContextManager) -> None:
    """
    Test __init__ creates ContextManager with empty context.

    Tests that new ContextManager starts with empty context
    dictionary and correct app name.
    """
    # ASSERT
    assert context_manager.app_name == "test_app"
    assert context_manager._context == {}


def test_set_stores_value_correctly(context_manager: ContextManager) -> None:
    """
    Test set stores key-value pair in context.

    Tests that set method correctly stores value and
    makes it retrievable.
    """
    # ARRANGE
    key: str = "test_key"
    value: str = "test_value"

    # ACT
    context_manager.set(key, value)

    # ASSERT
    assert context_manager._context[key] == value


def test_set_overwrites_existing_value(context_manager: ContextManager) -> None:
    """
    Test set overwrites existing context value.

    Tests that set method replaces existing value for
    same key without error.
    """
    # ARRANGE
    key: str = "test_key"
    context_manager.set(key, "old_value")

    # ACT
    context_manager.set(key, "new_value")

    # ASSERT
    assert context_manager._context[key] == "new_value"


def test_get_returns_value_when_exists(context_manager: ContextManager) -> None:
    """
    Test get returns value when key exists.

    Tests that get method retrieves stored value
    correctly.
    """
    # ARRANGE
    context_manager.set("test_key", "test_value")

    # ACT
    result: Any = context_manager.get("test_key")

    # ASSERT
    assert result == "test_value"


def test_get_returns_default_when_key_not_exists(context_manager: ContextManager) -> None:
    """
    Test get returns default value when key missing.

    Tests that get method returns provided default
    when key doesn't exist in context.
    """
    # ARRANGE
    default_value: str = "default"

    # ACT
    result: Any = context_manager.get("missing_key", default_value)

    # ASSERT
    assert result == default_value


def test_get_returns_none_when_no_default_and_missing(context_manager: ContextManager) -> None:
    """
    Test get returns None when no default provided.

    Tests that get method returns None when key missing
    and no default specified.
    """
    # ACT
    result: Any = context_manager.get("missing_key")

    # ASSERT
    assert result is None


def test_clear_removes_specific_key(context_manager: ContextManager) -> None:
    """
    Test clear removes specific key from context.

    Tests that clear with key argument removes only
    that specific key.
    """
    # ARRANGE
    context_manager.set("key1", "value1")
    context_manager.set("key2", "value2")

    # ACT
    context_manager.clear("key1")

    # ASSERT
    assert "key1" not in context_manager._context
    assert "key2" in context_manager._context


def test_clear_removes_all_when_no_key(context_manager: ContextManager) -> None:
    """
    Test clear removes all context when no key specified.

    Tests that clear without arguments empties entire
    context dictionary.
    """
    # ARRANGE
    context_manager.set("key1", "value1")
    context_manager.set("key2", "value2")

    # ACT
    context_manager.clear()

    # ASSERT
    assert context_manager._context == {}


def test_clear_handles_missing_key_gracefully(context_manager: ContextManager) -> None:
    """
    Test clear handles non-existent key without error.

    Tests that clear with non-existent key doesn't
    raise exception.
    """
    # ACT & ASSERT - Should not raise
    context_manager.clear("nonexistent")


def test_has_returns_true_when_key_exists(context_manager: ContextManager) -> None:
    """
    Test has returns True when key exists in context.

    Tests that has method correctly identifies
    existing keys.
    """
    # ARRANGE
    context_manager.set("test_key", "value")

    # ACT
    result: bool = context_manager.has("test_key")

    # ASSERT
    assert result is True


def test_has_returns_false_when_key_not_exists(context_manager: ContextManager) -> None:
    """
    Test has returns False when key missing from context.

    Tests that has method correctly identifies
    missing keys.
    """
    # ACT
    result: bool = context_manager.has("missing_key")

    # ASSERT
    assert result is False


def test_get_all_returns_copy_of_context(context_manager: ContextManager) -> None:
    """
    Test get_all returns copy of context dictionary.

    Tests that get_all returns independent copy that
    doesn't affect original context when modified.
    """
    # ARRANGE
    context_manager.set("key1", "value1")
    context_manager.set("key2", "value2")

    # ACT
    context_copy: Dict[str, Any] = context_manager.get_all()
    context_copy["key1"] = "modified"

    # ASSERT
    assert context_copy["key1"] == "modified"
    assert context_manager._context["key1"] == "value1"


# -------------------------------------------------------------
# TESTS: Prompt Generation
# -------------------------------------------------------------


def test_get_prompt_returns_basic_prompt_when_empty(context_manager: ContextManager) -> None:
    """
    Test get_prompt returns basic prompt when context empty.

    Tests that get_prompt returns simple app_name prompt
    when no context is set.
    """
    # ACT
    prompt: str = context_manager.get_prompt()

    # ASSERT
    assert prompt == "test_app> "


def test_get_prompt_includes_context_when_set(populated_context_manager: ContextManager) -> None:
    """
    Test get_prompt includes context values when present.

    Tests that get_prompt incorporates context values
    into prompt string.
    """
    # ACT
    prompt: str = populated_context_manager.get_prompt()

    # ASSERT
    assert "test_app[" in prompt
    assert "]> " in prompt
    assert "prod_instance" in prompt or "main_db" in prompt


def test_get_prompt_formats_multiple_context_values(context_manager: ContextManager) -> None:
    """
    Test get_prompt formats multiple context values correctly.

    Tests that get_prompt joins multiple context values
    with dot separator.
    """
    # ARRANGE
    context_manager.set("instance", "prod")
    context_manager.set("database", "users")
    context_manager.set("table", "accounts")

    # ACT
    prompt: str = context_manager.get_prompt()

    # ASSERT
    assert "test_app[" in prompt
    assert "." in prompt  # Values should be joined with dots


# -------------------------------------------------------------
# TESTS: resolve_argument() - CRITICAL
# -------------------------------------------------------------


def test_resolve_argument_uses_arg_when_provided(context_manager: ContextManager) -> None:
    """
    Test resolve_argument returns provided arg when given.

    Tests that resolve_argument prefers provided argument
    over context value.
    """
    # ARRANGE
    context_manager.set("instance", "context_value")
    arg: str = "provided_value"

    # ACT
    result: str = context_manager.resolve_argument(arg, "instance")

    # ASSERT
    assert result == "provided_value"


def test_resolve_argument_uses_context_when_no_arg(context_manager: ContextManager) -> None:
    """
    Test resolve_argument falls back to context when no arg.

    Tests that resolve_argument retrieves value from context
    when no argument provided.
    """
    # ARRANGE
    context_manager.set("instance", "context_value")

    # ACT
    result: str = context_manager.resolve_argument(None, "instance")

    # ASSERT
    assert result == "context_value"


def test_resolve_argument_raises_when_both_missing(context_manager: ContextManager) -> None:  # CRITICAL TEST
    """
    Test resolve_argument raises ValueError when both missing.

    Tests that resolve_argument raises descriptive error when
    argument not provided and not in context.
    """
    # ACT & ASSERT
    with pytest.raises(ValueError, match="No .* specified and no context set"):
        context_manager.resolve_argument(None, "missing_key")


# -------------------------------------------------------------
# TESTS: resolve_target() - CRITICAL Path Traversal
# -------------------------------------------------------------


def test_resolve_target_parses_compound_argument(context_manager: ContextManager) -> None:
    """
    Test resolve_target splits compound argument correctly.

    Tests that resolve_target parses "primary.secondary" format
    and returns both parts.
    """
    # ARRANGE
    arg: str = "instance.database"

    # ACT
    primary, secondary = context_manager.resolve_target(arg, "instance", "database")

    # ASSERT
    assert primary == "instance"
    assert secondary == "database"


def test_resolve_target_combines_arg_and_context(context_manager: ContextManager) -> None:
    """
    Test resolve_target combines arg with context value.

    Tests that resolve_target uses provided primary argument
    and retrieves secondary from context.
    """
    # ARRANGE
    context_manager.set("database", "context_db")
    arg: str = "instance_arg"

    # ACT
    primary, secondary = context_manager.resolve_target(arg, "instance", "database")

    # ASSERT
    assert primary == "instance_arg"
    assert secondary == "context_db"


def test_resolve_target_uses_both_from_context(context_manager: ContextManager) -> None:
    """
    Test resolve_target retrieves both values from context.

    Tests that resolve_target uses context for both primary
    and secondary when no argument provided.
    """
    # ARRANGE
    context_manager.set("instance", "context_instance")
    context_manager.set("database", "context_db")

    # ACT
    primary, secondary = context_manager.resolve_target(None, "instance", "database")

    # ASSERT
    assert primary == "context_instance"
    assert secondary == "context_db"


def test_resolve_target_raises_when_context_missing(context_manager: ContextManager) -> None:  # CRITICAL TEST
    """
    Test resolve_target raises when context values missing.

    Tests that resolve_target raises ValueError when attempting
    to resolve from context but values not set.
    """
    # ACT & ASSERT
    with pytest.raises(ValueError, match="No .* specified and no context set"):
        context_manager.resolve_target(None, "missing_primary", "missing_secondary")


def test_resolve_target_raises_when_secondary_context_missing(  # CRITICAL TEST
    context_manager: ContextManager,
) -> None:
    """
    Test resolve_target raises when secondary context missing.

    Tests that resolve_target raises ValueError when primary
    provided but secondary not in context.
    """
    # ARRANGE
    arg: str = "primary_value"

    # ACT & ASSERT
    with pytest.raises(ValueError, match="No .* specified and no context set"):
        context_manager.resolve_target(arg, "instance", "missing_secondary")


def test_resolve_target_does_not_validate_path_traversal(context_manager: ContextManager) -> None:  # CRITICAL TEST
    """
    Test resolve_target does NOT prevent path traversal patterns.

    Tests that resolve_target processes compound arguments with
    path traversal patterns by splitting on dots without validation.

    Notes
    -----
    CRITICAL: This test documents that resolve_target splits on '.'
    without validating path safety. If input contains path traversal
    patterns, they will be split but NOT rejected.
    Command handlers MUST validate paths before use.
    """
    # ARRANGE
    # Use traversal pattern with dot separator
    # This will split: "malicious" and "../../etc/passwd"
    traversal_compound: str = "malicious.../../etc/passwd"

    # ACT
    primary, secondary = context_manager.resolve_target(traversal_compound, "instance", "database")

    # ASSERT
    # Should split on first dot, creating potentially dangerous secondary
    assert primary == "malicious"
    assert secondary == "../../etc/passwd"
    # WARNING: secondary contains path traversal - command handlers must validate!


def test_resolve_target_handles_multiple_dots_correctly(context_manager: ContextManager) -> None:
    """
    Test resolve_target splits only on first dot.

    Tests that resolve_target treats additional dots as part
    of secondary component.
    """
    # ARRANGE
    arg: str = "instance.database.table.column"

    # ACT
    primary, secondary = context_manager.resolve_target(arg, "instance", "database")

    # ASSERT
    assert primary == "instance"
    assert secondary == "database.table.column"
