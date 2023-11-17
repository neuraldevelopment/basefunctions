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
#  online provide basic downloading functionality
#
# =============================================================================

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import requests

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
# FUNCTION DEFINITIONS
# -------------------------------------------------------------
def downloadURL(url, *args, **kwargs):
    """download a url and do error checking for status code 200

    Parameters
    ----------
    url : str
        url to download

    Returns
    -------
    str
        content of page

    Raises
    ------
    RuntimeError
        raises RuntimeError when status code != 200
    """
    response = requests.get(url, *args, **kwargs)
    if response.status_code != 200:
        raise RuntimeError (f"error {response.status_code} while downloading url {url}")
    return response.content
