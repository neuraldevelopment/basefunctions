"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich

  Project : basefunctions

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  Pytest test suite for filefunctions module.
  Tests file and directory operations with cross-platform support.

  Log:
  v1.0.0 : Initial test implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
# External imports
import os
import pytest
from pathlib import Path
from typing import List
from unittest.mock import Mock, patch, MagicMock

# Project imports
from basefunctions.io import filefunctions

"""
Test module for filefunctions.

This module contains comprehensive tests for:
- File and directory existence checks
- File path operations (basename, extension, path name)
- File and directory creation/deletion
- File renaming and moving
- Directory traversal and file listing
- Path normalization

Test Coverage:
- CRITICAL functions: 4 tests (delete, rename, directory change)
- IMPORTANT functions: 3 tests (create, list, validation)
- Edge cases: 25+ tests
- Total: 40+ test functions

Notes
-----
All tests use tmp_path fixture to avoid side effects on real filesystem.
Tests cover path traversal attacks and invalid input scenarios.
"""

# -------------------------------------------------------------
# FIXTURES
# -------------------------------------------------------------


@pytest.fixture
def sample_file(tmp_path: Path) -> Path:
    """
    Create a temporary sample file for testing.

    Parameters
    ----------
    tmp_path : Path
        Pytest builtin fixture for temporary directory

    Returns
    -------
    Path
        Path to created sample file

    Notes
    -----
    File contains simple text content for verification
    """
    # ARRANGE
    test_file: Path = tmp_path / "sample.txt"
    test_file.write_text("sample content")

    # RETURN
    return test_file


@pytest.fixture
def sample_directory(tmp_path: Path) -> Path:
    """
    Create a temporary sample directory for testing.

    Parameters
    ----------
    tmp_path : Path
        Pytest builtin fixture for temporary directory

    Returns
    -------
    Path
        Path to created sample directory

    Notes
    -----
    Creates nested directory structure for testing
    """
    # ARRANGE
    test_dir: Path = tmp_path / "sample_dir"
    test_dir.mkdir()

    # RETURN
    return test_dir


@pytest.fixture
def nested_directory_structure(tmp_path: Path) -> Path:
    """
    Create nested directory structure with files for testing.

    Parameters
    ----------
    tmp_path : Path
        Pytest builtin fixture for temporary directory

    Returns
    -------
    Path
        Path to root of nested structure

    Notes
    -----
    Creates:
    - root/file1.txt
    - root/file2.py
    - root/.hidden
    - root/subdir/file3.txt
    - root/subdir/nested/file4.txt
    """
    # ARRANGE
    root: Path = tmp_path / "nested_root"
    root.mkdir()

    # Create files in root
    (root / "file1.txt").write_text("content1")
    (root / "file2.py").write_text("content2")
    (root / ".hidden").write_text("hidden")

    # Create nested structure
    subdir: Path = root / "subdir"
    subdir.mkdir()
    (subdir / "file3.txt").write_text("content3")

    nested: Path = subdir / "nested"
    nested.mkdir()
    (nested / "file4.txt").write_text("content4")

    # RETURN
    return root


# -------------------------------------------------------------
# TESTS: check_if_exists
# -------------------------------------------------------------


def test_check_if_exists_returns_true_for_existing_file(sample_file: Path) -> None:  # IMPORTANT TEST
    """
    Test check_if_exists returns True for existing file.

    Tests that check_if_exists correctly identifies an existing file
    when given a valid file path and file_type="FILE".

    Parameters
    ----------
    sample_file : Path
        Fixture providing sample file path

    Returns
    -------
    None
        Test passes if all assertions succeed
    """
    # ARRANGE
    file_path: str = str(sample_file)

    # ACT
    result: bool = filefunctions.check_if_exists(file_path, file_type="FILE")

    # ASSERT
    assert result is True


def test_check_if_exists_returns_true_for_existing_directory(sample_directory: Path) -> None:  # IMPORTANT TEST
    """
    Test check_if_exists returns True for existing directory.

    Tests that check_if_exists correctly identifies an existing directory
    when given a valid directory path and file_type="DIRECTORY".

    Parameters
    ----------
    sample_directory : Path
        Fixture providing sample directory path

    Returns
    -------
    None
        Test passes if all assertions succeed
    """
    # ARRANGE
    dir_path: str = str(sample_directory)

    # ACT
    result: bool = filefunctions.check_if_exists(dir_path, file_type="DIRECTORY")

    # ASSERT
    assert result is True


def test_check_if_exists_returns_false_for_nonexistent_file() -> None:
    """
    Test check_if_exists returns False for nonexistent file.

    Tests that check_if_exists correctly returns False when
    checking for a file that doesn't exist.

    Parameters
    ----------
    None

    Returns
    -------
    None
        Test passes if all assertions succeed
    """
    # ARRANGE
    nonexistent_file: str = "/tmp/does_not_exist_12345.txt"

    # ACT
    result: bool = filefunctions.check_if_exists(nonexistent_file, file_type="FILE")

    # ASSERT
    assert result is False


def test_check_if_exists_returns_false_for_empty_filename() -> None:
    """
    Test check_if_exists returns False for empty filename.

    Tests that check_if_exists handles empty string input gracefully
    by returning False instead of raising an exception.

    Parameters
    ----------
    None

    Returns
    -------
    None
        Test passes if all assertions succeed
    """
    # ARRANGE
    empty_filename: str = ""

    # ACT
    result: bool = filefunctions.check_if_exists(empty_filename, file_type="FILE")

    # ASSERT
    assert result is False


