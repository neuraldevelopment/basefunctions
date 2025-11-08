"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich
  Project : basefunctions
  Copyright (c) by neuraldevelopment
  All rights reserved.

  Description:
  Pytest test suite for basefunctions.io.serializer module.
  Tests unified serialization framework with multiple format support.

  Log:
  v1.0.0 : Initial test implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
# External imports (alphabetical)
import gzip
import json
import pickle
import pytest
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from unittest.mock import Mock, MagicMock, patch, mock_open

# Project imports (relative to project root)
from basefunctions.io.serializer import (
    Serializer,
    SerializationError,
    UnsupportedFormatError,
    JSONSerializer,
    PickleSerializer,
    YAMLSerializer,
    MessagePackSerializer,
    SerializerFactory,
    serialize,
    deserialize,
    to_file,
    from_file,
    _detect_format_from_extension,
    HAS_YAML,
    HAS_MSGPACK,
)


# -------------------------------------------------------------
# FIXTURES
# -------------------------------------------------------------


@pytest.fixture
def sample_data() -> Dict[str, Any]:
    """
    Provide sample data for serialization tests.

    Returns
    -------
    Dict[str, Any]
        Sample dictionary with various data types
    """
    return {
        "string": "test_value",
        "integer": 42,
        "float": 3.14,
        "boolean": True,
        "list": [1, 2, 3],
        "nested": {"key": "value"},
    }


@pytest.fixture
def json_serializer() -> JSONSerializer:
    """
    Create JSONSerializer instance.

    Returns
    -------
    JSONSerializer
        Configured JSON serializer
    """
    return JSONSerializer()


@pytest.fixture
def pickle_serializer() -> PickleSerializer:
    """
    Create PickleSerializer instance.

    Returns
    -------
    PickleSerializer
        Configured Pickle serializer
    """
    return PickleSerializer()


@pytest.fixture
def yaml_serializer() -> Optional[YAMLSerializer]:
    """
    Create YAMLSerializer instance if YAML available.

    Returns
    -------
    Optional[YAMLSerializer]
        YAML serializer or None if not available
    """
    if not HAS_YAML:
        pytest.skip("PyYAML not installed")
    return YAMLSerializer()


@pytest.fixture
def msgpack_serializer() -> Optional[MessagePackSerializer]:
    """
    Create MessagePackSerializer instance if msgpack available.

    Returns
    -------
    Optional[MessagePackSerializer]
        MessagePack serializer or None if not available
    """
    if not HAS_MSGPACK:
        pytest.skip("msgpack not installed")
    return MessagePackSerializer()


@pytest.fixture
def temp_file(tmp_path: Path) -> Path:
    """
    Create temporary file path.

    Parameters
    ----------
    tmp_path : Path
        Pytest builtin fixture for temporary directory

    Returns
    -------
    Path
        Temporary file path
    """
    return tmp_path / "test_file.json"


@pytest.fixture
def serializer_factory() -> SerializerFactory:
    """
    Create SerializerFactory instance.

    Returns
    -------
    SerializerFactory
        Fresh factory instance
    """
    return SerializerFactory()


# -------------------------------------------------------------
# EXCEPTION TESTS
# -------------------------------------------------------------


def test_serialization_error_inherits_from_exception() -> None:
    """Test SerializationError is proper Exception subclass."""
    # ARRANGE
    error: SerializationError = SerializationError("test error")

    # ASSERT
    assert isinstance(error, Exception)
    assert str(error) == "test error"


def test_unsupported_format_error_inherits_from_serialization_error() -> None:
    """Test UnsupportedFormatError is SerializationError subclass."""
    # ARRANGE
    error: UnsupportedFormatError = UnsupportedFormatError("unsupported")

    # ASSERT
    assert isinstance(error, SerializationError)
    assert isinstance(error, Exception)
    assert str(error) == "unsupported"


# -------------------------------------------------------------
# JSONSerializer TESTS
# -------------------------------------------------------------


def test_json_serializer_serializes_dict_correctly(
    json_serializer: JSONSerializer, sample_data: Dict[str, Any]
) -> None:
    """Test JSONSerializer serializes dictionary to JSON string."""
    # ACT
    result: str = json_serializer.serialize(sample_data)

    # ASSERT
    assert isinstance(result, str)
    assert "test_value" in result
    assert "42" in result
    parsed: Dict[str, Any] = json.loads(result)
    assert parsed == sample_data


def test_json_serializer_deserializes_string_correctly(json_serializer: JSONSerializer) -> None:
    """Test JSONSerializer deserializes JSON string to dict."""
    # ARRANGE
    json_string: str = '{"key":"value","number":123}'

    # ACT
    result: Dict[str, Any] = json_serializer.deserialize(json_string)

    # ASSERT
    assert isinstance(result, dict)
    assert result["key"] == "value"
    assert result["number"] == 123


def test_json_serializer_deserializes_bytes_correctly(json_serializer: JSONSerializer) -> None:
    """Test JSONSerializer deserializes JSON bytes to dict."""
    # ARRANGE
    json_bytes: bytes = b'{"key":"value"}'

    # ACT
    result: Dict[str, Any] = json_serializer.deserialize(json_bytes)

    # ASSERT
    assert isinstance(result, dict)
    assert result["key"] == "value"


