"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich

  Project : basefunctions

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  Pandas accessor extensions for DataFrame and Series operations

  Log:
  v1.0 : Initial implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Any, List
import pandas as pd
from basefunctions.utils.logging import setup_logger, get_logger

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
setup_logger(__name__)


# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


class _PandasAccessorBase:
    """
    Internal base class providing common attribute methods for pandas objects.
    """

    def get_attrs(self, name: str) -> Any:
        """
        Retrieve an attribute by its name.

        Parameters
        ----------
        name : str
            The name of the attribute to retrieve.

        Returns
        -------
        Any
            The value of the requested attribute.
        """
        return self._obj.attrs.get(name)

    def set_attrs(self, name: str, value: Any) -> Any:
        """
        Set an attribute to a specified value.

        Parameters
        ----------
        name : str
            The name of the attribute to set.
        value : Any
            The value to assign to the specified attribute.

        Returns
        -------
        Any
            The value of the attribute after setting.
        """
        self._obj.attrs[name] = value
        return value

    def has_attrs(self, names: str | List[str], abort: bool = True) -> bool:
        """
        Checks if the object has all the necessary attributes.

        Parameters
        ----------
        names : str | List[str]
            The name or list of names of the attributes to check.
        abort : bool, optional
            If True, raises an error when attributes are missing.

        Returns
        -------
        bool
            True if all attributes are available, False otherwise.
        """
        if isinstance(names, str):
            names = [names]
        missing_attrs = [name for name in names if name not in self._obj.attrs]
        if missing_attrs and abort:
            raise ValueError(f"Object needs to have the following attributes set: {', '.join(missing_attrs)}")
        return not missing_attrs

    def list_attrs(self) -> List[str]:
        """
        List all attribute names on the object.

        Returns
        -------
        List[str]
            A list of attribute names.
        """
        return list(self._obj.attrs.keys())

    def del_attrs(self, name: str) -> None:
        """
        Delete an attribute from the object.

        Parameters
        ----------
        name : str
            The name of the attribute to delete.

        Returns
        -------
        None
        """
        if name in self._obj.attrs:
            del self._obj.attrs[name]


@pd.api.extensions.register_dataframe_accessor("pf")
class PandasDataFrame(_PandasAccessorBase):
    """
    BasefunctionsDataFrame class provides additional functionality for
    pandas dataframes.
    """

    def __init__(self, pandas_obj: pd.DataFrame) -> None:
        super().__init__()
        self._validate(pandas_obj)
        self._obj = pandas_obj

    @staticmethod
    def _validate(obj) -> None:
        if not isinstance(obj, pd.DataFrame):
            get_logger(__name__).error("invalid object type for DataFrame: %s", type(obj))
            raise RuntimeError(f"expected pandas dataframe object, received {type(obj)}")


@pd.api.extensions.register_series_accessor("pf")
class PandasSeries(_PandasAccessorBase):
    """
    BasefunctionsSeries class provides additional functionality for
    pandas series.
    """

    def __init__(self, pandas_obj: pd.Series) -> None:
        super().__init__()
        self._validate(pandas_obj)
        self._obj = pandas_obj

    @staticmethod
    def _validate(obj) -> None:
        if not isinstance(obj, pd.Series):
            get_logger(__name__).error("invalid object type for Series: %s", type(obj))
            raise RuntimeError(f"expected pandas series object, received {type(obj)}")