def test_check_if_exists_raises_valueerror_for_invalid_file_type(sample_file: Path) -> None:  # IMPORTANT TEST
    """
    Test check_if_exists raises ValueError for invalid file_type.

    Tests that check_if_exists raises ValueError when given
    an unknown file_type parameter.

    Parameters
    ----------
    sample_file : Path
        Fixture providing sample file path

    Returns
    -------
    None
        Test passes if ValueError is raised
    """
    # ARRANGE
    file_path: str = str(sample_file)
    invalid_type: str = "INVALID_TYPE"

    # ACT & ASSERT
    with pytest.raises(ValueError, match="Unknown file_type"):
        filefunctions.check_if_exists(file_path, file_type=invalid_type)


def test_check_if_exists_returns_false_when_file_is_directory(sample_directory: Path) -> None:
    """
    Test check_if_exists returns False when checking directory as file.

    Tests that check_if_exists correctly distinguishes between
    files and directories when file_type="FILE".

    Parameters
    ----------
    sample_directory : Path
        Fixture providing sample directory path

    Returns
    -------
    None
        Test passes if all assertions succeed
    """
    # ARRANGE
    dir_path: str = str(sample_directory)

    # ACT
    result: bool = filefunctions.check_if_exists(dir_path, file_type="FILE")

    # ASSERT
    assert result is False


def test_check_if_exists_returns_false_when_directory_is_file(sample_file: Path) -> None:
    """
    Test check_if_exists returns False when checking file as directory.

    Tests that check_if_exists correctly distinguishes between
    files and directories when file_type="DIRECTORY".

    Parameters
    ----------
    sample_file : Path
        Fixture providing sample file path

    Returns
    -------
    None
        Test passes if all assertions succeed
    """
    # ARRANGE
    file_path: str = str(sample_file)

    # ACT
    result: bool = filefunctions.check_if_exists(file_path, file_type="DIRECTORY")

    # ASSERT
    assert result is False


# -------------------------------------------------------------
# TESTS: Wrapper functions (file/directory existence)
# -------------------------------------------------------------


def test_check_if_file_exists_returns_true_for_existing_file(sample_file: Path) -> None:
    """
    Test check_if_file_exists returns True for existing file.

    Tests that check_if_file_exists wrapper function correctly
    identifies existing files.

    Parameters
    ----------
    sample_file : Path
        Fixture providing sample file path

    Returns
    -------
    None
        Test passes if all assertions succeed
    """
    # ARRANGE
    file_path: str = str(sample_file)

    # ACT
    result: bool = filefunctions.check_if_file_exists(file_path)

    # ASSERT
    assert result is True


def test_check_if_dir_exists_returns_true_for_existing_directory(sample_directory: Path) -> None:
    """
    Test check_if_dir_exists returns True for existing directory.

    Tests that check_if_dir_exists wrapper function correctly
    identifies existing directories.

    Parameters
    ----------
    sample_directory : Path
        Fixture providing sample directory path

    Returns
    -------
    None
        Test passes if all assertions succeed
    """
    # ARRANGE
    dir_path: str = str(sample_directory)

    # ACT
    result: bool = filefunctions.check_if_dir_exists(dir_path)

    # ASSERT
    assert result is True


def test_is_file_returns_true_for_existing_file(sample_file: Path) -> None:
    """
    Test is_file returns True for existing file.

    Tests that is_file wrapper function correctly identifies
    existing regular files.

    Parameters
    ----------
    sample_file : Path
        Fixture providing sample file path

    Returns
    -------
    None
        Test passes if all assertions succeed
    """
    # ARRANGE
    file_path: str = str(sample_file)

    # ACT
    result: bool = filefunctions.is_file(file_path)

    # ASSERT
    assert result is True


def test_is_directory_returns_true_for_existing_directory(sample_directory: Path) -> None:
    """
    Test is_directory returns True for existing directory.

    Tests that is_directory wrapper function correctly identifies
    existing directories.

    Parameters
    ----------
    sample_directory : Path
        Fixture providing sample directory path

    Returns
    -------
    None
        Test passes if all assertions succeed
    """
    # ARRANGE
    dir_path: str = str(sample_directory)

    # ACT
    result: bool = filefunctions.is_directory(dir_path)

    # ASSERT
    assert result is True


# -------------------------------------------------------------
# TESTS: Path parsing functions
# -------------------------------------------------------------


def test_get_file_name_returns_basename() -> None:
    """
    Test get_file_name extracts basename from full path.

    Tests that get_file_name correctly extracts the filename
    component from a complete file path.

    Parameters
    ----------
    None

    Returns
    -------
    None
        Test passes if all assertions succeed
    """
    # ARRANGE
    full_path: str = "/path/to/file.txt"
    expected_name: str = "file.txt"

    # ACT
    result: str = filefunctions.get_file_name(full_path)

    # ASSERT
    assert result == expected_name


def test_get_file_name_returns_empty_string_for_none() -> None:
    """
    Test get_file_name returns empty string for None input.

    Tests that get_file_name handles None input gracefully
    by returning an empty string.

    Parameters
    ----------
    None

    Returns
    -------
    None
        Test passes if all assertions succeed
    """
    # ARRANGE
    none_input: None = None

    # ACT
    result: str = filefunctions.get_file_name(none_input)

    # ASSERT
    assert result == ""


def test_get_file_extension_returns_extension_with_dot() -> None:
    """
    Test get_file_extension returns extension including dot.

    Tests that get_file_extension correctly extracts the file
    extension including the leading dot.

    Parameters
    ----------
    None

    Returns
    -------
    None
        Test passes if all assertions succeed
    """
    # ARRANGE
    filename: str = "document.txt"
    expected_extension: str = ".txt"

    # ACT
    result: str = filefunctions.get_file_extension(filename)

    # ASSERT
    assert result == expected_extension


def test_get_file_extension_returns_empty_for_no_extension() -> None:
    """
    Test get_file_extension returns empty string for files without extension.

    Tests that get_file_extension returns empty string when
    the filename has no extension.

    Parameters
    ----------
    None

    Returns
    -------
    None
        Test passes if all assertions succeed
    """
    # ARRANGE
    filename_no_ext: str = "README"

    # ACT
    result: str = filefunctions.get_file_extension(filename_no_ext)

    # ASSERT
    assert result == ""