def test_json_serializer_raises_error_on_invalid_json(json_serializer: JSONSerializer) -> None:
    """Test JSONSerializer raises SerializationError for invalid JSON."""
    # ARRANGE
    invalid_json: str = "{invalid json syntax"

    # ACT & ASSERT
    with pytest.raises(SerializationError, match="JSON deserialization failed"):
        json_serializer.deserialize(invalid_json)


def test_json_serializer_raises_error_on_non_serializable_data(json_serializer: JSONSerializer) -> None:
    """Test JSONSerializer raises SerializationError for non-serializable objects."""
    # ARRANGE
    class NonSerializable:
        pass

    non_serializable_data: NonSerializable = NonSerializable()

    # ACT & ASSERT
    with pytest.raises(SerializationError, match="JSON serialization failed"):
        json_serializer.serialize(non_serializable_data)


@pytest.mark.parametrize(
    "input_data,expected_type",
    [
        (None, type(None)),
        ("", str),
        ([], list),
        ({}, dict),
        (0, int),
        (False, bool),
    ],
)
def test_json_serializer_handles_edge_case_values(
    json_serializer: JSONSerializer, input_data: Any, expected_type: type
) -> None:
    """Test JSONSerializer correctly handles edge case values."""
    # ACT
    serialized: str = json_serializer.serialize(input_data)
    deserialized: Any = json_serializer.deserialize(serialized)

    # ASSERT
    assert type(deserialized) == expected_type
    assert deserialized == input_data


# -------------------------------------------------------------
# PickleSerializer TESTS
# -------------------------------------------------------------


def test_pickle_serializer_serializes_data_correctly(
    pickle_serializer: PickleSerializer, sample_data: Dict[str, Any]
) -> None:
    """Test PickleSerializer serializes data to bytes."""
    # ACT
    result: bytes = pickle_serializer.serialize(sample_data)

    # ASSERT
    assert isinstance(result, bytes)
    assert len(result) > 0


def test_pickle_serializer_deserializes_bytes_correctly(pickle_serializer: PickleSerializer) -> None:
    """Test PickleSerializer deserializes pickle bytes to object."""
    # ARRANGE
    original_data: Dict[str, int] = {"key": 123}
    pickled_data: bytes = pickle.dumps(original_data)

    # ACT
    result: Dict[str, int] = pickle_serializer.deserialize(pickled_data)

    # ASSERT
    assert isinstance(result, dict)
    assert result == original_data


def test_pickle_serializer_deserializes_string_by_encoding(pickle_serializer: PickleSerializer) -> None:
    """Test PickleSerializer converts string to bytes before unpickling."""
    # ARRANGE
    original_data: List[int] = [1, 2, 3]
    pickled_bytes: bytes = pickle.dumps(original_data)
    pickled_string: str = pickled_bytes.decode("latin-1")  # Use latin-1 for binary data

    # ACT
    result: List[int] = pickle_serializer.deserialize(pickled_string)

    # ASSERT
    assert result == original_data


def test_pickle_serializer_raises_error_on_corrupted_data(pickle_serializer: PickleSerializer) -> None:  # CRITICAL TEST
    """Test PickleSerializer raises SerializationError for corrupted pickle data."""
    # ARRANGE
    corrupted_data: bytes = b"this is not valid pickle data"

    # ACT & ASSERT
    with pytest.raises(SerializationError, match="Pickle deserialization failed"):
        pickle_serializer.deserialize(corrupted_data)


def test_pickle_serializer_handles_complex_objects(pickle_serializer: PickleSerializer) -> None:
    """Test PickleSerializer handles complex Python objects."""
    # ARRANGE
    class CustomClass:
        def __init__(self, value: int):
            self.value: int = value

        def __eq__(self, other: Any) -> bool:
            return isinstance(other, CustomClass) and self.value == other.value

    original_obj: CustomClass = CustomClass(42)

    # ACT
    serialized: bytes = pickle_serializer.serialize(original_obj)
    deserialized: CustomClass = pickle_serializer.deserialize(serialized)

    # ASSERT
    assert isinstance(deserialized, CustomClass)
    assert deserialized.value == 42
    assert deserialized == original_obj


# -------------------------------------------------------------
# YAMLSerializer TESTS
# -------------------------------------------------------------


def test_yaml_serializer_raises_import_error_when_yaml_not_available() -> None:
    """Test YAMLSerializer raises ImportError when PyYAML not installed."""
    # ARRANGE & ACT & ASSERT
    if HAS_YAML:
        pytest.skip("YAML is available, cannot test ImportError")
    else:
        with pytest.raises(ImportError, match="PyYAML is required"):
            YAMLSerializer()


def test_yaml_serializer_serializes_data_correctly(
    yaml_serializer: Optional[YAMLSerializer], sample_data: Dict[str, Any]
) -> None:
    """Test YAMLSerializer serializes data to YAML string."""
    # ACT
    result: str = yaml_serializer.serialize(sample_data)

    # ASSERT
    assert isinstance(result, str)
    assert "test_value" in result
    assert "string:" in result or "string :" in result


def test_yaml_serializer_deserializes_string_correctly(yaml_serializer: Optional[YAMLSerializer]) -> None:
    """Test YAMLSerializer deserializes YAML string to dict."""
    # ARRANGE
    yaml_string: str = "key: value\nnumber: 123\n"

    # ACT
    result: Dict[str, Any] = yaml_serializer.deserialize(yaml_string)

    # ASSERT
    assert isinstance(result, dict)
    assert result["key"] == "value"
    assert result["number"] == 123


