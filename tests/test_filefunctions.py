"""
This module contains unit tests for the filefunctions module in the
basefunctions package.
"""
import os

import pytest

from basefunctions import filefunctions


def test_check_if_file_exists():
    """
    Test the check_if_file_exists function.

    This function tests the behavior of the check_if_file_exists function
    in different scenarios:
    - When the file exists
    - When the file does not exist
    - When the file is a directory
    - When the file is a symbolic link

    Each scenario is tested using assert statements to verify the expected
    return value of the function.

    Returns:
        None
    """
    assert (
        filefunctions.check_if_file_exists(
            "./tests/test_filefunctions.py"
        )
    ) is True

    assert (
        filefunctions.check_if_file_exists(
            "/path/to/nonexistent/file.txt"
        )
    ) is False

    assert filefunctions.check_if_file_exists(".") is False

    assert (
        filefunctions.check_if_file_exists("/path/to/symlink")
    ) is False


def test_check_if_dir_exists():
    """
    Test the check_if_dir_exists function.

    This function tests the behavior of the check_if_dir_exists function
    in different scenarios:
    - When the directory exists
    - When the directory does not exist
    - When the directory is a file
    - When the directory is a symbolic link
    """

    # Test when directory exists
    assert filefunctions.check_if_dir_exists(".") is True

    # Test when directory does not exist
    assert (
        filefunctions.check_if_dir_exists(
            "/path/to/nonexistent/directory"
        )
    ) is False

    # Test when directory is a file
    assert (
        filefunctions.check_if_dir_exists("./test_filefunctions.py")
    ) is False

    # Test when directory is a symbolic link
    assert (
        filefunctions.check_if_dir_exists("/path/to/symlink")
    ) is False


def test_check_if_exists():
    """
    Test the check_if_exists function.

    This function tests the behavior of the check_if_exists function in
    different scenarios:
    - When the file exists
    - When the file does not exist
    - When the directory exists
    - When the directory does not exist
    - When the file is a symbolic link
    - When the directory is a symbolic link
    """

    # Test when file exists
    assert (
        filefunctions.check_if_exists(
            "./tests/test_filefunctions.py", "FILE"
        )
    ) is True

    # Test when file does not exist
    assert (
        filefunctions.check_if_exists(
            "/path/to/nonexistent/file.txt", "FILE"
        )
    ) is False

    # Test when directory exists
    assert filefunctions.check_if_exists(".", "DIRECTORY") is True

    # Test when directory does not exist
    assert (
        filefunctions.check_if_exists(
            "/path/to/nonexistent/directory", "DIRECTORY"
        )
    ) is False

    # Test when file is a symbolic link
    assert (
        filefunctions.check_if_exists("/path/to/symlink", "FILE")
    ) is False

    # Test when directory is a symbolic link
    assert (
        filefunctions.check_if_exists(
            "/path/to/symlink", "DIRECTORY"
        )
    ) is False


def test_is_file():
    """
    Test the is_file function.

    This function tests the behavior of the is_file function from the
    filefunctions module.

    The tests include:
    - Checking if a file exists
    - Checking if a file does not exist
    - Checking if a file is a directory
    - Checking if a file is a symbolic link
    """

    # Test when file exists
    assert (
        filefunctions.is_file("./tests/test_filefunctions.py")
        is True
    )

    # Test when file does not exist
    assert (
        filefunctions.is_file("/path/to/nonexistent/file.txt")
    ) is False

    # Test when file is a directory
    assert filefunctions.is_file(".") is False

    # Test when file is a symbolic link
    assert filefunctions.is_file("/path/to/symlink") is False


def test_is_directory():
    """
    Test the is_directory function.

    This function tests the behavior of the is_directory function from the
    filefunctions module.

    Test cases:
    - Test when directory exists
    - Test when directory does not exist
    - Test when directory is a file
    - Test when directory is a symbolic link
    """

    # Test when directory exists
    assert filefunctions.is_directory(".") is True

    # Test when directory does not exist
    assert (
        filefunctions.is_directory("/path/to/nonexistent/directory")
    ) is False

    # Test when directory is a file
    assert (
        filefunctions.is_directory("./test_filefunctions.py")
    ) is False

    # Test when directory is a symbolic link
    assert filefunctions.is_directory("/path/to/symlink") is False