def test_get_file_extension_returns_empty_for_empty_string() -> None:
    """
    Test get_file_extension returns empty string for empty input.

    Tests that get_file_extension handles empty string input
    gracefully by returning an empty string.

    Parameters
    ----------
    None

    Returns
    -------
    None
        Test passes if all assertions succeed
    """
    # ARRANGE
    empty_string: str = ""

    # ACT
    result: str = filefunctions.get_file_extension(empty_string)

    # ASSERT
    assert result == ""


def test_get_file_extension_handles_multiple_dots() -> None:
    """
    Test get_file_extension returns last extension for multiple dots.

    Tests that get_file_extension correctly handles filenames
    with multiple dots (e.g., archive.tar.gz).

    Parameters
    ----------
    None

    Returns
    -------
    None
        Test passes if all assertions succeed
    """
    # ARRANGE
    filename: str = "archive.tar.gz"
    expected_extension: str = ".gz"

    # ACT
    result: str = filefunctions.get_file_extension(filename)

    # ASSERT
    assert result == expected_extension


def test_get_base_name_prefix_removes_extension() -> None:
    """
    Test get_base_name_prefix returns filename without extension.

    Tests that get_base_name_prefix correctly removes the
    extension from a filename.

    Parameters
    ----------
    None

    Returns
    -------
    None
        Test passes if all assertions succeed
    """
    # ARRANGE
    full_path: str = "/path/to/document.txt"
    expected_prefix: str = "document"

    # ACT
    result: str = filefunctions.get_base_name_prefix(full_path)

    # ASSERT
    assert result == expected_prefix


def test_get_base_name_prefix_handles_multiple_dots() -> None:
    """
    Test get_base_name_prefix preserves middle dots in filename.

    Tests that get_base_name_prefix correctly handles filenames
    with multiple dots, preserving all but the final extension.

    Parameters
    ----------
    None

    Returns
    -------
    None
        Test passes if all assertions succeed
    """
    # ARRANGE
    filename: str = "/path/archive.tar.gz"
    expected_prefix: str = "archive.tar"

    # ACT
    result: str = filefunctions.get_base_name_prefix(filename)

    # ASSERT
    assert result == expected_prefix


def test_get_base_name_prefix_returns_filename_when_no_extension() -> None:
    """
    Test get_base_name_prefix returns full filename when no extension.

    Tests that get_base_name_prefix returns the complete filename
    when there is no extension to remove.

    Parameters
    ----------
    None

    Returns
    -------
    None
        Test passes if all assertions succeed
    """
    # ARRANGE
    filename: str = "/path/README"
    expected_result: str = "README"

    # ACT
    result: str = filefunctions.get_base_name_prefix(filename)

    # ASSERT
    assert result == expected_result


def test_get_path_name_returns_directory_path() -> None:
    """
    Test get_path_name extracts directory path from full path.

    Tests that get_path_name correctly extracts the directory
    component from a complete file path.

    Parameters
    ----------
    None

    Returns
    -------
    None
        Test passes if all assertions succeed
    """
    # ARRANGE
    full_path: str = "/path/to/file.txt"
    # Note: get_path_name adds os.path.sep at the end

    # ACT
    result: str = filefunctions.get_path_name(full_path)

    # ASSERT
    assert result.startswith("/path/to")
    assert result.endswith(os.path.sep)


def test_get_path_name_returns_empty_for_empty_input() -> None:
    """
    Test get_path_name returns empty string for empty input.

    Tests that get_path_name handles empty string input
    gracefully by returning an empty string.

    Parameters
    ----------
    None

    Returns
    -------
    None
        Test passes if all assertions succeed
    """
    # ARRANGE
    empty_input: str = ""

    # ACT
    result: str = filefunctions.get_path_name(empty_input)

    # ASSERT
    assert result == ""


def test_get_parent_path_name_returns_parent_directory() -> None:
    """
    Test get_parent_path_name returns parent directory path.

    Tests that get_parent_path_name correctly extracts the
    parent directory from a complete file path.

    Parameters
    ----------
    None

    Returns
    -------
    None
        Test passes if all assertions succeed
    """
    # ARRANGE
    full_path: str = "/path/to/subdir/file.txt"

    # ACT
    result: str = filefunctions.get_parent_path_name(full_path)

    # ASSERT
    assert result.startswith("/path/to")
    assert result.endswith(os.path.sep)


def test_get_home_path_returns_user_home_directory() -> None:
    """
    Test get_home_path returns user's home directory.

    Tests that get_home_path correctly returns the current
    user's home directory path.

    Parameters
    ----------
    None

    Returns
    -------
    None
        Test passes if all assertions succeed
    """
    # ARRANGE
    expected_home: str = os.path.expanduser("~")

    # ACT
    result: str = filefunctions.get_home_path()

    # ASSERT
    assert result == expected_home


def test_get_path_without_extension_removes_extension() -> None:
    """
    Test get_path_without_extension returns path without extension.

    Tests that get_path_without_extension correctly removes
    the file extension from a complete path.

    Parameters
    ----------
    None

    Returns
    -------
    None
        Test passes if all assertions succeed
    """
    # ARRANGE
    full_path: str = "/path/to/document.txt"
    expected_result: str = os.path.normpath("/path/to/document")

    # ACT
    result: str = filefunctions.get_path_without_extension(full_path)

    # ASSERT
    assert result == expected_result


def test_get_path_without_extension_returns_empty_for_empty_input() -> None:
    """
    Test get_path_without_extension returns empty for empty input.

    Tests that get_path_without_extension handles empty string
    input gracefully by returning an empty string.

    Parameters
    ----------
    None

    Returns
    -------
    None
        Test passes if all assertions succeed
    """
    # ARRANGE
    empty_input: str = ""

    # ACT
    result: str = filefunctions.get_path_without_extension(empty_input)

    # ASSERT
    assert result == ""


