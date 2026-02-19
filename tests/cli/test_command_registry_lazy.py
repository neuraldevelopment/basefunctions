"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.

 Description:
 Tests for CommandRegistry lazy loading functionality.
 Validates lazy handler registration, import, caching, and error handling.
 Added tests for multiple handlers per group (Bug Fix NEURAL-326).

 Log:
 v1.0.0 : Initial test implementation for lazy loading pattern
 v1.1.0 : Added tests for multiple lazy handlers per group (NEURAL-326)
 v1.2.0 : Added tests for get_all_groups with lazy groups
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
# Standard library imports
from unittest.mock import Mock, patch

# External imports
import pytest

# Project imports
from basefunctions.cli import CommandRegistry, ContextManager, BaseCommand, CommandMetadata


# -------------------------------------------------------------
# FIXTURES
# -------------------------------------------------------------


@pytest.fixture
def registry_with_context(mock_context_manager: ContextManager) -> CommandRegistry:
    """
    Provide CommandRegistry with context set.

    Parameters
    ----------
    mock_context_manager : ContextManager
        Context manager fixture

    Returns
    -------
    CommandRegistry
        Registry with context configured

    Notes
    -----
    Required for lazy loading tests
    """
    registry = CommandRegistry()
    registry.set_context(mock_context_manager)
    return registry


@pytest.fixture
def mock_handler_class():
    """
    Provide mock handler class for lazy loading tests.

    Returns
    -------
    Mock
        Mock handler class that can be instantiated

    Notes
    -----
    Simulates external command handler module
    """
    mock_class = Mock(spec=BaseCommand)
    mock_instance = Mock(spec=BaseCommand)
    mock_class.return_value = mock_instance
    return mock_class


# -------------------------------------------------------------
# TESTS: register_group_lazy
# -------------------------------------------------------------


def test_register_group_lazy_with_valid_module_path_succeeds(registry_with_context: CommandRegistry):
    """Test lazy registration with valid module path succeeds."""
    # Arrange
    group_name = "db"
    module_path = "dbfunctions.commands:DatabaseCommands"

    # Act
    registry_with_context.register_group_lazy(group_name, module_path)

    # Assert
    assert group_name in registry_with_context._lazy_groups
    assert registry_with_context._lazy_groups[group_name] == [module_path]


def test_register_group_lazy_with_root_group_succeeds(registry_with_context: CommandRegistry):
    """Test lazy registration for root-level commands succeeds."""
    # Arrange
    group_name = ""
    module_path = "myapp.root:RootCommands"

    # Act
    registry_with_context.register_group_lazy(group_name, module_path)

    # Assert
    assert group_name in registry_with_context._lazy_groups
    assert registry_with_context._lazy_groups[group_name] == [module_path]


def test_register_group_lazy_without_colon_raises_value_error(registry_with_context: CommandRegistry):
    """Test lazy registration without colon raises ValueError."""
    # Arrange
    module_path = "invalid.module.path"

    # Act & Assert
    with pytest.raises(ValueError, match="Invalid module_path format"):
        registry_with_context.register_group_lazy("db", module_path)


def test_register_group_lazy_with_empty_module_path_raises_value_error(registry_with_context: CommandRegistry):
    """Test lazy registration with empty module path raises ValueError."""
    # Arrange
    module_path = ""

    # Act & Assert
    with pytest.raises(ValueError, match="Invalid module_path format"):
        registry_with_context.register_group_lazy("db", module_path)


def test_register_group_lazy_with_multiple_colons_accepts_first_split(registry_with_context: CommandRegistry):
    """Test lazy registration with multiple colons uses rsplit correctly."""
    # Arrange
    group_name = "test"
    module_path = "my:module:with:colons:ClassName"

    # Act
    registry_with_context.register_group_lazy(group_name, module_path)

    # Assert
    assert registry_with_context._lazy_groups[group_name] == [module_path]


def test_register_group_lazy_appends_to_existing_lazy_registration(registry_with_context: CommandRegistry):
    """Test lazy registration appends to previous lazy registration for same group."""
    # Arrange
    group_name = "db"
    first_path = "module.a:ClassA"
    second_path = "module.b:ClassB"

    # Act
    registry_with_context.register_group_lazy(group_name, first_path)
    registry_with_context.register_group_lazy(group_name, second_path)

    # Assert
    assert registry_with_context._lazy_groups[group_name] == [first_path, second_path]


