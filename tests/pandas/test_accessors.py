"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich
  Project : basefunctions
  Copyright (c) by neuraldevelopment
  All rights reserved.

  Description:
  Pytest test suite for pandas accessor extensions.
  Tests DataFrame and Series accessor functionality including attribute
  management, validation, and error handling.

  Log:
  v1.0.0 : Initial test implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
# External imports (alphabetical)
import pandas as pd
import pytest
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import Mock, patch, call

# Project imports (relative to project root)
from basefunctions.pandas.accessors import (
    _PandasAccessorBase,
    PandasDataFrame,
    PandasSeries,
)


# -------------------------------------------------------------
# FIXTURES
# -------------------------------------------------------------


@pytest.fixture
def sample_dataframe() -> pd.DataFrame:
    """
    Create sample DataFrame for testing.

    Returns
    -------
    pd.DataFrame
        DataFrame with sample data and no custom attributes
    """
    # ARRANGE
    df: pd.DataFrame = pd.DataFrame({
        "col1": [1, 2, 3],
        "col2": ["a", "b", "c"],
        "col3": [1.1, 2.2, 3.3],
    })

    # RETURN
    return df


@pytest.fixture
def sample_series() -> pd.Series:
    """
    Create sample Series for testing.

    Returns
    -------
    pd.Series
        Series with sample data and no custom attributes
    """
    # ARRANGE
    series: pd.Series = pd.Series([1, 2, 3, 4, 5], name="test_series")

    # RETURN
    return series


@pytest.fixture
def dataframe_with_attrs(sample_dataframe: pd.DataFrame) -> pd.DataFrame:
    """
    Create DataFrame with pre-configured attributes.

    Parameters
    ----------
    sample_dataframe : pd.DataFrame
        Base DataFrame fixture

    Returns
    -------
    pd.DataFrame
        DataFrame with custom attributes set
    """
    # ARRANGE
    sample_dataframe.attrs["source"] = "test_data"
    sample_dataframe.attrs["version"] = "1.0"
    sample_dataframe.attrs["timestamp"] = 1234567890
    sample_dataframe.attrs["metadata"] = {"key": "value"}

    # RETURN
    return sample_dataframe


@pytest.fixture
def series_with_attrs(sample_series: pd.Series) -> pd.Series:
    """
    Create Series with pre-configured attributes.

    Parameters
    ----------
    sample_series : pd.Series
        Base Series fixture

    Returns
    -------
    pd.Series
        Series with custom attributes set
    """
    # ARRANGE
    sample_series.attrs["unit"] = "meters"
    sample_series.attrs["precision"] = 2
    sample_series.attrs["description"] = "test measurements"

    # RETURN
    return sample_series


# -------------------------------------------------------------
# TEST CASES: PandasDataFrame Accessor Registration
# -------------------------------------------------------------


def test_dataframe_accessor_registered_successfully(sample_dataframe: pd.DataFrame) -> None:
    """
    Test DataFrame accessor is registered under 'pf' namespace.

    Verifies that the custom accessor is accessible via df.pf
    and is of the correct type.

    Parameters
    ----------
    sample_dataframe : pd.DataFrame
        Sample DataFrame fixture

    Returns
    -------
    None
        Test passes if accessor is registered correctly
    """
    # ACT & ASSERT
    assert hasattr(sample_dataframe, "pf")
    assert isinstance(sample_dataframe.pf, PandasDataFrame)
    assert hasattr(sample_dataframe.pf, "get_attrs")
    assert hasattr(sample_dataframe.pf, "set_attrs")
    assert hasattr(sample_dataframe.pf, "has_attrs")
    assert hasattr(sample_dataframe.pf, "list_attrs")
    assert hasattr(sample_dataframe.pf, "del_attrs")


def test_series_accessor_registered_successfully(sample_series: pd.Series) -> None:
    """
    Test Series accessor is registered under 'pf' namespace.

    Verifies that the custom accessor is accessible via series.pf
    and is of the correct type.

    Parameters
    ----------
    sample_series : pd.Series
        Sample Series fixture

    Returns
    -------
    None
        Test passes if accessor is registered correctly
    """
    # ACT & ASSERT
    assert hasattr(sample_series, "pf")
    assert isinstance(sample_series.pf, PandasSeries)
    assert hasattr(sample_series.pf, "get_attrs")
    assert hasattr(sample_series.pf, "set_attrs")
    assert hasattr(sample_series.pf, "has_attrs")
    assert hasattr(sample_series.pf, "list_attrs")
    assert hasattr(sample_series.pf, "del_attrs")


