"""
=============================================================================

  Licensed Materials, Property of neuraldevelopment, Munich

  Project : basefunctions

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  a simple framework for base functionalities in python

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Any, Optional
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
# VARIABLE DEFINITIONS
# -------------------------------------------------------------


# -------------------------------------------------------------
# CLASS DEFINITIONS
# -------------------------------------------------------------
@basefunctions.singleton
class SecretHandler:
    """
    class SecretHandler loads a .env file and makes all values available
    via get_secret_value method
    """

    def __init__(self, env_file: Optional[str] = None):
        """
        Constructor of SecretHandler class, reads the .env file in home directory
        as the standard config file and makes all values available

        Parameters:
        ----------
        env_file : Optional[str]
            Optional path to a specific .env file. If None, defaults to ~/.env
        """
        if env_file is None:
            env_file = f"{os.path.expanduser('~')}{os.path.sep}.env"
        if os.path.exists(env_file):
            load_dotenv(env_file)

    def get_secret_value(self, key: str, default_value: Any = None) -> Any:
        """
        Summary:
        get the secret value from the .env file

        Parameters:
        ----------
        key : str
            the key to get the secret for
        default_value : Any
            the default value to return if the key is not found

        Returns:
        -------
        Any
            the secret value or the default value
        """
        val = os.getenv(key)
        if val is None:
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
            the secret value or None
        """
        return self.get_secret_value(key)