def test_yaml_serializer_deserializes_bytes_correctly(yaml_serializer: Optional[YAMLSerializer]) -> None:
    """Test YAMLSerializer deserializes YAML bytes to dict."""
    # ARRANGE
    yaml_bytes: bytes = b"key: value\n"

    # ACT
    result: Dict[str, Any] = yaml_serializer.deserialize(yaml_bytes)

    # ASSERT
    assert isinstance(result, dict)
    assert result["key"] == "value"


def test_yaml_serializer_raises_error_on_invalid_yaml(yaml_serializer: Optional[YAMLSerializer]) -> None:
    """Test YAMLSerializer raises SerializationError for invalid YAML."""
    # ARRANGE
    invalid_yaml: str = "key: value\n  invalid indentation"

    # ACT & ASSERT
    with pytest.raises(SerializationError, match="YAML deserialization failed"):
        yaml_serializer.deserialize(invalid_yaml)


# -------------------------------------------------------------
# MessagePackSerializer TESTS
# -------------------------------------------------------------


def test_msgpack_serializer_raises_import_error_when_msgpack_not_available() -> None:
    """Test MessagePackSerializer raises ImportError when msgpack not installed."""
    # ARRANGE & ACT & ASSERT
    if HAS_MSGPACK:
        pytest.skip("msgpack is available, cannot test ImportError")
    else:
        with pytest.raises(ImportError, match="msgpack is required"):
            MessagePackSerializer()


def test_msgpack_serializer_serializes_data_correctly(
    msgpack_serializer: Optional[MessagePackSerializer], sample_data: Dict[str, Any]
) -> None:
    """Test MessagePackSerializer serializes data to bytes."""
    # ACT
    result: bytes = msgpack_serializer.serialize(sample_data)

    # ASSERT
    assert isinstance(result, bytes)
    assert len(result) > 0


def test_msgpack_serializer_deserializes_bytes_correctly(
    msgpack_serializer: Optional[MessagePackSerializer],
) -> None:
    """Test MessagePackSerializer deserializes msgpack bytes to dict."""
    # ARRANGE
    if not HAS_MSGPACK:
        pytest.skip("msgpack not installed")
    import msgpack

    original_data: Dict[str, int] = {"key": 123}
    packed_data: bytes = msgpack.packb(original_data, use_bin_type=True)

    # ACT
    result: Dict[str, int] = msgpack_serializer.deserialize(packed_data)

    # ASSERT
    assert isinstance(result, dict)
    assert result == original_data


def test_msgpack_serializer_raises_error_on_corrupted_data(
    msgpack_serializer: Optional[MessagePackSerializer],
) -> None:
    """Test MessagePackSerializer raises SerializationError for corrupted data."""
    # ARRANGE
    corrupted_data: bytes = b"this is not valid msgpack data"

    # ACT & ASSERT
    with pytest.raises(SerializationError, match="MessagePack deserialization failed"):
        msgpack_serializer.deserialize(corrupted_data)


# -------------------------------------------------------------
# Serializer.configure() TESTS
# -------------------------------------------------------------


def test_serializer_configure_sets_compression(json_serializer: JSONSerializer) -> None:
    """Test Serializer.configure() sets compression flag."""
    # ARRANGE
    assert json_serializer.compression is False

    # ACT
    json_serializer.configure(compression=True)

    # ASSERT
    assert json_serializer.compression is True


def test_serializer_configure_sets_encoding(json_serializer: JSONSerializer) -> None:
    """Test Serializer.configure() sets encoding."""
    # ARRANGE
    assert json_serializer.encoding == "utf-8"

    # ACT
    json_serializer.configure(encoding="latin-1")

    # ASSERT
    assert json_serializer.encoding == "latin-1"


def test_serializer_configure_sets_both_options(json_serializer: JSONSerializer) -> None:
    """Test Serializer.configure() sets multiple options."""
    # ACT
    json_serializer.configure(compression=True, encoding="utf-16")

    # ASSERT
    assert json_serializer.compression is True
    assert json_serializer.encoding == "utf-16"


# -------------------------------------------------------------
# Serializer.to_file() TESTS (CRITICAL)
# -------------------------------------------------------------


def test_serializer_to_file_writes_json_correctly(
    json_serializer: JSONSerializer, sample_data: Dict[str, Any], temp_file: Path
) -> None:  # CRITICAL TEST
    """Test Serializer.to_file() writes JSON data to file."""
    # ACT
    json_serializer.to_file(sample_data, str(temp_file))

    # ASSERT
    assert temp_file.exists()
    content: str = temp_file.read_text()
    parsed: Dict[str, Any] = json.loads(content)
    assert parsed == sample_data


def test_serializer_to_file_writes_compressed_correctly(
    json_serializer: JSONSerializer, sample_data: Dict[str, Any], tmp_path: Path
) -> None:  # CRITICAL TEST
    """Test Serializer.to_file() writes compressed gzip file."""
    # ARRANGE
    compressed_file: Path = tmp_path / "compressed.json.gz"
    json_serializer.configure(compression=True)

    # ACT
    json_serializer.to_file(sample_data, str(compressed_file))

    # ASSERT
    assert compressed_file.exists()
    with gzip.open(compressed_file, "rb") as f:
        content: bytes = f.read()
        parsed: Dict[str, Any] = json.loads(content)
    assert parsed == sample_data


