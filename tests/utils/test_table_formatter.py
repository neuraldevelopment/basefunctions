"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Tests for get_table_format() function from table_renderer module
 Log:
 v1.4 : Updated imports - get_table_format() moved from table_formatter to table_renderer
 v1.3 : Rewritten import pattern - module import FIRST, then patch ConfigHandler
 v1.2 : Fixed circular import with isolated module patch
 v1.1 : Fixed coverage 0% issue - import module before mocking
 v1.0 : Initial implementation
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
# Standard Library
from unittest.mock import MagicMock, patch


# =============================================================================
# TEST FUNCTIONS - get_table_format()
# =============================================================================
def test_get_table_format_returns_default_grid():
    """Test get_table_format() returns default 'grid' format."""
    # Arrange - Import module FIRST
    from basefunctions.utils.table_renderer import get_table_format

    # Then patch ConfigHandler
    with patch("basefunctions.config.config_handler.ConfigHandler") as MockConfigHandler:
        mock_instance = MagicMock()
        mock_instance.get_config_parameter.return_value = "grid"
        MockConfigHandler.return_value = mock_instance

        # Act
        result = get_table_format()

        # Assert
        assert result == "grid"
        mock_instance.get_config_parameter.assert_called_once_with(
            "basefunctions/table_format", default_value="grid"
        )


def test_get_table_format_returns_custom_format_simple():
    """Test get_table_format() returns custom format 'simple' from config."""
    from basefunctions.utils.table_renderer import get_table_format

    with patch("basefunctions.config.config_handler.ConfigHandler") as MockConfigHandler:
        mock_instance = MagicMock()
        mock_instance.get_config_parameter.return_value = "simple"
        MockConfigHandler.return_value = mock_instance
        result = get_table_format()
        assert result == "simple"


def test_get_table_format_returns_custom_format_plain():
    """Test get_table_format() returns custom format 'plain' from config."""
    from basefunctions.utils.table_renderer import get_table_format

    with patch("basefunctions.config.config_handler.ConfigHandler") as MockConfigHandler:
        mock_instance = MagicMock()
        mock_instance.get_config_parameter.return_value = "plain"
        MockConfigHandler.return_value = mock_instance
        result = get_table_format()
        assert result == "plain"


def test_get_table_format_uses_correct_config_path():
    """Test get_table_format() uses correct config path 'basefunctions/table_format'."""
    from basefunctions.utils.table_renderer import get_table_format

    with patch("basefunctions.config.config_handler.ConfigHandler") as MockConfigHandler:
        mock_instance = MagicMock()
        mock_instance.get_config_parameter.return_value = "grid"
        MockConfigHandler.return_value = mock_instance
        get_table_format()
        call_args = mock_instance.get_config_parameter.call_args
        assert call_args[0][0] == "basefunctions/table_format"
        assert call_args[1]["default_value"] == "grid"


def test_get_table_format_returns_default_when_config_missing():
    """Test get_table_format() returns 'grid' when config entry missing (ConfigHandler default)."""
    from basefunctions.utils.table_renderer import get_table_format

    with patch("basefunctions.config.config_handler.ConfigHandler") as MockConfigHandler:
        mock_instance = MagicMock()
        mock_instance.get_config_parameter.return_value = "grid"
        MockConfigHandler.return_value = mock_instance
        result = get_table_format()
        assert result == "grid"


def test_get_table_format_returns_default_when_config_none():
    """Test get_table_format() returns 'grid' when config value is None (ConfigHandler default fallback)."""
    from basefunctions.utils.table_renderer import get_table_format

    with patch("basefunctions.config.config_handler.ConfigHandler") as MockConfigHandler:
        mock_instance = MagicMock()
        mock_instance.get_config_parameter.return_value = "grid"
        MockConfigHandler.return_value = mock_instance
        result = get_table_format()
        assert result == "grid"


def test_get_table_format_creates_config_handler_instance():
    """Test get_table_format() creates ConfigHandler instance."""
    from basefunctions.utils.table_renderer import get_table_format

    with patch("basefunctions.config.config_handler.ConfigHandler") as MockConfigHandler:
        mock_instance = MagicMock()
        mock_instance.get_config_parameter.return_value = "grid"
        MockConfigHandler.return_value = mock_instance
        get_table_format()
        MockConfigHandler.assert_called_once()