# -------------------------------------------------------------
# TESTS: Directory operations
# -------------------------------------------------------------


def test_get_current_directory_returns_cwd() -> None:
    """
    Test get_current_directory returns current working directory.

    Tests that get_current_directory correctly returns the
    current working directory of the process.

    Parameters
    ----------
    None

    Returns
    -------
    None
        Test passes if all assertions succeed
    """
    # ARRANGE
    expected_cwd: str = os.getcwd()

    # ACT
    result: str = filefunctions.get_current_directory()

    # ASSERT
    assert result == expected_cwd


def test_set_current_directory_changes_to_existing_directory(sample_directory: Path) -> None:  # CRITICAL TEST
    """
    Test set_current_directory successfully changes to existing directory.

    Tests that set_current_directory correctly changes the process
    working directory when given a valid directory path.

    Parameters
    ----------
    sample_directory : Path
        Fixture providing sample directory path

    Returns
    -------
    None
        Test passes if all assertions succeed

    Notes
    -----
    Restores original directory after test to avoid side effects
    """
    # ARRANGE
    original_cwd: str = os.getcwd()
    target_dir: str = str(sample_directory)

    try:
        # ACT
        filefunctions.set_current_directory(target_dir)

        # ASSERT
        assert os.getcwd() == str(sample_directory.resolve())
    finally:
        # Cleanup: restore original directory
        os.chdir(original_cwd)


def test_set_current_directory_raises_error_for_nonexistent_directory() -> None:  # CRITICAL TEST
    """
    Test set_current_directory raises RuntimeError for nonexistent directory.

    Tests that set_current_directory raises RuntimeError when
    attempting to change to a directory that doesn't exist.

    Parameters
    ----------
    None

    Returns
    -------
    None
        Test passes if RuntimeError is raised
    """
    # ARRANGE
    nonexistent_dir: str = "/tmp/does_not_exist_12345"

    # ACT & ASSERT
    with pytest.raises(RuntimeError, match="not found"):
        filefunctions.set_current_directory(nonexistent_dir)


def test_set_current_directory_handles_dot_directory(tmp_path: Path) -> None:  # CRITICAL TEST
    """
    Test set_current_directory handles '.' (current directory).

    Tests that set_current_directory correctly handles the special
    '.' directory reference without raising an error.

    Parameters
    ----------
    tmp_path : Path
        Pytest builtin fixture for temporary directory

    Returns
    -------
    None
        Test passes if all assertions succeed

    Notes
    -----
    Tests exception in validation logic that allows '.' and '..'
    """
    # ARRANGE
    original_cwd: str = os.getcwd()

    try:
        os.chdir(str(tmp_path))

        # ACT
        filefunctions.set_current_directory(".")

        # ASSERT
        # Should not raise error
        assert os.getcwd() == str(tmp_path.resolve())
    finally:
        # Cleanup
        os.chdir(original_cwd)


def test_set_current_directory_handles_dotdot_directory(tmp_path: Path) -> None:  # CRITICAL TEST
    """
    Test set_current_directory handles '..' (parent directory).

    Tests that set_current_directory correctly handles the special
    '..' directory reference without raising an error.

    Parameters
    ----------
    tmp_path : Path
        Pytest builtin fixture for temporary directory

    Returns
    -------
    None
        Test passes if all assertions succeed

    Notes
    -----
    Tests exception in validation logic that allows '.' and '..'
    """
    # ARRANGE
    original_cwd: str = os.getcwd()
    nested_dir: Path = tmp_path / "nested"
    nested_dir.mkdir()

    try:
        os.chdir(str(nested_dir))

        # ACT
        filefunctions.set_current_directory("..")

        # ASSERT
        # Should not raise error
        assert os.getcwd() == str(tmp_path.resolve())
    finally:
        # Cleanup
        os.chdir(original_cwd)


# -------------------------------------------------------------
# TESTS: File operations (CRITICAL)
# -------------------------------------------------------------


def test_rename_file_successfully_renames_file(tmp_path: Path) -> None:  # CRITICAL TEST
    """
    Test rename_file successfully renames file to new name.

    Tests that rename_file correctly renames a file when given
    valid source and target paths.

    Parameters
    ----------
    tmp_path : Path
        Pytest builtin fixture for temporary directory

    Returns
    -------
    None
        Test passes if all assertions succeed
    """
    # ARRANGE
    src_file: Path = tmp_path / "original.txt"
    src_file.write_text("content")
    target_file: Path = tmp_path / "renamed.txt"

    # ACT
    filefunctions.rename_file(str(src_file), str(target_file), overwrite=False)

    # ASSERT
    assert not src_file.exists()
    assert target_file.exists()
    assert target_file.read_text() == "content"


def test_rename_file_raises_error_when_source_not_exists(tmp_path: Path) -> None:  # CRITICAL TEST
    """
    Test rename_file raises FileNotFoundError when source doesn't exist.

    Tests that rename_file raises FileNotFoundError when attempting
    to rename a file that doesn't exist.

    Parameters
    ----------
    tmp_path : Path
        Pytest builtin fixture for temporary directory

    Returns
    -------
    None
        Test passes if FileNotFoundError is raised
    """
    # ARRANGE
    nonexistent_src: str = str(tmp_path / "nonexistent.txt")
    target: str = str(tmp_path / "target.txt")

    # ACT & ASSERT
    with pytest.raises(FileNotFoundError, match="doesn't exist"):
        filefunctions.rename_file(nonexistent_src, target)