def test_serializer_to_file_writes_bytes_correctly(
    pickle_serializer: PickleSerializer, sample_data: Dict[str, Any], tmp_path: Path
) -> None:  # CRITICAL TEST
    """Test Serializer.to_file() writes binary pickle data correctly."""
    # ARRANGE
    pickle_file: Path = tmp_path / "data.pkl"

    # ACT
    pickle_serializer.to_file(sample_data, str(pickle_file))

    # ASSERT
    assert pickle_file.exists()
    content: bytes = pickle_file.read_bytes()
    unpickled: Dict[str, Any] = pickle.loads(content)
    assert unpickled == sample_data


def test_serializer_to_file_raises_error_when_write_fails(
    json_serializer: JSONSerializer, sample_data: Dict[str, Any]
) -> None:  # CRITICAL TEST
    """Test Serializer.to_file() raises SerializationError when write fails."""
    # ARRANGE
    invalid_path: str = "/nonexistent/directory/file.json"

    # ACT & ASSERT
    with pytest.raises(SerializationError, match="Failed to write to file"):
        json_serializer.to_file(sample_data, invalid_path)


def test_serializer_to_file_raises_error_on_permission_denied(
    json_serializer: JSONSerializer, sample_data: Dict[str, Any], tmp_path: Path
) -> None:  # CRITICAL TEST
    """Test Serializer.to_file() raises SerializationError on permission denied."""
    # ARRANGE
    protected_file: Path = tmp_path / "protected.json"
    protected_file.touch()
    protected_file.chmod(0o000)  # Remove all permissions

    # ACT & ASSERT
    try:
        with pytest.raises(SerializationError, match="Failed to write to file"):
            json_serializer.to_file(sample_data, str(protected_file))
    finally:
        # Cleanup: restore permissions
        protected_file.chmod(0o644)


def test_serializer_to_file_creates_parent_directory_if_possible(
    json_serializer: JSONSerializer, sample_data: Dict[str, Any], tmp_path: Path
) -> None:  # CRITICAL TEST
    """Test Serializer.to_file() behavior when parent directory doesn't exist."""
    # ARRANGE
    nested_file: Path = tmp_path / "subdir" / "file.json"

    # ACT & ASSERT
    # Should raise error because parent directory doesn't exist
    with pytest.raises(SerializationError, match="Failed to write to file"):
        json_serializer.to_file(sample_data, str(nested_file))


# -------------------------------------------------------------
# Serializer.from_file() TESTS (CRITICAL)
# -------------------------------------------------------------


def test_serializer_from_file_reads_json_correctly(
    json_serializer: JSONSerializer, sample_data: Dict[str, Any], temp_file: Path
) -> None:  # CRITICAL TEST
    """Test Serializer.from_file() reads JSON file correctly."""
    # ARRANGE
    temp_file.write_text(json.dumps(sample_data))

    # ACT
    result: Dict[str, Any] = json_serializer.from_file(str(temp_file))

    # ASSERT
    assert result == sample_data


def test_serializer_from_file_reads_compressed_correctly(
    json_serializer: JSONSerializer, sample_data: Dict[str, Any], tmp_path: Path
) -> None:  # CRITICAL TEST
    """Test Serializer.from_file() reads compressed gzip file."""
    # ARRANGE
    compressed_file: Path = tmp_path / "compressed.json.gz"
    json_serializer.configure(compression=True)
    with gzip.open(compressed_file, "wt") as f:
        json.dump(sample_data, f)

    # ACT
    result: Dict[str, Any] = json_serializer.from_file(str(compressed_file))

    # ASSERT
    assert result == sample_data


def test_serializer_from_file_auto_detects_gzip_from_extension(
    json_serializer: JSONSerializer, sample_data: Dict[str, Any], tmp_path: Path
) -> None:  # CRITICAL TEST
    """Test Serializer.from_file() auto-detects .gz files without explicit config."""
    # ARRANGE
    gz_file: Path = tmp_path / "data.json.gz"
    with gzip.open(gz_file, "wt") as f:
        json.dump(sample_data, f)

    # ACT (without configuring compression)
    result: Dict[str, Any] = json_serializer.from_file(str(gz_file))

    # ASSERT
    assert result == sample_data


def test_serializer_from_file_reads_bytes_correctly(
    pickle_serializer: PickleSerializer, sample_data: Dict[str, Any], tmp_path: Path
) -> None:  # CRITICAL TEST
    """Test Serializer.from_file() reads binary pickle file correctly."""
    # ARRANGE
    pickle_file: Path = tmp_path / "data.pkl"
    pickle_file.write_bytes(pickle.dumps(sample_data))

    # ACT
    result: Dict[str, Any] = pickle_serializer.from_file(str(pickle_file))

    # ASSERT
    assert result == sample_data


def test_serializer_from_file_raises_error_when_file_not_found(
    json_serializer: JSONSerializer,
) -> None:  # CRITICAL TEST
    """Test Serializer.from_file() raises SerializationError when file doesn't exist."""
    # ARRANGE
    nonexistent_file: str = "/tmp/does_not_exist_12345.json"

    # ACT & ASSERT
    with pytest.raises(SerializationError, match="Failed to read from file"):
        json_serializer.from_file(nonexistent_file)