def test_get_file_name():
    """
    Test case for the get_file_name function.

    This function tests the behavior of the get_file_name function in the
    filefunctions module.

    Test cases:
    - Test when path contains a file name
    - Test when path ends with a slash
    - Test when path is empty
    - Test when path contains multiple directories
    - Test when path contains special characters
    """

    assert (
        filefunctions.get_file_name("/path/to/file.txt")
        == "file.txt"
    )

    assert filefunctions.get_file_name("/path/to/directory/") == ""

    assert filefunctions.get_file_name("") == ""

    assert (
        filefunctions.get_file_name("/path/to/directory/file.txt")
        == "file.txt"
    )

    assert (
        filefunctions.get_file_name("/path/to/file with spaces.txt")
        == "file with spaces.txt"
    )


def test_get_file_extension():
    """
    Test case for the get_file_extension function.

    This function tests the behavior of the get_file_extension function in the
    filefunctions module.

    Test cases:
    1. Test when path contains a file extension
    2. Test when path does not contain a file extension
    3. Test when path ends with a dot
    4. Test when path is empty
    5. Test when path contains multiple dots

    """

    # Test when path contains a file extension
    assert (
        filefunctions.get_file_extension("/path/to/file.txt")
        == ".txt"
    )

    # Test when path does not contain a file extension
    assert filefunctions.get_file_extension("/path/to/file") == ""

    # Test when path ends with a dot
    assert filefunctions.get_file_extension("/path/to/file.") == ""

    # Test when path is empty
    assert filefunctions.get_file_extension("") == ""

    # Test when path contains multiple dots
    assert (
        filefunctions.get_file_extension("/path/to/file.tar.gz")
        == ".gz"
    )

    # Test when path contains special characters
    assert (
        filefunctions.get_file_extension(
            "/path/to/file with spaces.txt"
        )
        == ".txt"
    )


def test_get_path_name():
    """
    Test case for the get_path_name function.

    Test cases:
    1. Test when path contains a file name.
    2. Test when path ends with a slash.
    3. Test when path is empty.
    4. Test when path contains multiple directories.
    5. Test when path contains special characters.
    """

    # Test when path contains a file name
    assert (
        filefunctions.get_path_name("/path/to/file.txt")
        == "/path/to/"
    )

    # Test when path ends with a slash
    assert (
        filefunctions.get_path_name("/path/to/directory/")
        == "/path/to/directory/"
    )

    # Test when path is empty
    assert filefunctions.get_path_name("") == "./"

    # Test when path contains multiple directories
    assert (
        filefunctions.get_path_name("/path/to/directory/file.txt")
        == "/path/to/directory/"
    )

    # Test when path contains special characters
    assert (
        filefunctions.get_path_name("/path/to/file with spaces.txt")
        == "/path/to/"
    )


def test_get_parent_path_name():
    """
    Test case for the get_parent_path_name function.

    Test cases:
    1. Test when path contains a file name.
    2. Test when path ends with a slash.
    3. Test when path is empty.
    4. Test when path contains multiple directories.
    5. Test when path contains special characters.
    """

    # Test when path contains a file name
    assert (
        filefunctions.get_parent_path_name("/path/to/file.txt")
        == "/path/"
    )

    # Test when path ends with a slash
    assert (
        filefunctions.get_parent_path_name("/path/to/directory/")
        == "/path/to/"
    )

    # Test when path is empty
    assert filefunctions.get_parent_path_name("") is None

    # Test when path contains multiple directories
    assert (
        filefunctions.get_parent_path_name(
            "/path/to/directory/file.txt"
        )
        == "/path/to/"
    )

    # Test when path contains special characters
    assert (
        filefunctions.get_parent_path_name(
            "/path/to/file with spaces.txt"
        )
        == "/path/"
    )


def test_get_base_name():
    """
    Test case for the get_base_name function.

    Test cases:
    1. Test when path contains a file name.
    2. Test when path ends with a slash.
    3. Test when path is empty.
    4. Test when path contains multiple directories.
    5. Test when path contains special characters.
    """

    # Test when path contains a file name
    assert (
        filefunctions.get_base_name("/path/to/file.txt")
        == "file.txt"
    )

    # Test when path ends with a slash
    assert filefunctions.get_base_name("/path/to/directory/") == ""

    # Test when path is empty
    assert filefunctions.get_base_name("") == ""

    # Test when path contains multiple directories
    assert (
        filefunctions.get_base_name("/path/to/directory/file.txt")
        == "file.txt"
    )

    # Test when path contains special characters
    assert (
        filefunctions.get_base_name("/path/to/file with spaces.txt")
        == "file with spaces.txt"
    )


