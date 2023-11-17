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
#  dfext provides some dataframe extensions
#
# =============================================================================

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import pandas as pd
import tabulate

# -------------------------------------------------------------
# DEFINITIONS REGISTRY
# -------------------------------------------------------------

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# VARIABLE DEFINTIONS
# -------------------------------------------------------------


@pd.api.extensions.register_dataframe_accessor("bf")
class DataFrameExtensions:

    def __init__(self, pandas_obj):
        self._validate(pandas_obj)
        self._obj = pandas_obj

    @staticmethod
    def _validate(obj):
        # no check here
        pass

    # -------------------------------------------------------------
    # helper functions
    # -------------------------------------------------------------
    def setAdjClose(self):
        if 'adjclose' in self._obj.columns:
            self._obj = self.dropUnusedColumns(columnsUsed=['open', 'high', 'low', 'adjclose', 'volume'])
            self._obj.columns = ['open', 'high', 'low', 'close', 'volume']
        elif ('Adjclose' in self._obj.columns):
            self._obj = self.dropUnusedColumns(columnsUsed=['Open', 'High', 'Low', 'Adjclose', 'Volume'])
            self._obj.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        return self._obj

    def dropUnusedColumns(self, columnsUsed=None):
        """drop unused columns in dataframe

        Parameters
        ----------
        columnsUsed : list of str, optional
            columns to stay in dataframe, e.g ['adjclose']

        Returns
        -------
        pandas dataframe
            dataframe with requested columns or None if no column in dataframe
        """
        cols = []
        for column in columnsUsed:
            if column in self._obj.columns:
                cols.append(column)
            elif column.capitalize() in self._obj.columns:
                cols.append(column)
        if not len(cols):
            return None
        return self._obj[cols]

    def renameColumns(self, prefix="", postfix="", capitalize=False):
        """rename columns in dataframe

        Parameters
        ----------
        prefix : str, optional
            prefix for all column names, by default ""
        postfix : str, optional
            postfix for all column names, by default ""
        """
        colNames = []
        if not isinstance(self._obj.columns, pd.MultiIndex):
            for column in self._obj.columns:
                if capitalize:
                    column = column.capitalize()
                colNames.append(f"{prefix}{column}{postfix}")
            self._obj.columns = colNames
        else:
            for column in self._obj.columns:
                colName = column[0]
                if capitalize:
                    colName = colName.capitalize()
                colNames.append((f"{prefix}{colName}{postfix}", column[1]))
            self._obj.columns = pd.MultiIndex.from_tuples(colNames)
        return self._obj

    # -------------------------------------------------------------
    # print functions
    # -------------------------------------------------------------
    def print(self, tableFormat="psql"):
        """print dataframe as simple table

        Parameters
        ----------
        format : str, optional
            printing format supported from tabulate
        """
        print(tabulate.tabulate(tabular_data=self._obj, headers="keys", tablefmt=tableFormat))


@pd.api.extensions.register_series_accessor("bf")
class SeriesExtensions:

    def __init__(self, pandas_obj):
        self._validate(pandas_obj)
        self._obj = pandas_obj

    @staticmethod
    def _validate(obj):
        # no check here
        pass

    # -------------------------------------------------------------
    # print functions
    # -------------------------------------------------------------
    def print(self, format="psql"):
        """print dataframe as simple table

        Parameters
        ----------
        format : str, optional
            printing format supported from tabulate
        """
        print(tabulate.tabulate(tabular_data=self._obj.to_frame(), headers="keys", tablefmt=format))
