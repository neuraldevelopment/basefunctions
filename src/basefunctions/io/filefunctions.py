"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich

  Project : basefunctions

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  File and directory operations with cross-platform support

  Log:
  v1.0 : Initial implementation
  v1.1 : Added deployment/development path detection
  v1.2 : Removed basefunctions special handling, uses bootstrap config
=============================================================================
"""

from __future__ import annotations

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import fnmatch
import os
import shutil
from basefunctions.utils.logging import get_logger, get_logger

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# LOGGING INITIALIZE
# -------------------------------------------------------------
# Enable logging for this module
get_logger(__name__)

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


def check_if_exists(file_name: str, file_type: str = "FILE") -> bool:
    """
    Check if a specific file or directory exists.

    Parameters
    ----------
    file_name : str
        Name of the file or directory to be checked.
    file_type : str, optional
        Type of file or directory to be checked, by default "FILE".

    Returns
    -------
    bool
        True if the file or directory exists, False otherwise.

    Raises
    ------
    ValueError
        If an unknown file_type is passed.
    """
    if not file_name:
        return False
    path_exists = os.path.exists(file_name)
    if file_type == "FILE":
        return path_exists and os.path.isfile(file_name)
    if file_type == "DIRECTORY":
        return path_exists and os.path.isdir(file_name)
    raise ValueError(f"Unknown file_type: {file_type}")


def check_if_file_exists(file_name: str) -> bool:
    """
    Check if a file exists.

    Parameters
    ----------
    file_name : str
        The name of the file to be checked.

    Returns
    -------
    bool
        True if the file exists, False otherwise.
    """
    return check_if_exists(file_name, file_type="FILE")


def check_if_dir_exists(dir_name: str) -> bool:
    """
    Check if directory exists.

    Parameters
    ----------
    dir_name : str
        Directory name to be checked.

    Returns
    -------
    bool
        True if directory exists, False otherwise.
    """
    return check_if_exists(dir_name, file_type="DIRECTORY")


def is_file(file_name: str) -> bool:
    """
    Check if file_name is a regular file.

    Parameters
    ----------
    file_name : str
        Name of the file to be checked.

    Returns
    -------
    bool
        True if the file exists and is a regular file.
    """
    return check_if_file_exists(file_name)


def is_directory(dir_name: str) -> bool:
    """
    Check if `dir_name` is a regular directory.

    Parameters
    ----------
    dir_name : str
        Name of the directory to be checked.

    Returns
    -------
    bool
        True if the directory exists and is a directory, False otherwise.
    """
    return check_if_dir_exists(dir_name)


def get_file_name(path_file_name: str) -> str:
    """
    Get the file name part from a complete file path.

    Parameters
    ----------
    path_file_name : str
        The complete file path.

    Returns
    -------
    str
        The file name part of the file path.
    """
    return os.path.basename(path_file_name) if path_file_name is not None else ""


def get_file_extension(path_file_name: str) -> str:
    """
    Get the file extension from a complete file name.

    Parameters
    ----------
    path_file_name : str
        The path file name to get the file extension from.

    Returns
    -------
    str
        The file extension of the file name.
    """
    if not path_file_name:
        return ""
    _, extension = os.path.splitext(path_file_name)
    return extension if extension and extension != "." else ""


def get_extension(path_file_name: str) -> str:
    """
    Get the extension from a complete file name.

    Parameters
    ----------
    path_file_name : str
        The path file name to get the extension from.

    Returns
    -------
    str
        The extension of the file name.
    """
    return get_file_extension(path_file_name)


def get_base_name(path_file_name: str) -> str:
    """
    Get the base name part from a complete file name.

    Parameters
    ----------
    path_file_name : str
        The path file name to get information from.

    Returns
    -------
    str
        The base name of the file.
    """
    return get_file_name(path_file_name)


def get_base_name_prefix(path_file_name: str) -> str:
    """
    Get the basename prefix from a complete file name.

    Parameters
    ----------
    path_file_name : str
        The path file name to get information from.

    Returns
    -------
    str
        The basename prefix of the file name.
    """
    base_name = get_base_name(path_file_name)
    parts = base_name.split(".")
    return ".".join(parts[:-1]) if len(parts) > 1 else base_name


def get_path_name(path_file_name: str) -> str:
    """
    Get the path name from a complete file name.

    Parameters
    ----------
    path_file_name : str
        The path file name to get information from.

    Returns
    -------
    str
        The path name of the file name.
    """
    return os.path.dirname(os.path.normpath(path_file_name)) + os.path.sep if path_file_name else ""


def get_parent_path_name(path_file_name: str) -> str:
    """
    Get the parent path name from a complete file name.

    Parameters
    ----------
    path_file_name : str
        The path file name to get information from.

    Returns
    -------
    str
        The parent path name.
    """
    return os.path.dirname(os.path.dirname(os.path.normpath(path_file_name))) + os.path.sep if path_file_name else ""


def get_home_path() -> str:
    """
    Get the home path of the user.

    Returns
    -------
    str
        The home path of the user.
    """
    return os.path.expanduser("~")


def get_path_without_extension(path_file_name: str) -> str:
    """
    Get the full path of a file without its extension.

    Parameters
    ----------
    path_file_name : str
        The path file name to get information from.

    Returns
    -------
    str
        The path without the extension.
    """
    return os.path.splitext(os.path.normpath(path_file_name))[0] if path_file_name else ""


def get_current_directory() -> str:
    """
    Get the current directory of the process.

    Returns
    -------
    str
        The name of the current directory.
    """
    return os.getcwd()


def set_current_directory(directory_name: str) -> None:
    """
    Set the current directory of the process.

    Parameters
    ----------
    directory_name : str
        The name of the directory to set as the current directory.

    Raises
    ------
    RuntimeError
        If the specified directory does not exist.
    """
    if directory_name not in [".", ".."] and not check_if_dir_exists(directory_name):
        raise RuntimeError(f"Directory '{directory_name}' not found.")
    os.chdir(directory_name)


def rename_file(src: str, target: str, overwrite: bool = False) -> None:
    """
    Rename a file.

    Parameters
    ----------
    src : str
        The source file name or path.
    target : str
        The target file name or path.
    overwrite : bool, optional
        Whether to overwrite the target if it exists. Default is False.

    Raises
    ------
    FileNotFoundError
        If the source file or target directory does not exist.
    FileExistsError
        If the target file exists and overwrite is False.
    """
    dir_name = get_path_name(target)
    if not dir_name or not check_if_dir_exists(dir_name):
        raise FileNotFoundError(f"{dir_name} doesn't exist, can't rename file")
    if not overwrite and check_if_file_exists(target):
        raise FileExistsError(f"{target} already exists and overwrite flag set False")
    if not check_if_file_exists(src):
        raise FileNotFoundError(f"{src} doesn't exist")
    os.rename(src, target)
    get_logger(__name__).info("renamed file from %s to %s", src, target)


def remove_file(file_name: str) -> None:
    """
    Remove a file.

    Parameters
    ----------
    file_name : str
        The name of the file to remove.

    Raises
    ------
    FileNotFoundError
        If the specified file does not exist.
    """
    if check_if_file_exists(file_name):
        os.remove(file_name)
        get_logger(__name__).info("removed file %s", file_name)


def create_directory(dir_name: str) -> None:
    """
    Create a directory recursively.

    Parameters
    ----------
    dir_name : str
        Directory path to create.

    Raises
    ------
    OSError
        If there is an error while creating the directory.
    """
    os.makedirs(dir_name, exist_ok=True)
    get_logger(__name__).info("created directory %s", dir_name)


def remove_directory(dir_name: str) -> None:
    """
    Remove a directory and all its contents.

    Parameters
    ----------
    dir_name : str
        The name of the directory to be removed.

    Raises
    ------
    RuntimeError
        If attempting to remove the root directory ('/').
    """
    if not check_if_dir_exists(dir_name):
        return
    if os.path.abspath(dir_name) == os.path.sep:
        raise RuntimeError("can't delete the root directory ('/')")
    shutil.rmtree(dir_name)
    get_logger(__name__).info("Removed directory %s", dir_name)


def create_file_list(
    pattern_list: list[str] | None = None,
    dir_name: str = "",
    recursive: bool = False,
    append_dirs: bool = False,
    add_hidden_files: bool = False,
    reverse_sort: bool = False,
) -> list[str]:
    """
    Create a file list from a given directory.

    Parameters
    ----------
    pattern_list : list[str], optional
        Pattern elements to search for. Default is ["*"].
    dir_name : str, optional
        Directory to search. Default is current directory.
    recursive : bool, optional
        Recursive search. Default is False.
    append_dirs : bool, optional
        Append directories matching the patterns. Default is False.
    add_hidden_files : bool, optional
        Include hidden files. Default is False.
    reverse_sort : bool, optional
        Reverse sort the result list. Default is False.

    Returns
    -------
    list
        List of files and directories matching the patterns.
    """
    if pattern_list is None:
        pattern_list = ["*"]
    result_list: list[str] = []
    if not dir_name:
        dir_name = "."
    elif not os.path.isabs(dir_name) and not dir_name.startswith("."):
        dir_name = os.path.join(".", dir_name)
    if not isinstance(pattern_list, list):
        pattern_list = [pattern_list]
    if not check_if_dir_exists(dir_name):
        return result_list

    for file_name in os.listdir(dir_name):
        full_path = os.path.join(dir_name, file_name)
        for pattern in pattern_list:
            if fnmatch.fnmatch(file_name, pattern):
                if os.path.isdir(full_path) and append_dirs:
                    result_list.append(full_path)
                elif is_file(full_path):
                    if not add_hidden_files and file_name.startswith("."):
                        continue
                    result_list.append(full_path)
            if recursive and os.path.isdir(full_path):
                result_list.extend(
                    create_file_list(
                        pattern_list,
                        full_path,
                        recursive,
                        append_dirs,
                        add_hidden_files,
                        reverse_sort,
                    )
                )
    result_list.sort(reverse=reverse_sort)
    return result_list


def norm_path(file_name: str) -> str:
    """
    Normalize a path.

    Parameters
    ----------
    file_name : str
        File name to normalize.

    Returns
    -------
    str
        Normalized path name.
    """
    return os.path.normpath(file_name.replace("\\", "/"))
