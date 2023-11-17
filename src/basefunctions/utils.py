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
#  utils provide basic functionality for misc stuff
#
# =============================================================================

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import re

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
def removeNonASCIICharsFromString(string):
    """remove all non ASCII chars from string

    Parameters
    ----------
    string : str
        string with non ASCII chars

    Returns
    -------
    str
        string with removed non ASCII chars
    """
    return re.sub(r'[^\x00-\x7F]+','', string)

def removeCharsFromNumString(string, separator="."):
    """remove chars from number string

    Parameters
    ----------
    string : str
        string with numbers and other characters

    Returns
    -------
    str
        string only with numbers and period (.)
    """
    return re.sub(r'[^0-9'+re.escape(separator) + r']', '', string)


def removeWhitespacesFromString(string):
    """remove all whitespaces from string, removes whitespaces everywhere in
       the string, not just at start and end like the strip method

    Parameters
    ----------
    string : str
        string with whitespaces

    Returns
    -------
    str
        string without whitespaces
    """
    return re.sub(r'\s+', '', string)

def convertStringWithUnitToNum(string):
    """convert a string with unit to num, e.g. 402 M = 402_000_000_000

    supported are the following units:
    'B'     -   'Billion'   1_000_000_000
    'M'     -   'Million'   1_000_000
    'T'     -   'Thousand'  1_000

    Parameters
    ----------
    string : str
        string with unit

    Returns
    -------
    num
        corresponding number
    """
    units = {
        'B':1_000_000_000,
        'M':1_000_000,
        'K':1_000,
        'T':1_000,
        '$':1,
        '€':1,
    }
    unit = string[-1].upper()
    if not unit in units:
        unit = '$'
    return float(removeCharsFromNumString(string))*units[unit]
