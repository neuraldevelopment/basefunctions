"""
=============================================================================

  Licensed Materials, Property of Ralph Vogl, Munich

  Project : basefunctions

  Copyright (c) by Ralph Vogl

  All rights reserved.

  Description:

  Tests for filefunctions module

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import os
import shutil
import pytest
import basefunctions as bf

# -------------------------------------------------------------
# FUNCTION DEFINITIONS
# -------------------------------------------------------------


def test_check_if_exists_file(tmp_path):
    file = tmp_path / "testfile.txt"
    file.write_text("hello")
    assert bf.check_if_exists(str(file))
    assert not bf.check_if_exists(str(tmp_path / "nofile.txt"))


def test_check_if_exists_directory(tmp_path):
    assert bf.check_if_exists(str(tmp_path), file_type="DIRECTORY")
    assert not bf.check_if_exists(str(tmp_path / "missing_dir"), file_type="DIRECTORY")


def test_check_if_file_exists(tmp_path):
    file = tmp_path / "file.txt"
    file.write_text("data")
    assert bf.check_if_file_exists(str(file))


def test_check_if_dir_exists(tmp_path):
    assert bf.check_if_dir_exists(str(tmp_path))


def test_is_file(tmp_path):
    file = tmp_path / "myfile.txt"
    file.write_text("123")
    assert bf.is_file(str(file))


def test_is_directory(tmp_path):
    assert bf.is_directory(str(tmp_path))


def test_get_file_name():
    assert bf.get_file_name("/path/to/file.txt") == "file.txt"


def test_get_file_extension():
    assert bf.get_file_extension("/path/to/file.txt") == ".txt"
    assert bf.get_file_extension("/path/to/file") == ""


def test_get_extension():
    assert bf.get_extension("test.tar.gz") == ".gz"


def test_get_base_name():
    assert bf.get_base_name("/any/path/file.dat") == "file.dat"


def test_get_base_name_prefix():
    assert bf.get_base_name_prefix("folder/sub/file.tar.gz") == "file.tar"
    assert bf.get_base_name_prefix("file") == "file"


def test_get_path_name():
    path_name = bf.get_path_name("/some/path/file.txt")
    assert path_name.endswith("/path/") or path_name.endswith("\\path\\")


def test_get_parent_path_name():
    parent_path = bf.get_parent_path_name("/home/user/folder/file.txt")
    assert parent_path.endswith("/user/") or parent_path.endswith("\\user\\")


def test_get_home_path():
    home = bf.get_home_path()
    assert os.path.isdir(home)


def test_get_path_without_extension():
    assert bf.get_path_without_extension("/path/to/file.txt").endswith(
        os.path.normpath("/path/to/file")
    )


def test_get_current_directory():
    current = bf.get_current_directory()
    assert os.path.isdir(current)


def test_set_current_directory(tmp_path):
    old_dir = os.getcwd()
    bf.set_current_directory(str(tmp_path))
    assert os.getcwd() == str(tmp_path)
    os.chdir(old_dir)


def test_rename_file(tmp_path):
    src = tmp_path / "source.txt"
    src.write_text("content")
    target = tmp_path / "renamed.txt"
    bf.rename_file(str(src), str(target))
    assert target.exists()
    assert not src.exists()


def test_remove_file(tmp_path):
    file = tmp_path / "toremove.txt"
    file.write_text("bye")
    bf.remove_file(str(file))
    assert not file.exists()


def test_create_directory(tmp_path):
    new_dir = tmp_path / "newdir"
    bf.create_directory(str(new_dir))
    assert new_dir.exists()


def test_remove_directory(tmp_path):
    dir_to_remove = tmp_path / "dir"
    dir_to_remove.mkdir()
    bf.remove_directory(str(dir_to_remove))
    assert not dir_to_remove.exists()


def test_create_file_list_basic(tmp_path):
    (tmp_path / "file1.txt").write_text("A")
    (tmp_path / "file2.log").write_text("B")
    result = bf.create_file_list(["*.txt"], str(tmp_path))
    assert len(result) == 1
    assert result[0].endswith("file1.txt")


def test_create_file_list_recursive(tmp_path):
    subdir = tmp_path / "sub"
    subdir.mkdir()
    (subdir / "file.txt").write_text("Sub")
    result = bf.create_file_list(["*.txt"], str(tmp_path), recursive=True)
    assert any("file.txt" in file for file in result)


def test_create_file_list_append_dirs(tmp_path):
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    result = bf.create_file_list(["*"], str(tmp_path), append_dirs=True)
    assert any(str(subdir) == file for file in result)


def test_create_file_list_hidden(tmp_path):
    hidden = tmp_path / ".hiddenfile"
    hidden.write_text("Hidden")
    result = bf.create_file_list(["*"], str(tmp_path), add_hidden_files=True)
    assert any(".hiddenfile" in file for file in result)


def test_norm_path():
    assert bf.norm_path("some\\weird\\path") == os.path.normpath("some/weird/path")


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
# CLASS DEFINITIONS
# -------------------------------------------------------------