# -------------------------------------------------------------
# TESTS: _import_handler
# -------------------------------------------------------------


def test_import_handler_with_valid_module_succeeds(
    registry_with_context: CommandRegistry, mock_handler_class
):
    """Test import handler with valid module succeeds."""
    # Arrange
    module_path = "test_module:TestClass"

    with patch("importlib.import_module") as mock_import:
        mock_module = Mock()
        mock_module.TestClass = mock_handler_class
        mock_import.return_value = mock_module

        # Act
        handler = registry_with_context._import_handler(module_path)

        # Assert
        assert handler is not None
        mock_import.assert_called_once_with("test_module")
        mock_handler_class.assert_called_once_with(registry_with_context._context)


def test_import_handler_caches_imported_handler(
    registry_with_context: CommandRegistry, mock_handler_class
):
    """Test import handler caches handler after first import."""
    # Arrange
    module_path = "test_module:TestClass"

    with patch("importlib.import_module") as mock_import:
        mock_module = Mock()
        mock_module.TestClass = mock_handler_class
        mock_import.return_value = mock_module

        # Act
        handler1 = registry_with_context._import_handler(module_path)
        handler2 = registry_with_context._import_handler(module_path)

        # Assert
        assert handler1 is handler2
        mock_import.assert_called_once()  # Only imported once
        mock_handler_class.assert_called_once()  # Only instantiated once


def test_import_handler_without_context_raises_runtime_error(mock_command_registry: CommandRegistry):
    """Test import handler without context set raises RuntimeError."""
    # Arrange
    module_path = "test_module:TestClass"

    # Act & Assert
    with pytest.raises(RuntimeError, match="Context not set"):
        mock_command_registry._import_handler(module_path)


def test_import_handler_with_missing_module_raises_module_not_found_error(
    registry_with_context: CommandRegistry
):
    """Test import handler with missing module raises ModuleNotFoundError."""
    # Arrange
    module_path = "nonexistent_module:TestClass"

    with patch("importlib.import_module", side_effect=ModuleNotFoundError("Module not found")):
        # Act & Assert
        with pytest.raises(ModuleNotFoundError, match="Modul nicht gefunden"):
            registry_with_context._import_handler(module_path)


def test_import_handler_with_missing_class_raises_attribute_error(
    registry_with_context: CommandRegistry
):
    """Test import handler with missing class raises AttributeError."""
    # Arrange
    module_path = "test_module:NonExistentClass"

    with patch("importlib.import_module") as mock_import:
        mock_module = Mock(spec=[])  # Empty module
        mock_import.return_value = mock_module

        # Act & Assert
        with pytest.raises(AttributeError, match="Klasse 'NonExistentClass' nicht gefunden"):
            registry_with_context._import_handler(module_path)


def test_import_handler_with_instantiation_failure_raises_runtime_error(
    registry_with_context: CommandRegistry
):
    """Test import handler with instantiation failure raises RuntimeError."""
    # Arrange
    module_path = "test_module:BrokenClass"

    with patch("importlib.import_module") as mock_import:
        mock_module = Mock()
        mock_class = Mock(side_effect=Exception("Init failed"))
        mock_module.BrokenClass = mock_class
        mock_import.return_value = mock_module

        # Act & Assert
        with pytest.raises(RuntimeError, match="Handler-Instanziierung fehlgeschlagen"):
            registry_with_context._import_handler(module_path)


def test_import_handler_with_invalid_format_raises_value_error(registry_with_context: CommandRegistry):
    """Test import handler with invalid format raises ValueError."""
    # Arrange
    module_path = "no_colon_here"

    # Act & Assert
    with pytest.raises(ValueError, match="Ungültiges module_path Format"):
        registry_with_context._import_handler(module_path)


# -------------------------------------------------------------
# TESTS: get_handlers (lazy)
# -------------------------------------------------------------