# -------------------------------------------------------------
# TEST CASES: PandasDataFrame Validation
# -------------------------------------------------------------


def test_dataframe_init_with_valid_dataframe(sample_dataframe: pd.DataFrame) -> None:
    """
    Test PandasDataFrame initializes correctly with valid DataFrame.

    Parameters
    ----------
    sample_dataframe : pd.DataFrame
        Sample DataFrame fixture

    Returns
    -------
    None
        Test passes if initialization succeeds
    """
    # ACT
    accessor: PandasDataFrame = PandasDataFrame(sample_dataframe)

    # ASSERT
    assert accessor._obj is sample_dataframe


def test_dataframe_validate_raises_error_for_invalid_type() -> None:  # CRITICAL TEST
    """
    Test DataFrame _validate raises RuntimeError for non-DataFrame objects.

    Validates security by rejecting invalid object types to prevent
    attribute injection vulnerabilities.

    Returns
    -------
    None
        Test passes if RuntimeError is raised
    """
    # ARRANGE
    invalid_objects: List[Any] = [
        None,
        [],
        {},
        "not a dataframe",
        123,
        pd.Series([1, 2, 3]),  # Wrong pandas type
    ]

    # ACT & ASSERT
    for invalid_obj in invalid_objects:
        with patch("basefunctions.get_logger") as mock_logger:
            with pytest.raises(RuntimeError, match="expected pandas dataframe object"):
                PandasDataFrame._validate(invalid_obj)
            # Verify error was logged
            mock_logger.return_value.error.assert_called_once()


def test_dataframe_init_raises_error_for_series() -> None:  # CRITICAL TEST
    """
    Test PandasDataFrame initialization fails when given Series object.

    Returns
    -------
    None
        Test passes if RuntimeError is raised
    """
    # ARRANGE
    series: pd.Series = pd.Series([1, 2, 3])

    # ACT & ASSERT
    with pytest.raises(RuntimeError, match="expected pandas dataframe object"):
        PandasDataFrame(series)


# -------------------------------------------------------------
# TEST CASES: PandasSeries Validation
# -------------------------------------------------------------


def test_series_init_with_valid_series(sample_series: pd.Series) -> None:
    """
    Test PandasSeries initializes correctly with valid Series.

    Parameters
    ----------
    sample_series : pd.Series
        Sample Series fixture

    Returns
    -------
    None
        Test passes if initialization succeeds
    """
    # ACT
    accessor: PandasSeries = PandasSeries(sample_series)

    # ASSERT
    assert accessor._obj is sample_series


def test_series_validate_raises_error_for_invalid_type() -> None:  # CRITICAL TEST
    """
    Test Series _validate raises RuntimeError for non-Series objects.

    Validates security by rejecting invalid object types to prevent
    attribute injection vulnerabilities.

    Returns
    -------
    None
        Test passes if RuntimeError is raised
    """
    # ARRANGE
    invalid_objects: List[Any] = [
        None,
        [],
        {},
        "not a series",
        456,
        pd.DataFrame({"col": [1, 2, 3]}),  # Wrong pandas type
    ]

    # ACT & ASSERT
    for invalid_obj in invalid_objects:
        with patch("basefunctions.get_logger") as mock_logger:
            with pytest.raises(RuntimeError, match="expected pandas series object"):
                PandasSeries._validate(invalid_obj)
            # Verify error was logged
            mock_logger.return_value.error.assert_called_once()


def test_series_init_raises_error_for_dataframe() -> None:  # CRITICAL TEST
    """
    Test PandasSeries initialization fails when given DataFrame object.

    Returns
    -------
    None
        Test passes if RuntimeError is raised
    """
    # ARRANGE
    df: pd.DataFrame = pd.DataFrame({"col": [1, 2, 3]})

    # ACT & ASSERT
    with pytest.raises(RuntimeError, match="expected pandas series object"):
        PandasSeries(df)


# -------------------------------------------------------------
# TEST CASES: get_attrs() - DataFrame
# -------------------------------------------------------------