def test_get_base_name_prefix():
    """
    Test case for the get_base_name_prefix function.

    Test cases:
    1. Test when path contains a file name.
    2. Test when path ends with a slash.
    3. Test when path is empty.
    4. Test when path contains multiple directories.
    5. Test when path contains special characters.
    """

    # Test when path contains a file name
    assert (
        filefunctions.get_base_name_prefix("/path/to/file.txt")
        == "file"
    )

    # Test when path ends with a slash
    assert (
        filefunctions.get_base_name_prefix("/path/to/directory/")
        == ""
    )

    # Test when path is empty
    assert filefunctions.get_base_name_prefix("") == ""

    # Test when path contains multiple directories
    assert (
        filefunctions.get_base_name_prefix(
            "/path/to/directory/file.txt"
        )
        == "file"
    )

    # Test when path contains special characters
    assert (
        filefunctions.get_base_name_prefix(
            "/path/to/file with spaces.txt"
        )
        == "file with spaces"
    )


def test_get_extension():
    """
    Test case for the get_extension function.

    Test cases:
    1. Test when path contains a file extension.
    2. Test when path ends with a slash.
    3. Test when path is empty.
    4. Test when path contains multiple extensions.
    5. Test when path contains special characters.
    """

    # Test when path contains a file extension
    assert filefunctions.get_extension("/path/to/file.txt") == "txt"

    # Test when path ends with a slash
    assert filefunctions.get_extension("/path/to/directory/") == ""

    # Test when path is empty
    assert filefunctions.get_extension("") == ""

    # Test when path contains multiple extensions
    assert (
        filefunctions.get_extension("/path/to/directory/file.tar.gz")
        == "gz"
    )

    # Test when path contains special characters
    assert (
        filefunctions.get_extension("/path/to/file with spaces.txt")
        == "txt"
    )


def test_get_path_and_base_name_prefix():
    """
    Test case for the get_path_and_base_name_prefix function.

    Test cases:
    1. Test when path contains a file name.
    2. Test when path ends with a slash.
    3. Test when path is empty.
    4. Test when path contains multiple directories.
    5. Test when path contains special characters.
    """
    # Test when path contains a file name
    assert (
        filefunctions.get_path_and_base_name_prefix(
            "/path/to/file.txt"
        )
        == "/path/to/file"
    )

    # Test when path ends with a slash
    assert (
        filefunctions.get_path_and_base_name_prefix(
            "/path/to/directory/"
        )
        == "/path/to/directory"
    )

    # Test when path is empty
    assert filefunctions.get_path_and_base_name_prefix("") == "."

    # Test when path contains multiple directories
    assert (
        filefunctions.get_path_and_base_name_prefix(
            "/path/to/directory/file.txt"
        )
        == "/path/to/directory/file"
    )

    # Test when path contains special characters
    assert (
        filefunctions.get_path_and_base_name_prefix(
            "/path/to/file with spaces.txt"
        )
        == "/path/to/file with spaces"
    )


def test_get_current_directory():
    """
    Test case for the get_current_directory function.

    This test case checks if the get_current_directory function
    """
    assert filefunctions.get_current_directory() == os.getcwd()


def test_set_current_directory():
    """
    Test case for the function set_current_directory().

    This test case checks the behavior of the set_current_directory() function
    when the directory exists and when it does not exist.

    Test cases:
    1. When the directory exists:
       - Set the current directory to a valid directory.
       - Check if the current working directory is updated correctly.

    2. When the directory does not exist:
       - Set the current directory to a non-existent directory.
       - Check if a RuntimeError is raised.
    """
    # remember current directory
    current_dir = filefunctions.get_current_directory()

    # Test when directory exists
    directory_name = filefunctions.norm_path(
        current_dir + os.path.sep + "/src/basefunctions"
    )
    filefunctions.set_current_directory(directory_name)
    assert os.getcwd() == directory_name

    # Test when directory does not exist
    directory_name = "/nonexistent/directory"
    with pytest.raises(RuntimeError):
        filefunctions.set_current_directory(directory_name)

    # restore current directory
    os.chdir(current_dir)


