"""
=============================================================================

  Licensed Materials, Property of neuraldevelopment, Munich

  Project : basefunctions - tests for ConfigHandler

  Copyright (c) by neuraldevelopment

  All rights reserved.

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import shutil
from pathlib import Path
import json
import pytest
import basefunctions as bf


# -------------------------------------------------------------
# FUNCTION DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# DEFINITIONS REGISTRY
# -------------------------------------------------------------

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------
TEST_PACKAGE = "testpackage"
TEST_CONFIG_DIR = Path(bf.get_home_path()) / ".config" / TEST_PACKAGE
TEST_CONFIG_FILE = TEST_CONFIG_DIR / f"{TEST_PACKAGE}.json"

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# FIXTURES
# -------------------------------------------------------------


@pytest.fixture(autouse=True)
def clean_environment():
    if TEST_CONFIG_DIR.exists():
        shutil.rmtree(TEST_CONFIG_DIR)
    handler = bf.ConfigHandler()
    handler.config = {}
    yield handler
    if TEST_CONFIG_DIR.exists():
        shutil.rmtree(TEST_CONFIG_DIR)


# -------------------------------------------------------------
# TESTS
# -------------------------------------------------------------


def test_create_default_config_creates_empty_dict(clean_environment):
    handler = clean_environment
    handler.create_default_config(TEST_PACKAGE)
    assert TEST_CONFIG_FILE.exists()
    with open(TEST_CONFIG_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)
    assert isinstance(data, dict)
    assert TEST_PACKAGE in data
    assert data[TEST_PACKAGE] == {}


def test_load_config_valid_file(clean_environment):
    handler = clean_environment
    handler.create_default_config(TEST_PACKAGE)
    handler.load_config(str(TEST_CONFIG_FILE))
    assert TEST_PACKAGE in handler.get_config()


def test_load_default_config_creates_and_loads(clean_environment):
    handler = clean_environment
    handler.load_default_config(TEST_PACKAGE)
    assert TEST_PACKAGE in handler.get_config()


def test_get_config_value_existing_path(clean_environment):
    handler = clean_environment
    handler.config = {TEST_PACKAGE: {"key": {"subkey": "value"}}}
    value = handler.get_config_value(f"{TEST_PACKAGE}/key/subkey")
    assert value == "value"


def test_get_config_value_nonexistent_path_returns_default(clean_environment):
    handler = clean_environment
    handler.config = {TEST_PACKAGE: {"key": {}}}
    value = handler.get_config_value(f"{TEST_PACKAGE}/key/missing", default_value="default")
    assert value == "default"


def test_get_config_without_package_returns_all(clean_environment):
    handler = clean_environment
    sample_config = {TEST_PACKAGE: {"somekey": "somevalue"}}
    handler.config = sample_config
    assert handler.get_config() == sample_config


def test_get_config_with_package_returns_subset(clean_environment):
    handler = clean_environment
    handler.config = {TEST_PACKAGE: {"somekey": "somevalue"}}
    assert handler.get_config(TEST_PACKAGE) == {"somekey": "somevalue"}


def test_list_available_paths(clean_environment):
    handler = clean_environment
    handler.config = {TEST_PACKAGE: {"a": {"b": {"c": 123}}, "d": 456}}
    paths = handler.list_available_paths()
    expected_paths = [
        f"{TEST_PACKAGE}",
        f"{TEST_PACKAGE}/a",
        f"{TEST_PACKAGE}/a/b",
        f"{TEST_PACKAGE}/a/b/c",
        f"{TEST_PACKAGE}/d",
    ]
    assert set(paths) == set(expected_paths)