def test_dataframe_get_attrs_returns_existing_attribute(
    dataframe_with_attrs: pd.DataFrame
) -> None:
    """
    Test get_attrs retrieves existing attribute value from DataFrame.

    Parameters
    ----------
    dataframe_with_attrs : pd.DataFrame
        DataFrame with pre-configured attributes

    Returns
    -------
    None
        Test passes if attribute value is retrieved correctly
    """
    # ACT
    source_value: str = dataframe_with_attrs.pf.get_attrs("source")
    version_value: str = dataframe_with_attrs.pf.get_attrs("version")
    timestamp_value: int = dataframe_with_attrs.pf.get_attrs("timestamp")

    # ASSERT
    assert source_value == "test_data"
    assert version_value == "1.0"
    assert timestamp_value == 1234567890


def test_dataframe_get_attrs_returns_none_for_nonexistent_attribute(
    sample_dataframe: pd.DataFrame
) -> None:
    """
    Test get_attrs returns None for attribute that doesn't exist.

    Parameters
    ----------
    sample_dataframe : pd.DataFrame
        DataFrame without custom attributes

    Returns
    -------
    None
        Test passes if None is returned
    """
    # ACT
    result: Optional[Any] = sample_dataframe.pf.get_attrs("nonexistent")

    # ASSERT
    assert result is None


def test_dataframe_get_attrs_returns_complex_object(
    dataframe_with_attrs: pd.DataFrame
) -> None:
    """
    Test get_attrs retrieves complex object (dict) attribute.

    Parameters
    ----------
    dataframe_with_attrs : pd.DataFrame
        DataFrame with metadata dict attribute

    Returns
    -------
    None
        Test passes if complex object is retrieved correctly
    """
    # ACT
    metadata: Dict[str, str] = dataframe_with_attrs.pf.get_attrs("metadata")

    # ASSERT
    assert isinstance(metadata, dict)
    assert metadata["key"] == "value"


# -------------------------------------------------------------
# TEST CASES: get_attrs() - Series
# -------------------------------------------------------------


def test_series_get_attrs_returns_existing_attribute(
    series_with_attrs: pd.Series
) -> None:
    """
    Test get_attrs retrieves existing attribute value from Series.

    Parameters
    ----------
    series_with_attrs : pd.Series
        Series with pre-configured attributes

    Returns
    -------
    None
        Test passes if attribute value is retrieved correctly
    """
    # ACT
    unit_value: str = series_with_attrs.pf.get_attrs("unit")
    precision_value: int = series_with_attrs.pf.get_attrs("precision")

    # ASSERT
    assert unit_value == "meters"
    assert precision_value == 2


def test_series_get_attrs_returns_none_for_nonexistent_attribute(
    sample_series: pd.Series
) -> None:
    """
    Test get_attrs returns None for attribute that doesn't exist in Series.

    Parameters
    ----------
    sample_series : pd.Series
        Series without custom attributes

    Returns
    -------
    None
        Test passes if None is returned
    """
    # ACT
    result: Optional[Any] = sample_series.pf.get_attrs("nonexistent")

    # ASSERT
    assert result is None


# -------------------------------------------------------------
# TEST CASES: set_attrs() - DataFrame
# -------------------------------------------------------------


def test_dataframe_set_attrs_creates_new_attribute(
    sample_dataframe: pd.DataFrame
) -> None:
    """
    Test set_attrs creates new attribute on DataFrame.

    Parameters
    ----------
    sample_dataframe : pd.DataFrame
        DataFrame without custom attributes

    Returns
    -------
    None
        Test passes if attribute is created and returned
    """
    # ARRANGE
    expected_value: str = "new_value"

    # ACT
    result: str = sample_dataframe.pf.set_attrs("new_attr", expected_value)

    # ASSERT
    assert result == expected_value
    assert sample_dataframe.attrs["new_attr"] == expected_value


def test_dataframe_set_attrs_updates_existing_attribute(
    dataframe_with_attrs: pd.DataFrame
) -> None:
    """
    Test set_attrs updates existing attribute value on DataFrame.

    Parameters
    ----------
    dataframe_with_attrs : pd.DataFrame
        DataFrame with existing attributes

    Returns
    -------
    None
        Test passes if attribute is updated correctly
    """
    # ARRANGE
    new_version: str = "2.0"

    # ACT
    result: str = dataframe_with_attrs.pf.set_attrs("version", new_version)

    # ASSERT
    assert result == new_version
    assert dataframe_with_attrs.attrs["version"] == new_version