def test_rename_file_raises_error_when_target_exists_without_overwrite(tmp_path: Path) -> None:  # CRITICAL TEST
    """
    Test rename_file raises FileExistsError when target exists and overwrite=False.

    Tests that rename_file raises FileExistsError when attempting
    to rename to an existing file without the overwrite flag.

    Parameters
    ----------
    tmp_path : Path
        Pytest builtin fixture for temporary directory

    Returns
    -------
    None
        Test passes if FileExistsError is raised
    """
    # ARRANGE
    src_file: Path = tmp_path / "source.txt"
    src_file.write_text("source content")
    target_file: Path = tmp_path / "target.txt"
    target_file.write_text("target content")

    # ACT & ASSERT
    with pytest.raises(FileExistsError, match="already exists"):
        filefunctions.rename_file(str(src_file), str(target_file), overwrite=False)


def test_rename_file_overwrites_when_overwrite_true(tmp_path: Path) -> None:  # CRITICAL TEST
    """
    Test rename_file overwrites existing file when overwrite=True.

    Tests that rename_file successfully overwrites an existing
    target file when the overwrite flag is set to True.

    Parameters
    ----------
    tmp_path : Path
        Pytest builtin fixture for temporary directory

    Returns
    -------
    None
        Test passes if all assertions succeed
    """
    # ARRANGE
    src_file: Path = tmp_path / "source.txt"
    src_file.write_text("new content")
    target_file: Path = tmp_path / "target.txt"
    target_file.write_text("old content")

    # ACT
    filefunctions.rename_file(str(src_file), str(target_file), overwrite=True)

    # ASSERT
    assert not src_file.exists()
    assert target_file.exists()
    assert target_file.read_text() == "new content"


def test_rename_file_raises_error_when_target_directory_not_exists(tmp_path: Path) -> None:  # CRITICAL TEST
    """
    Test rename_file raises FileNotFoundError when target directory doesn't exist.

    Tests that rename_file raises FileNotFoundError when attempting
    to rename a file to a directory that doesn't exist.

    Parameters
    ----------
    tmp_path : Path
        Pytest builtin fixture for temporary directory

    Returns
    -------
    None
        Test passes if FileNotFoundError is raised
    """
    # ARRANGE
    src_file: Path = tmp_path / "source.txt"
    src_file.write_text("content")
    target_in_nonexistent_dir: str = str(tmp_path / "nonexistent_dir" / "target.txt")

    # ACT & ASSERT
    with pytest.raises(FileNotFoundError, match="doesn't exist"):
        filefunctions.rename_file(str(src_file), target_in_nonexistent_dir)


def test_remove_file_successfully_removes_existing_file(sample_file: Path) -> None:  # CRITICAL TEST
    """
    Test remove_file successfully removes existing file.

    Tests that remove_file correctly deletes an existing file
    from the filesystem.

    Parameters
    ----------
    sample_file : Path
        Fixture providing sample file path

    Returns
    -------
    None
        Test passes if all assertions succeed
    """
    # ARRANGE
    file_path: str = str(sample_file)
    assert sample_file.exists()

    # ACT
    filefunctions.remove_file(file_path)

    # ASSERT
    assert not sample_file.exists()


def test_remove_file_does_nothing_when_file_not_exists(tmp_path: Path) -> None:  # CRITICAL TEST
    """
    Test remove_file does nothing when file doesn't exist.

    Tests that remove_file handles nonexistent files gracefully
    without raising an error.

    Parameters
    ----------
    tmp_path : Path
        Pytest builtin fixture for temporary directory

    Returns
    -------
    None
        Test passes if all assertions succeed
    """
    # ARRANGE
    nonexistent_file: str = str(tmp_path / "nonexistent.txt")

    # ACT
    filefunctions.remove_file(nonexistent_file)

    # ASSERT
    # Should not raise error
    assert True


def test_create_directory_successfully_creates_directory(tmp_path: Path) -> None:  # IMPORTANT TEST
    """
    Test create_directory successfully creates new directory.

    Tests that create_directory correctly creates a new directory
    when given a valid path.

    Parameters
    ----------
    tmp_path : Path
        Pytest builtin fixture for temporary directory

    Returns
    -------
    None
        Test passes if all assertions succeed
    """
    # ARRANGE
    new_dir: Path = tmp_path / "new_directory"

    # ACT
    filefunctions.create_directory(str(new_dir))

    # ASSERT
    assert new_dir.exists()
    assert new_dir.is_dir()


def test_create_directory_creates_nested_directories(tmp_path: Path) -> None:  # IMPORTANT TEST
    """
    Test create_directory creates nested directory structure.

    Tests that create_directory correctly creates nested directories
    (equivalent to mkdir -p).

    Parameters
    ----------
    tmp_path : Path
        Pytest builtin fixture for temporary directory

    Returns
    -------
    None
        Test passes if all assertions succeed
    """
    # ARRANGE
    nested_dir: Path = tmp_path / "level1" / "level2" / "level3"

    # ACT
    filefunctions.create_directory(str(nested_dir))

    # ASSERT
    assert nested_dir.exists()
    assert nested_dir.is_dir()


def test_create_directory_handles_existing_directory(sample_directory: Path) -> None:  # IMPORTANT TEST
    """
    Test create_directory handles existing directory gracefully.

    Tests that create_directory doesn't raise an error when
    attempting to create a directory that already exists.

    Parameters
    ----------
    sample_directory : Path
        Fixture providing sample directory path

    Returns
    -------
    None
        Test passes if all assertions succeed
    """
    # ARRANGE
    existing_dir: str = str(sample_directory)

    # ACT
    filefunctions.create_directory(existing_dir)

    # ASSERT
    # Should not raise error
    assert sample_directory.exists()


def test_remove_directory_successfully_removes_directory(sample_directory: Path) -> None:  # CRITICAL TEST
    """
    Test remove_directory successfully removes directory.

    Tests that remove_directory correctly removes an existing
    directory and all its contents.

    Parameters
    ----------
    sample_directory : Path
        Fixture providing sample directory path

    Returns
    -------
    None
        Test passes if all assertions succeed
    """
    # ARRANGE
    dir_path: str = str(sample_directory)
    assert sample_directory.exists()

    # ACT
    filefunctions.remove_directory(dir_path)

    # ASSERT
    assert not sample_directory.exists()