def test_get_handlers_with_lazy_group_imports_handler(
    registry_with_context: CommandRegistry, mock_handler_class
):
    """Test get_handlers with lazy group imports and returns handler."""
    # Arrange
    group_name = "db"
    module_path = "test_module:TestClass"
    registry_with_context.register_group_lazy(group_name, module_path)

    with patch("importlib.import_module") as mock_import:
        mock_module = Mock()
        mock_module.TestClass = mock_handler_class
        mock_import.return_value = mock_module

        # Act
        handlers = registry_with_context.get_handlers(group_name)

        # Assert
        assert len(handlers) == 1
        assert handlers[0] == mock_handler_class.return_value


def test_get_handlers_with_lazy_group_caches_on_second_call(
    registry_with_context: CommandRegistry, mock_handler_class
):
    """Test get_handlers with lazy group uses cache on second call."""
    # Arrange
    group_name = "db"
    module_path = "test_module:TestClass"
    registry_with_context.register_group_lazy(group_name, module_path)

    with patch("importlib.import_module") as mock_import:
        mock_module = Mock()
        mock_module.TestClass = mock_handler_class
        mock_import.return_value = mock_module

        # Act
        handlers1 = registry_with_context.get_handlers(group_name)
        handlers2 = registry_with_context.get_handlers(group_name)

        # Assert
        assert handlers1[0] is handlers2[0]  # Same instance
        mock_import.assert_called_once()  # Only imported once


def test_get_handlers_with_both_eager_and_lazy_returns_both(
    registry_with_context: CommandRegistry, mock_handler_class, concrete_base_command: BaseCommand
):
    """Test get_handlers with both eager and lazy handlers returns both."""
    # Arrange
    group_name = "db"
    module_path = "test_module:TestClass"

    registry_with_context.register_group(group_name, concrete_base_command)  # Eager
    registry_with_context.register_group_lazy(group_name, module_path)  # Lazy

    with patch("importlib.import_module") as mock_import:
        mock_module = Mock()
        mock_module.TestClass = mock_handler_class
        mock_import.return_value = mock_module

        # Act
        handlers = registry_with_context.get_handlers(group_name)

        # Assert
        assert len(handlers) == 2
        assert concrete_base_command in handlers
        assert mock_handler_class.return_value in handlers


def test_get_handlers_with_nonexistent_lazy_group_returns_empty_list(
    registry_with_context: CommandRegistry
):
    """Test get_handlers with nonexistent lazy group returns empty list."""
    # Arrange
    group_name = "nonexistent"

    # Act
    handlers = registry_with_context.get_handlers(group_name)

    # Assert
    assert handlers == []


def test_get_handlers_with_lazy_import_error_propagates_exception(
    registry_with_context: CommandRegistry
):
    """Test get_handlers with lazy import error propagates exception."""
    # Arrange
    group_name = "db"
    module_path = "broken_module:BrokenClass"
    registry_with_context.register_group_lazy(group_name, module_path)

    with patch("importlib.import_module", side_effect=ModuleNotFoundError("Module not found")):
        # Act & Assert
        with pytest.raises(ModuleNotFoundError):
            registry_with_context.get_handlers(group_name)


# -------------------------------------------------------------
# TESTS: dispatch (lazy)
# -------------------------------------------------------------


def test_dispatch_with_lazy_handler_executes_command(
    registry_with_context: CommandRegistry, mock_handler_class
):
    """Test dispatch with lazy handler executes command successfully."""
    # Arrange
    group_name = "db"
    command = "list"
    args = ["--verbose"]
    module_path = "test_module:TestClass"

    mock_instance = mock_handler_class.return_value
    mock_instance.validate_command.return_value = True
    mock_instance.execute = Mock()

    registry_with_context.register_group_lazy(group_name, module_path)

    with patch("importlib.import_module") as mock_import:
        mock_module = Mock()
        mock_module.TestClass = mock_handler_class
        mock_import.return_value = mock_module

        # Act
        result = registry_with_context.dispatch(group_name, command, args)

        # Assert
        assert result is True
        mock_instance.validate_command.assert_called_once_with(command)
        mock_instance.execute.assert_called_once_with(command, args)