def test_dataframe_set_attrs_handles_none_value(
    sample_dataframe: pd.DataFrame
) -> None:
    """
    Test set_attrs correctly handles None as attribute value.

    Parameters
    ----------
    sample_dataframe : pd.DataFrame
        Sample DataFrame

    Returns
    -------
    None
        Test passes if None value is stored correctly
    """
    # ACT
    result: None = sample_dataframe.pf.set_attrs("nullable_attr", None)

    # ASSERT
    assert result is None
    assert sample_dataframe.attrs["nullable_attr"] is None


def test_dataframe_set_attrs_handles_complex_objects(
    sample_dataframe: pd.DataFrame
) -> None:
    """
    Test set_attrs handles complex object types (dict, list, etc.).

    Parameters
    ----------
    sample_dataframe : pd.DataFrame
        Sample DataFrame

    Returns
    -------
    None
        Test passes if complex objects are stored correctly
    """
    # ARRANGE
    dict_value: Dict[str, Any] = {"nested": {"key": "value"}, "list": [1, 2, 3]}
    list_value: List[int] = [10, 20, 30]

    # ACT
    result_dict: Dict[str, Any] = sample_dataframe.pf.set_attrs("dict_attr", dict_value)
    result_list: List[int] = sample_dataframe.pf.set_attrs("list_attr", list_value)

    # ASSERT
    assert result_dict == dict_value
    assert result_list == list_value
    assert sample_dataframe.attrs["dict_attr"] == dict_value
    assert sample_dataframe.attrs["list_attr"] == list_value


# -------------------------------------------------------------
# TEST CASES: set_attrs() - Series
# -------------------------------------------------------------


def test_series_set_attrs_creates_new_attribute(
    sample_series: pd.Series
) -> None:
    """
    Test set_attrs creates new attribute on Series.

    Parameters
    ----------
    sample_series : pd.Series
        Series without custom attributes

    Returns
    -------
    None
        Test passes if attribute is created and returned
    """
    # ARRANGE
    expected_value: str = "celsius"

    # ACT
    result: str = sample_series.pf.set_attrs("temperature_unit", expected_value)

    # ASSERT
    assert result == expected_value
    assert sample_series.attrs["temperature_unit"] == expected_value


def test_series_set_attrs_updates_existing_attribute(
    series_with_attrs: pd.Series
) -> None:
    """
    Test set_attrs updates existing attribute value on Series.

    Parameters
    ----------
    series_with_attrs : pd.Series
        Series with existing attributes

    Returns
    -------
    None
        Test passes if attribute is updated correctly
    """
    # ARRANGE
    new_precision: int = 5

    # ACT
    result: int = series_with_attrs.pf.set_attrs("precision", new_precision)

    # ASSERT
    assert result == new_precision
    assert series_with_attrs.attrs["precision"] == new_precision


# -------------------------------------------------------------
# TEST CASES: has_attrs() - DataFrame
# -------------------------------------------------------------


def test_dataframe_has_attrs_returns_true_for_existing_single_attribute(
    dataframe_with_attrs: pd.DataFrame
) -> None:
    """
    Test has_attrs returns True when single attribute exists.

    Parameters
    ----------
    dataframe_with_attrs : pd.DataFrame
        DataFrame with pre-configured attributes

    Returns
    -------
    None
        Test passes if True is returned
    """
    # ACT
    result: bool = dataframe_with_attrs.pf.has_attrs("source")

    # ASSERT
    assert result is True


def test_dataframe_has_attrs_returns_true_for_multiple_existing_attributes(
    dataframe_with_attrs: pd.DataFrame
) -> None:
    """
    Test has_attrs returns True when all specified attributes exist.

    Parameters
    ----------
    dataframe_with_attrs : pd.DataFrame
        DataFrame with pre-configured attributes

    Returns
    -------
    None
        Test passes if True is returned
    """
    # ACT
    result: bool = dataframe_with_attrs.pf.has_attrs(["source", "version", "timestamp"])

    # ASSERT
    assert result is True


def test_dataframe_has_attrs_returns_false_for_missing_attribute_when_abort_false(
    dataframe_with_attrs: pd.DataFrame
) -> None:
    """
    Test has_attrs returns False when attribute missing and abort=False.

    Parameters
    ----------
    dataframe_with_attrs : pd.DataFrame
        DataFrame with some attributes

    Returns
    -------
    None
        Test passes if False is returned without raising error
    """
    # ACT
    result: bool = dataframe_with_attrs.pf.has_attrs("nonexistent", abort=False)

    # ASSERT
    assert result is False


