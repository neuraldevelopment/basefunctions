"""
=============================================================================

 Licensed Materials, Property of neuraldevelopment , Munich

 Project : test_header_recognition

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 Test script to debug header recognition for neuraldevelopment headers

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import re
import sys

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


def extract_first_multiline_comment(content):
    """Extract the first multiline comment from Python file content."""
    start = content.find('"""')
    if start == -1:
        return None

    end = content.find('"""', start + 3)
    if end == -1:
        return None

    header = content[start + 3 : end].strip()
    return header


def is_neuraldevelopment_header(header_content):
    """Check if header matches neuraldevelopment pattern using regex."""
    if not header_content:
        return False

    print(f"Header content to analyze:\n{repr(header_content)}\n")

    patterns = [
        r"Licensed Materials.*Property of neuraldevelopment",
        r"Project\s*:",
        r"Copyright.*neuraldevelopment",
        r"All rights reserved",
        r"Description",
    ]

    for i, pattern in enumerate(patterns):
        match = re.search(pattern, header_content, re.IGNORECASE | re.DOTALL)
        print(f"Pattern {i+1}: {pattern}")
        print(f"  Match: {'YES' if match else 'NO'}")
        if match:
            print(f"  Matched text: {repr(match.group())}")
        print()

    # Check if all patterns match
    all_match = all(
        re.search(pattern, header_content, re.IGNORECASE | re.DOTALL) for pattern in patterns
    )

    return all_match


def main():
    filename = "test.py"

    try:
        with open(filename, "r", encoding="utf-8") as f:
            content = f.read()

        print(f"Reading file: {filename}")
        print("=" * 60)

        header = extract_first_multiline_comment(content)

        if header is None:
            print("No multiline comment found!")
            return

        print("Header extraction successful!")
        print("=" * 60)

        result = is_neuraldevelopment_header(header)

        print("=" * 60)
        print(
            f"Final result: {'NEURALDEVELOPMENT HEADER DETECTED' if result else 'NO NEURALDEVELOPMENT HEADER'}"
        )

    except FileNotFoundError:
        print(f"Error: File '{filename}' not found!")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