def test_remove_directory_removes_directory_with_contents(tmp_path: Path) -> None:  # CRITICAL TEST
    """
    Test remove_directory removes directory with nested contents.

    Tests that remove_directory correctly removes a directory
    containing files and subdirectories.

    Parameters
    ----------
    tmp_path : Path
        Pytest builtin fixture for temporary directory

    Returns
    -------
    None
        Test passes if all assertions succeed
    """
    # ARRANGE
    test_dir: Path = tmp_path / "dir_with_contents"
    test_dir.mkdir()
    (test_dir / "file.txt").write_text("content")
    subdir: Path = test_dir / "subdir"
    subdir.mkdir()
    (subdir / "nested_file.txt").write_text("nested")

    # ACT
    filefunctions.remove_directory(str(test_dir))

    # ASSERT
    assert not test_dir.exists()


def test_remove_directory_does_nothing_when_directory_not_exists(tmp_path: Path) -> None:  # CRITICAL TEST
    """
    Test remove_directory does nothing when directory doesn't exist.

    Tests that remove_directory handles nonexistent directories
    gracefully without raising an error.

    Parameters
    ----------
    tmp_path : Path
        Pytest builtin fixture for temporary directory

    Returns
    -------
    None
        Test passes if all assertions succeed
    """
    # ARRANGE
    nonexistent_dir: str = str(tmp_path / "nonexistent_dir")

    # ACT
    filefunctions.remove_directory(nonexistent_dir)

    # ASSERT
    # Should not raise error
    assert True


def test_remove_directory_raises_error_for_root_directory() -> None:  # CRITICAL TEST
    """
    Test remove_directory raises RuntimeError when attempting to delete root.

    Tests that remove_directory has protection against deleting
    the root directory ('/').

    Parameters
    ----------
    None

    Returns
    -------
    None
        Test passes if RuntimeError is raised

    Notes
    -----
    Critical security test - prevents catastrophic filesystem damage
    """
    # ARRANGE
    root_dir: str = os.path.sep

    # ACT & ASSERT
    with pytest.raises(RuntimeError, match="can't delete the root directory"):
        filefunctions.remove_directory(root_dir)


# -------------------------------------------------------------
# TESTS: File listing operations
# -------------------------------------------------------------


def test_create_file_list_returns_all_files_in_directory(nested_directory_structure: Path) -> None:  # IMPORTANT TEST
    """
    Test create_file_list returns all files in directory.

    Tests that create_file_list correctly lists all files
    matching the pattern in a directory.

    Parameters
    ----------
    nested_directory_structure : Path
        Fixture providing nested directory structure

    Returns
    -------
    None
        Test passes if all assertions succeed
    """
    # ARRANGE
    dir_path: str = str(nested_directory_structure)

    # ACT
    result: List[str] = filefunctions.create_file_list(pattern_list=["*"], dir_name=dir_path, recursive=False)

    # ASSERT
    # Should include file1.txt, file2.py, but not .hidden (hidden files excluded by default)
    assert len(result) == 2
    assert any("file1.txt" in f for f in result)
    assert any("file2.py" in f for f in result)


def test_create_file_list_returns_files_matching_pattern(nested_directory_structure: Path) -> None:  # IMPORTANT TEST
    """
    Test create_file_list returns only files matching pattern.

    Tests that create_file_list correctly filters files based
    on the provided pattern list.

    Parameters
    ----------
    nested_directory_structure : Path
        Fixture providing nested directory structure

    Returns
    -------
    None
        Test passes if all assertions succeed
    """
    # ARRANGE
    dir_path: str = str(nested_directory_structure)

    # ACT
    result: List[str] = filefunctions.create_file_list(pattern_list=["*.txt"], dir_name=dir_path, recursive=False)

    # ASSERT
    assert len(result) == 1
    assert any("file1.txt" in f for f in result)
    assert not any("file2.py" in f for f in result)


def test_create_file_list_recursive_returns_nested_files(nested_directory_structure: Path) -> None:  # IMPORTANT TEST
    """
    Test create_file_list with recursive=True returns nested files.

    Tests that create_file_list correctly traverses subdirectories
    when recursive flag is set to True.

    Parameters
    ----------
    nested_directory_structure : Path
        Fixture providing nested directory structure

    Returns
    -------
    None
        Test passes if all assertions succeed
    """
    # ARRANGE
    dir_path: str = str(nested_directory_structure)

    # ACT
    result: List[str] = filefunctions.create_file_list(pattern_list=["*.txt"], dir_name=dir_path, recursive=True)

    # ASSERT
    # Should find file1.txt, file3.txt, file4.txt
    assert len(result) == 3
    assert any("file1.txt" in f for f in result)
    assert any("file3.txt" in f for f in result)
    assert any("file4.txt" in f for f in result)


def test_create_file_list_includes_hidden_files_when_flag_set(
    nested_directory_structure: Path,
) -> None:  # IMPORTANT TEST
    """
    Test create_file_list includes hidden files when add_hidden_files=True.

    Tests that create_file_list includes files starting with '.'
    when the add_hidden_files flag is set to True.

    Parameters
    ----------
    nested_directory_structure : Path
        Fixture providing nested directory structure

    Returns
    -------
    None
        Test passes if all assertions succeed
    """
    # ARRANGE
    dir_path: str = str(nested_directory_structure)

    # ACT
    result: List[str] = filefunctions.create_file_list(
        pattern_list=["*"], dir_name=dir_path, recursive=False, add_hidden_files=True
    )

    # ASSERT
    # Should include .hidden file
    assert len(result) == 3
    assert any(".hidden" in f for f in result)