def test_dataframe_has_attrs_raises_error_when_attribute_missing_and_abort_true(
    dataframe_with_attrs: pd.DataFrame
) -> None:  # CRITICAL TEST
    """
    Test has_attrs raises ValueError when attribute missing and abort=True.

    This is critical validation functionality that prevents operations
    on improperly configured DataFrames.

    Parameters
    ----------
    dataframe_with_attrs : pd.DataFrame
        DataFrame with some attributes

    Returns
    -------
    None
        Test passes if ValueError is raised with correct message
    """
    # ACT & ASSERT
    with pytest.raises(ValueError, match="Object needs to have the following attributes set: nonexistent"):
        dataframe_with_attrs.pf.has_attrs("nonexistent", abort=True)


def test_dataframe_has_attrs_raises_error_with_multiple_missing_attributes(
    dataframe_with_attrs: pd.DataFrame
) -> None:  # CRITICAL TEST
    """
    Test has_attrs raises ValueError listing all missing attributes.

    Parameters
    ----------
    dataframe_with_attrs : pd.DataFrame
        DataFrame with some attributes

    Returns
    -------
    None
        Test passes if ValueError contains all missing attribute names
    """
    # ACT & ASSERT
    with pytest.raises(ValueError, match="missing1, missing2, missing3"):
        dataframe_with_attrs.pf.has_attrs(["source", "missing1", "missing2", "missing3"], abort=True)


def test_dataframe_has_attrs_handles_empty_string_as_single_attribute(
    sample_dataframe: pd.DataFrame
) -> None:
    """
    Test has_attrs handles empty string attribute name.

    Parameters
    ----------
    sample_dataframe : pd.DataFrame
        DataFrame without attributes

    Returns
    -------
    None
        Test passes if empty string is treated as valid attribute name
    """
    # ACT
    result: bool = sample_dataframe.pf.has_attrs("", abort=False)

    # ASSERT
    assert result is False


def test_dataframe_has_attrs_handles_empty_list(
    sample_dataframe: pd.DataFrame
) -> None:
    """
    Test has_attrs returns True for empty attribute list.

    Parameters
    ----------
    sample_dataframe : pd.DataFrame
        Sample DataFrame

    Returns
    -------
    None
        Test passes if True is returned (no missing attributes)
    """
    # ACT
    result: bool = sample_dataframe.pf.has_attrs([])

    # ASSERT
    assert result is True


def test_dataframe_has_attrs_converts_string_to_list(
    dataframe_with_attrs: pd.DataFrame
) -> None:
    """
    Test has_attrs correctly converts single string to list internally.

    Parameters
    ----------
    dataframe_with_attrs : pd.DataFrame
        DataFrame with attributes

    Returns
    -------
    None
        Test passes if string parameter works same as single-item list
    """
    # ACT
    result_string: bool = dataframe_with_attrs.pf.has_attrs("source")
    result_list: bool = dataframe_with_attrs.pf.has_attrs(["source"])

    # ASSERT
    assert result_string == result_list
    assert result_string is True


# -------------------------------------------------------------
# TEST CASES: has_attrs() - Series
# -------------------------------------------------------------


def test_series_has_attrs_returns_true_for_existing_single_attribute(
    series_with_attrs: pd.Series
) -> None:
    """
    Test has_attrs returns True when single attribute exists in Series.

    Parameters
    ----------
    series_with_attrs : pd.Series
        Series with pre-configured attributes

    Returns
    -------
    None
        Test passes if True is returned
    """
    # ACT
    result: bool = series_with_attrs.pf.has_attrs("unit")

    # ASSERT
    assert result is True


def test_series_has_attrs_returns_true_for_multiple_existing_attributes(
    series_with_attrs: pd.Series
) -> None:
    """
    Test has_attrs returns True when all specified attributes exist in Series.

    Parameters
    ----------
    series_with_attrs : pd.Series
        Series with pre-configured attributes

    Returns
    -------
    None
        Test passes if True is returned
    """
    # ACT
    result: bool = series_with_attrs.pf.has_attrs(["unit", "precision", "description"])

    # ASSERT
    assert result is True


