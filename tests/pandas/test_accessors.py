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

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------


# -------------------------------------------------------------
# FUNCTION DEFINITIONS
# -------------------------------------------------------------
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