def test_serializer_from_file_raises_error_on_corrupted_file(
    json_serializer: JSONSerializer, temp_file: Path
) -> None:  # CRITICAL TEST
    """Test Serializer.from_file() raises SerializationError for corrupted file."""
    # ARRANGE
    temp_file.write_text("this is not valid json content {{{")

    # ACT & ASSERT
    with pytest.raises(SerializationError, match="Failed to read from file"):
        json_serializer.from_file(str(temp_file))


def test_serializer_from_file_handles_unicode_decode_error_gracefully(
    pickle_serializer: PickleSerializer, tmp_path: Path
) -> None:  # CRITICAL TEST
    """Test Serializer.from_file() handles binary data that can't be decoded."""
    # ARRANGE
    binary_file: Path = tmp_path / "binary.pkl"
    binary_data: bytes = pickle.dumps({"key": "value"})
    binary_file.write_bytes(binary_data)

    # ACT
    result: Dict[str, str] = pickle_serializer.from_file(str(binary_file))

    # ASSERT
    assert result == {"key": "value"}


# -------------------------------------------------------------
# SerializerFactory TESTS
# -------------------------------------------------------------


def test_serializer_factory_get_serializer_returns_json(serializer_factory: SerializerFactory) -> None:
    """Test SerializerFactory.get_serializer() returns JSONSerializer."""
    # ACT
    serializer: Serializer = serializer_factory.get_serializer("json")

    # ASSERT
    assert isinstance(serializer, JSONSerializer)


def test_serializer_factory_get_serializer_returns_pickle(serializer_factory: SerializerFactory) -> None:
    """Test SerializerFactory.get_serializer() returns PickleSerializer."""
    # ACT
    serializer: Serializer = serializer_factory.get_serializer("pickle")

    # ASSERT
    assert isinstance(serializer, PickleSerializer)


def test_serializer_factory_get_serializer_case_insensitive(serializer_factory: SerializerFactory) -> None:
    """Test SerializerFactory.get_serializer() is case-insensitive."""
    # ACT
    serializer_lower: Serializer = serializer_factory.get_serializer("json")
    serializer_upper: Serializer = serializer_factory.get_serializer("JSON")
    serializer_mixed: Serializer = serializer_factory.get_serializer("JsOn")

    # ASSERT
    assert type(serializer_lower) == type(serializer_upper) == type(serializer_mixed)


def test_serializer_factory_get_serializer_raises_error_for_unsupported_format(
    serializer_factory: SerializerFactory,
) -> None:
    """Test SerializerFactory.get_serializer() raises UnsupportedFormatError."""
    # ACT & ASSERT
    with pytest.raises(UnsupportedFormatError, match="Unsupported format 'xml'"):
        serializer_factory.get_serializer("xml")


@pytest.mark.parametrize(
    "format_type,expected_class",
    [
        ("json", JSONSerializer),
        ("pickle", PickleSerializer),
    ],
)
def test_serializer_factory_get_serializer_various_formats(
    serializer_factory: SerializerFactory, format_type: str, expected_class: type
) -> None:
    """Test SerializerFactory.get_serializer() returns correct serializer types."""
    # ACT
    serializer: Serializer = serializer_factory.get_serializer(format_type)

    # ASSERT
    assert isinstance(serializer, expected_class)


def test_serializer_factory_register_serializer_adds_custom_format(
    serializer_factory: SerializerFactory,
) -> None:
    """Test SerializerFactory.register_serializer() registers custom serializer."""
    # ARRANGE
    class CustomSerializer(Serializer):
        def serialize(self, data: Any) -> str:
            return "custom"

        def deserialize(self, data: Union[str, bytes]) -> Any:
            return "custom"

    # ACT
    serializer_factory.register_serializer("custom", CustomSerializer)
    serializer: Serializer = serializer_factory.get_serializer("custom")

    # ASSERT
    assert isinstance(serializer, CustomSerializer)


def test_serializer_factory_register_serializer_raises_type_error_for_invalid_class(
    serializer_factory: SerializerFactory,
) -> None:
    """Test SerializerFactory.register_serializer() raises TypeError for non-Serializer class."""
    # ARRANGE
    class NotASerializer:
        pass

    # ACT & ASSERT
    with pytest.raises(TypeError, match="must be subclass of Serializer"):
        serializer_factory.register_serializer("invalid", NotASerializer)


def test_serializer_factory_register_serializer_handles_case_insensitive(
    serializer_factory: SerializerFactory,
) -> None:
    """Test SerializerFactory.register_serializer() converts format to lowercase."""
    # ARRANGE
    class CustomSerializer(Serializer):
        def serialize(self, data: Any) -> str:
            return "custom"

        def deserialize(self, data: Union[str, bytes]) -> Any:
            return "custom"

    # ACT
    serializer_factory.register_serializer("CUSTOM", CustomSerializer)
    serializer: Serializer = serializer_factory.get_serializer("custom")

    # ASSERT
    assert isinstance(serializer, CustomSerializer)


def test_serializer_factory_list_available_formats_returns_sorted_list(
    serializer_factory: SerializerFactory,
) -> None:
    """Test SerializerFactory.list_available_formats() returns sorted format list."""
    # ACT
    formats: List[str] = serializer_factory.list_available_formats()

    # ASSERT
    assert isinstance(formats, list)
    assert "json" in formats
    assert "pickle" in formats
    assert formats == sorted(formats)