def test_dispatch_with_lazy_group_not_found_raises_value_error(
    registry_with_context: CommandRegistry
):
    """Test dispatch with nonexistent lazy group raises ValueError."""
    # Arrange
    group_name = "nonexistent"
    command = "list"
    args = []

    # Act & Assert
    with pytest.raises(ValueError, match="Unknown command group"):
        registry_with_context.dispatch(group_name, command, args)


def test_dispatch_with_lazy_handler_command_not_found_raises_value_error(
    registry_with_context: CommandRegistry, mock_handler_class
):
    """Test dispatch with lazy handler but invalid command raises ValueError."""
    # Arrange
    group_name = "db"
    command = "invalid_command"
    args = []
    module_path = "test_module:TestClass"

    mock_instance = mock_handler_class.return_value
    mock_instance.validate_command.return_value = False
    mock_instance.get_available_commands.return_value = ["list", "create", "delete"]

    registry_with_context.register_group_lazy(group_name, module_path)

    with patch("importlib.import_module") as mock_import:
        mock_module = Mock()
        mock_module.TestClass = mock_handler_class
        mock_import.return_value = mock_module

        # Act & Assert
        with pytest.raises(ValueError, match="Unknown command: invalid_command"):
            registry_with_context.dispatch(group_name, command, args)


# -------------------------------------------------------------
# TESTS: get_command_metadata (lazy)
# -------------------------------------------------------------


def test_get_command_metadata_with_lazy_handler_returns_metadata(
    registry_with_context: CommandRegistry, mock_handler_class, sample_command_metadata
):
    """Test get_command_metadata with lazy handler returns metadata."""
    # Arrange
    group_name = "db"
    command = "list"
    module_path = "test_module:TestClass"

    mock_instance = mock_handler_class.return_value
    mock_instance.get_command_metadata.return_value = sample_command_metadata

    registry_with_context.register_group_lazy(group_name, module_path)

    with patch("importlib.import_module") as mock_import:
        mock_module = Mock()
        mock_module.TestClass = mock_handler_class
        mock_import.return_value = mock_module

        # Act
        metadata = registry_with_context.get_command_metadata(group_name, command)

        # Assert
        assert metadata == sample_command_metadata
        mock_instance.get_command_metadata.assert_called_once_with(command)


def test_get_command_metadata_with_lazy_handler_not_found_returns_none(
    registry_with_context: CommandRegistry, mock_handler_class
):
    """Test get_command_metadata with lazy handler but command not found returns None."""
    # Arrange
    group_name = "db"
    command = "nonexistent"
    module_path = "test_module:TestClass"

    mock_instance = mock_handler_class.return_value
    mock_instance.get_command_metadata.return_value = None

    registry_with_context.register_group_lazy(group_name, module_path)

    with patch("importlib.import_module") as mock_import:
        mock_module = Mock()
        mock_module.TestClass = mock_handler_class
        mock_import.return_value = mock_module

        # Act
        metadata = registry_with_context.get_command_metadata(group_name, command)

        # Assert
        assert metadata is None


# -------------------------------------------------------------
# TESTS: Edge Cases
# -------------------------------------------------------------


def test_lazy_handler_with_none_context_raises_runtime_error(mock_command_registry: CommandRegistry):
    """Test lazy handler access without context raises RuntimeError."""
    # Arrange
    group_name = "db"
    module_path = "test_module:TestClass"
    mock_command_registry.register_group_lazy(group_name, module_path)

    # Act & Assert
    with pytest.raises(RuntimeError, match="Context not set"):
        mock_command_registry.get_handlers(group_name)


def test_lazy_handler_with_empty_group_name_succeeds(
    registry_with_context: CommandRegistry, mock_handler_class
):
    """Test lazy handler with empty group name (root) succeeds."""
    # Arrange
    group_name = ""
    module_path = "test_module:TestClass"
    registry_with_context.register_group_lazy(group_name, module_path)

    with patch("importlib.import_module") as mock_import:
        mock_module = Mock()
        mock_module.TestClass = mock_handler_class
        mock_import.return_value = mock_module

        # Act
        handlers = registry_with_context.get_handlers(group_name)

        # Assert
        assert len(handlers) == 1


