# =============================================================================
#
#  Licensed Materials, Property of Ralph Vogl, Munich
#
#  Project : basefunctions
#
#  Copyright (c) by Ralph Vogl
#
#  All rights reserved.
#
#  Description:
#
#  filefunctions provide basic functionality for file handling stuff
#
# =============================================================================

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import os.path
import shutil
import fnmatch

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------


# -------------------------------------------------------------
# DEFINITIONS REGISTRY
# -------------------------------------------------------------

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# VARIABLE DEFINTIONS
# -------------------------------------------------------------

def checkIfFileExists(fileName):
    """check if file exists

    Parameters
    ----------
    fileName : str,
        file name to be checked

    Returns
    -------
    bool
        True if file exists
    """
    if fileName:
        return _checkIfExists(fileName, fileType="FILE")
    else:
        return False

def checkIfDirExists(dirName):
    """check if directory exists

    Parameters
    ----------
    dirName : str,
        directory name to be checked

    Returns
    -------
    bool
        True if directory exists
    """
    if dirName:
        return _checkIfExists(dirName, fileType="DIR")
    else:
        return False

def _checkIfExists(fileName, fileType = "FILE"):
    """check if a specific filetype exists

    Parameters
    ----------
    fileName : str
        name of file or directory to be checked
    fileType : str
        type of file or directory to be checked, by default "FILE"

    Returns
    -------
    bool
        True if file or directory exists
    """
    if fileType == "FILE":
        return os.path.exists(fileName) and os.path.isfile(fileName)
    if fileType == "DIR":
        return os.path.exists(fileName) and os.path.isdir(fileName)


def isFile(fileName):
    """check if fileName is a regular file

    Parameters
    ----------
    fileName : str,
        name of file to be checked

    Returns
    -------
    bool
        True if file exists and is a regular file
    """
    return checkIfFileExists(fileName)


def isDirectory(dirName):
    """check if dirName is a regular directory

    Parameters
    ----------
    dirName : str,
        name of directory to be checked

    Returns
    -------
    bool
        True if directory exists and is a directory
    """
    return checkIfDirExists(dirName)

def getFileName(pathFileName):
    """get file name part from complete fileName
       /cygdrive/c/Users/Q202999/Desktop/2352222.pdf -> 2352222.pdf

    Parameters
    ----------
    pathFileName : str
        path file name to get info from

    Returns
    -------
    str
        file name of file name
    """
    if pathFileName:
        # split up path and return last element as basename
        return normpath(os.path.split(pathFileName)[-1])
    else:
        return None

def getPathName(pathFileName):
    """get path name from complete fileName
       /cygdrive/c/Users/Q202999/Desktop/2352222.abc.pdf -> /cygdrive/c/Users/Q202999/Desktop/

    Parameters
    ----------
    pathFileName : str
        path file name to get info from

    Returns
    -------
    str
        path name of file name
    """
    if pathFileName:
        # split up path
        return normpath(os.path.split(pathFileName)[0]) + os.path.sep
    else:
        return None

def getParentPathName(pathFileName):
    """get path name from complete fileName
       /cygdrive/c/Users/Q202999/Desktop -> /cygdrive/c/Users/Q202999/

    Parameters
    ----------
    pathFileName : str
        path file name to get info from

    Returns
    -------
    str
        parrent path name
    """
    if pathFileName:
        # split up path
        return normpath(os.path.split(os.path.split(pathFileName)[0])[0]) + os.path.sep
    else:
        return None

def getBaseName(pathFileName):
    """get base name part from complete fileName
       /cygdrive/c/Users/Q202999/Desktop/2352222.abc.pdf -> 2352222.abc

    Parameters
    ----------
    pathFileName : str
        path file name to get info from

    Returns
    -------
    str
        base name of file
    """
    if pathFileName:
        # split up path
        return normpath(os.path.splitext(os.path.split(pathFileName)[-1])[0])
    else:
        return None

def getBaseNamePrefix(pathFileName):
    """get basename prefix from complete fileName
       /cygdrive/c/Users/Q202999/Desktop/2352222.abc.pdf -> 2352222

    Parameters
    ----------
    pathFileName : str
        path file name to get info from

    Returns
    -------
    str
        basename prefix of file name
    """
    if pathFileName:
        # split up path
        return normpath(os.path.splitext(os.path.split(pathFileName)[-1])[0].split(".")[0])
    else:
        return None

def getExtension(pathFileName):
    """get extension from complete fileName
       /cygdrive/c/Users/Q202999/Desktop/2352222.pdf -> .pdf

    Parameters
    ----------
    pathFileName : str
        path file name to get info from

    Returns
    -------
    str
        extension of file name
    """
    if pathFileName:
        # split up path
        return normpath(os.path.splitext(os.path.split(pathFileName)[-1])[1])
    else:
        return None