def test_rename_file():
    """
    Test case for the rename_file function.

    Test cases:
    1. Test when source file exists and target file does not exist.
    2. Test when source file exists and target file exists with
       overwrite=True.
    3. Test when source file exists and target file exists with
       overwrite=False.
    4. Test when source file does not exist.
    5. Test when target file is a directory.
    """

    # remove target file if it exists
    target_file = "./target.txt"
    if os.path.exists(target_file):
        os.remove(target_file)

    # Test when source file exists and target file does not exist
    source_file = "./source.txt"
    target_file = "./target.txt"
    open(
        source_file, "w", encoding="UTF-8"
    ).close()  # create source file
    filefunctions.rename_file(source_file, target_file)
    assert os.path.exists(target_file)
    assert not os.path.exists(source_file)

    # Test when source file exists and target file exists with overwrite=True
    source_file = "./source.txt"
    target_file = "./target.txt"
    open(
        source_file, "w", encoding="utf-8"
    ).close()  # create source file
    open(
        target_file, "w", encoding="utf-8"
    ).close()  # create target file
    filefunctions.rename_file(
        source_file, target_file, overwrite=True
    )
    assert os.path.exists(target_file)
    assert not os.path.exists(source_file)

    # Test when source file exists and target file exists with overwrite=False
    source_file = "./source.txt"
    target_file = "./target.txt"
    open(
        source_file, "w", encoding="utf-8"
    ).close()  # create source file
    open(
        target_file, "w", encoding="utf-8"
    ).close()  # create target file
    with pytest.raises(FileExistsError):
        filefunctions.rename_file(
            source_file, target_file, overwrite=False
        )

    # Test when source file does not exist
    source_file = "./nonexistent.txt"
    target_file = "./target.txt"
    os.remove(target_file)
    with pytest.raises(FileNotFoundError):
        filefunctions.rename_file(source_file, target_file)

    # Test when target file is a directory
    source_file = "./source.txt"
    target_dir = "./target_dir"
    if os.path.exists(target_dir):
        os.rmdir(target_dir)
    os.makedirs(target_dir)  # create target directory
    with pytest.raises(IsADirectoryError):
        filefunctions.rename_file(source_file, target_dir)

    # cleanup for source and target files
    if filefunctions.check_if_file_exists(source_file):
        os.remove(source_file)
    if filefunctions.check_if_file_exists(target_file):
        os.remove(target_file)
    if os.path.exists(target_dir):
        os.rmdir(target_dir)


def test_remove_file():
    """
    Test case for the remove_file function.

    This test verifies that the remove_file function correctly removes a file
    and checks if the file no longer exists after removal.
    """

    temp_file = "./temp.txt"

    # Create a temporary file
    open(temp_file, "w", encoding="utf-8").close()

    # Remove the file
    filefunctions.remove_file(temp_file)

    # Check if the file no longer exists
    assert not os.path.exists(temp_file)


def test_create_directory():
    """
    Test the create_directory function.

    This function tests the behavior of the create_directory function in
    different scenarios:
    - When the directory does not exist
    - When the directory already exists
    - When more than one directory needs to be created

    It also performs clean-up by removing the created directories after
    the tests.

    """

    # Test when directory does not exist
    dir_name = "test_directory"
    filefunctions.create_directory(dir_name)
    assert os.path.exists(dir_name)
    assert os.path.isdir(dir_name)

    # Test when directory already exists
    filefunctions.create_directory(dir_name)
    assert os.path.exists(dir_name)
    assert os.path.isdir(dir_name)

    # Test when more than one directory needs to be created
    filefunctions.create_directory(
        "test_directory/test_subdirectory"
    )
    assert os.path.exists(dir_name)
    assert os.path.isdir(dir_name)

    # Clean up
    filefunctions.remove_directory(dir_name)


