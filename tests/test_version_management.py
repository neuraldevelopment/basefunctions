"""Tests for version management in basefunctions package."""

import re
import basefunctions


def test_version_attribute_exists():
    """Test that __version__ attribute exists."""
    assert hasattr(basefunctions, "__version__")


def test_version_attribute_type():
    """Test that __version__ is a string."""
    assert isinstance(basefunctions.__version__, str)


def test_version_format():
    """Test that version follows semantic versioning."""
    version = basefunctions.__version__

    # Should match: X.Y.Z or X.Y.Z-dev or X.Y.Z-dev+N
    pattern = r"^\d+\.\d+\.\d+(-dev(\+\d+)?)?$"
    assert re.match(pattern, version), f"Version '{version}' doesn't match pattern"


def test_get_version_function_exists():
    """Test that get_version() function exists."""
    assert hasattr(basefunctions, "get_version")
    assert callable(basefunctions.get_version)


def test_get_version_returns_string():
    """Test that get_version() returns a string."""
    version = basefunctions.get_version()
    assert isinstance(version, str)


def test_get_version_matches_attribute():
    """Test that get_version() returns same value as __version__."""
    assert basefunctions.get_version() == basefunctions.__version__


def test_version_consistency_with_runtime():
    """Test that __version__ matches runtime.version()."""
    from basefunctions.runtime.version import version

    runtime_version = version("basefunctions")
    assert basefunctions.__version__ == runtime_version


def test_version_in_all():
    """Test that version symbols are exported in __all__."""
    assert "__version__" in basefunctions.__all__
    assert "get_version" in basefunctions.__all__