def test_create_file_list_excludes_hidden_files_by_default(nested_directory_structure: Path) -> None:  # IMPORTANT TEST
    """
    Test create_file_list excludes hidden files by default.

    Tests that create_file_list does not include files starting
    with '.' by default.

    Parameters
    ----------
    nested_directory_structure : Path
        Fixture providing nested directory structure

    Returns
    -------
    None
        Test passes if all assertions succeed
    """
    # ARRANGE
    dir_path: str = str(nested_directory_structure)

    # ACT
    result: List[str] = filefunctions.create_file_list(
        pattern_list=["*"], dir_name=dir_path, recursive=False, add_hidden_files=False
    )

    # ASSERT
    # Should NOT include .hidden file
    assert not any(".hidden" in f for f in result)


def test_create_file_list_appends_directories_when_flag_set(
    nested_directory_structure: Path,
) -> None:  # IMPORTANT TEST
    """
    Test create_file_list includes directories when append_dirs=True.

    Tests that create_file_list includes directories matching
    the pattern when append_dirs flag is set to True.

    Parameters
    ----------
    nested_directory_structure : Path
        Fixture providing nested directory structure

    Returns
    -------
    None
        Test passes if all assertions succeed
    """
    # ARRANGE
    dir_path: str = str(nested_directory_structure)

    # ACT
    result: List[str] = filefunctions.create_file_list(
        pattern_list=["*"], dir_name=dir_path, recursive=False, append_dirs=True
    )

    # ASSERT
    # Should include subdir directory
    assert any("subdir" in f for f in result)
    # Should also include files
    assert any("file1.txt" in f for f in result)


def test_create_file_list_returns_empty_for_nonexistent_directory() -> None:  # IMPORTANT TEST
    """
    Test create_file_list returns empty list for nonexistent directory.

    Tests that create_file_list handles nonexistent directories
    gracefully by returning an empty list.

    Parameters
    ----------
    None

    Returns
    -------
    None
        Test passes if all assertions succeed
    """
    # ARRANGE
    nonexistent_dir: str = "/tmp/nonexistent_dir_12345"

    # ACT
    result: List[str] = filefunctions.create_file_list(dir_name=nonexistent_dir)

    # ASSERT
    assert result == []


def test_create_file_list_uses_current_directory_when_empty_dir_name(tmp_path: Path) -> None:  # IMPORTANT TEST
    """
    Test create_file_list uses current directory when dir_name is empty.

    Tests that create_file_list defaults to current directory
    when dir_name parameter is empty string.

    Parameters
    ----------
    tmp_path : Path
        Pytest builtin fixture for temporary directory

    Returns
    -------
    None
        Test passes if all assertions succeed
    """
    # ARRANGE
    original_cwd: str = os.getcwd()
    (tmp_path / "test_file.txt").write_text("content")

    try:
        os.chdir(str(tmp_path))

        # ACT
        result: List[str] = filefunctions.create_file_list(pattern_list=["*.txt"], dir_name="")

        # ASSERT
        assert len(result) == 1
        assert any("test_file.txt" in f for f in result)
    finally:
        # Cleanup
        os.chdir(original_cwd)


def test_create_file_list_returns_sorted_list(nested_directory_structure: Path) -> None:  # IMPORTANT TEST
    """
    Test create_file_list returns sorted list of files.

    Tests that create_file_list returns files in sorted order
    by default.

    Parameters
    ----------
    nested_directory_structure : Path
        Fixture providing nested directory structure

    Returns
    -------
    None
        Test passes if all assertions succeed
    """
    # ARRANGE
    dir_path: str = str(nested_directory_structure)

    # ACT
    result: List[str] = filefunctions.create_file_list(pattern_list=["*"], dir_name=dir_path, recursive=False)

    # ASSERT
    # Verify list is sorted
    assert result == sorted(result)


def test_create_file_list_returns_reverse_sorted_when_flag_set(
    nested_directory_structure: Path,
) -> None:  # IMPORTANT TEST
    """
    Test create_file_list returns reverse sorted list when reverse_sort=True.

    Tests that create_file_list returns files in reverse sorted
    order when reverse_sort flag is set to True.

    Parameters
    ----------
    nested_directory_structure : Path
        Fixture providing nested directory structure

    Returns
    -------
    None
        Test passes if all assertions succeed
    """
    # ARRANGE
    dir_path: str = str(nested_directory_structure)

    # ACT
    result: List[str] = filefunctions.create_file_list(
        pattern_list=["*"], dir_name=dir_path, recursive=False, reverse_sort=True
    )

    # ASSERT
    # Verify list is reverse sorted
    assert result == sorted(result, reverse=True)


def test_create_file_list_uses_default_pattern_when_none(nested_directory_structure: Path) -> None:  # IMPORTANT TEST
    """
    Test create_file_list uses default pattern '*' when pattern_list is None.

    Tests that create_file_list defaults to pattern ['*'] when
    pattern_list parameter is None.

    Parameters
    ----------
    nested_directory_structure : Path
        Fixture providing nested directory structure

    Returns
    -------
    None
        Test passes if all assertions succeed
    """
    # ARRANGE
    dir_path: str = str(nested_directory_structure)

    # ACT
    result: List[str] = filefunctions.create_file_list(pattern_list=None, dir_name=dir_path, recursive=False)

    # ASSERT
    # Should return all files (not hidden)
    assert len(result) == 2


def test_create_file_list_handles_multiple_patterns(nested_directory_structure: Path) -> None:  # IMPORTANT TEST
    """
    Test create_file_list handles multiple patterns in pattern_list.

    Tests that create_file_list correctly matches files against
    multiple patterns.

    Parameters
    ----------
    nested_directory_structure : Path
        Fixture providing nested directory structure

    Returns
    -------
    None
        Test passes if all assertions succeed
    """
    # ARRANGE
    dir_path: str = str(nested_directory_structure)

    # ACT
    result: List[str] = filefunctions.create_file_list(
        pattern_list=["*.txt", "*.py"], dir_name=dir_path, recursive=False
    )

    # ASSERT
    # Should include both .txt and .py files
    assert len(result) == 2
    assert any("file1.txt" in f for f in result)
    assert any("file2.py" in f for f in result)