def test_create_file_list():
    """
    Test case for the create_file_list function.

    This function tests the behavior of the create_file_list function in
    different scenarios.

    Scenarios:
    1. Test when pattern_list contains a single pattern.
    2. Test when pattern_list contains multiple patterns.
    3. Test when dir_name is None.
    4. Test when recursive is True.
    5. Test when append_dirs is True.
    6. Test when add_hidden_files is True.
    7. Test when reverse_sort is True.
    """

    # prepare test directory
    dir_name = "./test_directory"
    filefunctions.create_directory(dir_name)
    open(dir_name + "/file1.txt", "w", encoding="utf-8").close()
    open(dir_name + "/file2.txt", "w", encoding="utf-8").close()
    open(dir_name + "/file3.csv", "w", encoding="utf-8").close()
    open(dir_name + "/.file4.txt", "w", encoding="utf-8").close()
    dir_name2 = "./test_directory/sub_directory"
    filefunctions.create_directory(dir_name2)
    open(dir_name2 + "/file5.txt", "w", encoding="utf-8").close()
    open(dir_name2 + "/file6.txt", "w", encoding="utf-8").close()

    # Test when pattern_list contains a single pattern
    file_list = filefunctions.create_file_list(
        pattern_list=["*.txt"], dir_name=dir_name
    )
    assert (
        len(file_list) == 2
    )  # Assuming there are 2 text files in the test_directory

    # Test when pattern_list contains multiple patterns
    file_list = filefunctions.create_file_list(
        pattern_list=["*.txt", "*.csv"], dir_name=dir_name
    )
    assert (
        len(file_list) == 3
    )  # Assuming there are 2 text files and 1 CSV file in the test_directory

    # Test when dir_name is None
    file_list = filefunctions.create_file_list(
        pattern_list=["*.txt"]
    )
    assert (
        len(file_list) == 0
    )  # Assuming there are no text files in the current directory

    # Test when recursive is True
    file_list = filefunctions.create_file_list(
        pattern_list=["*.txt"], dir_name=dir_name, recursive=True
    )
    assert len(file_list) == 4
    # Assuming there are 4 text files in the test_directory and its
    # subdirectories

    # Test when append_dirs is True
    file_list = filefunctions.create_file_list(
        pattern_list=["*.txt"], dir_name=dir_name, append_dirs=True
    )
    assert len(file_list) == 2
    # Assuming there are 2 text files in the test_directory and 1 subdirectory

    # Test when add_hidden_files is True
    file_list = filefunctions.create_file_list(
        pattern_list=["*.txt"],
        dir_name=dir_name,
        add_hidden_files=True,
    )
    assert len(file_list) == 3
    # Assuming there are 2 text files and 1 hidden file in the test_directory

    # Test when reverse_sort is True
    file_list = filefunctions.create_file_list(
        pattern_list=["*"], dir_name=dir_name, reverse_sort=True
    )
    assert file_list == [
        "./test_directory/file3.csv",
        "./test_directory/file2.txt",
        "./test_directory/file1.txt",
    ]
    # Assuming the files are named file1.txt, file2.txt, file3.txt in
    # that order

    # clean up test directory
    filefunctions.remove_directory(dir_name)


def test_normpath():
    """
    Test case for the `norm_path` function.

    Test cases:
    1. Test when path contains backslashes
    2. Test when path contains duplicate slashes
    3. Test when path contains relative directory references
    4. Test when path contains current directory references
    5. Test when path is already normalized
    """

    # Test when path contains backslashes
    path = "C:\\Users\\username\\Documents\\file.txt"
    expected_result = "C:/Users/username/Documents/file.txt"
    assert filefunctions.norm_path(path) == expected_result

    # Test when path contains duplicate slashes
    path = "C:/Users//username/Documents//file.txt"
    expected_result = "C:/Users/username/Documents/file.txt"
    assert filefunctions.norm_path(path) == expected_result

    # Test when path contains relative directory references
    path = "C:/Users/username/Documents/../file.txt"
    expected_result = "C:/Users/username/file.txt"
    assert filefunctions.norm_path(path) == expected_result

    # Test when path contains current directory references
    path = "C:/Users/username/Documents/./file.txt"
    expected_result = "C:/Users/username/Documents/file.txt"
    assert filefunctions.norm_path(path) == expected_result

    # Test when path is already normalized
    path = "C:/Users/username/Documents/file.txt"
    expected_result = "C:/Users/username/Documents/file.txt"
    assert filefunctions.norm_path(path) == expected_result
