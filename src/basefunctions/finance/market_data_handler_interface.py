"""
=============================================================================

 Licensed Materials, Property of neuraldevelopment , Munich

 Project : basefunctions

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 market data handler interface for financial applications

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from abc import ABC, abstractmethod
from typing import List, Union, Dict
import pandas as pd

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
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------
class MarketDataHandlerInterface(ABC):
    """
    abstract base class for market data handlers

    this interface defines the common methods that all market data handlers
    should implement, regardless of whether they retrieve data from external
    apis or from a local database
    """

    @abstractmethod
    def get_exchanges(self) -> Dict[str, pd.DataFrame]:
        """
        get all available exchanges

        returns
        -------
        dict
            dictionary with exchange names as keys and DataFrames as values
        """

    @abstractmethod
    def get_exchanges_symbols(
        self, exchanges: Union[List[str], str] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        get symbols for specified exchanges

        parameters
        ----------
        exchanges : Union[List[str], str], optional
            exchange code(s) to retrieve symbols for, default: None
            if None, a default exchange will be used (typically "XETRA")
            can be a single exchange code as string or a list of exchange codes

        returns
        -------
        dict
            dictionary with exchange names as keys and DataFrames as values
        """

    @abstractmethod
    def get_symbols_prices(
        self, symbols: Union[List[str], str] = None, start_date: str = None, end_date: str = None
    ) -> Dict[str, pd.DataFrame]:
        """
        get price data for specified symbols

        parameters
        ----------
        symbols : Union[List[str], str], optional
            symbol(s) to retrieve prices for, default: None
            if None, default symbols will be used
            can be a single symbol as string or a list of symbols
        start_date : str, optional
            start date for data retrieval in format "YYYY-MM-DD", default: None
        end_date : str, optional
            end date for data retrieval in format "YYYY-MM-DD", default: None

        returns
        -------
        dict
            dictionary with symbols as keys and DataFrames as values
        """

    @abstractmethod
    def get_symbols_dividends(
        self, symbols: Union[List[str], str] = None, start_date: str = None, end_date: str = None
    ) -> Dict[str, pd.DataFrame]:
        """
        get dividend data for specified symbols

        parameters
        ----------
        symbols : Union[List[str], str], optional
            symbol(s) to retrieve dividends for, default: None
            if None, default symbols will be used
            can be a single symbol as string or a list of symbols
        start_date : str, optional
            start date for data retrieval in format "YYYY-MM-DD", default: None
        end_date : str, optional
            end date for data retrieval in format "YYYY-MM-DD", default: None

        returns
        -------
        dict
            dictionary with symbols as keys and DataFrames as values
        """

    @abstractmethod
    def get_symbols_splits(
        self, symbols: Union[List[str], str] = None, start_date: str = None, end_date: str = None
    ) -> Dict[str, pd.DataFrame]:
        """
        get split data for specified symbols

        parameters
        ----------
        symbols : Union[List[str], str], optional
            symbol(s) to retrieve splits for, default: None
            if None, default symbols will be used
            can be a single symbol as string or a list of symbols
        start_date : str, optional
            start date for data retrieval in format "YYYY-MM-DD", default: None
        end_date : str, optional
            end date for data retrieval in format "YYYY-MM-DD", default: None

        returns
        -------
        dict
            dictionary with symbols as keys and DataFrames as values
        """
