"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich

  Project : basefunctions

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  Unified serialization framework with multiple format support

  Log:
  v1.0 : Initial implementation
=============================================================================
"""

from __future__ import annotations

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Any, Type
from abc import ABC, abstractmethod
from pathlib import Path
import json
import pickle
import gzip
import os
from basefunctions.utils.logging import setup_logger
from basefunctions.utils.decorators import singleton

# Optional imports with fallbacks
try:
    import yaml

    HAS_YAML = True
except ImportError:
    HAS_YAML = False

try:
    import msgpack

    HAS_MSGPACK = True
except ImportError:
    HAS_MSGPACK = False

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


class SerializationError(Exception):
    """Base exception for serialization errors."""

    pass


class UnsupportedFormatError(SerializationError):
    """Raised when unsupported format is requested."""

    pass


class Serializer(ABC):
    """Abstract base class for all serializers."""

    def __init__(self):
        self.compression = False
        self.encoding = "utf-8"

    def configure(self, compression: bool = False, encoding: str = "utf-8") -> None:
        """
        Configure serializer options.

        Parameters
        ----------
        compression : bool, optional
            Enable gzip compression, by default False
        encoding : str, optional
            Text encoding for string data, by default 'utf-8'
        """
        self.compression = compression
        self.encoding = encoding

    @abstractmethod
    def serialize(self, data: Any) -> str | bytes:
        """
        Serialize data to string or bytes.

        Parameters
        ----------
        data : Any
            Data to serialize

        Returns
        -------
        Union[str, bytes]
            Serialized data
        """
        pass

    @abstractmethod
    def deserialize(self, data: str | bytes) -> Any:
        """
        Deserialize data from string or bytes.

        Parameters
        ----------
        data : Union[str, bytes]
            Serialized data

        Returns
        -------
        Any
            Deserialized object
        """
        pass

    def to_file(self, data: Any, filepath: str) -> None:
        """
        Serialize data to file.

        Parameters
        ----------
        data : Any
            Data to serialize
        filepath : str
            Target file path
        """
        try:
            serialized = self.serialize(data)

            if self.compression:
                if isinstance(serialized, str):
                    serialized = serialized.encode(self.encoding)

                with gzip.open(filepath, "wb") as f:
                    f.write(serialized)
            else:
                mode = "wb" if isinstance(serialized, bytes) else "w"
                encoding = None if isinstance(serialized, bytes) else self.encoding

                with open(filepath, mode, encoding=encoding) as f:
                    f.write(serialized)

        except Exception as e:
            raise SerializationError(f"Failed to write to file {filepath}: {str(e)}") from e

    def from_file(self, filepath: str) -> Any:
        """
        Deserialize data from file.

        Parameters
        ----------
        filepath : str
            Source file path

        Returns
        -------
        Any
            Deserialized object
        """
        try:
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"File not found: {filepath}")

            if self.compression or filepath.endswith(".gz"):
                with gzip.open(filepath, "rb") as f:
                    data = f.read()
                    # Try to decode if it's text-based format
                    try:
                        data = data.decode(self.encoding)
                    except UnicodeDecodeError:
                        pass  # Keep as bytes for binary formats
            else:
                # Auto-detect binary vs text
                with open(filepath, "rb") as f:
                    raw_data = f.read()

                try:
                    data = raw_data.decode(self.encoding)
                except UnicodeDecodeError:
                    data = raw_data

            return self.deserialize(data)

        except Exception as e:
            raise SerializationError(f"Failed to read from file {filepath}: {str(e)}") from e


class JSONSerializer(Serializer):
    """JSON serializer implementation."""

    def serialize(self, data: Any) -> str:
        """Serialize data to JSON string."""
        try:
            return json.dumps(data, ensure_ascii=False, indent=None, separators=(",", ":"))
        except Exception as e:
            raise SerializationError(f"JSON serialization failed: {str(e)}") from e

    def deserialize(self, data: str | bytes) -> Any:
        """Deserialize JSON string to object."""
        try:
            if isinstance(data, bytes):
                data = data.decode(self.encoding)
            return json.loads(data)
        except Exception as e:
            raise SerializationError(f"JSON deserialization failed: {str(e)}") from e


class PickleSerializer(Serializer):
    """Pickle serializer implementation."""

    def serialize(self, data: Any) -> bytes:
        """Serialize data to pickle bytes."""
        try:
            return pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)
        except Exception as e:
            raise SerializationError(f"Pickle serialization failed: {str(e)}") from e

    def deserialize(self, data: str | bytes) -> Any:
        """Deserialize pickle bytes to object."""
        try:
            if isinstance(data, str):
                data = data.encode(self.encoding)
            return pickle.loads(data)
        except Exception as e:
            raise SerializationError(f"Pickle deserialization failed: {str(e)}") from e


class YAMLSerializer(Serializer):
    """YAML serializer implementation."""

    def __init__(self):
        super().__init__()
        if not HAS_YAML:
            raise ImportError("PyYAML is required for YAML serialization")

    def serialize(self, data: Any) -> str:
        """Serialize data to YAML string."""
        try:
            return yaml.dump(data, default_flow_style=False, allow_unicode=True)
        except Exception as e:
            raise SerializationError(f"YAML serialization failed: {str(e)}") from e

    def deserialize(self, data: str | bytes) -> Any:
        """Deserialize YAML string to object."""
        try:
            if isinstance(data, bytes):
                data = data.decode(self.encoding)
            return yaml.safe_load(data)
        except Exception as e:
            raise SerializationError(f"YAML deserialization failed: {str(e)}") from e


class MessagePackSerializer(Serializer):
    """MessagePack serializer implementation."""

    def __init__(self):
        super().__init__()
        if not HAS_MSGPACK:
            raise ImportError("msgpack is required for MessagePack serialization")

    def serialize(self, data: Any) -> bytes:
        """Serialize data to MessagePack bytes."""
        try:
            return msgpack.packb(data, use_bin_type=True)
        except Exception as e:
            raise SerializationError(f"MessagePack serialization failed: {str(e)}") from e

    def deserialize(self, data: str | bytes) -> Any:
        """Deserialize MessagePack bytes to object."""
        try:
            if isinstance(data, str):
                data = data.encode(self.encoding)
            return msgpack.unpackb(data, raw=False, strict_map_key=False)
        except Exception as e:
            raise SerializationError(f"MessagePack deserialization failed: {str(e)}") from e


@singleton
class SerializerFactory:
    """Factory for creating serializer instances."""

    def __init__(self):
        self._serializers: dict[str, type[Serializer]] = {
            "json": JSONSerializer,
            "pickle": PickleSerializer,
        }

        # Register optional serializers if available
        if HAS_YAML:
            self._serializers["yaml"] = YAMLSerializer
            self._serializers["yml"] = YAMLSerializer

        if HAS_MSGPACK:
            self._serializers["msgpack"] = MessagePackSerializer
            self._serializers["mp"] = MessagePackSerializer

    def get_serializer(self, format_type: str) -> Serializer:
        """
        Get serializer instance for specified format.

        Parameters
        ----------
        format_type : str
            Serialization format (json, pickle, yaml, msgpack)

        Returns
        -------
        Serializer
            Serializer instance

        Raises
        ------
        UnsupportedFormatError
            If format is not supported
        """
        format_type = format_type.lower()

        if format_type not in self._serializers:
            available = ", ".join(self.list_available_formats())
            raise UnsupportedFormatError(f"Unsupported format '{format_type}'. Available: {available}")

        try:
            return self._serializers[format_type]()
        except Exception as e:
            raise SerializationError(f"Failed to create {format_type} serializer: {str(e)}") from e

    def register_serializer(self, format_type: str, serializer_class: type[Serializer]) -> None:
        """
        Register custom serializer.

        Parameters
        ----------
        format_type : str
            Format identifier
        serializer_class : Type[Serializer]
            Serializer class
        """
        if not issubclass(serializer_class, Serializer):
            raise TypeError("serializer_class must be subclass of Serializer")

        self._serializers[format_type.lower()] = serializer_class

    def list_available_formats(self) -> list[str]:
        """
        Get list of available serialization formats.

        Returns
        -------
        List[str]
            Available format names
        """
        return sorted(self._serializers.keys())


def _detect_format_from_extension(filepath: str) -> str | None:
    """
    Detect serialization format from file extension.

    Parameters
    ----------
    filepath : str
        File path

    Returns
    -------
    Optional[str]
        Detected format or None
    """
    suffix = Path(filepath).suffix.lower()

    # Handle compressed files
    if suffix == ".gz":
        suffix = Path(filepath).suffixes[-2].lower() if len(Path(filepath).suffixes) > 1 else ""

    extension_map = {
        ".json": "json",
        ".pkl": "pickle",
        ".pickle": "pickle",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".mp": "msgpack",
        ".msgpack": "msgpack",
    }

    return extension_map.get(suffix)


# -------------------------------------------------------------
# CONVENIENCE FUNCTIONS
# -------------------------------------------------------------


def serialize(data: Any, format_type: str) -> str | bytes:
    """
    Serialize data using specified format.

    Parameters
    ----------
    data : Any
        Data to serialize
    format_type : str
        Serialization format

    Returns
    -------
    Union[str, bytes]
        Serialized data
    """
    factory = SerializerFactory()
    serializer = factory.get_serializer(format_type)
    return serializer.serialize(data)


def deserialize(data: str | bytes, format_type: str) -> Any:
    """
    Deserialize data using specified format.

    Parameters
    ----------
    data : Union[str, bytes]
        Serialized data
    format_type : str
        Serialization format

    Returns
    -------
    Any
        Deserialized object
    """
    factory = SerializerFactory()
    serializer = factory.get_serializer(format_type)
    return serializer.deserialize(data)


def to_file(data: Any, filepath: str, format_type: str | None = None, **kwargs) -> None:
    """
    Serialize data to file with auto-format detection.

    Parameters
    ----------
    data : Any
        Data to serialize
    filepath : str
        Target file path
    format_type : Optional[str], optional
        Explicit format type, auto-detected if None
    **kwargs
        Additional serializer configuration options
    """
    if format_type is None:
        format_type = _detect_format_from_extension(filepath)
        if format_type is None:
            raise UnsupportedFormatError(f"Cannot detect format from file extension: {filepath}")

    factory = SerializerFactory()
    serializer = factory.get_serializer(format_type)

    if kwargs:
        serializer.configure(**kwargs)

    serializer.to_file(data, filepath)


def from_file(filepath: str, format_type: str | None = None, **kwargs) -> Any:
    """
    Deserialize data from file with auto-format detection.

    Parameters
    ----------
    filepath : str
        Source file path
    format_type : Optional[str], optional
        Explicit format type, auto-detected if None
    **kwargs
        Additional serializer configuration options

    Returns
    -------
    Any
        Deserialized object
    """
    if format_type is None:
        format_type = _detect_format_from_extension(filepath)
        if format_type is None:
            raise UnsupportedFormatError(f"Cannot detect format from file extension: {filepath}")

    factory = SerializerFactory()
    serializer = factory.get_serializer(format_type)

    if kwargs:
        serializer.configure(**kwargs)

    return serializer.from_file(filepath)