def test_series_has_attrs_raises_error_when_attribute_missing_and_abort_true(
    series_with_attrs: pd.Series
) -> None:  # CRITICAL TEST
    """
    Test has_attrs raises ValueError when attribute missing in Series.

    Parameters
    ----------
    series_with_attrs : pd.Series
        Series with some attributes

    Returns
    -------
    None
        Test passes if ValueError is raised
    """
    # ACT & ASSERT
    with pytest.raises(ValueError, match="Object needs to have the following attributes set: missing_attr"):
        series_with_attrs.pf.has_attrs("missing_attr", abort=True)


# -------------------------------------------------------------
# TEST CASES: list_attrs() - DataFrame
# -------------------------------------------------------------


def test_dataframe_list_attrs_returns_all_attribute_names(
    dataframe_with_attrs: pd.DataFrame
) -> None:
    """
    Test list_attrs returns list of all attribute names from DataFrame.

    Parameters
    ----------
    dataframe_with_attrs : pd.DataFrame
        DataFrame with pre-configured attributes

    Returns
    -------
    None
        Test passes if all attribute names are returned
    """
    # ACT
    result: List[str] = dataframe_with_attrs.pf.list_attrs()

    # ASSERT
    assert isinstance(result, list)
    assert "source" in result
    assert "version" in result
    assert "timestamp" in result
    assert "metadata" in result
    assert len(result) == 4


def test_dataframe_list_attrs_returns_empty_list_when_no_attributes(
    sample_dataframe: pd.DataFrame
) -> None:
    """
    Test list_attrs returns empty list when DataFrame has no attributes.

    Parameters
    ----------
    sample_dataframe : pd.DataFrame
        DataFrame without custom attributes

    Returns
    -------
    None
        Test passes if empty list is returned
    """
    # ACT
    result: List[str] = sample_dataframe.pf.list_attrs()

    # ASSERT
    assert isinstance(result, list)
    assert len(result) == 0


def test_dataframe_list_attrs_reflects_added_attributes(
    sample_dataframe: pd.DataFrame
) -> None:
    """
    Test list_attrs reflects newly added attributes.

    Parameters
    ----------
    sample_dataframe : pd.DataFrame
        Sample DataFrame

    Returns
    -------
    None
        Test passes if list updates after adding attributes
    """
    # ARRANGE
    initial_list: List[str] = sample_dataframe.pf.list_attrs()

    # ACT
    sample_dataframe.pf.set_attrs("new_attr1", "value1")
    sample_dataframe.pf.set_attrs("new_attr2", "value2")
    updated_list: List[str] = sample_dataframe.pf.list_attrs()

    # ASSERT
    assert len(initial_list) == 0
    assert len(updated_list) == 2
    assert "new_attr1" in updated_list
    assert "new_attr2" in updated_list


# -------------------------------------------------------------
# TEST CASES: list_attrs() - Series
# -------------------------------------------------------------


def test_series_list_attrs_returns_all_attribute_names(
    series_with_attrs: pd.Series
) -> None:
    """
    Test list_attrs returns list of all attribute names from Series.

    Parameters
    ----------
    series_with_attrs : pd.Series
        Series with pre-configured attributes

    Returns
    -------
    None
        Test passes if all attribute names are returned
    """
    # ACT
    result: List[str] = series_with_attrs.pf.list_attrs()

    # ASSERT
    assert isinstance(result, list)
    assert "unit" in result
    assert "precision" in result
    assert "description" in result
    assert len(result) == 3


def test_series_list_attrs_returns_empty_list_when_no_attributes(
    sample_series: pd.Series
) -> None:
    """
    Test list_attrs returns empty list when Series has no attributes.

    Parameters
    ----------
    sample_series : pd.Series
        Series without custom attributes

    Returns
    -------
    None
        Test passes if empty list is returned
    """
    # ACT
    result: List[str] = sample_series.pf.list_attrs()

    # ASSERT
    assert isinstance(result, list)
    assert len(result) == 0


# -------------------------------------------------------------
# TEST CASES: del_attrs() - DataFrame
# -------------------------------------------------------------