def test_lazy_handler_cache_isolation_between_groups(
    registry_with_context: CommandRegistry
):
    """Test lazy handler cache maintains isolation between different groups."""
    # Arrange
    group1 = "db"
    group2 = "api"
    path1 = "module.a:ClassA"
    path2 = "module.b:ClassB"

    registry_with_context.register_group_lazy(group1, path1)
    registry_with_context.register_group_lazy(group2, path2)

    # Create separate mock handler classes for each path
    mock_class_a = Mock(spec=BaseCommand)
    mock_instance_a = Mock(spec=BaseCommand)
    mock_class_a.return_value = mock_instance_a

    mock_class_b = Mock(spec=BaseCommand)
    mock_instance_b = Mock(spec=BaseCommand)
    mock_class_b.return_value = mock_instance_b

    with patch("importlib.import_module") as mock_import:
        def side_effect(module_name):
            mock_module = Mock()
            if "module.a" in module_name:
                mock_module.ClassA = mock_class_a
            else:
                mock_module.ClassB = mock_class_b
            return mock_module

        mock_import.side_effect = side_effect

        # Act
        handlers1 = registry_with_context.get_handlers(group1)
        handlers2 = registry_with_context.get_handlers(group2)

        # Assert
        assert len(handlers1) == 1
        assert len(handlers2) == 1
        assert handlers1[0] is not handlers2[0]  # Different instances
        assert handlers1[0] == mock_instance_a
        assert handlers2[0] == mock_instance_b


def test_lazy_handler_with_complex_module_path_succeeds(
    registry_with_context: CommandRegistry, mock_handler_class
):
    """Test lazy handler with deeply nested module path succeeds."""
    # Arrange
    group_name = "db"
    module_path = "deeply.nested.module.structure.commands:VerySpecificCommand"
    registry_with_context.register_group_lazy(group_name, module_path)

    with patch("importlib.import_module") as mock_import:
        mock_module = Mock()
        mock_module.VerySpecificCommand = mock_handler_class
        mock_import.return_value = mock_module

        # Act
        handlers = registry_with_context.get_handlers(group_name)

        # Assert
        assert len(handlers) == 1
        mock_import.assert_called_once_with("deeply.nested.module.structure.commands")


# -------------------------------------------------------------
# TESTS: Multiple Lazy Handlers (Bug Fix NEURAL-326)
# -------------------------------------------------------------


def test_multiple_lazy_root_groups_no_collision(
    registry_with_context: CommandRegistry
):
    """Test multiple lazy root groups with empty group name do not collide."""
    # Arrange
    group_name = ""
    paths = [
        "module1.commands:Handler1",
        "module2.commands:Handler2",
        "module3.commands:Handler3",
        "module4.commands:Handler4",
    ]

    # Create separate mock handlers for each path
    mock_handlers = []
    for _ in range(4):
        mock_class = Mock(spec=BaseCommand)
        mock_instance = Mock(spec=BaseCommand)
        mock_class.return_value = mock_instance
        mock_handlers.append((mock_class, mock_instance))

    # Act - Register all 4 handlers
    for path in paths:
        registry_with_context.register_group_lazy(group_name, path)

    # Assert - All 4 paths stored
    assert len(registry_with_context._lazy_groups[group_name]) == 4
    assert registry_with_context._lazy_groups[group_name] == paths

    # Act - Load handlers
    with patch("importlib.import_module") as mock_import:
        def side_effect(module_name):
            mock_module = Mock()
            if "module1" in module_name:
                mock_module.Handler1 = mock_handlers[0][0]
            elif "module2" in module_name:
                mock_module.Handler2 = mock_handlers[1][0]
            elif "module3" in module_name:
                mock_module.Handler3 = mock_handlers[2][0]
            elif "module4" in module_name:
                mock_module.Handler4 = mock_handlers[3][0]
            return mock_module

        mock_import.side_effect = side_effect
        handlers = registry_with_context.get_handlers(group_name)

        # Assert - All 4 handlers loaded
        assert len(handlers) == 4
        assert handlers[0] == mock_handlers[0][1]
        assert handlers[1] == mock_handlers[1][1]
        assert handlers[2] == mock_handlers[2][1]
        assert handlers[3] == mock_handlers[3][1]


