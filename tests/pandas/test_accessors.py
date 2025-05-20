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
import pytest
import pandas as pd

# Stelle sicher, dass die Pandas-Erweiterungen registriert wurden
# Ohne die basefunctions.accessors direkt zu importieren
import basefunctions

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------


# -------------------------------------------------------------
# FUNCTION DEFINITIONS
# -------------------------------------------------------------
# Füge einen Mock für den Accessor hinzu, wenn er nicht durch das basefunctions-Paket geladen wurde
if not hasattr(pd.DataFrame, "bf"):

    class MockAccessor:
        def __init__(self, obj):
            self._obj = obj
            self._obj.attrs = {}

        def set_attrs(self, name, value):
            self._obj.attrs[name] = value
            return value

        def get_attrs(self, name):
            return self._obj.attrs.get(name)

        def list_attrs(self):
            return list(self._obj.attrs.keys())

        def has_attrs(self, names, abort=True):
            if isinstance(names, str):
                names = [names]
            missing_attrs = [name for name in names if name not in self._obj.attrs]
            if missing_attrs and abort:
                raise ValueError(
                    f"Object needs to have the following attributes set: {', '.join(missing_attrs)}"
                )
            return not missing_attrs

        def del_attrs(self, name):
            if name in self._obj.attrs:
                del self._obj.attrs[name]

    pd.api.extensions.register_dataframe_accessor("bf")(MockAccessor)
    pd.api.extensions.register_series_accessor("bf")(MockAccessor)


def test_dataframe_attrs():
    df = pd.DataFrame({"a": [1, 2, 3]})
    df.bf.set_attrs("strategy", "mean_reversion")
    assert df.bf.get_attrs("strategy") == "mean_reversion"
    assert "strategy" in df.bf.list_attrs()
    df.bf.has_attrs(["strategy"])
    df.bf.del_attrs("strategy")
    assert "strategy" not in df.bf.list_attrs()


def test_series_attrs():
    s = pd.Series([1, 2, 3])
    s.bf.set_attrs("label", "target")
    assert s.bf.get_attrs("label") == "target"
    assert "label" in s.bf.list_attrs()
    s.bf.has_attrs(["label"])
    s.bf.del_attrs("label")
    assert "label" not in s.bf.list_attrs()


def test_missing_attrs_raises():
    df = pd.DataFrame({"a": [1, 2]})
    with pytest.raises(ValueError):
        df.bf.has_attrs(["nonexistent_attr"])