def test_serializer_factory_is_singleton() -> None:
    """Test SerializerFactory is singleton (same instance returned)."""
    # ACT
    factory1: SerializerFactory = SerializerFactory()
    factory2: SerializerFactory = SerializerFactory()

    # ASSERT
    assert factory1 is factory2


# -------------------------------------------------------------
# _detect_format_from_extension() TESTS
# -------------------------------------------------------------


@pytest.mark.parametrize(
    "filepath,expected_format",
    [
        ("file.json", "json"),
        ("file.pkl", "pickle"),
        ("file.pickle", "pickle"),
        ("file.yaml", "yaml"),
        ("file.yml", "yaml"),
        ("file.mp", "msgpack"),
        ("file.msgpack", "msgpack"),
        ("file.JSON", "json"),  # Case insensitive
        ("/path/to/file.json", "json"),
        ("../relative/path/file.pkl", "pickle"),
    ],
)
def test_detect_format_from_extension_recognizes_standard_extensions(
    filepath: str, expected_format: str
) -> None:
    """Test _detect_format_from_extension() recognizes standard file extensions."""
    # ACT
    result: Optional[str] = _detect_format_from_extension(filepath)

    # ASSERT
    assert result == expected_format


@pytest.mark.parametrize(
    "filepath,expected_format",
    [
        ("file.json.gz", "json"),
        ("file.pkl.gz", "pickle"),
        ("file.yaml.gz", "yaml"),
        ("/path/to/compressed.json.gz", "json"),
    ],
)
def test_detect_format_from_extension_handles_compressed_files(
    filepath: str, expected_format: str
) -> None:
    """Test _detect_format_from_extension() handles .gz compressed files."""
    # ACT
    result: Optional[str] = _detect_format_from_extension(filepath)

    # ASSERT
    assert result == expected_format


@pytest.mark.parametrize(
    "filepath",
    [
        "file.txt",
        "file.csv",
        "file",
        "file.",
        "/path/without/extension",
        "file.unknown",
    ],
)
def test_detect_format_from_extension_returns_none_for_unknown_extensions(filepath: str) -> None:
    """Test _detect_format_from_extension() returns None for unknown extensions."""
    # ACT
    result: Optional[str] = _detect_format_from_extension(filepath)

    # ASSERT
    assert result is None


def test_detect_format_from_extension_handles_only_gz_extension() -> None:
    """Test _detect_format_from_extension() handles file with only .gz extension."""
    # ACT
    result: Optional[str] = _detect_format_from_extension("file.gz")

    # ASSERT
    assert result is None


@pytest.mark.parametrize(
    "filepath",
    [
        "",
        "   ",
    ],
)
def test_detect_format_from_extension_handles_empty_filepath(filepath: str) -> None:
    """Test _detect_format_from_extension() handles empty filepath."""
    # ACT
    result: Optional[str] = _detect_format_from_extension(filepath)

    # ASSERT
    assert result is None


# -------------------------------------------------------------
# CONVENIENCE FUNCTION TESTS
# -------------------------------------------------------------


def test_serialize_function_delegates_to_factory(sample_data: Dict[str, Any]) -> None:
    """Test serialize() convenience function delegates to SerializerFactory."""
    # ACT
    result: str = serialize(sample_data, "json")

    # ASSERT
    assert isinstance(result, str)
    parsed: Dict[str, Any] = json.loads(result)
    assert parsed == sample_data


def test_serialize_function_raises_error_for_invalid_format() -> None:
    """Test serialize() raises UnsupportedFormatError for invalid format."""
    # ACT & ASSERT
    with pytest.raises(UnsupportedFormatError, match="Unsupported format"):
        serialize({"key": "value"}, "invalid_format")


def test_deserialize_function_delegates_to_factory() -> None:
    """Test deserialize() convenience function delegates to SerializerFactory."""
    # ARRANGE
    json_data: str = '{"key":"value"}'

    # ACT
    result: Dict[str, str] = deserialize(json_data, "json")

    # ASSERT
    assert isinstance(result, dict)
    assert result["key"] == "value"


def test_deserialize_function_raises_error_for_invalid_format() -> None:
    """Test deserialize() raises UnsupportedFormatError for invalid format."""
    # ACT & ASSERT
    with pytest.raises(UnsupportedFormatError, match="Unsupported format"):
        deserialize('{"key":"value"}', "invalid_format")


# -------------------------------------------------------------
# to_file() CONVENIENCE FUNCTION TESTS (CRITICAL)
# -------------------------------------------------------------


def test_to_file_writes_json_with_auto_detection(
    sample_data: Dict[str, Any], tmp_path: Path
) -> None:  # CRITICAL TEST
    """Test to_file() auto-detects format and writes JSON file."""
    # ARRANGE
    json_file: Path = tmp_path / "data.json"

    # ACT
    to_file(sample_data, str(json_file))

    # ASSERT
    assert json_file.exists()
    content: str = json_file.read_text()
    parsed: Dict[str, Any] = json.loads(content)
    assert parsed == sample_data