def test_multiple_lazy_same_named_group_preserves_order(
    registry_with_context: CommandRegistry
):
    """Test multiple lazy handlers for same named group preserves order."""
    # Arrange
    group_name = "mygroup"
    paths = [
        "moduleA:HandlerA",
        "moduleB:HandlerB",
        "moduleC:HandlerC",
    ]

    # Create mock handlers
    mock_handlers = []
    for _ in range(3):
        mock_class = Mock(spec=BaseCommand)
        mock_instance = Mock(spec=BaseCommand)
        mock_class.return_value = mock_instance
        mock_handlers.append((mock_class, mock_instance))

    # Act - Register 3 handlers
    for path in paths:
        registry_with_context.register_group_lazy(group_name, path)

    # Assert - Order preserved
    assert registry_with_context._lazy_groups[group_name] == paths

    # Act - Load handlers
    with patch("importlib.import_module") as mock_import:
        def side_effect(module_name):
            mock_module = Mock()
            if "moduleA" in module_name:
                mock_module.HandlerA = mock_handlers[0][0]
            elif "moduleB" in module_name:
                mock_module.HandlerB = mock_handlers[1][0]
            elif "moduleC" in module_name:
                mock_module.HandlerC = mock_handlers[2][0]
            return mock_module

        mock_import.side_effect = side_effect
        handlers = registry_with_context.get_handlers(group_name)

        # Assert - All 3 loaded in order
        assert len(handlers) == 3
        assert handlers[0] == mock_handlers[0][1]
        assert handlers[1] == mock_handlers[1][1]
        assert handlers[2] == mock_handlers[2][1]


def test_mixed_eager_lazy_same_group_combines_all_handlers(
    registry_with_context: CommandRegistry, concrete_base_command: BaseCommand
):
    """Test mixed eager and lazy handlers for same group combines all."""
    # Arrange
    group_name = "test"

    # Create second eager handler
    from unittest.mock import Mock
    from typing import Dict, List

    class SecondEagerHandler(BaseCommand):
        def register_commands(self) -> Dict[str, CommandMetadata]:
            return {"second": CommandMetadata("second", "desc", "usage", [])}

        def execute(self, command: str, args: List[str]) -> None:  # pyright: ignore[reportUnusedParameter]
            pass

    second_eager = SecondEagerHandler(registry_with_context._context)

    # Create mock lazy handlers
    mock_lazy1 = Mock(spec=BaseCommand)
    mock_lazy1_instance = Mock(spec=BaseCommand)
    mock_lazy1.return_value = mock_lazy1_instance

    mock_lazy2 = Mock(spec=BaseCommand)
    mock_lazy2_instance = Mock(spec=BaseCommand)
    mock_lazy2.return_value = mock_lazy2_instance

    # Act - Register 2 eager + 2 lazy
    registry_with_context.register_group(group_name, concrete_base_command)
    registry_with_context.register_group(group_name, second_eager)
    registry_with_context.register_group_lazy(group_name, "lazy1:Handler1")
    registry_with_context.register_group_lazy(group_name, "lazy2:Handler2")

    # Assert - Lazy storage correct
    assert len(registry_with_context._lazy_groups[group_name]) == 2

    # Act - Load all handlers
    with patch("importlib.import_module") as mock_import:
        def side_effect(module_name):
            mock_module = Mock()
            if "lazy1" in module_name:
                mock_module.Handler1 = mock_lazy1
            elif "lazy2" in module_name:
                mock_module.Handler2 = mock_lazy2
            return mock_module

        mock_import.side_effect = side_effect
        handlers = registry_with_context.get_handlers(group_name)

        # Assert - All 4 handlers present (2 eager + 2 lazy)
        assert len(handlers) == 4
        assert concrete_base_command in handlers
        assert second_eager in handlers
        assert mock_lazy1_instance in handlers
        assert mock_lazy2_instance in handlers


