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
#  datasets provide basic access to well known datasets used for machine learning
#
# =============================================================================

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import os
import pandas as pd
import basefunctions.filefunctions as filefuncs

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# DEFINITIONS REGISTRY
# -------------------------------------------------------------

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------
_dataSetDict = {
    "aapl": ("/basefunctions/datasets/apple.csv", {
        "index_col": [0],
        "parse_dates": [0],
        "header": [0]
    }),
    "aaplfb": ("/basefunctions/datasets/aaplfb.csv", {
        "index_col": [0],
        "parse_dates": [0],
        "header": [0]
    }),
    "airports": ("/basefunctions/datasets/airports.csv", {
        "index_col": [0]
    }),
    "bmw": ("/basefunctions/datasets/bmw.csv", {
        "index_col": [0],
        "parse_dates": [0],
        "header": [0]
    }),
    "dax": ("/basefunctions/datasets/dax.csv", {
        "index_col": [0],
        "parse_dates": [0],
        "header": [0, 1]
    }),
    "eurusd": ("/basefunctions/datasets/eurusd.csv", {
        "index_col": [0],
        "parse_dates": [0],
        "header": [0]
    }),
    "eurojackpot": ("/basefunctions/datasets/eurojackpot.csv", {
        "index_col": [0],
        "parse_dates": [0],
        "header": [0]
    }),
    "listings": ("/basefunctions/datasets/listings.csv", {
        "index_col": [0],
        "header": [0]
    }),
    "portfolio": ("/basefunctions/datasets/portfolio.csv", {
        "index_col": [0],
        "parse_dates": [0],
        "header": [0]
    }),
    "port_stocks": ("/basefunctions/datasets/port_stocks.csv", {
        "index_col": [0],
        "parse_dates": [0],
        "header": [0]
    }),
    "sp500": ("/basefunctions/datasets/sp500.csv", {
        "index_col": [0],
        "parse_dates": [0],
        "header": [0]
    }),
    "stockdataframe": ("/basefunctions/datasets/stockdataframe.csv", {
        "index_col": [0],
        "parse_dates": [0],
        "header": [0, 1]
    }),
    "stocklistings": ("/basefunctions/datasets/stocklistings.csv", {
        "index_col": [0],
        "header": [0]
    }),
    "summergames": ("/basefunctions/datasets/summergames.csv", {
        "index_col": [0],
        "header": [0]
    }),
    "temperature": ("/basefunctions/datasets/temperature.csv", {
        "index_col": [0],
        "parse_dates": [0],
        "header": [0]
    }),
    "tickers": ("/basefunctions/datasets/tickers.csv", {}),
    "titanic": ("/basefunctions/datasets/titanic.csv", {})
}

_textsDict = {
    "christmascarol": "/basefunctions/texts/christmas_carol_de.txt",
    "christmascarol-en": "/basefunctions/texts/christmas_carol_en.txt",
    "faust": "/basefunctions/texts/faust.txt",
    "lea": "/basefunctions/texts/lea.txt"
}


# -------------------------------------------------------------
# VARIABLE DEFINTIONS
# -------------------------------------------------------------
def getDataSetList():
    """get a list of all available datasets

    Returns
    -------
    list
        list of available datasets
    """
    return list(_dataSetDict.keys())


def getDataSetFileName(dataSetName):
    """get the filename for a specific dataset

    Parameters
    ----------
    dataSetName : str
        name of dataset

    Returns
    -------
    str
        file name of dataset

    Raises
    ------
    RuntimeError
        raises RuntimeError if dataset name can't be found
    """
    if dataSetName in _dataSetDict:
        return filefuncs.normpath(
            os.path.sep.join(
                [filefuncs.getParentPathName(os.path.abspath(filefuncs.__file__)), _dataSetDict[dataSetName][0]]))
    else:
        raise RuntimeError(f"dataset {dataSetName} not found")


def getDataSet(dataSetName, capitalize=False):
    """get a specific dataset

    Parameters
    ----------
    dataSetName : str
        name of dataset
    capitalize : boolean
        capitalize column names

    Returns
    -------
    pandas dataframe
        dataframe of dataset

    Raises
    ------
    RuntimeError
        raises RuntimeError if dataset name can't be found
    """
    if dataSetName in _dataSetDict:
        fileName, kwargs = _dataSetDict[dataSetName]
        if not capitalize:
            return pd.read_csv(getDataSetFileName(dataSetName), **kwargs)
        else:
            return pd.read_csv(getDataSetFileName(dataSetName), **kwargs).bf.renameColumns(capitalize=True)
    else:
        raise RuntimeError(f"dataset {dataSetName} not found")


def getTextList():
    """get a list of all available texts

    Returns
    -------
    list
        list of available texts
    """
    return list(_textsDict.keys())


def getTextFileName(textName):
    """get the filename for a specific text

    Parameters
    ----------
    textName : str
        name of text

    Returns
    -------
    str
        file name of text

    Raises
    ------
    RuntimeError
        raises RuntimeError if text name can't be found
    """
    if textName in _textsDict:
        return filefuncs.normpath(
            os.path.sep.join([filefuncs.getParentPathName(os.path.abspath(filefuncs.__file__)), _textsDict[textName]]))
    else:
        raise RuntimeError(f"dataset {textName} not found")


def getText(textName):
    """get a specific text

    Parameters
    ----------
    textName : str
        name of text

    Returns
    -------
    str
        text content

    Raises
    ------
    RuntimeError
        raises RuntimeError if text name can't be found
    """
    if textName in _textsDict:
        return open(getTextFileName(textName), "r").read()
    else:
        raise RuntimeError(f"dataset {textName} not found")