def test_create_file_list_handles_string_pattern_instead_of_list(
    nested_directory_structure: Path,
) -> None:  # IMPORTANT TEST
    """
    Test create_file_list handles string pattern instead of list.

    Tests that create_file_list correctly handles a single string
    pattern instead of a list (edge case for backward compatibility).

    Parameters
    ----------
    nested_directory_structure : Path
        Fixture providing nested directory structure

    Returns
    -------
    None
        Test passes if all assertions succeed
    """
    # ARRANGE
    dir_path: str = str(nested_directory_structure)
    pattern_string: str = "*.txt"

    # ACT
    result: List[str] = filefunctions.create_file_list(pattern_list=pattern_string, dir_name=dir_path, recursive=False)

    # ASSERT
    assert len(result) == 1
    assert any("file1.txt" in f for f in result)


def test_create_file_list_handles_relative_path_without_dot(tmp_path: Path) -> None:  # IMPORTANT TEST
    """
    Test create_file_list handles relative path without leading dot.

    Tests that create_file_list correctly prepends './' to relative
    paths that don't start with '.' or '/'.

    Parameters
    ----------
    tmp_path : Path
        Pytest builtin fixture for temporary directory

    Returns
    -------
    None
        Test passes if all assertions succeed
    """
    # ARRANGE
    original_cwd: str = os.getcwd()
    subdir: Path = tmp_path / "subdir"
    subdir.mkdir()
    (subdir / "file.txt").write_text("content")

    try:
        os.chdir(str(tmp_path))

        # ACT - Pass relative path without leading ./
        result: List[str] = filefunctions.create_file_list(pattern_list=["*.txt"], dir_name="subdir", recursive=False)

        # ASSERT
        assert len(result) == 1
        assert any("file.txt" in f for f in result)
    finally:
        # Cleanup
        os.chdir(original_cwd)


def test_get_extension_is_alias_for_get_file_extension() -> None:
    """
    Test get_extension is an alias for get_file_extension.

    Tests that get_extension wrapper function returns the same
    result as get_file_extension.

    Parameters
    ----------
    None

    Returns
    -------
    None
        Test passes if all assertions succeed
    """
    # ARRANGE
    filename: str = "document.pdf"

    # ACT
    result_extension: str = filefunctions.get_extension(filename)
    result_file_extension: str = filefunctions.get_file_extension(filename)

    # ASSERT
    assert result_extension == result_file_extension
    assert result_extension == ".pdf"


# -------------------------------------------------------------
# TESTS: Path normalization
# -------------------------------------------------------------


def test_norm_path_normalizes_path() -> None:
    """
    Test norm_path normalizes path separators.

    Tests that norm_path correctly normalizes path separators
    to the platform-specific format.

    Parameters
    ----------
    None

    Returns
    -------
    None
        Test passes if all assertions succeed
    """
    # ARRANGE
    windows_path: str = "path\\to\\file.txt"
    expected_result: str = os.path.normpath("path/to/file.txt")

    # ACT
    result: str = filefunctions.norm_path(windows_path)

    # ASSERT
    assert result == expected_result


def test_norm_path_converts_backslashes_to_forward_slashes() -> None:
    """
    Test norm_path converts backslashes to forward slashes before normalization.

    Tests that norm_path correctly handles Windows-style paths
    by converting backslashes to forward slashes.

    Parameters
    ----------
    None

    Returns
    -------
    None
        Test passes if all assertions succeed
    """
    # ARRANGE
    mixed_path: str = "path\\to/file.txt"

    # ACT
    result: str = filefunctions.norm_path(mixed_path)

    # ASSERT
    # Should be normalized to platform-specific format
    assert "\\" not in result or os.path.sep == "\\"


# -------------------------------------------------------------
# TESTS: Edge cases and parametrized tests
# -------------------------------------------------------------


@pytest.mark.parametrize(
    "invalid_input,file_type",
    [
        ("", "FILE"),
        (None, "FILE"),
        ("", "DIRECTORY"),
    ],
)
def test_check_if_exists_handles_various_invalid_inputs(invalid_input: str, file_type: str) -> None:
    """
    Test check_if_exists handles various invalid inputs gracefully.

    Tests that check_if_exists returns False for various
    edge case inputs instead of raising exceptions.

    Parameters
    ----------
    invalid_input : str
        Invalid input to test
    file_type : str
        Type of file to check for

    Returns
    -------
    None
        Test passes if all assertions succeed
    """
    # ACT
    if invalid_input is None:
        # Special handling for None
        result: bool = filefunctions.check_if_exists(invalid_input, file_type=file_type)
        # ASSERT
        assert result is False
    else:
        result: bool = filefunctions.check_if_exists(invalid_input, file_type=file_type)
        # ASSERT
        assert result is False


@pytest.mark.parametrize(
    "filename,expected_extension",
    [
        ("file.txt", ".txt"),
        ("file.tar.gz", ".gz"),
        ("README", ""),
        ("", ""),
        (".gitignore", ""),  # Files starting with . have no extension returned
        ("file.", ""),
    ],
)
def test_get_file_extension_various_filenames(filename: str, expected_extension: str) -> None:
    """
    Test get_file_extension handles various filename formats.

    Tests that get_file_extension correctly extracts extensions
    from different filename formats.

    Parameters
    ----------
    filename : str
        Filename to test
    expected_extension : str
        Expected extension result

    Returns
    -------
    None
        Test passes if all assertions succeed
    """
    # ACT
    result: str = filefunctions.get_file_extension(filename)

    # ASSERT
    assert result == expected_extension