def test_lazy_single_handler_regression_still_works(
    registry_with_context: CommandRegistry, mock_handler_class
):
    """Test single lazy handler registration still works after list change."""
    # Arrange
    group_name = "single"
    module_path = "single.module:SingleHandler"
    registry_with_context.register_group_lazy(group_name, module_path)

    with patch("importlib.import_module") as mock_import:
        mock_module = Mock()
        mock_module.SingleHandler = mock_handler_class
        mock_import.return_value = mock_module

        # Act
        handlers = registry_with_context.get_handlers(group_name)

        # Assert - Single handler works
        assert len(handlers) == 1
        assert handlers[0] == mock_handler_class.return_value
        mock_import.assert_called_once_with("single.module")


def test_lazy_load_cache_not_broken_by_multiple_groups(
    registry_with_context: CommandRegistry
):
    """Test lazy handler cache maintains isolation with multiple groups using same module."""
    # Arrange
    group1 = "group1"
    group2 = "group2"
    same_path = "shared.module:SharedHandler"

    # Create mock handler
    mock_class = Mock(spec=BaseCommand)
    mock_instance = Mock(spec=BaseCommand)
    mock_class.return_value = mock_instance

    # Act - Register same module path for 2 different groups
    registry_with_context.register_group_lazy(group1, same_path)
    registry_with_context.register_group_lazy(group2, same_path)

    with patch("importlib.import_module") as mock_import:
        mock_module = Mock()
        mock_module.SharedHandler = mock_class
        mock_import.return_value = mock_module

        # Act - Load handlers from both groups
        handlers1 = registry_with_context.get_handlers(group1)
        handlers2 = registry_with_context.get_handlers(group2)

        # Assert - Module imported only once (cache works)
        mock_import.assert_called_once_with("shared.module")
        mock_class.assert_called_once()  # Instantiated only once

        # Assert - Both groups return same instance (from cache)
        assert len(handlers1) == 1
        assert len(handlers2) == 1
        assert handlers1[0] is handlers2[0]  # Same cached instance
        assert handlers1[0] == mock_instance


# -------------------------------------------------------------
# TESTS: get_all_groups
# -------------------------------------------------------------


def test_get_all_groups_with_only_lazy_groups_returns_lazy_groups(
    mock_command_registry: CommandRegistry,
) -> None:
    """
    Test get_all_groups returns lazy-only groups when no eager groups registered.

    Parameters
    ----------
    mock_command_registry : CommandRegistry
        Fresh registry without context

    Notes
    -----
    get_all_groups must not trigger lazy loading, so no context needed
    """
    # Arrange
    mock_command_registry._lazy_groups["db"] = ["module.a:ClassA"]
    mock_command_registry._lazy_groups["api"] = ["module.b:ClassB"]

    # Act
    result = mock_command_registry.get_all_groups()

    # Assert
    assert set(result) == {"db", "api"}


def test_get_all_groups_with_eager_and_lazy_groups_returns_all(
    mock_command_registry: CommandRegistry,
    concrete_base_command: BaseCommand,
) -> None:
    """
    Test get_all_groups returns combined eager and lazy groups.

    Parameters
    ----------
    mock_command_registry : CommandRegistry
        Fresh registry without context
    concrete_base_command : BaseCommand
        Eager handler instance

    Notes
    -----
    Verifies that both registration paths are visible in get_all_groups
    """
    # Arrange
    mock_command_registry.register_group("eager_group", concrete_base_command)
    mock_command_registry._lazy_groups["lazy_group"] = ["module.x:ClassX"]

    # Act
    result = mock_command_registry.get_all_groups()

    # Assert
    assert set(result) == {"eager_group", "lazy_group"}


def test_get_all_groups_with_group_in_both_returns_deduplicated(
    mock_command_registry: CommandRegistry,
    concrete_base_command: BaseCommand,
) -> None:
    """
    Test get_all_groups deduplicates when a group appears in both registries.

    Parameters
    ----------
    mock_command_registry : CommandRegistry
        Fresh registry without context
    concrete_base_command : BaseCommand
        Eager handler instance

    Notes
    -----
    dict.fromkeys preserves insertion order and removes duplicates
    """
    # Arrange
    mock_command_registry.register_group("shared", concrete_base_command)
    mock_command_registry._lazy_groups["shared"] = ["module.y:ClassY"]

    # Act
    result = mock_command_registry.get_all_groups()

    # Assert - "shared" appears exactly once
    assert result.count("shared") == 1