def test_get_table_format_supports_github_markdown_format():
    """Test get_table_format() returns 'github' format (GitHub Markdown tables)."""
    from basefunctions.utils.table_renderer import get_table_format

    with patch("basefunctions.config.config_handler.ConfigHandler") as MockConfigHandler:
        mock_instance = MagicMock()
        mock_instance.get_config_parameter.return_value = "github"
        MockConfigHandler.return_value = mock_instance
        result = get_table_format()
        assert result == "github"


def test_get_table_format_supports_fancy_grid_format():
    """Test get_table_format() returns 'fancy_grid' format (box-drawing characters)."""
    from basefunctions.utils.table_renderer import get_table_format

    with patch("basefunctions.config.config_handler.ConfigHandler") as MockConfigHandler:
        mock_instance = MagicMock()
        mock_instance.get_config_parameter.return_value = "fancy_grid"
        MockConfigHandler.return_value = mock_instance
        result = get_table_format()
        assert result == "fancy_grid"


def test_get_table_format_supports_pipe_format():
    """Test get_table_format() returns 'pipe' format (Markdown pipe tables)."""
    from basefunctions.utils.table_renderer import get_table_format

    with patch("basefunctions.config.config_handler.ConfigHandler") as MockConfigHandler:
        mock_instance = MagicMock()
        mock_instance.get_config_parameter.return_value = "pipe"
        MockConfigHandler.return_value = mock_instance
        result = get_table_format()
        assert result == "pipe"


def test_get_table_format_returns_string():
    """Test get_table_format() always returns string type."""
    from basefunctions.utils.table_renderer import get_table_format

    with patch("basefunctions.config.config_handler.ConfigHandler") as MockConfigHandler:
        mock_instance = MagicMock()
        mock_instance.get_config_parameter.return_value = "grid"
        MockConfigHandler.return_value = mock_instance
        result = get_table_format()
        assert isinstance(result, str)


# =============================================================================
# EDGE CASE TESTS
# =============================================================================
def test_get_table_format_with_empty_string_returns_empty():
    """Test get_table_format() returns empty string when config has empty string."""
    from basefunctions.utils.table_renderer import get_table_format

    with patch("basefunctions.config.config_handler.ConfigHandler") as MockConfigHandler:
        mock_instance = MagicMock()
        mock_instance.get_config_parameter.return_value = ""
        MockConfigHandler.return_value = mock_instance
        result = get_table_format()
        assert result == ""


def test_get_table_format_with_whitespace_string():
    """Test get_table_format() returns whitespace when config has whitespace string."""
    from basefunctions.utils.table_renderer import get_table_format

    with patch("basefunctions.config.config_handler.ConfigHandler") as MockConfigHandler:
        mock_instance = MagicMock()
        mock_instance.get_config_parameter.return_value = "   "
        MockConfigHandler.return_value = mock_instance
        result = get_table_format()
        assert result == "   "


def test_get_table_format_thread_safe_singleton():
    """Test get_table_format() works with ConfigHandler thread-safe singleton."""
    from basefunctions.utils.table_renderer import get_table_format

    with patch("basefunctions.config.config_handler.ConfigHandler") as MockConfigHandler:
        mock_instance = MagicMock()
        mock_instance.get_config_parameter.return_value = "grid"
        MockConfigHandler.return_value = mock_instance
        result1 = get_table_format()
        result2 = get_table_format()
        assert result1 == result2
        assert result1 == "grid"


# =============================================================================
# BACKWARD COMPATIBILITY TESTS
# =============================================================================
def test_get_table_format_backward_compatibility_grid_default():
    """Test get_table_format() maintains backward compatibility with 'grid' as default."""
    from basefunctions.utils.table_renderer import get_table_format

    with patch("basefunctions.config.config_handler.ConfigHandler") as MockConfigHandler:
        mock_instance = MagicMock()
        mock_instance.get_config_parameter.return_value = "grid"
        MockConfigHandler.return_value = mock_instance
        result = get_table_format()
        assert result == "grid"