def test_to_file_writes_pickle_with_auto_detection(
    sample_data: Dict[str, Any], tmp_path: Path
) -> None:  # CRITICAL TEST
    """Test to_file() auto-detects format and writes pickle file."""
    # ARRANGE
    pickle_file: Path = tmp_path / "data.pkl"

    # ACT
    to_file(sample_data, str(pickle_file))

    # ASSERT
    assert pickle_file.exists()
    content: bytes = pickle_file.read_bytes()
    unpickled: Dict[str, Any] = pickle.loads(content)
    assert unpickled == sample_data


def test_to_file_writes_with_explicit_format(
    sample_data: Dict[str, Any], tmp_path: Path
) -> None:  # CRITICAL TEST
    """Test to_file() uses explicit format parameter."""
    # ARRANGE
    file_path: Path = tmp_path / "data.txt"

    # ACT
    to_file(sample_data, str(file_path), format_type="json")

    # ASSERT
    assert file_path.exists()
    content: str = file_path.read_text()
    parsed: Dict[str, Any] = json.loads(content)
    assert parsed == sample_data


def test_to_file_passes_kwargs_to_serializer(
    sample_data: Dict[str, Any], tmp_path: Path
) -> None:  # CRITICAL TEST
    """Test to_file() passes configuration kwargs to serializer."""
    # ARRANGE
    compressed_file: Path = tmp_path / "data.json.gz"

    # ACT
    to_file(sample_data, str(compressed_file), compression=True)

    # ASSERT
    assert compressed_file.exists()
    with gzip.open(compressed_file, "rb") as f:
        content: bytes = f.read()
        parsed: Dict[str, Any] = json.loads(content)
    assert parsed == sample_data


def test_to_file_raises_error_when_format_cannot_be_detected(
    sample_data: Dict[str, Any], tmp_path: Path
) -> None:  # CRITICAL TEST
    """Test to_file() raises UnsupportedFormatError when format undetectable."""
    # ARRANGE
    unknown_file: Path = tmp_path / "data.unknown"

    # ACT & ASSERT
    with pytest.raises(UnsupportedFormatError, match="Cannot detect format"):
        to_file(sample_data, str(unknown_file))


def test_to_file_raises_error_for_invalid_explicit_format(
    sample_data: Dict[str, Any], tmp_path: Path
) -> None:  # CRITICAL TEST
    """Test to_file() raises UnsupportedFormatError for invalid explicit format."""
    # ARRANGE
    file_path: Path = tmp_path / "data.txt"

    # ACT & ASSERT
    with pytest.raises(UnsupportedFormatError, match="Unsupported format"):
        to_file(sample_data, str(file_path), format_type="invalid")


# -------------------------------------------------------------
# from_file() CONVENIENCE FUNCTION TESTS (CRITICAL)
# -------------------------------------------------------------


def test_from_file_reads_json_with_auto_detection(
    sample_data: Dict[str, Any], tmp_path: Path
) -> None:  # CRITICAL TEST
    """Test from_file() auto-detects format and reads JSON file."""
    # ARRANGE
    json_file: Path = tmp_path / "data.json"
    json_file.write_text(json.dumps(sample_data))

    # ACT
    result: Dict[str, Any] = from_file(str(json_file))

    # ASSERT
    assert result == sample_data


def test_from_file_reads_pickle_with_auto_detection(
    sample_data: Dict[str, Any], tmp_path: Path
) -> None:  # CRITICAL TEST
    """Test from_file() auto-detects format and reads pickle file."""
    # ARRANGE
    pickle_file: Path = tmp_path / "data.pkl"
    pickle_file.write_bytes(pickle.dumps(sample_data))

    # ACT
    result: Dict[str, Any] = from_file(str(pickle_file))

    # ASSERT
    assert result == sample_data


def test_from_file_reads_with_explicit_format(
    sample_data: Dict[str, Any], tmp_path: Path
) -> None:  # CRITICAL TEST
    """Test from_file() uses explicit format parameter."""
    # ARRANGE
    file_path: Path = tmp_path / "data.txt"
    file_path.write_text(json.dumps(sample_data))

    # ACT
    result: Dict[str, Any] = from_file(str(file_path), format_type="json")

    # ASSERT
    assert result == sample_data


def test_from_file_passes_kwargs_to_serializer(
    sample_data: Dict[str, Any], tmp_path: Path
) -> None:  # CRITICAL TEST
    """Test from_file() passes configuration kwargs to serializer."""
    # ARRANGE
    compressed_file: Path = tmp_path / "data.json.gz"
    with gzip.open(compressed_file, "wt") as f:
        json.dump(sample_data, f)

    # ACT
    result: Dict[str, Any] = from_file(str(compressed_file), compression=True)

    # ASSERT
    assert result == sample_data


def test_from_file_raises_error_when_format_cannot_be_detected(tmp_path: Path) -> None:  # CRITICAL TEST
    """Test from_file() raises UnsupportedFormatError when format undetectable."""
    # ARRANGE
    unknown_file: Path = tmp_path / "data.unknown"
    unknown_file.write_text("some content")

    # ACT & ASSERT
    with pytest.raises(UnsupportedFormatError, match="Cannot detect format"):
        from_file(str(unknown_file))


def test_from_file_raises_error_for_invalid_explicit_format(tmp_path: Path) -> None:  # CRITICAL TEST
    """Test from_file() raises UnsupportedFormatError for invalid explicit format."""
    # ARRANGE
    file_path: Path = tmp_path / "data.txt"
    file_path.write_text("content")

    # ACT & ASSERT
    with pytest.raises(UnsupportedFormatError, match="Unsupported format"):
        from_file(str(file_path), format_type="invalid")