def test_dataframe_del_attrs_removes_existing_attribute(
    dataframe_with_attrs: pd.DataFrame
) -> None:  # CRITICAL TEST
    """
    Test del_attrs successfully removes existing attribute from DataFrame.

    This is a CRITICAL test as it involves data deletion.

    Parameters
    ----------
    dataframe_with_attrs : pd.DataFrame
        DataFrame with pre-configured attributes

    Returns
    -------
    None
        Test passes if attribute is removed
    """
    # ARRANGE
    assert "source" in dataframe_with_attrs.attrs

    # ACT
    dataframe_with_attrs.pf.del_attrs("source")

    # ASSERT
    assert "source" not in dataframe_with_attrs.attrs
    assert dataframe_with_attrs.pf.get_attrs("source") is None


def test_dataframe_del_attrs_handles_nonexistent_attribute_gracefully(
    sample_dataframe: pd.DataFrame
) -> None:  # CRITICAL TEST
    """
    Test del_attrs doesn't raise error when deleting nonexistent attribute.

    This prevents errors from deletion operations on missing attributes.

    Parameters
    ----------
    sample_dataframe : pd.DataFrame
        DataFrame without custom attributes

    Returns
    -------
    None
        Test passes if no error is raised
    """
    # ACT (should not raise error)
    sample_dataframe.pf.del_attrs("nonexistent")

    # ASSERT
    assert "nonexistent" not in sample_dataframe.attrs


def test_dataframe_del_attrs_only_removes_specified_attribute(
    dataframe_with_attrs: pd.DataFrame
) -> None:  # CRITICAL TEST
    """
    Test del_attrs only removes specified attribute, leaving others intact.

    Critical to ensure deletion doesn't affect other attributes.

    Parameters
    ----------
    dataframe_with_attrs : pd.DataFrame
        DataFrame with multiple attributes

    Returns
    -------
    None
        Test passes if only target attribute is removed
    """
    # ARRANGE
    initial_attrs: List[str] = dataframe_with_attrs.pf.list_attrs()
    assert "version" in initial_attrs

    # ACT
    dataframe_with_attrs.pf.del_attrs("version")

    # ASSERT
    assert "version" not in dataframe_with_attrs.attrs
    assert "source" in dataframe_with_attrs.attrs
    assert "timestamp" in dataframe_with_attrs.attrs
    assert "metadata" in dataframe_with_attrs.attrs


def test_dataframe_del_attrs_multiple_deletions(
    dataframe_with_attrs: pd.DataFrame
) -> None:  # CRITICAL TEST
    """
    Test del_attrs can be called multiple times successfully.

    Parameters
    ----------
    dataframe_with_attrs : pd.DataFrame
        DataFrame with multiple attributes

    Returns
    -------
    None
        Test passes if multiple deletions work correctly
    """
    # ARRANGE
    initial_count: int = len(dataframe_with_attrs.pf.list_attrs())

    # ACT
    dataframe_with_attrs.pf.del_attrs("source")
    dataframe_with_attrs.pf.del_attrs("version")
    dataframe_with_attrs.pf.del_attrs("timestamp")

    # ASSERT
    assert len(dataframe_with_attrs.pf.list_attrs()) == initial_count - 3
    assert "source" not in dataframe_with_attrs.attrs
    assert "version" not in dataframe_with_attrs.attrs
    assert "timestamp" not in dataframe_with_attrs.attrs


# -------------------------------------------------------------
# TEST CASES: del_attrs() - Series
# -------------------------------------------------------------


def test_series_del_attrs_removes_existing_attribute(
    series_with_attrs: pd.Series
) -> None:  # CRITICAL TEST
    """
    Test del_attrs successfully removes existing attribute from Series.

    This is a CRITICAL test as it involves data deletion.

    Parameters
    ----------
    series_with_attrs : pd.Series
        Series with pre-configured attributes

    Returns
    -------
    None
        Test passes if attribute is removed
    """
    # ARRANGE
    assert "unit" in series_with_attrs.attrs

    # ACT
    series_with_attrs.pf.del_attrs("unit")

    # ASSERT
    assert "unit" not in series_with_attrs.attrs
    assert series_with_attrs.pf.get_attrs("unit") is None


def test_series_del_attrs_handles_nonexistent_attribute_gracefully(
    sample_series: pd.Series
) -> None:  # CRITICAL TEST
    """
    Test del_attrs doesn't raise error when deleting nonexistent attribute.

    Parameters
    ----------
    sample_series : pd.Series
        Series without custom attributes

    Returns
    -------
    None
        Test passes if no error is raised
    """
    # ACT (should not raise error)
    sample_series.pf.del_attrs("nonexistent")

    # ASSERT
    assert "nonexistent" not in sample_series.attrs


