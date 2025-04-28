"""
=============================================================================

  Licensed Materials, Property of Ralph Vogl, Munich

  Project : basefunctions

  Copyright (c) by Ralph Vogl

  All rights reserved.

  Description:

  a simple framework for base functionalities in python

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Any
import os
from dotenv import load_dotenv
import basefunctions

# -------------------------------------------------------------
#  FUNCTION DEFINITIONS
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


# -------------------------------------------------------------
# CLASS DEFINTIONS
# -------------------------------------------------------------
@basefunctions.singleton
class SecretHandler:
    """
    class SecretHandler loads .env file in home directory and makes all values available
    via get_secret_value method
    """

    def __init__(self):
        """
        Constructor of SecretHandler class, reads the .env file in home directory
        as the standard config file and makes all values available
        """
        env_filename = f"{os.path.expanduser('~')}{os.path.sep}.env"
        if os.path.exists(env_filename):
            load_dotenv(env_filename)

    def get_secret_value(self, key: str, default_value: Any = None) -> Any:
        """
        Summary:
        get the secret key from the settings.ini file

        Parameters:
        ----------
        key : str
            the key to get the secret for
        section : str
            the section in the config file
        default_value : Any
            the default value to return if the key is not found

        Returns:
        -------
        Any
            the secret key or the default value
        """
        val = os.getenv(key)
        if not val:
            return default_value
        return val

    def __getitem__(self, key: str) -> Any:
        """
        Summary:
        allows dict-style access to secrets via SecretHandler[key]

        Parameters:
        ----------
        key : str
            the key to get the secret for

        Returns:
        -------
        Any
            the secret key or None
        """
        return self.get_secret_value(key)
