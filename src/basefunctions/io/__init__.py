"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 I/O utilities including file operations, output redirection,
 and serialization support
 Log:
 v1.0 : Initial implementation
=============================================================================
"""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# File Functions
from basefunctions.io.filefunctions import (
    check_if_exists,
    check_if_file_exists,
    check_if_dir_exists,
    is_file,
    is_directory,
    get_file_name,
    get_file_extension,
    get_extension,
    get_base_name,
    get_base_name_prefix,
    get_path_name,
    get_parent_path_name,
    get_home_path,
    get_path_without_extension,
    get_current_directory,
    set_current_directory,
    rename_file,
    remove_file,
    create_directory,
    remove_directory,
    create_file_list,
    norm_path,
)

# Output Redirector
from basefunctions.io.output_redirector import (
    OutputTarget,
    OutputRedirector,
    FileTarget,
    DatabaseTarget,
    MemoryTarget,
    ThreadSafeOutputRedirector,
    redirect_output,
)

# Serializer
from basefunctions.io.serializer import (
    SerializerFactory,
    Serializer,
    JSONSerializer,
    PickleSerializer,
    YAMLSerializer,
    MessagePackSerializer,
    SerializationError,
    UnsupportedFormatError,
    serialize,
    deserialize,
    to_file,
    from_file,
)

# =============================================================================
# EXPORT DEFINITIONS
# =============================================================================
__all__ = [
    # File Functions
    "check_if_exists",
    "check_if_file_exists",
    "check_if_dir_exists",
    "is_file",
    "is_directory",
    "get_file_name",
    "get_file_extension",
    "get_extension",
    "get_base_name",
    "get_base_name_prefix",
    "get_path_name",
    "get_parent_path_name",
    "get_home_path",
    "get_path_without_extension",
    "get_current_directory",
    "set_current_directory",
    "rename_file",
    "remove_file",
    "create_directory",
    "remove_directory",
    "create_file_list",
    "norm_path",
    # Output Redirector
    "OutputTarget",
    "OutputRedirector",
    "FileTarget",
    "DatabaseTarget",
    "MemoryTarget",
    "ThreadSafeOutputRedirector",
    "redirect_output",
    # Serializer
    "SerializerFactory",
    "Serializer",
    "JSONSerializer",
    "PickleSerializer",
    "YAMLSerializer",
    "MessagePackSerializer",
    "SerializationError",
    "UnsupportedFormatError",
    "serialize",
    "deserialize",
    "to_file",
    "from_file",
]