def test_from_file_raises_error_when_file_not_found() -> None:  # CRITICAL TEST
    """Test from_file() raises SerializationError when file doesn't exist."""
    # ARRANGE
    nonexistent_file: str = "/tmp/nonexistent_12345.json"

    # ACT & ASSERT
    with pytest.raises(SerializationError, match="Failed to read from file"):
        from_file(nonexistent_file)


# -------------------------------------------------------------
# INTEGRATION TESTS
# -------------------------------------------------------------


@pytest.mark.parametrize(
    "format_type,file_extension",
    [
        ("json", ".json"),
        ("pickle", ".pkl"),
    ],
)
def test_roundtrip_serialization_integration(
    sample_data: Dict[str, Any], tmp_path: Path, format_type: str, file_extension: str
) -> None:
    """Test complete roundtrip: data -> file -> data with various formats."""
    # ARRANGE
    file_path: Path = tmp_path / f"roundtrip{file_extension}"

    # ACT
    to_file(sample_data, str(file_path), format_type=format_type)
    result: Dict[str, Any] = from_file(str(file_path), format_type=format_type)

    # ASSERT
    assert result == sample_data


def test_roundtrip_with_compression_integration(sample_data: Dict[str, Any], tmp_path: Path) -> None:
    """Test complete roundtrip with compression enabled."""
    # ARRANGE
    file_path: Path = tmp_path / "compressed.json.gz"

    # ACT
    to_file(sample_data, str(file_path), compression=True)
    result: Dict[str, Any] = from_file(str(file_path), compression=True)

    # ASSERT
    assert result == sample_data


def test_multiple_serializers_coexist_independently() -> None:
    """Test multiple serializer instances work independently."""
    # ARRANGE
    data1: Dict[str, int] = {"key": 1}
    data2: Dict[str, int] = {"key": 2}
    serializer1: JSONSerializer = JSONSerializer()
    serializer2: JSONSerializer = JSONSerializer()
    serializer1.configure(compression=True)
    serializer2.configure(compression=False)

    # ACT
    result1_compression: bool = serializer1.compression
    result2_compression: bool = serializer2.compression

    # ASSERT
    assert result1_compression is True
    assert result2_compression is False


# -------------------------------------------------------------
# EDGE CASE AND ERROR SCENARIO TESTS
# -------------------------------------------------------------


@pytest.mark.parametrize(
    "invalid_data",
    [
        {"circular_ref": None},  # Will add circular reference below
    ],
)
def test_json_serializer_handles_circular_references(json_serializer: JSONSerializer) -> None:
    """Test JSONSerializer raises error for circular references."""
    # ARRANGE
    circular_data: Dict[str, Any] = {"key": "value"}
    circular_data["circular_ref"] = circular_data  # Create circular reference

    # ACT & ASSERT
    with pytest.raises(SerializationError, match="JSON serialization failed"):
        json_serializer.serialize(circular_data)


def test_serializer_handles_very_large_data(json_serializer: JSONSerializer, tmp_path: Path) -> None:
    """Test serializer handles large data volumes."""
    # ARRANGE
    large_data: Dict[str, List[int]] = {"data": list(range(100000))}
    large_file: Path = tmp_path / "large.json"

    # ACT
    json_serializer.to_file(large_data, str(large_file))
    result: Dict[str, List[int]] = json_serializer.from_file(str(large_file))

    # ASSERT
    assert len(result["data"]) == 100000
    assert result == large_data


def test_serializer_handles_unicode_content(json_serializer: JSONSerializer, tmp_path: Path) -> None:
    """Test serializer correctly handles Unicode characters."""
    # ARRANGE
    unicode_data: Dict[str, str] = {
        "emoji": "😀🎉",
        "chinese": "你好世界",
        "arabic": "مرحبا بالعالم",
        "german": "Übergrößenträger",
    }
    unicode_file: Path = tmp_path / "unicode.json"

    # ACT
    json_serializer.to_file(unicode_data, str(unicode_file))
    result: Dict[str, str] = json_serializer.from_file(str(unicode_file))

    # ASSERT
    assert result == unicode_data


def test_pickle_serializer_security_warning_for_untrusted_data() -> None:  # CRITICAL TEST
    """
    Test pickle deserialization security consideration.

    WARNING: Pickle deserialization of untrusted data can execute arbitrary code.
    This test documents the security risk but does NOT test malicious payloads.
    """
    # ARRANGE
    serializer: PickleSerializer = PickleSerializer()
    safe_data: Dict[str, str] = {"safe": "data"}

    # ACT
    serialized: bytes = serializer.serialize(safe_data)
    deserialized: Dict[str, str] = serializer.deserialize(serialized)

    # ASSERT
    assert deserialized == safe_data
    # NOTE: In production, NEVER deserialize pickle data from untrusted sources!


def test_empty_file_handling(json_serializer: JSONSerializer, tmp_path: Path) -> None:
    """Test serializer handles empty file gracefully."""
    # ARRANGE
    empty_file: Path = tmp_path / "empty.json"
    empty_file.touch()

    # ACT & ASSERT
    with pytest.raises(SerializationError, match="Failed to read from file"):
        json_serializer.from_file(str(empty_file))