def getPathAndBaseName(pathFileName):
    """get path and base name from complete fileName
       /cygdrive/c/Users/Q202999/Desktop/2352222.abc.pdf -> /cygdrive/c/Users/Q202999/Desktop/2352222.abc

    Parameters
    ----------
    pathFileName : str
        path file name to get info from

    Returns
    -------
    str
        path and base name of file name
    """
    if pathFileName:
        # split up path
        return normpath(os.path.splitext(pathFileName)[0])
    else:
        return None

def getCurrentDirectory():
    """get current directory of process

    Returns
    -------
    str
        current directory name
    """
    return os.getcwd()

def setCurrentDirectory(directoryName):
    """set current directory of process

    Parameters
    ----------
    directoryName : str
        current directory name to set

    Raises
    ------
    RuntimeError
        raises RuntimeError when directoryName doesn't exist
    """
    if (directoryName != "." and directoryName != ".."):
        if not checkIfDirExists(directoryName):
            raise RuntimeError(f"directory {directoryName} not found")
        os.chdir(directoryName)

def renameFile(src, target, overwrite=False):
    """rename a file

    Parameters
    ----------
    src : src
        source file name
    target : str
        target file name
    overwrite : bool, optional
        overwrite flag if target already exists, by default False

    Raises
    ------
    RuntimeError
        raises RuntimeError when target directory doesn't exist
    RuntimeError
        raises RuntimeError when target file already exists and overwrite flag is False
    RuntimeError
        raises RuntimeError when src file doesn't exist
    """
    # check if target directory exists if available
    dirName = getPathName(target)
    if not dirName or not checkIfDirExists(dirName):
        raise RuntimeError(f"{dirName} doesn't exist, can't rename file")
    # check if target file exists already and we should not overwrite it
    if overwrite == False and checkIfFileExists(target):
        raise RuntimeError(f"{target} already exists and overwrite flag set False")
    # check if source file exists
    if checkIfFileExists(src):
        os.rename(src, target)
    else:
        raise RuntimeError(f"{src} doesn't exist")

def removeFile(fileName):
    """remove a file

    Parameters
    ----------
    fileName : str
        file name to remove
    """
    if checkIfFileExists(fileName):
        os.remove(fileName)

def createDirectory(dirName):
    """create a directory recursively, this means a complete path to
       the requested structure will be created if it doesn't exist yet

    Parameters
    ----------
    dirName : str
        directory path to create
    """
    # correct path separator if necessary
    dirName = dirName.replace("/", os.path.sep)
    # split path elements
    dirNameList = ((dirName).split(os.path.sep))
    # iterate over all path elements
    pathName = dirNameList[0]
    for i in range(1, len(dirNameList)):
        pathName += os.path.sep + dirNameList[i]
        if not checkIfDirExists(pathName):
            os.mkdir(pathName)

def removeDirectory(dirName):
    """remove a directory

    Parameters
    ----------
    dirName : str
        directory name

    Raises
    ------
    RuntimeError
        raises RuntimeError when trying to remove '/' directory
    """
    if not checkIfDirExists(dirName):
        return
    if dirName == os.path.sep or dirName == "/":
        raise RuntimeError("can't delete complete / directory")
    shutil.rmtree(dirName)

def createFileList(patternList=["*"], dirName=None, recursive=False, appendDirs=False, addHiddenFiles=False, reverseSort=False):
    """create a file list from a given directory

    Parameters
    ----------
    patternList : list, optional
        pattern elements to search for, by default ["*"]
    dirName : str, optional
        directory to search, if None we use current directory, by default None
    recursive : bool, optional
        recursive search, by default False
    appendDirs : bool, optional
        append directories matching the patterns, by default False
    addHiddenFiles : bool, optional
        append hidden files matching the patterns, by default False
    reverseSort : bool, optional
        reverse sort the result list, by default False

    Returns
    -------
    list
        list of files and directories matching the patterns
    """
    resultList = []
    if not dirName:
        dirName="."
    if not ( dirName.startswith(os.path.sep) or ":" in dirName ) and not ( dirName.startswith(".")):
        dirName = ".%s%s"%(os.path.sep, dirName)
    if not isinstance(patternList, list):
        patternList = [patternList]
    if not checkIfDirExists(dirName):
        return resultList
    for fileName in os.listdir(dirName):
        for pattern in patternList:
            if recursive and isDirectory(fileName):
                resultList.extend(createFileList(patternList, fileName, recursive, appendDirs, addHiddenFiles, reverseSort))
            if fnmatch.fnmatch(fileName, pattern):
                if appendDirs and isDirectory(os.path.sep.join([dirName, fileName])):
                    resultList.append(fileName)
                if isFile(os.path.sep.join([dirName,fileName])):
                    if not addHiddenFiles and fileName.startswith("."):
                        continue
                    resultList.append(os.path.sep.join([dirName, fileName]))
    if not reverseSort:
        resultList.sort()
    else:
        resultList.sort(reverse=True)
    return resultList

def normpath(fileName):
    """normalize a path

    Parameters
    ----------
    fileName : str
        file name to normalize

    Returns
    -------
    str
        normalized path name
    """
    return os.path.normpath(fileName)