# -------------------------------------------------------------
# TEST CASES: Integration and Edge Cases
# -------------------------------------------------------------


def test_accessor_operations_chain_correctly(sample_dataframe: pd.DataFrame) -> None:
    """
    Test multiple accessor operations can be chained together.

    Parameters
    ----------
    sample_dataframe : pd.DataFrame
        Sample DataFrame

    Returns
    -------
    None
        Test passes if operations chain correctly
    """
    # ACT
    sample_dataframe.pf.set_attrs("attr1", "value1")
    sample_dataframe.pf.set_attrs("attr2", "value2")
    sample_dataframe.pf.set_attrs("attr3", "value3")

    attr_list: List[str] = sample_dataframe.pf.list_attrs()
    has_all: bool = sample_dataframe.pf.has_attrs(["attr1", "attr2", "attr3"])

    sample_dataframe.pf.del_attrs("attr2")
    remaining_attrs: List[str] = sample_dataframe.pf.list_attrs()

    # ASSERT
    assert len(attr_list) == 3
    assert has_all is True
    assert len(remaining_attrs) == 2
    assert "attr2" not in remaining_attrs


def test_accessor_preserves_dataframe_data(sample_dataframe: pd.DataFrame) -> None:
    """
    Test accessor operations don't modify DataFrame data, only attributes.

    Parameters
    ----------
    sample_dataframe : pd.DataFrame
        Sample DataFrame with data

    Returns
    -------
    None
        Test passes if DataFrame data remains unchanged
    """
    # ARRANGE
    original_data: pd.DataFrame = sample_dataframe.copy()

    # ACT
    sample_dataframe.pf.set_attrs("test", "value")
    sample_dataframe.pf.del_attrs("test")

    # ASSERT
    pd.testing.assert_frame_equal(sample_dataframe, original_data)


def test_accessor_preserves_series_data(sample_series: pd.Series) -> None:
    """
    Test accessor operations don't modify Series data, only attributes.

    Parameters
    ----------
    sample_series : pd.Series
        Sample Series with data

    Returns
    -------
    None
        Test passes if Series data remains unchanged
    """
    # ARRANGE
    original_data: pd.Series = sample_series.copy()

    # ACT
    sample_series.pf.set_attrs("test", "value")
    sample_series.pf.del_attrs("test")

    # ASSERT
    pd.testing.assert_series_equal(sample_series, original_data)


def test_accessor_attributes_persist_across_operations(
    sample_dataframe: pd.DataFrame
) -> None:
    """
    Test attributes persist across DataFrame operations.

    Parameters
    ----------
    sample_dataframe : pd.DataFrame
        Sample DataFrame

    Returns
    -------
    None
        Test passes if attributes persist
    """
    # ARRANGE
    sample_dataframe.pf.set_attrs("persistent", "value")

    # ACT
    modified_df = sample_dataframe.copy()

    # ASSERT
    # Note: .copy() preserves attrs in pandas
    assert modified_df.pf.get_attrs("persistent") == "value"


@pytest.mark.parametrize("invalid_attr_name,expected_behavior", [
    ("", "treated as valid attribute name"),
    ("attr with spaces", "treated as valid attribute name"),
    ("attr/with/slashes", "treated as valid attribute name"),
    ("attr;with;semicolons", "treated as valid attribute name"),
    ("attr\nwith\nnewlines", "treated as valid attribute name"),
])
def test_dataframe_set_attrs_handles_unusual_attribute_names(
    sample_dataframe: pd.DataFrame,
    invalid_attr_name: str,
    expected_behavior: str
) -> None:
    """
    Test set_attrs handles unusual but technically valid attribute names.

    Parameters
    ----------
    sample_dataframe : pd.DataFrame
        Sample DataFrame
    invalid_attr_name : str
        Unusual attribute name to test
    expected_behavior : str
        Description of expected behavior

    Returns
    -------
    None
        Test passes if unusual names are handled correctly
    """
    # ACT
    sample_dataframe.pf.set_attrs(invalid_attr_name, "test_value")
    result: str = sample_dataframe.pf.get_attrs(invalid_attr_name)

    # ASSERT
    assert result == "test_value"
    assert invalid_attr_name in sample_dataframe.pf.list_attrs()
